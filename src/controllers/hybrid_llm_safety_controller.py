from __future__ import annotations

import os
from pathlib import Path

from common import CONFIG
from src.controllers.decision_pipeline import run_pipeline_controller


SUMO_BINARY = CONFIG["sumo_gui_binary_path"]
SUMO_CONFIG = Path(os.getenv("SUMO_CONFIG_PATH", str(CONFIG["sumo_config_path"])))
SCENARIO = os.getenv("SCENARIO_ID", "debug_four_vehicle")
VEHICLE_COUNT = int(os.getenv("VEHICLE_COUNT", "4"))
SEED = CONFIG["default_seed"]
SIMULATION_STEPS = int(os.getenv("SIMULATION_STEPS", str(CONFIG["default_simulation_duration"])))
LLM_MODE = os.getenv("LLM_MODE", "mock").strip().lower()
LLM_DECISION_INTERVAL = max(1, int(os.getenv("LLM_DECISION_INTERVAL", "1")))
LLM_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("OPENROUTER_API_KEY", "")
LLM_BASE_URL = os.getenv(
    "LLM_BASE_URL",
    "https://api.groq.com/openai/v1" if os.getenv("GROQ_API_KEY") else "https://openrouter.ai/api/v1",
)
LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "openai/gpt-oss-20b" if os.getenv("GROQ_API_KEY") else "openrouter/free",
)


def main() -> int:
    run_pipeline_controller(
        experiment_id="E06_HYBRID_LLM_SAFETY_4V_S1",
        controller_name="HybridLLMSafetyController",
        stage_mode="hybrid_safety",
        scenario=SCENARIO,
        vehicle_count=VEHICLE_COUNT,
        seed=SEED,
        sumo_binary=SUMO_BINARY,
        sumo_config=SUMO_CONFIG,
        simulation_steps=SIMULATION_STEPS,
        llm_mode=LLM_MODE,
        llm_decision_interval=LLM_DECISION_INTERVAL,
        llm_model=LLM_MODEL,
        llm_base_url=LLM_BASE_URL,
        llm_api_key=LLM_API_KEY,
        prompt_version="v2-stage-separated",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
