from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import fmean
from typing import Callable

from src.llm.candidate_selector import build_candidate_selection_context
from src.llm.postprocessor import apply_interface_rule
from src.safety.candidate_groups import build_safe_candidate_groups
from src.safety.cooperative_comparator import build_decisions_from_selection


DETERMINISTIC_CANDIDATE = "DETERMINISTIC_CANDIDATE"
GEMINI_CANDIDATE = "GEMINI_CANDIDATE"
CANDIDATE_PLANNER_MODES = {DETERMINISTIC_CANDIDATE, GEMINI_CANDIDATE}
DEFAULT_GRANT_TIMEOUT_SECONDS = 45.0


def normalize_candidate_planner_mode(planner_mode: str) -> str:
    normalized = str(planner_mode).strip().upper()
    if normalized not in CANDIDATE_PLANNER_MODES:
        raise ValueError(f"Unsupported candidate planner mode: {planner_mode}")
    return normalized


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


@dataclass(frozen=True)
class PlannerDecision:
    trace: dict[str, dict]
    prompt_hash: str = ""
    request_parameters: dict = field(default_factory=dict)
    provider_default_parameters: tuple[str, ...] = ()


@dataclass
class ActivePassageGrant:
    candidate_id: str
    vehicle_ids: tuple[str, ...]
    start_step: int
    start_time: float
    trace_template: dict
    decision_record: dict


@dataclass(frozen=True)
class GrantUpdate:
    trace: dict[str, dict]
    decision_epoch_started: bool
    grant_started: bool
    grant_ended: bool
    grant_clearance_reason: str = ""


