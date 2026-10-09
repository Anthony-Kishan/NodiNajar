# Video 1: 240-second prescreening video

**Status (10 October 2026): not submitted.** The guide's deadline was 1 October 2026, 11:59 PM.

**Hard limit: 240 seconds.** Anything longer gets cut off. Aim for 3:50.
Upload to YouTube (Unlisted or Public) and paste the link in the Google Form.

## Step 0: ask the Local Lead today

Video 1 is late, so the first job is a message, not a recording. Send this to your Local Lead or the Bangladesh Space Apps Slack:

> Team AlphaMatrix (Dancing with the SARs) has not submitted Video 1 yet. Can we still submit it, and what is the last date? Also: we are building data caches and a prototype in a public repo before the event. Is that allowed?

Their answer sets the recording date. Keep it in writing.

## When to record

Don't wait for the finished prototype. Video 1 is judged as a concept, and the working demo belongs in Video 2 (Day 1, 18:30). Record as soon as you have these three things. That takes about 3 days of work:

1. **One real NISAR image of the Jamuna.** Download 1 or 2 GCOV files and run `tools/inspect_h5.py --quicklook auto --db`. A real radar picture proves you've touched the data.
2. **The coverage fact.** From `docs/COVERAGE.md`: NISAR passed over the reach on 31 dates from 18 June to 29 September 2026.
3. **The prototype screen recording.** If real scenes are loaded by then, use them with the PROVISIONAL badge. If not, use the synthetic demo with the red badge visible and say "test data".

If the Local Lead gives you less than 3 days, skip item 1 and use the synthetic demo plus the coverage fact.

## Must include (Video 1 requirements)

- [ ] Team name: Team AlphaMatrix
- [ ] Every team member by name, on screen
- [ ] The problem, and the challenge named: "Dancing with the SARs"
- [ ] The solution approach (concept is enough at this stage)
- [ ] Credits for every third-party image, clip, music track, template and AI tool

## Rules to respect

- No recognisable face, name or voice of anyone under 18. Don't use news photos showing children. "Mitu" in the story is illustrative only: no photo, no real child.
- Any prototype footage that uses synthetic data must show the red "SYNTHETIC TEST DATA" badge. Say "test data" in the narration.
- Any NISAR footage must say "provisional".
- Don't show or imply a NISAR pass between 26 July and 12 August 2026. There wasn't one over our reach.
- Add English subtitles.
- Get written permission for any interview, and credit the person if they agree.

## Shot list and narration (about 310 words)

At 130 to 140 words a minute, the narration takes about 2:20 of the 3:55. The rest is the silent opening, title cards, the prototype running without talk, and the credits. If you have a 15 to 20 second interview clip with a field worker (with consent), put it after the Jotpara line.

