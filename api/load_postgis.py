"""
Load the exported results into PostgreSQL + PostGIS (blueprint database).

    docker compose up -d db
    DATABASE_URL=postgresql://nodinajar:nodinajar@localhost:5432/nodinajar python -m api.load_postgis

Tables: passes, segments (polygon + centre), homes (point), banklines (line per pass).
Martin then serves segments/homes/banklines as vector tiles straight from these tables.
"""
from __future__ import annotations

import json
import os

import psycopg

from api.main import DATA

DDL = """
CREATE EXTENSION IF NOT EXISTS postgis;
DROP TABLE IF EXISTS passes, segments, homes, banklines;
CREATE TABLE passes (date date PRIMARY KEY, granule text, pol text, threshold_db real, threshold_from text, water_km2 real);
CREATE TABLE segments (id text PRIMARY KEY, rank int, level text, side text, retreat_m real, lost_ha real, homes_near int,
                       history_m real[], geom geometry(Polygon, 4326), centre geometry(Point, 4326));
CREATE TABLE homes (id serial PRIMARY KEY, geom geometry(Point, 4326));
CREATE TABLE banklines (id serial PRIMARY KEY, pass int, date date, side text, geom geometry(LineString, 4326));
"""


def main():
    url = os.environ["DATABASE_URL"]
    m = json.loads((DATA / "manifest.json").read_text())
    segs = json.loads((DATA / m["files"]["segments"]).read_text())["features"]
    homes = json.loads((DATA / m["files"]["homes"]).read_text())["features"]
    lines = json.loads((DATA / m["files"]["banklines"]).read_text())["features"] if m["files"].get("banklines") else []
    with psycopg.connect(url) as con, con.cursor() as cur:
        cur.execute(DDL)
        for p in m["passes"]:
            cur.execute("INSERT INTO passes VALUES (%s,%s,%s,%s,%s,%s)",
                        (p["date"], p["granule"], p["pol"], p["threshold_db"], p["threshold_from"], p["water_km2"]))
        for f in segs:
            q = f["properties"]
            cur.execute("INSERT INTO segments VALUES (%s,%s,%s,%s,%s,%s,%s,%s, ST_SetSRID(ST_GeomFromGeoJSON(%s),4326), "
                        "ST_SetSRID(ST_MakePoint(%s,%s),4326))",
                        (q["id"], q["rank"], q["level"], q["side"], q["retreat_m"], q["lost_ha"], q["homes_near"], q["history_m"],
                         json.dumps(f["geometry"]), q["centre"][0], q["centre"][1]))
        cur.executemany("INSERT INTO homes (geom) VALUES (ST_SetSRID(ST_MakePoint(%s,%s),4326))",
                        [tuple(h["geometry"]["coordinates"]) for h in homes])
        cur.executemany("INSERT INTO banklines (pass, date, side, geom) VALUES (%s,%s,%s, ST_SetSRID(ST_GeomFromGeoJSON(%s),4326))",
                        [(f["properties"]["pass"], f["properties"]["date"], f["properties"]["side"], json.dumps(f["geometry"])) for f in lines])
        cur.execute("CREATE INDEX ON segments USING gist (geom); CREATE INDEX ON homes USING gist (geom); CREATE INDEX ON banklines USING gist (geom);")
    print(f"loaded {len(m['passes'])} passes, {len(segs)} segments, {len(homes)} homes, {len(lines)} bank lines")


if __name__ == "__main__":
    main()
