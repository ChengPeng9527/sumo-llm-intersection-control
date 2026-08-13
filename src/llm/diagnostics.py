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
            "reasoning_tokens": None,
            "visible_completion_tokens": None,
        }

    prompt_tokens = _extract_nested_value(usage, "prompt_tokens")
    completion_tokens = _extract_nested_value(usage, "completion_tokens")
    total_tokens = _extract_nested_value(usage, "total_tokens")
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
        "reasoning_tokens": reasoning_tokens,
        "visible_completion_tokens": visible_completion_tokens,
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
    exception_type = type(exception).__name__ if exception is not None else ""
    exception_message = redact_sensitive_text(exception) if exception is not None else ""
    return {
        "provider_request_attempted": provider_request_attempted,
        "provider_request_success": provider_request_success,
        "provider_name": provider_name,
        "model_name": model_name,
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
