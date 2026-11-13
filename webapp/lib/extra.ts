"use client";
import { useEffect, useState } from "react";
import { dataUrl } from "./data";

const cache = new Map<string, Promise<unknown>>();

/** Load an optional JSON file from public/data; null while loading or if it is missing. */
export function useJson<T>(file: string): T | null {
  const [v, setV] = useState<T | null>(null);
  useEffect(() => {
    if (!cache.has(file)) cache.set(file, fetch(dataUrl(file)).then((r) => (r.ok ? r.json() : null)).catch(() => null));
    cache.get(file)!.then((x) => setV(x as T | null));
  }, [file]);
  return v;
}

export interface RainFile {
  source: string; request: string; point: [number, number]; note: string;
  daily: { date: string; mm: number }[];
  by_pass: { date: string; window_days: number; rain_window_mm: number; missing_window: number; days_since_prev?: number; rain_since_prev_mm?: number }[];
}
