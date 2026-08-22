from src.safety.route_conflict import get_route_ids, routes_compatible, routes_conflict, validate_conflict_matrix


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


def test_route_ids_exist():
    route_ids = get_route_ids()
    assert set(route_ids) == EXPECTED_ROUTE_IDS


def test_conflict_matrix_is_valid():
    result = validate_conflict_matrix()
    assert result["valid"] is True
    assert ("N_S", "E_W") in result["conflict_pairs"]
    assert ("N_W", "E_N") in result["compatible_pairs"]
    assert ("N_E", "E_S") in result["conflict_pairs"]


def test_mixed_turn_compatibility_rules_are_deterministic():
    assert routes_compatible("N_W", "E_N") is True
    assert routes_compatible("N_W", "S_E") is True
    assert routes_conflict("N_S", "E_W") is True
    assert routes_conflict("N_E", "W_N") is True
