#!/usr/bin/env python3
"""
buildings_to_csv.py: turn a building-footprint file into one point per building.

The demo only needs where each building is, not its outline. A CSV of centres
is about 20x smaller than the footprints and loads in seconds.

  # 1. download building footprints for the AOI box from Overture Maps
  #    (combines Google Open Buildings, Microsoft building footprints and OpenStreetMap)
  pip install overturemaps
  overturemaps download --bbox=89.60,24.00,89.92,24.72 -f geoparquet --type=building -o cache/buildings.parquet

  # 2. convert to centres
  python tools/buildings_to_csv.py cache/buildings.parquet cache/buildings.csv

  # 3. build the demo with homes
  python -m src.pipeline.build_demo --subsets cache/subsets/*.npz --buildings cache/buildings.csv

Also accepts GeoJSON (.geojson/.json) input. Output columns: longitude, latitude, source.
Credit on screen and in README: Overture Maps Foundation (ODbL), which includes
OpenStreetMap contributors, Google Open Buildings and Microsoft building footprints.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np


def centres_from_parquet(path):
    import pyarrow.parquet as pq
    import shapely
    table = pq.read_table(path, columns=None)
    names = table.column_names
    geom_col = "geometry" if "geometry" in names else next(c for c in names if "geom" in c.lower())
    geoms = shapely.from_wkb(table.column(geom_col).to_numpy(zero_copy_only=False))
    pts = shapely.centroid(geoms)
    xy = shapely.get_coordinates(pts)
    src = None
    if "sources" in names:   # Overture: list of {dataset: ...}
        src = []
        for s in table.column("sources").to_pylist():
            src.append(s[0].get("dataset", "") if s else "")
    return xy, src


def centres_from_geojson(path):
    from shapely.geometry import shape
    data = json.loads(Path(path).read_text())
    xy, src = [], []
    for f in data.get("features", []):
        c = shape(f["geometry"]).centroid
        xy.append((c.x, c.y))
        s = (f.get("properties") or {}).get("sources")
        src.append(s[0].get("dataset", "") if isinstance(s, list) and s else "")
    return np.array(xy).reshape(-1, 2), src


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", help="Footprints: .parquet (Overture GeoParquet) or .geojson")
    ap.add_argument("out", help="Output CSV (longitude, latitude, source)")
    args = ap.parse_args()

    suffix = Path(args.src).suffix.lower()
    xy, src = centres_from_parquet(args.src) if suffix in (".parquet", ".geoparquet") else centres_from_geojson(args.src)
    if not len(xy):
        sys.exit("No buildings found in the input.")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["longitude", "latitude", "source"])
        for i, (lon, lat) in enumerate(xy):
            w.writerow([f"{lon:.6f}", f"{lat:.6f}", src[i] if src else ""])
    counts = {}
    for s in (src or []):
        counts[s or "unknown"] = counts.get(s or "unknown", 0) + 1
    print(f"{len(xy)} buildings -> {args.out}")
    if counts:
        print("  by source: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1])))
    print(f"  box: lon {xy[:, 0].min():.4f} to {xy[:, 0].max():.4f}, lat {xy[:, 1].min():.4f} to {xy[:, 1].max():.4f}")


if __name__ == "__main__":
    main()
