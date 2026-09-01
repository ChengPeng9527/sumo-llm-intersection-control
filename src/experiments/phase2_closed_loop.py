from __future__ import annotations

from pathlib import Path
from typing import Callable

from src.common.config import load_project_config
from src.controllers.candidate_runtime import DETERMINISTIC_CANDIDATE, GEMINI_CANDIDATE
from src.controllers.decision_pipeline import run_pipeline_controller
from src.experiments.scenario_generator import generate_targeted_scenario
from src.llm.request_config import PHASE2_BASE_URL, PHASE2_MODEL


def prepare_phase2_targeted_demand(
    scenario_class: str,
    *,
    vehicle_count: int,
    seed: int,
) -> dict:
    scenario_id = f"phase2_{scenario_class.lower()}_v{vehicle_count}_seed{seed}"
    return generate_targeted_scenario(
        scenario_id,
        scenario_class,
        seed,
        vehicle_count,
    )


def initial_condition_record(generation: dict) -> dict:
    return {
        "scenario_id": generation["scenario_id"],
        "scenario_class": generation["scenario_class"],
        "vehicle_count": generation["vehicle_count"],
        "seed": generation["seed"],
        "route_sequence": list(generation["route_sequence"]),
        "departure_times": list(generation["departure_times"]),
        "movement_sequence": list(generation["movement_sequence"]),
        "seed_semantics": dict(generation.get("seed_semantics", {})),
        "initial_demand_signature": generation["initial_demand_signature"],
    }


def run_phase2_closed_loop_episode(
    generation: dict,
    *,
    planner_mode: str,
    api_key: str = "",
    candidate_provider_call: Callable[[str], object] | None = None,
    grant_timeout_seconds: float = 45.0,
    max_gemini_requests: int = 0,
    strict_llm_mode: bool = False,
    run_label: str = "step8_smoke",
) -> dict:
    project = load_project_config()
    scenario_class = generation["scenario_class"]
    vehicle_count = int(generation["vehicle_count"])
    seed = int(generation["seed"])
    controller_name = (
        "GeminiCandidateController"
        if planner_mode == GEMINI_CANDIDATE
        else "DeterministicCandidateController"
    )
    result = run_pipeline_controller(
        experiment_id=f"{run_label}_{scenario_class.lower()}",
        controller_name=controller_name,
        stage_mode="hybrid_safety",
        scenario=generation["scenario_id"],
        vehicle_count=vehicle_count,
        seed=seed,
        sumo_binary=Path(project["sumo_binary_path"]),
        sumo_config=Path(generation["sumocfg_path"]),
        simulation_steps=int(generation["simulation_duration_seconds"]),
        llm_mode="real" if planner_mode == GEMINI_CANDIDATE else "mock",
        llm_decision_interval=1,
        llm_model=PHASE2_MODEL,
        llm_base_url=PHASE2_BASE_URL,
        llm_api_key=api_key,
        prompt_version="phase2-candidate-v1",
        candidate_planner_mode=planner_mode,
        grant_timeout_seconds=grant_timeout_seconds,
        candidate_provider_call=candidate_provider_call,
        max_candidate_provider_requests=max_gemini_requests,
        initial_demand_signature=generation["initial_demand_signature"],
        strict_llm_mode=strict_llm_mode,
    )
    result["initial_conditions"] = initial_condition_record(generation)
    return result


def verify_paired_initial_conditions(left: dict, right: dict) -> bool:
    return initial_condition_record(left) == initial_condition_record(right)


def run_deterministic_closed_loop_smoke(
    scenario_class: str = "S3_COOPERATIVE_OPPORTUNITY",
    *,
    vehicle_count: int = 8,
    seed: int = 7,
    grant_timeout_seconds: float = 45.0,
) -> dict:
    generation = prepare_phase2_targeted_demand(
        scenario_class,
        vehicle_count=vehicle_count,
        seed=seed,
    )
    return run_phase2_closed_loop_episode(
        generation,
        planner_mode=DETERMINISTIC_CANDIDATE,
        grant_timeout_seconds=grant_timeout_seconds,
    )
