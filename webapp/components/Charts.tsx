"use client";
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Line, LineChart, ReferenceArea, ReferenceLine,
  ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis,
} from "recharts";
import { fmtDate, parseDate } from "@/lib/format";
import type { Level, Pass, SegmentProps } from "@/lib/types";

const C = { grid: "#24404f", axis: "#93a9b4", water: "#57b8c9", red: "#e5533d", amber: "#e9a93b", green: "#6cc28f", home: "#f6d365" };
const LEVEL_C: Record<Level, string> = { red: C.red, amber: C.amber, green: C.green };
const tip = { contentStyle: { background: "rgba(13,27,36,.96)", border: "1px solid #2f5163", borderRadius: 10, color: "#e8eef1", fontSize: 12.5 },
  labelStyle: { color: "#93a9b4" }, itemStyle: { color: "#e8eef1" }, cursor: { stroke: "#2f5163" } };
const axis = { stroke: C.axis, tick: { fill: C.axis, fontSize: 11.5 }, tickLine: false, axisLine: { stroke: C.grid } };

/** Water in the box on each pass, by real date, with missing passes shaded. */
export function WaterChart({ passes, gaps, selected, height = 230 }: { passes: Pass[]; gaps: { from: string; to: string }[]; selected?: number; height?: number }) {
  const rows = passes.map((p) => ({ t: parseDate(p.date).getTime(), km2: p.water_km2, date: p.date }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={rows} margin={{ top: 10, right: 12, left: -6, bottom: 0 }}>
        <defs>
          <linearGradient id="wfill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={C.water} stopOpacity={0.55} />
            <stop offset="100%" stopColor={C.water} stopOpacity={0.04} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={C.grid} strokeDasharray="3 4" vertical={false} />
        {gaps.map((g) => (
          <ReferenceArea key={g.from} x1={parseDate(g.from).getTime()} x2={parseDate(g.to).getTime()} fill="#93a9b4" fillOpacity={0.07}
            label={{ value: "no pass", fill: "#6c8591", fontSize: 11, position: "insideTop" }} />
        ))}
        <XAxis dataKey="t" type="number" scale="time" domain={["dataMin", "dataMax"]} {...axis}
          tickFormatter={(t) => fmtDate(new Date(t))} ticks={rows.map((r) => r.t)} interval="preserveStartEnd" />
        <YAxis {...axis} width={48} tickFormatter={(v) => `${v}`} unit="" />
        <Tooltip {...tip} labelFormatter={(t) => fmtDate(new Date(Number(t)), true)} formatter={((v: number) => [`${v.toFixed(1)} km²`, "Water in box"]) as never} />
        {selected !== undefined && <ReferenceLine x={rows[selected]?.t} stroke="#e8eef1" strokeDasharray="4 4" />}
        <Area type="linear" dataKey="km2" stroke={C.water} strokeWidth={2.4} fill="url(#wfill)" isAnimationActive
          dot={{ r: 3.5, fill: C.water, stroke: "#0b161d", strokeWidth: 1.5 }} activeDot={{ r: 6 }} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

/** Bank position on each pass, metres into the land since the first pass. Missing passes break the line. */
export function RetreatChart({ dates, history, level, height = 200 }: { dates: string[]; history: (number | null)[]; level: Level; height?: number }) {
  const rows = dates.map((d, i) => ({ t: parseDate(d).getTime(), m: history[i] }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={rows} margin={{ top: 10, right: 12, left: -10, bottom: 0 }}>
        <CartesianGrid stroke={C.grid} strokeDasharray="3 4" vertical={false} />
        <XAxis dataKey="t" type="number" scale="time" domain={["dataMin", "dataMax"]} {...axis} tickFormatter={(t) => fmtDate(new Date(t))}
          ticks={[rows[0].t, rows[Math.floor(rows.length / 2)].t, rows[rows.length - 1].t]} />
        <YAxis {...axis} width={46} unit=" m" />
        <ReferenceLine y={0} stroke="#2f5163" />
        <Tooltip {...tip} labelFormatter={(t) => fmtDate(new Date(Number(t)), true)}
          formatter={((v: number | null) => [v === null ? "bank not measured" : `${v} m`, "Bank moved"]) as never} />
        <Line type="monotone" dataKey="m" stroke={LEVEL_C[level]} strokeWidth={2.6} connectNulls={false}
          dot={{ r: 3.5, fill: LEVEL_C[level], stroke: "#0b161d" }} activeDot={{ r: 6 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

/** Every measured stretch along the river: latitude (south to north) against retreat; bubble size = homes near. */
export function RiverProfile({ segs, onPick, height = 260 }: { segs: SegmentProps[]; onPick?: (id: string) => void; height?: number }) {
  const rows = segs.map((s) => ({ lat: s.centre[1], m: s.retreat_m, homes: Math.max(1, s.homes_near), id: s.id, level: s.level, side: s.side }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ScatterChart margin={{ top: 10, right: 16, left: -6, bottom: 0 }}>
        <CartesianGrid stroke={C.grid} strokeDasharray="3 4" />
        <XAxis dataKey="lat" type="number" domain={["dataMin - 0.02", "dataMax + 0.02"]} {...axis} tickFormatter={(v) => `${v.toFixed(2)}°N`} name="Latitude" />
        <YAxis dataKey="m" type="number" {...axis} width={50} unit=" m" name="Retreat" />
        <ZAxis dataKey="homes" range={[40, 520]} name="Homes" />
        <ReferenceLine y={100} stroke={C.red} strokeDasharray="5 5" label={{ value: "100 m", fill: "#ff8b78", fontSize: 11, position: "right" }} />
        <Tooltip {...tip} cursor={{ strokeDasharray: "3 3" }}
          formatter={((v: number, n: string) => (n === "Latitude" ? [`${v.toFixed(3)}° N`, n] : n === "Retreat" ? [`${v} m`, n] : [v, "Homes within 200 m"])) as never} />
        <Scatter data={rows} onClick={((d: { id?: string }) => d?.id && onPick?.(d.id)) as never} cursor="pointer">
          {rows.map((r) => <Cell key={r.id} fill={LEVEL_C[r.level]} fillOpacity={0.8} stroke="#0b161d" />)}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  );
}

/** Stretches by risk level on each bank. */
export function LevelBars({ segs, height = 200 }: { segs: SegmentProps[]; height?: number }) {
  const rows = (["west", "east"] as const).map((side) => ({
    side: side === "west" ? "West bank" : "East bank",
    red: segs.filter((s) => s.side === side && s.level === "red").length,
    amber: segs.filter((s) => s.side === side && s.level === "amber").length,
  }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 16, left: 10, bottom: 0 }} barSize={22}>
        <CartesianGrid stroke={C.grid} strokeDasharray="3 4" horizontal={false} />
        <XAxis type="number" {...axis} allowDecimals={false} />
        <YAxis type="category" dataKey="side" {...axis} width={78} />
        <Tooltip {...tip} cursor={{ fill: "rgba(87,184,201,.06)" }} />
        <Bar dataKey="red" stackId="a" name="High risk" fill={C.red} radius={[4, 0, 0, 4]} />
        <Bar dataKey="amber" stackId="a" name="Watch" fill={C.amber} radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
