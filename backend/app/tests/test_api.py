import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

def test_root():
    response = client.get("/")
    assert response.status_code == 200

def test_translate_latin_to_bali():
    response = client.post("/api/translate", json={
        "text": "bali",
        "direction": "latin-to-bali"
    })
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert len(data["result"]) > 0
    assert data["original"] == "bali"

def test_translate_bali_to_latin():
    response = client.post("/api/translate", json={
        "text": "ᬩᬮᬶ",
        "direction": "bali-to-latin"
    })
    assert response.status_code == 200
    data = response.json()
    assert "result" in data

def test_translate_batch():
    response = client.post("/api/translate/batch", json={
        "items": [
            {"text": "bali", "direction": "latin-to-bali"},
            {"text": "ᬩᬮᬶ", "direction": "bali-to-latin"}
        ]
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2

def test_classify():
    response = client.post("/api/classify", json={"text": "ᬩ"})
    assert response.status_code == 200
    data = response.json()
    assert "classifications" in data

def test_classify_types():
    response = client.get("/api/classify/types")
    assert response.status_code == 200
    data = response.json()
    assert "types" in data

def test_lessons():
    response = client.get("/api/lessons")
    assert response.status_code == 200
    data = response.json()
    assert "lessons" in data
    assert data["total"] > 0

def test_lesson_detail():
    response = client.get("/api/lessons/wresastra-01")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "wresastra-01"

def test_quiz_list():
    response = client.get("/api/quiz")
    assert response.status_code == 200
    data = response.json()
    assert "quizzes" in data

def test_quiz_check():
    # Get a quiz first
    response = client.get("/api/quiz?limit=1")
    quizzes = response.json()["quizzes"]
    if quizzes:
        quiz_id = quizzes[0]["id"]
        correct = quizzes[0]["correct_answer"]
        check_resp = client.post("/api/quiz/check", json={
            "quiz_id": quiz_id,
            "answer": correct
        })
        assert check_resp.status_code == 200
        check_data = check_resp.json()
        assert check_data["correct"] == True

def test_validate_pair():
    response = client.post("/api/quiz/validate-pair", json={
        "question_latin": "bali",
        "question_bali": "ᬩᬮᬶ",
        "user_bali": "ᬩᬮᬶ",
        "mode": "exact"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] == True

def test_gantungan_rules():
    response = client.get("/api/translate/gantungan/rules")
    assert response.status_code == 200
    data = response.json()
    assert "rules" in data

def test_gantungan_analyze():
    response = client.post("/api/translate/gantungan/analyze", json={
        "text": "dharma",
        "direction": "latin-to-bali"
    })
    assert response.status_code == 200
    data = response.json()
    assert "has_gantungan" in data
