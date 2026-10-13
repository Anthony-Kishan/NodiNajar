import numpy as np

from src.compute import bankline


def river(h=200, w=300, west=100, east=200, char=None):
    m = np.zeros((h, w), bool)
    m[:, west:east] = True
    if char:                     # a sandbar inside the river: must not move the banks
        r0, r1, c0, c1 = char
        m[r0:r1, c0:c1] = False
    return m


def test_banks_ignore_chars_inside_the_river():
    a = river()
    b = river(char=(20, 180, 130, 170))
    wa, ea = bankline.bank_columns(bankline.main_river(a, 10.0, 0.5, 50))
    wb, eb = bankline.bank_columns(bankline.main_river(b, 10.0, 0.5, 50))
    assert np.nanmax(np.abs(wa - wb)) == 0 and np.nanmax(np.abs(ea - eb)) == 0


def test_east_bank_retreat_measured_in_metres():
    a = river()
    b = river(); b[0:50, 200:215] = True          # east bank moves 15 px = 150 m in rows 0-49
    fa = bankline.bank_columns(a)
    fb = bankline.bank_columns(b)
    segs = bankline.segment_retreat(bankline.outward_m(fa[1], fb[1], "east", 10.0), 50)
    assert segs[0]["status"] == "ok" and segs[0]["retreat_m"] == 150.0
    assert all(s["retreat_m"] == 0.0 for s in segs[1:])
    west = bankline.segment_retreat(bankline.outward_m(fa[0], fb[0], "west", 10.0), 50)
    assert all(s["retreat_m"] == 0.0 for s in west)


def test_channel_switch_is_flagged_not_counted():
    a = river()
    b = river(); b[0:50, 200:290] = True          # a far side channel joins: 900 m "move"
    fa, fb = bankline.bank_columns(a), bankline.bank_columns(b)
    segs = bankline.segment_retreat(bankline.outward_m(fa[1], fb[1], "east", 10.0), 50)
    assert segs[0]["status"] == "jump" and segs[0]["retreat_m"] is None


def test_river_touching_the_edge_is_a_gap():
    a = river(west=0)
    w, _ = bankline.bank_columns(a)
    assert np.isnan(w).all()
    segs = bankline.segment_retreat(bankline.outward_m(w, w, "west", 10.0), 50)
    assert all(s["status"] == "gap" for s in segs)


def test_confirmed_retreat_ignores_a_flood_that_recedes():
    first = river()
    flood = river(); flood[0:50, 200:212] = True   # +120 m, then gone
    back = river()
    late = river(); late[0:50, 200:205] = True     # +50 m that stays
    cols = [bankline.bank_columns(m) for m in (first, flood, back, late, late)]
    rows = bankline.confirmed_retreat(cols[0], cols[1:], "east", 10.0, 50)
    assert rows[0]["status"] == "ok" and rows[0]["retreat_m"] == 50.0 and rows[0]["confirmed"]
    assert rows[0]["history_m"][:3] == [0.0, 120.0, 0.0]


def test_bank_polylines_follow_the_bank_and_break_at_gaps():
    cols = np.full(200, 120.0)
    cols[90:110] = np.nan                       # no bank measured here: the line must break
    cols[150:] = 180.0                          # bank switches channel: break, do not join
    lines = bankline.bank_polylines(cols, step=5, smooth=1, max_jump_px=30)
    assert len(lines) == 3
    assert all(abs(c - 120) < 1e-9 for _, c in lines[0])
    assert lines[0][-1][0] < 90 and lines[1][0][0] >= 110
    assert all(c == 180 for _, c in lines[2])


def test_bank_polylines_drop_tiny_pieces():
    cols = np.full(40, np.nan); cols[10:16] = 50.0
    assert bankline.bank_polylines(cols, step=5, smooth=1, min_points=4) == []
