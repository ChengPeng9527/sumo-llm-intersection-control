from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from src.llm.diagnostics import build_provider_diagnostics
from src.llm.provider_architecture import (
    GeminiProviderAdapter,
    GroqProviderAdapter,
    MultiProviderClient,
    OpenRouterProviderAdapter,
    ProviderRequestError,
    ProviderResponse,
    build_provider_response,
)


class FakeHTTPResponse:
    def __init__(self, payload: dict[str, object], *, status: int = 200, headers: dict[str, str] | None = None) -> None:
        self.status = status
        self.code = status
        self.headers = headers or {}
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body


class ScriptedOpener:
    def __init__(self, script: list[object]) -> None:
        self.script = list(script)
        self.calls = 0
        self.requests: list[object] = []
        self.timeouts: list[float] = []
        self.bodies: list[dict[str, object]] = []

    def __call__(self, request, timeout):
        self.calls += 1
        self.requests.append(request)
        self.timeouts.append(timeout)
        body = getattr(request, "data", None)
        self.bodies.append(json.loads(body.decode("utf-8")) if body else {})
        if not self.script:
            raise AssertionError("script exhausted")
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class FakeProvider:
    def __init__(self, *, provider_name: str, model_name: str, response: ProviderResponse | None = None, error: Exception | None = None) -> None:
        self.provider_name = provider_name
        self.model_name = model_name
        self.response = response
        self.error = error
        self.calls = 0
        self.state = SimpleNamespace(tag=provider_name)

    def request(self, messages, request_config, request_context):
        self.calls += 1
        if self.error is not None:
            raise self.error
        assert self.response is not None
        response = self.response
        response.request_id = str(request_context.get("request_id", response.request_id))
        response.request_simulation_step = request_context.get("request_simulation_step")
        response.requested_provider = str(request_context.get("requested_provider", response.requested_provider))
        response.requested_model = str(request_context.get("requested_model", response.requested_model))
        response.actual_provider = self.provider_name
        response.actual_model = self.model_name
        response.provider_chain = tuple(request_context.get("provider_chain", response.provider_chain))
        response.provider_switch_count = int(request_context.get("provider_switch_count", response.provider_switch_count))
        response.provider_success = True
        response.success = True
        return response


def _build_success_response(provider_name: str, model_name: str, content: str) -> ProviderResponse:
    return build_provider_response(
        provider_name=provider_name,
        model_name=model_name,
        request_id="req-1",
        http_attempt_id=1,
        success=True,
        status_code=200,
        raw_response={"choices": [{"message": {"content": content}, "finish_reason": "stop"}]},
        parsed_content=content,
        latency_ms=12.3,
        prompt_tokens=11,
        completion_tokens=22,
        total_tokens=33,
        requested_provider=provider_name,
        requested_model=model_name,
        actual_provider=provider_name,
        actual_model=model_name,
        provider_chain=(provider_name,),
        provider_success=True,
        choices=[SimpleNamespace(message=SimpleNamespace(content=content), finish_reason="stop")],
        usage=SimpleNamespace(prompt_tokens=11, completion_tokens=22, total_tokens=33),
        headers={"x-ratelimit-limit-tokens": "8000"},
        finish_reason="stop",
        retry_count=0,
        request_attempt_count=1,
        request_pacing_delay_ms=0.0,
        rate_limit_info={"limit_tokens": 8000},
        request_started_at="2026-08-18T00:00:00.000Z",
        request_finished_at="2026-08-18T00:00:00.010Z",
        request_simulation_step=1,
        response_object_type="SimpleNamespace",
    )


def test_provider_response_interface_exposes_required_fields():
    response = _build_success_response("Groq", "openai/gpt-oss-20b", '{"decisions":{"car0":"PROCEED"}}')

    assert isinstance(response, ProviderResponse)
    assert response.provider_name == "Groq"
    assert response.actual_provider == "Groq"
    assert response.provider_success is True
    assert response.success is True
    assert response.prompt_tokens == 11
    assert response.total_tokens == 33
    assert response.choices[0].message.content


