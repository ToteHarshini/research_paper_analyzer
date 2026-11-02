"""
Unit tests for Groq HTTP 429 Rate-Limit Retry Handling and Token Optimization.
Runs completely offline using mock exceptions and mock HTTP responses.
"""

import re
from unittest.mock import MagicMock, patch
import pytest

from src.llm import (
    is_rate_limit_error,
    is_groq_json_truncation_error,
    extract_retry_delay,
    execute_with_retry,
    generate_llm_response,
    record_groq_diagnostics,
    record_groq_rate_limit_event,
    get_groq_diagnostics,
    clear_groq_diagnostics,
    parse_reset_time_to_seconds,
    LLMResponse,
)


class MockRateLimitError(Exception):
    def __init__(self, message, status_code=429, headers=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = MagicMock()
        self.response.headers = headers or {}


class MockAuthError(Exception):
    def __init__(self, message="Invalid API key", status_code=401):
        super().__init__(message)
        self.status_code = status_code
        self.response = MagicMock()
        self.response.headers = {}


class MockGroqJsonTruncationError(Exception):
    def __init__(self, message="Failed to generate JSON."):
        super().__init__(message)
        self.status_code = 400
        self.body = {
            "error": {
                "message": "Failed to generate JSON.",
                "type": "invalid_request_error",
                "code": "json_validate_failed",
                "failed_generation": "max completion tokens reached before generating a valid document."
            }
        }


# ---------------------------------------------------------------------------
# 1. Test 429 Error Detection
# ---------------------------------------------------------------------------

def test_is_rate_limit_error_detection():
    # 429 status code
    err_429 = MockRateLimitError("Rate limit reached", status_code=429)
    assert is_rate_limit_error(err_429) is True

    # Named RateLimit error
    class CustomRateLimit(Exception):
        pass
    assert is_rate_limit_error(CustomRateLimit("Too many requests")) is True

    # Error message containing 429 and rate_limit
    generic_429 = RuntimeError("Error 429: rate_limit_exceeded on TPM")
    assert is_rate_limit_error(generic_429) is True

    # Non-429 errors must return False
    auth_err = MockAuthError("Invalid credentials", status_code=401)
    assert is_rate_limit_error(auth_err) is False

    bad_request = ValueError("Invalid prompt parameters")
    assert is_rate_limit_error(bad_request) is False

    server_err = RuntimeError("500 Internal Server Error")
    assert is_rate_limit_error(server_err) is False


# ---------------------------------------------------------------------------
# 2. Test Retry-After Header Extraction
# ---------------------------------------------------------------------------

def test_extract_retry_delay_from_retry_after_header():
    err = MockRateLimitError(
        "Rate limit exceeded",
        headers={"retry-after": "4.5"}
    )
    delay = extract_retry_delay(err, attempt=0)
    # Should extract 4.5 + margin (0.25)
    assert 4.5 <= delay <= 5.0


def test_extract_retry_delay_from_reset_tokens_header():
    err = MockRateLimitError(
        "Tokens per minute exceeded",
        headers={"x-ratelimit-reset-tokens": "6.2s"}
    )
    delay = extract_retry_delay(err, attempt=0)
    assert 6.0 <= delay <= 7.0


# ---------------------------------------------------------------------------
# 3. Test Error Message Regex Extraction
# ---------------------------------------------------------------------------

def test_extract_retry_delay_from_message_patterns():
    # Pattern: "try again in 5.2s"
    err1 = MockRateLimitError("Rate limit reached. Please try again in 5.2s.")
    delay1 = extract_retry_delay(err1, attempt=0)
    assert 5.0 <= delay1 <= 6.0

    # Pattern: "retry after 3.8s"
    err2 = MockRateLimitError("TPM exceeded. Retry after 3.8s")
    delay2 = extract_retry_delay(err2, attempt=0)
    assert 3.8 <= delay2 <= 4.5

    # Pattern: "wait 2s"
    err3 = MockRateLimitError("429 Too Many Requests: wait 2s")
    delay3 = extract_retry_delay(err3, attempt=0)
    assert 2.0 <= delay3 <= 2.5


# ---------------------------------------------------------------------------
# 4. Test Exponential Backoff Fallback
# ---------------------------------------------------------------------------

def test_extract_retry_delay_exponential_fallback():
    err_no_time = MockRateLimitError("rate_limit_exceeded")
    
    delay_att0 = extract_retry_delay(err_no_time, attempt=0, initial_delay=2.0)
    delay_att1 = extract_retry_delay(err_no_time, attempt=1, initial_delay=2.0)
    delay_att2 = extract_retry_delay(err_no_time, attempt=2, initial_delay=2.0)

    # Attempt 0: ~2.0 + jitter
    assert 2.0 <= delay_att0 <= 3.0
    # Attempt 1: ~4.0 + jitter
    assert 4.0 <= delay_att1 <= 5.0
    # Attempt 2: ~8.0 + jitter
    assert 8.0 <= delay_att2 <= 9.0

    # Delay must scale exponentially
    assert delay_att0 < delay_att1 < delay_att2

    # Delay must respect max_delay cap
    delay_capped = extract_retry_delay(err_no_time, attempt=10, max_delay=15.0)
    assert delay_capped <= 15.0


# ---------------------------------------------------------------------------
# 5. Test execute_with_retry Execution Flow
# ---------------------------------------------------------------------------

def test_execute_with_retry_succeeds_first_try():
    mock_fn = MagicMock(return_value="Success")
    with patch("time.sleep") as mock_sleep:
        result = execute_with_retry(mock_fn, max_retries=3)
        assert result == "Success"
        assert mock_fn.call_count == 1
        assert mock_sleep.call_count == 0


def test_execute_with_retry_recovers_after_transient_429():
    err = MockRateLimitError("Rate limit reached. Please try again in 1s.")
    mock_fn = MagicMock(side_effect=[err, err, "Success on third attempt"])

    with patch("time.sleep") as mock_sleep:
        result = execute_with_retry(mock_fn, max_retries=3)
        assert result == "Success on third attempt"
        assert mock_fn.call_count == 3
        assert mock_sleep.call_count == 2


def test_execute_with_retry_exhausts_and_raises():
    err = MockRateLimitError("Persistent rate limit", status_code=429)
    mock_fn = MagicMock(side_effect=err)

    with patch("time.sleep"):
        with pytest.raises(MockRateLimitError):
            execute_with_retry(mock_fn, max_retries=3)
        # 1 initial try + 3 retries = 4 total invocations
        assert mock_fn.call_count == 4


def test_execute_with_retry_does_not_retry_auth_error():
    auth_err = MockAuthError("Invalid API Key", status_code=401)
    mock_fn = MagicMock(side_effect=auth_err)

    with patch("time.sleep") as mock_sleep:
        with pytest.raises(MockAuthError):
            execute_with_retry(mock_fn, max_retries=3)
        # Must fail immediately on attempt 0
        assert mock_fn.call_count == 1
        assert mock_sleep.call_count == 0


# ---------------------------------------------------------------------------
# 6. Test Groq Client Integration With Retry
# ---------------------------------------------------------------------------

@patch.dict("os.environ", {"LLM_PROVIDER": "groq", "GROQ_API_KEY": "test_groq_key"})
@patch("groq.Groq")
@patch("time.sleep")
def test_groq_generate_llm_response_with_retry(mock_sleep, mock_groq_cls):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client

    rate_limit_err = MockRateLimitError("429 rate_limit_exceeded: Please try again in 1.5s.")
    success_resp = MagicMock()
    success_resp.choices = [MagicMock(message=MagicMock(content="Analyzed research findings."))]

    # Fail once with 429, then return success
    mock_client.chat.completions.create.side_effect = [rate_limit_err, success_resp]

    resp = generate_llm_response(prompt="Summarize paper methodology", max_output_tokens=500)
    assert resp.text == "Analyzed research findings."
    assert mock_client.chat.completions.create.call_count == 2
    assert mock_sleep.call_count == 1


# ---------------------------------------------------------------------------
# 7. Test Groq JSON Truncation (json_validate_failed) Detection & Recovery
# ---------------------------------------------------------------------------

def test_is_groq_json_truncation_error_detection():
    # True positive: status 400 with json_validate_failed and max completion tokens
    err = MockGroqJsonTruncationError()
    assert is_groq_json_truncation_error(err) is True

    # True positive via string representation
    str_err = RuntimeError(
        "Error code: 400 - {'error': {'code': 'json_validate_failed', "
        "'failed_generation': 'max completion tokens reached before generating a valid document.'}}"
    )
    setattr(str_err, "status_code", 400)
    assert is_groq_json_truncation_error(str_err) is True

    # False positive: Ordinary malformed JSON not caused by max completion tokens
    bad_syntax_err = RuntimeError("Error code: 400 - {'error': {'code': 'json_validate_failed', 'message': 'Syntax error at line 1'}}")
    setattr(bad_syntax_err, "status_code", 400)
    assert is_groq_json_truncation_error(bad_syntax_err) is False

    # False positive: 401 Auth error
    auth_err = MockAuthError("Unauthorized", status_code=401)
    assert is_groq_json_truncation_error(auth_err) is False

    # False positive: 429 RateLimit error
    rl_err = MockRateLimitError("Too Many Requests", status_code=429)
    assert is_groq_json_truncation_error(rl_err) is False


@patch.dict("os.environ", {"LLM_PROVIDER": "groq", "GROQ_API_KEY": "test_groq_key"})
@patch("groq.Groq")
def test_groq_json_truncation_recovery_success(mock_groq_cls):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client

    trunc_err = MockGroqJsonTruncationError()
    success_resp = MagicMock()
    success_resp.choices = [MagicMock(message=MagicMock(content='{"claims": ["Verified Claim 1"]}'))]

    # First attempt fails with json_validate_failed (max completion tokens reached), second attempt succeeds
    mock_client.chat.completions.create.side_effect = [trunc_err, success_resp]

    resp = generate_llm_response(
        prompt="Extract claims",
        max_output_tokens=500,
        response_mime_type="application/json"
    )

    assert resp.text == '{"claims": ["Verified Claim 1"]}'
    assert mock_client.chat.completions.create.call_count == 2
    # Second call should have boosted max_completion_tokens (500 * 1.4 = 700)
    second_call_kwargs = mock_client.chat.completions.create.call_args_list[1][1]
    assert second_call_kwargs["max_completion_tokens"] == 700


@patch.dict("os.environ", {"LLM_PROVIDER": "groq", "GROQ_API_KEY": "test_groq_key"})
@patch("groq.Groq")
def test_groq_json_truncation_exhausts_and_raises(mock_groq_cls):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client

    trunc_err = MockGroqJsonTruncationError()
    # Always fails with truncation
    mock_client.chat.completions.create.side_effect = trunc_err

    with pytest.raises(MockGroqJsonTruncationError):
        generate_llm_response(
            prompt="Extract claims",
            max_output_tokens=500,
            response_mime_type="application/json"
        )

    # Must retry only once (total 2 attempts) to strictly prevent uncontrolled TPM usage
    assert mock_client.chat.completions.create.call_count == 2


@patch.dict("os.environ", {"LLM_PROVIDER": "groq", "GROQ_API_KEY": "test_groq_key"})
@patch("groq.Groq")
def test_groq_ordinary_bad_request_not_retried(mock_groq_cls):
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client

    bad_param_err = RuntimeError("Error code: 400 - Invalid parameter 'foo'")
    setattr(bad_param_err, "status_code", 400)
    mock_client.chat.completions.create.side_effect = bad_param_err

    with pytest.raises(RuntimeError):
        generate_llm_response(
            prompt="Extract claims",
            max_output_tokens=500,
            response_mime_type="application/json"
        )

    # Must fail immediately without retrying (only 1 invocation)
    assert mock_client.chat.completions.create.call_count == 1


# ---------------------------------------------------------------------------
# 8. Test Groq GPT-OSS Reasoning Parameters Specification
# ---------------------------------------------------------------------------

@patch.dict("os.environ", {
    "LLM_PROVIDER": "groq",
    "GROQ_MODEL": "openai/gpt-oss-120b",
    "GROQ_API_KEY": "test_groq_key"
})
@patch("groq.Groq")
def test_groq_gpt_oss_json_receives_correct_reasoning_params(mock_groq_cls):
    """
    Verifies that for Groq JSON-mode requests using openai/gpt-oss-120b:
    1. reasoning_effort="low"
    2. include_reasoning=False
    3. reasoning_format is NOT sent (as GPT-OSS does not support it)
    4. response_format={"type": "json_object"}
    """
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content='{"subquestions": ["Subq 1"]}'))]
    mock_client.chat.completions.create.return_value = mock_resp

    generate_llm_response(
        prompt="Generate subquestions",
        max_output_tokens=600,
        response_mime_type="application/json"
    )

    assert mock_client.chat.completions.create.call_count == 1
    call_kwargs = mock_client.chat.completions.create.call_args[1]

    # Verify JSON mode
    assert call_kwargs.get("response_format") == {"type": "json_object"}
    # Verify reasoning parameters
    assert call_kwargs.get("reasoning_effort") == "low"
    assert call_kwargs.get("include_reasoning") is False
    # Verify reasoning_format is NOT present
    assert "reasoning_format" not in call_kwargs


