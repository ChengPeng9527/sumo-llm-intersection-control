from __future__ import annotations


LIVE_PROVIDER_NAME = "Groq"
LIVE_BASE_URL = "https://api.groq.com/openai/v1"
LIVE_MODEL = "openai/gpt-oss-20b"

# Frozen for dissertation reproducibility and to avoid hidden truncation/retry behavior.
LIVE_MAX_COMPLETION_TOKENS = 256
LIVE_REASONING_EFFORT = "low"
LIVE_TIMEOUT_SECONDS = 30.0
LIVE_MAX_RETRIES = 0


def build_live_client_kwargs(*, base_url: str, api_key: str) -> dict[str, object]:
    return {
        "base_url": base_url,
        "api_key": api_key,
        "timeout": LIVE_TIMEOUT_SECONDS,
        "max_retries": LIVE_MAX_RETRIES,
    }


def build_live_request_kwargs() -> dict[str, object]:
    return {
        "max_completion_tokens": LIVE_MAX_COMPLETION_TOKENS,
        "reasoning_effort": LIVE_REASONING_EFFORT,
    }

