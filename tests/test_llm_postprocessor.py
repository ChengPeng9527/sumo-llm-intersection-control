from src.controllers.decision_pipeline import apply_safety_filter, build_decision_trace
from src.llm.postprocessor import apply_cooperative_postprocessing, apply_interface_rule


def _build_state(vehicle_id: str, route_id: str, tti: float, inside: bool) -> dict:
    return {
        "vehicle_id": vehicle_id,
        "route_id": route_id,
        "speed": 5.0,
        "distance_to_intersection": 10.0,
        "time_to_intersection": tti,
        "inside_control_zone": inside,
    }


def test_raw_llm_wait_remains_wait_without_promotion():
    traffic_state = [_build_state("car0", "N_S", 2.0, True)]
    trace = build_decision_trace(traffic_state, {"car0": "WAIT"}, {"car0": "WAIT"}, {"llm_called": True})

    assert trace["car0"]["llm_raw_decision"] == "WAIT"
    assert trace["car0"]["validated_llm_decision"] == "WAIT"
    assert trace["car0"]["postprocessed_decision"] == "WAIT"
    assert trace["car0"]["final_decision"] == "WAIT"


def test_raw_llm_does_not_promote_compatible_vehicle():
    traffic_state = [_build_state("car0", "N_S", 2.0, True)]
    trace = build_decision_trace(traffic_state, {"car0": "WAIT"}, {"car0": "WAIT"}, {"llm_called": True})

    assert trace["car0"]["postprocessed_decision"] == "WAIT"
    assert trace["car0"]["decision_source"] == "LLM_RAW"


def test_hybrid_promotes_compatible_wait_vehicle():
    traffic_state = [
        _build_state("car0", "N_S", 1.0, True),
        _build_state("car1", "N_S", 2.0, True),
    ]
    trace = build_decision_trace(
        traffic_state,
        {"car0": "PROCEED", "car1": "WAIT"},
        {"car0": "PROCEED", "car1": "WAIT"},
        {"llm_called": True},
    )
    trace = apply_interface_rule(trace, traffic_state, target_field="postprocessed_decision")
    trace = apply_cooperative_postprocessing(trace, traffic_state)

    assert trace["car1"]["postprocessed_decision"] == "PROCEED"
    assert trace["car1"]["postprocess_applied"] is True
    assert trace["car1"]["decision_source"] == "COOPERATIVE_POSTPROCESSOR"


def test_hybrid_does_not_promote_conflicting_routes():
    traffic_state = [
        _build_state("car0", "N_S", 1.0, True),
        _build_state("car1", "E_W", 2.0, True),
    ]
    trace = build_decision_trace(
        traffic_state,
        {"car0": "PROCEED", "car1": "WAIT"},
        {"car0": "PROCEED", "car1": "WAIT"},
        {"llm_called": True},
    )
    trace = apply_interface_rule(trace, traffic_state, target_field="postprocessed_decision")
    trace = apply_cooperative_postprocessing(trace, traffic_state)

    assert trace["car1"]["postprocessed_decision"] == "WAIT"
    assert trace["car1"]["postprocess_applied"] is False


def test_invalid_llm_action_becomes_wait():
    traffic_state = [_build_state("car0", "N_S", 1.0, True)]
    trace = build_decision_trace(traffic_state, {"car0": "GO"}, {"car0": "WAIT"}, {"llm_called": True})

    assert trace["car0"]["llm_raw_decision"] == "GO"
    assert trace["car0"]["validated_llm_decision"] == "WAIT"


def test_missing_vehicle_decision_becomes_wait():
    traffic_state = [_build_state("car0", "N_S", 1.0, True), _build_state("car1", "E_W", 2.0, True)]
    trace = build_decision_trace(traffic_state, {"car0": "PROCEED"}, {"car0": "PROCEED"}, {"llm_called": True})

    assert trace["car1"]["llm_raw_decision"] == "MISSING"
    assert trace["car1"]["validated_llm_decision"] == "WAIT"


def test_outside_control_zone_free_rule_is_logged_deterministically():
    traffic_state = [_build_state("car0", "N_S", 1.0, False)]
    trace = build_decision_trace(traffic_state, {"car0": "PROCEED"}, {"car0": "PROCEED"}, {"llm_called": True})
    trace = apply_interface_rule(trace, traffic_state, target_field="final_decision")

    assert trace["car0"]["final_decision"] == "FREE"
    assert trace["car0"]["outside_control_zone_rule_applied"] is True
    assert trace["car0"]["decision_source"] == "DETERMINISTIC_INTERFACE_RULE"


def test_four_decision_fields_contain_expected_values():
    traffic_state = [_build_state("car0", "N_S", 1.0, True)]
    trace = build_decision_trace(traffic_state, {"car0": "WAIT"}, {"car0": "WAIT"}, {"llm_called": True})
    trace = apply_interface_rule(trace, traffic_state, target_field="postprocessed_decision")
    trace = apply_cooperative_postprocessing(trace, traffic_state)

    assert trace["car0"]["llm_raw_decision"] == "WAIT"
    assert trace["car0"]["validated_llm_decision"] == "WAIT"
    assert trace["car0"]["postprocessed_decision"] == "PROCEED"
    assert trace["car0"]["final_decision"] == "WAIT"


def test_postprocess_and_safety_override_remain_separate():
    traffic_state = [
        _build_state("car0", "N_S", 1.0, True),
        _build_state("car1", "E_W", 1.2, True),
    ]
    trace = build_decision_trace(
        traffic_state,
        {"car0": "PROCEED", "car1": "PROCEED"},
        {"car0": "PROCEED", "car1": "PROCEED"},
        {"llm_called": True},
    )
    trace = apply_interface_rule(trace, traffic_state, target_field="postprocessed_decision")
    trace = apply_cooperative_postprocessing(trace, traffic_state)
    trace = apply_safety_filter(trace, traffic_state)

    assert trace["car0"]["postprocess_applied"] is False
    assert trace["car0"]["safety_override"] is False
    assert trace["car1"]["postprocess_applied"] is False
    assert trace["car1"]["safety_override"] is True
    assert trace["car1"]["final_decision"] == "WAIT"
