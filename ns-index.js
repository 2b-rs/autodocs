/* ns-index.js — Verhalten der einheitlichen Namespace-Übersicht (lib_nsindex.py).
   - Gliederung links mit umschaltbarer Gruppierung (Typ, Themen, Historie).
   - Klick auf einen Eintrag (Gliederung, Karte, Inspektor) wählt ihn aus: Die
     Detailansicht zeigt seine kanonische Darstellung (Record bzw. Klassenseite),
     der Inspektor rechts seine Bezüge. Hover hebt nur in der Karte hervor und
     verändert die Auswahl nicht.
   - KI-Symbol vor einem Eintrag: Detailansicht mit aufgeklapptem KI-Kommentar.
   - Mittlere Folds (User Guide, Themenkarte, Detailansicht) lassen sich per Griff
     umsortieren; der Inspektor ist in der Breite veränderbar. Beides wird lokal
     gemerkt.
   - Classic-Modulseiten (section.nsx-mod): gleiches Verhalten ohne Klassenseiten; die
     Elemente des Modul-Records erscheinen in der Detailansicht, im Komfortmodus bleibt
     die Seite unverändert.
   - Clusterseiten (section.nsx-clu): Einträge sind die Elemente aller Teile (Classic-
     Module bzw. Adaptive-Namespaces und Service-Interfaces). Ihre Records liegen auf den
     Seiten der Teile (data-page) und werden von dort in die Detailansicht geholt; Klassen-
     und Dienstseiten wie bei Namespaces als Ganzes. Im Komfortmodus bleibt die Seite
     unverändert.
   - Release-Kontext (#release=… bzw. ?release=…): entfallene Elemente werden
     markiert; ohne Elementdaten für das Release erscheint ein Hinweis.
   Ohne Skript bleibt die Seite als Liste mit Dokumentation vollständig lesbar. */

/* Historie-Vergleich (Inspektor/Mitte): gleicher nichtleerer text_key = unverändert;
   Roh-OCR/content nur wenn ein Schlüssel fehlt oder leer ist. Exportiert für gezielte Tests. */
function nsxHistRecordState(d, fromRel, toRel) {
  function versionAt(doc, rel) {
    var vs = (doc && doc.versions || []).filter(function (v) { return v.release === rel; });
    if (!vs.length) return null;
    var withText = vs.filter(function (v) { return v.text_captured !== false && v.content; });
    return withText.length ? withText[withText.length - 1] : false;
  }
  var va = fromRel ? versionAt(d, fromRel) : null;
  var vb = toRel ? versionAt(d, toRel) : null;
  if (va === false || vb === false) return { state: "notext" };
  if (va === null && vb === null) return { state: "none" };
  if (va === null) return { state: "add", a: null, b: vb.content };
  if (vb === null) return { state: "del", a: va.content, b: null };
  var ka = va.text_key || "", kb = vb.text_key || "";
  if (ka && kb && ka === kb) return { state: "same", text_key: ka, a: va.content, b: vb.content };
  return { state: "raw", a: va.content || "", b: vb.content || "", text_key_a: ka, text_key_b: kb };
}
if (typeof window !== "undefined") window.nsxHistRecordState = nsxHistRecordState;
if (typeof module !== "undefined" && module.exports) module.exports.nsxHistRecordState = nsxHistRecordState;

