/*
 * evidence-sections.js — Abschnitte des Versions-Explorers auf den kanonischen Belegseiten
 * (spec/snippets/<stamm>.html, spec/figures/FIG-*.html).
 *
 * Gleiche Daten wie der Explorer-Viewer: versions/explorer/items/<stamm>.json (export_explorer.py), für
 * Snippets ergänzt um den Wortlaut je Release aus dem Pack (static/frozen-pack.js, Felder rv/rt/rk).
 *   Snippet:   „Versionen & Provenienz“ (Zeitachse über die Releases mit Vergleich zweier Fassungen,
 *              VersionsExplorerCore.revisionKit().mountSnippet – derselbe Code wie im Explorer) und
 *              „Zugeordnete Elemente (n)“.
 *   Schaubild: „Zugeordnete Elemente (n)“ (Fassungen und Vergleich zeigt die Seite schon über
 *              series-explorer.js).
 * Voraussetzungen auf der Seite: static/versions-explorer-i18n.js, static/versions-explorer.js (nur der Kern;
 * ohne #ve-app startet die Explorer-Oberfläche nicht), static/text-diff.js, static/frozen-pack.js.
 * Ohne Skript oder ohne Explorer-Eintrag bleibt der Hinweis mit dem Explorer-Link stehen.
 */
(function () {
  "use strict";
  if (typeof document === "undefined") return;
  var script = document.currentScript;
  var m = /^(.*\/)static\/evidence-sections\.js(?:[?#].*)?$/.exec((script && script.src) || "");
  var ROOT = m ? m[1] : "../../";

  function esc(s) {
    return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  var I = (window.VE_I18N && window.VE_I18N.de) || {};
  function t(key, vars) {
    var s = I[key] != null ? I[key] : key;
    if (vars) Object.keys(vars).forEach(function (k) { s = s.split("{" + k + "}").join(vars[k]); });
    return s;
  }
  function spanText(rels) { rels = rels || []; return rels.length > 1 ? rels[0] + " → " + rels[rels.length - 1] : (rels[0] || "–"); }
  function recordHref(id) { return ROOT + "spec/record.html?id=" + encodeURIComponent(id); }   // Trampolin → Sprache

  function targetsHtml(info, series) {
    var targets = info.targets || [];
    var h = '<h3>' + esc(t("targets_head", { n: targets.length })) + "</h3>";
    if (series) h += '<p class="ev-muted">Zuordnungen der Bildreihe (Basis <code>' + esc(info.id) + "</code>), wie im Versions-Explorer.</p>";
    if (!targets.length) return h + '<p class="ev-muted">' + esc(t("no_data")) + "</p>";
    h += '<ul class="ev-targets">';
    targets.forEach(function (tg) {
      var bits = [];
      if (tg.rel && tg.rel.length) bits.push(esc(spanText(tg.rel)));
      if (tg.role) bits.push('<span class="ev-role ev-role-' + esc(tg.role) + '">' + esc(t("role_" + tg.role)) + "</span>");
      if (tg.conf != null) bits.push(esc(t("conf", { p: Math.round(tg.conf * 100) })));
      if (tg.m) bits.push(esc(t("by", { m: tg.m })));
      h += '<li><a class="swsref" href="' + esc(recordHref(tg.id)) + '"><code>' + esc(tg.id) + "</code></a>" +
        (bits.length ? '<div class="ev-meta">' + bits.join('<span aria-hidden="true"> · </span>') + "</div>" : "") +
        (tg.why ? '<div class="ev-why"><span>' + esc(t("why")) + ":</span> " + esc(tg.why) + "</div>" : "") + "</li>";
    });
    return h + "</ul>";
  }

  function loadItem(id, stems) {
    var i = 0;
    function next() {
      if (i >= stems.length) return Promise.resolve(null);
      var stem = stems[i++];
      return fetch(ROOT + "versions/explorer/items/" + encodeURIComponent(stem) + ".json").then(function (r) {
        return r.ok ? r.json() : null;
      }).catch(function () { return null; }).then(function (info) {
        // Kennungen, die sich nur in der Schreibweise unterscheiden, teilen sich auf manchen Dateisystemen den Stamm
        return info && info.id === id ? info : next();
      });
    }
    return next();
  }

  function run() {
    var host = document.querySelector("[data-evidence-sections]");
    var C = window.VersionsExplorerCore, TD = window.TextDiff;
    if (!host || !C) return;
    var id = host.getAttribute("data-id"), kind = host.getAttribute("data-kind");
    var stems = [host.getAttribute("data-item"), C.safeStem(id)].filter(function (s, k, a) { return s && a.indexOf(s) === k; });
    loadItem(id, stems).then(function (info) {
      if (!info) return null;
      if (kind !== "snip" || typeof FrozenPack === "undefined") return info;
      return FrozenPack.record(ROOT, id).catch(function () { return null; }).then(function (rec) {
        if (rec && rec.rv && !info.rv) { info.rv = rec.rv; info.rt = rec.rt; info.rk = rec.rk; }
        return info;
      });
    }).then(function (info) {
      if (!info) return;   // kein Explorer-Eintrag: Hinweis bleibt
      var html = "";
      if (kind === "snip") html += '<section class="ev-card" data-role="versions"><h3>' + esc(t("v_ver")) + '</h3><div class="ev-rev"></div></section>';
      html += '<section class="ev-card" data-role="targets">' + targetsHtml(info, kind === "fig" && host.getAttribute("data-series") === "1") + "</section>";
      host.innerHTML = html;
      var rev = host.querySelector(".ev-rev");
      // Zeitachse und Vergleich wie im Explorer-Viewer (geteilter Baukasten C.revisionKit)
      if (rev && TD && C.revisionKit) C.revisionKit({ t: t, esc: esc, TD: TD, root: ROOT }).mountSnippet(rev, info, { mode: "side" });
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run);
  else run();
})();
