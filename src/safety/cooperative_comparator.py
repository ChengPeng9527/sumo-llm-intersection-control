from __future__ import annotations

from dataclasses import dataclass, field
from math import inf
from typing import Iterable


def _as_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_vehicle_ids(vehicle_ids: Iterable[str]) -> tuple[str, ...]:
    return tuple(str(vehicle_id) for vehicle_id in vehicle_ids)


def _candidate_id(vehicle_ids: tuple[str, ...]) -> str:
    return "|".join(vehicle_ids)


@dataclass(frozen=True)
class CandidateScore:
    candidate_id: str
    vehicle_ids: tuple[str, ...]
    size: int
    aggregate_waiting_time: float
    max_waiting_time: float
    minimum_time_to_intersection: float
    sort_key: tuple[float, float, float, float, str]


@dataclass(frozen=True)
class CooperativeSelectionResult:
    selected_candidate_id: str
    selected_vehicle_ids: tuple[str, ...] = field(default_factory=tuple)
    ranked_candidates: tuple[CandidateScore, ...] = field(default_factory=tuple)
    selection_reason: str = ""
    selection_rule: str = "size_desc_aggregate_wait_desc_max_wait_desc_min_tti_asc_candidate_id_asc"

    @property
    def has_selection(self) -> bool:
        return bool(self.selected_candidate_id and self.selected_vehicle_ids)

    def ranking_trace(self) -> tuple[dict, ...]:
        return tuple(
            {
                "rank": index + 1,
                "candidate_id": score.candidate_id,
                "vehicle_ids": score.vehicle_ids,
                "size": score.size,
                "aggregate_waiting_time": score.aggregate_waiting_time,
                "max_waiting_time": score.max_waiting_time,
                "minimum_time_to_intersection": score.minimum_time_to_intersection,
                "sort_key": score.sort_key,
            }
            for index, score in enumerate(self.ranked_candidates)
        )


def _score_candidate_group(vehicle_states: list[dict], candidate_group: Iterable[str]) -> CandidateScore:
    vehicle_ids = _normalize_vehicle_ids(candidate_group)
    state_by_vehicle_id = {state["vehicle_id"]: state for state in vehicle_states}
    waiting_times = [
        max(0.0, _as_float(state_by_vehicle_id[vehicle_id].get("waiting_time", 0.0)))
        for vehicle_id in vehicle_ids
        if vehicle_id in state_by_vehicle_id
    ]
    time_to_intersections = [
        _as_float(state_by_vehicle_id[vehicle_id].get("time_to_intersection", inf), default=inf)
        for vehicle_id in vehicle_ids
        if vehicle_id in state_by_vehicle_id
    ]
    size = len(vehicle_ids)
    aggregate_waiting_time = sum(waiting_times)
    max_waiting_time = max(waiting_times) if waiting_times else 0.0
    minimum_time_to_intersection = min(time_to_intersections) if time_to_intersections else inf
    candidate_id = _candidate_id(vehicle_ids)
    sort_key = (
        -float(size),
        -aggregate_waiting_time,
        -max_waiting_time,
        minimum_time_to_intersection,
        candidate_id,
    )
    return CandidateScore(
        candidate_id=candidate_id,
        vehicle_ids=vehicle_ids,
        size=size,
        aggregate_waiting_time=aggregate_waiting_time,
        max_waiting_time=max_waiting_time,
        minimum_time_to_intersection=minimum_time_to_intersection,
        sort_key=sort_key,
    )


def rank_candidate_groups(vehicle_states: list[dict], candidate_groups: list[list[str]]) -> tuple[CandidateScore, ...]:
    ranked_scores = [_score_candidate_group(vehicle_states, group) for group in candidate_groups]
    ranked_scores.sort(key=lambda score: score.sort_key)
    return tuple(ranked_scores)


def select_candidate_group(
    vehicle_states: list[dict],
    candidate_groups: list[list[str]],
) -> CooperativeSelectionResult:
    ranked_candidates = rank_candidate_groups(vehicle_states, candidate_groups)
    if not ranked_candidates:
        return CooperativeSelectionResult(
            selected_candidate_id="",
            selected_vehicle_ids=(),
            ranked_candidates=(),
            selection_reason="no_candidate_groups",
        )

    selected = ranked_candidates[0]
    selection_reason = (
        "selected_highest_ranked_candidate:"
        f"size={selected.size},"
        f"aggregate_waiting_time={selected.aggregate_waiting_time:.3f},"
        f"max_waiting_time={selected.max_waiting_time:.3f},"
        f"minimum_time_to_intersection={selected.minimum_time_to_intersection:.3f}"
    )
    return CooperativeSelectionResult(
        selected_candidate_id=selected.candidate_id,
        selected_vehicle_ids=selected.vehicle_ids,
        ranked_candidates=ranked_candidates,
        selection_reason=selection_reason,
    )


def build_decisions_from_selection(
    vehicle_states: list[dict],
    selected_vehicle_ids: Iterable[str],
) -> dict[str, str]:
    selected = set(_normalize_vehicle_ids(selected_vehicle_ids))
    decisions: dict[str, str] = {}
    for state in vehicle_states:
        vehicle_id = state["vehicle_id"]
        if not state.get("inside_control_zone"):
            decisions[vehicle_id] = "FREE"
        elif vehicle_id in selected:
            decisions[vehicle_id] = "PROCEED"
        else:
            decisions[vehicle_id] = "WAIT"
    return decisions


def compare_and_build_decisions(
    vehicle_states: list[dict],
    candidate_groups: list[list[str]],
) -> tuple[dict[str, str], CooperativeSelectionResult]:
    result = select_candidate_group(vehicle_states, candidate_groups)
    return build_decisions_from_selection(vehicle_states, result.selected_vehicle_ids), result