| Time | Visual | Narration |
| --- | --- | --- |
| 0:00–0:12 | Black screen, sound of a riverbank collapsing. Text: "18 August 2026. Bhorer Pakhi Char, Gaibandha." Then: "The river took the only school." | (silence, then) "On the eighteenth of August, the Teesta River took the only school on Bhorer Pakhi Char." |
| 0:12–0:30 | Team card: logo, "Team AlphaMatrix", each member's name and role | "We are Team AlphaMatrix from Bangladesh: [name], [name], [name], [name], [name] and [name]." |
| 0:30–1:00 | Map of the Jamuna in Sirajganj with pins for the 2026 events in `ground_truth/events.csv`; news headlines with credits | "This is not one bad day. Riverbank erosion displaces around one hundred thousand people in Bangladesh every year. This July, the Jamuna took homes and part of a primary school in Jotpara, Chauhali, in under an hour. Families get a list of victims after the land is gone. They get no warning before." |
| 1:00–1:12 | Title card: NASA Space Apps 2026 · "Dancing with the SARs" | "Our challenge is Dancing with the SARs: using radar from space to see how Earth's surface is changing." |
| 1:12–1:40 | Split screen: NASA Worldview true-colour image of Bangladesh on a July 2026 date (all cloud) beside the real NISAR quick-look of the Jamuna, labelled "NISAR L-band · provisional" | "Erosion peaks in the monsoon. That is exactly when clouds blind normal satellites. NASA and ISRO's new NISAR satellite uses radar. It sees through cloud and rain. Between June and September it passed over our stretch of the Jamuna on thirty-one dates." |
| 1:40–2:50 | Screen recording of the prototype: swipe from June to September, click a red cell, the retreat chart climbs, the Bangla alert appears and plays. Badge visible. | "NodiNajar, meaning River Watch, turns each radar pass into a map. Water is dark, land is bright. We compare passes, measure how far the bank moved in every five-hundred-metre cell, and count the homes now close to the edge. What you see here runs on test data; real NISAR scenes go in next. When a cell turns red, families nearby get a Bangla voice call and SMS, and local officials see which banks to protect first." |
| 2:50–3:15 | The architecture diagram from the blueprint, simplified to four boxes; the embankment layer as a concept | "A second engine uses radar interferometry to spot flood embankments that are slowly sinking, before they breach. All calculations run in tested code, not AI, and every number links to its source data." |
| 3:15–3:35 | Back-test plan graphic: 2026 events vs flagged cells | "We will test it honestly against this year's real erosion events, and publish how many we caught and how early. This is a warning weeks ahead, not a siren." |
| 3:35–3:45 | The same method switching to another river outline | "The same code works on any river NISAR sees: the Brahmaputra, the Mekong, the Indus." |
| 3:45–3:55 | Closing line, then a credits card | "The river gives no warning. Now the sky can." |

## Assets to prepare

| Asset | How | Owner |
| --- | --- | --- |
| Team card with all names and roles | Figma or Canva, 1920×1080 | Story lead |
| Event map with 2026 pins | QGIS or the web demo's base, from `ground_truth/events.csv` | Geospatial |
| Cloud vs radar split screen | NASA Worldview screenshot of a July 2026 date + `tools/inspect_h5.py` quick-look of a real NISAR scene | Radar lead |
| Prototype screen recording | Open `web/index.html`, browser full screen, record at 1080p, swipe slowly, click the top red cell, press Play voice | Full-stack |
| Bangla voice for the alert | Record a team member reading the alert (adults only), or a named TTS tool credited in AI_USE.md | Alerts lead |
| Headlines | Screenshots of the BSS, Daily Ittefaq and New Nation reports, credited on screen | Backend |
| Music/sound | Royalty-free (for example the YouTube Audio Library), credited | Story lead |
| Subtitles | YouTube auto-captions, then correct by hand; also burn them into the video | Story lead |

## How to record it

1. **Narration first.** Record the voice before any editing, then cut the pictures to fit the voice. One clear speaker for the whole script sounds better than six.
2. **Sound.** A quiet room with soft furnishings, a phone or USB mic about 15 cm from the mouth. Record in Audacity, then apply Noise Reduction and Normalize to −1 dB. Do three takes of each line and keep the best.
3. **Screen.** OBS Studio at 1920×1080, 30 fps. Close other tabs and hide the bookmarks bar. Set the browser zoom so the panel text reads at phone size. Move the mouse slowly and pause one second on each click.
4. **Edit.** Kdenlive or DaVinci Resolve (both free on Ubuntu), or CapCut. Keep on-screen text large: at least 48 px at 1080p. Hold every text card long enough to read it twice.
5. **Music.** Keep it 20 to 25 dB under the voice, or drop it during the narration.
6. **Export.** H.264 MP4, 1080p, 30 fps. Check the length in the player: 3:59 is the maximum.
7. **Upload.** YouTube Unlisted, add the corrected English SRT, then open the link in a private window to make sure strangers can watch it.

## Before you upload

- [ ] Length is 4:00 or less
- [ ] Every member named
- [ ] Challenge named
- [ ] Synthetic badge visible in any prototype shot; narration says "test data"
- [ ] Any NISAR image labelled provisional
- [ ] No under-18 faces, names or voices
- [ ] Credits card lists every source and AI tool
- [ ] English subtitles
- [ ] YouTube visibility "Unlisted" or "Public", link tested in a private window
