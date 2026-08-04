from __future__ import annotations

import json


def build_basic_prompt(traffic_state: list[dict]) -> str:
    return (
        "You are a centralized autonomous intersection decision module.\n"
        "Return JSON only with actions PROCEED, WAIT, or FREE.\n\n"
        f"Traffic state:\n{json.dumps(traffic_state, indent=2)}\n"
    )


def build_structured_prompt(
    traffic_state: list[dict],
    route_conflicts: dict | None = None,
    policy_hints: dict | None = None,
) -> str:
    route_conflicts = route_conflicts or {}
    policy_hints = policy_hints or {}
    return (
        "You are a throughput-biased centralized autonomous intersection decision module.\n"
        "Use the structured vehicle state and route conflict matrix.\n"
        "Safety first, but do not overuse WAIT.\n"
        "Vehicles outside the control zone MUST be FREE.\n"
        "For vehicles inside the control zone, prefer PROCEED when routes are compatible with the priority vehicle.\n"
        "Multiple compatible vehicles may PROCEED together.\n"
        "Use WAIT only for genuine route conflicts or when a vehicle should yield to a conflicting priority flow.\n"
        "Minimize unnecessary waiting while keeping the intersection safe.\n"
        "Return JSON only.\n\n"
        f"Route conflict matrix:\n{json.dumps(route_conflicts, indent=2)}\n\n"
        f"Policy hints:\n{json.dumps(policy_hints, indent=2)}\n\n"
        f"Traffic state:\n{json.dumps(traffic_state, indent=2)}\n"
    )
