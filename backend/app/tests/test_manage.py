import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.services import data_store

client = TestClient(app)


@pytest.fixture
def restore_data():
    """Backup data dinamis agar test CRUD tidak menular."""
    backup = {
        "lessons": data_store.get_lessons(),
        "quizzes": data_store.get_quizzes(),
        "dictionary": data_store.get_dictionary(),
    }
    yield
    data_store.save_lessons(backup["lessons"])
    data_store.save_quizzes(backup["quizzes"])
    data_store.save_dictionary(backup["dictionary"])


@pytest.fixture
def prod_mode(monkeypatch):
    monkeypatch.setattr(settings, "mode", "prod")
    yield
    monkeypatch.setattr(settings, "mode", "dev")


# ── Status ──────────────────────────────────────────────────────────────

def test_status_dev_is_guru():
    r = client.get("/api/manage/status").json()
    assert r["mode"] == "dev"
    assert r["is_guru"] is True


# ── Materi (lessons) ────────────────────────────────────────────────────

def test_lesson_crud_flow(restore_data):
    # create (id otomatis)
    r = client.post("/api/manage/lessons", json={
        "title": "Materi Uji Coba", "level": 2, "order": 99,
        "description": "deskripsi uji", "aksara_ids": ["ha", "na"],
        "xp_reward": 30, "estimated_minutes": 5,
    })
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["id"].startswith("materi-uji-coba")
    assert created["is_published"] is True

    # langsung terlihat di endpoint publik /api/lessons (baca per-request)
    pub = client.get("/api/lessons", params={"search": "Materi Uji"}).json()
    assert pub["total"] == 1
    assert pub["lessons"][0]["title"] == "Materi Uji Coba"

    # detail
    detail = client.get(f"/api/lessons/{created['id']}").json()
    assert detail["aksara_details"][0]["id"] == "ha"

    # update
    r = client.put(f"/api/manage/lessons/{created['id']}", json={
        "title": "Materi Sudah Diubah", "level": 3, "xp_reward": 40,
        "is_published": False,
    })
    assert r.status_code == 200
    assert r.json()["title"] == "Materi Sudah Diubah"
    assert r.json()["level"] == 3
    assert r.json()["is_published"] is False

    # delete
    r = client.delete(f"/api/manage/lessons/{created['id']}")
    assert r.status_code == 200
    assert client.get(f"/api/lessons/{created['id']}").status_code == 404


def test_lesson_create_duplicate_id_409(restore_data):
    r = client.post("/api/manage/lessons", json={"title": "Duplikat", "id": "wresastra-01"})
    assert r.status_code == 409


def test_lesson_auto_id_uniqueness(restore_data):
    r1 = client.post("/api/manage/lessons", json={"title": "Bali Indah"})
    r2 = client.post("/api/manage/lessons", json={"title": "Bali Indah"})
    assert r1.status_code == 201 and r2.status_code == 201
    assert r1.json()["id"] != r2.json()["id"]


# ── Kuis ────────────────────────────────────────────────────────────────

def test_quiz_crud_flow(restore_data):
    # create
    r = client.post("/api/manage/quizzes", json={
        "lesson_id": "wresastra-01", "type": "write_aksara", "difficulty": "easy",
        "question": {"text": "Tuliskan kata 'bali'", "latin": "bali", "bali": "ᬩ",
                     "hint": "ba + li"},
        "options": [], "correct_answer": "", "explanation": "uji", "xp": 15,
    })
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["type"] == "write_aksara"

    # terlihat di /api/quiz
    lst = client.get("/api/quiz", params={"type": "write_aksara", "limit": 50}).json()
    assert any(q["id"] == created["id"] for q in lst["quizzes"])

    # update
    r = client.put(f"/api/manage/quizzes/{created['id']}", json={
        "lesson_id": "wresastra-01", "type": "write_aksara", "difficulty": "medium",
        "question": {"text": "Tuliskan kata 'bali' (perbarui)", "latin": "bali", "bali": "ᬩᬶ"},
        "options": [], "correct_answer": "", "explanation": "uji update", "xp": 20,
    })
    assert r.status_code == 200
    assert r.json()["difficulty"] == "medium"
    assert r.json()["xp"] == 20

    # delete
    r = client.delete(f"/api/manage/quizzes/{created['id']}")
    assert r.status_code == 200
    assert client.get(f"/api/quiz/{created['id']}").status_code == 404


def test_quiz_delete_cleans_lesson_refs(restore_data):
    # buat kuis, lalu rangkai ke materi
    r = client.post("/api/manage/quizzes", json={
        "id": "quiz-uji-ref", "lesson_id": "wresastra-01", "type": "true_false",
        "question": {"text": "uji"}, "options": [], "correct_answer": "a",
    })
    quiz_id = r.json()["id"]
    client.put("/api/manage/lessons/wresastra-01", json={
        "title": "Ha Na Ca Ra Ka", "level": 1, "order": 1,
        "quiz_ids": [quiz_id],
    })
    client.delete(f"/api/manage/quizzes/{quiz_id}")
    lesson = client.get("/api/lessons/wresastra-01").json()
    assert quiz_id not in lesson["quiz_ids"]


# ── Kamus ───────────────────────────────────────────────────────────────

SAMPLE_BALI = chr(0x1B22) + chr(0x1B38) + chr(0x1B13) + chr(0x1B38) + " " + chr(0x1B2B) + chr(0x1B13)


def test_dictionary_upsert_delete(restore_data):
    r = client.post("/api/manage/dictionary", json={
        "latin": "Uji Kata", "bali": SAMPLE_BALI, "meaning": "pengujian", "note": "test",
    })
    assert r.status_code == 201
    assert r.json()["bali"] == SAMPLE_BALI

    entries = client.get("/api/manage/dictionary").json()
    assert any(e["latin"].lower() == "uji kata" for e in entries["entries"])

    # upsert (perbarui)
    r = client.post("/api/manage/dictionary", json={
        "latin": "uji kata", "bali": SAMPLE_BALI, "meaning": "perbarui",
    })
    assert r.status_code == 201
    assert r.json()["meaning"] == "perbarui"

    # delete
    r = client.delete("/api/manage/dictionary/Uji%20Kata")
    assert r.status_code == 200
    entries = client.get("/api/manage/dictionary").json()
    assert not any(e["latin"].lower() == "uji kata" for e in entries["entries"])


# ── Prod mode: auth ─────────────────────────────────────────────────────

def test_prod_blocks_without_token(restore_data, prod_mode):
    assert client.post("/api/manage/lessons", json={"title": "X"}).status_code == 403
    assert client.delete("/api/manage/quizzes/quiz-wres-01-1").status_code == 403
    assert client.post("/api/manage/dictionary", json={"latin": "x", "bali": "y"}).status_code == 403

    # token guru benar → boleh
    tok = {"X-Admin-Token": settings.guru_token}
    r = client.post("/api/manage/lessons", json={"title": "Uji Prod", "id": "uji-prod"}, headers=tok)
    assert r.status_code == 201
    assert client.delete("/api/manage/lessons/uji-prod", headers=tok).status_code == 200

    # status memuat is_guru sesuai token
    assert client.get("/api/manage/status").json()["is_guru"] is False
    assert client.get("/api/manage/status", headers=tok).json()["is_guru"] is True


def test_prod_accepts_admin_token_too(restore_data, prod_mode):
    tok = {"X-Admin-Token": settings.admin_token}
    r = client.get("/api/manage/status", headers=tok)
    assert r.json()["is_guru"] is True
    assert r.json()["is_admin"] is True
