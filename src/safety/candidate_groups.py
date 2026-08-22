from __future__ import annotations

from itertools import combinations
from math import inf

from src.safety.route_conflict import routes_conflict
from src.safety.route_semantics import supported_route_ids


_SUPPORTED_ROUTE_IDS = set(supported_route_ids())


def _route_id_from_state(state: dict) -> str:
    route_id = state.get("route_id", "")
    if isinstance(route_id, str) and route_id.strip():
        normalized = route_id.strip().upper()
        return normalized if normalized in _SUPPORTED_ROUTE_IDS else ""

    incoming_edge = str(state.get("incoming_edge", "")).strip().upper()
    outgoing_edge = str(state.get("outgoing_edge", "")).strip().upper().lstrip("-")
    if incoming_edge and outgoing_edge:
        composed = f"{incoming_edge}_{outgoing_edge}"
        return composed if composed in _SUPPORTED_ROUTE_IDS else ""
    return ""


def _is_relevant_vehicle(state: dict) -> bool:
    return bool(state.get("inside_control_zone")) and bool(state.get("vehicle_id")) and bool(_route_id_from_state(state))


def _vehicle_sort_key(state: dict) -> tuple[float, str]:
    return (float(state.get("time_to_intersection", inf)), str(state.get("vehicle_id", "")))


def _candidate_sort_key(group: list[str]) -> tuple[int, tuple[str, ...]]:
    return (len(group), tuple(group))


def _vehicle_compatible(state_a: dict, state_b: dict) -> bool:
    route_a = _route_id_from_state(state_a)
    route_b = _route_id_from_state(state_b)
    if not route_a or not route_b:
        return False
    return not routes_conflict(route_a, route_b)


def _is_safe_group(group: list[str], state_by_vehicle_id: dict[str, dict]) -> bool:
    for vid_a, vid_b in combinations(group, 2):
        if routes_conflict(
            _route_id_from_state(state_by_vehicle_id[vid_a]),
            _route_id_from_state(state_by_vehicle_id[vid_b]),
        ):
            return False
    return True


def build_safe_candidate_groups(vehicle_states: list[dict]) -> list[list[str]]:
    relevant_states = sorted(
        [state for state in vehicle_states if _is_relevant_vehicle(state)],
        key=_vehicle_sort_key,
    )
    if not relevant_states:
        return []

    state_by_vehicle_id = {state["vehicle_id"]: state for state in relevant_states}
    seen: set[tuple[str, ...]] = set()
    groups: list[list[str]] = []

    def add_group(candidate_group: list[str]) -> None:
        candidate_key = tuple(candidate_group)
        if candidate_key in seen:
            return
        if not _is_safe_group(candidate_group, state_by_vehicle_id):
            return
        seen.add(candidate_key)
        groups.append(candidate_group)

    for state in relevant_states:
        add_group([state["vehicle_id"]])

    for index, seed_state in enumerate(relevant_states):
        candidate_group = [seed_state["vehicle_id"]]
        for other_state in relevant_states[index + 1 :]:
            if all(_vehicle_compatible(state_by_vehicle_id[vid], other_state) for vid in candidate_group):
                candidate_group.append(other_state["vehicle_id"])
        if len(candidate_group) > 1:
            add_group(candidate_group)

    for index, left_state in enumerate(relevant_states):
        for right_state in relevant_states[index + 1 :]:
            if _vehicle_compatible(left_state, right_state):
                add_group([left_state["vehicle_id"], right_state["vehicle_id"]])

    groups.sort(key=_candidate_sort_key)
    return groups
