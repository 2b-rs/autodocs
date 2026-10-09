/*
 * figure-images.js — geschützte Schaubilder im Browser (Versions-Explorer, Belegseiten spec/figures/*).
 *
 * Die Bilder liegen nicht auf GitHub Pages und nicht im öffentlichen Repository, sondern in einem privaten
 * Repository hinter dem Worker (proxy/figure-access.mjs, GET <dienst>/fig/<sha256>.webp). Wer angemeldet ist
 * und eine aktive Freigabe hat (oder Verwalter ist), bekommt sie mit dem eigenen Firebase-ID-Token
 * (AiAccess.idToken aus ai-access.js); angezeigt werden sie als blob:-URL. Lokal (localhost, _src/serve.py)
 * kommen sie direkt aus dem Asset-Store (<wurzel>assets/figures/<sha[:2]>/<sha>.webp).
 *
 * Platzhalter im HTML: <div data-fig-sha="<64 hex>" data-fig-alt="…" data-fig-size="big|thumb|tiny"
 * [data-fig-img-class="…"]>. Geladen wird erst, wenn der Platzhalter sichtbar wird (IntersectionObserver).
 * Ohne Zugang sagt der Platzhalter, was fehlt, und bietet die wirksame Aktion an derselben Stelle an:
 * „Anmelden“ (AiAccess.open("signin")), „Zugang anfragen“ (AiAccess.open("request"), dieselbe Freigabe wie
 * das Projektkontingent) oder bei Störungen „Erneut laden“. Ohne eingerichtete Anmeldung gibt es keinen Knopf.
 * Links mit data-fig-full="<sha>" (Vollbild) werden erst sichtbar, wenn das Bild geladen ist.
 *
 * Dienst: ai-access.config.json "bilder_dienst", sonst "projekt_dienst". Texte: Deutsch/Englisch eingebaut,
 * der Explorer reicht seine Übersetzungen über FigureImages.configure({ text }) herein.
 * Der reine Kern ist unter Node als module.exports verfügbar (_src/tests/test_figure_access.py).
 */
