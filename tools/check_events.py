#!/usr/bin/env python3
"""
check_events.py: sanity-check the ground-truth table and show what is missing.

  python tools/check_events.py ground_truth/events.csv

The back-test needs dated 2026 bank-erosion events inside the main reach
(Jamuna, Sirajganj), each with a latitude and longitude inside the AOI box.
This script counts them and flags rows with errors.

  lat, lon             decimal degrees, e.g. 24.1832, 89.7741 (from Google Maps: right-click > copy)
  location_precision   point | village | union | upazila   (back-test uses point and village only)
  location_source      where the coordinates came from, e.g. "Google Maps, Jotpara village label"
"""
import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AOI = ROOT / "aoi" / "jamuna_sirajganj.geojson"
PRECISIONS = {"point", "village", "union", "upazila"}


def aoi_bbox():
    coords = json.loads(AOI.read_text())["features"][0]["geometry"]["coordinates"][0]
    xs, ys = [c[0] for c in coords], [c[1] for c in coords]
    return min(xs), min(ys), max(xs), max(ys)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

REQUIRED = ["event_id", "event_type", "river", "district", "event_date", "report_date", "source_url"]
TYPES = {"bank_erosion", "embankment_breach"}
NISAR_START = date(2026, 6, 17)


def parse(d):
    try:
        return date.fromisoformat(d)
    except (TypeError, ValueError):
        return None


def main(path):
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
    problems, ids = [], set()
    for i, r in enumerate(rows, start=2):  # line 1 is the header
        for col in REQUIRED:
            if not (r.get(col) or "").strip():
                problems.append(f"line {i}: missing {col}")
        if r.get("event_type") and r["event_type"] not in TYPES:
            problems.append(f"line {i}: event_type must be one of {sorted(TYPES)}")
        ev, rep = parse(r.get("event_date")), parse(r.get("report_date"))
        if r.get("event_date") and not ev:
            problems.append(f"line {i}: event_date is not YYYY-MM-DD")
        if r.get("report_date") and not rep:
            problems.append(f"line {i}: report_date is not YYYY-MM-DD")
        if ev and rep and rep < ev:
            problems.append(f"line {i}: report_date is before event_date")
        lat, lon = num(r.get("lat")), num(r.get("lon"))
        if (r.get("lat") or r.get("lon")) and (lat is None or lon is None):
            problems.append(f"line {i}: lat/lon must be decimal numbers")
        if lat is not None and lon is not None and not (20 < lat < 27 and 88 < lon < 93):
            problems.append(f"line {i}: lat/lon outside Bangladesh; did you swap them?")
        prec = (r.get("location_precision") or "").strip()
        if prec and prec not in PRECISIONS:
            problems.append(f"line {i}: location_precision must be one of {sorted(PRECISIONS)}")
        if lat is not None and not (r.get("location_source") or "").strip():
            problems.append(f"line {i}: add location_source (where the coordinates came from)")
        if r.get("event_id") in ids:
            problems.append(f"line {i}: duplicate event_id {r['event_id']}")
        ids.add(r.get("event_id"))

    def is_backtest(r):
        ev = parse(r.get("event_date"))
        return (r.get("event_type") == "bank_erosion" and ev and ev >= NISAR_START
                and r.get("in_main_reach", "").lower() == "yes")

    w, s_, e, n = aoi_bbox()

    def located(r):
        lat, lon = num(r.get("lat")), num(r.get("lon"))
        return (lat is not None and lon is not None and w <= lon <= e and s_ <= lat <= n
                and r.get("location_precision") in ("point", "village"))

    backtest = [r for r in rows if is_backtest(r)]
    ready = [r for r in backtest if located(r)]
    outside = [r for r in backtest if num(r.get("lat")) is not None and not (
        w <= num(r.get("lon")) <= e and s_ <= num(r.get("lat")) <= n)]
    erosion_2026 = [r for r in rows if r.get("event_type") == "bank_erosion"
                    and (parse(r.get("event_date")) or date.min) >= NISAR_START]
    breaches = [r for r in rows if r.get("event_type") == "embankment_breach"]
    unverified = [r for r in rows if not (r.get("verified_by") or "").strip()]

    print(f"{len(rows)} events in {path}")
    print(f"  2026 erosion events (any reach, after NISAR start): {len(erosion_2026)}")
    print(f"  2026 erosion events in the MAIN reach (back-test set): {len(backtest)}")
    print(f"  embankment breaches: {len(breaches)}")
    print(f"  not yet verified by a team member: {len(unverified)}")
    print(f"  back-test events with village-level coordinates inside the box: {len(ready)} of {len(backtest)}")
    for r in outside:
        print(f"    {r['event_id']} {r['place']}: coordinates fall OUTSIDE the AOI box {w},{s_},{e},{n}")
    missing = [r["event_id"] for r in backtest if num(r.get("lat")) is None]
    if missing:
        print(f"    still need coordinates: {', '.join(missing)}")
    if len(ready) < 8:
        print(f"\nNEED MORE: aim for at least 8 located back-test events on the Jamuna in Sirajganj "
              f"(you have {len(ready)}). Search Bangla and English news for Kazipur, "
              f"Sirajganj Sadar, Belkuchi and Chauhali, 17 June to 30 September 2026.")
    if problems:
        print("\nProblems:")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print("\nNo format problems.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "ground_truth/events.csv")
