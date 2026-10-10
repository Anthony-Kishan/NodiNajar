"""
Outer bank lines of a braided river, and how far they move per 500 m segment.

Deterministic, tested, no AI.

Why this exists: on real NISAR data the Jamuna's sandbars (chars) go under water
as the monsoon rises. Counting every land-to-water pixel as "land lost" then
reports kilometres of false erosion in 12 days (18 to 30 June 2026). Families
live on the OUTER banks, so we measure only those:

1. main_river: water bodies of at least min_area_km2 after removing channels
   narrower than min_width_m (so ponds and thin creeks cannot set the bank).
2. bank_columns: for every image row, the westmost and eastmost river pixel.
   Chars inside the belt are ignored by construction. The river runs roughly
   north-south in our box, so rows cut across it.
3. segment_retreat: per 500 m segment, the median outward movement of the bank
   (positive = river moved into the land). A segment is "jump" when the bank
   line switched to another channel (median > max_jump_m, or rows disagree by
   more than max_spread_m), and "gap" when too few rows have a bank.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage

OK, JUMP, GAP = "ok", "jump", "gap"


def _disk(radius_px: int) -> np.ndarray:
    r = max(1, int(radius_px))
    yy, xx = np.ogrid[-r:r + 1, -r:r + 1]
    return xx * xx + yy * yy <= r * r


def main_river(water: np.ndarray, pixel_m: float, min_area_km2: float = 2.0,
               min_width_m: float = 200.0) -> np.ndarray:
    """The main river: wide channels in water bodies of at least min_area_km2."""
    opened = ndimage.binary_opening(water, structure=_disk(min_width_m / pixel_m / 2))
    labels, n = ndimage.label(opened)
    if n == 0:
        return np.zeros_like(water, dtype=bool)
    sizes = ndimage.sum(opened, labels, range(1, n + 1)) * pixel_m ** 2 / 1e6
    return np.isin(labels, np.flatnonzero(sizes >= min_area_km2) + 1)


def bank_columns(river: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Column of the westmost and eastmost river pixel in each row (float, NaN when
    the row has no river or the river touches the image edge, which is not a bank).
    """
    h, w = river.shape
    west, east = np.full(h, np.nan), np.full(h, np.nan)
    has = river.any(axis=1)
    first = np.argmax(river, axis=1)
    last = w - 1 - np.argmax(river[:, ::-1], axis=1)
    west[has], east[has] = first[has], last[has]
    west[west <= 1] = np.nan
    east[east >= w - 2] = np.nan
    return west, east


def outward_m(cols_a: np.ndarray, cols_b: np.ndarray, side: str, pixel_m: float) -> np.ndarray:
    """Per-row bank movement from date A to date B in metres; positive = into the land."""
    if side == "west":
        return (cols_a - cols_b) * pixel_m
    if side == "east":
        return (cols_b - cols_a) * pixel_m
    raise ValueError("side must be 'west' or 'east'")


def segment_retreat(move_m: np.ndarray, rows_per_segment: int, max_jump_m: float = 400.0,
                    max_spread_m: float = 150.0, min_valid: float = 0.6) -> list[dict]:
    """Median movement per segment of rows, with a status of ok / jump / gap."""
    out = []
    h = move_m.size
    for r0 in range(0, h, rows_per_segment):
        r1 = min(r0 + rows_per_segment, h)
        v = move_m[r0:r1]
        v = v[np.isfinite(v)]
        if v.size < min_valid * (r1 - r0):
            out.append({"r0": r0, "r1": r1, "retreat_m": None, "status": GAP})
            continue
        med = float(np.median(v))
        spread = float(np.percentile(v, 75) - np.percentile(v, 25))
        status = JUMP if (abs(med) > max_jump_m or spread > max_spread_m) else OK
        out.append({"r0": r0, "r1": r1, "retreat_m": round(med, 1) if status == OK else None, "status": status})
    return out


def confirmed_retreat(first: tuple, later: list[tuple], side: str, pixel_m: float,
                      rows_per_segment: int, **kw) -> list[dict]:
    """
    Retreat from the first date to each later date, per segment. The confirmed
    value is the smallest of the last two dates (land that stays lost), so a
    short flood that recedes is not counted. Status is ok only if both are ok.
    """
    k = 0 if side == "west" else 1
    per_date = [segment_retreat(outward_m(first[k], d[k], side, pixel_m), rows_per_segment, **kw) for d in later]
    tail = per_date[-2:] if len(per_date) >= 2 else per_date[-1:]
    rows = []
    for i, base in enumerate(per_date[-1]):
        segs = [p[i] for p in tail]
        ok = all(s["status"] == OK for s in segs)
        status = OK if ok else (GAP if any(s["status"] == GAP for s in segs) else JUMP)
        rows.append({
            "r0": base["r0"], "r1": base["r1"], "side": side, "status": status,
            "retreat_m": round(min(s["retreat_m"] for s in segs), 1) if ok else None,
            "confirmed": len(tail) == 2,
            "history_m": [0.0] + [p[i]["retreat_m"] if p[i]["status"] == OK else None for p in per_date],
        })
    return rows
