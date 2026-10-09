"""Tests for helper logic in tools/ that does not need the network."""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import asf_pass_dates  # noqa: E402


def test_cycles_groups_dates_12_days_apart():
    ds = [date(2026, 6, 18), date(2026, 6, 20), date(2026, 6, 30), date(2026, 7, 2), date(2026, 7, 12)]
    groups = asf_pass_dates.cycles(ds)
    assert sorted(len(v) for v in groups.values()) == [2, 3]
    assert [date(2026, 6, 18), date(2026, 6, 30), date(2026, 7, 12)] in groups.values()


def test_cycles_keeps_a_missed_pass_in_the_same_cycle():
    ds = [date(2026, 7, 24), date(2026, 8, 17)]   # 24 days apart: one pass missing
    assert len(asf_pass_dates.cycles(ds)) == 1
