from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.schemas import AnalysisRequest
from app.services.report_service import build_pdf_report

router = APIRouter(prefix="", tags=["reports"])


@router.post("/report/pdf")
def post_pdf_report(payload: AnalysisRequest) -> Response:
    try:
        pdf_bytes = build_pdf_report(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    headers = {"Content-Disposition": 'attachment; filename="deal-analysis-report.pdf"'}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
