from pydantic import BaseModel, Field
from typing import List, Optional

class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=100, description="Balinese character or text to classify")

class ClassificationItem(BaseModel):
    char: str
    unicode: str
    latin: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    warga: Optional[str] = None
    description: Optional[str] = None
    gantungan_form: Optional[str] = None
    is_gantungan: bool = False
    is_pangangge: bool = False
    examples: Optional[List] = None

class ClassifyResponse(BaseModel):
    input: str
    classifications: List[ClassificationItem]
    overall_type: str
    syllable_count: int = 0
    has_gantungan: bool = False
    has_pangangge: bool = False

class TypesResponse(BaseModel):
    types: List[dict]
