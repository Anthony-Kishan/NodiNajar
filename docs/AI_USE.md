# Use of AI in this project

Keep this file current as you work. The NASA project page asks for every AI tool, the prompts, the reasoning, and the data the AI worked on.

## Tools

| Tool | Used for | Who |
| --- | --- | --- |
| Claude (Anthropic), claude.ai | Challenge selection research, project blueprint, story draft, prep scripts, prototype scaffolding (reader, compute functions, pipeline, web demo), repo clean-up, Video 1 plan | Team lead |
| ElevenLabs (text-to-speech) | English narration voice in Videos 2 and 3, read from the team's script. Acknowledged in the video credits, YouTube descriptions and the video file metadata. | Team lead |

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

- **2026-10-13 (later):** Switched the web app basemaps to keyless Esri services after CARTO raster tiles began returning "API KEY REQUIRED" images, and added a before/after swipe compare on the Live map (`webapp/components/CompareMap.tsx`). No numbers changed; the compare view shows the existing radar and water images for two real passes.

- **2026-10-14:** Collected 2026 erosion reports from Bangladeshi newspapers into `ground_truth/events.csv` (GT007 split into GT007a to e, GT009 to GT018) and pinned some places from Google Maps and OpenStreetMap labels, marked "team to verify". Wrote `src/compute/forecast.py`, `src/compute/hindcast.py`, `src/pipeline/scorecard.py`, their tests, and the Track record tab. The numbers come from the tested code, not from the AI.

- **2026-11-13 (hackathon day 1):** Read the challenge statement and the Bangladesh Participants Guide with the team lead and wrote the day plan. Updated the README (data status, prior-work disclosure, data credits) and added NASA data layers to the web app as listed in the commit messages.

- **2026-11-13 (hackathon day 1, later):** Claude did the day's data tasks the team had split three ways. NASA POWER rainfall (`src/compute/rain.py`, tests, `src/pipeline/export_rain.py`, chart on Radar passes); NASA HLS optical days and the optical-and-radar swipe; the OPERA DSWx-HLS water check (`src/compute/validate.py`, tests, `tools/dswx_check.py`, Track record section); NASA tags on map layers; two more news reports (GT019, GT020); a phone-width check of every page. The data was read in the team lead's browser because NASA hosts were blocked from the build machine; the rainfall series was copied from that browser and checked against its total (1442.4 mm) and sample days.

- **2026-11-13 (hackathon day 1, afternoon):** Claude wrote the Why it moves tab (`webapp/app/why/page.tsx`) and `src/compute/drivers.py` with tests. The analysis found that the measured bank moves with the water level between passes, so part of the pass-to-pass change is the waterline, and the page says so. Driver statements cite Banglapedia, Shampa et al. 2025 (Frontiers in Earth Science), a 2020 UNB report on sand lifting and NASA JPL's NISAR science page, each opened before citing. The team lead ran the HV download and export.

- **2026-11-13 to 15:** Claude edited Video 2 (240 s, local judging) and cut Video 3 (30 s, global demo) from the team's ElevenLabs narration, the NISAR animation (NASA/JPL-Caltech), Pexels and team-supplied footage and automated screen recordings of a local build of the app. It also drafted the NASA project page text (summary, details, data lists, AI use, references). Every number in the videos and page comes from `src/compute` output.

## What the AI did not do

- No AI computes any number shown in the demo. All figures come from `src/compute`, which is deterministic and unit-tested.
- No AI writes alert messages at runtime. Alerts are fixed Bangla/English templates filled with computed numbers.
- Team decisions (challenge, proof site, thresholds after back-testing, story, video) are made by the team.

## What the team did

| Member | Role | Own work |
| --- | --- | --- |
| Kishan Modhu | Team lead, ML and back-test | Chose the challenge and the Jamuna study site with the team; ran the NISAR downloads and the HV export with his own Earthdata login; ran the pipeline and pushed every commit; tested the live site and reported the problems that were fixed (basemap key errors, the missing before/after slider); generated the narration in ElevenLabs; filled in and submitted the local form and this project page. |
| Kazi Majedul Islam | Backend, research, geospatial | Planned owner of the rain (GPM/POWER), HLS and news-pinning tasks and the data sources for the NASA page. |
| Mahbub Al Hasan Akib | Radar lead (SAR), video editing | Planned owner of the HV export and the OPERA DSWx-HLS check, and co-editor of Video 2. |
| Sajib Rahman | Full-stack, UI/UX | Planned owner of the optical and radar slider, the NASA data tags on every layer and the mobile check. |
| Raihana Ferdosh | Story, video and presentation | Planned owner of the video scripts, voice-over and subtitles. |

The team also supplied the two ASF search scripts that became `tools/asf_pass_dates.py`, the team photos, and the flood, school and river timelapse clips used in the videos.

To be clear about the split: on 13 November the data, app and video tasks planned for Kazi, Akib, Sajib and Raihana were carried out by Claude with the team lead, as logged above, so the team could submit on time. Members add their own review notes below.

## Prompts

Main prompts, summarised. Paste the full text of any prompt that produced code or text you kept.

1. "Help me pick a challenge from NASA Space Apps 2026... intermediate to advanced... strong story..."
2. "Create a detailed document: what we're building, problem, resources, knowledge needed, stack, story..."
3. "Start building our core project as planned in the document." (We chose a prep-only toolkit at that point.)
4. "Do all the necessary steps now..." (repository, prototype, Video 1 plan)
5. "Make sure that we have the proper file and folder structure for the project to push into GitHub..." (repo clean-up, coverage notes, Video 1 recording advice)
6. "Confirm which dates have GCOV files... download 2 scenes and look inside one" (coverage check, box-only reading, previews)
7. "Let's start creating the Video 1 as planned in the VIDEO1_PLAN.md file. Use the /ignis-demo-video-method skill..." (Video 1 production)
