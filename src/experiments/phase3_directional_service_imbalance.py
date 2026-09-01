"""Preregistered observer and orchestration for the final Q3 extension.

This module defines demand and derives measurements. It does not change the
candidate selector, comparator, grant lifecycle, or safety verifier.
"""
from __future__ import annotations

import csv
import json
import math
import random
import shutil
import statistics
from dataclasses import dataclass
from pathlib import Path

from src.common.config import load_project_config
from src.controllers.candidate_runtime import DETERMINISTIC_CANDIDATE, GEMINI_CANDIDATE
from src.experiments.scenario_generator import (
    CAR_FOLLOWING_SIGMA,
    _initial_demand_signature,
    _write_scenario,
)
from src.safety.route_semantics import supported_route_catalog


EXTENSION_ID = "phase3_directional_service_imbalance"
CONDITION = "DIRECTIONAL_SERVICE_IMBALANCE_STRESS"
SOURCE_SCENARIO = "S3_COOPERATIVE_OPPORTUNITY"
VEHICLE_COUNT = 16
SEEDS = (1, 2, 3)
STAGE1 = "deterministic-feasibility"
STAGE2 = "gemini-evaluation"
DEPARTURE_JITTER_SECONDS = 1
SIMULATION_DURATION_SECONDS = 300
HISTORICAL_S3_MAX_TARGET_AGGREGATE_WAITING = 24.0
MINIMUM_ELIGIBLE_NOT_SELECTED_COUNT = 2
MINIMUM_CONSECUTIVE_NOT_SELECTED_EPOCHS = 2
MINIMUM_PASSING_SEEDS = 2

# The first twelve entries are the frozen S3-12V demand. The final four are
# one fixed R4 reinforcement wave at the existing nine-second S3 spacing.
FIXED_ROUTE_SEQUENCE = (
    "N_W", "E_N", "S_E", "W_S", "N_S", "S_N", "E_S", "W_N",
    "N_W", "E_N", "S_E", "W_S",
    "N_W", "E_N", "S_E", "W_S",
)
FIXED_BASE_DEPARTURES = (0, 0, 1, 1, 3, 3, 5, 5, 9, 9, 10, 10, 18, 18, 19, 19)
TARGET_ROUTE_IDS = frozenset(("N_S", "S_N"))


@dataclass(frozen=True)
class RunSpec:
    condition: str
    seed: int
    planner_mode: str

    @property
    def run_id(self) -> str:
        return f"{EXTENSION_ID}_{self.condition.lower()}_{self.planner_mode.lower()}_seed{self.seed}"


def results_root() -> Path:
    return Path(load_project_config()["results_dir_path"]) / EXTENSION_ID


def build_plan(stage: str) -> tuple[RunSpec, ...]:
    if stage == STAGE1:
        planner = DETERMINISTIC_CANDIDATE
    elif stage == STAGE2:
        planner = GEMINI_CANDIDATE
    else:
        raise ValueError(f"Unknown stage: {stage}")
    return tuple(RunSpec(CONDITION, seed, planner) for seed in SEEDS)


def build_fixed_demand(seed: int) -> tuple[list[str], list[int], list[int]]:
    """Apply the frozen S3 jitter rule to one fixed, non-swept schedule."""
    rnd = random.Random(seed)
    demand: list[tuple[int, int, str]] = []
    last_departure_by_approach: dict[str, int] = {}
    for source_index, (route_id, base_departure) in enumerate(
        zip(FIXED_ROUTE_SEQUENCE, FIXED_BASE_DEPARTURES)
    ):
        departure = base_departure + rnd.randint(0, DEPARTURE_JITTER_SECONDS)
        approach = route_id.split("_", 1)[0]
        previous = last_departure_by_approach.get(approach)
        if previous is not None and departure <= previous:
            departure = previous + 1
        last_departure_by_approach[approach] = departure
        demand.append((departure, source_index, route_id))
    demand.sort(key=lambda item: (item[0], item[1]))
    return (
        [item[2] for item in demand],
        [item[0] for item in demand],
        [item[1] for item in demand],
    )


