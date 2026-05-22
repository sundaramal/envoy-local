"""Tests for envoy_local.cert TLS certificate utilities."""

import os
import pytest
from unittest.mock import patch, MagicMock
from envoy_local import cert as certmod
from envoy_local.cert import (
    generate_self_signed,
    cert_exists,
    get_cert_info,
    delete_cert,
    list_certs,
    CertInfo,
)


@pytest.fixture
def cert_dir(tmp_path):
    return str(tmp_path / "certs")


def _fake_openssl(name, cert_dir):
    """Create stub cert/key files without calling openssl."""
    os.makedirs(cert_dir, exist_ok=True)
    open(os.path.join(cert_dir, f"{name}.crt"), "w").close()
    open(os.path.join(cert_dir, f"{name}.key"), "w").close()


def test_generate_self_signed_returns_cert_info(cert_dir):
    with patch("envoy_local.cert.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        _fake_openssl("test", cert_dir)
        info = generate_self_signed("test", cert_dir=cert_dir)
    assert isinstance(info, CertInfo)
    assert info.cert_path.endswith("test.crt")
    assert info.key_path.endswith("test.key")


def test_generate_self_signed_calls_openssl(cert_dir):
    with patch("envoy_local.cert.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        generate_self_signed("myservice", cert_dir=cert_dir, days=90)
    args = mock_run.call_args[0][0]
    assert "openssl" in args
    assert "90" in args
    assert "/CN=myservice/O=envoy-local" in args


def test_cert_exists_true(cert_dir):
    _fake_openssl("svc", cert_dir)
    assert cert_exists("svc", cert_dir=cert_dir) is True


def test_cert_exists_false(cert_dir):
    assert cert_exists("missing", cert_dir=cert_dir) is False


def test_get_cert_info_returns_paths(cert_dir):
    _fake_openssl("alpha", cert_dir)
    info = get_cert_info("alpha", cert_dir=cert_dir)
    assert os.path.basename(info.cert_path) == "alpha.crt"
    assert os.path.basename(info.key_path) == "alpha.key"


def test_get_cert_info_raises_if_missing(cert_dir):
    with pytest.raises(FileNotFoundError):
        get_cert_info("ghost", cert_dir=cert_dir)


def test_delete_cert_removes_files(cert_dir):
    _fake_openssl("beta", cert_dir)
    assert cert_exists("beta", cert_dir=cert_dir)
    delete_cert("beta", cert_dir=cert_dir)
    assert not cert_exists("beta", cert_dir=cert_dir)


def test_delete_cert_noop_if_missing(cert_dir):
    # Should not raise
    delete_cert("nonexistent", cert_dir=cert_dir)


def test_list_certs_returns_names(cert_dir):
    for name in ("aaa", "bbb", "ccc"):
        _fake_openssl(name, cert_dir)
    names = list_certs(cert_dir=cert_dir)
    assert names == ["aaa", "bbb", "ccc"]


def test_list_certs_empty_dir(cert_dir):
    os.makedirs(cert_dir)
    assert list_certs(cert_dir=cert_dir) == []


def test_list_certs_missing_dir(cert_dir):
    assert list_certs(cert_dir=cert_dir) == []
