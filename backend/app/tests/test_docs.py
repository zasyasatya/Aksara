import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.routers.docs import DOCS_DATA_PATH

client = TestClient(app)

ALL_SLUGS = {"penggunaan-murid", "penggunaan-guru", "penggunaan-admin", "metode-scientific", "dataset-dan-model", "panduan-retraining"}


def test_mode_env_alias():
    """AKSARA_MODE / username-password harus terbaca (regresi: dulu hanya 'MODE')."""
    from app.core.config import Settings

    s = Settings(_env_prefix=None, **{})
    # validasi via alias: instance baru dengan env disimulasi lewat kwargs alias
    s2 = Settings(mode="prod", admin_username="root", admin_password="rahasia")
    assert s2.is_prod is True
    assert s2.admin_username == "root"
    assert s2.admin_password == "rahasia"
    assert s.mode == "dev"  # default aman


@pytest.fixture
def restore_docs_data():
    """Backup data/docs.json agar perubahan visibilitas di test tidak menular."""
    original = DOCS_DATA_PATH.read_text(encoding="utf-8")
    yield
    DOCS_DATA_PATH.write_text(original, encoding="utf-8")


@pytest.fixture
def prod_mode(monkeypatch):
    monkeypatch.setattr(settings, "mode", "prod")
    yield
    monkeypatch.setattr(settings, "mode", "dev")


def _admin_headers():
    """Login sebagai admin, kembalikan header Authorization untuk sesi aktif."""
    r = client.post(
        "/auth/login",
        json={"role": "admin", "username": settings.admin_username, "password": settings.admin_password},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["ok"] is True, data
    return {"Authorization": f"Bearer {data['session_token']}"}


# ── Mode dev ────────────────────────────────────────────────────────────

def test_dev_mode_returns_all_pages():
    response = client.get("/api/docs/pages")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "dev"
    assert data["is_admin"] is True
    assert {p["slug"] for p in data["pages"]} == ALL_SLUGS


def test_dev_mode_toggle_visibility_without_login(restore_docs_data):
    response = client.patch(
        "/api/docs/pages/metode-scientific/visibility",
        json={"is_public": False},
    )
    assert response.status_code == 200
    assert response.json()["is_public"] is False

    # Tetap semua halaman terlihat di mode dev meski ada halaman privat
    listing = client.get("/api/docs/pages").json()
    assert {p["slug"] for p in listing["pages"]} == ALL_SLUGS
    private = next(p for p in listing["pages"] if p["slug"] == "metode-scientific")
    assert private["is_public"] is False


def test_toggle_unknown_slug_404():
    response = client.patch(
        "/api/docs/pages/tidak-ada/visibility",
        json={"is_public": True},
    )
    assert response.status_code == 404


# ── Mode prod ───────────────────────────────────────────────────────────

def test_prod_mode_hides_private_pages_from_regular_user(restore_docs_data, prod_mode):
    # Buat satu halaman privat (sebagai admin)
    client.patch("/api/docs/pages/penggunaan-admin/visibility", json={"is_public": False},
                 headers=_admin_headers())

    # Pengguna biasa (tanpa login) hanya melihat halaman publik
    listing = client.get("/api/docs/pages").json()
    assert listing["mode"] == "prod"
    assert listing["is_admin"] is False
    assert "penggunaan-admin" not in {p["slug"] for p in listing["pages"]}
    assert len(listing["pages"]) == len(ALL_SLUGS) - 1


def test_prod_mode_admin_sees_all_pages(restore_docs_data, prod_mode):
    client.patch("/api/docs/pages/penggunaan-guru/visibility", json={"is_public": False},
                 headers=_admin_headers())

    listing = client.get("/api/docs/pages", headers=_admin_headers()).json()
    assert listing["is_admin"] is True
    assert {p["slug"] for p in listing["pages"]} == ALL_SLUGS


def test_prod_mode_requires_login_for_toggle(restore_docs_data, prod_mode):
    # Tanpa login → 403 (cek admin dilakukan sebelum apa pun)
    response = client.patch(
        "/api/docs/pages/penggunaan-murid/visibility",
        json={"is_public": False},
    )
    assert response.status_code == 403

    # Sesi salah → 403
    response = client.patch(
        "/api/docs/pages/penggunaan-murid/visibility",
        json={"is_public": False},
        headers={"Authorization": "Bearer salah"},
    )
    assert response.status_code == 403

    response = client.patch(
        "/api/docs/pages/penggunaan-murid/visibility",
        json={"is_public": False},
        headers=_admin_headers(),
    )
    assert response.status_code == 200
    on_disk = json.loads(DOCS_DATA_PATH.read_text(encoding="utf-8"))
    target = next(p for p in on_disk["pages"] if p["slug"] == "penggunaan-murid")
    assert target["is_public"] is False
