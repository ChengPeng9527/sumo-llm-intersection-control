from __future__ import annotations

import os


LIVE_PROVIDER_NAME = "Groq"
LIVE_BASE_URL = "https://api.groq.com/openai/v1"
LIVE_MODEL = "openai/gpt-oss-20b"

# Frozen for dissertation reproducibility and to avoid hidden truncation/retry behavior.
LIVE_MAX_COMPLETION_TOKENS = 512
LIVE_REASONING_EFFORT = "low"
LIVE_TIMEOUT_SECONDS = 30.0
GEMINI_TIMEOUT_SECONDS = 60.0
LIVE_MAX_RETRIES = 4

LIVE_PROVIDER_MODE = os.getenv("LLM_PROVIDER_MODE", "RESEARCH_FIXED_PROVIDER").strip().upper()
LIVE_REQUESTED_PROVIDER = os.getenv("LLM_REQUESTED_PROVIDER", LIVE_PROVIDER_NAME).strip() or LIVE_PROVIDER_NAME
LIVE_REQUESTED_MODEL = os.getenv("LLM_REQUESTED_MODEL", LIVE_MODEL).strip() or LIVE_MODEL
LIVE_PROVIDER_CHAIN = tuple(part.strip() for part in os.getenv("LLM_PROVIDER_CHAIN", LIVE_PROVIDER_NAME).split(",") if part.strip()) or (LIVE_PROVIDER_NAME,)


def build_live_client_kwargs(*, base_url: str, api_key: str) -> dict[str, object]:
    return {
        "base_url": base_url,
        "api_key": api_key,
        "timeout": LIVE_TIMEOUT_SECONDS,
        "max_retries": LIVE_MAX_RETRIES,
    }


def resolve_provider_timeout(provider_name: str, timeout: float | None = None) -> float:
    if timeout is not None:
        return float(timeout)
    if str(provider_name).strip().lower() == "gemini":
        return GEMINI_TIMEOUT_SECONDS
    return LIVE_TIMEOUT_SECONDS


def build_live_request_kwargs() -> dict[str, object]:
    return {
        "max_completion_tokens": LIVE_MAX_COMPLETION_TOKENS,
        "reasoning_effort": LIVE_REASONING_EFFORT,
        "response_format": {"type": "json_object"},
    }


def _normalize_provider_chain(value: object | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        chain = tuple(str(item).strip() for item in value if str(item).strip())
        return chain or default
    if isinstance(value, str):
        chain = tuple(part.strip() for part in value.split(",") if part.strip())
        return chain or default
    return default



def create_live_client(
    *,
    base_url: str,
    api_key: str,
    timeout: float | None = None,
    max_retries: int | None = None,
    state=None,
    sleep_fn=None,
    monotonic_fn=None,
    opener=None,
    provider_mode: str | None = None,
    requested_provider: str | None = None,
    requested_model: str | None = None,
    provider_chain: tuple[str, ...] | str | None = None,
    provider_models: dict[str, str] | None = None,
    provider_api_keys: dict[str, str] | None = None,
    provider_base_urls: dict[str, str] | None = None,
):
    kwargs: dict[str, object] = {
        "base_url": base_url,
        "api_key": api_key,
        "timeout": timeout if timeout is not None else LIVE_TIMEOUT_SECONDS,
        "max_retries": max_retries if max_retries is not None else LIVE_MAX_RETRIES,
    }
    if state is not None:
        kwargs["state"] = state
    if sleep_fn is not None:
        kwargs["sleep_fn"] = sleep_fn
    if monotonic_fn is not None:
        kwargs["monotonic_fn"] = monotonic_fn

    effective_provider_mode = str(provider_mode or LIVE_PROVIDER_MODE).strip().upper()
    effective_requested_provider = str(requested_provider or LIVE_REQUESTED_PROVIDER).strip() or LIVE_PROVIDER_NAME
    effective_requested_model = str(requested_model or LIVE_REQUESTED_MODEL).strip() or LIVE_MODEL
    effective_provider_chain = _normalize_provider_chain(provider_chain, LIVE_PROVIDER_CHAIN)
    effective_timeout = resolve_provider_timeout(effective_requested_provider, timeout)

    if opener is not None:
        kwargs["opener"] = opener

    use_multi_provider = (
        effective_provider_mode != "RESEARCH_FIXED_PROVIDER"
        or effective_requested_provider != LIVE_PROVIDER_NAME
        or effective_provider_chain != (LIVE_PROVIDER_NAME,)
    )
    if not use_multi_provider:
        kwargs["timeout"] = effective_timeout
        try:
            from src.llm.live_provider_client import create_live_client as _create_live_provider_client

            return _create_live_provider_client(**kwargs)
        except Exception:
            from src.llm.live_provider_sdk_client import create_live_client as _create_live_provider_client

            return _create_live_provider_client(**kwargs)

    from src.llm.provider_architecture import MultiProviderClient

    provider_api_keys = dict(provider_api_keys or {})
    provider_api_keys.setdefault("Groq", api_key)
    provider_api_keys.setdefault("Gemini", os.getenv("GEMINI_API_KEY", ""))
    provider_api_keys.setdefault("OpenRouter", os.getenv("OPENROUTER_API_KEY", ""))
    provider_api_keys.setdefault("Cerebras", os.getenv("CEREBRAS_API_KEY", ""))
    provider_models = dict(provider_models or {})
    provider_models.setdefault("Groq", LIVE_MODEL)
    provider_models.setdefault("Gemini", os.getenv("GEMINI_MODEL", "gemini-3.6-flash"))
    provider_models.setdefault("OpenRouter", os.getenv("OPENROUTER_MODEL", LIVE_MODEL))
    provider_models.setdefault("Cerebras", os.getenv("CEREBRAS_MODEL", "llama-4-scout-17b-16e-instruct"))
    provider_base_urls = dict(provider_base_urls or {})
    provider_base_urls.setdefault("Groq", LIVE_BASE_URL)
    provider_base_urls.setdefault("Gemini", os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"))
    provider_base_urls.setdefault("OpenRouter", os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"))
    provider_base_urls.setdefault("Cerebras", os.getenv("CEREBRAS_BASE_URL", "https://api.cerebras.ai/v1"))
    if timeout is None:
        provider_timeouts = {
            "Groq": LIVE_TIMEOUT_SECONDS,
            "Gemini": GEMINI_TIMEOUT_SECONDS,
            "OpenRouter": LIVE_TIMEOUT_SECONDS,
            "Cerebras": LIVE_TIMEOUT_SECONDS,
        }
    else:
        provider_timeouts = {
            "Groq": float(timeout),
            "Gemini": float(timeout),
            "OpenRouter": float(timeout),
            "Cerebras": float(timeout),
        }
    return MultiProviderClient(
        execution_mode=effective_provider_mode,
        requested_provider=effective_requested_provider,
        requested_model=effective_requested_model,
        provider_chain=effective_provider_chain,
        provider_models=provider_models,
        provider_api_keys=provider_api_keys,
        provider_base_urls=provider_base_urls,
        provider_timeouts=provider_timeouts,
        timeout=effective_timeout,
        max_retries=max_retries if max_retries is not None else LIVE_MAX_RETRIES,
        state=state,
        sleep_fn=sleep_fn or __import__("time").sleep,
        monotonic_fn=monotonic_fn or __import__("time").monotonic,
        opener=opener,
    )
