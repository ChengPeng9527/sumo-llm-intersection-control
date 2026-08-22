from __future__ import annotations

import io
import json
import urllib.error
from types import SimpleNamespace

from src.llm.diagnostics import build_provider_diagnostics
from src.llm.live_provider_client import _parse_rate_limit_info
from src.llm.live_provider_client import GroqCompatClient, GroqHTTPError, ProviderReliabilityState, reset_shared_provider_reliability_state
from src.llm.request_config import LIVE_MODEL, LIVE_MAX_RETRIES, LIVE_TIMEOUT_SECONDS, create_live_client


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.slept: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(round(seconds, 6))
        self.now += seconds


class ScriptedOpener:
    def __init__(self, script: list[object]):
        self.script = list(script)
        self.calls = 0

    def __call__(self, request, timeout):
        self.calls += 1
        if not self.script:
            raise AssertionError('script exhausted')
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _make_http_error(status: int, body: str, headers: dict[str, str] | None = None) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url='https://api.groq.com/openai/v1/chat/completions',
        code=status,
        msg=f'HTTP {status}',
        hdrs=headers or {},
        fp=io.BytesIO(body.encode('utf-8')),
    )


def _make_success_response(*, content: str, headers: dict[str, str] | None = None, status: int = 200, usage: dict[str, object] | None = None) -> SimpleNamespace:
    payload = {
        'id': 'chatcmpl-test',
        'object': 'chat.completion',
        'created': 1,
        'model': LIVE_MODEL,
        'choices': [
            {
                'message': {'content': content},
                'finish_reason': 'stop',
            }
        ],
        'usage': usage or {
            'prompt_tokens': 12,
            'completion_tokens': 34,
            'total_tokens': 46,
            'completion_tokens_details': {
                'reasoning_tokens': 5,
                'visible_tokens': 29,
            },
        },
    }
    body = json.dumps(payload).encode('utf-8')
    return SimpleNamespace(status=status, headers=headers or {}, read=lambda: body)


def _make_client(*, script: list[object], state: ProviderReliabilityState | None, clock: FakeClock, max_retries: int = LIVE_MAX_RETRIES) -> GroqCompatClient:
    kwargs = dict(
        base_url='https://api.groq.com/openai/v1',
        api_key='test-key',
        timeout=LIVE_TIMEOUT_SECONDS,
        max_retries=max_retries,
        sleep_fn=clock.sleep,
        monotonic_fn=clock.monotonic,
        opener=ScriptedOpener(script),
    )
    if state is not None:
        kwargs['state'] = state
    return create_live_client(**kwargs)


def test_retry_after_header_is_respected_before_retry():
    clock = FakeClock()
    state = ProviderReliabilityState(tokens_per_minute_limit=100000, request_tokens_estimate=10, retry_jitter_fraction=0.0)
    client = _make_client(
        script=[
            _make_http_error(429, '{"error": {"message": "retry later"}}', {'Retry-After': '2.5'}),
            _make_success_response(content='{"decisions":{"car0":"PROCEED"}}'),
        ],
        state=state,
        clock=clock,
    )

    response = client.chat.completions.create(model=LIVE_MODEL, messages=[{'role': 'user', 'content': 'test'}], **{'max_completion_tokens': 16, 'reasoning_effort': 'low'})

    assert response.retry_count == 1
    assert clock.slept[0] == 2.5


def test_429_retries_until_exhaustion():
    clock = FakeClock()
    state = ProviderReliabilityState(tokens_per_minute_limit=100000, request_tokens_estimate=10, retry_jitter_fraction=0.0)
    client = _make_client(
        script=[
            _make_http_error(429, '{"error": {"message": "rate limit"}}'),
            _make_http_error(429, '{"error": {"message": "rate limit"}}'),
            _make_http_error(429, '{"error": {"message": "rate limit"}}'),
            _make_http_error(429, '{"error": {"message": "rate limit"}}'),
        ],
        state=state,
        clock=clock,
        max_retries=3,
    )

    try:
        client.chat.completions.create(model=LIVE_MODEL, messages=[{'role': 'user', 'content': 'test'}], **{'max_completion_tokens': 16, 'reasoning_effort': 'low'})
        raise AssertionError('expected GroqHTTPError')
    except GroqHTTPError as exc:
        assert exc.status_code == 429
        assert exc.retry_count == 3
        assert len(clock.slept) == 3
        assert clock.slept == [1.0, 2.0, 4.0]


def test_5xx_retries_then_succeeds():
    clock = FakeClock()
    state = ProviderReliabilityState(tokens_per_minute_limit=100000, request_tokens_estimate=10, retry_jitter_fraction=0.0)
    client = _make_client(
        script=[
            _make_http_error(503, '{"error": {"message": "temporary"}}'),
            _make_http_error(502, '{"error": {"message": "temporary"}}'),
            _make_success_response(content='{"decisions":{"car0":"PROCEED"}}'),
        ],
        state=state,
        clock=clock,
    )

    response = client.chat.completions.create(model=LIVE_MODEL, messages=[{'role': 'user', 'content': 'test'}], **{'max_completion_tokens': 16, 'reasoning_effort': 'low'})

    assert response.retry_count == 2
    assert clock.slept == [1.0, 2.0]


