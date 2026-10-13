"use client";
import { useEffect, useRef } from "react";
import maplibregl, { type ImageSource, type Map as MLMap } from "maplibre-gl";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { ColumnLayer, GeoJsonLayer, PathLayer, ScatterplotLayer } from "@deck.gl/layers";
import type { PickingInfo } from "@deck.gl/core";
import { basemapStyle, type BasemapId } from "@/lib/basemaps";
import { dataUrl } from "@/lib/data";
import type { Feature, Level, RiverData, SegmentProps } from "@/lib/types";
import type { MapLayers } from "@/lib/mapLayers";


const LEVEL_RGB: Record<Level, [number, number, number]> = { red: [229, 83, 61], amber: [233, 169, 59], green: [108, 194, 143] };

interface Props {
  data: RiverData;
  passIndex: number;
  basemap: BasemapId;
  layers: MapLayers;
  radarOpacity: number;
  threeD: boolean;
  selectedId: string | null;
  onSelect?: (id: string | null) => void;
  /** Called once the map exists, so a before/after compare map can follow its camera. */
  onMapReady?: (m: MLMap | null) => void;
  compact?: boolean;
  className?: string;
}

type SegFeature = Feature<{ type: "Polygon"; coordinates: [number, number][][] }, SegmentProps>;

