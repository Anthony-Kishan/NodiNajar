"use client";
import type React from "react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ErrorBox, LevelPill, Loading, SegmentRow } from "@/components/Bits";
import { RetreatChart } from "@/components/Charts";
import { IconLayers, IconPause, IconPlay, IconX } from "@/components/Icons";
import { RiverMap } from "@/components/MapClient";
import { DEFAULT_LAYERS, type MapLayers } from "@/lib/mapLayers";
import { BASEMAPS, type BasemapId } from "@/lib/basemaps";
import { useRiver } from "@/lib/data";
import { fmtDate, latStr, lonStr, nf, parseDate } from "@/lib/format";

const LAYER_LABELS: [keyof MapLayers, string, string][] = [
  ["radar", "NISAR radar (HH)", "#cfd8dc"],
  ["water", "Water on this pass", "#57b8c9"],
  ["loss", "Land the river took", "#e5533d"],
  ["banks", "Outer bank on this pass", "#57d2e6"],
  ["firstBank", "Bank on 18 Jun (compare)", "#ffffff"],
  ["segments", "Bank stretches by risk", "#e9a93b"],
  ["homes", "Homes near the new bank", "#f6d365"],
];

export default function MapPage() {
  const { data, error } = useRiver();
  const [pass, setPass] = useState<number | null>(null);
  const [playing, setPlaying] = useState(false);
  const [basemap, setBasemap] = useState<BasemapId>("satellite");
  const [layers, setLayers] = useState<MapLayers>(DEFAULT_LAYERS);
  const [opacity, setOpacity] = useState(0.7);
  const [threeD, setThreeD] = useState(false);
  const [sel, setSel] = useState<string | null>(null);
  const [panelOpen, setPanelOpen] = useState(false);

  const segs = useMemo(() => data?.segments.features.map((f) => f.properties) ?? [], [data]);
  const P = data?.manifest.passes ?? [];
  const idx = pass ?? Math.max(0, P.length - 1);

  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get("seg");
    if (q) setSel(q);
  }, []);
  useEffect(() => {
    if (!playing || !P.length) return;
    const t = setInterval(() => setPass((i) => ((i ?? 0) + 1) % P.length), 1400);
    return () => clearInterval(t);
  }, [playing, P.length]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement)?.tagName === "INPUT") return;
      if (e.key === "ArrowRight") setPass((i) => Math.min(P.length - 1, (i ?? P.length - 1) + 1));
      if (e.key === "ArrowLeft") setPass((i) => Math.max(0, (i ?? P.length - 1) - 1));
      if (e.key === " ") { e.preventDefault(); setPlaying((v) => !v); }
      if (e.key === "Escape") setSel(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [P.length]);

  if (error) return <ErrorBox error={error} />;
  if (!data) return <Loading what="the map" />;
  const m = data.manifest;
  const cur = P[idx];
  const maxKm2 = Math.max(...P.map((p) => p.water_km2));
  const s = segs.find((x) => x.id === sel) ?? null;

  const ticks: React.ReactElement[] = [];
  P.forEach((p, i) => {
    if (i > 0) {
      const gapDays = (parseDate(p.date).getTime() - parseDate(P[i - 1].date).getTime()) / 86_400_000;
      if (gapDays > (m.track?.repeat_days ?? 12) + 1) {
        ticks.push(<div key={`g${i}`} className="tick gap" title={`No NISAR pass for ${gapDays} days`}>
          <span className="bar" style={{ height: 18 }} />no pass</div>);
      }
    }
    ticks.push(
      <button key={p.date} type="button" className="tick" aria-pressed={i === idx} onClick={() => { setPlaying(false); setPass(i); }}
        title={`${fmtDate(p.date, true)}: ${p.water_km2} km² water`}>
        <span className="bar" style={{ height: 8 + 30 * (p.water_km2 / maxKm2) }} />
        {fmtDate(p.date)}
      </button>,
    );
  });

  return (
    <main className="map-shell">
      <RiverMap data={data} passIndex={idx} basemap={basemap} layers={layers} radarOpacity={opacity} threeD={threeD}
        selectedId={sel} onSelect={(id) => setSel(id)} />

      <div className="float stamp" aria-live="polite">
        <b className="num">{fmtDate(cur.date, true)}</b>
        <span>Pass {idx + 1} of {P.length} · {nf(cur.water_km2, 1)} km² water · threshold {cur.threshold_db} dB</span>
      </div>

      <aside className={`float panel-left${panelOpen ? " open" : ""}`} aria-label="Map layers">
        <button type="button" className="sheet-toggle" onClick={() => setPanelOpen((v) => !v)} aria-expanded={panelOpen}>
          <IconLayers /> {panelOpen ? "Hide layers" : "Layers and basemap"}
        </button>
        <div className="ctrl-title">Basemap</div>
        <div className="chips">
          {BASEMAPS.map((b) => (
            <button key={b.id} type="button" className="chip" aria-pressed={basemap === b.id} title={b.note} onClick={() => setBasemap(b.id)}>{b.name}</button>
          ))}
        </div>
        <div className="ctrl-title">Layers</div>
        {LAYER_LABELS.map(([k, label, col]) => (
          <label key={k} className="toggle">
            <span><i className="swatch" style={{ background: col }} />{label}</span>
            <input type="checkbox" checked={layers[k]} onChange={(e) => setLayers({ ...layers, [k]: e.target.checked })} />
          </label>
        ))}
        <div className="ctrl-title">Radar opacity</div>
        <input type="range" min={0} max={1} step={0.05} value={opacity} onChange={(e) => setOpacity(Number(e.target.value))} aria-label="Radar opacity" />
        <div className="ctrl-title">View</div>
        <label className="toggle"><span>3D: columns show how far each stretch moved</span>
          <input type="checkbox" checked={threeD} onChange={(e) => setThreeD(e.target.checked)} /></label>
        <div className="ctrl-title">Legend</div>
        <div style={{ display: "grid", gap: 4, fontSize: 12.5 }} className="muted">
          <span><i className="swatch" style={{ background: "#e5533d", borderRadius: "50%" }} />High risk: moved ≥ 100 m, homes within 200 m</span>
          <span><i className="swatch" style={{ background: "#e9a93b", borderRadius: "50%" }} />Watch: moved ≥ 30 m</span>
          <span><i className="swatch" style={{ background: "#f6d365", borderRadius: "50%" }} />Home within 200 m of the new bank</span>
        </div>
        <p className="note">Radar: dark is water, bright is land. Keys: ← → step passes, space plays.</p>
      </aside>

      {s ? (
        <aside className="float panel-right" aria-label="Selected bank stretch">
          <div className="card-head">
            <div>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}><LevelPill level={s.level} /><span className="dim">#{s.rank} · {s.id}</span></div>
              <h3 style={{ marginTop: 8, fontSize: 18 }}>{s.side === "west" ? "West" : "East"} bank, {latStr(s.centre[1])}</h3>
            </div>
            <button type="button" className="btn sm ghost" onClick={() => setSel(null)} aria-label="Close"><IconX /></button>
          </div>
          <div className="stat-2">
            <div><div className="dim" style={{ fontSize: 12 }}>Bank moved</div><div className="num" style={{ fontSize: 28, fontWeight: 700 }}>{s.retreat_m} m</div></div>
            <div><div className="dim" style={{ fontSize: 12 }}>Homes within 200 m</div><div className="num" style={{ fontSize: 28, fontWeight: 700 }}>{s.homes_near}</div></div>
            <div><div className="dim" style={{ fontSize: 12 }}>Land taken</div><div className="num" style={{ fontSize: 18, fontWeight: 600 }}>{s.lost_ha} ha</div></div>
            <div><div className="dim" style={{ fontSize: 12 }}>Location</div><div className="num" style={{ fontSize: 13.5 }}>{latStr(s.centre[1])}<br />{lonStr(s.centre[0])}</div></div>
          </div>
          <div className="dim" style={{ fontSize: 12.5, marginBottom: 4 }}>Bank position on each pass, metres into the land since 18 Jun</div>
          <RetreatChart dates={P.map((p) => p.date)} history={s.history_m} level={s.level} height={170} />
          <p className="note">A missing point means the bank line switched channel on that pass, so it is left out, not guessed.</p>
          <div style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
            <Link className="btn sm primary" href={`/alerts/?seg=${s.id}`}>Alert for this stretch</Link>
            <Link className="btn sm" href={`/banks/?seg=${s.id}`}>In the table</Link>
          </div>
        </aside>
      ) : (
        <aside className="float panel-right hide-sm" aria-label="Priority list" style={{ display: undefined }}>
          <h3 style={{ margin: "0 0 4px" }}>Where to act first</h3>
          <p className="sub muted" style={{ fontSize: 13, margin: "0 0 10px" }}>Click a stretch, or one on the map</p>
          <ul className="list">{segs.slice(0, 8).map((x) => <li key={x.id}><SegmentRow s={x} onClick={() => setSel(x.id)} /></li>)}</ul>
        </aside>
      )}

      <div className="float timeline-bar" role="group" aria-label="Radar passes">
        <button type="button" className="play" onClick={() => setPlaying((v) => !v)} aria-label={playing ? "Pause" : "Play the season"}>
          {playing ? <IconPause /> : <IconPlay />}
        </button>
        <div className="ticks">{ticks}</div>
      </div>
    </main>
  );
}
