"""
Export a finished demo build (web/demo_fixtures) for the NodiNajar web app (webapp/).

    python -m src.pipeline.build_demo --subsets cache/subsets/*.npz --buildings cache/buildings.csv
    python -m src.pipeline.export_web                      # writes webapp/public/data/

No numbers are computed here except unit conversions and ranking; every value
comes from stats.json and the GeoJSON files written by build_demo.py.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
LEVEL_ORDER = {"red": 0, "amber": 1, "green": 2}


def to_webp(src: Path, dst: Path, quality: int = 82, width: int | None = None) -> dict:
    """Convert a PNG (radar or mask) to WebP, keeping transparency. Returns size info."""
    im = Image.open(src)
    if width and im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    lossless = im.mode == "RGBA" and src.name.startswith(("water_", "loss"))
    im.save(dst, "WEBP", quality=quality, method=6, lossless=lossless)
    return {"w": im.width, "h": im.height, "bytes": dst.stat().st_size}


def rank_segments(features: list[dict]) -> list[dict]:
    """Red first, then by retreat (largest first), then by homes near; adds a 1-based rank."""
    out = sorted(features, key=lambda f: (LEVEL_ORDER.get(f["properties"]["level"], 9),
                                          -(f["properties"]["retreat_m"] or 0),
                                          -f["properties"]["homes_near"]))
    for i, f in enumerate(out, 1):
        f["properties"]["rank"] = i
    return out


def segments_csv(features: list[dict], dates: list[str]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["rank", "id", "level", "side", "lat", "lon", "retreat_m", "lost_ha", "homes_within_200m"]
               + [f"bank_m_{d}" for d in dates])
    for f in features:
        p = f["properties"]
        w.writerow([p["rank"], p["id"], p["level"], p["side"], p["centre"][1], p["centre"][0], p["retreat_m"],
                    p["lost_ha"], p["homes_near"]] + ["" if v is None else v for v in p["history_m"]])
    return buf.getvalue()


def main(argv: list[str] | None = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", default=str(ROOT / "web" / "demo_fixtures"), help="build_demo output folder")
    ap.add_argument("--out", default=str(ROOT / "webapp" / "public" / "data"), help="web app data folder")
    a = ap.parse_args(argv)
    src, out = Path(a.src), Path(a.out)
    stats = json.loads((src / "stats.json").read_text())
    if out.exists():
        shutil.rmtree(out)
    (out / "radar").mkdir(parents=True)

    passes = []
    for sc in stats["scenes"]:
        i, d = sc["index"], sc["date"]
        radar = to_webp(src / sc["image"], out / "radar" / f"{d}.webp")
        to_webp(src / sc["image"], out / "radar" / f"{d}_thumb.webp", quality=70, width=260)
        water_png = src / f"water_{i:02d}.png"
        has_water = water_png.exists()
        if has_water:
            to_webp(water_png, out / "water" / f"{d}.webp")
        passes.append({"index": i, "date": d, "granule": sc["granule"], "pol": sc["pol"],
                       "threshold_db": sc["threshold_db"], "threshold_from": sc["threshold_from"],
                       "water_km2": sc["water_km2"], "radar": f"radar/{d}.webp", "thumb": f"radar/{d}_thumb.webp",
                       "water": f"water/{d}.webp" if has_water else None, "px": [radar["w"], radar["h"]]})
    to_webp(src / "loss.png", out / "loss.webp")

    cells = json.loads((src / "cells.geojson").read_text())
    feats = rank_segments(cells["features"])
    (out / "segments.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    (out / "segments.csv").write_text(segments_csv(feats, [p["date"] for p in passes]))
    shutil.copy(src / "homes.geojson", out / "homes.geojson")
    if (src / "banklines.geojson").exists():
        shutil.copy(src / "banklines.geojson", out / "banklines.geojson")

    manifest = {
        "label": stats["label"], "mode": stats["mode"], "generated_utc": stats["generated_utc"],
        "aoi_bbox": stats["aoi_bbox"], "corners": stats["image_corners"], "pixel_m": stats["pixel_m"],
        "display_step": stats["display_step"], "period_days": stats["period_days"],
        "totals": stats["totals"], "segments": stats.get("segments"), "method": stats["method"],
        "lost_rule": stats["lost_rule"], "homes_source": "Overture Maps buildings" if stats["mode"] == "nisar" else stats["homes_source"],
        "track": {"repeat_days": 12, "track": 69, "frame": 14, "direction": "ascending"} if stats["mode"] == "nisar" else None,
        "passes": passes, "loss": "loss.webp",
        "files": {"segments": "segments.geojson", "homes": "homes.geojson",
                  "banklines": "banklines.geojson" if (out / "banklines.geojson").exists() else None,
                  "csv": "segments.csv"},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"wrote {out}: {len(passes)} passes, {len(feats)} segments")
    return out


if __name__ == "__main__":
    main()