(function () {
  "use strict";
  var SVGNS = "http://www.w3.org/2000/svg";
  var ORDER_KEY = "nsx-fold-order", BY_KEY = "nsx-group-by", W_KEY = "nsx-aside-w", TDOCK_KEY = "nsx-titledock", TOPDOCK_KEY = "nsx-topdock";
  var ICON_DOCK = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2.5v7M5 6.5l3 3 3-3M2.5 13h11"/></svg>';
  var ICON_CLOSE = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 4l8 8M12 4l-8 8"/></svg>';
  // Lösen aus der Titelleiste auf die Fläche (Panel eines angedockten Reiters): Kasten mit Pfeil nach außen.
  // Ein „ד bedeutet Schließen und bleibt echten Schließknöpfen vorbehalten (Admin, 2026-10-13).
  var ICON_UNDOCK = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M9.5 2.5h4v4M13.5 2.5L8 8"/><path d="M11.5 9.5v4h-9v-9h4"/></svg>';
  // Aus einer Ablage der Fläche in die mittlere Spalte: drei Spalten, Pfeil in die mittlere
  var ICON_TOCENTER = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2.5 2.5h11v11h-11z"/><path d="M6 2.5v11M10 2.5v11"/><path d="M8 4.5v6M6.8 9.2L8 10.5l1.2-1.3"/></svg>';
  var ICON_TABDOCK = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2.5 3.5h11v9h-11z" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M2.5 6.5h11" stroke="currentColor" stroke-width="1.4"/><path d="M6 3.5v3" stroke="currentColor" stroke-width="1.4"/></svg>';

  function clearSelection() {
    try {
      if (window.getSelection) {
        var sel = window.getSelection();
        if (sel) {
          if (sel.removeAllRanges) sel.removeAllRanges();
          if (sel.empty) sel.empty();
        }
      }
      if (document.selection && document.selection.empty) {
        document.selection.empty();
      }
    } catch (e) {}
  }

  function dict() { return Object.create(null); }
  function words(el, a) { return (el && el.getAttribute(a) || "").split(" ").filter(Boolean); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function svgEl(tag, attrs) {
    var e = document.createElementNS(SVGNS, tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    return e;
  }
  function load(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function save(k, v) { try { if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) { /* ohne Speicher */ } }
  function currentRelease() {
    var h = (location.hash || "").replace(/^#/, "");
    try { h = decodeURIComponent(h); } catch (e) { /* unkodiert */ }
    var m = /(?:^|&)release=([^&]*)/.exec(h) || /[?&]release=([^&#]+)/.exec(location.search || "");
    return m ? String(m[1]).trim() : "";
  }
  // Anker der Seite: ein Ziel (Eintrag nsx-e-…, Record-ID) plus Schlüssel=Wert-Teile (release=, ai=, at=),
  // durch „&“ getrennt. Das Ziel steht vorn, die Reihenfolge der übrigen Teile bleibt erhalten.
  function hashParts() {
    var h = (location.hash || "").replace(/^#/, "");
    try { h = decodeURIComponent(h); } catch (e) { /* unkodiert */ }
    var out = { target: "", params: [] };
    h.split("&").forEach(function (x) {
      if (!x) return;
      if (x.indexOf("=") > 0) out.params.push(x);
      else if (!out.target) out.target = x;
    });
    return out;
  }
  function hasParam(parts, key) {
    return parts.params.some(function (x) { return x.split("=")[0] === key; });
  }
  // Auswahl im Anker festhalten, ohne Verlaufseintrag und ohne hashchange: Neuladen, geteilte Links und
  // der Sprachumschalter (fold.js) führen so zum selben Eintrag. Leseposition (at=) gilt dann nicht mehr.
  function writeHash(target, ai) {
    var parts = hashParts();
    var keep = parts.params.filter(function (x) { var k = x.split("=")[0]; return k !== "at" && k !== "ai"; });
    if (target && ai) keep.push("ai=1");
    var next = (target ? [target] : []).concat(keep).join("&");
    next = next ? "#" + next : "";
    if (next === (location.hash || "")) return;
    try { history.replaceState(history.state, "", location.pathname + location.search + next); } catch (e) { /* file:// u. ä. */ }
  }
  // Wurzel der veröffentlichten Seite (ns-index.js liegt dort): versions/data/, static/
  var SITE_ROOT = (typeof document !== "undefined" && document.currentScript && document.currentScript.src)
    ? document.currentScript.src.replace(/[^\/]*$/, "") : "";
  var specTextI18nReady = null;
  function loadSpecTextI18n() {
    if (window.SpecTextI18n) return Promise.resolve(window.SpecTextI18n);
    if (specTextI18nReady) return specTextI18nReady;
    specTextI18nReady = new Promise(function (resolve) {
      var script = document.querySelector('script[data-nsx-spec-text-i18n], script[src$="static/spec-text-i18n.js"], script[src*="static/spec-text-i18n.js?"]');
      if (!script) {
        script = document.createElement("script");
        script.src = SITE_ROOT + "static/spec-text-i18n.js";
        script.setAttribute("data-nsx-spec-text-i18n", "1");
        document.head.appendChild(script);
      } else {
        script.setAttribute("data-nsx-spec-text-i18n", "1");
      }
      function done() { resolve(window.SpecTextI18n || null); }
      script.addEventListener("load", done, { once: true });
      script.addEventListener("error", done, { once: true });
    });
    return specTextI18nReady;
  }
  var reduceMotion = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  var behavior = reduceMotion ? "auto" : "smooth";

  // Requirement-Verweise in KI-Leitfäden bleiben normale Links. Bei Hover bzw. Tastaturfokus
  // ergänzt ein leichtgewichtiges, nicht-modales Popover den im Versions-Store vorhandenen
  // Wortlaut und dessen Release-/PDF-Provenienz. So muss man den Lesekontext nicht verlassen,
  // kann den Link mit Klick/Enter aber weiterhin unverändert öffnen.
  function requirementCaseMask(id) {
    var out = "", value = 0, count = 0;
    String(id).split("").forEach(function (ch) {
      if (!/[A-Za-z]/.test(ch)) return;
      value = value * 2 + (/[A-Z]/.test(ch) ? 1 : 0);
      count += 1;
      if (count === 4) { out += value.toString(16); value = 0; count = 0; }
    });
    if (count) out += (value << (4 - count)).toString(16);
    return out || "0";
  }
  function installRequirementPreviews() {
    if (document._nsxRequirementPreviews) return;
    document._nsxRequirementPreviews = true;
    var cache = dict(), active = null, closeTimer = 0;
    var pop = document.createElement("aside");
    pop.className = "req-preview";
    pop.id = "req-preview";
    pop.hidden = true;
    pop.setAttribute("role", "tooltip");
    document.body.appendChild(pop);

    function candidate(target) {
      var a = target && target.closest && target.closest("a.spec-record-ref[data-req]");
      return a && a.closest(".ai, .ai-guide-container, details[data-fold^='guide']") ? a : null;
    }
    function getJson(id) {
      if (cache[id]) return cache[id];
      var stem = String(id).replace(/[^A-Za-z0-9_.\-]/g, "_");
      function get(name) {
        return fetch(SITE_ROOT + "versions/data/" + encodeURIComponent(name) + ".json").then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          return r.json();
        });
      }
      cache[id] = get(stem).then(function (data) {
        var own = String(data && data.canonical_id || "").split("/").pop();
        if (own && own !== id && own.toLowerCase() === String(id).toLowerCase()) throw new Error("case variant");
        return data;
      }).catch(function () { return get(stem + "~" + requirementCaseMask(id)); });
      cache[id].catch(function () { delete cache[id]; });
      return cache[id];
    }
    function versionFor(data) {
      var all = (data && data.versions || []), captured = all.filter(function (v) { return v && v.content; });
      if (!captured.length) return null;
      var rel = currentRelease(), exact = captured.filter(function (v) { return rel && v.release === rel; })[0];
      if (exact) return exact;
      if (rel) {
        var at = all.map(function (v) { return v.release; }).indexOf(rel), prior = at < 0 ? [] : all.slice(0, at + 1).filter(function (v) { return v && v.content; });
        if (prior.length) return prior[prior.length - 1];
      }
      return captured[captured.length - 1];
    }
    function place() {
      if (!active || pop.hidden) return;
      var r = active.getBoundingClientRect(), margin = 10, width = Math.min(480, document.documentElement.clientWidth - margin * 2);
      pop.style.width = width + "px";
      var h = pop.offsetHeight, below = r.bottom + 8, top = below + h <= innerHeight - margin ? below : Math.max(margin, r.top - h - 8);
      pop.style.top = Math.round(top) + "px";
      pop.style.left = Math.round(Math.min(Math.max(margin, r.left), document.documentElement.clientWidth - width - margin)) + "px";
    }
    function clearDescription(a) {
      if (!a) return;
      var before = a.getAttribute("data-req-preview-describedby");
      if (before) a.setAttribute("aria-describedby", before); else a.removeAttribute("aria-describedby");
      a.removeAttribute("data-req-preview-describedby");
    }
    function close() {
      clearTimeout(closeTimer);
      clearDescription(active);
      active = null;
      pop.hidden = true;
      pop.textContent = "";
    }
    function laterClose() { clearTimeout(closeTimer); closeTimer = setTimeout(close, 120); }
    function render(a, id, data) {
      if (active !== a) return;
      var version = versionFor(data);
      if (!version) { close(); return; }
      var lang = String(document.documentElement.lang || "en").toLowerCase().split("-")[0];
      loadSpecTextI18n().then(function (api) {
        var original = api ? api.decodeFully(api.shownContent(version)) : String(version.content || "");
        var lookup = api && version.text_key ? api.lookup(SITE_ROOT, lang, id, version.text_key) : Promise.resolve(null);
        return lookup.then(function (fields) { return { api: api, fields: fields, original: original }; });
      }).then(function (result) {
        if (active !== a) return;
        var api = result.api, fields = result.fields, original = result.original;
        var tr = fields && fields.description, translated = !!tr;
        var wording = original;
        if (tr) {
          var tmp = document.createElement("div");
          tmp.innerHTML = tr.html;
          wording = tmp.textContent || original;
        }
        var S = api ? api.strings(lang) : { note: "Machine-translated", original_note: "Showing the original (English)" };
        pop.textContent = "";
        var head = document.createElement("div");
        head.className = "req-preview-head";
        var code = document.createElement("code");
        code.textContent = id;
        var release = document.createElement("span");
        release.className = "req-preview-release";
        release.textContent = version.release || "";
        head.appendChild(code); head.appendChild(release);
        var text = document.createElement("p");
        text.className = "req-preview-text";
        text.textContent = wording;
        var source = document.createElement("p");
        source.className = "req-preview-source";
        source.textContent = (translated ? S.note : S.original_note) + " · "
          + ((version.meta && version.meta.source_pdf) || "Versions-Store");
        pop.appendChild(head); pop.appendChild(text); pop.appendChild(source);
        place();
      }, function () { if (active === a) close(); });
    }
    function show(a) {
      clearTimeout(closeTimer);
      if (active === a && !pop.hidden) return;
      if (active && active !== a) clearDescription(active);
      active = a;
      var old = a.getAttribute("aria-describedby") || "";
      a.setAttribute("data-req-preview-describedby", old);
      a.setAttribute("aria-describedby", [old, pop.id].filter(Boolean).join(" "));
      pop.hidden = false;
      var api = window.SpecTextI18n, lang = String(document.documentElement.lang || "en").toLowerCase().split("-")[0];
      var heading = api ? api.strings(lang).heading : "Specification Text";
      pop.innerHTML = '<p class="req-preview-loading">' + esc(heading) + ' …</p>';
      place();
      var id = a.getAttribute("data-req") || "";
      getJson(id).then(function (data) { render(a, id, data); }, function () { if (active === a) close(); });
    }
    document.addEventListener("mouseover", function (ev) { var a = candidate(ev.target); if (a && a !== active) show(a); });
    document.addEventListener("mouseout", function (ev) {
      if (!active) return;
      var next = ev.relatedTarget;
      if (next && (active.contains(next) || pop.contains(next))) return;
      laterClose();
    });
    document.addEventListener("focusin", function (ev) { var a = candidate(ev.target); if (a) show(a); });
    document.addEventListener("focusout", function (ev) { if (active && ev.target === active) laterClose(); });
    document.addEventListener("keydown", function (ev) { if (ev.key === "Escape" && active) close(); });
    pop.addEventListener("mouseenter", function () { clearTimeout(closeTimer); });
    pop.addEventListener("mouseleave", laterClose);
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, { passive: true });
  }

  function init(root) {
    if (root._nsxInitialized) return;
    root._nsxInitialized = true;

    // Building in Pieces — Progressiver Aufbau der Seite
    root.classList.add("nsx-assembling");
    var pieces = [];
    var parent = root.parentElement;
    if (parent) {
      var ov = parent.querySelector(".cluster-overview");
      if (ov) pieces.push(ov);
      parent.querySelectorAll(".cards > .card").forEach(function (c) { pieces.push(c); });
    }
    root.querySelectorAll(".nsx-col").forEach(function (col) { pieces.push(col); });
    if (parent) {
      parent.querySelectorAll(".nsx-topdock details.nsx-fold").forEach(function (f) { pieces.push(f); });
    }
    var folds = root.querySelector(".nsx-folds");
    if (folds) {
      folds.querySelectorAll("details.nsx-fold").forEach(function (f) { pieces.push(f); });
    }
    pieces.forEach(function (el, idx) {
      el.style.setProperty("--nsx-piece-idx", idx);
    });
    setTimeout(function () {
      root.classList.remove("nsx-assembling");
      if (typeof placePop === "function") placePop();
    }, 700);

    // Namensschlüssel ohne Prototyp: Mitglieder heißen auch toString oder constructor
    var rows = dict(), chips = dict(), oitems = dict(), recOwner = dict();
    root.querySelectorAll(".nsx-row").forEach(function (r) {
      var n = r.getAttribute("data-n");
      rows[n] = r;
      words(r, "data-recs").concat(words(r, "data-fns")).forEach(function (id) { recOwner[id] = n; });
    });
    root.querySelectorAll(".nsx-chip").forEach(function (c) { chips[c.getAttribute("data-n")] = c; });
    root.querySelectorAll(".nsx-oi").forEach(function (o) { (oitems[o.getAttribute("data-n")] = oitems[o.getAttribute("data-n")] || []).push(o); });
    var relnote = root.querySelector(".nsx-relnote");
    var labels = {};
    root.querySelectorAll(".nsx-labels [data-l]").forEach(function (s) { labels[s.getAttribute("data-l")] = s.textContent.trim(); });

    function applyRelease() {
      var rel = currentRelease(), any = false;
      Object.keys(rows).forEach(function (n) {
        var r = rows[n], gone = rel && words(r, "data-dropped").indexOf(rel) >= 0;
        if (rel && (words(r, "data-releases").indexOf(rel) >= 0 || words(r, "data-present").indexOf(rel) >= 0 || gone)) any = true;
        [r, chips[n]].concat(oitems[n] || []).forEach(function (el) {
          if (!el) return;
          el.classList.toggle("nsx-dropped", !!gone);
          if (gone) el.setAttribute("title", (labels.dropped || "") + " " + words(r, "data-dropped")[0]);
          else if (el.getAttribute("title")) el.removeAttribute("title");
        });
      });
      if (relnote) {
        relnote.hidden = !rel || any;
        var code = relnote.querySelector(".nsx-relnote-r");
        if (code) code.textContent = rel;
      }
    }
    window.addEventListener("hashchange", applyRelease);
    applyRelease();
    // Dichte „Comfortable“: bisherige flache Seite (Übersichten, Diagramm, Dokumentation);
    // „Compact“: interaktive Ansicht. Ein Wechsel der Dichte lädt die Seite neu.
    // Classic-Modulseiten: Die Übersicht ist aus dem Modul-Record abgeleitet; im
    // Komfortmodus entfällt sie, der Record darüber ist die bisherige Seite.
    var isMod = root.classList.contains("nsx-mod");
    var isClu = root.classList.contains("nsx-clu");
    if (document.documentElement.getAttribute("data-density") !== "compact") {
      if (isMod || isClu) root.remove();
      else flattenClassIndex(document.querySelector("main") || document.body);
      return;
    }
    if (root.classList.contains("nsx-small")) return;
    // Modulseite: Der Record bleibt Datenquelle; seine Elemente erscheinen in der Detailansicht
    var modName = root.getAttribute("data-module") || "";
    if (isMod) {
      var modRec = document.getElementById(root.getAttribute("data-rec") || "");
      if (modRec) modRec.hidden = true;
    }

    root.classList.add("nsx-live");
    var map = root.querySelector(".nsx-map");
    var outline = root.querySelector(".nsx-outline");
    var folds = root.querySelector(".nsx-folds");
    var detFold = root.querySelector('.nsx-fold[data-fold="detail"]');
    var detBody = detFold && detFold.querySelector(".nsx-detbody");
    var detTitle = detFold && detFold.querySelector(".nsx-dettitle");
    var detLink = detFold && detFold.querySelector(".nsx-canon-link");
    var aside = root.querySelector(".nsx-aside");
    var relBox = aside && aside.querySelector(".nsx-rel");
    var hint = aside && aside.querySelector(".nsx-hint");
    var ext = {};
    try { ext = JSON.parse((root.querySelector("script.nsx-ext") || {}).textContent || "{}"); } catch (e) { ext = {}; }
    // Seitenpfad → Eintrag, damit Verweise aus Klassenseiten und Signaturen auf die Auswahl führen
    var byPath = {}, partPaths = {};
    Object.keys(rows).forEach(function (n) {
      var h = rows[n].getAttribute("data-href"), pg = rows[n].getAttribute("data-page");
      if (h && h.charAt(0) !== "#" && !rows[n].getAttribute("data-recs")) byPath[new URL(h, location.href).pathname] = n;
      if (pg) partPaths[new URL(pg, location.href).pathname] = pg;
    });
    // Clusterseiten: Name des Clusters, Plattform und Beschriftung der Teile
    var cluName = root.getAttribute("data-cluster") || "", cluClassic = root.getAttribute("data-platform") !== "adaptive";
    // Signaturen der Nicht-Member-Funktionen nach Name (für „Kommt vor in“)
    var fnIndex = dict();
    // Verweis „zum Record“ (a.nsx-go): auf Clusterseiten führt der Link auf die Seite des Teils (data-fn trägt die ID),
    // sonst ist er ein Seitenanker (#ID)
    function fnId(go) { return go.getAttribute("data-fn") || go.getAttribute("href").slice(1); }
    // In der Kompaktansicht wählt der Verweis den Eintrag hier aus (Klickbehandlung über recOwner), statt die Seite zu wechseln
    root.querySelectorAll(".nsx-row a.nsx-go[data-fn]").forEach(function (go) {
      if (recOwner[go.getAttribute("data-fn")]) go.setAttribute("href", "#" + go.getAttribute("data-fn"));
    });
    root.querySelectorAll(".nsx-row .nsx-sig").forEach(function (sg) {
      var code = sg.querySelector("code"), go = sg.querySelector("a.nsx-go");
      var m = code && go && /(operator\s*[^\s(]+|[A-Za-z_~][\w:]*)\s*\(/.exec(code.textContent);
      if (!m) return;
      var fname = m[1].replace(/\s+/g, "").split("::").pop();
      (fnIndex[fname] = fnIndex[fname] || []).push({ id: fnId(go), code: code });
    });

    // ---- Clusterseiten: Definition und Modulkarten als Folds mit Griffen
    var cluOv = document.querySelector("main > div.cluster-overview");
    if (cluOv && !cluOv.closest("details[data-fold]")) {
      var ovFold = document.createElement("details");
      ovFold.className = "fold nsx-fold";
      ovFold.setAttribute("data-fold", "overview");
      ovFold.open = true;
      ovFold._initTop = true;
      ovFold._initDock = "lead";
      var ovSm = document.createElement("summary");
      var ovGr = document.createElement("span");
      ovGr.className = "nsx-grip";
      ovGr.setAttribute("role", "button");
      ovGr.setAttribute("tabindex", "0");
      ovSm.appendChild(ovGr);
      var ovH2 = document.createElement("h2");
      ovH2.className = "sect";
      ovH2.textContent = labels.overview || "Definition";
      ovSm.appendChild(ovH2);
      ovFold.appendChild(ovSm);
      cluOv.parentNode.insertBefore(ovFold, cluOv);
      ovFold.appendChild(cluOv);
    }

    var cluCards = isClu && document.querySelector("main > div.cards");
    if (cluCards && !cluCards.closest("details[data-fold]")) {
      var ch2 = cluCards.previousElementSibling;
      var cardsTitle = (ch2 && ch2.matches("h2.sect")) ? ch2.textContent.trim() : (labels.cards || "Module im Cluster");
      if (ch2 && ch2.matches("h2.sect")) ch2.remove();

      var cardsFold = document.createElement("details");
      cardsFold.className = "fold nsx-fold";
      cardsFold.setAttribute("data-fold", "cards");
      cardsFold.open = true;
      cardsFold._initTop = true;
      cardsFold._initDock = "post";
      var cSm = document.createElement("summary");
      var cGr = document.createElement("span");
      cGr.className = "nsx-grip";
      cGr.setAttribute("role", "button");
      cGr.setAttribute("tabindex", "0");
      cSm.appendChild(cGr);
      var cH2 = document.createElement("h2");
      cH2.className = "sect";
      cH2.textContent = cardsTitle;
      cSm.appendChild(cH2);
      cardsFold.appendChild(cSm);
      cluCards.parentNode.insertBefore(cardsFold, cluCards);
      cardsFold.appendChild(cluCards);
      cluCards.classList.add("nsx-clucards");
    }

    // ---- Content Area „Elemente“ (Gliederung, Inspektor, Elementansicht) als andockbares Element;
    // Beschriftung aus dem UI-Katalog (Schlüssel „elements“). Admin 2026-10-14: auf Namespace-, Klassen-, Modul- und
    // Clusterseiten wieder „Elemente“ (API-Elemente und Anforderungen); „Anforderungen“ heißt nur der Reiter des
    // Versions-Explorers und die Kopfsuche, wo die Liste wirklich Anforderungen enthält
    root.setAttribute("data-fold", "elements");
    var elHead = root.querySelector(".nsx-elements-head");
    if (!elHead) {
      elHead = document.createElement("div");
      elHead.className = "nsx-elements-head";
      var elGr = document.createElement("span");
      elGr.className = "nsx-grip";
      elGr.setAttribute("role", "button");
      elGr.setAttribute("tabindex", "0");
      elHead.appendChild(elGr);
      var elH2 = document.createElement("h2");
      elH2.className = "sect";
      elH2.textContent = labels.elements || "Elemente";
      elHead.appendChild(elH2);
      root.insertBefore(elHead, root.firstChild);
    }
    // Ein- und Ausklappen wie bei den Folds (Pfeil vor dem Titel, Klick auf die Kopfzeile),
    // angedockt über den Reiter in der Titelleiste
    var elChev = elHead.querySelector(".nsx-elchev");
    if (!elChev) {
      elChev = document.createElement("span");
      elChev.className = "nsx-elchev";
      elChev.setAttribute("role", "button");
      elChev.setAttribute("tabindex", "0");
      elChev.setAttribute("aria-label", labels.elements || "Elemente");
      var elH = elHead.querySelector("h2");
      elHead.insertBefore(elChev, elH || null);
    }

    // ---- Titelleiste des Namespace bleibt oben stehen
    var title = document.querySelector("main > h1");
    function pinH() { return title ? title.offsetHeight : 0; }
    function navTop() { return title ? Math.max(0, title.getBoundingClientRect().bottom) : 0; }
    if (title) {
      title.classList.add("nsx-pin");
      var setTop = function () { document.documentElement.style.setProperty("--nsx-top", pinH() + "px"); };
      setTop();
      if (window.ResizeObserver) new ResizeObserver(setTop).observe(title);
    }

    // ---- Seitenspannende Dropzonen (Lead unter der Überschrift, Pre vor der Gliederung, Post hinter der Gliederung)
    var dockLead = document.querySelector(".nsx-dock-lead");
    if (!dockLead && root) {
      dockLead = document.createElement("div");
      dockLead.className = "nsx-topdock nsx-dock-lead";
      dockLead.setAttribute("data-dock", "lead");
      if (title && title.nextSibling) title.parentNode.insertBefore(dockLead, title.nextSibling);
      else if (root.parentNode) root.parentNode.insertBefore(dockLead, root.parentNode.firstChild);
    }
    var dockPre = document.querySelector(".nsx-dock-pre");
    if (!dockPre && root) {
      dockPre = document.createElement("div");
      dockPre.className = "nsx-topdock nsx-dock-pre";
      dockPre.setAttribute("data-dock", "pre");
      root.parentNode.insertBefore(dockPre, root);
    }
    var dockPost = document.querySelector(".nsx-dock-post");
    if (!dockPost && root) {
      dockPost = document.createElement("div");
      dockPost.className = "nsx-topdock nsx-dock-post";
      dockPost.setAttribute("data-dock", "post");
      if (root.nextSibling) root.parentNode.insertBefore(dockPost, root.nextSibling);
      else root.parentNode.appendChild(dockPost);
    }
    var topDock = dockPre;
    var allDocks = [dockLead, dockPre, dockPost];

    // ---- Dokumentationsabschnitte: Inhalt erscheint nur noch in der Detailansicht
    document.querySelectorAll("details.nsx-doc").forEach(function (d) { d.hidden = true; });

    // Schlüssel der Titelleiste: „guide“/„impl“ bleiben dem ersten Fold der Art (der
    // Übersicht am nächsten). Weitere Guides (z. B. Cluster Guide neben User Guide)
    // bekommen einen eigenen andockbaren Schlüssel; ein gemerktes „guide“ springt
    // dadurch nicht auf einen anderen Fold.
    function titleKeyKind(k) {
      if (!k || k === "detail") return "";
      var m = /^(guide|impl)(?:-[A-Za-z0-9_-]+)?$|^(map|uml)$/.exec(k);
      if (m) return m[1] || m[2];
      return k;
    }
    var usedFoldKeys = {};
    function allocFoldKey(el, kind) {
      if (!usedFoldKeys[kind]) { usedFoldKeys[kind] = true; return kind; }
      var slug = (el.getAttribute("id") || "").replace(/[^A-Za-z0-9_-]/g, "");
      var base = slug ? kind + "-" + slug : kind;
      var key = slug ? base : kind + "-2", n = 2;
      while (usedFoldKeys[key]) { n += 1; key = base + "-" + n; }
      usedFoldKeys[key] = true;
      return key;
    }
    // ---- User Guide, Cluster Guide und Implementer's Guide als erste Folds der Mitte
    var guideFold = null;
    var candidateGuides = [];
    var guideAt = dockPre || root;
    for (var p = root.previousElementSibling, prevP; p; p = prevP) {
      prevP = p.previousElementSibling;   // vor dem Umhängen merken
      if (p.tagName === "DETAILS" && p.classList.contains("fold") && !p.classList.contains("nsx-doc") && p.querySelector(".ai")) {
        candidateGuides.push(p);
      }
    }
    for (var n = root.nextElementSibling, nextN; n; n = nextN) {
      nextN = n.nextElementSibling;
      if (n.tagName === "DETAILS" && n.classList.contains("fold") && !n.classList.contains("nsx-doc") && n.querySelector(".ai")) {
        candidateGuides.push(n);
      }
    }
    candidateGuides.forEach(function (g) {
      var gkind = g.classList.contains("impl-fold") ? "impl" : "guide";
      var key = allocFoldKey(g, gkind);
      g.classList.add("nsx-fold");
      g.setAttribute("data-fold", key);
      if (key === "guide" || (key === "impl" && !guideFold)) guideFold = g;
      var sm = g.querySelector("summary");
      if (sm && !sm.querySelector(".nsx-grip")) {
        var gr = document.createElement("span");
        gr.className = "nsx-grip";
        gr.setAttribute("role", "button");
        gr.setAttribute("tabindex", "0");
        bindGrip(gr);
        sm.insertBefore(gr, sm.firstChild);
      }
      // Guides gehören nicht in die Elemente: Ablage auf der Fläche der Seite (vor der Gliederung)
      guideAt.parentNode.insertBefore(g, guideAt);
      guideAt = g;
    });

    // ---- Service-Interfaces: die Mitgliederliste der Seite (Überschrift + Liste, jeder
    // Eintrag verweist auf einen Record) ersetzt im Kompaktmodus die Gliederung
    if (root.classList.contains("nsx-svc")) {
      for (var sq = root.previousElementSibling; sq; sq = sq.previousElementSibling) {
        if (!sq.matches("ul.mlist")) continue;
        var ids = Array.prototype.map.call(sq.querySelectorAll("li > a[href^='#']"), function (a) { return decodeURIComponent(a.getAttribute("href").slice(1)); });
        if (!ids.length || !ids.every(function (id) { return recOwner[id]; })) continue;
        sq.hidden = true;
        var sh = sq.previousElementSibling;
        if (sh && /^H[34]$/.test(sh.tagName)) sh.hidden = true;
      }
    }

    // ---- Große Themen und Abschnitte vor oder hinter der Übersicht (z.B. Namespaces,
    // Service-Interfaces, UML-Diagramme, Synopsis, Ablauf- oder Lebenszyklusdiagramme):
    // je Überschrift ein Fold mit Griff und Summary.
    (function () {
      var beforeKids = [], afterKids = [], cur = null, n = 0;
      var at = Array.prototype.filter.call(folds.children, function (x) {
        var k = titleKeyKind(x.getAttribute("data-fold") || "");
        return k !== "guide" && k !== "impl";
      })[0] || null;

      for (var q = root.previousElementSibling; q; q = q.previousElementSibling) beforeKids.unshift(q);
      for (var a = root.nextElementSibling, nextA; a; a = nextA) {
        nextA = a.nextElementSibling;
        if (a.matches("details.fold, dialog, script, footer, article.rec, .dossier-modal")) continue;
        afterKids.push(a);
      }

      function sectionKind(h2El) {
        var txt = (h2El.textContent || "").toLowerCase();
        if (/uml|diagramm|kollaboration/.test(txt)) return "uml";
        if (/namespace/.test(txt)) return "namespaces";
        if (/service/.test(txt)) return "services";
        if (/modul/.test(txt)) return "modules";
        if (/klasse/.test(txt)) return "classes";
        return "sec";
      }

      function processKids(kids, isAfter) {
        kids.forEach(function (k) {
          if (k.matches("h2.sect") && !k.hidden) {
            cur = document.createElement("details");
            cur.className = "fold nsx-fold nsx-secfold";
            cur.open = true;
            var kind = sectionKind(k);
            var key = allocFoldKey(cur, kind);
            cur.setAttribute("data-fold", key);
            var sm = document.createElement("summary"), gr = document.createElement("span");
            gr.className = "nsx-grip";
            gr.setAttribute("role", "button");
            gr.setAttribute("tabindex", "0");
            bindGrip(gr);
            sm.appendChild(gr);
            sm.appendChild(k);
            cur.appendChild(sm);
            if (isAfter || kind === "namespaces" || kind === "uml" || kind === "services" || kind === "modules") {
              cur._initTop = true;
              cur._initDock = "pre";
            }
            folds.insertBefore(cur, at);
          } else if (cur && !k.matches("details, dialog, script, article.rec, footer, .dossier-modal")) {
            cur.appendChild(k);
          } else {
            cur = null;
          }
        });
      }

      processKids(beforeKids, false);
      cur = null;
      processKids(afterKids, true);
    })();

    // ---- Auf- und Zuklappen lässt die Fold-Zeile an ihrer Bildschirmposition
    folds.addEventListener("click", function (ev) {
      var sm = ev.target.closest("details.nsx-fold > summary");
      if (!sm || ev.target.closest(".nsx-grip, a, button") || sm.parentNode.classList.contains("nsx-pop")) return;
      var d = sm.parentNode, y = sm.getBoundingClientRect().top;
      d.addEventListener("toggle", function () {
        var dy = sm.getBoundingClientRect().top - y;
        if (Math.abs(dy) >= 1) window.scrollBy(0, dy);
      }, { once: true });
    });

    // ---- Reihenfolge der Folds
    function foldList() {
      var list = Array.prototype.filter.call(folds.children, function (x) { return x.matches("details[data-fold]"); });
      allDocks.forEach(function (dock) {
        if (!dock) return;
        Array.prototype.forEach.call(dock.children, function (x) {
          if (x.matches("details[data-fold]") && list.indexOf(x) < 0) list.push(x);
        });
      });
      document.querySelectorAll("main > details.nsx-fold[data-fold]").forEach(function (x) {
        if (list.indexOf(x) < 0) list.push(x);
      });
      return list;
    }
    // Reihenfolge der mittleren Spalte gehört zum gemerkten Layout (saveAllDocks)
    function saveOrder() { saveAllDocks(); }
    var dragging = null;
    var gripActive = false;
    var draggingJustNow = false;

    function cleanupDnd() {
      gripActive = false;
      draggingJustNow = true;
      setTimeout(function () { draggingJustNow = false; }, 300);
      document.querySelectorAll("details[data-fold]").forEach(function (el) {
        el.draggable = false;
        el.removeAttribute("draggable");
      });
      document.querySelectorAll(".nsx-tab-dragging").forEach(function (t) {
        t.classList.remove("nsx-tab-dragging");
      });
      root.classList.remove("nsx-dnd");
      document.body.classList.remove("nsx-dnd-active");
      allDocks.forEach(function (d) {
        if (d) d.classList.remove("nsx-drop-zone", "nsx-drop-over");
      });
      if (title) title.classList.remove("nsx-drop-zone", "nsx-drop-over");
      if (dropZone) dropZone.classList.remove("nsx-drop-over");
      if (dragging) {
        dragging.classList.remove("nsx-dragging");
        dragging = null;
      }
      lastDrag = null;
      clearSelection();
      setTimeout(clearSelection, 0);
      setTimeout(clearSelection, 30);
      setTimeout(clearSelection, 100);
    }

    function startFoldDrag(ev, f, fromTitle) {
      if (!f) return;
      clearSelection();
      dragging = f;
      f._fromTitle = !!fromTitle;
      f._fromTop = f.classList.contains("nsx-topdocked");
      f._fromZone = f.getAttribute("data-docked-zone") || (f._fromTop ? "pre" : "center");
      f._dropped = false;
      f.classList.add("nsx-dragging");
      root.classList.add("nsx-dnd");
      document.body.classList.add("nsx-dnd-active");

      if (fromTitle) {
        var tab = tdock && tdock.querySelector('[data-fold="' + f.getAttribute("data-fold") + '"]');
        if (tab) tab.classList.add("nsx-tab-dragging");
        setPop(null);
      }

      if (canTopDock(f)) {
        allDocks.forEach(function (d) {
          if (d) d.classList.add("nsx-drop-zone");
        });
      }
      if (canTitleDock(f) && title) title.classList.add("nsx-drop-zone");

      ev.dataTransfer.effectAllowed = "move";
      try { ev.dataTransfer.setData("text/plain", f.getAttribute("data-fold")); } catch (e) {}

      var sm = f.querySelector("summary") || f.querySelector(".nsx-elements-head");
      if (ev.dataTransfer.setDragImage) {
        var imgSource = fromTitle ? (tdock && tdock.querySelector('[data-fold="' + f.getAttribute("data-fold") + '"]')) : sm;
        if (imgSource) {
          try { ev.dataTransfer.setDragImage(imgSource, 20, 16); } catch (e) {}
        }
      }
    }

    function bindGrip(g) {
      var d = g.closest("details[data-fold], section.nsx[data-fold]");
      var gl = (canTopDock(d) || canTitleDock(d) ? labels.gripdock : labels.grip) || "";
      g.setAttribute("title", gl);
      g.setAttribute("aria-label", gl);
      g.setAttribute("draggable", "true");
      g.draggable = true;

      function armDraggable() {
        gripActive = true;
        if (d && d !== root) {
          d.draggable = true;
          d.setAttribute("draggable", "true");
        }
      }
      function disarmDraggable() {
        if (!dragging) {
          gripActive = false;
          if (d && d !== root) {
            d.draggable = false;
            d.removeAttribute("draggable");
          }
        }
      }

      g.addEventListener("mouseenter", armDraggable);
      g.addEventListener("pointerenter", armDraggable);
      g.addEventListener("pointerdown", function () {
        armDraggable();
        clearSelection();
      });
      g.addEventListener("mousedown", function () {
        armDraggable();
        clearSelection();
      });
      g.addEventListener("selectstart", function (ev) { ev.preventDefault(); return false; });
      g.addEventListener("dragstart", function (ev) {
        armDraggable();
        var f = g.closest("details[data-fold], section.nsx[data-fold]");
        if (f) startFoldDrag(ev, f, f.classList.contains("nsx-tdocked"));
      });
      g.addEventListener("click", function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        return false;
      });
      g.addEventListener("keydown", function (ev) {
        if (ev.key !== "ArrowUp" && ev.key !== "ArrowDown") return;
        ev.preventDefault();
        var f = g.closest("details[data-fold], section.nsx[data-fold]");
        if (!f) return;
        if (f === root) {
          if (ev.key === "ArrowUp") dockTitle(root);
          return;
        }
        if (f.classList.contains("nsx-topdocked")) {
          if (ev.key === "ArrowDown" && canCenter(f)) undockTop(f);
          else if (ev.key === "ArrowUp" && !canCenter(f) && canTitleDock(f)) dockTitle(f);
          return;
        }
        var fl = foldList().filter(function (x) { return !x.classList.contains("nsx-tdocked"); }), i = fl.indexOf(f);
        if (ev.key === "ArrowUp" && i === 0 && canTitleDock(f)) { dockTitle(f); return; }
        if (ev.key === "ArrowUp" && i > 0) folds.insertBefore(f, fl[i - 1]);
        else if (ev.key === "ArrowDown" && i < fl.length - 1) folds.insertBefore(fl[i + 1], f);
        else return;
        g.focus();
        saveOrder();
      });
    }

    document.querySelectorAll(".nsx-grip").forEach(bindGrip);

    document.addEventListener("pointerdown", function (ev) {
      if (!ev.target.closest || !ev.target.closest(".nsx-grip")) {
        gripActive = false;
        document.querySelectorAll("details[data-fold]").forEach(function (el) {
          el.draggable = false;
          el.removeAttribute("draggable");
        });
      }
    });

    function onDragStart(ev) {
      var g = ev.target.closest && ev.target.closest(".nsx-grip");
      var f = ev.target.closest && ev.target.closest("details[data-fold], section.nsx[data-fold]");
      if (!f && g) f = g.closest("details[data-fold], section.nsx[data-fold]");
      if (!f) return;
      var allowed = gripActive || g || (ev.target.classList && ev.target.classList.contains("nsx-grip"));
      if (!allowed) {
        ev.preventDefault();
        return;
      }
      startFoldDrag(ev, f, f.classList.contains("nsx-tdocked"));
    }
    document.addEventListener("dragstart", onDragStart);
    folds.addEventListener("dragstart", onDragStart);

    // Klicks auf den Griff oder kurz nach dem Ziehen auf Summary blockieren, damit Safari den Fold nicht umschaltet
    document.addEventListener("click", function (ev) {
      if (ev.target.closest && ev.target.closest(".nsx-grip")) {
        ev.preventDefault();
        ev.stopPropagation();
        return false;
      }
      if (draggingJustNow && ev.target.closest && ev.target.closest("details > summary")) {
        ev.preventDefault();
        ev.stopPropagation();
        return false;
      }
    }, true);

    // Ablagefläche ist die ganze mittlere Spalte, nicht nur die Folds
    var dropZone = folds.parentNode;
    dropZone.addEventListener("dragover", function (ev) {
      if (!dragging) return;
      var at = { x: ev.clientX, y: ev.clientY };
      var overTop = allDocks.some(function (d) { return d && d.contains(ev.target); });
      if (dropZoneAt(at) === "lead" || dropZoneAt(at) === "pre" || dropZoneAt(at) === "post" || overTop) return;
      ev.preventDefault();
      try { ev.dataTransfer.dropEffect = "move"; } catch (e) { /* alte Browser */ }
      // Die Elemente selbst und Guides werden nie in die Mitte (in die Elemente) eingefügt
      if (!canCenter(dragging)) return;
      var t = ev.target.closest && ev.target.closest("details[data-fold]");
      if (t && t !== dragging && t.parentNode === folds) {
        var r = t.getBoundingClientRect();
        folds.insertBefore(dragging, ev.clientY < r.top + Math.min(r.height / 2, 60) ? t : t.nextSibling);
        return;
      }
      if (t) return;
      // Freie Fläche: über dem ersten sichtbaren Fold an den Anfang, sonst ans Ende
      var vis = foldList().filter(function (x) { return x !== dragging && docked(x) && x.parentNode === folds; });
      if (!vis.length) return;
      if (ev.clientY < vis[0].getBoundingClientRect().top) folds.insertBefore(dragging, vis[0]);
      else if (ev.clientY > vis[vis.length - 1].getBoundingClientRect().bottom) folds.insertBefore(dragging, vis[vis.length - 1].nextSibling);
    });

    dropZone.addEventListener("drop", function (ev) {
      if (!dragging) return;
      var at = { x: ev.clientX, y: ev.clientY };
      var dz = dropZoneAt(at);
      var f = dragging;
      f._dropped = true;
      if ((dz === "lead" || dz === "pre" || dz === "post") && canTopDock(f)) {
        ev.preventDefault();
        dockTo(f, dz);
      } else if (dz === "title" && canTitleDock(f)) {
        ev.preventDefault();
        dockTitle(f);
      } else {
        ev.preventDefault();
        dockTo(f, "center");
      }
      cleanupDnd();
    });

    var lastDrag = null;
    document.addEventListener("dragover", function (ev) {
      if (!dragging) return;
      lastDrag = { x: ev.clientX, y: ev.clientY };
      var dz = dropZoneAt(lastDrag);
      if (dz) {
        ev.preventDefault();
        try { ev.dataTransfer.dropEffect = "move"; } catch (e) {}
      }
      if (title) {
        title.classList.toggle("nsx-drop-over", dz === "title" && canTitleDock(dragging));
      }
      allDocks.forEach(function (d) {
        if (d) {
          var z = d.getAttribute("data-dock");
          d.classList.toggle("nsx-drop-over", dz === z && canTopDock(dragging));
        }
      });
    });

    document.addEventListener("drop", function (ev) {
      if (!dragging) return;
      var at = { x: ev.clientX, y: ev.clientY };
      var dz = dropZoneAt(at);
      var f = dragging;
      if (dz === "title" && canTitleDock(f)) {
        ev.preventDefault();
        ev.stopPropagation();
        f._dropped = true;
        dockTitle(f);
        cleanupDnd();
      } else if ((dz === "lead" || dz === "pre" || dz === "post") && canTopDock(f)) {
        ev.preventDefault();
        ev.stopPropagation();
        f._dropped = true;
        dockTo(f, dz);
        cleanupDnd();
      } else if (dz === "center") {
        ev.preventDefault();
        ev.stopPropagation();
        f._dropped = true;
        dockTo(f, "center");
        cleanupDnd();
      }
    });

    function inRect(p, r, tol) { return p && r && p.x >= r.left - tol && p.x <= r.right + tol && p.y >= r.top - tol && p.y <= r.bottom + tol; }
    // Ablagezone für den gerade gezogenen Fold: Guides dürfen nicht in die Elemente; über der
    // mittleren Spalte gilt für sie die Fläche direkt vor der Gliederung (pre).
    function dropZoneAt(p) {
      var z = rawZoneAt(p);
      if (z === "center" && dragging && dragging !== root && !canCenter(dragging)) return "pre";
      return z;
    }
    function rawZoneAt(p) {
      if (!p) return null;
      var tb = title ? title.getBoundingClientRect() : null;
      var rb = root ? root.getBoundingClientRect() : null;
      var zb = dropZone ? dropZone.getBoundingClientRect() : null;

      // 0. Oberhalb der Überschrift / Titelleiste darf überhaupt nichts abgelegt werden:
      if (tb && p.y < tb.top - 8) return null;

      // 1. Titelleiste: Maus über oder nahe der Titelleiste
      if (tb && (p.y <= tb.bottom + 20 || inRect(p, tb, 24))) return "title";

      // 2. Lead: direkt unter der Überschrift (über dockLead oder cluster-overview)
      var leadEnd = rb ? rb.top : (tb ? tb.bottom + 120 : 200);
      if (dockLead && (inRect(p, dockLead.getBoundingClientRect(), 20) || (tb && p.y > tb.bottom + 20 && p.y < leadEnd - 30))) return "lead";

      // 3. Pre: oberhalb der Gliederung
      if (dockPre && (inRect(p, dockPre.getBoundingClientRect(), 20) || (rb && p.y >= leadEnd - 30 && p.y <= rb.top + 10))) return "pre";

      // 4. Post: unterhalb der Gliederung
      if (dockPost && (inRect(p, dockPost.getBoundingClientRect(), 20) || (rb && p.y >= rb.bottom - 10 && p.y <= rb.bottom + 80))) return "post";

      // 5. Center: mittlere Spalte (zwischen Gliederung links und Inspektor rechts)
      if (zb && p.x >= zb.left - 30 && p.x <= zb.right + 30 && p.y > tb.bottom) return "center";

      return null;
    }

    var dropHint = null, dropHintTimer = 0;
    function showDropHint(p) {
      if (!dropHint) {
        dropHint = document.createElement("div");
        dropHint.className = "nsx-drophint";
        dropHint.setAttribute("role", "status");
        document.body.appendChild(dropHint);
      }
      dropHint.textContent = labels.drophint || "";
      dropHint.style.left = Math.max(8, Math.min((p ? p.x : innerWidth / 2) - 160, innerWidth - 330)) + "px";
      dropHint.style.top = Math.max(8, Math.min((p ? p.y : 80) + 16, innerHeight - 80)) + "px";
      dropHint.hidden = false;
      clearTimeout(dropHintTimer);
      dropHintTimer = setTimeout(function () { dropHint.hidden = true; }, 4000);
    }

    document.addEventListener("dragend", function () {
      if (!dragging) { cleanupDnd(); return; }
      var f = dragging;
      var at = lastDrag, zone = dropZoneAt(at);
      var tb = title ? title.getBoundingClientRect() : null;
      if (!f._dropped && f === root) {
        // Elemente: auf der Titelleiste andocken, unterhalb davon an ihren Platz auf der Fläche
        if (zone === "title") { f._dropped = true; dockTitle(root); }
        else if (at && tb && at.y > tb.bottom) { f._dropped = true; undockTitle(root); }
        else { showDropHint(at); if (f._fromTitle) dockTitle(root); }
      } else if (!f._dropped) {
        if (f._fromTitle) {
          // Tab aus der Titelleiste nach unten gezogen:
          // Soll immer zuverlässig ausdocken, wenn unterhalb der Titelleiste abgelegt!
          if (at && tb && at.y > tb.bottom) {
            f._dropped = true;
            if ((zone === "lead" || zone === "pre" || zone === "post") && canTopDock(f)) {
              dockTo(f, zone);
            } else {
              dockTo(f, "center");
            }
          } else if (zone === "title" && canTitleDock(f)) {
            f._dropped = true;
            dockTitle(f);
          } else if (zone === "lead" || zone === "pre" || zone === "post") {
            f._dropped = true;
            if (canTopDock(f)) dockTo(f, zone);
            else dockTo(f, "center");
          } else if (zone === "center") {
            f._dropped = true;
            dockTo(f, "center");
          } else {
            // Nur oberhalb der Titelleiste darf nicht abgelegt werden
            if (at && tb && at.y < tb.top - 8) showDropHint(at);
            dockTitle(f);
          }
        } else if ((zone === "lead" || zone === "pre" || zone === "post") && canTopDock(f)) {
          f._dropped = true;
          dockTo(f, zone);
        } else if (zone === "title" && canTitleDock(f)) {
          f._dropped = true;
          dockTitle(f);
        } else if (zone === "center") {
          f._dropped = true;
          dockTo(f, "center");
        } else {
          showDropHint(at);
          if (f._fromTop) dockTo(f, f._fromZone);
          else dockTo(f, "center");
        }
      }
      if (f._fromTitle && f._dropped && !f.classList.contains("nsx-tdocked")) {
        var tbEl = tdock.querySelector('[data-fold="' + f.getAttribute("data-fold") + '"]');
        if (tbEl) tbEl.remove();
        saveTitleDock();
      }
      cleanupDnd();
      saveOrder();
      saveAllDocks();
      if (selected) drawArrows(selected);
    });

    document.addEventListener("pointerup", function () {
      if (dragging) cleanupDnd();
    });
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && dragging) {
        ev.preventDefault();
        cleanupDnd();
      }
    });

    function isClassRow(r) { return r.getAttribute("data-kind") === "class"; }
    // Einträge mit eigener Seite (Klassen, Service-Interfaces): Detailansicht lädt die ganze Seite
    function isPageRow(r) {
      var h = r.getAttribute("data-href") || "";
      return !!h && h.charAt(0) !== "#" && !r.getAttribute("data-recs");
    }
    // Sichtbare Kurzmetadaten eines KI-Texts: Prüfstatus, Release und Abschnitte; das Dossier bleibt separat.
    function statsHtml(scope) {
      var rel = currentRelease(), all = scope.querySelectorAll(".ai-guide-release-variant");
      var v = Array.prototype.filter.call(all, function (x) { return rel && words(x, "data-applicable-releases").indexOf(rel) >= 0; })[0] || all[0] || scope;
      var ai = v.matches && v.matches(".ai") ? v : (v.querySelector(".ai") || v);
      // Guides mit Ausführlichkeitsstufen: Kennzahlen der ausführlichen Fassung (Stufe 4)
      var body = (ai.querySelector && ai.querySelector(':scope > .ai-level[data-ai-level="4"]')) || ai;
      var rev = ai.querySelector(".ai-review-state"), parts = [];
      var revState = ai.getAttribute("data-trace-review") || "";
      // "ungeprüft" weglassen (Nutzerwunsch: Ungeprüft wird in der Titelzeile nicht benötigt)
      if (rev && revState && revState !== "unreviewed") {
        parts.push('<span class="nsx-st nsx-st-rev nsx-st-' + esc(revState) + '">' + esc(rev.textContent.trim()) + "</span>");
      }

      var asof = v.getAttribute && v.getAttribute("data-asof-release");
      if (asof) parts.push('<span class="nsx-st nsx-st-asof">' + esc(asof) + "</span>");
      function st(k, n) { if (n) parts.push('<span class="nsx-st nsx-st-' + k + '">' + esc(labels[k] || "") + " <b>" + n + "</b></span>"); }
      st("secs", body.querySelectorAll("h4, h3").length);

      var dosBtn = scope.querySelector(".dossier-open-link, .ai-badge-dossier-btn");
      var dossierHtml = "";
      if (dosBtn) {
        var tgt = dosBtn.getAttribute("data-dossier-target") || "";
        dossierHtml = '<button type="button" class="nsx-st nsx-st-dossier dossier-open-link" data-dossier-target="' + esc(tgt) + '" title="' + esc(labels.dossier || "Audit-Dossier öffnen") + '">🗎 ' + esc(labels.dossierbtn || "Dossier") + '</button>';
      }

      // Die Metadaten-Pillen in einen schrumpfbaren Track packen, Dossier direkt daneben anheften
      return '<span class="nsx-stats-track">' + parts.join("") + '</span>' + dossierHtml;
    }

    // ---- Kennzahlen aller Guides in ihren Titelzeilen
    function guideStats() {
      var allG = (candidateGuides && candidateGuides.length) ? candidateGuides : (guideFold ? [guideFold] : []);
      allG.forEach(function (g) {
        if (!g) return;
        var sm = g.querySelector("summary");
        if (!sm) return;
        var box = sm.querySelector(".nsx-stats");
        if (!box) {
          box = document.createElement("span");
          box.className = "nsx-stats";
          var refBtn = sm.querySelector(".nsx-tabbtn, .nsx-hbtn");
          if (refBtn) sm.insertBefore(box, refBtn);
          else sm.appendChild(box);
        }
        box.innerHTML = statsHtml(g);
        if (typeof fillTab === "function" && g.classList.contains("nsx-tdocked")) fillTab(g);
      });
    }

    // ---- Andocken von User Guide und Themenkarte in die Titelleiste
    // Griff auf die Titelleiste ziehen: Der Fold wird dort zum Reiter, der ihn als
    // Panel unter der Leiste aufklappt. Reiter zurück in die Mitte ziehen (oder der
    // Knopf im Panel, Pfeil-ab am Reiter) löst ihn wieder. Tastatur: Pfeil-auf am
    // Griff des obersten Folds dockt an.
    var tdock = null, popFold = null;
    function canTitleDock(f) {
      if (!title || !f) return false;
      var k = f.getAttribute("data-fold");
      return !!(k && k !== "detail");
    }
    function canTopDock(f) {
      if (!f || f === root) return false;
      var k = f.getAttribute("data-fold");
      return !!(k && k !== "detail" && k !== "elements");
    }
    // User Guide, Cluster Guide, Implementer's Guide: andockbar an Titelleiste und Fläche,
    // aber nie innerhalb der Elemente (mittlere Spalte)
    function isGuideFold(f) {
      var kind = titleKeyKind((f && f.getAttribute && f.getAttribute("data-fold")) || "");
      return kind === "guide" || kind === "impl";
    }
    function canCenter(f) { return !!f && f !== root && !isGuideFold(f); }

    // ---- Elemente ein- und ausklappen (gelöst über die Kopfzeile, angedockt über den Reiter)
    // Gelöst klappen die Elemente an ihrem Platz auf der Fläche auf, nie als schwebendes Panel.
    // Angedockt gehören sie dem Reiter wie jeder andere angedockte Fold (Admin, 2026-10-13):
    // eingeklappt nicht auf der Fläche, ausgeklappt als Panel unter dem Reiter.
    function elementsOpen() { return !root.classList.contains("nsx-collapsed"); }
    function markElementsOpen(open) {
      root.classList.toggle("nsx-collapsed", !open);
      elHead.setAttribute("aria-expanded", String(open));
      if (elChev) elChev.setAttribute("aria-expanded", String(open));
      var tb = tdock && tdock.querySelector('[data-fold="elements"]');
      if (tb) tb.setAttribute("aria-expanded", String(open));
    }
    function setElementsOpen(open) {
      markElementsOpen(open);
      if (root.classList.contains("nsx-tdocked")) {
        if (open && popFold !== root) setPop(root);
        else if (!open && popFold === root) setPop(null);
      }
      updateEmpty();
      placePop();
      if (open && selected) drawArrows(selected);
    }
    elHead.addEventListener("click", function (ev) {
      if (ev.target.closest(".nsx-grip, button, a")) return;
      if (root.classList.contains("nsx-tdocked")) return;
      setElementsOpen(!elementsOpen());
      saveAllDocks();
    });
    elHead.addEventListener("keydown", function (ev) {
      if ((ev.key !== "Enter" && ev.key !== " ") || !ev.target.matches(".nsx-elchev")) return;
      ev.preventDefault();
      setElementsOpen(!elementsOpen());
      saveAllDocks();
    });
    function foldLabel(f) {
      if (!f) return "";
      if (f === root || f.getAttribute("data-fold") === "elements") return labels.elements || "Elemente";
      var h = f.querySelector("summary > h2, .nsx-elements-head > h2");
      if (!h) return f.getAttribute("data-fold") || "";
      var c = h.cloneNode(true);
      c.querySelectorAll(".ai-badge").forEach(function (x) { x.remove(); });
      return c.textContent.trim();
    }
    if (title) {
      tdock = document.createElement("span");
      tdock.className = "nsx-tdock";
      title.appendChild(tdock);
    }
    var isCls = root.classList.contains("nsx-cls"), isSvc = root.classList.contains("nsx-svc");
    // ---- Layout der Kompaktansicht (Admin, 2026-10-13): Vorgabe beim ersten Besuch und nach dem
    // Zurücksetzen: gelöst und ausgeklappt Definition, Kurzfassung des Guides und Elemente (die
    // Box „elements“, am 2026-10-13 kurz „Anforderungen“; Schlüssel und IDs unverändert) (in dieser
    // Reihenfolge), alles Übrige als eingeklappter Reiter in der Titelleiste. Gemerkt wird je Seitenart
    // (Cluster, Modul, Klasse, Namespace, Service) nur, was der Nutzer selbst ändert und von der Vorgabe
    // abweicht: Andockplätze, Reihenfolge, Ein-/Ausgeklappt. Die angedockten Elemente gelten nur für die
    // Die angedockten Elemente gehören dazu (Reiter „elements“ in der Titelleiste, seit 2026-10-13
    // nicht mehr nur für die Sitzung des Tabs); die Stufe der Guides merkt fold.js je Guide-Art.
    var pageKind = isSvc ? "service" : isCls ? "class" : isClu ? "cluster" : isMod ? "module" : "namespace";
    var layoutKey = "nsx-layout:" + pageKind;
    // Breite der Gliederung (linke Liste der Elemente) je Seitenart, Teiler zwischen Gliederung und Mitte
    var OLW_KEY = "nsx-ol-w:" + pageKind;
    // Frühere Speicherorte (bis 2026-10-13 bei jedem Besuch geschrieben): nicht mehr gelesen, beim
    // Zurücksetzen entfernt
    var LEGACY_KEYS = [ORDER_KEY, TDOCK_KEY, TDOCK_KEY + "-cls", TOPDOCK_KEY, TOPDOCK_KEY + "-cls", "nsx-docks:" + location.pathname];
    var GUIDE_LEVEL_KEY = "autodocs-guide-level:";       // wie in fold.js (Stufe je Guide-Art)
    // Früherer Sitzungsschlüssel der angedockten Elemente: nicht mehr gelesen, beim Zurücksetzen entfernt
    var elDockKey = "nsx-el-docked:" + location.pathname;
    function sessionSave(k, v) { try { if (v === null) sessionStorage.removeItem(k); else sessionStorage.setItem(k, v); } catch (e) { /* ohne Speicher */ } }
    var layoutApplying = false;

    function keysIn(el) {
      // angedockte Folds warten verborgen in der Mitte bzw. auf der Fläche: sie zählen zur Titelleiste
      return el ? Array.prototype.filter.call(el.querySelectorAll(":scope > details[data-fold]"), function (f) {
        return !f.classList.contains("nsx-tdocked");
      }).map(function (f) { return f.getAttribute("data-fold"); }).filter(Boolean) : [];
    }
    function currentLayout() {
      var closed = [];
      foldList().forEach(function (f) {
        var k = f.getAttribute("data-fold");
        if (k && f !== detFold && !f.classList.contains("nsx-tdocked") && !f.open) closed.push(k);
      });
      if (!root.classList.contains("nsx-tdocked") && !elementsOpen()) closed.push("elements");
      return {
        title: tdock ? Array.prototype.filter.call(tdock.querySelectorAll(":scope > .nsx-tab"), function (b) { return !b.hidden; })
          .map(function (b) { return b.getAttribute("data-fold"); }).filter(Boolean) : [],
        lead: keysIn(dockLead), pre: keysIn(dockPre), post: keysIn(dockPost), center: keysIn(folds),
        closed: closed.sort()
      };
    }
    function defaultLayout() {
      var lay = { title: [], lead: [], pre: [], post: [], center: [], closed: [] }, rest = [];
      var ov = foldByKey("overview");
      if (ov && ov !== root) lay.lead.push("overview");
      if (guideFold) lay.pre.push(guideFold.getAttribute("data-fold"));
      function add(k) {
        if (k && k !== "detail" && k !== "elements" && rest.indexOf(k) < 0 && lay.lead.indexOf(k) < 0 && lay.pre.indexOf(k) < 0) rest.push(k);
      }
      candidateGuides.slice().reverse().forEach(function (g) { add(g.getAttribute("data-fold")); });
      ["map", "cards", "uml"].forEach(function (k) { var f = foldByKey(k); if (f && f !== root) add(k); });
      foldList().forEach(function (f) { add(f.getAttribute("data-fold")); });
      rest.forEach(function (k) {
        var f = foldByKey(k);
        if (f && canTitleDock(f)) lay.title.push(k);
        else if (f && canTopDock(f)) lay.pre.push(k);
      });
      if (detFold) lay.center.push("detail");
      return lay;
    }
    function sameLayout(a, b) {
      function norm(l) {
        return JSON.stringify(["title", "lead", "pre", "post", "center", "closed"].map(function (z) {
          var v = (l && l[z]) || [];
          return z === "closed" ? v.slice().sort() : v;
        }));
      }
      return norm(a) === norm(b);
    }
    function loadLayout() {
      try {
        var l = JSON.parse(load(layoutKey) || "null");
        return l && typeof l === "object" && !Array.isArray(l) ? l : null;
      } catch (e) { return null; }
    }
    // Gemerkt wird nur eine Abweichung von der Vorgabe; während applyLayout nichts
    function saveAllDocks() {
      if (layoutApplying || !document.contains(root)) return;    // Seitenwechsel: alte Ansicht schreibt nichts
      var cur = currentLayout();
      if (sameLayout(cur, defaultLayout())) { save(layoutKey, null); updateResetBtn(); return; }
      // Folds anderer Seiten derselben Art (z. B. „Klassendiagramm“, das hier fehlt) behalten ihren
      // gemerkten Platz; diese Seite überschreibt nur, was sie selbst zeigt
      var old = loadLayout();
      if (old) ["title", "lead", "pre", "post", "center", "closed"].forEach(function (z) {
        (old[z] || []).forEach(function (k) {
          if (k !== "elements" && !foldByKey(k) && cur[z].indexOf(k) < 0) cur[z].push(k);
        });
      });
      save(layoutKey, JSON.stringify(cur));
      updateResetBtn();
    }
    function saveTitleDock() { saveAllDocks(); }

    // Das Panel hängt bündig unter seinem Reiter; der Reiter ist sein Titel
    function placePop() {
      if (!popFold) return;
      var b = tdock.querySelector('[data-fold="' + popFold.getAttribute("data-fold") + '"]');
      if (!b) return;
      var t = b.getBoundingClientRect(), c = folds.getBoundingClientRect();
      var rtl = getComputedStyle(root).direction === "rtl";
      var w = Math.max(t.width, Math.min(Math.max(c.width, 480), innerWidth - 24));
      var left = rtl ? Math.max(12, Math.min(t.right - w, innerWidth - 12 - w)) : Math.max(12, Math.min(t.left, innerWidth - 12 - w));
      // Guides bei sichtbarer Gliederung: das Panel beginnt am Rand der Gliederung und deckt
      // die mittlere Spalte (mindestens bis unter den Reiter); die Gliederung bleibt frei.
      var ob = outline && isGuideFold(popFold) && outline.getClientRects().length ? outline.getBoundingClientRect() : null;
      var bb = ob && dropZone.getBoundingClientRect();
      if (ob && ob.width && bb && bb.width) {
        if (rtl) {
          var gr = ob.left, gl = Math.max(12, Math.min(bb.left, t.left));
          if (gr - gl >= t.width) { left = gl; w = gr - gl; }
        } else {
          var gl2 = ob.right, gr2 = Math.min(innerWidth - 12, Math.max(bb.right, t.right));
          if (gr2 - gl2 >= t.width) { left = gl2; w = gr2 - gl2; }
        }
      }
      if (popFold === root) {
        // Elemente: Panel über die Breite der Seite, Höhe bis knapp über den Fensterrand
        var mb = root.parentNode.getBoundingClientRect();
        left = Math.max(12, Math.min(mb.left, t.left));
        w = Math.max(t.width, Math.min(innerWidth - 12, Math.max(mb.right, t.right)) - left);
        popFold.style.setProperty("--nsx-pop-h", Math.max(240, innerHeight - t.bottom - 12) + "px");
      }
      var tabx = rtl ? left + w - t.right : t.left - left;
      popFold.style.top = t.bottom - 1 + "px";
      popFold.style.left = left + "px";
      popFold.style.width = w + "px";
      popFold.style.setProperty("--nsx-tabw", t.width + "px");
      popFold.style.setProperty("--nsx-tabx", Math.max(0, tabx) + "px");
      popFold.classList.toggle("nsx-pop-shift", tabx > 1);
    }
    function setPop(f) {
      // Elemente erscheinen nur angedockt als Panel unter ihrem Reiter; gelöst klappen sie an ihrem Platz auf
      if (f === root && !root.classList.contains("nsx-tdocked")) f = null;
      if (popFold && popFold !== f) {
        popFold.classList.remove("nsx-pop", "nsx-pop-shift");
        ["top", "left", "width"].forEach(function (k) { popFold.style[k] = ""; });
        popFold.style.removeProperty("--nsx-pop-h");
        var ob = tdock.querySelector('[data-fold="' + popFold.getAttribute("data-fold") + '"]');
        if (ob) ob.setAttribute("aria-expanded", "false");
        if (popFold === root) markElementsOpen(false);   // Panel zu: angedockte Elemente eingeklappt
      }
      popFold = f;
      if (!f) return;
      if (f === root) markElementsOpen(true);
      f.classList.add("nsx-pop");
      if (f.tagName === "DETAILS") f.open = true;
      placePop();
      var b = tdock.querySelector('[data-fold="' + f.getAttribute("data-fold") + '"]');
      if (b) b.setAttribute("aria-expanded", "true");
      if (selected) drawArrows(selected);
    }
    function fillTab(f) {
      var b = tdock && tdock.querySelector('[data-fold="' + f.getAttribute("data-fold") + '"]');
      if (!b) return;
      var headerEl = f.querySelector("summary, .nsx-elements-head");
      if (!headerEl) return;
      var c = headerEl.cloneNode(true);
      c.querySelectorAll(".nsx-hbtn, .nsx-canon-link, .nsx-tabbtn, .nsx-backbtn, .nsx-elchev").forEach(function (x) { x.remove(); });
      c.querySelectorAll("[role], [tabindex], [id]").forEach(function (x) { x.removeAttribute("role"); x.removeAttribute("tabindex"); x.removeAttribute("id"); });
      var g = c.querySelector(".nsx-grip");
      if (g) { g.removeAttribute("title"); g.removeAttribute("aria-label"); g.setAttribute("aria-hidden", "true"); }
      var h = c.querySelector("h2");
      if (h) {
        var hs = document.createElement("span");
        hs.className = "nsx-tab-h";
        hs.innerHTML = h.innerHTML;
        h.replaceWith(hs);
      }
      b.innerHTML = c.innerHTML;
    }

    function foldByKey(k) {
      if (!k) return null;
      if (k === "elements" || (root && root.getAttribute("data-fold") === k)) return root;
      var f = folds && folds.querySelector(':scope > details[data-fold="' + k + '"]');
      if (f) return f;
      for (var i = 0; i < allDocks.length; i++) {
        if (allDocks[i]) {
          f = allDocks[i].querySelector(':scope > details[data-fold="' + k + '"]');
          if (f) return f;
        }
      }
      return document.querySelector('details.nsx-fold[data-fold="' + k + '"]');
    }

    function decorateFoldButtons(f) {
      if (!f) return;
      var sm = f.querySelector("summary, .nsx-elements-head");
      if (!sm) return;
      var gr = sm.querySelector(".nsx-grip");
      if (gr && !gr.draggable) bindGrip(gr);
      
      // Tab-Knopf: Als Reiter in die Titelleiste
      var tabBtn = sm.querySelector(".nsx-tabbtn");
      if (canTitleDock(f) && !f.classList.contains("nsx-tdocked")) {
        if (!tabBtn) {
          tabBtn = document.createElement("button");
          tabBtn.type = "button";
          tabBtn.className = "nsx-hbtn nsx-tabbtn";
          tabBtn.innerHTML = ICON_TABDOCK;
          tabBtn.title = labels.tdock || "Als Reiter in die Titelleiste";
          tabBtn.setAttribute("aria-label", labels.tdock || "Als Reiter in die Titelleiste");
          tabBtn.addEventListener("click", function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            dockTitle(f);
          });
          sm.appendChild(tabBtn);
        }
      } else if (tabBtn) {
        tabBtn.remove();
      }
      
      // Zurück-Knopf: In die mittlere Spalte zurück
      var backBtn = sm.querySelector(".nsx-backbtn");
      // Guides auf der Fläche haben kein „zurück in die Mitte“ (sie gehören nicht in die Elemente)
      if ((f.classList.contains("nsx-topdocked") && canCenter(f)) || f.classList.contains("nsx-tdocked")) {
        if (!backBtn) {
          backBtn = document.createElement("button");
          backBtn.type = "button";
          backBtn.className = "nsx-hbtn nsx-backbtn";
          backBtn.addEventListener("click", function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            if (f.classList.contains("nsx-tdocked")) {
              undockTitle(f);
            } else {
              undockTop(f);
            }
          });
          sm.appendChild(backBtn);
        }
        // Symbol und Beschriftung folgen dem Zustand (derselbe Knopf wandert zwischen Ablage und Reiter)
        var undock = f.classList.contains("nsx-tdocked");
        var act = undock ? "undock" : "center";
        var blab = undock ? (labels.tpop || "Abdocken – im Inhalt anzeigen") : (labels.tback || "In die mittlere Spalte");
        if (backBtn.getAttribute("data-act") !== act) {
          backBtn.innerHTML = undock ? ICON_UNDOCK : ICON_TOCENTER;
          backBtn.setAttribute("data-act", act);
        }
        backBtn.title = blab;
        backBtn.setAttribute("aria-label", blab);
      } else if (backBtn && !f.classList.contains("nsx-pop")) {
        backBtn.remove();
      }
    }

    function dockTitle(f) {
      if (!canTitleDock(f)) return;
      var key = f.getAttribute("data-fold");
      f.classList.remove("nsx-topdocked", "nsx-pop", "nsx-pop-shift", "nsx-dragging");
      f.removeAttribute("data-docked-zone");
      ["top", "left", "width"].forEach(function (k) { f.style[k] = ""; });
      if (f !== root) {
        // Guides warten angedockt auf der Fläche der Seite (verborgen), nicht in den Elementen
        if (canCenter(f)) { if (f.parentNode !== folds) folds.appendChild(f); }
        else if (root.contains(f) || f.parentNode !== root.parentNode) root.parentNode.insertBefore(f, dockPre || root);
      }
      f.classList.add("nsx-tdocked");

      var old = tdock.querySelector('[data-fold="' + key + '"]');
      if (old) {
        old.hidden = false;
      } else {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "nsx-tab";
        b.draggable = true;
        b.setAttribute("data-fold", key);
        b.setAttribute("aria-expanded", f === root ? String(elementsOpen()) : "false");
        b.title = labels.tundock || "";
        tdock.appendChild(b);
      }
      fillTab(f);
      decorateFoldButtons(f);
      if (f === root) {
        // Angedockt verlassen die Elemente die Fläche: der Reiter besitzt sie, zunächst eingeklappt
        setElementsOpen(false);
      }
      saveAllDocks();
      updateEmpty();
    }

    function undockTitle(f, before, preview) {
      if (!f || !f.classList.contains("nsx-tdocked")) return;
      if (popFold === f) setPop(null);
      f.classList.remove("nsx-tdocked");
      if (f === root) {
        // Zurück auf die Fläche: Lösen stellt Gliederung, Mitte und Inspektor ausgeklappt wieder her
        markElementsOpen(true);
      }
      var b = tdock.querySelector('[data-fold="' + f.getAttribute("data-fold") + '"]');
      if (b) { if (preview) b.hidden = true; else b.remove(); }
      if (f !== root && !canCenter(f)) {
        // Guide: zurück auf die Fläche (vor der Gliederung), nie in die Elemente
        dockTo(f, "pre");
        return;
      }
      if (f !== root) {
        if (before !== undefined) folds.insertBefore(f, before);
        else if (f.parentNode !== folds) folds.appendChild(f);
      }
      decorateFoldButtons(f);
      if (preview) { updateEmpty(); return; }
      saveAllDocks();
      updateEmpty();
      saveOrder();
      if (selected) drawArrows(selected);
    }

    function dockTo(f, zoneName, beforeEl) {
      if (!f) return;
      if (f === root) {
        if (zoneName === "title") dockTitle(root);
        else undockTitle(root);
        return;
      }
      if (zoneName === "title") {
        dockTitle(f);
        return;
      }
      if (zoneName === "center" && !canCenter(f)) zoneName = "pre";
      if (zoneName === "center") {
        if (!elementsOpen()) setElementsOpen(true);   // Ziel in den Elementen muss sichtbar sein
        if (f.classList.contains("nsx-tdocked")) {
          undockTitle(f, beforeEl || folds.firstChild);
        } else {
          f.classList.remove("nsx-topdocked");
          f.removeAttribute("data-docked-zone");
          if (beforeEl && beforeEl.parentNode === folds) folds.insertBefore(f, beforeEl);
          else if (f.parentNode !== folds) folds.appendChild(f);
        }
        f.classList.remove("nsx-topdocked");
        f.removeAttribute("data-docked-zone");
        f.open = true;
        decorateFoldButtons(f);
        saveOrder();
        saveAllDocks();
        updateEmpty();
        if (selected) drawArrows(selected);
        return;
      }
      
      var targetDock = (zoneName === "lead" ? dockLead : (zoneName === "post" ? dockPost : dockPre));
      if (!targetDock) targetDock = dockPre;
      if (f.classList.contains("nsx-tdocked")) {
        undockTitle(f);
      }
      f.classList.add("nsx-topdocked");
      f.setAttribute("data-docked-zone", zoneName);
      f.classList.remove("nsx-tdocked", "nsx-pop", "nsx-pop-shift");
      ["top", "left", "width"].forEach(function (k) { f.style[k] = ""; });
      f.open = true;
      if (beforeEl && beforeEl.parentNode === targetDock) {
        targetDock.insertBefore(f, beforeEl);
      } else if (f.parentNode !== targetDock) {
        targetDock.appendChild(f);
      }
      decorateFoldButtons(f);
      saveAllDocks();
      updateEmpty();
      if (selected) drawArrows(selected);
    }

    function dockTop(f, targetZone) {
      dockTo(f, targetZone || (f.getAttribute("data-docked-zone") || "pre"));
    }

    function undockTop(f) {
      dockTo(f, "center");
    }

    // Layout herstellen (Beim Öffnen, Zurücksetzen und Rückgängig): jeder Fold an seinen Platz in der
    // gemerkten Reihenfolge; Folds ohne gemerkten Platz wie in der Vorgabe.
    function applyLayout(lay) {
      layoutApplying = true;
      var elDocked = !!(lay && lay.title && lay.title.indexOf("elements") >= 0);
      setPop(null);
      if (root.classList.contains("nsx-tdocked")) undockTitle(root);
      var def = defaultLayout(), placed = {};
      function place(k, zone) {
        if (!k || placed[k] || k === "elements") return;
        var f = foldByKey(k);
        if (!f || f === root) return;
        if (f === detFold) {
          if (zone === "center") { folds.appendChild(f); placed[k] = 1; }
          return;
        }
        if (zone === "title") {
          if (!canTitleDock(f)) return;
          dockTitle(f);
          var b = tdock.querySelector('.nsx-tab[data-fold="' + k + '"]');
          if (b) tdock.appendChild(b);
        } else if (zone === "center") {
          if (!canCenter(f)) return;
          dockTo(f, "center");
          folds.appendChild(f);
        } else {
          if (!canTopDock(f)) return;
          dockTo(f, zone);
          var z = zone === "lead" ? dockLead : zone === "post" ? dockPost : dockPre;
          if (z) z.appendChild(f);
        }
        placed[k] = 1;
      }
      ["title", "lead", "pre", "post", "center"].forEach(function (z) {
        ((lay && lay[z]) || []).forEach(function (k) { place(k, z); });
      });
      ["title", "lead", "pre", "post", "center"].forEach(function (z) {
        def[z].forEach(function (k) { place(k, z); });
      });
      var closed = (lay && lay.closed) || [];
      foldList().forEach(function (f) {
        var k = f.getAttribute("data-fold");
        if (k && f !== detFold && !f.classList.contains("nsx-tdocked")) f.open = closed.indexOf(k) < 0;
        f._layoutOpen = f.open;          // toggle dieses Setzens ist keine Änderung des Nutzers
      });
      if (elDocked && canTitleDock(root)) dockTitle(root);           // eingeklappt im Reiter
      else setElementsOpen(closed.indexOf("elements") < 0);
      // Reiter in der gemerkten Reihenfolge (auch der Reiter der Elemente), danach Reiter ohne
      // gemerkten Platz in der Reihenfolge der Vorgabe
      if (tdock) ((lay && lay.title) || []).concat(def.title).forEach(function (k) {
        var b = tdock.querySelector(':scope > .nsx-tab[data-fold="' + k + '"]');
        if (b && !b._ordered) { b._ordered = true; tdock.appendChild(b); }
      });
      if (tdock) Array.prototype.forEach.call(tdock.children, function (b) { b._ordered = false; });
      foldList().forEach(decorateFoldButtons);
      decorateFoldButtons(root);
      layoutApplying = false;
      updateEmpty();
      if (selected) drawArrows(selected);
      updateResetBtn();
    }
    function applyAllDocks() {
      applyLayout(loadLayout() || defaultLayout());
    }

    // ---- Standardansicht wiederherstellen (Knopf neben dem Dichteschalter): löscht das gemerkte
    // Layout dieser Seitenart samt angedockten Elementen, Breite des Inspektors und gemerkter Stufe der
    // Guides dieser Seite und stellt die Vorgabe sofort her. Keine Rückfrage; stattdessen bietet ein
    // Hinweis einige Sekunden lang „Rückgängig“ an. Aktiv nur, wenn etwas von der Vorgabe abweicht
    // (gemerkt wird ohnehin nur eine Abweichung, die Prüfung kostet nur einige Speicherzugriffe).
    var ICON_RESET = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3.5 12a8.5 8.5 0 1 0 2.6-6.1"/><path d="M3.5 3.5v4.6h4.6"/><rect x="9" y="9" width="6" height="6" rx="1"/></svg>';
    var UNDO_MS = 8000;
    var resetBtn = null, undoBox = null, undoTimer = 0;
    function pageGuides() {
      return Array.prototype.filter.call(document.querySelectorAll(".ai[data-ai-levels][data-ai-level-kind]"), function (a) {
        return !(detBody && detBody.contains(a));
      });
    }
    function firstLevel(a) { return parseInt((a.getAttribute("data-ai-levels-shown") || "2").split(/\s+/)[0], 10) || 2; }
    function setLevel(a, n) {
      if (window.autodocsGuideLevels && n) window.autodocsGuideLevels.set(a, n, false);
      else if (n) a.setAttribute("data-ai-level-cur", String(n));
    }
    function levelKinds() {
      var ks = {};
      pageGuides().forEach(function (a) { var k = a.getAttribute("data-ai-level-kind"); if (!(k in ks)) ks[k] = firstLevel(a); });
      return ks;
    }
    function layoutCustomized() {
      if (load(layoutKey) !== null || load(W_KEY) !== null || load(OLW_KEY) !== null) return true;
      var ks = levelKinds();
      return Object.keys(ks).some(function (k) { var v = load(GUIDE_LEVEL_KEY + k); return v !== null && parseInt(v, 10) !== ks[k]; });
    }
    function updateResetBtn() {
      if (!resetBtn) return;
      var on = layoutCustomized();
      resetBtn.setAttribute("aria-disabled", String(!on));
      resetBtn.classList.toggle("is-off", !on);
    }
    function layoutSnapshot() {
      var lv = {};
      Object.keys(levelKinds()).forEach(function (k) { lv[k] = load(GUIDE_LEVEL_KEY + k); });
      return { layout: currentLayout(), raw: load(layoutKey), w: load(W_KEY), olw: load(OLW_KEY),
               wStyle: root.style.getPropertyValue("--nsx-aside-w"), olStyle: root.style.getPropertyValue("--nsx-ol-w"), lv: lv,
               cur: pageGuides().map(function (a) { return [a, parseInt(a.getAttribute("data-ai-level-cur"), 10) || 0]; }),
               legacy: LEGACY_KEYS.map(function (k) { return [k, load(k)]; }) };
    }
    function restoreLayout(snap) {
      save(layoutKey, snap.raw);
      save(W_KEY, snap.w);
      save(OLW_KEY, snap.olw);
      if (snap.olStyle) root.style.setProperty("--nsx-ol-w", snap.olStyle); else root.style.removeProperty("--nsx-ol-w");
      Object.keys(snap.lv).forEach(function (k) { save(GUIDE_LEVEL_KEY + k, snap.lv[k]); });
      snap.legacy.forEach(function (kv) { save(kv[0], kv[1]); });
      if (snap.wStyle) root.style.setProperty("--nsx-aside-w", snap.wStyle); else root.style.removeProperty("--nsx-aside-w");
      applyLayout(snap.layout);
      snap.cur.forEach(function (p) { setLevel(p[0], p[1]); });
      updateResetBtn();
    }
    function hideUndo() {
      clearTimeout(undoTimer);
      if (undoBox) undoBox.hidden = true;
    }
    function showUndo(snap) {
      if (!undoBox) {
        undoBox = document.createElement("div");
        undoBox.className = "nsx-undo";
        undoBox.setAttribute("role", "status");
        undoBox.innerHTML = '<span class="nsx-undo-t"></span><button type="button" class="nsx-undo-b"></button>';
        document.body.appendChild(undoBox);
      }
      undoBox.querySelector(".nsx-undo-t").textContent = labels.resetdone || "Standardansicht wiederhergestellt";
      var ub = undoBox.querySelector(".nsx-undo-b");
      ub.textContent = labels.undo || "Rückgängig";
      ub.onclick = function () { hideUndo(); restoreLayout(snap); };
      if (resetBtn) {
        var r = resetBtn.getBoundingClientRect();
        undoBox.style.top = Math.round(r.bottom + 8) + "px";
        undoBox.style.insetInlineEnd = Math.max(12, Math.round(getComputedStyle(root).direction === "rtl" ? r.left : innerWidth - r.right)) + "px";
      }
      undoBox.hidden = false;
      clearTimeout(undoTimer);
      undoTimer = setTimeout(hideUndo, UNDO_MS);
    }
    function resetLayout() {
      var snap = layoutSnapshot();
      save(layoutKey, null);
      sessionSave(elDockKey, null);
      save(W_KEY, null);
      save(OLW_KEY, null);
      root.style.removeProperty("--nsx-ol-w");
      LEGACY_KEYS.forEach(function (k) { save(k, null); });
      Object.keys(levelKinds()).forEach(function (k) { save(GUIDE_LEVEL_KEY + k, null); });
      root.style.removeProperty("--nsx-aside-w");
      applyLayout(defaultLayout());
      pageGuides().forEach(function (a) { setLevel(a, firstLevel(a)); });
      updateResetBtn();
      showUndo(snap);
    }
    (function () {
      var tools = document.querySelector(".crumb-tools");
      if (!tools && !title) return;
      resetBtn = document.createElement("button");
      resetBtn.type = "button";
      resetBtn.className = "crumb-toggle nsx-resetbtn";
      resetBtn.innerHTML = ICON_RESET;
      resetBtn.title = labels.reset || "Standardansicht wiederherstellen";
      resetBtn.setAttribute("aria-label", labels.reset || "Standardansicht wiederherstellen");
      resetBtn.addEventListener("click", function (ev) {
        ev.preventDefault();
        if (resetBtn.getAttribute("aria-disabled") === "true") return;
        resetLayout();
      });
      var dens = tools && tools.querySelector("[data-density-toggle]");
      if (dens) dens.parentNode.insertBefore(resetBtn, dens.nextSibling);
      else if (tools) tools.appendChild(resetBtn);
      else title.appendChild(resetBtn);
    })();
    // Ein- und Ausklappen gelöster Folds gehört zum Layout (toggle bubbelt nicht: Capture)
    document.addEventListener("toggle", function (ev) {
      var f = ev.target;
      if (!document.contains(root)) return;
      if (!f.matches || !f.matches("details.nsx-fold[data-fold]") || f === detFold) return;
      if (f.classList.contains("nsx-tdocked") || f.classList.contains("nsx-pop")) return;
      if (f._layoutOpen === f.open) return;               // von applyLayout gesetzt
      f._layoutOpen = f.open;
      saveAllDocks();
    }, true);
    // Stufenwahl im Guide (fold.js) ändert, ob die Ansicht von der Vorgabe abweicht
    document.addEventListener("click", function (ev) {
      if (document.contains(root) && ev.target.closest && ev.target.closest("[data-ai-level-cycle], [data-ai-level-step]")) setTimeout(function () { updateResetBtn(); markAi(); }, 0);
    });

    function applyTopDock() {
      applyAllDocks();
    }

    allDocks.forEach(function (dock) {
      if (!dock) return;
      dock.addEventListener("dragstart", onDragStart);
      dock.addEventListener("dragover", function (ev) {
        if (!dragging || !canTopDock(dragging)) return;
        ev.preventDefault();
        try { ev.dataTransfer.dropEffect = "move"; } catch (e) {}
        dock.classList.add("nsx-drop-over");
        var t = ev.target.closest && ev.target.closest("details[data-fold]");
        if (t && t !== dragging && t.parentNode === dock) {
          var r = t.getBoundingClientRect();
          dock.insertBefore(dragging, ev.clientY < r.top + r.height / 2 ? t : t.nextSibling);
        }
      });
      dock.addEventListener("dragleave", function (ev) {
        if (!dock.contains(ev.relatedTarget)) dock.classList.remove("nsx-drop-over");
      });
      dock.addEventListener("drop", function (ev) {
        // Elemente über einer Ablage der Fläche: kein Abbruch, dragend legt sie an ihren Platz
        if (dragging === root) return;
        if (!dragging || !canTopDock(dragging)) { cleanupDnd(); return; }
        ev.preventDefault();
        ev.stopPropagation();
        var f = dragging;
        f._dropped = true;
        var zone = dock.getAttribute("data-dock") || "pre";
        var t = ev.target.closest && ev.target.closest("details[data-fold]");
        var beforeEl = (t && t !== f && t.parentNode === dock) ? (ev.clientY < t.getBoundingClientRect().top + t.getBoundingClientRect().height / 2 ? t : t.nextSibling) : undefined;
        dockTo(f, zone, beforeEl);
        cleanupDnd();
      });
      dock.addEventListener("click", function (ev) {
        var back = ev.target.closest(".nsx-backbtn");
        if (back) {
          ev.preventDefault();
          ev.stopPropagation();
          var f = back.closest("details[data-fold]");
          if (f) undockTop(f);
        }
      });
    });

    // Ist die Mitte leer (alles angedockt, nichts ausgewählt), steht dort der Hinweis
    var emptyHint = detBody && detBody.querySelector(".nsx-hint");
    if (emptyHint) folds.setAttribute("data-empty", emptyHint.textContent.trim());
    function updateEmpty() { folds.classList.toggle("nsx-empty", !foldList().some(function (f) { return !f.hidden && !f.classList.contains("nsx-tdocked"); })); }

    if (tdock) {
      tdock.addEventListener("click", function (ev) {
        var b = ev.target.closest(".nsx-tab");
        if (!b) return;
        clearSelection();
        var f = foldByKey(b.getAttribute("data-fold"));
        if (f === root) { setElementsOpen(!elementsOpen()); return; }   // Panel der Elemente auf/zu
        setPop(popFold === f ? null : f);
      });
      tdock.addEventListener("keydown", function (ev) {
        var b = ev.target.closest(".nsx-tab");
        if (!b) return;
        if (ev.key === "ArrowLeft" || ev.key === "ArrowRight") {
          ev.preventDefault();
          var fwd = (ev.key === "ArrowRight") !== (getComputedStyle(root).direction === "rtl");
          if (fwd && b.nextElementSibling) tdock.insertBefore(b.nextElementSibling, b);
          else if (!fwd && b.previousElementSibling) tdock.insertBefore(b, b.previousElementSibling);
          b.focus();
          saveAllDocks();
          return;
        }
        if (ev.key !== "ArrowDown") return;
        ev.preventDefault();
        undockTitle(foldByKey(b.getAttribute("data-fold")), folds.firstChild);
      });
      // Reiter zurück in die Mitte oder ins topDock ziehen
      tdock.addEventListener("dragstart", function (ev) {
        var b = ev.target.closest && ev.target.closest(".nsx-tab");
        if (!b) return;
        var f = foldByKey(b.getAttribute("data-fold"));
        if (!f) return;
        startFoldDrag(ev, f, true);
      });
      // Fold auf die Titelleiste ziehen
      title.addEventListener("dragover", function (ev) {
        if (!dragging || !canTitleDock(dragging)) return;
        if (dragging._fromTitle) {
          // Zurück über der Leiste: Vorschau sofort wieder andocken; über einem anderen
          // Reiter wird umsortiert
          ev.preventDefault();
          if (!dragging.classList.contains("nsx-tdocked")) dockTitle(dragging);
          var me = tdock.querySelector('[data-fold="' + dragging.getAttribute("data-fold") + '"]');
          var over = ev.target.closest && ev.target.closest(".nsx-tab");
          if (me && over && over !== me) {
            var r = over.getBoundingClientRect(), rtl = getComputedStyle(root).direction === "rtl";
            var after = rtl ? ev.clientX < r.left + r.width / 2 : ev.clientX > r.left + r.width / 2;
            tdock.insertBefore(me, after ? over.nextSibling : over);
          }
          return;
        }
        ev.preventDefault();
        ev.dataTransfer.dropEffect = "move";
        title.classList.add("nsx-drop-over");
      });
      title.addEventListener("dragleave", function (ev) { if (!title.contains(ev.relatedTarget)) title.classList.remove("nsx-drop-over"); });
      title.addEventListener("drop", function (ev) {
        if (dragging && dragging._fromTitle) {
          ev.preventDefault();
          dragging._dropped = true;
          saveAllDocks();
          cleanupDnd();
          return;
        }
        if (!dragging || !canTitleDock(dragging)) {
          cleanupDnd();
          return;
        }
        ev.preventDefault();
        var f = dragging;
        f._dropped = true;
        dockTitle(f);
        cleanupDnd();
      });
      document.addEventListener("keydown", function (ev) {
        if (ev.key !== "Escape" || !popFold) return;
        // Escape in einem Dialog oder Eingabefeld der Elemente schließt nur diesen, nicht das Panel
        if (popFold === root && ev.target.closest && ev.target.closest("dialog, input, textarea, select, [contenteditable]")) return;
        setPop(null);
      });
      document.addEventListener("click", function (ev) {
        // Das Panel der Elemente ist Arbeitsfläche (Dialoge, Kuration): Klick daneben lässt es offen
        if (popFold && popFold !== root && !popFold.contains(ev.target) && !tdock.contains(ev.target)) setPop(null);
      });
      window.addEventListener("scroll", placePop, { passive: true });
      window.addEventListener("resize", placePop);
    }
    function addButton(f, cls, html, label) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "nsx-hbtn " + cls;
      b.innerHTML = html;
      b.title = label || "";
      b.setAttribute("aria-label", label || "");
      f.querySelector("summary").appendChild(b);
      return b;
    }
    guideStats();
    window.addEventListener("hashchange", guideStats);

    // ---- Gruppierung der Gliederung
    function setBy(mode) {
      var btn = outline.querySelector('.nsx-by button[data-by="' + mode + '"]');
      if (!btn) return false;
      outline.querySelectorAll(".nsx-by button").forEach(function (b) { b.setAttribute("aria-pressed", String(b === btn)); });
      outline.querySelectorAll(".nsx-ol").forEach(function (o) { o.hidden = o.getAttribute("data-by") !== mode; });
      revealSelected();
      histModeChanged(mode === "since");
      return true;
    }
    setBy(load(BY_KEY) || "");

    // ---- Gruppen der Gliederung ein- und ausklappen (Aufnahme 13:03): Pfeil vor dem Titel,
    // Klick auf den Titel (außer Verweis bzw. Release-Titel der Historie), Tastatur am Pfeil.
    // Vorgabe ausgeklappt; gemerkt wird je Seite nur für die Sitzung (sessionStorage).
    var OL_KEY = "nsx-ol-collapsed:" + location.pathname, collapsed = {};
    try { collapsed = JSON.parse(sessionStorage.getItem(OL_KEY) || "{}") || {}; } catch (e) { collapsed = {}; }
    function ogKey(og) { return (og.parentNode.getAttribute("data-by") || "") + "|" + og.textContent.trim(); }
    function ogItems(og) {
      var out = [];
      for (var x = og.nextElementSibling; x && !x.matches(".nsx-og"); x = x.nextElementSibling) out.push(x);
      return out;
    }
    function setOg(og, open, keep) {
      og.setAttribute("aria-expanded", String(open));
      var ch = og.querySelector(":scope > .nsx-chev");
      if (ch) ch.setAttribute("aria-expanded", String(open));
      ogItems(og).forEach(function (x) { x.hidden = !open; });
      if (!keep) return;
      if (open) delete collapsed[ogKey(og)]; else collapsed[ogKey(og)] = 1;
      try { sessionStorage.setItem(OL_KEY, JSON.stringify(collapsed)); } catch (e) { /* ohne Speicher */ }
    }
    if (outline) outline.querySelectorAll(".nsx-ol > .nsx-og").forEach(function (og) {
      var ch = document.createElement("span");
      ch.className = "nsx-chev";
      ch.setAttribute("role", "button");
      ch.setAttribute("tabindex", "0");
      ch.setAttribute("aria-label", og.textContent.trim());
      og.insertBefore(ch, og.firstChild);
      setOg(og, !collapsed[ogKey(og)], false);
    });
    if (outline) {
      outline.addEventListener("click", function (ev) {
        var og = ev.target.closest(".nsx-og");
        if (!og || ev.target.closest("a") || (og.classList.contains("nsx-hg") && !ev.target.closest(".nsx-chev"))) return;
        ev.preventDefault();
        setOg(og, og.getAttribute("aria-expanded") === "false", true);
      });
      outline.addEventListener("keydown", function (ev) {
        if ((ev.key !== "Enter" && ev.key !== " ") || !ev.target.matches(".nsx-chev")) return;
        ev.preventDefault();
        var og = ev.target.closest(".nsx-og");
        setOg(og, og.getAttribute("aria-expanded") === "false", true);
      });
    }

    // ---- Inspektorbreite
    var split = aside && aside.querySelector(".nsx-split");
    function setW(w) {
      w = Math.round(Math.max(220, Math.min(w, root.clientWidth * 0.55)));
      root.style.setProperty("--nsx-aside-w", w + "px");
      split.setAttribute("aria-valuenow", String(w));
      return w;
    }
    if (split) {
      split.setAttribute("title", labels.split || "");
      split.setAttribute("aria-label", labels.split || "");
      split.setAttribute("aria-valuemin", "220");
      var w0 = parseInt(load(W_KEY), 10);
      if (w0) setW(w0);
      var rtl = getComputedStyle(root).direction === "rtl";
      split.addEventListener("pointerdown", function (ev) {
        ev.preventDefault();
        split.setPointerCapture(ev.pointerId);
        root.classList.add("nsx-resizing");
        function move(e) {
          var r = aside.getBoundingClientRect();
          setW(rtl ? e.clientX - r.left : r.right - e.clientX);
        }
        function up() {
          split.removeEventListener("pointermove", move);
          split.removeEventListener("pointerup", up);
          root.classList.remove("nsx-resizing");
          save(W_KEY, String(aside.getBoundingClientRect().width | 0));
          updateResetBtn();
          if (selected) { drawArrows(selected); showRelations(selected); }
        }
        split.addEventListener("pointermove", move);
        split.addEventListener("pointerup", up);
      });
      split.addEventListener("keydown", function (ev) {
        var d = { ArrowLeft: 24, ArrowRight: -24 }[ev.key];
        if (!d) return;
        ev.preventDefault();
        save(W_KEY, String(setW(aside.getBoundingClientRect().width + (rtl ? -d : d))));
        updateResetBtn();
      });
      split.addEventListener("dblclick", function () { root.style.removeProperty("--nsx-aside-w"); save(W_KEY, null); updateResetBtn(); });
    }

    // ---- Breite der Gliederung (Admin, 2026-10-14): Teiler zwischen Gliederung und Mitte. Ziehen oder Pfeiltasten
    // am fokussierten Teiler (Pos1/Ende: schmalste/breiteste), Doppelklick setzt die Vorgabe der Ansicht zurück
    // (style.css: 220 px, Historie 330 px). Gemerkt je Seitenart in localStorage (nsx-ol-w:<art>); ohne Speicher
    // gilt die Breite nur für den Besuch. Rechts-nach-links (ar): die Gliederung steht rechts, die Richtungen kehren um.
    var OLW_MIN = 160, OLW_MAX = 640, OLW_STEP = 16;
    var olBody = root.querySelector(":scope > .nsx-body"), olSplit = null;
    function olRtl() { return getComputedStyle(root).direction === "rtl"; }
    function olMax() { return Math.max(OLW_MIN, Math.min(OLW_MAX, Math.round(root.clientWidth * 0.5))); }
    function olWidth() { return outline ? Math.round(outline.getBoundingClientRect().width) : 0; }
    function setOlW(w) {
      w = Math.round(Math.max(OLW_MIN, Math.min(w, olMax())));
      root.style.setProperty("--nsx-ol-w", w + "px");
      if (olSplit) { olSplit.setAttribute("aria-valuenow", String(w)); placeOlSplit(); }
      return w;
    }
    // Lage: in der Spaltenlücke zwischen Gliederung und Mitte, von der Oberkante der Spalten bis zum Ende der
    // Box (die Gliederung klebt beim Scrollen, die Lücke bleibt überall greifbar); ausgeblendet ohne Gliederung
    function placeOlSplit() {
      if (!olSplit) return;
      var vis = !!outline.offsetParent && !!olBody.offsetParent;
      olSplit.hidden = !vis;
      if (!vis) return;
      var gap = parseFloat(getComputedStyle(root).columnGap) || 16;
      var x = olRtl() ? olBody.offsetLeft + olBody.offsetWidth : olBody.offsetLeft - gap;
      olSplit.style.left = Math.round(x) + "px";
      olSplit.style.width = Math.round(gap) + "px";
      olSplit.style.top = Math.round(Math.min(olBody.offsetTop, outline.offsetTop)) + "px";
    }
    function olSyncAria() {
      if (!olSplit) return;
      placeOlSplit();
      olSplit.setAttribute("aria-valuemax", String(olMax()));
      olSplit.setAttribute("aria-valuenow", String(olWidth()));
    }
    if (outline && olBody) {
      olSplit = document.createElement("div");
      olSplit.className = "nsx-olsplit";
      olSplit.setAttribute("role", "separator");
      olSplit.setAttribute("aria-orientation", "vertical");
      olSplit.setAttribute("tabindex", "0");
      olSplit.setAttribute("aria-valuemin", String(OLW_MIN));
      olSplit.setAttribute("title", labels.olsplit || labels.split || "");
      olSplit.setAttribute("aria-label", labels.olsplit || labels.split || "");
      root.insertBefore(olSplit, outline);       // vor der Gliederung: Reihenfolge der übrigen Teile bleibt
      var olw0 = parseInt(load(OLW_KEY), 10);
      if (olw0) setOlW(olw0);
      olSyncAria();
      var olDone = function () {
        save(OLW_KEY, String(olWidth()));
        olSyncAria();
        updateResetBtn();
        if (selected) { drawArrows(selected); showRelations(selected); }
      };
      olSplit.addEventListener("pointerdown", function (ev) {
        if (ev.button !== 0) return;
        ev.preventDefault();
        olSplit.setPointerCapture(ev.pointerId);
        root.classList.add("nsx-resizing");
        var x0 = ev.clientX, w0 = olWidth(), rtl = olRtl();
        function move(e) { setOlW(w0 + (rtl ? x0 - e.clientX : e.clientX - x0)); }
        function up() {
          olSplit.removeEventListener("pointermove", move);
          olSplit.removeEventListener("pointerup", up);
          olSplit.removeEventListener("pointercancel", up);
          root.classList.remove("nsx-resizing");
          olDone();
        }
        olSplit.addEventListener("pointermove", move);
        olSplit.addEventListener("pointerup", up);
        olSplit.addEventListener("pointercancel", up);
      });
      olSplit.addEventListener("keydown", function (ev) {
        var w = olWidth(), rtl = olRtl(), d = 0;
        if (ev.key === "ArrowRight") d = rtl ? -OLW_STEP : OLW_STEP;
        else if (ev.key === "ArrowLeft") d = rtl ? OLW_STEP : -OLW_STEP;
        else if (ev.key === "Home") d = OLW_MIN - w;
        else if (ev.key === "End") d = olMax() - w;
        else return;
        ev.preventDefault();
        setOlW(w + d);
        olDone();
      });
      olSplit.addEventListener("dblclick", function () {
        root.style.removeProperty("--nsx-ol-w");
        save(OLW_KEY, null);
        olSyncAria();
        updateResetBtn();
      });
      window.addEventListener("resize", olSyncAria);
      if (window.ResizeObserver) {
        var olRo = new ResizeObserver(function () { placeOlSplit(); });
        olRo.observe(root);
        olRo.observe(olBody);
        olRo.observe(outline);
      }
    }

    // ---- Leiste „Gruppierung nach“ bleibt oben in der Gliederung stehen; der Kopf des Release-Rasters
    // (Historie) klebt darunter (--nsx-by-h)
    var byBar = outline && outline.querySelector(":scope > .nsx-by");
    if (byBar) {
      var setByH = function () { outline.style.setProperty("--nsx-by-h", byBar.offsetHeight + "px"); };
      setByH();
      if (window.ResizeObserver) new ResizeObserver(setByH).observe(byBar);
    }

    // ---- Pfeile über der Karte
    var overlay = null;
    if (map) {
      overlay = svgEl("svg", { "class": "nsx-arrows", "aria-hidden": "true" });
      var defs = svgEl("defs");
      var mk = svgEl("marker", { id: "nsx-ah-" + Math.random().toString(36).slice(2), viewBox: "0 0 8 8", refX: "7", refY: "4", markerWidth: "6", markerHeight: "6", orient: "auto-start-reverse" });
      mk.appendChild(svgEl("path", { d: "M0,0 L8,4 L0,8 z", "class": "nsx-ah" }));
      defs.appendChild(mk);
      overlay.appendChild(defs);
      overlay._marker = mk.id;
      map.appendChild(overlay);
    }
    function edgePoint(r, toward) {
      var cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      var dx = toward.x - cx, dy = toward.y - cy;
      if (!dx && !dy) return { x: cx, y: cy };
      var s = Math.min((r.width / 2) / Math.abs(dx || 1e-9), (r.height / 2) / Math.abs(dy || 1e-9));
      return { x: cx + dx * s, y: cy + dy * s };
    }
    function clearArrows() { if (overlay) overlay.querySelectorAll("path.nsx-edge").forEach(function (p) { p.remove(); }); }
    function drawArrows(name) {
      clearArrows();
      if (!overlay || !chips[name] || !map.offsetParent) return;
      var base = map.getBoundingClientRect();
      overlay.setAttribute("width", map.scrollWidth);
      overlay.setAttribute("height", map.scrollHeight);
      function rect(n) {
        var b = chips[n].getBoundingClientRect();
        return { left: b.left - base.left, top: b.top - base.top, width: b.width, height: b.height };
      }
      var edges = [];
      words(chips[name], "data-out").forEach(function (t) { if (chips[t]) edges.push([name, t]); });
      words(chips[name], "data-in").forEach(function (s) { if (chips[s]) edges.push([s, name]); });
      edges.slice(0, 60).forEach(function (e) {
        var a = rect(e[0]), b = rect(e[1]);
        var ac = { x: a.left + a.width / 2, y: a.top + a.height / 2 }, bc = { x: b.left + b.width / 2, y: b.top + b.height / 2 };
        var p1 = edgePoint(a, bc), p2 = edgePoint(b, ac);
        var mx = (p1.x + p2.x) / 2, my = (p1.y + p2.y) / 2;
        var dx = p2.x - p1.x, dy = p2.y - p1.y, len = Math.sqrt(dx * dx + dy * dy) || 1;
        var bend = Math.min(28, len / 4);
        overlay.appendChild(svgEl("path", {
          "class": "nsx-edge" + (e[0] === name ? " out" : " in"),
          d: "M" + p1.x.toFixed(1) + "," + p1.y.toFixed(1) + " Q" + (mx - dy / len * bend).toFixed(1) + "," + (my + dx / len * bend).toFixed(1) + " " + p2.x.toFixed(1) + "," + p2.y.toFixed(1),
          "marker-end": "url(#" + overlay._marker + ")"
        }));
      });
    }

    // ---- Hervorheben in der Karte
    function highlight(name) {
      if (!map) return;
      var rel = words(rows[name], "data-out").concat(words(rows[name], "data-in"));
      map.classList.add("dim");
      Object.keys(chips).forEach(function (n) {
        chips[n].classList.toggle("self", n === name);
        chips[n].classList.toggle("rel", rel.indexOf(n) >= 0);
      });
      drawArrows(name);
    }
    function unhighlight() {
      if (!map) return;
      map.classList.remove("dim");
      Object.keys(chips).forEach(function (n) { chips[n].classList.remove("self", "rel"); });
      clearArrows();
    }
    function restore() { if (selected) highlight(selected); else unhighlight(); }

    // ---- Vererbungsdiagramm
    function bases(n) { return rows[n] ? words(rows[n], "data-base") : []; }
    // Ebenen mit drei oder mehr Klassen (oder zu breit für die Spalte) werden als
    // Baum untereinander gezeichnet, sofern die Nachbarebene zur Auswahl hin nur
    // einen Knoten hat; sonst nebeneinander mit waagrechtem Scrollen.
    function inheritanceSvg(name, avail) {
      var up = [], seen = dict(), level = bases(name);
      seen[name] = 1;
      for (var d = 0; d < 5 && level.length; d++) {
        level = level.filter(function (x) { return !seen[x]; });
        level.forEach(function (x) { seen[x] = 1; });
        if (!level.length) break;
        up.unshift(level);
        var next = [];
        level.forEach(function (x) { bases(x).forEach(function (y) { if (next.indexOf(y) < 0) next.push(y); }); });
        level = next;
      }
      var down = rows[name] ? words(rows[name], "data-derived") : [];
      if (!up.length && !down.length) return null;
      var layers = up.concat([[name]]).concat(down.length ? [down] : []);
      var selfIdx = up.length;
      var CH = 6.6, H = 20, HG = 8, VG = 26, SG = 6, IND = 18, PAD = 4, pos = dict();
      function bw(n) { return n.length * CH + 12; }
      function lw(layer) { return layer.reduce(function (s, n) { return s + bw(n); }, 0) + HG * (layer.length - 1); }
      var stacked = layers.map(function (layer, li) {
        if (li === selfIdx || layer.length < 2) return false;
        var anchor = layers[li < selfIdx ? li + 1 : li - 1];
        return anchor.length === 1 && (layer.length >= 3 || lw(layer) + 2 * PAD > avail);
      });
      var anyStack = stacked.some(Boolean);
      var width = 0;
      layers.forEach(function (layer, li) {
        width = Math.max(width, stacked[li] ? IND + Math.max.apply(null, layer.map(bw)) : lw(layer));
      });
      width += 2 * PAD;
      // senkrechte Lage: gestapelte Ebenen über der Auswahl in umgekehrter Folge
      var y = PAD, tops = [];
      layers.forEach(function (layer, li) {
        tops[li] = y;
        y += (stacked[li] ? layer.length * (H + SG) - SG : H) + VG;
      });
      var height = y - VG + PAD;
      layers.forEach(function (layer, li) {
        if (stacked[li]) {
          layer.forEach(function (n, k) { pos[n] = { x: PAD + IND, y: tops[li] + k * (H + SG), w: bw(n) }; });
        } else {
          var x = anyStack ? PAD : (width - lw(layer)) / 2;
          layer.forEach(function (n) { pos[n] = { x: x, y: tops[li], w: bw(n) }; x += bw(n) + HG; });
        }
      });
      var svg = svgEl("svg", { "class": "nsx-inhsvg", width: Math.ceil(width), height: Math.ceil(height), role: "img" });
      var defs = svgEl("defs");
      var tri = svgEl("marker", { id: "nsx-tri-" + Math.random().toString(36).slice(2), viewBox: "0 0 10 10", refX: "9", refY: "5", markerWidth: "9", markerHeight: "9", orient: "auto" });
      tri.appendChild(svgEl("path", { d: "M0,0 L10,5 L0,10 z", "class": "nsx-tri" }));
      defs.appendChild(tri);
      svg.appendChild(defs);
      function path(d, arrow) {
        var a = { "class": "nsx-inh-edge", d: d };
        if (arrow) a["marker-end"] = "url(#" + tri.id + ")";
        svg.appendChild(svgEl("path", a));
      }
      var drawn = dict();
      layers.forEach(function (layer, li) {
        if (!stacked[li]) return;
        var anchor = layers[li < selfIdx ? li + 1 : li - 1][0], A = pos[anchor];
        var tx = PAD + IND / 2;
        if (li > selfIdx) {
          // Ableitungen: gemeinsamer Stamm mit einem Pfeil zur Basis
          var last = pos[layer[layer.length - 1]];
          layer.forEach(function (n) { path("M" + pos[n].x + "," + (pos[n].y + H / 2) + " H" + tx, false); drawn[n + ">" + anchor] = 1; });
          path("M" + tx + "," + (last.y + H / 2) + " V" + (A.y + H + 1), false);
          path("M" + tx + "," + (A.y + H + 12) + " V" + (A.y + H), true);
        } else {
          // Basisklassen: Stamm vom Kind nach oben, Pfeil an jede Basis
          var first = pos[layer[0]];
          path("M" + tx + "," + A.y + " V" + (first.y + H / 2), false);
          layer.forEach(function (n) { path("M" + tx + "," + (pos[n].y + H / 2) + " H" + pos[n].x, true); drawn[anchor + ">" + n] = 1; });
        }
      });
      function edge(child, parent) {
        var c = pos[child], p = pos[parent];
        if (!c || !p || drawn[child + ">" + parent]) return;
        path("M" + (c.x + c.w / 2) + "," + c.y + " L" + (p.x + p.w / 2) + "," + (p.y + H), true);
      }
      Object.keys(pos).forEach(function (n) { bases(n).forEach(function (b) { edge(n, b); }); });
      down.forEach(function (d) { edge(d, name); });
      Object.keys(pos).forEach(function (n) {
        var p = pos[n], g = svgEl("g", { "class": "nsx-inh-node" + (n === name ? " self" : "") + (rows[n] ? "" : " ext") });
        g.appendChild(svgEl("rect", { x: p.x, y: p.y, width: p.w, height: H, rx: 4 }));
        var t = svgEl("text", { x: p.x + p.w / 2, y: p.y + 14, "text-anchor": "middle" });
        t.textContent = n;
        g.appendChild(t);
        if (rows[n]) { g.setAttribute("data-jump", n); g.setAttribute("tabindex", "0"); }
        svg.appendChild(g);
      });
      return svg;
    }

    // ---- Inspektor: allgemeine Angaben, Übersichten und Bezüge des Eintrags
    // Verweise auf Einträge dieses Namespace wählen aus und heben beim Überfahren
    // hervor; Klassen anderer Namespaces tragen ihr Paket.
    function decorate(box) {
      box.querySelectorAll("a[href]").forEach(function (a) {
        if (a.hasAttribute("data-jump") || a.hasAttribute("data-n")) return;
        var href = a.getAttribute("href");
        if (href.indexOf("#nsx-c-") === 0) return;
        var u;
        try { u = new URL(href, location.href); } catch (e) { return; }
        if (u.pathname === location.pathname && u.hash) {
          var id = decodeURIComponent(u.hash.slice(1));
          if (recOwner[id]) { a.setAttribute("href", "#" + id); a.setAttribute("data-n", recOwner[id]); }
          return;
        }
        // Clusterseiten: Verweise auf Elemente anderer Teile dieses Clusters wählen hier aus
        var pid = u.hash && decodeURIComponent(u.hash.slice(1));
        if (isClu && pid && recOwner[pid] && partPaths[u.pathname]) {
          a.setAttribute("href", "#" + pid);
          a.setAttribute("data-n", recOwner[pid]);
          return;
        }
        var n = byPath[u.pathname];
        if (n) { a.setAttribute("data-jump", n); a.setAttribute("href", "#" + rows[n].id); return; }
        var m = /\/(cl_[A-Za-z0-9_]+)\.html$/.exec(u.pathname);
        if (m && ext[m[1]]) { a.classList.add("nsx-ext"); a.title = ext[m[1]]; }
        var mf = (isMod || isClu && cluClassic) && /\/([^\/]+\.html)$/.exec(u.pathname);
        if (mf && ext[mf[1]]) { a.classList.add("nsx-ext"); a.title = ext[mf[1]]; }
      });
    }
    function fnSig(name, ctx) {
      var c = fnIndex[name] || [];
      var re = new RegExp("\\b" + ctx.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\b");
      return c.filter(function (x) { return re.test(x.code.textContent); })[0] || c[0] || null;
    }
    function relItems(names, ctx) {
      return names.map(function (n) {
        if (rows[n]) return '<li><a href="#' + rows[n].id + '" data-jump="' + esc(n) + '">' + esc(n) + "</a></li>";
        var f = fnSig(n, ctx);
        if (f) return '<li class="nsx-ifn"><a class="nsx-fname" href="#' + esc(f.id) + '">' + esc(n) + '</a><code class="nsx-isig">' + f.code.innerHTML + "</code></li>";
        return "<li>" + esc(n) + "</li>";
      });
    }
    var pageCache = {}, insTimer = 0;
    // Lange Abschnitte sind einklappbar; der Zustand gilt je Überschrift für die ganze Sitzung
    var secOpen = {};
    function section(title, n) {
      var head = "<h4>" + esc(title || "") + (n ? ' <span class="nsx-cnt">' + n + "</span>" : "") + "</h4>";
      var sct;
      if (n > 8) {
        sct = document.createElement("details");
        sct.className = "nsx-is";
        sct.open = secOpen[title] === true;
        sct.innerHTML = "<summary>" + head + "</summary>";
        sct.addEventListener("toggle", function () { secOpen[title] = sct.open; });
      } else {
        sct = document.createElement("section");
        sct.className = "nsx-is";
        sct.innerHTML = head;
      }
      relBox.appendChild(sct);
      return sct;
    }
    function renderInspector(name, main) {
      var r = rows[name], kindEl = r.querySelector(".nsx-nm > .kind"), isClass = r.getAttribute("data-kind") === "class";
      relBox.setAttribute("data-owner", name);
      relBox.hidden = false;
      if (hint) hint.hidden = true;
      relBox.innerHTML = '<div class="t"><a href="#' + r.id + '" data-jump="' + esc(name) + '">' + esc(name) + '</a></div><div class="k">' + esc(kindEl ? kindEl.textContent : "") + "</div>";
      var dropped = words(r, "data-dropped");
      if (dropped.length) relBox.insertAdjacentHTML("beforeend", '<p class="nsx-dropnote">' + esc(labels.dropped || "") + " " + esc(dropped[0]) + "</p>");
      // Klassenhierarchie zuoberst
      var svg = isClass && inheritanceSvg(name, relBox.clientWidth || (aside ? aside.clientWidth - 24 : 260));
      if (svg) {
        var wrap = document.createElement("div");
        wrap.className = "nsx-inhwrap";
        wrap.appendChild(svg);
        section(labels.inh).appendChild(wrap);
      }
      var recs = words(r, "data-recs").map(function (id) { return isClu ? remote[id] : document.getElementById(id); }).filter(Boolean);
      // Clusterseiten, solange die Seite des Teils noch nicht geladen ist: Signatur aus der Übersicht
      if (isClu && !recs.length && !isClass) {
        var rs = r.querySelector(".nsx-ds > .nsx-sig code");
        if (rs) {
          var stub = document.createElement("article"), spre = document.createElement("pre");
          stub.className = "rec";
          spre.className = "syntax";
          spre.innerHTML = rs.innerHTML;
          stub.appendChild(spre);
          recs = [stub];
        }
      }
      // Beschreibung
      var desc = main ? main.querySelector(":scope > .desc") : (recs[0] && recs[0].querySelector(".desc:not(.nsx-hmark)"));
      if (!desc) desc = r.querySelector(".nsx-desc");
      if (desc) {
        var d = desc.cloneNode(true);
        d.removeAttribute("id");
        d.hidden = false;                       // Original kann in der Historie verborgen sein
        d.removeAttribute("data-nsx-hhide");
        d.className = "nsx-idesc";
        relBox.appendChild(d);
      }
      // Signatur (Funktionen, Typen, Enumerationen)
      if (!isClass) {
        var sigs = recs.map(function (rec) { return rec.querySelector("pre.syntax:not(.nsx-hmark)"); }).filter(Boolean);
        if (sigs.length) {
          var ss = section(labels.sig, sigs.length > 1 ? sigs.length : 0);
          sigs.forEach(function (sg) { var c = sg.cloneNode(true); c.removeAttribute("id"); c.removeAttribute("data-nsx-hhide"); c.hidden = false; c.className = "nsx-isig"; ss.appendChild(c); });
        }
      }
      // Allgemeine Angaben
      var props = main ? main.querySelector(":scope > table.props") : (recs.length === 1 && recs[0].querySelector("table.props"));
      if (props) { var pc = props.cloneNode(true); pc.className = "nsx-iprops"; section(labels.gen).appendChild(pc); }
      if (r.getAttribute("data-kind") === "enumeration" && recs.length === 1) {
        var vals = Array.prototype.map.call(recs[0].querySelectorAll("table.params tr td:first-child"), function (td) { return td.textContent.trim(); })
          .filter(function (v) { return v && v.indexOf("=") < 0; });
        if (vals.length) section(labels.vals, vals.length).insertAdjacentHTML("beforeend", '<ul class="nsx-ilist nsx-icols">' + vals.map(function (v) { return "<li><code>" + esc(v) + "</code></li>"; }).join("") + "</ul>");
      }
      // Methoden-, Typ- und Enum-Übersichten der Klassenseite
      if (main) Array.prototype.forEach.call(main.querySelectorAll(":scope > h3"), function (h) {
        var ul = h.nextElementSibling;
        if (!ul || !ul.matches("ul.mlist")) return;
        var c = ul.cloneNode(true);
        c.className = "nsx-ilist";
        section(h.textContent.trim(), c.children.length).appendChild(c);
      });
      // Nicht-Member-Funktionen der Klasse
      var own = words(r, "data-fns").length ? r.querySelectorAll(".nsx-sig") : [];
      if (own.length) {
        var fl = document.createElement("ul");
        fl.className = "nsx-ilist";
        own.forEach(function (sg) {
          var code = sg.querySelector("code"), go = sg.querySelector("a.nsx-go");
          var fm = code && /(operator\s*[^\s(]+|[A-Za-z_~][\w:]*)\s*\(/.exec(code.textContent);
          var fname = fm ? fm[1].replace(/\s+/g, "").split("::").pop() : go && go.textContent;
          if (code && go) fl.insertAdjacentHTML("beforeend", '<li class="nsx-ifn"><a class="nsx-fname" href="#' + esc(fnId(go)) + '">' + esc(fname) + '</a><code class="nsx-isig">' + code.innerHTML + "</code></li>");
        });
        section(labels.fns, own.length).appendChild(fl);
      }
      // Bezüge: Verwendet (auch Klassen anderer Pakete), Verwendet von, Kommt vor in
      var out = relItems(words(r, "data-out"), name), seen = dict();
      words(r, "data-out").forEach(function (n) { seen[n] = 1; });
      if (main) main.querySelectorAll("a[href]").forEach(function (a) {
        var m = /\/(cl_[A-Za-z0-9_]+)\.html(?:#|$)/.exec(a.getAttribute("href"));
        var n = a.textContent.trim();
        if (!m || !ext[m[1]] || seen[n]) return;
        seen[n] = 1;
        out.push('<li><a href="' + esc(a.getAttribute("href").split("#")[0]) + '" class="nsx-ext">' + esc(n) + '</a> <span class="nsx-pkg">' + esc(ext[m[1]]) + "</span></li>");
      });
      // Modulseiten: Typen anderer Module (Plattform-, ComStack-, Std-Typen) aus der Signatur;
      // Classic-Cluster: Typen außerhalb des Clusters (innerhalb sind es Bezüge)
      if (isMod || isClu && cluClassic) recs.forEach(function (rec) {
        rec.querySelectorAll(":scope > pre.syntax a[href]").forEach(function (a) {
          var href = a.getAttribute("href"), f = href.split("#")[0], n = a.textContent.trim();
          if (!f || !n || seen[n]) return;
          var hid = href.split("#")[1];
          if (isClu && hid && recOwner[decodeURIComponent(hid)]) return;
          var fb = (/([^\/]+\.html)$/.exec(f) || [])[1] || f;
          seen[n] = 1;
          out.push('<li><a href="' + esc(href) + '" class="nsx-ext">' + esc(n) + '</a> <span class="nsx-pkg">' + esc(ext[fb] || ext[f] || fb) + "</span></li>");
        });
      });
      [["out", out], ["in", relItems(words(r, "data-in"), name)], ["uses", isClass ? [] : relItems(words(r, "data-uses"), name)]].forEach(function (x) {
        if (x[1].length) section(labels[x[0]], x[1].length).insertAdjacentHTML("beforeend", "<ul>" + x[1].join("") + "</ul>");
      });
      if (relBox.children.length <= 2) relBox.insertAdjacentHTML("beforeend", '<p class="nsx-hint">' + esc(labels.none || "") + "</p>");
      decorate(relBox);
      histInspector(name);
    }
    function showRelations(name) {
      var r = rows[name];
      if (!r || !relBox) return;
      var href = isPageRow(r) && r.getAttribute("data-href");
      renderInspector(name, href && pageCache[href] || null);
      clearTimeout(insTimer);
      if (href && !pageCache[href]) {
        insTimer = setTimeout(function () {
          classPage(href).then(function (main) {
            pageCache[href] = main;
            if (relBox.getAttribute("data-owner") === name && !relBox.hidden) renderInspector(name, main);
          }, function () { /* Inspektor bleibt bei den Angaben der Übersicht */ });
        }, name === selected ? 0 : 250);
      } else if (!href && missingRemote(r).length) {
        insTimer = setTimeout(function () {
          remotePage(r.getAttribute("data-page")).then(function () {
            if (relBox.getAttribute("data-owner") === name && !relBox.hidden) renderInspector(name, null);
          }, function () { /* Inspektor bleibt bei den Angaben der Übersicht */ });
        }, name === selected ? 0 : 250);
      }
    }

    // ---- Detailansicht: kanonische Darstellung des ausgewählten Elements
    var moved = [], token = 0, pages = {};
    function restoreMoved() {
      clearHistMarks();              // Markierungen der Historie nicht mit zurückgeben
      moved.forEach(function (m) { m.ph.parentNode.insertBefore(m.el, m.ph); m.ph.parentNode.removeChild(m.ph); });
      moved = [];
    }
    // Clusterseiten: Records der Teile (Modul- bzw. Namespace-Seiten) nach Anker; einmal je
    // Seite geladen, Verweise auf diese Seite umgerechnet, Elemente des Clusters wählen aus.
    var remote = {}, remotePages = {};
    function missingRemote(r) {
      if (!isClu || !r.getAttribute("data-page")) return [];
      return words(r, "data-recs").concat(words(r, "data-fns")).filter(function (id) { return !remote[id]; });
    }
    function rebase(el, url) {
      el.querySelectorAll("script").forEach(function (x) { x.remove(); });
      [el].concat(Array.prototype.slice.call(el.querySelectorAll("[href]"))).forEach(function (a) {
        var v = a.getAttribute && a.getAttribute("href");
        if (v === null || v === undefined) return;
        var u;
        try { u = new URL(v, url); } catch (e) { return; }
        var hid = u.hash ? decodeURIComponent(u.hash.slice(1)) : "";
        if (hid && recOwner[hid] && (u.pathname === url.pathname || partPaths[u.pathname])) a.setAttribute("href", "#" + hid);
        else a.setAttribute("href", u.href);
      });
      el.querySelectorAll("[src]").forEach(function (e) { e.setAttribute("src", new URL(e.getAttribute("src"), url).href); });
      return el;
    }
    function remotePage(href) {
      var url = new URL(href, location.href), key = url.pathname;
      if (remotePages[key]) return remotePages[key];
      var p = (location.protocol === "file:" || !window.fetch ? Promise.reject(new Error("file")) :
        fetch(url.href).then(function (res) { if (!res.ok) throw new Error(res.status); return res.text(); })).then(function (t) {
        var doc = new DOMParser().parseFromString(t, "text/html");
        Object.keys(recOwner).forEach(function (id) {
          if (remote[id]) return;
          var pg = rows[recOwner[id]].getAttribute("data-page");
          if (!pg || new URL(pg, location.href).pathname !== key) return;
          var el = doc.getElementById(id);
          if (el) remote[id] = rebase(document.importNode(el, true), url);
        });
        return true;
      });
      remotePages[key] = p;
      p.catch(function () { delete remotePages[key]; });
      return p;
    }
    // Clusterseiten entleihen nie aus dem eigenen Dokument: dort können gleiche IDs in
    // Kurationsdialogen stehen; die Records kommen aus den Seiten der Teile
    function borrow(id, into) {
      if (isClu) {
        if (!remote[id] || detBody.querySelector('[id="' + CSS.escape(id) + '"]')) return null;
        var c = remote[id].cloneNode(true);
        into.appendChild(c);
        return c;
      }
      var el = document.getElementById(id);
      if (!el || detBody.contains(el)) return null;
      var ph = document.createComment("nsx");
      el.parentNode.insertBefore(ph, el);
      into.appendChild(el);
      moved.push({ el: el, ph: ph });
      return el;
    }
    // Klassenseiten im neuen Layout (cls-index) erscheinen in der Detailansicht flach,
    // wie die kanonische Klassenseite ohne Skript: Übersicht je Mitgliedsart,
    // Klassendiagramm und Dokumentation, ohne Gliederung, Folds und Inspektor.
    function flattenClassIndex(main) {
      var sec = main.querySelector("section.nsx");
      if (!sec) return;
      // Service-Interfaces: Die Seite zeigt Mitgliederliste und Dokumentation schon selbst
      if (sec.classList.contains("nsx-svc")) { sec.parentNode.removeChild(sec); unfoldDocs(main); return; }
      var doc = main.ownerDocument, frag = doc.createDocumentFragment();
      var rowsBy = dict();
      sec.querySelectorAll(".nsx-row").forEach(function (r) { rowsBy[r.getAttribute("data-n")] = r; });
      var ol = sec.querySelector('.nsx-ol[data-by="kind"]');
      var title = null, ul = null;
      function group(text) {
        title = doc.createElement("h3");
        title.textContent = text;
        ul = doc.createElement("ul");
        ul.className = "mlist";
        frag.appendChild(title);
        frag.appendChild(ul);
      }
      if (ol) Array.prototype.forEach.call(ol.children, function (x) {
        if (x.matches(".nsx-og")) group(x.textContent.trim());
        else if (ul && x.matches("a.nsx-oi")) item(rowsBy[x.getAttribute("data-n")]);
      });
      // Seiten mit wenigen Einträgen (schlichte Liste ohne Gliederung): Übersicht aus den
      // Gruppen der Liste
      else sec.querySelectorAll(".nsx-list > .nsx-sec").forEach(function (gs) {
        var gt = gs.querySelector(":scope > .nsx-gt");
        group(gt ? gt.textContent.trim() : "");
        gs.querySelectorAll(":scope > .nsx-row").forEach(item);
      });
      function item(r) {
        if (!r) return;
        var d = r.querySelector(".nsx-desc");
        var sigs = r.getAttribute("data-kind") === "class" ? [] : r.querySelectorAll(".nsx-sig code");
        var li = doc.createElement("li");
        if (sigs.length) sigs.forEach(function (c, i) {
          var code = doc.createElement("code");
          code.className = "sig";
          code.innerHTML = c.innerHTML;
          if (i) li.appendChild(doc.createElement("br"));
          li.appendChild(code);
        });
        else li.innerHTML = '<a href="' + esc(r.getAttribute("data-href") || "") + '"><code>' + esc(r.getAttribute("data-n")) + "</code></a>";
        if (d) li.insertAdjacentHTML("beforeend", ' <span class="dim">' + d.innerHTML + "</span>");
        ul.appendChild(li);
      }
      var uml = sec.querySelector('.nsx-fold[data-fold="uml"]');
      if (uml) {
        var h = doc.createElement("h2");
        h.className = "sect";
        h.textContent = uml.querySelector("summary h2").textContent.trim();
        frag.appendChild(h);
        Array.prototype.slice.call(uml.children, 1).forEach(function (c) { frag.appendChild(c); });
      }
      sec.parentNode.replaceChild(frag, sec);
      unfoldDocs(main);
    }
    // Eingeklappte Dokumentationsabschnitte wieder in den Fluss der Seite stellen
    function unfoldDocs(main) {
      var doc = main.ownerDocument;
      main.querySelectorAll("details.nsx-doc").forEach(function (dd) {
        var f2 = doc.createDocumentFragment(), kids = Array.prototype.slice.call(dd.childNodes);
        kids.forEach(function (k) {
          if (k.nodeType === 1 && k.tagName === "SUMMARY") Array.prototype.slice.call(k.childNodes).forEach(function (c) { f2.appendChild(c); });
          else f2.appendChild(k);
        });
        dd.parentNode.replaceChild(f2, dd);
      });
    }
    function classPage(href) {
      if (pages[href]) return pages[href];
      var url = new URL(href, location.href);
      var p = (location.protocol === "file:" || !window.fetch ? Promise.reject(new Error("file")) :
        fetch(url.href).then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })).then(function (t) {
        var main = new DOMParser().parseFromString(t, "text/html").querySelector("main");
        if (!main) throw new Error("main");
        flattenClassIndex(main);
        main.querySelectorAll("script").forEach(function (s) { s.remove(); });
        // Kurations-Dialoge behalten ihre IDs: „Kuratieren“ findet sie über data-dossier-target
        function inDialog(e) { return !!e.closest("dialog.dossier-modal"); }
        main.querySelectorAll("[id]").forEach(function (e) { if (!inDialog(e)) e.id = "nsx-c-" + e.id; });
        ["aria-labelledby", "aria-controls", "aria-describedby", "for"].forEach(function (a) {
          main.querySelectorAll("[" + a + "]").forEach(function (e) {
            if (inDialog(e)) return;
            e.setAttribute(a, e.getAttribute(a).split(" ").map(function (x) { return "nsx-c-" + x; }).join(" "));
          });
        });
        main.querySelectorAll("[href]").forEach(function (a) {
          var v = a.getAttribute("href");
          if (v.charAt(0) === "#") { if (v.length > 1) a.setAttribute("href", "#nsx-c-" + v.slice(1)); }
          else a.setAttribute("href", new URL(v, url).href);
        });
        main.querySelectorAll("[src]").forEach(function (e) { e.setAttribute("src", new URL(e.getAttribute("src"), url).href); });
        return main;
      });
      pages[href] = p;
      p.catch(function () { delete pages[href]; });
      return p;
    }
    // ---- Scrollverhalten
    // Eine Auswahl lässt stehen, was der Leser gerade sieht (der angeklickte Eintrag
    // bleibt unter der Maus). Gescrollt wird nur, wenn die Detailansicht nicht im
    // Blick ist, dann in einer Bewegung an den oberen Rand unter der Titelleiste.
    // Gliederung und Inspektor holen zusätzlich den Anfang der Detailansicht, wenn
    // ihr Kopf gerade über dem Fenster liegt (der gelesene Inhalt wird ersetzt).
    var anchorEl = null;
    function keepAnchor(fn) {
      var a = anchorEl, y = a && a.isConnected && a.getClientRects().length ? a.getBoundingClientRect().top : null;
      fn();
      if (y === null || !a.isConnected || !a.getClientRects().length) return;
      var d = a.getBoundingClientRect().top - y;
      if (Math.abs(d) >= 1) window.scrollBy(0, d);
    }
    function docked(f) { return !f.hidden && !f.classList.contains("nsx-tdocked"); }
    function firstVisibleFold() {
      return foldList().filter(function (f) { return docked(f) && f.getBoundingClientRect().bottom > navTop(); })[0] || null;
    }
    function detailVisible() {
      if (!detFold || detFold.hidden) return false;
      // sichtbar heißt: ein lesbarer Teil, nicht nur die Kopfzeile am Fensterrand
      var b = detFold.getBoundingClientRect();
      var seen = Math.min(b.bottom, innerHeight) - Math.max(b.top, navTop());
      return seen >= Math.min(200, b.height * 0.5);
    }
    function headerAbove() { return detFold.getBoundingClientRect().top < pinH() - 2; }
    function toDetail() {
      if (!detFold || detFold.hidden) return;
      detFold.open = true;
      if (Math.abs(detFold.getBoundingClientRect().top - pinH()) > 2) detFold.scrollIntoView({ block: "start", behavior: behavior });
    }
    // Element der Detailansicht nach ID (vor gleichen IDs anderswo im Dokument)
    function inDetail(id) { return detBody && detBody.querySelector('[id="' + CSS.escape(id) + '"]') || null; }
    function openTo(el) {
      for (var p = el.parentElement; p && p !== detBody; p = p.parentElement) if (p.tagName === "DETAILS") p.open = true;
      if (el.tagName === "DETAILS") el.open = true;          // z.B. Review-Panel eines Records
      el.scrollIntoView({ block: "start", behavior: behavior });
    }
    // Titelzeile der Detailansicht: Art (in API-Farbe), voll qualifizierter Name als Link
    // auf die kanonische Sicht (Klassen- bzw. Record-Seite), eigene SWS-ID; kein Upstream.
    // Eigene Kompaktansicht eines Eintrags: Klassen- bzw. Dienstseite, auf Clusterseiten die Seite
    // des Teils mit dem Eintragsanker (#nsx-e-…), sonst der Eintragsanker dieser Seite
    function ownHref(name) {
      var r = rows[name];
      if (!r) return "";
      if (isPageRow(r)) return r.getAttribute("data-href");
      var pg = r.getAttribute("data-page");
      return (pg ? pg : "") + "#" + r.id;
    }
    function setTitle(name, info) {
      if (!detTitle) return;
      var r = rows[name];
      info = info || {};
      var k = info.kind || (r.querySelector(".nsx-nm > .kind") || {}).textContent || "";
      // Name in der Titelzeile führt zur eigenen Kompaktansicht des Elements (Wunsch des Admins
      // vom 2026-10-13); der Versions-Explorer bleibt über die SWS-ID erreichbar
      var href = ownHref(name) || info.href || "";
      var qn = info.qname || name;
      detTitle.innerHTML = (k ? '<span class="kind">' + esc(k.trim()) + "</span> " : "")
        + (href ? '<a class="nsx-detname" href="' + esc(href) + '">' + esc(qn) + "</a>" : '<span class="nsx-detname">' + esc(qn) + "</span>")
        + (info.sws ? " " + info.sws : "")
        + (isMod && modName ? ' <span class="nsx-modbadge"><span class="kind">' + esc(labels.mod || "") + "</span> " + esc(modName) + "</span>" : "")
        + (isClu ? cluBadges(r) : "");
      var vis = chips[name] && /(?:^|\s)(vis-[a-z]+)/.exec(chips[name].className);
      detFold.setAttribute("data-vis", vis ? vis[1] : "");
    }
    // Clusterseiten: Abzeichen „Cluster <Name>“ und „Modul/Namespace <Teil>“ (Verweis auf dessen Seite)
    function cluBadges(r) {
      var part = r.getAttribute("data-part") || "", pg = r.getAttribute("data-page") || "", out = "";
      if (part) out += ' <a class="nsx-modbadge nsx-partbadge" href="' + esc(pg) + '"><span class="kind">' + esc(labels.mod || "") + "</span> " + esc(part) + "</a>";
      if (cluName) out += ' <span class="nsx-modbadge nsx-clubadge" title="' + esc(cluName) + '"><span class="kind">' + esc(labels.clu || "") + "</span> " + esc(cluName) + "</span>";
      return out;
    }
    function swsHtml(el) {
      var sw = el && el.querySelector(".sws");
      if (!sw) return "";
      var c = sw.cloneNode(true);
      c.querySelectorAll("[id]").forEach(function (e) { e.removeAttribute("id"); });
      return '<span class="sws">' + c.innerHTML + "</span>";
    }
    function scopeOf(rec) {
      var out = "";
      if (rec) rec.querySelectorAll("table.props tr").forEach(function (tr) {
        var th = tr.querySelector("th"), td = tr.querySelector("td");
        if (!out && th && td && /^(Scope|Geltungsbereich)$/i.test(th.textContent.trim())) out = td.textContent.trim().replace(/^(?:service\s+interface|\S+)\s+/, "");
      });
      return out;
    }
    // Der Name des Elements in seiner eigenen Signatur wird zum Link auf die kanonische Sicht
    function linkOwnNames(box) {
      box.querySelectorAll("article.rec").forEach(function (rec) {
        var pre = rec.querySelector(":scope > pre.syntax"), rn = rec.querySelector(":scope > .recname");
        var sw = rn && rn.querySelector(".sws a");
        if (!pre || !sw || pre.querySelector("a.nsx-fnlink")) return;
        var c = rn.cloneNode(true);
        c.querySelectorAll(".kind, .sws, .ups").forEach(function (x) { x.remove(); });
        var nm = c.textContent.trim().split("::").pop();
        if (!nm) return;
        var re = new RegExp("(^|[^\\w~])(" + nm.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")(\\s*\\()");
        var walker = document.createTreeWalker(pre, NodeFilter.SHOW_TEXT, null);
        for (var tn = walker.nextNode(); tn; tn = walker.nextNode()) {
          if (tn.parentNode.closest("a")) continue;
          var m = re.exec(tn.nodeValue);
          if (!m) continue;
          var after = tn.splitText(m.index + m[1].length);
          after.splitText(m[2].length);
          var a = document.createElement("a");
          a.className = "nsx-fnlink";
          a.href = sw.getAttribute("href");
          a.textContent = m[2];
          after.parentNode.replaceChild(a, after);
          break;
        }
      });
    }
    function recordTitle(name, rec) {
      var rn = rec.querySelector(".recname"), kind = rn && rn.querySelector(".kind");
      var sw = rn && rn.querySelector(".sws a");
      var sc = scopeOf(rec);
      // Clusterseiten: Namenszusatz „ (Teil)“ gleichnamiger Einträge gehört nicht zum Namen
      var pt = rows[name] && rows[name].getAttribute("data-part"), sfx = pt ? " (" + pt + ")" : "";
      if (sfx && name.slice(-sfx.length) === sfx) name = name.slice(0, -sfx.length);
      return { kind: kind ? kind.textContent : "", qname: sc ? sc + "::" + name : name,
               href: sw ? sw.getAttribute("href") : "", sws: swsHtml(rn) };
    }

    // KI-Text des Elements (User Guide der Klasse, KI-Kommentar eines Records): als Reiter
    // in der Titelzeile der Detailansicht angedockt; klappt bündig darunter auf.
    var dTab = null, dPanel = null;
    function dockDetailAi(src, label, statsRoot) {
      dPanel = document.createElement("div");
      dPanel.className = "nsx-detpanel";
      dPanel.hidden = true;
      if (src.tagName === "DETAILS") {
        Array.prototype.slice.call(src.children, 1).forEach(function (c) { dPanel.appendChild(c); });
        src.remove();
      } else {
        var ph = document.createComment("nsx");
        src.parentNode.insertBefore(ph, src);
        dPanel.appendChild(src);
        moved.push({ el: src, ph: ph });
      }
      detBody.insertBefore(dPanel, detBody.firstChild);
      dTab = document.createElement("button");
      dTab.type = "button";
      dTab.className = "nsx-tab nsx-dtab";
      dTab.setAttribute("aria-expanded", "false");
      // Einzeiler des Guides (fold.js, Ausführlichkeitsstufen) auch im eingeklappten Reiter
      var one = window.autodocsGuideLevels ? window.autodocsGuideLevels.oneliner(statsRoot || dPanel) : "";
      dTab.innerHTML = '<span class="nsx-tab-h">' + label + '</span>'
        + (one ? '<span class="ai-oneliner" title="' + esc(one) + '">' + esc(one) + "</span>" : "")
        + '<span class="nsx-stats">' + statsHtml(statsRoot || dPanel) + "</span>";
      detTitle.parentNode.insertBefore(dTab, detTitle.nextSibling);
    }
    function clearDetailAi() {
      if (dTab) dTab.remove();
      dTab = dPanel = null;
      detFold.classList.remove("nsx-dp-open");
      markAi();
    }
    function aiOpen() { return !!(dTab && dTab.getAttribute("aria-expanded") === "true"); }
    // Zustand der Sterne: gedrückt beim ausgewählten Eintrag mit offenem KI-Text
    // Ein Symbol je gezeigter Stufe (lib_nsindex._ai_icons): gedrückt ist das der sichtbaren Stufe
    function markAi() {
      var open = aiOpen(), lv = open ? detailAiLevel() : 0;
      root.querySelectorAll(".nsx-ai").forEach(function (s) {
        var mine = !!selected && s.getAttribute("data-ai") === selected && open;
        var sl = parseInt(s.getAttribute("data-lv"), 10) || 0;
        s.setAttribute("aria-pressed", String(mine && (!sl || sl === lv)));
      });
    }
    function detailGuides() {
      return dPanel ? Array.prototype.filter.call(dPanel.querySelectorAll(".ai[data-ai-levels]"), function (a) {
        var v = a.closest(".ai-guide-release-variant");
        return !v || v.style.display !== "none";
      }) : [];
    }
    function detailAiLevel() {
      var a = detailGuides()[0];
      return a ? parseInt(a.getAttribute("data-ai-level-cur"), 10) || 4 : 4;
    }
    function setDetailAiLevel(lv) {
      if (!lv) return;
      detailGuides().forEach(function (a) { if (window.autodocsGuideLevels) window.autodocsGuideLevels.set(a, lv, false); });
      markAi();
    }
    function setDetailAi(open) {
      if (!dTab || !dPanel) return;
      if (selected && selAnchor) writeHash(selAnchor, open);
      dPanel.hidden = !open;
      dTab.setAttribute("aria-expanded", String(open));
      detFold.classList.toggle("nsx-dp-open", open);
      markAi();
      if (open) {
        var t = dTab.getBoundingClientRect(), pr = dPanel.getBoundingClientRect();
        var rtl = getComputedStyle(root).direction === "rtl";
        dPanel.style.setProperty("--nsx-tabx", (rtl ? pr.right - t.right : t.left - pr.left) + "px");
        dPanel.style.setProperty("--nsx-tabw", t.width + "px");
      }
    }
    function showCanonical(name, opts) {
      if (!detBody) return;
      var r = rows[name], my = ++token;
      detBody.style.minHeight = detBody.offsetHeight + "px";
      clearHistMarks();              // geliehene Records ohne Markierungen zurückgeben
      restoreMoved();
      clearDetailAi();
      detBody.innerHTML = "";
      setTitle(name, isPageRow(r) ? { href: r.getAttribute("data-href") } : null);
      detFold.hidden = false;
      updateEmpty();
      var isClass = isPageRow(r);
      if (detLink) detLink.hidden = true;
      detFold.open = true;
      var wrap = document.createElement("div");
      wrap.className = "nsx-canon";
      detBody.appendChild(wrap);
      function fallback(msg) {
        var ds = r.querySelector(".nsx-ds");
        if (ds) wrap.appendChild(ds.cloneNode(true));
        if (msg) wrap.insertAdjacentHTML("beforeend", '<p class="nsx-hint">' + esc(msg) + "</p>");
      }
      function finish() {
        var fns = words(r, "data-fns");
        if (fns.length) {
          var sec = document.createElement("section");
          sec.className = "nsx-canon-fns";
          sec.innerHTML = "<h3>" + esc(labels.fns || "") + " <span class=\"nsx-cnt\">" + fns.length + "</span></h3>";
          fns.forEach(function (id) { borrow(id, sec); });
          detBody.appendChild(sec);
        }
        var head = wrap.querySelector(":scope > h1");
        var recs = wrap.querySelectorAll(":scope > article.rec");
        if (head) {
          var hk = head.querySelector(".kind"), hc = head.cloneNode(true);
          if (hc.querySelector(".kind")) hc.querySelector(".kind").remove();
          var meta = head.nextElementSibling;
          setTitle(name, { kind: hk ? hk.textContent : "", qname: hc.textContent.trim(), href: r.getAttribute("data-href"),
                           sws: meta && meta.matches("p.meta") ? swsHtml(meta) : "" });
          var gf = Array.prototype.filter.call(wrap.querySelectorAll(":scope > details.fold"), function (d) { return d.querySelector(".ai"); })[0];
          if (gf) {
            var gh = gf.querySelector("summary h2"), lab = gh ? gh.cloneNode(true) : null;
            if (lab) lab.querySelectorAll("[id]").forEach(function (e) { e.removeAttribute("id"); });
            dockDetailAi(gf, lab ? lab.innerHTML : esc(labels.ai || ""), null);
          }
        } else if (recs.length) {
          var ti = recordTitle(name, recs[0]);
          if (recs.length > 1) ti.sws = "";
          setTitle(name, ti);
          // Mit Guide-Reitern (User Guide / Implementer's Guide) den ganzen Reiterblock andocken,
          // sonst bliebe im Körper ein leerer Reiter zurück; Beschriftung = einziger Reiter bzw. „Guides“.
          var gtabs = wrap.querySelector("article.rec .guide-tabs");
          var gbtn = gtabs ? gtabs.querySelectorAll('[role="tab"]') : [];
          var usage = gtabs || wrap.querySelector("article.rec .ai.usage");
          var ulab = gbtn.length > 1 ? "Guides" : gbtn.length ? esc(gbtn[0].textContent) : esc(labels.ai || "");
          if (usage && usage.textContent.trim()) dockDetailAi(usage, ulab, gtabs ? gtabs.querySelector(".guide-panel") : null);
        }
        linkOwnNames(detBody);
        if (window.autodocsGuideLevels && window.autodocsGuideLevels.inlineMore) window.autodocsGuideLevels.inlineMore(detBody);
        detBody.style.minHeight = "";
        histDetail(name);
      }
      function done() {
        if (my !== token) return;
        if (opts.ai && dPanel) { setDetailAi(true); setDetailAiLevel(opts.level); toDetail(); return; }
        var target = opts.ai ? detBody.querySelector(".ai") : (opts.anchor && inDetail(opts.anchor));
        if (target && detBody.contains(target)) openTo(target);
        else if (opts.ai || opts.anchor) toDetail();
      }
      var need = missingRemote(r);
      if (isClass) {
        wrap.classList.add("nsx-loading");
        Promise.all([classPage(r.getAttribute("data-href")),
                     need.length ? remotePage(r.getAttribute("data-page")).catch(function () { return null; }) : null]).then(function (res) {
          var main = res[0];
          pageCache[r.getAttribute("data-href")] = main;
          if (my !== token) return;
          keepAnchor(function () {
            wrap.classList.remove("nsx-loading");
            var c = main.cloneNode(true);
            while (c.firstChild) wrap.appendChild(c.firstChild);
            finish();
          });
          done();
        }, function () {
          if (my !== token) return;
          keepAnchor(function () {
            wrap.classList.remove("nsx-loading");
            fallback(labels.fail);
            finish();
          });
          done();
        });
      } else if (need.length) {
        // Clusterseiten: Records liegen auf der Seite des Teils
        wrap.classList.add("nsx-loading");
        remotePage(r.getAttribute("data-page")).then(function () {
          if (my !== token) return;
          keepAnchor(function () {
            wrap.classList.remove("nsx-loading");
            words(r, "data-recs").forEach(function (id) { borrow(id, wrap); });
            if (!wrap.children.length) fallback(labels.fail);
            finish();
          });
          done();
        }, function () {
          if (my !== token) return;
          keepAnchor(function () {
            wrap.classList.remove("nsx-loading");
            fallback(labels.fail);
            finish();
          });
          done();
        });
      } else {
        words(r, "data-recs").forEach(function (id) { borrow(id, wrap); });
        if (!wrap.children.length) {
          fallback("");
          // Abgeleitete Einträge ohne eigenen Record (Datentypen, Application Errors eines
          // Service-Interface): die Mitglieder, die sie verwenden
          var users = words(r, "data-in");
          if (users.length) wrap.insertAdjacentHTML("beforeend", '<section class="nsx-canon-fns"><h3>' + esc(labels.in || "")
            + ' <span class="nsx-cnt">' + users.length + "</span></h3><ul>" + relItems(users, name).join("") + "</ul></section>");
        }
        finish();
        return { done: done };
      }
      return { done: done, pending: true };
    }

    // ---- Auswahl
    var selected = null;
    function revealSelected() {
      if (!selected || !outline) return;
      // Eingeklappte Gruppe des ausgewählten Eintrags öffnen (ohne es zu merken)
      (oitems[selected] || []).forEach(function (o) {
        if (!o.hidden) return;
        for (var g = o.previousElementSibling; g; g = g.previousElementSibling) if (g.matches(".nsx-og")) { setOg(g, true, false); break; }
      });
      (oitems[selected] || []).forEach(function (o) {
        if (!o.offsetParent) return;
        var top = o.offsetTop - outline.offsetTop;
        if (top < outline.scrollTop || top > outline.scrollTop + outline.clientHeight - 20) outline.scrollTop = top - outline.clientHeight / 3;
      });
    }
    var selAnchor = "";   // Anker der Auswahl im URL-Hash (Eintrag nsx-e-… oder Record-ID)
    function discussRecordId(name, opts) {
      var row = rows[name];
      if (!row) return "";
      if (opts && opts.anchor && recOwner[opts.anchor] === name) return opts.anchor;
      return words(row, "data-recs")[0] || words(row, "data-fns")[0] || "";
    }
    // opts.origin: "map" (Themenkarte), "side" (Gliederung, Inspektor), "nav" (Anker von außen)
    // opts.from: angeklicktes Element; opts.ai / opts.anchor: Sprungziel in der Detailansicht
    function select(name, opts) {
      if (!rows[name]) return;
      opts = opts || {};
      if (histPick && histPick.name !== name) {   // angeklickte Zelle gilt nur für ihr Element
        histPick = null;
        root.querySelectorAll(".nsx-hc.sel").forEach(function (x) { x.classList.remove("sel"); });
        updateHistArrows();
      }
      if (opts.from && popFold && popFold !== root && popFold.contains(opts.from)) setPop(null);   // Auswahl im Panel schließt es
      // Angedockte, eingeklappte Elemente: die Auswahl öffnet ihr Panel, damit die Detailansicht sichtbar ist
      if (root.classList.contains("nsx-tdocked") && !elementsOpen()) setElementsOpen(true);
      var origin = opts.origin || "side", was = detailVisible();
      var jump = !!(opts.ai || opts.anchor);
      var go = !jump && (origin === "nav" || !was || (origin !== "map" && headerAbove()));
      anchorEl = opts.from && folds.contains(opts.from) ? opts.from : firstVisibleFold();
      if (anchorEl === detFold) anchorEl = null;
      selected = name;
      selAnchor = opts.anchor && recOwner[opts.anchor] === name ? opts.anchor : (rows[name].id || "");
      var discussId = discussRecordId(name, opts);
      if (discussId) root.setAttribute("data-discuss-record-id", discussId);
      else root.removeAttribute("data-discuss-record-id");
      writeHash(selAnchor, !!opts.ai);
      root.querySelectorAll(".nsx-oi.sel, .nsx-chip.pin").forEach(function (x) { x.classList.remove("sel", "pin"); x.removeAttribute("aria-current"); });
      (oitems[name] || []).forEach(function (o) { o.classList.add("sel"); o.setAttribute("aria-current", "true"); });
      if (chips[name]) chips[name].classList.add("pin");
      revealSelected();
      highlight(name);
      showRelations(name);
      var res;
      keepAnchor(function () { res = showCanonical(name, opts); });
      if (go || jump) anchorEl = detFold;
      if (go) toDetail();
      if (jump && res && !res.pending) res.done();
    }
    function deselect() {
      if (!detFold || detFold.hidden) return;
      ++token;
      function hide() {
        restoreMoved();
        detBody.innerHTML = "";
        detFold.hidden = true;
        updateEmpty();
        selected = null;
        selAnchor = "";
        root.removeAttribute("data-discuss-record-id");
        histPick = null;
        root.querySelectorAll(".nsx-hc.sel").forEach(function (x) { x.classList.remove("sel"); });
        updateHistArrows();
        writeHash("", false);
        root.querySelectorAll(".nsx-oi.sel, .nsx-chip.pin").forEach(function (x) { x.classList.remove("sel", "pin"); x.removeAttribute("aria-current"); });
        unhighlight();
        if (relBox) { relBox.hidden = true; relBox.removeAttribute("data-owner"); }
        if (hint) hint.hidden = false;
        markAi();
      }
      var fv = firstVisibleFold();
      if (fv === detFold) {
        // Was unter der Detailansicht folgt, rückt an ihre Stelle
        var y = Math.max(detFold.getBoundingClientRect().top, pinH()), fl = foldList().filter(docked), nx = fl[fl.indexOf(detFold) + 1];
        hide();
        if (nx) window.scrollBy(0, nx.getBoundingClientRect().top - y);
      } else {
        anchorEl = fv;
        keepAnchor(hide);
      }
    }

    // ---- Ereignisse
    function nameFrom(target) {
      var el = target.closest && target.closest(".nsx-chip, .nsx-oi");
      return el ? el.getAttribute("data-n") : null;
    }
    var last = null;
    root.addEventListener("mouseover", function (ev) {
      var n = nameFrom(ev.target);
      if (!n || n === last) return;
      last = n;
      highlight(n);
      if (!selected) showRelations(n);
    });
    [outline, map].forEach(function (zone) {
      if (zone) zone.addEventListener("mouseleave", function () { last = null; restore(); });
    });
    root.addEventListener("click", function (ev) {
      var t = ev.target;
      var ai = t.closest(".nsx-ai");
      if (ai) {
        // Stern: öffnet den KI-Text des Eintrags; beim ausgewählten Eintrag schaltet er ihn um
        ev.preventDefault();
        // Symbol einer Stufe: öffnet den Guide genau in dieser Stufe; dasselbe Symbol bei offenem
        // Guide in dieser Stufe schließt ihn wieder, ein anderes wechselt die Stufe
        var an = ai.getAttribute("data-ai"), alv = parseInt(ai.getAttribute("data-lv"), 10) || 0;
        if (an === selected && dTab) {
          var op = !(aiOpen() && (!alv || detailAiLevel() === alv));
          setDetailAi(op);
          if (op) { setDetailAiLevel(alv); toDetail(); }
        } else select(an, { ai: true, level: alv });
        return;
      }
      var dt = t.closest(".nsx-dtab");
      if (dt) {
        ev.preventDefault();
        var willOpen = dt.getAttribute("aria-expanded") !== "true";
        setDetailAi(willOpen);
        if (willOpen && headerAbove()) toDetail();
        return;
      }
      var hb = t.closest(".nsx-hbtn");
      if (hb) {
        ev.preventDefault();
        var hf = hb.closest("details");
        if (hb.classList.contains("nsx-closebtn")) deselect();
        else if (hb.classList.contains("nsx-backbtn")) {
          if (hf && hf.classList.contains("nsx-topdocked")) undockTop(hf);
          else undockTitle(hf, folds.firstChild);
        }
        return;
      }
      var by = t.closest(".nsx-by button");
      if (by) { if (setBy(by.getAttribute("data-by"))) save(BY_KEY, by.getAttribute("data-by")); return; }
      var a = t.closest("a.nsx-chip, a.nsx-oi, a[data-jump], g[data-jump]");
      if (a) {
        var n = a.getAttribute("data-n") || a.getAttribute("data-jump");
        if (!rows[n]) return;
        ev.preventDefault();
        // Klick auf den Namen des ausgewählten Eintrags schließt einen offenen KI-Text
        // wieder (Aufnahme 12:01), sonst springt er zur Detailansicht; im Historie-Modus
        // löst ein Klick auf den Eintragsnamen (außerhalb der Zellen) auch eine Zellenauswahl
        if (n === selected) {
          if (histPick && histPick.name === n) {
            histPick = null;
            root.querySelectorAll(".nsx-hc.sel").forEach(function (x) { x.classList.remove("sel"); });
            updateHistArrows();
            showRelations(n);
            histDetail(n);
          } else if (aiOpen()) setDetailAi(false);
          else toDetail();
        } else select(n, { origin: a.classList.contains("nsx-chip") ? "map" : "side", from: a });
        return;
      }
      // Sprünge auf dieser Seite: reine Anker (#…) und Verweise mit Seitenpfad, etwa
      // die internen Links der KI-Diagramme (SVG-<a>, lib_diaglinks)
      var link = t.closest("a[href]");
      if (!link) return;
      var url;
      try { url = new URL(link.getAttribute("href"), location.href); } catch (e) { return; }
      if (!url.hash || url.origin !== location.origin || url.pathname !== location.pathname) return;
      var id = decodeURIComponent(url.hash.slice(1));
      if (id === "class-decl" && title) {
        // Verweis auf die Klasse selbst: sie steht in der Titelleiste; nicht nach oben springen
        ev.preventDefault();
        title.classList.remove("nsx-flash");
        void title.offsetWidth;
        title.classList.add("nsx-flash");
        return;
      }
      if (id.indexOf("nsx-c-") === 0) {
        var local = detBody && detBody.querySelector("#" + CSS.escape(id));
        var owner = link.closest("[data-owner]");
        if (local) { ev.preventDefault(); openTo(local); }
        else if (owner) { ev.preventDefault(); select(owner.getAttribute("data-owner"), { anchor: id }); }
        return;
      }
      if (id.indexOf("nsx-e-") === 0) {
        var row = document.getElementById(id);
        if (row && rows[row.getAttribute("data-n")]) {
          ev.preventDefault();
          if (link.classList.contains("nsx-detname") && row.getAttribute("data-n") === selected) toDetail();
          else select(row.getAttribute("data-n"), { from: link });
        }
        return;
      }
      if (recOwner[id]) {
        ev.preventDefault();
        if (popFold && popFold.contains(link)) setPop(null);   // Sprung aus dem Panel schließt es
        if (selected === recOwner[id] && inDetail(id)) openTo(inDetail(id));
        else select(recOwner[id], { anchor: id });
      }
    });
    root.addEventListener("keydown", function (ev) {
      if ((ev.key === "Enter" || ev.key === " ") && ev.target.matches(".nsx-ai, g[data-jump]")) {
        ev.preventDefault();
        ev.stopPropagation();
        ev.target.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
      }
    });
    root.querySelectorAll(".nsx-ai").forEach(function (s) {
      var l = labels["ailv" + (s.getAttribute("data-lv") || "")] || labels.ai || "";
      s.setAttribute("title", l);
      s.setAttribute("aria-label", l);
    });
    root.querySelectorAll(".nsx-rv").forEach(function (s) { s.setAttribute("title", labels.rv || ""); s.setAttribute("role", "img"); s.setAttribute("aria-label", labels.rv || ""); });

    // ---- Review-Bedarf: Die Hinweisleiste der Seite verweist auf die Review-Panels der Records
    // (#review-<ID>). Kompakt liegen die Records in der Detailansicht: Ein Klick wählt den
    // Eintrag und öffnet dort das Panel; „In der Gliederung zeigen“ schaltet auf die
    // Gliederung „Review-Bedarf“.
    function reviewTarget(href) {
      var m = /^#review-(.+)$/.exec(href || "");
      var id = m && decodeURIComponent(m[1]);
      return id && recOwner[id] ? { name: recOwner[id], anchor: "review-" + id } : null;
    }
    document.querySelectorAll(".page-review-notice").forEach(function (notice) {
      var links = notice.querySelector(".page-review-links");
      if (links && outline && outline.querySelector('.nsx-by button[data-by="review"]') && !notice.querySelector(".nsx-rvshow")) {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "nsx-rvshow";
        b.textContent = labels.rvshow || "";
        links.appendChild(b);
      }
      notice.addEventListener("click", function (ev) {
        if (ev.target.closest(".nsx-rvshow")) {
          ev.preventDefault();
          if (setBy("review")) save(BY_KEY, "review");
          outline.scrollIntoView({ block: "nearest", behavior: behavior });
          return;
        }
        var a = ev.target.closest("a.page-review-link"), tg = a && reviewTarget(a.getAttribute("href"));
        if (!tg) return;
        ev.preventDefault();
        if (selected === tg.name && inDetail(tg.anchor)) openTo(inDetail(tg.anchor));
        else select(tg.name, { anchor: tg.anchor, from: a });
      });
    });
    if (map) {
      var mapFold = map.closest("details");
      if (mapFold) mapFold.addEventListener("toggle", restore);
    }
    // Überfahren im Inspektor hebt den Eintrag in Karte und Gliederung hervor
    var peeked = null;
    function peek(n) {
      if (peeked === n) return;
      [peeked, n].forEach(function (x, i) {
        if (!x) return;
        [chips[x]].concat(oitems[x] || []).forEach(function (el) { if (el) el.classList.toggle("peek", i === 1); });
      });
      peeked = n;
    }
    if (aside) {
      aside.addEventListener("mouseover", function (ev) {
        var e = ev.target.closest && ev.target.closest("[data-jump], a[data-n]");
        peek(e ? e.getAttribute("data-jump") || e.getAttribute("data-n") : null);
      });
      aside.addEventListener("mouseleave", function () { peek(null); });
    }
    // Doppelklick auf ein Element im Inspektor öffnet seine Ansicht (Wunsch des Admins vom
    // 2026-10-13): Einträge dieser Seite wie die Auswahl in der Gliederung, der Kopf des
    // Inspektors die eigene Kompaktansicht (auf Clusterseiten die Seite des Teils). Namen ohne
    // Verweis (Listen, Signaturen) zählen, wenn sie ein Eintrag dieser Seite sind. Verweise auf
    // andere Seiten führen schon beim einfachen Klick dorthin (Record-Anker wählen dort aus).
    // Der erste Klick wählt wie bisher aus und baut den Inspektor neu; gemerkt wird, worauf er fiel
    var insPick = null;
    if (relBox) relBox.addEventListener("click", function (ev) {
      // Zweiter Klick eines Doppelklicks: fällt auf den neu aufgebauten Inspektor und darf dort
      // nichts anderes auswählen; der Doppelklick gilt dem zuerst getroffenen Element
      if (ev.detail >= 2 && insPick && Date.now() - insPick.at < 800) { ev.preventDefault(); ev.stopPropagation(); return; }
      var j = ev.target.closest && ev.target.closest("[data-jump], a[data-n]");
      insPick = j ? { n: j.getAttribute("data-jump") || j.getAttribute("data-n"), own: !!j.closest(".nsx-rel > .t"), at: Date.now() } : null;
    }, true);
    if (relBox) relBox.addEventListener("dblclick", function (ev) {
      var t = ev.target;
      if (!t || !t.closest) return;
      var fresh = insPick && Date.now() - insPick.at < 800 ? insPick : null;
      var j = fresh ? null : t.closest("[data-jump], a[data-n]");
      var n = fresh ? fresh.n : j ? (j.getAttribute("data-jump") || j.getAttribute("data-n")) : "";
      var own = fresh ? fresh.own : !!(j && j.closest(".nsx-rel > .t"));
      if (!fresh && !j) {
        var w = window.getSelection ? String(getSelection()).trim() : "";
        n = /^[A-Za-z_~][\w~]*$/.test(w) ? w : "";
      }
      if (!n || !rows[n]) return;
      ev.preventDefault();
      clearSelection();
      var href = ownHref(n);
      if (own && href && href.charAt(0) !== "#") {
        location.assign(new URL(href, location.href).href);   // anderes Verzeichnis: vollständig laden
        return;
      }
      if (n === selected) toDetail();
      else select(n, { origin: "nav" });
    });
    if (detFold) {
      addButton(detFold, "nsx-closebtn", ICON_CLOSE, labels.close);
      detFold.hidden = true;
    }
    updateEmpty();
    // Beim Öffnen: gemerktes Layout der Seitenart, sonst die Vorgabe (Guide gelöst in der Kurzfassung)
    applyAllDocks();

    // Klick auf eine leere Fläche löst die Auswahl; der Inspektor folgt dann wieder
    // dem Mauszeiger. Lesebereiche (Detailansicht, Guide-Text, Inspektor) und
    // Bedienelemente zählen nicht als leer.
    function release() {
      if (!selected && !histPick) return;
      selected = null;
      histPick = null;
      root.querySelectorAll(".nsx-hc.sel").forEach(function (x) { x.classList.remove("sel"); });
      updateHistArrows();
      markAi();
      root.querySelectorAll(".nsx-oi.sel, .nsx-chip.pin").forEach(function (x) { x.classList.remove("sel", "pin"); x.removeAttribute("aria-current"); });
      unhighlight();
      last = null;
      if (relBox) { relBox.hidden = true; relBox.removeAttribute("data-owner"); }
      if (hint) hint.hidden = false;
    }
    document.addEventListener("click", function (ev) {
      var t = ev.target;
      if (ev.button !== 0 || !t.closest || !root.contains(t) && !(title && title.contains(t))) return;
      if (t.closest("a, button, summary, input, select, textarea, label, [role=button], [tabindex], [data-jump], .nsx-chip, .nsx-oi, " +
        ".nsx-detbody, .nsx-rel, details[data-fold=guide] > :not(summary), details[data-fold^=\"guide-\"] > :not(summary), .nsx-tdock, .nsx-og")) return;
      if (window.getSelection && String(getSelection())) return;
      release();
    });

    // ---- Historie: je Eintrag die letzte Änderung bis zum gewählten Release (links) und die
    // nächste danach (rechts). Klick wählt das Release, Überfahren hebt alle Einträge hervor,
    // die in diesem Release geändert wurden.
    var allRels = {};
    root.querySelectorAll("[data-changes]").forEach(function (el) { words(el, "data-changes").forEach(function (r) { allRels[r] = 1; }); });
    function relKey(r) {
      var m = /^R(\d+)-(\d+)/.exec(r || "");
      return m ? +m[1] * 100 + +m[2] : 0;
    }
    function latestRel() { return Object.keys(allRels).sort(function (a, b) { return relKey(a) - relKey(b); }).pop() || ""; }
    // ---- Historie (Gruppierung „Historie“), Wunsch des Admins vom 2026-10-13:
    // - Gliederung: Tabelle Release × Element statt KI-Symbol und Release-Kästchen; eine Zelle
    //   je Release, markiert, wenn das Element darin vorkommt (neu, geändert, unverändert, entfallen).
    // - Inspektor: Unterschiede des ausgewählten Elements zwischen zwei Releases (gewähltes Release
    //   und Vorgänger oder zwei Zellen der Tabelle), nach Angaben der Spezifikationstabelle zerlegt.
    // - Mitte: die gewohnte Darstellung, nur die Unterschiede farbig markiert.
    var HL = (document.documentElement.getAttribute("lang") || "de").slice(0, 2) === "de" ? {
      add: "neu", chg: "geändert", pre: "unverändert", del: "entfallen", none: "nicht enthalten",
      changes: "Änderungen", same: "Keine inhaltliche Änderung", first: "Erstmals in", gone: "Entfallen in",
      nodata: "Keine Versionsdaten verfügbar.", loading: "Versionsdaten werden geladen …", text: "Text",
      notext: "Wortlaut in diesem Release nicht erfasst", pick: "Zelle zeigen oder anklicken: gegen das gewählte Release vergleichen · Release-Kopf anklicken: Release wählen",
      selrel: "Release wählen", props: "Angaben", rel: "Release", elem: "Element", onlyone: "Nur ein Release mit Wortlaut",
      pdf: "im PDF vorhanden, Wortlaut noch nicht übernommen", cap: "Wortlaut erstmals erfasst",
      since: "unverändert seit {rel}", colors: "Release-Farben",
      oldest: "ältestes Release", newest: "neuestes Release"
    } : {
      add: "added", chg: "changed", pre: "unchanged", del: "removed", none: "not included",
      changes: "Changes", same: "No change in content", first: "First in", gone: "Removed in",
      nodata: "No version data available.", loading: "Loading version data …", text: "Text",
      notext: "Wording not captured for this release", pick: "Hover or click a cell: compare with the selected release · Click a release header: select the release",
      selrel: "Select release", props: "Properties", rel: "Release", elem: "Element", onlyone: "Only one release with wording",
      pdf: "present in PDF, wording not yet imported", cap: "Wording captured for the first time",
      since: "unchanged since {rel}", colors: "Release colors",
      oldest: "oldest release", newest: "newest release"
    };
    // Beschriftungen der Seite (übersetzt über _src/i18n/ui.json, Gruppe „kind“) haben Vorrang;
    // die Tabellen oben sind nur der Rückfall für Seiten ohne diese Beschriftungen
    Object.keys(HL).forEach(function (k) { if (labels["h" + k]) HL[k] = labels["h" + k]; });
    // Chronologische Gesamtreihenfolge aller im Repository belegten Releases. Die R-Bezeichner
    // tragen Jahr und Monat; die Änderungshistorien der Classic-Dossiers belegen 4.0.1 am 2009-12-18,
    // 4.1.1 am 2013-03-15, 4.2.1 am 2014-10-31, 4.3.0 am 2016-11-30 und 4.4.0 am 2018-10-31.
    // 4.4 und R18-10 fallen in denselben Monat (Store-Alias: derselbe Stand); 4.4 steht davor.
    // Für S-Core v0.6.0 enthält das Repository kein Publikationsdatum; es steht nach R25-11. Einziger
    // Datumshinweis ist der Commit-Zeitstempel des Tag-Archivs (2026-06-24), kein Publikationsdatum.
    var REPOSITORY_RELEASE_ORDER = [
      "4.0", "4.1", "4.2", "4.3", "R17-03", "R17-10", "R18-03", "4.4", "R18-10",
      "R19-03", "R19-11", "R20-11", "R21-11", "R22-11", "R23-11", "R24-11", "R25-11",
      "v0.6.0"
    ];
    var repositoryReleaseRank = {};
    REPOSITORY_RELEASE_ORDER.forEach(function (rel, i) { repositoryReleaseRank[rel] = i; });
    function histKey(r) {
      if (Object.prototype.hasOwnProperty.call(repositoryReleaseRank, r)) return repositoryReleaseRank[r];
      var m = /^R(\d+)-(\d+)/.exec(r || "");
      if (m) return 1000 + +m[1] * 100 + +m[2];
      m = /^(\d+)\.(\d+)/.exec(r || "");
      if (m) return 2000 + +m[1] * 10 + +m[2];
      m = /^v(\d+)\.(\d+)(?:\.(\d+))?/.exec(r || "");
      return m ? 3000 + +m[1] * 10000 + +m[2] * 100 + +(m[3] || 0) : 4000;
    }
    function bySort(a, b) { return histKey(a) - histKey(b) || (a < b ? -1 : a > b ? 1 : 0); }

    // Wellenlängen-zu-sRGB-Näherung nach den Farbwinkel-Stützstellen von Brutons Spektralfunktion
    // (580 nm Gelb, 510 nm Grün, 490 nm Cyan, 440 nm Blau, 400 nm Violett). Brutons flaches Rotband
    // 645…700 nm entfällt: der Farbwinkel fällt bis 700 nm stetig auf 0° (Tiefrot), dazwischen wird
    // er stückweise linear interpoliert. Die Spektralfarben liegen außerhalb des sRGB-Gamuts; statt
    // abgeschnittener Kanäle bleibt die Sättigung konstant, und ein Helligkeitsbogen dunkelt beide
    // Enden ab (geringere Hellempfindlichkeit an den Spektralrändern). Weil der Farbwinkel streng
    // monoton ist, bleiben Nachbarränge verschieden.
    function wavelengthRgb(wavelength) {
      var SPECTRAL_HUE_STOPS = [[700, 0], [580, 60], [510, 120], [490, 180], [440, 240], [400, 275]];
      var w = Math.max(400, Math.min(700, wavelength)), h = 275, t = (700 - w) / 300;
      for (var k = 1; k < SPECTRAL_HUE_STOPS.length; k += 1) {
        var hi = SPECTRAL_HUE_STOPS[k - 1], lo = SPECTRAL_HUE_STOPS[k];
        if (w >= lo[0]) { h = hi[1] + (lo[1] - hi[1]) * (hi[0] - w) / (hi[0] - lo[0]); break; }
      }
      var s = 0.82, v = 0.58 + 0.18 * Math.sin(Math.PI * t) + 0.08 * t;
      var c = v * s, hp = h / 60, x = c * (1 - Math.abs(hp % 2 - 1));
      var rgb = hp < 1 ? [c, x, 0] : hp < 2 ? [x, c, 0] : hp < 3 ? [0, c, x] :
        hp < 4 ? [0, x, c] : hp < 5 ? [x, 0, c] : [c, 0, x];
      var m = v - c;
      return rgb.map(function (channel) { return Math.round(255 * (channel + m)); });
    }
    function rgbCss(rgb) { return "rgb(" + rgb.join(", ") + ")"; }
    function lighten(rgb, amount) {
      return rgb.map(function (x) { return Math.round(x + (255 - x) * amount); });
    }
    function repositoryReleases() {
      var seen = {}, rels = [], cfg = window.__autodocsRelease && window.__autodocsRelease.u;
      REPOSITORY_RELEASE_ORDER.forEach(function (rel) { seen[rel] = 1; rels.push(rel); });
      if (cfg) Object.keys(cfg).forEach(function (uid) {
        ((cfg[uid] && cfg[uid].r) || []).forEach(function (rel) {
          if (!seen[rel]) { seen[rel] = 1; rels.push(rel); }
        });
      });
      histColumns().forEach(function (rel) { if (!seen[rel]) { seen[rel] = 1; rels.push(rel); } });
      return rels.sort(bySort);
    }
    var releaseRainbow = null;
    function installReleaseRainbow() {
      if (releaseRainbow) return releaseRainbow;
      var rels = repositoryReleases(), index = {};
      rels.forEach(function (rel, i) {
        index[rel] = i;
        var wavelength = rels.length < 2 ? 550 : 700 - 300 * i / (rels.length - 1);
        var rgb = wavelengthRgb(wavelength);
        root.style.setProperty("--nsx-rel-" + i, rgbCss(rgb));
        root.style.setProperty("--nsx-rel-" + i + "-dark", rgbCss(lighten(rgb, 0.18)));
      });
      root.dataset.nsxReleaseOrder = JSON.stringify(rels);
      var stops = rels.map(function (_, i) { return "var(--nsx-rel-" + i + ")"; });
      var darkStops = rels.map(function (_, i) { return "var(--nsx-rel-" + i + "-dark)"; });
      root.style.setProperty("--nsx-rainbow-gradient", "linear-gradient(to right," + stops.join(",") + ")");
      root.style.setProperty("--nsx-rainbow-gradient-dark", "linear-gradient(to right," + darkStops.join(",") + ")");
      releaseRainbow = { rels: rels, index: index };
      return releaseRainbow;
    }
    function entryRels(r) {
      var all = words(r, "data-releases").concat(words(r, "data-changes"), words(r, "data-dropped"), words(r, "data-present"));
      return all.filter(function (x, i) { return all.indexOf(x) === i; }).sort(bySort);
    }
    function spanStartIndexes(states) {
      var starts = [], start = -1;
      states.forEach(function (state, i) {
        if (state === "add" || state === "chg" || state === "cap") start = i;
        else if (state !== "pre") start = -1;
        starts[i] = start;
      });
      return starts;
    }
    // Zustand einer Zelle: add (erstes Auftreten), chg (geändert), pre (unverändert enthalten), del (entfallen),
    // pdf (im PDF vorhanden, Wortlaut noch nicht übernommen: kein Vergleich, nie „unverändert“/„geändert“),
    // cap (erste Fassung mit Wortlaut nach Präsenz-Zellen: nicht „neu“, nicht „geändert“), "" (nicht enthalten)
    function cellState(r, rel) {
      if (words(r, "data-dropped").indexOf(rel) >= 0) return "del";
      var have = words(r, "data-releases").concat(words(r, "data-changes")).sort(bySort);
      var pres = words(r, "data-present");
      if (have.indexOf(rel) < 0) return pres.indexOf(rel) >= 0 ? "pdf" : "";
      if (rel === have[0]) return pres.some(function (x) { return histKey(x) < histKey(rel); }) ? "cap" : "add";
      return words(r, "data-changes").indexOf(rel) >= 0 ? "chg" : "pre";
    }
    var histCols = [];
    function histColumns() {
      var seen = {};
      Object.keys(rows).forEach(function (n) { entryRels(rows[n]).forEach(function (x) { seen[x] = 1; }); });
      return Object.keys(seen).sort(bySort);
    }
    function shortRel(x) { return String(x).replace(/^R/, ""); }
    function historyLegend(rainbow) {
      if (!rainbow.rels.length) return "";
      var oldest = rainbow.rels[0], newest = rainbow.rels[rainbow.rels.length - 1];
      var scaleLabel = HL.colors + ": " + HL.oldest + " " + oldest + ", " + HL.newest + " " + newest;
      return '<span class="nsx-hlegend" role="img" data-oldest="' + esc(oldest) + '" data-newest="' + esc(newest) +
        '" aria-label="' + esc(scaleLabel) + '"><span class="nsx-hlegend-states">' +
        '<span><i class="nsx-hlegend-swatch nsx-hc-add span-start" aria-hidden="true"></i>' + esc(HL.add) + '</span>' +
        '<span><i class="nsx-hlegend-swatch nsx-hc-chg span-start" aria-hidden="true"></i>' + esc(HL.chg) + '</span>' +
        '<span><i class="nsx-hlegend-swatch nsx-hc-cap span-start" aria-hidden="true"></i>' + esc(HL.cap) + '</span></span>' +
        '<span class="nsx-hscale" title="' + esc(scaleLabel) + '"><span>' + esc(oldest) +
        '</span><i class="nsx-hscale-bar" aria-hidden="true"></i><span>' + esc(newest) + '</span></span></span>';
    }
    function renderHistory() {
      var cur = currentRelease() || latestRel();
      histCols = histColumns();
      var rainbow = installReleaseRainbow();
      var ol = root.querySelector('.nsx-ol[data-by="since"]');
      if (ol) {
        var head = ol.querySelector(":scope > .nsx-hhead");
        if (!head) {
          head = document.createElement("div");
          head.className = "nsx-hhead";
          ol.insertBefore(head, ol.firstChild);
        }
        head.innerHTML = '<span class="nsx-hhead-n"><span class="nsx-hhead-title">' + esc(HL.elem) + '</span>' + historyLegend(rainbow) + '</span><span class="nsx-hcells">' + histCols.map(function (c) {
          return '<span class="nsx-hcol' + (c === cur ? " cur" : "") + '" role="button" tabindex="0" aria-pressed="' + (c === cur) + '" data-rel="' + esc(c) +
            '" title="' + esc(HL.selrel + ": " + c) + '" aria-label="' + esc(HL.selrel + ": " + c) + '">' + esc(shortRel(c)) + "</span>";
        }).join("") + "</span>";
        ol.style.setProperty("--nsx-hcols", histCols.length);
      }
      root.querySelectorAll("a.nsx-oi-h").forEach(function (a) {
        a.querySelectorAll(".nsx-hb, .nsx-hcells").forEach(function (x) { x.remove(); });
        var n = a.getAttribute("data-n"), r = rows[n];
        if (!r) return;
        var stts = histCols.map(function (c) { return cellState(r, c); });
        var spanStarts = spanStartIndexes(stts);
        var html = histCols.map(function (c, i) {
          var stt = stts[i];
          var start = spanStarts[i], inSpan = start >= 0;
          var prevSpan = inSpan && i > 0 && spanStarts[i - 1] === start;
          var nextSpan = inSpan && i + 1 < stts.length && spanStarts[i + 1] === start;
          var run = inSpan && (prevSpan || nextSpan) ? (prevSpan && nextSpan ? " run-m span-m" : prevSpan ? " run-e span-e" : " run-s span-s") : (inSpan ? " span-one" : "");
          var spanRel = inSpan ? histCols[start] : "", rank = rainbow.index[spanRel];
          var spanAttrs = inSpan ? ' data-span-start="' + esc(spanRel) + '" data-release-rank="' + rank + '"' +
            ' style="--nsx-span-color:var(--nsx-rel-' + rank + ');--nsx-span-color-dark:var(--nsx-rel-' + rank + '-dark)"' : "";
          var spanClass = inSpan ? " nsx-hc-span" + (i === start ? " span-start" : "") : "";
          var curCls = c === cur ? " cur" + (!stt || stt === "del" ? " cur-abs" : "") : "";
          var picked = histPick && histPick.name === n && histPick.rel === c && c !== cur;
          var since = String(HL.since || "").replace("{rel}", spanRel);
          var label = c + " · " + (stt ? HL[stt] : HL.none) + (inSpan ? " · " + since : "");
          return '<span class="nsx-hc' + (stt ? " nsx-hc-" + stt : "") + spanClass + run + curCls + (picked ? " sel" : "") + '" role="button" tabindex="-1" data-rel="' + esc(c) + '"' + spanAttrs +
            ' title="' + esc(label) + '" aria-label="' + esc(label) + '"></span>';
        }).join("");
        a.insertAdjacentHTML("beforeend", '<span class="nsx-hcells">' + html + "</span>");
      });
      root.querySelectorAll('.nsx-ol[data-by="since"] .nsx-og').forEach(function (g) {
        var t = g.textContent.trim();
        if (relKey(t)) { g.setAttribute("data-rel", t); g.classList.add("nsx-hg"); g.classList.toggle("cur", t === cur); }
      });
      updateHistArrows();
    }

    // Vergleichspaar je Element {name, from, to} folgt aus der Auswahl in der Gliederung:
    // Ohne angeklickte/überfahrene Zelle oder bei der Zelle des gewählten Releases (cur) gibt es
    // keinen Vergleich (from: null, to: cur); sonst das Paar aus Zelle und gewähltem Release (älter → neuer).
    var histPick = null, hoverPair = null;
    function selRel() { return currentRelease() || latestRel(); }
    function pairWith(name, cell) {
      var s = selRel();
      if (!cell || cell === s || !s) return { name: name, from: null, to: s || null };
      var two = [cell, s].sort(bySort);
      return { name: name, from: two[0], to: two[1] };
    }
    function pairFor(name) {
      if (hoverPair && hoverPair.name === name) return hoverPair;
      return pairWith(name, histPick && histPick.name === name ? histPick.rel : null);
    }
    function samePair(a, b) { return !!a && !!b && a.name === b.name && a.from === b.from && a.to === b.to; }
    function updateHistArrows() {
      root.querySelectorAll(".nsx-harrow").forEach(function (x) { x.remove(); });
      if (!histOn()) return;
      var names = {};
      if (histPick && histPick.name) names[histPick.name] = 1;
      if (hoverPair && hoverPair.name) names[hoverPair.name] = 1;
      var rtl = getComputedStyle(root).direction === "rtl";
      Object.keys(names).forEach(function (name) {
        var pr = pairFor(name);
        if (!pr || !pr.from || !pr.to || pr.from === pr.to) return;
        root.querySelectorAll('.nsx-ol[data-by="since"] a.nsx-oi-h[data-n="' + CSS.escape(name) + '"]').forEach(function (a) {
          var box = a.querySelector(".nsx-hcells");
          if (!box) return;
          var cFrom = box.querySelector('.nsx-hc[data-rel="' + CSS.escape(pr.from) + '"]');
          var cTo = box.querySelector('.nsx-hc[data-rel="' + CSS.escape(pr.to) + '"]');
          if (!cFrom || !cTo) return;
          var x1, x2;
          if (cFrom.offsetWidth > 0 && cTo.offsetWidth > 0) {
            x1 = cFrom.offsetLeft + cFrom.offsetWidth / 2;
            x2 = cTo.offsetLeft + cTo.offsetWidth / 2;
          } else {
            var i1 = histCols.indexOf(pr.from), i2 = histCols.indexOf(pr.to), nCols = histCols.length;
            x1 = (rtl ? nCols - 1 - i1 : i1) * 17 + 7.5;
            x2 = (rtl ? nCols - 1 - i2 : i2) * 17 + 7.5;
          }
          var left = Math.min(x1, x2), w = Math.max(1, Math.abs(x2 - x1)), toRight = x2 >= x1;
          var xs = toRight ? 0 : w, xe = toRight ? w : 0, d = toRight ? 1 : -1;
          var ah = Math.min(3.5, w * 0.35);
          var svg = '<svg class="nsx-harrow" aria-hidden="true" data-from="' + esc(pr.from) + '" data-to="' + esc(pr.to) +
            '" data-dir="' + (toRight ? "ltr" : "rtl") + '" style="left:' + left + "px;width:" + w + 'px" viewBox="0 0 ' + w + ' 6" preserveAspectRatio="none">' +
            '<path d="M' + xs + " 0.5 Q" + (w / 2) + " 5 " + xe + ' 1.5" fill="none" stroke="currentColor" stroke-width="1.25" stroke-linecap="round"/>' +
            '<path d="M' + (xe - d * ah) + " 0.4 L" + xe + " 1.5 L" + (xe - d * ah * 0.75) + ' 4.2" fill="none" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/>' +
            "</svg>";
          box.insertAdjacentHTML("beforeend", svg);
        });
      });
    }
    function histModeChanged(on) {
      root.classList.toggle("nsx-hist", !!on);
      if (typeof placePop === "function") placePop();
      updateHistArrows();
      if (!selected) return;
      showRelations(selected);
      histDetail(selected);
    }
    function histOn() { return root.classList.contains("nsx-hist"); }

    // Versionsdaten (versions/data/<ID>.json) und Wortvergleich (static/text-diff.js), je einmal geladen
    var histData = {}, tdLoad = null;
    function versionsOf(id) {
      if (!histData[id]) {
        var stem = String(id).replace(/[^A-Za-z0-9_.\-]/g, "_");
        histData[id] = fetch(SITE_ROOT + "versions/data/" + encodeURIComponent(stem) + ".json").then(function (res) {
          if (!res.ok) throw new Error("HTTP " + res.status);
          return res.json();
        }).catch(function () { return null; });
      }
      return histData[id];
    }
    function textDiffLib() {
      if (window.TextDiff) return Promise.resolve(window.TextDiff);
      if (!tdLoad) tdLoad = new Promise(function (ok) {
        var sc = document.createElement("script");
        sc.src = SITE_ROOT + "static/text-diff.js";
        sc.onload = function () { ok(window.TextDiff || null); };
        sc.onerror = function () { ok(null); };
        document.head.appendChild(sc);
      });
      return tdLoad;
    }
    // Wortgenauer Vergleich in einer Zeile: entfallene Wörter durchgestrichen, neue hinterlegt
    // (Tokenisierung und Opcodes wie TextDiff.wordDiff)
    function udiff(a, b) {
      var td = window.TextDiff;
      a = a || ""; b = b || "";
      if (!td || !td.opcodes) return (a ? '<del class="ve-word-deleted">' + esc(a) + "</del> " : "") + (b ? '<ins class="ve-word-added">' + esc(b) + "</ins>" : "");
      var re = /[<>\-]|[\wÀ-ɏ]+|[^\s\wÀ-ɏ<>\-]+|\s+/g, A = a.match(re) || [], B = b.match(re) || [], out = "";
      td.opcodes(A, B).forEach(function (op) {
        var sa = A.slice(op[1], op[2]).join(""), sb = B.slice(op[3], op[4]).join("");
        if (op[0] === "equal") { out += esc(sb); return; }
        if (op[0] !== "insert" && sa.trim()) out += '<del class="ve-word-deleted">' + esc(sa) + "</del>";
        if (op[0] !== "delete") out += sb.trim() ? '<ins class="ve-word-added">' + esc(sb) + "</ins>" : esc(sb);
      });
      return out;
    }
    // Wortlaut eines Records in einem Release: letzte erfasste Fassung; null = nicht enthalten,
    // false = enthalten, aber ohne erfassten Wortlaut
    function textIn(d, rel) {
      var st = nsxHistRecordState(d, rel, rel);
      if (st.state === "none") return null;
      if (st.state === "notext") return false;
      return st.a || st.b || "";
    }
    // Spezifikationstabelle in Angaben zerlegen (Classic-Funktionen und -Typen); sonst ein Feld „Text“
    var FIELD_SETS = [
      ["Service Name", "Syntax", "Service ID [hex]", "Sync/Async", "Reentrancy", "Parameters (in)", "Parameters (inout)",
       "Parameters (out)", "Return value", "Description", "Available via"],
      ["Name", "Kind", "Type", "Derived from", "Elements", "Range", "Description", "Variation", "Available via"],
      ["Kind", "Header file", "Forwarding header", "Scope", "Symbol", "Syntax", "Template param", "Parameters (in)",
       "Parameters (out)", "Return value", "Exception Safety", "Thread Safety", "Errors", "Violations", "Description"]
    ];
    function parseFields(text) {
      var t = String(text || "").replace(/\s+/g, " ").trim(), best = null;
      FIELD_SETS.forEach(function (set) {
        var hits = [], pos = 0;
        set.forEach(function (lab) {
          var i = pos;
          while ((i = t.indexOf(lab, i)) >= 0) {
            var before = i === 0 || t.charAt(i - 1) === " ", after = t.charAt(i + lab.length);
            if (before && (after === " " || after === "")) break;
            i += lab.length;
          }
          if (i >= 0) { hits.push({ label: lab, at: i }); pos = i + lab.length; }
        });
        if (hits.length >= 2 && (!best || hits.length > best.length)) best = hits;
      });
      if (!best) return [{ label: HL.text, value: t }];
      var out = [];
      if (best[0].at > 0) out.push({ label: HL.text, value: t.slice(0, best[0].at).trim() });
      best.forEach(function (h, k) {
        var end = k + 1 < best.length ? best[k + 1].at : t.length;
        out.push({ label: h.label, value: t.slice(h.at + h.label.length, end).trim() });
      });
      return out;
    }
    // Vergleich zweier Fassungen: [{label, kind: same|chg|add|del, a, b, html}]
    function fieldDiff(ta, tb) {
      var fa = ta ? parseFields(ta) : [], fb = tb ? parseFields(tb) : [], ma = {}, mb = {}, order = [];
      fa.forEach(function (f) { ma[f.label] = f.value; if (order.indexOf(f.label) < 0) order.push(f.label); });
      fb.forEach(function (f) { mb[f.label] = f.value; if (order.indexOf(f.label) < 0) order.push(f.label); });
      return order.map(function (l) {
        var a = ma[l], b = mb[l], kind = a === undefined ? "add" : b === undefined ? "del" : a === b ? "same" : "chg";
        return { label: l, kind: kind, a: a, b: b, html: kind === "chg" ? udiff(a, b) : esc(b !== undefined ? b : a) };
      });
    }
    function histRecIds(name) {
      var r = rows[name], ids = words(r, "data-recs").concat(words(r, "data-fns"));
      if (!ids.length && isPageRow(r)) {
        var main = pageCache[r.getAttribute("data-href")];
        if (main) ids = Array.prototype.map.call(main.querySelectorAll("article.rec[id]"), function (a) { return a.id; }).slice(0, 60);
      }
      return ids;
    }
    // Ergebnis je Record für das aktuelle Paar: {id, state: same|chg|add|del|none|notext, fields}
    // Gleicher nichtleerer text_key: unverändert (kein OCR-del/ins); Rohvergleich nur ohne Schlüssel.
    function histCompare(name, pr) {
      var ids = histRecIds(name);
      return Promise.all([textDiffLib()].concat(ids.map(versionsOf))).then(function (res) {
        var ds = res.slice(1);
        return ids.map(function (id, k) {
          var d = ds[k];
          if (!d) return { id: id, state: "none" };
          var cmp = nsxHistRecordState(d, pr.from, pr.to);
          if (cmp.state === "notext") return { id: id, state: "notext" };
          if (cmp.state === "none") return { id: id, state: "none" };
          if (cmp.state === "same") return { id: id, state: "same", fields: [] };
          var a = cmp.a, b = cmp.b;
          var fields = fieldDiff(a, b);
          var state = cmp.state === "add" || cmp.state === "del" ? cmp.state
            : fields.some(function (f) { return f.kind !== "same"; }) ? "chg" : "same";
          return { id: id, state: state, fields: fields };
        });
      });
    }
    // Inspektor: Abschnitt „Release“ bzw. „Änderungen“ oben (ausgewähltes oder in der Tabelle überfahrenes Element,
    // nur im Historie-Modus). Ohne gewählte Vergleichszelle wird die aktuelle Fassung ohne Diff gezeigt.
    function histInspector(name) {
      var hov = hoverPair && hoverPair.name === name;
      if (!histOn() || (name !== selected && !hov) || !relBox || relBox.getAttribute("data-owner") !== name) return;
      var old = relBox.querySelector(":scope > .nsx-hist-is");
      if (old) old.remove();
      var r = rows[name], pr = pairFor(name);
      var sec = document.createElement("section");
      sec.className = "nsx-is nsx-hist-is";
      sec.classList.toggle("nsx-hist-hover", hov);
      var k = relBox.querySelector(":scope > .k");
      if (!pr.from) {
        var stt = pr.to ? cellState(r, pr.to) : "";
        var badge = "";
        if (!stt || stt === "del") {
          badge = '<p class="nsx-hstate nsx-hk-none">' + esc(stt === "del" ? HL.gone + " " + (pr.to || "") : HL.none + (pr.to ? " · " + pr.to : "")) + "</p>";
        } else if (stt === "add") {
          badge = '<p class="nsx-hstate nsx-hk-add">' + esc(HL.first + " " + (pr.to || "")) + "</p>";
        } else if (stt === "pdf" || stt === "cap") {
          badge = '<p class="nsx-hstate nsx-hk-notext">' + esc(HL[stt]) + "</p>";
        }
        sec.innerHTML = "<h4>" + esc(HL.rel) + '</h4><p class="nsx-hpair" data-from="" data-to="' + esc(pr.to || "") + '"><code>' + esc(pr.to || "–") + "</code></p>" +
          '<p class="nsx-hnote">' + esc(HL.pick) + '</p><div class="nsx-hres">' + badge + "</div>";
        if (k) k.insertAdjacentElement("afterend", sec); else relBox.insertBefore(sec, relBox.firstChild);
        return;
      }
      sec.innerHTML = "<h4>" + esc(HL.changes) + '</h4><p class="nsx-hpair" data-from="' + esc(pr.from || "") + '" data-to="' + esc(pr.to || "") + '">' +
        "<code>" + esc(pr.from) + '</code> <span aria-hidden="true">→</span> <code>' + esc(pr.to || "–") + "</code></p>" +
        '<p class="nsx-hnote">' + esc(HL.pick) + '</p><div class="nsx-hres"><p class="nsx-hint">' + esc(HL.loading) + "</p></div>";
      if (k) k.insertAdjacentElement("afterend", sec); else relBox.insertBefore(sec, relBox.firstChild);
      histCompare(name, pr).then(function (list) {
        if (!sec.isConnected) return;
        var box = sec.querySelector(".nsx-hres"), html = "";
        if (!list.length || list.every(function (x) { return x.state === "none"; })) {
          box.innerHTML = '<p class="nsx-hint">' + esc(HL.nodata) + "</p>";
          return;
        }
        list.forEach(function (x) {
          if (list.length > 1) html += '<h5 class="nsx-hrec">' + esc(x.id) + ' <span class="nsx-hk nsx-hk-' + esc(x.state) + '">' + esc(HL[x.state] || "") + "</span></h5>";
          if (x.state === "none") return;
          if (x.state === "notext") { html += '<p class="nsx-hint">' + esc(HL.notext) + "</p>"; return; }
          if (x.state === "same") { html += '<p class="nsx-hint">' + esc(HL.same) + "</p>"; return; }
          if (x.state === "add" && list.length === 1) html += '<p class="nsx-hstate nsx-hk-add">' + esc(HL.first + " " + pr.to) + "</p>";
          if (x.state === "del" && list.length === 1) html += '<p class="nsx-hstate nsx-hk-del">' + esc(HL.gone + " " + pr.to) + "</p>";
          var ch = x.fields.filter(function (f) { return f.kind !== "same"; });
          if (x.state === "add" || x.state === "del") ch = ch.filter(function (f) { return f.label === "Syntax" || f.label === "Description"; });
          html += '<dl class="nsx-hdl">' + ch.map(function (f) {
            return '<dt>' + esc(f.label) + ' <span class="nsx-hk nsx-hk-' + f.kind + '">' + esc(HL[f.kind] || "") + "</span></dt>" +
              '<dd class="nsx-hd-' + f.kind + '">' + (f.kind === "del" ? "<del>" + esc(f.a) + "</del>" : f.html) + "</dd>";
          }).join("") + "</dl>";
        });
        box.innerHTML = html;
      });
    }
    // Mitte: gewohnte Darstellung der Records, Unterschiede farbig (nur bei aktivem Vergleich)
    function clearHistMarks() {
      if (!detBody) return;
      detBody.querySelectorAll(".nsx-hmark").forEach(function (x) { x.remove(); });
      detBody.querySelectorAll("[data-nsx-hhide]").forEach(function (x) { x.hidden = false; x.removeAttribute("data-nsx-hhide"); });
      detBody.querySelectorAll(".nsx-hl-add, .nsx-hl-del, .nsx-hl-chg, .nsx-hl-same").forEach(function (x) {
        x.classList.remove("nsx-hl-add", "nsx-hl-del", "nsx-hl-chg", "nsx-hl-same");
      });
    }
    function replaceShown(el, html, tag, cls) {
      var n = document.createElement(tag);
      n.className = cls + " nsx-hmark nsx-hl-chg";
      n.innerHTML = html;
      el.hidden = true;
      el.setAttribute("data-nsx-hhide", "1");
      el.insertAdjacentElement("afterend", n);
    }
    function histDetail(name) {
      clearHistMarks();
      if (!histOn() || name !== selected || !detBody) return;
      var pr = hoverPair && hoverPair.name === name ? pairWith(name, histPick && histPick.name === name ? histPick.rel : null) : pairFor(name), my = token;
      if (!pr.from) {
        var r = rows[name], stt = r && pr.to ? cellState(r, pr.to) : "";
        if (r && pr.to && (!stt || stt === "del")) {
          var note = '<p class="nsx-hmark nsx-hrelnote"><span class="nsx-hk nsx-hk-none">' +
            esc(stt === "del" ? HL.gone + " " + pr.to : HL.none + " · " + pr.to) + "</span></p>";
          var arts = detBody.querySelectorAll("article.rec");
          if (arts.length) arts.forEach(function (art) {
            var rn = art.querySelector(":scope > .recname");
            if (rn) rn.insertAdjacentHTML("afterend", note); else art.insertAdjacentHTML("afterbegin", note);
          });
          else detBody.insertAdjacentHTML("afterbegin", note);
        }
        return;
      }
      histCompare(name, pr).then(function (list) {
        if (my !== token || !histOn()) return;
        var now = pairWith(name, histPick && histPick.name === name ? histPick.rel : null);
        if (!samePair(now, pr)) return;
        clearHistMarks();
        list.forEach(function (x) {
          var art = detBody.querySelector('article.rec[id="' + CSS.escape(x.id) + '"]');
          if (!art || x.state === "none" || x.state === "notext") return;
          art.classList.add("nsx-hl-" + x.state);
          var tag = '<p class="nsx-hmark nsx-hrelnote"><span class="nsx-hk nsx-hk-' + x.state + '">' + esc(HL[x.state]) + "</span> " +
            esc((pr.from ? pr.from + " → " : "") + (pr.to || "")) + "</p>";
          var rn = art.querySelector(":scope > .recname");
          if (rn) rn.insertAdjacentHTML("afterend", tag); else art.insertAdjacentHTML("afterbegin", tag);
          if (x.state !== "chg") return;
          var byL = {};
          x.fields.forEach(function (f) { byL[f.label] = f; });
          var syn = art.querySelector(":scope > pre.syntax"), desc = art.querySelector(":scope > .desc");
          if (syn && byL.Syntax && byL.Syntax.kind === "chg") replaceShown(syn, byL.Syntax.html, "pre", "syntax");
          if (desc && byL.Description && byL.Description.kind === "chg") replaceShown(desc, "<p>" + byL.Description.html + "</p>", "div", "desc");
          // Übrige Angaben der Spezifikationstabelle als Tabelle, nur Unterschiede farbig
          var rest = x.fields.filter(function (f) { return ["Syntax", "Description", "Service Name", "Name"].indexOf(f.label) < 0; });
          if (rest.length && rest.some(function (f) { return f.kind !== "same"; })) {
            var tb = '<table class="nsx-hmark nsx-hprops"><caption>' + esc(HL.props + " " + (pr.to || "")) + "</caption>" + rest.map(function (f) {
              return '<tr class="' + (f.kind === "same" ? "" : "nsx-hl-" + f.kind) + '"><th>' + esc(f.label) + "</th><td>" +
                (f.kind === "del" ? "<del>" + esc(f.a) + "</del>" : f.html) + "</td></tr>";
            }).join("") + "</table>";
            (desc || syn || art.lastElementChild).insertAdjacentHTML("afterend", tb);
          }
        });
      });
    }
    function relHighlight(rel) {
      root.classList.toggle("nsx-relhl", !!rel);
      root.querySelectorAll(".relhit").forEach(function (x) { x.classList.remove("relhit"); });
      if (!rel) return;
      root.querySelectorAll("a.nsx-oi[data-changes], a.nsx-chip[data-changes]").forEach(function (x) {
        if (words(x, "data-changes").indexOf(rel) >= 0) x.classList.add("relhit");
      });
    }
    renderHistory();
    window.addEventListener("hashchange", renderHistory);
    // Gewähltes Release geändert (Release-Kopf, Release-Wahl, Anker): Vergleich neu
    window.addEventListener("hashchange", function () {
      hoverPair = null;
      clearTimeout(hoverTimer);
      if (!histOn() || !selected) return;
      showRelations(selected);
      histDetail(selected);
    });
    function selectRelease(rel) {
      if (!rel || rel === currentRelease()) return;
      var hp = hashParts(), rest = hp.params.filter(function (x) { return x.split("=")[0] !== "release"; });
      rest.unshift("release=" + rel);
      location.hash = (hp.target ? [hp.target] : []).concat(rest).join("&");
    }
    // Vorschau beim Überfahren einer Zelle: Unterschied des Elements zwischen diesem und dem
    // gewählten Release im Inspektor; beim Verlassen wieder der gewählte Vergleich
    var hoverTimer = 0, noHoverCell = null;
    function endHover() {
      clearTimeout(hoverTimer);
      noHoverCell = null;
      if (!hoverPair) return;
      var was = hoverPair.name;
      hoverPair = null;
      updateHistArrows();
      if (selected) showRelations(selected);
      else if (relBox && relBox.getAttribute("data-owner") === was) showRelations(was);
    }
    if (outline) {
      outline.addEventListener("mouseover", function (ev) {
        if (!histOn()) return;
        var c = ev.target.closest && ev.target.closest(".nsx-hc"), a = c && c.closest("a.nsx-oi"), n = a && a.getAttribute("data-n");
        var crel = c && c.getAttribute("data-rel");
        if (!c || !n || !rows[n] || !cellState(rows[n], crel) || crel === selRel()) {
          if (!c) noHoverCell = null;
          if (hoverPair) { clearTimeout(hoverTimer); hoverTimer = setTimeout(endHover, 120); }
          return;
        }
        if (noHoverCell === n + ":" + crel) return;
        noHoverCell = null;
        clearTimeout(hoverTimer);
        var pr = pairWith(n, crel);
        if (samePair(pr, hoverPair)) return;
        hoverPair = pr;
        updateHistArrows();
        showRelations(n);
      });
      outline.addEventListener("mouseleave", endHover);
      outline.addEventListener("keydown", function (ev) {
        var hc = ev.target.closest && ev.target.closest(".nsx-hcol");
        if (!hc || (ev.key !== "Enter" && ev.key !== " ")) return;
        ev.preventDefault();
        selectRelease(hc.getAttribute("data-rel"));
      });
    }
    histModeChanged(!!outline && !!outline.querySelector('.nsx-by button[data-by="since"][aria-pressed="true"]'));
    root.addEventListener("mouseover", function (ev) {
      var h = ev.target.closest && ev.target.closest(".nsx-hb, .nsx-hg");
      relHighlight(h ? h.getAttribute("data-rel") : null);
    });
    root.addEventListener("click", function (ev) {
      var hc = ev.target.closest && ev.target.closest(".nsx-hc");
      if (hc) {
        ev.preventDefault();
        ev.stopPropagation();
        var ha = hc.closest("a.nsx-oi"), hn = ha && ha.getAttribute("data-n"), hrel = hc.getAttribute("data-rel"), cur = selRel();
        if (!hn || !rows[hn] || (!cellState(rows[hn], hrel) && hrel !== cur)) return;
        hoverPair = null;
        noHoverCell = hn + ":" + hrel;
        clearTimeout(hoverTimer);
        root.querySelectorAll(".nsx-hc.sel").forEach(function (x) { x.classList.remove("sel"); });
        if (hrel === cur || (histPick && histPick.name === hn && histPick.rel === hrel)) {
          histPick = null;
        } else {
          histPick = { name: hn, rel: hrel };
          hc.classList.add("sel");
        }
        updateHistArrows();
        if (hn === selected) { showRelations(hn); histDetail(hn); }
        else select(hn, { origin: "side", from: ha });
        return;
      }
      var hcol = ev.target.closest && ev.target.closest(".nsx-hcol");
      if (hcol) {
        ev.preventDefault();
        ev.stopPropagation();
        selectRelease(hcol.getAttribute("data-rel"));
        return;
      }
      var h = ev.target.closest && ev.target.closest(".nsx-hb, .nsx-hg");
      if (!h || ev.target.closest(".nsx-chev")) return;
      ev.preventDefault();
      ev.stopPropagation();
      var rel = h.getAttribute("data-rel");
      // Release umschalten, Auswahl (Ziel, ai=) behalten
      var hp = hashParts(), rest = hp.params.filter(function (x) { return x.split("=")[0] !== "release"; });
      if (rel !== currentRelease()) rest.unshift("release=" + rel);
      location.hash = (hp.target ? [hp.target] : []).concat(rest).join("&");
    }, true);
    root.addEventListener("keydown", function (ev) {
      if ((ev.key === "Enter" || ev.key === " ") && ev.target.matches(".nsx-hb")) { ev.preventDefault(); ev.target.click(); }
    });

    // Sprünge von außerhalb (Record-Anker, Eintragsanker)
    function fromHash() {
      var parts = hashParts(), h = parts.target, ai = hasParam(parts, "ai");
      if (!h || h === selAnchor) return;
      var rvt = reviewTarget("#" + h);
      if (h.indexOf("nsx-e-") === 0) {
        var row = document.getElementById(h);
        if (row && row.classList.contains("nsx-row")) select(row.getAttribute("data-n"), { origin: "nav", ai: ai });
      } else if (rvt) {
        select(rvt.name, { anchor: rvt.anchor, ai: ai });
      } else if (recOwner[h]) {
        select(recOwner[h], { anchor: h, ai: ai });
      }
    }
    window.addEventListener("hashchange", fromHash);
    fromHash();
  }
  function boot() {
    var any = !!document.querySelector("section.nsx");    // vor init: Modulseiten entfernen sie im Komfortmodus
    if (document.querySelector("a.spec-record-ref[data-req]")) {
      loadSpecTextI18n();
      installRequirementPreviews();
    }
    document.querySelectorAll("section.nsx").forEach(init);
    // Ein Beobachter je Dokument: der Seamless Router (fold.js) ruft boot nach jedem Seitenwechsel erneut auf
    if (window.MutationObserver && any && !boot.watching) {
      boot.watching = true;
      var dens = document.documentElement.getAttribute("data-density");
      new MutationObserver(function () {
        if (document.documentElement.getAttribute("data-density") !== dens) location.reload();
      }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-density"] });
    }
  }
  if (typeof window !== "undefined") {
    window.initNsx = boot;
    // Node-Tests laden nur nsxHistRecordState; ohne document kein Auto-Boot.
    if (typeof document !== "undefined") {
      if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
    }
  }
})();
