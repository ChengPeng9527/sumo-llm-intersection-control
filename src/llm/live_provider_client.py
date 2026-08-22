from __future__ import annotations

import hashlib
import json
import random
import re
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from types import SimpleNamespace
from typing import Any, Callable
import uuid

DEFAULT_TOKENS_PER_MINUTE_LIMIT = 8000
try:  # pragma: no cover - optional dependency in minimal runtimes
    from openai import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError
except Exception:  # pragma: no cover - fallback path when openai is unavailable
    APIConnectionError = APIStatusError = APITimeoutError = RateLimitError = None

DEFAULT_REQUESTS_PER_MINUTE_LIMIT = 30
DEFAULT_ESTIMATED_REQUEST_TOKENS = 256 + 512
DEFAULT_SAFETY_MARGIN = 0.9
DEFAULT_WINDOW_SECONDS = 60.0
DEFAULT_MAX_RETRIES = 4
DEFAULT_TIMEOUT_SECONDS = 30.0

_SHARED_STATE_LOCK = threading.Lock()
_SHARED_STATE_BY_KEY: dict[str, "ProviderReliabilityState"] = {}


def _as_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _as_int(value: object) -> int | None:
    try:
        if value is None:
            return None
        return int(float(value))
    except Exception:
        return None


def _header_dict(headers: object) -> dict[str, str]:
    if headers is None:
        return {}
    if isinstance(headers, dict):
        return {str(key).lower(): str(value) for key, value in headers.items()}
    items = getattr(headers, "items", None)
    if callable(items):
        return {str(key).lower(): str(value) for key, value in items()}
    return {}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _sha256_text(text: object) -> str:
    if text is None:
        return ""
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest().upper()


def _normalize_request_context(request_context: object) -> dict[str, Any]:
    if isinstance(request_context, dict):
        return dict(request_context)
    return {}


