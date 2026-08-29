import json
import unicodedata
from pathlib import Path
from typing import Dict, List, Tuple
import random

DATA_DIR = Path(__file__).parent.parent / "data"

with open(DATA_DIR / "quiz.json", "r", encoding="utf-8") as f:
    QUIZZES = json.load(f)

with open(DATA_DIR / "lessons.json", "r", encoding="utf-8") as f:
    LESSONS = json.load(f)

QUIZ_BY_ID = {q["id"]: q for q in QUIZZES}
LESSON_BY_ID = {l["id"]: l for l in LESSONS}

def normalize_bali(text: str) -> str:
    """Normalize Balinese text for comparison"""
    if not text:
        return ""
    # NFC normalization
    text = unicodedata.normalize('NFC', text)
    # Trim
    text = text.strip()
    return text

def check_answer(quiz_id: str, answer, user_input: str = None) -> Dict:
    """Check quiz answer"""
    quiz = QUIZ_BY_ID.get(quiz_id)
    if not quiz:
        return {"error": "Quiz not found", "quiz_id": quiz_id}
    
    correct_answer = quiz.get("correct_answer")
    explanation = quiz.get("explanation", "")
    
    is_correct = False
    feedback_type = "error"
    feedback_message = "Ups, kurang tepat"
    details = ""
    xp_earned = 0
    
    q_type = quiz.get("type", "multiple_choice")
    
    if q_type == "multiple_choice" or q_type == "gantungan_choice":
        # answer is option id like "a", "b"
        is_correct = (str(answer).lower() == str(correct_answer).lower())
    elif q_type == "true_false":
        is_correct = (str(answer).lower() == str(correct_answer).lower())
    elif q_type == "arrangement":
        # answer is list of bali chars or string
        # Compare normalized
        expected_bali = ""
        # Find correct option bali
        for opt in quiz.get("options", []):
            if opt.get("is_correct") or opt.get("id") == correct_answer:
                expected_bali = opt.get("bali", "")
                break
        # If user_input provided as string
        user_bali = user_input if user_input else "".join(answer) if isinstance(answer, list) else str(answer)
        is_correct = normalize_bali(user_bali) == normalize_bali(expected_bali)
        if not is_correct:
            details = f"Expected: {expected_bali}, Got: {user_bali}"
    else:
        is_correct = (str(answer) == str(correct_answer))
    
    if is_correct:
        feedback_type = "success"
        feedback_message = "Mantap! Kamu benar 🎉"
        xp_earned = quiz.get("xp", 10)
        details = explanation
    else:
        feedback_type = "error"
        feedback_message = "Hampir benar! Coba lagi"
        # Provide correct answer
        correct_bali = ""
        correct_latin = ""
        for opt in quiz.get("options", []):
            if opt.get("is_correct") or opt.get("id") == correct_answer:
                correct_bali = opt.get("bali", "")
                correct_latin = opt.get("latin", "")
                break
        details = explanation
        # Additional feedback for gantungan errors
        if "gantungan" in quiz_id or q_type == "gantungan_choice":
            details += " Perhatikan penggunaan gantungan vs adeg-adeg dan aturan tumpuk telu."
    
    # Find next quiz in same lesson
    next_quiz = None
    lesson_id = quiz.get("lesson_id")
    if lesson_id and lesson_id in LESSON_BY_ID:
        lesson = LESSON_BY_ID[lesson_id]
        quiz_ids = lesson.get("quiz_ids", [])
        try:
            idx = quiz_ids.index(quiz_id)
            if idx + 1 < len(quiz_ids):
                next_quiz = quiz_ids[idx + 1]
        except ValueError:
            pass
    
    return {
        "quiz_id": quiz_id,
        "correct": is_correct,
        "correct_answer": correct_answer,
        "user_answer": answer,
        "explanation": explanation,
        "xp_earned": xp_earned,
        "feedback": {
            "type": feedback_type,
            "message": feedback_message,
            "details": details,
            "correct_bali": correct_bali if not is_correct else "",
            "correct_latin": correct_latin if not is_correct else ""
        },
        "next_quiz": next_quiz
    }

