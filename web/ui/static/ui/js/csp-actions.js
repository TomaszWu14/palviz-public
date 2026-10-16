/* US-008 faza 2 (ADR-0020): deklaratywne akcje zamiast atrybutów on*= w szablonach.
 *
 * Ścisła CSP blokuje inline handlery (onclick, onsubmit, onchange…). Ten plik (statyczny,
 * więc dozwolony przez script-src 'self') obsługuje je przez delegację zdarzeń na document:
 *
 *   data-confirm="Tekst?"   formularz: pyta przed wysłaniem; przycisk/link: przed kliknięciem
 *   data-scan="input-id"    klik → palvizScan(id); opcjonalnie data-scan-src="scan" ustawia #scan-src
 *   data-click="el-id"      klik → klik w element #el-id (np. ukryty input[type=file])
 *   data-hide="el-id"       klik → ukrywa #el-id
 *   data-remove-closest="tr"  klik → usuwa najbliższego przodka pasującego do selektora (np. wiersz)
 *   data-autosubmit         change → form.submit(); data-autosubmit="request" → form.requestSubmit()
 *   data-enable-submit      change → odblokowuje przycisk formularza
 *   data-check-all="sel"    klik w checkbox → zaznacza/odznacza wszystkie pasujące do selektora
 *   data-no-submit          formularz nie wysyła się (np. filtry działające tylko w JS)
 *   data-upload             change → gvUpload(this) (planer) / pvUpload(this) (skaner)
 *   data-action="fn"        wywołuje window.fn(el, ...argumenty); zwrot false = preventDefault
 *   data-call="fn"          wywołuje window.fn(...argumenty) — bez elementu (np. showTab('csv'))
 *                           Argumenty: data-arg="1" (jeden) albo data-args='["a", 2]' (JSON).
 *                           Zdarzenie: data-on="click" (domyślnie) | "change" | "input" | "dblclick".
 */
(function () {
  'use strict';

  function args(el) {
    if (el.dataset.args !== undefined) {
      try { return JSON.parse(el.dataset.args); } catch (e) { return []; }
    }
    var a = el.dataset.arg;
    if (a === undefined) return [];
    return [a !== '' && !isNaN(+a) ? +a : a];
  }

  // data-action → fn(el, ...args); data-call → fn(...args).
  function run(el, ev) {
    var withEl = el.dataset.action !== undefined;
    var fn = window[withEl ? el.dataset.action : el.dataset.call];
    if (typeof fn !== 'function') return;
    var result = fn.apply(window, withEl ? [el].concat(args(el)) : args(el));
    if (result === false) ev.preventDefault();
  }

  var ACTION = '[data-action],[data-call]';
  function onEvent(name) {
    return function (ev) {
      if (!(ev.target instanceof Element)) return;
      var el = ev.target.closest(ACTION);
      if (el && (el.dataset.on || 'click') === name) run(el, ev);
    };
  }

  function byId(id) { return id ? document.getElementById(id) : null; }

  // Potwierdzenie przed wysłaniem formularza — w fazie przechwytywania, żeby anulowanie
  // zatrzymało też inne nasłuchy submit (np. blokadę podwójnego wysłania).
  document.addEventListener('submit', function (ev) {
    var f = ev.target;
    if (f.dataset && f.dataset.noSubmit !== undefined) { ev.preventDefault(); return; }
    if (f.dataset && f.dataset.confirm && !window.confirm(f.dataset.confirm)) {
      ev.preventDefault();
      ev.stopImmediatePropagation();
    }
  }, true);

  document.addEventListener('click', function (ev) {
    if (!(ev.target instanceof Element)) return;
    var c = ev.target.closest('[data-confirm]:not(form)');
    if (c && !window.confirm(c.dataset.confirm)) {
      ev.preventDefault();
      ev.stopImmediatePropagation();
      return;
    }
    var act = ev.target.closest(ACTION);
    if (act && (act.dataset.on || 'click') === 'click') run(act, ev);

    var scan = ev.target.closest('[data-scan]');
    if (scan) {
      if (scan.dataset.scanSrc) {
        var src = byId('scan-src');
        if (src) src.value = scan.dataset.scanSrc;
      }
      if (typeof window.palvizScan === 'function') window.palvizScan(scan.dataset.scan);
    }
    var clk = ev.target.closest('[data-click]');
    if (clk) { var t = byId(clk.dataset.click); if (t) t.click(); }
    var hide = ev.target.closest('[data-hide]');
    if (hide) { var h = byId(hide.dataset.hide); if (h) h.style.display = 'none'; }
    var all = ev.target.closest('[data-check-all]');
    if (all) {
      document.querySelectorAll(all.dataset.checkAll).forEach(function (c) { c.checked = all.checked; });
    }
    var rm = ev.target.closest('[data-remove-closest]');
    if (rm) { var row = rm.closest(rm.dataset.removeClosest); if (row) row.remove(); }
  });

  document.addEventListener('change', function (ev) {
    var el = ev.target;
    if (!(el instanceof Element)) return;
    if (el.matches('[data-autosubmit]') && el.form) {
      if (el.dataset.autosubmit === 'request' && el.form.requestSubmit) el.form.requestSubmit();
      else el.form.submit();
    }
    if (el.matches('[data-enable-submit]') && el.form) {
      var btn = el.form.querySelector('button');
      if (btn) btn.disabled = false;
    }
    if (el.matches('[data-upload]')) {
      var up = window.gvUpload || window.pvUpload;
      if (typeof up === 'function') up(el);
    }
  });
  document.addEventListener('change', onEvent('change'));
  document.addEventListener('input', onEvent('input'));
  document.addEventListener('dblclick', onEvent('dblclick'));
})();
