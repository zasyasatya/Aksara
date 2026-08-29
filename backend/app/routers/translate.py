from fastapi import APIRouter, HTTPException, Request
from ..schemas.translate import (
    TranslateRequest, TranslateResponse, 
    BatchTranslateRequest, BatchTranslateResponse,
    GantunganAnalyzeRequest, GantunganAnalyzeResponse
)
from ..services.transliterator import transliterate, analyze_gantungan
from ..core.config import settings
import time
from collections import defaultdict

router = APIRouter(prefix="/translate", tags=["translate"])

# Simple in-memory rate limiting
request_counts = defaultdict(list)

def check_rate_limit(ip: str):
    now = time.time()
    # Clean old entries (older than 60s)
    request_counts[ip] = [t for t in request_counts[ip] if now - t < 60]
    if len(request_counts[ip]) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} per minute")
    request_counts[ip].append(now)

@router.post("", response_model=TranslateResponse)
async def translate_text(req: TranslateRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)
    
    if len(req.text) > settings.max_text_length:
        raise HTTPException(status_code=400, detail=f"Text too long, max {settings.max_text_length}")
    
    use_dict = True
    if req.options:
        use_dict = req.options.use_dictionary
    
    try:
        result, breakdown, warnings = transliterate(req.text, req.direction, use_dict)
        confidence = 0.95
        if warnings:
            confidence = 0.85
        # Check if result still contains latin when should be bali
        if req.direction == "latin-to-bali" and any(c.isascii() and c.isalpha() and c not in [" ", ",", "."] for c in result):
            # Might have untranslated parts
            confidence = 0.7
        
        return TranslateResponse(
            original=req.text,
            result=result,
            direction=req.direction,
            breakdown=breakdown,
            confidence=confidence,
            warnings=warnings
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transliteration failed: {str(e)}")

@router.post("/batch", response_model=BatchTranslateResponse)
async def translate_batch(req: BatchTranslateRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)
    
    results = []
    for item in req.items:
        if len(item.text) > settings.max_text_length:
            raise HTTPException(status_code=400, detail=f"Text too long: {item.text[:20]}...")
        try:
            result, breakdown, warnings = transliterate(item.text, item.direction, True)
            results.append(TranslateResponse(
                original=item.text,
                result=result,
                direction=item.direction,
                breakdown=breakdown,
                confidence=0.95 if not warnings else 0.85,
                warnings=warnings
            ))
        except Exception as e:
            results.append(TranslateResponse(
                original=item.text,
                result="",
                direction=item.direction,
                breakdown=[],
                confidence=0.0,
                warnings=[str(e)]
            ))
    
    return BatchTranslateResponse(results=results)

@router.post("/gantungan/analyze", response_model=GantunganAnalyzeResponse)
async def analyze_gantungan_endpoint(req: GantunganAnalyzeRequest):
    try:
        analysis = analyze_gantungan(req.text, req.direction)
        return GantunganAnalyzeResponse(**analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gantungan/rules")
async def get_gantungan_rules():
    return {
        "rules": [
            {
                "id": "tumpuk-telu",
                "name": "Tumpuk Telu",
                "description": "Tidak boleh ada 2 gantungan pada 1 aksara dasar. Maksimal 1 gantungan per aksara.",
                "example_wrong": "ka + gantungan ra + gantungan ya (forbidden) - 3 lapis",
                "example_correct": "ka + gantungan ra, ya di suku kata baru dengan adeg-adeg",
                "severity": "forbidden"
            },
            {
                "id": "pepet-cakra",
                "name": "Pepet + Cakra Forbidden",
                "description": "Kombinasi pepet (◌ᭂ) dan cakra (◌᭄ᬭ) tidak diperbolehkan karena secara fonetik tidak mungkin",
                "example_wrong": "kra + pepet (krě)",
                "example_correct": "Gunakan alternatif penulisan atau pisah suku kata",
                "severity": "forbidden"
            },
            {
                "id": "la-pepet-allowed",
                "name": "La Gantungan + Pepet Allowed",
                "description": "Kombinasi gantungan La (◌᭄ᬮ) + Pepet (◌ᭂ) DIPERBOLEHKAN, contoh bleganjur ᬩᬼᬕᬜ᭄ᬚᬸᬃ",
                "example_correct": "ᬩᬼᬕᬜ᭄ᬚᬸᬃ bleganjur",
                "severity": "allowed"
            },
            {
                "id": "gantungan-usage",
                "name": "Penggunaan Gantungan",
                "description": "Gantungan digunakan untuk konsonan rangkap di tengah kata, menghilangkan vokal inheren /a/ dari aksara sebelumnya",
                "example_correct": "dharma = da + surang + ma gantungan = ᬤᬃᬫ",
                "severity": "rule"
            },
            {
                "id": "adeg-adeg-final",
                "name": "Adeg-adeg untuk Akhiran",
                "description": "Adeg-adeg (◌᭄) digunakan untuk mematikan vokal inheren di akhir kata yang berakhir konsonan",
                "example_correct": "anak = a + na + ka + adeg-adeg = ᬅᬦᬓ᭄",
                "severity": "rule"
            },
            {
                "id": "cecek-vs-nga",
                "name": "Cecek vs Nga Gantungan",
                "description": "Cecek (◌ᬂ) untuk akhiran ng, sedangkan Nga gantungan (◌᭄ᬗ) untuk cluster medial seperti angka",
                "example_correct": "angklung = ᬅᬗ᭄ᬓ᭄ᬮᬸᬂ (cecek di akhir), angka = ᬅᬗ᭄ᬓ (nga gantungan)",
                "severity": "rule"
            }
        ]
    }
