"use client";
import Link from "next/link";
import { useMemo, useState } from "react";
import { ErrorBox, Kpi, Loading, SegmentRow } from "@/components/Bits";
import { LevelBars, RiverProfile, WaterChart } from "@/components/Charts";
import { RiverMap } from "@/components/MapClient";
import { DEFAULT_LAYERS } from "@/lib/mapLayers";
import { Footer } from "@/components/Shell";
import { useNow, useRiver } from "@/lib/data";
import { fmtDate, nf } from "@/lib/format";
import { expectedPasses, gaps } from "@/lib/schedule";

export default function Overview() {
  const { data, error } = useRiver();
  const now = useNow(60_000);
  const [sel, setSel] = useState<string | null>(null);
  const segs = useMemo(() => data?.segments.features.map((f) => f.properties) ?? [], [data]);
  if (error) return <ErrorBox error={error} />;
  if (!data) return <Loading />;
  const m = data.manifest, t = m.totals, P = m.passes;
  const first = P[0], last = P[P.length - 1];
  const peak = P.reduce((a, b) => (b.water_km2 > a.water_km2 ? b : a));
  const sched = expectedPasses(m, now, 2);
  const measured = m.segments ? m.segments.ok + m.segments.jump + m.segments.gap : 0;
  const top = segs.slice(0, 6);
  const homesRed = segs.filter((s) => s.level === "red").reduce((a, s) => a + s.homes_near, 0);

  return (
    <>
      <main className="page">
        <div className="page-head">
          <div>
            <h2>The Jamuna moved into the land along {t.cells_red + t.cells_amber} stretches this monsoon</h2>
            <p>
              Eight NISAR L-band radar passes, {fmtDate(first.date)} to {fmtDate(last.date, true)}, seen through cloud.
              {" "}{t.cells_red} stretches are next to homes and need action first. Every number below is measured, not guessed.
            </p>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <Link className="btn primary" href="/map/">Open the live map</Link>
            <Link className="btn" href="/alerts/">See the alerts</Link>
          </div>
        </div>

        <section className="grid g-4" aria-label="Season totals">
          <Kpi label="High-risk stretches" value={t.cells_red} unit={`of ${t.cells_red + t.cells_amber}`} accent="var(--erosion)"
            foot={<>Moved ≥ 100 m with homes within 200 m · {nf(homesRed)} homes</>} />
          <Kpi label="Land the river took" value={nf(t.land_lost_ha, 1)} unit="ha" accent="var(--watch)" foot={<>Outer banks only, confirmed on the last two passes</>} />
          <Kpi label="Largest bank movement" value={t.max_retreat_m} unit="m" accent="var(--monsoon)" foot={<>Over {m.period_days} days, one 500 m stretch</>} />
          <Kpi label="Homes near the new bank" value={nf(t.homes_near_new_bank)} accent="var(--home)" foot={<>Overture Maps buildings within 200 m</>} />
        </section>

        <section className="grid g-3" style={{ marginTop: 16 }}>
          <div className="card span-2" style={{ padding: 0, overflow: "hidden", display: "flex", flexDirection: "column" }}>
            <div style={{ padding: "16px 18px 10px" }} className="card-head">
              <div><h3>Where the bank moved</h3><p className="sub" style={{ margin: 0 }}>Satellite view with the radar change on top. Click a stretch.</p></div>
              <Link className="btn sm" href={sel ? `/map/?seg=${sel}` : "/map/"}>Full map →</Link>
            </div>
            <div className="map-mini" style={{ borderRadius: 0, border: 0, borderTop: "1px solid var(--line)" }}>
              <RiverMap data={data} passIndex={P.length - 1} basemap="satellite" layers={{ ...DEFAULT_LAYERS, radar: false, firstBank: true }}
                radarOpacity={0.8} threeD={false} selectedId={sel} onSelect={setSel} compact />
            </div>
          </div>
          <div className="card">
            <div className="card-head"><div><h3>Where to act first</h3><p className="sub">Ranked: red first, then by how far the bank moved</p></div></div>
            <ul className="list">
              {top.map((s) => <li key={s.id}><SegmentRow s={s} current={sel === s.id} onClick={() => setSel(s.id)} /></li>)}
            </ul>
            <Link href="/banks/" className="btn ghost sm" style={{ marginTop: 10 }}>All {segs.length} stretches →</Link>
          </div>
        </section>

        <section className="grid g-3" style={{ marginTop: 16 }}>
          <div className="card span-2">
            <h3>The monsoon, pass by pass</h3>
            <p className="sub">Water inside the box. The river grows to {nf(peak.water_km2)} km² on {fmtDate(peak.date)}, more than twice its June size, then falls back. That swelling is flooding, not erosion, so it is not counted.</p>
            <WaterChart passes={P} gaps={gaps(m)} />
          </div>
          <div className="card">
            <h3>Radar schedule</h3>
            <p className="sub">NISAR repeats track {m.track?.track} every {m.track?.repeat_days} days</p>
            <ul className="list">
              <li className="row-link" style={{ cursor: "default" }}>
                <span className="rank" style={{ color: "var(--ok)" }}>✓</span>
                <span className="row-main"><b>{P.length} passes processed</b><div>{fmtDate(first.date)} – {fmtDate(last.date, true)}</div></span>
                <span className="pill green">done</span>
              </li>
              {sched.map((s) => (
                <li key={s.date} className="row-link" style={{ cursor: "default" }}>
                  <span className="rank">{s.status === "upcoming" ? "◷" : "…"}</span>
                  <span className="row-main"><b>{fmtDate(s.date, true)}</b>
                    <div>{s.status === "upcoming" ? `expected in ${Math.ceil(s.daysAway)} day${Math.ceil(s.daysAway) === 1 ? "" : "s"}` : "expected, not processed yet"}</div></span>
                  <span className={`pill ${s.status === "upcoming" ? "blue" : "grey"}`}>{s.status === "upcoming" ? "next" : "to fetch"}</span>
                </li>
              ))}
            </ul>
            <p className="note">Expected dates follow the 12-day repeat. A pass counts only after its granule is downloaded and processed.</p>
          </div>
        </section>

        <section className="grid g-3" style={{ marginTop: 16 }}>
          <div className="card span-2">
            <h3>Along the river, south to north</h3>
            <p className="sub">Each dot is a 500 m stretch that moved at least 30 m. Bigger dots have more homes nearby. Click one to open it on the map.</p>
            <RiverProfile segs={segs} onPick={(id) => (window.location.href = `/map/?seg=${id}`)} />
          </div>
          <div className="card">
            <h3>Stretches by bank</h3>
            <p className="sub">{measured} stretches checked; {m.segments?.jump ?? 0} skipped where the bank switched channel</p>
            <LevelBars segs={segs} />
            <p className="note warn">NISAR data is provisional. Thresholds are starting values until the back-test against 2026 reports.</p>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
