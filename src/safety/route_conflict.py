from __future__ import annotations

from src.safety.route_semantics import describe_route_id, supported_route_ids


OPPOSITE_APPROACH = {
    "N": "S",
    "E": "W",
    "S": "N",
    "W": "E",
}


def _normalize_route_id(route_id: str) -> str:
    if not isinstance(route_id, str):
        raise ValueError(f"Invalid route id: {route_id!r}")
    return route_id.strip().upper()


def _describe(route_id: str):
    return describe_route_id(_normalize_route_id(route_id))


def _is_opposite(incoming_a: str, incoming_b: str) -> bool:
    return OPPOSITE_APPROACH.get(incoming_a) == incoming_b


def _movement_compatible(route_a, route_b) -> bool:
    if route_a.route_id == route_b.route_id:
        return True
    if route_a.incoming_edge == route_b.incoming_edge:
        return False

    if route_a.movement == "RIGHT" and route_b.movement == "RIGHT":
        return True
    if route_a.movement == "STRAIGHT" and route_b.movement == "STRAIGHT":
        return _is_opposite(route_a.incoming_edge, route_b.incoming_edge)
    if route_a.movement == "LEFT" and route_b.movement == "LEFT":
        return _is_opposite(route_a.incoming_edge, route_b.incoming_edge)
    return False


def get_route_ids() -> list[str]:
    return supported_route_ids()


def routes_compatible(route_a: str, route_b: str) -> bool:
    if route_a == route_b:
        return True
    try:
        semantics_a = _describe(route_a)
        semantics_b = _describe(route_b)
    except ValueError:
        return False
    return _movement_compatible(semantics_a, semantics_b)


def routes_conflict(route_a: str, route_b: str) -> bool:
    if route_a == route_b:
        return False
    return not routes_compatible(route_a, route_b)


def validate_conflict_matrix() -> dict:
    route_ids = get_route_ids()
    compatible_pairs: list[tuple[str, str]] = []
    conflict_pairs: list[tuple[str, str]] = []
    missing_pairs: list[tuple[str, str]] = []

    for route_a in route_ids:
        for route_b in route_ids:
            if route_a == route_b:
                continue
            try:
                compatible = routes_compatible(route_a, route_b)
                conflict = routes_conflict(route_a, route_b)
            except ValueError:
                missing_pairs.append((route_a, route_b))
                continue
            if compatible:
                compatible_pairs.append((route_a, route_b))
            elif conflict:
                conflict_pairs.append((route_a, route_b))
            else:
                missing_pairs.append((route_a, route_b))

    return {
        "route_ids": list(route_ids),
        "compatible_pairs": compatible_pairs,
        "conflict_pairs": conflict_pairs,
        "missing_pairs": missing_pairs,
        "valid": not missing_pairs,
    }
