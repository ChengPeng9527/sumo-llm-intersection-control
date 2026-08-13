from __future__ import annotations

from src.controllers.decision_pipeline import build_decision_trace
from src.llm.provider_gate_diagnostics import build_live_provider_gate_diagnostics


def _build_state(vehicle_id: str, inside: bool = True) -> dict:
    return {
        "vehicle_id": vehicle_id,
        "route_id": "N_S",
        "speed": 5.0,
        "distance_to_intersection": 10.0,
        "time_to_intersection": 2.0,
        "inside_control_zone": inside,
    }


def test_live_enabled_with_credential_and_eligible_state_attempts_provider():
    diagnostics = build_live_provider_gate_diagnostics(
        llm_mode="real",
        credential_available=True,
        openai_available=True,
        live_client_constructed=True,
        llm_branch_entered=True,
        provider_call_function_entered=True,
        provider_request_kwargs_built=True,
        provider_request_attempted=True,
        provider_request_skipped=False,
        eligible_vehicle_count=1,
        decision_source="LLM_RAW",
    )

    assert diagnostics["live_provider_gate_entered"] is True
    assert diagnostics["live_client_constructed"] is True
    assert diagnostics["provider_call_function_entered"] is True
    assert diagnostics["provider_request_attempted"] is True
    assert diagnostics["provider_request_skipped"] is False
    assert diagnostics["provider_skip_reason"] == ""


def test_live_disabled_sets_explicit_skip_reason():
    diagnostics = build_live_provider_gate_diagnostics(
        llm_mode="mock",
        credential_available=True,
        openai_available=True,
        live_client_constructed=False,
        llm_branch_entered=True,
        provider_call_function_entered=False,
        provider_request_kwargs_built=False,
        provider_request_attempted=False,
        provider_request_skipped=True,
        eligible_vehicle_count=1,
        decision_source="FALLBACK",
    )

    assert diagnostics["live_provider_enabled"] is False
    assert diagnostics["provider_request_attempted"] is False
    assert diagnostics["provider_skip_reason"] == "LIVE_MODE_DISABLED"


def test_missing_credential_sets_explicit_skip_reason():
    diagnostics = build_live_provider_gate_diagnostics(
        llm_mode="real",
        credential_available=False,
        openai_available=True,
        live_client_constructed=False,
        llm_branch_entered=True,
        provider_call_function_entered=False,
        provider_request_kwargs_built=False,
        provider_request_attempted=False,
        provider_request_skipped=True,
        eligible_vehicle_count=1,
        decision_source="FALLBACK",
    )

    assert diagnostics["provider_skip_reason"] == "MISSING_CREDENTIAL"
    assert diagnostics["provider_request_attempted"] is False


def test_no_eligible_vehicle_sets_explicit_skip_reason():
    diagnostics = build_live_provider_gate_diagnostics(
        llm_mode="real",
        credential_available=True,
        openai_available=True,
        live_client_constructed=True,
        llm_branch_entered=True,
        provider_call_function_entered=False,
        provider_request_kwargs_built=False,
        provider_request_attempted=False,
        provider_request_skipped=True,
        eligible_vehicle_count=0,
        decision_source="FALLBACK",
    )

    assert diagnostics["provider_skip_reason"] == "NO_LLM_ELIGIBLE_VEHICLES"


def test_interface_rule_short_circuit_is_distinct_from_provider_attempt():
    diagnostics = build_live_provider_gate_diagnostics(
        llm_mode="real",
        credential_available=True,
        openai_available=True,
        live_client_constructed=True,
        llm_branch_entered=True,
        provider_call_function_entered=False,
        provider_request_kwargs_built=False,
        provider_request_attempted=False,
        provider_request_skipped=True,
        eligible_vehicle_count=1,
        interface_rule_short_circuit=True,
        decision_source="DETERMINISTIC_INTERFACE_RULE",
    )

    assert diagnostics["provider_skip_reason"] == "INTERFACE_RULE_SHORT_CIRCUIT"
    assert diagnostics["provider_request_attempted"] is False


def test_llm_called_is_branch_entry_not_request_attempt():
    trace = build_decision_trace(
        [_build_state("car0")],
        {"car0": "FREE"},
        {"car0": "FREE"},
        {
            "llm_called": True,
            "llm_branch_entered": True,
            "provider_request_attempted": False,
            "provider_request_skipped": True,
            "provider_skip_reason": "MISSING_CREDENTIAL",
            "decision_source": "FALLBACK",
        },
    )

    assert trace["car0"]["llm_called"] is True
    assert trace["car0"]["llm_branch_entered"] is True
    assert trace["car0"]["provider_request_attempted"] is False
    assert trace["car0"]["provider_request_skipped"] is True
