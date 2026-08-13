from __future__ import annotations

from types import SimpleNamespace

from src.controllers.decision_pipeline import run_live_llm_request
from src.llm.request_config import (
    LIVE_BASE_URL,
    LIVE_MAX_COMPLETION_TOKENS,
    LIVE_MAX_RETRIES,
    LIVE_MODEL,
    LIVE_PROVIDER_NAME,
    LIVE_REASONING_EFFORT,
    LIVE_TIMEOUT_SECONDS,
    build_live_client_kwargs,
    build_live_request_kwargs,
)


def test_live_request_config_constants_are_frozen():
    assert LIVE_PROVIDER_NAME == "Groq"
    assert LIVE_BASE_URL == "https://api.groq.com/openai/v1"
    assert LIVE_MODEL == "openai/gpt-oss-20b"
    assert LIVE_MAX_COMPLETION_TOKENS == 256
    assert LIVE_REASONING_EFFORT == "low"
    assert LIVE_TIMEOUT_SECONDS == 30.0
    assert LIVE_MAX_RETRIES == 0


def test_live_request_config_helpers_return_explicit_shared_kwargs():
    client_kwargs = build_live_client_kwargs(base_url=LIVE_BASE_URL, api_key="redacted")
    request_kwargs = build_live_request_kwargs()

    assert client_kwargs == {
        "base_url": LIVE_BASE_URL,
        "api_key": "redacted",
        "timeout": LIVE_TIMEOUT_SECONDS,
        "max_retries": LIVE_MAX_RETRIES,
    }
    assert request_kwargs == {
        "max_completion_tokens": LIVE_MAX_COMPLETION_TOKENS,
        "reasoning_effort": LIVE_REASONING_EFFORT,
    }
    assert "temperature" not in request_kwargs
    assert "top_p" not in request_kwargs
    assert "seed" not in request_kwargs
    assert "reasoning_format" not in request_kwargs


def test_run_live_llm_request_forwards_shared_budget_to_client():
    captured: dict[str, object] = {}

    class DummyCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(choices=[])

    class DummyClient:
        def __init__(self):
            self.chat = SimpleNamespace(completions=DummyCompletions())

    run_live_llm_request(DummyClient(), llm_model=LIVE_MODEL, prompt="test prompt")

    assert captured["model"] == LIVE_MODEL
    assert captured["messages"] == [{"role": "user", "content": "test prompt"}]
    assert captured["max_completion_tokens"] == LIVE_MAX_COMPLETION_TOKENS
    assert captured["reasoning_effort"] == LIVE_REASONING_EFFORT

