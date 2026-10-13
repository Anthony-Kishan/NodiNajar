"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useNow, useRiver } from "@/lib/data";
import { fmtDate } from "@/lib/format";
import { nextPass } from "@/lib/schedule";
import { IconBell, IconBook, IconGrid, IconMap, IconSat, IconShield, IconWaves, Mark } from "./Icons";

const TABS = [
  { href: "/", label: "Overview", icon: IconGrid },
  { href: "/map/", label: "Live map", icon: IconMap },
  { href: "/banks/", label: "Bank stretches", icon: IconWaves },
  { href: "/passes/", label: "Radar passes", icon: IconSat },
  { href: "/alerts/", label: "Alerts", icon: IconBell },
  { href: "/embankments/", label: "Embankments", icon: IconShield, tag: "next" },
  { href: "/methods/", label: "Methods & data", icon: IconBook },
];

function countdown(days: number): string {
  const s = Math.max(0, Math.round(days * 86400));
  const d = Math.floor(s / 86400), h = Math.floor((s % 86400) / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
  return d > 0 ? `${d}d ${h}h ${String(m).padStart(2, "0")}m` : `${h}h ${String(m).padStart(2, "0")}m ${String(sec).padStart(2, "0")}s`;
}

function LiveStatus() {
  const { data } = useRiver();
  const now = useNow(1000);
  if (!data) return <div className="live"><span className="live-text">Loading radar data…</span></div>;
  const m = data.manifest;
  const last = m.passes[m.passes.length - 1].date;
  const next = nextPass(m, now);
  return (
    <div className="live" title="NISAR repeats this track every 12 days; the next date is the expected pass, not yet observed">
      <span className="pulse-dot" />
      <span className="live-text">Data to <b>{fmtDate(last, true)}</b>{next && <> · next NISAR pass in <b className="num">{countdown(next.daysAway)}</b></>}</span>
    </div>
  );
}

export default function Shell({ children }: { children: ReactNode }) {
  const path = usePathname() || "/";
  const norm = (p: string) => (p.endsWith("/") ? p : p + "/");
  return (
    <>
      <header className="header">
        <div className="header-row">
          <Link href="/" className="brand" aria-label="NodiNajar home">
            <Mark />
            <div>
              <h1>NodiNajar<span lang="bn">নদীনজর</span></h1>
              <p>Jamuna riverbank watch · Sirajganj, Bangladesh</p>
            </div>
          </Link>
          <div className="header-spacer" />
          <LiveStatus />
          <span className="badge" title="NISAR science data is provisional (validated at a limited set of sites)">NISAR · PROVISIONAL</span>
        </div>
        <nav className="tabs" aria-label="Sections">
          {TABS.map(({ href, label, icon: I, tag }) => {
            const active = href === "/" ? norm(path) === "/" : norm(path).startsWith(href);
            return (
              <Link key={href} href={href} className={`tab${active ? " active" : ""}`} aria-current={active ? "page" : undefined}>
                <I /> {label} {tag && <span className="tag">{tag}</span>}
              </Link>
            );
          })}
        </nav>
      </header>
      {children}
    </>
  );
}

export function Footer() {
  return (
    <footer className="footer">
      Radar: NASA-ISRO NISAR L2 GCOV (provisional) via NASA ASF DAAC · Homes: Overture Maps (OpenStreetMap, Google, Microsoft) ·
      Team AlphaMatrix, NASA Space Apps Challenge 2026 · <a href="https://github.com/Anthony-Kishan/NodiNajar">Open source (Apache-2.0)</a>
    </footer>
  );
}
