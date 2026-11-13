"use client";
import { ErrorBox, Loading } from "@/components/Bits";
import { Footer } from "@/components/Shell";
import { dataUrl, useRiver } from "@/lib/data";
import { useJson, type RainFile } from "@/lib/extra";
import { fmtDate, nf } from "@/lib/format";

interface Drivers {
  note: string;
  intervals: { from: string; to: string; water_from_km2: number; water_to_km2: number; river: "rising" | "falling"; n: number; median_change_m: number | null; share_inland_pct: number | null; share_riverward_pct: number | null }[];
  same_stage: { a: string; b: string; water_a_km2: number; water_b_km2: number; n: number; median_change_m: number; share_inland_pct: number; share_riverward_pct: number }[];
}

const SRC = {
  banglapedia: { t: "Banglapedia: Riverbank Erosion", u: "https://en.banglapedia.org/index.php/Riverbank_Erosion" },
  frontiers: { t: "Shampa et al. 2025, Frontiers in Earth Science 13:1570577", u: "https://www.frontiersin.org/articles/10.3389/feart.2025.1570577/full" },
  tbs: { t: "UNB in The Business Standard, 12 Dec 2020", u: "https://www.tbsnews.net/node/170509" },
  jpl: { t: "NASA JPL: NISAR science", u: "https://www.jpl.nasa.gov/press-kits/nisar/mission-overview/science/" },
};
const Cite = ({ s }: { s: keyof typeof SRC }) => <a className="dim" href={SRC[s].u} target="_blank" rel="noreferrer">[{SRC[s].t}]</a>;

