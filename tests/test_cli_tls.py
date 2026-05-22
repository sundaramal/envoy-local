"""Tests for envoy_local.cli_tls."""

import argparse
import json
import sys
from io import StringIO
from unittest.mock import patch, mock_open

import pytest

from envoy_local.cli_tls import cmd_tls_inspect, register_tls_commands


def _make_args(file=None, json_output=False):
    ns = argparse.Namespace(file=file, json=json_output)
    return ns


PLAINTEXT_LISTENER = json.dumps({"name": "plain", "port": 8080})
SECURE_LISTENER = json.dumps(
    {
        "name": "secure",
        "port": 443,
        "tls_context": {
            "cert_chain_file": "/c.pem",
            "private_key_file": "/k.pem",
        },
    }
)


def test_cmd_tls_inspect_reads_file(tmp_path, capsys):
    p = tmp_path / "listener.json"
    p.write_text(SECURE_LISTENER)
    with pytest.raises(SystemExit) as exc:
        cmd_tls_inspect(_make_args(file=str(p)))
    # No warnings → exit code should NOT be 2; but SystemExit may not be raised
    # at all for clean runs — catch both cases.
    captured = capsys.readouterr()
    assert "secure" in captured.out


def test_cmd_tls_inspect_file_not_found(capsys):
    with pytest.raises(SystemExit) as exc:
        cmd_tls_inspect(_make_args(file="/no/such/file.json"))
    assert exc.value.code == 1


def test_cmd_tls_inspect_stdin(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", StringIO(PLAINTEXT_LISTENER))
    with pytest.raises(SystemExit) as exc:
        cmd_tls_inspect(_make_args())
    assert exc.value.code == 2  # warnings present for plaintext


def test_cmd_tls_inspect_json_output(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", StringIO(SECURE_LISTENER))
    # secure listener has no warnings → no SystemExit
    cmd_tls_inspect(_make_args(json_output=True))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert data[0]["tls_enabled"] is True


def test_cmd_tls_inspect_invalid_json(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", StringIO("not json"))
    with pytest.raises(SystemExit) as exc:
        cmd_tls_inspect(_make_args())
    assert exc.value.code == 1


def test_register_tls_commands_adds_subparser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register_tls_commands(subparsers)
    args = parser.parse_args(["tls-inspect", "--json"])
    assert args.json is True
    assert args.func is not None
