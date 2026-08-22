from src.experiments.scenario_generator import generate_scenario
from src.safety.route_semantics import describe_route_id, movement_from_edges, supported_route_ids


EXPECTED_ROUTE_IDS = {
    "N_S",
    "N_W",
    "N_E",
    "E_N",
    "E_W",
    "E_S",
    "S_E",
    "S_N",
    "S_W",
    "W_S",
    "W_E",
    "W_N",
}


def test_supported_route_catalog_includes_all_mixed_turn_routes():
    assert set(supported_route_ids()) == EXPECTED_ROUTE_IDS


def test_straight_left_right_mappings_are_deterministic():
    assert describe_route_id("N_S").movement == "STRAIGHT"
    assert describe_route_id("N_W").movement == "RIGHT"
    assert describe_route_id("N_E").movement == "LEFT"
    assert describe_route_id("E_W").movement == "STRAIGHT"
    assert describe_route_id("E_N").movement == "RIGHT"
    assert describe_route_id("E_S").movement == "LEFT"
    assert movement_from_edges("S", "-N") == "STRAIGHT"
    assert movement_from_edges("S", "-E") == "RIGHT"
    assert movement_from_edges("S", "-W") == "LEFT"
    assert movement_from_edges("W", "-E") == "STRAIGHT"
    assert movement_from_edges("W", "-S") == "RIGHT"
    assert movement_from_edges("W", "-N") == "LEFT"


def test_unknown_edge_pair_fails_explicitly():
    try:
        movement_from_edges("N", "-N")
    except ValueError as exc:
        assert "Unsupported movement" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid movement")

    try:
        describe_route_id("N_X")
    except ValueError as exc:
        assert "Unsupported route id" in str(exc) or "Invalid route id" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid route id")


def test_existing_straight_routes_retain_previous_behavior():
    assert describe_route_id("N_S").incoming_edge == "N"
    assert describe_route_id("N_S").outgoing_edge == "-S"
    assert describe_route_id("S_N").movement == "STRAIGHT"
    assert describe_route_id("E_W").movement == "STRAIGHT"
    assert describe_route_id("W_E").movement == "STRAIGHT"


def test_generate_scenario_can_reference_mixed_turn_routes(monkeypatch):
    from src.experiments import scenario_generator

    custom_matrix = {
        "densities": {
            "mixed_smoke": {
                "vehicles_per_hour": 60,
                "simulation_duration_seconds": 240,
                "route_distribution": {
                    "N_W": 0.34,
                    "N_S": 0.33,
                    "N_E": 0.33,
                },
                "minimum_depart_gap": 2,
                "maximum_depart_gap": 4,
            }
        }
    }
    monkeypatch.setattr(scenario_generator, "load_experiment_matrix", lambda: custom_matrix)

    config = generate_scenario("pytest_phase2_mixed_smoke", "mixed_smoke", 7, vehicle_count=3)
    assert config["vehicle_count"] == 3
    assert set(config["route_sequence"]).issubset({"N_W", "N_S", "N_E"})
    assert set(custom_matrix["densities"]["mixed_smoke"]["route_distribution"].keys()).issubset(EXPECTED_ROUTE_IDS)
