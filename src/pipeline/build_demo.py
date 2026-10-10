#!/usr/bin/env python3
"""
build_demo.py: turn radar scenes into the files the web demo reads.

Real NISAR, from small subsets (tools/fetch_subset.py, recommended):
  python -m src.pipeline.build_demo --subsets cache/subsets/*.npz --buildings cache/open_buildings.csv

Real NISAR, from full GCOV files on disk:
  python -m src.pipeline.build_demo --scenes cache/nisar/*.h5 --buildings cache/open_buildings.csv

Synthetic test data (works offline, labelled SYNTHETIC everywhere):
  python -m src.pipeline.build_demo --synthetic

Output: web/demo_fixtures/ (PNGs, cells.geojson, homes.geojson, stats.json).
All numbers come from src/compute. No AI is involved in any figure.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.compute import change, water  # noqa: E402
from src.acquire import nisar  # noqa: E402

OUT = ROOT / "web" / "demo_fixtures"
MAX_PX = 1600


def load_bbox(aoi_path):
    from shapely.geometry import shape
    data = json.loads(Path(aoi_path).read_text())
    geom = data["features"][0]["geometry"] if data.get("type") == "FeatureCollection" else data.get("geometry", data)
    return shape(geom).bounds   # (west, south, east, north)


def load_buildings(path):
    """CSV with latitude/longitude columns (Google Open Buildings) or GeoJSON points/polygons."""
    path = Path(path)
    if path.suffix.lower() == ".csv":
        with path.open(newline="") as f:
            rows = csv.DictReader(f)
            pts = [(float(r["longitude"]), float(r["latitude"])) for r in rows]
        return np.array(pts)
    from shapely.geometry import shape
    data = json.loads(path.read_text())
    pts = []
    for feat in data["features"]:
        c = shape(feat["geometry"]).centroid
        pts.append((c.x, c.y))
    return np.array(pts)


def png_db(db, path, lo=-25.0, hi=-3.0, step=1):
    a = db[::step, ::step]
    g = np.clip((a - lo) / (hi - lo), 0, 1)
    img = np.nan_to_num(g * 255).astype("uint8")
    alpha = np.where(np.isfinite(a), 255, 0).astype("uint8")
    Image.fromarray(np.dstack([img, img, img, alpha]), "RGBA").save(path, optimize=True)


def png_mask(mask, path, rgb, step=1, alpha=200):
    m = mask[::step, ::step]
    rgba = np.zeros(m.shape + (4,), "uint8")
    rgba[m] = (*rgb, alpha)
    Image.fromarray(rgba, "RGBA").save(path, optimize=True)


def corners(ref, to_ll):
    """Image corners [TL, TR, BR, BL] in lon/lat for MapLibre image sources."""
    h = ref.pixel_m / 2
    x0, x1 = ref.x[0] - h, ref.x[-1] + h
    y0, y1 = ref.y[0] + h, ref.y[-1] - h
    lons, lats = to_ll.transform([x0, x1, x1, x0], [y0, y0, y1, y1])
    return [[round(a, 6), round(b, 6)] for a, b in zip(lons, lats)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenes", nargs="*", help="NISAR GCOV .h5 files (same track/frame)")
    ap.add_argument("--subsets", nargs="*", help="Cropped scenes from tools/fetch_subset.py (.npz)")
    ap.add_argument("--synthetic", action="store_true", help="Use synthetic test scenes")
    ap.add_argument("--aoi", default=str(ROOT / "aoi" / "jamuna_sirajganj.geojson"))
    ap.add_argument("--pol", default=None, help="HHHH, VVVV ... (default: first found)")
    ap.add_argument("--threshold", type=float, default=None, help="Water threshold in dB (default: Otsu per scene)")
    ap.add_argument("--cell", type=float, default=500.0, help="Cell size in metres")
    ap.add_argument("--near", type=float, default=200.0, help="Homes within this distance of the new bank (m)")
    ap.add_argument("--buildings", help="Open Buildings CSV or GeoJSON")
    args = ap.parse_args()

    bbox = load_bbox(args.aoi)
    if args.synthetic:
        from src.pipeline import synthetic
        scenes = synthetic.scenes(bbox)
        homes_ll = synthetic.buildings(bbox)
        mode = "synthetic"
    elif args.scenes or args.subsets:
        scenes = ([nisar.read_gcov(p, bbox, args.pol) for p in args.scenes] if args.scenes
                  else [nisar.load_scene(p) for p in args.subsets])
        homes_ll = load_buildings(args.buildings) if args.buildings else np.zeros((0, 2))
        mode = "nisar"
    else:
        sys.exit("Give --subsets FILES, --scenes FILES or --synthetic")

    scenes.sort(key=lambda s: s.date)
    if len(scenes) < 2:
        sys.exit("Need at least 2 dates")
    ref = scenes[0]
    pixel = ref.pixel_m
    to_ll = Transformer.from_crs(ref.epsg, 4326, always_xy=True)
    to_xy = Transformer.from_crs(4326, ref.epsg, always_xy=True)
    step = max(1, int(np.ceil(max(ref.power.shape) / MAX_PX)))

    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*"):
        old.unlink()

    masks, scene_meta = [], []
    for i, s in enumerate(scenes):
        power = s.power if i == 0 else nisar.align_to(ref, s)
        db = water.speckle_filter(water.to_db(power))
        m, thr = water.water_mask(db, args.threshold)
        masks.append(m)
        png_db(db, OUT / f"scene_{i:02d}.png", step=step)
        scene_meta.append({"index": i, "date": s.date, "granule": s.granule, "pol": s.pol,
                           "threshold_db": round(thr, 2), "water_km2": round(m.sum() * pixel ** 2 / 1e6, 2),
                           "image": f"scene_{i:02d}.png"})
        print(f"  {s.date}  threshold {thr:6.2f} dB  water {scene_meta[-1]['water_km2']:8.2f} km2")

    first, last = masks[0], masks[-1]
    if len(masks) >= 3:
        lost = change.persistent_loss([first, masks[-2], last])
        lost_rule = "land on the first date and water on the last two dates"
    else:
        lost = change.land_lost(first, last)
        lost_rule = "land on the first date and water on the last date (unconfirmed: only 2 dates)"
    retreat = change.retreat_distance(last, lost, pixel)
    png_mask(lost, OUT / "loss.png", (230, 57, 70), step=step)

    # homes as pixel positions on the reference grid
    if len(homes_ll):
        hx, hy = to_xy.transform(homes_ll[:, 0], homes_ll[:, 1])
        hc = (np.asarray(hx) - (ref.x[0] - pixel / 2)) / pixel
        hr = ((ref.y[0] + pixel / 2) - np.asarray(hy)) / pixel
        inside = (hc >= 0) & (hc < ref.x.size) & (hr >= 0) & (hr < ref.y.size)
        homes_rc = np.column_stack([hr[inside], hc[inside]])
        homes_ll = homes_ll[inside]
        near = change.count_near(homes_rc, last, pixel, args.near)
    else:
        homes_rc, near = np.zeros((0, 2)), np.zeros(0, bool)

    cells = change.summarise_cells(lost, retreat, pixel, args.cell)
    # Retreat history per cell, pass by pass, relative to the first date.
    # One distance transform per date (not per cell): at 10 m a scene is ~15 million pixels.
    history = [[] for _ in cells]
    for m in masks:
        li_all = change.land_lost(first, m)
        ri_all = change.retreat_distance(m, li_all, pixel)
        for k, c in enumerate(cells):
            li = li_all[c["r0"]:c["r1"], c["c0"]:c["c1"]]
            history[k].append(round(float(np.percentile(ri_all[c["r0"]:c["r1"], c["c0"]:c["c1"]][li], 95)), 1)
                              if li.any() else 0.0)
        del li_all, ri_all
    pad = int(round(args.near / pixel))
    features, at_risk_idx = [], set()
    for k, c in enumerate(cells):
        c["history_m"] = history[k]
        if len(homes_rc):
            sel = ((homes_rc[:, 0] >= c["r0"] - pad) & (homes_rc[:, 0] < c["r1"] + pad) &
                   (homes_rc[:, 1] >= c["c0"] - pad) & (homes_rc[:, 1] < c["c1"] + pad) & near)
            idx = np.flatnonzero(sel)
        else:
            idx = np.array([], int)
        c["homes_near"] = int(idx.size)
        c["level"] = change.risk_level(c["retreat_m"], c["homes_near"])
        if c["level"] != "green":
            at_risk_idx.update(idx.tolist())
        xs = [ref.x[c["c0"]] - pixel / 2, ref.x[c["c1"] - 1] + pixel / 2]
        ys = [ref.y[c["r0"]] + pixel / 2, ref.y[c["r1"] - 1] - pixel / 2]
        lon, lat = to_ll.transform([xs[0], xs[1], xs[1], xs[0], xs[0]], [ys[0], ys[0], ys[1], ys[1], ys[0]])
        clon, clat = to_ll.transform(sum(xs) / 2, sum(ys) / 2)
        c["id"] = f"C{k + 1:03d}"
        c["centre"] = [round(clon, 5), round(clat, 5)]
        props = {kk: vv for kk, vv in c.items() if kk not in ("r0", "r1", "c0", "c1")}
        features.append({"type": "Feature", "properties": props,
                         "geometry": {"type": "Polygon", "coordinates": [[[round(a, 6), round(b, 6)] for a, b in zip(lon, lat)]]}})

    # keep only cells that matter for the map, biggest first
    features.sort(key=lambda f: (-{"red": 2, "amber": 1, "green": 0}[f["properties"]["level"]], -f["properties"]["retreat_m"]))
    (OUT / "cells.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    homes = [{"type": "Feature", "properties": {},
              "geometry": {"type": "Point", "coordinates": [round(homes_ll[i, 0], 6), round(homes_ll[i, 1], 6)]}}
             for i in sorted(at_risk_idx)]
    (OUT / "homes.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": homes}))

    levels = [f["properties"]["level"] for f in features]
    d0, d1 = date.fromisoformat(scenes[0].date), date.fromisoformat(scenes[-1].date)
    stats = {
        "mode": mode,
        "label": "SYNTHETIC TEST DATA - NOT REAL" if mode == "synthetic" else "NISAR L-band GCOV - PROVISIONAL",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "aoi_bbox": [round(v, 4) for v in bbox],
        "epsg": ref.epsg, "pixel_m": pixel, "display_step": step,
        "image_corners": corners(ref, to_ll),
        "scenes": scene_meta,
        "period_days": (d1 - d0).days,
        "lost_rule": lost_rule,
        "totals": {
            "land_lost_ha": round(float(lost.sum() * pixel ** 2 / 1e4), 1),
            "max_retreat_m": max([f["properties"]["retreat_m"] for f in features], default=0),
            "cells_red": levels.count("red"), "cells_amber": levels.count("amber"),
            "homes_near_new_bank": int(len(at_risk_idx)),
        },
        "method": {
            "speckle_filter": "median 5x5",
            "water_rule": "dB below threshold (Otsu per scene unless set); specks < 50 px removed",
            "retreat": "95th percentile distance from lost pixels to the nearest land on the last date",
            "cell_m": args.cell, "near_m": args.near,
            "risk_rule": "red: retreat >= 100 m and homes within near_m; amber: retreat >= 30 m",
            "uncertainty": "Pixel spacing sets the minimum detectable retreat (about 2 pixels). Flooding of low land can look like erosion; only land that stays water on the last two passes is counted.",
        },
        "homes_source": "synthetic points" if mode == "synthetic" else (args.buildings or "none"),
    }
    (OUT / "stats.json").write_text(json.dumps(stats, indent=2))
    # One JS file with everything inlined, so web/index.html works by double-click (file://)
    import base64
    def data_uri(name):
        return "data:image/png;base64," + base64.b64encode((OUT / name).read_bytes()).decode()
    images = {m["image"]: data_uri(m["image"]) for m in scene_meta}
    images["loss.png"] = data_uri("loss.png")
    (OUT / "demo_data.js").write_text(
        "window.DEMO = " + json.dumps({"stats": stats, "images": images,
                                      "cells": json.loads((OUT / 'cells.geojson').read_text()),
                                      "homes": json.loads((OUT / 'homes.geojson').read_text())}) + ";\n")
    t = stats["totals"]
    print(f"\n{stats['label']}\n  {d0} to {d1} ({stats['period_days']} days)\n"
          f"  land lost {t['land_lost_ha']} ha, max retreat {t['max_retreat_m']} m, "
          f"red cells {t['cells_red']}, amber {t['cells_amber']}, homes near new bank {t['homes_near_new_bank']}\n"
          f"  wrote {OUT}")


if __name__ == "__main__":
    main()
