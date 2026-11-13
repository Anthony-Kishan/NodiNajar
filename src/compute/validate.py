"""
Independent check of our NISAR water masks against NASA OPERA DSWx-HLS.

DSWx-HLS is NASA JPL's surface-water map from optical Landsat and Sentinel-2
(30 m). Where the optical view is clear on the same day as a NISAR pass, the two
maps should agree. DSWx classes used here (from the GIBS colour table):
1 = not water, 2 = open water, 3 = partial surface water, 4 = cloud or shadow,
0 = no data, 5 = other (snow, fill). Only cells that DSWx calls clearly water or
clearly not water are compared; partial water and cloud are counted and left out.
"""
from __future__ import annotations

import math

import numpy as np

NOT_WATER, OPEN_WATER, PARTIAL, CLOUD = 1, 2, 3, 4


def merc_pixel_to_lonlat(px: np.ndarray, py: np.ndarray, z: int, tile: int = 256) -> tuple[np.ndarray, np.ndarray]:
    """Web Mercator global pixel coordinates (at zoom z, `tile` px per tile) to lon/lat in degrees."""
    n = tile * 2 ** z
    lon = px / n * 360.0 - 180.0
    lat = np.degrees(np.arctan(np.sinh(math.pi * (1 - 2 * py / n))))
    return lon, lat


def lonlat_to_image(corners: list[list[float]], width: int, height: int):
    """
    Affine map from lon/lat to (col, row) in an image whose corners are
    [top-left, top-right, bottom-right, bottom-left] in lon/lat. Least-squares fit
    on the four corners; over an 80 km box the error is well under one 30 m pixel's
    worth of the comparison grid (about 75 m).
    """
    src = np.array([[c[0], c[1], 1.0] for c in corners])
    dst = np.array([[0, 0], [width, 0], [width, height], [0, height]], dtype=float)
    coef, *_ = np.linalg.lstsq(src, dst, rcond=None)

    def f(lon: np.ndarray, lat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        a = np.stack([lon, lat, np.ones_like(lon)], axis=-1)
        out = a @ coef
        return out[..., 0], out[..., 1]
    return f


def compare(nisar_water: np.ndarray, dswx: np.ndarray, valid: np.ndarray) -> dict:
    """Agreement between a NISAR water mask and DSWx classes on the same grid."""
    if not (nisar_water.shape == dswx.shape == valid.shape):
        raise ValueError("arrays must have the same shape")
    v = valid.astype(bool)
    clear = v & np.isin(dswx, (NOT_WATER, OPEN_WATER))
    n = int(clear.sum())
    if n == 0:
        return {"n_compared": 0}
    d_w = (dswx == OPEN_WATER) & clear
    n_w = nisar_water.astype(bool) & clear
    both = int((d_w & n_w).sum())
    either = int((d_w | n_w).sum())
    agree = int(((d_w == n_w) & clear).sum())
    return {
        "n_compared": n,
        "n_partial_skipped": int((v & (dswx == PARTIAL)).sum()),
        "n_cloud_skipped": int((v & (dswx == CLOUD)).sum()),
        "agreement_pct": round(100 * agree / n, 1),
        "water_iou_pct": round(100 * both / either, 1) if either else None,
        "nisar_water_pct": round(100 * int(n_w.sum()) / n, 1),
        "dswx_water_pct": round(100 * int(d_w.sum()) / n, 1),
        "dswx_water_found_by_nisar_pct": round(100 * both / int(d_w.sum()), 1) if d_w.any() else None,
    }
