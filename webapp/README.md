# NodiNajar web app

Next.js + MapLibre GL + deck.gl + Recharts (the blueprint's front-end stack). A static site: every page is
plain files, so it runs on Vercel, GitHub Pages, or from a laptop with no server.

Tabs: Overview, Live map, Bank stretches, Radar passes, Alerts, Embankments (next), Methods & data.

## Run it

```bash
cd webapp
npm install
npm run dev            # http://localhost:3000
npm run build          # static site in webapp/out/
```

## Refresh the data

The app reads `webapp/public/data/`, written from the real NISAR run:

```bash
python -m src.pipeline.build_demo --subsets cache/subsets/*.npz --buildings cache/buildings.csv
python -m src.pipeline.export_web
```

No number is computed in the browser except dates and counts. Risk levels, retreat, homes and
thresholds all come from `src/compute` (tested Python).

## Launch on Vercel (2 minutes)

Option A, from your terminal:

```bash
cd webapp
npx vercel --prod      # log in when asked, accept the defaults
```

Option B, from GitHub: push the repo, then in vercel.com choose **Add New → Project**, import
`NodiNajar`, set **Root Directory** to `webapp`, and deploy. Every push then redeploys.

## Maps

Basemaps need internet: Esri World Imagery (satellite), EOX Sentinel-2 cloudless 2025, Esri World Topographic, Street and Dark Gray Canvas (keyless; CARTO raster tiles now need an API key),
and Mapzen terrain tiles for hillshade and 3D. Offline, the radar, banks, stretches and homes still show on a
dark background. Google's photorealistic 3D tiles need a Google Maps Platform key (not set up yet).

## Live parts

- The header counts down to the next expected NISAR pass on track 69 (12-day repeat), from the current time.
- Expected passes stay labelled "expected" until a real granule is processed.
- `NEXT_PUBLIC_DATA_BASE` can point the app at another data folder or at the API's static data.