export default function RiverMap(p: Props) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<MLMap | null>(null);
  const overlay = useRef<MapboxOverlay | null>(null);
  const ready = useRef(false);
  const front = useRef<"A" | "B">("A");
  const shownPass = useRef<number>(-1);
  const props = useRef(p);
  props.current = p;

  const corners = p.data.manifest.corners;
  const passes = p.data.manifest.passes;

  /** Radar (two layers for cross-fading), water mask and land-lost overlays; re-added after every style change. */
  function addOverlays(m: MLMap) {
    const cur = props.current;
    const url = (i: number) => dataUrl(passes[i].radar);
    for (const k of ["A", "B"] as const) {
      if (!m.getSource(`radar${k}`)) m.addSource(`radar${k}`, { type: "image", url: url(cur.passIndex), coordinates: corners });
      if (!m.getLayer(`radar${k}`)) m.addLayer({ id: `radar${k}`, type: "raster", source: `radar${k}`,
        paint: { "raster-opacity": 0, "raster-opacity-transition": { duration: 650, delay: 0 }, "raster-fade-duration": 0, "raster-contrast": 0.15 } });
    }
    const w = passes[cur.passIndex].water;
    if (w && !m.getSource("water")) m.addSource("water", { type: "image", url: dataUrl(w), coordinates: corners });
    if (w && !m.getLayer("water")) m.addLayer({ id: "water", type: "raster", source: "water", paint: { "raster-opacity": 0, "raster-fade-duration": 0 } });
    if (!m.getSource("loss")) m.addSource("loss", { type: "image", url: dataUrl(p.data.manifest.loss), coordinates: corners });
    if (!m.getLayer("loss")) m.addLayer({ id: "loss", type: "raster", source: "loss", paint: { "raster-opacity": 0, "raster-fade-duration": 0 } });
    shownPass.current = -1;
    syncOverlays(m);
  }

  function syncOverlays(m: MLMap) {
    const cur = props.current;
    if (!m.getLayer("radarA")) return;
    const op = cur.layers.radar ? cur.radarOpacity : 0;
    if (shownPass.current !== cur.passIndex) {
      // load the new pass into the hidden layer, then cross-fade
      const next = front.current === "A" ? "B" : "A";
      const src = m.getSource(`radar${next}`) as ImageSource | undefined;
      src?.updateImage({ url: dataUrl(passes[cur.passIndex].radar), coordinates: corners });
      front.current = next;
      shownPass.current = cur.passIndex;
      const w = passes[cur.passIndex].water;
      if (w) (m.getSource("water") as ImageSource | undefined)?.updateImage({ url: dataUrl(w), coordinates: corners });
    }
    m.setPaintProperty(`radar${front.current}`, "raster-opacity", op);
    m.setPaintProperty(`radar${front.current === "A" ? "B" : "A"}`, "raster-opacity", 0);
    if (m.getLayer("water")) m.setPaintProperty("water", "raster-opacity", cur.layers.water ? 0.9 : 0);
    m.setPaintProperty("loss", "raster-opacity", cur.layers.loss ? 0.95 : 0);
  }

  function deckLayers() {
    const cur = props.current;
    const segs = cur.data.segments.features as SegFeature[];
    const sel = cur.selectedId;
    const out = [];
    if (cur.layers.segments) {
      out.push(new GeoJsonLayer<SegmentProps>({
        id: "segments", data: cur.data.segments as never, pickable: true, stroked: true, filled: true,
        getFillColor: (f) => [...LEVEL_RGB[f.properties.level], f.properties.id === sel ? 120 : 60] as [number, number, number, number],
        getLineColor: (f) => (f.properties.id === sel ? [255, 255, 255, 255] : [...LEVEL_RGB[f.properties.level], 230]) as [number, number, number, number],
        getLineWidth: (f) => (f.properties.id === sel ? 3 : 1.5), lineWidthUnits: "pixels",
        updateTriggers: { getFillColor: sel, getLineColor: sel, getLineWidth: sel },
      }));
      // always-visible markers at each stretch centre, so stretches read at any zoom
      out.push(new ScatterplotLayer<SegFeature>({
        id: "segment-dots", data: segs, pickable: true, getPosition: (f) => f.properties.centre,
        getRadius: (f) => (f.properties.level === "red" ? 260 : 170), radiusMinPixels: 4, radiusMaxPixels: 14,
        getFillColor: (f) => [...LEVEL_RGB[f.properties.level], 235] as [number, number, number, number],
        stroked: true, getLineColor: (f) => (f.properties.id === sel ? [255, 255, 255, 255] : [11, 22, 29, 220]) as [number, number, number, number],
        lineWidthMinPixels: 1.5, getLineWidth: (f) => (f.properties.id === sel ? 3 : 1.5), lineWidthUnits: "pixels",
        updateTriggers: { getLineColor: sel, getLineWidth: sel }, visible: !cur.threeD,
      }));
      if (cur.threeD) {
        out.push(new ColumnLayer<SegFeature>({
          id: "retreat-columns", data: segs, pickable: true, extruded: true, diskResolution: 24, radius: 170,
          getPosition: (f) => f.properties.centre, getElevation: (f) => f.properties.retreat_m * 9, elevationScale: 1,
          getFillColor: (f) => [...LEVEL_RGB[f.properties.level], f.properties.id === sel ? 255 : 215] as [number, number, number, number],
          material: { ambient: 0.5, diffuse: 0.6, shininess: 24 },
          transitions: { getElevation: 600 }, updateTriggers: { getFillColor: sel },
        }));
      }
    }
    if (cur.layers.homes) {
      out.push(new ScatterplotLayer({
        id: "homes", data: cur.data.homes.features, getPosition: (f: { geometry: { coordinates: [number, number] } }) => f.geometry.coordinates,
        getRadius: 16, radiusMinPixels: 1.6, radiusMaxPixels: 6, getFillColor: [246, 211, 101, 225], stroked: false,
      }));
    }
    const bl = cur.data.banklines;
    if (bl && cur.layers.banks) {
      const firstLines = bl.features.filter((f) => f.properties.pass === 0);
      const nowLines = bl.features.filter((f) => f.properties.pass === cur.passIndex);
      if (cur.layers.firstBank && cur.passIndex !== 0) {
        out.push(new PathLayer({ id: "bank-first", data: firstLines, getPath: (f: { geometry: { coordinates: [number, number][] } }) => f.geometry.coordinates,
          getColor: [255, 255, 255, 170], getWidth: 1.6, widthUnits: "pixels", jointRounded: true, capRounded: true }));
      }
      out.push(new PathLayer({ id: "bank-now", data: nowLines, getPath: (f: { geometry: { coordinates: [number, number][] } }) => f.geometry.coordinates,
        getColor: [87, 210, 230, 255], getWidth: 3, widthUnits: "pixels", jointRounded: true, capRounded: true,
        updateTriggers: { getPath: cur.passIndex } }));
    }
    return out;
  }

  // create the map once
  useEffect(() => {
    if (!el.current) return;
    const [w, s, e, n] = p.data.manifest.aoi_bbox;
    const m = new maplibregl.Map({
      container: el.current, style: basemapStyle(p.basemap), bounds: [[w, s], [e, n]],
      fitBoundsOptions: { padding: p.compact ? 20 : { top: 80, bottom: 140, left: 40, right: 40 } },
      attributionControl: { compact: true }, maxPitch: 75, dragRotate: !p.compact, cooperativeGestures: !!p.compact,
    });
    map.current = m;
    p.onMapReady?.(m);
    if (!p.compact) {
      m.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
      m.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-right");
      m.addControl(new maplibregl.FullscreenControl(), "top-right");
    }
    const ov = new MapboxOverlay({
      interleaved: false, layers: [],
      onClick: (info: PickingInfo) => {
        const f = info.object as SegFeature | undefined;
        props.current.onSelect?.(f?.properties?.id ?? null);
      },
      getTooltip: ({ object }: PickingInfo) => {
        const f = object as SegFeature | undefined;
        if (!f?.properties?.id) return null;
        const q = f.properties;
        return { html: `<b>${q.id}</b> · ${q.side} bank<br/>moved <b>${q.retreat_m} m</b> into the land<br/>${q.homes_near} homes within 200 m`,
          style: { background: "rgba(13,27,36,.95)", color: "#e8eef1", border: "1px solid #2f5163", borderRadius: "10px", fontSize: "12.5px", padding: "8px 10px", fontFamily: "Hind Siliguri, sans-serif" } };
      },
    });
    m.addControl(ov as unknown as maplibregl.IControl);
    overlay.current = ov;
    m.on("style.load", () => { addOverlays(m); applyTerrain(m); ready.current = true; ov.setProps({ layers: deckLayers() }); });
    return () => { ready.current = false; props.current.onMapReady?.(null); m.remove(); map.current = null; overlay.current = null; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function applyTerrain(m: MLMap) {
    const cur = props.current;
    try { m.setTerrain(cur.threeD ? { source: "dem", exaggeration: 12 } : null); } catch { /* DEM not reachable offline */ }
  }

  // basemap change
  const lastBase = useRef(p.basemap);
  useEffect(() => {
    const m = map.current;
    if (!m || lastBase.current === p.basemap) return;
    lastBase.current = p.basemap;
    ready.current = false;
    m.setStyle(basemapStyle(p.basemap));
  }, [p.basemap]);

  // overlays and deck layers follow props
  useEffect(() => {
    const m = map.current;
    if (m && ready.current) syncOverlays(m);
    overlay.current?.setProps({ layers: deckLayers() });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [p.passIndex, p.layers, p.radarOpacity, p.selectedId, p.threeD, p.data]);

  // 3D view
  useEffect(() => {
    const m = map.current;
    if (!m) return;
    if (ready.current) applyTerrain(m);
    m.easeTo({ pitch: p.threeD ? 58 : 0, bearing: p.threeD ? -18 : 0, duration: 900 });
  }, [p.threeD]);

  // fly to a selected stretch
  useEffect(() => {
    const m = map.current;
    if (!m || !p.selectedId) return;
    const f = (p.data.segments.features as SegFeature[]).find((x) => x.properties.id === p.selectedId);
    if (f) m.flyTo({ center: f.properties.centre, zoom: p.compact ? 11.5 : 13.2, speed: 1.2, essential: true });
  }, [p.selectedId, p.data, p.compact]);

  return <div ref={el} className={p.className ?? "map-el"} />;
}
