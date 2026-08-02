from src.safety.route_conflict import get_route_ids, validate_conflict_matrix


def test_route_ids_exist():
    route_ids = get_route_ids()
    assert route_ids == ["N_S", "S_N", "E_W", "W_E"]


def test_conflict_matrix_is_valid():
    result = validate_conflict_matrix()
    assert result["valid"] is True
    assert ("N_S", "E_W") in result["conflict_pairs"]
