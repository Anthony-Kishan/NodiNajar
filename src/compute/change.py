"""
Bank change between two water masks, summarised per square cell.

Deterministic, tested, no AI.

Definitions (state these in the methods panel):
- land_lost: pixel was land on date A and water on date B.
- retreat_m: for land_lost pixels, the distance to the nearest land on date B.
  The cell value is the 95th percentile, so one noisy pixel cannot set it.
- Caveat: during the monsoon, rising water also floods low land. A pixel that
  turns to water may be flooding, not erosion. Only land that stays water on
  later passes is confirmed erosion (see persistent_loss).
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage


def land_lost(mask_a: np.ndarray, mask_b: np.ndarray) -> np.ndarray:
    """Pixels that were land on date A and are water on date B."""
    return (~mask_a) & mask_b


def persistent_loss(masks: list[np.ndarray]) -> np.ndarray:
    """Land on the first date that is water on every later date (confirmed loss)."""
    if len(masks) < 3:
        raise ValueError("Need at least 3 dates to confirm persistence")
    later = np.logical_and.reduce(masks[1:])
    return (~masks[0]) & later


def retreat_distance(mask_b: np.ndarray, lost: np.ndarray, pixel_m: float) -> np.ndarray:
    """Distance (m) from each lost pixel to the nearest land on date B. 0 elsewhere."""
    dist_to_land = ndimage.distance_transform_edt(mask_b) * pixel_m
    return np.where(lost, dist_to_land, 0.0)


def summarise_cells(lost: np.ndarray, retreat: np.ndarray, pixel_m: float,
                    cell_m: float = 500.0) -> list[dict]:
    """
    Split the grid into square cells of cell_m and summarise each cell that lost land.
    Returns rows with row/col pixel bounds, lost area (ha) and retreat (m, p95).
    """
    step = max(1, int(round(cell_m / pixel_m)))
    rows = []
    h, w = lost.shape
    for r0 in range(0, h, step):
        for c0 in range(0, w, step):
            blk = lost[r0:r0 + step, c0:c0 + step]
            n = int(blk.sum())
            if n == 0:
                continue
            ret = retreat[r0:r0 + step, c0:c0 + step][blk]
            rows.append({
                "r0": r0, "c0": c0, "r1": min(r0 + step, h), "c1": min(c0 + step, w),
                "lost_ha": round(n * pixel_m ** 2 / 1e4, 2),
                "retreat_m": round(float(np.percentile(ret, 95)), 1),
            })
    return rows


def count_near(points_rc: np.ndarray, water_b: np.ndarray, pixel_m: float,
               within_m: float = 200.0) -> np.ndarray:
    """
    For points given as (row, col) pixel positions, return a boolean array:
    True where the point is on land and within `within_m` of water on date B.
    """
    if len(points_rc) == 0:
        return np.zeros(0, dtype=bool)
    dist_to_water = ndimage.distance_transform_edt(~water_b) * pixel_m
    r = np.clip(points_rc[:, 0].astype(int), 0, water_b.shape[0] - 1)
    c = np.clip(points_rc[:, 1].astype(int), 0, water_b.shape[1] - 1)
    d = dist_to_water[r, c]
    return (d > 0) & (d <= within_m)


def risk_level(retreat_m: float, homes_near: int, red_m: float = 100.0,
               amber_m: float = 30.0) -> str:
    """
    Starting thresholds (tune on the back-test, see docs/METHODS.md):
    red   = retreat >= red_m and at least one home within 200 m of the new bank
    amber = retreat >= amber_m
    green = otherwise
    """
    if retreat_m >= red_m and homes_near > 0:
        return "red"
    if retreat_m >= amber_m:
        return "amber"
    return "green"
