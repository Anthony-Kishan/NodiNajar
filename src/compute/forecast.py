"""
Bank position forecast per stretch, from its own measured history.

A stretch's history is the outer-bank position on each NISAR pass, in metres
into the land since the first pass (None where the bank line switched channel
and was not measured). We fit a straight line with the Theil-Sen estimator
(median of all pairwise slopes), which ignores the odd wild pass, and project
it to future pass dates.

The range comes from the 10th to 90th percentile of the pairwise slopes, so a
stretch whose passes disagree gets a wide range. A bank does not grow back into the
river in this model: a negative slope is reported as "no advance".

Everything here is deterministic. Output is PROVISIONAL: a straight-line trend
over one monsoon, not a hydraulic model.
"""
from __future__ import annotations

from datetime import date
from itertools import combinations
from statistics import median

import numpy as np

MIN_POINTS = 4  # measured passes needed before we forecast at all
BAND = (10, 90)  # percentiles of the pairwise slopes used for the low-high range


def _days(dates: list[str]) -> list[int]:
    d0 = date.fromisoformat(dates[0])
    return [(date.fromisoformat(d) - d0).days for d in dates]


def measured(dates: list[str], history: list[float | None]) -> tuple[list[int], list[float]]:
    """Day offsets and positions for passes where the bank was measured."""
    t = _days(dates)
    pts = [(ti, float(h)) for ti, h in zip(t, history) if h is not None]
    return [p[0] for p in pts], [p[1] for p in pts]


def theil_sen(t: list[int], y: list[float], band: tuple[float, float] = BAND) -> dict:
    """Median pairwise slope (m/day), its low/high percentiles, and the matching intercept."""
    slopes = [(y[j] - y[i]) / (t[j] - t[i]) for i, j in combinations(range(len(t)), 2) if t[j] != t[i]]
    if not slopes:
        raise ValueError("need at least two passes on different dates")
    b = median(slopes)
    a = median(yi - b * ti for ti, yi in zip(t, y))
    lo, hi = (float(v) for v in np.percentile(slopes, list(band)))
    return {"slope": b, "intercept": a, "slope_lo": lo, "slope_hi": hi, "n_pairs": len(slopes)}


def forecast_stretch(dates: list[str], history: list[float | None], targets: list[str]) -> dict:
    """
    Forecast the bank position on each target date.

    Returns {"ok": False, "reason": ...} when there are too few measured passes.
    Otherwise: rate in m per 12 days (the NISAR repeat), and for each target the
    expected position and a low-high range, all in metres since the first pass,
    plus the expected further advance beyond the last measured position.
    """
    t, y = measured(dates, history)
    if len(t) < MIN_POINTS:
        return {"ok": False, "reason": f"only {len(t)} measured passes (need {MIN_POINTS})"}
    fit = theil_sen(t, y)
    d0 = date.fromisoformat(dates[0])
    last_t, last_y = t[-1], y[-1]
    # anchor the projection at the fitted value on the last measured pass
    anchor = fit["intercept"] + fit["slope"] * last_t
    out = []
    for d in targets:
        tt = (date.fromisoformat(d) - d0).days
        if tt <= last_t:
            raise ValueError(f"target {d} is not after the last measured pass")
        dt = tt - last_t
        mid = anchor + max(fit["slope"], 0.0) * dt
        lo = anchor + max(min(fit["slope_lo"], fit["slope"]), 0.0) * dt
        hi = anchor + max(fit["slope_hi"], fit["slope"], 0.0) * dt
        out.append({"date": d, "days_ahead": dt, "expected_m": round(mid, 1), "low_m": round(lo, 1),
                    "high_m": round(hi, 1), "advance_m": round(max(mid - last_y, 0.0), 1)})
    return {
        "ok": True,
        "rate_m_per_12d": round(fit["slope"] * 12, 1),
        "advancing": fit["slope"] > 0,
        "n_passes": len(t),
        "last_measured": {"date": dates[_days(dates).index(last_t)], "position_m": last_y},
        "targets": out,
    }


def backtest(dates: list[str], history: list[float | None], n_holdout: int = 2) -> dict:
    """
    Hide the last n passes, forecast them from the earlier ones, and compare with
    what NISAR measured. Returns per-pass error and whether the measured value
    fell inside the forecast range.
    """
    if n_holdout < 1 or n_holdout >= len(dates):
        raise ValueError("n_holdout must leave at least one training pass")
    train_d, train_h = dates[:-n_holdout], history[:-n_holdout]
    test_d, test_h = dates[-n_holdout:], history[-n_holdout:]
    # forecast from the last *measured* training pass
    f = forecast_stretch(train_d, train_h, test_d)
    if not f["ok"]:
        return {"ok": False, "reason": f["reason"]}
    rows = []
    for pred, actual in zip(f["targets"], test_h):
        if actual is None:
            rows.append({**pred, "measured_m": None, "error_m": None, "in_range": None})
            continue
        rows.append({**pred, "measured_m": actual, "error_m": round(actual - pred["expected_m"], 1),
                     "in_range": pred["low_m"] <= actual <= pred["high_m"]})
    return {"ok": True, "rate_m_per_12d": f["rate_m_per_12d"], "passes": rows}


def summarise_backtests(results: list[dict]) -> dict:
    """Mean absolute error, median error and share inside the range over all scored passes."""
    errs = [r["error_m"] for res in results if res.get("ok") for r in res["passes"] if r["error_m"] is not None]
    inr = [r["in_range"] for res in results if res.get("ok") for r in res["passes"] if r["in_range"] is not None]
    if not errs:
        return {"n_scored": 0}
    return {
        "n_stretches": sum(1 for res in results if res.get("ok") and any(r["error_m"] is not None for r in res["passes"])),
        "n_scored": len(errs),
        "mae_m": round(float(np.mean(np.abs(errs))), 1),
        "median_abs_error_m": round(float(np.median(np.abs(errs))), 1),
        "bias_m": round(float(np.mean(errs)), 1),
        "share_in_range": round(sum(inr) / len(inr), 3),
    }
