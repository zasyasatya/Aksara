from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

class TranslateOptions(BaseModel):
    use_dictionary: bool = True
    strict: bool = False

class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to translate")
    direction: Literal["latin-to-bali", "bali-to-latin"] = Field(..., description="Translation direction")
    options: Optional[TranslateOptions] = None

class BreakdownItem(BaseModel):
    latin: Optional[str] = None
    bali: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    base: Optional[str] = None
    pangangge: Optional[str] = None
    pangangge_name: Optional[str] = None

class TranslateResponse(BaseModel):
    original: str
    result: str
    direction: str
    breakdown: List[Dict[str, Any]] = []
    confidence: float = 1.0
    warnings: List[str] = []

class BatchTranslateItem(BaseModel):
    text: str
    direction: Literal["latin-to-bali", "bali-to-latin"]

class BatchTranslateRequest(BaseModel):
    items: List[BatchTranslateItem] = Field(..., max_length=50)

class BatchTranslateResponse(BaseModel):
    results: List[TranslateResponse]

class GantunganAnalyzeRequest(BaseModel):
    text: str = Field(..., max_length=5000)
    direction: Literal["latin-to-bali", "bali-to-latin"] = "latin-to-bali"

class GantunganCluster(BaseModel):
    position: int
    latin: Optional[str] = None
    bali: Optional[str] = None
    type: Optional[str] = None
    explanation: Optional[str] = None

class GantunganAnalyzeResponse(BaseModel):
    original: str
    bali: str
    clusters: List[GantunganCluster] = []
    has_gantungan: bool
    gantungan_count: int
    has_tumpuk_telu: bool = False
    breakdown: List[Dict[str, Any]] = []
