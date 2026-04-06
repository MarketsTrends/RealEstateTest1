from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class PropertyType(str, Enum):
    apartment = "apartment"
    house = "house"
    unknown = "unknown"


class PropertyInput(BaseModel):
    address: str | None = None
    lat: float | None = None
    lon: float | None = None
    property_type: PropertyType = PropertyType.unknown
    surface_m2: float | None = Field(default=None, ge=0)
    rooms: int | None = Field(default=None, ge=0)
    country_code: str = "FR"


class AcquisitionInput(BaseModel):
    purchase_price_eur: float = Field(ge=0)
    fees_and_works_eur: float = Field(ge=0)


class IncomeInput(BaseModel):
    monthly_rent_eur: float = Field(ge=0)
    other_monthly_income_eur: float = Field(default=0, ge=0)
    vacancy_rate: float = Field(default=0.05, ge=0, le=1)


class OperatingExpensesInput(BaseModel):
    annual_operating_expenses_eur: float = Field(ge=0)


class FinancingInput(BaseModel):
    down_payment_eur: float = Field(ge=0)
    loan_amount_eur: float = Field(ge=0)
    interest_rate_annual: float = Field(ge=0)
    term_years: int = Field(ge=1, le=40)


class ExitAssumptionsInput(BaseModel):
    hold_years: int = Field(ge=1, le=40)
    appreciation_rate_annual: float = Field(ge=-0.5, le=0.5)
    sale_cost_rate: float = Field(default=0.06, ge=0, le=1)


class ValuationInput(BaseModel):
    discount_rate_annual_for_npv: float = Field(default=0.10, ge=-0.5, le=0.5)


class ModelInput(BaseModel):
    cashflow_frequency: str = "annual"
    debt_compounding: str = "monthly"
    rounding: str = "cent"

    @field_validator("cashflow_frequency")
    @classmethod
    def validate_cashflow_frequency(cls, value: str) -> str:
        if value != "annual":
            raise ValueError("cashflow_frequency must be 'annual'")
        return value

    @field_validator("debt_compounding")
    @classmethod
    def validate_debt_compounding(cls, value: str) -> str:
        if value != "monthly":
            raise ValueError("debt_compounding must be 'monthly'")
        return value

    @field_validator("rounding")
    @classmethod
    def validate_rounding(cls, value: str) -> str:
        if value != "cent":
            raise ValueError("rounding must be 'cent'")
        return value


class AnalysisRequest(BaseModel):
    property: PropertyInput
    acquisition: AcquisitionInput
    income: IncomeInput
    expenses: OperatingExpensesInput
    financing: FinancingInput
    exit: ExitAssumptionsInput
    valuation: ValuationInput = Field(default_factory=ValuationInput)
    model: ModelInput = Field(default_factory=ModelInput)


class RiskSeverity(str, Enum):
    info = "info"
    medium = "medium"
    high = "high"


class RiskFlag(BaseModel):
    code: str
    severity: RiskSeverity
    message: str


class AnalysisMetrics(BaseModel):
    gross_rent_annual_eur: float
    effective_rent_annual_eur: float
    noi_annual_eur: float
    gross_yield_on_purchase_price: float | None
    cap_rate_on_purchase_price: float | None
    cap_rate_on_total_cost: float | None
    loan_payment_monthly_eur: float
    annual_debt_service_eur: float
    cashflow_annual_eur: float
    cashflow_monthly_eur: float
    cash_on_cash_return: float | None
    dscr: float | None
    break_even_occupancy: float | None
    sale_price_year_n_eur: float
    loan_balance_end_of_hold_eur: float
    sale_proceeds_net_eur: float
    npv_eur: float
    irr_annual: float | None


class YearlyProjection(BaseModel):
    year: int
    gross_rent_annual_eur: float
    vacancy_loss_annual_eur: float
    effective_rent_annual_eur: float
    operating_expenses_annual_eur: float
    noi_annual_eur: float
    debt_service_annual_eur: float
    cashflow_annual_eur: float
    loan_balance_end_eur: float
    property_value_end_eur: float
    equity_end_eur: float


class ScenarioOutput(BaseModel):
    deltas: dict[str, float]
    metrics: AnalysisMetrics


class AnalysisMeta(BaseModel):
    engine_version: str
    created_at: datetime
    warnings: list[str]


class AnalysisResponse(BaseModel):
    meta: AnalysisMeta
    metrics: AnalysisMetrics
    risk_flags: list[RiskFlag]
    pro_forma_yearly: list[YearlyProjection]
    scenarios: dict[str, ScenarioOutput]


class CompsQuery(BaseModel):
    lat: float
    lon: float
    radius_m: int = 1000
    months_back: int = 24


class CompsStats(BaseModel):
    n: int
    median_price_per_sqm_eur: float | None
    p25_price_per_sqm_eur: float | None
    p75_price_per_sqm_eur: float | None
    median_price_eur: float | None
    median_surface_m2: float | None


class CompRecord(BaseModel):
    transaction_id: str
    sold_at: date
    price_eur: float
    surface_m2: float | None
    rooms: int | None
    property_type: PropertyType
    distance_m: float


class CompsResponse(BaseModel):
    available: bool
    warnings: list[str]
    query: CompsQuery
    stats: CompsStats
    comps: list[CompRecord]


def round_money(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 2)


def round_ratio(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def rounded_metrics(metrics: dict[str, Any]) -> AnalysisMetrics:
    return AnalysisMetrics(
        gross_rent_annual_eur=round_money(metrics["gross_rent_annual_eur"]),
        effective_rent_annual_eur=round_money(metrics["effective_rent_annual_eur"]),
        noi_annual_eur=round_money(metrics["noi_annual_eur"]),
        gross_yield_on_purchase_price=round_ratio(metrics["gross_yield_on_purchase_price"]),
        cap_rate_on_purchase_price=round_ratio(metrics["cap_rate_on_purchase_price"]),
        cap_rate_on_total_cost=round_ratio(metrics["cap_rate_on_total_cost"]),
        loan_payment_monthly_eur=round_money(metrics["loan_payment_monthly_eur"]),
        annual_debt_service_eur=round_money(metrics["annual_debt_service_eur"]),
        cashflow_annual_eur=round_money(metrics["cashflow_annual_eur"]),
        cashflow_monthly_eur=round_money(metrics["cashflow_monthly_eur"]),
        cash_on_cash_return=round_ratio(metrics["cash_on_cash_return"]),
        dscr=round_ratio(metrics["dscr"]),
        break_even_occupancy=round_ratio(metrics["break_even_occupancy"]),
        sale_price_year_n_eur=round_money(metrics["sale_price_year_n_eur"]),
        loan_balance_end_of_hold_eur=round_money(metrics["loan_balance_end_of_hold_eur"]),
        sale_proceeds_net_eur=round_money(metrics["sale_proceeds_net_eur"]),
        npv_eur=round_money(metrics["npv_eur"]),
        irr_annual=round_ratio(metrics["irr_annual"]),
    )
