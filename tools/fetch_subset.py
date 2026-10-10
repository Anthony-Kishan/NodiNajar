#!/usr/bin/env python3
"""
fetch_subset.py: pull only our river box out of each NISAR GCOV granule.

A GCOV granule is about 7 GB, but the Jamuna box is about 2% of it. This reads
the box straight from NASA's servers (HTTP range requests with your Earthdata
login) and saves a small .npz per date in cache/subsets/ (gitignored).

  export EARTHDATA_TOKEN="..."      # or EARTHDATA_USERNAME + EARTHDATA_PASSWORD, or ~/.netrc
  python tools/fetch_subset.py --csv docs/coverage/gcov_jamuna_track069_frame014.csv
  python tools/fetch_subset.py --csv docs/coverage/gcov_jamuna_track069_frame014.csv --limit 2
  python tools/fetch_subset.py --url https://nisar.asf.earthdatacloud.nasa.gov/.../file.h5
  python tools/fetch_subset.py --files cache/nisar/*.h5          # already-downloaded files

Then build the demo from the subsets:
  python -m src.pipeline.build_demo --subsets cache/subsets/*.npz

NISAR products are PROVISIONAL (validated at a limited set of sites).
"""
import argparse
import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.acquire import nisar  # noqa: E402
from src.pipeline.build_demo import load_bbox  # noqa: E402


def sources_from_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows or "h5_url" not in rows[0]:
        sys.exit(f"{path} needs an h5_url column")
    return [r["h5_url"] for r in sorted(rows, key=lambda r: r.get("date", ""))]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv", help="Granule list with an h5_url column (docs/coverage/)")
    src.add_argument("--url", nargs="+", help="One or more GCOV .h5 URLs")
    src.add_argument("--files", nargs="+", help="Local GCOV .h5 files")
    ap.add_argument("--aoi", default=str(ROOT / "aoi" / "jamuna_sirajganj.geojson"))
    ap.add_argument("--pol", default="HHHH", help="Backscatter layer (default HHHH)")
    ap.add_argument("--out", default=str(ROOT / "cache" / "subsets"))
    ap.add_argument("--limit", type=int, default=0, help="Only the first N granules")
    ap.add_argument("--force", action="store_true", help="Fetch again even if the subset exists")
    args = ap.parse_args()

    sources = sources_from_csv(args.csv) if args.csv else (args.url or args.files)
    if args.limit:
        sources = sources[: args.limit]
    bbox = load_bbox(args.aoi)
    out = Path(args.out)
    print(f"{len(sources)} granule(s), box {[round(v, 4) for v in bbox]}, layer {args.pol} -> {out}/")

    done, failed = 0, []
    for i, s in enumerate(sources, 1):
        target = out / f"{nisar.granule_name(s)}.npz"
        if target.exists() and not args.force:
            print(f"[{i}/{len(sources)}] exists, skipping: {target.name}")
            done += 1
            continue
        t = time.time()
        try:
            sc = nisar.read_gcov(s, bbox, args.pol)
        except Exception as e:  # keep going: one bad granule must not stop the rest
            print(f"[{i}/{len(sources)}] FAILED {nisar.granule_name(s)}: {type(e).__name__}: {e}")
            failed.append(s)
            continue
        nisar.save_scene(sc, target)
        print(f"[{i}/{len(sources)}] {sc.date}  {sc.power.shape[0]}x{sc.power.shape[1]} px at {sc.pixel_m:g} m, "
              f"EPSG {sc.epsg}, {target.stat().st_size / 1e6:.1f} MB, {time.time() - t:.0f}s")
        done += 1

    print(f"\n{done} subset(s) ready in {out}/" + (f", {len(failed)} failed" if failed else ""))
    if failed:
        print("If every one failed with an auth error: check EARTHDATA_TOKEN or ~/.netrc.\n"
              "If the layer was not found: run tools/inspect_h5.py on one URL and send the output.")
        sys.exit(1)
    print("Next: python -m src.pipeline.build_demo --subsets cache/subsets/*.npz")


if __name__ == "__main__":
    main()
