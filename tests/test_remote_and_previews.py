"""Remote (HTTP range) reading of GCOV crops, subset save/load, and preview georeferencing."""
import functools
import http.server
import io
import os
import sys
import threading
from pathlib import Path

import h5py
import numpy as np
import pytest
from pyproj import Transformer

from src.acquire import nisar

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import browse_previews  # noqa: E402

NAME = "NISAR_L2_PR_GCOV_023_069_A_014_4005_DHDH_A_20260618T232135_20260618T232210_P05023_N_F_J_001.h5"


def _mock(path, n=800, px=20.0):
    x = 150000 + px * np.arange(n) + px / 2
    y = 2800000 - px * np.arange(n) - px / 2
    a = np.random.default_rng(0).gamma(4, .04, (n, n)).astype("float32")
    with h5py.File(path, "w") as f:
        g = f.create_group("science/LSAR/GCOV/grids/frequencyA")
        g.create_dataset("HHHH", data=a, chunks=(128, 128))
        g.create_dataset("xCoordinates", data=x)
        g.create_dataset("yCoordinates", data=y)
        g.create_dataset("projection", data=np.int32(32646)).attrs["epsg_code"] = 32646
    return x, y


class _RangeHandler(http.server.SimpleHTTPRequestHandler):
    served = 0

    def log_message(self, *a):
        pass

    def send_head(self):
        rng, path = self.headers.get("Range"), self.translate_path(self.path)
        if not rng or not os.path.isfile(path):
            return super().send_head()
        a, b = rng.replace("bytes=", "").split("-")
        size = os.path.getsize(path)
        a, b = int(a), min(int(b) if b else size - 1, size - 1)
        with open(path, "rb") as f:
            f.seek(a)
            data = f.read(b - a + 1)
        _RangeHandler.served += len(data)
        self.send_response(206)
        self.send_header("Content-Range", f"bytes {a}-{b}/{size}")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        return io.BytesIO(data)


def test_remote_crop_matches_local_and_roundtrips(tmp_path):
    fsspec = pytest.importorskip("fsspec")
    pytest.importorskip("aiohttp")
    x, y = _mock(tmp_path / NAME)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_RangeHandler, directory=str(tmp_path)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        to_ll = Transformer.from_crs(32646, 4326, always_xy=True)
        w, n = to_ll.transform(x[300], y[300])
        e, s = to_ll.transform(x[420], y[500])
        url = f"http://127.0.0.1:{srv.server_address[1]}/{NAME}"
        remote = nisar.read_gcov(url, (w, s, e, n), fs=fsspec.filesystem("http"))
        local = nisar.read_gcov(tmp_path / NAME, (w, s, e, n))
    finally:
        srv.shutdown()
    assert remote.date == "2026-06-18" and remote.granule == NAME[:-3]
    assert np.array_equal(remote.power, local.power, equal_nan=True)
    back = nisar.load_scene(nisar.save_scene(remote, tmp_path / "s.npz"))
    assert np.array_equal(back.power, remote.power, equal_nan=True)
    assert (back.date, back.epsg, back.pixel_m, back.granule) == (remote.date, remote.epsg, remote.pixel_m, remote.granule)


def test_preview_affine_fit_recovers_known_transform():
    # A rotated quadrilateral footprint drawn into a north-up lat/lon image
    lon0, lat0, dlon, dlat = 88.6, 26.29, 0.0017, -0.0016
    foot = [(91.90, 24.01), (91.30, 26.14), (88.85, 25.53), (89.50, 23.41)]
    h, w = 1984, 2011
    jj, ii = np.meshgrid(np.arange(w), np.arange(h))
    lon, lat = lon0 + jj * dlon, lat0 + ii * dlat

    def inside(px, py, poly):
        c = np.zeros_like(px, bool)
        for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
            cross = ((y1 > py) != (y2 > py)) & (px < (x2 - x1) * (py - y1) / (y2 - y1 + 1e-12) + x1)
            c ^= cross
        return c

    alpha = inside(lon, lat, foot).astype("uint8") * 255
    M, resid = browse_previews.fit_lonlat_to_pixel(alpha, foot)
    assert resid < 2.0
    # the Jamuna bridge should land where the true transform puts it
    bx, by = np.array([89.77, 24.40, 1.0]) @ M
    assert abs(bx - (89.77 - lon0) / dlon) < 2 and abs(by - (24.40 - lat0) / dlat) < 2
