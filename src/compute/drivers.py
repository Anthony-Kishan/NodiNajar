"""
How bank positions change between passes, set against the water level.

If the measured bank moved only because land was lost, it would move inland in
every interval. If it partly tracks the waterline, it moves inland when the river
rises and back when it falls. These summaries let us see which, from the data.
"""
from __future__ import annotations

from statistics import median


def interval_changes(histories: list[list[float | None]], dates: list[str], water_km2: list[float], threshold: float = 30.0) -> list[dict]:
    """For each pair of consecutive passes: water change and the median bank change over stretches measured on both."""
    out = []
    for k in range(1, len(dates)):
        inc = [h[k] - h[k - 1] for h in histories if h[k] is not None and h[k - 1] is not None]
        out.append({
            "from": dates[k - 1], "to": dates[k],
            "water_from_km2": water_km2[k - 1], "water_to_km2": water_km2[k],
            "river": "rising" if water_km2[k] > water_km2[k - 1] else "falling",
            "n": len(inc),
            "median_change_m": round(median(inc), 1) if inc else None,
            "share_inland_pct": round(100 * sum(1 for v in inc if v >= threshold) / len(inc)) if inc else None,
            "share_riverward_pct": round(100 * sum(1 for v in inc if v <= -threshold) / len(inc)) if inc else None,
        })
    return out


def same_stage_pairs(dates: list[str], water_km2: list[float], tolerance: float = 0.05) -> list[tuple[int, int]]:
    """Pairs of passes (i < j) whose water areas differ by at most `tolerance` (fraction of the larger)."""
    pairs = []
    for i in range(len(dates)):
        for j in range(i + 1, len(dates)):
            a, b = water_km2[i], water_km2[j]
            if abs(a - b) <= tolerance * max(a, b):
                pairs.append((i, j))
    return pairs


def pair_change(histories: list[list[float | None]], i: int, j: int, threshold: float = 30.0) -> dict:
    inc = [h[j] - h[i] for h in histories if h[i] is not None and h[j] is not None]
    if not inc:
        return {"n": 0}
    return {"n": len(inc), "median_change_m": round(median(inc), 1),
            "share_inland_pct": round(100 * sum(1 for v in inc if v >= threshold) / len(inc)),
            "share_riverward_pct": round(100 * sum(1 for v in inc if v <= -threshold) / len(inc))}
