from __future__ import annotations

import json
from types import SimpleNamespace

from src.controllers.decision_pipeline import execute_llm_candidate_selector_pipeline
from src.llm.candidate_selector import run_live_candidate_request, select_candidate_with_llm
from src.llm.provider_architecture import GeminiProviderAdapter, ProviderRequestError
from src.llm.request_config import (
    PHASE2_BASE_URL,
    PHASE2_MODEL,
    PHASE2_PROVIDER_MODE,
    PHASE2_PROVIDER_NAME,
    PHASE2_TIMEOUT_SECONDS,
    build_candidate_selection_request_kwargs,
    create_live_client,
    create_phase2_live_client,
)


class FakeHTTPResponse:
    def __init__(self, payload, *, status=200):
        self._payload = payload
        self.status = status
        self.code = status
        self.headers = {}

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


class CapturingOpener:
    def __init__(self, payload):
        self.payload = payload
        self.requests = []
        self.timeouts = []

    def __call__(self, request, timeout):
        self.requests.append(request)
        self.timeouts.append(timeout)
        return FakeHTTPResponse(self.payload)


def _state(vehicle_id, route_id, *, waiting=0.0, tti=5.0):
    incoming, outgoing = route_id.split("_")
    return {
        "vehicle_id": vehicle_id,
        "route_id": route_id,
        "incoming_edge": incoming,
        "outgoing_edge": f"-{outgoing}",
        "movement": "STRAIGHT",
        "waiting_time": waiting,
        "speed": 4.0,
        "time_to_intersection": tti,
        "inside_control_zone": True,
    }


def _scenario():
    return (
        [
            _state("a", "N_S", waiting=3, tti=2),
            _state("b", "S_N", waiting=2, tti=3),
            _state("c", "E_W", waiting=1, tti=1),
        ],
        [["a"], ["b"], ["c"], ["a", "b"]],
    )


def _provider_response(content, *, success=True):
    return SimpleNamespace(
        provider_name="Gemini",
        model_name=PHASE2_MODEL,
        actual_provider="Gemini",
        actual_model=PHASE2_MODEL,
        requested_provider="Gemini",
        requested_model=PHASE2_MODEL,
        provider_chain=("Gemini",),
        provider_switch_count=0,
        provider_success=success,
        success=success,
        parsed_content=content,
        status_code=200 if success else 500,
        latency_ms=12.5,
        usage=SimpleNamespace(
            prompt_tokens=21,
            completion_tokens=6,
            total_tokens=27,
            thoughts_token_count=None,
            completion_tokens_details=SimpleNamespace(reasoning_tokens=None, visible_tokens=6),
        ),
        choices=[],
        finish_reason="STOP",
    )


def test_phase2_gemini_configuration_is_frozen_and_single_provider():
    assert PHASE2_PROVIDER_NAME == "Gemini"
    assert PHASE2_MODEL == "gemini-3.6-flash"
    assert PHASE2_BASE_URL == "https://generativelanguage.googleapis.com/v1beta"
    assert PHASE2_TIMEOUT_SECONDS == 60.0
    assert PHASE2_PROVIDER_MODE == "RESEARCH_FIXED_PROVIDER"

    client = create_phase2_live_client(api_key="redacted")
    assert client.requested_provider == "Gemini"
    assert client.requested_model == PHASE2_MODEL
    assert client.provider_chain == ("Gemini",)
    assert client._build_provider("Gemini").timeout == 60.0


def test_candidate_request_schema_restricts_gemini_to_supplied_ids():
    kwargs = build_candidate_selection_request_kwargs(["a", "a|b"])
    schema = kwargs["response_json_schema"]
    assert schema["properties"]["selected_candidate_id"]["enum"] == ["a", "a|b"]
    assert schema["required"] == ["selected_candidate_id"]
    assert schema["additionalProperties"] is False


