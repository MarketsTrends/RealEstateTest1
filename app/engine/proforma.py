from __future__ import annotations

from typing import TypedDict

from app.engine.loan import remaining_balance
from app.engine.metrics import effective_rent_annual, gross_rent_annual, noi_annual


class YearlyOperatingStatement(TypedDict):
    year: int
    gross_rent_annual_eur: float
    vacancy_loss_annual_eur: float
    effective_rent_annual_eur: float
    operating_expenses_annual_eur: float
    noi_annual_eur: float


class YearlyProjection(YearlyOperatingStatement):
    debt_service_annual_eur: float
    cashflow_annual_eur: float
    loan_balance_end_eur: float
    property_value_end_eur: float
    equity_end_eur: float


def yearly_operating_statement(
    *,
    year: int,
    monthly_rent_eur: float,
    other_monthly_income_eur: float,
    vacancy_rate: float,
    annual_operating_expenses_eur: float,
) -> YearlyOperatingStatement:
    gross = gross_rent_annual(monthly_rent_eur, other_monthly_income_eur)
    effective = effective_rent_annual(gross, vacancy_rate)
    noi = noi_annual(effective, annual_operating_expenses_eur)
    return {
        "year": year,
        "gross_rent_annual_eur": gross,
        "vacancy_loss_annual_eur": gross - effective,
        "effective_rent_annual_eur": effective,
        "operating_expenses_annual_eur": annual_operating_expenses_eur,
        "noi_annual_eur": noi,
    }


def build_yearly_projections(
    *,
    purchase_price_eur: float,
    appreciation_rate_annual: float,
    monthly_rent_eur: float,
    other_monthly_income_eur: float,
    vacancy_rate: float,
    annual_operating_expenses_eur: float,
    annual_debt_service_eur: float,
    loan_amount_eur: float,
    interest_rate_annual: float,
    term_years: int,
    hold_years: int,
) -> list[YearlyProjection]:
    rows: list[YearlyProjection] = []
    for year in range(1, hold_years + 1):
        op = yearly_operating_statement(
            year=year,
            monthly_rent_eur=monthly_rent_eur,
            other_monthly_income_eur=other_monthly_income_eur,
            vacancy_rate=vacancy_rate,
            annual_operating_expenses_eur=annual_operating_expenses_eur,
        )
        months_paid = min(year * 12, term_years * 12)
        loan_balance = remaining_balance(loan_amount_eur, interest_rate_annual, term_years, months_paid)
        property_value = purchase_price_eur * ((1 + appreciation_rate_annual) ** year)
        cashflow = op["noi_annual_eur"] - annual_debt_service_eur
        rows.append(
            {
                **op,
                "debt_service_annual_eur": annual_debt_service_eur,
                "cashflow_annual_eur": cashflow,
                "loan_balance_end_eur": loan_balance,
                "property_value_end_eur": property_value,
                "equity_end_eur": property_value - loan_balance,
            }
        )
    return rows


def build_yearly_cashflows(
    *,
    hold_years: int,
    cashflow_annual_eur: float,
    sale_proceeds_net_eur: float,
    initial_cash_invested_eur: float,
) -> list[float]:
    cashflows = [-initial_cash_invested_eur]
    if hold_years > 1:
        cashflows.extend([cashflow_annual_eur] * (hold_years - 1))
    cashflows.append(cashflow_annual_eur + sale_proceeds_net_eur)
    return cashflows
