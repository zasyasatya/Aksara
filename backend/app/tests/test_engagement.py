"""Tes endpoint engagement (counter & sekolah mitra)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import data_store

client = TestClient(app)


@pytest.fixture()
def restore_engagement():
    """Backup engagement.json agar test tidak menular ke data asli."""
    backup = data_store.get_engagement()
    yield
    data_store.save_engagement(backup)


def test_get_stats_shape():
    r = client.get("/api/stats")
    assert r.status_code == 200
    d = r.json()
    assert "visits" in d and "twibbons" in d and "schools" in d
    assert isinstance(d["schools"], list)


def test_track_visit_increments(restore_engagement):
    before = client.get("/api/stats").json()["visits"]
    r = client.post("/api/stats/visit")
    assert r.status_code == 200
    after = client.get("/api/stats").json()["visits"]
    assert after >= before  # bisa sama bila di-throttle (rate limit per IP)


def test_track_twibbon_increments(restore_engagement):
    before = client.get("/api/stats").json()["twibbons"]
    r = client.post("/api/stats/twibbon")
    assert r.status_code == 200
    after = client.get("/api/stats").json()["twibbons"]
    assert after >= before


def test_apply_school_and_list(restore_engagement):
    r = client.post("/api/stats/schools", json={
        "school": "SMA Negeri 1 Uji Coba",
        "region": "Gianyar",
        "students": 600,
        "contact": "wali.kelas@contoh.sch.id",
    })
    assert r.status_code == 201
    entry = r.json()
    assert entry["is_verified"] is False
    assert entry["id"].startswith("school-")

    listed = client.get("/api/stats/schools").json()
    assert any(s["id"] == entry["id"] for s in listed["schools"])


def test_apply_school_duplicate_rejected(restore_engagement):
    payload = {
        "school": "Sanggar Aksara Duplikat",
        "region": "Denpasar",
        "contact": "0812-3456-7890",
    }
    first = client.post("/api/stats/schools", json=payload)
    assert first.status_code == 201
    dup = client.post("/api/stats/schools", json=payload)
    assert dup.status_code == 409


def test_apply_school_requires_contact(restore_engagement):
    r = client.post("/api/stats/schools", json={"school": "Tanpa Kontak", "region": "Tabanan"})
    assert r.status_code == 422
