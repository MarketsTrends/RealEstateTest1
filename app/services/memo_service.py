from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from fastapi import HTTPException

from app.schemas import AnalysisRequest, MemoResponse
from app.services.analysis_service import run_analysis
from app.services.comps_service import get_sales_comps
from app.settings import Settings
from app.llm.memo_prompt import SYSTEM_PROMPT, user_prompt


def build_memo_context(
    payload: AnalysisRequest,
    *,
    analysis: Any,
    comps: Any | None,
) -> dict[str, Any]:
    return {
        "request": payload.model_dump(),
        "analysis": analysis.model_dump(),
        "comps": comps.model_dump() if comps is not None else None,
        "notes": {
            "pre_tax_only": True,
            "rule": "AI explanation only; deterministic metrics must not be recalculated",
        },
    }


def _call_openai_json(*, api_key: str, model: str, context: dict[str, Any]) -> dict[str, Any]:
    url = "https://api.openai.com/v1/chat/completions"
    body = {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt(json.dumps(context, ensure_ascii=False))},
        ],
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise HTTPException(status_code=502, detail=f"Memo generation failed: {detail}") from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"Memo generation failed: {exc}") from exc

    content = payload["choices"][0]["message"]["content"]
    try:
        return json.loads(content)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Memo provider returned invalid JSON") from exc


def generate_memo(payload: AnalysisRequest, settings: Settings) -> MemoResponse:
    if not settings.openai_api_key:
        raise HTTPException(status_code=503, detail="Memo feature unavailable: OPENAI_API_KEY not configured")

    analysis = run_analysis(payload)

    comps = None
    if payload.property.lat is not None and payload.property.lon is not None:
        try:
            comps = get_sales_comps(
                database_url=settings.database_url,
                lat=payload.property.lat,
                lon=payload.property.lon,
                radius_m=1000,
                months_back=24,
                property_type=payload.property.property_type,
                surface_m2=payload.property.surface_m2,
                surface_tolerance_pct=0.2,
            )
        except Exception:
            comps = None

    context = build_memo_context(payload, analysis=analysis, comps=comps)
    output = _call_openai_json(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        context=context,
    )
    return MemoResponse(**output)
