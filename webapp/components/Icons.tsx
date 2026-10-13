import type { SVGProps } from "react";
const base = (p: SVGProps<SVGSVGElement>) => ({ width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor",
  strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, ...p });
export const IconGrid = (p: SVGProps<SVGSVGElement>) => <svg {...base(p)}><rect x="3" y="3" width="7" height="9" rx="2"/><rect x="14" y="3" width="7" height="5" rx="2"/><rect x="14" y="12" width="7" height="9" rx="2"/><rect x="3" y="16" width="7" height="5" rx="2"/></svg>;
export const IconMap = (p: SVGProps<SVGSVGElement>) => <svg {...base(p)}><path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2Z"/><path d="M9 4v14M15 6v14"/></svg>;
export const IconWaves = (p: SVGProps<SVGSVGElement>) => <svg {...base(p)}><path d="M3 8c3-2 6 2 9 0s6 2 9 0M3 13c3-2 6 2 9 0s6 2 9 0M3 18c3-2 6 2 9 0s6 2 9 0"/></svg>;
export const IconSat = (p: SVGProps<SVGSVGElement>) => <svg {...base(p)}><path d="m13 7 4-4 4 4-4 4zM3 17l4-4 4 4-4 4z"/><path d="m9 15 6-6M15 21a6 6 0 0 0 6-6M15 17a2 2 0 0 0 2-2"/></svg>;
export const IconBell = (p: SVGProps<SVGSVGElement>) => <svg {...base(p)}><path d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0"/></svg>;
export const IconShield = (p: SVGProps<SVGSVGElement>) => <svg {...base(p)}><path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/></svg>;
export const IconBook = (p: SVGProps<SVGSVGElement>) => <svg {...base(p)}><path d="M4 5a2 2 0 0 1 2-2h14v16H6a2 2 0 0 0-2 2z"/><path d="M4 19V5M8 7h8"/></svg>;
export const IconPlay = (p: SVGProps<SVGSVGElement>) => <svg {...base({ ...p, fill: "currentColor", stroke: "none" })}><path d="M8 5v14l11-7z"/></svg>;
export const IconPause = (p: SVGProps<SVGSVGElement>) => <svg {...base({ ...p, fill: "currentColor", stroke: "none" })}><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>;
export const IconLayers = (p: SVGProps<SVGSVGElement>) => <svg {...base(p)}><path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/></svg>;
export const IconX = (p: SVGProps<SVGSVGElement>) => <svg {...base(p)}><path d="M6 6l12 12M18 6 6 18"/></svg>;
export const IconDownload = (p: SVGProps<SVGSVGElement>) => <svg {...base(p)}><path d="M12 4v11m0 0-4-4m4 4 4-4M5 20h14"/></svg>;
export const Mark = ({ size = 36 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden="true">
    <circle cx="20" cy="20" r="18" fill="none" stroke="#e8eef1" strokeWidth="1.5" opacity=".35" />
    <path d="M15 4c6 6-4 10 2 16s-3 11 3 16" fill="none" stroke="#57b8c9" strokeWidth="3" strokeLinecap="round" />
    <circle cx="26" cy="15" r="2.6" fill="#e5533d" />
  </svg>
);
