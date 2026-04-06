from __future__ import annotations

from app.schemas import AnalysisRequest, RiskFlag


def build_risk_flags(
    payload: AnalysisRequest,
    *,
    dscr_value: float | None,
    break_even_occupancy_value: float | None,
) -> list[RiskFlag]:
    flags: list[RiskFlag] = []

    if dscr_value is None or dscr_value < 1.2:
        flags.append(
            RiskFlag(
                code="LOW_DSCR",
                severity="high",
                message="DSCR below prudent threshold (1.20)",
            )
        )

    if break_even_occupancy_value is None or break_even_occupancy_value > 0.85:
        flags.append(
            RiskFlag(
                code="HIGH_BREAK_EVEN_OCCUPANCY",
                severity="medium",
                message="Break-even occupancy above 85%",
            )
        )

    if payload.income.vacancy_rate > 0.08:
        flags.append(
            RiskFlag(
                code="HIGH_VACANCY",
                severity="medium",
                message="Vacancy assumption higher than 8%",
            )
        )

    weak_data = (
        payload.property.address is None
        and payload.property.lat is None
        and payload.property.lon is None
        and payload.property.surface_m2 is None
    )
    if weak_data:
        flags.append(
            RiskFlag(
                code="WEAK_DATA_CONFIDENCE",
                severity="medium",
                message="Limited property inputs reduce confidence",
            )
        )

    if payload.property.country_code.upper() == "FR":
        flags.append(
            RiskFlag(
                code="REGULATORY_DPE_FG_PLACEHOLDER",
                severity="info",
                message="Placeholder: verify DPE class (F/G can affect rental feasibility)",
            )
        )

    return flags
