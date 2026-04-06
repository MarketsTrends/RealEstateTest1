from __future__ import annotations

from fastapi import APIRouter

from app.schemas import AnalysisRequest, MemoResponse
from app.services.memo_service import generate_memo
from app.settings import get_settings

router = APIRouter(prefix="", tags=["memo"])


@router.post("/memo", response_model=MemoResponse)
def post_memo(payload: AnalysisRequest) -> MemoResponse:
    return generate_memo(payload, get_settings())
