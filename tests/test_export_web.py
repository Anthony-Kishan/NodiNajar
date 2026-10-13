import csv
import io

from src.pipeline.export_web import rank_segments, segments_csv


def seg(id, level, retreat, homes):
    return {"properties": {"id": id, "level": level, "retreat_m": retreat, "homes_near": homes, "side": "west",
                           "centre": [89.7, 24.3], "lost_ha": 1.0, "history_m": [0.0, None, retreat]}}


def test_red_first_then_biggest_retreat():
    out = rank_segments([seg("A", "amber", 360, 0), seg("B", "red", 160, 67), seg("C", "red", 230, 33)])
    assert [f["properties"]["id"] for f in out] == ["C", "B", "A"]
    assert [f["properties"]["rank"] for f in out] == [1, 2, 3]


def test_csv_keeps_missing_passes_empty():
    feats = rank_segments([seg("B", "red", 160, 67)])
    rows = list(csv.reader(io.StringIO(segments_csv(feats, ["d0", "d1", "d2"]))))
    assert rows[0][-3:] == ["bank_m_d0", "bank_m_d1", "bank_m_d2"]
    assert rows[1][-3:] == ["0.0", "", "160"]
