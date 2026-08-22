from __future__ import annotations

import re
from typing import Any


_SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"gsk_[A-Za-z0-9]{8,}"), "[REDACTED_GROQ_API_KEY]"),
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-+=/]+\b"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization:\s*Bearer\s+[A-Za-z0-9._\-+=/]+\b"), "Authorization: Bearer [REDACTED]"),
)


def redact_sensitive_text(text: Any, *, max_length: int | None = None) -> str:
    if text is None:
        return ""
    redacted = str(text)
    for pattern, replacement in _SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    if max_length is not None and max_length >= 0 and len(redacted) > max_length:
        redacted = redacted[:max_length]
    return redacted


def _first_choice_message_content(response: Any) -> str:
    if response is None:
        return ""
    if isinstance(response, str):
        return response
    choices = getattr(response, "choices", None)
    if choices:
        first_choice = choices[0]
        message = getattr(first_choice, "message", None)
        content = getattr(message, "content", None)
        if isinstance(content, str):
            return content
        if content is not None:
            return str(content)
    content = getattr(response, "content", None)
    if isinstance(content, str):
        return content
    if content is not None:
        return str(content)
    return ""


def extract_http_status(response: Any) -> int | None:
    if response is None:
        return None
    for attr in ("status_code", "status"):
        value = getattr(response, attr, None)
        if isinstance(value, int):
            return value
    inner = getattr(response, "_response", None)
    if inner is not None:
        for attr in ("status_code", "status"):
            value = getattr(inner, attr, None)
            if isinstance(value, int):
                return value
    inner = getattr(response, "response", None)
    if inner is not None:
        for attr in ("status_code", "status"):
            value = getattr(inner, attr, None)
            if isinstance(value, int):
                return value
    return None


def _extract_nested_value(value: Any, *path: str) -> Any:
    current = value
    for key in path:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(key)
        else:
            current = getattr(current, key, None)
    return current


def extract_finish_reason(response: Any) -> str:
    if response is None:
        return ""
    choices = getattr(response, "choices", None)
    if choices:
        first_choice = choices[0]
        finish_reason = getattr(first_choice, "finish_reason", None)
        if finish_reason is not None:
            return str(finish_reason)
    finish_reason = getattr(response, "finish_reason", None)
    if finish_reason is not None:
        return str(finish_reason)
    inner = getattr(response, "_response", None)
    if inner is not None:
        finish_reason = getattr(inner, "finish_reason", None)
        if finish_reason is not None:
            return str(finish_reason)
    return ""


def extract_usage_metadata(response: Any) -> dict[str, Any]:
    usage = getattr(response, "usage", None)
    if usage is None:
        inner = getattr(response, "_response", None)
        if inner is not None:
            usage = getattr(inner, "usage", None)
    if usage is None and isinstance(response, dict):
        usage = response.get("usage")
    if usage is None:
        return {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
            "thoughts_token_count": None,
            "reasoning_tokens": None,
            "visible_completion_tokens": None,
        }

    prompt_tokens = _extract_nested_value(usage, "prompt_tokens")
    completion_tokens = _extract_nested_value(usage, "completion_tokens")
    total_tokens = _extract_nested_value(usage, "total_tokens")
    thoughts_token_count = _extract_nested_value(usage, "thoughts_token_count")
    if thoughts_token_count is None:
        thoughts_token_count = _extract_nested_value(usage, "thoughtsTokenCount")
    reasoning_tokens = _extract_nested_value(usage, "completion_tokens_details", "reasoning_tokens")
    if reasoning_tokens is None:
        reasoning_tokens = _extract_nested_value(usage, "reasoning_tokens")
    visible_completion_tokens = _extract_nested_value(usage, "completion_tokens_details", "visible_tokens")
    if visible_completion_tokens is None and isinstance(completion_tokens, int) and isinstance(reasoning_tokens, int):
        visible_completion_tokens = completion_tokens - reasoning_tokens
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "thoughts_token_count": thoughts_token_count,
        "reasoning_tokens": reasoning_tokens,
        "visible_completion_tokens": visible_completion_tokens,
    }


