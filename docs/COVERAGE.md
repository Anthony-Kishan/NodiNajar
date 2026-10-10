# NISAR coverage over our reaches

**Decision: use track 69, frame 14 (ascending) for the Jamuna.** It has a GCOV file on all 8 dates of the 18 Jun cycle, each covering 100% of our box.

**Box changed on 10 October:** now 24.00–24.72° N, 89.60–89.92° E, to include Chauhali upazila (24°01′–24°17′ N), where most of our 2026 ground-truth events are. Still fully inside the track 69 footprint on all 8 dates (checked by `tests/test_tools.py`). The coverage table below was computed on the earlier, smaller box. Subsets fetched before this change must be fetched again.

## GCOV check (10 October 2026)

Searched ASF for NISAR L2 GCOV over `aoi/jamuna_sirajganj.geojson`, 17 June to 30 September 2026: 36 products. Coverage is the share of our box inside each granule footprint.

| Track / frame | Pass | Cycle | GCOV dates | Box covered | File size | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| **69 / 14** | Ascending, 23:21 UTC | 18 Jun | **8**: 18 Jun, 30 Jun, 12 Jul, 24 Jul, 17 Aug, 29 Aug, 10 Sep, 22 Sep | **100%** | 6.7–6.9 GB | **Use this** |
| 19 / 76 | Descending, 12:42 UTC | 27 Jun | 7 dates; some dates have 2 products in different modes | 100% | 1.8–9.4 GB | Backup. Mixed modes need care |
| 170 / 14 | Ascending, 23:29 UTC | 25 Jun | 8 | 64–65% | 6.8–7.0 GB | Misses a third of the box |
| 91 / 76 | Descending, 12:34 UTC | 20 Jun | 8 | 22–34% | 7.0–8.7 GB | Not usable |

All products are processing version P05023, HH/HV (dual-pol) or quad-pol, and labelled PROVISIONAL.

The full list for track 69, with download URLs, preview URLs and footprints, is in [`docs/coverage/gcov_jamuna_track069_frame014.csv`](coverage/gcov_jamuna_track069_frame014.csv).

## Files are large: read only the box

Each GCOV granule is about 7 GB. All 8 dates on track 69 total **54 GB**. Our box is about 2% of a frame, so we never download whole files:

- `tools/fetch_subset.py` reads just the box over HTTPS with your Earthdata login and saves a small `.npz` per date in `cache/subsets/` (tens of MB each instead of 7 GB).
- `tools/browse_previews.py` makes video images from ASF's public preview PNGs (about 170 m per pixel), with no login at all.

## First real files (10 October 2026)

`tools/inspect_h5.py` on the 18 June granule confirmed the layout the reader expects:

| Item | Value |
| --- | --- |
| Backscatter layer | `/science/LSAR/GCOV/grids/frequencyA/HHHH` (also `HVHV`), float32, fill value NaN |
| Pixel size | 10 m (frequency A); a coarser 80 m copy sits in frequency B |
| Full frame | 34,200 × 33,552 pixels |
| Projection | EPSG 32646 (UTM 46N) |
| Our box (first, smaller version) | 5,114 × 2,856 pixels, 100% valid |
| HH range in the box | about −21 to +0.6 dB (2nd to 98th percentile) |
| Subset per date | about 44 MB, about 2 minutes over home internet |

## Earlier search (9 October, GCOV + GUNW together)

31 acquisition dates over the Jamuna box in 4 repeat cycles of 12 days. The raw dates are in `docs/coverage/nisar_pass_dates_*.csv`.

1. **One missed pass per cycle, all in the same window.** No cycle has a pass between 26 July and 12 August. On track 69 the gap runs from 24 July to 17 August (24 days instead of 12). The back-test and the video must not imply a pass in that window.
2. **Teesta.** The 9 October search found the 18 Jun cycle over the Teesta box too. Not yet checked for GCOV coverage there: run `tools/asf_pass_dates.py --aoi aoi/teesta_sundarganj.geojson --products GCOV`.
3. **Back-test timing.** Jotpara (GT008) happened on 25 July and was reported on 29 July. A catch needs a red flag by 17 July. Track 69 has 3 passes before that (18 Jun, 30 Jun, 12 Jul), enough for the two-date rule.

## The synthetic demo

The synthetic test scenes in `src/pipeline/synthetic.py` use the 8 real dates of track 69. When real subsets are loaded, the demo takes its dates from the files.
