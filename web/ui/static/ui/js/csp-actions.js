/* US-008 faza 2 (ADR-0020): deklaratywne akcje zamiast atrybutów on*= w szablonach.
 *
 * Ścisła CSP blokuje inline handlery (onclick, onsubmit, onchange…). Ten plik (statyczny,
 * więc dozwolony przez script-src 'self') obsługuje je przez delegację zdarzeń na document:
 *
 *   data-confirm="Tekst?"   formularz: pyta przed wysłaniem; przycisk/link: przed kliknięciem
 *   data-scan="input-id"    klik → palvizScan(id); opcjonalnie data-scan-src="scan" ustawia #scan-src
 *   data-click="el-id"      klik → klik w element #el-id (np. ukryty input[type=file])
 *   data-hide="el-id"       klik → ukrywa #el-id
 *   data-autosubmit         change → form.submit() (jak dawne onchange="this.form.submit()")
 *   data-upload             change → pvUpload(this) (skaner: wysyłka zdjęcia z informacją)
 *   data-action="fn"        wywołuje window.fn(el[, data-arg]); zwrot false = preventDefault.
 *                           Zdarzenie: data-on="click" (domyślnie) | "change" | "dblclick".
 */
(function () {
  'use strict';

  function arg(el) {
    var a = el.dataset.arg;
    if (a === undefined) return undefined;
    return a !== '' && !isNaN(+a) ? +a : a;
  }

  function runAction(el, ev) {
    var fn = window[el.dataset.action];
    if (typeof fn !== 'function') return;
    var a = arg(el);
    var result = a === undefined ? fn(el) : fn(el, a);
    if (result === false) ev.preventDefault();
  }

  function byId(id) { return id ? document.getElementById(id) : null; }

  // Potwierdzenie przed wysłaniem formularza — w fazie przechwytywania, żeby anulowanie
  // zatrzymało też inne nasłuchy submit (np. blokadę podwójnego wysłania).
  document.addEventListener('submit', function (ev) {
    var f = ev.target;
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
    var act = ev.target.closest('[data-action]');
    if (act && (act.dataset.on || 'click') === 'click') runAction(act, ev);

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
  });

  document.addEventListener('change', function (ev) {
    var el = ev.target;
    if (!(el instanceof Element)) return;
    if (el.matches('[data-autosubmit]') && el.form) el.form.submit();
    if (el.matches('[data-upload]') && typeof window.pvUpload === 'function') window.pvUpload(el);
    if (el.matches('[data-action][data-on="change"]')) runAction(el, ev);
  });

  document.addEventListener('dblclick', function (ev) {
    if (!(ev.target instanceof Element)) return;
    var el = ev.target.closest('[data-action][data-on="dblclick"]');
    if (el) runAction(el, ev);
  });
})();