(function (root, factory) {
  var core = factory();
  if (typeof module === "object" && module.exports) module.exports = core;
  else root.FigureImagesCore = core;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";
  var SHA_RE = /^[0-9a-f]{64}$/;

  // HTTP-Status des Workers -> Zustand des Platzhalters
  function statusKind(status) {
    if (status === 200) return "ok";
    if (status === 401) return "signin";
    if (status === 403) return "forbidden";
    if (status === 404) return "missing";
    if (status === 429 || status === 503) return "busy";
    return "error";
  }

  function hostLocal(hostname) { return /^(localhost|127\.0\.0\.1|\[::1\]|::1)$/.test(String(hostname || "")); }
  function isLocalHost(loc) { loc = loc || {}; return loc.protocol === "file:" || hostLocal(loc.hostname); }

  // Basis-URL des Bilddienstes: https, http nur für localhost; ohne Pfadreste, Abfrage oder Zugangsdaten
  function serviceFrom(cfg) {
    var raw = String((cfg && (cfg.bilder_dienst || cfg.projekt_dienst)) || "").trim();
    if (!raw) return "";
    var u;
    try { u = new URL(raw); } catch (e) { return ""; }
    if (u.username || u.password || u.search || u.hash) return "";
    if (u.protocol !== "https:" && !(u.protocol === "http:" && hostLocal(u.hostname))) return "";
    return (u.origin + u.pathname).replace(/\/+$/, "");
  }

  function figureUrl(service, sha) { return SHA_RE.test(sha) && service ? service + "/fig/" + sha + ".webp" : ""; }
  function localUrl(root, sha) { return SHA_RE.test(sha) ? root + "assets/figures/" + sha.slice(0, 2) + "/" + sha + ".webp" : ""; }

  // Wurzel der Website aus der Adresse dieses Skripts (…/static/figure-images.js)
  function rootFromSrc(src) {
    var m = /^(.*\/)static\/figure-images\.js(?:[?#].*)?$/.exec(String(src || ""));
    return m ? m[1] : "";
  }

  var TEXTS = {
    de: {
      loading: "Bild wird geladen …",
      signin_t: "Bilder sehen angemeldete Personen mit Freigabe.",
      signin: "Anmelden",
      forbidden_t: "Für Bilder braucht dein Konto eine Freigabe – dieselbe wie für das Projektkontingent.",
      request: "Zugang anfragen",
      private_t: "Bild nicht öffentlich.",
      missing_t: "Bild nicht im Bildarchiv.",
      busy_t: "Zu viele Bildabrufe – bitte kurz warten.",
      error_t: "Bild konnte nicht geladen werden.",
      retry: "Erneut laden"
    },
    en: {
      loading: "Loading image …",
      signin_t: "Images are shown to signed-in people with access.",
      signin: "Sign in",
      forbidden_t: "Your account needs access approval for images – the same approval as for the project quota.",
      request: "Request access",
      private_t: "Image not public.",
      missing_t: "Image not in the image archive.",
      busy_t: "Too many image requests – please wait a moment.",
      error_t: "The image could not be loaded.",
      retry: "Load again"
    }
  };

  return { SHA_RE: SHA_RE, statusKind: statusKind, isLocalHost: isLocalHost, serviceFrom: serviceFrom,
           figureUrl: figureUrl, localUrl: localUrl, rootFromSrc: rootFromSrc, TEXTS: TEXTS };
});

/* ======================================================================== Browser */
(function () {
  "use strict";
  if (typeof document === "undefined" || typeof window === "undefined") return;
  var C = window.FigureImagesCore;
  if (!C || window.FigureImages) return;

  var script = document.currentScript;
  var ROOT = (function () {
    var r = C.rootFromSrc(script && script.src);
    if (r) return r;
    var link = document.querySelector('link[href*="style.css"]');
    return link ? link.href.replace(/style\.css(?:[?#].*)?$/, "") : "";
  })();
  var LOCAL = C.isLocalHost(window.location);
  var LANG = (document.documentElement.getAttribute("lang") || "de").slice(0, 2);
  var textFn = null;
  function tx(key) {
    var v = textFn ? textFn(key) : null;
    if (v && v !== "fi_" + key) return v;
    var d = C.TEXTS[LANG] || C.TEXTS.en;
    return d[key] || C.TEXTS.de[key] || key;
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  // ---------------------------------------------------------------- Zustand
  var S = { service: "", access: "unknown", probeAt: 0, authKey: null, booted: null };
  var urls = new Map();       // sha -> blob:-URL (zuletzt benutzt am Ende)
  var inflight = new Map();   // sha -> Promise<{kind, url?}>
  var queue = [], running = 0;
  var MAX_URLS = 300;

  function boot() {
    if (S.booted) return S.booted;
    var dom = new Promise(function (res) {
      if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", res, { once: true });
      else res();
    });
    S.booted = dom.then(function () {
      return fetch(ROOT + "ai-access.config.json", { cache: "no-cache", credentials: "same-origin" })
        .then(function (r) { return r.ok ? r.json() : {}; })
        .catch(function () { return {}; });
    }).then(function (cfg) { S.service = C.serviceFrom(cfg); });
    return S.booted;
  }

  function api() { return window.AiAccess || null; }
  function authOffered() {
    var A = api(), s = A && A.snapshot ? A.snapshot() : null;
    return !!(A && typeof A.open === "function" && s && s.auth !== "unconfigured");
  }
  function token(force) {
    var A = api();
    if (!A || typeof A.idToken !== "function") return Promise.resolve(null);
    return Promise.resolve(A.idToken(force)).catch(function () { return null; });
  }

  function remember(sha, url) {
    urls.delete(sha);
    urls.set(sha, url);
    if (urls.size <= MAX_URLS) return;
    for (var [k, v] of urls) {
      if (urls.size <= MAX_URLS) break;
      if (document.querySelector('img[src="' + v + '"]')) continue;   // noch angezeigt
      urls.delete(k);
      try { URL.revokeObjectURL(v); } catch (e) { /* ignore */ }
    }
  }

  function blocked() {
    if (!S.service) return "private";
    if (S.access === "signin" || S.access === "forbidden" || S.access === "private") return S.access;
    return null;
  }

  // ---------------------------------------------------------------- Darstellung
  var ICON = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">' +
    '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>';
  var ICON_IMG = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">' +
    '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/></svg>';
  var VIEW = {
    loading: { t: "loading", ico: ICON_IMG },
    signin: { t: "signin_t", act: "signin", label: "signin", ico: ICON },
    forbidden: { t: "forbidden_t", act: "request", label: "request", ico: ICON },
    private: { t: "private_t", ico: ICON },
    missing: { t: "missing_t", ico: ICON_IMG },
    busy: { t: "busy_t", act: "retry", label: "retry", ico: ICON_IMG },
    error: { t: "error_t", act: "retry", label: "retry", ico: ICON_IMG }
  };

  function sizeOf(el) { return el.getAttribute("data-fig-size") || "thumb"; }

  function placeholder(el, kind) {
    var v = VIEW[kind] || VIEW.error;
    var size = sizeOf(el);
    var text = tx(v.t);
    el.setAttribute("data-fig-state", kind);
    el.classList.remove("fia-loaded");
    var html;
    if (size === "tiny") {
      html = v.act
        ? '<button type="button" class="fia-btn fia-icobtn" data-fig-act="' + v.act + '" title="' + esc(text + " " + tx(v.label)) +
          '" aria-label="' + esc(text + " " + tx(v.label)) + '">' + v.ico + "</button>"
        : '<span class="fia-ico" role="img" title="' + esc(text) + '" aria-label="' + esc(text) + '">' + v.ico + "</span>";
    } else {
      html = '<span class="fia-ico">' + v.ico + '</span><span class="fia-t">' + esc(text) + "</span>" +
        (v.act ? '<button type="button" class="fia-btn" data-fig-act="' + v.act + '">' + esc(tx(v.label)) + "</button>" : "");
    }
    el.innerHTML = '<div class="fia fia-' + kind + " fia-" + size + '"' + (kind === "loading" ? ' aria-busy="true"' : "") + ">" + html + "</div>";
  }

  function show(el, url) {
    var sha = el.getAttribute("data-fig-sha");
    var img = document.createElement("img");
    img.alt = el.getAttribute("data-fig-alt") || "";
    img.decoding = "async";
    var cls = el.getAttribute("data-fig-img-class");
    if (cls) img.className = cls;
    img.src = url;
    el.innerHTML = "";
    el.appendChild(img);
    el.setAttribute("data-fig-state", "ok");
    el.classList.add("fia-loaded");
    document.querySelectorAll('[data-fig-full="' + sha + '"]').forEach(function (a) { a.href = url; a.hidden = false; });
  }

  // ---------------------------------------------------------------- Laden
  function request(sha, tok) {
    return fetch(C.figureUrl(S.service, sha), { headers: { Authorization: "Bearer " + tok }, credentials: "omit", mode: "cors" });
  }

  function getFigure(sha) {
    if (inflight.has(sha)) return inflight.get(sha);
    var p = token(false).then(function (tok) {
      if (!tok) { S.access = authOffered() ? "signin" : "private"; return { kind: S.access }; }
      return request(sha, tok).then(function (res) {
        if (res.status !== 401) return res;
        return token(true).then(function (t2) { return t2 ? request(sha, t2) : res; });
      }).then(function (res) {
        var kind = C.statusKind(res.status);
        if (kind === "ok") {
          return res.blob().then(function (b) {
            var url = URL.createObjectURL(b);
            remember(sha, url);
            S.access = "ok";
            return { kind: "ok", url: url };
          });
        }
        if (kind === "signin" || kind === "forbidden") { S.access = kind; S.probeAt = Date.now(); }
        return { kind: kind };
      });
    }).catch(function () { return { kind: "error" }; }).then(function (r) { inflight.delete(sha); return r; });
    inflight.set(sha, p);
    return p;
  }

  function loadOne(el) {
    var sha = el.getAttribute("data-fig-sha");
    if (urls.has(sha)) { var u = urls.get(sha); remember(sha, u); show(el, u); return Promise.resolve(); }
    var b = blocked();
    if (b) { placeholder(el, b); return Promise.resolve(); }
    if (el.getAttribute("data-fig-state") !== "loading") placeholder(el, "loading");
    return getFigure(sha).then(function (r) {
      if (!el.isConnected) return;
      if (r.url) show(el, r.url);
      else placeholder(el, r.kind);
    });
  }

  function limit() { return S.access === "ok" ? 4 : 1; }
  function pump() {
    boot().then(function () {
      while (queue.length && running < limit()) {
        var el = queue.shift();
        if (!el.isConnected) continue;
        running++;
        loadOne(el).catch(function () { placeholder(el, "error"); }).then(function () { running--; pump(); });
      }
    });
  }
  function enqueue(el) {
    if (queue.indexOf(el) < 0) queue.push(el);
    pump();
  }

  function start(el) {
    var sha = el.getAttribute("data-fig-sha") || "";
    if (!C.SHA_RE.test(sha)) { placeholder(el, "missing"); return; }
    if (urls.has(sha)) { show(el, urls.get(sha)); return; }
    if (LOCAL && !el.__figLocalFailed) {
      // Lokal: direkt aus dem Asset-Store von serve.py; fehlt die Datei, über den Dienst wie öffentlich
      var img = document.createElement("img");
      img.alt = el.getAttribute("data-fig-alt") || "";
      img.decoding = "async";
      var cls = el.getAttribute("data-fig-img-class");
      if (cls) img.className = cls;
      img.onload = function () {
        el.setAttribute("data-fig-state", "ok");
        el.classList.add("fia-loaded");
        document.querySelectorAll('[data-fig-full="' + sha + '"]').forEach(function (a) { a.href = img.src; a.hidden = false; });
      };
      img.onerror = function () { el.__figLocalFailed = true; placeholder(el, "loading"); enqueue(el); };
      img.src = C.localUrl(ROOT, sha);
      el.innerHTML = "";
      el.appendChild(img);
      el.setAttribute("data-fig-state", "local");
      return;
    }
    placeholder(el, "loading");
    enqueue(el);
  }

  var watched = new Set();
  var io = typeof IntersectionObserver === "function" ? new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      io.unobserve(e.target);
      watched.delete(e.target);
      start(e.target);
    });
  }, { rootMargin: "200px 0px" }) : null;

  function observe(container) {
    ensureStyle();
    // Platzhalter, die mit neu gerenderten Ansichten verschwunden sind, nicht weiter beobachten
    watched.forEach(function (el) { if (!el.isConnected) { io.unobserve(el); watched.delete(el); } });
    var scope = container || document;
    var list = scope.querySelectorAll ? scope.querySelectorAll("[data-fig-sha]") : [];
    Array.prototype.forEach.call(list, function (el) {
      if (el.__figBound) return;
      el.__figBound = true;
      if (!el.getAttribute("data-fig-state")) placeholder(el, "loading");
      if (io) { io.observe(el); watched.add(el); } else start(el);
    });
  }

  // Blockierte Platzhalter nach einer Änderung der Anmeldung oder Freigabe erneut versuchen
  function requeueBlocked() {
    document.querySelectorAll('[data-fig-sha][data-fig-state="signin"],[data-fig-sha][data-fig-state="forbidden"],[data-fig-sha][data-fig-state="private"]')
      .forEach(function (el) { placeholder(el, "loading"); enqueue(el); });
  }
  window.addEventListener("aiaccess-change", function (e) {
    var snap = (e && e.detail) || {};
    var key = String(snap.auth || "") + "|" + String((snap.user && snap.user.uid) || "");
    var uidChanged = S.authKey !== null && S.authKey.split("|")[1] !== key.split("|")[1];
    var changed = key !== S.authKey;
    S.authKey = key;
    if (uidChanged) {
      urls.forEach(function (u) { try { URL.revokeObjectURL(u); } catch (err) { /* ignore */ } });
      urls.clear();
    }
    if (changed && S.access !== "ok") { S.access = "unknown"; requeueBlocked(); }
    else if (uidChanged) { S.access = "unknown"; requeueBlocked(); }
    else if (S.access === "forbidden" && Date.now() - S.probeAt > 3000) { S.access = "unknown"; requeueBlocked(); }
  });

  document.addEventListener("click", function (e) {
    var b = e.target && e.target.closest ? e.target.closest("[data-fig-act]") : null;
    if (!b) return;
    e.preventDefault();
    e.stopPropagation();
    var act = b.getAttribute("data-fig-act");
    var A = api();
    if (act === "retry") {
      var el = b.closest("[data-fig-sha]");
      if (el) { if (S.access !== "ok") S.access = "unknown"; placeholder(el, "loading"); enqueue(el); }
      return;
    }
    if (A && typeof A.open === "function") A.open(act === "request" ? "request" : "signin");
  }, true);

  var styled = false;
  function ensureStyle() {
    if (styled || document.getElementById("fia-style")) { styled = true; return; }
    styled = true;
    var st = document.createElement("style");
    st.id = "fia-style";
    st.textContent =
      ".fia{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:.35rem;width:100%;height:100%;min-height:inherit;" +
      "padding:.5rem;text-align:center;color:var(--color-ink-muted,#475569);font-size:.78rem;line-height:1.3;box-sizing:border-box;" +
      "background:repeating-linear-gradient(45deg,var(--bg-subtle,#f1f5f9),var(--bg-subtle,#f1f5f9) 8px,var(--bg-canvas,#fff) 8px,var(--bg-canvas,#fff) 16px)}" +
      ".fia-big{min-height:160px;font-size:.9rem;gap:.5rem;padding:1rem;border-radius:8px}" +
      ".fia-tiny{padding:0;gap:0}" +
      ".fia-loading{background:var(--bg-subtle,#f1f5f9)}" +
      ".fia-ico{display:inline-flex;color:var(--color-ink-muted,#475569)}" +
      ".fia-t{max-width:34ch;overflow-wrap:anywhere}" +
      ".fia-btn{font:inherit;font-size:.78rem;font-weight:600;cursor:pointer;border:1px solid var(--color-teal-600,#0d9488);" +
      "background:var(--bg-canvas,#fff);color:var(--color-teal-700,#0f766e);border-radius:6px;padding:.25rem .65rem;min-height:28px}" +
      ".fia-big .fia-btn{font-size:.88rem;padding:.4rem .9rem;min-height:34px}" +
      ".fia-btn:hover{background:var(--color-teal-600,#0d9488);color:#fff}" +
      ".fia-btn:focus-visible{outline:2px solid var(--color-teal-600,#0d9488);outline-offset:2px}" +
      ".fia-icobtn{padding:.2rem;min-height:0;display:inline-flex;border-radius:50%}" +
      "[data-fig-sha]>img{max-width:100%;height:auto}";
    (document.head || document.documentElement).appendChild(st);
  }

  window.FigureImages = {
    observe: observe,
    configure: function (opts) { if (opts && typeof opts.text === "function") textFn = opts.text; },
    // für Tests
    _state: function () { return { access: S.access, service: S.service, cached: urls.size, local: LOCAL, root: ROOT }; }
  };
  boot().then(function () { observe(document); });
})();
