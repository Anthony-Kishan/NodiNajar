#!/usr/bin/env python3
"""
browse_previews.py: real NISAR pictures of our reach, with no login and no download.

ASF publishes a public preview image (LATLON.png, about 170 m per pixel) next to
every GCOV granule. This script fetches the previews listed in a granule CSV,
cuts out a box around the river, labels each frame "PROVISIONAL" and writes:

  outputs/previews/<date>.png        one labelled frame per pass
  outputs/previews/jamuna_passes.gif  all passes as an animation
  outputs/previews/first_last.png     first and last pass side by side

  python tools/browse_previews.py --csv docs/coverage/gcov_jamuna_track069_frame014.csv

These are for the video and slides only. Previews are too coarse to measure
bank retreat; the science uses the 20 m GCOV data (tools/fetch_subset.py).

How the preview is placed on the map: the preview is a north-up lat/lon image.
The four extreme corners of its valid (non-transparent) area are matched to the
four corners of the granule footprint, and a least-squares affine transform is
fitted. Checked against the Jamuna (Bangabandhu) Bridge on two dates.
"""
import argparse
import csv
import io
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOX = (89.45, 24.05, 90.05, 24.80)   # west, south, east, north: Sirajganj reach with context


def extreme_corners(alpha):
    """Pixel (x, y) of the top, bottom, left and right extremes of the valid area."""
    ys, xs = np.nonzero(alpha > 0)
    if xs.size == 0:
        raise ValueError("Preview has no valid pixels")
    return [(xs[ys.argmin()], ys.min()), (xs[ys.argmax()], ys.max()),
            (xs.min(), ys[xs.argmin()]), (xs.max(), ys[xs.argmax()])]


def footprint_corners(wkt_or_points):
    """North, south, west and east vertices of the footprint polygon."""
    if isinstance(wkt_or_points, str):
        pts = [tuple(map(float, p.split())) for p in re.findall(r"-?[\d.]+ -?[\d.]+", wkt_or_points)]
    else:
        pts = list(wkt_or_points)
    pts = pts[:4] if len(pts) >= 5 and pts[0] == pts[-1] else pts
    return [max(pts, key=lambda p: p[1]), min(pts, key=lambda p: p[1]),
            min(pts, key=lambda p: p[0]), max(pts, key=lambda p: p[0])]


def fit_lonlat_to_pixel(alpha, footprint):
    """Least-squares affine (lon, lat, 1) -> (x, y). Returns matrix and max residual in pixels."""
    P = np.array(extreme_corners(alpha), float)
    G = np.array(footprint_corners(footprint), float)
    A = np.c_[G, np.ones(len(G))]
    M, *_ = np.linalg.lstsq(A, P, rcond=None)
    return M, float(np.abs(A @ M - P).max())


def crop_box(img, M, box):
    w, s, e, n = box
    (x0, y0), (x1, y1) = np.array([w, n, 1]) @ M, np.array([e, s, 1]) @ M
    return img.crop((int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))))


def label(img, text, scale=3):
    big = img.convert("RGB").resize((img.width * scale, img.height * scale), Image.LANCZOS)
    bar = 34
    out = Image.new("RGB", (big.width, big.height + bar), (17, 17, 17))
    out.paste(big, (0, bar))
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
    ImageDraw.Draw(out).text((10, 8), text, fill=(240, 240, 240), font=font)
    return out


def fetch(url):
    import requests
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGBA")


def footprint_from_asf(granule):
    """Footprint polygon from the public ASF search API (no login)."""
    import requests
    r = requests.get("https://api.daac.asf.alaska.edu/services/search/param",
                     params={"granule_list": granule, "output": "jsonlite"}, timeout=60)
    r.raise_for_status()
    res = r.json().get("results", [])
    if not res:
        raise ValueError(f"ASF has no footprint for {granule}")
    return res[0]["wkt"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", default=str(ROOT / "docs" / "coverage" / "gcov_jamuna_track069_frame014.csv"))
    ap.add_argument("--box", nargs=4, type=float, default=DEFAULT_BOX, metavar=("W", "S", "E", "N"))
    ap.add_argument("--out", default=str(ROOT / "outputs" / "previews"))
    ap.add_argument("--scale", type=int, default=3, help="Upscale factor for video use")
    args = ap.parse_args()

    rows = sorted(csv.DictReader(open(args.csv, newline="", encoding="utf-8")), key=lambda r: r["date"])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    frames = []
    for r in rows:
        img = fetch(r["browse_latlon_png"])
        foot = r.get("footprint_wkt") or footprint_from_asf(r["granule"])
        M, resid = fit_lonlat_to_pixel(np.array(img)[:, :, 3], foot)
        if resid > 5:
            print(f"  warning {r['date']}: corner fit residual {resid:.1f} px; check this frame by eye")
        crop = crop_box(img, M, args.box)
        text = f"NISAR L-band (NASA-ISRO) · {r['date']} · track {r['track']} · PROVISIONAL · ASF preview"
        frame = label(crop, text, args.scale)
        frame.save(out / f"{r['date']}.png")
        frames.append(frame)
        print(f"  {r['date']}  fit residual {resid:.1f} px  -> {out / (r['date'] + '.png')}")

    if frames:
        frames[0].save(out / "jamuna_passes.gif", save_all=True, append_images=frames[1:], duration=900, loop=0)
        a, b = frames[0], frames[-1]
        pair = Image.new("RGB", (a.width + b.width + 12, max(a.height, b.height)), (255, 255, 255))
        pair.paste(a, (0, 0)); pair.paste(b, (a.width + 12, 0))
        pair.save(out / "first_last.png")
        print(f"\n{len(frames)} frames, GIF and side-by-side in {out}/")
        print("Credit on screen: NASA-ISRO NISAR data, ASF DAAC. Say 'provisional'.")


if __name__ == "__main__":
    sys.exit(main())
