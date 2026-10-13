import type { StyleSpecification } from "maplibre-gl";

export type BasemapId = "satellite" | "sentinel" | "terrain" | "streets" | "dark";

export const BASEMAPS: { id: BasemapId; name: string; note: string }[] = [
  { id: "satellite", name: "Satellite", note: "Esri World Imagery, high-resolution photos" },
  { id: "sentinel", name: "Sentinel-2", note: "EOX Sentinel-2 cloudless 2025, true colour" },
  { id: "terrain", name: "Terrain", note: "Shaded relief from open elevation tiles" },
  { id: "streets", name: "Streets", note: "CARTO Voyager on OpenStreetMap" },
  { id: "dark", name: "Dark", note: "CARTO Dark Matter on OpenStreetMap" },
];

const carto = (style: string) => ["a", "b", "c", "d"].map((s) => `https://${s}.basemaps.cartocdn.com/rastertiles/${style}/{z}/{x}/{y}@2x.png`);
const CARTO_ATTR = '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="https://carto.com/attributions">CARTO</a>';
const DEM = {
  type: "raster-dem" as const,
  tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
  encoding: "terrarium" as const,
  tileSize: 256,
  maxzoom: 14,
  attribution: "Elevation: Mapzen Terrain Tiles (AWS Open Data)",
};

/** Raster-only styles (no fonts or sprites needed), each with a DEM source for hillshade and 3D terrain. */
export function basemapStyle(id: BasemapId): StyleSpecification {
  const sources: StyleSpecification["sources"] = { dem: DEM };
  const layers: StyleSpecification["layers"] = [{ id: "bg", type: "background", paint: { "background-color": "#0b161d" } }];
  const raster = (key: string, tiles: string[], attribution: string, maxzoom = 19, paint: Record<string, unknown> = {}) => {
    sources[key] = { type: "raster", tiles, tileSize: 256, maxzoom, attribution };
    layers.push({ id: key, type: "raster", source: key, paint });
  };
  if (id === "satellite") {
    raster("imagery", ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
      "Imagery © Esri, Maxar, Earthstar Geographics", 19, { "raster-saturation": -0.1 });
    raster("labels", carto("dark_only_labels"), CARTO_ATTR);
  } else if (id === "sentinel") {
    raster("imagery", ["https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2025_3857/default/g/{z}/{y}/{x}.jpg"],
      '<a href="https://s2maps.eu">Sentinel-2 cloudless 2025</a> by EOX (Copernicus Sentinel data 2025), CC BY-NC-SA 4.0', 15);
    raster("labels", carto("dark_only_labels"), CARTO_ATTR);
  } else if (id === "terrain") {
    raster("base", carto("voyager_nolabels"), CARTO_ATTR, 20, { "raster-opacity": 0.85 });
    layers.push({ id: "hillshade", type: "hillshade", source: "dem",
      paint: { "hillshade-exaggeration": 0.9, "hillshade-shadow-color": "#2b3a42", "hillshade-highlight-color": "#ffffff" } });
    raster("labels", carto("voyager_only_labels"), CARTO_ATTR);
  } else if (id === "streets") {
    raster("base", carto("voyager"), CARTO_ATTR);
  } else {
    raster("base", carto("dark_all"), CARTO_ATTR);
  }
  return { version: 8, sources, layers };
}
