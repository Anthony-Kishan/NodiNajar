"use client";
import { useEffect, useState } from "react";
import { dataUrl } from "./data";

export interface FcTarget { date: string; days_ahead: number; expected_m: number; low_m: number; high_m: number; advance_m: number }
export interface FcPassCheck extends FcTarget { measured_m: number | null; error_m: number | null; in_range: boolean | null }
export interface FcStretch {
  id: string; level: "red" | "amber" | "green";
  forecast: { ok: true; rate_m_per_12d: number; advancing: boolean; n_passes: number; last_measured: { date: string; position_m: number }; targets: FcTarget[] } | { ok: false; reason: string };
  backtest: { ok: true; rate_m_per_12d: number; passes: FcPassCheck[] } | { ok: false; reason: string };
}
export interface FcSummary { n_stretches?: number; n_scored: number; mae_m?: number; median_abs_error_m?: number; bias_m?: number; share_in_range?: number }
export interface Forecast {
  label: string; method: string; status: string; targets: string[]; trained_through: string;
  backtest: { hidden_passes: string[]; trained_through: string; all: FcSummary; red: FcSummary; amber: FcSummary };
  stretches: FcStretch[];
}
export type Outcome = "warned" | "late" | "missed" | "off_bank" | "unscorable" | "too_early";
export interface ScoredEvent {
  id: string; date: string; outcome: Outcome; outcome_with_latency: Outcome;
  stretch?: string; nearest?: string; distance_m?: number; flag_date?: string; lead_days?: number; reason?: string;
  meta: Record<string, string>;
}
export interface ScoreSummary { counts: Record<Outcome, number>; on_bank: number; hit_rate: number | null; median_lead_days: number | null }
export interface Scorecard {
  label: string; status: string; season: [string, string]; rule: string; latency_days: number;
  summary: ScoreSummary; summary_with_latency: ScoreSummary; events: ScoredEvent[];
}

type S = { forecast: Forecast | null; scorecard: Scorecard | null; error: string | null };
let cache: Promise<S> | null = null;

function load(): Promise<S> {
  if (!cache) {
    cache = Promise.all(["forecast.json", "scorecard.json"].map((f) => fetch(dataUrl(f)).then((r) => (r.ok ? r.json() : null))))
      .then(([forecast, scorecard]) => ({ forecast, scorecard, error: null }))
      .catch((e) => { cache = null; return { forecast: null, scorecard: null, error: String(e) }; });
  }
  return cache;
}

/** Forecast and back-test outputs; null when the files are not built yet. */
export function useProof(): S & { loading: boolean } {
  const [s, setS] = useState<S & { loading: boolean }>({ forecast: null, scorecard: null, error: null, loading: true });
  useEffect(() => { load().then((v) => setS({ ...v, loading: false })); }, []);
  return s;
}

export const OUTCOME: Record<Outcome, { label: string; pill: string; note: string }> = {
  warned: { label: "Warned before", pill: "green", note: "A nearby stretch was flagged on a pass before the reported date." },
  late: { label: "Flagged after", pill: "amber", note: "A nearby stretch was flagged, but only after the reported date." },
  missed: { label: "Missed", pill: "red", note: "A measured stretch is nearby but was never flagged." },
  off_bank: { label: "Not on a watched bank", pill: "grey", note: "No measured outer-bank stretch near the place: usually a char island, which version 1 does not watch." },
  unscorable: { label: "Place not pinned", pill: "grey", note: "The place is not pinned to a village yet; a union is too large to match a 500 m stretch." },
  too_early: { label: "Before season", pill: "grey", note: "Happened before the second pass, the earliest any warning could exist." },
};
