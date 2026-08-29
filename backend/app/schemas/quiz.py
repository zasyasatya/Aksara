from pydantic import BaseModel, Field
from typing import List, Optional, Any, Literal

class QuizOption(BaseModel):
    id: str
    bali: Optional[str] = None
    latin: Optional[str] = None
    label: Optional[str] = None
    is_correct: Optional[bool] = None

class QuizQuestion(BaseModel):
    text: str
    latin: Optional[str] = None
    bali: Optional[str] = None
    pair: Optional[dict] = None
    hint: Optional[str] = None

class QuizItem(BaseModel):
    id: str
    lesson_id: Optional[str] = None
    type: str
    difficulty: str
    question: QuizQuestion
    options: List[QuizOption]
    correct_answer: str
    explanation: Optional[str] = None
    xp: int = 10
    tags: Optional[List[str]] = None

class QuizListResponse(BaseModel):
    quizzes: List[QuizItem]
    total: int

class QuizCheckRequest(BaseModel):
    quiz_id: str
    answer: Any = Field(..., description="Answer: option id or list")
    user_input: Optional[str] = None
    time_spent_seconds: Optional[int] = None

class QuizFeedback(BaseModel):
    type: str
    message: str
    details: Optional[str] = None
    correct_bali: Optional[str] = None
    correct_latin: Optional[str] = None

class QuizCheckResponse(BaseModel):
    quiz_id: str
    correct: bool
    correct_answer: str
    user_answer: Any
    explanation: Optional[str] = None
    xp_earned: int = 0
    feedback: QuizFeedback
    next_quiz: Optional[str] = None

class ValidatePairRequest(BaseModel):
    question_latin: str = Field(..., description="Latin question")
    question_bali: str = Field(..., description="Expected Bali answer")
    user_bali: str = Field(..., description="User's Bali answer")
    mode: Literal["exact", "tolerant"] = "exact"

class DifferenceItem(BaseModel):
    type: Optional[str] = None
    expected: Optional[str] = None
    got: Optional[str] = None
    position: Optional[int] = None
    reason: Optional[str] = None

class ValidatePairResponse(BaseModel):
    is_correct: bool
    similarity: float
    differences: List[DifferenceItem] = []
    suggestions: List[str] = []
    expected: Optional[str] = None
    got: Optional[str] = None
    question_bali: Optional[str] = None
