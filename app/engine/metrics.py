from __future__ import annotations


def gross_rent_annual(monthly_rent: float, other_monthly_income: float = 0) -> float:
    return (monthly_rent + other_monthly_income) * 12


def effective_rent_annual(gross_rent: float, vacancy_rate: float) -> float:
    return gross_rent * (1 - vacancy_rate)


def noi_annual(effective_rent: float, operating_expenses_annual: float) -> float:
    return effective_rent - operating_expenses_annual


def safe_ratio(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def cap_rate(noi: float, value: float) -> float | None:
    return safe_ratio(noi, value)


def cash_on_cash(cashflow_annual: float, cash_invested: float) -> float | None:
    return safe_ratio(cashflow_annual, cash_invested)


def dscr(noi: float, annual_debt_service: float) -> float | None:
    return safe_ratio(noi, annual_debt_service)


def break_even_occupancy(
    operating_expenses_annual: float,
    annual_debt_service: float,
    gross_rent: float,
) -> float | None:
    return safe_ratio(operating_expenses_annual + annual_debt_service, gross_rent)