def extract_retry_metadata(source: Any) -> dict[str, Any]:
    if source is None:
        return {
            "retry_count": 0,
            "retry_after_seconds": None,
            "request_attempt_count": None,
            "request_pacing_delay_ms": None,
            "request_id": "",
            "request_simulation_step": None,
            "http_attempt_id": None,
            "prompt_hash": "",
            "request_started_at": "",
            "request_finished_at": "",
            "rate_limit_limit_tokens": None,
            "rate_limit_remaining_tokens": None,
            "rate_limit_reset_tokens_seconds": None,
            "rate_limit_limit_requests": None,
            "rate_limit_remaining_requests": None,
            "rate_limit_reset_requests_seconds": None,
        }

    rate_limit_info = getattr(source, "rate_limit_info", None)
    if rate_limit_info is None and isinstance(source, dict):
        rate_limit_info = source.get("rate_limit_info")
    if rate_limit_info is None:
        rate_limit_info = {}
    if not isinstance(rate_limit_info, dict):
        rate_limit_info = {
            "retry_after_seconds": getattr(rate_limit_info, "retry_after_seconds", None),
            "limit_tokens": getattr(rate_limit_info, "limit_tokens", None),
            "remaining_tokens": getattr(rate_limit_info, "remaining_tokens", None),
            "reset_tokens_seconds": getattr(rate_limit_info, "reset_tokens_seconds", None),
            "limit_requests": getattr(rate_limit_info, "limit_requests", None),
            "remaining_requests": getattr(rate_limit_info, "remaining_requests", None),
            "reset_requests_seconds": getattr(rate_limit_info, "reset_requests_seconds", None),
        }

    def _source_value(key: str, default: Any = None) -> Any:
        if isinstance(source, dict):
            return source.get(key, default)
        return getattr(source, key, default)

    return {
        "retry_count": _source_value("retry_count", 0),
        "retry_after_seconds": rate_limit_info.get("retry_after_seconds"),
        "request_attempt_count": _source_value("request_attempt_count"),
        "request_pacing_delay_ms": _source_value("request_pacing_delay_ms"),
        "rate_limit_limit_tokens": rate_limit_info.get("limit_tokens"),
        "rate_limit_remaining_tokens": rate_limit_info.get("remaining_tokens"),
        "rate_limit_reset_tokens_seconds": rate_limit_info.get("reset_tokens_seconds"),
        "rate_limit_limit_requests": rate_limit_info.get("limit_requests"),
        "rate_limit_remaining_requests": rate_limit_info.get("remaining_requests"),
        "rate_limit_reset_requests_seconds": rate_limit_info.get("reset_requests_seconds"),
    }


