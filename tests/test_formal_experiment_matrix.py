from __future__ import annotations

from collections import defaultdict
from types import SimpleNamespace

import scripts.run_formal_experiment_matrix as formal_runner

from src.experiments.formal_experiment_matrix import (
    FORMAL_BATCH_ORDER,
    FORMAL_CONTROLLER_ORDER_BY_SEED,
    FORMAL_VEHICLE_COUNTS,
    FORMAL_SEEDS,
    build_formal_run_plan,
    formal_results_root,
)
from src.experiments.scenario_generator import generate_scenario



def test_formal_run_plan_covers_24_unique_runs_with_counterbalanced_order():
    plan = build_formal_run_plan()

    assert len(plan) == 24
    assert sorted(FORMAL_SEEDS) == [1, 2, 3]
    assert sorted(FORMAL_VEHICLE_COUNTS) == [4, 8]
    assert len({spec.run_id for spec in plan}) == 24
    assert all(spec.density == "low" for spec in plan)

    batches: dict[str, list] = defaultdict(list)
    for spec in plan:
        batches[spec.batch_id].append(spec)

    assert len(batches) == len(FORMAL_BATCH_ORDER)
    for batch_id, specs in batches.items():
        assert len(specs) == 4
        assert [spec.order_position for spec in specs] == [1, 2, 3, 4]
        seed = specs[0].seed
        expected_order = list(FORMAL_CONTROLLER_ORDER_BY_SEED[seed])
        assert [spec.controller for spec in specs] == expected_order
        assert len({spec.controller for spec in specs}) == 4
        assert {spec.seed for spec in specs} == {specs[0].seed}


def test_formal_run_ids_are_seed_and_vehicle_specific():
    plan = build_formal_run_plan()
    keys = {(spec.controller, spec.vehicle_count, spec.seed) for spec in plan}
    assert len(keys) == 24
    assert {spec.experiment_id for spec in plan} == {"FE01_RULE_BASED", "FE04_RAW_LLM", "FE05_HYBRID", "FE06_HYBRID_SAFETY"}


def test_formal_run_ids_for_live_controllers_include_mode_suffix():
    plan = build_formal_run_plan()
    live_specs = [spec for spec in plan if spec.llm_mode]
    assert live_specs
    assert all(spec.run_id.endswith(f"_{spec.llm_mode}") for spec in live_specs)


def test_merge_runtime_credentials_loads_env_file_without_overwriting_existing_values(tmp_path, monkeypatch):
    codex_env_dir = tmp_path / ".codex"
    codex_env_dir.mkdir()
    (codex_env_dir / ".env").write_text(
        "GROQ_API_KEY=test-groq\nSUMO_HOME=C:/Sumo\nPYTHONPATH=D:/Sumo/src\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(formal_runner.Path, "home", classmethod(lambda cls: tmp_path / "sandbox-home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path / "sandbox-home"))
    monkeypatch.setattr(formal_runner, "PROJECT_ROOT", tmp_path / "repo")

    merged = formal_runner._merge_runtime_credentials({"PYTHONPATH": "existing-path"})

    assert merged["GROQ_API_KEY"] == "test-groq"
    assert merged["SUMO_HOME"] == "C:/Sumo"
    assert merged["PYTHONPATH"] == "existing-path"


def test_formal_env_uses_scenario_specific_horizon_for_4v_and_8v(monkeypatch):
    monkeypatch.delenv("LLM_MODE", raising=False)
    spec4 = SimpleNamespace(experiment_id="FE04_RAW_LLM", seed=1, scenario_id="formal_low_v4_seed1", vehicle_count=4, llm_mode="real")
    spec8 = SimpleNamespace(experiment_id="FE04_RAW_LLM", seed=1, scenario_id="formal_low_v8_seed1", vehicle_count=8, llm_mode="real")
    env4 = formal_runner._build_env(spec4, generate_scenario("formal_low_v4_seed1", "low", 1, vehicle_count=4))
    env8 = formal_runner._build_env(spec8, generate_scenario("formal_low_v8_seed1", "low", 1, vehicle_count=8))

    assert env4["SIMULATION_STEPS"] == "240"
    assert env8["SIMULATION_STEPS"] == "400"


def test_formal_results_root_can_be_redirected(monkeypatch):
    monkeypatch.setenv("FORMAL_RESULTS_ID", "dissertation_formal_v3")

    assert formal_results_root().name == "dissertation_formal_v3"
    assert formal_results_root().parts[-1] == "dissertation_formal_v3"
