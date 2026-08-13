from __future__ import annotations

from pathlib import Path

import common


def test_resolve_llm_api_key_prefers_existing_env(monkeypatch, tmp_path):
    monkeypatch.setenv("GROQ_API_KEY", "env-value")
    codex_env = tmp_path / ".codex" / ".env"
    codex_env.parent.mkdir(parents=True)
    codex_env.write_text("GROQ_API_KEY=file-value\n", encoding="utf-8")
    monkeypatch.setattr(common.Path, "home", classmethod(lambda cls: tmp_path))
    assert common.resolve_llm_api_key() == "env-value"


def test_resolve_llm_api_key_falls_back_to_dotenv(monkeypatch, tmp_path):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_CREDENTIAL_FILE", raising=False)
    monkeypatch.delenv("LLM_CREDENTIAL_FILE", raising=False)
    codex_env = tmp_path / ".codex" / ".env"
    codex_env.parent.mkdir(parents=True)
    codex_env.write_text("GROQ_API_KEY=file-value\n", encoding="utf-8")
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(common.Path, "home", classmethod(lambda cls: tmp_path / "sandbox-home"))
    assert common.resolve_llm_api_key() == "file-value"

