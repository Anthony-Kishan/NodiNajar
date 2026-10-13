"use client";
import { ErrorBox, Loading } from "@/components/Bits";
import { WaterChart } from "@/components/Charts";
import { Footer } from "@/components/Shell";
import { dataUrl, useNow, useRiver } from "@/lib/data";
import { fmtDate, nf } from "@/lib/format";
import { expectedPasses, gaps } from "@/lib/schedule";

export default function Passes() {
  const { data, error } = useRiver();
  const now = useNow(60_000);
  if (error) return <ErrorBox error={error} />;
  if (!data) return <Loading />;
  const m = data.manifest, P = m.passes, G = gaps(m);
  const sched = expectedPasses(m, now, 3);
  return (
    <>
      <main className="page">
        <div className="page-head">
          <div>
            <h2>Radar passes</h2>
            <p>NASA-ISRO NISAR, L-band radar, Level-2 GCOV, HH polarisation, 10 m pixels. Track {m.track?.track}, frame {m.track?.frame}, {m.track?.direction}. Radar sees through monsoon cloud: calm water is dark, land is bright.</p>
          </div>
          <span className="badge">PROVISIONAL DATA</span>
        </div>
        <div className="card" style={{ marginBottom: 16 }}>
          <h3>Water in the box on each pass</h3>
          <p className="sub">{G.length ? `No NISAR pass between ${fmtDate(G[0].from)} and ${fmtDate(G[0].to)} (${G[0].days} days).` : "Every 12-day pass is present."} Thresholds are set per pass from the radar histogram; passes without a clear valley use the season median.</p>
          <WaterChart passes={P} gaps={G} height={250} />
        </div>
        <div className="grid g-4">
          {P.map((p) => (
            <article key={p.date} className="card" style={{ padding: 12 }}>
              <div style={{ aspectRatio: "3 / 4", borderRadius: 10, overflow: "hidden", background: "#081218", border: "1px solid var(--line)" }}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={dataUrl(p.thumb)} alt={`NISAR radar of the Jamuna on ${fmtDate(p.date, true)}`} loading="lazy"
                  style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginTop: 10 }}>
                <b style={{ fontSize: 17 }}>{fmtDate(p.date, true)}</b><span className="dim num">#{p.index + 1}</span>
              </div>
              <div className="muted num" style={{ fontSize: 13.5 }}>{nf(p.water_km2, 1)} km² water · {p.threshold_db} dB</div>
              <div className="dim" style={{ fontSize: 12 }}>threshold: {p.threshold_from}</div>
              <div className="dim" style={{ fontSize: 10.5, marginTop: 6, wordBreak: "break-all" }}>{p.granule}</div>
            </article>
          ))}
        </div>
        <div className="card" style={{ marginTop: 16 }}>
          <h3>Next passes on this track</h3>
          <p className="sub">Computed from the 12-day repeat. They become data only after the granule is downloaded from NASA ASF and processed.</p>
          <div className="grid g-4">
            {sched.map((s) => (
              <div key={s.date} className="card" style={{ padding: 14 }}>
                <b>{fmtDate(s.date, true)}</b>
                <div className="muted" style={{ fontSize: 13 }}>{s.status === "upcoming" ? `in ${Math.ceil(s.daysAway)} days` : "should be available, not processed yet"}</div>
              </div>
            ))}
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
