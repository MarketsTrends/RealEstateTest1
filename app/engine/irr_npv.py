from __future__ import annotations

from typing import Sequence

import numpy_financial as npf


def npv(rate: float, cashflows: Sequence[float]) -> float:
    return sum(cf / ((1 + rate) ** t) for t, cf in enumerate(cashflows))


def _has_sign_change(values: Sequence[float]) -> bool:
    has_pos = any(v > 0 for v in values)
    has_neg = any(v < 0 for v in values)
    return has_pos and has_neg


def _bisection_irr(cashflows: Sequence[float], low: float = -0.9999, high: float = 10.0) -> float | None:
    f_low = npv(low, cashflows)
    f_high = npv(high, cashflows)
    if f_low == 0:
        return low
    if f_high == 0:
        return high
    if f_low * f_high > 0:
        return None
    for _ in range(200):
        mid = (low + high) / 2
        f_mid = npv(mid, cashflows)
        if abs(f_mid) < 1e-12:
            return mid
        if f_low * f_mid <= 0:
            high, f_high = mid, f_mid
        else:
            low, f_low = mid, f_mid
    return (low + high) / 2


def irr(cashflows: Sequence[float]) -> float | None:
    if not _has_sign_change(cashflows):
        return None
    try:
        result = npf.irr(cashflows)
        if result is not None:
            result_f = float(result)
            if result_f == result_f and result_f > -1:
                return result_f
    except Exception:
        pass
    return _bisection_irr(cashflows)
