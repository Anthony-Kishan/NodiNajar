import { DAY_MS, isoDate, parseDate } from "./format";
import type { Manifest } from "./types";

export interface PlannedPass { date: string; status: "processed" | "expected-unprocessed" | "upcoming"; daysAway: number }

/**
 * NISAR repeats each track every 12 days. From the last processed pass we list the
 * dates the same track is expected again. These are a schedule, not observations:
 * the app labels them "expected" until the pipeline has processed a real granule.
 */
export function expectedPasses(m: Manifest, now: Date, ahead = 3): PlannedPass[] {
  const repeat = m.track?.repeat_days ?? 12;
  const last = parseDate(m.passes[m.passes.length - 1].date);
  const out: PlannedPass[] = [];
  for (let t = last.getTime() + repeat * DAY_MS, n = 0; n < 40; t += repeat * DAY_MS, n++) {
    const days = (t - now.getTime()) / DAY_MS;
    if (days < -1e-9) out.push({ date: isoDate(new Date(t)), status: "expected-unprocessed", daysAway: days });
    else {
      out.push({ date: isoDate(new Date(t)), status: "upcoming", daysAway: days });
      if (out.filter((p) => p.status === "upcoming").length >= ahead) break;
    }
  }
  return out;
}

export function nextPass(m: Manifest, now: Date): PlannedPass | undefined {
  return expectedPasses(m, now, 1).find((p) => p.status === "upcoming");
}

/** Gaps longer than one repeat between processed passes (a pass NISAR did not make or that is missing). */
export function gaps(m: Manifest): { from: string; to: string; days: number }[] {
  const repeat = m.track?.repeat_days ?? 12;
  const out = [];
  for (let i = 1; i < m.passes.length; i++) {
    const d = (parseDate(m.passes[i].date).getTime() - parseDate(m.passes[i - 1].date).getTime()) / DAY_MS;
    if (d > repeat + 1) out.push({ from: m.passes[i - 1].date, to: m.passes[i].date, days: d });
  }
  return out;
}