def test_permanent_4xx_does_not_retry():
    clock = FakeClock()
    state = ProviderReliabilityState(tokens_per_minute_limit=100000, request_tokens_estimate=10, retry_jitter_fraction=0.0)
    client = _make_client(
        script=[_make_http_error(422, '{"error": {"message": "invalid request"}}')],
        state=state,
        clock=clock,
    )

    try:
        client.chat.completions.create(model=LIVE_MODEL, messages=[{'role': 'user', 'content': 'test'}], **{'max_completion_tokens': 16, 'reasoning_effort': 'low'})
        raise AssertionError('expected GroqHTTPError')
    except GroqHTTPError as exc:
        assert exc.status_code == 422
        assert exc.retry_count == 0
        assert clock.slept == []


def test_tpm_budget_does_not_over_pace_sequential_requests():
    clock = FakeClock()
    state = ProviderReliabilityState(
        tokens_per_minute_limit=8000,
        requests_per_minute_limit=30,
        request_tokens_estimate=768,
        safety_margin=0.9,
        retry_jitter_fraction=0.0,
    )
    client = _make_client(
        script=[
            _make_success_response(content='{"decisions":{"car0":"PROCEED"}}', headers={
                'x-ratelimit-limit-tokens': '8000',
                'x-ratelimit-remaining-tokens': '6682',
                'x-ratelimit-limit-requests': '1000',
            }),
            _make_success_response(content='{"decisions":{"car0":"WAIT"}}', headers={
                'x-ratelimit-limit-tokens': '8000',
                'x-ratelimit-remaining-tokens': '6580',
                'x-ratelimit-limit-requests': '1000',
            }),
        ],
        state=state,
        clock=clock,
    )

    first = client.chat.completions.create(model=LIVE_MODEL, messages=[{'role': 'user', 'content': 'test'}], **{'max_completion_tokens': 16, 'reasoning_effort': 'low'})
    second = client.chat.completions.create(model=LIVE_MODEL, messages=[{'role': 'user', 'content': 'test'}], **{'max_completion_tokens': 16, 'reasoning_effort': 'low'})

    assert first.retry_count == 0
    assert second.retry_count == 0
    assert state.requests_per_minute_limit == 30
    assert state.last_provider_limit_requests == 1000
    assert state.last_provider_limit_tokens == 8000
    assert clock.slept == []
    assert second.request_pacing_delay_seconds == 0.0

def test_shared_rate_limiter_is_process_wide_across_clients():
    reset_shared_provider_reliability_state()
    clock = FakeClock()
    client1 = _make_client(
        script=[_make_success_response(content='{"decisions":{"car0":"PROCEED"}}', headers={'x-ratelimit-limit-tokens': '600', 'x-ratelimit-remaining-tokens': '480'})],
        state=None,
        clock=clock,
    )
    client2 = _make_client(
        script=[_make_success_response(content='{"decisions":{"car0":"WAIT"}}', headers={'x-ratelimit-limit-tokens': '600', 'x-ratelimit-remaining-tokens': '420'})],
        state=None,
        clock=clock,
    )

    assert client1.state is client2.state
    client1.state.tokens_per_minute_limit = 600
    client1.state.request_tokens_estimate = 60
    client1.state.retry_jitter_fraction = 0.0

    first = client1.chat.completions.create(model=LIVE_MODEL, messages=[{'role': 'user', 'content': 'test'}], **{'max_completion_tokens': 16, 'reasoning_effort': 'low'})
    second = client2.chat.completions.create(model=LIVE_MODEL, messages=[{'role': 'user', 'content': 'test'}], **{'max_completion_tokens': 16, 'reasoning_effort': 'low'})

    assert first.request_id
    assert second.request_id
    assert clock.slept == []
    assert second.request_pacing_delay_seconds == 0.0


def test_limiter_trace_two_request_sequence_has_no_long_wait():
    clock = FakeClock()
    state = ProviderReliabilityState(
        tokens_per_minute_limit=8000,
        requests_per_minute_limit=30,
        request_tokens_estimate=768,
        safety_margin=0.9,
        retry_jitter_fraction=0.0,
    )

    wait1, reservation1, trace1 = state.acquire_request_slot(now=clock.monotonic(), sleep_fn=clock.sleep, estimated_tokens=768, request_id='req1', trace=True)
    state.finalize_request(reservation1, finished_at=0.1, actual_tokens=893, headers={'x-ratelimit-limit-tokens': '8000', 'x-ratelimit-remaining-tokens': '6682', 'x-ratelimit-limit-requests': '1000'})
    wait2, reservation2, trace2 = state.acquire_request_slot(now=0.1, sleep_fn=clock.sleep, estimated_tokens=768, request_id='req2', trace=True)

    assert wait1 == 0.0
    assert wait2 == 0.0
    assert clock.slept == []
    assert trace1['calculated_token_wait'] == 0.0
    assert trace1['calculated_request_wait'] == 0.0
    assert trace2['calculated_token_wait'] == 0.0
    assert trace2['calculated_request_wait'] == 0.0
    assert trace2['local_estimated_used_tokens'] == 893.0
    assert trace2['local_available_tokens'] == 6307.0
    assert reservation1['request_id'] == 'req1'
    assert reservation2['request_id'] == 'req2'


