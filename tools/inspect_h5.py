#!/usr/bin/env python3
"""
inspect_h5.py: learn the layout of a NISAR HDF5 product before the event.

Prints every group and dataset (shape, type, key attributes), points out the
layers we care about, and saves a quick-look PNG.

Examples
  python tools/inspect_h5.py outputs/samples/NISAR_L2_..._GCOV_....h5
  python tools/inspect_h5.py file.h5 --quicklook auto
  python tools/inspect_h5.py file.h5 --quicklook /science/LSAR/GCOV/grids/frequencyA/HHHH --db
  python tools/inspect_h5.py file.h5 --max-depth 4

It does not assume exact NISAR paths: it searches by layer name, so it keeps
working if the product layout changes between releases.
"""
import argparse
import sys
from pathlib import Path

try:
    import h5py
    import numpy as np
except ImportError:
    sys.exit("Missing packages. Run: pip install -r requirements.txt")

# Layer names worth flagging, with what each one is for in NodiNajar.
INTERESTING = {
    "HHHH": "backscatter, HH pol (erosion engine: water mask)",
    "VVVV": "backscatter, VV pol (erosion engine: water mask)",
    "HVHV": "backscatter, cross-pol (helps separate wet sand from water)",
    "VHVH": "backscatter, cross-pol",
    "unwrappedPhase": "unwrapped interferogram (embankment engine: deformation)",
    "wrappedInterferogram": "wrapped interferogram",
    "coherenceMagnitude": "coherence (embankment engine: quality mask)",
    "connectedComponents": "unwrapping regions (mask jumps between regions)",
    "mask": "validity / water / shadow mask",
    "layoverShadowMask": "layover and shadow mask",
    "projection": "map projection (EPSG code in attributes)",
    "xCoordinateSpacing": "pixel size in x",
    "yCoordinateSpacing": "pixel size in y",
    "zeroDopplerStartTime": "acquisition start time",
    "referenceZeroDopplerStartTime": "first date of the pair",
    "secondaryZeroDopplerStartTime": "second date of the pair",
}
ATTR_KEYS = ("units", "description", "epsg_code", "spatial_ref", "grid_mapping", "_FillValue")


def short(value, n=80):
    if isinstance(value, bytes):
        value = value.decode(errors="replace")
    if isinstance(value, np.ndarray) and value.size == 1:
        value = value.item()
    s = str(value).replace("\n", " ")
    return s if len(s) <= n else s[: n - 3] + "..."


def walk(f, max_depth):
    found = []

    def visit(name, obj):
        depth = name.count("/")
        leaf = name.rsplit("/", 1)[-1]
        if leaf in INTERESTING:
            found.append((name, obj))
        if depth >= max_depth:
            return
        indent = "  " * depth
        if isinstance(obj, h5py.Group):
            print(f"{indent}{leaf}/")
        else:
            info = f"{indent}{leaf}  shape={obj.shape} dtype={obj.dtype}"
            if obj.size == 1 or (obj.dtype.kind in "SO" and obj.size < 4):
                try:
                    info += f"  value={short(obj[()])}"
                except Exception:
                    pass
            print(info)
            for k in ATTR_KEYS:
                if k in obj.attrs:
                    print(f"{indent}    @{k} = {short(obj.attrs[k])}")

    f.visititems(visit)
    return found


def pick_auto(found):
    """Prefer a 2-D backscatter layer, then coherence, then unwrapped phase."""
    order = ["HHHH", "VVVV", "HVHV", "coherenceMagnitude", "unwrappedPhase"]
    for want in order:
        for name, obj in found:
            if name.endswith("/" + want) and isinstance(obj, h5py.Dataset) and obj.ndim == 2:
                return name
    return None


def quicklook(f, path, out_png, db, max_px=1500):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ds = f[path]
    if ds.ndim != 2:
        sys.exit(f"{path} is not 2-D (shape {ds.shape}); pick another layer.")
    step = max(1, int(max(ds.shape) / max_px))
    arr = ds[::step, ::step].astype("float64")
    if np.iscomplexobj(arr):
        arr = np.abs(arr)
    arr[~np.isfinite(arr)] = np.nan
    if db:
        with np.errstate(divide="ignore", invalid="ignore"):
            arr = 10 * np.log10(arr)
        arr[~np.isfinite(arr)] = np.nan
    lo, hi = np.nanpercentile(arr, [2, 98])

    fig, ax = plt.subplots(figsize=(8, 8 * arr.shape[0] / arr.shape[1]))
    im = ax.imshow(arr, cmap="gray", vmin=lo, vmax=hi)
    ax.set_title(f"{path.rsplit('/', 1)[-1]}  (shown at 1/{step} resolution)" + ("  [dB]" if db else ""))
    ax.set_axis_off()
    fig.colorbar(im, ax=ax, fraction=0.03)
    fig.savefig(out_png, dpi=120, bbox_inches="tight")
    valid = np.isfinite(arr).mean() * 100
    print(f"\nQuick-look saved: {out_png}")
    print(f"  shape {ds.shape}, shown at 1/{step}, valid pixels {valid:.0f}%, 2-98% range {lo:.2f} to {hi:.2f}")
    if db:
        print("  Tip: open water is usually the darkest cluster (often below about -18 dB);"
              " note the value you see for the Jamuna channel.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help="NISAR .h5 file")
    ap.add_argument("--max-depth", type=int, default=8, help="How deep to print the tree")
    ap.add_argument("--quicklook", help="'auto' or a full dataset path to render as PNG")
    ap.add_argument("--db", action="store_true", help="Show backscatter in decibels")
    ap.add_argument("--out", default="outputs", help="Folder for the PNG")
    args = ap.parse_args()

    with h5py.File(args.file, "r") as f:
        print(f"File: {args.file}\n")
        found = walk(f, args.max_depth)

        print("\nLayers NodiNajar will use:")
        if not found:
            print("  none of the expected names found; read the tree above and update INTERESTING")
        for name, obj in found:
            leaf = name.rsplit("/", 1)[-1]
            shape = getattr(obj, "shape", "")
            print(f"  {name}  {shape}\n      -> {INTERESTING[leaf]}")

        if args.quicklook:
            path = pick_auto(found) if args.quicklook == "auto" else args.quicklook
            if not path:
                sys.exit("No 2-D layer found for --quicklook auto; pass a dataset path.")
            Path(args.out).mkdir(parents=True, exist_ok=True)
            png = Path(args.out) / f"{Path(args.file).stem}_{path.rsplit('/', 1)[-1]}.png"
            quicklook(f, path, png, db=args.db or path.endswith(("HHHH", "VVVV", "HVHV", "VHVH")))


if __name__ == "__main__":
    main()
