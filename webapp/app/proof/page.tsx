"use client";
import Link from "next/link";
import { useMemo } from "react";
import { ErrorBox, Kpi, LevelPill, Loading } from "@/components/Bits";
import { ForecastCheckChart } from "@/components/Charts";
import { Footer } from "@/components/Shell";
import { useRiver } from "@/lib/data";
import { fmtDate, latStr, nf } from "@/lib/format";
import { OUTCOME, useProof, type FcPassCheck } from "@/lib/proof";

const pct = (v?: number | null) => (v === undefined || v === null ? "–" : `${Math.round(v * 100)}%`);

export default function Proof() {
  const { data, error } = useRiver();
  const { forecast: F, scorecard: S, loading } = useProof();
  const segs = useMemo(() => new Map((data?.segments.features ?? []).map((f) => [f.properties.id, f.properties])), [data]);

  if (error) return <ErrorBox error={error} />;
  if (!data || loading) return <Loading what="the track record" />;
  if (!F || !S) return <ErrorBox error="forecast.json or scorecard.json is missing. Run python -m src.pipeline.scorecard." />;

  const name = (id?: string) => {
    const s = id ? segs.get(id) : undefined;
    return s ? `${s.side === "west" ? "West" : "East"} bank, ${latStr(s.centre[1])}` : id ?? "";
  };
  const bt = F.backtest;
  const checks: (FcPassCheck & { id: string; level: string })[] = F.stretches.flatMap((s) =>
    s.backtest.ok ? s.backtest.passes.filter((p) => p.measured_m !== null).map((p) => ({ ...p, id: s.id, level: s.level })) : []);
  const ranked = [...F.stretches].sort((a, b) => (segs.get(a.id)?.rank ?? 999) - (segs.get(b.id)?.rank ?? 999));
  const top = ranked.filter((s) => s.forecast.ok).slice(0, 10);
  const btRows = ranked.filter((s) => s.backtest.ok && s.level !== "green").slice(0, 8);
  const c = S.summary.counts, cl = S.summary_with_latency;
  const events = [...S.events].sort((a, b) => a.date.localeCompare(b.date));

  return (
    <>
      <main className="page">
        <div className="page-head">
          <div>
            <h2>Track record</h2>
            <p>Does it work? We test NodiNajar two ways, using only radar passes and news reports that already exist. Nothing here is tuned to look good: misses and gaps are shown as they are.</p>
          </div>
          <span className="badge">PROVISIONAL</span>
        </div>

        {/* ---------- 1. forecast back-test ---------- */}
        <section className="card" style={{ marginBottom: 16 }}>
          <h3>1 · Forecast check: we hid the last two passes</h3>
          <p className="sub">We trained the forecast on the passes up to {fmtDate(bt.trained_through, true)}, predicted where each bank would be on {bt.hidden_passes.map((d) => fmtDate(d, true)).join(" and ")}, then compared with what NISAR measured.</p>
          <div className="grid g-4" style={{ marginBottom: 14 }}>
            <Kpi label="Typical error, all stretches" value={bt.all.median_abs_error_m ?? "–"} unit="m" foot={`median of ${bt.all.n_scored} checks on ${bt.all.n_stretches} stretches`} accent="var(--monsoon)" />
            <Kpi label="Typical error, high-risk stretches" value={bt.red.median_abs_error_m ?? "–"} unit="m" foot={`median of ${bt.red.n_scored} checks`} accent="var(--erosion)" />
            <Kpi label="Measured value inside the forecast range" value={pct(bt.all.share_in_range)} foot={`target is about 80%: our range is still too narrow`} accent="var(--watch)" />
            <Kpi label="Average error (all)" value={bt.all.mae_m ?? "–"} unit="m" foot="pulled up by a few stretches where the channel switched" />
          </div>
          <div className="grid g-2">
            <div>
              <div className="dim" style={{ fontSize: 12.5, marginBottom: 4 }}>Each dot is one stretch on one hidden pass. On the line = perfect forecast.</div>
              <ForecastCheckChart rows={checks.map((r) => ({ id: r.id, date: r.date, measured: r.measured_m as number, expected: r.expected_m, low: r.low_m, high: r.high_m }))} />
            </div>
            <div className="table-wrap">
              <table className="data" style={{ minWidth: 520 }}>
                <thead><tr><th>Stretch</th><th>Pass</th><th>Forecast (m)</th><th>Measured (m)</th><th>Inside range</th></tr></thead>
                <tbody>
                  {btRows.flatMap((s) => (s.backtest.ok ? s.backtest.passes : []).map((p, i) => (
                    <tr key={s.id + p.date}>
                      <td>{i === 0 ? <Link href={`/map/?seg=${s.id}`}><LevelPill level={s.level} /> {s.id}</Link> : ""}</td>
                      <td className="num">{fmtDate(p.date)}</td>
                      <td className="num">{p.expected_m} <span className="dim">({p.low_m}–{p.high_m})</span></td>
                      <td className="num"><b>{p.measured_m ?? "not measured"}</b></td>
                      <td>{p.in_range === null ? "–" : p.in_range ? "yes" : <span className="muted">no ({p.error_m! > 0 ? "+" : ""}{p.error_m} m)</span>}</td>
                    </tr>
                  )))}
                </tbody>
              </table>
            </div>
          </div>
          <p className="note">{F.method} Positions are metres into the land since 18 Jun.</p>
        </section>

        {/* ---------- 2. next passes ---------- */}
        <section className="card" style={{ marginBottom: 16 }}>
          <h3>2 · Forecast for the next passes</h3>
          <p className="sub">Trained on all {data.manifest.passes.length} passes to {fmtDate(F.trained_through, true)}. The {fmtDate(F.targets[0], true)} pass has been acquired; when we process it, this table becomes the next check, made in public before the answer is known.</p>
          <div className="table-wrap">
            <table className="data">
              <thead><tr><th>#</th><th>Stretch</th><th>Rate (m per 12 days)</th>{F.targets.map((t) => <th key={t}>Further by {fmtDate(t)}</th>)}<th>Homes ≤ 200 m</th></tr></thead>
              <tbody>
                {top.map((s) => {
                  const p = segs.get(s.id);
                  const fo = s.forecast;
                  if (!fo.ok) return null;
                  return (
                    <tr key={s.id}>
                      <td className="num">{p?.rank}</td>
                      <td><Link href={`/map/?seg=${s.id}`}><LevelPill level={s.level} /> {name(s.id)}</Link></td>
                      <td className="num">{fo.advancing ? fo.rate_m_per_12d : "not advancing"}</td>
                      {fo.targets.map((t) => (
                        <td key={t.date} className="num"><b>{t.advance_m}</b> m <span className="dim">({Math.max(0, Math.round(t.low_m - fo.last_measured.position_m))}–{Math.max(0, Math.round(t.high_m - fo.last_measured.position_m))})</span></td>
                      ))}
                      <td className="num">{nf(p?.homes_near ?? 0)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="note">“Further” is the expected extra movement into the land beyond the last measured bank, with the low–high range in brackets. A straight-line trend over one monsoon: treat it as a ranking of urgency, not a promise.</p>
        </section>

        {/* ---------- 3. news check ---------- */}
        <section className="card">
          <h3>3 · News check: would it have warned before the papers reported erosion?</h3>
          <p className="sub">{events.length} erosion reports from this monsoon in the box ({fmtDate(S.season[0])} to {fmtDate(S.season[1])}, plus 12 days). We replay the season pass by pass and ask whether a nearby stretch was flagged before the reported date. Rule: {S.rule}.</p>
          <div className="grid g-4" style={{ marginBottom: 14 }}>
            <Kpi label="On a watched bank" value={S.summary.on_bank} foot={`${c.warned} warned before · ${c.late} flagged after · ${c.missed} missed`} accent="var(--monsoon)" />
            <Kpi label="Warning lead time" value={S.summary.median_lead_days ?? "–"} unit="days" foot={`from the radar pass; ${cl.median_lead_days ?? "–"} days if processing takes ${S.latency_days} days`} accent="var(--ok)" />
            <Kpi label="On char islands or unwatched banks" value={c.off_bank} foot="version 1 watches the outer banks only" accent="var(--watch)" />
            <Kpi label="Place not pinned yet" value={c.unscorable} foot="reports naming only a union; the team is pinning them" />
          </div>
          <p className="callout" style={{ marginTop: 0 }}>
            {S.summary.on_bank < 5
              ? `Only ${S.summary.on_bank} of ${events.length} reports fall on a bank we measure, so this is not yet a hit rate. The clearest finding so far: most reported losses this monsoon were on char islands, where many families live and version 1 does not look.`
              : `Hit rate ${pct(S.summary.hit_rate)} on ${S.summary.on_bank} reports on watched banks.`}
          </p>
          <div className="table-wrap" style={{ marginTop: 12 }}>
            <table className="data">
              <thead><tr><th>Reported date</th><th>Place</th><th>Lost</th><th>Result</th><th>Source</th></tr></thead>
              <tbody>
                {events.map((e) => {
                  const o = OUTCOME[e.outcome];
                  return (
                    <tr key={e.id}>
                      <td className="num">{fmtDate(e.date, true)}<div className="dim" style={{ fontSize: 11.5 }}>{e.meta.date_precision}</div></td>
                      <td style={{ whiteSpace: "normal", minWidth: 220 }}>{e.meta.place}<div className="dim" style={{ fontSize: 12 }}>{[e.meta.union, e.meta.upazila].filter(Boolean).join(", ")}</div></td>
                      <td style={{ whiteSpace: "normal", minWidth: 160 }}>{e.meta.homes_lost || e.meta.other_losses || "–"}</td>
                      <td style={{ whiteSpace: "normal", minWidth: 200 }}>
                        <span className={`pill ${o.pill}`}>{o.label}</span>
                        {e.outcome === "warned" || e.outcome === "late" ? (
                          <div className="dim" style={{ fontSize: 12, marginTop: 4 }}>
                            <Link href={`/map/?seg=${e.stretch}`}>{e.stretch}</Link> flagged {fmtDate(e.flag_date!, true)} ({Math.abs(e.lead_days!)} days {e.lead_days! >= 0 ? "before" : "after"}), {nf(e.distance_m!)} m away
                          </div>
                        ) : <div className="dim" style={{ fontSize: 12, marginTop: 4 }}>{o.note}</div>}
                      </td>
                      <td><a href={e.meta.source_url} target="_blank" rel="noreferrer">{e.meta.source_name}</a><div className="dim" style={{ fontSize: 11.5 }}>{fmtDate(e.meta.report_date)}</div></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="note">Places were pinned from Google Maps and OpenStreetMap labels and still need a team check. A union is too large to match a 500 m stretch, so union-only reports are listed but not scored. Lead time counts from the radar pass date. We had planned a stricter rule (red at least 12 days ahead); neither on-bank stretch reached red, so under that rule both reports count as missed.</p>
        </section>
      </main>
      <Footer />
    </>
  );
}
