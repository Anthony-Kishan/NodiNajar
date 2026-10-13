"use client";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { Banklines, Homes, Manifest, RiverData, Segments } from "./types";

const BASE = (process.env.NEXT_PUBLIC_DATA_BASE ?? "/data").replace(/\/$/, "");
export const dataUrl = (p: string) => `${BASE}/${p}`;

type State = { data: RiverData | null; error: string | null };
const Ctx = createContext<State>({ data: null, error: null });
let cache: Promise<RiverData> | null = null;

async function getJson<T>(p: string): Promise<T> {
  const r = await fetch(dataUrl(p));
  if (!r.ok) throw new Error(`${p}: HTTP ${r.status}`);
  return r.json() as Promise<T>;
}

export function loadRiverData(): Promise<RiverData> {
  if (!cache) {
    cache = (async () => {
      const manifest = await getJson<Manifest>("manifest.json");
      const [segments, homes, banklines] = await Promise.all([
        getJson<Segments>(manifest.files.segments),
        getJson<Homes>(manifest.files.homes),
        manifest.files.banklines ? getJson<Banklines>(manifest.files.banklines) : Promise.resolve(null),
      ]);
      return { manifest, segments, homes, banklines };
    })();
    cache.catch(() => { cache = null; });
  }
  return cache;
}

export function DataProvider({ children }: { children: ReactNode }) {
  const [s, setS] = useState<State>({ data: null, error: null });
  useEffect(() => {
    loadRiverData().then((data) => setS({ data, error: null }), (e) => setS({ data: null, error: String(e) }));
  }, []);
  return <Ctx.Provider value={s}>{children}</Ctx.Provider>;
}

export const useRiver = () => useContext(Ctx);

/** Ticks every `ms` so countdowns and "data age" stay live. */
export function useNow(ms = 1000): Date {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => { const t = setInterval(() => setNow(new Date()), ms); return () => clearInterval(t); }, [ms]);
  return now;
}