def prepare_demand(seed: int) -> dict:
    routes, departures, source_indices = build_fixed_demand(seed)
    scenario_id = f"{EXTENSION_ID}_{CONDITION.lower()}_seed{seed}"
    movements = {route.route_id: route.movement for route in supported_route_catalog()}
    generation = _write_scenario(
        scenario_id=scenario_id,
        density_name="phase3_directional_stress",
        seed=seed,
        route_ids=routes,
        departure_times=departures,
        duration=SIMULATION_DURATION_SECONDS,
        vehicles_per_hour=0,
        extra_config={
            "scenario_class": CONDITION,
            "source_scenario": SOURCE_SCENARIO,
            "purpose": "Preregistered directional service-imbalance stress",
            "movement_sequence": [movements[route_id] for route_id in routes],
            "departure_jitter_seconds": DEPARTURE_JITTER_SECONDS,
            "fixed_base_departures": list(FIXED_BASE_DEPARTURES),
            "fixed_source_route_sequence": list(FIXED_ROUTE_SEQUENCE),
            "source_indices_after_departure_sort": source_indices,
            "seed_semantics": {
                "route_assignment_changes": False,
                "departure_timing_changes": True,
                "departure_jitter_seconds": DEPARTURE_JITTER_SECONDS,
                "sumo_car_following_changes": True,
                "sumo_car_following_sigma": CAR_FOLLOWING_SIGMA,
            },
        },
    )
    generation["initial_demand_signature"] = _initial_demand_signature(
        scenario_name=CONDITION,
        seed=seed,
        route_ids=routes,
        departure_times=departures,
    )
    target_indices = [index for index, route_id in enumerate(routes) if route_id in TARGET_ROUTE_IDS]
    generation["target_smaller_vehicle_ids"] = [
        f"{scenario_id}_{seed}_{index}" for index in target_indices
    ]
    generation["source_indices_after_departure_sort"] = source_indices
    scenario_dir = Path(generation["sumocfg_path"]).parent
    (scenario_dir / "generation_config.json").write_text(
        json.dumps(generation, indent=2), encoding="utf-8"
    )
    return generation


def percentile(values: list[float], probability: float) -> float:
    """Hyndman-Fan type 7 linear percentile, matching common array tools."""
    if not values:
        return 0.0
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be between zero and one")
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def waiting_metrics(step_records: list[dict]) -> dict:
    per_vehicle: dict[str, dict] = {}
    for row in step_records:
        vehicle_id = str(row.get("vehicle_id", ""))
        if not vehicle_id:
            continue
        waiting = float(row.get("waiting_time") or 0.0)
        current = per_vehicle.setdefault(
            vehicle_id,
            {"waiting": 0.0, "approach": str(row.get("incoming_edge", "")) or "UNKNOWN"},
        )
        if str(row.get("incoming_edge", "")):
            current["approach"] = str(row["incoming_edge"])
        current["waiting"] = max(float(current["waiting"]), waiting)
    waits = [float(item["waiting"]) for item in per_vehicle.values()]
    by_approach: dict[str, list[float]] = {}
    for item in per_vehicle.values():
        by_approach.setdefault(str(item["approach"]), []).append(float(item["waiting"]))
    approach_means = {
        approach: statistics.fmean(values)
        for approach, values in sorted(by_approach.items())
    }
    return {
        "total_waiting": sum(waits),
        "mean_waiting": statistics.fmean(waits) if waits else 0.0,
        "maximum_vehicle_waiting": max(waits, default=0.0),
        "p95_vehicle_waiting": percentile(waits, 0.95),
        "waiting_sample_sd": statistics.stdev(waits) if len(waits) >= 2 else 0.0,
        "approach_mean_waiting": approach_means,
        "maximum_approach_mean_waiting": max(approach_means.values(), default=0.0),
        "approach_waiting_range": (
            max(approach_means.values()) - min(approach_means.values())
            if approach_means else 0.0
        ),
    }


def _candidate_descriptor(feature: dict) -> dict:
    movements = list(feature.get("movement_summary", []))
    return {
        "candidate_id": str(feature.get("candidate_id", "")),
        "vehicle_ids": [str(value) for value in feature.get("vehicle_ids", [])],
        "group_size": int(feature.get("group_size", len(feature.get("vehicle_ids", [])))),
        "aggregate_waiting_time": float(feature.get("aggregate_waiting_time") or 0.0),
        "maximum_waiting_time": float(feature.get("maximum_waiting_time") or 0.0),
        "minimum_time_to_intersection": feature.get("minimum_time_to_intersection"),
        "movements": [str(item.get("movement", "UNKNOWN")) for item in movements],
        "approaches": [str(item.get("incoming_edge", "")) for item in movements],
    }


