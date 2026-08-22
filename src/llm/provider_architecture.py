from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, Callable, Protocol

from src.llm.diagnostics import extract_usage_metadata
from src.llm.live_provider_client import (
    GroqCompatClient,
    GroqHTTPError,
    _attach_request_metadata,
    _header_dict,
    _normalize_request_context,
    _parse_rate_limit_info,
    _utc_now_iso,
    get_shared_provider_reliability_state,
)


def _normalized_name(value: object, default: str = "") -> str:
    text = str(value or default).strip()
    return text


def _provider_key(provider_name: str, model_name: str = "", base_url: str = "") -> str:
    return ":".join(part for part in (provider_name.strip().lower(), base_url.strip().lower(), model_name.strip().lower()) if part)


def _extract_first_choice_content(response: Any) -> str:
    if response is None:
        return ""
    if isinstance(response, str):
        return response
    choices = getattr(response, "choices", None)
    if choices:
        first_choice = choices[0]
        message = getattr(first_choice, "message", None)
        content = getattr(message, "content", None)
        if content is None:
            return ""
        return str(content)
    content = getattr(response, "content", None)
    if content is None:
        return ""
    return str(content)


def _usage_namespace(
    prompt_tokens: int | None,
    completion_tokens: int | None,
    total_tokens: int | None,
    thoughts_token_count: int | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        thoughts_token_count=thoughts_token_count,
        completion_tokens_details=SimpleNamespace(
            reasoning_tokens=thoughts_token_count,
            accepted_prediction_tokens=None,
            rejected_prediction_tokens=None,
            audio_tokens=None,
            visible_tokens=completion_tokens,
        ),
    )


def _to_int(value: object) -> int | None:
    try:
        if value is None:
            return None
        return int(float(value))
    except Exception:
        return None


def _coerce_text_message(message: object) -> str:
    if message is None:
        return ""
    if isinstance(message, str):
        return message
    return str(message)


def _request_context_value(request_context: dict[str, Any], key: str, default: Any = None) -> Any:
    value = request_context.get(key, default)
    return default if value is None else value


