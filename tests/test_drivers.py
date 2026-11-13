from src.compute.drivers import interval_changes, pair_change, same_stage_pairs

D = ["a", "b", "c"]


def test_interval_changes_tracks_rise_and_fall():
    h = [[0.0, 50.0, 10.0], [0.0, 40.0, None], [0.0, None, 20.0]]
    r = interval_changes(h, D, [100.0, 150.0, 120.0])
    assert r[0]["river"] == "rising" and r[0]["n"] == 2 and r[0]["median_change_m"] == 45.0
    assert r[0]["share_inland_pct"] == 100
    assert r[1]["river"] == "falling" and r[1]["n"] == 1 and r[1]["median_change_m"] == -40.0
    assert r[1]["share_riverward_pct"] == 100


def test_same_stage_pairs_and_pair_change():
    assert same_stage_pairs(D, [100.0, 200.0, 103.0]) == [(0, 2)]
    h = [[0.0, 9.0, 40.0], [0.0, 1.0, -35.0], [None, 0.0, 5.0]]
    r = pair_change(h, 0, 2)
    assert r == {"n": 2, "median_change_m": 2.5, "share_inland_pct": 50, "share_riverward_pct": 50}
    assert pair_change([[None, 1.0]], 0, 1) == {"n": 0}
