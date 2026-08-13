from src.controllers.decision_pipeline import apply_safety_filter, build_decision_trace, execute_decision_pipeline, normalize_action
from src.controllers.decision_rules import baseline_decide, cooperative_decide
from src.llm.postprocessor import apply_cooperative_postprocessing, apply_interface_rule

from tests.fakes import FixedPostprocessor, FixedSafetyGuard, PassThroughPostprocessor, PassThroughSafetyGuard, StubDecisionProvider


def _build_state(vehicle_id: str, route_id: str, tti: float, inside: bool) -> dict:
    return {
        "vehicle_id": vehicle_id,
        "route_id": route_id,
        "speed": 5.0,
        "distance_to_intersection": 10.0,
        "time_to_intersection": tti,
        "inside_control_zone": inside,
    }


def test_raw_proceed_passes_through_pipeline():
    traffic_state = [_build_state("car0", "N_S", 2.0, True)]
    provider = StubDecisionProvider({"car0": "PROCEED"}, meta={"llm_called": True, "decision_source": "LLM_RAW"})
    raw_decisions, llm_meta = provider(traffic_state)
    trace = execute_decision_pipeline(traffic_state, raw_decisions, stage_mode="raw", llm_meta=llm_meta)

    assert provider.calls == 1
    assert trace["car0"]["llm_raw_decision"] == "PROCEED"
    assert trace["car0"]["validated_llm_decision"] == "PROCEED"
    assert trace["car0"]["postprocessed_decision"] == "PROCEED"
    assert trace["car0"]["final_decision"] == "PROCEED"


def test_pipeline_preserves_diagnostic_meta_without_changing_decisions():
    traffic_state = [_build_state("car0", "N_S", 2.0, True)]
    provider = StubDecisionProvider(
        {"car0": "PROCEED"},
        meta={
            "llm_called": True,
            "decision_source": "LLM_RAW",
            "provider_request_attempted": True,
            "provider_request_success": True,
            "provider_name": "Groq",
            "model_name": "openai/gpt-oss-20b",
            "http_status": 200,
            "response_object_type": "Response",
            "response_content_present": True,
            "response_content_length": 32,
            "response_content_redacted": "{\"car0\":\"PROCEED\"}",
            "parser_input_present": True,
            "parser_input_length": 32,
            "parser_input_redacted": "{\"car0\":\"PROCEED\"}",
            "parser_success": True,
            "parser_action": "PROCEED",
            "parser_failure_reason": "",
            "fallback_triggered": False,
            "fallback_reason": "",
            "exception_type": "",
            "exception_message_redacted": "",
            "latency_ms": 12.34,
        },
    )
    raw_decisions, llm_meta = provider(traffic_state)
    trace = execute_decision_pipeline(traffic_state, raw_decisions, stage_mode="raw", llm_meta=llm_meta)

    assert trace["car0"]["final_decision"] == "PROCEED"
    assert trace["car0"]["provider_request_attempted"] is True
    assert trace["car0"]["provider_request_success"] is True
    assert trace["car0"]["provider_name"] == "Groq"
    assert trace["car0"]["model_name"] == "openai/gpt-oss-20b"
    assert trace["car0"]["parser_success"] is True
    assert trace["car0"]["parser_action"] == "PROCEED"
    assert trace["car0"]["latency_ms"] == 12.34


def test_normalize_action_strips_and_uppercases():
    assert normalize_action(" proceed ") == "PROCEED"


def test_invalid_action_becomes_wait():
    traffic_state = [_build_state("car0", "N_S", 1.0, True)]
    trace = execute_decision_pipeline(
        traffic_state,
        {"car0": "FLY"},
        stage_mode="raw",
        llm_meta={"llm_called": True, "decision_source": "FALLBACK"},
    )

    assert trace["car0"]["llm_raw_decision"] == "FLY"
    assert trace["car0"]["validated_llm_decision"] == "WAIT"
    assert trace["car0"]["final_decision"] == "WAIT"
    assert trace["car0"]["decision_source"] == "FALLBACK"


def test_postprocessor_can_change_decision_and_keep_fields_separate():
    traffic_state = [
        _build_state("car0", "N_S", 1.0, True),
        _build_state("car1", "N_S", 2.0, True),
    ]
    postprocessor = FixedPostprocessor({"car1": "PROCEED"})
    trace = execute_decision_pipeline(
        traffic_state,
        {"car0": "PROCEED", "car1": "WAIT"},
        stage_mode="hybrid",
        llm_meta={"llm_called": True, "decision_source": "LLM_RAW"},
        postprocessor_fn=postprocessor,
    )

    assert postprocessor.calls == 1
    assert trace["car1"]["llm_raw_decision"] == "WAIT"
    assert trace["car1"]["validated_llm_decision"] == "WAIT"
    assert trace["car1"]["postprocessed_decision"] == "PROCEED"
    assert trace["car1"]["final_decision"] == "PROCEED"
    assert trace["car1"]["postprocess_applied"] is True


