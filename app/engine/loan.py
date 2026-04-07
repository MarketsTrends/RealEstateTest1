from __future__ import annotations

from typing import TypedDict


class AmortizationRow(TypedDict):
    month: int
    payment: float
    interest: float
    principal: float
    balance_end: float


def monthly_loan_payment(principal: float, annual_rate: float, term_years: int) -> float:
    months = term_years * 12
    if principal <= 0 or months <= 0:
        return 0.0
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        return principal / months
    return principal * monthly_rate / (1 - (1 + monthly_rate) ** (-months))


def amortization_schedule(principal: float, annual_rate: float, term_years: int) -> list[AmortizationRow]:
    months = term_years * 12
    if principal <= 0 or months <= 0:
        return []

    payment = monthly_loan_payment(principal, annual_rate, term_years)
    monthly_rate = annual_rate / 12
    balance = principal
    schedule: list[AmortizationRow] = []

    for month in range(1, months + 1):
        interest = balance * monthly_rate if monthly_rate > 0 else 0.0
        principal_paid = min(payment - interest, balance)
        balance = max(0.0, balance - principal_paid)
        schedule.append(
            {
                "month": month,
                "payment": payment,
                "interest": interest,
                "principal": principal_paid,
                "balance_end": balance,
            }
        )

    return schedule


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
    pmt = payment if payment is not None else monthly_loan_payment(principal, annual_rate, term_years)

    if monthly_rate == 0:
        return max(0.0, principal - pmt * months_paid)

    factor = (1 + monthly_rate) ** months_paid
    balance = principal * factor - pmt * ((factor - 1) / monthly_rate)
    return max(0.0, balance)
