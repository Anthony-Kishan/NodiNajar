import numpy as np
import pytest

from src.compute import change, water


def test_to_db_known_values():
    out = water.to_db(np.array([1.0, 0.1, 0.01]))
    assert np.allclose(out, [0.0, -10.0, -20.0])


def test_otsu_splits_two_classes():
    rng = np.random.default_rng(0)
    db = np.concatenate([rng.normal(-24, 1.5, 5000), rng.normal(-8, 1.5, 5000)])
    thr = water.otsu_threshold(db)
    assert -20 < thr < -12


def test_water_mask_finds_river_and_drops_specks():
    db = np.full((100, 100), -8.0)
    db[:, 40:60] = -25.0          # river 20 px wide
    db[5, 5] = -25.0              # single dark speck on land
    m, thr = water.water_mask(db, threshold_db=-16, min_pixels=10)
    assert m[:, 40:60].all()
    assert not m[5, 5]
    assert m.sum() == 100 * 20
    assert thr == -16


def test_retreat_distance_matches_bank_shift():
    pixel = 10.0
    a = np.zeros((50, 100), bool); a[:, :40] = True    # water west of col 40
    b = np.zeros((50, 100), bool); b[:, :52] = True    # bank moved 12 px = 120 m east
    lost = change.land_lost(a, b)
    assert lost.sum() == 50 * 12
    ret = change.retreat_distance(b, lost, pixel)
    assert ret.max() == pytest.approx(120.0)
    cells = change.summarise_cells(lost, ret, pixel, cell_m=500)
    assert sum(c["lost_ha"] for c in cells) == pytest.approx(50 * 12 * 100 / 1e4)
    assert max(c["retreat_m"] for c in cells) == pytest.approx(120.0, abs=10)


def test_persistent_loss_ignores_flood_that_recedes():
    a = np.zeros((10, 10), bool)
    b = a.copy(); b[:, :5] = True        # flooded on date B
    c = a.copy(); c[:, :2] = True        # water receded by date C
    p = change.persistent_loss([a, b, c])
    assert p.sum() == 10 * 2


def test_count_near_only_land_points_within_range():
    pixel = 10.0
    w = np.zeros((40, 40), bool); w[:, :10] = True
    pts = np.array([[20, 5], [20, 12], [20, 35]])    # in water, 30 m away, 260 m away
    near = change.count_near(pts, w, pixel, within_m=200)
    assert near.tolist() == [False, True, False]


def test_risk_levels():
    assert change.risk_level(150, 3) == "red"
    assert change.risk_level(150, 0) == "amber"
    assert change.risk_level(40, 9) == "amber"
    assert change.risk_level(10, 9) == "green"
