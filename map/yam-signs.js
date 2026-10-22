// You Are Minecraft: player name labels over the statues, readable signs up close, and a name/sign search.
// Data comes from tools/build_sign_index.py (data/plots.json, data/signs.json).
(() => {
  const LABEL_DIST = 220;   // camera distance below which name labels show
  const SIGN_DIST = 40;     // ...and below which every other sign's text shows
  const MAX_LABELS = 160;
  const CELL = 64;
  const $ = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
  const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);

  let plots = null, signs = null, signsLoading = null;
  const grid = { plots: new Map(), signs: new Map() };

  function index(list, g) {
    for (const s of list) {
      const k = Math.floor(s[0] / CELL) + ',' + Math.floor(s[2] / CELL);
      (g.get(k) || g.set(k, []).get(k)).push(s);
    }
  }
  function near(g, x, z, r) {
    const out = [];
    for (let cx = Math.floor((x - r) / CELL); cx <= Math.floor((x + r) / CELL); cx++)
      for (let cz = Math.floor((z - r) / CELL); cz <= Math.floor((z + r) / CELL); cz++)
        for (const s of g.get(cx + ',' + cz) || []) {
          const d = Math.hypot(s[0] - x, s[2] - z);
          if (d <= r) out.push([d, s]);
        }
    return out.sort((a, b) => a[0] - b[0]).map(e => e[1]);
  }
  const load = f => fetch('data/' + f).then(r => r.json());
  function loadSigns() {
    return signsLoading || (signsLoading = load('signs.json').then(d => { signs = d; index(d, grid.signs); refresh(); }));
  }

  // ---- labels ----
  let set, shown = new Map(), hitId = null;
  function label(s, kind) {
    const id = kind + ':' + s[0] + ',' + s[1] + ',' + s[2];
    let m = shown.get(id);
    if (!m) {
      m = new BlueMap.HtmlMarker('yam-' + id);
      m.position.set(s[0] + 0.5, s[1] + (kind === 'p' ? 1.6 : 0.6), s[2] + 0.5);
      m.html = kind === 'p'
        ? `<div class="yam-name">${esc(s[4])}</div>`
        : `<div class="yam-sign">${esc(s[4]).replace(/\n/g, '<br>')}</div>`;
      if (id === hitId) m.element.firstElementChild.classList.add('yam-hit');
      set.add(m);
      shown.set(id, m);
    }
    return id;
  }
  function refresh() {
    if (!set || !plots) return;
    const c = bluemap.mapViewer.controlsManager, x = c.position.x, z = c.position.z, d = c.distance;
    const keep = new Set();
    if (d < LABEL_DIST) {
      const r = Math.min(Math.max(d * 0.9, 40), 160);
      for (const s of near(grid.plots, x, z, r).slice(0, MAX_LABELS)) keep.add(label(s, 'p'));
      if (d < SIGN_DIST) {
        if (signs) for (const s of near(grid.signs, x, z, Math.max(d * 0.8, 24)).slice(0, 60)) keep.add(label(s, 's'));
        else loadSigns();
      }
    }
    for (const [id, m] of shown) if (!keep.has(id)) { set.remove(m); shown.delete(id); }
  }
  let pending = 0;
  const schedule = () => { if (!pending) pending = setTimeout(() => { pending = 0; refresh(); }, 120); };

  // ---- camera ----
  function flyTo(s) {
    const c = bluemap.mapViewer.controlsManager;
    if (bluemap.appState.controls.state !== 'perspective') bluemap.setPerspectiveView(0);
    const from = { x: c.position.x, y: c.position.y, z: c.position.z, d: c.distance, a: c.angle };
    // Sign facing is in 16ths of a turn, 0 = text faces south (+z). Put the camera in front of the text.
    const to = { x: s[0] + 0.5, y: s[1] + 14, z: s[2] + 0.5, d: 34, a: 1.3 };
    c.rotation = -(s[3] / 16) * Math.PI * 2;
    const t0 = performance.now(), dur = 900;
    const ease = t => t < .5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;
    (function step(now) {
      const t = Math.min((now - t0) / dur, 1), k = ease(t);
      for (const p of ['x', 'y', 'z']) c.position[p] = from[p] + (to[p] - from[p]) * k;
      c.distance = from.d + (to.d - from.d) * k;
      c.angle = from.a + (to.a - from.a) * k;
      if (t < 1) requestAnimationFrame(step); else { bluemap.updatePageAddress(); bluemap.mapViewer.updateLoadedMapArea(); }
    })(t0);
    for (const m of shown.values()) m.element.firstElementChild.classList.remove('yam-hit');
    hitId = (s.length === 6 ? 'p:' : 's:') + s[0] + ',' + s[1] + ',' + s[2];
    const m = shown.get(hitId);
    if (m) m.element.firstElementChild.classList.add('yam-hit');
  }

  // ---- search ----
  const ui = $('div', 'yam-search');
  ui.innerHTML = `
    <button class="yam-toggle" aria-label="Find a player" title="Find a player">
      <svg viewBox="0 0 24 24" width="22" height="22"><circle cx="10" cy="10" r="6.5" fill="none" stroke="currentColor" stroke-width="2.5"/><path d="M15 15l6 6" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/></svg>
    </button>
    <div class="yam-panel">
      <input type="search" placeholder="Find a player or sign" autocomplete="off" spellcheck="false" aria-label="Find a player or sign">
      <label class="yam-all"><input type="checkbox"> Search all sign text too</label>
      <div class="yam-results" role="listbox"></div>
    </div>`;
  const input = ui.querySelector('input[type=search]'), all = ui.querySelector('.yam-all input'), results = ui.querySelector('.yam-results');

  function search() {
    const q = input.value.trim().toLowerCase();
    results.innerHTML = '';
    if (!plots) { results.append($('div', 'yam-note', 'Loading names…')); return; }
    if (q.length < 2) { results.append($('div', 'yam-note', `${plots.length.toLocaleString()} statues. Type at least 2 letters.`)); return; }
    const exact = [], starts = [], has = [];
    for (const s of plots) {
      const n = s[4].toLowerCase();
      if (n === q) exact.push(s); else if (n.startsWith(q)) starts.push(s); else if (n.includes(q)) has.push(s);
    }
    let hits = [...exact, ...starts.sort((a, b) => a[4].length - b[4].length), ...has];
    if (all.checked) {
      if (!signs) { loadSigns().then(search); results.append($('div', 'yam-note', 'Loading signs…')); }
      else for (const s of signs) if (s[4].toLowerCase().includes(q)) hits.push(s);
    }
    const total = hits.length;
    hits = hits.slice(0, 60);
    if (!total) results.append($('div', 'yam-note', 'No match.'));
    for (const s of hits) {
      const b = $('button', 'yam-hit-row');
      b.innerHTML = s.length === 6
        ? `<b>${esc(s[4])}</b>${s[5] ? `<small>${esc(s[5])}</small>` : ''}`
        : `<span class="yam-quote">${esc(s[4]).replace(/\n/g, ' / ')}</span>`;
      b.onclick = () => { flyTo(s); if (matchMedia('(max-width: 600px)').matches) ui.classList.remove('open'); history.replaceState(null, '', '?find=' + encodeURIComponent(s.length === 6 ? s[4] : input.value.trim()) + location.hash); };
      results.append(b);
    }
    if (total > hits.length) results.append($('div', 'yam-note', `${(total - hits.length).toLocaleString()} more, keep typing.`));
  }
  let st = 0;
  input.addEventListener('input', () => { clearTimeout(st); st = setTimeout(search, 120); });
  input.addEventListener('keydown', e => { if (e.key === 'Enter') { const b = results.querySelector('button'); if (b) b.click(); } if (e.key === 'Escape') ui.classList.remove('open'); });
  all.addEventListener('change', search);
  ui.querySelector('.yam-toggle').onclick = () => { ui.classList.toggle('open'); if (ui.classList.contains('open')) { input.focus(); search(); } };
  // Keep map keyboard controls from firing while typing
  for (const ev of ['keydown', 'keyup', 'keypress']) ui.addEventListener(ev, e => e.stopPropagation());

  // ---- boot ----
  function start() {
    if (!window.bluemap || !bluemap.mapViewer || !bluemap.mapViewer.map) return setTimeout(start, 200);
    set = new BlueMap.MarkerSet('yam-names');
    set.data.toggleable = false;
    // BlueMap's marker-file refresh drops unknown top-level sets; the popup set is spared, so live under it
    bluemap.popupMarkerSet.add(set);
    document.body.append(ui);
    bluemap.events.addEventListener('bluemapCameraMoved', schedule);
    load('plots.json').then(d => {
      plots = d; index(d, grid.plots); refresh();
      if (ui.classList.contains('open')) search();
      const find = new URLSearchParams(location.search).get('find');
      if (find) {
        input.value = find;
        const f = find.toLowerCase(), s = plots.find(p => p[4].toLowerCase() === f);
        if (s) flyTo(s); else { ui.classList.add('open'); search(); }
      }
    });
  }
  start();
})();
