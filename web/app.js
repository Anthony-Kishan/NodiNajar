/* NodiNajar demo: radar swipe through the monsoon, bank stretches ranked for action, Bangla alert.
   Reads window.DEMO from demo_fixtures/demo_data.js (built by src/pipeline/build_demo.py).
   Every number shown comes from that file. Nothing here computes science. */
(function () {
  'use strict';
  const D = window.DEMO;
  const $ = (id) => document.getElementById(id);
  if (!D) { $('badge').textContent = 'No data: run python -m src.pipeline.build_demo'; return; }

  const S = D.stats, scenes = S.scenes, corners = S.image_corners, last = scenes.length - 1;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const bn = (s) => String(s).replace(/[0-9]/g, (d) => '০১২৩৪৫৬৭৮৯'[d]);
  const fmt = (n) => Number(n).toLocaleString('en-US', { maximumFractionDigits: 1 });
  const dShort = (iso) => new Date(iso + 'T00:00:00Z').toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' });
  const dLong = (iso) => new Date(iso + 'T00:00:00Z').toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
  const words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'];
  const say = (n) => (n <= 10 ? words[n] : fmt(n));
  const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);

  // ---- honesty first: the data label never goes away
  const synthetic = S.mode === 'synthetic';
  $('badge').textContent = S.label;
  $('badge').className = 'badge ' + (synthetic ? 'synthetic' : 'provisional');
  $('credit').textContent = (synthetic
    ? 'Data: SYNTHETIC test scenes shaped like NISAR GCOV, not real observations.'
    : 'Data: NASA-ISRO NISAR L-band GCOV via NASA ASF DAAC, provisional.') +
    (S.homes_source && S.homes_source !== 'none' && !synthetic ? ' Buildings: Overture Maps (OpenStreetMap, Google Open Buildings, Microsoft).' : '') +
    ' Team AlphaMatrix, NASA Space Apps Challenge 2026, Dancing with the SARs. Apache-2.0.';

  // ---- the stretches that matter, ranked: high risk first, then by how far the bank moved
  const ranked = D.cells.features.filter((f) => f.properties.level !== 'green')
    .sort((a, b) => (b.properties.level === 'red') - (a.properties.level === 'red') || b.properties.retreat_m - a.properties.retreat_m);
  const cells = { type: 'FeatureCollection', features: ranked.map((f, i) => ({ ...f, id: i })) };
  const nRed = ranked.filter((f) => f.properties.level === 'red').length;
  const nAll = ranked.length;
  const homes = S.totals.homes_near_new_bank;

  $('season').innerHTML = nAll
    ? `From ${dShort(scenes[0].date)} to ${dShort(scenes[last].date)}, the Jamuna's outer banks moved into the land along <b class="a">${say(nAll)}</b> stretches of 500 m. ` +
      (nRed ? `<b class="r">${cap(say(nRed))}</b> of them are next to homes, and <b class="h">${fmt(homes)}</b> homes now stand within ${S.method.near_m} m of the new bank.`
            : `None of them has a mapped home within ${S.method.near_m} m yet.`)
    : `From ${dShort(scenes[0].date)} to ${dShort(scenes[last].date)}, no outer bank stretch moved 30 m or more.`;
  const seg = S.segments;
  $('coverage').textContent = seg
    ? `Measured ${seg.ok} of ${seg.ok + seg.jump + seg.gap} bank stretches on ${scenes.length} radar passes. ${seg.jump} were skipped where the outer bank switched channel, rather than guessed.`
    : `${scenes.length} radar passes.`;

  $('priority').innerHTML = ranked.map((f, i) => {
    const p = f.properties;
    const sub = p.homes_near ? `${p.homes_near} homes within ${S.method.near_m} m` : 'No mapped homes nearby';
    return `<li><button type="button" data-id="${i}">
      <span class="where"><i class="dot ${p.level}"></i>${cap(p.side || '')} bank, ${p.centre[1].toFixed(3)}° N</span>
      <span class="sub">${sub}</span>
      <span class="m">${fmt(p.retreat_m)}<small> m</small></span></button></li>`;
  }).join('');
  $('priority').addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) select(+b.dataset.id, true); });

  // ---- maps: one per side of the swipe, kept in step
  const lons = corners.map((c) => c[0]), lats = corners.map((c) => c[1]);
  const bounds = [[Math.min(...lons), Math.min(...lats)], [Math.max(...lons), Math.max(...lats)]];
  const style = { version: 8, sources: {}, layers: [{ id: 'bg', type: 'background', paint: { 'background-color': '#0B161D' } }] };
  const mk = (id) => new maplibregl.Map({ container: id, style, bounds, fitBoundsOptions: { padding: { top: 70, bottom: 30, left: 30, right: 30 } },
    attributionControl: false, maxZoom: 16, dragRotate: false, pitchWithRotate: false, touchPitch: false });
  const before = mk('mapBefore'), after = mk('mapAfter');
  after.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
  after.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-right');
  let syncing = false;
  const sync = (a, b) => a.on('move', () => { if (syncing) return; syncing = true; b.jumpTo({ center: a.getCenter(), zoom: a.getZoom() }); syncing = false; });
  sync(before, after); sync(after, before);

  const C = { red: '#E5533D', amber: '#E9A93B', home: '#F6D365' };
  function setup(map, idx, withLoss) {
    map.addSource('radar', { type: 'image', url: D.images[scenes[idx].image], coordinates: corners });
    map.addLayer({ id: 'radar', type: 'raster', source: 'radar', paint: { 'raster-fade-duration': 0, 'raster-contrast': 0.15 } });
    if (withLoss) {
      map.addSource('loss', { type: 'image', url: D.images['loss.png'], coordinates: corners });
      map.addLayer({ id: 'loss', type: 'raster', source: 'loss', paint: { 'raster-opacity': 0.95, 'raster-resampling': 'nearest' } });
    }
    map.addSource('cells', { type: 'geojson', data: cells });
    map.addLayer({ id: 'cells-fill', type: 'fill', source: 'cells', paint: {
      'fill-color': ['match', ['get', 'level'], 'red', C.red, C.amber],
      'fill-opacity': ['case', ['boolean', ['feature-state', 'sel'], false], 0.32, 0.14] } });
    map.addLayer({ id: 'cells-line', type: 'line', source: 'cells', paint: {
      'line-color': ['match', ['get', 'level'], 'red', C.red, C.amber],
      'line-width': ['case', ['boolean', ['feature-state', 'sel'], false], 3.5, 1.6] } });
    map.addSource('homes', { type: 'geojson', data: D.homes });
    map.addLayer({ id: 'homes', type: 'circle', source: 'homes', paint: {
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 9, 1.4, 12, 3, 15, 6],
      'circle-color': C.home, 'circle-stroke-color': '#2b2100', 'circle-stroke-width': 0.6 } });
    map.on('click', 'cells-fill', (e) => select(e.features[0].id, false));
    map.on('mouseenter', 'cells-fill', () => { map.getCanvas().style.cursor = 'pointer'; });
    map.on('mouseleave', 'cells-fill', () => { map.getCanvas().style.cursor = ''; });
  }

  // ---- which passes are compared
  let iBefore = 0, iAfter = last;
  $('selBefore').innerHTML = scenes.map((s, i) => `<option value="${i}">${dShort(s.date)}</option>`).join('');
  const shown = { before: 0, after: last };      // images loaded by setup()
  function show() {
    if (shown.before !== iBefore) { before.getSource('radar').updateImage({ url: D.images[scenes[iBefore].image], coordinates: corners }); shown.before = iBefore; }
    if (shown.after !== iAfter) { after.getSource('radar').updateImage({ url: D.images[scenes[iAfter].image], coordinates: corners }); shown.after = iAfter; }
    // the red "land lost" layer is the season result, so it only shows on the last pass
    after.setLayoutProperty('loss', 'visibility', iAfter === last ? 'visible' : 'none');
    $('labelBefore').textContent = dLong(scenes[iBefore].date);
    $('labelAfter').textContent = dLong(scenes[iAfter].date);
    $('labelAfterNote').textContent = iAfter === last ? 'after, red = land the river took' : 'after';
    $('selBefore').value = iBefore;
    document.querySelectorAll('.pass').forEach((el, i) => {
      el.classList.toggle('is-after', i === iAfter);
      el.classList.toggle('is-before', i === iBefore);
      el.setAttribute('aria-pressed', i === iAfter);
    });
  }
  $('selBefore').onchange = (e) => { iBefore = +e.target.value; show(); };

  // ---- monsoon pulse: one bar per pass, placed by its real date
  const t = scenes.map((s) => Date.parse(s.date)), t0 = t[0], span = Math.max(1, t[last] - t0);
  const pos = (ms) => 4 + ((ms - t0) / span) * 92;      // percent across, with margins for the edge labels
  const maxKm = Math.max(...scenes.map((s) => s.water_km2));
  const DAY = 864e5;
  let tl = '';
  for (let i = 1; i < scenes.length; i++) {
    if ((t[i] - t[i - 1]) / DAY > 18) {
      const a = pos(t[i - 1]), b = pos(t[i]);
      tl += `<div class="gap" style="left:calc(${a}% + 34px);width:calc(${b - a}% - 68px)">no NISAR pass<br>${Math.round((t[i] - t[i - 1]) / DAY)} days</div>`;
    }
  }
  tl += scenes.map((s, i) => `<button class="pass" type="button" style="left:${pos(t[i])}%" data-i="${i}"
      aria-label="${dLong(s.date)}, water ${fmt(s.water_km2)} square kilometres">
      <span class="km">${Math.round(s.water_km2)} km²</span>
      <span class="bar" style="height:${Math.max(6, (s.water_km2 / maxKm) * 66)}px"></span>
      <span class="d">${dShort(s.date)}</span></button>`).join('');
  $('timeline').innerHTML = tl;
  $('timeline').addEventListener('click', (e) => { const b = e.target.closest('.pass'); if (!b) return; const i = +b.dataset.i; if (i === iBefore) return; stop(); iAfter = i; show(); });
  const peak = scenes.reduce((a, s) => (s.water_km2 > a.water_km2 ? s : a), scenes[0]);
  $('pulseNote').textContent = `Peak ${fmt(Math.round(peak.water_km2))} km² on ${dShort(peak.date)}`;

  let timer = null;
  const icon = { play: 'M7 4l13 8-13 8z', pause: 'M6 4h4v16H6zM14 4h4v16h-4z' };
  function stop() { clearInterval(timer); timer = null; $('playIcon').setAttribute('d', icon.play); $('play').setAttribute('aria-label', 'Play through the season'); }
  function step(dir) { iAfter = (iAfter + dir + scenes.length) % scenes.length; if (iAfter === iBefore) iAfter = (iAfter + dir + scenes.length) % scenes.length; show(); }
  function play() {
    if (timer) { stop(); return; }
    $('playIcon').setAttribute('d', icon.pause); $('play').setAttribute('aria-label', 'Pause');
    iBefore = 0; iAfter = iAfter === last ? 0 : iAfter;
    timer = setInterval(() => { step(1); if (iAfter === last) stop(); }, 1300);
  }
  $('play').onclick = play;
  document.addEventListener('keydown', (e) => {
    if (e.target.closest('select, input, .divider') || !$('methods').hidden) return;
    if (e.key === ' ') { e.preventDefault(); play(); }
    if (e.key === 'ArrowRight') { stop(); step(1); }
    if (e.key === 'ArrowLeft') { stop(); step(-1); }
  });

  // ---- swipe handle
  const stage = document.querySelector('.stage'), div = $('divider');
  function setSwipe(pct) {
    pct = Math.max(0, Math.min(100, pct));
    div.style.left = pct + '%';
    $('mapAfter').style.clipPath = `inset(0 0 0 ${pct}%)`;
    div.setAttribute('aria-valuenow', Math.round(pct));
  }
  let dragging = false;
  div.addEventListener('pointerdown', (e) => { dragging = true; div.setPointerCapture(e.pointerId); });
  div.addEventListener('pointermove', (e) => { if (!dragging) return; const r = stage.getBoundingClientRect(); setSwipe(((e.clientX - r.left) / r.width) * 100); });
  div.addEventListener('pointerup', () => { dragging = false; });
  div.addEventListener('keydown', (e) => { const v = parseFloat(div.style.left || '50'); if (e.key === 'ArrowLeft') setSwipe(v - 5); if (e.key === 'ArrowRight') setSwipe(v + 5); });
  setSwipe(50);

  // ---- selected stretch: number, chart, alert
  let selected = null, lang = 'bn';
  function select(id, fly) {
    if (!cells.features[id]) return;
    [before, after].forEach((m) => {
      if (selected !== null) m.setFeatureState({ source: 'cells', id: selected }, { sel: false });
      m.setFeatureState({ source: 'cells', id }, { sel: true });
    });
    selected = id;
    document.querySelectorAll('.priority button').forEach((b) => b.setAttribute('aria-current', +b.dataset.id === id));
    const p = cells.features[id].properties;
    if (fly) after.flyTo({ center: p.centre, zoom: 13, duration: reduce ? 0 : 1400, essential: true });
    $('cellBox').innerHTML = `
      <h2>${cap(p.side || '')} bank stretch ${p.id} <span class="chip ${p.level}">${p.level === 'red' ? 'High risk' : 'Watch'}</span></h2>
      <div class="big"><b>${fmt(p.retreat_m)} m</b><span>the river moved into the land since ${dShort(scenes[0].date)}</span></div>
      <dl class="facts">
        <dt>Homes within ${S.method.near_m} m</dt><dd>${p.homes_near}</dd>
        <dt>Land the river took</dt><dd>${fmt(p.lost_ha)} ha</dd>
        <dt>Location</dt><dd>${p.centre[1].toFixed(4)}° N, ${p.centre[0].toFixed(4)}° E</dd>
      </dl>
      ${chart(p.history_m, p.level)}
      <p class="chart-cap">Bank position on each radar pass, metres into the land from ${dShort(scenes[0].date)}. A missing point means the bank line switched channel on that pass.</p>`;
    showAlert(p);
  }

  function chart(vals, level) {
    const W = 340, H = 150, L = 34, R = 10, T = 12, B = 22;
    const ok = vals.filter((v) => v != null);
    const hi = Math.max(50, ...ok), lo = Math.min(0, ...ok);
    const X = (i) => L + ((t[i] - t0) / span) * (W - L - R);
    const Y = (v) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B);
    const col = level === 'red' ? C.red : C.amber;
    let gaps = '';
    for (let i = 1; i < vals.length; i++) if ((t[i] - t[i - 1]) / DAY > 18) {
      gaps += `<rect x="${X(i - 1)}" y="${T}" width="${X(i) - X(i - 1)}" height="${H - T - B}" fill="currentColor" opacity=".07"/>`;
    }
    // draw segments only between consecutive measured passes: never bridge a missing one
    let path = '';
    for (let i = 0; i < vals.length; i++) {
      if (vals[i] == null) continue;
      path += (i > 0 && vals[i - 1] != null ? 'L' : 'M') + X(i).toFixed(1) + ' ' + Y(vals[i]).toFixed(1);
    }
    const ticks = [];
    [0, Math.round(hi / 2), Math.round(hi), lo].forEach((v) => { if (ticks.every((u) => Math.abs(Y(u) - Y(v)) > 14)) ticks.push(v); });
    return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Bank retreat by radar pass">
      ${gaps}
      ${ticks.map((v) => `<line x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}" stroke="currentColor" stroke-opacity="${v === 0 ? .45 : .15}"/>
        <text x="${L - 6}" y="${Y(v) + 4}" font-size="11" text-anchor="end" fill="currentColor">${Math.round(v)}</text>`).join('')}
      <path d="${path}" fill="none" stroke="${col}" stroke-width="2.4" stroke-linejoin="round"/>
      ${vals.map((v, i) => (v == null ? '' : `<circle cx="${X(i)}" cy="${Y(v)}" r="3.6" fill="${col}"><title>${dLong(scenes[i].date)}: ${fmt(v)} m</title></circle>`)).join('')}
      ${[0, Math.floor(last / 2), last].map((i) => `<text x="${X(i)}" y="${H - 6}" font-size="10.5" text-anchor="${i === 0 ? 'start' : i === last ? 'end' : 'middle'}" fill="currentColor">${dShort(scenes[i].date)}</text>`).join('')}
    </svg>`;
  }

  function showAlert(p) {
    $('phone').hidden = false;
    const m = Math.round(p.retreat_m), days = S.period_days;
    const bnText = `নদীনজর সতর্কবার্তা: গত ${bn(days)} দিনে আপনার এলাকায় যমুনার পাড় ${bn(m)} মিটার সরে এসেছে। ভাঙনের ঝুঁকি: ${p.level === 'red' ? 'উচ্চ' : 'মাঝারি'}। মূল্যবান জিনিস ও গবাদিপশু নিরাপদ স্থানে সরানোর প্রস্তুতি নিন এবং ইউনিয়ন পরিষদের সাথে যোগাযোগ করুন। (${p.id})`;
    const enText = `NodiNajar alert: in the last ${days} days the Jamuna bank near you moved ${m} m. Erosion risk: ${p.level === 'red' ? 'HIGH' : 'MEDIUM'}. Prepare to move valuables and livestock to safety and contact your union parishad. (${p.id})`;
    $('msg').dataset.bn = bnText; $('msg').dataset.en = enText;
    setLang(lang);
  }
  function setLang(l) {
    lang = l;
    $('msg').textContent = $('msg').dataset[l] || '';
    $('msg').lang = l;
    $('tabBn').setAttribute('aria-selected', l === 'bn'); $('tabEn').setAttribute('aria-selected', l === 'en');
  }
  $('tabBn').onclick = () => setLang('bn');
  $('tabEn').onclick = () => setLang('en');
  $('speak').onclick = () => {
    if (!('speechSynthesis' in window)) { $('speak').textContent = 'No voice in this browser'; return; }
    const u = new SpeechSynthesisUtterance($('msg').textContent);
    const want = lang === 'bn' ? 'bn' : 'en';
    const v = speechSynthesis.getVoices().find((x) => x.lang && x.lang.toLowerCase().startsWith(want));
    if (v) { u.voice = v; u.lang = v.lang; } else { u.lang = lang === 'bn' ? 'bn-BD' : 'en-GB'; if (lang === 'bn') $('speak').textContent = 'No Bangla voice installed'; }
    speechSynthesis.cancel(); speechSynthesis.speak(u);
  };

  // ---- methods drawer: every processing step and the raw numbers
  const passRows = scenes.map((s) => `<tr><td>${dLong(s.date)}</td><td>${s.threshold_db} dB${s.threshold_from ? ` (${s.threshold_from})` : ''}</td><td>${fmt(s.water_km2)} km²</td></tr>`).join('');
  const rows = [
    ['Data', synthetic ? 'SYNTHETIC test scenes (not real)' : 'NASA-ISRO NISAR L-band L2 GCOV, PROVISIONAL (validated at a limited set of sites)'],
    ['Passes', `${scenes.length}, ${dLong(scenes[0].date)} to ${dLong(scenes[last].date)}, same track and frame`],
    ['Polarisation', scenes[0].pol],
    ['Pixel size', `${S.pixel_m} m, EPSG:${S.epsg}`],
    ['Speckle filter', S.method.speckle_filter],
    ['Water rule', S.method.water_rule],
    ['River rule', S.method.river_rule || ''],
    ['Bank movement', S.method.retreat],
    ['Counted as lost', S.lost_rule],
    ['Risk rule', S.method.risk_rule],
    ['Homes', S.homes_source],
    ['Uncertainty', S.method.uncertainty],
    ['Granules', scenes.map((s) => s.granule).join('<br>')],
  ];
  $('methodsBody').innerHTML = `
    <table>${rows.map((r) => `<tr><td>${r[0]}</td><td>${r[1]}</td></tr>`).join('')}</table>
    <h3>Each pass</h3>
    <table class="passes"><tr><td>Date</td><td>Water threshold</td><td>Water in the box</td></tr>${passRows}</table>
    <p class="muted">Raw output behind every number on screen (stats.json):</p>
    <pre>${JSON.stringify(S, null, 2).replace(/</g, '&lt;')}</pre>`;
  const openM = () => { $('methods').hidden = false; $('closeMethods').focus(); stop(); };
  const closeM = () => { $('methods').hidden = true; $('openMethods').focus(); };
  $('openMethods').onclick = openM; $('closeMethods').onclick = closeM;
  $('methods').addEventListener('click', (e) => { if (e.target.id === 'methods') closeM(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !$('methods').hidden) closeM(); });

  // ---- start
  let ready = 0;
  const onReady = () => { if (++ready < 2) return; show(); if (cells.features.length) select(0, false); };
  before.on('load', () => { setup(before, 0, false); onReady(); });
  after.on('load', () => { setup(after, last, true); onReady(); });
})();
