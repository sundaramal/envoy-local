"""Tests for envoy_local.health module."""

import pytest
from unittest.mock import patch, MagicMock
from envoy_local.health import (
    check_admin_endpoint,
    wait_for_admin,
    get_health_status,
    HealthStatus,
)


ADMIN_PORT = 9901


def test_check_admin_endpoint_success():
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        assert check_admin_endpoint(ADMIN_PORT) is True


def test_check_admin_endpoint_failure():
    import urllib.error

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
        assert check_admin_endpoint(ADMIN_PORT) is False


def test_wait_for_admin_succeeds_on_first_try():
    with patch("envoy_local.health.check_admin_endpoint", return_value=True):
        assert wait_for_admin(ADMIN_PORT, retries=3, interval=0) is True


def test_wait_for_admin_exhausts_retries():
    with patch("envoy_local.health.check_admin_endpoint", return_value=False):
        assert wait_for_admin(ADMIN_PORT, retries=3, interval=0) is False


def test_wait_for_admin_succeeds_after_retries():
    side_effects = [False, False, True]
    with patch("envoy_local.health.check_admin_endpoint", side_effect=side_effects):
        assert wait_for_admin(ADMIN_PORT, retries=5, interval=0) is True


def test_get_health_status_no_pid():
    status = get_health_status(ADMIN_PORT, pid=None)
    assert isinstance(status, HealthStatus)
    assert status.alive is False
    assert status.ready is False
    assert "No PID" in status.message


def test_get_health_status_dead_process():
    status = get_health_status(ADMIN_PORT, pid=9999, is_alive_fn=lambda _: False)
    assert status.alive is False
    assert status.ready is False
    assert "9999" in status.message


def test_get_health_status_alive_and_ready():
    with patch("envoy_local.health.check_admin_endpoint", return_value=True):
        status = get_health_status(ADMIN_PORT, pid=1234, is_alive_fn=lambda _: True)
    assert status.alive is True
    assert status.admin_reachable is True
    assert status.ready is True


def test_get_health_status_alive_but_admin_down():
    with patch("envoy_local.health.check_admin_endpoint", return_value=False):
        status = get_health_status(ADMIN_PORT, pid=1234, is_alive_fn=lambda _: True)
    assert status.alive is True
    assert status.admin_reachable is False
    assert status.ready is False
    assert "not reachable" in status.message
