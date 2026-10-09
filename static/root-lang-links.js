/*
 * root-lang-links.js — Seiten außerhalb der Sprachbäume (Belegseiten spec/figures/*, spec/snippets/*).
 *
 * Diese Seiten liegen einmal unter <wurzel>/spec/… (lib_docmodel.render_page mit page["root_level"]) und
 * verweisen für Kopf, Brotkrumen und Belege in den kanonischen Sprachbaum (<wurzel>de/…). Das Skript lenkt
 * diese Verweise (Links und das Suchformular) auf die Sprache der Besucherin um, nach derselben Regel wie
 * index.html und spec/record.html: gemerkte Wahl (localStorage "autodocs_user_lang"), sonst die Sprache der
 * Seite, von der sie kam, sonst die Browsersprache, sonst Deutsch. Ein Klick auf eine Flagge merkt die Wahl.
 *
 * Einbindung: <script src="<wurzel>static/root-lang-links.js" data-root="<wurzel>" data-lang="de" defer>.
 * Der reine Kern (pickLang) ist unter Node als module.exports verfügbar.
 */
(function (root, factory) {
  var core = factory();
  if (typeof module === "object" && module.exports) module.exports = core;
  else root.RootLangLinks = core;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";
  var LANGS = ["de", "en", "es", "pt", "fr", "ru", "ar", "hi", "ko", "zh", "nl"];

  // o: { saved, referrer, origin, base, languages, dflt } -> Sprachkürzel
  function pickLang(o) {
    if (o.saved && LANGS.indexOf(o.saved) >= 0) return o.saved;
    try {
      var r = new URL(o.referrer || "");
      if (r.origin === o.origin && r.pathname.indexOf(o.base) === 0) {
        var seg = r.pathname.slice(o.base.length).split("/")[0];
        if (LANGS.indexOf(seg) >= 0) return seg;
      }
    } catch (e) { /* kein oder fremder Referrer */ }
    var nav = o.languages || [];
    for (var i = 0; i < nav.length; i++) {
      var code = String(nav[i] || "").toLowerCase().split("-")[0];
      if (LANGS.indexOf(code) >= 0) return code;
    }
    return o.dflt || "de";
  }

  // Präfix <wurzel><von>/ in <wurzel><nach>/ umschreiben; andere Verweise bleiben
  function retargetHref(href, rootPrefix, from, to) {
    var a = rootPrefix + from + "/";
    if (!href || from === to || href.indexOf(a) !== 0) return href;
    return rootPrefix + to + "/" + href.slice(a.length);
  }

  return { LANGS: LANGS, pickLang: pickLang, retargetHref: retargetHref };
});

(function () {
  "use strict";
  if (typeof document === "undefined") return;
  var C = typeof module === "object" && module.exports ? null : window.RootLangLinks;
  if (!C) return;
  var KEY = "autodocs_user_lang";
  var me = document.currentScript;
  var rootPrefix = (me && me.getAttribute("data-root")) || "";
  var dflt = (me && me.getAttribute("data-lang")) || "de";
  var saved = null;
  try { saved = window.localStorage.getItem(KEY); } catch (e) { /* gesperrt */ }
  var base = "/";
  try { base = new URL(rootPrefix || "./", window.location.href).pathname; } catch (e) { /* ignore */ }
  var lang = C.pickLang({ saved: saved, referrer: document.referrer, origin: window.location.origin, base: base,
                          languages: navigator.languages || [navigator.language || ""], dflt: dflt });

  function apply() {
    if (lang !== dflt) {
      document.querySelectorAll("a[href]:not([data-set-lang]), form[action]").forEach(function (el) {
        var attr = el.tagName === "FORM" ? "action" : "href";
        var v = el.getAttribute(attr);
        var n = C.retargetHref(v, rootPrefix, dflt, lang);
        if (n !== v) el.setAttribute(attr, n);
      });
    }
    document.documentElement.setAttribute("data-link-lang", lang);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", apply);
  else apply();

  document.addEventListener("click", function (e) {
    var a = e.target && e.target.closest ? e.target.closest("a[data-set-lang]") : null;
    if (!a) return;
    try { window.localStorage.setItem(KEY, a.getAttribute("data-set-lang")); } catch (err) { /* gesperrt */ }
  });
})();
