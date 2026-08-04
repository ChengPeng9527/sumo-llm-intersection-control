from src.llm.prompt_builder import build_structured_prompt


def test_structured_prompt_includes_throughput_bias_guidance():
    traffic_state = [
        {
            "vehicle_id": "car0",
            "route_id": "N_S",
            "speed": 3.2,
            "distance_to_intersection": 12.0,
            "time_to_intersection": 4.0,
            "inside_control_zone": True,
        }
    ]
    prompt = build_structured_prompt(
        traffic_state,
        route_conflicts={"valid": True},
        policy_hints={"priority_route_id": "N_S"},
    )

    assert "throughput-biased" in prompt
    assert "do not overuse WAIT" in prompt
    assert "Multiple compatible vehicles may PROCEED together" in prompt
    assert "priority_route_id" in prompt
