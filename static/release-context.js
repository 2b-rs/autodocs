/*
 * release-context.js — das gewählte Release geht bei jeder Navigation mit (alle Seiten, defer, nach fold.js).
 *
 * Quelle des aktiven Releases (gleich für alle Seitentypen, _src/WARTUNG.md „Release-Kontext“):
 *   1. URL: ?release=… (Record-Seite) bzw. #release=… (Seiten der Universen),
 *   2. sonst die gespeicherte Wahl dieses Browsers je Universum (localStorage "autodocs-release",
 *      geschrieben bei einer Wahl im Release-Menü oder auf der Record-Seite),
 *   3. sonst der Standard (jüngstes Release des Menüs; wird nicht in Verweise geschrieben).
 * Das Kopfskript der Seite (lib_release_context.boot_script) übernimmt Schritt 2 schon vor dem ersten
 * Zeichnen in die URL; danach gilt nur noch die URL.
 *
 * Verweise: Ziele mit releaseabhängigem Inhalt bekommen das Release in ihrer eigenen Form —
 * Seiten der Universen (adaptive/, modules/, namespaces/, classes/, services/, classic/, score/)
 * #release=…, nur wenn das Universum des Ziels dieses Release kennt (sonst dessen gespeicherte Wahl);
 * spec/record.html ?release=…. Releaseunabhängig (keine Änderung): Versions-Explorer, Snippet- und
 * Schaubildseiten (zeigen alle Releases nebeneinander), Berichte, Startseite. Links im Inhalt und in
 * der Brotkrumenleiste werden sofort umgeschrieben (sichtbar beim Überfahren und Kopieren), Kopf-Links
 * erst beim Klick (der Seitenrouter in fold.js vergleicht die Kopf-Assets zweier Seiten). Ein Release,
 * das ein Verweis schon trägt, bleibt. Wechsel des Releases (Menü, Record-Auswahl, Zurück) schreibt
 * alle Verweise neu.
 *
 * Brotkrumen: Ohne gewähltes Release zeigt das Release-Menü den Standard (jüngstes Release) statt
 * „Release“, damit die Leiste immer sagt, welcher Stand zu sehen ist.
 */
