"""
Bank change against water level, for the Why it moves tab.

    python -m src.pipeline.export_drivers    # after export_web
"""
from __future__ import annotations

import json
from pathlib import Path

from src.compute.drivers import interval_changes, pair_change, same_stage_pairs

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    data = ROOT / "webapp" / "public" / "data"
    man = json.loads((data / "manifest.json").read_text())
    segs = json.loads((data / "segments.geojson").read_text())["features"]
    dates = [p["date"] for p in man["passes"]]
    water = [p["water_km2"] for p in man["passes"]]
    hist = [f["properties"]["history_m"] for f in segs]
    pairs = [{"a": dates[i], "b": dates[j], "water_a_km2": water[i], "water_b_km2": water[j], **pair_change(hist, i, j)}
             for i, j in same_stage_pairs(dates, water)]
    out = {"note": "Over the 38 stretches the engine flagged (chosen because they moved), so the shares are not for the whole river.",
           "intervals": interval_changes(hist, dates, water), "same_stage": pairs}
    (data / "drivers.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(pairs, indent=1))


if __name__ == "__main__":
    main()
