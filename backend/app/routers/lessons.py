from fastapi import APIRouter, HTTPException, Query
from ..schemas.lessons import LessonListResponse, LessonDetailResponse, LessonSummary, AksaraDetail
from typing import List, Optional
import json
from pathlib import Path

router = APIRouter(prefix="/lessons", tags=["lessons"])

DATA_DIR = Path(__file__).parent.parent / "data"

with open(DATA_DIR / "lessons.json", "r", encoding="utf-8") as f:
    LESSONS = json.load(f)

with open(DATA_DIR / "aksara_master.json", "r", encoding="utf-8") as f:
    MASTER = json.load(f)

# Build aksara lookup
AKSARA_LOOKUP = {}
for cat in ["wresastra", "swalalita_extra", "suara"]:
    for item in MASTER.get(cat, []):
        AKSARA_LOOKUP[item["id"]] = item
for cat in ["pangangge_suara", "pangangge_tengenan", "pangangge_aksara"]:
    for item in MASTER.get(cat, []):
        AKSARA_LOOKUP[item["id"]] = item

LESSON_BY_ID = {l["id"]: l for l in LESSONS}

@router.get("", response_model=LessonListResponse)
async def list_lessons(
    level: Optional[int] = Query(None, description="Filter by level"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search title"),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0)
):
    filtered = LESSONS
    
    if level is not None:
        filtered = [l for l in filtered if l.get("level") == level]
    
    if category:
        filtered = [l for l in filtered if l.get("category") == category]
    
    if search:
        search_lower = search.lower()
        filtered = [l for l in filtered if search_lower in l.get("title", "").lower() or search_lower in l.get("description", "").lower()]
    
    total = len(filtered)
    paginated = filtered[offset:offset+limit]
    
    level_info = {
        "1": {"name": "Pemula", "description": "Wresastra dasar Ha Na Ca Ra Ka", "color": "#FF6B35"},
        "2": {"name": "Pangangge Suara", "description": "Vokal I, U, E, O", "color": "#7A9E7E"},
        "3": {"name": "Pangangge Tengenan", "description": "Akhiran H, R, NG", "color": "#2A6F8E"},
        "4": {"name": "Gantungan", "description": "Konsonan rangkap & cluster", "color": "#C45A3C"},
        "5": {"name": "Swalalita", "description": "Sanskerta & Kawi", "color": "#2C1810"},
        "6": {"name": "Kalimat", "description": "Merangkai kalimat", "color": "#F9A825"},
    }
    
    return LessonListResponse(
        lessons=[LessonSummary(**l) for l in paginated],
        total=total,
        level_info=level_info
    )

@router.get("/{lesson_id}", response_model=LessonDetailResponse)
async def get_lesson(lesson_id: str):
    lesson = LESSON_BY_ID.get(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Build aksara details
    aksara_details = []
    for aks_id in lesson.get("aksara_ids", []):
        if aks_id in AKSARA_LOOKUP:
            item = AKSARA_LOOKUP[aks_id]
            aksara_details.append(AksaraDetail(
                id=item.get("id", aks_id),
                bali=item.get("bali", ""),
                latin=item.get("latin", ""),
                name=item.get("name", ""),
                description=item.get("description", ""),
                gantungan=item.get("gantungan", ""),
                examples=item.get("examples", [])
            ))
    
    # Find next lesson
    sorted_lessons = sorted(LESSONS, key=lambda x: x.get("order", 0))
    next_lesson = None
    for idx, l in enumerate(sorted_lessons):
        if l["id"] == lesson_id and idx + 1 < len(sorted_lessons):
            next_lesson = sorted_lessons[idx+1]["id"]
            break
    
    return LessonDetailResponse(
        id=lesson["id"],
        title=lesson["title"],
        slug=lesson.get("slug"),
        description=lesson.get("description"),
        story=lesson.get("story"),
        level=lesson["level"],
        order=lesson["order"],
        category=lesson.get("category"),
        content={
            "story": lesson.get("story"),
            "aksara_ids": lesson.get("aksara_ids", []),
            "pangangge_ids": lesson.get("pangangge_ids", []),
            "learning_points": lesson.get("content", {}).get("learning_points", []) if isinstance(lesson.get("content"), dict) else []
        },
        aksara_details=aksara_details,
        estimated_minutes=lesson.get("estimated_minutes", 10),
        xp_reward=lesson.get("xp_reward", 50),
        prerequisites=lesson.get("prerequisites", []),
        quiz_ids=lesson.get("quiz_ids", []),
        next_lesson=next_lesson,
        thumbnail=lesson.get("thumbnail")
    )
