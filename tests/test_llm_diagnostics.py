from types import SimpleNamespace

from src.llm.diagnostics import (
    build_provider_diagnostics,
    classify_response_format,
    extract_finish_reason,
    extract_http_status,
    extract_usage_metadata,
    infer_parser_failure_reason,
    redact_sensitive_text,
)


def test_redact_sensitive_text_removes_api_key_and_bearer_token():
    text = "Authorization: Bearer abc.def.ghi gsk_1234567890abcdef"

    redacted = redact_sensitive_text(text)

    assert "gsk_" not in redacted
    assert "Bearer [REDACTED]" in redacted


def test_extract_http_status_handles_common_response_shapes():
    response = SimpleNamespace(status_code=200)
    wrapped = SimpleNamespace(_response=SimpleNamespace(status=201))

    assert extract_http_status(response) == 200
    assert extract_http_status(wrapped) == 201


def test_extract_finish_reason_handles_choice_and_top_level_shapes():
    response = SimpleNamespace(choices=[SimpleNamespace(finish_reason="length")])
    wrapped = SimpleNamespace(finish_reason="stop")

    assert extract_finish_reason(response) == "length"
    assert extract_finish_reason(wrapped) == "stop"


def test_extract_usage_metadata_handles_nested_usage_shapes():
    response = SimpleNamespace(
        usage=SimpleNamespace(
            prompt_tokens=12,
            completion_tokens=34,
            total_tokens=46,
            completion_tokens_details=SimpleNamespace(reasoning_tokens=9, visible_tokens=25),
        )
    )

    usage = extract_usage_metadata(response)

    assert usage["prompt_tokens"] == 12
    assert usage["completion_tokens"] == 34
    assert usage["total_tokens"] == 46
    assert usage["reasoning_tokens"] == 9
    assert usage["visible_completion_tokens"] == 25


def test_build_provider_diagnostics_captures_response_and_exception_details():
    response = SimpleNamespace(
        status_code=200,
        choices=[SimpleNamespace(message=SimpleNamespace(content='```json\n{"car0":"PROCEED"}\n```'), finish_reason="stop")],
        usage=SimpleNamespace(
            prompt_tokens=11,
            completion_tokens=22,
            total_tokens=33,
            completion_tokens_details=SimpleNamespace(reasoning_tokens=5, visible_tokens=17),
        ),
    )
    diagnostics = build_provider_diagnostics(
        provider_name="Groq",
        model_name="openai/gpt-oss-20b",
        response=response,
        parser_input='{"car0":"PROCEED"}',
        parser_success=True,
        parser_action="PROCEED",
        fallback_triggered=False,
        latency_ms=12.345,
        provider_request_attempted=True,
        provider_request_success=True,
    )

    assert diagnostics["provider_request_attempted"] is True
    assert diagnostics["provider_request_success"] is True
    assert diagnostics["provider_name"] == "Groq"
    assert diagnostics["model_name"] == "openai/gpt-oss-20b"
    assert diagnostics["http_status"] == 200
    assert diagnostics["finish_reason"] == "stop"
    assert diagnostics["prompt_tokens"] == 11
    assert diagnostics["completion_tokens"] == 22
    assert diagnostics["total_tokens"] == 33
    assert diagnostics["reasoning_tokens"] == 5
    assert diagnostics["visible_completion_tokens"] == 17
    assert diagnostics["response_object_type"] == "SimpleNamespace"
    assert diagnostics["response_content_present"] is True
    assert diagnostics["response_content_length"] > 0
    assert diagnostics["parser_input_present"] is True
    assert diagnostics["parser_input_length"] > 0
    assert diagnostics["parser_success"] is True
    assert diagnostics["parser_action"] == "PROCEED"
    assert diagnostics["latency_ms"] == 12.35


def test_build_provider_diagnostics_redacts_exception_message():
    diagnostics = build_provider_diagnostics(
        provider_name="Groq",
        model_name="openai/gpt-oss-20b",
        exception=RuntimeError("failed with gsk_1234567890abcdef"),
        parser_failure_reason="PROVIDER_REQUEST_EXCEPTION",
        fallback_triggered=True,
        fallback_reason="PROVIDER_REQUEST_EXCEPTION",
        latency_ms=1.5,
        provider_request_attempted=True,
        provider_request_success=False,
    )

    assert diagnostics["exception_type"] == "RuntimeError"
    assert "gsk_" not in diagnostics["exception_message_redacted"]
    assert diagnostics["fallback_triggered"] is True
    assert diagnostics["fallback_reason"] == "PROVIDER_REQUEST_EXCEPTION"


def test_classify_response_format_covers_common_shapes():
    assert classify_response_format("PROCEED") == "PURE_EXPECTED_ACTION"
    assert classify_response_format("```json\n{\"car0\":\"PROCEED\"}\n```") == "MARKDOWN_WRAPPED_JSON"
    assert classify_response_format("<decision>WAIT</decision>") == "XML_OR_TAGS"


def test_infer_parser_failure_reason_flags_list_collapsing_gap():
    text = '[{"vehicle_id":"diag_car0","decision":"PROCEED"}]'

    assert infer_parser_failure_reason(text, True, "MISSING") == "TOP_LEVEL_JSON_LIST_WAS_COLLAPSED_TO_OBJECT"
