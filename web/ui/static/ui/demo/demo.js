/* Tryb pokazu LogViz (?demo=1): krok = akcja/podświetlenie → nagranie lektora → 500 ms → następny.
 * Ładowany wyłącznie, gdy URL ma ?demo=1 (ui/_demo.html) — bez parametru aplikacja jest nietknięta.
 * Stan (krok, odtwarzanie, głośność) w sessionStorage, bo pokaz przechodzi przez wiele stron.
 * Jedno nagranie naraz: każdy start kroku najpierw zatrzymuje bieżące audio / syntezę. */
(function () {
  'use strict';
  // Katalog bazowy z adresu skryptu (działa też z hashowanymi nazwami statyk na produkcji).
  var BASE = document.currentScript.src.replace(/[^/]*$/, '');   // .../ui/demo/
  var KEY = 'lvDemo', PAUSE_MS = 500;
  var steps = [], lexicon = {}, manifest = {};
  var st = load(), audio = null, preloaded = {}, token = 0, ui = {};

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
    el.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }

  // ── Dźwięk ───────────────────────────────────────────────────────────────────────
  function stopAudio() {
    token++;                                   // unieważnia zaległe „ended”/timery
    if (audio) { audio.pause(); audio.onended = null; }
    if (window.speechSynthesis) speechSynthesis.cancel();
  }
  function audioFor(i) {
    var file = steps[i] && manifest[steps[i].id];
    if (!file) return null;
    if (!preloaded[i]) { preloaded[i] = new Audio(BASE + 'audio/' + file); preloaded[i].preload = 'auto'; }
    return preloaded[i];
  }
  function speakText(text) {
    Object.keys(lexicon).sort(function (a, b) { return b.length - a.length; }).forEach(function (k) {
      text = text.split(k).join(lexicon[k]);
    });
    return text;
  }
  function play(i) {
    var my = token;
    function done() { if (my === token) setTimeout(function () { if (my === token) go(i + 1); }, PAUSE_MS); }
    audio = audioFor(i);
    audioFor(i + 1);                           // preload następnego kroku
    if (audio) {
      audio.muted = !!st.muted; audio.volume = st.vol == null ? 1 : st.vol;
      audio.currentTime = 0;
      audio.onended = done;
      audio.ontimeupdate = function () { progress(i, audio.duration ? audio.currentTime / audio.duration : 0); };
      audio.play().catch(function (e) {
        if (e && e.name === 'NotAllowedError') { setPlaying(false); caption('Kliknij „Wznów”, aby kontynuować prezentację.'); }
      });
      return;
    }
    console.warn('[demo] brak nagrania dla ' + steps[i].id + ' — czytam przez speechSynthesis (pl-PL)');
    if (!window.speechSynthesis) { setTimeout(done, 4000); return; }
    var u = new SpeechSynthesisUtterance(speakText(steps[i].text));
    u.lang = 'pl-PL'; u.volume = st.muted ? 0 : (st.vol == null ? 1 : st.vol);
    u.onend = done;
    speechSynthesis.speak(u);
  }

  // ── Kroki ────────────────────────────────────────────────────────────────────────
  function go(i) {
    if (i >= steps.length) { finish(); return; }
    run(Math.max(0, i), st.playing);
  }
  function run(i, andPlay) {
    stopAudio();
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
    stopAudio(); setPlaying(false); st.i = 0; save();
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
    if (st.playing) { stopAudio(); setPlaying(false); return; }
    st.started = true; setPlaying(true);
    if (audio && audio.currentTime > 0 && !audio.ended && manifest[steps[st.i].id]) {
      var my = ++token, i = st.i;                      // wznowienie w połowie nagrania
      audio.onended = function () { if (my === token) setTimeout(function () { if (my === token) go(i + 1); }, PAUSE_MS); };
      audio.play();
    } else {
      run(st.i || 0, true);
    }
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
    ui.mute = btn(st.muted ? 'Włącz dźwięk' : 'Wycisz', function () {
      st.muted = !st.muted; save(); ui.mute.textContent = st.muted ? 'Włącz dźwięk' : 'Wycisz';
      if (audio) audio.muted = st.muted;
    });
    var vol = document.createElement('input');
    vol.type = 'range'; vol.min = 0; vol.max = 1; vol.step = 0.05; vol.value = st.vol == null ? 1 : st.vol;
    vol.className = 'lv-demo__vol'; vol.setAttribute('aria-label', 'Głośność');
    vol.addEventListener('input', function () { st.vol = +vol.value; save(); if (audio) audio.volume = st.vol; });
    var close = btn('✕', function () {
      stopAudio(); try { sessionStorage.removeItem(KEY); } catch (e) { /* nic */ }
      location.href = location.pathname;
    }, 'lv-demo__btn--close');
    close.setAttribute('aria-label', 'Zakończ tryb pokazu');
    [ui.play, prev, next, ui.mute, vol, ui.count, close].forEach(function (n) { panel.appendChild(n); });
    panel.appendChild(track);
    wrap.appendChild(ui.cap); wrap.appendChild(panel);
    document.body.appendChild(wrap);
  }

  // ── Start ────────────────────────────────────────────────────────────────────────
  Promise.all([getJSON(BASE + 'demo_script.json'), getJSON(BASE + 'audio/manifest.json')])
    .then(function (r) {
      steps = (r[0] && r[0].steps) || []; lexicon = (r[0] && r[0].lexicon) || {}; manifest = r[1] || {};
      if (!steps.length) { console.warn('[demo] brak scenariusza'); return; }
      if (st.i == null || st.i >= steps.length) st.i = 0;
      buildPanel();
      setPlaying(!!st.playing);
      progress(st.i, 0);
      if (st.playing) run(st.i, true);                  // ciąg dalszy po przejściu na nową stronę
      else if (st.arrived) run(st.i, false);            // Poprzedni/Następny w pauzie: pokaż krok
    });
})();
