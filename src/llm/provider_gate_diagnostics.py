from __future__ import annotations

from typing import Any


def determine_provider_skip_reason(
    *,
    llm_mode: str,
    credential_available: bool,
    openai_available: bool,
    live_client_constructed: bool,
    provider_call_function_entered: bool,
    provider_request_attempted: bool,
    eligible_vehicle_count: int,
    interface_rule_short_circuit: bool = False,
    precondition_failed: bool = False,
) -> str:
    if llm_mode != "real":
        return "LIVE_MODE_DISABLED"
    if not credential_available:
        return "MISSING_CREDENTIAL"
    if not openai_available or not live_client_constructed:
        return "CLIENT_NOT_AVAILABLE"
    if interface_rule_short_circuit:
        return "INTERFACE_RULE_SHORT_CIRCUIT"
    if eligible_vehicle_count <= 0:
        return "NO_LLM_ELIGIBLE_VEHICLES"
    if precondition_failed:
        return "PRECONDITION_FAILED"
    if not provider_call_function_entered and not provider_request_attempted:
        return "PRECONDITION_FAILED"
    return ""


def build_live_provider_gate_diagnostics(
    *,
    llm_mode: str,
    credential_available: bool,
    openai_available: bool,
    live_client_constructed: bool,
    llm_branch_entered: bool,
    provider_call_function_entered: bool,
    provider_request_kwargs_built: bool,
    provider_request_attempted: bool,
    provider_request_skipped: bool,
    eligible_vehicle_count: int,
    interface_rule_short_circuit: bool = False,
    precondition_failed: bool = False,
    fallback_trigger_reason: str = "",
    decision_source: str = "",
) -> dict[str, Any]:
    live_provider_enabled = llm_mode == "real"
    live_provider_gate_entered = llm_branch_entered and live_provider_enabled
    provider_skip_reason = determine_provider_skip_reason(
        llm_mode=llm_mode,
        credential_available=credential_available,
        openai_available=openai_available,
        live_client_constructed=live_client_constructed,
        provider_call_function_entered=provider_call_function_entered,
        provider_request_attempted=provider_request_attempted,
        eligible_vehicle_count=eligible_vehicle_count,
        interface_rule_short_circuit=interface_rule_short_circuit,
        precondition_failed=precondition_failed,
    )
    fallback_reason = fallback_trigger_reason or provider_skip_reason
    return {
        "llm_branch_entered": llm_branch_entered,
        "live_provider_gate_entered": live_provider_gate_entered,
        "live_provider_enabled": live_provider_enabled,
        "credential_available": credential_available,
        "live_client_constructed": live_client_constructed,
        "provider_call_function_entered": provider_call_function_entered,
        "provider_request_kwargs_built": provider_request_kwargs_built,
        "provider_request_attempted": provider_request_attempted,
        "provider_request_skipped": provider_request_skipped,
        "provider_skip_reason": provider_skip_reason,
        "fallback_trigger_reason": fallback_reason,
        "decision_source": decision_source,
    }