class CandidateGrantController:
    """Persist one selected candidate until every granted vehicle leaves control scope."""

    def __init__(
        self,
        *,
        planner_mode: str,
        planner_fn: Callable[[list[dict], list[list[str]], int, int, float], PlannerDecision | dict[str, dict]],
        safety_guard_fn: Callable[[dict[str, dict], list[dict]], dict[str, dict]],
        run_id: str,
        scenario_id: str,
        vehicle_count: int,
        seed: int,
        grant_timeout_seconds: float = DEFAULT_GRANT_TIMEOUT_SECONDS,
    ) -> None:
        self.planner_mode = normalize_candidate_planner_mode(planner_mode)
        if grant_timeout_seconds <= 0:
            raise ValueError("Grant timeout must be positive")
        self.planner_fn = planner_fn
        self.safety_guard_fn = safety_guard_fn
        self.run_id = run_id
        self.scenario_id = scenario_id
        self.vehicle_count = int(vehicle_count)
        self.seed = int(seed)
        self.grant_timeout_seconds = float(grant_timeout_seconds)
        self.active_grant: ActivePassageGrant | None = None
        self.completed_decision_records: list[dict] = []
        self.decision_epoch_count = 0

    def _clearance_reason(self, vehicle_states: list[dict], simulation_time: float) -> str:
        if self.active_grant is None:
            return ""
        state_by_id = {state["vehicle_id"]: state for state in vehicle_states}
        still_in_scope = [
            vehicle_id
            for vehicle_id in self.active_grant.vehicle_ids
            if vehicle_id in state_by_id and bool(state_by_id[vehicle_id].get("inside_control_zone"))
        ]
        if not still_in_scope:
            return "ALL_GRANTED_VEHICLES_LEFT_CONTROL_SCOPE"
        if simulation_time - self.active_grant.start_time >= self.grant_timeout_seconds:
            return "GRANT_TIMEOUT"
        return ""

    @staticmethod
    def _trace_entry(trace: dict[str, dict]) -> dict:
        return next(iter(trace.values()), {})

    def _build_active_trace(self, vehicle_states: list[dict]) -> dict[str, dict]:
        from src.controllers.decision_pipeline import build_decision_trace

        if self.active_grant is None:
            selected_vehicle_ids: tuple[str, ...] = ()
            meta = {
                "decision_source": "FALLBACK",
                "selection_source": "NO_ACTIVE_GRANT",
                "selected_vehicle_ids": (),
            }
        else:
            selected_vehicle_ids = self.active_grant.vehicle_ids
            meta = dict(self.active_grant.trace_template)

        decisions = build_decisions_from_selection(vehicle_states, selected_vehicle_ids)
        trace = build_decision_trace(vehicle_states, decisions, decisions, llm_meta=meta)
        trace = apply_interface_rule(trace, vehicle_states, target_field="postprocessed_decision")
        for entry in trace.values():
            entry["final_decision"] = entry["postprocessed_decision"]
        return self.safety_guard_fn(trace, vehicle_states)

    def _canonical_record(
        self,
        *,
        vehicle_states: list[dict],
        candidate_groups: list[list[str]],
        decision: PlannerDecision,
        simulation_step: int,
        simulation_time: float,
        request_started_at: str,
        request_finished_at: str,
        planner_wall_latency_ms: float,
    ) -> dict:
        entry = self._trace_entry(decision.trace)
        local_state, candidate_features, _ = build_candidate_selection_context(vehicle_states, candidate_groups)
        return {
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "vehicle_count": self.vehicle_count,
            "seed": self.seed,
            "planner": self.planner_mode,
            "decision_epoch": self.decision_epoch_count,
            "simulation_step": int(simulation_step),
            "simulation_time": float(simulation_time),
            "candidate_set": [
                {"candidate_id": "|".join(group), "vehicle_ids": list(group)}
                for group in candidate_groups
            ],
            "candidate_features": candidate_features,
            "privacy_minimised_vehicle_inputs": local_state,
            "deterministic_candidate_id": entry.get("deterministic_candidate_id", ""),
            "llm_candidate_id": entry.get("llm_candidate_id", ""),
            "candidate_agreement": entry.get("candidate_agreement"),
            "candidate_disagreement": bool(entry.get("candidate_disagreement")),
            "llm_raw_output": entry.get("llm_raw_output", ""),
            "parser_success": bool(entry.get("parser_success")),
            "parser_failure_reason": entry.get("parser_failure_reason", ""),
            "provider_request_attempted": bool(entry.get("provider_request_attempted")),
            "provider_request_success": bool(entry.get("provider_request_success")),
            "provider_failure_reason": entry.get("provider_failure_reason", ""),
            "fallback_used": bool(entry.get("fallback_used")),
            "fallback_reason": entry.get("fallback_reason", ""),
            "selected_candidate_id": entry.get("final_selected_candidate", entry.get("selected_candidate_id", "")),
            "selection_source": entry.get("selection_source", ""),
            "grant_source": entry.get("selection_source", ""),
            "grant_vehicle_ids": list(entry.get("selected_vehicle_ids", ())),
            "grant_start_step": int(simulation_step),
            "grant_start_time": float(simulation_time),
            "grant_end_step": None,
            "grant_end_time": None,
            "grant_duration_seconds": None,
            "grant_clearance_reason": "",
            "safety_interventions_during_grant": 0,
            "executed_actions": [],
            "provider": entry.get("actual_provider", entry.get("provider_name", "")),
            "model": entry.get("actual_model", entry.get("model_name", "")),
            "request_parameters": decision.request_parameters,
            "provider_default_parameters": list(decision.provider_default_parameters),
            "request_started_at": entry.get("request_started_at") or request_started_at,
            "request_finished_at": entry.get("request_finished_at") or request_finished_at,
            "latency_ms": entry.get("latency_ms", planner_wall_latency_ms),
            "planner_wall_latency_ms": round(planner_wall_latency_ms, 2),
            "prompt_tokens": entry.get("prompt_tokens"),
            "completion_tokens": entry.get("completion_tokens"),
            "total_tokens": entry.get("total_tokens"),
            "prompt_hash": entry.get("prompt_hash") or decision.prompt_hash,
            "canonical_prompt_reconstruction_data": {
                "prompt_builder": "build_candidate_selection_prompt",
                "privacy_minimised_vehicle_inputs": local_state,
                "candidate_features": candidate_features,
            },
        }

    def _record_execution(self, trace: dict[str, dict], simulation_step: int, simulation_time: float) -> None:
        if self.active_grant is None:
            return
        intended_actions = {
            vehicle_id: entry.get("postprocessed_decision", "WAIT")
            for vehicle_id, entry in trace.items()
        }
        final_actions = {
            vehicle_id: entry.get("final_decision", "WAIT")
            for vehicle_id, entry in trace.items()
        }
        safety_interventions = sorted(
            vehicle_id
            for vehicle_id, entry in trace.items()
            if entry.get("safety_intervened") or entry.get("safety_override")
        )
        self.active_grant.decision_record["executed_actions"].append(
            {
                "simulation_step": int(simulation_step),
                "simulation_time": float(simulation_time),
                "intended_actions": intended_actions,
                "final_actions": final_actions,
                "safety_intervention_vehicle_ids": safety_interventions,
            }
        )
        self.active_grant.decision_record["safety_interventions_during_grant"] += len(safety_interventions)

    def _finish_active_grant(self, *, simulation_step: int, simulation_time: float, reason: str) -> None:
        if self.active_grant is None:
            return
        record = self.active_grant.decision_record
        record["grant_end_step"] = int(simulation_step)
        record["grant_end_time"] = float(simulation_time)
        record["grant_duration_seconds"] = max(0.0, float(simulation_time) - self.active_grant.start_time)
        record["grant_clearance_reason"] = reason
        self.completed_decision_records.append(record)
        self.active_grant = None

    def update(
        self,
        vehicle_states: list[dict],
        *,
        simulation_step: int,
        simulation_time: float,
    ) -> GrantUpdate:
        clearance_reason = self._clearance_reason(vehicle_states, simulation_time)
        grant_ended = bool(clearance_reason)
        if grant_ended:
            self._finish_active_grant(
                simulation_step=simulation_step,
                simulation_time=simulation_time,
                reason=clearance_reason,
            )

        decision_epoch_started = False
        grant_started = False
        candidate_groups: list[list[str]] = []
        # A timeout deliberately produces one all-WAIT update before replanning.
        if self.active_grant is None and clearance_reason != "GRANT_TIMEOUT":
            candidate_groups = build_safe_candidate_groups(vehicle_states)
            if candidate_groups:
                self.decision_epoch_count += 1
                decision_epoch_started = True
                request_started_at = _utc_now()
                started = time.perf_counter()
                raw_decision = self.planner_fn(
                    vehicle_states,
                    candidate_groups,
                    self.decision_epoch_count,
                    simulation_step,
                    simulation_time,
                )
                planner_wall_latency_ms = (time.perf_counter() - started) * 1000
                request_finished_at = _utc_now()
                decision = raw_decision if isinstance(raw_decision, PlannerDecision) else PlannerDecision(trace=raw_decision)
                entry = self._trace_entry(decision.trace)
                selected_ids = tuple(entry.get("selected_vehicle_ids", ()))
                selected_candidate_id = entry.get("final_selected_candidate", entry.get("selected_candidate_id", ""))
                if selected_candidate_id and selected_ids:
                    record = self._canonical_record(
                        vehicle_states=vehicle_states,
                        candidate_groups=candidate_groups,
                        decision=decision,
                        simulation_step=simulation_step,
                        simulation_time=simulation_time,
                        request_started_at=request_started_at,
                        request_finished_at=request_finished_at,
                        planner_wall_latency_ms=planner_wall_latency_ms,
                    )
                    self.active_grant = ActivePassageGrant(
                        candidate_id=selected_candidate_id,
                        vehicle_ids=selected_ids,
                        start_step=simulation_step,
                        start_time=simulation_time,
                        trace_template=dict(entry),
                        decision_record=record,
                    )
                    trace = decision.trace
                    grant_started = True
                    self._record_execution(trace, simulation_step, simulation_time)
                    return GrantUpdate(
                        trace=trace,
                        decision_epoch_started=True,
                        grant_started=True,
                        grant_ended=grant_ended,
                        grant_clearance_reason=clearance_reason,
                    )

        trace = self._build_active_trace(vehicle_states)
        self._record_execution(trace, simulation_step, simulation_time)
        return GrantUpdate(
            trace=trace,
            decision_epoch_started=decision_epoch_started,
            grant_started=grant_started,
            grant_ended=grant_ended,
            grant_clearance_reason=clearance_reason,
        )

    def finish(self, *, simulation_step: int, simulation_time: float, reason: str = "EPISODE_TERMINATED") -> None:
        self._finish_active_grant(
            simulation_step=simulation_step,
            simulation_time=simulation_time,
            reason=reason,
        )

    @property
    def decision_records(self) -> list[dict]:
        return list(self.completed_decision_records)

    def summary(self) -> dict:
        records = self.completed_decision_records
        durations = [float(record.get("grant_duration_seconds") or 0.0) for record in records]
        latencies = [float(record.get("latency_ms") or 0.0) for record in records]
        request_count = sum(bool(record.get("provider_request_attempted")) for record in records)
        fallback_count = sum(bool(record.get("fallback_used")) for record in records)
        return {
            "planner_mode": self.planner_mode,
            "decision_epoch_count": self.decision_epoch_count,
            "grant_count": len(records),
            "mean_grant_duration_seconds": fmean(durations) if durations else 0.0,
            "maximum_grant_duration_seconds": max(durations, default=0.0),
            "grant_timeout_count": sum(record.get("grant_clearance_reason") == "GRANT_TIMEOUT" for record in records),
            "provider_request_count": request_count,
            "fallback_count": fallback_count,
            "fallback_rate": fallback_count / len(records) if records else 0.0,
            "safety_intervention_count": sum(
                int(record.get("safety_interventions_during_grant", 0)) for record in records
            ),
            "mean_decision_latency_ms": fmean(latencies) if latencies else 0.0,
            "total_prompt_tokens": sum(int(record.get("prompt_tokens") or 0) for record in records),
            "total_completion_tokens": sum(int(record.get("completion_tokens") or 0) for record in records),
            "total_tokens": sum(int(record.get("total_tokens") or 0) for record in records),
        }
