# NodiNajar (নদীনজর) · River Watch

**Team AlphaMatrix · NASA Space Apps Challenge 2026 · Challenge: Dancing with the SARs**

NodiNajar uses NASA-ISRO NISAR L-band radar, which sees through monsoon cloud, to measure how far riverbanks move between passes. It marks 500 m cells where the bank is retreating toward homes and turns that into a Bangla voice and SMS alert. The proof site is the Jamuna River in Sirajganj, Bangladesh.

> **Data status:** NISAR products are **provisional** (validated at a limited set of sites). The demo currently ships with **synthetic test scenes** placed on the real track 69 pass dates. The interface says so in red until real NISAR scenes are loaded. Never present synthetic output as real.

## Run the demo (no internet needed)

Open `web/index.html` in Chrome or Firefox. That's it: the data is inlined in `web/demo_fixtures/demo_data.js`.

Drag the white handle to swipe between two radar passes. Click a red or amber cell to see its retreat chart and the Bangla alert. Open "Methods and data" for every processing step and the raw numbers.

## Setup for development

```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q                              # 21 tests, all should pass
```

## Load real NISAR data (target: before 12 November)

We use **NISAR track 69, frame 14**: 8 GCOV dates from 18 June to 22 September 2026, each covering 100% of the Jamuna box. Each file is about 7 GB, so we read only our box (about 2% of a frame) straight from NASA's servers. Details: [`docs/COVERAGE.md`](docs/COVERAGE.md).

```bash
# 0. Real preview images for video and slides (no login, about 2 minutes)
python tools/browse_previews.py

# 1. Earthdata login: urs.earthdata.nasa.gov > profile > Generate Token
export EARTHDATA_TOKEN="..."           # PowerShell: $env:EARTHDATA_TOKEN="..."

# 2. Look inside one real file without downloading it (metadata + a quick-look of our box)
python tools/inspect_h5.py "$(sed -n 2p docs/coverage/gcov_jamuna_track069_frame014.csv | cut -d, -f11)" --quicklook auto --db

# 3. Pull our box from 2 dates, then all 8 (small .npz files in cache/subsets/)
python tools/fetch_subset.py --csv docs/coverage/gcov_jamuna_track069_frame014.csv --limit 2
python tools/fetch_subset.py --csv docs/coverage/gcov_jamuna_track069_frame014.csv

# 4. Build the demo from the subsets (+ Open Buildings CSV for homes)
python -m src.pipeline.build_demo --subsets cache/subsets/*.npz --buildings cache/open_buildings.csv
```

Step 4 rewrites `web/demo_fixtures/`. The badge turns amber ("NISAR L-band GCOV - PROVISIONAL") and the footer credits NISAR.

If step 2 or 3 can't find a layer, send the step 2 output to whoever maintains `src/acquire/nisar.py`. The provisional product layout may differ from what we expect.

Homes: download Google Open Buildings for the AOI (CSV with `latitude`,`longitude` columns) or pass any GeoJSON of points or polygons.

To search coverage again: `tools/asf_pass_dates.py` (dates per repeat cycle) and `tools/check_coverage.py` (track, frame and size per product).

## Repository layout

```
.github/workflows/    runs the tests on every push
aoi/                  area-of-interest boxes for the Jamuna and the Teesta
cache/  outputs/      downloads and scratch output (gitignored)
docs/                 methods, NISAR coverage, AI use log, Video 1 plan
docs/coverage/        NISAR pass dates per reach (from the team's ASF search)
ground_truth/         dated, sourced erosion and embankment events for the back-test
src/acquire/          NISAR GCOV reader (crop to AOI, align grids)
src/compute/          the science: water mask, outer bank lines, retreat per segment, homes near bank, risk. No AI.
src/pipeline/         build_demo.py (scenes -> demo fixtures), synthetic.py (test scenes)
tests/                unit tests for src/compute, the reader and the tools
tools/                coverage search, box-only NISAR reader (fetch_subset), previews, HDF5 inspector, ground-truth checker
web/                  offline demo: MapLibre swipe map, risk cells, Bangla alert
```

## Team AlphaMatrix

| Member | Role |
| --- | --- |
| Kishan Modhu | Team lead, ML and back-test |
| Kazi Majedul Islam | Backend, Geospatial |
| Mahbub Al Hasan Akib | Radar lead (SAR) |
| Sajib Rahman | Full-stack and demo |
| Anika Rahman | Story, video and presentation |

How we work together: [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Rules we follow

- All science lives in `src/compute`, in tested functions. AI tools never compute a number shown to users.
- Every figure in the interface traces to `stats.json` (shown in the Methods drawer).
- Alerts use fixed templates filled from computed numbers.
- NISAR output is labelled provisional; synthetic output is labelled synthetic.
- AI use is logged in `docs/AI_USE.md` as we go.

## Data and credits

- NASA-ISRO NISAR L-band L2 GCOV, via NASA Alaska Satellite Facility DAAC (provisional)
- Sentinel-1 (ESA, Copernicus) via ASF, for history and fallback
- Google Open Buildings (homes), news reports listed in `ground_truth/events.csv`
- MapLibre GL JS 4.7.1 (BSD-3-Clause, `web/vendor/MAPLIBRE_LICENSE.txt`)

Licence: Apache-2.0 (see `LICENSE`).
