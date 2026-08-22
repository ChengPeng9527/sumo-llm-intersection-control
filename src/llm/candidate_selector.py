from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Callable

from src.llm.diagnostics import build_provider_diagnostics, redact_sensitive_text
from src.llm.prompt_builder import build_candidate_selection_prompt
from src.llm.response_parser import parse_candidate_selection_response
from src.safety.cooperative_comparator import CandidateScore, rank_candidate_groups, select_candidate_group


def _finite_or_none(value: float) -> float | None:
    return value if math.isfinite(value) else None


def _local_vehicle_state(state: dict) -> dict:
    return {
        "vehicle_id": state["vehicle_id"],
        "incoming_edge": state.get("incoming_edge", ""),
        "outgoing_edge": state.get("outgoing_edge", ""),
        "movement": state.get("movement", "UNKNOWN"),
        "waiting_time": state.get("waiting_time", 0.0),
        "speed": state.get("speed", 0.0),
        "time_to_intersection": _finite_or_none(float(state.get("time_to_intersection", math.inf))),
        "inside_control_zone": bool(state.get("inside_control_zone", False)),
    }


def _candidate_feature(score: CandidateScore, state_by_vehicle_id: dict[str, dict]) -> dict:
    return {
        "candidate_id": score.candidate_id,
        "vehicle_ids": list(score.vehicle_ids),
        "movement_summary": [
            {
                "vehicle_id": vehicle_id,
                "incoming_edge": state_by_vehicle_id[vehicle_id].get("incoming_edge", ""),
                "outgoing_edge": state_by_vehicle_id[vehicle_id].get("outgoing_edge", ""),
                "movement": state_by_vehicle_id[vehicle_id].get("movement", "UNKNOWN"),
            }
            for vehicle_id in score.vehicle_ids
            if vehicle_id in state_by_vehicle_id
        ],
        "group_size": score.size,
        "aggregate_waiting_time": score.aggregate_waiting_time,
        "maximum_waiting_time": score.max_waiting_time,
        "minimum_time_to_intersection": _finite_or_none(score.minimum_time_to_intersection),
    }


def build_candidate_selection_context(
    vehicle_states: list[dict],
    candidate_groups: list[list[str]],
) -> tuple[list[dict], list[dict], tuple[CandidateScore, ...]]:
    ranked_candidates = rank_candidate_groups(vehicle_states, candidate_groups)
    candidate_vehicle_ids = {vehicle_id for group in candidate_groups for vehicle_id in group}
    local_traffic_state = [
        _local_vehicle_state(state)
        for state in vehicle_states
        if state.get("vehicle_id") in candidate_vehicle_ids
    ]
    local_traffic_state.sort(key=lambda state: state["vehicle_id"])
    state_by_vehicle_id = {state["vehicle_id"]: state for state in vehicle_states}
    score_by_vehicle_ids = {score.vehicle_ids: score for score in ranked_candidates}
    candidate_features = [
        _candidate_feature(score_by_vehicle_ids[tuple(group)], state_by_vehicle_id)
        for group in candidate_groups
    ]
    return local_traffic_state, candidate_features, ranked_candidates


def _response_text(response: object) -> str:
    if isinstance(response, str):
        return response
    parsed_content = getattr(response, "parsed_content", None)
    if parsed_content is not None:
        return str(parsed_content)
    choices = getattr(response, "choices", None)
    if choices:
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", None)
        return "" if content is None else str(content)
    content = getattr(response, "content", None)
    return "" if content is None else str(content)


@dataclass(frozen=True)
class LLMCandidateSelectionResult:
    prompt: str
    local_traffic_state: tuple[dict, ...]
    candidate_features: tuple[dict, ...]
    candidate_ranking: tuple[dict, ...]
    llm_raw_output: str
    llm_candidate_id: str
    deterministic_candidate_id: str
    fallback_selected_candidate: str
    final_selected_candidate: str
    selected_vehicle_ids: tuple[str, ...]
    candidate_agreement: bool | None
    candidate_disagreement: bool
    provider_success: bool
    parser_success: bool
    fallback_used: bool
    fallback_reason: str
    selection_source: str
    provider_meta: dict = field(default_factory=dict)


