"""
Forecast and back-test outputs for the web app.

    python -m src.pipeline.export_web          # first (writes segments and manifest)
    python -m src.pipeline.scorecard           # writes forecast.json and scorecard.json

Reads webapp/public/data/{manifest.json,segments.geojson} and ground_truth/events.csv.
All numbers come from src/compute/forecast.py and src/compute/hindcast.py.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date, timedelta
from pathlib import Path

from src.compute import forecast as fc
from src.compute import hindcast as hc

ROOT = Path(__file__).resolve().parents[2]
EVENT_TYPES = {"bank_erosion", "embankment_breach"}
KEEP = ("event_type", "district", "upazila", "union", "place", "event_date", "date_precision", "report_date",
        "homes_lost", "other_losses", "location_precision", "location_source", "source_name", "source_url",
        "verified_by", "notes")


def _float(v: str) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_events(path: Path, start: str, end: str) -> list[dict]:
    """Jamuna events in Sirajganj inside the season window, as dicts for the scorer."""
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["event_type"] not in EVENT_TYPES or r["river"] != "Jamuna" or r["district"] != "Sirajganj":
                continue
            if not (start <= r["event_date"] <= end):
                continue
            out.append({"id": r["event_id"], "date": r["event_date"], "lat": _float(r["lat"]), "lon": _float(r["lon"]),
                        "precision": r["location_precision"], "meta": {k: r.get(k, "") for k in KEEP}})
    return out


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=str(ROOT / "webapp" / "public" / "data"))
    ap.add_argument("--events", default=str(ROOT / "ground_truth" / "events.csv"))
    ap.add_argument("--ahead", type=int, default=3, help="future passes to forecast")
    ap.add_argument("--holdout", type=int, default=2, help="passes hidden for the forecast back-test")
    ap.add_argument("--latency", type=int, default=7, help="days from pass to alert, for the cautious lead time")
    a = ap.parse_args(argv)
    data = Path(a.data)
    man = json.loads((data / "manifest.json").read_text())
    segs = json.loads((data / "segments.geojson").read_text())["features"]
    dates = [p["date"] for p in man["passes"]]
    repeat = (man.get("track") or {}).get("repeat_days", 12)
    last = date.fromisoformat(dates[-1])
    targets = [(last + timedelta(days=repeat * k)).isoformat() for k in range(1, a.ahead + 1)]

    # ---- forecast ----
    rows, tests = [], {"all": [], "red": [], "amber": []}
    for f in segs:
        p = f["properties"]
        fut = fc.forecast_stretch(dates, p["history_m"], targets)
        bt = fc.backtest(dates, p["history_m"], a.holdout)
        tests["all"].append(bt)
        if p["level"] in tests:
            tests[p["level"]].append(bt)
        rows.append({"id": p["id"], "level": p["level"], "forecast": fut, "backtest": bt})
    forecast = {
        "label": man["label"], "method": "Theil-Sen straight-line trend of each stretch's bank position; "
        f"range from the {fc.BAND[0]}th to {fc.BAND[1]}th percentile of pairwise slopes; "
        f"needs {fc.MIN_POINTS} measured passes; a bank is never moved back into the river.",
        "status": "PROVISIONAL", "targets": targets, "trained_through": dates[-1],
        "backtest": {"hidden_passes": dates[-a.holdout:], "trained_through": dates[-a.holdout - 1],
                     **{k: fc.summarise_backtests(v) for k, v in tests.items()}},
        "stretches": rows,
    }
    (data / "forecast.json").write_text(json.dumps(forecast))

    # ---- hindcast scorecard ----
    # events up to one repeat after the last pass can still be warned by that pass
    events = load_events(Path(a.events), dates[0], (last + timedelta(days=repeat)).isoformat())
    stretches = [{"id": f["properties"]["id"], "centre": f["properties"]["centre"], "history_m": f["properties"]["history_m"]}
                 for f in segs]
    sc0 = hc.scorecard(events, stretches, dates, latency_days=0)
    scl = hc.scorecard(events, stretches, dates, latency_days=a.latency)
    meta = {e["id"]: e["meta"] for e in events}
    for r, rl in zip(sc0["events"], scl["events"]):
        r["meta"] = meta[r["id"]]
        r["outcome_with_latency"] = rl["outcome"]
    scorecard = {
        "label": man["label"], "status": "PROVISIONAL", "season": [dates[0], dates[-1]],
        "rule": f"flag = confirmed retreat >= {hc.AMBER_M:g} m on a stretch within "
                f"{hc.RADIUS_M['village']:g} m (village) or {hc.RADIUS_M['point']:g} m (named point) of the reported place",
        "latency_days": a.latency,
        "summary": {k: sc0[k] for k in ("counts", "on_bank", "hit_rate", "median_lead_days")},
        "summary_with_latency": {k: scl[k] for k in ("counts", "on_bank", "hit_rate", "median_lead_days")},
        "events": sc0["events"],
    }
    (data / "scorecard.json").write_text(json.dumps(scorecard))
    b = forecast["backtest"]["all"]
    print(f"forecast: {sum(r['forecast']['ok'] for r in rows)}/{len(rows)} stretches, targets {targets}; "
          f"back-test MAE {b.get('mae_m')} m, median {b.get('median_abs_error_m')} m, in range {b.get('share_in_range')}")
    print(f"scorecard: {len(events)} events, counts {sc0['counts']}, hit rate {sc0['hit_rate']}, "
          f"median lead {sc0['median_lead_days']} d")


if __name__ == "__main__":
    main()
