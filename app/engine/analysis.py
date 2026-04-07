from __future__ import annotations

from typing import Any

from app.engine.irr_npv import irr, npv
from app.engine.loan import monthly_loan_payment, remaining_balance
from app.engine.metrics import (
    break_even_occupancy,
    cap_rate,
    cash_on_cash,
    dscr,
    effective_rent_annual,
    gross_rent_annual,
    gross_yield,
    noi_annual,
)
from app.engine.proforma import build_yearly_cashflows, build_yearly_projections
from app.schemas import AnalysisRequest


def analyze_financials(payload: AnalysisRequest) -> tuple[dict[str, Any], list[str], list[float], list[dict[str, Any]]]:
    warnings: list[str] = []
    acq = payload.acquisition
    inc = payload.income
    exp = payload.expenses
    fin = payload.financing
    exit_data = payload.exit

    total_cost = acq.purchase_price_eur + acq.fees_and_works_eur

    gross = gross_rent_annual(inc.monthly_rent_eur, inc.other_monthly_income_eur)
    effective = effective_rent_annual(gross, inc.vacancy_rate)
    noi = noi_annual(effective, exp.annual_operating_expenses_eur)

    pmt = monthly_loan_payment(fin.loan_amount_eur, fin.interest_rate_annual, fin.term_years)
    annual_debt = pmt * 12
    cashflow = noi - annual_debt

    dscr_value = dscr(noi, annual_debt)
    if dscr_value is None:
        warnings.append("DSCR unavailable because annual debt service is zero")

    break_even = break_even_occupancy(exp.annual_operating_expenses_eur, annual_debt, gross)
    if break_even is None:
        warnings.append("Break-even occupancy unavailable because gross rent is zero")

    sale_price = acq.purchase_price_eur * ((1 + exit_data.appreciation_rate_annual) ** exit_data.hold_years)
    months_paid = min(fin.term_years * 12, exit_data.hold_years * 12)
    loan_balance = remaining_balance(
        fin.loan_amount_eur,
        fin.interest_rate_annual,
        fin.term_years,
        months_paid,
        payment=pmt,
    )
    sale_net = sale_price * (1 - exit_data.sale_cost_rate)
    sale_proceeds_net = sale_net - loan_balance

    cash_invested = fin.down_payment_eur + acq.fees_and_works_eur
    cocr = cash_on_cash(cashflow, cash_invested)

    cashflows = build_yearly_cashflows(
        hold_years=exit_data.hold_years,
        cashflow_annual_eur=cashflow,
        sale_proceeds_net_eur=sale_proceeds_net,
        initial_cash_invested_eur=cash_invested,
    )
    irr_value = irr(cashflows)
    if irr_value is None:
        warnings.append("IRR unavailable for given cashflows")
    npv_value = npv(payload.valuation.discount_rate_annual_for_npv, cashflows)

    metrics: dict[str, Any] = {
        "gross_rent_annual_eur": gross,
        "effective_rent_annual_eur": effective,
        "noi_annual_eur": noi,
        "gross_yield_on_purchase_price": gross_yield(gross, acq.purchase_price_eur),
        "cap_rate_on_purchase_price": cap_rate(noi, acq.purchase_price_eur),
        "cap_rate_on_total_cost": cap_rate(noi, total_cost),
        "loan_payment_monthly_eur": pmt,
        "annual_debt_service_eur": annual_debt,
        "cashflow_annual_eur": cashflow,
        "cashflow_monthly_eur": cashflow / 12,
        "cash_on_cash_return": cocr,
        "dscr": dscr_value,
        "break_even_occupancy": break_even,
        "sale_price_year_n_eur": sale_price,
        "loan_balance_end_of_hold_eur": loan_balance,
        "sale_proceeds_net_eur": sale_proceeds_net,
        "npv_eur": npv_value,
        "irr_annual": irr_value,
    }

    yearly = build_yearly_projections(
        purchase_price_eur=acq.purchase_price_eur,
        appreciation_rate_annual=exit_data.appreciation_rate_annual,
        monthly_rent_eur=inc.monthly_rent_eur,
        other_monthly_income_eur=inc.other_monthly_income_eur,
        vacancy_rate=inc.vacancy_rate,
        annual_operating_expenses_eur=exp.annual_operating_expenses_eur,
        annual_debt_service_eur=annual_debt,
        loan_amount_eur=fin.loan_amount_eur,
        interest_rate_annual=fin.interest_rate_annual,
        term_years=fin.term_years,
        hold_years=exit_data.hold_years,
        monthly_payment_eur=pmt,
    )

    return metrics, warnings, cashflows, yearly
