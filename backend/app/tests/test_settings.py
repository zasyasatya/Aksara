from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.services.data_store import DATA_DIR

client = TestClient(app)
SETTINGS_PATH = DATA_DIR / "settings.json"


def _restore():
    SETTINGS_PATH.write_text('{\n  "theme": "native"\n}\n', encoding="utf-8")


def test_default_theme_is_native():
    _restore()
    r = client.get("/api/settings/theme")
    assert r.status_code == 200
    data = r.json()
    assert data["theme"] == "native"
    assert data["default"] == "native"
    assert "lontar" in data["available"]


def test_set_theme_dev_mode_and_persist():
    try:
        r = client.put("/api/settings/theme", json={"theme": "segara"})
        assert r.status_code == 200, r.text
        assert client.get("/api/settings/theme").json()["theme"] == "segara"
        # kembali ke native
        r = client.put("/api/settings/theme", json={"theme": "native"})
        assert r.json()["theme"] == "native"
    finally:
        _restore()


def test_unknown_theme_rejected():
    r = client.put("/api/settings/theme", json={"theme": "neon-pink"})
    assert r.status_code == 422


def test_prod_requires_admin(monkeypatch):
    monkeypatch.setattr(settings, "mode", "prod")
    try:
        r = client.put("/api/settings/theme", json={"theme": "lontar"})
        assert r.status_code == 403
        # publik tetap bisa membaca
        assert client.get("/api/settings/theme").status_code == 200
        login = client.post("/auth/login", json={"role": "admin", "username": settings.admin_username, "password": settings.admin_password}).json()
        hdr = {"Authorization": f"Bearer {login['session_token']}"}
        r = client.put("/api/settings/theme", json={"theme": "lontar"}, headers=hdr)
        assert r.status_code == 200
    finally:
        monkeypatch.setattr(settings, "mode", "dev")
        _restore()
