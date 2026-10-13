/* Tryb pokazu LogViz (?demo=1): krok = akcja/podświetlenie + napis → czas na przeczytanie → następny.
 * Ładowany wyłącznie, gdy URL ma ?demo=1 (ui/_demo.html) — bez parametru aplikacja jest nietknięta.
 * Bez lektora: czas kroku zależy od długości napisu (READ_MS na znak, min. MIN_MS).
 * Stan (krok, odtwarzanie) w sessionStorage, bo pokaz przechodzi przez wiele stron.
 * Start kroku wysyła zdarzenie `lv-demo-step` (id, ms) — z niego korzysta nagrywanie filmu. */
(function () {
  'use strict';
  // Katalog bazowy z adresu skryptu (działa też z hashowanymi nazwami statyk na produkcji).
  var BASE = document.currentScript.src.replace(/[^/]*$/, '');   // .../ui/demo/
  var KEY = 'lvDemo', READ_MS = 65, MIN_MS = 4500;
  var steps = [];
  var st = load(), token = 0, ui = {};
  var clock = { i: -1, total: 0, left: 0, t0: 0, timer: null, tick: null };

  function load() {
    try { return JSON.parse(sessionStorage.getItem(KEY)) || {}; } catch (e) { return {}; }
  }
  function save() { try { sessionStorage.setItem(KEY, JSON.stringify(st)); } catch (e) { /* tryb prywatny */ } }
  function getJSON(url) {
    return fetch(url, { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : {}; })
      .catch(function () { return {}; });
  }
  function withDemo(url) {
    var u = new URL(url, location.origin);
    u.searchParams.set('demo', '1');
    return u.pathname + u.search + u.hash;
  }

  // ── Elementy strony ──────────────────────────────────────────────────────────────
  function find(sel, contains, closest) {
    if (!sel) return null;
    var nodes = document.querySelectorAll(sel);
    for (var k = 0; k < nodes.length; k++) {
      if (!contains || nodes[k].textContent.indexOf(contains) !== -1) {
        return (closest && nodes[k].closest(closest)) || nodes[k];
      }
    }
    return null;
  }
  function highlight(el) {
    var old = document.querySelectorAll('.lv-demo-hl');
    for (var k = 0; k < old.length; k++) old[k].classList.remove('lv-demo-hl');
    if (!el) return;
    el.classList.add('lv-demo-hl');
    // Element wyższy niż ekran (np. #result-area z widokiem 3D): „center” ucinał jego górę.
    var tall = el.getBoundingClientRect().height > window.innerHeight * 0.8;
    el.scrollIntoView({ block: tall ? 'start' : 'center', behavior: 'smooth' });
  }

  // ── Czas kroku ───────────────────────────────────────────────────────────────────
  function dwell(i) { return Math.max(MIN_MS, steps[i].text.length * READ_MS); }
  function stopClock() {
    token++;                                   // unieważnia zaległe timery
    if (clock.timer) clearTimeout(clock.timer);
    if (clock.tick) clearInterval(clock.tick);
    if (clock.t0) clock.left = Math.max(0, clock.left - (Date.now() - clock.t0));
    clock.timer = clock.tick = null; clock.t0 = 0;
  }
  function startClock(i) {
    var my = token;
    clock.t0 = Date.now();
    clock.timer = setTimeout(function () { if (my === token) { clock.t0 = 0; go(i + 1); } }, clock.left);
    clock.tick = setInterval(function () {
      var gone = clock.total - clock.left + (Date.now() - clock.t0);
      progress(i, Math.min(1, gone / clock.total));
    }, 200);
  }
  function play(i) {
    clock.i = i; clock.total = clock.left = dwell(i);
    try { document.dispatchEvent(new CustomEvent('lv-demo-step', { detail: { id: steps[i].id, ms: clock.total } })); } catch (e) { /* stara przeglądarka */ }
    startClock(i);
  }

  // ── Kroki ────────────────────────────────────────────────────────────────────────
  function go(i) {
    if (i >= steps.length) { finish(); return; }
    run(Math.max(0, i), st.playing);
  }
  function run(i, andPlay) {
    stopClock(); clock.i = -1;
    var step = steps[i];
    st.i = i; save();
    progress(i, 0); caption(step.text);
    var here = step.url && new URL(step.url, location.origin).pathname === location.pathname;
    if (step.action === 'navigate' && st.arrived !== step.id && !here) {
      var link = step.follow && document.querySelector(step.follow);
      var target = step.url || (link && link.getAttribute('href'));
      if (target) { st.arrived = step.id; save(); location.href = withDemo(target); return; }
    }
    st.arrived = null; save();
    if (/^\/login/.test(location.pathname)) {
      setPlaying(false); caption('Zaloguj się (np. jako planista), potem kliknij „Wznów”.'); return;
    }
    var my = token;
    var el = find(step.selector, step.contains, step.closest);
    highlight(el);
    if (step.action === 'click' && el) {
      el.click();
      setTimeout(function () {
        if (my !== token) return;
        if (step.focus) highlight(document.querySelector(step.focus));
        if (andPlay) play(i);
      }, 1500);
      return;
    }
    if (andPlay) play(i);
  }
  function finish() {
    stopClock(); setPlaying(false); st.i = 0; save();
    highlight(null); progress(steps.length - 1, 1);
    caption('Koniec prezentacji. Dziękuję!');
  }

  // ── Panel ────────────────────────────────────────────────────────────────────────
  function setPlaying(on) {
    st.playing = on; save();
    ui.play.textContent = on ? 'Pauza' : (st.started ? 'Wznów' : 'Rozpocznij prezentację');
    ui.play.classList.toggle('lv-demo__btn--primary', !on);
  }
  function caption(t) { ui.cap.textContent = t; ui.cap.hidden = !t; }
  function progress(i, frac) {
    ui.bar.style.width = (100 * (i + frac) / Math.max(1, steps.length)).toFixed(1) + '%';
    ui.count.textContent = (i + 1) + ' / ' + steps.length;
  }
  function togglePlay() {
    if (st.playing) { stopClock(); setPlaying(false); return; }
    st.started = true; setPlaying(true);
    if (clock.i === st.i && clock.left > 0) { token++; startClock(st.i); }   // wznowienie w połowie kroku
    else run(st.i || 0, true);
  }
  function btn(label, onClick, cls) {
    var b = document.createElement('button');
    b.type = 'button'; b.className = 'lv-demo__btn' + (cls ? ' ' + cls : ''); b.textContent = label;
    b.addEventListener('click', onClick);
    return b;
  }
  function buildPanel() {
    var wrap = document.createElement('div'); wrap.className = 'lv-demo';
    ui.cap = document.createElement('div'); ui.cap.className = 'lv-demo__cap'; ui.cap.hidden = true;
    var panel = document.createElement('div'); panel.className = 'lv-demo__panel';
    panel.setAttribute('role', 'region'); panel.setAttribute('aria-label', 'Sterowanie prezentacją');
    var track = document.createElement('div'); track.className = 'lv-demo__track';
    ui.bar = document.createElement('div'); ui.bar.className = 'lv-demo__bar'; track.appendChild(ui.bar);
    ui.count = document.createElement('span'); ui.count.className = 'lv-demo__count';
    ui.play = btn('Rozpocznij prezentację', togglePlay, 'lv-demo__btn--primary');
    var prev = btn('◀ Poprzedni', function () { go((st.i || 0) - 1); });
    var next = btn('Następny ▶', function () { go((st.i || 0) + 1); });
    var close = btn('✕', function () {
      stopClock(); try { sessionStorage.removeItem(KEY); } catch (e) { /* nic */ }
      location.href = location.pathname;
    }, 'lv-demo__btn--close');
    close.setAttribute('aria-label', 'Zakończ tryb pokazu');
    [ui.play, prev, next, ui.count, close].forEach(function (n) { panel.appendChild(n); });
    panel.appendChild(track);
    wrap.appendChild(ui.cap); wrap.appendChild(panel);
    document.body.appendChild(wrap);
  }

  // ── Start ────────────────────────────────────────────────────────────────────────
  getJSON(BASE + 'demo_script.json')
    .then(function (r) {
      steps = (r && r.steps) || [];
      if (!steps.length) { console.warn('[demo] brak scenariusza'); return; }
      if (st.i == null || st.i >= steps.length) st.i = 0;
      buildPanel();
      setPlaying(!!st.playing);
      progress(st.i, 0);
      if (st.playing) run(st.i, true);                  // ciąg dalszy po przejściu na nową stronę
      else if (st.arrived) run(st.i, false);            // Poprzedni/Następny w pauzie: pokaż krok
    });
})();
