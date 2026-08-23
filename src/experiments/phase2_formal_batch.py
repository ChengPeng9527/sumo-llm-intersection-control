from __future__ import annotations

import csv
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean

from src.common.config import load_project_config
from src.controllers.candidate_runtime import DETERMINISTIC_CANDIDATE, GEMINI_CANDIDATE
from src.common.metrics import run_artifact_paths
from src.llm.request_config import PHASE2_MODEL, PHASE2_PROVIDER_NAME


FORMAL_BATCH_ID = "batch1_seed1"
FORMAL_RUN_LABEL = "phase2_formal_batch1"
FORMAL_SEED = 1
FORMAL_VEHICLE_COUNT = 8
FORMAL_SCENARIOS = (
    "S1_BALANCED_MIXED_TURN",
    "S3_COOPERATIVE_OPPORTUNITY",
    "S4_FAIRNESS_PRESSURE",
)
FORMAL_PLANNERS = (DETERMINISTIC_CANDIDATE, GEMINI_CANDIDATE)
FORMAL_RESULTS_ROOT = (
    Path(load_project_config()["results_dir_path"])
    / "phase2_formal"
    / FORMAL_BATCH_ID
)

REQUIRED_DECISION_RECORD_FIELDS = {
    "run_id",
    "scenario_id",
    "vehicle_count",
    "seed",
    "planner",
    "decision_epoch",
    "simulation_time",
    "candidate_set",
    "candidate_features",
    "privacy_minimised_vehicle_inputs",
    "deterministic_candidate_id",
    "llm_candidate_id",
    "candidate_agreement",
    "candidate_disagreement",
    "llm_raw_output",
    "parser_success",
    "provider_request_success",
    "fallback_used",
    "fallback_reason",
    "selected_candidate_id",
    "selection_source",
    "grant_vehicle_ids",
    "grant_start_time",
    "grant_end_time",
    "grant_clearance_reason",
    "safety_interventions_during_grant",
    "executed_actions",
    "provider",
    "model",
    "request_parameters",
    "latency_ms",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "prompt_hash",
    "canonical_prompt_reconstruction_data",
}


@dataclass(frozen=True)
class Phase2FormalRunSpec:
    order: int
    scenario_class: str
    vehicle_count: int
    seed: int
    planner_mode: str
    run_id: str

    @property
    def pair_id(self) -> str:
        return f"{self.scenario_class.lower()}_v{self.vehicle_count}_seed{self.seed}"


def formal_run_id(scenario_class: str, vehicle_count: int, seed: int, planner_mode: str) -> str:
    return (
        f"{FORMAL_RUN_LABEL}_{scenario_class.lower()}"
        f"_v{vehicle_count}_seed{seed}_{planner_mode.lower()}"
    )


def build_phase2_formal_batch_plan() -> list[Phase2FormalRunSpec]:
    plan: list[Phase2FormalRunSpec] = []
    order = 1
    for scenario_class in FORMAL_SCENARIOS:
        for planner_mode in FORMAL_PLANNERS:
            plan.append(
                Phase2FormalRunSpec(
                    order=order,
                    scenario_class=scenario_class,
                    vehicle_count=FORMAL_VEHICLE_COUNT,
                    seed=FORMAL_SEED,
                    planner_mode=planner_mode,
                    run_id=formal_run_id(
                        scenario_class,
                        FORMAL_VEHICLE_COUNT,
                        FORMAL_SEED,
                        planner_mode,
                    ),
                )
            )
            order += 1
    return plan


def formal_run_target(spec: Phase2FormalRunSpec) -> Path:
    return FORMAL_RESULTS_ROOT / "runs" / spec.pair_id / spec.run_id


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def copy_formal_run_artifacts(source: Path, target: Path) -> None:
    if target.exists():
        raise FileExistsError(f"Formal target already exists: {target}")
    if not source.is_dir():
        raise FileNotFoundError(f"Raw run artifacts are missing: {source}")
    shutil.copytree(source, target)


