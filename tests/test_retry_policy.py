"""Unit tests for envoy_local.retry_policy."""

import pytest
from envoy_local.retry_policy import (
    RetryPolicy,
    validate_retry_policy,
    _parse_timeout_ms,
)


def test_default_retry_policy_is_valid():
    policy = RetryPolicy()
    assert validate_retry_policy(policy) == []


def test_to_dict_contains_retry_on():
    policy = RetryPolicy(retry_on=["5xx", "reset"])
    d = policy.to_dict()
    assert d["retry_on"] == "5xx,reset"


def test_to_dict_includes_per_try_timeout():
    policy = RetryPolicy(per_try_timeout_ms=250)
    d = policy.to_dict()
    assert d["per_try_timeout"] == "250ms"


def test_to_dict_omits_timeout_when_none():
    policy = RetryPolicy(per_try_timeout_ms=None)
    assert "per_try_timeout" not in policy.to_dict()


def test_to_dict_includes_retriable_status_codes():
    policy = RetryPolicy(
        retry_on=["retriable-status-codes"],
        retriable_status_codes=[503, 429],
    )
    d = policy.to_dict()
    assert d["retriable_status_codes"] == [503, 429]


def test_from_dict_parses_retry_on():
    policy = RetryPolicy.from_dict({"retry_on": "5xx,reset", "num_retries": 2})
    assert policy.retry_on == ["5xx", "reset"]
    assert policy.num_retries == 2


def test_from_dict_defaults_when_missing():
    policy = RetryPolicy.from_dict({})
    assert policy.num_retries == 3
    assert policy.retry_on == ["5xx"]


def test_parse_timeout_ms_from_ms_string():
    assert _parse_timeout_ms("500ms") == 500


def test_parse_timeout_ms_from_s_string():
    assert _parse_timeout_ms("2s") == 2000


def test_parse_timeout_ms_from_int_string():
    assert _parse_timeout_ms("300") == 300


def test_parse_timeout_ms_none_returns_none():
    assert _parse_timeout_ms(None) is None


def test_unknown_retry_on_condition_is_error():
    policy = RetryPolicy(retry_on=["bogus-condition"])
    errors = validate_retry_policy(policy)
    assert any("bogus-condition" in e for e in errors)


def test_negative_num_retries_is_error():
    policy = RetryPolicy(num_retries=-1)
    errors = validate_retry_policy(policy)
    assert any("num_retries" in e for e in errors)


def test_zero_per_try_timeout_is_error():
    policy = RetryPolicy(per_try_timeout_ms=0)
    errors = validate_retry_policy(policy)
    assert any("per_try_timeout_ms" in e for e in errors)


def test_retriable_status_codes_required_when_condition_set():
    policy = RetryPolicy(retry_on=["retriable-status-codes"], retriable_status_codes=[])
    errors = validate_retry_policy(policy)
    assert any("retriable_status_codes" in e for e in errors)


def test_retriable_status_codes_ok_when_set():
    policy = RetryPolicy(
        retry_on=["retriable-status-codes"],
        retriable_status_codes=[503],
    )
    assert validate_retry_policy(policy) == []
