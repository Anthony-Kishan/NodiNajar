"""
Read a NISAR L2 GCOV file and crop it to an area of interest.

The reader tries the documented GCOV paths first (/science/LSAR/GCOV/grids/
frequencyA/...), then falls back to searching by layer name, because the
provisional product layout may change between releases.

`src` can be a local .h5 path or an https:// URL. For a URL, only the bytes of
the cropped area (plus metadata) are read over the network with your Earthdata
login, so a 7 GB granule costs tens of MB instead of a full download.

NISAR products are PROVISIONAL (validated at a limited set of sites).
"""
from __future__ import annotations

import os
import re
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path

import h5py
import numpy as np
from pyproj import Transformer

POL_NAMES = ("HHHH", "VVVV", "HVHV", "VHVH")
GRID_GROUPS = ("science/LSAR/GCOV/grids/frequencyA", "science/LSAR/GCOV/grids/frequencyB")
REMOTE_BLOCK = 8 * 1024 * 1024   # bytes per HTTP range request
DATE_KEYS = ("zeroDopplerStartTime", "referenceZeroDopplerStartTime")


@dataclass
class Scene:
    power: np.ndarray            # linear backscatter, cropped
    x: np.ndarray                # projected x of column centres
    y: np.ndarray                # projected y of row centres
    epsg: int
    date: str                    # YYYY-MM-DD
    granule: str
    pol: str
    pixel_m: float
    source: str = "NISAR GCOV (provisional)"
    notes: list = field(default_factory=list)


def _find(f: h5py.File, leaf: str, prefer_parent: str | None = None):
    # Fast path: the documented location. Avoids walking the whole file,
    # which is slow over the network.
    for parent in ([prefer_parent] if prefer_parent else []) + list(GRID_GROUPS):
        if parent and f"{parent}/{leaf}" in f and isinstance(f[f"{parent}/{leaf}"], h5py.Dataset):
            return f"{parent}/{leaf}"
    hits = []
    f.visititems(lambda n, o: hits.append(n) if n.rsplit("/", 1)[-1] == leaf and isinstance(o, h5py.Dataset) else None)
    if prefer_parent:
        same = [h for h in hits if h.rsplit("/", 1)[0] == prefer_parent]
        if same:
            return same[0]
    return hits[0] if hits else None


def _scalar(ds) -> str:
    v = ds[()]
    if isinstance(v, np.ndarray):
        v = v.ravel()[0] if v.size else ""
    return v.decode() if isinstance(v, bytes) else str(v)


def _epsg(f: h5py.File, parent: str) -> int:
    path = _find(f, "projection", parent)
    if path:
        ds = f[path]
        for k in ("epsg_code", "epsg"):
            if k in ds.attrs:
                return int(np.ravel(ds.attrs[k])[0])
        try:
            return int(_scalar(ds))
        except ValueError:
            pass
    raise KeyError("Could not find the EPSG code; check the file with tools/inspect_h5.py")


def _date(f: h5py.File, fallback_name: str) -> str:
    # NISAR granule names carry the start time (..._20260618T232135_...): no file reads needed.
    m = re.search(r"_(20\d{2})(\d{2})(\d{2})T\d{6}_", fallback_name)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    for key in DATE_KEYS:
        p = _find(f, key)
        if p:
            m = re.search(r"\d{4}-\d{2}-\d{2}", _scalar(f[p]))
            if m:
                return m.group(0)
    m = re.search(r"(20\d{2})(\d{2})(\d{2})T", fallback_name)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    raise KeyError("Could not find the acquisition date")


def is_url(src) -> bool:
    return str(src).startswith(("http://", "https://", "s3://"))


def granule_name(src) -> str:
    return Path(str(src).split("?", 1)[0]).stem


def _https_filesystem():
    """fsspec filesystem carrying the Earthdata login (token, env vars or ~/.netrc)."""
    import earthaccess
    if os.environ.get("EARTHDATA_TOKEN") or os.environ.get("EARTHDATA_USERNAME"):
        earthaccess.login(strategy="environment")
    else:
        earthaccess.login(strategy="netrc")
    return earthaccess.get_fsspec_https_session()


