from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ManageStatus(BaseModel):
    mode: str
    is_guru: bool
    is_admin: bool


# ── Materi (lessons) ────────────────────────────────────────────────────

class LessonIn(BaseModel):
    id: Optional[str] = Field(None, description="Kosongkan saat create → dibuat otomatis dari judul")
    title: str = Field(..., min_length=1, max_length=120)
    slug: Optional[str] = None
    description: Optional[str] = None
    story: Optional[str] = None
    level: int = Field(1, ge=1, le=6)
    order: int = 0
    category: Optional[str] = "wresastra"
    aksara_ids: List[str] = []
    pangangge_ids: List[str] = []
    estimated_minutes: int = Field(10, ge=1)
    xp_reward: int = Field(50, ge=0)
    prerequisites: List[str] = []
    quiz_ids: List[str] = []
    is_published: bool = True
    thumbnail: Optional[str] = None


# ── Kuis ────────────────────────────────────────────────────────────────

QuizType = str  # multiple_choice | true_false | gantungan_choice | write_aksara | arrangement


class QuizQuestionIn(BaseModel):
    text: str = Field("", max_length=500)
    latin: Optional[str] = None
    bali: Optional[str] = None
    pair: Optional[Dict[str, Any]] = None
    hint: Optional[str] = None


class QuizOptionIn(BaseModel):
    id: str
    bali: Optional[str] = None
    latin: Optional[str] = None
    label: Optional[str] = None
    is_correct: Optional[bool] = None


class QuizIn(BaseModel):
    id: Optional[str] = Field(None, description="Kosongkan saat create → dibuat otomatis")
    lesson_id: Optional[str] = None
    type: str = Field("multiple_choice")
    difficulty: str = Field("easy", pattern="^(easy|medium|hard)$")
    question: QuizQuestionIn = QuizQuestionIn()
    options: List[QuizOptionIn] = []
    correct_answer: Optional[str] = ""
    explanation: Optional[str] = None
    xp: int = Field(10, ge=0)
    tags: Optional[List[str]] = None


# ── Kamus (dictionary) ──────────────────────────────────────────────────

class DictIn(BaseModel):
    latin: str = Field(..., min_length=1, max_length=80)
    bali: str = Field(..., min_length=1, max_length=200)
    meaning: Optional[str] = None
    note: Optional[str] = None


class MessageResponse(BaseModel):
    message: str