(function (root, factory) {
  var core = factory();
  if (typeof module === "object" && module.exports) module.exports = core;
  else root.AutodocsReleaseCore = core;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";
  var LANGS = ["de", "en", "es", "pt", "fr", "ru", "ar", "hi", "ko", "zh", "nl"];
  var STORE = "autodocs-release";

  function releaseOf(search, hash) {
    var m = /[?&]release=([^&#]+)/.exec(search || "");
    if (m) { try { return decodeURIComponent(m[1]).trim(); } catch (e) { return m[1]; } }
    var h = String(hash || "").replace(/^#/, "");
    try { h = decodeURIComponent(h); } catch (e) { /* unkodiert */ }
    m = /(?:^|&)release=([^&]*)/.exec(h);
    return m ? String(m[1] || "").trim() : "";
  }

  // Pfad relativ zur Site-Wurzel (ohne Sprachbaum) -> { kind: "record"|"universe"|"", uni }
  function classify(relPath, cfg) {
    var p = String(relPath || "").replace(/^\/+/, "");
    var seg = p.split("/");
    if (LANGS.indexOf(seg[0]) >= 0) p = seg.slice(1).join("/");
    if (p === "spec/record.html") return { kind: "record", uni: "" };
    var unis = (cfg && cfg.u) || {};
    for (var uid in unis) {
      var pre = unis[uid].p || [];
      for (var k = 0; k < pre.length; k++) if (p.indexOf(pre[k]) === 0) return { kind: "universe", uni: uid };
    }
    return { kind: "", uni: "" };
  }

  function stored(uni) {
    try { var all = JSON.parse(window.localStorage.getItem(STORE) || "{}") || {}; return uni ? all[uni] || "" : all; }
    catch (e) { return uni ? "" : {}; }
  }
  function store(uni, rel) {
    if (!uni || !rel) return;
    try {
      var all = JSON.parse(window.localStorage.getItem(STORE) || "{}") || {};
      all[uni] = rel;
      window.localStorage.setItem(STORE, JSON.stringify(all));
    } catch (e) { /* privater Modus: nur die URL */ }
  }

  // Release für ein Ziel: das aktive, wenn das Ziel es kennt; sonst die gespeicherte Wahl seines Universums
  function releaseFor(target, active, cfg, storedMap) {
    if (!target.kind) return "";
    if (target.kind === "record") return active || "";
    var rels = (((cfg && cfg.u) || {})[target.uni] || {}).r || [];
    if (active && rels.indexOf(active) >= 0) return active;
    var st = storedMap && storedMap[target.uni];
    return st && rels.indexOf(st) >= 0 ? st : "";
  }

  // href (Original) + Release -> neues href; Form je Ziel (Record: Query, sonst Hash); vorhandenes Release bleibt
  function withRelease(href, base, target, rel) {
    var u;
    try { u = new URL(href, base); } catch (e) { return href; }
    if (releaseOf(u.search, u.hash)) return href;
    if (!rel) return href;
    if (target.kind === "record") {
      u.searchParams.set("release", rel);
    } else {
      var h = (u.hash || "").replace(/^#/, "");
      var parts = h ? h.split("&").filter(function (x) { return x && x.indexOf("release=") !== 0; }) : [];
      var anchor = parts.filter(function (x) { return x.indexOf("=") < 0; }).slice(0, 1);
      var rest = parts.filter(function (x) { return x.indexOf("=") >= 0; });
      u.hash = anchor.concat(["release=" + encodeURIComponent(rel)], rest).join("&");
    }
    return u.pathname + u.search + u.hash;
  }

  return { releaseOf: releaseOf, classify: classify, releaseFor: releaseFor, withRelease: withRelease,
           stored: stored, store: store, STORE: STORE, LANGS: LANGS };
});

(function () {
  "use strict";
  if (typeof document === "undefined") return;
  var R = window.AutodocsReleaseCore;
  var cfg = window.__autodocsRelease || null;
  if (!R || !cfg) return;
  var SELF = document.currentScript;
  var siteRoot = (function () {
    var m = /^(.*\/)static\/release-context\.js(?:[?#].*)?$/.exec((SELF && SELF.src) || "");
    return m ? new URL(m[1]).pathname : "/";
  })();

  function active() {
    var rel = R.releaseOf(location.search, location.hash);
    if (rel) return rel;
    // Seiten ohne eigenes Release (Berichte, Explorer, Belegseiten): nichts Aktives, Ziele nehmen ihre
    // gespeicherte Wahl (releaseFor)
    return "";
  }
  function targetOf(url) {
    if (url.origin !== location.origin || url.pathname.indexOf(siteRoot) !== 0) return { kind: "", uni: "" };
    return R.classify(url.pathname.slice(siteRoot.length), cfg);
  }
  function rewriteLink(a, rel, st) {
    if (a.closest("details.release-dropdown, .langs")) return;
    // Original merken; setzt ein Seitenskript das href später neu (z. B. Record: Explorer-Knopf), gilt das neue
    var cur = a.getAttribute("href");
    var orig = a.getAttribute("data-rel-orig");
    if (orig === null || cur !== a.getAttribute("data-rel-set")) {
      orig = cur;
      if (!orig || orig.charAt(0) === "#" || /^(?:[a-z]+:|\/\/)/i.test(orig) && orig.indexOf(location.origin) !== 0) return;
      a.setAttribute("data-rel-orig", orig);
    }
    var url;
    try { url = new URL(orig, location.href); } catch (e) { return; }
    var target = targetOf(url);
    var next = target.kind ? R.withRelease(orig, location.href, target, R.releaseFor(target, rel, cfg, st)) : orig;
    if (a.getAttribute("href") !== next) a.setAttribute("href", next);
    a.setAttribute("data-rel-set", next);
  }
  // Inhalt und Brotkrumen sofort; Kopf (außerhalb von <main> und der Brotkrumenleiste) erst beim Klick
  function scopes() {
    var out = [];
    var main = document.querySelector("main");
    if (main) out.push(main);
    var bar = document.querySelector(".crumbbar") || document.querySelector("nav.crumbs");
    if (bar) out.push(bar);
    return out;
  }
  function rewriteAll(rootEl) {
    var rel = active(), st = R.stored();
    (rootEl ? [rootEl] : scopes()).forEach(function (s) {
      s.querySelectorAll("a[href]").forEach(function (a) { rewriteLink(a, rel, st); });
    });
  }
  document.addEventListener("click", function (e) {
    var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
    if (!a) return;
    // Wahl im Release-Menü einer Universumsseite merken (fold.js setzt danach #release=)
    var menu = a.closest("details.release-dropdown");
    if (menu) {
      var rel = a.getAttribute("data-release") || R.releaseOf("", (a.getAttribute("href") || "").replace(/^[^#]*/, "")) ||
        String(a.textContent || "").trim();
      if (cfg.page) R.store(cfg.page, rel);
      return;
    }
    rewriteLink(a, active(), R.stored());
  }, true);

  // Ohne gewähltes Release: Standard (jüngstes Release des Menüs) als Brotkrume statt „Release“
  function showDefault() {
    if (!cfg.page || active()) return;
    document.querySelectorAll("details.release-dropdown").forEach(function (d) {
      if (d.closest(".rec-release-nav")) return;
      var first = d.querySelector(".releases a");
      var sum = d.querySelector("summary");
      if (!first || !sum) return;
      var rel = first.getAttribute("data-release") || String(first.textContent || "").trim();
      var caret = sum.querySelector(".dropdown-caret");
      Array.prototype.slice.call(sum.childNodes).forEach(function (n) { if (n !== caret) sum.removeChild(n); });
      sum.insertBefore(document.createTextNode(rel + (caret ? " " : "")), caret || null);
      sum.classList.add("is-default-release");
    });
  }
  function refresh() {
    document.querySelectorAll("summary.is-default-release").forEach(function (s) { s.classList.remove("is-default-release"); });
    rewriteAll();
    showDefault();
  }

  var pending = null;
  function later(node) {
    if (!pending) {
      pending = [];
      (window.requestAnimationFrame || setTimeout)(function () {
        var nodes = pending;
        pending = null;
        var rel = active(), st = R.stored();
        nodes.forEach(function (n) {
          if (!n.isConnected) return;
          if (n.matches && n.matches("a[href]")) rewriteLink(n, rel, st);
          if (n.querySelectorAll) n.querySelectorAll("a[href]").forEach(function (a) { rewriteLink(a, rel, st); });
        });
      });
    }
    pending.push(node);
  }
  function watch() {
    if (!window.MutationObserver) return;
    var mo = new MutationObserver(function (list) {
      list.forEach(function (m) {
        m.addedNodes.forEach(function (n) {
          if (n.nodeType === 1 && (n.closest("main") || n.closest(".crumbbar"))) later(n);
        });
      });
    });
    mo.observe(document.body, { childList: true, subtree: true });
  }

  window.addEventListener("hashchange", refresh);
  window.addEventListener("popstate", refresh);
  window.addEventListener("autodocs:release", refresh);
  window.addEventListener("autodocs:navigated", refresh);
  window.AutodocsRelease = { refresh: refresh, active: active, store: R.store, stored: R.stored, config: cfg };
  function start() { refresh(); watch(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
