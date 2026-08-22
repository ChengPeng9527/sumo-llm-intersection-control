from __future__ import annotations

from pathlib import Path

import common


def test_resolve_llm_api_key_prefers_existing_env(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "env-value")
    codex_env = tmp_path / ".codex" / ".env"
    codex_env.parent.mkdir(parents=True)
    codex_env.write_text("GEMINI_API_KEY=file-value\n", encoding="utf-8")
    monkeypatch.setattr(common.Path, "home", classmethod(lambda cls: tmp_path))
    assert common.resolve_llm_api_key() == "env-value"


def test_resolve_sumo_config_path_prefers_generated_scenario_config(monkeypatch, tmp_path):
    scenario_dir = tmp_path / "simulation" / "generated_routes" / "formal_low_v8_seed1"
    scenario_dir.mkdir(parents=True)
    scenario_cfg = scenario_dir / "simulation.sumocfg"
    scenario_cfg.write_text("<configuration />", encoding="utf-8")

    monkeypatch.delenv("SUMO_CONFIG_PATH", raising=False)
    monkeypatch.setattr(common, "PROJECT_ROOT", tmp_path)

    assert common.resolve_sumo_config_path("formal_low_v8_seed1") == scenario_cfg


def test_resolve_llm_api_key_falls_back_to_dotenv(monkeypatch, tmp_path):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_CREDENTIAL_FILE", raising=False)
    monkeypatch.delenv("LLM_CREDENTIAL_FILE", raising=False)
    codex_env = tmp_path / ".codex" / ".env"
    codex_env.parent.mkdir(parents=True)
    codex_env.write_text("GEMINI_API_KEY=file-value\n", encoding="utf-8")
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(common.Path, "home", classmethod(lambda cls: tmp_path / "sandbox-home"))
    assert common.resolve_llm_api_key() == "file-value"
