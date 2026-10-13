"use client";
import { useEffect, useRef, useState } from "react";
import maplibregl, { type ImageSource, type Map as MLMap } from "maplibre-gl";
import { basemapStyle, type BasemapId } from "@/lib/basemaps";
import { dataUrl } from "@/lib/data";
import { fmtDate } from "@/lib/format";
import type { RiverData } from "@/lib/types";

interface Props {
  data: RiverData;
  /** The main (after) map; this component follows its camera. */
  main: MLMap;
  beforeIndex: number;
  afterIndex: number;
  basemap: BasemapId;
  radarOpacity: number;
  showWater: boolean;
}

/**
 * Before/after swipe: a second map showing the "before" pass sits over the main map and is clipped
 * to the left of a draggable divider. It takes no pointer input; it copies the main map's camera.
 */
export default function CompareMap(p: Props) {
  const el = useRef<HTMLDivElement>(null);
  const shell = useRef<HTMLDivElement>(null);
  const map = useRef<MLMap | null>(null);
  const props = useRef(p);
  props.current = p;
  const [x, setX] = useState(0.5);
  const dragging = useRef(false);
  const corners = p.data.manifest.corners;
  const passes = p.data.manifest.passes;

  function addOverlays(m: MLMap) {
    const cur = props.current;
    const pass = passes[cur.beforeIndex];
    if (!m.getSource("radar")) m.addSource("radar", { type: "image", url: dataUrl(pass.radar), coordinates: corners });
    if (!m.getLayer("radar")) m.addLayer({ id: "radar", type: "raster", source: "radar", paint: { "raster-opacity": cur.radarOpacity, "raster-fade-duration": 0, "raster-contrast": 0.15 } });
    if (pass.water && !m.getSource("water")) m.addSource("water", { type: "image", url: dataUrl(pass.water), coordinates: corners });
    if (pass.water && !m.getLayer("water")) m.addLayer({ id: "water", type: "raster", source: "water", paint: { "raster-opacity": cur.showWater ? 0.9 : 0, "raster-fade-duration": 0 } });
  }

  function follow() {
    const m = map.current, src = props.current.main;
    if (!m) return;
    m.jumpTo({ center: src.getCenter(), zoom: src.getZoom(), bearing: src.getBearing(), pitch: src.getPitch() });
  }

  useEffect(() => {
    if (!el.current) return;
    const src = p.main;
    const m = new maplibregl.Map({
      container: el.current, style: basemapStyle(p.basemap), interactive: false, attributionControl: false,
      center: src.getCenter(), zoom: src.getZoom(), bearing: src.getBearing(), pitch: src.getPitch(), maxPitch: 75,
    });
    map.current = m;
    m.on("style.load", () => addOverlays(m));
    src.on("move", follow);
    const ro = new ResizeObserver(() => m.resize());
    ro.observe(el.current);
    return () => { src.off("move", follow); ro.disconnect(); m.remove(); map.current = null; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [p.main]);

  // before pass, opacity and water toggles
  useEffect(() => {
    const m = map.current;
    if (!m || !m.getLayer("radar")) return;
    const pass = passes[p.beforeIndex];
    (m.getSource("radar") as ImageSource).updateImage({ url: dataUrl(pass.radar), coordinates: corners });
    if (pass.water && m.getSource("water")) (m.getSource("water") as ImageSource).updateImage({ url: dataUrl(pass.water), coordinates: corners });
    m.setPaintProperty("radar", "raster-opacity", p.radarOpacity);
    if (m.getLayer("water")) m.setPaintProperty("water", "raster-opacity", p.showWater ? 0.9 : 0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [p.beforeIndex, p.radarOpacity, p.showWater]);

  // basemap
  const lastBase = useRef(p.basemap);
  useEffect(() => {
    const m = map.current;
    if (!m || lastBase.current === p.basemap) return;
    lastBase.current = p.basemap;
    m.setStyle(basemapStyle(p.basemap));
  }, [p.basemap]);

  // divider dragging (mouse, touch, pen) and keyboard
  useEffect(() => {
    const move = (e: PointerEvent) => {
      if (!dragging.current || !shell.current) return;
      const r = shell.current.getBoundingClientRect();
      setX(Math.min(0.98, Math.max(0.02, (e.clientX - r.left) / r.width)));
    };
    const up = () => { dragging.current = false; };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
    return () => { window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up); };
  }, []);

  const pct = `${(x * 100).toFixed(2)}%`;
  return (
    <div ref={shell} className="compare-shell" aria-hidden={false}>
      <div ref={el} className="compare-map" style={{ clipPath: `inset(0 calc(100% - ${pct}) 0 0)` }} />
      <div className="compare-divider" style={{ left: pct }}>
        <button type="button" className="compare-handle" role="slider" aria-label="Drag to compare before and after"
          aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(x * 100)}
          onPointerDown={(e) => { dragging.current = true; (e.target as HTMLElement).setPointerCapture?.(e.pointerId); e.preventDefault(); }}
          onKeyDown={(e) => {
            if (e.key === "ArrowLeft") { e.preventDefault(); e.stopPropagation(); setX((v) => Math.max(0.02, v - 0.04)); }
            if (e.key === "ArrowRight") { e.preventDefault(); e.stopPropagation(); setX((v) => Math.min(0.98, v + 0.04)); }
          }}>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M9 6l-6 6 6 6M15 6l6 6-6 6" /></svg>
        </button>
      </div>
      <div className="compare-tag left" style={{ right: `calc(100% - ${pct} + 12px)` }}>Before · {fmtDate(passes[p.beforeIndex].date, true)}</div>
      <div className="compare-tag right" style={{ left: `calc(${pct} + 12px)` }}>After · {fmtDate(passes[p.afterIndex].date, true)}</div>
    </div>
  );
}
