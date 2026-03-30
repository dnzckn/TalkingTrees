"""Tests for WP-15: Security & Access Control."""

import pytest
from fastapi.testclient import TestClient

from talking_trees.api.main import app
from talking_trees.security.config import SecurityConfig
from talking_trees.security.middleware import configure_security, _rate_limit_tracker
from talking_trees.security.roles import Role


@pytest.fixture
def client():
    configure_security(SecurityConfig())
    return TestClient(app)


@pytest.fixture
def secure_client():
    config = SecurityConfig(
        enabled=True,
        api_keys={
            "viewer-key": Role.VIEWER,
            "operator-key": Role.OPERATOR,
            "admin-key": Role.ADMIN,
        },
    )
    configure_security(config)
    _rate_limit_tracker.clear()
    yield TestClient(app)
    configure_security(SecurityConfig())
    _rate_limit_tracker.clear()


def test_auth_disabled_passes(client):
    assert client.get("/health").status_code == 200


def test_whoami_no_auth(client):
    resp = client.get("/auth/whoami")
    assert resp.status_code == 200
    assert resp.json()["authenticated"] is False


def test_whoami_with_key(secure_client):
    resp = secure_client.get("/auth/whoami", headers={"X-API-Key": "admin-key"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


def test_missing_key_rejected(secure_client):
    assert secure_client.get("/auth/whoami").status_code == 401


def test_invalid_key_rejected(secure_client):
    resp = secure_client.get("/auth/whoami", headers={"X-API-Key": "bad"})
    assert resp.status_code == 401


def test_rate_limiting():
    config = SecurityConfig(
        enabled=True,
        api_keys={"test-key": Role.ADMIN},
        rate_limit_rpm=5,
    )
    configure_security(config)
    _rate_limit_tracker.clear()
    client = TestClient(app)

    for _ in range(5):
        assert client.get("/auth/whoami", headers={"X-API-Key": "test-key"}).status_code == 200

    assert client.get("/auth/whoami", headers={"X-API-Key": "test-key"}).status_code == 429

    configure_security(SecurityConfig())
    _rate_limit_tracker.clear()
