from __future__ import annotations


def gross_rent_annual(monthly_rent: float, other_monthly_income: float = 0.0) -> float:
    return (monthly_rent + other_monthly_income) * 12


def gross_yield(gross_rent_annual_eur: float, purchase_price_eur: float) -> float | None:
    if purchase_price_eur == 0:
        return None
    return gross_rent_annual_eur / purchase_price_eur


def effective_rent_annual(gross_rent_annual_eur: float, vacancy_rate: float) -> float:
    return gross_rent_annual_eur * (1 - vacancy_rate)


def noi_annual(effective_rent_annual_eur: float, annual_operating_expenses_eur: float) -> float:
    return effective_rent_annual_eur - annual_operating_expenses_eur


def safe_ratio(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def cap_rate(noi_annual_eur: float, value_eur: float) -> float | None:
    return safe_ratio(noi_annual_eur, value_eur)


def cash_on_cash(cashflow_annual_eur: float, cash_invested_eur: float) -> float | None:
    return safe_ratio(cashflow_annual_eur, cash_invested_eur)


def dscr(noi_annual_eur: float, annual_debt_service_eur: float) -> float | None:
    return safe_ratio(noi_annual_eur, annual_debt_service_eur)


def break_even_occupancy(
    annual_operating_expenses_eur: float,
    annual_debt_service_eur: float,
    gross_rent_annual_eur: float,
) -> float | None:
    return safe_ratio(
        annual_operating_expenses_eur + annual_debt_service_eur,
        gross_rent_annual_eur,
    )
