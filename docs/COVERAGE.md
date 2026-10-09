# NISAR coverage over our reaches

Searched by the team on 9 October 2026 with ASF (`asf_search`), NISAR L2 GCOV + GUNW, production products, 17 June to 30 September 2026. Raw dates are in `docs/coverage/`. Re-run with `tools/asf_pass_dates.py`.

**Result: NISAR is enough. We do not need the Sentinel-1 fallback for the main reach.** Every repeat cycle over the Jamuna has 7 or 8 passes, and a time series needs about 6.

## Jamuna at Sirajganj (main proof site)

31 acquisition dates, 18 June to 29 September. They fall into 4 repeat cycles of 12 days, which most likely means 4 different tracks (ascending and descending, neighbouring orbits).

| Cycle (named by first date) | Dates | Passes | Also covers the Teesta? |
| --- | --- | --- | --- |
| 18 Jun cycle | 18 Jun, 30 Jun, 12 Jul, 24 Jul, 17 Aug, 29 Aug, 10 Sep, 22 Sep | 8 | Yes |
| 20 Jun cycle | 20 Jun, 2 Jul, 14 Jul, 26 Jul, 19 Aug, 31 Aug, 12 Sep, 24 Sep | 8 | No |
| 25 Jun cycle | 25 Jun, 7 Jul, 19 Jul, 12 Aug, 24 Aug, 5 Sep, 17 Sep, 29 Sep | 8 | Yes |
| 27 Jun cycle | 27 Jun, 9 Jul, 21 Jul, 14 Aug, 26 Aug, 7 Sep, 19 Sep | 7 | Yes |

## Teesta at Sundarganj (story site)

23 dates in 3 cycles: the 18 Jun, 25 Jun and 27 Jun cycles above. The 20 Jun cycle does not reach the Teesta box.

## What this means for the build

1. **One missed pass per cycle, all in the same window.** No cycle has a pass between 26 July and 12 August. Each track loses one pass there, leaving a gap of 24 days instead of 12. The back-test and the video must not imply a pass in that window.
2. **Pick a cycle that also covers the Teesta.** The 18 Jun or 25 Jun cycle gives 8 passes on both rivers. That makes the "same code, another river" demo simpler.
3. **Dates are not yet split by product.** These counts merge GCOV and GUNW. Run `tools/check_coverage.py --products GCOV` before downloading to confirm every date has a GCOV file, and to get the real track and frame numbers.
4. **Back-test timing.** Jotpara (GT008) happened on 25 July and was reported on 29 July. A catch needs a red flag by 17 July. The 18 Jun cycle gives 3 passes before that (18 Jun, 30 Jun, 12 Jul), enough for the two-date rule.

## The synthetic demo

The synthetic test scenes in `src/pipeline/synthetic.py` use the real dates of the 18 Jun cycle (8 passes), the cycle we plan to use. When real scenes are loaded, the demo takes its dates from the files.