def validate_formal_run_result(result: dict, spec: Phase2FormalRunSpec) -> list[str]:
    errors: list[str] = []
    summary = result.get("summary", {})
    initial = result.get("initial_conditions", {})
    records = result.get("decision_records", [])
    artifacts = result.get("artifact_paths", {})

    if result.get("run_id") != spec.run_id:
        errors.append("run_id_mismatch")
    if summary.get("planner_mode") != spec.planner_mode:
        errors.append("planner_mode_mismatch")
    if int(summary.get("departed", -1)) != spec.vehicle_count:
        errors.append("departed_count_mismatch")
    if int(summary.get("arrived", -1)) != spec.vehicle_count:
        errors.append("episode_incomplete")
    if float(summary.get("completion_rate", 0.0)) != 1.0:
        errors.append("completion_rate_not_one")
    if initial.get("scenario_class") != spec.scenario_class:
        errors.append("scenario_class_mismatch")
    if int(initial.get("vehicle_count", -1)) != spec.vehicle_count:
        errors.append("initial_vehicle_count_mismatch")
    if int(initial.get("seed", -1)) != spec.seed:
        errors.append("initial_seed_mismatch")
    if not initial.get("initial_demand_signature"):
        errors.append("missing_initial_demand_signature")
    if int(summary.get("decision_epoch_count", 0)) != len(records):
        errors.append("decision_record_count_mismatch")
    if not records:
        errors.append("missing_decision_records")

    required_artifacts = ("step_records", "run_metadata", "events", "decision_records", "summary")
    for artifact_name in required_artifacts:
        artifact_path = Path(str(artifacts.get(artifact_name, "")))
        if not artifact_path.is_file():
            errors.append(f"missing_artifact:{artifact_name}")

    for index, record in enumerate(records, start=1):
        missing = sorted(REQUIRED_DECISION_RECORD_FIELDS - set(record))
        if missing:
            errors.append(f"decision_{index}_missing_fields:{','.join(missing)}")
        if record.get("run_id") != spec.run_id:
            errors.append(f"decision_{index}_run_id_mismatch")
        if record.get("planner") != spec.planner_mode:
            errors.append(f"decision_{index}_planner_mismatch")
        if not record.get("selected_candidate_id"):
            errors.append(f"decision_{index}_missing_selection")
        if not record.get("executed_actions"):
            errors.append(f"decision_{index}_missing_executed_actions")
        reconstruction = record.get("canonical_prompt_reconstruction_data", {})
        if not reconstruction.get("privacy_minimised_vehicle_inputs"):
            errors.append(f"decision_{index}_missing_reconstruction_state")
        if not reconstruction.get("candidate_features"):
            errors.append(f"decision_{index}_missing_reconstruction_candidates")
        if spec.planner_mode == GEMINI_CANDIDATE:
            if record.get("provider") != PHASE2_PROVIDER_NAME:
                errors.append(f"decision_{index}_provider_mismatch")
            if record.get("model") != PHASE2_MODEL:
                errors.append(f"decision_{index}_model_mismatch")
            if record.get("request_parameters", {}).get("model") != PHASE2_MODEL:
                errors.append(f"decision_{index}_request_model_mismatch")
            if not record.get("prompt_hash"):
                errors.append(f"decision_{index}_missing_prompt_hash")

    return errors


def validate_formal_pair(deterministic: dict, gemini: dict) -> list[str]:
    errors: list[str] = []
    left = deterministic.get("initial_conditions", {})
    right = gemini.get("initial_conditions", {})
    comparable_fields = (
        "scenario_id",
        "scenario_class",
        "vehicle_count",
        "seed",
        "route_sequence",
        "departure_times",
        "movement_sequence",
        "seed_semantics",
        "initial_demand_signature",
    )
    for field in comparable_fields:
        if left.get(field) != right.get(field):
            errors.append(f"paired_initial_condition_mismatch:{field}")
    if deterministic.get("run_id") == gemini.get("run_id"):
        errors.append("paired_runs_not_independent")
    if deterministic.get("artifact_paths", {}).get("run_dir") == gemini.get("artifact_paths", {}).get("run_dir"):
        errors.append("paired_artifact_directory_collision")
    return errors


def summarize_formal_run(result: dict) -> dict:
    summary = result["summary"]
    records = result["decision_records"]
    comparable = [record for record in records if record.get("candidate_agreement") is not None]
    latencies = [float(record.get("latency_ms") or 0.0) for record in records]
    return {
        "run_id": result["run_id"],
        "scenario_class": result["initial_conditions"]["scenario_class"],
        "vehicle_count": result["initial_conditions"]["vehicle_count"],
        "seed": result["initial_conditions"]["seed"],
        "planner": summary["planner_mode"],
        "initial_demand_signature": result["initial_conditions"]["initial_demand_signature"],
        "departed": summary.get("departed", 0),
        "arrived": summary.get("arrived", 0),
        "completion_rate": summary.get("completion_rate", 0.0),
        "throughput": summary.get("throughput", 0),
        "mean_waiting_time": summary.get("mean_waiting_time", 0.0),
        "maximum_waiting_time": summary.get("maximum_waiting_time", 0.0),
        "mean_speed": summary.get("mean_speed", 0.0),
        "episode_duration_seconds": summary.get("episode_duration_seconds", 0.0),
        "collision_count": summary.get("collision_count", 0),
        "decision_epoch_count": summary.get("decision_epoch_count", 0),
        "grant_count": summary.get("grant_count", 0),
        "mean_grant_duration_seconds": summary.get("mean_grant_duration_seconds", 0.0),
        "grant_timeout_count": summary.get("grant_timeout_count", 0),
        "safety_intervention_count": summary.get("safety_intervention_count", 0),
        "gemini_request_count": summary.get("provider_request_count", 0),
        "provider_success_count": sum(bool(record.get("provider_request_success")) for record in records),
        "parser_success_count": sum(bool(record.get("parser_success")) for record in records),
        "fallback_count": summary.get("fallback_count", 0),
        "fallback_rate": summary.get("fallback_rate", 0.0),
        "mean_latency_ms": fmean(latencies) if latencies else 0.0,
        "prompt_tokens": summary.get("total_prompt_tokens", 0),
        "completion_tokens": summary.get("total_completion_tokens", 0),
        "total_tokens": summary.get("total_tokens", 0),
        "agreement_count": sum(record.get("candidate_agreement") is True for record in comparable),
        "disagreement_count": sum(bool(record.get("candidate_disagreement")) for record in comparable),
    }


