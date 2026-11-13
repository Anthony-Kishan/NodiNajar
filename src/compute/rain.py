"""
Rain before each radar pass, from a daily rainfall series (NASA POWER, mm/day).

Deterministic and simple: for each pass, the total over the N days up to and
including the pass date, and the total since the previous pass. Missing days
(the POWER fill value -999, or absent) are not counted and are reported.
"""
from __future__ import annotations

from datetime import date, timedelta

FILL = -999.0


def _key(d: date) -> str:
    return d.strftime("%Y%m%d")


def window_total(daily: dict[str, float], end: str, days: int) -> tuple[float, int]:
    """Sum of the `days` days ending on `end` (YYYY-MM-DD, inclusive) and how many days were missing."""
    if days < 1:
        raise ValueError("days must be at least 1")
    e = date.fromisoformat(end)
    total, missing = 0.0, 0
    for k in range(days):
        v = daily.get(_key(e - timedelta(days=k)))
        if v is None or v <= FILL:
            missing += 1
        else:
            total += v
    return round(total, 1), missing


def rain_by_pass(daily: dict[str, float], pass_dates: list[str], window_days: int = 12) -> list[dict]:
    """Per pass: rain in the window before it, rain since the previous pass, and missing-day counts."""
    out = []
    for i, d in enumerate(pass_dates):
        w, wm = window_total(daily, d, window_days)
        row = {"date": d, "window_days": window_days, "rain_window_mm": w, "missing_window": wm}
        if i > 0:
            gap = (date.fromisoformat(d) - date.fromisoformat(pass_dates[i - 1])).days
            s, sm = window_total(daily, d, gap)
            row.update({"days_since_prev": gap, "rain_since_prev_mm": s, "missing_since_prev": sm})
        out.append(row)
    return out
