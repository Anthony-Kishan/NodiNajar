# Use of AI in this project

Keep this file current as you work. The NASA project page asks for every AI tool, the prompts, the reasoning, and the data the AI worked on.

## Tools

| Tool | Used for | Who |
| --- | --- | --- |
| Claude (Anthropic), claude.ai | Challenge selection research, project blueprint, story draft, prep scripts, prototype scaffolding (reader, compute functions, pipeline, web demo), repo clean-up, Video 1 plan | Team lead |

Add a row for every other tool (ChatGPT, Copilot, image or voice generators, translation tools).

## What the AI did

- **2026-10-07:** Compared the 2026 challenge summaries and recommended "Dancing with the SARs" with a Bangladesh riverbank erosion focus. Researched erosion figures and NISAR data availability, with sources cited in the blueprint.
- **2026-10-08:** Drafted the project blueprint (story, architecture, stack, plan). The story uses a composite family; real events come from cited news reports.
- **2026-10-09:** Wrote the prep tools (`tools/check_coverage.py`, `tools/inspect_h5.py`, `tools/check_events.py`) and seeded `ground_truth/events.csv` from cited news reports.
- **2026-10-10:** Scaffolded this repository: `src/compute` functions with unit tests, the NISAR GCOV reader, the demo pipeline, the synthetic test-scene generator and the web demo.
- **2026-10-10:** Prepared the repo for GitHub: `.gitignore`, `.gitattributes`, CI workflow, `CONTRIBUTING.md`. Merged the team's two ASF search scripts into `tools/asf_pass_dates.py` with a 12-day cycle grouping and tests. Wrote `docs/COVERAGE.md` from the team's search results. Moved the synthetic scenes onto real NISAR pass dates and set the AOI boxes to the boxes the team searched with. Updated the Video 1 plan.
- **2026-10-10:** Fixed CI (`pytest.ini`). Queried the public ASF search API for NISAR GCOV over the Jamuna box (36 products) and chose track 69 frame 14 (8 dates, 100% coverage). Wrote `tools/fetch_subset.py` and remote reading in `src/acquire/nisar.py` so only our box is read from each 7 GB file, `tools/browse_previews.py` for public preview images, and tests for both. Georeferencing of the previews was checked by eye against the Jamuna Bridge on two dates.
- **2026-10-10:** Tested the pipeline on the first two real NISAR dates (18 and 30 June). Found that Otsu thresholding over-detects water and that counting every land-to-water pixel reports flooded sandbars as erosion (8,218 ha in 12 days). Added `valley_threshold`, `near_river` and a new outer-bank engine (`src/compute/bankline.py`) with tests, made it the default, and sped up the demo build for 10 m data. The team should review the thresholds (200 m minimum channel width, 400 m jump limit, 150 m spread) on all 8 dates.
- **2026-10-10:** Found that Chauhali (24°01′–24°17′ N, Banglapedia) was mostly outside the AOI box and extended the box south and north, checked against all 8 track 69 footprints. Added coordinate columns and box checks to the events table and `tools/check_events.py`, `tools/buildings_to_csv.py` for Overture Maps buildings, and `docs/GUIDE_HOMES_AND_EVENTS.md`. Event coordinates and new events are to be found and verified by team members, not by AI.
- **2026-10-10:** On the full 8-date run, found two dates with impossible water thresholds and added the season-median fallback (`season_thresholds`) with a test. Redesigned the web demo (`web/index.html`, `style.css`, `app.js`): season summary built from the data, ranked list of bank stretches, selected-stretch chart, Bangla/English alert, monsoon pass timeline with play, methods drawer. Bundled the Hind Siliguri font (SIL OFL) for offline use. Updated the Video 1 plan with real numbers. All numbers on screen still come from `stats.json`.
- **2026-10-10:** Produced Video 1 (`Video1/` folder next to this repo): wrote the script in the IGNIS demo-video style with the team's names and roles, checked pace (2.0 words/s overall, no segment over 2.8), rendered motion cards from real NISAR stills and the team's photos, screen-recorded the real app with an automated browser, synthesized the music bed, built the 4-minute and 30-second cuts with a placeholder voice, and wrote the ElevenLabs narration files and captions. Checked the Bhorer Pakhi school story against UNB (19 Aug 2026) and corrected the wording. Amena is a composite character and the video says so. The final narration is an ElevenLabs AI voice.

- **2026-10-13:** Built the web app on the blueprint stack (`webapp/`: Next.js, MapLibre GL, deck.gl, Recharts) with satellite and terrain basemaps, a pass player, 3D retreat columns, tabs for stretches, passes, alerts, embankments (empty until GUNW is processed) and methods. Added `bank_polylines` (tested) and per-pass water masks and bank lines to the pipeline, `src/pipeline/export_web.py` (tested), fixed alert templates in Python (`src/alerts/templates.py`, tested), and a FastAPI + PostGIS + Martin + TiTiler scaffold (`api/`, `docker-compose.yml`). The web app shows only numbers from the pipeline; the next-pass countdown is a 12-day schedule and is labelled as expected, not observed.

## What the AI did not do

- No AI computes any number shown in the demo. All figures come from `src/compute`, which is deterministic and unit-tested.
- No AI writes alert messages at runtime. Alerts are fixed Bangla/English templates filled with computed numbers.
- Team decisions (challenge, proof site, thresholds after back-testing, story, video) are made by the team.

TODO for the team: describe here what each member reviewed, changed or rewrote. Judges look for where your own work went.

## Prompts

Main prompts, summarised. Paste the full text of any prompt that produced code or text you kept.

1. "Help me pick a challenge from NASA Space Apps 2026... intermediate to advanced... strong story..."
2. "Create a detailed document: what we're building, problem, resources, knowledge needed, stack, story..."
3. "Start building our core project as planned in the document." (We chose a prep-only toolkit at that point.)
4. "Do all the necessary steps now..." (repository, prototype, Video 1 plan)
5. "Make sure that we have the proper file and folder structure for the project to push into GitHub..." (repo clean-up, coverage notes, Video 1 recording advice)
6. "Confirm which dates have GCOV files... download 2 scenes and look inside one" (coverage check, box-only reading, previews)
7. "Let's start creating the Video 1 as planned in the VIDEO1_PLAN.md file. Use the /ignis-demo-video-method skill..." (Video 1 production)
