from pydantic import BaseModel
from typing import List, Optional

class LessonSummary(BaseModel):
    id: str
    title: str
    slug: Optional[str] = None
    description: Optional[str] = None
    story: Optional[str] = None
    level: int
    order: int
    category: Optional[str] = None
    aksara_ids: List[str] = []
    pangangge_ids: List[str] = []
    estimated_minutes: int = 10
    xp_reward: int = 50
    prerequisites: List[str] = []
    quiz_ids: List[str] = []
    is_published: bool = True
    thumbnail: Optional[str] = None

class LessonListResponse(BaseModel):
    lessons: List[LessonSummary]
    total: int
    level_info: Optional[dict] = None

class AksaraDetail(BaseModel):
    id: str
    bali: str
    latin: str
    name: str
    description: Optional[str] = None
    gantungan: Optional[str] = None
    examples: Optional[List[dict]] = None

class PanganggeDetail(BaseModel):
    id: str
    bali: str
    name: str
    latin_effect: str = ""
    # Template tampilan: ◌ (dotted circle) menandai posisi aksara dasar yang
    # bisa "diisi" — mis. ulu = "◌ᬶ", taleng = "◌ᬾ", taleng tedong = "◌ᭀ".
    mark: str = ""
    position: Optional[str] = None
    description: Optional[str] = None

class LessonDetailResponse(BaseModel):
    id: str
    title: str
    slug: Optional[str] = None
    description: Optional[str] = None
    story: Optional[str] = None
    level: int
    order: int
    category: Optional[str] = None
    content: Optional[dict] = None
    aksara_details: Optional[List[AksaraDetail]] = None
    pangangge_details: Optional[List[PanganggeDetail]] = None
    estimated_minutes: int
    xp_reward: int
    prerequisites: List[str] = []
    quiz_ids: List[str] = []
    next_lesson: Optional[str] = None
    thumbnail: Optional[str] = None
