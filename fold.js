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

  function syncShellControls() {
    var root = document.documentElement;
    var themeBtn = document.querySelector("[data-theme-toggle]");
    var densBtn = document.querySelector("[data-density-toggle]");
    var prefsLabel = document.querySelector("[data-prefs-label]");
    var theme = root.getAttribute("data-theme") || "light";
    var dens = root.getAttribute("data-density") || "comfortable";
    if (themeBtn) {
      themeBtn.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
      themeBtn.textContent = theme === "dark" ? "Dark" : "Light";
    }
    if (densBtn) {
      densBtn.setAttribute("aria-pressed", dens === "compact" ? "true" : "false");
      densBtn.textContent = dens === "compact" ? "Compact" : "Comfortable";
    }
    if (prefsLabel) {
      prefsLabel.textContent = (theme === "dark" ? "Dark" : "Light") + " · " + (dens === "compact" ? "Compact" : "Comfort");
    }
  }

  function bindShellControls() {
    var root = document.documentElement;
    var themeBtn = document.querySelector("[data-theme-toggle]");
    var densBtn = document.querySelector("[data-density-toggle]");
    var searchBtn = document.querySelector("[data-search-open]");
    var searchInput = document.querySelector("[data-search-input]");
    if (themeBtn) {
      themeBtn.addEventListener("click", function () {
        var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
        root.setAttribute("data-theme", next);
        try { localStorage.setItem("autodocs-theme", next); } catch (e) {}
        syncShellControls();
      });
    }
    if (densBtn) {
      densBtn.addEventListener("click", function () {
        var next = root.getAttribute("data-density") === "compact" ? "comfortable" : "compact";
        root.setAttribute("data-density", next);
        try { localStorage.setItem("autodocs-density", next); } catch (e) {}
        syncShellControls();
      });
    }
    if (searchBtn && searchInput) {
      searchBtn.addEventListener("click", function () {
        searchInput.focus();
      });
    }

    document.addEventListener("click", function (e) {
      document.querySelectorAll("details.universe-dropdown[open], details.shell-dropdown[open], details.shell-prefs[open], details[data-ai-model-widget][open]").forEach(function (d) {
        if (!d.contains(e.target)) {
          d.removeAttribute("open");
        }
      });
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        document.querySelectorAll("details.universe-dropdown[open], details.shell-dropdown[open], details.shell-prefs[open], details[data-ai-model-widget][open]").forEach(function (d) {
          d.removeAttribute("open");
        });
      }
    });

    try {
      var savedFolds = JSON.parse(sessionStorage.getItem("autodocs-open-folds") || "[]");
      if (Array.isArray(savedFolds) && savedFolds.length > 0) {
        savedFolds.forEach(function (id) {
          var el = document.getElementById(id);
          if (el && el.tagName === "DETAILS") {
            el.open = true;
          }
        });
      }
      document.querySelectorAll("details.fold[id]").forEach(function (d) {
        d.addEventListener("toggle", function () {
          try {
            var currentOpen = Array.from(document.querySelectorAll("details.fold[id][open]")).map(function (el) { return el.id; });
            sessionStorage.setItem("autodocs-open-folds", JSON.stringify(currentOpen));
          } catch (err) {}
        });
      });
    } catch (e) {}

    syncShellControls();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindShellControls);
  } else {
    bindShellControls();
  }
})();