def observe_decision(record: dict, target_vehicle_ids: list[str]) -> dict:
    candidates = [_candidate_descriptor(item) for item in record.get("candidate_features", [])]
    target_set = set(target_vehicle_ids)
    target = next(
        (candidate for candidate in candidates if set(candidate["vehicle_ids"]) == target_set),
        None,
    )
    selected = str(record.get("selected_candidate_id", ""))
    target_legal = target is not None
    selected_feature = next((item for item in candidates if item["candidate_id"] == selected), None)
    larger_available = bool(target and any(item["group_size"] > target["group_size"] for item in candidates))
    not_selected = bool(target_legal and larger_available and selected != target["candidate_id"])
    return {
        "decision_epoch": record.get("decision_epoch"),
        "simulation_time": record.get("simulation_time"),
        "candidate_set": candidates,
        "candidate_group_sizes": {item["candidate_id"]: item["group_size"] for item in candidates},
        "candidate_waiting": {
            item["candidate_id"]: {
                "aggregate": item["aggregate_waiting_time"],
                "maximum": item["maximum_waiting_time"],
            }
            for item in candidates
        },
        "candidate_approaches": {item["candidate_id"]: item["approaches"] for item in candidates},
        "candidate_movements": {item["candidate_id"]: item["movements"] for item in candidates},
        "target_candidate_id": target["candidate_id"] if target else "",
        "target_candidate_legal": target_legal,
        "target_candidate_group_size": target["group_size"] if target else None,
        "target_candidate_aggregate_waiting": target["aggregate_waiting_time"] if target else None,
        "target_candidate_maximum_waiting": target["maximum_waiting_time"] if target else None,
        "larger_candidate_available": larger_available,
        "eligible_but_not_selected": not_selected,
        "selected_candidate_id": selected,
        "selected_group_size": selected_feature["group_size"] if selected_feature else None,
        "deterministic_candidate_id": str(record.get("deterministic_candidate_id", "")),
        "gemini_candidate_id": str(record.get("llm_candidate_id", "")),
        "candidate_agreement": record.get("candidate_agreement"),
        "candidate_disagreement": bool(record.get("candidate_disagreement")),
        "provider_request_success": bool(record.get("provider_request_success")),
        "parser_success": bool(record.get("parser_success")),
        "fallback_used": bool(record.get("fallback_used")),
        "latency_ms": record.get("latency_ms"),
        "grant_start_time": record.get("grant_start_time"),
        "grant_end_time": record.get("grant_end_time"),
        "grant_duration_seconds": record.get("grant_duration_seconds"),
        "grant_clearance_reason": record.get("grant_clearance_reason", ""),
    }


def observe_episode(
    decision_records: list[dict],
    summary: dict,
    step_records: list[dict],
    target_vehicle_ids: list[str],
) -> dict:
    epochs: list[dict] = []
    current_streak = 0
    longest_streak = 0
    repeated_count = 0
    for record in decision_records:
        epoch = observe_decision(record, target_vehicle_ids)
        if epoch["eligible_but_not_selected"]:
            current_streak += 1
            repeated_count += 1
        else:
            current_streak = 0
        longest_streak = max(longest_streak, current_streak)
        epoch["eligible_but_not_selected_count_to_date"] = repeated_count
        epoch["eligible_but_not_selected_streak"] = current_streak
        epochs.append(epoch)
    nonservice = [epoch for epoch in epochs if epoch["eligible_but_not_selected"]]
    observation = {
        "run_id": summary.get("run_id", ""),
        "planner": summary.get("planner_mode", ""),
        "target_vehicle_ids": list(target_vehicle_ids),
        "decision_epochs": epochs,
        "target_eligible_epoch_count": sum(epoch["target_candidate_legal"] for epoch in epochs),
        "repeated_eligible_but_not_selected_count": repeated_count,
        "longest_consecutive_eligible_but_not_selected": longest_streak,
        "maximum_target_aggregate_waiting_while_not_selected": max(
            (float(epoch["target_candidate_aggregate_waiting"]) for epoch in nonservice),
            default=0.0,
        ),
        "maximum_target_vehicle_waiting_while_not_selected": max(
            (float(epoch["target_candidate_maximum_waiting"]) for epoch in nonservice),
            default=0.0,
        ),
        "departed": int(summary.get("departed", 0)),
        "arrived": int(summary.get("arrived", summary.get("throughput", 0))),
        "completion_rate": float(summary.get("completion_rate", 0.0)),
        "episode_duration_seconds": float(summary.get("episode_duration_seconds", 0.0)),
        "mean_speed": float(summary.get("mean_speed", 0.0)),
        "collisions": int(summary.get("collision_count", 0)),
        "safety_interventions": int(summary.get("safety_intervention_count", summary.get("safety_override_count", 0))),
        "grant_timeouts": int(summary.get("grant_timeout_count", 0)),
        "llm_valid_decisions": int(summary.get("llm_valid_decisions", 0)),
        "llm_failed_decisions": int(summary.get("llm_failed_decisions", 0)),
        "fallback_decisions": int(summary.get("fallback_decisions", summary.get("fallback_count", 0))),
        "llm_episode_valid": summary.get("llm_episode_valid"),
    }
    observation.update(waiting_metrics(step_records))
    return observation


