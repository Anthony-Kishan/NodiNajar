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
];