def build_paired_comparison(run_summaries: list[dict]) -> list[dict]:
    by_pair: dict[tuple[str, int, int], dict[str, dict]] = {}
    for row in run_summaries:
        key = (row["scenario_class"], int(row["vehicle_count"]), int(row["seed"]))
        by_pair.setdefault(key, {})[row["planner"]] = row

    comparisons: list[dict] = []
    for (scenario_class, vehicle_count, seed), planners in by_pair.items():
        deterministic = planners[DETERMINISTIC_CANDIDATE]
        gemini = planners[GEMINI_CANDIDATE]
        comparisons.append(
            {
                "scenario_class": scenario_class,
                "vehicle_count": vehicle_count,
                "seed": seed,
                "initial_demand_signature_match": (
                    deterministic["initial_demand_signature"] == gemini["initial_demand_signature"]
                ),
                "deterministic_run_id": deterministic["run_id"],
                "gemini_run_id": gemini["run_id"],
                "deterministic_completion_rate": deterministic["completion_rate"],
                "gemini_completion_rate": gemini["completion_rate"],
                "completion_rate_delta": gemini["completion_rate"] - deterministic["completion_rate"],
                "deterministic_throughput": deterministic["throughput"],
                "gemini_throughput": gemini["throughput"],
                "throughput_delta": gemini["throughput"] - deterministic["throughput"],
                "deterministic_mean_waiting_time": deterministic["mean_waiting_time"],
                "gemini_mean_waiting_time": gemini["mean_waiting_time"],
                "mean_waiting_time_delta": gemini["mean_waiting_time"] - deterministic["mean_waiting_time"],
                "deterministic_maximum_waiting_time": deterministic["maximum_waiting_time"],
                "gemini_maximum_waiting_time": gemini["maximum_waiting_time"],
                "deterministic_mean_speed": deterministic["mean_speed"],
                "gemini_mean_speed": gemini["mean_speed"],
                "mean_speed_delta": gemini["mean_speed"] - deterministic["mean_speed"],
                "deterministic_episode_duration_seconds": deterministic["episode_duration_seconds"],
                "gemini_episode_duration_seconds": gemini["episode_duration_seconds"],
                "episode_duration_delta_seconds": (
                    gemini["episode_duration_seconds"] - deterministic["episode_duration_seconds"]
                ),
                "deterministic_collision_count": deterministic["collision_count"],
                "gemini_collision_count": gemini["collision_count"],
                "deterministic_safety_interventions": deterministic["safety_intervention_count"],
                "gemini_safety_interventions": gemini["safety_intervention_count"],
                "gemini_fallback_count": gemini["fallback_count"],
                "gemini_request_count": gemini["gemini_request_count"],
                "agreement_count": gemini["agreement_count"],
                "disagreement_count": gemini["disagreement_count"],
                "gemini_total_tokens": gemini["total_tokens"],
            }
        )
    return comparisons


def extract_disagreements(results: list[dict]) -> list[dict]:
    disagreements: list[dict] = []
    for result in results:
        scenario_class = result["initial_conditions"]["scenario_class"]
        for record in result["decision_records"]:
            if not record.get("candidate_disagreement"):
                continue
            local_states = record.get("privacy_minimised_vehicle_inputs", [])
            disagreements.append(
                {
                    "scenario_class": scenario_class,
                    "simulation_time": record.get("simulation_time"),
                    "candidate_set": record.get("candidate_set", []),
                    "deterministic_candidate_id": record.get("deterministic_candidate_id", ""),
                    "gemini_candidate_id": record.get("llm_candidate_id", ""),
                    "candidate_features": record.get("candidate_features", []),
                    "maximum_waiting_time": max(
                        (float(state.get("waiting_time", 0.0)) for state in local_states),
                        default=0.0,
                    ),
                    "safety_interventions": record.get("safety_interventions_during_grant", 0),
                    "grant_clearance_reason": record.get("grant_clearance_reason", ""),
                    "grant_duration_seconds": record.get("grant_duration_seconds"),
                }
            )
    return disagreements
