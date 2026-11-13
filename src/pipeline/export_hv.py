"""
NISAR HV images for the web app (the "HV" channel switch on the Live map).

    python tools/fetch_subset.py --csv docs/coverage/gcov_jamuna_track069_frame014.csv --pol HVHV --out cache/subsets_hv
    python -m src.pipeline.export_hv

HH (co-polarised) separates water from land; HV (cross-polarised) is stronger
where radar bounces around inside vegetation, so crops and grass on chars stand
out. Images use the same grid, step and corners as the HH images. No numbers are
computed here; the images are for looking.
"""
from __future__ import annotations

import argparse
import glob
import json
import re
from pathlib import Path

from PIL import Image

from src.acquire.nisar import align_to, load_scene
from src.compute import water
from src.pipeline.build_demo import png_db

ROOT = Path(__file__).resolve().parents[2]


def date_of(path: str) -> str:
    m = re.search(r"_(\d{4})(\d{2})(\d{2})T", Path(path).name)
    if not m:
        raise ValueError(f"no date in {path}")
    return f"{m[1]}-{m[2]}-{m[3]}"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hh", default=str(ROOT / "cache" / "subsets"), help="HH subsets (the reference grid)")
    ap.add_argument("--hv", default=str(ROOT / "cache" / "subsets_hv"))
    ap.add_argument("--data", default=str(ROOT / "webapp" / "public" / "data"))
    ap.add_argument("--lo", type=float, default=-32.0, help="dB shown as black")
    ap.add_argument("--hi", type=float, default=-12.0, help="dB shown as white")
    a = ap.parse_args(argv)
    data = Path(a.data)
    man = json.loads((data / "manifest.json").read_text())
    step = man["display_step"]
    hh = {date_of(p): p for p in glob.glob(f"{a.hh}/*.npz")}
    hv = {date_of(p): p for p in glob.glob(f"{a.hv}/*.npz")}
    (data / "radar_hv").mkdir(exist_ok=True)
    done = 0
    for p in man["passes"]:
        d = p["date"]
        if d not in hv or d not in hh:
            continue
        ref = load_scene(hh[d])
        power = align_to(ref, load_scene(hv[d]))
        db = water.speckle_filter(water.to_db(power))
        tmp = data / "radar_hv" / f"{d}.png"
        png_db(db, tmp, lo=a.lo, hi=a.hi, step=step)
        Image.open(tmp).save(data / "radar_hv" / f"{d}.webp", "WEBP", quality=82, method=6)
        tmp.unlink()
        p["radar_hv"] = f"radar_hv/{d}.webp"
        done += 1
    (data / "manifest.json").write_text(json.dumps(man, indent=1))
    print(f"HV images for {done} of {len(man['passes'])} passes")


if __name__ == "__main__":
    main()