def test_valid_gemini_candidate_response_preserves_usage_and_provenance(monkeypatch):
    monkeypatch.setattr(GeminiProviderAdapter, "_gemini_sdk_client", lambda self: None)
    states, groups = _scenario()
    payload = {
        "candidates": [{"content": {"parts": [{"text": '{"selected_candidate_id":"a|b"}'}]}, "finishReason": "STOP"}],
        "usageMetadata": {"promptTokenCount": 21, "candidatesTokenCount": 6, "totalTokenCount": 27},
    }
    opener = CapturingOpener(payload)
    client = create_phase2_live_client(api_key="redacted", opener=opener)

    trace = execute_llm_candidate_selector_pipeline(
        states,
        groups,
        lambda prompt: run_live_candidate_request(
            client,
            model_name=PHASE2_MODEL,
            prompt=prompt,
            candidate_ids=["a", "b", "c", "a|b"],
        ),
        provider_name=PHASE2_PROVIDER_NAME,
        model_name=PHASE2_MODEL,
        llm_mode="real",
    )

    entry = trace["a"]
    assert entry["provider_success"] is True
    assert entry["parser_success"] is True
    assert entry["provider_name"] == "Gemini"
    assert entry["model_name"] == PHASE2_MODEL
    assert entry["prompt_tokens"] == 21
    assert entry["completion_tokens"] == 6
    assert entry["total_tokens"] == 27
    assert entry["llm_candidate_id"] == "a|b"
    assert entry["deterministic_candidate_id"] == "a|b"
    assert entry["fallback_used"] is False
    body = json.loads(opener.requests[0].data.decode("utf-8"))
    assert body["generationConfig"]["responseJsonSchema"] == build_candidate_selection_request_kwargs(
        ["a", "b", "c", "a|b"]
    )["response_json_schema"]


def test_mock_gemini_invalid_outputs_and_provider_error_use_comparator_fallback():
    states, groups = _scenario()
    malformed = select_candidate_with_llm(
        states,
        groups,
        lambda prompt: _provider_response("not json"),
        provider_name="Gemini",
        model_name=PHASE2_MODEL,
    )
    unknown = select_candidate_with_llm(
        states,
        groups,
        lambda prompt: _provider_response('{"selected_candidate_id":"unknown"}'),
        provider_name="Gemini",
        model_name=PHASE2_MODEL,
    )

    def provider_error(prompt):
        raise ProviderRequestError(
            provider_name="Gemini",
            model_name=PHASE2_MODEL,
            message="provider unavailable",
            provider_failure_reason="NETWORK_ERROR",
        )

    failed = select_candidate_with_llm(
        states,
        groups,
        provider_error,
        provider_name="Gemini",
        model_name=PHASE2_MODEL,
    )

    assert malformed.final_selected_candidate == "a|b"
    assert malformed.fallback_reason == "MALFORMED_JSON"
    assert unknown.final_selected_candidate == "a|b"
    assert unknown.fallback_reason == "UNKNOWN_CANDIDATE_ID"
    assert failed.final_selected_candidate == "a|b"
    assert failed.fallback_reason == "PROVIDER_FAILURE"
    assert failed.provider_meta["actual_provider"] == "Gemini"


def test_mock_gemini_legal_disagreement_is_preserved_without_fallback():
    states, groups = _scenario()
    result = select_candidate_with_llm(
        states,
        groups,
        lambda prompt: _provider_response('{"selected_candidate_id":"c"}'),
        provider_name="Gemini",
        model_name=PHASE2_MODEL,
    )

    assert result.llm_candidate_id == "c"
    assert result.deterministic_candidate_id == "a|b"
    assert result.candidate_disagreement is True
    assert result.fallback_used is False


def test_historical_groq_client_path_remains_available():
    client = create_live_client(
        base_url="https://api.groq.com/openai/v1",
        api_key="redacted",
        provider_mode="RESEARCH_FIXED_PROVIDER",
        requested_provider="Groq",
        requested_model="openai/gpt-oss-20b",
        provider_chain=("Groq",),
    )
    assert client.base_url == "https://api.groq.com/openai/v1"
