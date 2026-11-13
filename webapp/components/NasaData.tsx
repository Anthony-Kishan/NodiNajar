import { NASA_DATA } from "@/lib/nasaData";

/** The NASA datasets behind the app, each with what it does here. */
export function NasaDataCard({ compact = false }: { compact?: boolean }) {
  return (
    <div className="card nasa-card">
      <div className="card-head">
        <div>
          <h3>NASA data in NodiNajar</h3>
          {!compact && <p className="sub">Every number on this site starts from NASA open data.</p>}
        </div>
        <span className="badge">NASA OPEN DATA</span>
      </div>
      <ul className="nasa-list">
        {NASA_DATA.map((d) => (
          <li key={d.name}>
            <a href={d.url} target="_blank" rel="noreferrer"><b>{d.name}</b></a>
            <span className="dim"> · {d.from}</span>
            <div className="muted">{d.role}</div>
          </li>
        ))}
      </ul>
    </div>
  );
}
