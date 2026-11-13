"""
Compare our NISAR water masks with NASA OPERA DSWx-HLS on the same day.

    python tools/dswx_check.py 2026-08-29 2026-09-10      # needs internet to gibs.earthdata.nasa.gov

Downloads the DSWx-HLS tiles over the box from NASA GIBS (zoom 12, every 2nd
pixel, about 75 m), reads webapp/public/data/{water,radar}/<date>.webp, and runs
src.compute.validate.compare. Writes webapp/public/data/dswx_check.json.
"""
from __future__ import annotations

import io
import json
import math
import sys
from pathlib import Path

import numpy as np
import requests
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.compute.validate import compare, lonlat_to_image, merc_pixel_to_lonlat  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "webapp" / "public" / "data"
LAYER = "OPERA_L3_Dynamic_Surface_Water_Extent-HLS"
COLOURS = {(255, 255, 255): 1, (0, 0, 255): 2, (180, 213, 244): 3, (175, 175, 175): 4}
Z, STEP = 12, 2
BOX = (89.58, 23.99, 89.94, 24.73)


def tile_xy(lon: float, lat: float, z: int) -> tuple[int, int]:
    n = 2 ** z
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)
    return x, y


def dswx_grid(date: str):
    x0, y0 = tile_xy(BOX[0], BOX[3], Z)
    x1, y1 = tile_xy(BOX[2], BOX[1], Z)
    t = 256 // STEP
    grid = np.zeros(((y1 - y0 + 1) * t, (x1 - x0 + 1) * t), dtype=np.uint8)
    for j in range(y1 - y0 + 1):
        for i in range(x1 - x0 + 1):
            url = f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{LAYER}/default/{date}/GoogleMapsCompatible_Level12/{Z}/{y0 + j}/{x0 + i}.png"
            r = requests.get(url, timeout=60)
            if not r.ok:
                continue
            a = np.array(Image.open(io.BytesIO(r.content)).convert("RGBA"))[::STEP, ::STEP]
            c = np.full(a.shape[:2], 5, dtype=np.uint8)
            c[a[..., 3] == 0] = 0
            for rgb, k in COLOURS.items():
                c[(a[..., 0] == rgb[0]) & (a[..., 1] == rgb[1]) & (a[..., 2] == rgb[2]) & (a[..., 3] > 0)] = k
            grid[j * t:(j + 1) * t, i * t:(i + 1) * t] = c
    py, px = np.mgrid[0:grid.shape[0], 0:grid.shape[1]]
    lon, lat = merc_pixel_to_lonlat(x0 * 256 + px * STEP + 1.0, y0 * 256 + py * STEP + 1.0, Z)
    return grid, lon, lat


def sample(img: np.ndarray, f, lon, lat) -> np.ndarray:
    c, r = f(lon, lat)
    ci, ri = np.floor(c).astype(int), np.floor(r).astype(int)
    inside = (ci >= 0) & (ri >= 0) & (ci < img.shape[1]) & (ri < img.shape[0])
    out = np.zeros(lon.shape, dtype=bool)
    out[inside] = img[ri[inside], ci[inside]] > 0
    return out


def main(dates: list[str]) -> None:
    man = json.loads((DATA / "manifest.json").read_text())
    res = {}
    for d in dates:
        grid, lon, lat = dswx_grid(d)
        w = np.array(Image.open(DATA / "water" / f"{d}.webp").convert("RGBA"))[..., 3]
        rd = np.array(Image.open(DATA / "radar" / f"{d}.webp").convert("RGBA"))[..., 3]
        water = sample(w, lonlat_to_image(man["corners"], w.shape[1], w.shape[0]), lon, lat)
        valid = sample(rd, lonlat_to_image(man["corners"], rd.shape[1], rd.shape[0]), lon, lat)
        res[d] = compare(water, grid, valid)
        print(d, res[d])
    out = {"product": "NASA OPERA DSWx-HLS (JPL, distributed by PO.DAAC), read as the NASA GIBS layer " + LAYER,
           "grid": "about 75 m, every 2nd pixel of GIBS zoom 12", "by_date": res}
    (DATA / "dswx_check.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:] or ["2026-08-29", "2026-09-10"])
