from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import subprocess
import time

from src.common.config import load_project_config
from src.common.metrics import run_artifact_paths
from src.llm.request_config import (
    LIVE_BASE_URL,
    LIVE_MODEL,
    LIVE_PROVIDER_NAME,
    LIVE_REASONING_EFFORT,
    LIVE_TIMEOUT_SECONDS,
    LIVE_MAX_COMPLETION_TOKENS,
    LIVE_MAX_RETRIES,
)


PROJECT_ROOT = Path(load_project_config()["project_root"])
FORMAL_RESULTS_ROOT = PROJECT_ROOT / "results" / "formal_experiment" / "dissertation_formal_v1"
FORMAL_PROMPT_IDENTIFIER = "P1_BASELINE"
FORMAL_SCENARIO_DENSITY = "low"
FORMAL_SEEDS = (1, 2, 3)
FORMAL_VEHICLE_COUNTS = (4, 8)
FORMAL_BATCH_ORDER = ((1, 4), (2, 8), (3, 4), (1, 8), (2, 4), (3, 8))
FORMAL_CONTROLLER_ORDER_BY_SEED = {
    1: ("rule_based", "raw_llm", "hybrid", "hybrid_safety"),
    2: ("hybrid", "hybrid_safety", "rule_based", "raw_llm"),
    3: ("hybrid_safety", "rule_based", "raw_llm", "hybrid"),
}
FORMAL_CONTROLLER_SPECS = {
    "rule_based": {
        "experiment_id": "FE01_RULE_BASED",
        "controller_label": "Rule-based",
        "script": PROJECT_ROOT / "baseline_controller.py",
        "llm_mode": "",
        "stage_mode": "rule_based",
    },
    "raw_llm": {
        "experiment_id": "FE04_RAW_LLM",
        "controller_label": "Raw LLM",
        "script": PROJECT_ROOT / "raw_llm_controller.py",
        "llm_mode": "real",
        "stage_mode": "raw",
    },
    "hybrid": {
        "experiment_id": "FE05_HYBRID",
        "controller_label": "Hybrid",
        "script": PROJECT_ROOT / "hybrid_llm_controller.py",
        "llm_mode": "real",
        "stage_mode": "hybrid",
    },
    "hybrid_safety": {
        "experiment_id": "FE06_HYBRID_SAFETY",
        "controller_label": "Hybrid + Safety",
        "script": PROJECT_ROOT / "hybrid_llm_safety_controller.py",
        "llm_mode": "real",
        "stage_mode": "hybrid_safety",
    },
}
FORMAL_REQUEST_CONFIG = {
    "provider": LIVE_PROVIDER_NAME,
    "base_url": LIVE_BASE_URL,
    "model": LIVE_MODEL,
    "max_completion_tokens": LIVE_MAX_COMPLETION_TOKENS,
    "reasoning_effort": LIVE_REASONING_EFFORT,
    "timeout": LIVE_TIMEOUT_SECONDS,
    "max_retries": LIVE_MAX_RETRIES,
}


@dataclass(frozen=True)
class FormalRunSpec:
    batch_id: str
    order_position: int
    controller: str
    controller_label: str
    stage_mode: str
    experiment_id: str
    vehicle_count: int
    seed: int
    scenario_id: str
    run_id: str
    controller_script: Path
    llm_mode: str
    density: str = FORMAL_SCENARIO_DENSITY


def controller_order_for_seed(seed: int) -> tuple[str, ...]:
    if seed not in FORMAL_CONTROLLER_ORDER_BY_SEED:
        raise ValueError(f"Unsupported formal seed: {seed}")
    return FORMAL_CONTROLLER_ORDER_BY_SEED[seed]


def build_formal_run_plan() -> list[FormalRunSpec]:
    plan: list[FormalRunSpec] = []
    for seed, vehicle_count in FORMAL_BATCH_ORDER:
        batch_id = f"seed{seed}_v{vehicle_count}"
        for order_position, controller in enumerate(controller_order_for_seed(seed), start=1):
            spec = FORMAL_CONTROLLER_SPECS[controller]
            run_id = f"{spec['experiment_id']}_v{vehicle_count}_seed{seed}"
            plan.append(
                FormalRunSpec(
                    batch_id=batch_id,
                    order_position=order_position,
                    controller=controller,
                    controller_label=spec["controller_label"],
                    stage_mode=spec["stage_mode"],
                    experiment_id=spec["experiment_id"],
                    vehicle_count=vehicle_count,
                    seed=seed,
                    scenario_id=f"formal_{FORMAL_SCENARIO_DENSITY}_v{vehicle_count}_seed{seed}",
                    run_id=run_id,
                    controller_script=spec["script"],
                    llm_mode=spec["llm_mode"],
                )
            )
    return plan


def formal_run_artifacts(run_id: str) -> dict[str, Path]:
    return run_artifact_paths(run_id)


def formal_run_complete(run_id: str) -> bool:
    artifacts = formal_run_artifacts(run_id)
    return all(artifacts[name].exists() for name in ("step_records", "run_metadata", "events"))


def formal_results_dir(batch_id: str, run_id: str) -> Path:
    return FORMAL_RESULTS_ROOT / "runs" / batch_id / run_id


def _git_output(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    return result.stdout.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def formal_run_target_complete(batch_id: str, run_id: str) -> bool:
    target = formal_results_dir(batch_id, run_id)
    return (target / "step_records.csv").exists() and (target / "run_metadata.json").exists() and (target / "events.jsonl").exists()


def build_formal_manifest_row(spec: FormalRunSpec) -> dict[str, object]:
    prompt_path = PROJECT_ROOT / "results" / "prompt_development" / "canonical_prompt_selection_v1" / "prompt_candidates" / f"{FORMAL_PROMPT_IDENTIFIER}.txt"
    prompt_hash = _sha256(prompt_path) if prompt_path.exists() else ""
    freeze_commit = _git_output("rev-parse", "HEAD")
    tag_candidates = _git_output("tag", "--points-at", freeze_commit).splitlines()
    freeze_tag = tag_candidates[-1] if tag_candidates else ""
    return {
        "freeze_commit": freeze_commit,
        "freeze_tag": freeze_tag,
        "branch": _git_output("branch", "--show-current"),
        "timestamp": time.time(),
        "batch_id": spec.batch_id,
        "order_position": spec.order_position,
        "controller": spec.controller,
        "controller_label": spec.controller_label,
        "stage_mode": spec.stage_mode,
        "experiment_id": spec.experiment_id,
        "vehicle_count": spec.vehicle_count,
        "seed": spec.seed,
        "scenario_id": spec.scenario_id,
        "run_id": spec.run_id,
        "controller_script": str(spec.controller_script),
        "llm_mode": spec.llm_mode,
        "density": spec.density,
        "prompt_identifier": FORMAL_PROMPT_IDENTIFIER,
        "prompt_hash": prompt_hash,
        "request_config": dict(FORMAL_REQUEST_CONFIG),
        "raw_results_path": str(formal_run_artifacts(spec.run_id)["run_dir"]),
        "formal_results_path": str(formal_results_dir(spec.batch_id, spec.run_id)),
    }
