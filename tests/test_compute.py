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


def test_valley_threshold_sits_between_water_and_land_peaks():
    rng = np.random.default_rng(1)
    # minority dark water (20%) next to a broad bright land class, like the Jamuna
    db = np.concatenate([rng.normal(-18.5, 1.2, 20000), rng.normal(-10.5, 2.5, 80000)])
    thr = water.valley_threshold(db)
    assert -16.5 < thr < -13.5
    assert thr < water.otsu_threshold(db) + 1.0   # never far above Otsu


def test_valley_threshold_falls_back_to_otsu_without_water_peak():
    db = np.random.default_rng(2).normal(-10, 2, 50000)
    assert water.valley_threshold(db) == water.otsu_threshold(db)


def test_near_river_ignores_small_ponds():
    m = np.zeros((300, 300), bool)
    m[:, 100:140] = True            # river, 300 x 40 px at 10 m = 1.2 km2
    m[20:25, 250:255] = True        # pond
    near = change.near_river(m, pixel_m=10.0, min_area_km2=1.0, within_m=300)
    assert near[150, 120] and near[150, 160] and not near[150, 200]
    assert not near[22, 252]        # the pond is not river


def test_season_thresholds_fill_dates_without_a_valley():
    thr, how = water.season_thresholds([-15.0, None, -15.4, -14.9, None])
    assert thr[1] == thr[4] == -15.0 and thr[2] == -15.4
    assert how[0] == "valley" and how[1].startswith("median of 3")
    assert water.season_thresholds([None, None])[1] == ["otsu", "otsu"]