def build_provider_diagnostics(
    *,
    provider_name: str,
    model_name: str,
    response: Any = None,
    parser_input: str = "",
    parser_success: bool = False,
    parser_action: str = "",
    parser_failure_reason: str = "",
    fallback_triggered: bool = False,
    fallback_reason: str = "",
    exception: Exception | None = None,
    latency_ms: float = 0.0,
    provider_request_attempted: bool = False,
    provider_request_success: bool = False,
) -> dict[str, Any]:
    response_content = _first_choice_message_content(response) if response is not None else ""
    parser_input_text = parser_input if parser_input else response_content
    source = response if response is not None else exception

    def _source_value(key: str, default: Any = None) -> Any:
        if source is None:
            return default
        if isinstance(source, dict):
            return source.get(key, default)
        return getattr(source, key, default)

    provider_name_value = _source_value("actual_provider", _source_value("provider_name", provider_name))
    model_name_value = _source_value("actual_model", _source_value("model_name", model_name))
    requested_provider_value = _source_value("requested_provider", provider_name_value)
    requested_model_value = _source_value("requested_model", model_name_value)
    actual_provider_value = _source_value("actual_provider", provider_name_value)
    actual_model_value = _source_value("actual_model", model_name_value)
    provider_switch_count_value = _source_value("provider_switch_count", 0)
    provider_chain_value = _source_value("provider_chain", (actual_provider_value,))
    provider_failure_reason_value = _source_value("provider_failure_reason", fallback_reason)
    provider_success_value = bool(_source_value("provider_success", provider_request_success))
    exception_type = type(exception).__name__ if exception is not None else ""
    exception_message = redact_sensitive_text(exception) if exception is not None else ""
    retry_metadata = extract_retry_metadata(response if response is not None else exception)
    request_attempt_count_value = retry_metadata.get("request_attempt_count")
    http_attempt_id_value = _source_value("http_attempt_id", request_attempt_count_value)
    if http_attempt_id_value is None and provider_request_attempted:
        http_attempt_id_value = retry_metadata.get("retry_count", 0) + 1
    if request_attempt_count_value is None:
        request_attempt_count_value = http_attempt_id_value
    retry_metadata["request_attempt_count"] = request_attempt_count_value
    retry_metadata["http_attempt_id"] = http_attempt_id_value

    return {
        "provider_request_attempted": provider_request_attempted,
        "provider_request_success": provider_request_success,
        "provider_name": provider_name_value,
        "model_name": model_name_value,
        "requested_provider": requested_provider_value,
        "requested_model": requested_model_value,
        "actual_provider": actual_provider_value,
        "actual_model": actual_model_value,
        "provider_switch_count": provider_switch_count_value,
        "provider_chain": provider_chain_value,
        "provider_failure_reason": provider_failure_reason_value,
        "provider_success": provider_success_value,
        "request_id": _source_value("request_id", ""),
        "request_simulation_step": _source_value("request_simulation_step"),
        "http_attempt_id": http_attempt_id_value,
        "prompt_hash": _source_value("prompt_hash", ""),
        "request_started_at": _source_value("request_started_at", ""),
        "request_finished_at": _source_value("request_finished_at", ""),
        "http_status": extract_http_status(response),
        "finish_reason": extract_finish_reason(response),
        **extract_usage_metadata(response),
        "response_object_type": type(response).__name__ if response is not None else "",
        "response_content_present": bool(response_content),
        "response_content_length": len(response_content),
        "response_content_redacted": redact_sensitive_text(response_content),
        "parser_input_present": bool(parser_input_text),
        "parser_input_length": len(parser_input_text),
        "parser_input_redacted": redact_sensitive_text(parser_input_text),
        "parser_success": parser_success,
        "parser_action": parser_action,
        "parser_failure_reason": parser_failure_reason,
        "fallback_triggered": fallback_triggered,
        "fallback_reason": fallback_reason,
        "exception_type": exception_type,
        "exception_message_redacted": exception_message,
        "latency_ms": round(latency_ms, 2),
        **retry_metadata,
    }

def classify_response_format(response_text: str) -> str:
    text = (response_text or "").strip()
    if not text:
        return "EMPTY_RESPONSE"
    lower = text.lower()
    if re.fullmatch(r"(?i)(proceed|wait|free)", text):
        return "PURE_EXPECTED_ACTION"
    if text.startswith("```") and "{" in text and "}" in text:
        return "MARKDOWN_WRAPPED_JSON"
    if text.startswith("{") or text.startswith("["):
        return "JSON"
    if "<decision>" in lower or "<action>" in lower:
        return "XML_OR_TAGS"
    if "final decision" in lower or "decision:" in lower:
        return "REASONING_PLUS_ACTION"
    if any(token in lower for token in ("proceed", "wait", "free")):
        return "SENTENCE"
    return "OTHER"


def infer_parser_failure_reason(response_text: str, parser_success: bool, parser_action: str) -> str:
    text = (response_text or "").strip()
    if not text:
        return "EMPTY_RESPONSE"
    if parser_success and parser_action == "MISSING":
        if text.startswith("["):
            return "TOP_LEVEL_JSON_LIST_WAS_COLLAPSED_TO_OBJECT"
        if '"action"' in text and '"decision"' not in text:
            return "UNMAPPED_ACTION_FIELD"
        return "PARSER_COMPATIBILITY_GAP"
    if not parser_success and text.startswith("["):
        return "JSON_LIST_PARSE_FAILURE"
    if not parser_success and text.startswith("{"):
        return "JSON_OBJECT_PARSE_FAILURE"
    return ""