def test_build_provider_diagnostics_includes_retry_metadata():
    response = SimpleNamespace(
        status_code=200,
        headers={'x-ratelimit-limit-tokens': '8000', 'x-ratelimit-remaining-tokens': '7200'},
        choices=[SimpleNamespace(message=SimpleNamespace(content='{"decisions":{"car0":"PROCEED"}}'), finish_reason='stop')],
        usage=SimpleNamespace(
            prompt_tokens=12,
            completion_tokens=34,
            total_tokens=46,
            completion_tokens_details=SimpleNamespace(reasoning_tokens=5, visible_tokens=29),
        ),
        retry_count=2,
        request_id='run_step001',
        request_simulation_step=12,
        http_attempt_id=3,
        prompt_hash='ABC123',
        request_started_at='2026-08-17T10:00:00.000+00:00',
        request_finished_at='2026-08-17T10:00:01.000+00:00',
        request_attempt_count=3,
        request_pacing_delay_ms=6000.0,
        rate_limit_info={
            'retry_after_seconds': 1.5,
            'limit_tokens': 8000,
            'remaining_tokens': 7200,
            'reset_tokens_seconds': 30.0,
            'limit_requests': 30,
            'remaining_requests': 28,
            'reset_requests_seconds': 20.0,
        },
    )

    diagnostics = build_provider_diagnostics(
        provider_name='Groq',
        model_name=LIVE_MODEL,
        response=response,
        parser_input='{"decisions":{"car0":"PROCEED"}}',
        parser_success=True,
        parser_action='PROCEED',
        fallback_triggered=False,
        latency_ms=12.345,
        provider_request_attempted=True,
        provider_request_success=True,
    )

    assert diagnostics['retry_count'] == 2
    assert diagnostics['request_id'] == 'run_step001'
    assert diagnostics['request_simulation_step'] == 12
    assert diagnostics['http_attempt_id'] == 3
    assert diagnostics['prompt_hash'] == 'ABC123'
    assert diagnostics['request_started_at'] == '2026-08-17T10:00:00.000+00:00'
    assert diagnostics['request_finished_at'] == '2026-08-17T10:00:01.000+00:00'
    assert diagnostics['request_attempt_count'] == 3
    assert diagnostics['request_pacing_delay_ms'] == 6000.0
    assert diagnostics['retry_after_seconds'] == 1.5
    assert diagnostics['rate_limit_limit_tokens'] == 8000
    assert diagnostics['rate_limit_remaining_tokens'] == 7200
    assert diagnostics['rate_limit_reset_tokens_seconds'] == 30.0
    assert diagnostics['rate_limit_limit_requests'] == 30
    assert diagnostics['rate_limit_remaining_requests'] == 28
    assert diagnostics['rate_limit_reset_requests_seconds'] == 20.0

def test_high_token_usage_waits_until_window_rolls():
    clock = FakeClock()
    state = ProviderReliabilityState(
        tokens_per_minute_limit=8000,
        requests_per_minute_limit=30,
        request_tokens_estimate=768,
        safety_margin=0.9,
        retry_jitter_fraction=0.0,
    )
    reservation = {'request_id': 'existing', 'started_at': 0.0, 'estimated_tokens': 7600.0, 'actual_tokens': 7600.0, 'committed_at': 0.0}
    state.rolling_window.append(reservation)

    wait, reservation2, trace = state.acquire_request_slot(now=0.0, sleep_fn=clock.sleep, estimated_tokens=768, request_id='next', trace=True)

    assert wait == 60.0
    assert clock.slept == [60.0]
    assert trace['calculated_token_wait'] == 60.0
    assert trace['calculated_request_wait'] == 0.0
    assert reservation2['request_id'] == 'next'


def test_limit_requests_header_does_not_set_rpm():
    state = ProviderReliabilityState(tokens_per_minute_limit=8000, requests_per_minute_limit=30, request_tokens_estimate=768, safety_margin=0.9, retry_jitter_fraction=0.0)
    state.finalize_request({'started_at': 0.0, 'estimated_tokens': 768, 'actual_tokens': 768, 'committed_at': None}, finished_at=0.0, actual_tokens=768, headers={'x-ratelimit-limit-requests': '1000'})
    assert state.requests_per_minute_limit == 30
    assert state.last_provider_limit_requests == 1000


def test_reset_header_duration_parsing():
    info = _parse_rate_limit_info({'x-ratelimit-reset-tokens': '7.66s', 'x-ratelimit-reset-requests': '2m59.56s'})
    assert info['reset_tokens_seconds'] == 7.66
    assert info['reset_requests_seconds'] == 179.56

