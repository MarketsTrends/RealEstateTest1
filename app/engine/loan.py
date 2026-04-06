from __future__ import annotations


def monthly_payment(principal: float, annual_rate: float, term_years: int) -> float:
    months = term_years * 12
    if months <= 0 or principal <= 0:
        return 0.0
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        return principal / months
    return principal * monthly_rate / (1 - (1 + monthly_rate) ** (-months))


def remaining_balance(
    principal: float,
    annual_rate: float,
    term_years: int,
    months_paid: int,
    payment: float | None = None,
) -> float:
    if principal <= 0:
        return 0.0
    total_months = term_years * 12
    if months_paid <= 0:
        return principal
    if months_paid >= total_months:
        return 0.0

    monthly_rate = annual_rate / 12
    pmt = payment if payment is not None else monthly_payment(principal, annual_rate, term_years)

    if monthly_rate == 0:
        return max(0.0, principal - pmt * months_paid)

    return principal * (1 + monthly_rate) ** months_paid - pmt * (
        ((1 + monthly_rate) ** months_paid - 1) / monthly_rate
    )
