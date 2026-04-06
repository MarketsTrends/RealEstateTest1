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
) -> float:
    if principal <= 0:
        return 0.0
    schedule = amortization_schedule(principal, annual_rate, term_years)
    if months_paid <= 0:
        return principal
    if months_paid >= len(schedule):
        return 0.0
    return schedule[months_paid - 1]["balance_end"]
