from __future__ import annotations

import json


def build_basic_prompt(traffic_state: list[dict]) -> str:
    return (
        "You are a centralized autonomous intersection decision module.\n"
        "Return JSON only with actions PROCEED, WAIT, or FREE.\n\n"
        f"Traffic state:\n{json.dumps(traffic_state, indent=2)}\n"
    )


def build_structured_prompt(traffic_state: list[dict], route_conflicts: dict | None = None) -> str:
    route_conflicts = route_conflicts or {}
    return (
        "You are a centralized autonomous intersection decision module.\n"
        "Use the structured vehicle state and route conflict matrix.\n"
        "Return JSON only.\n\n"
        f"Route conflict matrix:\n{json.dumps(route_conflicts, indent=2)}\n\n"
        f"Traffic state:\n{json.dumps(traffic_state, indent=2)}\n"
    )
