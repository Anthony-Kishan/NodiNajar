"""
Back-test: would NodiNajar have warned before the news reported erosion?

For each reported erosion event (date + place) we find the measured bank
stretches near the place and replay the season pass by pass, using only the
passes that existed at the time. A stretch counts as flagged on pass k when its
confirmed retreat (the smaller of passes k-1 and k, the same "land that stays
lost" rule as the season map) reaches the watch threshold.

Outcomes per event:
  warned      a nearby stretch was flagged on or before the event date
              (after adding product latency)
  late        flagged, but only after the event
  missed      a measured stretch is nearby but was never flagged
  off_bank    no measured outer-bank stretch near the place (a char island,
              a minor channel, or outside the box): the v1 engine does not
              watch it, so this is reported, not hidden
  unscorable  the report names only a union or upazila, or has no coordinates
  too_early   the event happened before the second pass, the earliest date any
              warning could exist (two passes are needed to see movement)

Deterministic; no numbers are invented. Lead time is measured from the radar
pass date; real alerts arrive later by the product latency (latency_days).
"""
from __future__ import annotations

import math
from datetime import date
from statistics import median

AMBER_M = 30.0
RED_M = 100.0
RADIUS_M = {"point": 750.0, "village": 1500.0}


def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def confirmed_at(history: list[float | None], k: int) -> float | None:
    """Confirmed retreat known after pass k: min of passes k-1 and k, both measured."""
    if k < 1 or history[k] is None or history[k - 1] is None:
        return None
    return min(history[k - 1], history[k])


def first_flag(history: list[float | None], threshold: float = AMBER_M) -> int | None:
    """Index of the first pass whose confirmed retreat reaches the threshold."""
    for k in range(1, len(history)):
        v = confirmed_at(history, k)
        if v is not None and v >= threshold:
            return k
    return None


def score_event(event: dict, stretches: list[dict], dates: list[str], latency_days: int = 0) -> dict:
    """
    event: {id, date, lat, lon, precision}
    stretches: [{id, centre: [lon, lat], history_m: [...]}]
    """
    base = {"id": event["id"], "date": event["date"]}
    prec = (event.get("precision") or "").strip()
    if event.get("lat") is None or event.get("lon") is None or prec not in RADIUS_M:
        return {**base, "outcome": "unscorable", "reason": f"location precision '{prec or 'none'}'"}
    radius = RADIUS_M[prec]
    near = []
    for s in stretches:
        d = haversine_m(event["lon"], event["lat"], s["centre"][0], s["centre"][1])
        if d <= radius:
            near.append((d, s))
    if not near:
        return {**base, "outcome": "off_bank", "radius_m": radius}
    ev = date.fromisoformat(event["date"])
    if ev < date.fromisoformat(dates[1]):
        return {**base, "outcome": "too_early", "nearest": min(near, key=lambda x: x[0])[1]["id"]}
    best = None  # earliest flag among nearby stretches
    for d, s in sorted(near, key=lambda x: x[0]):
        k = first_flag(s["history_m"])
        if k is None:
            continue
        flag_date = date.fromisoformat(dates[k])
        if best is None or flag_date < best["flag_date"]:
            best = {"stretch": s["id"], "distance_m": round(d), "flag_pass": k, "flag_date": flag_date}
    if best is None:
        return {**base, "outcome": "missed", "nearest": near[0][1]["id"], "n_near": len(near)}
    ready = best["flag_date"].toordinal() + latency_days
    lead = ev.toordinal() - ready
    return {**base, "outcome": "warned" if lead >= 0 else "late", "stretch": best["stretch"],
            "distance_m": best["distance_m"], "flag_date": best["flag_date"].isoformat(),
            "lead_days": lead, "n_near": len(near)}


def scorecard(events: list[dict], stretches: list[dict], dates: list[str], latency_days: int = 0) -> dict:
    """Score every event and summarise. Hit rate counts only events on a measured bank."""
    rows = [score_event(e, stretches, dates, latency_days) for e in events]
    count = {k: sum(r["outcome"] == k for r in rows) for k in ("warned", "late", "missed", "off_bank", "unscorable", "too_early")}
    on_bank = count["warned"] + count["late"] + count["missed"]
    leads = sorted(r["lead_days"] for r in rows if r["outcome"] == "warned")
    return {
        "events": rows,
        "counts": count,
        "on_bank": on_bank,
        "hit_rate": round(count["warned"] / on_bank, 3) if on_bank else None,
        "median_lead_days": median(leads) if leads else None,
        "latency_days": latency_days,
    }
