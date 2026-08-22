from __future__ import annotations

import os

from common import CONFIG, get_env_int, get_env_str, resolve_sumo_config_path
from src.controllers.decision_pipeline import run_pipeline_controller


SUMO_BINARY = CONFIG["sumo_gui_binary_path"]
SCENARIO = os.getenv("SCENARIO_ID", "debug_four_vehicle")
SUMO_CONFIG = resolve_sumo_config_path(SCENARIO)
VEHICLE_COUNT = int(os.getenv("VEHICLE_COUNT", "4"))
SEED = get_env_int("SEED", CONFIG["default_seed"])
SIMULATION_STEPS = int(os.getenv("SIMULATION_STEPS", str(CONFIG["default_simulation_duration"])))
EXPERIMENT_ID = get_env_str("EXPERIMENT_ID", "FB_ONLY")


def main() -> int:
    run_pipeline_controller(
        experiment_id=EXPERIMENT_ID,
        controller_name="FallbackOnlyController",
        stage_mode="raw",
        scenario=SCENARIO,
        vehicle_count=VEHICLE_COUNT,
        seed=SEED,
        sumo_binary=SUMO_BINARY,
        sumo_config=SUMO_CONFIG,
        simulation_steps=SIMULATION_STEPS,
        llm_mode="mock",
        llm_decision_interval=1,
        llm_model="",
        llm_base_url="",
        llm_api_key="",
        prompt_version="v2-stage-separated",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
