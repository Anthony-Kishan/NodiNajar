/* NodiNajar demo: before/after radar swipe, risk cells, Bangla alert.
   Reads window.DEMO from demo_fixtures/demo_data.js (built by src/pipeline/build_demo.py).
   Every number shown comes from that file. Nothing here computes science. */
(function () {
  const D = window.DEMO;
  if (!D) { document.getElementById('badge').textContent = 'No demo data: run python -m src.pipeline.build_demo'; return; }
  const S = D.stats, scenes = S.scenes, corners = S.image_corners;
  const $ = (id) => document.getElementById(id);
  const bnDigits = (s) => String(s).replace(/[0-9]/g, (d) => '০১২৩৪৫৬৭৮৯'[d]);
  const fmt = (n) => Number(n).toLocaleString('en-US', { maximumFractionDigits: 1 });
  const fmtDate = (iso) => new Date(iso + 'T00:00:00Z').toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });

  // ---- header badge: honesty first
  const badge = $('badge');
  badge.textContent = S.label;
  badge.className = 'badge ' + (S.mode === 'synthetic' ? 'synthetic' : 'provisional');
  $('dataCredit').textContent = S.mode === 'synthetic'
    ? 'Data: SYNTHETIC test scenes shaped like NISAR GCOV (not real observations)'
    : 'Data: NASA-ISRO NISAR L-band GCOV via NASA ASF DAAC (provisional)';

  // ---- totals
  $('tLost').textContent = fmt(S.totals.land_lost_ha);
  $('tRetreat').textContent = fmt(S.totals.max_retreat_m);
  $('tRed').textContent = S.totals.cells_red;
  $('tHomes').textContent = S.totals.homes_near_new_bank;

  // ---- date pickers
  const opts = scenes.map((s, i) => `<option value="${i}">${fmtDate(s.date)}</option>`).join('');
  $('selBefore').innerHTML = opts; $('selAfter').innerHTML = opts;
  $('selBefore').value = 0; $('selAfter').value = scenes.length - 1;

  // ---- maps
  const lons = corners.map((c) => c[0]), lats = corners.map((c) => c[1]);
  const bounds = [[Math.min(...lons), Math.min(...lats)], [Math.max(...lons), Math.max(...lats)]];
  const style = { version: 8, sources: {}, layers: [{ id: 'bg', type: 'background', paint: { 'background-color': '#0b1013' } }] };
  const mk = (id) => new maplibregl.Map({ container: id, style, bounds, fitBoundsOptions: { padding: 20 }, attributionControl: false, maxZoom: 16, dragRotate: false, pitchWithRotate: false });
  const before = mk('mapBefore'), after = mk('mapAfter');
  after.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
  after.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-right');

  // keep the two maps in step
  let syncing = false;
  const sync = (a, b) => a.on('move', () => { if (syncing) return; syncing = true; b.jumpTo({ center: a.getCenter(), zoom: a.getZoom() }); syncing = false; });
  sync(before, after); sync(after, before);

  const cellPaint = {
    fill: { 'fill-color': ['match', ['get', 'level'], 'red', '#d62f2f', 'amber', '#e39b17', '#3b8a5a'], 'fill-opacity': ['case', ['boolean', ['feature-state', 'sel'], false], 0.35, 0.12] },
    line: { 'line-color': ['match', ['get', 'level'], 'red', '#ff4d4d', 'amber', '#f2b233', '#5fb07f'], 'line-width': ['case', ['boolean', ['feature-state', 'sel'], false], 3, 1.4] },
  };
  const cells = { type: 'FeatureCollection', features: D.cells.features.filter((f) => f.properties.level !== 'green').map((f, i) => ({ ...f, id: i })) };

  function setup(map, idx, withLoss) {
    map.addSource('radar', { type: 'image', url: D.images[scenes[idx].image], coordinates: corners });
    map.addLayer({ id: 'radar', type: 'raster', source: 'radar', paint: { 'raster-fade-duration': 0, 'raster-resampling': 'nearest' } });
    if (withLoss) {
      map.addSource('loss', { type: 'image', url: D.images['loss.png'], coordinates: corners });
      map.addLayer({ id: 'loss', type: 'raster', source: 'loss', paint: { 'raster-opacity': 0.9, 'raster-resampling': 'nearest' } });
    }
    map.addSource('cells', { type: 'geojson', data: cells });
    map.addLayer({ id: 'cells-fill', type: 'fill', source: 'cells', paint: cellPaint.fill });
    map.addLayer({ id: 'cells-line', type: 'line', source: 'cells', paint: cellPaint.line });
    map.addSource('homes', { type: 'geojson', data: D.homes });
    map.addLayer({ id: 'homes', type: 'circle', source: 'homes', paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 9, 1.5, 14, 5], 'circle-color': '#ffd166', 'circle-stroke-color': '#3a2a00', 'circle-stroke-width': 0.6 } });
    map.on('click', 'cells-fill', (e) => select(e.features[0].id));
    map.on('mouseenter', 'cells-fill', () => { map.getCanvas().style.cursor = 'pointer'; });
    map.on('mouseleave', 'cells-fill', () => { map.getCanvas().style.cursor = ''; });
  }
  let ready = 0;
  const onReady = () => { if (++ready === 2) { labels(); if (cells.features.length) select(0, true); } };
  before.on('load', () => { setup(before, 0, false); onReady(); });
  after.on('load', () => { setup(after, scenes.length - 1, true); onReady(); });

  function labels() {
    $('labelBefore').textContent = fmtDate(scenes[+$('selBefore').value].date);
    $('labelAfter').textContent = fmtDate(scenes[+$('selAfter').value].date) + ' · red = land lost';
  }
  $('selBefore').onchange = (e) => { before.getSource('radar').updateImage({ url: D.images[scenes[+e.target.value].image], coordinates: corners }); labels(); };
  $('selAfter').onchange = (e) => { after.getSource('radar').updateImage({ url: D.images[scenes[+e.target.value].image], coordinates: corners }); labels(); };

  // ---- swipe divider
  const wrap = document.querySelector('.mapwrap'), div = $('divider');
  function setSwipe(pct) {
    pct = Math.max(0, Math.min(100, pct));
    div.style.left = pct + '%';
    $('mapAfter').style.clipPath = `inset(0 0 0 ${pct}%)`;
    div.setAttribute('aria-valuenow', Math.round(pct));
  }
  let dragging = false;
  div.addEventListener('pointerdown', (e) => { dragging = true; div.setPointerCapture(e.pointerId); });
  div.addEventListener('pointermove', (e) => { if (!dragging) return; const r = wrap.getBoundingClientRect(); setSwipe(((e.clientX - r.left) / r.width) * 100); });
  div.addEventListener('pointerup', () => { dragging = false; });
  div.addEventListener('keydown', (e) => { const v = parseFloat(div.style.left || '50'); if (e.key === 'ArrowLeft') setSwipe(v - 5); if (e.key === 'ArrowRight') setSwipe(v + 5); });

  // ---- cell detail, sparkline and alert
  let selected = null;
  function select(id, fly) {
    [before, after].forEach((m) => {
      if (selected !== null) m.setFeatureState({ source: 'cells', id: selected }, { sel: false });
      m.setFeatureState({ source: 'cells', id }, { sel: true });
    });
    selected = id;
    const p = cells.features[id].properties;
    if (fly) after.flyTo({ center: p.centre, zoom: 12.3, duration: 0 });
    const first = scenes[0].date, last = scenes[scenes.length - 1].date;
    $('cellBox').innerHTML = `
      <h2>Cell ${p.id}${p.side ? ` · ${p.side} bank` : ''}<span class="lvl ${p.level}">${p.level === 'red' ? 'high risk' : p.level === 'amber' ? 'watch' : 'low'}</span></h2>
      <div class="big">${fmt(p.retreat_m)} m</div>
      <p class="muted">Bank moved between ${fmtDate(first)} and ${fmtDate(last)} (${S.period_days} days). ${fmt(p.lost_ha)} ha of land lost in this cell. <b>${p.homes_near}</b> homes within ${S.method.near_m} m of the new bank.</p>
      ${spark(p.history_m)}
      <p class="muted small">${p.centre[1].toFixed(4)}° N, ${p.centre[0].toFixed(4)}° E</p>`;
    alertText(p);
  }

  function spark(vals) {
    const W = 320, H = 132, L = 34, R = 8, T = 24, B = 24;
    const max = Math.max(50, ...vals.filter((v) => v != null)), n = vals.length;
    // x is placed by real date, so a missed pass shows as a wider gap
    const t = scenes.map((s) => Date.parse(s.date)), t0 = t[0], span = Math.max(1, t[n - 1] - t0);
    const X = (i) => L + ((t[i] - t0) / span) * (W - L - R), Y = (v) => T + (1 - v / max) * (H - T - B);
    // null = no reliable bank position on that pass (channel switch); leave a gap, never draw a guess
    const pts = vals.map((v, i) => (v == null ? null : `${X(i).toFixed(1)},${Y(v).toFixed(1)}`)).filter(Boolean).join(' ');
    const ticks = [0, Math.round(max / 2), Math.round(max)];
    return `<svg class="spark" viewBox="0 0 ${W} ${H}" role="img" aria-label="Bank retreat by radar pass">
      ${ticks.map((t) => `<line x1="${L}" x2="${W - R}" y1="${Y(t)}" y2="${Y(t)}" stroke="currentColor" stroke-opacity=".12"/><text x="${L - 6}" y="${Y(t) + 4}" font-size="10" text-anchor="end" fill="currentColor" fill-opacity=".6">${t}</text>`).join('')}
      <polyline points="${pts}" fill="none" stroke="#d62f2f" stroke-width="2"/>
      ${vals.map((v, i) => (v == null ? '' : `<circle cx="${X(i)}" cy="${Y(v)}" r="3" fill="#d62f2f"><title>${fmtDate(scenes[i].date)}: ${fmt(v)} m</title></circle>`)).join('')}
      <text x="${L}" y="${H - 6}" font-size="10" fill="currentColor" fill-opacity=".6">${fmtDate(scenes[0].date)}</text>
      <text x="${W - R}" y="${H - 6}" font-size="10" text-anchor="end" fill="currentColor" fill-opacity=".6">${fmtDate(scenes[n - 1].date)}</text>
      <text x="${L}" y="${T - 12}" font-size="10" fill="currentColor" fill-opacity=".6">retreat (m), one point per radar pass</text>
    </svg>`;
  }

  function alertText(p) {
    if (p.level === 'green') { $('phone').hidden = true; return; }
    $('phone').hidden = false;
    const lvlBn = p.level === 'red' ? 'উচ্চ' : 'মাঝারি';
    const lvlEn = p.level === 'red' ? 'HIGH' : 'MEDIUM';
    $('msgBn').textContent = `নদীনজর সতর্কবার্তা: গত ${bnDigits(S.period_days)} দিনে আপনার এলাকায় (${p.id}) যমুনার পাড় ${bnDigits(Math.round(p.retreat_m))} মিটার সরে এসেছে। ভাঙনের ঝুঁকি: ${lvlBn}। মূল্যবান জিনিস ও গবাদিপশু নিরাপদ স্থানে সরানোর প্রস্তুতি নিন এবং ইউনিয়ন পরিষদের সাথে যোগাযোগ করুন।`;
    $('msgEn').textContent = `NodiNajar alert: in the last ${S.period_days} days the Jamuna bank near you (${p.id}) moved ${Math.round(p.retreat_m)} m. Erosion risk: ${lvlEn}. Prepare to move valuables and livestock to safety and contact your union parishad.`;
  }

  $('speak').onclick = () => {
    if (!('speechSynthesis' in window)) { alert('This browser cannot play voice.'); return; }
    const u = new SpeechSynthesisUtterance($('msgBn').textContent);
    const v = speechSynthesis.getVoices().find((x) => x.lang && x.lang.toLowerCase().startsWith('bn'));
    if (v) { u.voice = v; u.lang = v.lang; } else { u.lang = 'bn-BD'; }
    if (!v) $('speak').textContent = 'No Bangla voice installed';
    speechSynthesis.cancel(); speechSynthesis.speak(u);
  };

  // ---- methods / provenance drawer
  const rows = [
    ['Data', S.mode === 'synthetic' ? 'SYNTHETIC test scenes (not real)' : 'NISAR L-band L2 GCOV, PROVISIONAL'],
    ['Dates', `${scenes.length} passes, ${fmtDate(scenes[0].date)} to ${fmtDate(scenes[scenes.length - 1].date)}`],
    ['Granules', scenes.map((s) => s.granule).join('<br>')],
    ['Polarisation', scenes[0].pol],
    ['Pixel size', `${S.pixel_m} m (EPSG:${S.epsg})`],
    ['Speckle filter', S.method.speckle_filter],
    ['Water rule', `${S.method.water_rule}. Thresholds used: ${scenes.map((s) => s.threshold_db).join(', ')} dB`],
    ['Land lost', S.lost_rule],
    ['Retreat', S.method.retreat],
    ['Risk rule', S.method.risk_rule],
    ['Homes', S.homes_source],
    ['Uncertainty', S.method.uncertainty],
  ];
  $('methods').innerHTML = `<table>${rows.map((r) => `<tr><td>${r[0]}</td><td>${r[1]}</td></tr>`).join('')}</table>
    <p class="muted small">Raw output behind every number (stats.json):</p><pre>${JSON.stringify(S, null, 2).replace(/</g, '&lt;')}</pre>`;
})();
