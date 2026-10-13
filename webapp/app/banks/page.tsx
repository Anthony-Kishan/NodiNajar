"use client";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ErrorBox, LevelPill, Loading } from "@/components/Bits";
import { RetreatChart } from "@/components/Charts";
import { IconDownload } from "@/components/Icons";
import { Footer } from "@/components/Shell";
import { dataUrl, useRiver } from "@/lib/data";
import { latStr, lonStr, nf } from "@/lib/format";
import type { SegmentProps } from "@/lib/types";

type Key = "rank" | "retreat_m" | "homes_near" | "lost_ha" | "lat";
const val = (s: SegmentProps, k: Key) => (k === "lat" ? s.centre[1] : s[k]);

export default function Banks() {
  const { data, error } = useRiver();
  const [level, setLevel] = useState<"all" | "red" | "amber">("all");
  const [side, setSide] = useState<"all" | "west" | "east">("all");
  const [sort, setSort] = useState<{ k: Key; asc: boolean }>({ k: "rank", asc: true });
  const [sel, setSel] = useState<string | null>(null);
  useEffect(() => { const q = new URLSearchParams(window.location.search).get("seg"); if (q) setSel(q); }, []);
  const all = useMemo(() => data?.segments.features.map((f) => f.properties) ?? [], [data]);
  const rows = useMemo(() => all
    .filter((s) => (level === "all" || s.level === level) && (side === "all" || s.side === side))
    .sort((a, b) => (sort.asc ? 1 : -1) * (val(a, sort.k) - val(b, sort.k))), [all, level, side, sort]);
  if (error) return <ErrorBox error={error} />;
  if (!data) return <Loading />;
  const dates = data.manifest.passes.map((p) => p.date);
  const s = all.find((x) => x.id === sel) ?? rows[0];
  const th = (k: Key, label: string) => (
    <th onClick={() => setSort((o) => ({ k, asc: o.k === k ? !o.asc : k === "rank" || k === "lat" }))} aria-sort={sort.k === k ? (sort.asc ? "ascending" : "descending") : "none"}>
      {label}{sort.k === k ? (sort.asc ? " ▲" : " ▼") : ""}
    </th>
  );
  return (
    <>
      <main className="page">
        <div className="page-head">
          <div>
            <h2>Bank stretches</h2>
            <p>Every 500 m stretch of the outer bank where the river moved at least 30 m into the land between 18 Jun and 22 Sep 2026. Red: moved at least 100 m with homes within 200 m.</p>
          </div>
          <a className="btn" href={dataUrl(data.manifest.files.csv)} download><IconDownload /> Download CSV</a>
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 14 }}>
          <div className="seg" role="group" aria-label="Risk level">
            {(["all", "red", "amber"] as const).map((l) => <button key={l} type="button" aria-pressed={level === l} onClick={() => setLevel(l)}>{l === "all" ? "All levels" : l === "red" ? "High risk" : "Watch"}</button>)}
          </div>
          <div className="seg" role="group" aria-label="Bank">
            {(["all", "west", "east"] as const).map((l) => <button key={l} type="button" aria-pressed={side === l} onClick={() => setSide(l)}>{l === "all" ? "Both banks" : l === "west" ? "West" : "East"}</button>)}
          </div>
          <span className="muted" style={{ alignSelf: "center", fontSize: 13 }}>{rows.length} stretches</span>
        </div>
        <div className="grid g-3">
          <div className="span-2 table-wrap" style={{ maxHeight: "70dvh" }}>
            <table className="data">
              <thead><tr>{th("rank", "#")}<th>Level</th><th>Bank</th>{th("lat", "Latitude")}{th("retreat_m", "Moved (m)")}{th("homes_near", "Homes ≤ 200 m")}{th("lost_ha", "Land taken (ha)")}<th /></tr></thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id} aria-selected={s?.id === r.id} onClick={() => setSel(r.id)} style={{ cursor: "pointer" }}>
                    <td className="num">{r.rank}</td><td><LevelPill level={r.level} /></td><td>{r.side === "west" ? "West" : "East"}</td>
                    <td className="num">{latStr(r.centre[1])}</td><td className="num"><b>{r.retreat_m}</b></td>
                    <td className="num">{nf(r.homes_near)}</td><td className="num">{r.lost_ha}</td>
                    <td><Link href={`/map/?seg=${r.id}`} onClick={(e) => e.stopPropagation()}>Map →</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {s && (
            <div className="card" style={{ alignSelf: "start", position: "sticky", top: 130 }}>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}><LevelPill level={s.level} /><span className="dim">#{s.rank} · {s.id}</span></div>
              <h3 style={{ marginTop: 8, fontSize: 19 }}>{s.side === "west" ? "West" : "East"} bank, {latStr(s.centre[1])}</h3>
              <p className="sub">{lonStr(s.centre[0])} · {s.homes_near} homes within 200 m · {s.lost_ha} ha taken</p>
              <RetreatChart dates={dates} history={s.history_m} level={s.level} />
              <p className="note">The value used for risk is the smaller of the last two passes ({s.retreat_m} m), so a short flood that recedes is not counted.</p>
              <div style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
                <Link className="btn sm primary" href={`/map/?seg=${s.id}`}>Show on map</Link>
                <Link className="btn sm" href={`/alerts/?seg=${s.id}`}>Alert text</Link>
              </div>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </>
  );
}