@patch.dict("os.environ", {
    "LLM_PROVIDER": "groq",
    "GROQ_MODEL": "openai/gpt-oss-120b",
    "GROQ_API_KEY": "test_groq_key"
})
@patch("groq.Groq")
def test_groq_non_json_mode_does_not_force_reasoning_overrides(mock_groq_cls):
    """
    Verifies that non-JSON calls (e.g. final report) do not pass response_format,
    include_reasoning, or reasoning_effort.
    """
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content="# 1. Executive Summary"))]
    mock_client.chat.completions.create.return_value = mock_resp

    generate_llm_response(
        prompt="Generate report",
        max_output_tokens=2000,
        response_mime_type=None
    )

    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert "response_format" not in call_kwargs
    assert "reasoning_effort" not in call_kwargs
    assert "include_reasoning" not in call_kwargs
    assert "reasoning_format" not in call_kwargs


@patch.dict("os.environ", {
    "LLM_PROVIDER": "openai",
    "OPENAI_MODEL": "gpt-4.1-mini",
    "OPENAI_API_KEY": "test_openai_key"
})
@patch("openai.OpenAI")
def test_openai_provider_config_remains_unchanged(mock_openai_cls):
    """
    Verifies that OpenAI provider configuration remains standard without groq-specific reasoning keys.
    """
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content='{"claims": []}'))]
    mock_client.chat.completions.create.return_value = mock_resp

    generate_llm_response(
        prompt="Test prompt",
        max_output_tokens=500,
        response_mime_type="application/json"
    )

    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs.get("response_format") == {"type": "json_object"}
    assert "reasoning_effort" not in call_kwargs
    assert "include_reasoning" not in call_kwargs
    assert "reasoning_format" not in call_kwargs


