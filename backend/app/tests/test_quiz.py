import pytest
from app.services.quiz_engine import check_answer, validate_pair, get_quizzes

def test_get_quizzes():
    quizzes = get_quizzes()
    assert len(quizzes) > 0

def test_get_quizzes_filter():
    quizzes = get_quizzes({"lesson_id": "wresastra-01", "limit": 5})
    assert len(quizzes) <= 5
    assert all(q["lesson_id"] == "wresastra-01" for q in quizzes)

def test_check_correct():
    # Find a quiz
    quizzes = get_quizzes({"limit": 1})
    if quizzes:
        q = quizzes[0]
        result = check_answer(q["id"], q["correct_answer"])
        assert result["correct"] == True
        assert result["xp_earned"] > 0

def test_check_incorrect():
    quizzes = get_quizzes({"limit": 1})
    if quizzes:
        q = quizzes[0]
        # Wrong answer
        wrong = "z" if q["correct_answer"] != "z" else "y"
        result = check_answer(q["id"], wrong)
        assert result["correct"] == False

def test_validate_pair_correct():
    result = validate_pair("bali", "ᬩᬮᬶ", "ᬩᬮᬶ", "exact")
    assert result["is_correct"] == True
    assert result["similarity"] == 1.0

def test_validate_pair_incorrect():
    result = validate_pair("bali", "ᬩᬮᬶ", "ᬩᬮ", "exact")
    assert result["is_correct"] == False
    assert result["similarity"] < 1.0
    assert len(result["differences"]) > 0 or len(result["suggestions"]) >= 0

def test_validate_pair_tolerant():
    result = validate_pair("bali", "ᬩᬮᬶ", "ᬩᬮᬶ", "tolerant")
    assert result["is_correct"] == True
