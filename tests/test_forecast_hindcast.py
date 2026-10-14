import pytest

from src.compute.forecast import backtest, forecast_stretch, summarise_backtests, theil_sen
from src.compute.hindcast import confirmed_at, first_flag, haversine_m, score_event, scorecard

DATES = ["2026-06-18", "2026-06-30", "2026-07-12", "2026-07-24", "2026-08-17", "2026-08-29", "2026-09-10", "2026-09-22"]


# ---------- forecast ----------

def test_theil_sen_exact_line():
    fit = theil_sen([0, 12, 24, 36], [0.0, 12.0, 24.0, 36.0])
    assert fit["slope"] == pytest.approx(1.0)
    assert fit["intercept"] == pytest.approx(0.0)
    assert fit["slope_lo"] == pytest.approx(1.0) and fit["slope_hi"] == pytest.approx(1.0)


def test_theil_sen_ignores_one_wild_pass():
    t = [0, 12, 24, 36, 60, 72]
    y = [0.0, 12.0, 24.0, -300.0, 60.0, 72.0]  # one channel-switch pass
    assert theil_sen(t, y)["slope"] == pytest.approx(1.0)


def test_forecast_straight_line_projects_forward():
    hist = [0.0, 10.0, 20.0, 30.0, 50.0, 60.0, 70.0, 80.0]  # 10 m per 12 days, gap of 24 days included
    f = forecast_stretch(DATES, hist, ["2026-10-04", "2026-10-16"])
    assert f["ok"] and f["rate_m_per_12d"] == pytest.approx(10.0)
    assert [t["expected_m"] for t in f["targets"]] == [90.0, 100.0]
    assert [t["advance_m"] for t in f["targets"]] == [10.0, 20.0]
    for t in f["targets"]:
        assert t["low_m"] <= t["expected_m"] <= t["high_m"]


def test_forecast_never_moves_bank_back_into_river():
    hist = [0.0, -10.0, -20.0, -30.0, -50.0, -60.0, -70.0, -80.0]
    f = forecast_stretch(DATES, hist, ["2026-10-16"])
    assert f["ok"] and not f["advancing"]
    t = f["targets"][0]
    assert t["advance_m"] == 0.0 and t["low_m"] == t["expected_m"]


def test_forecast_needs_enough_passes():
    hist = [0.0, None, None, None, None, 20.0, None, 40.0]
    f = forecast_stretch(DATES, hist, ["2026-10-16"])
    assert not f["ok"] and "need 4" in f["reason"]


def test_forecast_rejects_past_target():
    with pytest.raises(ValueError):
        forecast_stretch(DATES, [0.0, 10, 20, 30, 50, 60, 70, 80], ["2026-09-01"])


def test_backtest_scores_hidden_passes():
    hist = [0.0, 10.0, 20.0, 30.0, 50.0, 60.0, 70.0, 80.0]
    b = backtest(DATES, hist, n_holdout=2)
    assert b["ok"]
    assert [p["error_m"] for p in b["passes"]] == [0.0, 0.0]
    assert all(p["in_range"] for p in b["passes"])


def test_backtest_skips_unmeasured_and_summarises():
    hist = [0.0, 10.0, 20.0, 30.0, 50.0, 60.0, None, 100.0]
    b = backtest(DATES, hist, n_holdout=2)
    assert b["passes"][0]["error_m"] is None
    assert b["passes"][1]["error_m"] == pytest.approx(20.0)
    s = summarise_backtests([b, {"ok": False}])
    assert s["n_scored"] == 1 and s["mae_m"] == pytest.approx(20.0) and s["n_stretches"] == 1


# ---------- hindcast ----------

def test_haversine_one_degree_lat():
    assert haversine_m(89.7, 24.0, 89.7, 25.0) == pytest.approx(111_195, rel=1e-3)


def test_confirmed_uses_smaller_of_two_passes():
    h = [0.0, 50.0, 20.0, None]
    assert confirmed_at(h, 1) == 0.0
    assert confirmed_at(h, 2) == 20.0
    assert confirmed_at(h, 3) is None


def test_first_flag_needs_two_passes_over_threshold():
    assert first_flag([0.0, 40.0, 10.0, 35.0, 45.0]) == 4  # one spike at pass 1 is not enough
    assert first_flag([0.0, 5.0, 10.0]) is None


STRETCH = {"id": "C1", "centre": [89.75, 24.30], "history_m": [0.0, 40.0, 60.0, 80.0, 90.0, 100.0, 110.0, 120.0]}
# flagged at pass 2 (12 Jul): min(40, 60) >= 30


def test_event_warned_with_lead_time():
    ev = {"id": "E1", "date": "2026-07-25", "lat": 24.305, "lon": 89.75, "precision": "village"}
    r = score_event(ev, [STRETCH], DATES)
    assert r["outcome"] == "warned" and r["flag_date"] == "2026-07-12" and r["lead_days"] == 13


def test_latency_can_turn_warning_late():
    ev = {"id": "E1", "date": "2026-07-14", "lat": 24.30, "lon": 89.75, "precision": "point"}
    assert score_event(ev, [STRETCH], DATES)["outcome"] == "warned"
    assert score_event(ev, [STRETCH], DATES, latency_days=5)["outcome"] == "late"


def test_event_far_from_any_stretch_is_off_bank():
    ev = {"id": "E2", "date": "2026-07-25", "lat": 24.40, "lon": 89.75, "precision": "village"}
    assert score_event(ev, [STRETCH], DATES)["outcome"] == "off_bank"


def test_union_precision_is_unscorable():
    ev = {"id": "E3", "date": "2026-07-25", "lat": 24.30, "lon": 89.75, "precision": "union"}
    assert score_event(ev, [STRETCH], DATES)["outcome"] == "unscorable"


def test_scorecard_counts_and_hit_rate():
    quiet = {"id": "C2", "centre": [89.80, 24.50], "history_m": [0.0, 5, 5, 5, 5, 5, 5, 5]}
    events = [
        {"id": "a", "date": "2026-07-25", "lat": 24.30, "lon": 89.75, "precision": "village"},  # warned
        {"id": "b", "date": "2026-07-05", "lat": 24.30, "lon": 89.75, "precision": "village"},  # late
        {"id": "c", "date": "2026-08-01", "lat": 24.50, "lon": 89.80, "precision": "village"},  # missed
        {"id": "d", "date": "2026-08-01", "lat": 24.60, "lon": 89.80, "precision": "village"},  # off bank
        {"id": "e", "date": "2026-08-01", "lat": None, "lon": None, "precision": ""},          # unscorable
    ]
    sc = scorecard(events, [STRETCH, quiet], DATES)
    assert sc["counts"] == {"warned": 1, "late": 1, "missed": 1, "off_bank": 1, "unscorable": 1, "too_early": 0}
    assert sc["on_bank"] == 3 and sc["hit_rate"] == pytest.approx(0.333)
    assert sc["median_lead_days"] == 13


def test_event_before_second_pass_is_too_early():
    ev = {"id": "E4", "date": "2026-06-20", "lat": 24.30, "lon": 89.75, "precision": "village"}
    assert score_event(ev, [STRETCH], DATES)["outcome"] == "too_early"