# ---------------------------------------------------------------------------
# 9. Test Token Usage Diagnostics & Header Capture
# ---------------------------------------------------------------------------

def test_record_groq_diagnostics_extracts_tokens_and_headers():
    clear_groq_diagnostics()

    mock_completion = MagicMock()
    mock_completion.usage.prompt_tokens = 850
    mock_completion.usage.completion_tokens = 220
    mock_completion.usage.total_tokens = 1070

    headers = {
        "x-ratelimit-remaining-tokens": "5200",
        "x-ratelimit-reset-tokens": "2.4s",
        "x-ratelimit-remaining-requests": "28",
        "x-ratelimit-reset-requests": "1.1s",
    }

    diag = record_groq_diagnostics(mock_completion, headers=headers)

    assert diag["prompt_tokens"] == 850
    assert diag["completion_tokens"] == 220
    assert diag["total_tokens"] == 1070
    assert diag["x-ratelimit-remaining-tokens"] == "5200"
    assert diag["x-ratelimit-reset-tokens"] == "2.4s"

    # Verify diagnostics do not contain sensitive prompts or completion texts or keys
    for k, v in diag.items():
        assert "key" not in k.lower() or "remaining" in k.lower() or "reset" in k.lower()
        assert "prompt_text" not in k
        assert "completion_text" not in k

    history = get_groq_diagnostics()
    assert len(history) == 1
    assert history[0]["total_tokens"] == 1070
    clear_groq_diagnostics()


