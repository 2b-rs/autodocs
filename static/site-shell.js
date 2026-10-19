/*
 * site-shell.js — site-shell@1: zentrale, fehlertolerante Aktualisierung der Kopfzeile.
 *
 * Das vollständig bedienbare HTML bleibt in page.html.tmpl. Dieses Skript ersetzt keine
 * Header-, Such- oder Bedienknoten, damit ai-access.js, fold.js, review.js und
 * review_request.js ihre bestehenden Light-DOM-Selektoren und Listener behalten.
 */
(function (root, factory) {
  "use strict";
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else {
    root.AutodocsSiteShell = api;
    if (typeof document !== "undefined") api.boot(document);
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  var SCHEMA = "site-shell@1";
  var LANGS = ["de", "en", "es", "pt", "fr", "ru", "ar", "hi", "ko", "zh", "nl", "id", "bn", "ja", "he"];
  var REQUIRED_DOMAINS = ["explore", "pipeline", "context", "versions", "extract", "build", "curate", "review", "trace", "work"];
  var ALLOWED_EXTERNAL = { "https://autodocs-nexos.autodocs-2b-rs.workers.dev/dashboard": true };
  var ID = /^[a-z][a-z0-9-]{0,31}$/;
  var SAFE_PATH = /^(?!\/)(?!.*(?:^|\/)\.\.(?:\/|$))(?!.*[\\:])[A-Za-z0-9._~\-/]+(?:#[A-Za-z0-9._~%=&\-]+)?$/;

  function own(obj, key) { return Object.prototype.hasOwnProperty.call(obj, key); }
  function text(value) { return typeof value === "string" && value.trim() ? value : null; }
  function supportedLang(value) {
    value = String(value || "").toLowerCase().split("-")[0];
    return LANGS.indexOf(value) >= 0 ? value : "en";
  }
  function safePrefix(value) {
    value = String(value || "");
    return /^(?:\.\.\/)*$/.test(value) ? value : null;
  }
  function safeLangPrefix(value) {
    value = String(value || "");
    return /^(?:\.\.\/)*(?:(?:de|en|es|pt|fr|ru|ar|hi|ko|zh|nl|id|bn|ja|he)\/)?$/.test(value) ? value : null;
  }
  function validTarget(target) {
    if (!target || typeof target !== "object" || Array.isArray(target)) return null;
    if (target.kind === "lang" || target.kind === "root") {
      var path = text(target.path);
      return path && SAFE_PATH.test(path) ? { kind: target.kind, path: path } : null;
    }
    if (target.kind === "external") {
      var href = text(target.href);
      return href && own(ALLOWED_EXTERNAL, href) ? { kind: "external", href: href } : null;
    }
    return null;
  }
  function validateConfig(raw) {
    if (!raw || raw.schema !== SCHEMA || !text(raw.revision) || !text(raw.project_title)) return null;
    if (!Array.isArray(raw.domains) || raw.domains.length !== REQUIRED_DOMAINS.length ||
        !raw.labels || typeof raw.labels !== "object") return null;
    var domains = [], seen = {};
    for (var i = 0; i < raw.domains.length; i++) {
      var d = raw.domains[i], target;
      if (!d || !ID.test(d.id || "") || seen[d.id] || (d.group !== "primary" && d.group !== "legacy")) return null;
      target = validTarget(d.target);
      if (!target) return null;
      seen[d.id] = true;
      domains.push({ id: d.id, group: d.group, target: target });
    }
    if (REQUIRED_DOMAINS.some(function (id) { return !seen[id]; })) return null;
    var labels = {};
    for (var l = 0; l < LANGS.length; l++) {
      var lang = LANGS[l], src = raw.labels[lang], names = {};
      if (!src || !text(src.nav) || !text(src.legacy) || !text(src.search) ||
          !text(src.search_placeholder) || !text(src.review) || !text(src.review_aria) ||
          !src.domains || typeof src.domains !== "object") return null;
      for (var j = 0; j < domains.length; j++) {
        var id = domains[j].id, label = text(src.domains[id]);
        if (!label) return null;
        names[id] = label;
      }
      labels[lang] = {
        nav: src.nav, legacy: src.legacy, search: src.search,
        search_placeholder: src.search_placeholder, review: src.review,
        review_aria: src.review_aria, domains: names
      };
    }
    return { schema: SCHEMA, revision: raw.revision, project_title: raw.project_title, domains: domains, labels: labels };
  }
  function liveLangPrefix(host) {
    var home = host && host.querySelector ? host.querySelector("a.home") : null;
    var href = home && home.getAttribute("href");
    if (href && href.slice(-10) === "index.html") return safeLangPrefix(href.slice(0, -10));
    return safeLangPrefix(host && host.getAttribute("data-shell-lang-prefix"));
  }
  function resolveHref(target, prefixes) {
    var valid = validTarget(target);
    if (!valid) return null;
    if (valid.kind === "external") return valid.href;
    var prefix = valid.kind === "lang" ? safeLangPrefix(prefixes && prefixes.lang) : safePrefix(prefixes && prefixes.root);
    return prefix === null ? null : prefix + valid.path;
  }
  function applyConfig(doc, raw) {
    var config = validateConfig(raw);
    var host = doc && doc.querySelector && doc.querySelector("header.shell[data-site-shell]");
    if (!config || !host) return false;
    var linkedLang = doc.documentElement && doc.documentElement.getAttribute &&
      doc.documentElement.getAttribute("data-link-lang");
    var lang = supportedLang(linkedLang || host.getAttribute("data-shell-lang") ||
      (doc.documentElement && doc.documentElement.lang));
    var labels = config.labels[lang] || config.labels.en;
    var langPrefix = liveLangPrefix(host), rootPrefix = safePrefix(host.getAttribute("data-shell-root-prefix"));
    if (langPrefix === null || rootPrefix === null) return false;
    var hrefs = {}, byId = {};
    for (var i = 0; i < config.domains.length; i++) {
      var domain = config.domains[i];
      var href = resolveHref(domain.target, { lang: langPrefix, root: rootPrefix });
      if (!href) return false;
      hrefs[domain.id] = href;
      byId[domain.id] = domain;
    }

    var title = host.querySelector("a.home");
    if (title) title.textContent = config.project_title;
    var nav = host.querySelector("nav.shell-domains");
    if (nav) nav.setAttribute("aria-label", labels.nav);
    var legacy = host.querySelector(".shell-legacy > summary");
    if (legacy) legacy.textContent = labels.legacy;
    var links = host.querySelectorAll("a[data-domain]");
    for (var k = 0; k < links.length; k++) {
      var id = links[k].getAttribute("data-domain");
      if (!own(byId, id)) continue;
      links[k].textContent = labels.domains[id];
      links[k].setAttribute("href", hrefs[id]);
    }
    var active = host.getAttribute("data-shell-active-domain") || "explore";
    if (!own(byId, active)) active = "explore";
    for (var m = 0; m < links.length; m++) {
      if (links[m].getAttribute("data-domain") === active) links[m].setAttribute("aria-current", "page");
      else links[m].removeAttribute("aria-current");
    }
    var current = host.querySelector(".domain-current");
    if (current) current.textContent = labels.domains[active];

    var form = host.querySelector("form.shell-search"), input = host.querySelector("[data-search-input]");
    if (form) form.setAttribute("action", hrefs.explore);
    if (input) {
      input.setAttribute("placeholder", labels.search_placeholder);
      var searchLabel = form && form.querySelector('label[for="' + input.id + '"]');
      if (searchLabel) searchLabel.textContent = labels.search;
    }
    var reviewbar = host.querySelector(".reviewbar"), reviewButton = host.querySelector("[data-review-open]");
    if (reviewbar) reviewbar.setAttribute("aria-label", labels.review_aria);
    if (reviewButton) {
      var children = reviewButton.children;
      for (var n = 0; n < children.length; n++) {
        if (children[n].tagName === "SPAN" && !children[n].classList.contains("review-count")) {
          children[n].textContent = labels.review;
          break;
        }
      }
    }
    host.setAttribute("data-site-shell-state", "enhanced");
    host.setAttribute("data-site-shell-revision", config.revision);
    return true;
  }
  function configUrl(doc) {
    var script = doc && doc.currentScript;
    if (!script) {
      var scripts = doc && doc.querySelectorAll ? doc.querySelectorAll("script[data-site-shell-config]") : [];
      script = scripts.length ? scripts[scripts.length - 1] : null;
    }
    if (!script) return null;
    var ref = script.getAttribute("data-site-shell-config");
    if (!ref) return null;
    try {
      var url = new URL(ref, doc.baseURI || doc.location.href);
      if (url.origin !== doc.location.origin) return null;
      url.searchParams.set("m", String(Math.floor(Date.now() / 60000)));
      return url.href;
    } catch (e) { return null; }
  }
  function boot(doc) {
    var host = doc && doc.querySelector && doc.querySelector("header.shell[data-site-shell]");
    var url = configUrl(doc);
    if (!host || !url || typeof fetch !== "function") return Promise.resolve(false);
    host.setAttribute("data-site-shell-state", "fallback");
    return fetch(url, { cache: "no-store", credentials: "same-origin", redirect: "error" })
      .then(function (response) {
        if (!response.ok) throw new Error("HTTP " + response.status);
        if (response.url && new URL(response.url).origin !== doc.location.origin) throw new Error("cross-origin response");
        return response.json();
      })
      .then(function (config) {
        var applied = applyConfig(doc, config);
        if (doc.readyState === "loading" && doc.addEventListener) {
          doc.addEventListener("DOMContentLoaded", function () { applyConfig(doc, config); }, { once: true });
        }
        return applied;
      })
      .catch(function () { return false; });
  }
  return {
    SCHEMA: SCHEMA, LANGS: LANGS.slice(), validateConfig: validateConfig,
    validTarget: validTarget, resolveHref: resolveHref, liveLangPrefix: liveLangPrefix,
    applyConfig: applyConfig, configUrl: configUrl, boot: boot
  };
});
