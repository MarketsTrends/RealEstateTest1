from __future__ import annotations

from fastapi import APIRouter

from app.schemas import AnalysisRequest, AnalysisResponse
from app.services.analysis_service import run_analysis

router = APIRouter(prefix="", tags=["analysis"])


@router.post("/analysis", response_model=AnalysisResponse)
def post_analysis(payload: AnalysisRequest) -> AnalysisResponse:
    return run_analysis(payload)
