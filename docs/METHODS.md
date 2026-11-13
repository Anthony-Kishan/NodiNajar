# Methods

Every number in the demo comes from these steps, implemented in `src/compute` and tested in `tests/`.

1. **Read and crop.** Read the NISAR L2 GCOV backscatter layer (`/science/LSAR/GCOV/grids/frequencyA/HHHH`, 10 m pixels, EPSG 32646) and crop it to the AOI box. `tools/fetch_subset.py` reads only the box over HTTPS (about 45 MB per date instead of 7 GB). Every later scene is resampled to the first scene's grid by nearest neighbour (`src/acquire/nisar.py`). All scenes must come from the same track and frame. We plan to use the 18 Jun repeat cycle (8 passes over the Jamuna, see `docs/COVERAGE.md`).
2. **Decibels and speckle.** Convert linear power to dB (10·log10) and apply a 5×5 median filter.
3. **Water mask.** Pixels darker than the threshold are water. The threshold is the lowest point of the histogram between the water peak and the land peak (`valley_or_none`), per scene, unless `--threshold` is given. On 4 of our 8 dates (12 Jul, 24 Jul, 17 Aug, 29 Aug) wet land fills in that dip and there is no clear valley; those dates use the median of the dates that have one (`season_thresholds`, −15.0 dB). Without this, Otsu's method set −7.7 dB on 24 July and marked 2,021 km² (78% of the box) as water. With it, water on the 8 dates ranges from 454 km² (18 Jun) to 967 km² (24 Jul, the flood peak). Otsu's method is kept as an option but lands too high on the Jamuna: on 18 June 2026 Otsu gave −12.7 dB and marked wet fields and sandbars as water, while the valley sat at −15.0 dB between a water peak at −18.2 dB and a land peak at −10.3 dB. Water patches under 50 px are removed and land holes under 20 px are filled.
4. **Main river.** Water bodies of at least 2 km², after removing channels narrower than 200 m (`bankline.main_river`). Ponds, flooded fields and thin creeks cannot set the bank.
5. **Outer bank lines.** In every image row, the westmost and eastmost river pixel (`bankline.bank_columns`). Sandbars (chars) inside the river are ignored by construction. This matters: between 18 and 30 June 2026 rising water covered chars, and counting every land-to-water pixel reported 8,218 ha "lost" in 12 days. The outer-bank method reports 156 ha.
6. **Retreat per segment.** Each bank is cut into 500 m segments. Retreat is the median outward movement of the bank (positive = the river moved into the land). Confirmed retreat is the smaller of first→last and first→second-last, so a flood that recedes is not counted. A segment is left out (status "jump") when the bank line switched to another channel: median over 400 m, or rows disagreeing by more than 150 m. With only 2 dates, results are marked unconfirmed.
7. **Homes near the new bank.** Count building points on the land side within 200 m of the new bank, in the same segment.
8. **Risk level (starting thresholds, to tune on the back-test):**
   - red: retreat ≥ 100 m **and** at least one home near the new bank
   - amber: retreat ≥ 30 m
   - green: otherwise (not shown)

The original pixel-area method is still available with `--engine area`.

## Known limits

- **Minimum detectable change:** about 2 pixels. Our GCOV layer (frequency A) has 10 m pixels, so about 20 m.
- **Flooding vs erosion:** rising water can still push the outer bank line over low land next to the river. The last-two-dates rule reduces this but doesn't remove it. Comparing passes at a similar river level (BWDB gauge at Sirajganj) is the next improvement.
- **Channel switching:** in a braided river the outermost channel can change between passes. Those segments are reported as unreliable, never as erosion. On 18 to 30 June 2026, 52 of 206 bank segments were unreliable.
- **Wind and rain:** wind-roughened water can look bright and be missed.
- **Provisional data:** NISAR products are provisional.
- **Revisit:** NISAR repeats every 12 days, with 36 to 72 hours from acquisition to data. That supports a 2 to 4 week priority warning, not a same-night siren.
- **Missed pass:** in 2026 every repeat cycle over our reach skips one pass between late July and mid-August, so one interval is 24 days instead of 12.

