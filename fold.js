// fold.js — Verhalten der klappbaren KI-Guide-Abschnitte (<details class="fold">).
// Direkte Quelldatei (wie style.css), wird nicht generiert. Siehe _src/WARTUNG.md.
//
//  1. Deep Links: Zeigt ein Anker (#…) auf ein Element in einem eingeklappten
//     Abschnitt, wird der Abschnitt automatisch geöffnet und hingescrollt —
//     Querverweise auf #guide-…/#diag-…-Anker funktionieren so weiterhin.
//  2. Drucken: Vor dem Druck werden alle Abschnitte geöffnet, danach wieder
//     in den vorherigen Zustand versetzt.
(function () {
  "use strict";

  function oeffnePfad(el) {
    var geoeffnet = false;
    for (var d = el; d; d = d.parentElement) {
      if (d.tagName === "DETAILS" && !d.open) {
        d.open = true;
        geoeffnet = true;
      }
    }
    return geoeffnet;
  }

  function zumAnker() {
    if (!location.hash) return;
    var ziel = null;
    try {
      ziel = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    } catch (e) { /* ungültiger Hash */ }
    if (ziel && oeffnePfad(ziel)) {
      ziel.scrollIntoView();
    }
  }

  window.addEventListener("hashchange", zumAnker);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", zumAnker);
  } else {
    zumAnker();
  }

  window.addEventListener("beforeprint", function () {
    document.querySelectorAll("details.fold:not([open])").forEach(function (d) {
      d.setAttribute("data-druck-zu", "");
      d.open = true;
    });
  });
  window.addEventListener("afterprint", function () {
    document.querySelectorAll("details.fold[data-druck-zu]").forEach(function (d) {
      d.removeAttribute("data-druck-zu");
      d.open = false;
    });
  });
})();
