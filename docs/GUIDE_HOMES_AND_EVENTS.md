# Team guide: homes data and erosion events

Two jobs that unlock the red alerts and the back-test. Each can be done by one person in an afternoon.

**Before you start:** the AOI box was extended on 10 October to 24.00–24.72° N, 89.60–89.92° E. Chauhali upazila lies at 24°01′–24°17′ N ([Banglapedia](https://en.banglapedia.org/index.php/Chauhali_Upazila)) and most of it was outside the old box. If you fetched NISAR subsets before this change, delete them and fetch again:

```bash
rm -rf cache/subsets
python tools/fetch_subset.py --csv docs/coverage/gcov_jamuna_track069_frame014.csv
```

---

## Job 1: homes data (one person, about 30 minutes)

Without buildings the demo can only show amber cells. Red needs at least one home within 200 m of the new bank.

We use **Overture Maps**, which combines Google Open Buildings, Microsoft building footprints and OpenStreetMap in one download. No account needed.

1. Activate the project environment:
   ```bash
   cd ~/Documents/"NASA Space App Challenge 2026"/nodinajar
   source .venv/bin/activate
   pip install -r requirements.txt overturemaps
   ```
2. Download building footprints for the box (a few hundred MB; takes 5–15 minutes):
   ```bash
   overturemaps download --bbox=89.60,24.00,89.92,24.72 -f geoparquet --type=building -o cache/buildings.parquet
   ```
3. Convert to one point per building:
   ```bash
   python tools/buildings_to_csv.py cache/buildings.parquet cache/buildings.csv
   ```
   It prints how many buildings came from each source. Expect tens of thousands or more.
4. Rebuild the demo with homes:
   ```bash
   python -m src.pipeline.build_demo --subsets cache/subsets/*.npz --buildings cache/buildings.csv
   ```
5. Open `web/index.html`. Yellow dots are homes near a moving bank. Red cells should appear where the bank moved 100 m or more next to homes.
6. Spot-check 3 places: pick a yellow dot, copy its coordinates, and look at it in Google Maps satellite view. Is there really a building? Note the result in the PR description.
7. Add this line to the credits in `README.md` (Data and credits): `Buildings: Overture Maps Foundation (ODbL), including OpenStreetMap contributors, Google Open Buildings and Microsoft building footprints.`

Do not commit `cache/buildings.*`; it is gitignored. Commit only the README change.

---

## Job 2: event coordinates and more events (two or three people, 2–3 hours)

The back-test checks whether NodiNajar flagged a stretch of bank **before** the news reported erosion there. It needs:
- at least **8** erosion events on the Jamuna in Sirajganj, between 17 June and 30 September 2026;
- each with a **date** and a **location precise to the village**, inside the box.

Today the table has 2 such events (GT007, GT008) and neither has coordinates.

### Part A: add coordinates to existing rows

For each row in `ground_truth/events.csv`:

1. Open the `source_url` and read the article yourself. Note the village, union and upazila it names.
2. Find the village in Google Maps (search "Jotpara, Chauhali, Sirajganj"). If Google Maps doesn't know it, try OpenStreetMap (openstreetmap.org) or the union's page on `sirajganj.gov.bd`.
3. Right-click on the village label (or the riverbank next to it) and click the coordinates at the top of the menu. That copies them, e.g. `24.1832, 89.7741`.
4. Fill in four columns:

   | Column | What to write | Example |
   | --- | --- | --- |
   | `lat` | first number | `24.1832` |
   | `lon` | second number | `89.7741` |
   | `location_precision` | `point` if the article names an exact place (a school, a market), `village` if it names a village, `union` or `upazila` if that's all you have | `village` |
   | `location_source` | how you found it | `Google Maps village label` |

5. Put your name in `verified_by`.
6. If an article names several villages (like GT007), split it into one row per village with IDs GT007a, GT007b, and so on.

Rows with only `union` or `upazila` precision stay in the table but don't count for the back-test, because a union is too big to match a 500 m bank segment.

### Part B: find at least 6 more events

Search the news for **17 June to 30 September 2026**. Use Google with **Tools → Any time → Custom range**, or Google News.

Search terms that work (try each):
- Bangla: `যমুনা নদী ভাঙন কাজিপুর`, `যমুনা ভাঙন চৌহালী`, `সিরাজগঞ্জ সদর নদী ভাঙন`, `বেলকুচি যমুনা ভাঙন`, `যমুনার ভাঙনে বসতভিটা`, `ভাঙনে বিলীন সিরাজগঞ্জ`
- English: `Jamuna erosion Sirajganj`, `Kazipur erosion`, `Chauhali erosion`, `Belkuchi river erosion`

Good sources: Prothom Alo, Kaler Kantho, Samakal, Jugantor, Ittefaq, Daily Star, bdnews24, BSS, Dhaka Tribune, New Age, Somoy TV, Jamuna TV, and local Sirajganj news portals.

For each event, add a row:

| Column | Rule |
| --- | --- |
| `event_id` | next number, e.g. `GT009` |
| `event_type` | `bank_erosion` (or `embankment_breach`) |
| `river`, `district` | `Jamuna`, `Sirajganj` |
| `upazila`, `union`, `place` | as the article says |
| `lat`, `lon`, `location_precision`, `location_source` | Part A steps 2–4 |
| `event_date` | the day the erosion happened, `YYYY-MM-DD` |
| `date_precision` | `exact` if the article gives the day; otherwise e.g. `approx (last Saturday)` |
| `report_date` | the article's publication date, `YYYY-MM-DD` |
| `homes_lost`, `other_losses` | numbers and things the article states, nothing more |
| `in_main_reach` | `yes` if the location is inside the box |
| `source_name`, `source_url` | outlet and link |
| `verified_by` | your name |

Rules:
- Only what the article states. Don't estimate dates or numbers.
- One event per place and date. If two outlets report the same event, keep one row and add the second link in `notes`.
- Prefer events after 18 June. An event on 18–30 June can't be caught in advance because there is no earlier pass on our track.
- No photos of children, no names of minors, in the table or anywhere else.

### Check your work

After every few rows:

```bash
python tools/check_events.py
```

It reports format errors, coordinates outside the box, rows still missing coordinates, and how many back-test events are ready. Aim for **"back-test events with village-level coordinates inside the box: 8"** or more.

Then commit under your own name:

```bash
git checkout -b <your-name>/events
git add ground_truth/events.csv
git commit -m "Add N Jamuna erosion events with coordinates"
git push -u origin <your-name>/events
```
