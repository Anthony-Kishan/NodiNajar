#!/usr/bin/env python3
"""
check_coverage.py: count NISAR (and optionally Sentinel-1) passes over an area.

Answers the first prep question: does NISAR have enough passes over our reach
for June to September 2026 to build a time series? If not, we fall back to
Sentinel-1 on the same reach.

Examples
  python tools/check_coverage.py --aoi aoi/jamuna_sirajganj.geojson
  python tools/check_coverage.py --aoi aoi/jamuna_sirajganj.geojson --sentinel1
  python tools/check_coverage.py --aoi aoi/teesta_sundarganj.geojson --start 2026-06-01 --end 2026-10-31

Searching needs no login. Downloading (--download N) needs an Earthdata token
in the EARTHDATA_TOKEN environment variable.
"""
import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

try:
    import asf_search as asf
    from shapely.geometry import shape
except ImportError:
    sys.exit("Missing packages. Run: pip install -r requirements.txt")


def load_aoi_wkt(path):
    """Read the first polygon in a GeoJSON file and return it as WKT."""
    data = json.loads(Path(path).read_text())
    if data.get("type") == "FeatureCollection":
        geom = data["features"][0]["geometry"]
    elif data.get("type") == "Feature":
        geom = data["geometry"]
    else:
        geom = data
    return shape(geom).wkt


def prop(p, *keys):
    """Return the first non-empty property among several possible key names."""
    for k in keys:
        v = p.get(k)
        if v not in (None, "", []):
            return v
    return ""


def to_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        return None


def search(wkt, start, end, product, sentinel1=False):
    if sentinel1:
        # GRD high-res is the usual input for water masks (via RTC in HyP3).
        return asf.search(
            platform=asf.PLATFORM.SENTINEL1,
            processingLevel=asf.PRODUCT_TYPE.GRD_HD,
            intersectsWith=wkt,
            start=start,
            end=end,
        )
    return asf.search(
        dataset=asf.DATASET.NISAR,
        processingLevel=product,
        intersectsWith=wkt,
        start=start,
        end=end,
    )


def summarise(label, results):
    rows = []
    by_track = defaultdict(set)
    dates = set()
    for r in results:
        p = r.properties
        start = prop(p, "startTime")
        d = to_date(start)
        track = prop(p, "pathNumber", "relativeOrbit")
        frame = prop(p, "frameNumber", "frame")
        direction = prop(p, "flightDirection")
        if d:
            dates.add(d)
            by_track[(track, frame, direction)].add(d)
        rows.append({
            "product": label,
            "granule": prop(p, "sceneName", "fileID", "granuleName"),
            "start": start,
            "secondary_or_end": prop(p, "stopTime"),
            "track": track,
            "frame": frame,
            "direction": direction,
            "maturity": prop(p, "dataMaturity", "processingLevel"),
            "size_mb": round(float(prop(p, "bytes") or 0) / 1e6, 1),
            "url": prop(p, "url"),
        })

    print(f"\n=== {label}: {len(rows)} products, {len(dates)} distinct acquisition dates")
    if not rows:
        print("    Nothing found. Check the dates, the AOI, or try --sentinel1 as fallback.")
        return rows

    sorted_dates = sorted(dates)
    gaps = [(b - a).days for a, b in zip(sorted_dates, sorted_dates[1:])]
    print(f"    First: {sorted_dates[0]}   Last: {sorted_dates[-1]}")
    if gaps:
        print(f"    Gap between dates (days): median {sorted(gaps)[len(gaps)//2]}, max {max(gaps)}")

    print("    By track / frame / direction (a time series needs ONE geometry):")
    for (track, frame, direction), ds in sorted(by_track.items(), key=lambda kv: -len(kv[1])):
        ds = sorted(ds)
        print(f"      track {track or '?':>4}  frame {frame or '?':>4}  {direction or '?':<10} "
              f"{len(ds):>3} dates   {ds[0]} .. {ds[-1]}")

    best = max(by_track.values(), key=len) if by_track else set()
    verdict = "OK for a time series" if len(best) >= 6 else "THIN: consider Sentinel-1 fallback"
    print(f"    Best single geometry has {len(best)} dates -> {verdict}")
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aoi", required=True, help="GeoJSON polygon of the river reach")
    ap.add_argument("--start", default="2026-06-17", help="Start date (calibrated NISAR begins 2026-06-17)")
    ap.add_argument("--end", default="2026-09-30", help="End date")
    ap.add_argument("--products", nargs="+", default=["GCOV", "GUNW"], help="NISAR L2 products to count")
    ap.add_argument("--sentinel1", action="store_true", help="Also count Sentinel-1 GRD scenes (fallback)")
    ap.add_argument("--out", default="outputs", help="Folder for the CSV")
    ap.add_argument("--download", type=int, default=0, help="Download the first N GCOV products")
    ap.add_argument("--download-dir", default="cache/nisar", help="Where downloads go (gitignored)")
    args = ap.parse_args()

    wkt = load_aoi_wkt(args.aoi)
    aoi_name = Path(args.aoi).stem
    print(f"AOI: {aoi_name}   {args.start} to {args.end}")

    all_rows, gcov_results = [], None
    for product in args.products:
        try:
            res = search(wkt, args.start, args.end, product)
        except Exception as e:  # network or API errors should not hide the other products
            print(f"\n=== {product}: search failed: {e}")
            continue
        if product == "GCOV":
            gcov_results = res
        all_rows += summarise(f"NISAR {product}", res)

    if args.sentinel1:
        try:
            all_rows += summarise("Sentinel-1 GRD", search(wkt, args.start, args.end, None, sentinel1=True))
        except Exception as e:
            print(f"\n=== Sentinel-1: search failed: {e}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / f"coverage_{aoi_name}_{args.start}_{args.end}.csv"
    if all_rows:
        with out_csv.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            w.writeheader()
            w.writerows(all_rows)
        print(f"\nSaved {len(all_rows)} rows to {out_csv}")

    if args.download and gcov_results:
        token = os.environ.get("EARTHDATA_TOKEN")
        if not token:
            sys.exit("Set EARTHDATA_TOKEN (urs.earthdata.nasa.gov > Generate Token) to download.")
        session = asf.ASFSession().auth_with_token(token)
        dl_dir = Path(args.download_dir)
        dl_dir.mkdir(parents=True, exist_ok=True)
        subset = asf.ASFSearchResults(list(gcov_results)[: args.download])
        print(f"Downloading {len(subset)} GCOV sample(s) to {dl_dir} ...")
        subset.download(path=str(dl_dir), session=session)
        print(f"Done. Inspect with: python tools/inspect_h5.py {dl_dir}/<file>.h5 --quicklook auto")
        print(f"Then build the demo: python -m src.pipeline.build_demo --scenes {dl_dir}/*.h5")


if __name__ == "__main__":
    main()