export default function Why() {
  const { data, error } = useRiver();
  const drv = useJson<Drivers>("drivers.json");
  const rain = useJson<RainFile>("rain.json");
  if (error) return <ErrorBox error={error} />;
  if (!data) return <Loading what="the science page" />;
  const P = data.manifest.passes;
  const t = data.manifest.totals;
  const hvPass = P.find((p) => p.date === "2026-07-12" && p.radar_hv) ?? P.find((p) => p.radar_hv);
  const wettest = rain ? [...rain.by_pass].sort((a, b) => b.rain_window_mm - a.rain_window_mm)[0] : null;
  const widest = [...P].sort((a, b) => b.water_km2 - a.water_km2)[0];

  return (
    <>
      <main className="page">
        <div className="page-head">
          <div>
            <h2>Why the river moves</h2>
            <p>What we think drives the changes NISAR sees, which of it our own data can test, and what we are still unsure about. Hypotheses are marked as hypotheses.</p>
          </div>
          <span className="badge">HYPOTHESES</span>
        </div>

        <section className="card" style={{ marginBottom: 16 }}>
          <h3>1 · The monsoon rhythm</h3>
          <p>{wettest && <>The wettest 12 days at the box centre ended on <b>{fmtDate(wettest.date, true)}</b> ({nf(wettest.rain_window_mm, 0)} mm, NASA POWER). </>}
            The river was widest on <b>{fmtDate(widest.date, true)}</b> ({nf(widest.water_km2, 0)} km² of water in the box), then fell to {nf(P[4].water_km2, 0)} km² by {fmtDate(P[4].date, true)} and rose again. The Jamuna responds to rain over its whole basin upstream in India and Bhutan, so local rain only hints at the timing.</p>
          <p className="note">Charts of both are on the <a href="/passes/">Radar passes</a> tab.</p>
        </section>

        {drv && (
          <section className="card" style={{ marginBottom: 16 }}>
            <h3>2 · What our data says about the bank line</h3>
            <p>Between passes, the measured bank moves inland when the river rises and back when it falls. So part of what we measure from one pass to the next is the waterline climbing and dropping on the bank, not only land lost. That is why NodiNajar only counts retreat confirmed on two passes.</p>
            <div className="table-wrap">
              <table className="data">
                <thead><tr><th>Between passes</th><th>River</th><th>Water (km²)</th><th>Stretches measured</th><th>Median bank change</th><th>Moved inland ≥ 30 m</th><th>Moved riverward ≥ 30 m</th></tr></thead>
                <tbody>{drv.intervals.map((r) => (
                  <tr key={r.from}>
                    <td className="num">{fmtDate(r.from)} → {fmtDate(r.to)}</td>
                    <td>{r.river}</td>
                    <td className="num">{nf(r.water_from_km2, 0)} → {nf(r.water_to_km2, 0)}</td>
                    <td className="num">{r.n}</td>
                    <td className="num"><b>{r.median_change_m === null ? "–" : `${r.median_change_m > 0 ? "+" : ""}${r.median_change_m} m`}</b></td>
                    <td className="num">{r.share_inland_pct ?? "–"}%</td>
                    <td className="num">{r.share_riverward_pct ?? "–"}%</td>
                  </tr>))}</tbody>
              </table>
            </div>
            <p style={{ marginTop: 12 }}>The fairer test compares passes when the river held about the same amount of water:</p>
            <div className="table-wrap">
              <table className="data">
                <thead><tr><th>Passes at a similar water level</th><th>Water (km²)</th><th>Stretches</th><th>Median bank change</th><th>Inland ≥ 30 m</th><th>Riverward ≥ 30 m</th></tr></thead>
                <tbody>{drv.same_stage.map((r) => (
                  <tr key={r.a + r.b}>
                    <td className="num">{fmtDate(r.a, true)} and {fmtDate(r.b, true)}</td>
                    <td className="num">{nf(r.water_a_km2, 0)} and {nf(r.water_b_km2, 0)}</td>
                    <td className="num">{r.n}</td>
                    <td className="num"><b>{r.median_change_m > 0 ? "+" : ""}{r.median_change_m} m</b></td>
                    <td className="num">{r.share_inland_pct}%</td>
                    <td className="num">{r.share_riverward_pct}%</td>
                  </tr>))}</tbody>
              </table>
            </div>
            <p className="callout">What we are unsure about: the two fair comparisons disagree. From 30 June to 22 September the typical flagged stretch sits further inland; from 18 June to 17 August it does not. Our season totals compare a low-water June with a higher-water September, so some of the {nf(t.max_retreat_m)} m largest retreat may be water level, not lost land. Next step: measure the bank at a fixed water level, and add NISAR interferometry to tell a sinking bank from a wet one.</p>
            <p className="note">{drv.note} Computed by <code>src/compute/drivers.py</code> (tested).</p>
          </section>
        )}

        <section className="card" style={{ marginBottom: 16 }}>
          <h3>3 · Physical drivers (hypotheses)</h3>
          <ul className="list-plain">
            <li><b>Loose banks.</b> The Jamuna's banks are recently laid silt and fine sand that the current lifts easily. <Cite s="banglapedia" /> <Cite s="frontiers" /></li>
            <li><b>A braided river.</b> Four to six channels run side by side across a river about 10 km wide; when a channel shifts toward a bank, that bank fails. Our bank engine skips passes where the outer channel switched. <Cite s="frontiers" /></li>
            <li><b>Falling water.</b> Erosion speeds up when floodwater recedes quickly. Our pass-to-pass table cannot show this yet, because the waterline itself moves with the flood. <Cite s="banglapedia" /></li>
            <li><b>Rain upstream.</b> Heavy rain from early to mid July came before the widest river on {fmtDate(widest.date, true)}. One 50 km rain cell cannot prove the link.</li>
          </ul>
        </section>

        <section className="card" style={{ marginBottom: 16 }}>
          <h3>4 · Human drivers</h3>
          <ul className="list-plain">
            <li><b>Sand lifting.</b> Local reports link illegal sand dredging in Khukni, Jalalpur, Koijuri and Gala unions of Shahjadpur to bank erosion on a 6 km stretch. <Cite s="tbs" /> We cannot see dredgers in radar; this is a reported driver, not one we measured.</li>
            <li><b>Bank protection.</b> Hard protection holds a bank in place and can move the attack along the river; a published warning model misread protected banks for that reason. <Cite s="frontiers" /></li>
            <li><b>What people lose.</b> NodiNajar measured {nf(t.land_lost_ha, 1)} ha of land lost on the outer banks this season and {nf(t.homes_near_new_bank)} homes within 200 m of the new bank. Nationally, about a million people are affected by bank erosion each year. <Cite s="banglapedia" /></li>
          </ul>
        </section>

        <section className="card" style={{ marginBottom: 16 }}>
          <h3>5 · Two radar channels, two views</h3>
          <p>NISAR sends and receives radar waves in set directions. <b>HH</b> (sent and received horizontally) shows smooth water as dark and land as bright, which is how we map water. <b>HV</b> (sent horizontal, received vertical) gets brighter where waves bounce around inside vegetation such as crops and grass; open water is dark in both.</p>
          {hvPass?.radar_hv && (
            <div className="grid g-2" style={{ marginTop: 10 }}>
              <figure style={{ margin: 0 }}><img src={dataUrl(hvPass.radar)} alt={`NISAR HH on ${hvPass.date}`} style={{ width: "100%", height: 420, objectFit: "cover", objectPosition: "50% 45%", borderRadius: 10 }} /><figcaption className="dim">HH · {fmtDate(hvPass.date, true)} · NASA-ISRO NISAR</figcaption></figure>
              <figure style={{ margin: 0 }}><img src={dataUrl(hvPass.radar_hv)} alt={`NISAR HV on ${hvPass.date}`} style={{ width: "100%", height: 420, objectFit: "cover", objectPosition: "50% 45%", borderRadius: 10 }} /><figcaption className="dim">HV · {fmtDate(hvPass.date, true)} · NASA-ISRO NISAR</figcaption></figure>
            </div>
          )}
          <p className="note">Both channels come from the same NISAR L2 GCOV files. Switch between them on the Live map.</p>
        </section>

        <section className="card">
          <h3>6 · What NISAR could do next</h3>
          <ul className="list-plain">
            <li><b>A warning every 12 days, everywhere.</b> NISAR images any spot on Earth every 12 days, through cloud, so the same method can watch the Teesta, the Padma or the Brahmaputra in Assam. <Cite s="jpl" /></li>
            <li><b>Embankments that sink before they breach.</b> NISAR measures land moving by centimetres; interferometry over embankments could flag weak sections before the monsoon. <Cite s="jpl" /></li>
            <li><b>Chars and crops.</b> L-band follows changes in agricultural land and its soil moisture, which could show which char fields are lost or newly farmable. <Cite s="jpl" /></li>
            <li><b>S-band.</b> NISAR is the first satellite to collect L-band and S-band together; S-band is more sensitive to light vegetation such as young crops. <Cite s="jpl" /></li>
          </ul>
        </section>
      </main>
      <Footer />
    </>
  );
}
