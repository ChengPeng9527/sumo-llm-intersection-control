from __future__ import annotations

from types import SimpleNamespace

from src.controllers.decision_pipeline import run_live_llm_request
from src.llm.request_config import (
    LIVE_BASE_URL,
    GEMINI_TIMEOUT_SECONDS,
    LIVE_MAX_COMPLETION_TOKENS,
    LIVE_MAX_RETRIES,
    LIVE_MODEL,
    LIVE_PROVIDER_NAME,
    LIVE_REASONING_EFFORT,
    LIVE_TIMEOUT_SECONDS,
    build_live_client_kwargs,
    build_live_request_kwargs,
    create_live_client,
    resolve_provider_timeout,
)


def test_live_request_config_constants_are_frozen():
    assert LIVE_PROVIDER_NAME == "Groq"
    assert LIVE_BASE_URL == "https://api.groq.com/openai/v1"
    assert LIVE_MODEL == "openai/gpt-oss-20b"
    assert LIVE_MAX_COMPLETION_TOKENS == 512
    assert LIVE_REASONING_EFFORT == "low"
    assert LIVE_TIMEOUT_SECONDS == 30.0
    assert GEMINI_TIMEOUT_SECONDS == 60.0
    assert LIVE_MAX_RETRIES == 4


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
        "response_format": {"type": "json_object"},
    }
    assert "temperature" not in request_kwargs
    assert "top_p" not in request_kwargs
    assert "seed" not in request_kwargs
    assert "reasoning_format" not in request_kwargs


def test_provider_timeout_resolution_is_provider_specific():
    assert resolve_provider_timeout("Groq") == LIVE_TIMEOUT_SECONDS
    assert resolve_provider_timeout("Gemini") == GEMINI_TIMEOUT_SECONDS
    assert resolve_provider_timeout("OpenRouter") == LIVE_TIMEOUT_SECONDS
    assert resolve_provider_timeout("Gemini", 12.5) == 12.5
    assert resolve_provider_timeout("Groq", 12.5) == 12.5


def test_gemini_default_timeout_is_sixty_seconds_in_client_factory():
    client = create_live_client(
        base_url="https://generativelanguage.googleapis.com/v1beta",
        api_key="redacted",
        provider_mode="RESILIENT_MULTI_PROVIDER",
        requested_provider="Gemini",
        requested_model="gemini-3.6-flash",
        provider_chain=("Gemini",),
    )

    gemini_provider = client._build_provider("Gemini")
    assert gemini_provider.timeout == GEMINI_TIMEOUT_SECONDS


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
    assert captured["response_format"] == {"type": "json_object"}

