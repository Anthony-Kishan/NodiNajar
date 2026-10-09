import h5py
import numpy as np
from pyproj import Transformer

from src.acquire import nisar


def make_mock_gcov(path, x0=200000.0, y0=2740000.0, n=400, px=20.0, date="2026-07-15T00:10:22"):
    x = x0 + px * np.arange(n) + px / 2
    y = y0 - px * np.arange(n) - px / 2
    hh = np.full((n, n), 0.15, "float32"); hh[:, 150:220] = 0.004
    with h5py.File(path, "w") as f:
        g = f.create_group("science/LSAR/GCOV/grids/frequencyA")
        g.create_dataset("HHHH", data=hh)
        g.create_dataset("xCoordinates", data=x)
        g.create_dataset("yCoordinates", data=y)
        g.create_dataset("projection", data=np.int32(32646)).attrs["epsg_code"] = 32646
        f.create_dataset("science/LSAR/identification/zeroDopplerStartTime", data=date.encode())
    return x, y


def test_read_gcov_crops_to_bbox(tmp_path):
    p = tmp_path / "NISAR_L2_GCOV_mock.h5"
    x, y = make_mock_gcov(p)
    to_ll = Transformer.from_crs(32646, 4326, always_xy=True)
    # bbox covering the middle quarter of the grid
    w, n_ = to_ll.transform(x[100], y[100])
    e, s = to_ll.transform(x[300], y[300])
    sc = nisar.read_gcov(p, (w, s, e, n_))
    assert sc.epsg == 32646 and sc.date == "2026-07-15" and sc.pol == "HHHH"
    assert sc.pixel_m == 20.0
    assert 150 < sc.power.shape[0] < 260 and 150 < sc.power.shape[1] < 260
    assert np.nanmin(sc.power) < 0.01          # river kept inside the crop


def test_align_identical_grids_is_identity(tmp_path):
    a, b = tmp_path / "a.h5", tmp_path / "b.h5"
    x, y = make_mock_gcov(a); make_mock_gcov(b, date="2026-07-27T00:10:22")
    to_ll = Transformer.from_crs(32646, 4326, always_xy=True)
    w, n_ = to_ll.transform(x[0] - 1000, y[0] + 1000)
    e, s = to_ll.transform(x[-1] + 1000, y[-1] - 1000)
    bbox = (w, s, e, n_)
    sa, sb = nisar.read_gcov(a, bbox), nisar.read_gcov(b, bbox)
    assert np.array_equal(nisar.align_to(sa, sb), sb.power)
