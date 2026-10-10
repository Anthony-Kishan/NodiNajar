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
