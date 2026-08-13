from src.llm.prompt_builder import build_structured_prompt


def test_structured_prompt_matches_canonical_prompt_contract():
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

    assert "centralized autonomous intersection decision module" in prompt
    assert "Follow the canonical output contract exactly." in prompt
    assert '"decisions": {' in prompt
    assert '"<vehicle_id>": "PROCEED|WAIT|FREE"' in prompt
    assert "Use the exact vehicle_id values from Traffic state." in prompt
    assert "Include exactly one decision for every vehicle in Traffic state." in prompt
    assert "Vehicles outside the control zone must be FREE." in prompt
    assert "Route conflict matrix:" in prompt
    assert "Policy hints:" in prompt
    assert "Traffic state:" in prompt
    assert "priority_route_id" in prompt
