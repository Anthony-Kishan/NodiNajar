# Methods

Every number in the demo comes from these steps, implemented in `src/compute` and tested in `tests/`.

1. **Read and crop.** Read the NISAR L2 GCOV backscatter layer (HHHH, else VVVV) and crop it to the AOI box. Every later scene is resampled to the first scene's grid by nearest neighbour (`src/acquire/nisar.py`). All scenes must come from the same track and frame. We plan to use the 18 Jun repeat cycle (8 passes over the Jamuna, see `docs/COVERAGE.md`).
2. **Decibels and speckle.** Convert linear power to dB (10·log10) and apply a 5×5 median filter.
3. **Water mask.** Pixels darker than the threshold are water. The threshold comes from Otsu's method per scene unless `--threshold` is given. Water patches under 50 px are removed and land holes under 20 px are filled.
4. **Land lost.** A pixel is land lost if it was land on the first date and water on the **last two** dates. Requiring two dates filters out short floods that recede. With only two scenes the rule falls back to one date and is marked unconfirmed.
5. **Retreat.** For each lost pixel, measure the distance to the nearest land on the last date. Each 500 m cell reports the 95th percentile, so one noisy pixel can't set the value.
6. **Homes near the new bank.** Count building points on land within 200 m of last-date water, inside or within 200 m of the cell.
7. **Risk level (starting thresholds, to tune on the back-test):**
   - red: retreat ≥ 100 m **and** at least one home near the new bank
   - amber: retreat ≥ 30 m
   - green: otherwise

## Known limits

- **Minimum detectable change:** about 2 pixels (for example 40 m at 20 m spacing).
- **Flooding vs erosion:** monsoon flooding of low land can look like erosion. The two-date rule reduces this but doesn't remove it. Wet sandbars (chars) can also look like water.
- **Wind and rain:** wind-roughened water can look bright and be missed.
- **Provisional data:** NISAR products are provisional.
- **Revisit:** NISAR repeats every 12 days, with 36 to 72 hours from acquisition to data. That supports a 2 to 4 week priority warning, not a same-night siren.
- **Missed pass:** in 2026 every repeat cycle over our reach skips one pass between late July and mid-August, so one interval is 24 days instead of 12.

## Back-test (to do with real data)

Score flagged cells against `ground_truth/events.csv`. An event counts as caught if its cell was red at least 12 days before the report date. Report the hit rate, false alarm rate and median lead time, even if the numbers are modest.
