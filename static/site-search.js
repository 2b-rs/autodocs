/*
 * site-search.js — Volltextsuche der Kopfzeile (<form class="shell-search">).
 *
 * Statischer Index unter search/ (_src/tools/export_search.py): Termschnitte t/<kk>.json werden
 * je Suchwort nachgeladen, Dokumentschnitte d/<n>.json nur für angezeigte Treffer, l/<lang>.json
 * bringt Oberflächentexte und übersetzte Seitentitel. Durchsucht werden Spezifikations-Records
 * (Kennung, Name, Text), Seiten (Titel, Überschriften) und KI-Kommentare (Guides, Element-Notizen).
 *
 * Tokenisierung wie export_search.tokens(): NFKD ohne Zeichen der Kategorie M, klein, ß→ss,
 * Wörter aus Buchstaben/Ziffern/_, zusätzlich Teile an _ und (rein lateinisch) an Binnenmajuskeln. Jedes Suchwort
 * trifft gleiche Terme voll und längere Terme mit gleichem Anfang abgeschwächt; alle Suchwörter
 * müssen treffen (sonst Rückfall auf „eines davon“). Rang: Σ Gewicht × idf, Seiten bevorzugt.
 *
 * fold.js lädt dieses Skript beim ersten Fokus auf das Suchfeld (oder bei ?q=… in der Adresse).
 * Der reine Kern (tokens, Bewertung, Hervorhebung) ist unter Node als module.exports verfügbar
 * (_src/tests/test_site_search.py).
 */