def select_candidate_with_llm(
    vehicle_states: list[dict],
    candidate_groups: list[list[str]],
    provider_call: Callable[[str], object],
    *,
    provider_name: str = "",
    model_name: str = "",
) -> LLMCandidateSelectionResult:
    local_state, candidate_features, ranked_candidates = build_candidate_selection_context(
        vehicle_states,
        candidate_groups,
    )
    prompt = build_candidate_selection_prompt(local_state, candidate_features)
    deterministic = select_candidate_group(vehicle_states, candidate_groups)
    candidate_ids = [candidate["candidate_id"] for candidate in candidate_features]
    group_by_candidate_id = {
        score.candidate_id: score.vehicle_ids
        for score in ranked_candidates
    }
    state_by_vehicle_id = {state["vehicle_id"]: state for state in vehicle_states}

    response = None
    response_text = ""
    exception = None
    parser_success = False
    parser_failure_reason = ""
    llm_candidate_id = ""
    provider_success = False
    start_time = time.perf_counter()
    try:
        response = provider_call(prompt)
        provider_success = response is not None and bool(
            getattr(response, "provider_success", getattr(response, "success", True))
        )
        response_text = _response_text(response)
        if provider_success:
            llm_candidate_id, parser_success, parser_failure_reason = parse_candidate_selection_response(
                response_text,
                candidate_ids,
            )
        else:
            parser_failure_reason = "PROVIDER_FAILURE"
    except Exception as exc:
        exception = exc
        parser_failure_reason = "PROVIDER_FAILURE"
    latency_ms = (time.perf_counter() - start_time) * 1000

    fallback_used = not (provider_success and parser_success)
    fallback_reason = parser_failure_reason if fallback_used else ""
    final_candidate_id = deterministic.selected_candidate_id if fallback_used else llm_candidate_id
    fallback_candidate_id = deterministic.selected_candidate_id if fallback_used else ""
    candidate_agreement = (
        llm_candidate_id == deterministic.selected_candidate_id
        if provider_success and parser_success
        else None
    )
    provider_meta = build_provider_diagnostics(
        provider_name=provider_name,
        model_name=model_name,
        response=response,
        parser_input=response_text,
        parser_success=parser_success,
        parser_action=llm_candidate_id,
        parser_failure_reason=parser_failure_reason,
        fallback_triggered=fallback_used,
        fallback_reason=fallback_reason,
        exception=exception,
        latency_ms=latency_ms,
        provider_request_attempted=True,
        provider_request_success=provider_success,
    )
    return LLMCandidateSelectionResult(
        prompt=prompt,
        local_traffic_state=tuple(local_state),
        candidate_features=tuple(candidate_features),
        candidate_ranking=tuple(
            {
                "rank": index + 1,
                **_candidate_feature(score, state_by_vehicle_id),
            }
            for index, score in enumerate(ranked_candidates)
        ),
        llm_raw_output=redact_sensitive_text(response_text),
        llm_candidate_id=llm_candidate_id,
        deterministic_candidate_id=deterministic.selected_candidate_id,
        fallback_selected_candidate=fallback_candidate_id,
        final_selected_candidate=final_candidate_id,
        selected_vehicle_ids=group_by_candidate_id.get(final_candidate_id, ()),
        candidate_agreement=candidate_agreement,
        candidate_disagreement=candidate_agreement is False,
        provider_success=provider_success,
        parser_success=parser_success,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
        selection_source="DETERMINISTIC_FALLBACK" if fallback_used else "LLM_CANDIDATE",
        provider_meta=provider_meta,
    )


def summarize_candidate_selections(results: list[LLMCandidateSelectionResult]) -> dict[str, float | int]:
    comparable = [result for result in results if result.candidate_agreement is not None]
    agreement_count = sum(result.candidate_agreement is True for result in comparable)
    disagreement_count = sum(result.candidate_disagreement for result in comparable)
    return {
        "comparable_decisions": len(comparable),
        "agreement_count": agreement_count,
        "disagreement_count": disagreement_count,
        "agreement_rate": agreement_count / len(comparable) if comparable else 0.0,
    }
