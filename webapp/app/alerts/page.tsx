"use client";
import { useEffect, useMemo, useState } from "react";
import { ErrorBox, LevelPill, Loading, SegmentRow } from "@/components/Bits";
import { Footer } from "@/components/Shell";
import { useRiver } from "@/lib/data";
import { latStr } from "@/lib/format";
import { alertText, audience } from "@/lib/alerts";

export default function Alerts() {
  const { data, error } = useRiver();
  const [sel, setSel] = useState<string | null>(null);
  const [lang, setLang] = useState<"bn" | "en">("bn");
  const [speaking, setSpeaking] = useState(false);
  const [voiceMsg, setVoiceMsg] = useState("");
  useEffect(() => { const q = new URLSearchParams(window.location.search).get("seg"); if (q) setSel(q); }, []);
  const segs = useMemo(() => data?.segments.features.map((f) => f.properties) ?? [], [data]);
  if (error) return <ErrorBox error={error} />;
  if (!data) return <Loading />;
  const reds = segs.filter((s) => s.level === "red");
  const s = segs.find((x) => x.id === sel) ?? reds[0] ?? segs[0];
  const days = data.manifest.period_days;
  const text = alertText(s, days, lang);

  function speak() {
    if (!("speechSynthesis" in window)) { setVoiceMsg("This browser has no speech voices."); return; }
    const u = new SpeechSynthesisUtterance(text);
    const v = speechSynthesis.getVoices().find((x) => x.lang.toLowerCase().startsWith(lang === "bn" ? "bn" : "en"));
    if (v) u.voice = v; else if (lang === "bn") setVoiceMsg("No Bangla voice is installed in this browser; the real call uses a Bangla TTS service.");
    u.lang = lang === "bn" ? "bn-BD" : "en-GB";
    u.onend = () => setSpeaking(false);
    speechSynthesis.cancel(); speechSynthesis.speak(u); setSpeaking(true);
  }

  return (
    <>
      <main className="page">
        <div className="page-head">
          <div>
            <h2>Alerts</h2>
            <p>When a stretch turns red, the families within 200 m get an SMS and a voice call in Bangla, and officials get the priority list. The text is a fixed template filled with measured numbers. No AI writes alerts.</p>
          </div>
          <span className="pill grey">Sending switched off in this demo</span>
        </div>
        <div className="grid g-3">
          <div className="card">
            <h3>Red stretches ({reds.length})</h3>
            <p className="sub">Each one would trigger a family alert</p>
            <ul className="list">{reds.map((r) => <li key={r.id}><SegmentRow s={r} current={s.id === r.id} onClick={() => setSel(r.id)} /></li>)}</ul>
            <p className="note">Amber stretches ({segs.length - reds.length}) go to officials and NGOs only.</p>
          </div>
          <div className="card" style={{ display: "grid", placeItems: "center", gap: 14 }}>
            <div className="seg" role="tablist" aria-label="Language">
              <button type="button" role="tab" aria-pressed={lang === "bn"} onClick={() => setLang("bn")}>বাংলা</button>
              <button type="button" role="tab" aria-pressed={lang === "en"} onClick={() => setLang("en")}>English</button>
            </div>
            <div className="phone">
              <div className="notch" />
              <div className="dim" style={{ fontSize: 12, marginBottom: 8 }}>SMS · NodiNajar · now</div>
              <div className="bubble" lang={lang}>{text}</div>
              <div style={{ display: "flex", gap: 8, marginTop: 14, justifyContent: "center" }}>
                <button type="button" className="btn sm" onClick={speak} disabled={speaking}>{speaking ? "Playing…" : "▶ Play voice call"}</button>
              </div>
              {voiceMsg && <p className="dim" style={{ fontSize: 11.5, marginTop: 8, textAlign: "center" }}>{voiceMsg}</p>}
            </div>
          </div>
          <div className="card">
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}><LevelPill level={s.level} /><span className="dim">{s.id}</span></div>
            <h3 style={{ marginTop: 8 }}>{s.side === "west" ? "West" : "East"} bank, {latStr(s.centre[1])}</h3>
            <p className="sub">Moved {s.retreat_m} m in {days} days · {s.homes_near} homes within 200 m</p>
            <div className="ctrl-title">Who is told</div>
            <ul style={{ margin: 0, paddingLeft: 18 }}>{audience(s.level).map((a) => <li key={a}>{a}</li>)}</ul>
            <div className="ctrl-title">Delivery</div>
            <ol className="steps">
              <li><span><b>Opt-in list</b><span className="muted">Phone numbers registered through the union parishad. None stored in this demo.</span></span></li>
              <li><span><b>SMS + voice</b><span className="muted">Through a Bangladesh SMS/voice gateway (Twilio for the demo) with Bangla text-to-speech.</span></span></li>
              <li><span><b>Logged</b><span className="muted">Every alert is logged with the pass and numbers that triggered it.</span></span></li>
            </ol>
            <p className="note warn">Thresholds are starting values. They will be set from the back-test so families keep trusting the calls.</p>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
