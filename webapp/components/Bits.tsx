"use client";
import Link from "next/link";
import type { ReactNode } from "react";
import { latStr, levelName, nf } from "@/lib/format";
import type { SegmentProps } from "@/lib/types";

export function Kpi({ label, value, unit, foot, accent }: { label: string; value: ReactNode; unit?: string; foot?: ReactNode; accent?: string }) {
  return (
    <div className="card kpi" style={{ ["--accent" as string]: accent }}>
      <div className="label">{label}</div>
      <div className="value num">{value}{unit && <small>{unit}</small>}</div>
      {foot && <div className="foot">{foot}</div>}
    </div>
  );
}

export function LevelPill({ level }: { level: SegmentProps["level"] }) {
  return <span className={`pill ${level}`}>{levelName[level]}</span>;
}

export function SegmentRow({ s, onClick, current, href }: { s: SegmentProps; onClick?: () => void; current?: boolean; href?: string }) {
  const inner = (
    <>
      <span className={`rank ${s.level}`}>{s.rank}</span>
      <span className="row-main">
        <b>{s.side === "west" ? "West" : "East"} bank, {latStr(s.centre[1])}</b>
        <div>{s.homes_near ? `${nf(s.homes_near)} homes within 200 m` : "No mapped homes nearby"} · {s.id}</div>
      </span>
      <span className="row-val num">{s.retreat_m}<small>m moved</small></span>
    </>
  );
  if (href) return <Link className="row-link" href={href} aria-current={current}>{inner}</Link>;
  return <button type="button" className="row-link" onClick={onClick} aria-current={current}>{inner}</button>;
}

export function Loading({ what = "radar data" }: { what?: string }) {
  return (
    <div className="page">
      <div className="grid g-4" style={{ marginBottom: 16 }}>{[0, 1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 120 }} />)}</div>
      <div className="skeleton" style={{ height: 380 }} />
      <p className="muted" style={{ marginTop: 12 }}>Loading {what}…</p>
    </div>
  );
}

export function ErrorBox({ error }: { error: string }) {
  return <div className="page"><div className="card"><h3>Could not load the data</h3><p className="muted">{error}</p>
    <p className="note">Run <code>python -m src.pipeline.export_web</code> to create <code>webapp/public/data/</code>.</p></div></div>;
}
