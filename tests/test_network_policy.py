"""Tests for envoy_local.network_policy."""

import pytest
from envoy_local.network_policy import (
    PolicyRule,
    PolicyViolation,
    PolicyReport,
    evaluate_policy,
    _check_port_policy,
    _check_host_policy,
)


def _make_config(listener_port=8080, cluster_host="backend", cluster_port=9000):
    return {
        "static_resources": {
            "listeners": [
                {
                    "name": "listener_0",
                    "address": {"socket_address": {"port_value": listener_port}},
                }
            ],
            "clusters": [
                {
                    "name": "cluster_0",
                    "load_assignment": {
                        "endpoints": [
                            {
                                "lb_endpoints": [
                                    {
                                        "endpoint": {
                                            "address": {
                                                "socket_address": {
                                                    "address": cluster_host,
                                                    "port_value": cluster_port,
                                                }
                                            }
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                }
            ],
        }
    }


def test_no_violations_when_no_rules():
    report = evaluate_policy(_make_config(), rules=[])
    assert report.is_compliant
    assert report.violations == []


def test_denied_listener_port_is_error():
    rule = PolicyRule(name="no-8080", deny_ports=[8080])
    report = evaluate_policy(_make_config(listener_port=8080), rules=[rule])
    assert not report.is_compliant
    assert report.error_count == 1


def test_port_not_in_allow_list_is_warning():
    rule = PolicyRule(name="allow-only-80", allow_ports=[80])
    report = evaluate_policy(_make_config(listener_port=8080), rules=[rule])
    assert report.is_compliant  # warning only
    assert report.warning_count >= 1


def test_allowed_port_produces_no_violation():
    rule = PolicyRule(name="allow-8080", allow_ports=[8080])
    report = evaluate_policy(_make_config(listener_port=8080), rules=[rule])
    assert report.is_compliant
    assert report.error_count == 0


def test_denied_cluster_host_is_error():
    rule = PolicyRule(name="no-bad-host", deny_hosts=["bad-backend"])
    report = evaluate_policy(_make_config(cluster_host="bad-backend"), rules=[rule])
    assert not report.is_compliant
    assert any("bad-backend" in v.message for v in report.violations)


def test_host_not_in_allow_list_is_warning():
    rule = PolicyRule(name="allow-only-safe", allow_hosts=["safe-host"])
    report = evaluate_policy(_make_config(cluster_host="other-host"), rules=[rule])
    assert report.is_compliant
    assert report.warning_count >= 1


def test_check_port_policy_deny():
    rule = PolicyRule(name="r", deny_ports=[443])
    v = _check_port_policy(rule, 443, "ctx")
    assert v is not None
    assert v.severity == "error"


def test_check_port_policy_allow_pass():
    rule = PolicyRule(name="r", allow_ports=[443])
    v = _check_port_policy(rule, 443, "ctx")
    assert v is None


def test_check_host_policy_deny():
    rule = PolicyRule(name="r", deny_hosts=["evil.com"])
    v = _check_host_policy(rule, "evil.com", "ctx")
    assert v is not None
    assert v.severity == "error"


def test_policy_report_counts():
    report = PolicyReport(
        violations=[
            PolicyViolation(rule_name="r", message="m", severity="error"),
            PolicyViolation(rule_name="r", message="m", severity="warning"),
        ]
    )
    assert report.error_count == 1
    assert report.warning_count == 1
    assert not report.is_compliant