def test_groq_adapter_round_trips_chat_completion_response():
    opener = ScriptedOpener([
        FakeHTTPResponse(
            {
                "id": "chatcmpl-1",
                "object": "chat.completion",
                "created": 1,
                "model": "openai/gpt-oss-20b",
                "choices": [
                    {
                        "message": {"content": '{"decisions":{"car0":"PROCEED"}}'},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 11, "completion_tokens": 22, "total_tokens": 33},
            }
        )
    ])
    adapter = GroqProviderAdapter(
        api_key="test-key",
        model_name="openai/gpt-oss-20b",
        timeout=12.5,
        max_retries=0,
        opener=opener,
    )

    response = adapter.request(
        [{"role": "user", "content": "test"}],
        {"model": "openai/gpt-oss-20b", "max_completion_tokens": 16, "reasoning_effort": "low", "response_format": {"type": "json_object"}},
        {"request_id": "req-1", "request_simulation_step": 1, "prompt_hash": "HASH"},
    )

    assert response.provider_name == "Groq"
    assert response.actual_provider == "Groq"
    assert response.provider_success is True
    assert response.parsed_content == '{"decisions":{"car0":"PROCEED"}}'
    assert response.choices[0].message.content == '{"decisions":{"car0":"PROCEED"}}'
    assert opener.calls == 1


def test_openrouter_adapter_round_trips_chat_completion_response():
    opener = ScriptedOpener([
        FakeHTTPResponse(
            {
                "id": "chatcmpl-2",
                "object": "chat.completion",
                "created": 1,
                "model": "openai/gpt-oss-20b",
                "choices": [
                    {
                        "message": {"content": '{"decisions":{"car0":"WAIT"}}'},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 9, "completion_tokens": 18, "total_tokens": 27},
            }
        )
    ])
    adapter = OpenRouterProviderAdapter(
        api_key="openrouter-key",
        model_name="openai/gpt-oss-20b",
        timeout=12.5,
        max_retries=0,
        opener=opener,
    )

    response = adapter.request(
        [{"role": "user", "content": "test"}],
        {"model": "openai/gpt-oss-20b", "max_completion_tokens": 16, "reasoning_effort": "low", "response_format": {"type": "json_object"}},
        {"request_id": "req-2", "request_simulation_step": 2, "prompt_hash": "HASH2"},
    )

    assert response.provider_name == "OpenRouter"
    assert response.actual_provider == "OpenRouter"
    assert response.provider_success is True
    assert response.parsed_content == '{"decisions":{"car0":"WAIT"}}'
    assert opener.calls == 1


def test_gemini_adapter_rest_round_trips_response():
    opener = ScriptedOpener([
        FakeHTTPResponse(
            {
                "candidates": [
                    {
                        "content": {"parts": [{"text": '{"decisions":{"car0":"PROCEED"}}'}]},
                        "finishReason": "STOP",
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 7,
                    "candidatesTokenCount": 14,
                    "thoughtsTokenCount": 3,
                    "totalTokenCount": 24,
                },
            }
        )
    ])
    adapter = GeminiProviderAdapter(
        api_key="gemini-key",
        model_name="gemini-3.6-flash",
        timeout=12.5,
        max_retries=0,
        opener=opener,
    )

    response = adapter.request(
        [{"role": "user", "content": "test"}],
        {"model": "gemini-3.6-flash", "max_completion_tokens": 16, "response_format": {"type": "json_object"}},
        {"request_id": "req-3", "request_simulation_step": 3, "prompt_hash": "HASH3"},
    )

    assert response.provider_name == "Gemini"
    assert response.actual_provider == "Gemini"
    assert response.provider_success is True
    assert response.parsed_content == '{"decisions":{"car0":"PROCEED"}}'
    assert response.prompt_tokens == 7
    assert response.total_tokens == 24
    assert getattr(response.usage, "thoughts_token_count", None) == 3
    diagnostics = build_provider_diagnostics(provider_name="Gemini", model_name="gemini-3.6-flash", response=response)
    assert diagnostics["thoughts_token_count"] == 3
    assert opener.requests[0].full_url.endswith(":generateContent")
    assert opener.timeouts == [12.5]
    body = opener.bodies[0]
    assert body["generationConfig"]["maxOutputTokens"] == 16
    assert body["generationConfig"]["responseMimeType"] == "application/json"
    assert body["generationConfig"]["responseJsonSchema"] == {
        "type": "object",
        "properties": {
            "decisions": {
                "type": "object",
                "description": "Vehicle-id to decision mapping for every vehicle in the traffic state.",
                "additionalProperties": {
                    "type": "string",
                    "enum": ["PROCEED", "WAIT", "FREE"],
                    "description": "A canonical intersection control decision.",
                },
            }
        },
        "required": ["decisions"],
        "additionalProperties": False,
        "propertyOrdering": ["decisions"],
    }
    assert body["generationConfig"]["thinkingConfig"] == {"thinkingLevel": "minimal"}


def test_gemini_adapter_classifies_timeout_errors_as_timeout():
    opener = ScriptedOpener([TimeoutError("read timed out")])
    adapter = GeminiProviderAdapter(
        api_key="gemini-key",
        model_name="gemini-3.6-flash",
        timeout=60.0,
        max_retries=0,
        opener=opener,
    )

    with pytest.raises(ProviderRequestError) as exc_info:
        adapter.request(
            [{"role": "user", "content": "test"}],
            {"model": "gemini-3.6-flash", "response_format": {"type": "json_object"}},
            {"request_id": "req-timeout", "request_simulation_step": 4, "prompt_hash": "HASH4"},
        )

    error = exc_info.value
    assert error.provider_failure_reason == "TIMEOUT"
    assert error.actual_provider == "Gemini"
    assert error.actual_model == "gemini-3.6-flash"
    assert "timed out" in str(error).lower()
    assert opener.timeouts == [60.0]


def test_research_mode_never_switches_providers():
    groq_error = ProviderRequestError(
        provider_name="Groq",
        model_name="openai/gpt-oss-20b",
        message="boom",
        requested_provider="Groq",
        requested_model="openai/gpt-oss-20b",
        actual_provider="Groq",
        actual_model="openai/gpt-oss-20b",
        provider_chain=("Groq", "Gemini"),
        provider_switch_count=0,
        provider_failure_reason="SERVER_ERROR",
    )
    providers = {
        "Groq": FakeProvider(provider_name="Groq", model_name="openai/gpt-oss-20b", error=groq_error),
        "Gemini": FakeProvider(provider_name="Gemini", model_name="gemini-3.6-flash", response=_build_success_response("Gemini", "gemini-3.6-flash", '{"decisions":{"car0":"PROCEED"}}')),
    }
    client = MultiProviderClient(
        execution_mode="RESEARCH_FIXED_PROVIDER",
        requested_provider="Groq",
        requested_model="openai/gpt-oss-20b",
        provider_chain=("Groq", "Gemini"),
        providers=providers,
    )

    with pytest.raises(ProviderRequestError):
        client.request(
            [{"role": "user", "content": "test"}],
            {"model": "openai/gpt-oss-20b"},
            {"request_id": "req-fixed", "request_simulation_step": 1, "prompt_hash": "HASH"},
        )

    assert providers["Groq"].calls == 1
    assert providers["Gemini"].calls == 0


def test_resilient_mode_switches_from_groq_to_gemini():
    groq_error = ProviderRequestError(
        provider_name="Groq",
        model_name="openai/gpt-oss-20b",
        message="boom",
        requested_provider="Groq",
        requested_model="openai/gpt-oss-20b",
        actual_provider="Groq",
        actual_model="openai/gpt-oss-20b",
        provider_chain=("Groq", "Gemini", "OpenRouter"),
        provider_switch_count=0,
        provider_failure_reason="SERVER_ERROR",
    )
    providers = {
        "Groq": FakeProvider(provider_name="Groq", model_name="openai/gpt-oss-20b", error=groq_error),
        "Gemini": FakeProvider(provider_name="Gemini", model_name="gemini-3.6-flash", response=_build_success_response("Gemini", "gemini-3.6-flash", '{"decisions":{"car0":"PROCEED"}}')),
        "OpenRouter": FakeProvider(provider_name="OpenRouter", model_name="openai/gpt-oss-20b", response=_build_success_response("OpenRouter", "openai/gpt-oss-20b", '{"decisions":{"car0":"WAIT"}}')),
    }
    client = MultiProviderClient(
        execution_mode="RESILIENT_MULTI_PROVIDER",
        requested_provider="Groq",
        requested_model="openai/gpt-oss-20b",
        provider_chain=("Groq", "Gemini", "OpenRouter"),
        providers=providers,
    )

    response = client.request(
        [{"role": "user", "content": "test"}],
        {"model": "openai/gpt-oss-20b"},
        {"request_id": "req-resilient", "request_simulation_step": 2, "prompt_hash": "HASH2"},
    )

    assert response.provider_name == "Gemini"
    assert response.actual_provider == "Gemini"
    assert response.provider_success is True
    assert providers["Groq"].calls == 1
    assert providers["Gemini"].calls == 1
    assert providers["OpenRouter"].calls == 0
    assert response.provider_switch_count == 1


def test_resilient_mode_falls_back_when_all_providers_fail():
    groq_error = ProviderRequestError(
        provider_name="Groq",
        model_name="openai/gpt-oss-20b",
        message="boom",
        requested_provider="Groq",
        requested_model="openai/gpt-oss-20b",
        actual_provider="Groq",
        actual_model="openai/gpt-oss-20b",
        provider_chain=("Groq", "Gemini"),
        provider_switch_count=0,
        provider_failure_reason="SERVER_ERROR",
    )
    gemini_error = ProviderRequestError(
        provider_name="Gemini",
        model_name="gemini-3.6-flash",
        message="boom2",
        requested_provider="Groq",
        requested_model="openai/gpt-oss-20b",
        actual_provider="Gemini",
        actual_model="gemini-3.6-flash",
        provider_chain=("Groq", "Gemini"),
        provider_switch_count=1,
        provider_failure_reason="SERVER_ERROR",
    )
    providers = {
        "Groq": FakeProvider(provider_name="Groq", model_name="openai/gpt-oss-20b", error=groq_error),
        "Gemini": FakeProvider(provider_name="Gemini", model_name="gemini-3.6-flash", error=gemini_error),
    }
    client = MultiProviderClient(
        execution_mode="RESILIENT_MULTI_PROVIDER",
        requested_provider="Groq",
        requested_model="openai/gpt-oss-20b",
        provider_chain=("Groq", "Gemini"),
        providers=providers,
    )

    with pytest.raises(ProviderRequestError):
        client.request(
            [{"role": "user", "content": "test"}],
            {"model": "openai/gpt-oss-20b"},
            {"request_id": "req-fail", "request_simulation_step": 3, "prompt_hash": "HASH3"},
        )

    assert providers["Groq"].calls == 1
    assert providers["Gemini"].calls == 1
