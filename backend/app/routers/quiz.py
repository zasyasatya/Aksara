from fastapi import APIRouter, Query, HTTPException
from ..schemas.quiz import (
    QuizListResponse, QuizItem, QuizQuestion, QuizOption,
    QuizCheckRequest, QuizCheckResponse,
    ValidatePairRequest, ValidatePairResponse
)
from ..services.quiz_engine import get_quizzes, get_quiz_by_id, check_answer, validate_pair
from typing import Optional

router = APIRouter(prefix="/quiz", tags=["quiz"])

@router.get("", response_model=QuizListResponse)
async def list_quizzes(
    lesson_id: Optional[str] = Query(None),
    type: Optional[str] = Query(None, alias="type"),
    difficulty: Optional[str] = Query(None),
    limit: int = Query(10, le=50)
):
    filters = {
        "lesson_id": lesson_id,
        "type": type,
        "difficulty": difficulty,
        "limit": limit
    }
    quizzes = get_quizzes(filters)
    
    # Convert to response model
    items = []
    for q in quizzes:
        # Build question
        q_data = q.get("question", {})
        question = QuizQuestion(
            text=q_data.get("text", ""),
            latin=q_data.get("latin"),
            bali=q_data.get("bali"),
            pair=q_data.get("pair"),
            hint=q_data.get("hint")
        )
        options = []
        for opt in q.get("options", []):
            options.append(QuizOption(
                id=opt.get("id", ""),
                bali=opt.get("bali"),
                latin=opt.get("latin"),
                label=opt.get("label"),
                is_correct=opt.get("is_correct")
            ))
        items.append(QuizItem(
            id=q["id"],
            lesson_id=q.get("lesson_id"),
            type=q.get("type", "multiple_choice"),
            difficulty=q.get("difficulty", "easy"),
            question=question,
            options=options,
            correct_answer=q.get("correct_answer", ""),
            explanation=q.get("explanation"),
            xp=q.get("xp", 10),
            tags=q.get("tags")
        ))
    
    return QuizListResponse(quizzes=items, total=len(items))

@router.get("/{quiz_id}", response_model=QuizItem)
async def get_quiz(quiz_id: str):
    q = get_quiz_by_id(quiz_id)
    if not q:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    q_data = q.get("question", {})
    question = QuizQuestion(
        text=q_data.get("text", ""),
        latin=q_data.get("latin"),
        bali=q_data.get("bali"),
        pair=q_data.get("pair"),
        hint=q_data.get("hint")
    )
    options = [QuizOption(**opt) for opt in q.get("options", [])]
    
    return QuizItem(
        id=q["id"],
        lesson_id=q.get("lesson_id"),
        type=q.get("type", "multiple_choice"),
        difficulty=q.get("difficulty", "easy"),
        question=question,
        options=options,
        correct_answer=q.get("correct_answer", ""),
        explanation=q.get("explanation"),
        xp=q.get("xp", 10),
        tags=q.get("tags")
    )

@router.post("/check", response_model=QuizCheckResponse)
async def check_quiz_answer(req: QuizCheckRequest):
    result = check_answer(req.quiz_id, req.answer, req.user_input)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return QuizCheckResponse(**result)

@router.post("/validate-pair", response_model=ValidatePairResponse)
async def validate_pair_endpoint(req: ValidatePairRequest):
    result = validate_pair(req.question_latin, req.question_bali, req.user_bali, req.mode)
    return ValidatePairResponse(**result)
