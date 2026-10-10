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


def test_aoi_stays_inside_track69_on_every_date():
    import csv, json
    from shapely import wkt
    from shapely.geometry import shape
    root = Path(__file__).resolve().parents[1]
    aoi = shape(json.loads((root / "aoi" / "jamuna_sirajganj.geojson").read_text())["features"][0]["geometry"])
    rows = list(csv.DictReader(open(root / "docs" / "coverage" / "gcov_jamuna_track069_frame014.csv")))
    assert len(rows) == 8
    assert all(wkt.loads(r["footprint_wkt"]).contains(aoi) for r in rows)


def test_check_events_flags_rows_outside_the_box(tmp_path, capsys):
    import check_events
    header = ("event_id,event_type,river,district,upazila,union,place,lat,lon,location_precision,location_source,"
              "event_date,date_precision,report_date,homes_lost,other_losses,in_main_reach,source_name,source_url,verified_by,notes\n")
    good = "E1,bank_erosion,Jamuna,Sirajganj,Kazipur,,X,24.50,89.70,village,Google Maps,2026-07-10,exact,2026-07-12,,,yes,S,https://a,,\n"
    out = "E2,bank_erosion,Jamuna,Sirajganj,Kazipur,,Y,24.95,89.70,village,Google Maps,2026-07-10,exact,2026-07-12,,,yes,S,https://b,,\n"
    p = tmp_path / "events.csv"
    p.write_text(header + good + out, encoding="utf-8")
    check_events.main(str(p))
    text = capsys.readouterr().out
    assert "inside the box: 1 of 2" in text and "E2 Y: coordinates fall OUTSIDE" in text
