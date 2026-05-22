"""Tests for envoy_local.tls_inspector."""

import pytest

from envoy_local.tls_inspector import (
    TLSInspectionResult,
    inspect_listener_tls,
    format_tls_report,
)


# ---------------------------------------------------------------------------
# inspect_listener_tls
# ---------------------------------------------------------------------------

def test_no_tls_context_returns_disabled():
    result = inspect_listener_tls({"name": "ingress", "port": 8080})
    assert result.tls_enabled is False
    assert result.listener_name == "ingress"
    assert result.port == 8080


def test_no_tls_context_has_plaintext_warning():
    result = inspect_listener_tls({"name": "ingress", "port": 8080})
    assert any("plaintext" in w.lower() for w in result.warnings)


def test_full_tls_context_returns_enabled():
    listener = {
        "name": "secure",
        "port": 443,
        "tls_context": {
            "cert_chain_file": "/etc/certs/cert.pem",
            "private_key_file": "/etc/certs/key.pem",
        },
    }
    result = inspect_listener_tls(listener)
    assert result.tls_enabled is True
    assert result.cert_path == "/etc/certs/cert.pem"
    assert result.key_path == "/etc/certs/key.pem"
    assert result.warnings == []


def test_missing_cert_produces_warning():
    listener = {
        "name": "partial",
        "port": 443,
        "tls_context": {"private_key_file": "/etc/certs/key.pem"},
    }
    result = inspect_listener_tls(listener)
    assert result.tls_enabled is True
    assert any("cert_chain_file" in w for w in result.warnings)


def test_missing_key_produces_warning():
    listener = {
        "name": "partial",
        "port": 443,
        "tls_context": {"cert_chain_file": "/etc/certs/cert.pem"},
    }
    result = inspect_listener_tls(listener)
    assert result.tls_enabled is True
    assert any("private_key_file" in w for w in result.warnings)


def test_unnamed_listener_uses_placeholder():
    result = inspect_listener_tls({"port": 9000})
    assert result.listener_name == "<unnamed>"


def test_missing_port_defaults_to_zero():
    result = inspect_listener_tls({"name": "noport"})
    assert result.port == 0


# ---------------------------------------------------------------------------
# format_tls_report
# ---------------------------------------------------------------------------

def test_format_report_contains_listener_name():
    results = [inspect_listener_tls({"name": "edge", "port": 80})]
    report = format_tls_report(results)
    assert "edge" in report


def test_format_report_shows_disabled_status():
    results = [inspect_listener_tls({"name": "edge", "port": 80})]
    report = format_tls_report(results)
    assert "DISABLED" in report


def test_format_report_shows_enabled_status():
    listener = {
        "name": "secure",
        "port": 443,
        "tls_context": {
            "cert_chain_file": "/c.pem",
            "private_key_file": "/k.pem",
        },
    }
    results = [inspect_listener_tls(listener)]
    report = format_tls_report(results)
    assert "ENABLED" in report


def test_format_report_includes_warnings():
    listener = {"name": "w", "port": 443, "tls_context": {}}
    results = [inspect_listener_tls(listener)]
    report = format_tls_report(results)
    assert "[WARN]" in report
