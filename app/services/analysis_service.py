from __future__ import annotations

from datetime import datetime, timezone

from app.engine import ENGINE_VERSION
from app.engine.analysis import analyze_financials
from app.engine.risk_flags import build_risk_flags
from app.engine.scenarios import scenario_inputs
from app.schemas import (
    AnalysisMeta,
    AnalysisRequest,
    AnalysisResponse,
    ScenarioOutput,
    YearlyProjection,
    rounded_metrics,
)


def run_analysis(payload: AnalysisRequest) -> AnalysisResponse:
    base_metrics, warnings, _cashflows, yearly = analyze_financials(payload)

    risk_flags = build_risk_flags(
        payload,
        dscr_value=base_metrics["dscr"],
        break_even_occupancy_value=base_metrics["break_even_occupancy"],
    )

    scenarios: dict[str, ScenarioOutput] = {}
    for name, (deltas, scenario_payload) in scenario_inputs(payload).items():
        scenario_metrics, _, _, _ = analyze_financials(scenario_payload)
        scenarios[name] = ScenarioOutput(deltas=deltas, metrics=rounded_metrics(scenario_metrics))

    return AnalysisResponse(
        meta=AnalysisMeta(
            engine_version=ENGINE_VERSION,
            created_at=datetime.now(timezone.utc),
            warnings=warnings,
        ),
        metrics=rounded_metrics(base_metrics),
        risk_flags=risk_flags,
        pro_forma_yearly=[
            YearlyProjection(**{k: round(v, 2) if isinstance(v, float) else v for k, v in row.items()})
            for row in yearly
        ],
        scenarios=scenarios,
    )