def test_safety_guard_can_override_to_wait():
    traffic_state = [
        _build_state("car0", "N_S", 1.0, True),
        _build_state("car1", "N_S", 1.2, True),
    ]
    postprocessor = FixedPostprocessor({"car1": "PROCEED"})
    safety = FixedSafetyGuard({"car1": "WAIT"})
    trace = execute_decision_pipeline(
        traffic_state,
        {"car0": "PROCEED", "car1": "WAIT"},
        stage_mode="hybrid_safety",
        llm_meta={"llm_called": True, "decision_source": "LLM_RAW"},
        postprocessor_fn=postprocessor,
        safety_guard_fn=safety,
    )

    assert postprocessor.calls == 1
    assert safety.calls == 1
    assert trace["car1"]["postprocessed_decision"] == "PROCEED"
    assert trace["car1"]["final_decision"] == "WAIT"
    assert trace["car1"]["safety_override"] is True
    assert trace["car1"]["safety_reason"] == "fixed_guard"


def test_safety_guard_never_upgrades_wait_to_proceed():
    traffic_state = [_build_state("car0", "N_S", 1.0, True)]
    trace = build_decision_trace(
        traffic_state,
        {"car0": "WAIT"},
        {"car0": "WAIT"},
        {"llm_called": True},
    )
    trace = apply_safety_filter(trace, traffic_state)

    assert trace["car0"]["final_decision"] == "WAIT"
    assert trace["car0"]["safety_override"] is False


def test_pipeline_call_counts_and_outside_zone_rule():
    traffic_state = [
        _build_state("car0", "N_S", 1.0, True),
        _build_state("car1", "N_S", 2.0, True),
        _build_state("car2", "E_W", 3.0, False),
    ]
    provider = StubDecisionProvider(
        {"car0": "PROCEED", "car1": "WAIT", "car2": "PROCEED"},
        meta={"llm_called": True, "decision_source": "LLM_RAW"},
    )
    postprocessor = PassThroughPostprocessor()
    safety = PassThroughSafetyGuard()
    raw_decisions, llm_meta = provider(traffic_state)
    trace = execute_decision_pipeline(
        traffic_state,
        raw_decisions,
        stage_mode="hybrid_safety",
        llm_meta=llm_meta,
        postprocessor_fn=postprocessor,
        safety_guard_fn=safety,
    )

    assert provider.calls == 1
    assert postprocessor.calls == 1
    assert safety.calls == 1
    assert trace["car2"]["final_decision"] == "FREE"
    assert trace["car2"]["outside_control_zone_rule_applied"] is True
    assert trace["car2"]["decision_source"] == "DETERMINISTIC_INTERFACE_RULE"


def test_baseline_and_cooperative_rules_stay_consistent():
    baseline_states = [
        _build_state("car0", "N_S", 1.0, True),
        _build_state("car1", "E_W", 2.0, True),
        _build_state("car2", "W_E", 9.0, False),
    ]
    cooperative_states = [
        _build_state("car0", "N_S", 1.0, True),
        _build_state("car1", "N_S", 2.0, True),
        _build_state("car2", "W_E", 9.0, False),
    ]

    baseline = baseline_decide(baseline_states)
    cooperative = cooperative_decide(cooperative_states)

    assert baseline == {"car0": "PROCEED", "car1": "WAIT", "car2": "FREE"}
    assert cooperative == {"car0": "PROCEED", "car1": "PROCEED", "car2": "FREE"}


def test_decision_trace_fields_remain_distinct():
    traffic_state = [_build_state("car0", "N_S", 1.0, True)]
    trace = build_decision_trace(
        traffic_state,
        {"car0": "WAIT"},
        {"car0": "WAIT"},
        {"llm_called": True},
    )
    trace = apply_interface_rule(trace, traffic_state, target_field="postprocessed_decision")
    trace = apply_cooperative_postprocessing(trace, traffic_state)

    assert trace["car0"]["llm_raw_decision"] == "WAIT"
    assert trace["car0"]["validated_llm_decision"] == "WAIT"
    assert trace["car0"]["postprocessed_decision"] == "PROCEED"
    assert trace["car0"]["final_decision"] == "WAIT"