def stage1_run_passes(observation: dict) -> bool:
    return bool(
        observation.get("departed") == VEHICLE_COUNT
        and observation.get("arrived") == VEHICLE_COUNT
        and observation.get("completion_rate") == 1.0
        and observation.get("collisions") == 0
        and observation.get("safety_interventions") == 0
        and observation.get("grant_timeouts") == 0
        and observation.get("target_eligible_epoch_count", 0) >= MINIMUM_ELIGIBLE_NOT_SELECTED_COUNT
        and observation.get("repeated_eligible_but_not_selected_count", 0) >= MINIMUM_ELIGIBLE_NOT_SELECTED_COUNT
        and observation.get("longest_consecutive_eligible_but_not_selected", 0) >= MINIMUM_CONSECUTIVE_NOT_SELECTED_EPOCHS
        and observation.get("maximum_target_aggregate_waiting_while_not_selected", 0.0)
        > HISTORICAL_S3_MAX_TARGET_AGGREGATE_WAITING
    )


def stage1_feasibility(observations: list[dict]) -> dict:
    rows = [
        {"seed": int(item.get("seed", 0)), "passed": stage1_run_passes(item), "observation": item}
        for item in observations
    ]
    passing = sum(row["passed"] for row in rows)
    return {
        "criterion": {
            "minimum_passing_seeds": MINIMUM_PASSING_SEEDS,
            "required_vehicle_count": VEHICLE_COUNT,
            "minimum_target_eligible_epochs": MINIMUM_ELIGIBLE_NOT_SELECTED_COUNT,
            "minimum_repeated_eligible_but_not_selected_count": MINIMUM_ELIGIBLE_NOT_SELECTED_COUNT,
            "minimum_consecutive_eligible_but_not_selected_epochs": MINIMUM_CONSECUTIVE_NOT_SELECTED_EPOCHS,
            "target_aggregate_waiting_must_exceed_seconds": HISTORICAL_S3_MAX_TARGET_AGGREGATE_WAITING,
            "requires_safe_complete_episode": True,
            "gemini_selection_or_outcome_used": False,
        },
        "runs": rows,
        "passing_seeds": passing,
        "stage1_gate_passed": passing >= MINIMUM_PASSING_SEEDS,
    }


def require_stage2_authorization(stage1_report: dict, explicitly_approved: bool) -> None:
    if not explicitly_approved:
        raise PermissionError("Stage 2 requires new explicit human authorization")
    if not bool(stage1_report.get("stage1_gate_passed")):
        raise RuntimeError("STOP_SUPPLEMENTARY_EXPERIMENTS: Stage 1 feasibility gate failed")


def verify_matched_initial_conditions(stage1_manifest: dict, stage2_manifest: dict) -> None:
    stage1_signatures = {
        int(row["seed"]): row["initial_conditions"]["initial_demand_signature"]
        for row in stage1_manifest.get("runs", [])
        if row.get("status") == "valid"
    }
    for row in stage2_manifest.get("runs", []):
        if "initial_conditions" not in row:
            continue
        seed = int(row["seed"])
        signature = row["initial_conditions"]["initial_demand_signature"]
        if signature != stage1_signatures.get(seed):
            raise RuntimeError(f"matched_initial_demand_signature_mismatch:seed{seed}")


def valid_gemini_observation(observation: dict) -> bool:
    return bool(
        observation.get("llm_valid_decisions", 0) >= 1
        and observation.get("llm_failed_decisions", 0) == 0
        and observation.get("fallback_decisions", 0) == 0
        and observation.get("llm_episode_valid") is True
    )


