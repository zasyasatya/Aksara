from fastapi import APIRouter
from ..schemas.classify import ClassifyRequest, ClassifyResponse, TypesResponse
from ..services.classifier import classify_text, get_all_types

router = APIRouter(prefix="/classify", tags=["classify"])

@router.post("", response_model=ClassifyResponse)
async def classify(req: ClassifyRequest):
    result = classify_text(req.text)
    return ClassifyResponse(**result)

@router.get("/types", response_model=TypesResponse)
async def get_types():
    types = get_all_types()
    return TypesResponse(types=types)
