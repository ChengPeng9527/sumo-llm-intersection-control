from __future__ import annotations

import time
import uuid
from types import SimpleNamespace
from typing import Any, Callable

try:  # pragma: no cover - the bundled runtime may not ship with openai
    from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError
except Exception:  # pragma: no cover - fallback path for minimal runtimes
    APIConnectionError = APIStatusError = APITimeoutError = RateLimitError = None
    OpenAI = None

from src.llm.live_provider_client import (
    GroqHTTPError,
    ProviderReliabilityState,
    _attach_request_metadata,
    _build_response_object,
    _extract_usage_tokens,
    _hash_prompt_messages,
    _header_dict,
    _normalize_request_context,
    _parse_rate_limit_info,
    _utc_now_iso,
    get_shared_provider_reliability_state,
)


def _sdk_usage_to_dict(usage: Any) -> dict[str, Any]:
    if usage is None:
        return {}
    if isinstance(usage, dict):
        return dict(usage)
    payload: dict[str, Any] = {}
    for key in (
        'prompt_tokens',
        'completion_tokens',
        'total_tokens',
        'queue_time',
        'prompt_time',
        'completion_time',
        'total_time',
    ):
        value = getattr(usage, key, None)
        if value is not None:
            payload[key] = value
    completion_details = getattr(usage, 'completion_tokens_details', None)
    if completion_details is not None:
        payload['completion_tokens_details'] = {
            'reasoning_tokens': getattr(completion_details, 'reasoning_tokens', None),
            'accepted_prediction_tokens': getattr(completion_details, 'accepted_prediction_tokens', None),
            'rejected_prediction_tokens': getattr(completion_details, 'rejected_prediction_tokens', None),
            'audio_tokens': getattr(completion_details, 'audio_tokens', None),
            'visible_tokens': getattr(completion_details, 'visible_tokens', None),
        }
    return payload


def _sdk_response_to_json(response: Any) -> dict[str, Any]:
    if response is None:
        return {}
    model_dump = getattr(response, 'model_dump', None)
    if callable(model_dump):
        try:
            dumped = model_dump()
            if isinstance(dumped, dict):
                return dumped
        except Exception:
            pass
    choices: list[dict[str, Any]] = []
    for choice in getattr(response, 'choices', []) or []:
        message = getattr(choice, 'message', None)
        content = getattr(message, 'content', '') if message is not None else ''
        choices.append({
            'message': {'content': content},
            'finish_reason': getattr(choice, 'finish_reason', ''),
        })
    return {
        'id': getattr(response, 'id', ''),
        'object': getattr(response, 'object', 'chat.completion'),
        'created': getattr(response, 'created', 0),
        'model': getattr(response, 'model', ''),
        'choices': choices,
        'usage': _sdk_usage_to_dict(getattr(response, 'usage', None)),
    }


def _sdk_error_headers(error: Exception) -> dict[str, str]:
    response = getattr(error, 'response', None)
    if response is not None:
        return _header_dict(getattr(response, 'headers', None))
    return _header_dict(getattr(error, 'headers', None))


class _ChatCompletionsAPI:
    def __init__(self, client: 'GroqSDKClient') -> None:
        self._client = client

    def create(self, **kwargs: object) -> SimpleNamespace:
        return self._client._create_chat_completion(**kwargs)


class _ChatAPI:
    def __init__(self, client: 'GroqSDKClient') -> None:
        self.completions = _ChatCompletionsAPI(client)


class GroqSDKClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        max_retries: int = 4,
        state: ProviderReliabilityState | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        monotonic_fn: Callable[[], float] = time.monotonic,
    ) -> None:
        if OpenAI is None:  # pragma: no cover - guarded by request_config
            raise RuntimeError('OPENAI_SDK_NOT_AVAILABLE')
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.state = state or get_shared_provider_reliability_state(self.base_url)
        self._sleep = sleep_fn
        self._monotonic = monotonic_fn
        self._sdk_client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout, max_retries=0)
        self.chat = _ChatAPI(self)

    def _should_retry(self, error: Exception) -> tuple[bool, str]:
        status = getattr(error, 'status_code', None)
        if isinstance(status, int):
            if status == 429:
                return True, 'RATE_LIMIT'
            if status in {408}:
                return True, 'TIMEOUT'
            if 500 <= status < 600:
                return True, 'SERVER_ERROR'
            if status in {401, 403, 404, 422, 400}:
                return False, 'PERMANENT_CLIENT_ERROR'
        if RateLimitError is not None and isinstance(error, RateLimitError):
            return True, 'RATE_LIMIT'
        if APITimeoutError is not None and isinstance(error, APITimeoutError):
            return True, 'TIMEOUT'
        if APIConnectionError is not None and isinstance(error, APIConnectionError):
            return True, 'NETWORK_ERROR'
        if APIStatusError is not None and isinstance(error, APIStatusError):
            status = getattr(error, 'status_code', None)
            if isinstance(status, int):
                if status == 429:
                    return True, 'RATE_LIMIT'
                if 500 <= status < 600:
                    return True, 'SERVER_ERROR'
                if status in {408}:
                    return True, 'TIMEOUT'
                if status in {401, 403, 404, 422, 400}:
                    return False, 'PERMANENT_CLIENT_ERROR'
        message = str(error).lower()
        name = type(error).__name__.lower()
        if 'ratelimit' in name or 'rate limit' in message:
            return True, 'RATE_LIMIT'
        if 'timeout' in name or 'timed out' in message:
            return True, 'TIMEOUT'
        if 'connection' in name or 'connect' in message or 'network' in message or 'dns' in message:
            return True, 'NETWORK_ERROR'
        return False, 'UNKNOWN_ERROR'

    def _backoff_seconds(self, attempt_index: int) -> float:
        return min(self.state.max_backoff_seconds, float(2 ** max(0, attempt_index - 1)))

    def _send_request(self, payload: dict[str, Any]) -> tuple[dict[str, Any], object, int]:
        raw_response = self._sdk_client.chat.completions.with_raw_response.create(**payload)
        parsed_response = raw_response.parse()
        headers = getattr(raw_response, "headers", None)
        http_response = getattr(raw_response, "http_response", None)
        status_code = int(getattr(http_response, "status_code", getattr(http_response, "status", 200)) or 200)
        return _sdk_response_to_json(parsed_response), _header_dict(headers), status_code

    def _exception_from_sdk_error(self, error: Exception, attempt_count: int) -> GroqHTTPError:
        headers = _sdk_error_headers(error)
        body_text = str(error)
        status_code = getattr(error, 'status_code', None)
        try:
            if isinstance(status_code, int):
                status_code = int(status_code)
        except Exception:
            status_code = None
        rate_limit_info = _parse_rate_limit_info(headers, body_text)
        return GroqHTTPError(
            status_code=status_code if isinstance(status_code, int) else None,
            message=body_text or type(error).__name__,
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
        payload: dict[str, Any] = {'model': model, 'messages': messages}
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
                actual_tokens = _extract_usage_tokens(SimpleNamespace(usage=response_json.get('usage')))
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
    timeout: float = 30.0,
    max_retries: int = 4,
    state: ProviderReliabilityState | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    monotonic_fn: Callable[[], float] = time.monotonic,
) -> GroqSDKClient:
    return GroqSDKClient(
        base_url=base_url,
        api_key=api_key,
        timeout=timeout,
        max_retries=max_retries,
        state=state,
        sleep_fn=sleep_fn,
        monotonic_fn=monotonic_fn,
    )
