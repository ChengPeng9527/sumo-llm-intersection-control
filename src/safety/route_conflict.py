from __future__ import annotations

from pathlib import Path

from src.common.config import load_yaml_config


ROUTE_CONFIG = load_yaml_config("route_conflicts.yaml")
ROUTE_IDS = tuple(ROUTE_CONFIG.get("route_ids", []))
COMPATIBILITY = {tuple(pair) for pair in ROUTE_CONFIG.get("compatibility", [])}
CONFLICTS = {tuple(pair) for pair in ROUTE_CONFIG.get("conflicts", [])}


def get_route_ids() -> list[str]:
    return list(ROUTE_IDS)


def routes_compatible(route_a: str, route_b: str) -> bool:
    if route_a == route_b:
        return True
    return (route_a, route_b) in COMPATIBILITY


def routes_conflict(route_a: str, route_b: str) -> bool:
    if route_a == route_b:
        return False
    if (route_a, route_b) in CONFLICTS:
        return True
    return not routes_compatible(route_a, route_b)


def validate_conflict_matrix() -> dict:
    missing = []
    for a in ROUTE_IDS:
        for b in ROUTE_IDS:
            if a == b:
                continue
            if not routes_conflict(a, b) and not routes_compatible(a, b):
                missing.append((a, b))
    return {
        "route_ids": list(ROUTE_IDS),
        "compatible_pairs": sorted(COMPATIBILITY),
        "conflict_pairs": sorted(CONFLICTS),
        "missing_pairs": missing,
        "valid": not missing,
    }
