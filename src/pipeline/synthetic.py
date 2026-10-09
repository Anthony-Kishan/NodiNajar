"""
SYNTHETIC test scenes shaped like NISAR GCOV, over the real Jamuna AOI.

Purpose: let the team build and test the pipeline and web demo before real
NISAR scenes are downloaded. Everything produced from this is labelled
SYNTHETIC in the data and in the interface. Never present it as real data.
"""
from __future__ import annotations

from datetime import date

import numpy as np
from pyproj import Transformer

from src.acquire.nisar import Scene

EPSG = 32646          # UTM zone 46N covers the Jamuna in Sirajganj
HOTSPOTS = [          # (fraction down the reach, max eastward retreat in m)
    (0.22, 420.0),
    (0.55, 260.0),
    (0.80, 180.0),
]


def _grid(bbox, pixel_m):
    to_utm = Transformer.from_crs(4326, EPSG, always_xy=True)
    w, s, e, n = bbox
    xs, ys = to_utm.transform([w, e, w, e], [s, s, n, n])
    x = np.arange(min(xs), max(xs), pixel_m) + pixel_m / 2
    y = np.arange(max(ys), min(ys), -pixel_m) - pixel_m / 2
    return x, y


def _water(x, y, t, rng_state):
    """Water mask for progress t in [0, 1] through the season."""
    X, Y = np.meshgrid(x, y)
    xm = x.mean()
    ny = (y.max() - Y) / (y.max() - y.min())               # 0 at north, 1 at south
    centre = xm - 2500 + 1800 * np.sin(ny * 2 * np.pi * 1.3)
    water = np.zeros_like(X, dtype=bool)
    for offset, width in ((-2200, 900), (0, 1400), (2100, 1000)):   # braided channels
        c = centre + offset + 300 * np.sin(ny * 2 * np.pi * 3.1 + offset / 900)
        water |= np.abs(X - c) < width / 2
    east_bank = centre + 2100 + 500
    for frac, max_m in HOTSPOTS:                            # progressive erosion bulges
        shape = np.exp(-((ny - frac) / 0.035) ** 2)
        push = max_m * min(1.0, t * 1.15) * shape
        water |= (X > east_bank - 50) & (X < east_bank + push)
    flood = 60 * np.sin(np.pi * t)                          # mid-season flooding then recession
    water |= (X > east_bank) & (X < east_bank + flood)
    return water


# Real NISAR acquisition dates over the Jamuna AOI for ONE 12-day repeat track
# (the 18 Jun cycle in docs/COVERAGE.md, which also covers the Teesta). No pass
# exists between 24 Jul and 17 Aug on this track, so the synthetic series has
# the same gap. Real dates keep the demo honest: it never shows a pass that
# NISAR did not make.
TRACK_DATES = ["2026-06-18", "2026-06-30", "2026-07-12", "2026-07-24",
               "2026-08-17", "2026-08-29", "2026-09-10", "2026-09-22"]


def scenes(bbox, dates=TRACK_DATES, pixel_m=30.0, seed=7):
    rng = np.random.default_rng(seed)
    x, y = _grid(bbox, pixel_m)
    days = [date.fromisoformat(d) for d in dates]
    span = max(1, (days[-1] - days[0]).days)
    out = []
    for day in days:
        t = (day - days[0]).days / span          # season progress by real date, not pass index
        w = _water(x, y, t, rng)
        mean = np.where(w, 10 ** (-2.25), 10 ** (-0.85)).astype("float32")
        power = mean * rng.gamma(4.0, 0.25, size=mean.shape).astype("float32")
        d = day.isoformat()
        out.append(Scene(power=power, x=x, y=y, epsg=EPSG, date=d,
                         granule=f"SYNTHETIC_GCOV_{d.replace('-', '')}", pol="HHHH",
                         pixel_m=pixel_m, source="SYNTHETIC (not real data)"))
    return out


def buildings(bbox, n=4000, seed=11):
    """Synthetic homestead points (lon, lat), clustered east of the river."""
    rng = np.random.default_rng(seed)
    x, y = _grid(bbox, 30.0)
    xm = x.mean()
    ny = rng.uniform(0.02, 0.98, n)
    centre = xm - 2500 + 1800 * np.sin(ny * 2 * np.pi * 1.3)
    east_bank = centre + 2600
    px = east_bank + rng.gamma(2.0, 450.0, n) + 30
    west = rng.random(n) < 0.35
    px[west] = centre[west] - 3200 - rng.gamma(2.0, 500.0, west.sum())
    py = y.max() - ny * (y.max() - y.min())
    to_ll = Transformer.from_crs(EPSG, 4326, always_xy=True)
    lon, lat = to_ll.transform(px, py)
    return np.column_stack([lon, lat])