(function (root, factory) {
  var core = factory();
  if (typeof module === "object" && module.exports) module.exports = core;
  else { root.SiteSearchCore = core; core.boot(); }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var TYPES = ["page", "ai", "rec"];
  var TYPE_BOOST = { page: 1.6, ai: 1.05, rec: 1 };
  var PREFIX_WEIGHT = 0.45, MAX_EXPANSIONS = 40, PAGE_SIZE = 20, MAX_RESULTS = 2000;
  var STOP = {};
  ("a an and are as at be been but by can could did do does for from had has have if in into is it its " +
   "may must not of on or shall should such than that the their them then there these they this those to " +
   "was were when where which while who will with within without would also only other any all each " +
   "der die das den dem des ein eine einer eines einem einen und oder nicht ist sind wird werden wurde " +
   "kann können muss müssen soll sollen mit von auf aus bei nach über unter für zum zur im am vom beim " +
   "als auch nur noch wie wenn dann dass daß sich sie er es wir ihr man so zu an ab bis durch gegen ohne " +
   "um vor hier dort dies diese dieser dieses jeder jede jedes alle keine kein sein seine ihre ihrem ihren")
    .split(" ").forEach(function (w) { STOP[w] = 1; });
  var WORD = /[\p{L}\p{N}_]+/gu;
  var CAMEL = /[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+/g;

  function fold(s) { return String(s == null ? "" : s).normalize("NFKD").replace(/\p{M}+/gu, ""); }
  function lower(s) { return s.toLowerCase().replace(/ß/g, "ss"); }

  // Terme eines Texts (Reihenfolge, mit Wiederholung); keepStop: Stoppwörter behalten (Suche nur aus Stoppwörtern)
  function tokens(text, keepStop) {
    var out = [], m, src = fold(text);
    WORD.lastIndex = 0;
    while ((m = WORD.exec(src))) {
      var w = m[0], cand = [w], parts = w.indexOf("_") >= 0 ? w.split("_").filter(Boolean) : [w];
      if (w.indexOf("_") >= 0) cand = cand.concat(parts);
      parts.forEach(function (p) { var sub = /^[A-Za-z0-9]+$/.test(p) ? (p.match(CAMEL) || []) : []; if (sub.length > 1) cand = cand.concat(sub); });
      cand.forEach(function (c) {
        var t = lower(c);
        if (t.length >= 2 && t.length <= 40 && (keepStop || !STOP[t])) out.push(t);
      });
    }
    return out;
  }
  function queryTokens(q) {
    var t = tokens(q), seen = {};
    if (!t.length) t = tokens(q, true);
    return t.filter(function (x) { if (seen[x]) return false; seen[x] = 1; return true; });
  }
  function shardFile(key) {
    if (/^[a-z0-9_]+$/.test(key)) return key;
    var bytes = new TextEncoder().encode(key), hex = "";
    for (var i = 0; i < bytes.length; i++) hex += (bytes[i] < 16 ? "0" : "") + bytes[i].toString(16);
    return "x" + hex;
  }
  // längster vorhandener Termschnitt, dessen Schlüssel Präfix des Suchworts ist
  function shardFor(token, keys) {
    for (var n = Math.min(token.length, 8); n >= 2; n--) if (keys[token.slice(0, n)]) return token.slice(0, n);
    return null;
  }
  function decode(entry) {
    var ids = entry[0], ws = entry[1], out = new Array(ids.length), acc = 0;
    for (var i = 0; i < ids.length; i++) { acc += ids[i]; out[i] = [acc, ws[i]]; }
    return out;
  }
  function idf(df, n) { return Math.log(1 + (n - df + 0.5) / (df + 0.5)); }

  // Treffer eines Suchworts in einem Termschnitt: Map Dokument → Punkte
  function scoreToken(token, shard, nDocs) {
    var scores = new Map(), terms = shard && shard.t ? shard.t : {}, cands = [];
    Object.keys(terms).forEach(function (term) {
      if (term === token) cands.push([term, 1]);
      else if (term.length > token.length && term.indexOf(token) === 0) cands.push([term, PREFIX_WEIGHT]);
    });
    var exact = cands.filter(function (c) { return c[1] === 1; });
    var pre = cands.filter(function (c) { return c[1] !== 1; })
      .sort(function (a, b) { return terms[b[0]][0].length - terms[a[0]][0].length; }).slice(0, MAX_EXPANSIONS);
    exact.concat(pre).forEach(function (c) {
      var list = decode(terms[c[0]]), f = c[1] * idf(list.length, nDocs);
      for (var i = 0; i < list.length; i++) {
        var s = list[i][1] * f, d = list[i][0];
        if (!(scores.get(d) >= s)) scores.set(d, s);
      }
    });
    return scores;
  }

  // Punkte aller Suchwörter zusammenführen; typeOf(d) liefert den Typindex des Dokuments
  function combine(perToken, typeOf) {
    var all = new Map(), and = [];
    perToken.forEach(function (m, i) {
      m.forEach(function (s, d) {
        var cur = all.get(d) || { s: 0, n: 0 };
        cur.s += s; cur.n += 1; all.set(d, cur);
      });
    });
    all.forEach(function (v, d) { if (v.n === perToken.length) and.push([d, v.s]); });
    var list = and;
    var any = false;
    if (!list.length) { any = true; all.forEach(function (v, d) { list.push([d, v.s * v.n / perToken.length]); }); }
    list.forEach(function (x) { var t = typeOf ? typeOf(x[0]) : null; if (t != null) x[1] *= TYPE_BOOST[TYPES[t]] || 1; });
    list.sort(function (a, b) { return b[1] - a[1] || a[0] - b[0]; });
    return { hits: list.slice(0, MAX_RESULTS), partial: any, total: list.length };
  }

  // Gesamtliste mischen: Unter je zehn aufeinanderfolgenden Treffern höchstens fünf einer Art, solange
  // andere Arten noch Treffer haben; innerhalb einer Art bleibt die Rangfolge.
  function diversify(hits, typeOf) {
    var queues = [[], [], []], out = [], recent = [];
    hits.forEach(function (h) { queues[typeOf(h[0])].push(h); });
    var heads = [0, 0, 0];
    while (out.length < hits.length) {
      var best = -1;
      for (var t = 0; t < 3; t++) {
        if (heads[t] >= queues[t].length) continue;
        var inWindow = recent.filter(function (x) { return x === t; }).length;
        var others = [0, 1, 2].some(function (o) { return o !== t && heads[o] < queues[o].length; });
        if (inWindow >= 5 && others) continue;
        if (best < 0 || queues[t][heads[t]][1] > queues[best][heads[best]][1]) best = t;
      }
      if (best < 0) for (var u = 0; u < 3; u++) if (heads[u] < queues[u].length) { best = u; break; }
      out.push(queues[best][heads[best]++]);
      recent.push(best);
      if (recent.length > 9) recent.shift();
    }
    return out;
  }

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  // Normalisierte Fassung eines Texts mit Rückabbildung der Positionen auf das Original
  function normMap(text) {
    var norm = "", map = [];
    for (var i = 0; i < text.length; i++) {
      var ch = text[i], code = text.charCodeAt(i);
      if (code >= 0xd800 && code <= 0xdbff && i + 1 < text.length) { ch = text.slice(i, i + 2); }
      var n = lower(fold(ch));
      for (var k = 0; k < n.length; k++) { norm += n[k]; map.push(i); }
      if (ch.length === 2) i++;
    }
    map.push(text.length);
    return { norm: norm, map: map };
  }
  function ranges(text, terms) {
    var nm = normMap(text), out = [];
    terms.forEach(function (t) {
      if (!t) return;
      var from = 0, at;
      while ((at = nm.norm.indexOf(t, from)) >= 0) {
        out.push([nm.map[at], nm.map[at + t.length] != null ? nm.map[at + t.length] : text.length]);
        from = at + t.length;
      }
    });
    out.sort(function (a, b) { return a[0] - b[0]; });
    var merged = [];
    out.forEach(function (r) {
      var last = merged[merged.length - 1];
      if (last && r[0] <= last[1]) last[1] = Math.max(last[1], r[1]); else merged.push(r.slice());
    });
    return merged;
  }
  function highlight(text, terms) {
    text = String(text || "");
    var rs = ranges(text, terms), out = "", pos = 0;
    rs.forEach(function (r) { out += esc(text.slice(pos, r[0])) + "<mark>" + esc(text.slice(r[0], r[1])) + "</mark>"; pos = r[1]; });
    return out + esc(text.slice(pos));
  }
  // Ausschnitt um den ersten Treffer (len Zeichen)
  function snippet(text, terms, len) {
    text = String(text || "");
    len = len || 220;
    if (text.length <= len) return text;
    var rs = ranges(text, terms), start = 0;
    if (rs.length) start = Math.max(0, rs[0][0] - Math.round(len * 0.3));
    var cut = text.slice(start, start + len);
    return (start > 0 ? "…" : "") + cut.replace(/^\S*\s/, start > 0 ? "" : "$&") + (start + len < text.length ? "…" : "");
  }

  // ------------------------------------------------------------------ Browser

  var UI_DEFAULT = {
    all: "Alle", type_page: "Seite", type_ai: "KI-Kommentar", type_rec: "Spezifikation",
    tab_page: "Seiten", tab_ai: "KI-Kommentare", tab_rec: "Spezifikation",
    results: "{n} Treffer", none: "Keine Treffer für „{q}“", partial: "Nicht alle Suchwörter gefunden – Treffer für einzelne Wörter",
    loading: "Suchindex wird geladen…", more: "Weitere Treffer", error: "Der Suchindex ist nicht verfügbar.",
    hint: "↑↓ wählen · Enter öffnen · Esc schließen", label: "Suchergebnisse", min: "Mindestens zwei Zeichen eingeben",
    ai_modules: "Modul-Guide", ai_clusters: "Cluster-Guide", ai_classes: "Klassen-Guide", ai_namespaces: "Namespace-Guide",
    ai_services: "Service-Guide", ai_elements: "Element-Kommentar"
  };

  function boot() {
    if (typeof document === "undefined") return;
    var input = document.querySelector("[data-search-input]");
    if (!input || input.getAttribute("data-site-search")) return;
    input.setAttribute("data-site-search", "1");
    var form = input.closest("form");
    var script = document.currentScript || document.querySelector('script[src*="site-search.js"]');
    var base = new URL("../search/", script ? script.src : location.href).href;
    var home = document.querySelector("header.shell a.home");
    var langBase = home ? new URL(home.getAttribute("href") || "index.html", location.href).href.replace(/[^/]*$/, "") : "";
    var lang = (document.documentElement.getAttribute("lang") || "de").split("-")[0];
    var cache = {}, meta = null, keys = {}, langData = { ui: {}, titles: {}, kinds: {} };
    var ui = function (k, vars) {
      var s = (langData.ui && langData.ui[k]) || UI_DEFAULT[k] || k;
      return vars ? s.replace(/\{(\w+)\}/g, function (m, n) { return vars[n] != null ? vars[n] : m; }) : s;
    };
    function get(path) {
      if (!cache[path]) {
        var url = base + path + (meta && meta.build ? "?v=" + meta.build : "");
        cache[path] = fetch(url).then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); });
        cache[path].catch(function () { delete cache[path]; });
      }
      return cache[path];
    }
    var ready = get("meta.json").then(function (m) {
      meta = m;
      (m.term_shards || []).forEach(function (k) { keys[k] = 1; });
      return get("l/" + lang + ".json").then(function (l) { langData = l || langData; }, function () { /* ohne Sprachdatei */ });
    });

    // ---- Panel
    var panel = document.createElement("div");
    panel.className = "site-search-panel";
    panel.id = "site-search-panel";
    panel.hidden = true;
    panel.setAttribute("role", "dialog");
    document.body.appendChild(panel);
    input.setAttribute("role", "combobox");
    input.setAttribute("aria-autocomplete", "list");
    input.setAttribute("aria-controls", "site-search-panel");
    input.setAttribute("aria-expanded", "false");

    function place() {
      if (panel.hidden) return;
      var r = (form || input).getBoundingClientRect(), vw = document.documentElement.clientWidth;
      var narrow = vw < 640, width = narrow ? vw - 16 : Math.min(Math.max(r.width, 560), vw - 16);
      var left = narrow ? 8 : Math.min(Math.max(8, r.left), vw - width - 8);
      panel.style.top = Math.round(r.bottom + 6) + "px";
      panel.style.left = Math.round(left) + "px";
      panel.style.width = Math.round(width) + "px";
      panel.style.maxHeight = Math.max(200, window.innerHeight - r.bottom - 18) + "px";
    }
    function open() { panel.hidden = false; input.setAttribute("aria-expanded", "true"); place(); }
    function close() { panel.hidden = true; input.setAttribute("aria-expanded", "false"); input.removeAttribute("aria-activedescendant"); }
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, { passive: true });

    var state = { q: "", terms: [], hits: [], filter: "all", shown: PAGE_SIZE, active: -1, partial: false, seq: 0 };

    function typeOfFactory() {
      // Typ eines Dokuments ohne Dokumentschnitt: Seiten, KI-Texte und Records liegen in dieser Reihenfolge
      var c = (meta && meta.counts) || {}, p = c.page || 0, a = c.ai || 0;
      return function (d) { return d < p ? 0 : (d < p + a ? 1 : 2); };
    }

    function run(q) {
      var my = ++state.seq;
      state.q = q;
      var terms = queryTokens(q);
      if (!q.trim()) { close(); return; }
      open();
      if (!terms.length) { panel.innerHTML = '<p class="ss-msg">' + esc(ui("min")) + "</p>"; return; }
      if (!meta) panel.innerHTML = '<p class="ss-msg">' + esc(ui("loading")) + "</p>";
      ready.then(function () {
        return Promise.all(terms.map(function (t) {
          var k = shardFor(t, keys);
          return k ? get("t/" + shardFile(k) + ".json").catch(function () { return null; }) : Promise.resolve(null);
        }));
      }).then(function (shards) {
        if (my !== state.seq) return;
        var per = terms.map(function (t, i) { return scoreToken(t, shards[i], meta.docs); });
        titleMatches(terms).forEach(function (d) { per.forEach(function (m) { if (!m.has(d)) m.set(d, 0.0001); }); per[0].set(d, (per[0].get(d) || 0) + 40); });
        var res = combine(per, typeOfFactory());
        state.terms = terms; state.hits = res.hits; state.mixed = null; state.partial = res.partial; state.total = res.total;
        state.shown = PAGE_SIZE; state.active = -1;
        render();
      }).catch(function () {
        if (my === state.seq) panel.innerHTML = '<p class="ss-msg ss-err">' + esc(ui("error")) + "</p>";
      });
    }
    // Übersetzte Seitentitel der Sprache: Treffer, wenn jedes Suchwort einen Wortanfang trifft
    function titleMatches(terms) {
      var out = [];
      Object.keys(langData.titles || {}).forEach(function (id) {
        var words = tokens(langData.titles[id], true);
        if (terms.every(function (t) { return words.some(function (w) { return w.indexOf(t) === 0; }); })) out.push(+id);
      });
      return out;
    }
    function filtered() {
      var typeOf = typeOfFactory();
      if (state.filter === "all") return state.mixed || (state.mixed = diversify(state.hits, typeOf));
      var ti = TYPES.indexOf(state.filter);
      return state.hits.filter(function (h) { return typeOf(h[0]) === ti; });
    }
    function docs(ids) {
      var per = meta.per_shard || 200, need = {};
      ids.forEach(function (d) { need[Math.floor(d / per)] = 1; });
      return Promise.all(Object.keys(need).map(function (s) { return get("d/" + s + ".json").then(function (rows) { return [+s, rows]; }); }))
        .then(function (parts) {
          var map = {};
          parts.forEach(function (p) { p[1].forEach(function (row, i) { map[p[0] * per + i] = row; }); });
          return map;
        });
    }
    function render() {
      var my = state.seq, typeOf = typeOfFactory(), list = filtered(), view = list.slice(0, state.shown);
      var counts = { all: state.hits.length, page: 0, ai: 0, rec: 0 };
      state.hits.forEach(function (h) { counts[TYPES[typeOf(h[0])]]++; });
      if (!state.hits.length) {
        panel.innerHTML = '<p class="ss-msg">' + esc(ui("none", { q: state.q.trim() })) + "</p>";
        return;
      }
      docs(view.map(function (h) { return h[0]; })).then(function (map) {
        if (my !== state.seq) return;
        var tabs = ["all"].concat(TYPES).map(function (t) {
          if (t !== "all" && !counts[t]) return "";
          var label = t === "all" ? ui("all") : ui("tab_" + t);
          return '<button type="button" class="ss-tab' + (state.filter === t ? " is-active" : "") + '" data-ss-filter="' + t +
            '" aria-pressed="' + (state.filter === t) + '">' + esc(label) + ' <span class="ss-count">' + counts[t] + "</span></button>";
        }).join("");
        var items = view.map(function (h, i) {
          var row = map[h[0]];
          if (!row) return "";
          var type = TYPES[row[0]], title = row[1];
          if (type === "page" && langData.titles[h[0]]) title = langData.titles[h[0]];
          else if (type === "ai" && row[5] >= 0 && langData.titles[row[5]]) title = langData.titles[row[5]];
          var sub = type === "ai" ? ui("ai_" + row[2]) :
            String(row[2] || "").split(" · ").map(function (x) { return (langData.kinds || {})[x] || x; }).join(" · ");
          var href = langBase + row[3];
          return '<a class="ss-hit ss-' + type + '" role="option" id="ss-opt-' + i + '" href="' + esc(href) + '" data-ss-index="' + i + '">' +
            '<span class="ss-type">' + esc(ui("type_" + type)) + "</span>" +
            '<span class="ss-title">' + highlight(title, state.terms) + "</span>" +
            (sub ? '<span class="ss-sub">' + highlight(sub, state.terms) + "</span>" : "") +
            (row[4] ? '<span class="ss-text">' + highlight(snippet(row[4], state.terms, 220), state.terms) + "</span>" : "") +
            "</a>";
        }).join("");
        var more = list.length > state.shown ? '<button type="button" class="ss-more" data-ss-more>' + esc(ui("more")) + " (" + (list.length - state.shown) + ")</button>" : "";
        panel.innerHTML = '<div class="ss-head"><div class="ss-tabs" role="group">' + tabs + "</div>" +
          '<span class="ss-total">' + esc(ui("results", { n: state.total > state.hits.length ? state.hits.length + "+" : state.hits.length })) + "</span></div>" +
          (state.partial ? '<p class="ss-msg ss-partial">' + esc(ui("partial")) + "</p>" : "") +
          '<div class="ss-list" role="listbox" aria-label="' + esc(ui("label")) + '">' + items + "</div>" + more +
          '<p class="ss-hint">' + esc(ui("hint")) + "</p>";
        setActive(state.active);
        place();
      });
    }
    function options() { return panel.querySelectorAll(".ss-hit"); }
    function setActive(i) {
      var opts = options();
      state.active = Math.max(-1, Math.min(i, opts.length - 1));
      opts.forEach(function (o, k) { o.classList.toggle("is-active", k === state.active); o.setAttribute("aria-selected", k === state.active ? "true" : "false"); });
      if (state.active >= 0) { input.setAttribute("aria-activedescendant", opts[state.active].id); opts[state.active].scrollIntoView({ block: "nearest" }); }
      else input.removeAttribute("aria-activedescendant");
    }

    var timer = null;
    input.addEventListener("input", function () {
      clearTimeout(timer);
      var q = input.value;
      timer = setTimeout(function () { run(q); }, 120);
    });
    input.addEventListener("focus", function () { if (input.value.trim() && panel.innerHTML) open(); });
    input.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); if (panel.hidden && input.value.trim()) run(input.value); setActive(state.active + 1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); setActive(state.active - 1); }
      else if (e.key === "Escape") { close(); }
      else if (e.key === "Enter") {
        var opts = options(), pick = opts[state.active >= 0 ? state.active : 0];
        e.preventDefault();
        if (pick && !panel.hidden) location.href = pick.href; else run(input.value);
      }
    });
    if (form) form.addEventListener("submit", function (e) { e.preventDefault(); });
    panel.addEventListener("click", function (e) {
      var f = e.target.closest("[data-ss-filter]");
      if (f) { state.filter = f.getAttribute("data-ss-filter"); state.shown = PAGE_SIZE; state.active = -1; render(); return; }
      if (e.target.closest("[data-ss-more]")) { state.shown += PAGE_SIZE; render(); }
    });
    panel.addEventListener("mousemove", function (e) {
      var h = e.target.closest(".ss-hit");
      if (h) setActive(+h.getAttribute("data-ss-index"));
    });
    document.addEventListener("click", function (e) {
      // composedPath: Ein Klick auf einen Reiter rendert das Panel neu, e.target hängt dann nicht mehr darin
      var path = e.composedPath ? e.composedPath() : [e.target];
      if (panel.hidden || path.indexOf(panel) >= 0 || (form && path.indexOf(form) >= 0)) return;
      close();
    });

    var q0 = new URLSearchParams(location.search).get("q");
    if (q0 && !input.value) input.value = q0;
    if (input.value.trim()) run(input.value);
  }

  return {
    tokens: tokens, queryTokens: queryTokens, shardFile: shardFile, shardFor: shardFor, decode: decode,
    scoreToken: scoreToken, combine: combine, diversify: diversify, highlight: highlight, snippet: snippet, boot: boot, TYPES: TYPES
  };
});