def _provider_chain_tuple(value: object, fallback: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        chain = tuple(_normalized_name(item) for item in value if _normalized_name(item))
        return chain or fallback
    if isinstance(value, str):
        parts = tuple(part.strip() for part in value.split(",") if part.strip())
        return parts or fallback
    return fallback


def _response_to_provider_response(
    response: Any,
    *,
    provider_name: str,
    model_name: str,
    requested_provider: str,
    requested_model: str,
    provider_chain: tuple[str, ...],
    provider_switch_count: int,
    request_context: dict[str, Any],
) -> "ProviderResponse":
    usage = getattr(response, "usage", None)
    usage_meta = extract_usage_metadata(response)
    choices = list(getattr(response, "choices", []) or [])
    response_object_type = type(response).__name__
    parsed_content = _extract_first_choice_content(response)
    provider_response = ProviderResponse(
        provider_name=provider_name,
        model_name=model_name,
        request_id=_normalized_name(getattr(response, "request_id", "")),
        http_attempt_id=_to_int(getattr(response, "http_attempt_id", None)),
        success=True,
        status_code=_to_int(getattr(response, "status_code", None)),
        raw_response=response,
        parsed_content=parsed_content,
        latency_ms=float(getattr(response, "request_latency_ms", 0.0) or 0.0),
        prompt_tokens=_to_int(usage_meta.get("prompt_tokens")),
        completion_tokens=_to_int(usage_meta.get("completion_tokens")),
        total_tokens=_to_int(usage_meta.get("total_tokens")),
        error_type="",
        error_message="",
        requested_provider=requested_provider,
        requested_model=requested_model,
        actual_provider=provider_name,
        actual_model=model_name,
        provider_switch_count=provider_switch_count,
        provider_chain=provider_chain,
        provider_failure_reason="",
        provider_success=True,
        choices=choices,
        usage=usage if usage is not None else _usage_namespace(
            _to_int(usage_meta.get("prompt_tokens")),
            _to_int(usage_meta.get("completion_tokens")),
            _to_int(usage_meta.get("total_tokens")),
        ),
        headers=_header_dict(getattr(response, "headers", None)),
        finish_reason=_normalized_name(getattr(getattr(choices[0], "finish_reason", None), "__str__", lambda: "")() if choices else getattr(response, "finish_reason", "")),
        retry_count=_to_int(getattr(response, "retry_count", 0)) or 0,
        request_attempt_count=_to_int(getattr(response, "request_attempt_count", None)),
        request_pacing_delay_ms=getattr(response, "request_pacing_delay_ms", None),
        retry_after_seconds=getattr(response, "retry_after_seconds", None),
        rate_limit_info=dict(getattr(response, "rate_limit_info", {}) or {}),
        request_started_at=_normalized_name(getattr(response, "request_started_at", "")),
        request_finished_at=_normalized_name(getattr(response, "request_finished_at", "")),
        request_simulation_step=_request_context_value(request_context, "request_simulation_step", getattr(response, "request_simulation_step", None)),
        response_object_type=response_object_type,
    )
    _attach_request_metadata(
        provider_response,
        {
            "request_id": provider_response.request_id,
            "request_simulation_step": provider_response.request_simulation_step,
            "http_attempt_id": provider_response.http_attempt_id,
            "prompt_hash": _normalized_name(getattr(response, "prompt_hash", request_context.get("prompt_hash", ""))),
            "request_started_at": provider_response.request_started_at,
            "request_finished_at": provider_response.request_finished_at,
        },
    )
    return provider_response


def _provider_response_from_json(
    payload: dict[str, Any],
    *,
    provider_name: str,
    model_name: str,
    requested_provider: str,
    requested_model: str,
    provider_chain: tuple[str, ...],
    provider_switch_count: int,
    request_context: dict[str, Any],
    status_code: int | None,
    headers: object,
    request_started_at: str,
    request_finished_at: str,
    retry_count: int = 0,
    request_attempt_count: int | None = None,
    request_pacing_delay_ms: float | None = None,
    retry_after_seconds: float | None = None,
) -> "ProviderResponse":
    candidates = payload.get("candidates", []) or []
    first_candidate = candidates[0] if candidates else {}
    content = ""
    finish_reason = ""
    if isinstance(first_candidate, dict):
        finish_reason = _normalized_name(first_candidate.get("finishReason", first_candidate.get("finish_reason", "")))
        content_block = first_candidate.get("content", {}) or {}
        parts = content_block.get("parts", []) if isinstance(content_block, dict) else []
        if parts:
            part_texts = [str(part.get("text", "")) for part in parts if isinstance(part, dict) and part.get("text") is not None]
            content = "".join(part_texts)
    usage = payload.get("usageMetadata", payload.get("usage_metadata", {})) or {}
    prompt_tokens = _to_int(
        usage.get("promptTokenCount")
        if isinstance(usage, dict)
        else getattr(usage, "promptTokenCount", None)
    )
    completion_tokens = _to_int(
        usage.get("candidatesTokenCount")
        if isinstance(usage, dict)
        else getattr(usage, "candidatesTokenCount", None)
    )
    thoughts_token_count = _to_int(
        usage.get("thoughtsTokenCount")
        if isinstance(usage, dict)
        else getattr(usage, "thoughtsTokenCount", None)
    )
    if thoughts_token_count is None:
        thoughts_token_count = _to_int(
            usage.get("thoughts_token_count")
            if isinstance(usage, dict)
            else getattr(usage, "thoughts_token_count", None)
        )
    total_tokens = _to_int(
        usage.get("totalTokenCount")
        if isinstance(usage, dict)
        else getattr(usage, "totalTokenCount", None)
    )
    response = ProviderResponse(
        provider_name=provider_name,
        model_name=model_name,
        request_id=_normalized_name(request_context.get("request_id", "")),
        http_attempt_id=_to_int(request_context.get("http_attempt_id", None)),
        success=True,
        status_code=status_code,
        raw_response=payload,
        parsed_content=content,
        latency_ms=float(request_context.get("latency_ms", 0.0) or 0.0),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        error_type="",
        error_message="",
        requested_provider=requested_provider,
        requested_model=requested_model,
        actual_provider=provider_name,
        actual_model=model_name,
        provider_switch_count=provider_switch_count,
        provider_chain=provider_chain,
        provider_failure_reason="",
        provider_success=True,
        choices=[SimpleNamespace(message=SimpleNamespace(content=content), finish_reason=finish_reason)],
        usage=_usage_namespace(prompt_tokens, completion_tokens, total_tokens, thoughts_token_count),
        headers=_header_dict(headers),
        finish_reason=finish_reason,
        retry_count=retry_count,
        request_attempt_count=request_attempt_count,
        request_pacing_delay_ms=request_pacing_delay_ms,
        retry_after_seconds=retry_after_seconds,
        rate_limit_info=_parse_rate_limit_info(headers, ""),
        request_started_at=request_started_at,
        request_finished_at=request_finished_at,
        request_simulation_step=_request_context_value(request_context, "request_simulation_step", None),
        response_object_type="dict",
    )
    _attach_request_metadata(
        response,
        {
            "request_id": response.request_id,
            "request_simulation_step": response.request_simulation_step,
            "http_attempt_id": response.http_attempt_id,
            "prompt_hash": _normalized_name(request_context.get("prompt_hash", "")),
            "request_started_at": request_started_at,
            "request_finished_at": request_finished_at,
        },
    )
    return response


def _error_reason_from_status(status_code: int | None, message: str) -> str:
    text = (message or "").lower()
    if status_code == 429 or "rate limit" in text or "ratelimit" in text:
        return "RATE_LIMIT"
    if status_code in {408} or "timeout" in text or "timed out" in text:
        return "TIMEOUT"
    if status_code is not None and 500 <= status_code < 600:
        return "SERVER_ERROR"
    if status_code in {400, 401, 403, 404, 422}:
        return "PERMANENT_CLIENT_ERROR"
    if "connection" in text or "network" in text or "dns" in text:
        return "NETWORK_ERROR"
    return "UNKNOWN_ERROR"


def _gemini_response_schema() -> dict[str, Any]:
    decision_value_schema = {
        "type": "string",
        "enum": ["PROCEED", "WAIT", "FREE"],
        "description": "A canonical intersection control decision.",
    }
    return {
        "type": "object",
        "properties": {
            "decisions": {
                "type": "object",
                "description": "Vehicle-id to decision mapping for every vehicle in the traffic state.",
                "additionalProperties": decision_value_schema,
            }
        },
        "required": ["decisions"],
        "additionalProperties": False,
        "propertyOrdering": ["decisions"],
    }


def _gemini_structured_config(*, max_completion_tokens: int | None) -> dict[str, Any]:
    config: dict[str, Any] = {}
    if max_completion_tokens is not None:
        config["maxOutputTokens"] = max_completion_tokens
    config["responseMimeType"] = "application/json"
    config["responseJsonSchema"] = _gemini_response_schema()
    config["thinkingConfig"] = {"thinkingLevel": "minimal"}
    return config


@dataclass
class ProviderResponse:
    provider_name: str
    model_name: str
    request_id: str = ""
    http_attempt_id: int | None = None
    success: bool = False
    status_code: int | None = None
    raw_response: Any = None
    parsed_content: str = ""
    latency_ms: float = 0.0
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    error_type: str = ""
    error_message: str = ""
    requested_provider: str = ""
    requested_model: str = ""
    actual_provider: str = ""
    actual_model: str = ""
    provider_switch_count: int = 0
    provider_chain: tuple[str, ...] = ()
    provider_failure_reason: str = ""
    provider_success: bool = False
    choices: list[Any] = field(default_factory=list)
    usage: Any = None
    headers: dict[str, str] = field(default_factory=dict)
    finish_reason: str = ""
    retry_count: int = 0
    request_attempt_count: int | None = None
    request_pacing_delay_ms: float | None = None
    retry_after_seconds: float | None = None
    rate_limit_info: dict[str, Any] = field(default_factory=dict)
    request_started_at: str = ""
    request_finished_at: str = ""
    request_simulation_step: int | None = None
    response_object_type: str = "ProviderResponse"


class ProviderRequestError(RuntimeError):
    def __init__(
        self,
        *,
        provider_name: str,
        model_name: str,
        message: str,
        status_code: int | None = None,
        headers: object = None,
        body_text: str = "",
        rate_limit_info: dict[str, Any] | None = None,
        requested_provider: str = "",
        requested_model: str = "",
        actual_provider: str = "",
        actual_model: str = "",
        provider_switch_count: int = 0,
        provider_chain: tuple[str, ...] = (),
        provider_failure_reason: str = "",
        request_id: str = "",
        request_simulation_step: int | None = None,
        http_attempt_id: int | None = None,
        prompt_hash: str = "",
        request_started_at: str = "",
        request_finished_at: str = "",
        request_attempt_count: int | None = None,
        request_pacing_delay_ms: float | None = None,
        retry_count: int = 0,
    ) -> None:
        super().__init__(message)
        self.provider_name = provider_name
        self.model_name = model_name
        self.status_code = status_code
        self.headers = _header_dict(headers)
        self.body_text = body_text
        self.rate_limit_info = rate_limit_info or {}
        self.retry_after_seconds = self.rate_limit_info.get("retry_after_seconds")
        self.requested_provider = requested_provider
        self.requested_model = requested_model
        self.actual_provider = actual_provider or provider_name
        self.actual_model = actual_model or model_name
        self.provider_switch_count = provider_switch_count
        self.provider_chain = provider_chain
        self.provider_failure_reason = provider_failure_reason or _error_reason_from_status(status_code, message)
        self.provider_success = False
        self.request_id = request_id
        self.request_simulation_step = request_simulation_step
        self.http_attempt_id = http_attempt_id
        self.prompt_hash = prompt_hash
        self.request_started_at = request_started_at
        self.request_finished_at = request_finished_at
        self.request_attempt_count = request_attempt_count
        self.request_pacing_delay_ms = request_pacing_delay_ms
        self.retry_count = retry_count
        self.error_type = type(self).__name__
        self.error_message = message


class LLMProvider(Protocol):
    provider_name: str
    model_name: str

    def request(self, messages: list[dict[str, Any]], request_config: dict[str, Any], request_context: dict[str, Any]) -> ProviderResponse:
        ...


class _ProviderCompletionsAPI:
    def __init__(self, provider: "LLMProvider") -> None:
        self._provider = provider

    def create(self, **kwargs: object) -> ProviderResponse:
        request_context = _normalize_request_context(kwargs.pop("_request_context", {}))
        messages = list(kwargs.pop("messages", []) or [])
        return self._provider.request(messages, dict(kwargs), request_context)


class _ProviderChatAPI:
    def __init__(self, provider: "LLMProvider") -> None:
        self.completions = _ProviderCompletionsAPI(provider)


class OpenAICompatibleProviderAdapter:
    def __init__(
        self,
        *,
        provider_name: str,
        base_url: str,
        api_key: str,
        model_name: str,
        timeout: float,
        max_retries: int,
        state: Any | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        monotonic_fn: Callable[[], float] = time.monotonic,
        opener: Callable[[urllib.request.Request, float], Any] | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self._sleep = sleep_fn
        self._monotonic = monotonic_fn
        self._opener = opener or urllib.request.urlopen
        self._client = GroqCompatClient(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
            max_retries=self.max_retries,
            state=state or get_shared_provider_reliability_state(_provider_key(self.provider_name, self.model_name, self.base_url)),
            sleep_fn=self._sleep,
            monotonic_fn=self._monotonic,
            opener=self._opener,
        )
        self.state = self._client.state
        self.chat = _ProviderChatAPI(self)

    def request(self, messages: list[dict[str, Any]], request_config: dict[str, Any], request_context: dict[str, Any]) -> ProviderResponse:
        request_context = _normalize_request_context(request_context)
        request_config = dict(request_config or {})
        requested_provider = _normalized_name(request_context.get("requested_provider", self.provider_name))
        requested_model = _normalized_name(request_context.get("requested_model", request_config.get("model", self.model_name)))
        provider_chain = _provider_chain_tuple(request_context.get("provider_chain", (self.provider_name,)), (self.provider_name,))
        provider_switch_count = _to_int(request_context.get("provider_switch_count", 0)) or 0
        actual_model = _normalized_name(request_config.get("model", self.model_name)) or self.model_name
        request_started_at = _utc_now_iso()
        request_config["model"] = actual_model
        try:
            response = self._client.chat.completions.create(
                model=actual_model,
                messages=messages,
                _request_context=dict(request_context, requested_provider=requested_provider, requested_model=requested_model, provider_chain=provider_chain, provider_switch_count=provider_switch_count),
                **{key: value for key, value in request_config.items() if key != "model"},
            )
            provider_response = _response_to_provider_response(
                response,
                provider_name=self.provider_name,
                model_name=actual_model,
                requested_provider=requested_provider,
                requested_model=requested_model,
                provider_chain=provider_chain,
                provider_switch_count=provider_switch_count,
                request_context=dict(request_context, request_started_at=request_started_at),
            )
            provider_response.request_started_at = _normalized_name(getattr(response, "request_started_at", provider_response.request_started_at))
            provider_response.request_finished_at = _normalized_name(getattr(response, "request_finished_at", provider_response.request_finished_at))
            provider_response.request_id = _normalized_name(getattr(response, "request_id", provider_response.request_id))
            provider_response.http_attempt_id = _to_int(getattr(response, "http_attempt_id", provider_response.http_attempt_id))
            provider_response.response_object_type = type(response).__name__
            provider_response.provider_success = True
            provider_response.success = True
            provider_response.provider_failure_reason = ""
            return provider_response
        except Exception as exc:
            if isinstance(exc, GroqHTTPError):
                status_code = _to_int(getattr(exc, "status_code", None))
                failure_reason = _error_reason_from_status(status_code, str(exc))
                raise ProviderRequestError(
                    provider_name=self.provider_name,
                    model_name=actual_model,
                    message=str(exc) or type(exc).__name__,
                    status_code=status_code,
                    headers=getattr(exc, "headers", None),
                    body_text=getattr(exc, "body_text", str(exc)),
                    rate_limit_info=getattr(exc, "rate_limit_info", None),
                    requested_provider=requested_provider,
                    requested_model=requested_model,
                    actual_provider=self.provider_name,
                    actual_model=actual_model,
                    provider_switch_count=provider_switch_count,
                    provider_chain=provider_chain,
                    provider_failure_reason=failure_reason,
                    request_id=_normalized_name(getattr(exc, "request_id", "")),
                    request_simulation_step=_to_int(getattr(exc, "request_simulation_step", None)),
                    http_attempt_id=_to_int(getattr(exc, "http_attempt_id", None)),
                    prompt_hash=_normalized_name(getattr(exc, "prompt_hash", "")),
                    request_started_at=_normalized_name(getattr(exc, "request_started_at", "")),
                    request_finished_at=_normalized_name(getattr(exc, "request_finished_at", "")),
                    request_attempt_count=_to_int(getattr(exc, "request_attempt_count", None)),
                    request_pacing_delay_ms=getattr(exc, "request_pacing_delay_ms", None),
                    retry_count=_to_int(getattr(exc, "retry_count", 0)) or 0,
                ) from exc
            raise ProviderRequestError(
                provider_name=self.provider_name,
                model_name=actual_model,
                message=str(exc) or type(exc).__name__,
                status_code=None,
                headers={},
                body_text=str(exc),
                rate_limit_info={},
                requested_provider=requested_provider,
                requested_model=requested_model,
                actual_provider=self.provider_name,
                actual_model=actual_model,
                provider_switch_count=provider_switch_count,
                provider_chain=provider_chain,
                provider_failure_reason=_error_reason_from_status(None, str(exc)),
            ) from exc


class GroqProviderAdapter(OpenAICompatibleProviderAdapter):
    def __init__(
        self,
        *,
        api_key: str,
        model_name: str,
        timeout: float,
        max_retries: int,
        state: Any | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        monotonic_fn: Callable[[], float] = time.monotonic,
        opener: Callable[[urllib.request.Request, float], Any] | None = None,
        base_url: str = "https://api.groq.com/openai/v1",
    ) -> None:
        super().__init__(
            provider_name="Groq",
            base_url=base_url,
            api_key=api_key,
            model_name=model_name,
            timeout=timeout,
            max_retries=max_retries,
            state=state,
            sleep_fn=sleep_fn,
            monotonic_fn=monotonic_fn,
            opener=opener,
        )


class OpenRouterProviderAdapter(OpenAICompatibleProviderAdapter):
    def __init__(
        self,
        *,
        api_key: str,
        model_name: str,
        timeout: float,
        max_retries: int,
        state: Any | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        monotonic_fn: Callable[[], float] = time.monotonic,
        opener: Callable[[urllib.request.Request, float], Any] | None = None,
        base_url: str = "https://openrouter.ai/api/v1",
    ) -> None:
        super().__init__(
            provider_name="OpenRouter",
            base_url=base_url,
            api_key=api_key,
            model_name=model_name,
            timeout=timeout,
            max_retries=max_retries,
            state=state,
            sleep_fn=sleep_fn,
            monotonic_fn=monotonic_fn,
            opener=opener,
        )


class GeminiProviderAdapter:
    def __init__(
        self,
        *,
        api_key: str,
        model_name: str,
        timeout: float,
        max_retries: int,
        state: Any | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        monotonic_fn: Callable[[], float] = time.monotonic,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        opener: Callable[[urllib.request.Request, float], Any] | None = None,
    ) -> None:
        self.provider_name = "Gemini"
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._sleep = sleep_fn
        self._monotonic = monotonic_fn
        self._opener = opener or urllib.request.urlopen
        self.state = state or get_shared_provider_reliability_state(_provider_key(self.provider_name, self.model_name, self.base_url))
        self.chat = _ProviderChatAPI(self)

    def _gemini_sdk_client(self) -> Any | None:
        try:
            from google import genai  # type: ignore
            from google.genai import types  # type: ignore
        except Exception:
            return None
        try:
            return genai, types
        except Exception:
            return None

    def _build_contents(self, messages: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
        contents: list[dict[str, Any]] = []
        system_messages: list[str] = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            role = _normalized_name(message.get("role", "user")).lower()
            text = _coerce_text_message(message.get("content", ""))
            if not text:
                continue
            if role == "system":
                system_messages.append(text)
                continue
            mapped_role = "model" if role == "assistant" else "user"
            contents.append({"role": mapped_role, "parts": [{"text": text}]})
        return contents, "\n\n".join(system_messages).strip()

    def _request_via_rest(self, messages: list[dict[str, Any]], request_config: dict[str, Any], request_context: dict[str, Any]) -> ProviderResponse:
        requested_provider = _normalized_name(request_context.get("requested_provider", self.provider_name))
        requested_model = _normalized_name(request_context.get("requested_model", request_config.get("model", self.model_name)))
        provider_chain = _provider_chain_tuple(request_context.get("provider_chain", (self.provider_name,)), (self.provider_name,))
        provider_switch_count = _to_int(request_context.get("provider_switch_count", 0)) or 0
        actual_model = _normalized_name(request_config.get("model", self.model_name)) or self.model_name
        contents, system_instruction = self._build_contents(messages)
        generation_config: dict[str, Any] = {}
        max_completion_tokens = _to_int(request_config.get("max_completion_tokens", None))
        response_format = request_config.get("response_format")
        if isinstance(response_format, dict) and _normalized_name(response_format.get("type", "")).lower() == "json_object":
            generation_config = _gemini_structured_config(max_completion_tokens=max_completion_tokens)
        elif max_completion_tokens is not None:
            generation_config["maxOutputTokens"] = max_completion_tokens
        body: dict[str, Any] = {"contents": contents}
        if system_instruction:
            body["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        if generation_config:
            body["generationConfig"] = generation_config
        request_started = self._monotonic()
        request_started_at = _utc_now_iso()
        url = f"{self.base_url}/models/{urllib.parse.quote(actual_model, safe='')}:generateContent"
        request = urllib.request.Request(
            url,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            response = self._opener(request, timeout=self.timeout)
            status_code = _to_int(getattr(response, "status", getattr(response, "code", None)))
            headers = getattr(response, "headers", None)
            raw = response.read()
            payload = json.loads(raw.decode("utf-8", errors="replace"))
            provider_response = _provider_response_from_json(
                payload,
                provider_name=self.provider_name,
                model_name=actual_model,
                requested_provider=requested_provider,
                requested_model=requested_model,
                provider_chain=provider_chain,
                provider_switch_count=provider_switch_count,
                request_context=dict(
                    request_context,
                    request_id=_normalized_name(request_context.get("request_id", "")),
                    request_started_at=request_started_at,
                    latency_ms=round((self._monotonic() - request_started) * 1000, 2),
                ),
                status_code=status_code,
                headers=headers,
                request_started_at=request_started_at,
                request_finished_at=_utc_now_iso(),
            )
            provider_response.request_pacing_delay_ms = None
            provider_response.provider_success = True
            provider_response.success = True
            return provider_response
        except urllib.error.HTTPError as exc:
            body_text = ""
            try:
                body_text = exc.read().decode("utf-8", errors="replace")
            except Exception:
                body_text = str(exc)
            status_code = _to_int(getattr(exc, "code", None))
            raise ProviderRequestError(
                provider_name=self.provider_name,
                model_name=actual_model,
                message=body_text or f"HTTP {status_code or 'ERROR'}",
                status_code=status_code,
                headers=getattr(exc, "headers", None),
                body_text=body_text,
                rate_limit_info=_parse_rate_limit_info(getattr(exc, "headers", None), body_text),
                requested_provider=requested_provider,
                requested_model=requested_model,
                actual_provider=self.provider_name,
                actual_model=actual_model,
                provider_switch_count=provider_switch_count,
                provider_chain=provider_chain,
                provider_failure_reason=_error_reason_from_status(status_code, body_text),
                request_started_at=request_started_at,
                request_finished_at=_utc_now_iso(),
            ) from exc
        except Exception as exc:
            raise ProviderRequestError(
                provider_name=self.provider_name,
                model_name=actual_model,
                message=str(exc) or type(exc).__name__,
                status_code=None,
                headers={},
                body_text=str(exc),
                rate_limit_info={},
                requested_provider=requested_provider,
                requested_model=requested_model,
                actual_provider=self.provider_name,
                actual_model=actual_model,
                provider_switch_count=provider_switch_count,
                provider_chain=provider_chain,
                provider_failure_reason=_error_reason_from_status(None, str(exc)),
                request_started_at=request_started_at,
                request_finished_at=_utc_now_iso(),
            ) from exc

    def request(self, messages: list[dict[str, Any]], request_config: dict[str, Any], request_context: dict[str, Any]) -> ProviderResponse:
        sdk = self._gemini_sdk_client()
        if sdk is not None:
            genai, types = sdk
            requested_provider = _normalized_name(request_context.get("requested_provider", self.provider_name))
            requested_model = _normalized_name(request_context.get("requested_model", request_config.get("model", self.model_name)))
            provider_chain = _provider_chain_tuple(request_context.get("provider_chain", (self.provider_name,)), (self.provider_name,))
            provider_switch_count = _to_int(request_context.get("provider_switch_count", 0)) or 0
            actual_model = _normalized_name(request_config.get("model", self.model_name)) or self.model_name
            contents, system_instruction = self._build_contents(messages)
            client = genai.Client(api_key=self.api_key)
            config_kwargs: dict[str, Any] = {}
            max_completion_tokens = _to_int(request_config.get("max_completion_tokens", None))
            response_format = request_config.get("response_format")
            if isinstance(response_format, dict) and _normalized_name(response_format.get("type", "")).lower() == "json_object":
                if max_completion_tokens is not None:
                    config_kwargs["max_output_tokens"] = max_completion_tokens
                config_kwargs["response_mime_type"] = "application/json"
                config_kwargs["response_json_schema"] = _gemini_response_schema()
                try:
                    config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="minimal")
                except Exception:
                    config_kwargs["thinking_config"] = {"thinking_level": "minimal"}
            elif max_completion_tokens is not None:
                config_kwargs["max_output_tokens"] = max_completion_tokens
            if system_instruction:
                config_kwargs["system_instruction"] = system_instruction
            start = self._monotonic()
            started_at = _utc_now_iso()
            try:
                response = client.models.generate_content(
                    model=actual_model,
                    contents=contents,
                    config=types.GenerateContentConfig(**config_kwargs) if config_kwargs else None,
                )
                payload = getattr(response, "model_dump", lambda: {})()
                if not isinstance(payload, dict):
                    payload = {}
                provider_response = _provider_response_from_json(
                    payload,
                    provider_name=self.provider_name,
                    model_name=actual_model,
                    requested_provider=requested_provider,
                    requested_model=requested_model,
                    provider_chain=provider_chain,
                    provider_switch_count=provider_switch_count,
                    request_context=dict(
                        request_context,
                        request_started_at=started_at,
                        latency_ms=round((self._monotonic() - start) * 1000, 2),
                    ),
                    status_code=_to_int(getattr(response, "response_code", None)),
                    headers=getattr(response, "headers", None),
                    request_started_at=started_at,
                    request_finished_at=_utc_now_iso(),
                )
                provider_response.provider_success = True
                provider_response.success = True
                return provider_response
            except Exception as exc:
                raise ProviderRequestError(
                    provider_name=self.provider_name,
                    model_name=actual_model,
                    message=str(exc) or type(exc).__name__,
                    status_code=None,
                    headers={},
                    body_text=str(exc),
                    rate_limit_info={},
                    requested_provider=requested_provider,
                    requested_model=requested_model,
                    actual_provider=self.provider_name,
                    actual_model=actual_model,
                    provider_switch_count=provider_switch_count,
                    provider_chain=provider_chain,
                    provider_failure_reason=_error_reason_from_status(None, str(exc)),
                    request_started_at=started_at,
                    request_finished_at=_utc_now_iso(),
                ) from exc
        return self._request_via_rest(messages, request_config, request_context)


class CerebrasProviderAdapter(OpenAICompatibleProviderAdapter):
    def __init__(
        self,
        *,
        api_key: str,
        model_name: str,
        timeout: float,
        max_retries: int,
        state: Any | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        monotonic_fn: Callable[[], float] = time.monotonic,
        opener: Callable[[urllib.request.Request, float], Any] | None = None,
        base_url: str = "https://api.cerebras.ai/v1",
    ) -> None:
        super().__init__(
            provider_name="Cerebras",
            base_url=base_url,
            api_key=api_key,
            model_name=model_name,
            timeout=timeout,
            max_retries=max_retries,
            state=state,
            sleep_fn=sleep_fn,
            monotonic_fn=monotonic_fn,
            opener=opener,
        )


class MultiProviderClient:
    def __init__(
        self,
        *,
        execution_mode: str = "RESEARCH_FIXED_PROVIDER",
        requested_provider: str = "Groq",
        requested_model: str = "",
        provider_chain: tuple[str, ...] = ("Groq",),
        providers: dict[str, Any] | None = None,
        provider_models: dict[str, str] | None = None,
        provider_api_keys: dict[str, str] | None = None,
        provider_base_urls: dict[str, str] | None = None,
        provider_timeouts: dict[str, float] | None = None,
        timeout: float = 30.0,
        max_retries: int = 4,
        state: Any | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        monotonic_fn: Callable[[], float] = time.monotonic,
        opener: Callable[[urllib.request.Request, float], Any] | None = None,
    ) -> None:
        self.execution_mode = execution_mode.strip().upper() or "RESEARCH_FIXED_PROVIDER"
        self.requested_provider = _normalized_name(requested_provider, "Groq") or "Groq"
        self.requested_model = _normalized_name(requested_model)
        self.provider_chain = provider_chain
        self.provider_models = dict(provider_models or {})
        self.provider_api_keys = dict(provider_api_keys or {})
        self.provider_base_urls = dict(provider_base_urls or {})
        self.provider_timeouts = dict(provider_timeouts or {})
        self.timeout = timeout
        self.max_retries = max_retries
        self._sleep = sleep_fn
        self._monotonic = monotonic_fn
        self._opener = opener
        self._providers = dict(providers or {})
        self._states: dict[str, Any] = {}
        if state is not None:
            self._states[self.requested_provider] = state
        self.chat = _ProviderChatAPI(self)
        primary = self._providers.get(self.requested_provider)
        self.state = getattr(primary, "state", state)
        self.base_url = getattr(primary, "base_url", "")
        self.api_key = getattr(primary, "api_key", "")

    def _provider_model(self, provider_name: str) -> str:
        configured = _normalized_name(self.provider_models.get(provider_name, ""))
        if configured:
            return configured
        if provider_name == "Gemini":
            return self.requested_model or os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        if provider_name == "OpenRouter":
            return self.requested_model or os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b")
        if provider_name == "Cerebras":
            return self.requested_model or os.getenv("CEREBRAS_MODEL", "llama-4-scout-17b-16e-instruct")
        return self.requested_model or os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    def _build_provider(self, provider_name: str) -> Any:
        provider_name = _normalized_name(provider_name)
        cached = self._providers.get(provider_name)
        if cached is not None:
            return cached

        api_key = _normalized_name(self.provider_api_keys.get(provider_name, ""))
        base_url = _normalized_name(self.provider_base_urls.get(provider_name, ""))
        model_name = self._provider_model(provider_name)
        provider_state = self._states.get(provider_name)
        if provider_state is None:
            provider_state = get_shared_provider_reliability_state(_provider_key(provider_name, model_name, base_url))
            self._states[provider_name] = provider_state
        provider_timeout = float(self.provider_timeouts.get(provider_name, self.timeout))
        if provider_name == "Groq":
            provider = GroqProviderAdapter(
                api_key=api_key,
                model_name=model_name,
                timeout=provider_timeout,
                max_retries=self.max_retries,
                state=provider_state,
                sleep_fn=self._sleep,
                monotonic_fn=self._monotonic,
                opener=self._opener,
                base_url=base_url or "https://api.groq.com/openai/v1",
            )
        elif provider_name == "Gemini":
            provider = GeminiProviderAdapter(
                api_key=api_key,
                model_name=model_name,
                timeout=provider_timeout,
                max_retries=self.max_retries,
                state=provider_state,
                sleep_fn=self._sleep,
                monotonic_fn=self._monotonic,
                opener=self._opener,
                base_url=base_url or "https://generativelanguage.googleapis.com/v1beta",
            )
        elif provider_name == "OpenRouter":
            provider = OpenRouterProviderAdapter(
                api_key=api_key,
                model_name=model_name,
                timeout=provider_timeout,
                max_retries=self.max_retries,
                state=provider_state,
                sleep_fn=self._sleep,
                monotonic_fn=self._monotonic,
                opener=self._opener,
                base_url=base_url or "https://openrouter.ai/api/v1",
            )
        elif provider_name == "Cerebras":
            provider = CerebrasProviderAdapter(
                api_key=api_key,
                model_name=model_name,
                timeout=provider_timeout,
                max_retries=self.max_retries,
                state=provider_state,
                sleep_fn=self._sleep,
                monotonic_fn=self._monotonic,
                opener=self._opener,
                base_url=base_url or "https://api.cerebras.ai/v1",
            )
        else:
            raise ProviderRequestError(
                provider_name=provider_name or "Unknown",
                model_name=model_name,
                message=f"UNSUPPORTED_PROVIDER:{provider_name}",
                provider_failure_reason="UNSUPPORTED_PROVIDER",
            )
        self._providers[provider_name] = provider
        if self.state is None:
            self.state = getattr(provider, "state", None)
        if not self.base_url:
            self.base_url = getattr(provider, "base_url", "")
        if not self.api_key:
            self.api_key = getattr(provider, "api_key", "")
        return provider

    def request(self, messages: list[dict[str, Any]], request_config: dict[str, Any], request_context: dict[str, Any]) -> ProviderResponse:
        request_context = _normalize_request_context(request_context)
        request_config = dict(request_config or {})
        requested_provider = _normalized_name(request_context.get("requested_provider", self.requested_provider), self.requested_provider)
        requested_model = _normalized_name(request_context.get("requested_model", request_config.get("model", self.requested_model)))
        provider_chain = _provider_chain_tuple(request_context.get("provider_chain", self.provider_chain), self.provider_chain)
        if not provider_chain:
            provider_chain = (requested_provider,)
        providers_to_try = (requested_provider,) if self.execution_mode == "RESEARCH_FIXED_PROVIDER" else provider_chain
        last_error: ProviderRequestError | None = None
        for switch_count, provider_name in enumerate(providers_to_try):
            provider = self._build_provider(provider_name)
            actual_model = self._provider_model(provider_name)
            attempt_context = dict(
                request_context,
                requested_provider=requested_provider,
                requested_model=requested_model,
                actual_provider=provider_name,
                actual_model=actual_model,
                provider_chain=providers_to_try,
                provider_switch_count=switch_count,
                provider_mode=self.execution_mode,
            )
            attempt_request_config = dict(request_config)
            attempt_request_config["model"] = actual_model
            try:
                response = provider.request(messages, attempt_request_config, attempt_context)
                self._last_actual_provider = provider_name
                self._last_actual_model = actual_model
                _attach_request_metadata(
                    response,
                    {
                        "request_id": getattr(response, "request_id", request_context.get("request_id", "")),
                        "request_simulation_step": getattr(response, "request_simulation_step", request_context.get("request_simulation_step")),
                        "http_attempt_id": getattr(response, "http_attempt_id", None),
                        "prompt_hash": request_context.get("prompt_hash", ""),
                        "request_started_at": getattr(response, "request_started_at", ""),
                        "request_finished_at": getattr(response, "request_finished_at", ""),
                    },
                )
                return response
            except ProviderRequestError as exc:
                last_error = exc
                if self.execution_mode == "RESEARCH_FIXED_PROVIDER":
                    raise
                continue
        if last_error is not None:
            raise last_error
        raise ProviderRequestError(
            provider_name=requested_provider,
            model_name=requested_model or self._provider_model(requested_provider),
            message="PROVIDER_CHAIN_EMPTY",
            requested_provider=requested_provider,
            requested_model=requested_model,
            actual_provider=requested_provider,
            actual_model=requested_model or self._provider_model(requested_provider),
            provider_chain=providers_to_try,
            provider_switch_count=0,
            provider_failure_reason="PROVIDER_CHAIN_EMPTY",
        )

    @property
    def actual_provider(self) -> str:
        return _normalized_name(getattr(self, "_last_actual_provider", "")) or self.requested_provider


def build_provider_response(
    *,
    provider_name: str,
    model_name: str,
    request_id: str = "",
    http_attempt_id: int | None = None,
    success: bool = True,
    status_code: int | None = None,
    raw_response: Any = None,
    parsed_content: str = "",
    latency_ms: float = 0.0,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    total_tokens: int | None = None,
    error_type: str = "",
    error_message: str = "",
    requested_provider: str = "",
    requested_model: str = "",
    actual_provider: str = "",
    actual_model: str = "",
    provider_switch_count: int = 0,
    provider_chain: tuple[str, ...] = (),
    provider_failure_reason: str = "",
    provider_success: bool = False,
    choices: list[Any] | None = None,
    usage: Any = None,
    headers: dict[str, str] | None = None,
    finish_reason: str = "",
    retry_count: int = 0,
    request_attempt_count: int | None = None,
    request_pacing_delay_ms: float | None = None,
    retry_after_seconds: float | None = None,
    rate_limit_info: dict[str, Any] | None = None,
    request_started_at: str = "",
    request_finished_at: str = "",
    request_simulation_step: int | None = None,
    response_object_type: str = "ProviderResponse",
) -> ProviderResponse:
    return ProviderResponse(
        provider_name=provider_name,
        model_name=model_name,
        request_id=request_id,
        http_attempt_id=http_attempt_id,
        success=success,
        status_code=status_code,
        raw_response=raw_response,
        parsed_content=parsed_content,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        error_type=error_type,
        error_message=error_message,
        requested_provider=requested_provider,
        requested_model=requested_model,
        actual_provider=actual_provider,
        actual_model=actual_model,
        provider_switch_count=provider_switch_count,
        provider_chain=provider_chain,
        provider_failure_reason=provider_failure_reason,
        provider_success=provider_success,
        choices=list(choices or []),
        usage=usage,
        headers=dict(headers or {}),
        finish_reason=finish_reason,
        retry_count=retry_count,
        request_attempt_count=request_attempt_count,
        request_pacing_delay_ms=request_pacing_delay_ms,
        retry_after_seconds=retry_after_seconds,
        rate_limit_info=dict(rate_limit_info or {}),
        request_started_at=request_started_at,
        request_finished_at=request_finished_at,
        request_simulation_step=request_simulation_step,
        response_object_type=response_object_type,
    )

