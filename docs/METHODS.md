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

## Back-test (to do with real data)

Score flagged cells against `ground_truth/events.csv`. An event counts as caught if its cell was red at least 12 days before the report date. Report the hit rate, false alarm rate and median lead time, even if the numbers are modest.
