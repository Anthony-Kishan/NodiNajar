#!/usr/bin/env python3
"""
asf_pass_dates.py: list the dates NISAR passed over a river reach, and group
them into 12-day repeat cycles.

Based on the team's first ASF searches (Jamuna and Teesta, 2026-10-09), merged
into one script that takes any AOI file.

  python tools/asf_pass_dates.py --aoi aoi/jamuna_sirajganj.geojson
  python tools/asf_pass_dates.py --aoi aoi/teesta_sundarganj.geojson --products GCOV

No login needed. Output: docs/coverage/nisar_pass_dates_<aoi>.csv

Why the cycle grouping: NISAR repeats its orbit every 12 days, so dates that
are a multiple of 12 days apart usually come from the same track. A time series
must use ONE track and frame. This grouping is a quick check from dates alone;
tools/check_coverage.py confirms the actual track and frame numbers.
"""
import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPEAT_DAYS = 12


def load_bbox(path):
    from shapely.geometry import shape
    data = json.loads(Path(path).read_text())
    geom = data["features"][0]["geometry"] if data.get("type") == "FeatureCollection" else data.get("geometry", data)
    return list(shape(geom).bounds)   # west, south, east, north


def cycles(dates, repeat=REPEAT_DAYS):
    """Group dates by their position in the repeat cycle. Returns {phase: [dates]}."""
    ref = date(2026, 1, 1)
    groups = defaultdict(list)
    for d in sorted(dates):
        groups[(d - ref).days % repeat].append(d)
    return dict(groups)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aoi", required=True, help="GeoJSON polygon of the river reach")
    ap.add_argument("--start", default="2026-06-17", help="Start date (calibrated NISAR begins 2026-06-17)")
    ap.add_argument("--end", default="2026-09-30", help="End date")
    ap.add_argument("--products", nargs="+", default=["GCOV", "GUNW"], help="NISAR L2 products")
    ap.add_argument("--out", default=str(ROOT / "docs" / "coverage"), help="Folder for the CSV")
    args = ap.parse_args()
    try:
        import asf_search as asf
    except ImportError:
        sys.exit("Missing packages. Run: pip install -r requirements.txt")

    bbox = load_bbox(args.aoi)
    name = Path(args.aoi).stem
    opts = asf.ASFSearchOptions(
        dataset=[asf.DATASET.NISAR],
        processingLevel=args.products,
        bbox=bbox,
        start=f"{args.start}T00:00:00Z",
        end=f"{args.end}T23:59:59Z",
        productionConfiguration=["PR"],   # PR = standard production products
        maxResults=1000,
    )
    print(f"Searching ASF: NISAR {'+'.join(args.products)} over {name} {bbox}, {args.start} to {args.end}")
    results = asf.search(opts=opts)

    dates = set()
    for feature in results.geojson().get("features", []):
        start = feature.get("properties", {}).get("startTime")
        if start:
            dates.add(datetime.fromisoformat(start.replace("Z", "+00:00")).date())
    dates = sorted(dates)
    if not dates:
        sys.exit("No passes found. Check the AOI, the dates and the product names.")

    groups = cycles(dates)
    phase_of = {d: p for p, ds in groups.items() for d in ds}
    label = {p: f"C{i + 1}" for i, p in enumerate(sorted(groups, key=lambda p: groups[p][0]))}

    print(f"\n{len(dates)} distinct acquisition dates, {dates[0]} to {dates[-1]}")
    print(f"Grouped into {len(groups)} repeat cycles ({REPEAT_DAYS}-day):")
    for p in sorted(groups, key=lambda p: groups[p][0]):
        ds = groups[p]
        gaps = [(b - a).days for a, b in zip(ds, ds[1:])]
        missed = sum(g // REPEAT_DAYS - 1 for g in gaps)
        print(f"  {label[p]}: {len(ds)} dates  {', '.join(d.strftime('%d %b') for d in ds)}"
              f"{f'   ({missed} missed pass(es))' if missed else ''}")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    out_csv = out / f"nisar_pass_dates_{name}.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pass_number", "date", "day_of_week", "cycle", "products_searched"])
        for i, d in enumerate(dates, start=1):
            w.writerow([i, d.isoformat(), d.strftime("%A"), label[phase_of[d]], "+".join(args.products)])
    print(f"\nSaved {out_csv}")
    print("Next: python tools/check_coverage.py --aoi", args.aoi, "--products GCOV   (confirms track and frame)")


if __name__ == "__main__":
    main()
