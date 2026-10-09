/*
 * versions-explorer.js — Versions- & Provenienz-Explorer (<lang>/versions.html)
 *
 * Elemente, Schaubilder und Snippets als Master-Detail-Ansicht mit kombinierbaren
 * Facetten. Daten: versions/explorer/{elements,figures,snippets}.json und
 * versions/explorer/items/<id>.json (export_explorer.py), Versionsdaten aus
 * versions/data/<id>.json. Fehlt der Explorer-Index, dient versions/catalog.json
 * als Rückfall (nur Suche und Grundfilter).
 *
 * Dateinamen je Kennung folgen _src/tools/case_safe_names.py: schlicht <id>, bei
 * Kennungen, die sich nur in der Schreibweise unterscheiden, <id>~<Maske>. Welche
 * Stämme abweichen, steht in elements.json ("names") bzw. im "file" des Katalogs.
 *
 * Der reine Kern (Zustand <-> URL, Facettenfilter, Zählungen, abbruchsicheres Laden,
 * Markdown der KI-Beschreibungen) ist unter Node als module.exports verfügbar und wird
 * von _src/tests/test_versions_explorer.py und test_figure_access.py geprüft.
 *
 * Schaubilder sind nicht öffentlich: Bilder lädt static/figure-images.js (geschützt über
 * den Worker, nur mit Anmeldung und Freigabe); der Explorer setzt nur Platzhalter.
 */
