from src.experiments.scenario_generator import _route_sequence


def test_route_sequence_is_deterministic():
    route_distribution = {"N_S": 0.25, "S_N": 0.25, "E_W": 0.25, "W_E": 0.25}
    first = _route_sequence(route_distribution, 12, 7)
    second = _route_sequence(route_distribution, 12, 7)

    assert first == second
    assert len(first) == 12
    assert set(first).issubset(route_distribution.keys())