EFFICIENCY_MATERIAL_TOLERANCES = {
    "total_waiting": 10.0,
    "mean_waiting": 1.0,
    "episode_duration_seconds": 2.0,
}
EFFICIENCY_IMPROVEMENT_TOLERANCES = {
    "total_waiting": 5.0,
    "mean_waiting": 0.5,
    "episode_duration_seconds": 1.0,
}
SERVICE_IMPROVEMENT_TOLERANCE_SECONDS = 1.0
SERVICE_FIELDS = (
    "maximum_vehicle_waiting",
    "p95_vehicle_waiting",
    "maximum_approach_mean_waiting",
    "approach_waiting_range",
)


def _seed_domain_flags(deterministic: dict, gemini: dict) -> dict:
    deltas = {
        field: float(gemini[field]) - float(deterministic[field])
        for field in (*EFFICIENCY_MATERIAL_TOLERANCES, *SERVICE_FIELDS)
    }
    service_improvements = sum(
        deltas[field] <= -SERVICE_IMPROVEMENT_TOLERANCE_SECONDS for field in SERVICE_FIELDS
    )
    service_worsened = any(
        deltas[field] >= SERVICE_IMPROVEMENT_TOLERANCE_SECONDS for field in SERVICE_FIELDS
    )
    efficiency_improvements = sum(
        deltas[field] <= -threshold
        for field, threshold in EFFICIENCY_IMPROVEMENT_TOLERANCES.items()
    )
    material_efficiency_degradation = any(
        deltas[field] >= threshold
        for field, threshold in EFFICIENCY_MATERIAL_TOLERANCES.items()
    )
    deterministic_service_better = sum(
        deltas[field] >= SERVICE_IMPROVEMENT_TOLERANCE_SECONDS for field in SERVICE_FIELDS
    ) >= 3
    deterministic_efficiency_better = sum(
        deltas[field] >= threshold
        for field, threshold in EFFICIENCY_IMPROVEMENT_TOLERANCES.items()
    ) >= 2
    return {
        "deltas_gemini_minus_deterministic": deltas,
        "service_improved": service_improvements >= 3 and not service_worsened,
        "efficiency_improved": efficiency_improvements >= 2 and not material_efficiency_degradation,
        "material_efficiency_degradation": material_efficiency_degradation,
        "deterministic_better": deterministic_service_better or deterministic_efficiency_better,
    }


def classify_benefit(observations: list[dict]) -> dict:
    grouped: dict[int, dict[str, dict]] = {}
    for observation in observations:
        grouped.setdefault(int(observation["seed"]), {})[str(observation["planner"])] = observation
    matched: list[dict] = []
    for seed, pair in sorted(grouped.items()):
        deterministic = pair.get(DETERMINISTIC_CANDIDATE)
        gemini = pair.get(GEMINI_CANDIDATE)
        if not deterministic or not gemini or not valid_gemini_observation(gemini):
            continue
        matched.append({"seed": seed, **_seed_domain_flags(deterministic, gemini)})
    if len(matched) < 2:
        classification = "INCONCLUSIVE"
    else:
        service = sum(row["service_improved"] for row in matched) >= 2
        efficiency = sum(row["efficiency_improved"] for row in matched) >= 2
        degraded = sum(row["material_efficiency_degradation"] for row in matched) >= 2
        deterministic_better = sum(row["deterministic_better"] for row in matched) >= 2
        if service and not degraded:
            classification = "MULTI_DOMAIN_BENEFIT"
        elif service and degraded:
            classification = "SERVICE_DISTRIBUTION_EFFICIENCY_TRADEOFF"
        elif efficiency:
            classification = "EFFICIENCY_ONLY_BENEFIT"
        elif deterministic_better:
            classification = "DETERMINISTIC_BETTER"
        else:
            classification = "NO_OBSERVED_LLM_BENEFIT"
    return {
        "classification": classification,
        "valid_matched_seed_count": len(matched),
        "matched_seeds": matched,
    }


def copy_result_artifacts(result: dict, destination: Path) -> None:
    source = Path(result["artifact_paths"]["run_dir"])
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite directional-stress evidence: {destination}")
    shutil.copytree(source, destination)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_step_records(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_observer_output(target: Path, result: dict, target_vehicle_ids: list[str]) -> dict:
    paths = result["artifact_paths"]
    observation = observe_episode(
        result.get("decision_records") or read_jsonl(Path(paths["decision_records"])),
        result["summary"],
        read_step_records(Path(paths["step_records"])),
        target_vehicle_ids,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(observation, indent=2) + "\n", encoding="utf-8")
    return observation
