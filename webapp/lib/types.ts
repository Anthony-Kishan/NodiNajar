export type Level = "red" | "amber" | "green";
export type LngLat = [number, number];

export interface Pass {
  index: number;
  date: string;               // YYYY-MM-DD
  granule: string;
  pol: string;
  threshold_db: number;
  threshold_from: string;
  water_km2: number;
  radar: string;
  thumb: string;
  water: string | null;
  px: [number, number];
}

export interface Manifest {
  label: string;
  mode: "nisar" | "synthetic";
  generated_utc: string;
  aoi_bbox: [number, number, number, number];
  corners: [LngLat, LngLat, LngLat, LngLat];
  pixel_m: number;
  display_step: number;
  period_days: number;
  totals: { land_lost_ha: number; max_retreat_m: number; cells_red: number; cells_amber: number; homes_near_new_bank: number };
  segments: { ok: number; jump: number; gap: number } | null;
  method: Record<string, string | number>;
  lost_rule: string;
  homes_source: string;
  track: { repeat_days: number; track: number; frame: number; direction: string } | null;
  passes: Pass[];
  loss: string;
  files: { segments: string; homes: string; banklines: string | null; csv: string };
}

export interface SegmentProps {
  id: string;
  rank: number;
  level: Level;
  side: "west" | "east";
  lost_ha: number;
  retreat_m: number;
  history_m: (number | null)[];
  homes_near: number;
  centre: LngLat;
}

export interface Feature<G, P> { type: "Feature"; geometry: G; properties: P }
export interface FC<G, P> { type: "FeatureCollection"; features: Feature<G, P>[] }
export type Segments = FC<{ type: "Polygon"; coordinates: LngLat[][] }, SegmentProps>;
export type Homes = FC<{ type: "Point"; coordinates: LngLat }, Record<string, never>>;
export type Banklines = FC<{ type: "LineString"; coordinates: LngLat[] }, { pass: number; date: string; side: "west" | "east" }>;

export interface RiverData {
  manifest: Manifest;
  segments: Segments;
  homes: Homes;
  banklines: Banklines | null;
}