def _hash_prompt_messages(messages: list[dict[str, Any]]) -> str:
    return _sha256_text(json.dumps(messages, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def get_shared_provider_reliability_state(provider_key: str = "default") -> "ProviderReliabilityState":
    key = str(provider_key or "default").strip().lower()
    with _SHARED_STATE_LOCK:
        state = _SHARED_STATE_BY_KEY.get(key)
        if state is None:
            state = ProviderReliabilityState()
            _SHARED_STATE_BY_KEY[key] = state
        return state


def reset_shared_provider_reliability_state(provider_key: str | None = None) -> None:
    with _SHARED_STATE_LOCK:
        if provider_key is None:
            _SHARED_STATE_BY_KEY.clear()
        else:
            _SHARED_STATE_BY_KEY.pop(str(provider_key or "default").strip().lower(), None)


def _header_value(headers: object, *names: str) -> str:
    normalized = _header_dict(headers)
    for name in names:
        value = normalized.get(name.lower())
        if value not in {None, ""}:
            return str(value)
    return ""


def _parse_duration_seconds(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    numeric = _as_float(text)
    if numeric is not None:
        return max(0.0, numeric)
    unit_matches = re.findall(r"(\d+(?:\.\d+)?)(ms|s|m|h)", text, flags=re.IGNORECASE)
    if not unit_matches:
        return None
    total = 0.0
    for number_text, unit in unit_matches:
        number = float(number_text)
        unit = unit.lower()
        if unit == "ms":
            total += number / 1000.0
        elif unit == "s":
            total += number
        elif unit == "m":
            total += number * 60.0
        elif unit == "h":
            total += number * 3600.0
    return max(0.0, total)


def _parse_retry_after_seconds(headers: object, body_text: str = "") -> float | None:
    header_value = _header_value(headers, "retry-after")
    if header_value:
        delay = _parse_duration_seconds(header_value)
        if delay is not None:
            return max(0.0, delay)
        try:
            retry_at = parsedate_to_datetime(header_value)
            return max(0.0, (retry_at.timestamp() - time.time()))
        except Exception:
            pass

    message_match = re.search(r"try again in ([0-9]+(?:\.[0-9]+)?)s", body_text, re.IGNORECASE)
    if message_match:
        return max(0.0, float(message_match.group(1)))
    return None


def _parse_rate_limit_info(headers: object, body_text: str = "") -> dict[str, float | int | None]:
    header_map = _header_dict(headers)
    limit_tokens = _as_int(
        _header_value(
            header_map,
            "x-ratelimit-limit-tokens",
            "ratelimit-limit-tokens",
            "x-ratelimit-limit-token",
        )
    )
    remaining_tokens = _as_int(
        _header_value(
            header_map,
            "x-ratelimit-remaining-tokens",
            "ratelimit-remaining-tokens",
            "x-ratelimit-remaining-token",
        )
    )
    reset_tokens_seconds = _parse_duration_seconds(
        _header_value(
            header_map,
            "x-ratelimit-reset-tokens",
            "ratelimit-reset-tokens",
            "x-ratelimit-reset-token",
        )
    )
    limit_requests = _as_int(
        _header_value(
            header_map,
            "x-ratelimit-limit-requests",
            "ratelimit-limit-requests",
        )
    )
    remaining_requests = _as_int(
        _header_value(
            header_map,
            "x-ratelimit-remaining-requests",
            "ratelimit-remaining-requests",
        )
    )
    reset_requests_seconds = _parse_duration_seconds(
        _header_value(
            header_map,
            "x-ratelimit-reset-requests",
            "ratelimit-reset-requests",
        )
    )
    retry_after_seconds = _parse_retry_after_seconds(header_map, body_text)
    return {
        "retry_after_seconds": retry_after_seconds,
        "limit_tokens": limit_tokens,
        "remaining_tokens": remaining_tokens,
        "reset_tokens_seconds": reset_tokens_seconds,
        "limit_requests": limit_requests,
        "remaining_requests": remaining_requests,
        "reset_requests_seconds": reset_requests_seconds,
    }


def _extract_usage_tokens(response: Any) -> int | None:
    usage = getattr(response, "usage", None)
    if usage is None:
        inner = getattr(response, "_response", None)
        if inner is not None:
            usage = getattr(inner, "usage", None)
    if usage is None and isinstance(response, dict):
        usage = response.get("usage")
    if usage is None:
        return None

    prompt_tokens = _as_int(getattr(usage, "prompt_tokens", None))
    if prompt_tokens is None and isinstance(usage, dict):
        prompt_tokens = _as_int(usage.get("prompt_tokens"))
    completion_tokens = _as_int(getattr(usage, "completion_tokens", None))
    if completion_tokens is None and isinstance(usage, dict):
        completion_tokens = _as_int(usage.get("completion_tokens"))
    if prompt_tokens is None and completion_tokens is None:
        return None
    return int((prompt_tokens or 0) + (completion_tokens or 0))


def _build_response_object(response_json: dict[str, Any], *, headers: object, status_code: int, retry_count: int, pacing_delay_seconds: float) -> SimpleNamespace:
    choices: list[SimpleNamespace] = []
    for choice in response_json.get("choices", []) or []:
        message = choice.get("message", {}) if isinstance(choice, dict) else {}
        content = ""
        if isinstance(message, dict):
            content = str(message.get("content", "") or "")
        finish_reason = ""
        if isinstance(choice, dict):
            finish_reason = str(choice.get("finish_reason", "") or "")
        choices.append(
            SimpleNamespace(
                message=SimpleNamespace(content=content),
                finish_reason=finish_reason,
            )
        )

    usage = response_json.get("usage", {}) if isinstance(response_json, dict) else {}
    usage_ns = SimpleNamespace(
        prompt_tokens=getattr(usage, "prompt_tokens", None) if not isinstance(usage, dict) else usage.get("prompt_tokens"),
        completion_tokens=getattr(usage, "completion_tokens", None) if not isinstance(usage, dict) else usage.get("completion_tokens"),
        total_tokens=getattr(usage, "total_tokens", None) if not isinstance(usage, dict) else usage.get("total_tokens"),
        thoughts_token_count=getattr(usage, "thoughts_token_count", None) if not isinstance(usage, dict) else usage.get("thoughts_token_count"),
        completion_tokens_details=SimpleNamespace(
            reasoning_tokens=(
                getattr(getattr(usage, "completion_tokens_details", None), "reasoning_tokens", None)
                if not isinstance(usage, dict)
                else (usage.get("completion_tokens_details", {}) or {}).get("reasoning_tokens")
            ),
            visible_tokens=(
                getattr(getattr(usage, "completion_tokens_details", None), "visible_tokens", None)
                if not isinstance(usage, dict)
                else (usage.get("completion_tokens_details", {}) or {}).get("visible_tokens")
            ),
        ),
    )
    response = SimpleNamespace(
        id=response_json.get("id", ""),
        object=response_json.get("object", "chat.completion"),
        created=response_json.get("created", 0),
        model=response_json.get("model", ""),
        choices=choices,
        usage=usage_ns,
        status_code=status_code,
        headers=_header_dict(headers),
        retry_count=retry_count,
        request_pacing_delay_seconds=pacing_delay_seconds,
        rate_limit_info=_parse_rate_limit_info(headers, ""),
    )
    return response


@dataclass
class ProviderReliabilityState:
    tokens_per_minute_limit: int = DEFAULT_TOKENS_PER_MINUTE_LIMIT
    request_tokens_estimate: float = float(DEFAULT_ESTIMATED_REQUEST_TOKENS)
    requests_per_minute_limit: int = DEFAULT_REQUESTS_PER_MINUTE_LIMIT
    safety_margin: float = DEFAULT_SAFETY_MARGIN
    window_seconds: float = DEFAULT_WINDOW_SECONDS
    retry_jitter_fraction: float = 0.15
    max_backoff_seconds: float = 8.0
    observed_request_tokens: list[int] = field(default_factory=list)
    rolling_window: deque[dict[str, Any]] = field(default_factory=deque)
    last_provider_limit_tokens: int | None = None
    last_provider_remaining_tokens: int | None = None
    last_provider_reset_tokens_seconds: float | None = None
    last_provider_limit_requests: int | None = None
    last_provider_remaining_requests: int | None = None
    last_provider_reset_requests_seconds: float | None = None
    last_retry_after_seconds: float | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def _bounded_jitter(self, delay_seconds: float) -> float:
        if delay_seconds <= 0:
            return 0.0
        jitter = random.uniform(0.0, delay_seconds * self.retry_jitter_fraction)
        return delay_seconds + jitter

    def _safe_tpm_budget(self) -> float:
        return max(1.0, float(self.tokens_per_minute_limit) * float(self.safety_margin))

    def _update_limits_from_headers(self, headers: object) -> None:
        header_map = _header_dict(headers)
        self.last_provider_limit_tokens = _as_int(_header_value(header_map, "x-ratelimit-limit-tokens", "ratelimit-limit-tokens"))
        self.last_provider_remaining_tokens = _as_int(_header_value(header_map, "x-ratelimit-remaining-tokens", "ratelimit-remaining-tokens"))
        self.last_provider_reset_tokens_seconds = _parse_duration_seconds(_header_value(header_map, "x-ratelimit-reset-tokens", "ratelimit-reset-tokens", "x-ratelimit-reset-token"))
        self.last_provider_limit_requests = _as_int(_header_value(header_map, "x-ratelimit-limit-requests", "ratelimit-limit-requests"))
        self.last_provider_remaining_requests = _as_int(_header_value(header_map, "x-ratelimit-remaining-requests", "ratelimit-remaining-requests"))
        self.last_provider_reset_requests_seconds = _parse_duration_seconds(_header_value(header_map, "x-ratelimit-reset-requests", "ratelimit-reset-requests"))

    def _entry_tokens(self, entry: dict[str, Any]) -> float:
        actual = entry.get("actual_tokens")
        if actual is not None:
            return float(actual)
        return float(entry.get("estimated_tokens", 0.0))

    def _entry_time(self, entry: dict[str, Any]) -> float:
        committed_at = entry.get("committed_at")
        if committed_at is not None:
            return float(committed_at)
        return float(entry.get("started_at", 0.0))

    def _entry_expires_at(self, entry: dict[str, Any]) -> float:
        return self._entry_time(entry) + float(self.window_seconds)

    def _prune_window_locked(self, now: float) -> None:
        cutoff = now - float(self.window_seconds)
        kept: deque[dict[str, Any]] = deque()
        for entry in self.rolling_window:
            if self._entry_expires_at(entry) > cutoff:
                kept.append(entry)
        self.rolling_window = kept

    def _rolling_snapshot_locked(self, now: float) -> dict[str, Any]:
        self._prune_window_locked(now)
        active = list(self.rolling_window)
        used_tokens = sum(self._entry_tokens(entry) for entry in active)
        request_count = len(active)
        return {"used_tokens": used_tokens, "request_count": request_count, "active_entries": active}

    def _wait_for_token_budget_locked(self, now: float, estimated_tokens: float, active_entries: list[dict[str, Any]]) -> float:
        safe_budget = self._safe_tpm_budget()
        projected = sum(self._entry_tokens(entry) for entry in active_entries) + float(estimated_tokens)
        if projected <= safe_budget:
            return 0.0
        excess = projected - safe_budget
        expiring = sorted(((self._entry_expires_at(entry), self._entry_tokens(entry)) for entry in active_entries), key=lambda item: item[0])
        recovered = 0.0
        for expires_at, tokens in expiring:
            recovered += tokens
            if recovered >= excess:
                return max(0.0, expires_at - now)
        return float(self.window_seconds)

    def _wait_for_request_budget_locked(self, now: float, active_entries: list[dict[str, Any]]) -> float:
        limit = int(self.requests_per_minute_limit or 0)
        if limit <= 0 or len(active_entries) < limit:
            return 0.0
        expiring = sorted(self._entry_expires_at(entry) for entry in active_entries)
        index = len(active_entries) - limit + 1
        if index <= 0:
            return 0.0
        return max(0.0, expiring[index - 1] - now)

    def acquire_request_slot(
        self,
        *,
        now: float,
        sleep_fn: Callable[[float], None],
        estimated_tokens: float | None = None,
        request_id: str = "",
        trace: bool = False,
    ) -> tuple[float, dict[str, Any], dict[str, Any] | None]:
        request_estimate = float(estimated_tokens if estimated_tokens is not None else self.request_tokens_estimate)
        with self._lock:
            snapshot_before = self._rolling_snapshot_locked(now)
            token_wait = self._wait_for_token_budget_locked(now, request_estimate, snapshot_before["active_entries"])
            request_wait = self._wait_for_request_budget_locked(now, snapshot_before["active_entries"])
            chosen_sleep = max(token_wait, request_wait)
            reservation = {
                "request_id": request_id,
                "started_at": now + chosen_sleep,
                "estimated_tokens": request_estimate,
                "actual_tokens": None,
                "committed_at": None,
            }
            self.rolling_window.append(reservation)
            snapshot_after = self._rolling_snapshot_locked(now + chosen_sleep)
            self.last_retry_after_seconds = None
        if chosen_sleep > 0:
            sleep_fn(chosen_sleep)
        trace_payload = None
        if trace:
            trace_payload = {
                "monotonic_now": now,
                "TPM_limit": self.tokens_per_minute_limit,
                "provider_remaining_tokens": self.last_provider_remaining_tokens,
                "local_estimated_used_tokens": snapshot_before["used_tokens"],
                "local_available_tokens": max(0.0, self._safe_tpm_budget() - snapshot_before["used_tokens"]),
                "estimated_request_tokens": request_estimate,
                "RPM_limit": self.requests_per_minute_limit,
                "recent_request_count": snapshot_before["request_count"],
                "calculated_token_wait": token_wait,
                "calculated_request_wait": request_wait,
                "chosen_sleep": chosen_sleep,
                "state_before_sleep": {
                    "active_request_count": snapshot_before["request_count"],
                    "active_token_usage": snapshot_before["used_tokens"],
                },
                "state_after_sleep": {
                    "active_request_count": snapshot_after["request_count"],
                    "active_token_usage": snapshot_after["used_tokens"],
                },
            }
        return chosen_sleep, reservation, trace_payload

    def finalize_request(
        self,
        reservation: dict[str, Any],
        *,
        finished_at: float,
        actual_tokens: float | None = None,
        headers: object = None,
        retry_after_seconds: float | None = None,
    ) -> None:
        with self._lock:
            reservation["committed_at"] = finished_at
            reservation["actual_tokens"] = float(actual_tokens if actual_tokens is not None else reservation["estimated_tokens"])
            self.request_tokens_estimate = max(self.request_tokens_estimate, float(reservation["actual_tokens"]))
            if headers is not None:
                self._update_limits_from_headers(headers)
            if retry_after_seconds is not None:
                self.last_retry_after_seconds = float(retry_after_seconds)
            self._prune_window_locked(finished_at)

    def wait_before_attempt(self, now: float, sleep_fn: Callable[[float], None]) -> float:
        delay, _, _ = self.acquire_request_slot(now=now, sleep_fn=sleep_fn, estimated_tokens=self.request_tokens_estimate)
        return delay

    def schedule_success(self, *, now: float, response: object) -> float:
        headers = getattr(response, "headers", None)
        with self._lock:
            self._update_limits_from_headers(headers)
            observed_tokens = _extract_usage_tokens(response)
            if observed_tokens is not None:
                self.observed_request_tokens.append(observed_tokens)
                self.request_tokens_estimate = max(self.request_tokens_estimate, float(observed_tokens))
        return 0.0

    def schedule_retry(
        self,
        *,
        now: float,
        retry_after_seconds: float | None,
        backoff_seconds: float,
        headers: object = None,
        enforce_budget: bool = False,
    ) -> float:
        with self._lock:
            self._update_limits_from_headers(headers)
            base_delay = backoff_seconds
            if retry_after_seconds is not None:
                base_delay = max(retry_after_seconds, base_delay)
            delay = self._bounded_jitter(base_delay)
            self.last_retry_after_seconds = retry_after_seconds
        return delay


class GroqHTTPError(RuntimeError):
    def __init__(
        self,
        *,
        status_code: int | None,
        message: str,
        headers: object = None,
        body_text: str = "",
        retry_count: int = 0,
        rate_limit_info: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.headers = _header_dict(headers)
        self.body_text = body_text
        self.retry_count = retry_count
        self.rate_limit_info = rate_limit_info or {}
        self.retry_after_seconds = self.rate_limit_info.get("retry_after_seconds")
        self.rate_limit_limit_tokens = self.rate_limit_info.get("limit_tokens")
        self.rate_limit_remaining_tokens = self.rate_limit_info.get("remaining_tokens")
        self.rate_limit_reset_tokens_seconds = self.rate_limit_info.get("reset_tokens_seconds")
        self.rate_limit_limit_requests = self.rate_limit_info.get("limit_requests")
        self.rate_limit_remaining_requests = self.rate_limit_info.get("remaining_requests")
        self.rate_limit_reset_requests_seconds = self.rate_limit_info.get("reset_requests_seconds")
        self.request_id = ""
        self.request_simulation_step = None
        self.http_attempt_id = None
        self.prompt_hash = ""
        self.request_started_at = ""
        self.request_finished_at = ""


def _attach_request_metadata(target: object, metadata: dict[str, Any]) -> None:
    for key, value in metadata.items():
        try:
            setattr(target, key, value)
        except Exception:
            pass


class _ChatCompletionsAPI:
    def __init__(self, client: "GroqCompatClient") -> None:
        self._client = client

    def create(self, **kwargs: object) -> SimpleNamespace:
        return self._client._create_chat_completion(**kwargs)


class _ChatAPI:
    def __init__(self, client: "GroqCompatClient") -> None:
        self.completions = _ChatCompletionsAPI(client)


class GroqCompatClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        state: ProviderReliabilityState | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        monotonic_fn: Callable[[], float] = time.monotonic,
        opener: Callable[[urllib.request.Request, float], Any] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.state = state or get_shared_provider_reliability_state(self.base_url)
        self._sleep = sleep_fn
        self._monotonic = monotonic_fn
        self._opener = opener or urllib.request.urlopen
        self.chat = _ChatAPI(self)

    def _should_retry(self, error: Exception) -> tuple[bool, str]:
        status = getattr(error, "status_code", None)
        if isinstance(status, int):
            if status == 429:
                return True, "RATE_LIMIT"
            if status in {408}:
                return True, "TIMEOUT"
            if 500 <= status < 600:
                return True, "SERVER_ERROR"
            if status in {401, 403, 404, 422, 400}:
                return False, "PERMANENT_CLIENT_ERROR"
        message = str(error).lower()
        name = type(error).__name__.lower()
        if "ratelimit" in name or "rate limit" in message:
            return True, "RATE_LIMIT"
        if "timeout" in name or "timed out" in message:
            return True, "TIMEOUT"
        if "connection" in name or "connect" in message or "network" in message or "dns" in message:
            return True, "NETWORK_ERROR"
        return False, "UNKNOWN_ERROR"

    def _backoff_seconds(self, attempt_index: int) -> float:
        return min(self.state.max_backoff_seconds, float(2 ** max(0, attempt_index - 1)))

    def _send_request(self, payload: dict[str, Any]) -> tuple[dict[str, Any], object, int]:
        url = f"{self.base_url}/chat/completions"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        response = self._opener(request, timeout=self.timeout)
        status_code = int(getattr(response, "status", getattr(response, "code", 200)) or 200)
        headers = getattr(response, "headers", None)
        raw = response.read()
        text = raw.decode("utf-8", errors="replace")
        payload_json = json.loads(text)
        return payload_json, headers, status_code

    def _exception_from_http_error(self, error: urllib.error.HTTPError, attempt_count: int) -> GroqHTTPError:
        body_text = ""
        try:
            body_text = error.read().decode("utf-8", errors="replace")
        except Exception:
            body_text = ""
        headers = getattr(error, "headers", None)
        rate_limit_info = _parse_rate_limit_info(headers, body_text)
        message = body_text or f"HTTP {error.code}"
        return GroqHTTPError(
            status_code=int(error.code) if getattr(error, "code", None) is not None else None,
            message=message,
            headers=headers,
            body_text=body_text,
            retry_count=max(0, attempt_count - 1),
            rate_limit_info=rate_limit_info,
        )

    def _exception_from_generic(self, error: Exception, attempt_count: int) -> GroqHTTPError:
        message = str(error)
        rate_limit_info = _parse_rate_limit_info({}, message)
        return GroqHTTPError(
            status_code=None,
            message=message or type(error).__name__,
            headers={},
            body_text=message,
            retry_count=max(0, attempt_count - 1),
            rate_limit_info=rate_limit_info,
        )

    def _create_chat_completion(self, *, model: str, messages: list[dict[str, Any]], **kwargs: object) -> SimpleNamespace:
        request_context = _normalize_request_context(kwargs.pop("_request_context", {}))
        request_id = str(request_context.get("request_id") or uuid.uuid4().hex)
        request_simulation_step = request_context.get("request_simulation_step")
        prompt_hash = str(request_context.get("prompt_hash") or _hash_prompt_messages(messages))
        payload: dict[str, Any] = {"model": model, "messages": messages}
        payload.update(kwargs)
        attempt_count = 0
        retry_delays: list[float] = []
        last_error: GroqHTTPError | None = None
        request_started_at = ""
        reservation: dict[str, Any] | None = None

        while True:
            now = self._monotonic()
            if reservation is None:
                pre_delay, reservation, _ = self.state.acquire_request_slot(
                    now=now,
                    sleep_fn=self._sleep,
                    estimated_tokens=self.state.request_tokens_estimate,
                    request_id=request_id,
                    trace=False,
                )
            else:
                pre_delay = 0.0
            if not request_started_at:
                request_started_at = _utc_now_iso()
            attempt_count += 1
            http_attempt_id = attempt_count
            try:
                request_started = self._monotonic()
                response_json, headers, status_code = self._send_request(payload)
                actual_tokens = _extract_usage_tokens(response_json)
                self.state.finalize_request(
                    reservation,
                    finished_at=self._monotonic(),
                    actual_tokens=actual_tokens,
                    headers=headers,
                )
                response = _build_response_object(
                    response_json,
                    headers=headers,
                    status_code=status_code,
                    retry_count=max(0, attempt_count - 1),
                    pacing_delay_seconds=0.0,
                )
                _attach_request_metadata(
                    response,
                    {
                        "request_id": request_id,
                        "request_simulation_step": request_simulation_step,
                        "http_attempt_id": http_attempt_id,
                        "prompt_hash": prompt_hash,
                        "request_started_at": request_started_at,
                        "request_finished_at": _utc_now_iso(),
                    },
                )
                response.request_attempt_count = attempt_count
                response.request_latency_ms = round((self._monotonic() - request_started) * 1000, 2)
                response.request_pacing_delay_ms = round(pre_delay * 1000, 2)
                response.retry_delays_seconds = tuple(retry_delays)
                return response
            except Exception as error:  # pragma: no cover - live provider failures are environment dependent
                retryable_error_types = tuple(candidate for candidate in (RateLimitError, APITimeoutError, APIConnectionError, APIStatusError) if isinstance(candidate, type))
                if retryable_error_types and isinstance(error, retryable_error_types):
                    last_error = self._exception_from_sdk_error(error, attempt_count)
                elif isinstance(error, urllib.error.HTTPError):
                    last_error = self._exception_from_http_error(error, attempt_count)
                else:
                    last_error = self._exception_from_generic(error, attempt_count)

            assert last_error is not None
            self.state.finalize_request(
                reservation,
                finished_at=self._monotonic(),
                actual_tokens=self.state.request_tokens_estimate,
                headers=getattr(last_error, 'headers', None),
                retry_after_seconds=getattr(last_error, 'retry_after_seconds', None),
            )
            should_retry, _ = self._should_retry(last_error)
            if not should_retry or attempt_count > self.max_retries:
                _attach_request_metadata(
                    last_error,
                    {
                        "request_id": request_id,
                        "request_simulation_step": request_simulation_step,
                        "http_attempt_id": http_attempt_id,
                        "prompt_hash": prompt_hash,
                        "request_started_at": request_started_at,
                        "request_finished_at": _utc_now_iso(),
                    },
                )
                last_error.request_attempt_count = attempt_count
                last_error.retry_delays_seconds = tuple(retry_delays)
                last_error.request_pacing_delay_ms = round(pre_delay * 1000, 2)
                last_error.request_latency_ms = round((self._monotonic() - request_started) * 1000, 2)
                raise last_error

            backoff = self._backoff_seconds(attempt_count)
            retry_after_seconds = getattr(last_error, 'retry_after_seconds', None)
            delay = self.state.schedule_retry(
                now=self._monotonic(),
                retry_after_seconds=retry_after_seconds,
                backoff_seconds=backoff,
                headers=getattr(last_error, 'headers', None),
                enforce_budget=False,
            )
            retry_delays.append(delay)
            self._sleep(delay)


def create_live_client(


    *,
    base_url: str,
    api_key: str,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_MAX_RETRIES,
    state: ProviderReliabilityState | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    monotonic_fn: Callable[[], float] = time.monotonic,
    opener: Callable[[urllib.request.Request, float], Any] | None = None,
) -> GroqCompatClient:
    return GroqCompatClient(
        base_url=base_url,
        api_key=api_key,
        timeout=timeout,
        max_retries=max_retries,
        state=state,
        sleep_fn=sleep_fn,
        monotonic_fn=monotonic_fn,
        opener=opener,
    )

