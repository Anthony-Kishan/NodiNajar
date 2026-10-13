from datetime import date

import pytest

from src.alerts.templates import alert_text, bn_digits

SEG = {"id": "C011", "level": "red", "retreat_m": 160.0}


def test_bangla_alert_uses_bangla_digits_and_measured_numbers():
    t = alert_text(SEG, 96, "bn")
    assert "৯৬" in t and "১৬০" in t and "উচ্চ" in t and t.endswith("(C011)")
    assert bn_digits(2026) == "২০২৬"


def test_english_alert_and_unknown_language():
    assert "moved 160 m" in alert_text(SEG, 96, "en") and "HIGH" in alert_text(SEG, 96, "en")
    with pytest.raises(ValueError):
        alert_text(SEG, 96, "fr")


def test_schedule_marks_missed_and_upcoming_passes():
    fastapi = pytest.importorskip("fastapi")  # noqa: F841  (API extras are optional for the science tests)
    from api.main import expected_passes
    out = expected_passes(date(2026, 9, 22), 12, date(2026, 10, 13), ahead=2)
    assert [p["date"] for p in out] == ["2026-10-04", "2026-10-16", "2026-10-28"]
    assert [p["status"] for p in out] == ["expected-unprocessed", "upcoming", "upcoming"]
