"""Test otentikasi login (username + password) & sesi."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings

client = TestClient(app)


@pytest.fixture
def prod_mode(monkeypatch):
    monkeypatch.setattr(settings, "mode", "prod")
    yield
    monkeypatch.setattr(settings, "mode", "dev")


def test_info_returns_mode():
    assert client.get("/auth/info").json() == {"mode": "dev"}


def test_dev_login_auto_success():
    r = client.post("/auth/login", json={"role": "guru"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["role"] == "guru"
    assert data["session_token"]


def test_login_unknown_role():
    r = client.post("/auth/login", json={"role": "bos", "username": "x", "password": "y"})
    assert r.status_code == 200
    assert r.json()["ok"] is False


def test_prod_login_requires_credentials(prod_mode):
    r = client.post("/auth/login", json={"role": "guru"})
    assert r.json()["ok"] is False

    r = client.post(
        "/auth/login",
        json={"role": "guru", "username": settings.guru_username, "password": settings.guru_password},
    )
    assert r.json()["ok"] is True
    token = r.json()["session_token"]

    # Sesi aktif terbaca di /auth/session
    sess = client.get("/auth/session", headers={"Authorization": f"Bearer {token}"}).json()
    assert sess["is_guru"] is True
    assert sess["role"] == "guru"

    # Logout menghapus sesi
    client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    sess = client.get("/auth/session", headers={"Authorization": f"Bearer {token}"}).json()
    assert sess["is_guru"] is False


def test_prod_admin_can_login_as_guru(prod_mode):
    r = client.post(
        "/auth/login",
        json={"role": "guru", "username": settings.admin_username, "password": settings.admin_password},
    )
    assert r.json()["ok"] is True
