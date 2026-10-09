"""
Water / land classification from SAR backscatter.

Deterministic, tested, no AI. Calm open water reflects the radar pulse away
from the satellite, so it appears dark (low backscatter). Land returns more
energy and appears bright.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage


def to_db(power: np.ndarray, floor: float = 1e-6) -> np.ndarray:
    """Linear backscatter power (as in NISAR GCOV) to decibels. NaN stays NaN."""
    p = np.asarray(power, dtype="float64")
    with np.errstate(invalid="ignore"):
        return 10.0 * np.log10(np.maximum(p, floor))


def speckle_filter(db: np.ndarray, size: int = 5) -> np.ndarray:
    """Median filter to suppress speckle. NaNs are filled with the image median first."""
    a = np.array(db, dtype="float64")
    nan = ~np.isfinite(a)
    if nan.any():
        a[nan] = np.nanmedian(a)
    out = ndimage.median_filter(a, size=size)
    out[nan] = np.nan
    return out


def otsu_threshold(db: np.ndarray, bins: int = 256, lo: float = -35.0, hi: float = 5.0) -> float:
    """Otsu's method on the dB histogram. Returns the threshold that best splits two classes."""
    v = db[np.isfinite(db)]
    v = v[(v > lo) & (v < hi)]
    if v.size == 0:
        raise ValueError("No valid pixels for thresholding")
    hist, edges = np.histogram(v, bins=bins, range=(lo, hi))
    centers = (edges[:-1] + edges[1:]) / 2
    w0 = np.cumsum(hist)
    w1 = w0[-1] - w0
    m0 = np.cumsum(hist * centers) / np.maximum(w0, 1)
    m1 = (np.sum(hist * centers) - np.cumsum(hist * centers)) / np.maximum(w1, 1)
    between = w0 * w1 * (m0 - m1) ** 2
    return float(centers[int(np.argmax(between))])


def water_mask(db: np.ndarray, threshold_db: float | None = None,
               min_pixels: int = 50, fill_holes_px: int = 20) -> tuple[np.ndarray, float]:
    """
    Classify water. Returns (mask, threshold_used).

    threshold_db None -> Otsu on this scene. Small specks (< min_pixels) are
    removed and small land holes inside water (< fill_holes_px) are filled.
    """
    thr = otsu_threshold(db) if threshold_db is None else float(threshold_db)
    m = np.isfinite(db) & (db < thr)
    labels, n = ndimage.label(m)
    if n:
        sizes = ndimage.sum(m, labels, range(1, n + 1))
        m = np.isin(labels, np.flatnonzero(sizes >= min_pixels) + 1)
    holes = ~m
    hl, hn = ndimage.label(holes)
    if hn:
        hsizes = ndimage.sum(holes, hl, range(1, hn + 1))
        small = np.isin(hl, np.flatnonzero(hsizes < fill_holes_px) + 1)
        m = m | small
    return m, thr
