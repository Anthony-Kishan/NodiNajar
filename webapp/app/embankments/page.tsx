import { Footer } from "@/components/Shell";

export default function Embankments() {
  return (
    <>
      <main className="page">
        <div className="page-head">
          <div>
            <h2>Embankments <span className="pill blue" style={{ verticalAlign: "middle", marginLeft: 8 }}>Engine 2 · in development</span></h2>
            <p>An embankment rarely fails without warning. It sinks, slides or seeps first, a few millimetres at a time. NISAR can measure that movement from orbit along the whole length, every 12 days.</p>
          </div>
        </div>
        <div className="grid g-2">
          <div className="card">
            <h3>What this tab will show</h3>
            <ol className="steps" style={{ marginTop: 12 }}>
              <li><span><b>Ground movement along each embankment</b><span className="muted">Millimetres of sinking per pass from NISAR interferometry (GUNW products), low-coherence pixels masked.</span></span></li>
              <li><span><b>Sections sinking faster than their neighbours</b><span className="muted">Red: at least twice the neighbouring median and the river within 200 m. Amber: faster than neighbours, river farther away.</span></span></li>
              <li><span><b>River closing in</b><span className="muted">The erosion engine already measures the bank; when the bank reaches an embankment, that section scores higher.</span></span></li>
            </ol>
          </div>
          <div className="card">
            <h3>Why there is no map here yet</h3>
            <p className="muted">We show only measured numbers. The embankment engine needs a stack of NISAR GUNW interferograms over the Jamuna embankments, which we have not processed yet. Until then this page stays empty rather than showing invented values.</p>
            <div className="ctrl-title">Next steps</div>
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              <li>Download NISAR GUNW for track 69 over the Brahmaputra Right Embankment</li>
              <li>Build the deformation time series (MintPy, or our own stack)</li>
              <li>Test on the Muhuri embankment in Feni before the July 2025 breaches (Sentinel-1)</li>
            </ul>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
