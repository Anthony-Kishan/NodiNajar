#!/usr/bin/env python3
"""
check_events.py: sanity-check the ground-truth table and show what is missing.

  python tools/check_events.py ground_truth/events.csv

The back-test needs dated 2026 bank-erosion events inside the main reach
(Jamuna, Sirajganj). This script counts them and flags rows with errors.
"""
import csv
import sys
from datetime import date

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
        if r.get("event_id") in ids:
            problems.append(f"line {i}: duplicate event_id {r['event_id']}")
        ids.add(r.get("event_id"))

    def is_backtest(r):
        ev = parse(r.get("event_date"))
        return (r.get("event_type") == "bank_erosion" and ev and ev >= NISAR_START
                and r.get("in_main_reach", "").lower() == "yes")

    backtest = [r for r in rows if is_backtest(r)]
    erosion_2026 = [r for r in rows if r.get("event_type") == "bank_erosion"
                    and (parse(r.get("event_date")) or date.min) >= NISAR_START]
    breaches = [r for r in rows if r.get("event_type") == "embankment_breach"]
    unverified = [r for r in rows if not (r.get("verified_by") or "").strip()]

    print(f"{len(rows)} events in {path}")
    print(f"  2026 erosion events (any reach, after NISAR start): {len(erosion_2026)}")
    print(f"  2026 erosion events in the MAIN reach (back-test set): {len(backtest)}")
    print(f"  embankment breaches: {len(breaches)}")
    print(f"  not yet verified by a team member: {len(unverified)}")
    if len(backtest) < 8:
        print(f"\nNEED MORE: aim for at least 8 back-test events on the Jamuna in Sirajganj "
              f"(you have {len(backtest)}). Search Bangla and English news for Kazipur, "
              f"Sirajganj Sadar, Belkuchi, Shahjadpur and Chauhali, June to September 2026.")
    if problems:
        print("\nProblems:")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print("\nNo format problems.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "ground_truth/events.csv")
