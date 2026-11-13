import numpy as np
import pytest

from src.compute.validate import compare, lonlat_to_image, merc_pixel_to_lonlat


def test_compare_counts_only_clear_cells():
    dswx = np.array([[1, 2, 2, 3], [4, 1, 2, 0]])
    nisar = np.array([[0, 1, 0, 1], [1, 0, 1, 1]], dtype=bool)
    valid = np.ones_like(nisar)
    r = compare(nisar, dswx, valid)
    # clear cells: (0,0)=1,(0,1)=2,(0,2)=2,(1,1)=1,(1,2)=2 -> 5
    assert r["n_compared"] == 5
    assert r["n_partial_skipped"] == 1 and r["n_cloud_skipped"] == 1
    # agree: (0,0) no/no, (0,1) w/w, (0,2) w/no -> no, (1,1) no/no, (1,2) w/w -> 4 of 5
    assert r["agreement_pct"] == 80.0
    assert r["water_iou_pct"] == pytest.approx(66.7)
    assert r["dswx_water_found_by_nisar_pct"] == pytest.approx(66.7)


def test_compare_respects_valid_mask_and_shapes():
    dswx = np.array([[2, 2]])
    nisar = np.array([[1, 0]], dtype=bool)
    assert compare(nisar, dswx, np.array([[1, 0]]))["agreement_pct"] == 100.0
    with pytest.raises(ValueError):
        compare(nisar, np.array([2]), np.array([1]))


def test_mercator_origin_and_equator():
    lon, lat = merc_pixel_to_lonlat(np.array([0.0, 512.0]), np.array([512.0, 512.0]), z=2)
    assert lon[0] == pytest.approx(-180) and lon[1] == pytest.approx(0)
    assert lat[1] == pytest.approx(0, abs=1e-9)


def test_lonlat_to_image_hits_corners():
    corners = [[89.0, 25.0], [90.0, 25.0], [90.0, 24.0], [89.0, 24.0]]
    f = lonlat_to_image(corners, 100, 200)
    c, r = f(np.array([89.5]), np.array([24.5]))
    assert c[0] == pytest.approx(50) and r[0] == pytest.approx(100)
