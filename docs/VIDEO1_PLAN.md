# Video 1: 240-second prescreening video

**Status (10 October 2026): not submitted.** The guide's deadline was 1 October 2026, 11:59 PM. Ask the Local Lead today whether a late upload is accepted, and send it the moment it is ready.

**Hard limit: 240 seconds.** Aim for 3:50. English subtitles. Upload to YouTube (Unlisted) and paste the link in the Google Form.

## The 5-hour schedule

| Time | Who | Task |
| --- | --- | --- |
| 0:00–0:20 | Team lead | Rebuild the demo (`python -m src.pipeline.build_demo --subsets cache/subsets/*.npz --buildings cache/buildings.csv`, about 3 minutes), open `web/index.html` full screen, check every scene below works |
| 0:00–1:00 | Story lead | Record the narration (script below): quiet room, phone 15 cm from mouth, 3 takes per paragraph |
| 0:00–1:00 | Video editor | Make the title card, team card, challenge card and credits card (1920×1080, Hind Siliguri or any clean sans) |
| 0:20–1:20 | Full-stack | Screen-record the demo with OBS at 1920×1080, 30 fps, one clip per demo scene (list below), browser in full screen (F11) |
| 0:30–1:00 | Backend | Screenshot 2 news headlines (BSS Gaibandha, Daily Ittefaq Sirajganj) and a NASA Worldview cloud image for July 2026 over Bangladesh |
| 1:20–3:20 | Video editor | Cut pictures to the narration in DaVinci Resolve, Kdenlive or CapCut |
| 3:20–4:00 | Story lead | Subtitles: YouTube auto-captions or CapCut auto-captions, then fix every line by hand. Burn them in too |
| 4:00–4:30 | Everyone | Watch it once together. Check the list at the bottom |
| 4:30–5:00 | Team lead | Export, upload, test the link in a private window, submit the form |

## Demo scenes to record (each 10–25 seconds)

| # | What to do on screen | Used at |
| --- | --- | --- |
| A | Page loads on the full Jamuna box. Hold 3 seconds on the left-hand summary sentence | 1:50 |
| B | Press play. The timeline steps through all 8 passes; the river swells to 967 km² on 24 July and shrinks again | 2:05 |
| C | Drag the white swipe handle slowly left and right across the full box | 2:20 |
| D | Click row 4 in "Where to act first" (west bank, 24.306° N, 67 homes). The map flies in. Swipe slowly across the red strip | 2:30 |
| E | Point at the chart on the right: the bank moving 20, 40, 80 … 170 m into the land | 2:45 |
| F | Click English then বাংলা on the alert. Press Play voice if a Bangla voice is installed | 2:55 |
| G | Open "Methods and data", scroll the table of passes and thresholds | 3:10 |

Move the mouse slowly and pause 1 second before each click. The PROVISIONAL badge must be visible in every shot.

## Narration (about 390 words, about 3:00 of speech)

| Time | Picture | Narration |
| --- | --- | --- |
| 0:00–0:12 | Black. Sound of a riverbank falling. Text: "18 August 2026. Bhorer Pakhi Char, Gaibandha." | "On the eighteenth of August, the Teesta River took the only school on Bhorer Pakhi Char." |
| 0:12–0:28 | Team card: every member, name and role | "We are Team AlphaMatrix from Bangladesh: Kishan Modhu, Kazi Majedul Islam, Mahbub Al Hasan Akib, Sajib Rahman and Raihana Ferdosh." |
| 0:28–0:55 | News headlines (credited), then the Jamuna at Sirajganj | "Every monsoon, riverbank erosion forces around a hundred thousand people in Bangladesh from their homes. This July the Jamuna took homes and part of a primary school in Chauhali, in under an hour. Families get a list of victims after the land is gone. They get no warning before." |
| 0:55–1:08 | Title card: NASA Space Apps 2026, "Dancing with the SARs" | "Our challenge is Dancing with the SARs: using radar from space to see how Earth's surface is changing." |
| 1:08–1:35 | Worldview July image (all cloud), cut to the 10 m NISAR quick-look of the Jamuna, labelled provisional | "Erosion peaks in the monsoon, exactly when clouds blind camera satellites. NASA and ISRO's new NISAR satellite uses radar, which sees through cloud and rain. Its data is provisional, and only public since July." |
| 1:35–1:50 | Scene A | "NodiNajar, River Watch, reads eight NISAR passes over eighty kilometres of the Jamuna, from June to September 2026." |
| 1:50–2:20 | Scenes B and C | "Water is dark, land is bright. You can watch the monsoon arrive: the river grows to more than twice its June size on the twenty-fourth of July, then falls back. That flooding is not erosion, so we track only the outer banks, where people live, and only movement that stays." |
| 2:20–2:55 | Scenes D and E | "Along thirty-eight stretches, the outer bank moved into the land. Five are next to homes. Here, on the west bank, the river moved a hundred and sixty metres in three months, step by step, and sixty-seven homes now stand within two hundred metres of the edge." |
| 2:55–3:10 | Scene F | "When a stretch turns red, families nearby get this alert in Bangla, by SMS and voice call, and officials get this list of where to act first." |
| 3:10–3:25 | Scene G | "Every number comes from tested code, not AI, and every step is open: which passes, which thresholds, and where the radar couldn't tell, we say so." |
| 3:25–3:40 | Architecture: four boxes (NISAR, erosion engine, embankment engine, alerts) | "Next, we test it against this year's reported erosion, and add a second engine that uses radar interferometry to find flood embankments that are slowly sinking." |
| 3:40–3:50 | Closing card | "The river gives no warning. Now the sky can." |
| 3:50–4:00 | Credits card | (music only) |

If anyone's name in the team card is different, fix the narration line to match the README.

## Rules to respect

- No recognisable face, name or voice of anyone under 18. No news photos showing children. The school story uses the place and date only.
- Say "provisional" when NISAR appears. The badge stays visible.
- Do not imply a pass between 24 July and 17 August (there was none).
- The back-test is not done yet: say "next, we test", never "we caught".
- Credit everything on the final card: NASA-ISRO NISAR via NASA ASF DAAC; NASA Worldview; Overture Maps (OpenStreetMap contributors, Google Open Buildings, Microsoft); MapLibre; Hind Siliguri font; news outlets used; music; AI tools used (Claude, plus any caption or voice tool).

## Before you upload

- [ ] 4:00 or less
- [ ] Every member named, on screen and in the voice-over
- [ ] Challenge named: Dancing with the SARs
- [ ] PROVISIONAL visible whenever NISAR data is on screen
- [ ] No under-18 faces, names or voices
- [ ] English subtitles, checked by hand
- [ ] Credits card complete
- [ ] Link works in a private window
