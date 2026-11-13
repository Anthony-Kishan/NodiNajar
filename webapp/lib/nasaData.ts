/**
 * NASA (and NASA-partner) datasets used in NodiNajar. Shown on Overview and Methods.
 * Add a row only when the data is actually used in the app; say plainly what it does.
 */
export interface NasaDataset {
  name: string;
  from: string;
  role: string;
  url: string;
}

export const NASA_DATA: NasaDataset[] = [
  {
    name: "NISAR L2 GCOV (HH), 8 passes",
    from: "NASA-ISRO NISAR, via NASA ASF DAAC",
    role: "L-band radar through monsoon cloud: water and land on every pass, the bank lines and how far they moved",
    url: "https://nisar-docs.asf.alaska.edu/gcov/",
  },
  {
    name: "VIIRS true colour, daily",
    from: "NASA GIBS (as in NASA Worldview)",
    role: "The “NASA daily” map: what an optical satellite saw on each pass date, usually cloud",
    url: "https://www.earthdata.nasa.gov/eosdis/science-system-description/eosdis-components/gibs",
  },
  {
    name: "OPERA DSWx-HLS surface water",
    from: "NASA JPL OPERA, via NASA GIBS (PO.DAAC archive)",
    role: "An independent water map from optical satellites, to check our NISAR water masks on clear days (Track record tab)",
    url: "https://www.jpl.nasa.gov/go/opera/products/dswx-product-suite/",
  },
  {
    name: "HLS, Harmonized Landsat and Sentinel-2",
    from: "NASA HLS v2.0, via NASA GIBS",
    role: "The optical side of the optical-and-radar swipe on the Live map: what a camera saw near each pass date",
    url: "https://www.earthdata.nasa.gov/data/projects/hls",
  },
  {
    name: "POWER daily precipitation",
    from: "NASA POWER (MERRA-2 and GEOS-IT)",
    role: "Rain before each pass at the box centre, on the Radar passes tab, for our hypotheses on what drives the river",
    url: "https://power.larc.nasa.gov/",
  },
];