## Forecast (`src/compute/forecast.py`)

Each stretch's bank position on every pass (metres into the land since 18 June) gets a Theil-Sen straight line: the median of all pairwise slopes, so one wild pass (a channel switch) does not drag it. We project the line to the next passes. The range uses the 10th to 90th percentile of the pairwise slopes. A stretch needs 4 measured passes, and a negative trend is reported as "not advancing", never as land coming back.

Back-test: we hid the last two passes (10 and 22 September), trained on the six before, and compared. Result on the 2026 run: median absolute error 17 m over 56 checks on 28 stretches (10 m on the 5 high-risk stretches), mean 45 m, and 59% of measured values inside the range. We first tried a 25th to 75th percentile range; only 34% of values fell inside, so we widened it to 10th to 90th. That choice was made after seeing the back-test, so treat the 59% as optimistic. The range is still too narrow (the target is about 80%).

Run: `python -m src.pipeline.scorecard` after `export_web`. It writes `webapp/public/data/forecast.json` and `scorecard.json`.

## News back-test (`src/compute/hindcast.py`)

`ground_truth/events.csv` holds erosion reports from Bangladeshi newspapers (Jamuna, Sirajganj, 18 June to 4 October 2026). For each report pinned to a village or a named point, we replay the season pass by pass, using only passes that existed at the time. A stretch is flagged on pass k when its confirmed retreat (the smaller of passes k-1 and k) reaches 30 m. The report counts as warned if a stretch within 1.5 km (village) or 750 m (named point) was flagged on or before the reported date.

Result on the 2026 run: 14 reports in the window. Only 2 fall near a measured outer bank: one warned 23 days before (16 days with a 7-day processing allowance) and one flagged 35 days after. Five are on char islands or banks the v1 engine does not measure. Seven name only a union, so they cannot be matched to a 500 m stretch until the team pins them on a map. Two events are far too few for a hit rate, and the page says so.

Change from the plan: we had planned to count a report as caught only if its stretch was red at least 12 days before. Red needs 100 m of retreat plus homes, and neither on-bank stretch reached red, so under that rule both reports would count as missed. We report the watch-level (30 m) result and state the difference.

Lesson for version 2: most losses reported this monsoon were on chars, where many families live. The water masks already cover the chars; tracking char edges is the next engine.

## Independent water check with NASA OPERA DSWx-HLS (`src/compute/validate.py`)

On 29 August (Landsat) and 10 September (Sentinel-2), an optical satellite passed on the same day as NISAR. We compared our NISAR water mask with NASA JPL's OPERA DSWx-HLS surface-water map on a common grid of about 75 m (every second pixel of the NASA GIBS zoom-12 tiles). Only cells DSWx calls clearly water or clearly not water are compared; partial water and cloud are counted and left out. Cloud hid most of the box both days.

| Day | Cells compared | Same answer | OPERA water also found by NISAR | Water share NISAR / OPERA |
| --- | --- | --- | --- | --- |
| 29 Aug 2026 | 74,507 | 94.1% | 90.1% | 32.0% / 32.6% |
| 10 Sep 2026 | 96,809 | 96.0% | 91.3% | 16.6% / 15.3% |

These numbers were computed on 13 November in the browser with a JavaScript copy of `compare` (same classes and rules), because NASA GIBS was not reachable from our build machine. `python tools/dswx_check.py` reproduces them in Python on any machine that can reach gibs.earthdata.nasa.gov.

## Rain before each pass (`src/compute/rain.py`)

Daily precipitation from NASA POWER (PRECTOTCORR, MERRA-2 and GEOS-IT) at the box centre, summed over the 12 days up to each pass. The wettest window ended on 12 July (297 mm); the river was widest on 24 July. This is a hypothesis about timing, not a finding: the Jamuna rises on rain over its whole basin upstream, and one 50 km grid cell cannot show that.

## Optical days (HLS)

For the optical-and-radar swipe, each pass is paired with the HLS day within 6 days that had the fewest bright, cloud-like pixels on the GIBS tile at the box centre. The choice is recorded in `data/hls_days_2026.json`.
