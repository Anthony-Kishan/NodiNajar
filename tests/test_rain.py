import pytest

from src.compute.rain import rain_by_pass, window_total

DAILY = {"20260601": 1.0, "20260602": 2.0, "20260603": 3.0, "20260604": -999.0, "20260605": 5.0}


def test_window_is_inclusive_and_skips_fill():
    assert window_total(DAILY, "2026-06-05", 3) == (8.0, 1)  # 3rd, 4th (fill), 5th
    assert window_total(DAILY, "2026-06-03", 3) == (6.0, 0)


def test_missing_days_are_counted():
    assert window_total(DAILY, "2026-06-02", 5) == (3.0, 3)


def test_rain_by_pass_since_previous():
    rows = rain_by_pass(DAILY, ["2026-06-02", "2026-06-05"], window_days=2)
    assert rows[0] == {"date": "2026-06-02", "window_days": 2, "rain_window_mm": 3.0, "missing_window": 0}
    assert rows[1]["days_since_prev"] == 3
    assert rows[1]["rain_since_prev_mm"] == 8.0 and rows[1]["missing_since_prev"] == 1


def test_bad_window():
    with pytest.raises(ValueError):
        window_total(DAILY, "2026-06-02", 0)
