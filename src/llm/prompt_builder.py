from __future__ import annotations

import json


CANONICAL_OUTPUT_CONTRACT = (
    "Output contract:\n"
    'Return exactly one JSON object with this shape:\n'
    '{\n'
    '  "decisions": {\n'
    '    "<vehicle_id>": "PROCEED|WAIT|FREE"\n'
    '  }\n'
    '}\n'
    "Rules:\n"
    "- Use the exact vehicle_id values from Traffic state. Do not invent, rename, duplicate, or omit ids.\n"
    "- Include exactly one decision for every vehicle in Traffic state.\n"
    "- Vehicles outside the control zone must be FREE.\n"
    "- Vehicles inside the control zone must use only PROCEED, WAIT, or FREE.\n"
    "- No markdown, prose, comments, or reasoning.\n"
)

CANDIDATE_SELECTION_OUTPUT_CONTRACT = (
    "Output contract:\n"
    'Return exactly one JSON object with this shape: {"selected_candidate_id":"<candidate_id>"}\n'
    "Use exactly one candidate_id from Candidate groups.\n"
    "Do not invent candidates, vehicle combinations, or safety calculations.\n"
    "No markdown, prose, comments, rationale, or additional keys.\n"
)


def _build_prompt_header() -> str:
    return (
        "You are a centralized autonomous intersection decision module.\n"
        "Follow the canonical output contract exactly.\n"
        f"{CANONICAL_OUTPUT_CONTRACT}\n"
    )


def build_basic_prompt(traffic_state: list[dict]) -> str:
    return (
        f"{_build_prompt_header()}\n"
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
        f"{_build_prompt_header()}\n"
        f"Route conflict matrix:\n{json.dumps(route_conflicts, indent=2)}\n\n"
        f"Policy hints:\n{json.dumps(policy_hints, indent=2)}\n\n"
        f"Traffic state:\n{json.dumps(traffic_state, indent=2)}\n"
    )


def build_candidate_selection_prompt(
    local_traffic_state: list[dict],
    candidate_features: list[dict],
) -> str:
    return (
        "You are a high-level cooperative intersection candidate selector.\n"
        "All supplied candidate groups are already geometrically safe. Select one supplied candidate; do not perform geometry.\n"
        "Consider throughput, aggregate waiting, maximum waiting, arrival timing, and local traffic context.\n"
        f"{CANDIDATE_SELECTION_OUTPUT_CONTRACT}\n"
        f"Local traffic state:\n{json.dumps(local_traffic_state, indent=2, allow_nan=False)}\n\n"
        f"Candidate groups:\n{json.dumps(candidate_features, indent=2, allow_nan=False)}\n"
    )
