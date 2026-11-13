"""
Rain before each NISAR pass for the web app (Radar passes tab).

    python -m src.pipeline.export_rain     # after export_web

Reads data/nasa_power_precip_2026.json (NASA POWER daily precipitation for the
box centre) and webapp/public/data/manifest.json; writes webapp/public/data/rain.json.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.compute.rain import rain_by_pass

ROOT = Path(__file__).resolve().parents[2]


def main() -> Path:
    src = json.loads((ROOT / "data" / "nasa_power_precip_2026.json").read_text())
    man = json.loads((ROOT / "webapp" / "public" / "data" / "manifest.json").read_text())
    dates = [p["date"] for p in man["passes"]]
    first, last = dates[0].replace("-", ""), dates[-1].replace("-", "")
    daily = [{"date": f"{k[:4]}-{k[4:6]}-{k[6:]}", "mm": v} for k, v in sorted(src["daily"].items()) if "20260601" <= k <= last]
    out = {
        "source": src["source"], "request": src["request"], "point": src["point"], "units": "mm",
        "note": "One grid cell at the box centre (about 50 km across); rain over the upstream basin matters too.",
        "daily": daily, "by_pass": rain_by_pass(src["daily"], dates, 12), "first_pass": first,
    }
    p = ROOT / "webapp" / "public" / "data" / "rain.json"
    p.write_text(json.dumps(out))
    print("wrote", p)
    return p


if __name__ == "__main__":
    main()
