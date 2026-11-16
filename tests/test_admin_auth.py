import hashlib
import importlib

import pytest
from fastapi.testclient import TestClient


ADMIN_PASSWORD = "correct horse battery staple"
ADMIN_USERNAME = "teacher"
PASSWORD_HASH = (
    "pbkdf2_sha256$600000$"
    + bytes(range(16)).hex()
    + "$"
    + hashlib.pbkdf2_hmac(
        "sha256",
        ADMIN_PASSWORD.encode(),
        bytes(range(16)),
        600_000,
    ).hex()
)


def load_app(monkeypatch, configured=True):
    if configured:
        monkeypatch.setenv("ADMIN_USERNAME", ADMIN_USERNAME)
        monkeypatch.setenv("ADMIN_PASSWORD_HASH", PASSWORD_HASH)
        monkeypatch.setenv("SESSION_SECRET_KEY", "test-session-secret-key-that-is-at-least-32-characters")
    else:
        monkeypatch.delenv("ADMIN_USERNAME", raising=False)
        monkeypatch.delenv("ADMIN_PASSWORD_HASH", raising=False)
        monkeypatch.delenv("SESSION_SECRET_KEY", raising=False)
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "false")

    module = importlib.import_module("src.app")
    return importlib.reload(module)


@pytest.fixture
def configured_client(monkeypatch):
    module = load_app(monkeypatch)
    with TestClient(module.app) as client:
        yield client


def test_activity_listing_is_public_but_registration_changes_require_admin(configured_client):
    assert configured_client.get("/activities").status_code == 200
    assert configured_client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "new-student@mergington.edu"},
    ).status_code == 401
    assert configured_client.delete(
        "/activities/Chess%20Club/unregister",
        params={"email": "michael@mergington.edu"},
    ).status_code == 401


def test_invalid_credentials_do_not_create_an_admin_session(configured_client):
    response = configured_client.post(
        "/admin/login",
        json={"username": ADMIN_USERNAME, "password": "wrong password"},
    )

    assert response.status_code == 401
    assert configured_client.get("/admin/session").json() == {"authenticated": False}
    assert configured_client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "new-student@mergington.edu"},
    ).status_code == 401


def test_admin_can_manage_signups_until_logout(configured_client):
    login_response = configured_client.post(
        "/admin/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )

    assert login_response.status_code == 200
    assert "httponly" in login_response.headers["set-cookie"].lower()
    assert configured_client.get("/admin/session").json() == {"authenticated": True}

    signup_response = configured_client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "new-student@mergington.edu"},
    )
    assert signup_response.status_code == 200

    unregister_response = configured_client.delete(
        "/activities/Chess%20Club/unregister",
        params={"email": "new-student@mergington.edu"},
    )
    assert unregister_response.status_code == 200

    assert configured_client.post("/admin/logout").status_code == 200
    assert configured_client.get("/admin/session").json() == {"authenticated": False}
    assert configured_client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "new-student@mergington.edu"},
    ).status_code == 401


def test_admin_actions_are_disabled_when_authentication_is_not_configured(monkeypatch):
    module = load_app(monkeypatch, configured=False)
    with TestClient(module.app) as client:
        login_response = client.post(
            "/admin/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
        )

        assert login_response.status_code == 503
        assert client.get("/activities").status_code == 200
        assert client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "new-student@mergington.edu"},
        ).status_code == 503