def validate_pair(question_latin: str, question_bali: str, user_bali: str, mode: str = "exact") -> Dict:
    """Validate if user_bali is correct for given latin"""
    from .transliterator import transliterate_latin_to_bali
    
    # Normalize
    q_bali_norm = normalize_bali(question_bali)
    user_bali_norm = normalize_bali(user_bali)
    
    # If exact mode, direct compare
    if mode == "exact":
        is_correct = q_bali_norm == user_bali_norm
        similarity = 1.0 if is_correct else 0.0
        differences = []
        if not is_correct:
            # Simple diff: compare chars
            # For detailed, we could use difflib
            import difflib
            matcher = difflib.SequenceMatcher(None, q_bali_norm, user_bali_norm)
            similarity = matcher.ratio()
            # Find differences
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag != 'equal':
                    differences.append({
                        "type": tag,
                        "expected": q_bali_norm[i1:i2],
                        "got": user_bali_norm[j1:j2],
                        "position": i1,
                        "reason": f"Perbedaan pada posisi {i1}: diharapkan '{q_bali_norm[i1:i2]}' tapi dapat '{user_bali_norm[j1:j2]}'"
                    })
        
        suggestions = []
        if not is_correct:
            # Check common mistakes
            if "ᬶ" not in user_bali_norm and "ᬶ" in q_bali_norm:
                suggestions.append("Kamu kehilangan ulu (◌ᬶ) untuk vokal i")
            if "ᬸ" not in user_bali_norm and "ᬸ" in q_bali_norm:
                suggestions.append("Kamu kehilangan suku (◌ᬸ) untuk vokal u")
            if "᭄" not in user_bali_norm and "᭄" in q_bali_norm:
                suggestions.append("Seharusnya pakai adeg-adeg (◌᭄) untuk mematikan vokal atau membentuk gantungan")
            if "ᬂ" not in user_bali_norm and "ᬂ" in q_bali_norm:
                suggestions.append("Seharusnya pakai cecek (◌ᬂ) untuk akhiran ng")
            if "ᬃ" not in user_bali_norm and "ᬃ" in q_bali_norm:
                suggestions.append("Seharusnya pakai surang (◌ᬃ) untuk akhiran r")
            if "ᬄ" not in user_bali_norm and "ᬄ" in q_bali_norm:
                suggestions.append("Seharusnya pakai bisah (◌ᬄ) untuk akhiran h")
        
        return {
            "is_correct": is_correct,
            "similarity": similarity,
            "differences": differences,
            "suggestions": suggestions,
            "expected": q_bali_norm,
            "got": user_bali_norm
        }
    else:  # tolerant mode
        # Use transliterator to generate expected from latin and compare
        expected_bali, _, _ = transliterate_latin_to_bali(question_latin)
        expected_norm = normalize_bali(expected_bali)
        user_norm = normalize_bali(user_bali)
        is_correct = expected_norm == user_norm
        # Also check if user matches question_bali (if provided)
        if question_bali:
            is_correct = is_correct or (normalize_bali(question_bali) == user_norm)
        
        import difflib
        similarity = difflib.SequenceMatcher(None, expected_norm, user_norm).ratio()
        
        return {
            "is_correct": is_correct,
            "similarity": similarity,
            "differences": [],
            "suggestions": [],
            "expected": expected_norm,
            "got": user_norm,
            "question_bali": q_bali_norm
        }

def get_quizzes(filters: Dict = None) -> List[Dict]:
    """Get quizzes with filters"""
    if not filters:
        return QUIZZES
    
    result = QUIZZES
    
    if "lesson_id" in filters and filters["lesson_id"]:
        result = [q for q in result if q.get("lesson_id") == filters["lesson_id"]]
    
    if "type" in filters and filters["type"]:
        result = [q for q in result if q.get("type") == filters["type"]]
    
    if "difficulty" in filters and filters["difficulty"]:
        result = [q for q in result if q.get("difficulty") == filters["difficulty"]]
    
    limit = filters.get("limit", 10)
    if limit:
        # Shuffle for variety? But deterministic for testing? Use random sample
        if len(result) > limit:
            result = random.sample(result, limit)
        else:
            result = result[:limit]
    
    return result

def get_quiz_by_id(quiz_id: str):
    return QUIZ_BY_ID.get(quiz_id)