def test_parse_reset_time_to_seconds():
    assert parse_reset_time_to_seconds("6.2s") == 6.2
    assert parse_reset_time_to_seconds("450ms") == 0.45
    assert parse_reset_time_to_seconds("2.5") == 2.5
    assert parse_reset_time_to_seconds("0s") == 0.0
    assert parse_reset_time_to_seconds(None) == 0.0
    assert parse_reset_time_to_seconds("invalid") == 0.0


def test_record_groq_rate_limit_event_captures_429():
    clear_groq_diagnostics()
    err = MockRateLimitError(
        "TPM exceeded",
        headers={"x-ratelimit-remaining-tokens": "0", "x-ratelimit-reset-tokens": "5.1s"}
    )
    diag = record_groq_rate_limit_event(err)

    assert diag["event"] == "429_rate_limit"
    assert diag["x-ratelimit-remaining-tokens"] == "0"
    assert diag["x-ratelimit-reset-tokens"] == "5.1s"
    clear_groq_diagnostics()


# ---------------------------------------------------------------------------
# 10. Test Adaptive Pacing Based on Rate-Limit Remaining Header
# ---------------------------------------------------------------------------

@patch.dict("os.environ", {"LLM_PROVIDER": "groq", "GROQ_API_KEY": "test_groq_key"})
@patch("groq.Groq")
@patch("time.sleep")
def test_adaptive_pacing_triggers_only_when_tokens_low(mock_sleep, mock_groq_cls):
    """
    Verifies that adaptive pacing:
    - Triggers pause when x-ratelimit-remaining-tokens < 1500
    - Does NOT trigger pause when x-ratelimit-remaining-tokens >= 1500
    - Avoids arbitrary fixed sleeps
    """
    mock_client = MagicMock()
    mock_groq_cls.return_value = mock_client

    # Scenario 1: Remaining tokens are plentiful (6,000 >= 1500) -> 0 sleep
    resp_healthy = MagicMock()
    resp_healthy.choices = [MagicMock(message=MagicMock(content="Healthy response"))]
    resp_healthy.usage.prompt_tokens = 300
    resp_healthy.usage.completion_tokens = 100
    resp_healthy.usage.total_tokens = 400
    resp_healthy.headers = {
        "x-ratelimit-remaining-tokens": "6000",
        "x-ratelimit-reset-tokens": "1.2s",
    }

    mock_client.chat.completions.create.return_value = resp_healthy

    generate_llm_response(prompt="Healthy check", max_output_tokens=500)
    assert mock_sleep.call_count == 0

    # Scenario 2: Remaining tokens critically low (800 < 1500) -> pause based on reset header
    resp_low = MagicMock()
    resp_low.choices = [MagicMock(message=MagicMock(content="Low token response"))]
    resp_low.usage.prompt_tokens = 300
    resp_low.usage.completion_tokens = 100
    resp_low.usage.total_tokens = 400
    resp_low.headers = {
        "x-ratelimit-remaining-tokens": "800",
        "x-ratelimit-reset-tokens": "1.5s",
    }
    mock_client.chat.completions.create.return_value = resp_low

    generate_llm_response(prompt="Low token check", max_output_tokens=500)
    # Must trigger 1 adaptive sleep of reset (1.5s) + margin (0.25s) = 1.75s
    assert mock_sleep.call_count == 1
    sleep_arg = mock_sleep.call_args[0][0]
    assert 1.7 <= sleep_arg <= 1.8



