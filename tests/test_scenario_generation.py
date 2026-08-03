from src.experiments.scenario_generator import _route_sequence, generate_scenario


def test_route_sequence_is_deterministic():
    route_distribution = {"N_S": 0.25, "S_N": 0.25, "E_W": 0.25, "W_E": 0.25}
    first = _route_sequence(route_distribution, 12, 7)
    second = _route_sequence(route_distribution, 12, 7)

    assert first == second
    assert len(first) == 12
    assert set(first).issubset(route_distribution.keys())


def test_generate_scenario_records_requested_vehicle_count():
    config = generate_scenario("pytest_low_v8_seed7", "low", 7, vehicle_count=8)

    assert config["vehicle_count"] == 8
    assert config["total_vehicles"] == 8
    assert len(config["route_sequence"]) == 8
    assert config["sumocfg_path"].endswith("simulation.sumocfg")
