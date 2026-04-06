from __future__ import annotations

from typing import Any

from app.engine.loan import monthly_payment, remaining_balance
from app.engine.metrics import effective_rent_annual, gross_rent_annual, noi_annual


def build_pro_forma_yearly(
    purchase_price: float,
    appreciation_rate_annual: float,
    monthly_rent: float,
    other_monthly_income: float,
    vacancy_rate: float,
    annual_operating_expenses: float,
    loan_amount: float,
    interest_rate_annual: float,
    term_years: int,
    hold_years: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    gross = gross_rent_annual(monthly_rent, other_monthly_income)
    effective = effective_rent_annual(gross, vacancy_rate)
    noi = noi_annual(effective, annual_operating_expenses)
    pmt = monthly_payment(loan_amount, interest_rate_annual, term_years)
    annual_debt = pmt * 12

    for year in range(1, hold_years + 1):
        months_paid = min(year * 12, term_years * 12)
        loan_balance = remaining_balance(
            loan_amount,
            interest_rate_annual,
            term_years,
            months_paid,
            payment=pmt,
        )
        property_value = purchase_price * ((1 + appreciation_rate_annual) ** year)
        equity = property_value - loan_balance
        rows.append(
            {
                "year": year,
                "gross_rent_annual_eur": gross,
                "vacancy_loss_annual_eur": gross - effective,
                "effective_rent_annual_eur": effective,
                "operating_expenses_annual_eur": annual_operating_expenses,
                "noi_annual_eur": noi,
                "debt_service_annual_eur": annual_debt,
                "cashflow_annual_eur": noi - annual_debt,
                "loan_balance_end_eur": loan_balance,
                "property_value_end_eur": property_value,
                "equity_end_eur": equity,
            }
        )
    return rows
