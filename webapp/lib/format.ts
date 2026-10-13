const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
export const DAY_MS = 86_400_000;

export function parseDate(d: string): Date {
  const [y, m, dd] = d.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, dd));
}
export function fmtDate(d: string | Date, withYear = false): string {
  const x = typeof d === "string" ? parseDate(d) : d;
  return `${x.getUTCDate()} ${MONTHS[x.getUTCMonth()]}${withYear ? " " + x.getUTCFullYear() : ""}`;
}
export function isoDate(x: Date): string {
  return x.toISOString().slice(0, 10);
}
export const nf = (v: number, digits = 0) =>
  v.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
export const bnDigits = (s: string | number) => String(s).replace(/[0-9]/g, (d) => "০১২৩৪৫৬৭৮৯"[Number(d)]);
export const latStr = (lat: number) => `${lat.toFixed(3)}° N`;
export const lonStr = (lon: number) => `${lon.toFixed(3)}° E`;
export const levelName = { red: "High risk", amber: "Watch", green: "Stable" } as const;
