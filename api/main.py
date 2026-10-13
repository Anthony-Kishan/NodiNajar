"""
NodiNajar API (FastAPI). Serves the processed NISAR results to the web app,
officials' tools and anyone who wants the open data.

Run:  uvicorn api.main:app --reload            (from the repo root)
Data: NODINAJAR_DATA (default webapp/public/data), written by
      python -m src.pipeline.export_web. A PostGIS backend is the next step
      (see api/load_postgis.py and docker-compose.yml); the routes stay the same.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.alerts.templates import alert_text, audience

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("NODINAJAR_DATA", ROOT / "webapp" / "public" / "data"))

app = FastAPI(title="NodiNajar API", version="0.1.0",
              description="Riverbank erosion from NASA-ISRO NISAR radar (provisional data). Every number comes from tested code; none from AI.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


@lru_cache(maxsize=1)
def _load() -> dict:
    if not (DATA / "manifest.json").exists():
        raise RuntimeError(f"no data in {DATA}; run python -m src.pipeline.export_web")
    m = json.loads((DATA / "manifest.json").read_text())
    segs = json.loads((DATA / m["files"]["segments"]).read_text())
    return {"manifest": m, "segments": segs}


def expected_passes(last: date, repeat: int, today: date, ahead: int = 3) -> list[dict]:
    """Dates the same track is expected again (12-day repeat). A schedule, not observations."""
    out, d = [], last
    while sum(1 for p in out if p["status"] == "upcoming") < ahead:
        d += timedelta(days=repeat)
        out.append({"date": d.isoformat(), "status": "upcoming" if d >= today else "expected-unprocessed"})
    return out


@app.get("/health")
def health():
    return {"ok": True, "data": str(DATA), "time": datetime.now(timezone.utc).isoformat(timespec="seconds")}


@app.get("/stats")
def stats():
    m = _load()["manifest"]
    return {"label": m["label"], "generated_utc": m["generated_utc"], "period_days": m["period_days"],
            "totals": m["totals"], "segments": m["segments"], "first_pass": m["passes"][0]["date"], "last_pass": m["passes"][-1]["date"]}


@app.get("/passes")
def passes():
    return _load()["manifest"]["passes"]


@app.get("/schedule")
def schedule(today: date | None = None):
    m = _load()["manifest"]
    last = date.fromisoformat(m["passes"][-1]["date"])
    repeat = (m.get("track") or {}).get("repeat_days", 12)
    return {"last_processed": last.isoformat(), "repeat_days": repeat,
            "expected": expected_passes(last, repeat, today or datetime.now(timezone.utc).date())}


@app.get("/segments")
def segments(level: str | None = Query(None, pattern="^(red|amber)$"), side: str | None = Query(None, pattern="^(west|east)$")):
    fc = _load()["segments"]
    feats = [f for f in fc["features"] if (level is None or f["properties"]["level"] == level)
             and (side is None or f["properties"]["side"] == side)]
    return {"type": "FeatureCollection", "features": feats}


@app.get("/segments/{seg_id}")
def segment(seg_id: str):
    for f in _load()["segments"]["features"]:
        if f["properties"]["id"] == seg_id:
            return f
    raise HTTPException(404, f"no segment {seg_id}")


@app.get("/alerts/{seg_id}")
def alert(seg_id: str, lang: str = Query("bn", pattern="^(bn|en)$")):
    p = segment(seg_id)["properties"]
    days = _load()["manifest"]["period_days"]
    return {"id": seg_id, "level": p["level"], "lang": lang, "text": alert_text(p, days, lang),
            "audience": audience(p["level"]), "send": "disabled (needs SMS/voice gateway credentials)"}