(function (root, factory) {
  var core = factory();
  if (typeof module === "object" && module.exports) module.exports = core;
  else root.VersionsExplorerCore = core;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var STATUS = [["new", 1], ["changed", 2], ["removed", 4], ["unchanged", 8]];
  var HAS = ["fig", "snip", "ai", "cit"];

  // URL-Parameter je Bereich: [Zustandsschlüssel, URL-Name, mehrwertig]
  var PARAMS = {
    el: [["q", "q"], ["kind", "kind", 1], ["plat", "plat", 1], ["st", "st", 1], ["doc", "doc", 1],
         ["mod", "mod", 1], ["cl", "cl", 1], ["first", "first"], ["last", "last"], ["chg", "chg"],
         ["has", "has", 1]],
    fig: [["q", "fq"], ["plat", "fplat", 1], ["mod", "fmod", 1], ["doc", "fdoc"], ["multi", "fmulti"],
          ["id", "fid"]],
    snip: [["q", "sq"], ["plat", "splat", 1], ["mod", "smod", 1], ["doc", "sdoc"], ["role", "srole", 1],
           ["id", "sid"]]
  };
  var TABS = ["el", "fig", "snip"];
  var VIEWS = ["ver", "fig", "snip", "cit"];
  var UNIVERSES = ["CP", "AP", "FO", "other"];

  function emptyState() {
    var s = { tab: "el", id: "", view: "ver", from: "", to: "", el: {}, fig: {}, snip: {} };
    TABS.forEach(function (t) {
      PARAMS[t].forEach(function (p) { s[t][p[0]] = p[2] ? [] : ""; });
    });
    return s;
  }

  function parseState(search) {
    var u = new URLSearchParams(search || "");
    var s = emptyState();
    var tab = u.get("tab");
    if (TABS.indexOf(tab) >= 0) s.tab = tab;
    s.id = (u.get("id") || "").trim();
    var view = u.get("view");
    if (VIEWS.indexOf(view) >= 0) s.view = view;
    s.from = u.get("from") || "";
    s.to = u.get("to") || "";
    TABS.forEach(function (t) {
      PARAMS[t].forEach(function (p) {
        var v = u.get(p[1]);
        if (v == null && t === "el" && p[0] === "q") v = u.get("query");
        if (v == null) return;
        s[t][p[0]] = p[2] ? v.split(",").map(function (x) { return x.trim(); }).filter(Boolean) : v.trim();
      });
    });
    return s;
  }

  function serializeState(s) {
    var u = new URLSearchParams();
    if (s.tab && s.tab !== "el") u.set("tab", s.tab);
    TABS.forEach(function (t) {
      PARAMS[t].forEach(function (p) {
        var v = s[t][p[0]];
        if (p[2]) { if (v && v.length) u.set(p[1], v.join(",")); }
        else if (v) u.set(p[1], v);
      });
    });
    if (s.id) u.set("id", s.id);
    if (s.id && s.view && s.view !== "ver") u.set("view", s.view);
    if (s.id && s.from && s.to) { u.set("from", s.from); u.set("to", s.to); }
    var out = u.toString().replace(/%2C/g, ",");
    return out ? "?" + out : "";
  }

  function activeCount(s, tab) {
    var n = 0;
    PARAMS[tab].forEach(function (p) {
      if (p[0] === "q" || p[0] === "id") return;
      var v = s[tab][p[0]];
      n += p[2] ? v.length : (v ? 1 : 0);
    });
    return n;
  }

  // ------------------------------------------------------------------ Elementindex

  function decodeElements(raw) {
    var c = raw.cols;
    var n = c.id.length;
    var nm = raw.names || {};
    var zeros = function () { var a = new Array(n); for (var z = 0; z < n; z++) a[z] = 0; return a; };
    var idx = {
      n: n, ids: c.id, names: c.name, kind: c.kind, mod: c.mod, cl: c.cl, doc: c.doc, plat: c.plat,
      rel: c.rel, chg: c.chg, first: c.first, last: c.last, st: c.st, nv: c.nv, fig: c.fig, snip: c.snip,
      ai: c.ai, page: c.page, cit: c.cit || zeros(), ref: c.ref || zeros(), full: true,
      stems: { rec: nm.records || {}, item: nm.items || {}, ref: nm.refs || {} },
      dict: { kind: raw.kinds, plat: raw.platforms, doc: raw.docs, mod: raw.modules, cl: raw.clusters,
              rel: raw.releases, modUni: raw.module_universe || [] },
      aliases: raw.aliases || {}, lower: null,
      counts: raw.counts || {}, byId: new Map(), hay: new Array(n)
    };
    for (var i = 0; i < n; i++) {
      idx.byId.set(c.id[i], i);
      var m = c.mod[i] >= 0 ? raw.modules[c.mod[i]] : "";
      idx.hay[i] = (c.id[i] + " " + (c.name[i] || "") + " " + m).toLowerCase();
    }
    return idx;
  }

  // Zitierte Kennung -> Index des Elements: exakt, über einen Alias (andere Schreibweise)
  // oder eindeutig ohne Groß-/Kleinschreibung; sonst -1
  function resolveId(idx, id) {
    if (!idx) return -1;
    if (idx.byId.has(id)) return idx.byId.get(id);
    var a = idx.aliases && idx.aliases[id];
    if (a && idx.byId.has(a)) return idx.byId.get(a);
    if (!idx.lower) {
      idx.lower = new Map();
      idx.ids.forEach(function (x, k) {
        var key = x.toLowerCase();
        idx.lower.set(key, idx.lower.has(key) ? -2 : k);
      });
    }
    var k = idx.lower.get(String(id).toLowerCase());
    return k >= 0 ? k : -1;
  }

  // Rückfall ohne Explorer-Index: versions/catalog.json (Plattform, Releases, Wegfall)
  function decodeCatalog(items) {
    var rels = {};
    items.forEach(function (it) { (it.releases || []).forEach(function (r) { rels[r] = 1; }); });
    var releases = Object.keys(rels).sort();
    var ri = {};
    releases.forEach(function (r, i) { ri[r] = i; });
    var plats = ["AP", "CP"];
    var cols = { id: [], name: [], kind: [], mod: [], cl: [], doc: [], plat: [], rel: [], chg: [], first: [],
                 last: [], st: [], nv: [], fig: [], snip: [], ai: [], page: [] };
    var recStems = {};
    items.forEach(function (it) {
      var m = /^versions\/data\/(.+)\.json$/.exec(it.file || "");
      if (m && m[1] !== it.id) recStems[it.id] = m[1];
      var mask = 0, first = -1, last = -1;
      (it.releases || []).forEach(function (r) {
        var k = ri[r]; mask |= (1 << k);
        if (first < 0 || k < first) first = k;
        if (k > last) last = k;
      });
      cols.id.push(it.id); cols.name.push(""); cols.kind.push(-1); cols.mod.push(-1); cols.cl.push(-1);
      cols.doc.push(-1); cols.plat.push(Math.max(0, plats.indexOf(it.platform))); cols.rel.push(mask);
      cols.chg.push(0); cols.first.push(first); cols.last.push(last);
      cols.st.push(it.is_dropped ? 4 : 0); cols.nv.push(it.version_count || 0);
      cols.fig.push(0); cols.snip.push(0); cols.ai.push(0); cols.page.push(0);
    });
    var idx = decodeElements({ cols: cols, kinds: [], platforms: plats, docs: [], modules: [], clusters: [],
                               releases: releases, names: { records: recStems } });
    idx.full = false;
    return idx;
  }

  // Facettengruppen. type: one (ein Wert je Eintrag), many (Liste von Werten),
  // bits (Bitmaske, ODER), flags (Bitmaske, UND-verknüpfte Merkmale)
  function elementGroups(idx) {
    var g = [
      { key: "kind", type: "one", get: function (i) { return idx.kind[i]; }, values: idx.dict.kind },
      { key: "plat", type: "one", get: function (i) { return idx.plat[i]; }, values: idx.dict.plat },
      { key: "st", type: "bits", get: function (i) { return idx.st[i]; },
        values: STATUS.map(function (s) { return s[0]; }), bit: function (k) { return STATUS[k][1]; } },
      { key: "doc", type: "one", get: function (i) { return idx.doc[i]; }, values: idx.dict.doc },
      { key: "mod", type: "one", get: function (i) { return idx.mod[i]; }, values: idx.dict.mod },
      { key: "cl", type: "one", get: function (i) { return idx.cl[i]; }, values: idx.dict.cl },
      { key: "first", type: "one", get: function (i) { return idx.first[i]; }, values: idx.dict.rel },
      { key: "last", type: "one", get: function (i) { return idx.last[i]; }, values: idx.dict.rel },
      { key: "chg", type: "bits", get: function (i) { return idx.chg[i]; }, values: idx.dict.rel,
        bit: function (k) { return 1 << k; } },
      { key: "has", type: "flags", values: HAS, get: function (i) {
        return (idx.fig[i] > 0 ? 1 : 0) | (idx.snip[i] > 0 ? 2 : 0) | (idx.ai[i] ? 4 : 0) | (idx.cit[i] > 0 ? 8 : 0);
      }, bit: function (k) { return 1 << k; } }
    ];
    return g;
  }

  // Auswahl (Werte als Text aus der URL) -> Codes der Gruppe
  function selectionCodes(group, selected) {
    var sel = Array.isArray(selected) ? selected : (selected ? [selected] : []);
    var codes = [];
    sel.forEach(function (v) {
      var k = group.values.indexOf(v);
      if (k >= 0) codes.push(k);
    });
    return codes;
  }

  function groupMatches(group, codes, i) {
    if (!codes.length) return true;
    var v = group.get(i);
    if (group.type === "one") return codes.indexOf(v) >= 0;
    if (group.type === "many") {
      for (var m = 0; m < v.length; m++) if (codes.indexOf(v[m]) >= 0) return true;
      return false;
    }
    if (group.type === "bits") {
      for (var a = 0; a < codes.length; a++) if (v & group.bit(codes[a])) return true;
      return false;
    }
    for (var b = 0; b < codes.length; b++) if (!(v & group.bit(codes[b]))) return false;
    return true;
  }

  function countValues(group, i, counts) {
    var v = group.get(i);
    if (group.type === "one") { if (v >= 0) counts[v] = (counts[v] || 0) + 1; return; }
    if (group.type === "many") {
      for (var m = 0; m < v.length; m++) counts[v[m]] = (counts[v[m]] || 0) + 1;
      return;
    }
    for (var k = 0; k < group.values.length; k++) {
      if (v & group.bit(k)) counts[k] = (counts[k] || 0) + 1;
    }
  }

  /**
   * Facettensuche mit disjunktiven Zählungen: Der Zähler eines Werts gibt an,
   * wie viele Treffer es mit allen übrigen Filtern und diesem Wert gäbe.
   * textMatch(i) -> bool filtert vorab (Freitext).
   */
  function facetFilter(n, groups, selection, textMatch) {
    var codes = groups.map(function (g) { return selectionCodes(g, selection[g.key]); });
    var counts = groups.map(function () { return {}; });
    var matches = [];
    var G = groups.length;
    for (var i = 0; i < n; i++) {
      if (textMatch && !textMatch(i)) continue;
      var fails = 0, failG = -1;
      for (var g = 0; g < G; g++) {
        if (!groupMatches(groups[g], codes[g], i)) {
          fails++; failG = g;
          if (fails > 1) break;
        }
      }
      if (fails === 0) {
        matches.push(i);
        for (var h = 0; h < G; h++) countValues(groups[h], i, counts[h]);
      } else if (fails === 1 && groups[failG].type !== "flags") {
        countValues(groups[failG], i, counts[failG]);
      }
    }
    var byKey = {};
    groups.forEach(function (g, k) { byKey[g.key] = counts[k]; });
    return { matches: matches, counts: byKey };
  }

  function textMatcher(hay, q) {
    var terms = String(q || "").toLowerCase().split(/\s+/).filter(Boolean);
    if (!terms.length) return null;
    return function (i) {
      var h = hay[i];
      for (var k = 0; k < terms.length; k++) if (h.indexOf(terms[k]) < 0) return false;
      return true;
    };
  }

  function filterElements(idx, sel) {
    return facetFilter(idx.n, elementGroups(idx), sel, textMatcher(idx.hay, sel.q));
  }

  // ------------------------------------------------------------------ Schaubilder & Snippets

  function decodeItems(raw, elementIdx) {
    var n = raw.id.length;
    var plats = [], docs = [], roles = ["constitutive", "heuristic"];
    var pi = {}, di = {};
    var it = { n: n, ids: raw.id, title: raw.title, doc: raw.doc, page: raw.page, rel: raw.rel,
               targets: raw.targets, nser: raw.nser, sha: raw.sha, src: raw.src, role: raw.role,
               platCode: new Array(n), docCode: new Array(n), roleBits: new Array(n), modBits: new Array(n),
               hay: new Array(n), byId: new Map(), dict: { plat: plats, doc: docs, role: roles, mod: [] } };
    var mods = elementIdx && elementIdx.full ? elementIdx.dict.mod : [];
    it.dict.mod = mods;
    for (var i = 0; i < n; i++) {
      it.byId.set(raw.id[i], i);
      var p = raw.plat[i] || "";
      if (!(p in pi)) { pi[p] = plats.length; plats.push(p); }
      it.platCode[i] = pi[p];
      var d = raw.doc[i] || "";
      if (!(d in di)) { di[d] = docs.length; docs.push(d); }
      it.docCode[i] = di[d];
      var rb = 0;
      String(raw.role[i] || "").split(",").forEach(function (r) {
        var k = roles.indexOf(r); if (k >= 0) rb |= (1 << k);
      });
      it.roleBits[i] = rb;
      var ms = [];
      if (mods.length) {
        (raw.targets[i] || []).forEach(function (tid) {
          var e = elementIdx.byId.get(tid);
          if (e != null && elementIdx.mod[e] >= 0 && ms.indexOf(elementIdx.mod[e]) < 0) ms.push(elementIdx.mod[e]);
        });
      }
      it.modBits[i] = ms;
      it.hay[i] = (raw.id[i] + " " + (raw.title[i] || "") + " " + d).toLowerCase();
    }
    // Dokumente alphabetisch für die Auswahlliste
    it.docOrder = docs.map(function (d, k) { return k; }).sort(function (a, b) {
      return docs[a].localeCompare(docs[b]);
    });
    return it;
  }

  function itemGroups(it, kind) {
    var g = [
      { key: "plat", type: "one", get: function (i) { return it.platCode[i]; }, values: it.dict.plat },
      { key: "doc", type: "one", get: function (i) { return it.docCode[i]; }, values: it.dict.doc },
      { key: "mod", type: "many", get: function (i) { return it.modBits[i]; }, values: it.dict.mod }
    ];
    if (kind === "snip") {
      g.push({ key: "role", type: "bits", get: function (i) { return it.roleBits[i]; }, values: it.dict.role,
               bit: function (k) { return 1 << k; } });
    } else {
      g.push({ key: "multi", type: "flags", get: function (i) { return it.nser[i] > 1 ? 1 : 0; }, values: ["1"],
               bit: function () { return 1; } });
    }
    return g;
  }

  function filterItems(it, kind, sel) {
    return facetFilter(it.n, itemGroups(it, kind), sel, textMatcher(it.hay, sel.q));
  }

  // ------------------------------------------------------------------ Revisions-Zeitachse

  // Inhaltsvergleich ohne Leerraum und Bindestriche (gleiche Regel wie export_explorer.norm_content):
  // Extraktionsvarianten wie „erro r“ oder „develop- ment“ sind kein Änderungspunkt.
  var NORM_DROP = /[\s\u00ad\u2010\u2011-]+/g;
  var ENTITY = /&(?:([A-Za-z]+)|#(\d+)|#x([0-9A-Fa-f]+));/g;
  var NAMED = { lt: "<", gt: ">", amp: "&", quot: '"', apos: "'", nbsp: "\u00a0" };
  // HTML-Entitäten genau einmal auflösen (Anzeige von Versionstexten, die als HTML-Text erfasst sind)
  function decodeEntities(text) {
    return String(text == null ? "" : text).replace(ENTITY, function (m, name, dec, hex) {
      if (name) return Object.prototype.hasOwnProperty.call(NAMED, name) ? NAMED[name] : m;
      var code = dec ? parseInt(dec, 10) : parseInt(hex, 16);
      return code > 0 && code < 0x110000 ? String.fromCodePoint(code) : m;
    });
  }
  function decodeFully(text) {
    var out = String(text || "");
    for (var k = 0; k < 3; k++) { var next = decodeEntities(out); if (next === out) break; out = next; }
    return out;
  }
  function normContent(text) { return decodeFully(text).replace(NORM_DROP, ""); }

  // Spezifikationskennungen in Belegtexten (gleiche Regel wie export_explorer.CITE_RE)
  var CITE_SRC = "((?:AP_|CP_|FO_)?(?:SWS|SRS|RS|PRS|TPS|ECUC)_[A-Za-z][A-Za-z0-9]*(?:_CONSTR)?_\\d{4,5})(?![A-Za-z0-9])";
  function citedIds(text) {
    var re = new RegExp("(^|[^A-Za-z0-9_])" + CITE_SRC, "g"), out = [], m;
    while ((m = re.exec(String(text || "")))) if (out.indexOf(m[2]) < 0) out.push(m[2]);
    return out;
  }
  // Kennungen in bereits maskiertem HTML-Text durch render(id) ersetzen (render liefert HTML oder null)
  function linkifyIds(escapedHtml, render) {
    var re = new RegExp("(^|[^A-Za-z0-9_])" + CITE_SRC, "g");
    return String(escapedHtml).replace(re, function (all, pre, id) {
      var h = render(id);
      return h == null ? all : pre + h;
    });
  }

  function releaseKey(rel) {
    var m = /^R(\d{2})-(\d{2})/.exec(rel || "");
    return m ? (+m[1]) * 100 + (+m[2]) : 99999;
  }

  function sortReleases(list) {
    var seen = {}, out = [];
    list.forEach(function (r) { if (r && !seen[r]) { seen[r] = 1; out.push(r); } });
    return out.sort(function (a, b) { return releaseKey(a) - releaseKey(b) || (a < b ? -1 : a > b ? 1 : 0); });
  }

  function sortVersions(versions) {
    return (versions || []).map(function (v, i) { return [v, i]; }).sort(function (a, b) {
      return releaseKey(a[0].release) - releaseKey(b[0].release) || a[1] - b[1];
    }).map(function (x) { return x[0]; });
  }

  function versionHash(v) { return (String((v && v.version_id) || "").split("#")[1] || "").substring(0, 8); }

  /**
   * Segmente der Zeitachse in Release-Reihenfolge:
   *   absent    – Plattform-Releases vor dem ersten Auftreten (nicht vorhanden bis einschließlich …)
   *   content   – aufeinanderfolgende Releases mit gleichem (normalisiertem) Inhalt
   *   presence  – Releases, in denen das Spezifikations-PDF das Element definiert, der Wortlaut
   *               aber nicht erfasst ist (text_captured: false); kein Vergleich möglich
   *   gap       – Plattform-Releases zwischen zwei Auftreten, in denen das Element fehlt
   *   dropped   – Plattform-Releases nach dem letzten Auftreten (entfallen)
   *   unchecked – Releases, deren Spezifikation für das Element nicht ausgewertet wurde
   *               (lifecycle.unchecked); weder „entfallen“ noch „nicht vorhanden“
   * Ein Segment nennt nur die Releases, die es tatsächlich umfasst.
   */
  function buildTimeline(versions, lifecycle) {
    lifecycle = lifecycle || {};
    var byRel = [];
    sortVersions(versions).forEach(function (v) {
      if (!v.release) return;
      if (byRel.length && byRel[byRel.length - 1].release === v.release) byRel[byRel.length - 1] = v;
      else byRel.push(v);
    });
    var recorded = byRel.map(function (v) { return v.release; });
    var unchecked = sortReleases(lifecycle.unchecked || []);
    var dropIn = lifecycle.is_dropped ? sortReleases(lifecycle.dropped_in || []) : [];
    var universe = sortReleases([].concat(lifecycle.platform_releases || [], recorded, lifecycle.absent_before || [],
                                          lifecycle.dropped_in || [], unchecked));
    var segs = [];
    if (!recorded.length) return segs;
    function pushRuns(list, type) {
      var run = null;
      list.forEach(function (r) {
        var ty = unchecked.indexOf(r) >= 0 ? "unchecked" : type;
        if (run && run.type === ty) run.releases.push(r);
        else { run = { type: ty, releases: [r] }; segs.push(run); }
        if (ty === "absent") run.until = r;
        if (ty === "dropped" && !run.from) run.from = r;
      });
      return list.length > 0;
    }
    var firstKey = releaseKey(recorded[0]), lastKey = releaseKey(recorded[recorded.length - 1]);
    var before = lifecycle.platform_releases
      ? universe.filter(function (r) { return releaseKey(r) < firstKey && recorded.indexOf(r) < 0; })
      : sortReleases(lifecycle.absent_before || []);
    pushRuns(before, "absent");
    var seen = {}, cur = null, pres = null, prevRel = null, lastContent = null;
    byRel.forEach(function (v) {
      if (prevRel && lifecycle.platform_releases) {
        var lo = releaseKey(prevRel), hi = releaseKey(v.release);
        var gap = universe.filter(function (r) { var k = releaseKey(r); return k > lo && k < hi && recorded.indexOf(r) < 0; });
        if (pushRuns(gap, "gap")) { cur = null; pres = null; }
      }
      prevRel = v.release;
      if (v.text_captured === false) {
        if (pres) pres.releases.push(v.release);
        else { pres = { type: "presence", releases: [v.release] }; segs.push(pres); }
        cur = null;
        return;
      }
      pres = null;
      var n = normContent(v.content), h = versionHash(v);
      if (cur && cur.norm === n) {
        cur.releases.push(v.release); cur.versions.push(v); cur.lastRelease = v.release;
        if (cur.hashes.indexOf(h) < 0) cur.hashes.push(h);
      } else {
        var differs = !!lastContent && lastContent.norm !== n;
        cur = { type: "content", norm: n, releases: [v.release], versions: [v], hashes: [h], hash8: h,
                firstRelease: v.release, lastRelease: v.release, isInitial: !lastContent,
                isChange: differs && !seen[n], isRevert: differs && !!seen[n] };
        seen[n] = 1;
        segs.push(cur);
        lastContent = cur;
      }
    });
    var after = universe.filter(function (r) {
      return releaseKey(r) > lastKey && recorded.indexOf(r) < 0 && (unchecked.indexOf(r) >= 0 || dropIn.indexOf(r) >= 0);
    });
    pushRuns(after, "dropped");
    return segs;
  }

  // ------------------------------------------------------------------ Hilfen

  // Dateistämme (case_safe_names.py): Großschreibungsmaske = eine Hex-Ziffer je vier ASCII-Buchstaben,
  // erster Buchstabe höchstes Bit, 1 = groß (SWS_CanIf_00068 -> "f2", SWS_CANIF_00068 -> "ff").
  function caseMask(id) {
    var out = "", v = 0, k = 0, s = String(id);
    for (var i = 0; i < s.length; i++) {
      var ch = s.charAt(i);
      if (!/[A-Za-z]/.test(ch)) continue;
      v = v * 2 + (/[A-Z]/.test(ch) ? 1 : 0);
      if (++k === 4) { out += v.toString(16); v = 0; k = 0; }
    }
    if (k) out += (v << (4 - k)).toString(16);
    return out || "0";
  }
  function safeStem(id) { return String(id).replace(/[^A-Za-z0-9_.\-]/g, "_"); }
  function markedStem(id) { return safeStem(id) + "~" + caseMask(id); }
  // stems: abweichende Stämme aus dem Index (Kennung -> Stamm); sonst der schlichte Stamm
  function fileStem(id, stems) {
    return stems && Object.prototype.hasOwnProperty.call(stems, id) ? stems[id] : safeStem(id);
  }

  function figureHref(root, id, stems) {
    return root + "spec/" + (/^FIG-/.test(id) ? "figures/" : "snippets/") + encodeURIComponent(fileStem(id, stems)) + ".html";
  }

  function itemFile(id, stems) {
    return fileStem(id, stems) + ".json";
  }

  function recordFile(id, stems) {
    return fileStem(id, stems) + ".json";
  }

  function thumbUrl(root, sha) {
    return sha ? root + "assets/figures/" + sha.slice(0, 2) + "/" + sha + ".webp" : "";
  }

  // PDF-Pfad aus dem Bildkatalog (R22-11/AUTOSAR/AP/Datei.pdf) -> autosar.org
  function occurrencePdfUrl(pdf, page) {
    var parts = String(pdf || "").split("/");
    if (parts.length < 4) return "";
    var plat = parts[2] === "FOUNDATION" ? "FO" : parts[2];
    return "https://www.autosar.org/fileadmin/standards/" + encodeURIComponent(parts[0]) + "/" + plat + "/" +
      encodeURIComponent(parts[parts.length - 1]) + (page ? "#page=" + page : "");
  }

  // Dokumentname + Release über versions/snippets/pdf_catalog.json auflösen; sonst ""
  function catalogPdfUrl(cat, doc, rel, page) {
    if (!cat || !cat[rel] || !doc) return "";
    var clean = String(doc).replace(/\.pdf$/i, "");
    var norm = clean.replace(/^AUTOSAR_(AP_|CP_)?/i, "");
    var m = cat[rel][clean] || cat[rel][norm] || cat[rel][clean.toLowerCase()] || cat[rel][norm.toLowerCase()];
    if (!m) return "";
    return "https://www.autosar.org/fileadmin/standards/" + encodeURIComponent(rel) + "/" + m[1] + "/" +
      encodeURIComponent(m[0]) + (page ? "#page=" + page : "");
  }

  // ------------------------------------------------------------------ Laden (abbruchsicher)

  // Abbruch (AbortController, überholte Auswahl) ist kein Fehler; Netzfehler sind bei fetch ein TypeError
  // (Safari: „Load failed“, Chrome: „Failed to fetch“, Firefox: „NetworkError …“).
  function isAbortError(err) { return !!err && (err.name === "AbortError" || err.code === 20); }
  function isNetworkError(err) { return !!err && err.name === "TypeError" && !isAbortError(err); }
  function abortError() {
    try { return new DOMException("Aborted", "AbortError"); }
    catch (e) { var x = new Error("Aborted"); x.name = "AbortError"; return x; }
  }
  function waitFor(ms, signal) {
    return new Promise(function (resolve, reject) {
      if (signal && signal.aborted) { reject(abortError()); return; }
      var timer = setTimeout(resolve, ms);
      if (signal) signal.addEventListener("abort", function () { clearTimeout(timer); reject(abortError()); }, { once: true });
    });
  }
  /**
   * JSON laden: HTTP-Fehler als Error mit .status; ein Netzfehler wird nach opts.waitMs (400 ms) einmal
   * wiederholt; ein Abbruch über opts.signal endet als AbortError, ohne Wiederholung.
   */
  function loadJson(fetchImpl, url, opts) {
    opts = opts || {};
    var signal = opts.signal;
    function once() {
      return fetchImpl(url, signal ? { signal: signal } : undefined).then(function (r) {
        if (!r.ok) { var e = new Error(r.status + " " + url); e.status = r.status; throw e; }
        return r.json();
      });
    }
    return once().catch(function (err) {
      if (isAbortError(err) || (signal && signal.aborted)) throw (isAbortError(err) ? err : abortError());
      if (!isNetworkError(err) || opts.retries === 0) throw err;
      return waitFor(opts.waitMs == null ? 400 : opts.waitMs, signal).then(once);
    });
  }

  // ------------------------------------------------------------------ KI-Beschreibung (Markdown, sicher)

  // Einfache LaTeX-Schnipsel der Beschreibungen ($\rightarrow$ …) als Zeichen; Unbekanntes bleibt wörtlich.
  var MATH = { "\\rightarrow": "→", "\\to": "→", "\\leftarrow": "←", "\\gets": "←", "\\leftrightarrow": "↔",
    "\\longrightarrow": "⟶", "\\longleftarrow": "⟵", "\\Rightarrow": "⇒", "\\Leftarrow": "⇐", "\\Leftrightarrow": "⇔",
    "\\dashrightarrow": "⇢", "\\blacklozenge": "◆", "\\lozenge": "◇", "\\diamond": "◇", "\\blacktriangleright": "▶",
    "\\triangleright": "▷", "\\blacktriangleleft": "◀", "\\mu": "μ", "\\times": "×", "\\leq": "≤", "\\le": "≤",
    "\\geq": "≥", "\\ge": "≥", "\\neq": "≠", "\\ne": "≠", "\\cdot": "·", "\\ldots": "…", "\\dots": "…", "\\infty": "∞",
    "\\uparrow": "↑", "\\downarrow": "↓", "\\mapsto": "↦", "\\circ": "∘", "\\bullet": "•", "\\pm": "±", "\\approx": "≈",
    "\\in": "∈", "\\subset": "⊂", "\\cup": "∪", "\\cap": "∩", "\\forall": "∀", "\\exists": "∃", "\\emptyset": "∅" };
  function mathText(s) {
    return s.replace(/\$([^$\n]{1,60})\$/g, function (all, inner) {
      var out = inner.replace(/\\xrightarrow\{([^{}]*)\}/g, "–$1→")
        .replace(/\\(?:text|mathrm|mathit|mathbf|texttt)\{([^{}]*)\}/g, "$1")
        .replace(/\\[A-Za-z]+/g, function (cmd) { return Object.prototype.hasOwnProperty.call(MATH, cmd) ? MATH[cmd] : cmd; })
        .replace(/\\([_{}#%&$])/g, "$1").replace(/[{}]/g, "").replace(/\s+/g, " ").trim();
      return /\\[A-Za-z]/.test(out) ? all : out;
    });
  }
  function escHtml(str) {
    return String(str == null ? "" : str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  // Inline: Code, fett, kursiv. Alles wird zuerst maskiert; Links zeigen nur ihren Text (keine Adresse aus
  // der KI-Ausgabe, z. B. file:///…). Rohes HTML erscheint als Text.
  function mdInline(raw) {
    var codes = [];
    var s = String(raw == null ? "" : raw).replace(/[\u0001\u0002]/g, "");
    s = s.replace(/\[([^\]\n]+)\]\((?:[^()\s]|\([^()\s]*\))+\)/g, "$1");
    s = s.replace(/`([^`\n]+)`/g, function (all, code) { codes.push(code); return "\u0001" + (codes.length - 1) + "\u0002"; });
    s = escHtml(mathText(s));
    s = s.replace(/\*\*(?=\S)([^*\n]*?\S)\*\*/g, "<strong>$1</strong>").replace(/__(?=\S)([^_\n]*?\S)__/g, "<strong>$1</strong>");
    s = s.replace(/(^|[^*\w])\*(?=[^\s*])([^*\n]*?[^\s*])\*(?![*\w])/g, "$1<em>$2</em>");
    return s.replace(/\u0001(\d+)\u0002/g, function (all, k) { return "<code>" + escHtml(codes[+k]) + "</code>"; });
  }
  function mdCells(line) {
    var t = line.trim().replace(/^\|/, "").replace(/\|$/, "");
    return t.split("|").map(function (c) { return c.trim(); });
  }
  /**
   * Markdown der KI-Beschreibungen -> HTML ohne rohes HTML: Überschriften (h4/h5), Absätze, verschachtelte
   * Listen, Codeblöcke, Tabellen, Zitate, Trennlinien. Jeder Text wird maskiert.
   */
  function renderMarkdown(md) {
    var lines = String(md == null ? "" : md).replace(/\r\n?/g, "\n").replace(/\t/g, "    ").split("\n");
    var out = [], para = [], lists = [], fence = null, quote = [];
    function flushPara() { if (para.length) { out.push("<p>" + mdInline(para.join(" ")) + "</p>"); para = []; } }
    function flushQuote() { if (quote.length) { out.push("<blockquote><p>" + mdInline(quote.join(" ")) + "</p></blockquote>"); quote = []; } }
    function closeLists(minIndent) {
      while (lists.length && lists[lists.length - 1].indent >= minIndent) out.push("</li></" + lists.pop().type + ">");
    }
    function closeAll() { flushPara(); flushQuote(); closeLists(0); }
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      var fm = /^(\s*)(```|~~~)/.exec(line);
      if (fence) {
        if (fm && fm[2] === fence.mark) { out.push("<pre><code>" + escHtml(fence.body.join("\n")) + "</code></pre>"); fence = null; }
        else fence.body.push(line.slice(Math.min(fence.indent, (/^\s*/.exec(line) || [""])[0].length)));
        continue;
      }
      if (fm) {
        flushPara(); flushQuote();
        closeLists(fm[1].length);   // ein Codeblock gehört zu dem Listenpunkt, unter dem er eingerückt ist
        fence = { mark: fm[2], indent: fm[1].length, body: [] };
        continue;
      }
      if (!line.trim()) { flushPara(); flushQuote(); continue; }
      var h = /^\s*(#{1,6})\s+(.*?)\s*#*\s*$/.exec(line);
      if (h) { closeAll(); out.push(h[1].length <= 3 ? "<h4>" + mdInline(h[2]) + "</h4>" : "<h5>" + mdInline(h[2]) + "</h5>"); continue; }
      if (/^\s*([-*_])(\s*\1){2,}\s*$/.test(line)) { closeAll(); out.push("<hr>"); continue; }
      if (/^\s*\|.*\|\s*$/.test(line)) {
        closeAll();
        var rows = [];
        while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) rows.push(lines[i++]);
        i--;
        var head = rows.length > 1 && /^\s*\|?\s*:?-{2,}/.test(rows[1]) ? mdCells(rows[0]) : null;
        var body = rows.slice(head ? 2 : 0);
        out.push('<div class="ve-md-tw"><table>' +
          (head ? "<thead><tr>" + head.map(function (c) { return "<th>" + mdInline(c) + "</th>"; }).join("") + "</tr></thead>" : "") +
          "<tbody>" + body.map(function (r) {
            return "<tr>" + mdCells(r).map(function (c) { return "<td>" + mdInline(c) + "</td>"; }).join("") + "</tr>";
          }).join("") + "</tbody></table></div>");
        continue;
      }
      var q = /^\s*>\s?(.*)$/.exec(line);
      if (q) { flushPara(); closeLists(0); quote.push(q[1]); continue; }
      var li = /^(\s*)([-*+]|\d{1,3}[.)])\s+(.*)$/.exec(line);
      if (li) {
        flushPara(); flushQuote();
        var indent = li[1].length, type = /^\d/.test(li[2]) ? "ol" : "ul";
        closeLists(indent + 1);
        var top = lists[lists.length - 1];
        if (top && top.indent === indent && top.type !== type) { closeLists(indent); top = lists[lists.length - 1]; }
        if (top && top.indent === indent) out.push("</li><li>" + mdInline(li[3]));
        else { out.push("<" + type + "><li>" + mdInline(li[3])); lists.push({ type: type, indent: indent }); }
        continue;
      }
      var ind = (/^\s*/.exec(line) || [""])[0].length;
      if (lists.length && ind > 0 && !para.length) { out.push(" " + mdInline(line.trim())); continue; }
      if (lists.length && ind === 0) closeLists(0);
      flushQuote();
      para.push(line.trim());
    }
    if (fence) out.push("<pre><code>" + escHtml(fence.body.join("\n")) + "</code></pre>");
    closeAll();
    return out.join("");
  }

  return {
    STATUS: STATUS, HAS: HAS, PARAMS: PARAMS, emptyState: emptyState, parseState: parseState,
    serializeState: serializeState, activeCount: activeCount, decodeElements: decodeElements,
    decodeCatalog: decodeCatalog, elementGroups: elementGroups, facetFilter: facetFilter,
    filterElements: filterElements, decodeItems: decodeItems, filterItems: filterItems,
    figureHref: figureHref, itemFile: itemFile, recordFile: recordFile, caseMask: caseMask, safeStem: safeStem,
    markedStem: markedStem, fileStem: fileStem, thumbUrl: thumbUrl, occurrencePdfUrl: occurrencePdfUrl,
    catalogPdfUrl: catalogPdfUrl, textMatcher: textMatcher, normContent: normContent, releaseKey: releaseKey,
    sortVersions: sortVersions, buildTimeline: buildTimeline, versionHash: versionHash,
    decodeEntities: decodeEntities, decodeFully: decodeFully, citedIds: citedIds, linkifyIds: linkifyIds, resolveId: resolveId,
    UNIVERSES: UNIVERSES,
    isAbortError: isAbortError, isNetworkError: isNetworkError, loadJson: loadJson, renderMarkdown: renderMarkdown,
    mdInline: mdInline
  };
});

/* ======================================================================== UI */
(function () {
  "use strict";
  if (typeof document === "undefined") return;
  var C = window.VersionsExplorerCore;
  var app = document.getElementById("ve-app");
  if (!app || !C) return;

  var LANGS = ["de", "en", "es", "pt", "fr", "ru", "ar", "hi", "ko", "zh", "nl"];
  var LANG = (function () {
    var m = window.location.pathname.match(/\/(de|en|es|pt|fr|ru|ar|hi|ko|zh|nl)\//);
    if (m) return m[1];
    var h = (document.documentElement.getAttribute("lang") || "de").slice(0, 2);
    return LANGS.indexOf(h) >= 0 ? h : "de";
  })();
  var I18N = window.VE_I18N || {};
  var T = I18N[LANG] || I18N.en || {};
  var DE = I18N.de || {};
  function t(key, vars) {
    var s = T[key] != null ? T[key] : (DE[key] != null ? DE[key] : key);
    if (vars) Object.keys(vars).forEach(function (k) { s = s.split("{" + k + "}").join(vars[k]); });
    return s;
  }
  function num(n) { try { return Number(n).toLocaleString(LANG); } catch (e) { return String(n); } }
  function esc(str) {
    return String(str == null ? "" : str).replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function getRootPrefix() {
    var link = document.querySelector('link[href*="style.css"]');
    if (link) return link.getAttribute("href").replace("style.css", "") || "../";
    return "../";
  }
  var ROOT = getRootPrefix();
  var narrowMQ = window.matchMedia ? window.matchMedia("(max-width: 899px)") : { matches: false };
  var wideMQ = window.matchMedia ? window.matchMedia("(min-width: 1180px)") : { matches: true };

  var state = C.parseState(window.location.search);
  var data = { el: null, fig: null, snip: null, res: { el: null, fig: null, snip: null }, pdfCat: undefined };
  var ui = {};
  var ROW_H = { el: 58, fig: 62, snip: 62 };
  var PAGE = { fig: 24, snip: 30 };

  // ------------------------------------------------------------------ Gerüst
  function kindLabel(k) { return t("k_" + String(k).replace(/ /g, "_")); }
  function platLabel(p) { return t("plat_" + p); }
  function valueLabel(tab, key, v) {
    if (key === "kind") return kindLabel(v);
    if (key === "plat") return platLabel(v);
    if (key === "st") return t("st_" + v);
    if (key === "has") return t("has_" + v);
    if (key === "doc") return v === "other" ? t("doc_other") : (v || "–");
    if (key === "role") return t("role_" + v);
    if (key === "multi") return t("f_multi");
    if (key === "first") return t("rel_first") + " " + v;
    if (key === "last") return t("rel_last") + " " + v;
    if (key === "chg") return t("rel_chg") + " " + v;
    return v;
  }
  function facetTitle(key) {
    return t({ kind: "f_kind", plat: "f_plat", st: "f_status", has: "f_has", doc: "f_doc", mod: "f_mod",
               cl: "f_cl", first: "f_rel", last: "f_rel", chg: "f_rel", role: "f_role", multi: "f_has" }[key] || key);
  }

  function build() {
    var tabs = [["el", t("tab_el")], ["fig", t("tab_fig")], ["snip", t("tab_snip")]];
    var html = '<div class="ve-tabs" role="tablist" aria-label="' + esc(t("tabs_label")) + '">';
    tabs.forEach(function (x) {
      html += '<button type="button" role="tab" class="ve-tab" id="ve-tab-' + x[0] + '" data-tab="' + x[0] +
        '" aria-controls="ve-panel-' + x[0] + '"><span>' + esc(x[1]) + '</span> <span class="ve-tab-count" data-count="' +
        x[0] + '"></span></button>';
    });
    html += "</div>";
    tabs.forEach(function (x) {
      var tab = x[0];
      html += '<section class="ve-panel" id="ve-panel-' + tab + '" role="tabpanel" aria-labelledby="ve-tab-' + tab + '" hidden>' +
        '<div class="ve-toolbar">' +
        '<div class="ve-search"><span class="ve-search-icon" aria-hidden="true">⌕</span>' +
        '<input type="search" class="ve-input" autocomplete="off" spellcheck="false" data-role="q" aria-label="' +
        esc(t("ph_" + tab)) + '" placeholder="' + esc(t("ph_" + tab)) + '"></div>' +
        '<button type="button" class="ve-btn ve-filter-toggle" data-role="ftoggle" aria-expanded="false" aria-controls="ve-facets-' +
        tab + '">' + esc(t("filters")) + ' <span class="ve-badge" data-role="fbadge"></span></button>' +
        '<button type="button" class="ve-btn ve-reset" data-role="reset">' + esc(t("reset")) + "</button>" +
        '<button type="button" class="ve-btn ve-collapse" data-role="collapse" aria-pressed="false" aria-controls="ve-panel-' + tab + '">' +
        esc(t("cat_hide")) + "</button>" +
        "</div>" +
        '<div class="ve-chiprow" data-role="chips"></div>' +
        '<div class="ve-notice" data-role="notice" hidden></div>' +
        '<div class="ve-md" data-role="md">' +
        '<aside class="ve-facets" id="ve-facets-' + tab + '" data-role="facets" aria-label="' + esc(t("filters")) + '">' +
        '<div class="ve-facets-head"><strong>' + esc(t("filters")) + '</strong><button type="button" class="ve-btn ve-facets-close" data-role="fclose">' +
        esc(t("close")) + '</button></div><div class="ve-facets-body" data-role="fbody"></div></aside>' +
        '<div class="ve-listpane" data-role="listpane"><div class="ve-listhead"><span data-role="count">' +
        esc(t("loading")) + '</span><span class="ve-kbd-hint">' + esc(t("kbd_hint")) + '</span></div>' +
        '<div class="ve-vlist" role="listbox" tabindex="0" data-role="list" aria-label="' + esc(t("list_" + tab)) +
        '"><div class="ve-vspace" data-role="space"></div></div></div>' +
        '<section class="ve-viewer" data-role="viewer" tabindex="-1" aria-label="' + esc(t("viewer_" + tab)) + '">' +
        '<div class="ve-viewer-top"><button type="button" class="ve-btn ve-back" data-role="back">' + esc(t("back")) +
        '</button></div><div class="ve-mismatch" data-role="mismatch" role="status" hidden><strong>' + esc(t("mismatch")) +
        "</strong> <span>" + esc(t("mismatch_text")) + '</span><span class="ve-mismatch-acts">' +
        '<button type="button" class="ve-btn" data-role="mmreset">' + esc(t("reset")) + "</button>" +
        '<button type="button" class="ve-btn" data-role="mmclose">' + esc(t("close_viewer")) + "</button></span></div>" +
        '<div class="ve-viewer-body" data-role="vbody"><div class="ve-placeholder">' +
        esc(t("pick_" + tab)) + "</div></div></section>" +
        "</div></section>";
    });
    app.innerHTML = html;
    tabs.forEach(function (x) {
      var tab = x[0];
      var panel = document.getElementById("ve-panel-" + tab);
      var r = { panel: panel };
      panel.querySelectorAll("[data-role]").forEach(function (el) { r[el.getAttribute("data-role")] = el; });
      r.vlist = new VList(tab, r.list, r.space, ROW_H[tab]);
      ui[tab] = r;
      wirePanel(tab, r);
    });
    app.querySelectorAll(".ve-tab").forEach(function (b) {
      b.addEventListener("click", function () { switchTab(b.getAttribute("data-tab"), true); });
      b.addEventListener("keydown", function (e) {
        var order = ["el", "fig", "snip"], k = order.indexOf(b.getAttribute("data-tab"));
        if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
          e.preventDefault();
          var n = order[(k + (e.key === "ArrowRight" ? 1 : 2)) % 3];
          switchTab(n, true);
          document.getElementById("ve-tab-" + n).focus();
        }
      });
    });
  }

  // ------------------------------------------------------------------ Virtuelle Liste
  function VList(tab, el, space, rowH) {
    this.tab = tab; this.el = el; this.space = space; this.rowH = rowH;
    this.items = []; this.active = -1; this.openKey = null; this.raf = 0; this.version = 0; this.lastKey = "";
    var self = this;
    el.addEventListener("scroll", function () { self.schedule(); }, { passive: true });
    el.addEventListener("click", function (e) {
      var row = e.target.closest("[data-k]");
      if (!row) return;
      var k = +row.getAttribute("data-k");
      self.setActive(k, false);
      openFromList(self.tab, k, true);
    });
    el.addEventListener("keydown", function (e) {
      var n = self.items.length;
      if (!n) return;
      var page = Math.max(1, Math.floor(el.clientHeight / self.rowH) - 1);
      var k = self.active;
      if (e.key === "ArrowDown") k = Math.min(n - 1, k + 1);
      else if (e.key === "ArrowUp") k = Math.max(0, k - 1);
      else if (e.key === "PageDown") k = Math.min(n - 1, k + page);
      else if (e.key === "PageUp") k = Math.max(0, k - page);
      else if (e.key === "Home") k = 0;
      else if (e.key === "End") k = n - 1;
      else if (e.key === "Enter") {
        e.preventDefault();
        if (self.active >= 0) openFromList(self.tab, self.active, true);
        return;
      } else return;
      e.preventDefault();
      self.setActive(k < 0 ? 0 : k, true);
    });
    el.addEventListener("focus", function () {
      if (self.active < 0 && self.items.length) self.setActive(0, true);
    });
  }
  VList.prototype.schedule = function () {
    var self = this;
    if (this.raf) return;
    this.raf = requestAnimationFrame(function () { self.raf = 0; self.render(); });
  };
  VList.prototype.setItems = function (items, keyOf) {
    this.items = items; this.keyOf = keyOf;
    this.version = (this.version || 0) + 1;
    this.space.style.height = (items.length * this.rowH) + "px";
    if (this.active >= items.length) this.active = items.length - 1;
    if (this.openKey != null) {
      var k = this.indexOfKey(this.openKey);
      if (k >= 0) this.active = k;
    }
    if (!items.length) this.active = -1;
    this.render();
  };
  VList.prototype.indexOfKey = function (key) {
    for (var k = 0; k < this.items.length; k++) if (this.keyOf(this.items[k]) === key) return k;
    return -1;
  };
  VList.prototype.ensureVisible = function (k) {
    var top = k * this.rowH, el = this.el;
    if (top < el.scrollTop) el.scrollTop = top;
    else if (top + this.rowH > el.scrollTop + el.clientHeight) el.scrollTop = top + this.rowH - el.clientHeight;
  };
  VList.prototype.setActive = function (k, scroll) {
    this.active = k;
    if (scroll) this.ensureVisible(k);
    this.render();
  };
  VList.prototype.render = function () {
    var el = this.el, n = this.items.length, h = this.rowH;
    var start = Math.max(0, Math.floor(el.scrollTop / h) - 8);
    var end = Math.min(n, Math.ceil((el.scrollTop + (el.clientHeight || 600)) / h) + 8);
    // Zeilen nur neu aufbauen, wenn sich Fenster, Daten oder geöffnetes Element ändern; sonst
    // bleiben die Knoten erhalten (ein Klick, der den Fokus setzt, trifft weiter dieselbe Zeile)
    var key = start + ":" + end + ":" + this.version + ":" + this.openKey;
    if (key !== this.lastKey) {
      var out = [];
      for (var k = start; k < end; k++) {
        var it = this.items[k];
        var open = this.keyOf(it) === this.openKey;
        out.push('<div class="ve-row' + (open ? " is-open" : "") + '" role="option" id="ve-opt-' + this.tab + "-" + k +
          '" data-k="' + k + '" aria-selected="' + (open ? "true" : "false") + '" aria-setsize="' + n + '" aria-posinset="' + (k + 1) +
          '" style="top:' + (k * h) + "px;height:" + h + 'px">' + rowHtml(this.tab, it) + "</div>");
      }
      this.space.innerHTML = out.join("");
      this.lastKey = key;
    }
    var prev = this.space.querySelector(".ve-row.is-active");
    if (prev && +prev.getAttribute("data-k") !== this.active) prev.classList.remove("is-active");
    var cur = this.active >= 0 ? this.space.querySelector('[data-k="' + this.active + '"]') : null;
    if (cur) {
      cur.classList.add("is-active");
      el.setAttribute("aria-activedescendant", cur.id);
    } else el.removeAttribute("aria-activedescendant");
  };

  function rowHtml(tab, i) {
    if (tab === "el") {
      var E = data.el;
      if (i === -1) return "";
      var st = E.st[i];
      var badges = "";
      if (st & 2) badges += '<span class="ve-mini ve-mini-chg" title="' + esc(t("st_changed")) + '">' + esc(t("st_changed")) + "</span>";
      if (st & 4) badges += '<span class="ve-mini ve-mini-drop" title="' + esc(t("st_removed")) + '">' + esc(t("st_removed")) + "</span>";
      if (st & 1) badges += '<span class="ve-mini ve-mini-new">' + esc(t("st_new")) + "</span>";
      if (E.ref[i]) badges += '<span class="ve-mini ve-mini-ref" title="' + esc(t("ref_link_title")) + '">' + esc(t("k_cited")) + "</span>";
      var plat = E.dict.plat[E.plat[i]] || "";
      var rels = E.first[i] >= 0 ? E.dict.rel[E.first[i]] + (E.last[i] !== E.first[i] ? "–" + E.dict.rel[E.last[i]] : "") : "";
      var meta = [];
      if (E.full) meta.push(esc(kindLabel(E.dict.kind[E.kind[i]])));
      if (E.names[i]) meta.push('<span class="ve-row-name">' + esc(E.names[i]) + "</span>");
      if (rels) meta.push(esc(rels));
      if (E.fig[i]) meta.push('<span title="' + esc(t("v_fig")) + '">▣ ' + E.fig[i] + "</span>");
      if (E.snip[i]) meta.push('<span title="' + esc(t("v_snip")) + '">❝ ' + E.snip[i] + "</span>");
      if (E.cit[i]) meta.push('<span title="' + esc(t("has_cit")) + '">⌕ ' + E.cit[i] + "</span>");
      return '<div class="ve-row-top"><span class="ve-row-id">' + esc(E.ids[i]) + '</span><span class="ve-row-badges">' + badges +
        '<span class="ve-mini ve-plat-' + esc(plat) + '">' + esc(plat) + "</span></span></div>" +
        '<div class="ve-row-meta">' + meta.join('<span aria-hidden="true">·</span>') + "</div>";
    }
    var D = data[tab];
    var title = D.title[i] || D.ids[i];
    var sub = [esc(D.doc[i] || ""), D.page[i] ? esc(t("page_n", { p: D.page[i] })) : "",
               esc(t("n_elements", { n: (D.targets[i] || []).length }))];
    if (tab === "fig" && D.nser[i] > 1) sub.push(esc(t("series_n", { n: D.nser[i] })));
    return '<div class="ve-row-top"><span class="ve-row-title">' + esc(title) + '</span></div>' +
      '<div class="ve-row-meta">' + sub.filter(Boolean).join('<span aria-hidden="true">·</span>') + "</div>";
  }

  // ------------------------------------------------------------------ Panel-Verdrahtung
  function wirePanel(tab, r) {
    var timer = 0;
    r.q.addEventListener("input", function () {
      state[tab].q = r.q.value;
      clearTimeout(timer);
      timer = setTimeout(function () { refresh(tab); commit(false); }, 120);
    });
    r.q.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); r.list.focus(); }
      if (e.key === "Enter") {
        e.preventDefault();
        if (r.vlist.items.length) { r.vlist.setActive(0, true); openFromList(tab, 0, true); }
      }
    });
    r.ftoggle.addEventListener("click", function () { setFacetsOpen(tab, !r.panel.classList.contains("facets-open")); });
    r.fclose.addEventListener("click", function () { setFacetsOpen(tab, false); r.ftoggle.focus(); });
    r.reset.addEventListener("click", function () {
      var keep = tab === "el" ? null : state[tab].id;
      var fresh = C.emptyState()[tab];
      if (keep) fresh.id = keep;
      state[tab] = fresh;
      r.q.value = "";
      refresh(tab);
      commit(true);
    });
    r.back.addEventListener("click", function () { closeDetail(tab); });
    r.mmreset.addEventListener("click", function () { r.reset.click(); });
    r.mmclose.addEventListener("click", function () {
      if (tab === "el") state.id = ""; else state[tab].id = "";
      commit(true);
      setMismatch(tab, false);
      ui[tab].vlist.openKey = null;
      ui[tab].vlist.render();
      syncViewer(tab);
    });
    r.collapse.addEventListener("click", function () { setCollapsed(tab, !r.panel.classList.contains("catalog-collapsed")); });
    r.fbody.addEventListener("click", function (e) {
      var b = e.target.closest("[data-fkey]");
      if (b) {
        toggleValue(tab, b.getAttribute("data-fkey"), b.getAttribute("data-fval"));
        return;
      }
      var more = e.target.closest("[data-more]");
      if (more) {
        r.fbody.classList.toggle("show-all-" + more.getAttribute("data-more"));
        refreshFacets(tab);
      }
    });
    r.fbody.addEventListener("change", function (e) {
      var s = e.target.closest("select[data-fsel]");
      if (!s) return;
      state[tab][s.getAttribute("data-fsel")] = s.value;
      refresh(tab);
      commit(true);
    });
    r.fbody.addEventListener("input", function (e) {
      var f = e.target.closest("input[data-modfilter]");
      if (!f) return;
      r.modFilter = f.value;
      refreshFacets(tab, true);
    });
    r.chips.addEventListener("click", function (e) {
      var b = e.target.closest("[data-chip]");
      if (!b) return;
      var key = b.getAttribute("data-chip"), val = b.getAttribute("data-val");
      if (key === "*") {
        r.reset.click();
        return;
      }
      if (key === "q") {
        state[tab].q = "";
        r.q.value = "";
        refresh(tab);
        commit(true);
        r.q.focus();
        return;
      }
      toggleValue(tab, key, val);
    });
    r.vbody.addEventListener("click", function (e) { onViewerClick(tab, e); });
  }

  function setFacetsOpen(tab, open) {
    var r = ui[tab];
    r.panel.classList.toggle("facets-open", open);
    r.ftoggle.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) {
      var first = r.fbody.querySelector("button, input, select");
      if (first && !wideMQ.matches) first.focus();
    }
  }

  // Katalog (Facetten + Liste) jederzeit ein-/ausklappen; der Viewer nimmt dann die volle Breite ein
  function setCollapsed(tab, on) {
    var r = ui[tab];
    r.panel.classList.toggle("catalog-collapsed", on);
    r.collapse.setAttribute("aria-pressed", on ? "true" : "false");
    r.collapse.textContent = t(on ? "cat_show" : "cat_hide");
    if (on) setFacetsOpen(tab, false);
    else r.vlist.render();
    layout();
  }

  function toggleValue(tab, key, val) {
    var cur = state[tab][key];
    if (Array.isArray(cur)) {
      var k = cur.indexOf(val);
      if (k >= 0) cur.splice(k, 1); else cur.push(val);
    } else {
      state[tab][key] = cur === val ? "" : val;
    }
    refresh(tab);
    commit(true);
  }

  // ------------------------------------------------------------------ Verlauf / URL
  function commit(push, extra) {
    var qs = C.serializeState(state);
    var url = window.location.pathname + qs + window.location.hash;
    if (qs === window.location.search) return;
    var st = { ve: 1, detail: !!(extra && extra.detail), fromList: !!(extra && extra.fromList) };
    try {
      if (push) window.history.pushState(st, "", url);
      else window.history.replaceState(window.history.state || st, "", url);
    } catch (e) { /* file:// u. ä. */ }
  }

  window.addEventListener("popstate", function () {
    state = C.parseState(window.location.search);
    applyState();
  });

  function applyState() {
    ["el", "fig", "snip"].forEach(function (tab) {
      if (ui[tab].q.value !== state[tab].q) ui[tab].q.value = state[tab].q || "";
    });
    switchTab(state.tab, false);
    ["el", "fig", "snip"].forEach(function (tab) { if (data[tab]) refresh(tab); });
    syncViewer(state.tab);
  }

  function selectedKey(tab) { return tab === "el" ? state.id : state[tab].id; }

  function switchTab(tab, push) {
    if (["el", "fig", "snip"].indexOf(tab) < 0) tab = "el";
    var changed = state.tab !== tab;
    state.tab = tab;
    app.querySelectorAll(".ve-tab").forEach(function (b) {
      var on = b.getAttribute("data-tab") === tab;
      b.setAttribute("aria-selected", on ? "true" : "false");
      b.tabIndex = on ? 0 : -1;
      b.classList.toggle("is-active", on);
    });
    ["el", "fig", "snip"].forEach(function (x) { ui[x].panel.hidden = x !== tab; });
    if (push && changed) commit(true);
    ensureLoaded(tab).then(function () {
      refresh(tab);
      syncViewer(tab);
      layout();
    });
  }

  // ------------------------------------------------------------------ Laden
  var loading = {};
  // Abweichende Dateistämme aus dem geladenen Index (rec: versions/data, item: items/ und Belegseiten)
  function stems(kind) { return (data.el && data.el.stems && data.el.stems[kind]) || null; }
  // Abbruchsicher: überholte Ladevorgänge enden als AbortError (kein Fehlerhinweis), ein Netzfehler wird
  // einmal wiederholt (C.loadJson). Je Bereich gibt es höchstens einen laufenden Detail-Ladevorgang.
  function fetchJson(url, signal) {
    return C.loadJson(function (u, o) { return fetch(u, o); }, url, { signal: signal });
  }
  var ctrl = { el: null, fig: null, snip: null };
  function newSignal(tab) {
    if (ctrl[tab]) { try { ctrl[tab].abort(); } catch (e) { /* ignore */ } }
    ctrl[tab] = typeof AbortController === "function" ? new AbortController() : null;
    return ctrl[tab] ? ctrl[tab].signal : undefined;
  }
  // Beim Verlassen der Seite (Safari bricht laufende Abrufe mit „Load failed“ ab) keinen Fehler zeigen;
  // kommt die Seite aus dem Back-Forward-Cache zurück, unvollständige Details neu laden.
  var pageHidden = false;
  window.addEventListener("pagehide", function () { pageHidden = true; });
  window.addEventListener("pageshow", function (e) {
    pageHidden = false;
    if (!e.persisted) return;
    ["el", "fig", "snip"].forEach(function (tab) {
      var key = selectedKey(tab);
      if (!key || (tab !== "el" && !data[tab])) return;
      var done = tab === "el" ? shown.el === key + "|" + state.view : shown[tab] === key;
      if (!done) syncViewer(tab, false);
    });
  });
  function errorHtml(err) {
    var msg = C.isNetworkError(err) ? t("err_net") : t("load_error", { msg: (err && err.message) || "" });
    return '<div class="ve-error" role="alert"><p>' + esc(msg) + '</p><button type="button" class="ve-btn" data-act="retry">' +
      esc(t("retry")) + "</button></div>";
  }
  var figConfigured = false;
  function figObserve(container) {
    var F = window.FigureImages;
    if (!F || !container) return;
    if (!figConfigured) { F.configure({ text: function (k) { return t("fi_" + k); } }); figConfigured = true; }
    F.observe(container);
  }

  function ensureLoaded(tab) {
    if (data[tab]) return Promise.resolve();
    if (loading[tab]) return loading[tab];
    if (tab === "el") {
      loading.el = fetchJson(ROOT + "versions/explorer/elements.json")
        .then(function (raw) { data.el = C.decodeElements(raw); })
        .catch(function () {
          return fetchJson(ROOT + "versions/catalog.json")
            .catch(function () { return fetchJson("/api/versions?limit=50000"); })
            .then(function (cat) {
              data.el = C.decodeCatalog(cat.items || cat || []);
              showNotice("el", t("index_missing"));
            });
        })
        .then(function () { updateTabCounts(); })
        .catch(function (err) {
          loading.el = null;   // späterer Bereichswechsel versucht es erneut
          if (!pageHidden) ui.el.count.textContent = C.isNetworkError(err) ? t("err_net") : t("load_error", { msg: err.message });
        });
      return loading.el;
    }
    loading[tab] = ensureLoaded("el").then(function () {
      return fetchJson(ROOT + "versions/explorer/" + (tab === "fig" ? "figures" : "snippets") + ".json");
    }).then(function (raw) {
      data[tab] = C.decodeItems(raw, data.el);
      updateTabCounts();
    }).catch(function () {
      data[tab] = null;
      ui[tab].count.textContent = t("items_missing");
      showNotice(tab, t("items_missing"));
      loading[tab] = null;
    });
    return loading[tab];
  }

  function showNotice(tab, msg) {
    var n = ui[tab].notice;
    n.textContent = msg;
    n.hidden = false;
  }

  function updateTabCounts() {
    var c = (data.el && data.el.counts) || {};
    var vals = { el: data.el ? data.el.n : null, fig: data.fig ? data.fig.n : c.figures, snip: data.snip ? data.snip.n : c.snippets };
    app.querySelectorAll("[data-count]").forEach(function (s) {
      var v = vals[s.getAttribute("data-count")];
      s.textContent = v != null ? num(v) : "";
    });
  }

  function ensurePdfCatalog() {
    if (data.pdfCat !== undefined) return Promise.resolve(data.pdfCat);
    data.pdfCat = null;
    return fetchJson(ROOT + "versions/snippets/pdf_catalog.json")
      .then(function (c) { data.pdfCat = c; return c; })
      .catch(function () { data.pdfCat = null; return null; });
  }

  function fillPdfLinks(container) {
    ensurePdfCatalog().then(function (cat) {
      container.querySelectorAll("a[data-pdf-doc]").forEach(function (a) {
        var rels = (a.getAttribute("data-pdf-rel") || "").split(" ").filter(Boolean);
        var url = "";
        for (var k = rels.length - 1; k >= 0 && !url; k--) {
          url = C.catalogPdfUrl(cat, a.getAttribute("data-pdf-doc"), rels[k], a.getAttribute("data-pdf-page"));
        }
        if (url) { a.href = url; a.hidden = false; }
      });
    });
  }

  // ------------------------------------------------------------------ Filtern & Darstellen
  function refresh(tab, keepFacetFocus) {
    var D = data[tab];
    var r = ui[tab];
    if (!D) return;
    var sel = state[tab];
    var res = tab === "el" ? C.filterElements(D, sel) : C.filterItems(D, tab, sel);
    var list = res.matches;
    // Die Liste enthält nur Treffer. Passt das geöffnete Element nicht (mehr) zu den Filtern,
    // bleibt der Viewer offen und sagt das (targetId wird nie als Listenzeile eingeschoben).
    var targetId = selectedKey(tab);
    var mismatch = false;
    if (targetId && D.byId.has(targetId)) mismatch = list.indexOf(D.byId.get(targetId)) < 0;
    setMismatch(tab, mismatch);
    data.res[tab] = res;
    var openChanged = r.vlist.openKey !== (targetId || null);
    r.vlist.openKey = targetId || null;
    r.vlist.setItems(list, function (i) { return D.ids[i]; });
    if (targetId && openChanged && !mismatch && r.vlist.active >= 0) r.vlist.ensureVisible(r.vlist.active);
    var total = D.n;
    r.count.textContent = t("results", { n: num(res.matches.length), total: num(total) });
    var ac = C.activeCount(state, tab);
    r.fbadge.textContent = ac ? String(ac) : "";
    r.reset.disabled = !ac && !sel.q;
    if (!list.length) {
      r.space.innerHTML = '<div class="ve-empty">' + esc(t("no_results")) + "</div>";
    }
    refreshFacets(tab, keepFacetFocus);
    refreshChips(tab);
    if (tab === state.tab) layout();
  }

  function setMismatch(tab, on) {
    var r = ui[tab];
    r.panel.classList.toggle("is-mismatch", on);
    r.mismatch.hidden = !on;
  }

  function chipButton(key, k, label, count, on) {
    return '<button type="button" class="ve-fchip' + (on ? " is-on" : "") + '" data-fkey="' + key + '" data-fval="' + esc(k) +
      '" aria-pressed="' + (on ? "true" : "false") + '"' + (!count && !on ? " disabled" : "") + ">" +
      '<span class="ve-fchip-l">' + esc(label) + '</span><span class="ve-fchip-n">' + num(count || 0) + "</span></button>";
  }

  function facetChips(tab, key, values, counts, opts) {
    opts = opts || {};
    var sel = state[tab][key];
    var selArr = Array.isArray(sel) ? sel : (sel ? [sel] : []);
    var order = values.map(function (v, k) { return k; });
    if (opts.sortByCount) order.sort(function (a, b) { return (counts[b] || 0) - (counts[a] || 0) || String(values[a]).localeCompare(String(values[b])); });
    var html = "", shown = 0, hidden = 0;
    var filt = (opts.filter || "").toLowerCase();
    order.forEach(function (k) {
      var v = values[k];
      var on = selArr.indexOf(v) >= 0;
      var c = counts[k] || 0;
      if (filt && String(v).toLowerCase().indexOf(filt) < 0 && !on) return;
      if (!c && !on && opts.hideEmpty) return;
      if (opts.limit && shown >= opts.limit && !on) { hidden++; return; }
      shown++;
      html += chipButton(key, v, opts.label ? opts.label(v) : valueLabel(tab, key, v), c, on);
    });
    if (opts.limit && (hidden || opts.expanded)) {
      html += '<button type="button" class="ve-more" data-more="' + key + '">' +
        esc(opts.expanded ? t("show_less") : t("show_all", { n: num(shown + hidden) })) + "</button>";
    }
    return html;
  }

  function group(title, inner, extraCls) {
    return '<div class="ve-fgroup' + (extraCls ? " " + extraCls : "") + '"><div class="ve-fhead">' + esc(title) +
      '</div><div class="ve-fvals">' + inner + "</div></div>";
  }

  function releaseSelect(tab, key, label, counts) {
    var D = data.el;
    var cur = state[tab][key];
    var html = '<label class="ve-fsel"><span>' + esc(label) + '</span><select data-fsel="' + key + '"><option value="">' +
      esc(t("any")) + "</option>";
    D.dict.rel.forEach(function (rel, k) {
      var c = counts[k] || 0;
      if (!c && cur !== rel) return;
      html += '<option value="' + esc(rel) + '"' + (cur === rel ? " selected" : "") + ">" + esc(rel) + " (" + num(c) + ")</option>";
    });
    return html + "</select></label>";
  }

  function docSelect(tab, D, counts) {
    var cur = state[tab].doc;
    var html = '<label class="ve-fsel"><span>' + esc(t("f_docsel")) + '</span><select data-fsel="doc"><option value="">' +
      esc(t("all_docs")) + "</option>";
    D.docOrder.forEach(function (k) {
      var d = D.dict.doc[k], c = counts[k] || 0;
      if (!c && cur !== d) return;
      html += '<option value="' + esc(d) + '"' + (cur === d ? " selected" : "") + ">" + esc(d || "–") + " (" + num(c) + ")</option>";
    });
    return html + "</select></label>";
  }

  // Module nach Universum gruppiert (Classic, Adaptive, Foundation, übergreifend). Ohne Ausklappen:
  // je Gruppe die häufigsten Module mit Treffern; ausgeklappt oder beim Filtern nach Namen auch
  // Module ohne Treffer (deaktiviert, Zähler 0), damit sichtbar bleibt, was Suche und Filter ausschließen.
  var MOD_PER_GROUP = 6;
  function modGroup(tab, values, counts) {
    var r = ui[tab];
    var expanded = r.fbody.classList.contains("show-all-mod");
    var filt = (r.modFilter || "").toLowerCase();
    var sel = state[tab].mod || [];
    var uni = (data.el && data.el.dict.modUni) || [];
    var showZero = expanded || !!filt;
    var html = "", hidden = 0, any = false;
    C.UNIVERSES.forEach(function (u) {
      var ks = [];
      values.forEach(function (v, k) {
        if ((uni[k] || "other") !== u) return;
        if (filt && String(v).toLowerCase().indexOf(filt) < 0 && sel.indexOf(v) < 0) return;
        ks.push(k);
      });
      if (!ks.length) return;
      ks.sort(function (x, y) { return (counts[y] || 0) - (counts[x] || 0) || String(values[x]).localeCompare(String(values[y])); });
      var live = ks.filter(function (k) { return (counts[k] || 0) > 0 || sel.indexOf(values[k]) >= 0; });
      var list = showZero ? ks : live.slice(0, MOD_PER_GROUP);
      hidden += ks.length - list.length;
      var sum = 0;
      ks.forEach(function (k) { sum += counts[k] || 0; });
      any = any || list.length > 0;
      html += '<div class="ve-unigroup"><div class="ve-unihead">' + esc(t("uni_" + u)) + ' <span class="ve-fchip-n">' + num(sum) +
        "</span></div><div class=\"ve-fvals\">" + list.map(function (k) {
          return chipButton("mod", values[k], values[k], counts[k] || 0, sel.indexOf(values[k]) >= 0);
        }).join("") + (!list.length ? '<span class="ve-muted ve-fnone">' + esc(t("mod_none")) + "</span>" : "") + "</div></div>";
    });
    if (!filt && (hidden || expanded)) {
      html += '<button type="button" class="ve-more" data-more="mod">' +
        esc(expanded ? t("show_less") : t("show_all", { n: num(values.length) })) + "</button>";
    }
    if (!any && filt) html += '<p class="ve-muted ve-fnone">' + esc(t("mod_nomatch")) + "</p>";
    var inner = '<input type="search" class="ve-modfilter" data-modfilter="1" placeholder="' + esc(t("mod_ph")) +
      '" aria-label="' + esc(t("mod_ph")) + '" value="' + esc(r.modFilter || "") + '">' +
      '<div class="ve-fvals-scroll ve-unigroups">' + html + "</div>";
    return group(t("f_mod"), inner, "ve-fgroup-mod");
  }

  function refreshFacets(tab, keepFocus) {
    var D = data[tab], res = data.res[tab], r = ui[tab];
    if (!D || !res) return;
    var active = document.activeElement;
    var focusSel = keepFocus && active && active.matches && active.matches("input[data-modfilter]");
    var c = res.counts;
    var q = (state[tab].q || "").trim();
    var html = q ? '<p class="ve-fhint">' + esc(t("counts_hint_q", { q: q })) + "</p>" : "";
    if (tab === "el") {
      if (D.full) {
        html += group(t("f_kind"), facetChips(tab, "kind", D.dict.kind, c.kind, { hideEmpty: true }));
      }
      html += group(t("f_plat"), facetChips(tab, "plat", D.dict.plat, c.plat));
      html += group(t("f_status"), facetChips(tab, "st", D.full ? ["new", "changed", "removed", "unchanged"] : ["removed"],
        D.full ? c.st : { 0: c.st[2] }, {}));
      if (D.full) {
        html += group(t("f_has"), facetChips(tab, "has", C.HAS, c.has));
        html += group(t("f_doc"), facetChips(tab, "doc", D.dict.doc, c.doc, { hideEmpty: true }));
        html += modGroup(tab, D.dict.mod, c.mod);
        if (D.dict.cl.length) html += group(t("f_cl"), facetChips(tab, "cl", D.dict.cl, c.cl, { hideEmpty: true }));
      }
      html += group(t("f_rel"), releaseSelect(tab, "first", t("rel_first"), c.first) +
        releaseSelect(tab, "last", t("rel_last"), c.last) +
        (D.full ? releaseSelect(tab, "chg", t("rel_chg"), c.chg) : ""), "ve-fgroup-rel");
    } else {
      html += group(t("f_plat"), facetChips(tab, "plat", D.dict.plat, c.plat, { hideEmpty: true }));
      if (tab === "snip") html += group(t("f_role"), facetChips(tab, "role", D.dict.role, c.role));
      else html += group(t("f_series"), facetChips(tab, "multi", ["1"], c.multi));
      html += group(t("f_doc"), docSelect(tab, D, c.doc), "ve-fgroup-rel");
      if (D.dict.mod.length) html += modGroup(tab, D.dict.mod, c.mod);
    }
    // Statusänderung der Zähler, ohne den Fokus im Modulfilter zu verlieren
    r.fbody.innerHTML = html;
    if (focusSel) {
      var inp = r.fbody.querySelector("input[data-modfilter]");
      if (inp) { inp.focus(); inp.setSelectionRange(inp.value.length, inp.value.length); }
    }
  }

  function refreshChips(tab) {
    var r = ui[tab], sel = state[tab], html = "";
    // Der Suchtext ist ein Filter wie die Facetten: als entfernbarer Chip vorn
    if (sel.q && sel.q.trim()) {
      html += '<button type="button" class="ve-chip-on ve-chip-q" data-chip="q" data-val="" title="' + esc(t("remove_filter")) +
        '"><span class="ve-chip-k">' + esc(t("chip_q")) + ":</span> „" + esc(sel.q.trim()) + '“ <span aria-hidden="true">✕</span></button>';
    }
    C.PARAMS[tab].forEach(function (p) {
      var key = p[0];
      if (key === "q" || key === "id") return;
      var v = sel[key];
      (Array.isArray(v) ? v : (v ? [v] : [])).forEach(function (val) {
        html += '<button type="button" class="ve-chip-on" data-chip="' + key + '" data-val="' + esc(val) + '" title="' +
          esc(t("remove_filter")) + '"><span class="ve-chip-k">' + esc(facetTitle(key)) + ":</span> " +
          esc(valueLabel(tab, key, val)) + ' <span aria-hidden="true">✕</span></button>';
      });
    });
    if (html) html += '<button type="button" class="ve-chip-clear" data-chip="*">' + esc(t("reset")) + "</button>";
    r.chips.innerHTML = html;
    r.chips.hidden = !html;
  }

  // ------------------------------------------------------------------ Öffnen / Detail
  function openFromList(tab, k, push) {
    var D = data[tab];
    var r = ui[tab];
    var i = r.vlist.items[k];
    if (i == null) return;
    openItem(tab, D.ids[i], push, { fromList: true });
  }

  function openItem(tab, id, push, opts) {
    if (tab === "el") {
      if (state.id !== id) { state.from = ""; state.to = ""; }
      state.id = id;
      if (opts && opts.view) state.view = opts.view;
    } else state[tab].id = id;
    commit(push, { detail: true, fromList: !!(opts && opts.fromList) });
    var r = ui[tab];
    if (opts && opts.fromList) setMismatch(tab, false);
    r.vlist.openKey = id;
    r.vlist.render();
    syncViewer(tab, true);
  }

  function closeDetail(tab) {
    // Aus der Liste geöffnet: ein Schritt zurück stellt die Liste samt Filtern wieder her
    if (window.history.state && window.history.state.fromList) {
      window.history.back();
      return;
    }
    if (tab === "el") state.id = ""; else state[tab].id = "";
    commit(true);
    setMismatch(tab, false);
    ui[tab].vlist.openKey = null;
    ui[tab].vlist.render();
    syncViewer(tab);
  }

  var listScroll = { el: 0, fig: 0, snip: 0 };
  function setDetailMode(tab, on) {
    var r = ui[tab];
    var was = r.panel.classList.contains("is-detail");
    if (on && !was) listScroll[tab] = r.list.scrollTop;
    r.panel.classList.toggle("is-detail", on);
    if (on && !was) {
      var top = r.md.getBoundingClientRect().top;
      if (top < 0) window.scrollTo(0, window.scrollY + top - 8);
    }
    r.panel.classList.toggle("has-selection", !!selectedKey(tab));
    if (!on && was) {
      r.list.scrollTop = listScroll[tab];
      r.vlist.render();
    }
  }

  var shown = { el: null, fig: null, snip: null };
  var token = { el: 0, fig: 0, snip: 0 };

  function syncViewer(tab, userAction) {
    var key = selectedKey(tab);
    var r = ui[tab];
    setDetailMode(tab, !!key && narrowMQ.matches);
    if (!key) {
      // Keine Auswahl mehr (z. B. Zurück zur Liste): laufendes Laden abbrechen und verwerfen
      token[tab]++;
      if (ctrl[tab]) { try { ctrl[tab].abort(); } catch (e) { /* ignore */ } ctrl[tab] = null; }
      shown[tab] = null;
      r.vbody.innerHTML = '<div class="ve-placeholder">' + esc(t("pick_" + tab)) + "</div>";
      return;
    }
    if (tab === "el" && shown.el === key + "|" + state.view) return;
    if (tab !== "el" && shown[tab] === key) return;
    if (!data[tab] && tab !== "el") return;
    if (tab === "el") loadElement(key, userAction);
    else loadItem(tab, key, userAction);
    if (userAction && narrowMQ.matches) {
      r.back.focus({ preventScroll: true });
    }
  }

  // ------------------------------------------------------------------ Element-Viewer
  var EL = { rec: null, from: null, to: null, clicks: [], mode: "side", diff: null, figShown: PAGE.fig, snipShown: PAGE.snip };

  function loadElement(id, userAction) {
    var r = ui.el;
    var my = ++token.el;
    var signal = newSignal("el");
    shown.el = null;   // bis zum Erfolg zeigt der Viewer nicht mehr das vorige Element
    if (!EL.rec || EL.rec.id !== id) {
      r.vbody.innerHTML = '<div class="ve-placeholder">' + esc(t("loading_detail", { id: id })) + "</div>";
    }
    var D = data.el, di = D ? D.byId.get(id) : null;
    var isRef = di != null && D.ref[di] === 1;
    var p = (EL.rec && EL.rec.id === id) ? Promise.resolve(EL.rec) : isRef
      // nur zitierte Kennung: kein Versions-Record, Belege aus versions/explorer/refs/
      ? fetchJson(ROOT + "versions/explorer/refs/" + encodeURIComponent(C.recordFile(id, stems("ref"))), signal)
      : fetchJson(ROOT + "versions/data/" + encodeURIComponent(C.recordFile(id, stems("rec"))), signal)
        .catch(function (err) {
          // Rückfall auf die lokale API nur, wenn die Datei fehlt – nicht bei Abbruch oder Netzfehler
          if (C.isAbortError(err) || C.isNetworkError(err) || my !== token.el) throw err;
          return fetchJson("/api/versions?id=" + encodeURIComponent(id), signal);
        });
    p.then(function (rec) {
      if (my !== token.el) return;
      if (!rec || (!rec.ok && !rec.versions)) throw new Error(t("not_found", { id: id }));
      rec.id = id;
      if (EL.rec !== rec) {
        // Präsenz-Einträge (im PDF vorhanden, Wortlaut nicht erfasst) gehören in die Zeitachse,
        // aber nicht in den Vergleich: rec.versions enthält nur erfassten Wortlaut.
        if (rec.citation_only && state.view === "ver") state.view = "cit";
        rec.allVersions = C.sortVersions(rec.versions || []);
        rec.versions = rec.allVersions.filter(function (v) { return v.text_captured !== false; });
        EL.rec = rec;
        EL.figShown = PAGE.fig; EL.snipShown = PAGE.snip;
        initCompare(rec);
      }
      shown.el = id + "|" + state.view;
      renderElement();
      r.vbody.parentNode.scrollTop = 0;
      if (userAction && !narrowMQ.matches) r.list.focus({ preventScroll: true });
    }).catch(function (err) {
      if (my !== token.el || C.isAbortError(err) || pageHidden) return;
      shown.el = null;
      r.vbody.innerHTML = errorHtml(err);
    });
  }

  function initCompare(rec) {
    var versions = rec.versions || [];
    var lifecycle = rec.lifecycle || {};
    rec.timeline = C.buildTimeline(rec.allVersions || versions, lifecycle);
    var e = rec.epochs = rec.timeline.filter(function (x) { return x.type === "content"; });
    var drop = rec.timeline.filter(function (x) { return x.type === "dropped"; })[0];
    var from = state.from, to = state.to;
    var hasRel = function (r) { return versions.some(function (v) { return v.release === r; }); };
    if (from && to && hasRel(from) && (hasRel(to) || (lifecycle.is_dropped && (lifecycle.dropped_in || []).indexOf(to) >= 0))) {
      EL.from = from; EL.to = to;
    } else if (e.length > 1) {
      EL.from = e[0].firstRelease; EL.to = e[e.length - 1].firstRelease;
    } else if (e.length === 1 && drop) {
      EL.from = e[0].lastRelease; EL.to = drop.from;
    } else if (versions.length > 1) {
      EL.from = versions[0].release; EL.to = versions[versions.length - 1].release;
    } else if (versions.length === 1) {
      EL.from = EL.to = versions[0].release;
    } else { EL.from = EL.to = null; }
    EL.clicks = EL.from && EL.to && EL.from !== EL.to ? [EL.from, EL.to] : (EL.from ? [EL.from] : []);
  }

  function statusPill(rec) {
    var lc = rec.lifecycle || {};
    var versions = rec.versions || [];
    var latest = versions[versions.length - 1] || {};
    return lc.is_dropped
      ? '<span class="ve-pill-dropped">' + esc(t("pill_dropped", { rel: lc.first_dropped_release || "", last: lc.last_active_release || "" })) + "</span>"
      : '<span class="ve-pill-ok">' + esc(t("pill_active", { rel: lc.last_active_release || latest.release || "" })) + "</span>";
  }

  // Namen mit Spezifikations-Platzhaltern (<fwssi-sn>, {<symbol-fw-state>}, <LPDU_CalloutName>)
  function nameHtml(name, cls) {
    if (!name) return "";
    var ph = /<[^<>]+>/.test(name);
    return '<span class="' + cls + '">' + esc(name) + "</span>" +
      (ph ? '<span class="ve-ph" title="' + esc(t("placeholder_hint")) + '">' + esc(t("placeholder")) + "</span>" : "");
  }

  function renderElement() {
    var rec = EL.rec, r = ui.el;
    var el = rec.element || {};
    var ev = rec.evidence || { figures: [], snippets: [] };
    var isRef = !!rec.citation_only;
    var isCP = isRef ? el.platform === "CP" : String(rec.canonical_id || "").indexOf("AUTOSAR/CP") >= 0;
    var meta = [];
    meta.push([t("lbl_plat"), platLabel(isCP ? "CP" : "AP")]);
    if (el.universe === "FO") meta.push([t("lbl_universe"), t("uni_FO")]);
    if (el.module) meta.push([t("lbl_module"), el.module]);
    if (el.cluster) meta.push([t("lbl_cluster"), el.cluster]);
    if (!isRef) {
      if (el.first) meta.push([t("lbl_releases"), el.first + (el.last && el.last !== el.first ? " – " + el.last : "")]);
      meta.push([t("lbl_versions"), String(el.distinct || (rec.epochs || []).length)]);
      if (el.changed && el.changed.length) meta.push([t("lbl_changed_in"), el.changed.join(", ")]);
      if (el.ai) meta.push([t("lbl_ai"), t("ai_yes")]);
    }
    var links = "";
    if (!isRef) {
      if (el.page) links += '<a class="ve-linkbtn ve-linkbtn-primary" href="' + esc(el.page + "#" + rec.id) + '">' + esc(t("open_page")) + "</a>";
      links += '<a class="ve-linkbtn" href="spec/record.html?id=' + encodeURIComponent(rec.id) + '">' + esc(t("open_record")) + "</a>";
    }
    links += '<button type="button" class="ve-linkbtn" data-act="copy">' + esc(t("copy_link")) + "</button>";
    if (!el.page && !isRef) links += '<span class="ve-muted ve-nopage">' + esc(t("no_page")) + "</span>";
    var nf = ev.figures.length, ns = ev.snippets.length, nc = ev.cited_total || (ev.cited_in || []).length;
    var view = state.view;
    var sub = (isRef ? [] : [["ver", t("v_ver"), null]]).concat([["cit", t("v_cit"), nc], ["fig", t("v_fig"), nf], ["snip", t("v_snip"), ns]]);
    if (!isRef) sub = [sub[0], sub[2], sub[3], sub[1]];
    var subHtml = '<div class="ve-subtabs" role="tablist" aria-label="' + esc(t("viewer_el")) + '">';
    sub.forEach(function (s) {
      subHtml += '<button type="button" role="tab" class="ve-subtab' + (view === s[0] ? " is-active" : "") + '" data-view="' + s[0] +
        '" aria-selected="' + (view === s[0] ? "true" : "false") + '">' + esc(s[1]) +
        (s[2] != null ? ' <span class="ve-subcount' + (s[2] ? "" : " is-zero") + '">' + num(s[2]) + "</span>" : "") + "</button>";
    });
    subHtml += "</div>";
    var pill = isRef ? '<span class="ve-pill-ref">' + esc(t("ref_badge")) + "</span>" : statusPill(rec);
    r.vbody.innerHTML =
      '<div class="ve-vh"><div class="ve-vh-top"><h2 class="ve-vh-id">' + esc(rec.id) + "</h2>" + pill + "</div>" +
      '<div class="ve-vh-name">' + (el.kind ? '<span class="ve-kind' + (isRef ? " ve-kind-ref" : "") + '">' + esc(kindLabel(el.kind)) + "</span>" : "") +
      nameHtml(el.name, "ve-vh-elname") +
      (rec.canonical_id ? '<span class="ve-muted ve-cid">' + esc(rec.canonical_id) + "</span>" : "") + "</div>" +
      (isRef ? '<p class="ve-refnote">' + esc(t("ref_note")) + "</p>" : "") +
      '<dl class="ve-meta">' + meta.map(function (m) { return "<div><dt>" + esc(m[0]) + "</dt><dd>" + esc(m[1]) + "</dd></div>"; }).join("") + "</dl>" +
      '<div class="ve-links">' + links + "</div></div>" + subHtml +
      '<div class="ve-subpanel" data-role="subpanel"></div>';
    renderSubpanel();
  }

  // Belege, deren Text die Kennung zitiert, ohne ihr zugeordnet zu sein
  function citedList(list, total) {
    if (!list.length) return '<p class="ve-placeholder ve-placeholder-small">' + esc(t("cited_empty")) + "</p>";
    var html = '<p class="ve-muted ve-evhead">' + esc(t("cited_head", { n: num(total || list.length) })) + '</p><ul class="ve-citedlist">';
    list.forEach(function (c) {
      var tab = c.kind === "fig" ? "fig" : "snip";
      html += '<li><button type="button" class="ve-target" data-goto="' + tab + '" data-id="' + esc(c.id) + '">' +
        esc(c.t || c.id) + '</button><div class="ve-cardmeta"><span class="ve-mini">' + esc(t(tab === "fig" ? "v_fig" : "v_snip")) +
        "</span> <code>" + esc(c.id) + "</code>" + (c.doc ? " · " + esc(c.doc) + (c.p ? " · " + esc(t("page_n", { p: c.p })) : "") : "") +
        "</div></li>";
    });
    html += "</ul>";
    if (total > list.length) html += '<p class="ve-muted">' + esc(t("cited_more", { n: num(total - list.length) })) + "</p>";
    return html;
  }

  // Kennungen im (maskierten) Text als Sprung in den Element-Viewer
  function linkIds(escaped, selfId) {
    var D = data.el;
    if (!D) return escaped;
    return C.linkifyIds(escaped, function (id) {
      var k = C.resolveId(D, id);
      if (k < 0) return null;
      var target = D.ids[k];
      if (target === selfId) return '<strong class="ve-idself">' + esc(id) + "</strong>";
      var ref = D.ref[k] === 1;
      return '<button type="button" class="ve-idlink' + (ref ? " is-ref" : "") + '" data-open-el="' + esc(target) +
        '" title="' + esc(ref ? t("ref_link_title") : t("cited_link_title")) + (target !== id ? " (" + target + ")" : "") + '">' + esc(id) + "</button>";
    });
  }

  function renderSubpanel() {
    var box = ui.el.vbody.querySelector("[data-role=subpanel]");
    if (!box) return;
    var ev = EL.rec.evidence || { figures: [], snippets: [] };
    if (state.view === "fig") box.innerHTML = evidenceList("fig", ev.figures, EL.figShown);
    else if (state.view === "snip") box.innerHTML = evidenceList("snip", ev.snippets, EL.snipShown);
    else if (state.view === "cit" || EL.rec.citation_only) box.innerHTML = citedList(ev.cited_in || [], ev.cited_total || 0);
    else {
      box.innerHTML = versionsHtml();
      wireVersions(box);
      loadDiffView();
    }
    fillPdfLinks(box);
    fillCanonLinks(box);
    figObserve(box);
  }

  function relText(rels) { return (rels || []).join(", "); }

  // Kanonische Belegseite (spec/figures/<FIG>.html bzw. spec/snippets/<id>.html). Die Links bleiben
  // verborgen, bis feststeht, dass die Seiten veröffentlicht sind (Index der jeweiligen Seitenfamilie).
  function canonLink(id, cls) {
    var fam = /^FIG-/.test(id) ? "fig" : "snip";
    return '<a class="ve-linkbtn ' + (cls || "") + '" hidden data-canon="' + fam + '" href="' + esc(C.figureHref(ROOT, id, stems("item"))) + '">' +
      esc(t(fam === "fig" ? "page_fig" : "page_snip")) + "</a>";
  }
  var canonProbe = null;
  function ensureCanonPages() {
    if (canonProbe) return canonProbe;
    var probe = function (dir) {
      return fetch(ROOT + "spec/" + dir + "/index.html", { method: "HEAD" })
        .then(function (r) { return r.ok; }).catch(function () { return false; });
    };
    canonProbe = Promise.all([probe("figures"), probe("snippets")]).then(function (r) {
      if (!r[0] && !r[1]) canonProbe = null;   // z. B. abgebrochen: beim nächsten Mal erneut prüfen
      return { fig: r[0], snip: r[1] };
    });
    return canonProbe;
  }
  function fillCanonLinks(container) {
    ensureCanonPages().then(function (avail) {
      container.querySelectorAll("a[data-canon]").forEach(function (a) {
        if (avail[a.getAttribute("data-canon")]) a.hidden = false;
      });
    });
  }

  function pdfAnchor(doc, rels, page, platform) {
    var list = (rels || []).slice();
    if (!list.length) list = [platform === "classic" || platform === "CP" ? "R20-11" : "R25-11"];
    return '<a class="ve-linkbtn" hidden target="_blank" rel="noopener noreferrer" data-pdf-doc="' + esc(doc) + '" data-pdf-rel="' +
      esc(list.join(" ")) + '" data-pdf-page="' + esc(page || "") + '">' + esc(t("pdf_page", { p: page || "?" })) + "</a>";
  }

  function evidenceMeta(e) {
    var bits = [];
    if (e.doc) bits.push(esc(e.doc) + (e.p ? " · " + esc(t("page_n", { p: e.p })) : ""));
    if (e.rel && e.rel.length) bits.push(esc(relText(e.rel)));
    if (e.role) bits.push('<span class="ve-role ve-role-' + esc(e.role) + '">' + esc(t("role_" + e.role)) + "</span>");
    if (e.conf != null) bits.push(esc(t("conf", { p: Math.round(e.conf * 100) })));
    if (e.m) bits.push(esc(t("by", { m: e.m })));
    if (e.via) bits.push(esc(t("via_alias", { id: e.via })));
    return bits.join('<span aria-hidden="true"> · </span>');
  }

  function evidenceList(kind, list, limit) {
    var platform = EL.rec && String(EL.rec.canonical_id || "").indexOf("AUTOSAR/CP") >= 0 ? "CP" : "AP";
    if (!list.length) {
      return '<p class="ve-placeholder ve-placeholder-small">' + esc(t(kind === "fig" ? "figs_empty" : "snips_empty")) + "</p>" +
        '<p class="ve-muted">' + esc(t(kind === "fig" ? "figs_browse" : "snips_browse")) +
        ' <button type="button" class="ve-linkbtn" data-goto-tab="' + kind + '">' + esc(t(kind === "fig" ? "tab_fig" : "tab_snip")) + "</button></p>";
    }
    var html = '<p class="ve-muted ve-evhead">' + esc(t(kind === "fig" ? "figs_head" : "snips_head", { n: num(list.length) })) + "</p>";
    html += '<div class="' + (kind === "fig" ? "ve-figgrid" : "ve-sniplist") + '">';
    list.slice(0, limit).forEach(function (e) {
      var linkRow = '<div class="ve-cardlinks">' + canonLink(e.id, "") +
        pdfAnchor(e.doc, e.rel, e.p, platform) +
        '<button type="button" class="ve-linkbtn" data-goto="' + kind + '" data-id="' + esc(e.id) + '">' +
        esc(t(kind === "fig" ? "in_fig_browser" : "in_snip_browser")) + "</button></div>";
      if (kind === "fig") {
        html += '<article class="ve-figcard">' + thumbHtml(e.sha, e.cap) +
          '<div class="ve-cardbody"><div class="ve-cardtitle">' + linkIds(esc(C.decodeEntities(e.cap || e.id)), EL.rec && EL.rec.id) + "</div>" +
          '<div class="ve-cardmeta"><code>' + esc(e.id) + "</code>" + (e.nser > 1 ? ' · ' + esc(t("series_n", { n: e.nser })) : "") + "</div>" +
          '<div class="ve-cardmeta">' + evidenceMeta(e) + "</div>" +
          (e.why ? '<div class="ve-why"><span>' + esc(t("why")) + ":</span> " + esc(e.why) + "</div>" : "") + linkRow + "</div></article>";
      } else {
        html += '<article class="ve-snipcard"><blockquote class="ve-excerpt">' + linkIds(esc(C.decodeEntities(e.x || e.id)), EL.rec && EL.rec.id) + "</blockquote>" +
          '<div class="ve-cardmeta"><code>' + esc(e.id) + "</code></div>" +
          '<div class="ve-cardmeta">' + evidenceMeta(e) + "</div>" +
          (e.why ? '<div class="ve-why"><span>' + esc(t("why")) + ":</span> " + esc(e.why) + "</div>" : "") + linkRow + "</article>";
      }
    });
    html += "</div>";
    if (list.length > limit) {
      html += '<button type="button" class="ve-btn ve-showmore" data-showmore="' + kind + '">' +
        esc(t("more_n", { n: num(Math.min(PAGE[kind], list.length - limit)), rest: num(list.length - limit) })) + "</button>";
    }
    return html;
  }

  // Platzhalter für static/figure-images.js: lädt das Bild erst, wenn es sichtbar wird, und nur mit Zugang
  function thumbHtml(sha, alt, size) {
    if (!sha || !/^[0-9a-f]{64}$/.test(sha)) {
      return '<div class="ve-thumb is-missing"><span class="ve-thumb-ph">' + esc(t("thumb_none")) + "</span></div>";
    }
    return '<div class="ve-thumb" data-fig-sha="' + esc(sha) + '" data-fig-alt="' + esc(alt || "") + '" data-fig-size="' +
      esc(size || "thumb") + '"></div>';
  }

  // Nach dem Einklappen den Anfang des Abschnitts zeigen (im scrollenden Viewer bzw. auf der Seite)
  function revealTop(el) {
    if (!el) return;
    var sc = el.parentNode;
    while (sc && sc.nodeType === 1 && sc !== document.body) {
      var oy = window.getComputedStyle(sc).overflowY;
      if ((oy === "auto" || oy === "scroll") && sc.scrollHeight > sc.clientHeight) break;
      sc = sc.parentNode;
    }
    var top = el.getBoundingClientRect().top;
    if (sc && sc.nodeType === 1 && sc !== document.body) {
      var d = top - sc.getBoundingClientRect().top;
      if (d < 0) sc.scrollTop += d - 8;
    } else if (top < 0) window.scrollBy(0, top - 8);
  }

  function onViewerClick(tab, e) {
    var b = e.target.closest("[data-view],[data-goto],[data-goto-tab],[data-open-el],[data-showmore],[data-act],[data-set-left],[data-set-right],[data-mode],.ve-epoch-card");
    if (!b) return;
    if (b.hasAttribute("data-view") && tab === "el") {
      state.view = b.getAttribute("data-view");
      shown.el = EL.rec.id + "|" + state.view;
      commit(false);
      ui.el.vbody.querySelectorAll(".ve-subtab").forEach(function (s) {
        var on = s.getAttribute("data-view") === state.view;
        s.classList.toggle("is-active", on);
        s.setAttribute("aria-selected", on ? "true" : "false");
      });
      renderSubpanel();
      return;
    }
    if (b.hasAttribute("data-goto")) {
      var target = b.getAttribute("data-goto");
      state[target].id = b.getAttribute("data-id");
      state.tab = target;
      commit(true, { detail: true });
      switchTab(target, false);
      return;
    }
    if (b.hasAttribute("data-goto-tab")) { switchTab(b.getAttribute("data-goto-tab"), true); return; }
    if (b.hasAttribute("data-open-el")) {
      state.tab = "el";
      var id = b.getAttribute("data-open-el");
      if (state.id !== id) { state.from = ""; state.to = ""; }
      state.id = id;
      state.view = b.getAttribute("data-el-view") || state.view;
      commit(true, { detail: true });
      switchTab("el", false);
      return;
    }
    if (b.hasAttribute("data-showmore")) {
      var k = b.getAttribute("data-showmore");
      if (k === "fig") EL.figShown += PAGE.fig; else EL.snipShown += PAGE.snip;
      if (tab === "el") renderSubpanel();
      return;
    }
    if (b.getAttribute("data-act") === "retry") {
      if (tab === "el") shown.el = null; else shown[tab] = null;
      syncViewer(tab, false);
      return;
    }
    if (b.getAttribute("data-act") === "ai-toggle") {
      var body = ui[tab].vbody.querySelector(".ve-ai-body");
      if (!body) return;
      var open = body.classList.toggle("is-open");
      b.setAttribute("aria-expanded", open ? "true" : "false");
      b.textContent = t(open ? "ai_less" : "ai_more");
      if (!open) revealTop(body.closest(".ve-ai"));
      return;
    }
    if (b.getAttribute("data-act") === "copy") {
      var url = window.location.href;
      var done = function () { b.textContent = t("copied"); setTimeout(function () { b.textContent = t("copy_link"); }, 1500); };
      if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, done); else done();
      return;
    }
    if (tab !== "el") return;
    if (b.hasAttribute("data-set-left")) { e.stopPropagation(); EL.from = b.getAttribute("data-set-left"); EL.clicks = [EL.from, EL.to]; afterCompareChange(); return; }
    if (b.hasAttribute("data-set-right")) { e.stopPropagation(); EL.to = b.getAttribute("data-set-right"); EL.clicks = [EL.from, EL.to]; afterCompareChange(); return; }
    if (b.hasAttribute("data-mode")) {
      EL.mode = b.getAttribute("data-mode");
      ui.el.vbody.querySelectorAll(".ve-view-btn").forEach(function (x) { x.classList.toggle("is-active", x === b); });
      renderDiffContent();
      return;
    }
    if (b.classList.contains("ve-epoch-card")) recordEpochClick(b.getAttribute("data-rep-rel"));
  }

  // ------------------------------------------------------------------ Versionen & Diff
  function versionsHtml() {
    var rec = EL.rec, lc = rec.lifecycle || {};
    var cards = (rec.timeline || []).map(function (seg, idx) {
      var span = seg.releases.length === 1 ? seg.releases[0] : seg.releases[0] + " → " + seg.releases[seg.releases.length - 1];
      if (seg.type === "absent" || seg.type === "gap") {
        var title = seg.type === "absent" ? t("ep_absent_until", { rel: seg.releases[seg.releases.length - 1] }) : span;
        return '<div class="ve-epoch-card ve-epoch-absent" data-epoch="' + seg.type + '"><div class="ve-epoch-header"><span class="ve-epoch-span">' +
          esc(title) + '</span><span class="ve-epoch-status ve-status-absent">' + esc(t("ep_absent")) + '</span></div><div class="ve-epoch-body"><div>' +
          esc(seg.type === "absent" ? t("ep_absent_text", { rel: seg.releases[seg.releases.length - 1] }) : t("ep_gap_text", { rels: seg.releases.join(", ") })) +
          '</div><div class="ve-epoch-subreleases">' + seg.releases.map(function (r) { return '<span class="ve-epoch-rel-pill">' + esc(r) + "</span>"; }).join(" ") +
          "</div></div></div>";
      }
      if (seg.type === "presence" || seg.type === "unchecked") {
        var isPres = seg.type === "presence";
        return '<div class="ve-epoch-card ve-epoch-absent ve-epoch-' + seg.type + '" data-epoch="' + seg.type + '"><div class="ve-epoch-header"><span class="ve-epoch-span">' +
          esc(span) + '</span><span class="ve-epoch-status ' + (isPres ? "ve-status-presence" : "ve-status-unchecked") + '">' +
          esc(t(isPres ? "ep_presence" : "ep_unchecked")) + '</span></div><div class="ve-epoch-body"><div>' +
          esc(t(isPres ? "ep_presence_text" : "ep_unchecked_text")) + '</div><div class="ve-epoch-subreleases">' +
          seg.releases.map(function (r) { return '<span class="ve-epoch-rel-pill">' + esc(r) + "</span>"; }).join(" ") +
          "</div></div></div>";
      }
      if (seg.type === "dropped") {
        var dropRel = seg.from;
        return '<div class="ve-epoch-card ve-epoch-dropped' + (EL.to === dropRel ? " is-right" : "") + '" data-epoch="dropped" data-rep-rel="' +
          esc(dropRel) + '" data-releases="' + esc(seg.releases.join(",")) + '" role="button" tabindex="0"><div class="ve-epoch-header"><span class="ve-epoch-span">' +
          esc(t("ep_from", { rel: dropRel })) + '</span><span class="ve-epoch-status ve-status-dropped">' + esc(t("st_removed")) +
          '</span></div><div class="ve-epoch-body"><div><strong>' + esc(t("ep_dropped_title")) + '</strong></div><div class="ve-epoch-subreleases ve-muted">' +
          esc(t("ep_dropped_sub", { rels: seg.releases.join(", "), last: lc.last_active_release || "" })) + '</div></div><div class="ve-epoch-actions">' +
          '<button type="button" class="ve-epoch-btn ve-btn-set-right" data-set-right="' + esc(dropRel) + '">' + esc(t("ep_right_drop")) + "</button></div></div>";
      }
      var label = t("ep_baseline"), cls = "ve-status-initial";
      if (seg.isChange) { label = t("ep_changed", { rel: seg.firstRelease }); cls = "ve-status-changed"; }
      else if (seg.isRevert) { label = t("ep_revert", { rel: seg.firstRelease }); cls = "ve-status-revert"; }
      else if (!seg.isInitial) { label = t("ep_unchanged"); cls = "ve-status-stable"; }
      var act = [];
      if (seg.releases.indexOf(EL.from) >= 0) act.push("is-left");
      if (seg.releases.indexOf(EL.to) >= 0) act.push("is-right");
      var pills = seg.releases.map(function (r) { return '<span class="ve-epoch-rel-pill">' + esc(r) + "</span>"; }).join(" ");
      var subInfo = seg.releases.length === 1 ? esc(t("ep_one", { hash: seg.hash8 }))
        : "<strong>" + esc(t("ep_many", { n: seg.releases.length })) + "</strong> · #" + esc(seg.hash8);
      if (seg.hashes.length > 1) subInfo += '<div class="ve-epoch-variants">' + esc(t("ep_variants", { n: seg.hashes.length })) + "</div>";
      return '<div class="ve-epoch-card ' + act.join(" ") + '" data-epoch="' + idx + '" data-rep-rel="' + esc(seg.firstRelease) +
        '" data-releases="' + esc(seg.releases.join(",")) + '" role="button" tabindex="0"><div class="ve-epoch-header"><span class="ve-epoch-span">' +
        esc(span) + '</span><span class="ve-epoch-status ' + cls + '">' + esc(label) + '</span></div><div class="ve-epoch-body"><div>' +
        subInfo + '</div><div class="ve-epoch-subreleases">' + pills + '</div></div><div class="ve-epoch-actions">' +
        '<button type="button" class="ve-epoch-btn ve-btn-set-left" data-set-left="' + esc(seg.firstRelease) + '">' + esc(t("ep_left")) + "</button>" +
        '<button type="button" class="ve-epoch-btn ve-btn-set-right" data-set-right="' + esc(seg.firstRelease) + '">' + esc(t("ep_right")) + "</button></div></div>";
    }).join("");
    return '<div class="ve-timeline-wrap"><div class="ve-timeline-head"><span class="ve-timeline-title">' + esc(t("tl_title")) +
      '</span><span class="ve-timeline-hint">' + esc(t("tl_hint")) + '</span></div><div class="ve-timeline-epochs">' + cards + "</div></div>" +
      '<div class="ve-diff-toolbar"><div class="ve-compare-summary"><span>' + esc(t("cmp")) + '</span><span class="ve-tag-left" id="ve-tag-left-label">' +
      esc(EL.from || "–") + '</span><span class="ve-tag-arrow">➔</span><span class="ve-tag-right" id="ve-tag-right-label">' + esc(EL.to || "–") +
      '</span><button type="button" class="ve-btn-swap" data-act="swap" title="' + esc(t("swap_title")) + '">' + esc(t("swap")) + "</button></div>" +
      '<div class="ve-view-toggle">' + [["side", "mode_side"], ["unified", "mode_unified"], ["raw", "mode_raw"]].map(function (m) {
        return '<button type="button" class="ve-view-btn' + (EL.mode === m[0] ? " is-active" : "") + '" data-mode="' + m[0] + '">' + esc(t(m[1])) + "</button>";
      }).join("") + "</div></div>" +
      '<div id="ve-diff-output"></div>' +
      '<div class="ve-audit-box"><h3 class="ve-audit-title">' + esc(t("audit_title")) + '</h3><div class="ve-audit-grid">' +
      [["a_actor", "ve-audit-actor"], ["a_hash", "ve-audit-hash"], ["a_recorded", "ve-audit-recorded"], ["a_evidence", "ve-audit-evidence"]].map(function (a) {
        return '<div class="ve-audit-card"><span>' + esc(t(a[0])) + '</span><strong id="' + a[1] + '">-</strong></div>';
      }).join("") + "</div></div>";
  }

  function wireVersions(box) {
    var swap = box.querySelector("[data-act=swap]");
    if (swap) swap.addEventListener("click", function (e) {
      e.stopPropagation();
      var x = EL.from; EL.from = EL.to; EL.to = x; EL.clicks = [EL.from, EL.to];
      afterCompareChange();
    });
    box.querySelectorAll(".ve-epoch-card").forEach(function (card) {
      card.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); recordEpochClick(card.getAttribute("data-rep-rel")); }
      });
    });
  }

  function recordEpochClick(rel) {
    if (!rel) return;
    if (EL.clicks.length && EL.clicks[EL.clicks.length - 1] === rel) return;
    EL.clicks.push(rel);
    if (EL.clicks.length > 2) EL.clicks = EL.clicks.slice(-2);
    if (EL.clicks.length === 2) {
      var a = EL.clicks[0], b = EL.clicks[1];
      if (C.releaseKey(a) <= C.releaseKey(b)) { EL.from = a; EL.to = b; } else { EL.from = b; EL.to = a; }
    } else if (C.releaseKey(rel) >= C.releaseKey(EL.from || "")) EL.to = rel; else EL.from = rel;
    afterCompareChange();
  }

  function afterCompareChange() {
    state.from = EL.from || ""; state.to = EL.to || "";
    commit(false);
    var box = ui.el.vbody;
    box.querySelectorAll(".ve-epoch-card").forEach(function (card) {
      var rels = (card.getAttribute("data-releases") || "").split(",");
      card.classList.toggle("is-left", rels.indexOf(EL.from) >= 0);
      card.classList.toggle("is-right", rels.indexOf(EL.to) >= 0);
    });
    var l = document.getElementById("ve-tag-left-label"), r = document.getElementById("ve-tag-right-label");
    if (l) l.textContent = EL.from; if (r) r.textContent = EL.to;
    loadDiffView();
  }

  function formatReqLines(text) {
    if (!text) return [];
    var delimiters = ["Definition of callback function", "Definition of", "Upstream requirements:?", "Service [Nn]ame:?", "Syntax:?",
      "Service ID\\s*(?:\\[[^\\]]+\\])?:?", "Sync\\s*/\\s*Async:?", "Reentrancy:?", "Parameters\\s*\\((?:in|out|inout)\\):?", "Parameters:?",
      "\\(in\\)", "\\(inout\\)", "\\(out\\)", "Return value:?", "E_OK:?", "E_ OK:?", "E_NOT_OK:?", "E_ NOT_ OK:?", "Description:?",
      "Available via:?", "Specification of [^\\n:]+:", "Specification of [^\\n]+", "Document ID \\d+ : [^\\n]*", "Document ID \\d+ :", "AUTOSAR_[A-Z0-9_]+"];
    var delimRe = new RegExp("(" + delimiters.join("|") + "|\\([a-z]+\\))", "i");
    var parts = text.split(delimRe), lines = [], curr = "";
    parts.forEach(function (p) {
      if (!p) return;
      var ps = p.trim();
      var isDelim = delimiters.some(function (d) { return new RegExp("^" + d + "$", "i").test(ps); }) || ["(in)", "(out)", "(inout)"].indexOf(ps) >= 0;
      if (isDelim) { if (curr.trim()) lines.push(curr.trim()); curr = ps + " "; } else curr += p;
    });
    if (curr.trim()) lines.push(curr.trim());
    var out = [];
    lines.forEach(function (l) {
      var s = l.trim();
      if (!s) return;
      if (s.length > 100) s.split(/(?<=[.!?])\s+(?=[A-Z])/).forEach(function (x) { if (x.trim()) out.push(x.trim()); });
      else out.push(s);
    });
    return out;
  }

  function getDiffOpcodes(a, b) {
    var m = a.length, n = b.length, i, j;
    var dp = [];
    for (i = 0; i <= m; i++) dp.push(new Int32Array(n + 1));
    for (i = 0; i < m; i++) for (j = 0; j < n; j++) dp[i + 1][j + 1] = a[i] === b[j] ? dp[i][j] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
    i = m; j = n;
    var raw = [];
    while (i > 0 || j > 0) {
      if (i > 0 && j > 0 && a[i - 1] === b[j - 1]) { raw.push({ type: "equal", a: i - 1, b: j - 1 }); i--; j--; }
      else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) { raw.push({ type: "insert", a: i, b: j - 1 }); j--; }
      else { raw.push({ type: "delete", a: i - 1, b: j }); i--; }
    }
    raw.reverse();
    var ops = [], k = 0;
    while (k < raw.length) {
      var type = raw[k].type, sa = raw[k].a, sb = raw[k].b, ea = sa, eb = sb, q = k;
      while (q < raw.length && raw[q].type === type) {
        if (type === "equal") { ea = raw[q].a + 1; eb = raw[q].b + 1; }
        else if (type === "delete") ea = raw[q].a + 1;
        else eb = raw[q].b + 1;
        q++;
      }
      ops.push([type, sa, ea, sb, eb]);
      k = q;
    }
    var merged = [];
    for (var x = 0; x < ops.length; x++) {
      var c = ops[x], nx = ops[x + 1];
      if (nx && ((c[0] === "delete" && nx[0] === "insert") || (c[0] === "insert" && nx[0] === "delete"))) {
        merged.push(["replace", Math.min(c[1], nx[1]), Math.max(c[2], nx[2]), Math.min(c[3], nx[3]), Math.max(c[4], nx[4])]);
        x++;
      } else merged.push(c);
    }
    return merged;
  }

  function computeWordDiff(ta, tb) {
    var re = /[<>\-]|[\wÀ-ɏ]+|[^\s\wÀ-ɏ<>\-]+|\s+/g;
    var A = ta.match(re) || [], B = tb.match(re) || [];
    var outA = "", outB = "";
    getDiffOpcodes(A, B).forEach(function (op) {
      var sa = A.slice(op[1], op[2]).join(""), sb = B.slice(op[3], op[4]).join("");
      if (op[0] === "equal") { outA += esc(sa); outB += esc(sb); }
      else {
        if (op[0] !== "insert") outA += sa.trim() ? '<del class="ve-word-deleted">' + esc(sa) + "</del>" : sa;
        if (op[0] !== "delete") outB += sb.trim() ? '<ins class="ve-word-added">' + esc(sb) + "</ins>" : sb;
      }
    });
    return [outA, outB];
  }

  function performClientDiff(rec, fromRel, toRel) {
    var versions = rec.versions || [], lc = rec.lifecycle || {};
    var dropA = !!(lc.is_dropped && (lc.dropped_in || []).indexOf(fromRel) >= 0);
    var dropB = !!(lc.is_dropped && (lc.dropped_in || []).indexOf(toRel) >= 0);
    var kA = C.releaseKey(fromRel), kB = C.releaseKey(toRel);
    var eligA = versions.filter(function (v) { return C.releaseKey(v.release) <= kA; });
    var eligB = versions.filter(function (v) { return C.releaseKey(v.release) <= kB; });
    var vA = dropA ? null : (eligA.length ? eligA[eligA.length - 1] : null);
    var vB = dropB ? null : (eligB.length ? eligB[eligB.length - 1] : null);
    // Adaptive-Versionstexte sind als HTML-Text erfasst; ältere Store-Zeilen tragen noch doppelt
    // maskierte Kopfzeilen (&amp;lt;, Quelle inzwischen korrigiert). Zur Anzeige bis zum Fixpunkt auflösen.
    var linesA = formatReqLines(vA ? C.decodeFully(vA.content || "") : ""), linesB = formatReqLines(vB ? C.decodeFully(vB.content || "") : "");
    var blocks = [], lines = [], bi = 0;
    if (dropB) {
      linesA.forEach(function (l) {
        blocks.push({ id: "b-" + (++bi), tag: "delete", left_lines: [l], right_lines: [], left_html: esc(l), right_html: "" });
        lines.push({ type: "deleted", text: l });
      });
    } else {
      getDiffOpcodes(linesA, linesB).forEach(function (op) {
        var L = linesA.slice(op[1], op[2]), R = linesB.slice(op[3], op[4]), lh = "", rh = "";
        if (op[0] === "equal") { lh = esc(L.join("\n")); rh = esc(R.join("\n")); L.forEach(function (l) { lines.push({ type: "unchanged", text: l }); }); }
        else if (op[0] === "replace") {
          var w = computeWordDiff(L.join("\n"), R.join("\n")); lh = w[0]; rh = w[1];
          L.forEach(function (l) { lines.push({ type: "deleted", text: l }); });
          R.forEach(function (l) { lines.push({ type: "added", text: l }); });
        } else if (op[0] === "delete") { lh = esc(L.join("\n")); L.forEach(function (l) { lines.push({ type: "deleted", text: l }); }); }
        else { rh = esc(R.join("\n")); R.forEach(function (l) { lines.push({ type: "added", text: l }); }); }
        blocks.push({ id: "b-" + (++bi), tag: op[0], left_lines: L, right_lines: R, left_html: lh, right_html: rh });
      });
    }
    return { from: { release: fromRel, is_dropped: dropA, version: vA }, to: { release: toRel, is_dropped: dropB, version: vB },
             aligned_blocks: blocks, diff_lines: lines };
  }

  function loadDiffView() {
    if (!EL.rec || !EL.from || !EL.to) {
      var o = document.getElementById("ve-diff-output");
      if (o) o.innerHTML = '<div class="ve-placeholder ve-placeholder-small">' + esc(t("no_data")) + "</div>";
      return;
    }
    try {
      EL.diff = performClientDiff(EL.rec, EL.from, EL.to);
      renderDiffContent();
      updateAuditBox(EL.diff);
    } catch (err) {
      var out = document.getElementById("ve-diff-output");
      if (out) out.innerHTML = '<div class="ve-error">' + esc(t("err_diff", { msg: err.message })) + "</div>";
    }
  }

  function renderDiffContent() {
    var out = document.getElementById("ve-diff-output");
    if (!out || !EL.diff) return;
    if (EL.mode === "unified") renderUnified(EL.diff, out);
    else if (EL.mode === "raw") renderRaw(EL.diff, out);
    else renderSide(EL.diff, out);
  }

  function renderSide(d, container) {
    var blocks = d.aligned_blocks || [];
    if (!blocks.length) { container.innerHTML = '<div class="ve-placeholder ve-placeholder-small">' + esc(t("no_data")) + "</div>"; return; }
    var L = "", R = "";
    if (d.to && d.to.is_dropped) {
      blocks.forEach(function (b) {
        var tx = b.left_html || esc(b.left_lines.join("\n"));
        if (tx.trim()) L += '<div class="ve-block ve-block-deleted" data-block-id="' + b.id + '" data-tag="delete">' + tx + "</div>";
      });
      R = '<div class="ve-block-tombstone"><div class="ve-tombstone-icon">🚫</div><h4>' + esc(t("drop_title", { rel: d.to.release })) +
        "</h4><p>" + esc(t("drop_text", { rel: d.to.release })) + '</p><span class="ve-pill-dropped">' + esc(t("last_state", { rel: d.from.release })) + "</span></div>";
    } else {
      blocks.forEach(function (b) {
        var lh = b.left_html || esc(b.left_lines.join("\n")), rh = b.right_html || esc(b.right_lines.join("\n"));
        if (b.tag === "delete") { L += '<div class="ve-block ve-block-deleted" data-block-id="' + b.id + '" data-tag="delete">' + lh + "</div>"; R += '<div class="ve-block ve-block-anchor" data-block-id="' + b.id + '" data-tag="delete"></div>'; }
        else if (b.tag === "replace") { L += '<div class="ve-block ve-block-replaced ve-block-left" data-block-id="' + b.id + '" data-tag="replace">' + lh + "</div>"; R += '<div class="ve-block ve-block-replaced ve-block-right" data-block-id="' + b.id + '" data-tag="replace">' + rh + "</div>"; }
        else if (b.tag === "equal") { L += '<div class="ve-block ve-block-equal" data-block-id="' + b.id + '" data-tag="equal">' + lh + "</div>"; R += '<div class="ve-block ve-block-equal" data-block-id="' + b.id + '" data-tag="equal">' + lh + "</div>"; }
        else { L += '<div class="ve-block ve-block-anchor" data-block-id="' + b.id + '" data-tag="insert"></div>'; R += '<div class="ve-block ve-block-added" data-block-id="' + b.id + '" data-tag="insert">' + rh + "</div>"; }
      });
    }
    var hash = function (v) { return C.versionHash(v); };
    container.innerHTML = '<div class="ve-split-diff-wrapper" id="ve-split-diff-wrapper"><div class="ve-split-columns">' +
      '<div class="ve-split-pane ve-split-left"><div class="ve-split-header ve-header-left"><span>' + esc(t("base")) + " <strong>" + esc(d.from.release) +
      '</strong></span><code>#' + esc(hash(d.from.version)) + '</code></div><div class="ve-split-body" id="ve-pane-left">' + L + "</div></div>" +
      '<div class="ve-split-gutter" id="ve-split-gutter"><div class="ve-split-header ve-header-gutter"><span>Diff</span></div>' +
      '<div class="ve-gutter-canvas-wrap"><svg class="ve-gutter-svg" id="ve-gutter-svg" width="100%" height="100%" aria-hidden="true"></svg></div></div>' +
      '<div class="ve-split-pane ve-split-right"><div class="ve-split-header ve-header-right"><span>' + esc(t("target")) + " <strong>" + esc(d.to.release) +
      "</strong></span><code>#" + esc(d.to.is_dropped ? t("st_removed") : hash(d.to.version)) + '</code></div><div class="ve-split-body" id="ve-pane-right">' + R + "</div></div>" +
      "</div></div>";
    container.querySelectorAll(".ve-block").forEach(function (el) {
      var id = el.getAttribute("data-block-id");
      el.addEventListener("mouseenter", function () {
        container.querySelectorAll('[data-block-id="' + id + '"]').forEach(function (x) { x.classList.add("is-hovered"); });
        var path = container.querySelector('path[data-connector-id="' + id + '"]');
        if (path) path.classList.add("is-hovered");
      });
      el.addEventListener("mouseleave", function () {
        container.querySelectorAll('[data-block-id="' + id + '"]').forEach(function (x) { x.classList.remove("is-hovered"); });
        var path = container.querySelector('path[data-connector-id="' + id + '"]');
        if (path) path.classList.remove("is-hovered");
      });
    });
    initPiecewiseSyncScroll(document.getElementById("ve-split-diff-wrapper"), document.getElementById("ve-pane-left"),
      document.getElementById("ve-pane-right"), blocks, redrawSvgConnectors);
  }

  // Abschnittsweise synchrones Scrollen und SVG-Verbinder (aus dem bisherigen Viewer übernommen)
  function initPiecewiseSyncScroll(wrapper, paneLeft, paneRight, blocks, redrawFn) {
    if (!wrapper || !paneLeft || !paneRight || !blocks || blocks.length === 0) return;

    let blockLayouts = [];
    let cumV = [0];
    let V_total = 0;
    let globalS = 0;
    let isProgrammatic = false;

    function measureLayout() {
      blockLayouts = [];
      cumV = [0];
      let runningV = 0;

      for (let i = 0; i < blocks.length; i++) {
        const b = blocks[i];
        const elL = paneLeft.querySelector(`[data-block-id="${b.id}"]`);
        const elR = paneRight.querySelector(`[data-block-id="${b.id}"]`);

        const hL = (elL && b.tag !== 'insert') ? elL.offsetHeight : 0;
        const topL = elL ? elL.offsetTop : (i > 0 ? blockLayouts[i - 1].botL : 0);
        const botL = topL + hL;

        const hR = (elR && b.tag !== 'delete') ? elR.offsetHeight : 0;
        const topR = elR ? elR.offsetTop : (i > 0 ? blockLayouts[i - 1].botR : 0);
        const botR = topR + hR;

        const hV = Math.max(hL, hR);
        runningV += hV;
        cumV.push(runningV);

        blockLayouts.push({
          id: b.id,
          tag: b.tag,
          topL, hL, botL,
          topR, hR, botR,
          hV,
          startV: cumV[i],
          endV: runningV
        });
      }

      V_total = runningV;
    }

    function getTargetsForS(S) {
      if (blockLayouts.length === 0) return { targetL: 0, targetR: 0 };
      if (S <= 0) return { targetL: 0, targetR: 0 };

      let k = 0;
      while (k < blockLayouts.length - 1 && S >= blockLayouts[k].endV) {
        k++;
      }

      const blk = blockLayouts[k];
      const offset = S - blk.startV;
      const t = blk.hV > 0 ? Math.min(1, Math.max(0, offset / blk.hV)) : 0;

      const targetL = blk.topL + t * blk.hL;
      const targetR = blk.topR + t * blk.hR;

      return { targetL, targetR };
    }

    function getSFromR(scrollTopR) {
      if (blockLayouts.length === 0) return 0;
      for (let i = 0; i < blockLayouts.length; i++) {
        const blk = blockLayouts[i];
        if (scrollTopR >= blk.topR && (scrollTopR < blk.botR || i === blockLayouts.length - 1)) {
          const t = blk.hR > 0 ? (scrollTopR - blk.topR) / blk.hR : 0;
          return blk.startV + t * blk.hV;
        }
      }
      return 0;
    }

    function getSFromL(scrollTopL) {
      if (blockLayouts.length === 0) return 0;
      for (let i = 0; i < blockLayouts.length; i++) {
        const blk = blockLayouts[i];
        if (scrollTopL >= blk.topL && (scrollTopL < blk.botL || i === blockLayouts.length - 1)) {
          const t = blk.hL > 0 ? (scrollTopL - blk.topL) / blk.hL : 0;
          return blk.startV + t * blk.hV;
        }
      }
      return 0;
    }

    function applyScroll(S) {
      const maxScrollL = Math.max(0, paneLeft.scrollHeight - paneLeft.clientHeight);
      const maxScrollR = Math.max(0, paneRight.scrollHeight - paneRight.clientHeight);
      const viewH = Math.min(paneLeft.clientHeight || 500, paneRight.clientHeight || 500);
      const maxS = Math.max(0, V_total - viewH);

      globalS = Math.max(0, Math.min(maxS, S));
      const targets = getTargetsForS(globalS);

      isProgrammatic = true;
      paneLeft.scrollTop = Math.min(maxScrollL, Math.max(0, targets.targetL));
      paneRight.scrollTop = Math.min(maxScrollR, Math.max(0, targets.targetR));

      if (redrawFn) redrawFn();
      requestAnimationFrame(() => { isProgrammatic = false; });
    }

    paneLeft.addEventListener('scroll', () => {
      if (isProgrammatic) return;
      const S = getSFromL(paneLeft.scrollTop);
      applyScroll(S);
    }, { passive: true });

    paneRight.addEventListener('scroll', () => {
      if (isProgrammatic) return;
      const S = getSFromR(paneRight.scrollTop);
      applyScroll(S);
    }, { passive: true });

    wrapper._syncController = {
      scrollToBlock: (blockId) => {
        const idx = blockLayouts.findIndex(b => b.id === blockId);
        if (idx >= 0) {
          applyScroll(blockLayouts[idx].startV);
        }
      },
      applyScroll: applyScroll,
      measure: measureLayout
    };

    setTimeout(() => {
      measureLayout();
      applyScroll(0);
    }, 20);

    if (window.ResizeObserver) {
      const ro = new ResizeObserver(() => {
        measureLayout();
        if (redrawFn) redrawFn();
      });
      ro.observe(paneLeft);
      ro.observe(paneRight);
    }
  }

  function redrawSvgConnectors() {
    const wrapper = document.getElementById('ve-split-diff-wrapper');
    const svg = document.getElementById('ve-gutter-svg');
    const gutter = document.getElementById('ve-split-gutter');
    if (!wrapper || !svg || !EL.diff || !EL.diff.aligned_blocks) return;

    const canvasWrap = (gutter && gutter.querySelector('.ve-gutter-canvas-wrap')) || gutter;
    if (canvasWrap) {
      const gH = canvasWrap.offsetHeight || (gutter ? gutter.offsetHeight : 0);
      if (gH > 0) {
        svg.setAttribute('height', gH);
        svg.style.height = gH + 'px';
      }
    }

    const svgRect = svg.getBoundingClientRect();
    const W = Math.round(svg.getBoundingClientRect().width) || 70;
    const blocks = EL.diff.aligned_blocks;
    let pathsHtml = '';

    blocks.forEach(b => {
      if (b.tag === 'equal') return;

      const leftEl = wrapper.querySelector(`#ve-pane-left [data-block-id="${b.id}"]`);
      const rightEl = wrapper.querySelector(`#ve-pane-right [data-block-id="${b.id}"]`);
      if (!leftEl || !rightEl) return;

      const lRect = leftEl.getBoundingClientRect();
      const rRect = rightEl.getBoundingClientRect();

      const y1Top = lRect.top - svgRect.top;
      const y1Bot = (b.tag === 'insert') ? y1Top : (lRect.bottom - svgRect.top);
      const y2Top = rRect.top - svgRect.top;
      const y2Bot = (b.tag === 'delete') ? y2Top : (rRect.bottom - svgRect.top);

      const cp1x = W * 0.45;
      const cp2x = W * 0.55;

      let d = '';
      let cls = 've-connector ';

      if (b.tag === 'replace') {
        cls += 've-connector-replace';
        d = `M 0 ${y1Top} C ${cp1x} ${y1Top}, ${cp2x} ${y2Top}, ${W} ${y2Top} L ${W} ${y2Bot} C ${cp2x} ${y2Bot}, ${cp1x} ${y1Bot}, 0 ${y1Bot} Z`;
      } else if (b.tag === 'delete') {
        cls += 've-connector-delete';
        d = `M 0 ${y1Top} C ${cp1x} ${y1Top}, ${cp2x} ${y2Top}, ${W} ${y2Top} L ${W} ${y2Top} C ${cp2x} ${y2Top}, ${cp1x} ${y1Bot}, 0 ${y1Bot} Z`;
      } else if (b.tag === 'insert') {
        cls += 've-connector-insert';
        d = `M 0 ${y1Top} C ${cp1x} ${y1Top}, ${cp2x} ${y2Top}, ${W} ${y2Top} L ${W} ${y2Bot} C ${cp2x} ${y2Bot}, ${cp1x} ${y1Top}, 0 ${y1Top} Z`;
      }

      pathsHtml += `<path d="${d}" class="${cls}" data-connector-id="${b.id}"><title>${b.tag.toUpperCase()}: ${b.id}</title></path>`;
    });

    svg.innerHTML = pathsHtml;

    svg.querySelectorAll('.ve-connector').forEach(path => {
      const id = path.dataset.connectorId;
      path.addEventListener('mouseenter', () => {
        wrapper.querySelectorAll(`[data-block-id="${id}"]`).forEach(b => b.classList.add('is-hovered'));
        path.classList.add('is-hovered');
      });
      path.addEventListener('mouseleave', () => {
        wrapper.querySelectorAll(`[data-block-id="${id}"]`).forEach(b => b.classList.remove('is-hovered'));
        path.classList.remove('is-hovered');
      });
      path.addEventListener('click', () => {
        if (wrapper._syncController && typeof wrapper._syncController.scrollToBlock === 'function') {
          wrapper._syncController.scrollToBlock(id);
        }
      });
    });
  }

  function renderUnified(d, container) {
    if (!d.diff_lines || !d.diff_lines.length) { container.innerHTML = '<div class="ve-placeholder ve-placeholder-small">' + esc(t("identical")) + "</div>"; return; }
    container.innerHTML = '<div class="ve-unified-container">' + d.diff_lines.map(function (l) {
      var m = l.type === "added" ? "+" : (l.type === "deleted" ? "−" : " ");
      return '<div class="ve-diff-line ve-diff-' + l.type + '"><span class="ve-diff-marker">' + m + '</span><span class="ve-diff-text">' + esc(l.text) + "</span></div>";
    }).join("") + "</div>";
  }

  function renderRaw(d, container) {
    var v = d.to && d.to.version, dropped = d.to && d.to.is_dropped;
    container.innerHTML = '<div class="ve-raw"><div class="ve-raw-head">' + esc(t("raw_version")) + " " +
      esc(v ? v.version_id : (dropped ? t("st_removed") + " (" + d.to.release + ")" : t("none"))) + "</div><pre>" +
      esc(v ? C.decodeFully(v.content) : (dropped ? t("raw_dropped") : t("raw_empty"))) + "</pre></div>";
  }

  function updateAuditBox(d) {
    var v = d.to && d.to.version, dropped = d.to && d.to.is_dropped;
    var set = function (id, txt) { var el = document.getElementById(id); if (el) el.textContent = txt; };
    if (dropped) {
      set("ve-audit-actor", t("a_removed_actor")); set("ve-audit-hash", t("a_removed_hash"));
      set("ve-audit-recorded", t("a_since", { rel: d.to.release })); set("ve-audit-evidence", t("a_not_in", { rel: d.to.release }));
      return;
    }
    if (!v) return;
    var meta = v.meta || {};
    set("ve-audit-actor", meta.source_pdf ? t("a_release_pdf", { pdf: meta.source_pdf }) : (meta.actor || meta.trigger_kind || t("a_ingest")));
    set("ve-audit-hash", (String(v.version_id).split("#")[1] || "").substring(0, 8) || "–");
    set("ve-audit-recorded", v.recorded_at || "–");
    set("ve-audit-evidence", meta.source_pdf ? t("a_pdf", { pdf: meta.source_pdf }) + (meta.source_page ? " · " + t("page_n", { p: meta.source_page }) : "") : t("a_ingest"));
  }

  // ------------------------------------------------------------------ Schaubild-/Snippet-Viewer
  function loadItem(tab, id, userAction) {
    var r = ui[tab];
    var my = ++token[tab];
    var signal = newSignal(tab);
    shown[tab] = null;   // der Viewer zeigt jetzt „Lade …“, nicht mehr das vorige Element
    r.vbody.innerHTML = '<div class="ve-placeholder">' + esc(t("loading_detail", { id: id })) + "</div>";
    fetchJson(ROOT + "versions/explorer/items/" + encodeURIComponent(C.itemFile(id, stems("item"))), signal).then(function (info) {
      if (my !== token[tab]) return;
      shown[tab] = id;
      r.vbody.innerHTML = itemHtml(tab, info);
      r.vbody.parentNode.scrollTop = 0;
      fillPdfLinks(r.vbody);
      fillCanonLinks(r.vbody);
      figObserve(r.vbody);
      if (userAction && !narrowMQ.matches) r.list.focus({ preventScroll: true });
    }).catch(function (err) {
      // Überholt (neue Auswahl, Zurück im Verlauf) oder Seite verlassen: kein Fehlerhinweis
      if (my !== token[tab] || C.isAbortError(err) || pageHidden) return;
      shown[tab] = null;
      r.vbody.innerHTML = errorHtml(err);
    });
  }

  // KI-Beschreibung des Schaubilds (Item-Feld "ai", export_explorer.ai_info): oben im Viewer, Markdown sicher
  // gerendert, mit Herkunft (Modell, Rezept, Datum, beschriebene Fassung); lange Texte eingeklappt.
  function fmtDate(iso) {
    var d = new Date(iso + (String(iso).length === 10 ? "T00:00:00Z" : ""));
    if (isNaN(d.getTime())) return String(iso);
    try { return d.toLocaleDateString(LANG, { year: "numeric", month: "2-digit", day: "2-digit", timeZone: "UTC" }); }
    catch (e) { return String(iso).slice(0, 10); }
  }
  function aiHtml(info) {
    var ai = info.ai;
    if (!ai || !ai.md) {
      return '<section class="ve-sect ve-ai ve-ai-none"><h3>' + esc(t("ai_head")) + '</h3><p class="ve-muted">' + esc(t("ai_none")) + "</p></section>";
    }
    var prov = [];
    if (ai.model) prov.push(esc(ai.model));
    if (ai.recipe) prov.push(esc(t("ai_recipe", { r: ai.recipe })));
    if (ai.at) prov.push(esc(t("ai_at", { d: fmtDate(ai.at) })));
    var rel = (ai.rel || []).join(", ");
    var of = ai.of && ai.of !== info.id
      ? t("ai_of_other", { rel: rel || "–", id: ai.of })
      : t("ai_of_self", { rel: rel || "–" });
    var long = String(ai.md).length > 900;
    return '<section class="ve-sect ve-ai" aria-labelledby="ve-ai-h-' + esc(info.id) + '">' +
      '<h3 id="ve-ai-h-' + esc(info.id) + '"><span class="ve-ai-mark" aria-hidden="true">✦</span> ' + esc(t("ai_head")) + "</h3>" +
      '<p class="ve-ai-prov">' + prov.join('<span aria-hidden="true"> · </span>') + "</p>" +
      '<p class="ve-ai-of">' + esc(of) + (ai.full === false ? ' <span class="ve-ai-short">' + esc(t("ai_short")) + "</span>" : "") + "</p>" +
      '<div class="ve-ai-body' + (long ? "" : " is-open") + '" id="ve-ai-b-' + esc(info.id) + '">' + C.renderMarkdown(ai.md) + "</div>" +
      (long ? '<button type="button" class="ve-btn ve-ai-toggle" data-act="ai-toggle" aria-expanded="false" aria-controls="ve-ai-b-' +
        esc(info.id) + '">' + esc(t("ai_more")) + "</button>" : "") +
      '<p class="ve-ai-note">' + esc(t("ai_note")) + "</p></section>";
  }

  function itemHtml(tab, info) {
    var isFig = tab === "fig";
    var platform = info.platform || "";
    var rels = info.releases || [];
    var h = '<div class="ve-vh"><div class="ve-vh-top"><h2 class="ve-vh-id ve-vh-title">' + esc(info.caption || info.id) + "</h2></div>" +
      '<div class="ve-vh-name"><code>' + esc(info.id) + '</code><span class="ve-kind">' + esc(t(!isFig && info.src === "manifest" ? "src_section" : "src_" + (info.src || "matrix"))) + "</span></div>" +
      '<dl class="ve-meta">' +
      (info.doc ? "<div><dt>" + esc(t("lbl_doc")) + "</dt><dd>" + esc(info.doc) + (info.page ? " · " + esc(t("page_n", { p: info.page })) : "") + "</dd></div>" : "") +
      (platform ? "<div><dt>" + esc(t("lbl_plat")) + "</dt><dd>" + esc(platLabel(platform)) + "</dd></div>" : "") +
      (rels.length ? "<div><dt>" + esc(t("lbl_releases")) + "</dt><dd>" + esc(rels.join(", ")) + "</dd></div>" : "") +
      "</dl>" +
      '<div class="ve-links">' + canonLink(info.id, "ve-linkbtn-primary") +
      (info.doc ? pdfAnchor(info.doc, rels.filter(function (r) { return /^R\d\d-\d\d$/.test(r); }), info.page, platform) : "") + "</div></div>";
    if (isFig) {
      if (info.sha) h += '<div class="ve-figbig">' + thumbHtml(info.sha, info.caption, "big") + "</div>";
      h += aiHtml(info);
      var described = info.ai && info.ai.of;
      var series = info.series || [];
      if (series.length) {
        h += '<section class="ve-sect"><h3>' + esc(t("series_head", { n: series.length })) + '</h3><ol class="ve-series">';
        series.forEach(function (s) {
          var cur = s.id === info.id;
          var label = (s.releases || []).join(", ") || "–";
          h += '<li class="ve-series-item' + (cur ? " is-current" : "") + '">' +
            (s.sha ? '<span class="ve-series-thumb">' + thumbHtml(s.sha, label, "tiny") + "</span>" : "") +
            '<span class="ve-series-txt"><strong>' + esc(label) + "</strong>" +
            (described && s.id === described ? ' <span class="ve-ai-badge" title="' + esc(t("ai_head")) + '">✦ ' + esc(t("ai_badge")) + "</span>" : "") +
            (s.page ? " · " + esc(t("page_n", { p: s.page })) : "") +
            (/^FIG-/.test(s.id) ? ' · <code>' + esc(s.id) + "</code> " + canonLink(s.id, "ve-linkbtn-small") : "") +
            (s.caption ? '<span class="ve-series-cap">' + esc(s.caption) + "</span>" : "") + "</span></li>";
        });
        h += "</ol></section>";
      }
      var occ = info.occurrences || [];
      if (occ.length) {
        h += '<section class="ve-sect"><h3>' + esc(t("occ_head")) + '</h3><ul class="ve-occ">';
        occ.forEach(function (o) {
          var url = C.occurrencePdfUrl(o.pdf, o.page);
          h += "<li><strong>" + esc(o.release || "") + "</strong> · " + esc(o.doc || "") + (o.page ? " · " + esc(t("page_n", { p: o.page })) : "") +
            (url ? ' · <a href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">PDF</a>' : "") + "</li>";
        });
        h += "</ul></section>";
      }
    }
    if (info.text) {
      h += '<section class="ve-sect"><h3>' + esc(t(isFig ? "fig_text_head" : "text_head")) + '</h3><div class="ve-fulltext">' + linkIds(esc(info.text), null) + "</div></section>";
    }
    var targets = info.targets || [];
    var D = data.el;
    var targetIds = targets.map(function (tg) { return tg.id; });
    // Im Text zitierte Kennungen, die nicht schon zugeordnet sind
    var cited = C.citedIds(C.decodeEntities((info.caption || "") + "\n" + (info.text || ""))).filter(function (id) {
      return targetIds.indexOf(id) < 0;
    });
    if (cited.length) {
      h += '<section class="ve-sect"><h3>' + esc(t("cited_ids_head", { n: num(cited.length) })) + '</h3><div class="ve-idchips">' +
        cited.map(function (id) { return linkIds(esc(id), null); }).join(" ") + "</div></section>";
    }
    h += '<section class="ve-sect"><h3>' + esc(t("targets_head", { n: num(targets.length) })) + '</h3><ul class="ve-targets">';
    targets.forEach(function (tg) {
      var k = C.resolveId(D, tg.id);
      var target = k >= 0 ? D.ids[k] : null;
      var name = k >= 0 ? D.names[k] : "";
      var ref = k >= 0 && D.ref[k] === 1;
      h += "<li>" + (target ? '<button type="button" class="ve-target" data-open-el="' + esc(target) + '" data-el-view="' + (ref ? "cit" : (isFig ? "fig" : "snip")) +
        '"><code>' + esc(tg.id) + "</code>" + (name ? " " + esc(name) : "") + (target !== tg.id ? " → <code>" + esc(target) + "</code>" : "") + "</button>" +
        (ref ? ' <span class="ve-mini ve-mini-ref">' + esc(t("k_cited")) + "</span>" : "") :
        '<code>' + esc(tg.id) + '</code> <span class="ve-muted">' + esc(t("not_in_catalog")) + "</span>") +
        '<div class="ve-cardmeta">' + evidenceMeta({ role: tg.role, conf: tg.conf, m: tg.m, rel: tg.rel }) + "</div>" +
        (tg.why ? '<div class="ve-why"><span>' + esc(t("why")) + ":</span> " + esc(tg.why) + "</div>" : "") + "</li>";
    });
    h += "</ul></section>";
    return h;
  }

  // ------------------------------------------------------------------ Layout
  function layout() {
    var tab = state.tab, r = ui[tab];
    if (!r) return;
    var md = r.md;
    var top = md.getBoundingClientRect().top + window.scrollY;
    var h = Math.max(420, window.innerHeight - top - 16);
    app.style.setProperty("--ve-md-h", h + "px");
    r.vlist.render();
  }
  window.addEventListener("resize", function () {
    layout();
    if (EL.mode === "side") redrawSvgConnectors();
    ["el", "fig", "snip"].forEach(function (tab) { if (ui[tab]) setDetailMode(tab, !!selectedKey(tab) && narrowMQ.matches); });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      var r = ui[state.tab];
      if (r && r.panel.classList.contains("facets-open")) { setFacetsOpen(state.tab, false); r.ftoggle.focus(); }
    }
  });

  // ------------------------------------------------------------------ Start
  // Deep-Link auch als Fragment: versions.html#SWS_X oder #id=SWS_X
  if (!state.id && window.location.hash) {
    var hm = /^#(?:id=)?([A-Za-z][\w.\-]*)$/.exec(window.location.hash);
    if (hm) {
      state.id = hm[1];
      try { window.history.replaceState(null, "", window.location.pathname + C.serializeState(state)); } catch (e) { /* ignore */ }
    }
  }
  build();
  // Mit einem Element in der URL (ohne Filter) steht der Viewer im Vordergrund, der Katalog ist eingeklappt
  ["el", "fig", "snip"].forEach(function (tab) {
    if (selectedKey(tab) && !state[tab].q && !C.activeCount(state, tab)) setCollapsed(tab, true);
  });
  try { window.scrollTo(0, 0); } catch (e) { /* ignore */ }
  ["el", "fig", "snip"].forEach(function (tab) { ui[tab].q.value = state[tab].q || ""; });
  switchTab(state.tab, false);
  if (state.tab !== "el") ensureLoaded("el").then(function () { refresh("el"); syncViewer("el"); });
  layout();
})();