@contextmanager
def open_h5(src, fs=None):
    """Open a local path or a remote URL as an h5py.File. `fs` overrides the Earthdata filesystem (tests)."""
    if is_url(src):
        fs = fs or _https_filesystem()
        with fs.open(str(src), "rb", block_size=REMOTE_BLOCK, cache_type="blockcache") as fobj:
            with h5py.File(fobj, "r") as f:
                yield f
    else:
        with h5py.File(src, "r") as f:
            yield f


def read_gcov(src: str | Path, bbox_lonlat: tuple[float, float, float, float],
              pol: str | None = None, fs=None) -> Scene:
    """Read one GCOV file or URL, cropped to bbox (west, south, east, north) in lon/lat."""
    granule = granule_name(src)
    with open_h5(src, fs) as f:
        layer = None
        for name in ([pol] if pol else POL_NAMES):
            layer = _find(f, name)
            if layer:
                pol = name
                break
        if not layer:
            raise KeyError(f"No backscatter layer {POL_NAMES} in {granule}")
        parent = layer.rsplit("/", 1)[0]
        xp, yp = _find(f, "xCoordinates", parent), _find(f, "yCoordinates", parent)
        if not (xp and yp):
            raise KeyError("No xCoordinates / yCoordinates found next to the layer")
        x, y = f[xp][()], f[yp][()]
        epsg = _epsg(f, parent)

        to_proj = Transformer.from_crs(4326, epsg, always_xy=True)
        w, s, e, n = bbox_lonlat
        xs, ys = to_proj.transform([w, e, w, e], [s, s, n, n])
        cols = np.flatnonzero((x >= min(xs)) & (x <= max(xs)))
        rows = np.flatnonzero((y >= min(ys)) & (y <= max(ys)))
        if cols.size == 0 or rows.size == 0:
            raise ValueError(f"{granule} does not cover the area of interest")
        r0, r1, c0, c1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
        power = f[layer][r0:r1, c0:c1].astype("float32")
        fill = f[layer].attrs.get("_FillValue")
        if fill is not None:
            power[power == np.ravel(fill)[0]] = np.nan
        power[power <= 0] = np.nan
        date = _date(f, granule)

    pixel_m = float(abs(x[1] - x[0]))
    return Scene(power=power, x=x[c0:c1], y=y[r0:r1], epsg=epsg, date=date,
                 granule=granule, pol=pol, pixel_m=pixel_m)


def save_scene(scene: Scene, path: str | Path) -> Path:
    """Save a cropped scene as a small .npz so the demo never needs the 7 GB file again."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = {k: v for k, v in asdict(scene).items() if k not in ("power", "x", "y")}
    np.savez_compressed(path, power=scene.power, x=scene.x, y=scene.y,
                        meta=np.array(repr(meta)))
    return path


def load_scene(path: str | Path) -> Scene:
    import ast
    with np.load(path, allow_pickle=False) as z:
        meta = ast.literal_eval(str(z["meta"]))
        return Scene(power=z["power"], x=z["x"], y=z["y"], **meta)


def align_to(ref: Scene, other: Scene) -> np.ndarray:
    """Nearest-neighbour resample `other` onto `ref`'s grid. Same EPSG required."""
    if other.epsg != ref.epsg:
        raise ValueError("Scenes use different projections; reproject first")
    ci = np.clip(np.searchsorted(other.x, ref.x) if other.x[1] > other.x[0]
                 else np.searchsorted(-other.x, -ref.x), 0, other.x.size - 1)
    ri = np.clip(np.searchsorted(-other.y, -ref.y) if other.y[1] < other.y[0]
                 else np.searchsorted(other.y, ref.y), 0, other.y.size - 1)
    out = other.power[np.ix_(ri, ci)]
    outside = ((ref.x < other.x.min()) | (ref.x > other.x.max()))[None, :] | \
              ((ref.y < other.y.min()) | (ref.y > other.y.max()))[:, None]
    out = out.astype("float32")
    out[np.broadcast_to(outside, out.shape)] = np.nan
    return out
