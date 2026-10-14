/*
 * versions-explorer.js — Versions- & Provenienz-Explorer (<lang>/versions.html)
 *
 * Elemente, Schaubilder, Snippets und Fragen & Diskussionen als Master-Detail-Ansicht mit
 * kombinierbaren Facetten. Daten: versions/explorer/{elements,figures,snippets}.json und
 * versions/explorer/items/<id>.json (export_explorer.py), versions/explorer/questions.json und
 * versions/explorer/questions/<Q-…>.json (export_questions.py, Fragen-Speicher), Versionsdaten aus
 * versions/data/<id>.json. Fehlt der Explorer-Index, dient versions/catalog.json
 * als Rückfall (nur Suche und Grundfilter).
 *
 * Dateinamen je Kennung folgen _src/tools/case_safe_names.py: schlicht <id>, bei
 * Kennungen, die sich nur in der Schreibweise unterscheiden, <id>~<Maske>. Welche
 * Stämme abweichen, steht in elements.json ("names") bzw. im "file" des Katalogs.
 *
 * Der reine Kern (Zustand <-> URL, Facettenfilter, Zählungen, Gruppieren & Sortieren, abbruchsicheres
 * Laden, Markdown der KI-Beschreibungen) ist unter Node als module.exports verfügbar und wird
 * von _src/tests/test_versions_explorer.py und test_figure_access.py geprüft.
 *
 * Laden (docs/design/versions-explorer-load.md): Das Kopfskript der Seite (versions.json "head_html") holt
 * den Kopf des aktiven Index (<name>.head.json: erste Zeilen, Facettenzähler) bzw. bei Filtern, Suche oder
 * Gruppierung gleich den vollen Index; der Explorer übernimmt ihn (takeBoot). Schaubild- und Snippet-Index
 * kommen ohne elements.json aus; der Elementindex lädt im Leerlauf nach dem ersten Zeichnen.
 *
 * Gruppieren & Sortieren: bis zu drei Ebenen (Gruppierung + Sortierung je Ebene), in der URL (g/s, fg/fs,
 * sg/ss) und je Browser in localStorage ("autodocs-ve-order"); Gruppenköpfe sind Zeilen der virtuellen Liste.
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
          ["role", "frole", 1], ["id", "fid"]],
    snip: [["q", "sq"], ["plat", "splat", 1], ["mod", "smod", 1], ["doc", "sdoc"], ["role", "srole", 1],
           ["id", "sid"]],
    // Fragen & Diskussionen (Fragen-Speicher): Art, Status, Plattform, Modul, Gegenstand (qsub, z. B.
    // element:adaptive:SWS_CM_00093). Deep-Link versions.html?tab=q&id=Q-… (id gehört dann der Frage).
    q: [["q", "qq"], ["kind", "qkind", 1], ["st", "qst", 1], ["plat", "qplat", 1], ["mod", "qmod", 1],
        ["sub", "qsub", 1], ["id", "qid"]]
  };
  var TABS = ["el", "fig", "snip", "q"];
  var VIEWS = ["ver", "fig", "snip", "cit"];
  var UNIVERSES = ["CP", "AP", "FO", "other"];

  function emptyState() {
    // from/to: Vergleich im Element-Viewer (Releases); ffrom/fto bzw. sfrom/sto: Schaubild-Reihe (Fassungen)
    // bzw. Snippet (Releases). Sie gehören zur Auswahl, nicht zu den Filtern (zählen nicht in activeCount).
    var s = { tab: "el", id: "", view: "ver", from: "", to: "", ffrom: "", fto: "", sfrom: "", sto: "", el: {}, fig: {}, snip: {}, q: {} };
    TABS.forEach(function (t) {
      PARAMS[t].forEach(function (p) { s[t][p[0]] = p[2] ? [] : ""; });
      s[t].g = []; s[t].s = [];   // Gruppierung/Sortierung (Ebenen), kein Filter
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
    s.from = (u.get("from") || u.get("fromRel") || "").trim();
    s.to = (u.get("to") || u.get("toRel") || "").trim();
    ["ffrom", "fto", "sfrom", "sto"].forEach(function (k) { s[k] = (u.get(k) || "").trim(); });
    TABS.forEach(function (t) {
      PARAMS[t].forEach(function (p) {
        var v = u.get(p[1]);
        if (v == null && t === "el" && p[0] === "q") v = u.get("query");
        if (v == null) return;
        s[t][p[0]] = p[2] ? v.split(",").map(function (x) { return x.trim(); }).filter(Boolean) : v.trim();
      });
      s[t].g = parseOrderList(t, u.get(ORDER_PARAMS[t][0]), "g");
      s[t].s = parseOrderList(t, u.get(ORDER_PARAMS[t][1]), "s");
    });
    // Deep-Link einer Frage: versions.html?tab=q&id=Q-… (die Diskussionsverweise der Guides)
    if (s.tab === "q" && !s.q.id && /^Q-[0-9a-f]{16}$/.test(s.id)) { s.q.id = s.id; s.id = ""; }
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
      if (s[t].g && s[t].g.length) u.set(ORDER_PARAMS[t][0], orderListText(s[t].g));
      if (s[t].s && s[t].s.length) u.set(ORDER_PARAMS[t][1], orderListText(s[t].s));
    });
    // Frage im eigenen Reiter: kanonisch als id (versions.html?tab=q&id=Q-…), solange kein Element offen ist
    if (s.tab === "q" && s.q.id && !s.id) { u.delete("qid"); u.set("id", s.q.id); }
    if (s.id) u.set("id", s.id);
    if (s.id && s.view && s.view !== "ver") u.set("view", s.view);
    if (s.id && s.from && s.to) { u.set("from", s.from); u.set("to", s.to); }
    if (s.fig.id && s.ffrom && s.fto) { u.set("ffrom", s.ffrom); u.set("fto", s.fto); }
    if (s.snip.id && s.sfrom && s.sto) { u.set("sfrom", s.sfrom); u.set("sto", s.sto); }
    var out = u.toString().replace(/%2C/g, ",").replace(/%3A/g, ":");
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
      counts: raw.counts || {}, byId: new Map(), hay: null,
      // Suchtext erst bei der ersten Suche (haystack): spart beim Start ~43 000 Zeichenketten
      mkHay: function () {
        var h = new Array(n);
        for (var k = 0; k < n; k++) {
          var m = c.mod[k] >= 0 ? raw.modules[c.mod[k]] : "";
          h[k] = (c.id[k] + " " + (c.name[k] || "") + " " + m).toLowerCase();
        }
        return h;
      }
    };
    for (var i = 0; i < n; i++) idx.byId.set(c.id[i], i);
    return idx;
  }

  // Kleinschreibung des Suchtexts je Eintrag, beim ersten Bedarf gebaut
  function haystack(idx) {
    if (!idx.hay) idx.hay = idx.mkHay();
    return idx.hay;
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
    return facetFilter(idx.n, elementGroups(idx), sel, String(sel.q || "").trim() ? textMatcher(haystack(idx), sel.q) : null);
  }

  // ------------------------------------------------------------------ Schaubilder & Snippets

  // Schaubild-/Snippet-Index. v2 (export_explorer.slim_item_index, "cols"): Wörterbücher, Anzahl der Ziele
  // (nt) und deren Module (mod) sind vorberechnet; der Reiter braucht dafür elements.json nicht. v1 (ältere
  // Indizes, Testdaten: id/title/doc/…/targets je Feld) leitet die Module über elementIdx aus den Zielen ab.
  var ITEM_ROLES = ["constitutive", "heuristic"];
  function decodeItems(raw, elementIdx) {
    var v2 = !!(raw && raw.cols);
    var c = v2 ? raw.cols : raw;
    var n = c.id.length;
    var it = { n: n, ids: c.id, title: c.title, page: c.page, v2: v2,
               platCode: null, docCode: null, roleBits: null, modBits: null, nt: null, relCode: null,
               nser: c.nser || null, conf: c.conf || null, sha: v2 ? null : (c.sha || null),
               hay: null, byId: new Map(), names: (v2 && raw.names) || {}, counts: (v2 && raw.counts) || null,
               dict: { plat: [], doc: [], role: ITEM_ROLES.slice(), mod: [], modUni: [], relsets: [] } };
    for (var i = 0; i < n; i++) it.byId.set(c.id[i], i);
    if (v2) {
      it.platCode = c.plat; it.docCode = c.doc; it.roleBits = c.role; it.modBits = c.mod; it.nt = c.nt;
      it.relCode = c.rel;
      it.dict.plat = raw.platforms || []; it.dict.doc = raw.docs || []; it.dict.relsets = raw.relsets || [];
      it.dict.mod = raw.modules || []; it.dict.modUni = raw.module_universe || [];
      if (raw.roles && raw.roles.length) it.dict.role = raw.roles.slice();
    } else {
      var plats = it.dict.plat, docs = it.dict.doc, rels = it.dict.relsets, pi = {}, di = {}, ri = {};
      it.platCode = new Array(n); it.docCode = new Array(n); it.roleBits = new Array(n); it.modBits = new Array(n);
      it.nt = new Array(n); it.relCode = new Array(n);
      var mods = elementIdx && elementIdx.full ? elementIdx.dict.mod : [];
      it.dict.mod = mods;
      it.dict.modUni = (elementIdx && elementIdx.dict.modUni) || [];
      // Ältere Indizes ohne role-Spalte bleiben filterbar (keine Rolle = kein Treffer bei gesetztem Filter).
      var roleCol = Array.isArray(c.role) ? c.role : [];
      for (var j = 0; j < n; j++) {
        var p = c.plat[j] || "";
        if (!(p in pi)) { pi[p] = plats.length; plats.push(p); }
        it.platCode[j] = pi[p];
        var d = c.doc[j] || "";
        if (!(d in di)) { di[d] = docs.length; docs.push(d); }
        it.docCode[j] = di[d];
        var rs = (c.rel && c.rel[j]) || "";
        if (!(rs in ri)) { ri[rs] = rels.length; rels.push(rs); }
        it.relCode[j] = ri[rs];
        var rb = 0;
        String(roleCol[j] || "").split(",").forEach(function (r) {
          var k = ITEM_ROLES.indexOf(r); if (k >= 0) rb |= (1 << k);
        });
        it.roleBits[j] = rb;
        var tg = c.targets[j] || [];
        it.nt[j] = tg.length;
        var ms = [];
        if (mods.length) {
          tg.forEach(function (tid) {
            var e = elementIdx.byId.get(tid);
            if (e != null && elementIdx.mod[e] >= 0 && ms.indexOf(elementIdx.mod[e]) < 0) ms.push(elementIdx.mod[e]);
          });
        }
        it.modBits[j] = ms;
      }
    }
    if (!it.nser) { it.nser = new Array(n); for (var z = 0; z < n; z++) it.nser[z] = 0; }
    var D = it.dict.doc, dc = it.docCode;
    it.docOf = function (k) { return D[dc[k]] || ""; };
    it.mkHay = function () {
      var h = new Array(n);
      for (var k = 0; k < n; k++) h[k] = (c.id[k] + " " + (c.title[k] || "") + " " + (D[dc[k]] || "")).toLowerCase();
      return h;
    };
    // Dokumente alphabetisch für die Auswahlliste
    it.docOrder = D.map(function (x, k) { return k; }).sort(function (a, b) {
      return String(D[a]).localeCompare(String(D[b]));
    });
    return it;
  }

  // Braucht ein Schaubild-/Snippet-Index elements.json zum Dekodieren (v1: Module aus den Zielen)?
  function itemsNeedElements(raw) { return !(raw && raw.cols); }

  function itemGroups(it, kind) {
    var g = [
      { key: "plat", type: "one", get: function (i) { return it.platCode[i]; }, values: it.dict.plat },
      { key: "doc", type: "one", get: function (i) { return it.docCode[i]; }, values: it.dict.doc },
      { key: "mod", type: "many", get: function (i) { return it.modBits[i]; }, values: it.dict.mod }
    ];
    // Konstitutiv/heuristisch gilt für Snippets und Schaubilder (Matrix-Rolle je Zuordnung).
    // Bildreihen bleiben ein zusätzliches Kriterium nur der Schaubilder.
    g.push({ key: "role", type: "bits", get: function (i) { return it.roleBits[i]; }, values: it.dict.role,
             bit: function (k) { return 1 << k; } });
    if (kind === "fig") {
      g.push({ key: "multi", type: "flags", get: function (i) { return it.nser[i] > 1 ? 1 : 0; }, values: ["1"],
               bit: function () { return 1; } });
    }
    return g;
  }

  // Katalog und Filterliste: gleicher Start in allen Reitern. Eine Auswahl, auch per Deep-Link,
  // klappt sie nicht ein; das tut nur der Schalter.
  function catalogCollapsedOnLoad() { return false; }

  function filterItems(it, kind, sel) {
    return facetFilter(it.n, itemGroups(it, kind), sel, String(sel.q || "").trim() ? textMatcher(haystack(it), sel.q) : null);
  }

  // ------------------------------------------------------------------ Fragen & Diskussionen

  // Index der Fragen (export_questions.py, versions-explorer-questions@1): Wörterbücher für Art, Status, Plattform,
  // Modul, Ausgang und Gegenstände; Suchtext = Kennung, Frage und "x" (Annahme, Begründung, englische Form,
  // Verlauf, Gegenstände).
  function decodeQuestions(raw) {
    var c = raw.cols, n = c.id.length;
    var D = { n: n, ids: c.id, title: c.title, kind: c.kind, st: c.st, plat: c.plat, modBits: c.mod, sub: c.sub,
              oc: c.oc, na: c.na, ne: c.ne || [], at: c.at || [], x: c.x || [], asr: c.asr || [], byId: new Map(),
              hay: null, counts: raw.counts || null, names: {},
              dict: { kind: raw.kinds || [], st: raw.statuses || [], plat: raw.platforms || [], mod: raw.modules || [],
                      modUni: raw.module_universe || [], oc: raw.outcomes || [], sub: raw.subjects || [] } };
    for (var i = 0; i < n; i++) D.byId.set(c.id[i], i);
    D.mkHay = function () {
      var h = new Array(n);
      for (var k = 0; k < n; k++) h[k] = (c.id[k] + " " + (c.title[k] || "") + " " + ((c.x && c.x[k]) || "")).toLowerCase();
      return h;
    };
    return D;
  }

  function questionGroups(D) {
    return [
      { key: "kind", type: "one", get: function (i) { return D.kind[i]; }, values: D.dict.kind },
      { key: "st", type: "one", get: function (i) { return D.st[i]; }, values: D.dict.st },
      { key: "plat", type: "one", get: function (i) { return D.plat[i]; }, values: D.dict.plat },
      { key: "mod", type: "many", get: function (i) { return D.modBits[i] || []; }, values: D.dict.mod },
      { key: "sub", type: "many", get: function (i) { return D.sub[i] || []; }, values: D.dict.sub }
    ];
  }

  function filterQuestions(D, sel) {
    return facetFilter(D.n, questionGroups(D), sel, String(sel.q || "").trim() ? textMatcher(haystack(D), sel.q) : null);
  }

  // Gegenstand einer Frage (subject_key "art:plattform:name") -> {type, platform, name}
  function parseSubject(key) {
    var m = /^([a-z]+):([a-z]*):(.+)$/.exec(String(key || ""));
    return m ? { type: m[1], platform: m[2], name: m[3] } : { type: "", platform: "", name: String(key || "") };
  }

  // ------------------------------------------------------------------ Gruppieren & Sortieren
  // Bis zu ORDER_MAX Ebenen je Reiter, jede ein Paar aus Gruppierung (Feld, Richtung) und Sortierung (Feld,
  // Richtung). Gruppen schachteln sich in Ebenenfolge (Ebene 1 außen); innerhalb der innersten Gruppe gilt die
  // Sortierung in Ebenenfolge, danach die Indexreihenfolge (Kennung). Beides wirkt auf die gefilterte Trefferliste.
  // URL: el g/s, fig fg/fs, snip sg/ss; Felder kommagetrennt, „-“ vorn = absteigend (z. B. g=mod,-kind&s=id).
  var ORDER_MAX = 3;
  var ORDER_PARAMS = { el: ["g", "s"], fig: ["fg", "fs"], snip: ["sg", "ss"], q: ["qg", "qs"] };
  var STATUS_PRIO = [4, 1, 2, 8];          // primärer Status: entfallen vor neu vor geändert vor unverändert
  var STATUS_RANK = { 1: 0, 2: 1, 4: 2, 8: 3 };
  var MISSING = -1;                        // fehlender Wert: Gruppe „ohne Angabe“, beim Sortieren immer zuletzt

  function lowerRank(strings) {
    // Rang je Eintrag nach Kleinschreibung (schneller als localeCompare; stabil über die Indexreihenfolge)
    var n = strings.length, idx = new Array(n), low = new Array(n), rank = new Float64Array(n);
    for (var i = 0; i < n; i++) { idx[i] = i; low[i] = String(strings[i] || "").toLowerCase(); }
    idx.sort(function (a, b) { return low[a] < low[b] ? -1 : low[a] > low[b] ? 1 : a - b; });
    for (var k = 0; k < n; k++) rank[idx[k]] = strings[idx[k]] ? k : MISSING;
    return rank;
  }
  function dictRank(values) {
    // Code -> Rang nach Beschriftung (alphabetisch)
    var r = lowerRank(values), out = {};
    for (var k = 0; k < values.length; k++) out[k] = r[k];
    return out;
  }
  function codeKeys(codes, rank) {
    var n = codes.length, out = new Float64Array(n);
    for (var i = 0; i < n; i++) { var c = codes[i]; out[i] = c == null || c < 0 || rank[c] === MISSING ? MISSING : rank[c]; }
    return out;
  }
  function numKeys(n, get) {
    var out = new Float64Array(n);
    for (var i = 0; i < n; i++) { var v = get(i); out[i] = v == null || v < 0 ? MISSING : v; }
    return out;
  }
  // Release-Menge (Text „R19-11 R20-11“) -> erstes/letztes Release als Rang über alle vorkommenden Releases
  function relsetEnds(D) {
    if (D._relEnds) return D._relEnds;
    var sets = D.dict.relsets || [], all = [];
    var parts = sets.map(function (s) { var p = String(s || "").split(/\s+/).filter(Boolean); all = all.concat(p); return p; });
    var rels = sortReleases(all), ri = {};
    rels.forEach(function (r, k) { ri[r] = k; });
    var first = [], last = [];
    parts.forEach(function (p) {
      var ks = p.map(function (r) { return ri[r]; });
      first.push(ks.length ? Math.min.apply(null, ks) : MISSING);
      last.push(ks.length ? Math.max.apply(null, ks) : MISSING);
    });
    D._relEnds = { rels: rels, first: first, last: last };
    return D._relEnds;
  }
  function confBucket(c) { return c == null || c < 0 ? MISSING : c >= 90 ? 3 : c >= 70 ? 2 : c >= 50 ? 1 : 0; }

  // Felder je Reiter: g = gruppierbar, s = sortierbar; keys(D) -> Schlüssel je Eintrag (Zahl, MISSING = keiner)
  // für die Gruppierung (gkeys, falls abweichend) und die Sortierung; label(D, key, tr) -> Gruppenkopf.
  var ORDER_FIELDS = {
    el: [
      { f: "kind", g: 1, s: 1, keys: function (D) { return codeKeys(D.kind, dictRank(D.dict.kind)); },
        label: function (D, k, tr) { return tr.kind(D.dict.kind[rankCode(D, "kind", k)]); } },
      { f: "plat", g: 1, s: 1, keys: function (D) { return codeKeys(D.plat, dictRank(D.dict.plat)); },
        label: function (D, k, tr) { return tr.plat(D.dict.plat[rankCode(D, "plat", k)]); } },
      { f: "mod", g: 1, s: 1, keys: function (D) { return codeKeys(D.mod, dictRank(D.dict.mod)); },
        label: function (D, k) { return D.dict.mod[rankCode(D, "mod", k)]; } },
      { f: "cl", g: 1, s: 1, keys: function (D) { return codeKeys(D.cl, dictRank(D.dict.cl)); },
        label: function (D, k) { return D.dict.cl[rankCode(D, "cl", k)]; } },
      { f: "doc", g: 1, s: 1, keys: function (D) { return codeKeys(D.doc, dictRank(D.dict.doc)); },
        label: function (D, k, tr) { var v = D.dict.doc[rankCode(D, "doc", k)]; return v === "other" ? tr.t("doc_other") : v; } },
      { f: "st", g: 1, s: 1, keys: function (D) {
          return numKeys(D.n, function (i) {
            for (var p = 0; p < STATUS_PRIO.length; p++) if (D.st[i] & STATUS_PRIO[p]) return STATUS_RANK[STATUS_PRIO[p]];
            return MISSING;
          });
        }, label: function (D, k, tr) { return tr.t("st_" + STATUS[k][0]); } },
      { f: "first", g: 1, s: 1, keys: function (D) { return numKeys(D.n, function (i) { return D.first[i]; }); },
        label: function (D, k) { return D.dict.rel[k]; } },
      { f: "last", g: 1, s: 1, keys: function (D) { return numKeys(D.n, function (i) { return D.last[i]; }); },
        label: function (D, k) { return D.dict.rel[k]; } },
      { f: "fig", g: 1, s: 1, gkeys: function (D) { return numKeys(D.n, function (i) { return D.fig[i] > 0 ? 0 : 1; }); },
        keys: function (D) { return numKeys(D.n, function (i) { return D.fig[i]; }); },
        label: function (D, k, tr) { return tr.t(k === 0 ? "has_fig" : "grp_no_fig"); } },
      { f: "snip", g: 1, s: 1, gkeys: function (D) { return numKeys(D.n, function (i) { return D.snip[i] > 0 ? 0 : 1; }); },
        keys: function (D) { return numKeys(D.n, function (i) { return D.snip[i]; }); },
        label: function (D, k, tr) { return tr.t(k === 0 ? "has_snip" : "grp_no_snip"); } },
      { f: "ai", g: 1, s: 1, keys: function (D) { return numKeys(D.n, function (i) { return D.ai[i] ? 0 : 1; }); },
        label: function (D, k, tr) { return tr.t(k === 0 ? "has_ai" : "grp_no_ai"); } },
      { f: "nv", g: 1, s: 1, keys: function (D) { return numKeys(D.n, function (i) { return D.nv[i]; }); },
        label: function (D, k, tr) { return tr.t("grp_versions", { n: k }); } },
      { f: "name", s: 1, keys: function (D) { return lowerRank(D.names); } },
      { f: "id", s: 1, keys: function (D) { return numKeys(D.n, function (i) { return i; }); } }
    ],
    fig: [
      { f: "doc", g: 1, s: 1, keys: itemDocKeys, label: itemDocLabel },
      { f: "series", g: 1, s: 1, keys: function (D) { return numKeys(D.n, function (i) { return D.nser[i] > 1 ? 0 : 1; }); },
        label: function (D, k, tr) { return tr.t(k === 0 ? "grp_series" : "grp_single"); } },
      { f: "nver", g: 1, s: 1, keys: function (D) { return numKeys(D.n, function (i) { return D.nser[i]; }); },
        label: function (D, k, tr) { return tr.t("series_n", { n: k }); } },
      { f: "mod", g: 1, s: 1, keys: itemModKeys, label: itemModLabel },
      { f: "plat", g: 1, s: 1, keys: itemPlatKeys, label: itemPlatLabel },
      { f: "role", g: 1, s: 1, keys: itemRoleKeys, label: itemRoleLabel },
      { f: "conf", g: 1, s: 1, gkeys: function (D) { return numKeys(D.n, function (i) { return confBucket(D.conf ? D.conf[i] : -1); }); },
        keys: function (D) { return numKeys(D.n, function (i) { return D.conf ? D.conf[i] : -1; }); },
        label: function (D, k, tr) { return tr.t("grp_conf_" + k); } },
      { f: "page", s: 1, keys: function (D) { return numKeys(D.n, function (i) { return D.page[i] || -1; }); } },
      { f: "title", s: 1, keys: function (D) { return lowerRank(D.title); } },
      { f: "id", s: 1, keys: function (D) { return numKeys(D.n, function (i) { return i; }); } }
    ],
    snip: [
      { f: "doc", g: 1, s: 1, keys: itemDocKeys, label: itemDocLabel },
      { f: "plat", g: 1, s: 1, keys: itemPlatKeys, label: itemPlatLabel },
      { f: "mod", g: 1, s: 1, keys: itemModKeys, label: itemModLabel },
      { f: "role", g: 1, s: 1, keys: itemRoleKeys, label: itemRoleLabel },
      { f: "nt", g: 1, s: 1, keys: function (D) { return numKeys(D.n, function (i) { return D.nt[i]; }); },
        label: function (D, k, tr) { return tr.t("n_elements", { n: k }); } },
      { f: "first", g: 1, s: 1, keys: function (D) { var e = relsetEnds(D); return codeKeys(D.relCode, e.first); },
        label: function (D, k) { return relsetEnds(D).rels[k]; } },
      { f: "last", g: 1, s: 1, keys: function (D) { var e = relsetEnds(D); return codeKeys(D.relCode, e.last); },
        label: function (D, k) { return relsetEnds(D).rels[k]; } },
      { f: "page", s: 1, keys: function (D) { return numKeys(D.n, function (i) { return D.page[i] || -1; }); } },
      { f: "title", s: 1, keys: function (D) { return lowerRank(D.title); } },
      { f: "id", s: 1, keys: function (D) { return numKeys(D.n, function (i) { return i; }); } }
    ],
    q: [
      { f: "qst", g: 1, s: 1, keys: function (D) { return numKeys(D.n, function (i) { return D.st[i]; }); },
        label: function (D, k, tr) { return tr.t("qs_" + D.dict.st[k]); } },
      { f: "qkind", g: 1, s: 1, keys: function (D) { return codeKeys(D.kind, dictRank(D.dict.kind)); },
        label: function (D, k, tr) { return tr.t("qk_" + D.dict.kind[rankCode(D, "kind", k)]); } },
      { f: "plat", g: 1, s: 1, keys: function (D) { return codeKeys(D.plat, dictRank(D.dict.plat)); },
        label: function (D, k, tr) { return tr.plat(D.dict.plat[rankCode(D, "plat", k)]); } },
      { f: "mod", g: 1, s: 1, keys: itemModKeys, label: itemModLabel },
      { f: "qsub", g: 1, s: 1, keys: function (D) {
          var r = dictRank(D.dict.sub), many = D.dict.sub.length;
          return numKeys(D.n, function (i) { var ss = D.sub[i] || []; return !ss.length ? MISSING : ss.length > 1 ? many : r[ss[0]]; });
        }, label: function (D, k, tr) { return k === D.dict.sub.length ? tr.t("grp_multi_sub") : tr.sub(D.dict.sub[rankCode(D, "sub", k)]); } },
      { f: "qoc", g: 1, s: 1, keys: function (D) { return codeKeys(D.oc, dictRank(D.dict.oc)); },
        label: function (D, k, tr) { return tr.t("qo_" + D.dict.oc[rankCode(D, "oc", k)]); } },
      { f: "qna", g: 1, s: 1, keys: function (D) { return numKeys(D.n, function (i) { return D.na[i]; }); },
        label: function (D, k, tr) { return tr.t("q_anchors_n", { n: k }); } },
      { f: "qat", s: 1, keys: function (D) { return lowerRank(D.at); } },
      { f: "title", s: 1, keys: function (D) { return lowerRank(D.title); } },
      { f: "id", s: 1, keys: function (D) { return numKeys(D.n, function (i) { return i; }); } }
    ]
  };
  // Rang -> Code für Wörterbuchfelder (Beschriftung der Gruppe)
  function rankCode(D, f, rank) {
    D._rankCode = D._rankCode || {};
    if (!D._rankCode[f]) {
      var r = dictRank(D.dict[f] || []), inv = {};
      Object.keys(r).forEach(function (c) { inv[r[c]] = +c; });
      D._rankCode[f] = inv;
    }
    return D._rankCode[f][rank];
  }
  function itemDocKeys(D) { return codeKeys(D.docCode, dictRank(D.dict.doc)); }
  function itemDocLabel(D, k) { return D.dict.doc[rankCode(D, "doc", k)]; }
  function itemPlatKeys(D) { return codeKeys(D.platCode, dictRank(D.dict.plat)); }
  function itemPlatLabel(D, k, tr) { return tr.plat(D.dict.plat[rankCode(D, "plat", k)]); }
  // Module eines Eintrags: genau eines -> dieses, mehrere -> eigene Gruppe „mehrere Module“ (hinter allen)
  function itemModKeys(D) {
    var r = dictRank(D.dict.mod), many = D.dict.mod.length;
    return numKeys(D.n, function (i) {
      var ms = D.modBits[i] || [];
      return !ms.length ? MISSING : ms.length > 1 ? many : r[ms[0]];
    });
  }
  function itemModLabel(D, k, tr) { return k === D.dict.mod.length ? tr.t("grp_multi_mod") : D.dict.mod[rankCode(D, "mod", k)]; }
  var ROLE_RANK = { 1: 0, 2: 1, 3: 2 };
  function itemRoleKeys(D) { return numKeys(D.n, function (i) { var b = D.roleBits[i]; return b in ROLE_RANK ? ROLE_RANK[b] : MISSING; }); }
  function itemRoleLabel(D, k, tr) {
    return [tr.t("role_constitutive"), tr.t("role_heuristic"), tr.t("role_constitutive") + " + " + tr.t("role_heuristic")][k];
  }

  function orderField(tab, f) {
    var list = ORDER_FIELDS[tab] || [];
    for (var k = 0; k < list.length; k++) if (list[k].f === f) return list[k];
    return null;
  }
  // "mod,-kind" -> [{f:"mod",d:1},{f:"kind",d:-1}] (nur bekannte Felder der Art, höchstens ORDER_MAX, ohne Doppelte)
  function parseOrderList(tab, text, kind) {
    var out = [], seen = {};
    String(text || "").split(",").forEach(function (x) {
      x = x.trim();
      var d = 1;
      if (x.charAt(0) === "-") { d = -1; x = x.slice(1); }
      var fd = orderField(tab, x);
      if (!fd || !fd[kind] || seen[x] || out.length >= ORDER_MAX) return;
      seen[x] = 1;
      out.push({ f: x, d: d });
    });
    return out;
  }
  function orderListText(list) {
    return (list || []).map(function (o) { return (o.d < 0 ? "-" : "") + o.f; }).join(",");
  }
  function orderActive(s, tab) { return !!((s[tab].g && s[tab].g.length) || (s[tab].s && s[tab].s.length)); }

  // Schlüssel je Feld einmal je Index berechnen
  function fieldKeys(D, tab, f, forGroup) {
    var fd = orderField(tab, f);
    var name = (forGroup && fd.gkeys ? "g:" : "s:") + f;
    D._okeys = D._okeys || {};
    if (!D._okeys[name]) D._okeys[name] = (forGroup && fd.gkeys ? fd.gkeys : fd.keys)(D);
    return D._okeys[name];
  }

  /**
   * Treffer (Indizes) gruppieren und sortieren. Liefert { order: sortierte Indizes, groups: [{level, key, start,
   * end, path, parent}] } (start/end in order; Gruppen in Ausgabereihenfolge, Eltern vor Kindern).
   */
  function orderRows(D, tab, matches, spec) {
    var G = (spec.g || []).map(function (o) { return { k: fieldKeys(D, tab, o.f, true), d: o.d, f: o.f }; });
    var S = (spec.s || []).map(function (o) { return { k: fieldKeys(D, tab, o.f, false), d: o.d }; });
    var keys = G.concat(S), L = keys.length;
    var order = matches.slice();
    if (L) {
      order.sort(function (a, b) {
        for (var l = 0; l < L; l++) {
          var K = keys[l].k, x = K[a], y = K[b];
          if (x !== y) {
            if (x === MISSING) return 1;          // ohne Angabe immer zuletzt
            if (y === MISSING) return -1;
            return (x - y) * keys[l].d;
          }
        }
        return a - b;
      });
    }
    var groups = [];
    if (G.length) {
      var open = [];                              // offene Gruppe je Ebene
      for (var p = 0; p < order.length; p++) {
        var i = order[p], changed = false;
        for (var l = 0; l < G.length; l++) {
          var key = G[l].k[i];
          if (!changed && open[l] && open[l].key === key) continue;
          changed = true;
          if (open[l]) open[l].end = p;
          var parent = l ? open[l - 1] : null;
          var grp = { level: l, key: key, start: p, end: order.length, f: G[l].f,
                      path: (parent ? parent.path + "|" : "") + G[l].f + "=" + key, parent: parent };
          groups.push(grp);
          open[l] = grp;
        }
      }
    }
    return { order: order, groups: groups };
  }

  // Sichtbare Einträge der Liste: Zeilen als Index (>= 0), Gruppenköpfe als -(Nummer + 1); eingeklappte Gruppen
  // (Pfade in collapsed) ohne ihren Inhalt
  function flattenOrder(ordered, collapsed) {
    var order = ordered.order, groups = ordered.groups, out = [];
    if (!groups.length) return order;
    var g = 0, p = 0, n = order.length;
    collapsed = collapsed || {};
    while (p < n || g < groups.length) {
      if (g < groups.length && groups[g].start === p) {
        var grp = groups[g];
        out.push(-(g + 1));
        if (collapsed[grp.path]) {
          // Gruppe samt Untergruppen überspringen
          var end = grp.end;
          g++;
          while (g < groups.length && groups[g].start < end) g++;
          p = end;
          continue;
        }
        g++;
        continue;
      }
      out.push(order[p]);
      p++;
    }
    return out;
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
  // Angezeigter Wortlaut einer Fassung: Zeilenend-Trennungen und abgetrennte Plural-„s“ zusammengeführt
  // (export_versions/text_rejoin.py, Vermerk rejoin.e = [Beginn, Länge, Ersatz] in UTF-16-Einheiten über content).
  // Der gespeicherte Wortlaut (content, Rohansicht) bleibt unverändert.
  function shownContent(v) {
    var s = (v && v.content) || "", r = v && v.rejoin;
    if (!r || r.applied || !r.e || !r.e.length) return s;
    var out = "", pos = 0;
    for (var i = 0; i < r.e.length; i++) {
      var e = r.e[i];
      if (e[0] < pos || e[0] + e[1] > s.length) return s;
      out += s.slice(pos, e[0]) + e[2];
      pos = e[0] + e[1];
    }
    return out + s.slice(pos);
  }

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
  // Vergleichsschlüssel der Zeitachse: text_key aus dem Export (spec_text_key, derselbe Vergleich wie das
  // Release-Dropdown: Seitenkopf und -fuß, Trennungen, Schreibweise zählen nicht). Nur wenn eine Zeile ihn
  // nicht trägt (ältere Exporte), vergleichen alle Zeilen den Wortlaut ohne Leerraum und Bindestriche.
  function contentKeyFn(versions) {
    var all = (versions || []).every(function (v) { return v.text_captured === false || !!v.text_key; });
    return all ? function (v) { return "k:" + v.text_key; } : function (v) { return "n:" + normContent(v.content); };
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
    var seen = {}, cur = null, pres = null, prevRel = null, lastContent = null, keyOf = contentKeyFn(byRel);
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
      var n = keyOf(v), h = versionHash(v);
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

  /**
   * Zeitachse eines Snippets aus seiner Detaildatei (export_explorer: items/<id>.json):
   *   series – Spannen des kanonischen Snippet-Manifests in Release-Folge (releases, hash, page)
   *   trel   – Release, aus dem der gespeicherte Wortlaut stammt (Snippet-Speicher text_release)
   *   tstat  – Herkunft des Wortlauts (section, page, caption, placeholder)
   *   releases, drop – Releases mit Snippet; erstes Release, in dem es fehlt
   * Der Speicher hält genau einen Wortlaut je Snippet. Abschnitte:
   *   content  – Spannen mit demselben Inhalts-Hash wie die Spanne des gespeicherten Wortlauts (vergleichbar)
   *   other    – Spannen mit anderem Inhalts-Hash: der Wortlaut weicht ab, ist aber nicht erfasst
   *   presence – Releases ohne Spannen-Hash, in denen das Snippet vorkommt (Wortlaut nicht erfasst)
   *   dropped  – Snippet ab diesem Release nicht mehr vorhanden
   * Aufeinanderfolgende Spannen gleichen Inhalts bilden einen Abschnitt (isInitial/isChange/isRevert wie
   * buildTimeline).
   */
  function snippetTimeline(info) {
    info = info || {};
    if (info.rv && info.rv.length) return releaseTextTimeline(info);
    var hasText = !!String(info.text || "").trim() && info.tstat !== "placeholder";
    var trel = info.trel || null;
    var spans = (info.series || []).filter(function (x) { return x && x.releases && x.releases.length; });
    var segs = [];
    if (spans.length && spans.every(function (x) { return !!x.hash; })) {
      var own = null;
      spans.forEach(function (x) { if (trel && x.releases.indexOf(trel) >= 0) own = x; });
      if (!own && hasText && !trel) own = spans[spans.length - 1];   // Beschriftung: neueste Spanne
      var textHash = hasText && own ? own.hash : null;
      var seen = {}, cur = null, last = null;
      spans.forEach(function (x) {
        if (cur && cur.hash === x.hash) { x.releases.forEach(function (r) { cur.releases.push(r); }); return; }
        var differs = last !== null && last !== x.hash;
        var shot = x.screenshot_path || x.screenshot || null;
        cur = { type: textHash && x.hash === textHash ? "content" : "other", hash: x.hash, releases: x.releases.slice(),
                page: x.page || null, screenshot: shot, isInitial: last === null, isChange: differs && !seen[x.hash], isRevert: differs && !!seen[x.hash] };
        seen[x.hash] = 1; last = x.hash;
        segs.push(cur);
      });
    } else {
      var rels = (info.releases || []).slice();
      if (trel && rels.indexOf(trel) < 0) {
        rels.push(trel);
        if (rels.every(function (r) { return /^R\d\d-\d\d$/.test(r); })) rels = sortReleases(rels);
      }
      var textRel = hasText ? (trel || rels[rels.length - 1] || null) : null;
      var run = null;
      rels.forEach(function (r) {
        var ty = r === textRel ? "content" : "presence";
        if (run && run.type === ty && ty === "presence") { run.releases.push(r); return; }
        var shot = ty === "content" ? (info.screenshot_path || info.screenshot || null) : null;
        run = { type: ty, releases: [r], page: ty === "content" ? (info.page || null) : null, screenshot: shot,
                isInitial: !segs.some(function (x) { return x.type === "content"; }), isChange: false, isRevert: false };
        segs.push(run);
      });
    }
    if (info.drop) segs.push({ type: "dropped", releases: [info.drop], from: info.drop });
    return segs;
  }

  /**
   * Zeitachse aus dem Wortlaut je Release (export_explorer.release_versions, Quelle snippet_release_texts.py):
   *   rv – Releases in Folge: {r, t (Index in rt), m (section, caption, page_excerpt, none), p, pdf, cut, cl}
   *   rt – bereinigte Texte, rk – Vergleichsschlüssel je Text (spec_text_key, wie bei den Elementen)
   * Abschnitte wie buildTimeline: aufeinanderfolgende Releases mit gleichem Schlüssel bilden einen Abschnitt
   * (content); Releases ohne vergleichbaren Wortlaut (Überschrift nicht gefunden, kein PDF) bilden nocapture.
   */
  var COMPARABLE = { section: 1, caption: 1, page_excerpt: 1 };
  function releaseTextTimeline(info) {
    var segs = [], seen = {}, cur = null, gap = null, lastKey = null, rt = info.rt || [], rk = info.rk || [];
    var spanShots = {};
    (info.series || []).forEach(function (sp) {
      if (sp && sp.releases && (sp.screenshot_path || sp.screenshot)) {
        var s = sp.screenshot_path || sp.screenshot;
        sp.releases.forEach(function (r) { spanShots[r] = s; });
      }
    });
    info.rv.forEach(function (v) {
      var vShot = v.screenshot || v.screenshot_path || spanShots[v.r] || null;
      if (!COMPARABLE[v.m] || v.t == null || rt[v.t] == null) {
        cur = null;
        var reason = v.m === "page_excerpt" ? "page_excerpt" : "none";
        if (gap && gap.reason === reason) {
          gap.releases.push(v.r);
          if (vShot && !gap.screenshot) gap.screenshot = vShot;
          return;
        }
        gap = { type: "nocapture", reason: reason, releases: [v.r], page: v.p || null, screenshot: vShot };
        segs.push(gap);
        return;
      }
      gap = null;
      var k = rk[v.t] || "t" + v.t;
      if (cur && cur.key === k) {
        cur.releases.push(v.r); cur.entries.push(v);
        if (cur.texts.indexOf(v.t) < 0) cur.texts.push(v.t);
        if (vShot && !cur.screenshot) cur.screenshot = vShot;
        return;
      }
      var differs = lastKey !== null && lastKey !== k;
      cur = { type: "content", key: k, releases: [v.r], entries: [v], texts: [v.t], page: v.p || null,
              screenshot: vShot,
              isInitial: lastKey === null, isChange: differs && !seen[k], isRevert: differs && !!seen[k] };
      seen[k] = 1; lastKey = k;
      segs.push(cur);
    });
    if (info.drop) segs.push({ type: "dropped", releases: [info.drop], from: info.drop });
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

  function snippetScreenshotUrl(root, shot) {
    if (!shot) return "";
    if (/^https?:\/\//i.test(shot)) return shot;
    var clean = String(shot).replace(/^\/?(?:_src\/)?/, "");
    return (root || "") + clean;
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
  // Wurzel der Site aus der eigenen Skriptadresse (<wurzel>/static/versions-explorer.js), absolut.
  // Hängt nicht am style.css-Link im Kopf, den ein Inhaltsaustausch aus einem anderen Verzeichnis
  // stehen lassen kann (Wurzel dann ../../ statt ../ und alle Abrufe landen neben der Site).
  function rootFromSrc(src) {
    var m = /^(.*\/)static\/versions-explorer\.js(?:[?#].*)?$/.exec(String(src || ""));
    return m ? m[1] : "";
  }
  // Die lokale API (_src/serve.py) liegt immer unter /api/ der Origin-Wurzel eines lokalen Rechners.
  // Sie kann nur zur Site gehören, wenn die Site auf localhost selbst an der Wurzel liegt; unter
  // GitHub Pages (https://…/autodocs/) gehört /api/ jemand anderem und wird nie abgefragt.
  // root: absolute Wurzel der Site.
  function localApiAllowed(root) {
    var u;
    try { u = new URL(String(root || "")); } catch (e) { return false; }
    return /^https?:$/.test(u.protocol) && u.pathname === "/" &&
      /^(localhost|127\.0\.0\.1|\[::1\])$/.test(u.hostname);
  }
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
  // der KI-Ausgabe, z. B. lokale file:-Pfade). Rohes HTML erscheint als Text.
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


  // ------------------------------------------------------------------ Zeitachse und Vergleich (geteilt)
  // Karten der Revisions-Zeitachse und Vergleich zweier Fassungen für Elemente und Snippets (static/text-diff.js,
  // TD.revisions). Gemeinsam genutzt vom Explorer-Viewer, der Record-Seite (<lang>/spec/record.html) und den
  // Belegseiten (static/evidence-sections.js): dieselben Karten, Bedienung und Texte (versions-explorer-i18n.js).
  // o: { t: Übersetzer, esc, TD: window.TextDiff, root: Site-Wurzel für Seitenbilder }
  function revisionKit(o) {
    o = o || {};
    var t = o.t || function (k) { return k; }, esc = o.esc || escHtml, TD = o.TD, ROOT = o.root || "";
    var C = { releaseKey: releaseKey, decodeFully: decodeFully, shownContent: shownContent, versionHash: versionHash, snippetScreenshotUrl: snippetScreenshotUrl };
    function revLabels() {
      return {
        tl_title: t("tl_title"), tl_hint: t("tl_hint"), cmp: t("cmp"), left: t("ep_left"), right: t("ep_right"),
        right_drop: t("ep_right_drop"), swap: t("swap"), swap_title: t("swap_title"), base_side: t("base"), target_side: t("target"),
        mode_side: t("mode_side"), mode_unified: t("mode_unified"), mode_raw: t("mode_raw"), identical: t("identical"),
        no_data: t("no_data"), loading: t("td_loading"), stats: t("td_stats"), err: t("err_diff"), same: t("td_same"),
        single: t("tl_single"), mode_integrated: t("mode_integrated"), int_style: t("int_style"), int_style_a: t("int_style_a"),
        int_style_b: t("int_style_b"), int_legend_a: t("int_legend_a"), int_legend_b: t("int_legend_b"), int_removed: t("int_removed"),
        int_replaced: t("int_replaced")
      };
    }
    function spanText(rels) { rels = rels || []; return rels.length > 1 ? rels[0] + " → " + rels[rels.length - 1] : (rels[0] || "–"); }
    function relPillsHtml(rels) {
      return '<div class="ve-epoch-subreleases">' + (rels || []).map(function (r) { return '<span class="ve-epoch-rel-pill">' + esc(r) + "</span>"; }).join(" ") + "</div>";
    }
    function epochStatus(seg, rel) {
      if (seg.isChange) return { text: t("ep_changed", { rel: rel }), cls: "ve-status-changed" };
      if (seg.isRevert) return { text: t("ep_revert", { rel: rel }), cls: "ve-status-revert" };
      if (!seg.isInitial) return { text: t("ep_unchanged"), cls: "ve-status-stable" };
      return { text: t("ep_baseline"), cls: "ve-status-initial" };
    }

    // Abschnitte der Element-Zeitachse (C.buildTimeline) als Karten
    function elementSegments(rec) {
      var lc = rec.lifecycle || {};
      return (rec.timeline || []).map(function (seg) {
        var span = spanText(seg.releases), pills = relPillsHtml(seg.releases);
        if (seg.type === "absent" || seg.type === "gap") {
          var lastRel = seg.releases[seg.releases.length - 1];
          return { span: seg.type === "absent" ? t("ep_absent_until", { rel: lastRel }) : span, cls: "ve-epoch-absent",
                   status: { text: t("ep_absent"), cls: "ve-status-absent" },
                   body: "<div>" + esc(seg.type === "absent" ? t("ep_absent_text", { rel: lastRel }) : t("ep_gap_text", { rels: seg.releases.join(", ") })) +
                     "</div>" + pills };
        }
        if (seg.type === "presence" || seg.type === "unchecked") {
          var isPres = seg.type === "presence";
          return { span: span, cls: "ve-epoch-absent ve-epoch-" + seg.type,
                   status: { text: t(isPres ? "ep_presence" : "ep_unchecked"), cls: isPres ? "ve-status-presence" : "ve-status-unchecked" },
                   body: "<div>" + esc(t(isPres ? "ep_presence_text" : "ep_unchecked_text")) + "</div>" + pills };
        }
        if (seg.type === "dropped") {
          return { key: seg.from, keys: seg.releases, pick: "right", cls: "ve-epoch-dropped", span: t("ep_from", { rel: seg.from }),
                   status: { text: t("st_removed"), cls: "ve-status-dropped" },
                   body: "<div><strong>" + esc(t("ep_dropped_title")) + '</strong></div><div class="ve-epoch-subreleases ve-muted">' +
                     esc(t("ep_dropped_sub", { rels: seg.releases.join(", "), last: lc.last_active_release || "" })) + "</div>" };
        }
        var sub = seg.releases.length === 1 ? esc(t("ep_one", { hash: seg.hash8 }))
          : "<strong>" + esc(t("ep_many", { n: seg.releases.length })) + "</strong> · #" + esc(seg.hash8);
        if (seg.hashes.length > 1) sub += '<div class="ve-epoch-variants">' + esc(t("ep_variants", { n: seg.hashes.length })) + "</div>";
        // Wortlaut ohne Seitenkopf und -fuß (export_versions/record_text_cleaning.jsonl): offen benennen, was fehlt
        var cleaned = [];
        seg.versions.forEach(function (v) { ((v.cleaning || {}).removed || []).forEach(function (x) { cleaned.push(x); }); });
        if (cleaned.length) sub += '<div class="ve-epoch-cleaned" title="' + esc(t("ep_cleaned_title", { list: cleaned.join(" · ") })) +
          '">' + esc(t("ep_cleaned", { n: cleaned.length })) + "</div>";
        return { key: seg.firstRelease, keys: seg.releases, span: span, status: epochStatus(seg, seg.firstRelease),
                 body: "<div>" + sub + "</div>" + pills };
      });
    }

    function elementDiff(rec, from, to) {
      var d = performClientDiff(rec, from, to);
      var tomb = d.to.is_dropped
        ? '<div class="ve-block-tombstone"><div class="ve-tombstone-icon">🚫</div><h4>' + esc(t("drop_title", { rel: d.to.release })) +
          "</h4><p>" + esc(t("drop_text", { rel: d.to.release })) + '</p><span class="ve-pill-dropped">' + esc(t("last_state", { rel: d.from.release })) + "</span></div>"
        : null;
      function raw(x) {
        var v = x.version;
        return { head: esc(t("raw_version")) + " " + esc(v ? v.version_id : (x.is_dropped ? t("st_removed") + " (" + x.release + ")" : t("none"))),
                 html: "<pre>" + esc(v ? C.decodeFully(v.content || "") : (x.is_dropped ? t("raw_dropped") : t("raw_empty"))) + "</pre>" };
      }
      return {
        src: d, blocks: d.aligned_blocks, lines: d.diff_lines, tombstoneHtml: tomb,
        left: { label: esc(t("base")) + " <strong>" + esc(d.from.release) + "</strong>", tag: "#" + C.versionHash(d.from.version) },
        right: { label: esc(t("target")) + " <strong>" + esc(d.to.release) + "</strong>",
                 tag: "#" + (d.to.is_dropped ? t("st_removed") : C.versionHash(d.to.version)) },
        raw: { left: raw(d.from), right: raw(d.to) }
      };
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
      var linesA = formatReqLines(vA ? C.decodeFully(C.shownContent(vA)) : ""), linesB = formatReqLines(vB ? C.decodeFully(C.shownContent(vB)) : "");
      var blocks = [], lines = [], bi = 0;
      if (dropB) {
        linesA.forEach(function (l) {
          blocks.push({ id: "b-" + (++bi), tag: "delete", left_lines: [l], right_lines: [], left_html: esc(l), right_html: "" });
          lines.push({ type: "deleted", text: l });
        });
      } else {
        var al = TD.align(linesA, linesB);
        blocks = al.blocks; lines = al.lines;
      }
      return { from: { release: fromRel, is_dropped: dropA, version: vA }, to: { release: toRel, is_dropped: dropB, version: vB },
               aligned_blocks: blocks, diff_lines: lines };
    }

    function snippetSegments(info, segs) {
      return segs.map(function (seg) {
        var pills = relPillsHtml(seg.releases), span = spanText(seg.releases);
        var page = seg.page ? "<div>" + esc(t("page_n", { p: seg.page })) + "</div>" : "";
        if (seg.type === "dropped") {
          return { key: seg.from, keys: seg.releases, pick: "right", cls: "ve-epoch-dropped", span: t("ep_from", { rel: seg.from }),
                   status: { text: t("st_removed"), cls: "ve-status-dropped" }, body: "<div><strong>" + esc(t("snip_dropped")) + "</strong></div>" };
        }
        if (seg.type === "presence") {
          return { span: span, cls: "ve-epoch-absent ve-epoch-presence", status: { text: t("snip_presence"), cls: "ve-status-presence" },
                   body: "<div>" + esc(t("ep_presence_text")) + "</div>" + pills };
        }
        if (seg.type === "nocapture") {
          return { span: span, cls: "ve-epoch-absent ve-epoch-unchecked", status: { text: t("snip_nf_status"), cls: "ve-status-unchecked" },
                   body: "<div>" + esc(t(seg.reason === "page_excerpt" ? "snip_nf_page" : "snip_nf_none")) + "</div>" + page + pills };
        }
        var st = epochStatus(seg, seg.releases[0]);
        var shot = seg.screenshot || seg.screenshot_path;
        if (!shot && seg.entries) {
          for (var i = 0; i < seg.entries.length; i++) {
            if (seg.entries[i].screenshot || seg.entries[i].screenshot_path) {
              shot = seg.entries[i].screenshot || seg.entries[i].screenshot_path;
              break;
            }
          }
        }
        if (!shot && (info.screenshot_path || info.screenshot)) {
          if (seg.type === "content" || (info.trel && seg.releases && seg.releases.indexOf(info.trel) >= 0)) {
            shot = info.screenshot_path || info.screenshot;
          }
        }
        var shotBadge = "";
        if (shot) {
          var mShot = /([0-9a-f]{12})\/page_(\d+)\.webp/.exec(shot);
          var sHash = mShot ? mShot[1] : "";
          var sPage = mShot ? mShot[2] : "";
          var shotUrl = C.snippetScreenshotUrl(ROOT, shot);
          shotBadge = '<div class="ve-epoch-shot">' +
            '<a href="' + esc(shotUrl) + '" target="_blank" rel="noopener noreferrer" class="ve-shot-badge" ' +
            (sHash && sPage ? 'data-snip-hash="' + esc(sHash) + '" data-snip-page="' + esc(sPage) + '" ' : "") +
            'title="' + esc(t("open_page")) + '">' +
            '<span class="ve-shot-icon" aria-hidden="true">🖼️</span> ' + esc(t("v_snip")) +
            '</a></div>';
        }
        if (seg.type === "other") {
          return { span: span, cls: "ve-epoch-absent", status: st, body: "<div>" + esc(t("snip_other")) + "</div>" + page + pills + shotBadge };
        }
        if (seg.entries) {
          // Wortlaut je Release aus dem PDF: Quelle, Varianten, Schnitt, entfernte Seitenköpfe
          var sub = seg.releases.length === 1 ? "" : "<strong>" + esc(t("ep_many", { n: seg.releases.length })) + "</strong>";
          if (seg.texts.length > 1) sub += '<div class="ve-epoch-variants">' + esc(t("ep_variants", { n: seg.texts.length })) + "</div>";
          var ncl = 0, cut = false;
          seg.entries.forEach(function (v) {
            ncl += v.cl || 0;
            cut = cut || !!v.cut;
          });
          if (ncl) sub += '<div class="ve-epoch-cleaned">' + esc(t("ep_cleaned", { n: ncl })) + "</div>";
          if (cut) sub += '<div class="ve-epoch-cleaned">' + esc(t("snip_cut")) + "</div>";
          return { key: seg.releases[0], keys: seg.releases, span: span, status: st,
                   body: (sub ? "<div>" + sub + "</div>" : "") + page + pills + shotBadge };
        }
        var own = info.trel && seg.releases.indexOf(info.trel) >= 0;
        return { key: seg.releases[0], keys: seg.releases, span: span, status: st,
                 body: "<div>" + esc(own ? t("snip_captured_rel", { rel: info.trel }) : t("snip_captured_same")) + "</div>" + page + pills + shotBadge };
      });
    }
    // Fassungen ordnen: Präsenz-Einträge (im PDF vorhanden, Wortlaut nicht erfasst) gehören in die Zeitachse,
    // aber nicht in den Vergleich – rec.versions enthält danach nur erfassten Wortlaut. Wiederholt aufrufbar.
    function prepareRecord(rec) {
      if (!rec.allVersions) {
        rec.allVersions = sortVersions(rec.versions || []);
        rec.versions = rec.allVersions.filter(function (v) { return v.text_captured !== false; });
      }
      rec.timeline = buildTimeline(rec.allVersions, rec.lifecycle || {});
      rec.epochs = rec.timeline.filter(function (x) { return x.type === "content"; });
      return rec;
    }
    // Anfangspaar des Vergleichs: gewünschtes Paar, sonst erste gegen letzte Fassung, sonst letzte gegen Wegfall
    function initialPair(rec, from, to) {
      var versions = rec.versions || [], lifecycle = rec.lifecycle || {}, e = rec.epochs || [];
      var drop = (rec.timeline || []).filter(function (x) { return x.type === "dropped"; })[0];
      var hasRel = function (r) { return versions.some(function (v) { return v.release === r; }); };
      if (from && to && hasRel(from) && (hasRel(to) || (lifecycle.is_dropped && (lifecycle.dropped_in || []).indexOf(to) >= 0))) return [from, to];
      if (e.length > 1) return [e[0].firstRelease, e[e.length - 1].firstRelease];
      if (e.length === 1 && drop) return [e[0].lastRelease, drop.from];
      if (versions.length > 1) return [versions[0].release, versions[versions.length - 1].release];
      if (versions.length === 1) return [versions[0].release, versions[0].release];
      return [null, null];
    }
    // Revisions-Zeitachse eines Elements mit Vergleich in container (Rückgabe: Steuerobjekt von TD.revisions)
    function mountElement(container, rec, m) {
      m = m || {};
      return TD.revisions(container, {
        segments: elementSegments(rec), from: m.from, to: m.to, viewer: m.viewer || "el",
        diff: function (a, b) { return elementDiff(rec, a, b); },
        onChange: m.onChange, onRender: m.onRender
      }, { labels: revLabels(), mode: m.mode || "side", onMode: m.onMode });
    }
    // Snippet-Zeitachse (snippetTimeline) mit Vergleich der Wortlaute je Release
    function mountSnippet(box, info, m) {
      m = m || {};
      var gsegs = snippetSegments(info, snippetTimeline(info));
      if (!gsegs.length) { box.innerHTML = '<p class="ve-muted">' + esc(t("snip_notext")) + "</p>"; return null; }
      var contents = gsegs.filter(function (g) { return g.key != null && g.pick !== "right"; });
      var drop = gsegs.filter(function (g) { return g.pick === "right"; })[0] || null;
      var valid = function (k) { return !!k && gsegs.some(function (g) { return g.key != null && (g.keys || []).indexOf(k) >= 0; }); };
      var from = null, to = null;
      if (valid(m.from) && valid(m.to)) { from = m.from; to = m.to; }
      else if (contents.length > 1) { from = contents[0].key; to = contents[contents.length - 1].key; }
      else if (contents.length === 1) { from = contents[0].key; to = drop ? drop.key : contents[0].key; }
      // Wortlaut je Release (rv/rt) oder – ohne diese Angaben – der eine gespeicherte Wortlaut
      var perRel = !!(info.rv && info.rv.length), byRel = {};
      (info.rv || []).forEach(function (v) { byRel[v.r] = v; });
      function textOf(k) {
        if (!perRel) return C.decodeFully(info.text || "");
        var v = byRel[k];
        var relText = (v && v.t != null && info.rt) ? C.decodeFully(info.rt[v.t] || "") : "";
        return relText || C.decodeFully(info.text || "");
      }
      // PDF-Zeilen sind Layout-Umbrüche: zu Fließtext verbinden, dann an Satzgrenzen teilen
      function linesOf(k) { return TD.splitLong([textOf(k).replace(/\s*\n\s*/g, " ")]); }
      var isDrop = function (k) { return !!drop && k === drop.key; };
      function pageTag(k) { var v = byRel[k]; return v && v.p ? t("page_n", { p: v.p }) : ""; }
      function raw(k) {
        return { head: esc(t("raw_version")) + " " + esc(k) + (isDrop(k) ? " (" + esc(t("st_removed")) + ")" : (pageTag(k) ? " · " + esc(pageTag(k)) : "")),
                 html: "<pre>" + esc(isDrop(k) ? t("snip_dropped") : textOf(k)) + "</pre>" };
      }
      return TD.revisions(box, {
        segments: gsegs, from: from, to: to, hint: perRel ? null : t("snip_rev_hint"), viewer: m.viewer || "snip",
        emptyText: t("snip_notext"), singleText: !contents.length ? (info.text ? t("snip_rev_single") : t("snip_notext")) : (perRel ? t("tl_single") : t("snip_rev_single")),
        diff: function (a, b) {
          var al = TD.align(isDrop(a) ? [] : linesOf(a), isDrop(b) ? [] : linesOf(b));
          return {
            blocks: al.blocks, lines: al.lines,
            tombstoneHtml: isDrop(b) ? '<div class="ve-block-tombstone"><div class="ve-tombstone-icon">🚫</div><h4>' +
              esc(t("snip_drop_title", { rel: b })) + "</h4></div>" : null,
            left: { label: esc(t("base")) + " <strong>" + esc(a) + "</strong>", tag: isDrop(a) ? "" : pageTag(a) },
            right: { label: esc(t("target")) + " <strong>" + esc(b) + "</strong>", tag: isDrop(b) ? "" : pageTag(b) },
            raw: { left: raw(a), right: raw(b) }
          };
        },
        onChange: m.onChange
      }, { labels: revLabels(), mode: m.mode || "side", onMode: m.onMode });
    }
    return { revLabels: revLabels, spanText: spanText, relPillsHtml: relPillsHtml, epochStatus: epochStatus,
             elementSegments: elementSegments, elementDiff: elementDiff, performClientDiff: performClientDiff,
             formatReqLines: formatReqLines, snippetSegments: snippetSegments, prepareRecord: prepareRecord,
             initialPair: initialPair, mountElement: mountElement, mountSnippet: mountSnippet };
  }

  return {
    STATUS: STATUS, HAS: HAS, PARAMS: PARAMS, emptyState: emptyState, parseState: parseState,
    serializeState: serializeState, activeCount: activeCount, decodeElements: decodeElements,
    decodeCatalog: decodeCatalog, elementGroups: elementGroups, facetFilter: facetFilter,
    filterElements: filterElements, decodeItems: decodeItems, filterItems: filterItems, haystack: haystack,
    decodeQuestions: decodeQuestions, questionGroups: questionGroups, filterQuestions: filterQuestions,
    parseSubject: parseSubject, TABS: TABS,
    itemsNeedElements: itemsNeedElements,
    ORDER_MAX: ORDER_MAX, ORDER_FIELDS: ORDER_FIELDS, ORDER_PARAMS: ORDER_PARAMS, orderField: orderField,
    parseOrderList: parseOrderList, orderListText: orderListText, orderActive: orderActive, orderRows: orderRows,
    flattenOrder: flattenOrder,
    figureHref: figureHref, itemFile: itemFile, recordFile: recordFile, caseMask: caseMask, safeStem: safeStem,
    markedStem: markedStem, fileStem: fileStem, thumbUrl: thumbUrl, occurrencePdfUrl: occurrencePdfUrl,
    snippetScreenshotUrl: snippetScreenshotUrl,
    catalogPdfUrl: catalogPdfUrl, textMatcher: textMatcher, normContent: normContent, shownContent: shownContent, releaseKey: releaseKey,
    sortVersions: sortVersions, buildTimeline: buildTimeline, snippetTimeline: snippetTimeline, versionHash: versionHash,
    decodeEntities: decodeEntities, decodeFully: decodeFully, citedIds: citedIds, linkifyIds: linkifyIds, resolveId: resolveId,
    UNIVERSES: UNIVERSES,
    isAbortError: isAbortError, isNetworkError: isNetworkError, loadJson: loadJson, renderMarkdown: renderMarkdown,
    rootFromSrc: rootFromSrc, localApiAllowed: localApiAllowed, revisionKit: revisionKit,
    mdInline: mdInline, catalogCollapsedOnLoad: catalogCollapsedOnLoad
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

  var SELF = document.currentScript;
  function getRootPrefix() {
    var fromSrc = C.rootFromSrc(SELF && SELF.src);
    if (fromSrc) return fromSrc;
    var link = document.querySelector('link[href*="style.css"]');
    if (link) return link.getAttribute("href").replace("style.css", "") || "../";
    return "../";
  }
  var ROOT = getRootPrefix();
  var API = C.localApiAllowed(new URL(ROOT, window.location.href).href);
  // Zeitachse und Vergleich: geteilt mit Record-Seite und Belegseiten (C.revisionKit)
  var K = C.revisionKit({ t: t, esc: esc, TD: window.TextDiff, root: ROOT });
  var revLabels = K.revLabels, spanText = K.spanText, relPillsHtml = K.relPillsHtml, epochStatus = K.epochStatus,
      elementSegments = K.elementSegments, elementDiff = K.elementDiff, snippetSegments = K.snippetSegments,
      formatReqLines = K.formatReqLines;
  var narrowMQ = window.matchMedia ? window.matchMedia("(max-width: 899px)") : { matches: false };
  var wideMQ = window.matchMedia ? window.matchMedia("(min-width: 1180px)") : { matches: true };

  var state = C.parseState(window.location.search);
  var TABS = C.TABS;
  var data = { el: null, fig: null, snip: null, q: null, res: { el: null, fig: null, snip: null, q: null }, pdfCat: undefined };
  // Kopf je Index (<name>.head.json): erste Zeilen und Facettenzähler, solange der volle Index lädt
  var heads = { el: null, fig: null, snip: null, q: null };
  // Was die Liste gerade zeigt: voller Index, sonst sein Kopf
  function view(tab) { return data[tab] || heads[tab]; }
  var ui = {};
  var ROW_H = { el: 58, fig: 62, snip: 62, q: 62 };
  var PAGE = { fig: 24, snip: 30 };

  // ------------------------------------------------------------------ Gerüst
  function kindLabel(k) { return t("k_" + String(k).replace(/ /g, "_")); }
  function platLabel(p) { return t("plat_" + p); }
  // Gegenstand einer Frage für Chips und Gruppenköpfe: Kennung bzw. „Modul com“, „Cluster can“ …
  function subjectLabel(key) {
    var sj = C.parseSubject(key);
    if (sj.type === "element" || !sj.type) return sj.name;
    return t("qsub_" + sj.type, { name: sj.name });
  }
  function valueLabel(tab, key, v) {
    if (tab === "q") {
      if (key === "kind") return t("qk_" + v);
      if (key === "st") return t("qs_" + v);
      if (key === "plat") return platLabel(v);
      if (key === "sub") return subjectLabel(v);
      return v;
    }
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
  function facetTitle(key, tab) {
    if (tab === "q" && ({ kind: 1, st: 1, sub: 1 })[key]) return t({ kind: "f_qkind", st: "f_qstatus", sub: "f_qsub" }[key]);
    return t({ kind: "f_kind", plat: "f_plat", st: "f_status", has: "f_has", doc: "f_doc", mod: "f_mod",
               cl: "f_cl", first: "f_rel", last: "f_rel", chg: "f_rel", role: "f_role", multi: "f_has" }[key] || key);
  }

  function build() {
    var tabs = [["el", t("tab_el")], ["fig", t("tab_fig")], ["snip", t("tab_snip")], ["q", t("tab_q")]];
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
        '<button type="button" class="ve-btn ve-filter-toggle" data-role="ftoggle" aria-expanded="false" aria-controls="ve-facets-' +
        tab + '">' + esc(t("filters_search")) + ' <span class="ve-badge" data-role="fbadge"></span></button>' +
        '<button type="button" class="ve-btn ve-reset" data-role="reset">' + esc(t("reset")) + "</button>" +
        '<button type="button" class="ve-btn ve-collapse" data-role="collapse" aria-pressed="false" aria-controls="ve-panel-' + tab + '">' +
        esc(t("cat_hide")) + "</button>" +
        "</div>" +
        '<div class="ve-chiprow" data-role="chips"></div>' +
        '<div class="ve-notice" data-role="notice" hidden></div>' +
        '<div class="ve-md" data-role="md">' +
        '<aside class="ve-facets" id="ve-facets-' + tab + '" data-role="facets" aria-label="' + esc(t("filters")) + '">' +
        '<div class="ve-facets-head"><strong>' + esc(t("filters_search")) + '</strong><button type="button" class="ve-btn ve-facets-close" data-role="fclose">' +
        esc(t("close")) + '</button></div>' +
        // Suche oben in der Filterleiste, darunter Gruppieren & Sortieren als eingerückte Karte, dann die Facetten
        '<div class="ve-search"><span class="ve-search-icon" aria-hidden="true">⌕</span>' +
        '<input type="search" class="ve-input" autocomplete="off" spellcheck="false" data-role="q" aria-label="' +
        esc(t("ph_" + tab)) + '" placeholder="' + esc(t("ph_" + tab)) + '"></div>' +
        '<section class="ve-ocard" data-role="ocard">' +
        '<button type="button" class="ve-ohead" data-role="otoggle" aria-expanded="false" aria-controls="ve-order-' + tab + '" title="' +
        esc(t("order_hint")) + '"><span class="ve-ocaret" aria-hidden="true">▸</span><span class="ve-otitle">' + esc(t("order")) +
        '</span><span class="ve-badge" data-role="obadge"></span></button>' +
        '<div class="ve-obody" id="ve-order-' + tab + '" data-role="opanel" role="group" aria-label="' + esc(t("order")) + '" hidden></div>' +
        '</section>' +
        '<div class="ve-facets-body" data-role="fbody"></div></aside>' +
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
      // Rad am Listen- oder Filterrand bleibt im Bereich und zieht nicht die Seite mit.
      r.list.style.overscrollBehavior = "contain";
      r.facets.style.overscrollBehavior = "contain";
      r.viewer.style.overscrollBehavior = "contain";
      r.viewer.style.overflowAnchor = "none";
      wirePanel(tab, r);
    });
    app.querySelectorAll(".ve-tab").forEach(function (b) {
      b.addEventListener("click", function () { switchTab(b.getAttribute("data-tab"), true); });
      b.addEventListener("keydown", function (e) {
        var order = TABS, k = order.indexOf(b.getAttribute("data-tab"));
        if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
          e.preventDefault();
          var n = order[(k + (e.key === "ArrowRight" ? 1 : order.length - 1)) % order.length];
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
      var cur = k >= 0 ? self.items[k] : null;
      // Gruppenköpfe (Einträge < 0) sind Teil der Liste: ← klappt ein bzw. springt zum übergeordneten Kopf,
      // → klappt aus, Enter schaltet um
      if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
        if (cur == null) return;
        e.preventDefault();
        if (cur < 0) {
          var collapsed = groupCollapsed(self.tab, cur);
          if (e.key === "ArrowRight" && collapsed) toggleGroup(self.tab, k);
          else if (e.key === "ArrowLeft" && !collapsed) toggleGroup(self.tab, k);
          else if (e.key === "ArrowLeft") { var up = parentHeader(self.tab, k); if (up >= 0) self.setActive(up, true); }
        } else if (e.key === "ArrowLeft") {
          var hk = parentHeader(self.tab, k);
          if (hk >= 0) self.setActive(hk, true);
        }
        return;
      }
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
  // total: Höhe der Liste in Zeilen, wenn erst ein Teil geladen ist (Kopf); danach Platzhalter
  VList.prototype.setItems = function (items, keyOf, total) {
    this.items = items; this.keyOf = keyOf;
    this.total = Math.max(items.length, total || 0);
    this.version = (this.version || 0) + 1;
    this.space.style.height = (this.total * this.rowH) + "px";
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
    var el = this.el, n = this.items.length, h = this.rowH, total = Math.max(n, this.total || 0);
    var start = Math.max(0, Math.floor(el.scrollTop / h) - 8);
    var end = Math.min(total, Math.ceil((el.scrollTop + (el.clientHeight || 600)) / h) + 8);
    // Zeilen nur neu aufbauen, wenn sich Fenster, Daten oder geöffnetes Element ändern; sonst
    // bleiben die Knoten erhalten (ein Klick, der den Fokus setzt, trifft weiter dieselbe Zeile)
    var key = start + ":" + end + ":" + this.version + ":" + this.openKey;
    if (key !== this.lastKey) {
      var out = [];
      for (var k = start; k < end; k++) {
        if (k >= n) {
          out.push('<div class="ve-row ve-row-ph" aria-hidden="true" style="top:' + (k * h) + "px;height:" + h + 'px"></div>');
          continue;
        }
        var it = this.items[k];
        if (it < 0) {
          var gc = groupCollapsed(this.tab, it);
          out.push('<div class="ve-row ve-grow' + (gc ? " is-collapsed" : "") + '" role="option" id="ve-opt-' + this.tab + "-" + k +
            '" data-k="' + k + '" aria-selected="false" aria-expanded="' + (gc ? "false" : "true") + '" aria-setsize="' + total +
            '" aria-posinset="' + (k + 1) + '" style="top:' + (k * h) + "px;height:" + h + 'px">' + groupHtml(this.tab, it, gc) + "</div>");
          continue;
        }
        var open = this.keyOf(it) === this.openKey;
        out.push('<div class="ve-row' + (open ? " is-open" : "") + '" role="option" id="ve-opt-' + this.tab + "-" + k +
          '" data-k="' + k + '" aria-selected="' + (open ? "true" : "false") + '" aria-setsize="' + total + '" aria-posinset="' + (k + 1) +
          '" style="top:' + (k * h) + "px;height:" + h + "px" + (this.depth ? ";padding-inline-start:" + (0.75 + this.depth * 0.9) + "rem" : "") +
          '">' + rowHtml(this.tab, it) + "</div>");
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

  // ------------------------------------------------------------------ Gruppen in der Liste
  var TR = { t: t, kind: function (k) { return kindLabel(k); }, plat: function (p) { return platLabel(p); },
             sub: function (x) { return subjectLabel(x); } };
  function groupOf(tab, entry) {
    var o = ui[tab].ordered;
    return o ? o.groups[-entry - 1] : null;
  }
  function groupCollapsed(tab, entry) {
    var g = groupOf(tab, entry);
    return !!(g && ui[tab].collapsed[g.path]);
  }
  function groupLabel(tab, g) {
    if (g.key === -1) return t("grp_none");
    var fd = C.orderField(tab, g.f), v = fd && fd.label ? fd.label(view(tab), g.key, TR) : String(g.key);
    return v == null || v === "" ? t("grp_none") : v;
  }
  function groupHtml(tab, entry, collapsed) {
    var g = groupOf(tab, entry);
    if (!g) return "";
    var label = groupLabel(tab, g);
    return '<div class="ve-ghead" style="padding-inline-start:' + (g.level * 0.9) + 'rem" title="' + esc(t("grp_toggle")) + '">' +
      '<span class="ve-gcaret" aria-hidden="true">' + (collapsed ? "▸" : "▾") + "</span>" +
      '<span class="ve-gfield">' + esc(t("of_" + g.f)) + ":</span> " +
      '<span class="ve-glabel">' + esc(label) + "</span>" +
      '<span class="ve-gcount">' + num(g.end - g.start) + "</span></div>";
  }
  // Nächster Kopf oberhalb von k mit kleinerer Ebene (bei einer Zeile: ihre innerste Gruppe)
  function parentHeader(tab, k) {
    var items = ui[tab].vlist.items, cur = items[k];
    var lvl = cur < 0 ? groupOf(tab, cur).level : Infinity;
    for (var j = k - 1; j >= 0; j--) {
      if (items[j] < 0 && groupOf(tab, items[j]).level < lvl) return j;
    }
    return -1;
  }
  function toggleGroup(tab, k) {
    var r = ui[tab], g = groupOf(tab, r.vlist.items[k]);
    if (!g) return;
    if (r.collapsed[g.path]) delete r.collapsed[g.path]; else r.collapsed[g.path] = 1;
    relist(tab);
    r.vlist.setActive(k, true);
  }
  function setAllGroups(tab, collapse) {
    var r = ui[tab];
    r.collapsed = {};
    if (collapse && r.ordered) r.ordered.groups.forEach(function (g) { r.collapsed[g.path] = 1; });
    relist(tab);
  }
  // Sichtbare Einträge neu aus der sortierten Ordnung (Ein-/Ausklappen ohne neues Filtern oder Sortieren)
  function relist(tab) {
    var r = ui[tab], D = view(tab);
    if (!r.ordered) return;
    r.vlist.depth = r.ordered.groups.length ? (state[tab].g || []).length : 0;
    r.vlist.setItems(C.flattenOrder(r.ordered, r.collapsed), entryKey(D, r));
  }
  function entryKey(D, r) {
    return function (e) { return e >= 0 ? D.ids[e] : "\u0001" + (r.ordered && r.ordered.groups[-e - 1] ? r.ordered.groups[-e - 1].path : e); };
  }

  // ------------------------------------------------------------------ Gruppieren & Sortieren: Bedienung, Speicher
  var ORDER_STORE = "autodocs-ve-order";
  function loadStoredOrder() {
    try { return JSON.parse(window.localStorage.getItem(ORDER_STORE) || "{}") || {}; } catch (e) { return {}; }
  }
  function saveOrder(tab) {
    try {
      var all = loadStoredOrder();
      var g = C.orderListText(state[tab].g), so = C.orderListText(state[tab].s);
      if (g || so) all[tab] = { g: g, s: so }; else delete all[tab];
      window.localStorage.setItem(ORDER_STORE, JSON.stringify(all));
    } catch (e) { /* privater Modus u. ä.: nur die URL */ }
  }
  // Ohne Angabe in der URL gilt die gespeicherte Wahl dieses Browsers
  function restoreOrder() {
    var u = new URLSearchParams(window.location.search), stored = loadStoredOrder(), changed = false;
    TABS.forEach(function (tab) {
      var P = C.ORDER_PARAMS[tab], st = stored[tab];
      if (u.has(P[0]) || u.has(P[1]) || !st) return;
      state[tab].g = C.parseOrderList(tab, st.g, "g");
      state[tab].s = C.parseOrderList(tab, st.s, "s");
      changed = changed || C.orderActive(state, tab);
    });
    return changed;
  }
  function orderOptions(tab, kind, cur, used, empty) {
    // Leere Wahl nennt die Aufgabe (im kompakten Modus ohne Beschriftung über dem Feld)
    var html = '<option value="">' + esc(empty ? empty + " " + t("order_none") : t("order_none")) + "</option>";
    C.ORDER_FIELDS[tab].forEach(function (fd) {
      if (!fd[kind] || (used[fd.f] && fd.f !== cur)) return;
      html += '<option value="' + fd.f + '"' + (fd.f === cur ? " selected" : "") + ">" + esc(t("of_" + fd.f)) + "</option>";
    });
    return html;
  }
  function dirButton(kind, k, o) {
    var d = o ? o.d : 1, lbl = t(d < 0 ? "order_desc" : "order_asc");
    return '<button type="button" class="ve-btn ve-odir" data-odir="' + kind + '" data-k="' + k + '"' + (o ? "" : " disabled") +
      ' aria-label="' + esc(lbl) + '" title="' + esc(lbl) + '">' + (d < 0 ? "↓" : "↑") + "</button>";
  }
  // Karte „Gruppieren & Sortieren“ in der Filterleiste: drei Ebenen nebeneinander, je Ebene Gruppieren über
  // Sortieren; zwischen den Spalten „alle einklappen“ (nach Ebene 1) und „alle ausklappen“ (nach Ebene 2),
  // ganz rechts „zurücksetzen“. Zu schmal für drei Spalten: je Ebene eine Zeile mit ihrem Knopf daneben
  // (Containerabfrage im Stil, Spalten bleiben ausgerichtet).
  function iconButton(act, label, glyph, enabled) {
    return '<button type="button" class="ve-btn ve-oicon" data-oact="' + act + '"' + (enabled ? "" : " disabled") + ' aria-label="' +
      esc(label) + '" title="' + esc(label) + '"><span aria-hidden="true">' + glyph + "</span></button>";
  }
  function renderOrderPanel(tab) {
    var r = ui[tab], sel = state[tab], G = sel.g || [], S = sel.s || [];
    var usedG = {}, usedS = {};
    G.forEach(function (o) { usedG[o.f] = 1; });
    S.forEach(function (o) { usedS[o.f] = 1; });
    var grouped = G.length > 0;
    var gaps = [iconButton("collapse", t("order_collapse_all"), "⊟", grouped), iconButton("expand", t("order_expand_all"), "⊞", grouped),
                iconButton("reset", t("order_reset"), "↺", grouped || S.length > 0)];
    var html = '<p class="ve-ohint">' + esc(t("order_hint")) + '</p><div class="ve-ogrid">';
    for (var k = 0; k < C.ORDER_MAX; k++) {
      var g = G[k], so = S[k], lvl = t("order_level", { n: k + 1 });
      html += '<div class="ve-ocol" data-level="' + k + '"><div class="ve-olvl">' + esc(lvl) + "</div>" +
        '<div class="ve-osel"><span class="ve-ocap">' + esc(t("order_group")) + '</span><span class="ve-oline"><select data-ogroup="' + k +
        '" aria-label="' + esc(lvl + " · " + t("order_group")) + '">' + orderOptions(tab, "g", g && g.f, usedG, t("order_group")) +
        "</select>" + dirButton("g", k, g) + "</span></div>" +
        '<div class="ve-osel"><span class="ve-ocap">' + esc(t("order_sort")) + '</span><span class="ve-oline"><select data-osort="' + k +
        '" aria-label="' + esc(lvl + " · " + t("order_sort")) + '">' + orderOptions(tab, "s", so && so.f, usedS, t("order_sort")) +
        "</select>" + dirButton("s", k, so) + "</span></div></div>" +
        '<div class="ve-ogap" data-gap="' + k + '">' + gaps[k] + "</div>";
    }
    html += "</div>";
    r.opanel.innerHTML = html;
    var n = G.length + S.length;
    r.obadge.textContent = n ? String(n) : "";
  }
  function setOrderOpen(tab, open) {
    var r = ui[tab];
    r.opanel.hidden = !open;
    r.otoggle.setAttribute("aria-expanded", open ? "true" : "false");
    r.ocard.classList.toggle("is-open", open);
    if (open) renderOrderPanel(tab);
    layout();
  }
  // Auswahl im Panel -> Zustand (leere Ebenen rücken auf), Liste, URL und Speicher
  function readOrderPanel(tab) {
    var r = ui[tab], G = [], S = [], old = state[tab];
    function dirOf(list, f) { for (var k = 0; k < list.length; k++) if (list[k].f === f) return list[k].d; return 1; }
    r.opanel.querySelectorAll("select[data-ogroup]").forEach(function (sl) { if (sl.value) G.push({ f: sl.value, d: dirOf(old.g, sl.value) }); });
    r.opanel.querySelectorAll("select[data-osort]").forEach(function (sl) { if (sl.value) S.push({ f: sl.value, d: dirOf(old.s, sl.value) }); });
    return { g: G, s: S };
  }
  function applyOrder(tab, spec, focusSel) {
    var r = ui[tab];
    state[tab].g = C.parseOrderList(tab, C.orderListText(spec.g), "g");
    state[tab].s = C.parseOrderList(tab, C.orderListText(spec.s), "s");
    r.collapsed = {};
    saveOrder(tab);
    refresh(tab);
    commit(true);
    if (!r.opanel.hidden) {
      renderOrderPanel(tab);
      var f = focusSel ? r.opanel.querySelector(focusSel) : null;
      if (f) f.focus();
    } else renderOrderPanel(tab);
  }
  function wireOrder(tab, r) {
    r.collapsed = {};
    r.otoggle.addEventListener("click", function () { setOrderOpen(tab, r.opanel.hidden); });
    r.opanel.addEventListener("change", function (e) {
      var sl = e.target.closest("select[data-ogroup],select[data-osort]");
      if (!sl) return;
      var which = sl.hasAttribute("data-ogroup") ? "data-ogroup" : "data-osort";
      applyOrder(tab, readOrderPanel(tab), "select[" + which + '="' + sl.getAttribute(which) + '"]');
    });
    r.opanel.addEventListener("click", function (e) {
      var b = e.target.closest("[data-odir],[data-oact]");
      if (!b || b.disabled) return;
      var act = b.getAttribute("data-oact");
      if (act === "collapse" || act === "expand") { setAllGroups(tab, act === "collapse"); return; }
      if (act === "reset") { applyOrder(tab, { g: [], s: [] }, "select[data-ogroup]"); return; }
      var kind = b.getAttribute("data-odir"), k = +b.getAttribute("data-k");
      var spec = { g: state[tab].g.slice(), s: state[tab].s.slice() };
      var list = spec[kind];
      if (list[k]) list[k] = { f: list[k].f, d: -list[k].d };
      applyOrder(tab, spec, '[data-odir="' + kind + '"][data-k="' + k + '"]');
    });
  }

  function rowHtml(tab, i) {
    if (tab === "el") {
      var E = view("el");
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
    var D = view(tab);
    if (tab === "q") return questionRowHtml(D, i);
    var title = D.title[i] || D.ids[i];
    var sub = [esc(D.docOf(i)), D.page[i] ? esc(t("page_n", { p: D.page[i] })) : "",
               esc(t("n_elements", { n: D.nt[i] }))];
    if (tab === "fig" && D.nser[i] > 1) sub.push(esc(t("series_n", { n: D.nser[i] })));
    return '<div class="ve-row-top"><span class="ve-row-title">' + esc(title) + '</span></div>' +
      '<div class="ve-row-meta">' + sub.filter(Boolean).join('<span aria-hidden="true">·</span>') + "</div>";
  }

  function questionRowHtml(D, i) {
    var st = D.dict.st[D.st[i]] || "", kind = D.dict.kind[D.kind[i]] || "";
    var subs = (D.sub[i] || []).map(function (c) { return D.dict.sub[c]; });
    var meta = [];
    if (subs.length) meta.push('<span class="ve-row-name">' + esc(subjectLabel(subs[0])) + "</span>" +
      (subs.length > 1 ? " " + esc(t("q_more_n", { n: subs.length - 1 })) : ""));
    var mods = (D.modBits[i] || []).map(function (c) { return D.dict.mod[c]; });
    if (mods.length) meta.push(esc(mods.join(", ")));
    if (D.oc[i] >= 0) meta.push(esc(t("qo_" + D.dict.oc[D.oc[i]])));
    if (D.ne[i]) meta.push('<span title="' + esc(t("q_events")) + '">💬 ' + num(D.ne[i]) + "</span>");
    if (D.at[i]) meta.push(esc(D.at[i]));
    return '<div class="ve-row-top"><span class="ve-row-title">' + esc(D.title[i] || D.ids[i]) + '</span><span class="ve-row-badges">' +
      '<span class="ve-mini ve-qk ve-qk-' + esc(kind) + '">' + esc(t("qk_" + kind)) + "</span>" +
      '<span class="ve-mini ve-qst ve-qst-' + esc(st) + '">' + esc(t("qs_" + st)) + "</span></span></div>" +
      '<div class="ve-row-meta">' + meta.join('<span aria-hidden="true">·</span>') + "</div>";
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
        var first = -1;
        for (var k = 0; k < r.vlist.items.length && first < 0; k++) if (r.vlist.items[k] >= 0) first = k;
        if (first >= 0) { r.vlist.setActive(first, true); openFromList(tab, first, true); }
      }
    });
    r.ftoggle.addEventListener("click", function () { setFacetsOpen(tab, !r.panel.classList.contains("facets-open")); });
    r.fclose.addEventListener("click", function () { setFacetsOpen(tab, false); r.ftoggle.focus(); });
    r.reset.addEventListener("click", function () {
      var keep = tab === "el" ? null : state[tab].id;
      var fresh = C.emptyState()[tab];
      if (keep) fresh.id = keep;
      fresh.g = state[tab].g; fresh.s = state[tab].s;   // Gruppierung/Sortierung ist kein Filter
      state[tab] = fresh;
      r.q.value = "";
      refresh(tab);
      commit(true);
    });
    r.back.addEventListener("click", function () { closeDetail(tab); });
    wireOrder(tab, r);
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
      var first = r.facets.querySelector("input[data-role=q]") || r.fbody.querySelector("button, input, select");
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
    TABS.forEach(function (tab) {
      if (ui[tab].q.value !== state[tab].q) ui[tab].q.value = state[tab].q || "";
      renderOrderPanel(tab);
    });
    switchTab(state.tab, false);
    TABS.forEach(function (tab) { if (data[tab]) refresh(tab); });
    syncViewer(state.tab);
  }

  function selectedKey(tab) { return tab === "el" ? state.id : state[tab].id; }

  function switchTab(tab, push) {
    if (TABS.indexOf(tab) < 0) tab = "el";
    var changed = state.tab !== tab;
    state.tab = tab;
    app.querySelectorAll(".ve-tab").forEach(function (b) {
      var on = b.getAttribute("data-tab") === tab;
      b.setAttribute("aria-selected", on ? "true" : "false");
      b.tabIndex = on ? 0 : -1;
      b.classList.toggle("is-active", on);
    });
    TABS.forEach(function (x) { ui[x].panel.hidden = x !== tab; });
    if (push && changed) commit(true);
    return ensureLoaded(tab).then(function () {
      refresh(tab);
      syncViewer(tab);
      layout();
    });
  }

  // Nach dem ersten Zeichnen: Facetten im nächsten Task (die ersten Zeilen erscheinen vorher), Nebenarbeit
  // (übrige Indizes) erst im Leerlauf
  function afterPaint(fn) {
    var done = false;
    function run() { if (!done) { done = true; fn(); } }
    if (typeof requestAnimationFrame === "function") requestAnimationFrame(function () { setTimeout(run, 0); });
    setTimeout(run, 100);   // verborgener Tab: kein requestAnimationFrame
  }
  function whenIdle(fn) {
    if (typeof window.requestIdleCallback === "function") window.requestIdleCallback(function () { fn(); }, { timeout: 2000 });
    else setTimeout(fn, 200);
  }

  // ------------------------------------------------------------------ Laden
  var loading = {};
  // Abweichende Dateistämme aus dem geladenen Index (rec: versions/data, item: items/ und Belegseiten)
  function stems(kind) {
    var E = view("el");
    if (E && E.stems && E.stems[kind] && (data.el || kind !== "item")) return E.stems[kind];
    if (kind !== "item") return null;
    var m = {};
    ["fig", "snip"].forEach(function (x) { var D = view(x); if (D && D.names) Object.assign(m, D.names); });
    if (E && E.stems && E.stems.item) Object.assign(m, E.stems.item);
    return m;
  }
  // Abbruchsicher: überholte Ladevorgänge enden als AbortError (kein Fehlerhinweis), ein Netzfehler wird
  // einmal wiederholt (C.loadJson). Je Bereich gibt es höchstens einen laufenden Detail-Ladevorgang.
  function fetchJson(url, signal) {
    return C.loadJson(function (u, o) { return fetch(u, o); }, url, { signal: signal });
  }
  var ctrl = { el: null, fig: null, snip: null, q: null };
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
    // Index beim Verlassen abgebrochen (Liste leer, Zähler ohne Fehler): Bereich neu laden
    if (!data[state.tab] || (state.tab !== "el" && state.tab !== "q" && !data.el)) { switchTab(state.tab, false); return; }
    TABS.forEach(function (tab) {
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

  // Startabruf: Das Inline-Skript der Seite (versions.json, vor allen übrigen Skripten) holt den Index des
  // aktiven Reiters schon, während die Skripte laden (window.__veBoot = { url, p: Promise<Text> }). Er wird
  // genau einmal übernommen; scheitert er, lädt der Explorer selbst (mit Wiederholung und Rückfall).
  function takeBoot(url) {
    var boot = window.__veBoot || {}, abs;
    try { abs = new URL(url, window.location.href).href; } catch (e) { return null; }
    var hit = null;
    ["head", "full"].forEach(function (k) {
      var b = boot[k];
      if (b && !b.used && b.p && b.url === abs) { b.used = true; hit = b.p; }
    });
    return hit;
  }
  function mark(name) { try { performance.mark(name); } catch (e) { /* ignore */ } }
  function measure(name, from) { try { performance.measure(name, from); } catch (e) { /* ignore */ } }
  // Index laden und parsen; Zeiten als performance.measure("ve:…") (Messung: docs/design/versions-explorer-load.md)
  function loadIndex(tab, url) {
    var t0 = "ve:" + tab + ":start";
    mark(t0);
    var boot = takeBoot(url);
    var text = boot ? boot.catch(function () { return null; }) : Promise.resolve(null);
    return text.then(function (body) {
      if (body == null) {
        return C.loadJson(function (u, o) {
          return fetch(u, o).then(function (r) {
            // gleiche Fehlersemantik wie fetchJson, Parsen aber getrennt messbar (Text, wo es ihn gibt)
            return { ok: r.ok, status: r.status, json: function () { return bodyOf(r); } };
          });
        }, url, {});
      }
      return body;
    }).then(function (body) {
      measure("ve:" + tab + ":fetch", t0);
      return parseTimed(tab, body);
    });
  }
  function bodyOf(r) { return typeof r.text === "function" ? r.text() : r.json(); }
  function parseTimed(tab, body) {
    if (typeof body !== "string") return body;
    var p0 = "ve:" + tab + ":parse0";
    mark(p0);
    var raw = JSON.parse(body);
    measure("ve:" + tab + ":parse", p0);
    return raw;
  }
  function decodeTimed(tab, fn) {
    var d0 = "ve:" + tab + ":decode0";
    mark(d0);
    var out = fn();
    measure("ve:" + tab + ":decode", d0);
    return out;
  }

  // Kopf nur, wenn die Liste ohne Auswahl startet: dann sind seine Zeilen die ersten der Liste und seine
  // Zähler die der Facetten
  function headUsable(tab) {
    return !C.activeCount(state, tab) && !String(state[tab].q || "").trim() && !C.orderActive(state, tab);
  }
  var headLoading = {};
  function loadHead(tab) {
    if (headLoading[tab] || heads[tab] || data[tab] || !headUsable(tab)) return;
    var name = { el: "elements", fig: "figures", snip: "snippets", q: "questions" }[tab];
    var url = ROOT + "versions/explorer/" + name + ".head.json";
    var boot = takeBoot(url);
    headLoading[tab] = (boot || fetch(url).then(function (r) {
      if (!r.ok) throw new Error(r.status + " " + url);
      return bodyOf(r);
    })).then(function (body) {
      if (data[tab] || !headUsable(tab)) return;
      var raw = typeof body === "string" ? JSON.parse(body) : body;
      if (!raw || !raw.head || !raw.cols) return;
      var D = tab === "el" ? C.decodeElements(raw) : tab === "q" ? C.decodeQuestions(raw) : C.decodeItems(raw, null);
      D.head = raw.head;
      heads[tab] = D;
      updateTabCounts();
      if (tab === state.tab) showHead(tab);
    }).catch(function () { /* ohne Kopf: wie bisher auf den vollen Index warten */ });
  }
  function showHead(tab) {
    var D = heads[tab], r = ui[tab];
    if (!D || data[tab] || !headUsable(tab)) return;
    var list = [];
    for (var i = 0; i < D.n; i++) list.push(i);
    data.res[tab] = { matches: list, counts: D.head.facets, head: true };
    r.ordered = null;
    r.vlist.depth = 0;
    r.vlist.openKey = selectedKey(tab) || null;
    r.vlist.setItems(list, function (k) { return D.ids[k]; }, D.head.n);
    r.count.textContent = t("results", { n: num(D.head.n), total: num(D.head.n) });
    refreshFacets(tab);
    refreshChips(tab);
    layout();
    measure("ve:" + tab + ":head", "ve:" + tab + ":start");
  }

  function ensureLoaded(tab) {
    if (data[tab]) return Promise.resolve();
    if (loading[tab]) return loading[tab];
    if (tab === state.tab) loadHead(tab);
    if (tab === "el") {
      loading.el = loadIndex("el", ROOT + "versions/explorer/elements.json")
        .then(function (raw) { data.el = decodeTimed("el", function () { return C.decodeElements(raw); }); heads.el = null; })
        .catch(function () {
          return fetchJson(ROOT + "versions/catalog.json")
            .catch(function (err) {
              if (!API) throw err;
              return fetchJson("/api/versions?limit=50000");
            })
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
    if (tab === "q") {
      // Fragen & Diskussionen: eigener Index, unabhängig von elements.json
      loading.q = loadIndex("q", ROOT + "versions/explorer/questions.json")
        .then(function (raw) {
          data.q = decodeTimed("q", function () { return C.decodeQuestions(raw); });
          heads.q = null;
          updateTabCounts();
        }).catch(function () {
          data.q = null;
          ui.q.count.textContent = t("q_missing");
          showNotice("q", t("q_missing"));
          loading.q = null;
        });
      return loading.q;
    }
    // Eigener Index zuerst, nie hinter elements.json; nur ein v1-Index wartet danach auf den Elementindex
    loading[tab] = loadIndex(tab, ROOT + "versions/explorer/" + (tab === "fig" ? "figures" : "snippets") + ".json")
      .then(function (raw) {
        var ready = C.itemsNeedElements(raw) ? ensureLoaded("el") : Promise.resolve();
        return ready.then(function () {
          data[tab] = decodeTimed(tab, function () { return C.decodeItems(raw, data.el); });
          heads[tab] = null;
          updateTabCounts();
        });
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
    // Zähler aus dem ersten geladenen Index (alle drei tragen "counts"), sonst je Reiter sein eigener Umfang
    var c = {};
    ["el", "snip", "fig", "q"].forEach(function (x) {
      var D = view(x);
      if (D && D.counts) Object.keys(D.counts).forEach(function (k) { if (c[k] == null) c[k] = D.counts[k]; });
    });
    function size(x, fallback) { return data[x] ? data[x].n : (heads[x] ? heads[x].head.n : fallback); }
    var vals = { el: size("el", c.elements), fig: size("fig", c.figures), snip: size("snip", c.snippets),
                 q: size("q", c.questions) };
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
    if (!D) {
      // Kopf sichtbar, voller Index lädt noch: Auswahl/Suche greifen, sobald er da ist (switchTab)
      if (heads[tab]) {
        if (headUsable(tab)) showHead(tab);
        else {
          data.res[tab] = null;
          r.vlist.setItems([], function () { return ""; });
          r.space.innerHTML = '<div class="ve-empty">' + esc(t("loading")) + "</div>";
          r.count.textContent = t("loading");
          refreshChips(tab);
        }
      }
      return;
    }
    var first = !r.listShown;
    r.listShown = true;
    mark("ve:" + tab + ":list0");
    var sel = state[tab];
    var res = tab === "el" ? C.filterElements(D, sel) : tab === "q" ? C.filterQuestions(D, sel) : C.filterItems(D, tab, sel);
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
    if (C.orderActive(state, tab)) {
      mark("ve:" + tab + ":order0");
      r.ordered = C.orderRows(D, tab, list, { g: sel.g, s: sel.s });
      r.vlist.depth = r.ordered.groups.length ? sel.g.length : 0;
      r.vlist.setItems(C.flattenOrder(r.ordered, r.collapsed), entryKey(D, r));
      measure("ve:" + tab + ":order", "ve:" + tab + ":order0");
    } else {
      r.ordered = null;
      r.vlist.depth = 0;
      r.vlist.setItems(list, function (i) { return D.ids[i]; });
    }
    if (targetId && openChanged && !mismatch && r.vlist.active >= 0) r.vlist.ensureVisible(r.vlist.active);
    var total = D.n;
    r.count.textContent = t("results", { n: num(res.matches.length), total: num(total) });
    var ac = C.activeCount(state, tab);
    r.fbadge.textContent = ac ? String(ac) : "";
    r.reset.disabled = !ac && !sel.q;
    if (!list.length) {
      r.space.innerHTML = '<div class="ve-empty">' + esc(t("no_results")) + "</div>";
    }
    measure("ve:" + tab + ":list", "ve:" + tab + ":list0");
    if (tab === state.tab) layout();
    if (first) {
      // Erstes Zeichnen: Zeilen zuerst; Facetten und Chips im nächsten Task, damit die Liste sofort erscheint
      afterPaint(function () {
        if (data.res[tab] !== res) return;   // inzwischen neu gefiltert (dann schon vollständig gezeichnet)
        mark("ve:" + tab + ":facets0");
        refreshFacets(tab, keepFacetFocus);
        refreshChips(tab);
        measure("ve:" + tab + ":facets", "ve:" + tab + ":facets0");
      });
      return;
    }
    refreshFacets(tab, keepFacetFocus);
    refreshChips(tab);
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
    var D = view("el");
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
    var D = view(tab);
    var uni = (D && D.dict.modUni && D.dict.modUni.length ? D.dict.modUni : (data.el && data.el.dict.modUni)) || [];
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
    var D = view(tab), res = data.res[tab], r = ui[tab];
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
    } else if (tab === "q") {
      html += group(t("f_qstatus"), facetChips(tab, "st", D.dict.st, c.st, { hideEmpty: true }));
      html += group(t("f_qkind"), facetChips(tab, "kind", D.dict.kind, c.kind, { hideEmpty: true }));
      html += group(t("f_plat"), facetChips(tab, "plat", D.dict.plat, c.plat, { hideEmpty: true }));
      // Gegenstand (qsub): nur gewählte, z. B. aus dem Link „Offene Fragen (n)“ einer Element- oder Modulseite
      var subSel = state.q.sub || [];
      if (subSel.length) {
        html += group(t("f_qsub"), subSel.map(function (v) {
          var k = D.dict.sub.indexOf(v);
          return chipButton("sub", v, subjectLabel(v), k >= 0 ? (c.sub || {})[k] || 0 : 0, true);
        }).join(""));
      }
      if (D.dict.mod.length) html += modGroup(tab, D.dict.mod, c.mod);
    } else {
      html += group(t("f_plat"), facetChips(tab, "plat", D.dict.plat, c.plat, { hideEmpty: true }));
      html += group(t("f_role"), facetChips(tab, "role", D.dict.role, c.role));
      if (tab === "fig") html += group(t("f_series"), facetChips(tab, "multi", ["1"], c.multi));
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
          esc(t("remove_filter")) + '"><span class="ve-chip-k">' + esc(facetTitle(key, tab)) + ":</span> " +
          esc(valueLabel(tab, key, val)) + ' <span aria-hidden="true">✕</span></button>';
      });
    });
    if (html) html += '<button type="button" class="ve-chip-clear" data-chip="*">' + esc(t("reset")) + "</button>";
    r.chips.innerHTML = html;
    r.chips.hidden = !html;
  }

  // ------------------------------------------------------------------ Öffnen / Detail
  function openFromList(tab, k, push) {
    var D = view(tab);
    var r = ui[tab];
    var i = r.vlist.items[k];
    if (i == null) return;
    if (i < 0) { toggleGroup(tab, k); return; }
    openItem(tab, D.ids[i], push, { fromList: true });
  }

  function openItem(tab, id, push, opts) {
    if (tab === "el") {
      if (state.id !== id) { state.from = ""; state.to = ""; }
      state.id = id;
      if (opts && opts.view) state.view = opts.view;
    } else {
      if (state[tab].id !== id) resetCompare(tab);
      state[tab].id = id;
    }
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

  var listScroll = { el: 0, fig: 0, snip: 0, q: 0 };
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

  var shown = { el: null, fig: null, snip: null, q: null };
  var token = { el: 0, fig: 0, snip: 0, q: 0 };

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
    if (!view(tab) && tab !== "el") return;
    if (tab === "el") loadElement(key, userAction);
    else if (tab === "q") loadQuestion(key, userAction);
    else loadItem(tab, key, userAction);
    if (userAction && narrowMQ.matches) {
      r.back.focus({ preventScroll: true });
    }
  }

  // ------------------------------------------------------------------ Element-Viewer
  var EL = { rec: null, from: null, to: null, rev: null, figShown: PAGE.fig, snipShown: PAGE.snip };
  // Darstellungsart des Vergleichs (Nebeneinander, Unified, Volltext): eine Einstellung für alle drei Bereiche
  var cmpMode = "side";

  function loadElement(id, userAction) {
    var r = ui.el;
    var my = ++token.el;
    var signal = newSignal("el");
    shown.el = null;   // bis zum Erfolg zeigt der Viewer nicht mehr das vorige Element
    if (!EL.rec || EL.rec.id !== id) {
      r.vbody.innerHTML = '<div class="ve-placeholder">' + esc(t("loading_detail", { id: id })) + "</div>";
    }
    var D = view("el"), di = D ? (D.byId.get(id) != null ? D.byId.get(id) : resolveId(D, id)) : -1;
    var isRef = !!(D && di >= 0 && D.ref && D.ref[di] === 1);
    function loadFromFile() {
      return fetchJson(ROOT + "versions/data/" + encodeURIComponent(C.recordFile(id, stems("rec"))), signal)
        .catch(function (err) {
          // Rückfall auf die lokale API nur, wenn die Datei fehlt – nicht bei Abbruch oder Netzfehler
          if (C.isAbortError(err) || C.isNetworkError(err) || my !== token.el || !API) throw err;
          return fetchJson("/api/versions?id=" + encodeURIComponent(id), signal);
        });
    }
    var p;
    if (EL.rec && EL.rec.id === id) {
      p = Promise.resolve(EL.rec);
    } else if (isRef) {
      // nur zitierte Kennung: kein Versions-Record, Belege aus versions/explorer/refs/
      p = fetchJson(ROOT + "versions/explorer/refs/" + encodeURIComponent(C.recordFile(id, stems("ref"))), signal);
    } else if (typeof FrozenPack !== "undefined") {
      p = FrozenPack.record(ROOT, id, signal).then(function (rec) {
        if (!rec || !rec.versions) return loadFromFile();
        if (!rec.evidence) {
          return loadFromFile().then(function (full) {
            return (full && full.evidence) ? full : rec;
          }).catch(function () { return rec; });
        }
        return rec;
      }).catch(function (err) {
        if (C.isAbortError(err)) throw err;
        return loadFromFile();
      });
    } else {
      p = loadFromFile();
    }
    p.then(function (rec) {
      if (my !== token.el) return;
      if (!rec || (!rec.ok && !rec.versions)) throw new Error(t("not_found", { id: id }));
      rec.id = id;
      if (EL.rec !== rec) {
        // Präsenz-Einträge (im PDF vorhanden, Wortlaut nicht erfasst) gehören in die Zeitachse,
        // aber nicht in den Vergleich: rec.versions enthält nur erfassten Wortlaut.
        if (rec.citation_only && state.view === "ver") state.view = "cit";
        K.prepareRecord(rec);
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
    K.prepareRecord(rec);
    var pair = K.initialPair(rec, state.from, state.to);
    EL.from = pair[0]; EL.to = pair[1];
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
      '<div class="ve-links">' + links + "</div></div>" + reqTextHtml(rec) + subHtml +
      '<div class="ve-subpanel" data-role="subpanel"></div>';
    renderSubpanel();
  }

  // Wortlaut des aktuellen Releases (neueste erfasste Fassung, bereinigt laut export_versions) über den
  // Unterreitern: sichtbar, gleich welcher Reiter aktiv ist; lange Texte eingeklappt.
  function reqTextHtml(rec) {
    if (rec.citation_only) return "";
    var vs = rec.versions || [], v = vs[vs.length - 1], lc = rec.lifecycle || {};
    if (!v) return '<section class="ve-req ve-req-none"><p class="ve-muted">' + esc(t("req_none")) + "</p></section>";
    var lines = formatReqLines(C.decodeFully(C.shownContent(v))).map(function (l) { return l.replace(/[ \t\u00a0]{2,}/g, " "); });
    var text = lines.join("\n");
    var long = text.length > 700 || lines.length > 9;
    var removed = (v.cleaning || {}).removed || [];
    var head = lc.is_dropped ? t("req_head_last", { rel: v.release }) : t("req_head", { rel: v.release });
    return '<section class="ve-req" aria-labelledby="ve-req-h"><h3 id="ve-req-h"><span>' + esc(head) + "</span>" +
      (removed.length ? '<span class="ve-req-clean" title="' + esc(t("ep_cleaned_title", { list: removed.join(" · ") })) + '">' +
        esc(t("req_cleaned")) + "</span>" : "") + "</h3>" +
      '<div class="ve-req-body' + (long ? "" : " is-open") + '" id="ve-req-b">' + linkIds(esc(text), rec.id) + "</div>" +
      (long ? '<button type="button" class="ve-btn ve-req-toggle" data-act="req-toggle" aria-expanded="false" aria-controls="ve-req-b">' +
        esc(t("req_more")) + "</button>" : "") + "</section>";
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
    else mountElementRevisions(box);
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
    var b = e.target.closest("[data-view],[data-goto],[data-goto-tab],[data-open-el],[data-showmore],[data-act],.ve-shot-badge");
    if (!b) return;
    if (b.classList.contains("ve-shot-badge")) {
      var sHash = b.getAttribute("data-snip-hash");
      var sPage = parseInt(b.getAttribute("data-snip-page") || "0", 10);
      var F = window.FigureImages;
      if (sHash && sPage && F && typeof F.getSnippet === "function") {
        e.preventDefault();
        F.getSnippet(sHash, sPage).then(function (r) {
          if (r.url) {
            window.open(r.url, "_blank", "noopener,noreferrer");
          } else if (r.kind === "signin" || r.kind === "forbidden") {
            var A = window.AiAccess;
            if (A && typeof A.open === "function") A.open(r.kind === "forbidden" ? "request" : "signin");
          }
        });
        return;
      }
    }
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
      if (state[target].id !== b.getAttribute("data-id")) resetCompare(target);
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
    if (b.getAttribute("data-act") === "req-toggle") {
      var rb = ui[tab].vbody.querySelector(".ve-req-body");
      if (!rb) return;
      var ropen = rb.classList.toggle("is-open");
      b.setAttribute("aria-expanded", ropen ? "true" : "false");
      b.textContent = t(ropen ? "req_less" : "req_more");
      if (!ropen) revealTop(rb.closest(".ve-req"));
      return;
    }
    if (b.getAttribute("data-act") === "snip-zoom") {
      var wrap = ui[tab] && ui[tab].vbody ? ui[tab].vbody.querySelector(".ve-snipbig") : null;
      if (!wrap) wrap = b.closest(".ve-snipbig");
      if (wrap) {
        var exp = wrap.classList.toggle("is-expanded");
        b.setAttribute("aria-expanded", exp ? "true" : "false");
      }
      return;
    }
    if (b.getAttribute("data-act") === "copy") {
      var url = window.location.href;
      var done = function () { b.textContent = t("copied"); setTimeout(function () { b.textContent = t("copy_link"); }, 1500); };
      if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, done); else done();
      return;
    }
  }

  // ------------------------------------------------------------------ Versionen & Diff
  // Zeitachse und Vergleich aus static/text-diff.js (TD.revisions): dieselbe Bedienung für Elemente,
  // Fassungen einer Bildreihe und Snippets.
  function mountElementRevisions(box) {
    var rec = EL.rec;
    box.innerHTML = '<div data-role="rev"></div><div class="ve-audit-box"><h3 class="ve-audit-title">' + esc(t("audit_title")) +
      '</h3><div class="ve-audit-grid">' +
      [["a_actor", "ve-audit-actor"], ["a_hash", "ve-audit-hash"], ["a_recorded", "ve-audit-recorded"], ["a_evidence", "ve-audit-evidence"]].map(function (a) {
        return '<div class="ve-audit-card"><span>' + esc(t(a[0])) + '</span><strong id="' + a[1] + '">-</strong></div>';
      }).join("") + "</div></div>";
    EL.rev = K.mountElement(box.querySelector("[data-role=rev]"), rec, {
      from: EL.from, to: EL.to, mode: cmpMode, onMode: function (m) { cmpMode = m; },
      onChange: function (a, b) { EL.from = a; EL.to = b; state.from = a || ""; state.to = b || ""; commit(false); },
      onRender: function (a, b, d) { if (d && d.src) updateAuditBox(d.src); }
    });
  }

  // Zeilen-/Wortvergleich, Zeitachse und Darstellung: gemeinsam mit den Schaubild-Seiten in static/text-diff.js
  var TD = window.TextDiff;

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
    var elReady = ensureLoaded("el");
    fetchJson(ROOT + "versions/explorer/items/" + encodeURIComponent(C.itemFile(id, stems("item"))), signal).then(function (info) {
      return elReady.then(function () { return info; });
    }).then(function (info) {
      if (my !== token[tab]) return;
      var pack = (typeof FrozenPack === "undefined") ? Promise.resolve(null)
        : FrozenPack.record(ROOT, id, signal).catch(function (err) {
            if (C.isAbortError(err)) throw err;
            return null;
          });
      return pack.then(function (rec) {
        // Die Pack-Zeile beschreibt nur dieses eine Schaubild (eine Fassung, keine Übergänge). Gehört es zu einer
        // Reihe mit eigener Reihen-Datei (versions/explorer/series/), gilt diese: Sonst zeigte z. B.
        // FIG-0021fe4e24943bc3 neun Fassungen „ohne KI-Beschreibung“ und kein Delta.
        if (rec && rec.series && !info.seriesPayload && !info.series_file) info.seriesPayload = rec.series;
        if (rec && rec.rv && !info.rv) { info.rv = rec.rv; info.rt = rec.rt; info.rk = rec.rk; }
        return info;
      });
    }).then(function (info) {
      if (my !== token[tab] || !info) return;
      shown[tab] = id;
      r.vbody.innerHTML = itemHtml(tab, info);
      r.vbody.parentNode.scrollTop = 0;
      fillPdfLinks(r.vbody);
      fillCanonLinks(r.vbody);
      figObserve(r.vbody);
      if (tab === "fig") mountFigRevisions(r.vbody, info, my);
      else mountSnipRevisions(r.vbody, info);
      if (userAction && !narrowMQ.matches) r.list.focus({ preventScroll: true });
    }).catch(function (err) {
      // Überholt (neue Auswahl, Zurück im Verlauf) oder Seite verlassen: kein Fehlerhinweis
      if (my !== token[tab] || C.isAbortError(err) || pageHidden) return;
      shown[tab] = null;
      r.vbody.innerHTML = errorHtml(err);
    });
  }

  // Fassungen einer Bildreihe als Revisions-Zeitachse (Vorschaubild je Fassung) mit wortgenauem Vergleich der
  // KI-Beschreibungen (versions/explorer/series/<Reihe>.json, je Reihe bei Bedarf geladen). „Delta laut KI“ steht
  // als Tooltip am Änderungsklassen-Chip und gesammelt in der Ansicht „KI-Deltas“, nicht neben dem Vergleich.
  // Standard: beschriebene Fassung gegen ihre Vorgängerin.
  var FR = { ctl: null }, SR = { ctl: null };
  function resetCompare(tab) {
    if (tab === "fig") { state.ffrom = ""; state.fto = ""; }
    else if (tab === "snip") { state.sfrom = ""; state.sto = ""; }
  }
  function figLabels() {
    var L = revLabels();
    L.identical = t("td_identical"); L.base = t("td_base"); L.new_version = t("td_new"); L.current = t("td_current");
    L.delta = t("td_delta"); L.delta_none = t("td_delta_none"); L.delta_note = t("td_delta_note"); L.nodesc = t("td_nodesc");
    L.nodiff = t("td_nodiff"); L.open_page = t("page_fig"); L.summary = t("ai_short"); L.raw_head = t("td_raw_head");
    L.model = t("td_model"); L.mode_deltas = t("td_mode_deltas"); L.deltas_run = t("td_deltas_run");
    L.deltas_each = t("td_deltas_each"); L.deltas_intro = t("td_deltas_intro"); L.deltas_empty = t("td_deltas_empty");
    L.change = { normativ: t("td_ch_normativ"), redaktionell: t("td_ch_redaktionell"), keine: t("td_ch_keine"), offen: t("td_ch_offen") };
    return L;
  }
  function mountFigRevisions(vbody, info, my) {
    var box = vbody.querySelector("[data-role=figrev]");
    FR.ctl = null;
    if (!box) return;
    function mount(S, pending) {
      var prev = FR.ctl ? FR.ctl.state : null;
      FR.ctl = TD.seriesDiff(box, S, {
        current: info.ai && info.ai.of ? info.ai.of : null, labels: figLabels(), renderMarkdown: C.renderMarkdown,
        members: info.series || [], wrapClass: "ve-series",
        thumbHtml: function (m) { return thumbHtml(m.sha, spanText(m.releases), "tiny"); },
        pageHref: function (id) { return /^FIG-/.test(id) ? C.figureHref(ROOT, id, stems("item")) : null; },
        from: prev ? prev.from : state.ffrom, to: prev ? prev.to : state.fto, mode: cmpMode,
        onMode: function (m) { cmpMode = m; },
        onChange: function (a, b) { state.ffrom = a || ""; state.fto = b || ""; commit(false); },
        pending: pending, missingText: t("td_missing")
      });
      box.querySelectorAll("[data-td-link]").forEach(function (a) {
        a.setAttribute("data-canon", "fig"); a.hidden = true; a.title = a.getAttribute("data-td-link");
      });
      fillCanonLinks(box);
      figObserve(box);
    }
    if (info.seriesPayload) { mount(info.seriesPayload, false); return; }
    mount(null, !!info.series_file);
    if (!info.series_file) return;
    fetchJson(ROOT + "versions/explorer/series/" + encodeURIComponent(info.series_file), ctrl.fig ? ctrl.fig.signal : undefined)
      .then(function (S) { if (my === token.fig && box.isConnected) mount(S, false); })
      .catch(function (err) {
        if (my !== token.fig || C.isAbortError(err) || pageHidden || !box.isConnected) return;
        mount(null, false);
      });
  }

  // Snippet: dieselbe Zeitachse über die Releases (C.snippetTimeline). Der Speicher hält einen Wortlaut je
  // Snippet; Spannen mit anderem Inhalts-Hash (Snippet-Manifest) erscheinen, sind aber nicht vergleichbar.
  function mountSnipRevisions(vbody, info) {
    var box = vbody.querySelector("[data-role=sniprev]");
    SR.ctl = null;
    if (!box) return;
    SR.ctl = K.mountSnippet(box, info, {
      from: state.sfrom, to: state.sto, mode: cmpMode, onMode: function (m) { cmpMode = m; },
      onChange: function (a, b) { state.sfrom = a || ""; state.sto = b || ""; commit(false); }
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

  function figureSha(info) {
    if (info && info.sha && /^[0-9a-f]{64}$/i.test(info.sha)) return info.sha;
    // Ältere Indizes (v1) trugen den Hash auch in figures.json
    if (info && info.id && data.fig && data.fig.sha && data.fig.byId.has(info.id)) {
      var hs = data.fig.sha[data.fig.byId.get(info.id)];
      if (hs) return hs;
    }
    return (info && info.sha) || "";
  }

  function itemHtml(tab, info) {
    var isFig = tab === "fig";
    var platform = info.platform || "";
    var rels = info.releases || [];
    var targets = info.targets || [];
    var h = '<div class="ve-vh"><div class="ve-vh-top"><h2 class="ve-vh-id ve-vh-title">' + esc(info.caption || info.id) + "</h2></div>" +
      '<div class="ve-vh-name"><code>' + esc(info.id) + '</code><span class="ve-kind">' + esc(t(!isFig && info.src === "manifest" ? "src_section" : "src_" + (info.src || "matrix"))) + "</span></div>" +
      '<dl class="ve-meta">' +
      (info.doc ? "<div><dt>" + esc(t("lbl_doc")) + "</dt><dd>" + esc(info.doc) + (info.page ? " · " + esc(t("page_n", { p: info.page })) : "") + "</dd></div>" : "") +
      (platform ? "<div><dt>" + esc(t("lbl_plat")) + "</dt><dd>" + esc(platLabel(platform)) + "</dd></div>" : "") +
      (rels.length ? "<div><dt>" + esc(t("lbl_releases")) + "</dt><dd>" + esc(rels.join(", ")) + "</dd></div>" : "") +
      "</dl>" +
      '<div class="ve-links">' + canonLink(info.id, "ve-linkbtn-primary") +
      (info.doc ? pdfAnchor(info.doc, rels.filter(function (r) { return /^R\d\d-\d\d$/.test(r); }), info.page, platform) : "") +
      (!isFig && targets.length ? '<button type="button" class="ve-linkbtn" data-open-el="' + esc(targets[0].id) + '" data-el-view="snip">↗ ' + esc(targets[0].id) + '</button>' : "") +
      "</div></div>";
    if (isFig) {
      var fsha = figureSha(info);
      if (fsha) h += '<div class="ve-figbig">' + thumbHtml(fsha, info.caption, "big") + "</div>";
      h += aiHtml(info);
      var series = info.series || [];
      if (series.length) {
        h += '<section class="ve-sect ve-revsect" aria-labelledby="ve-fr-h"><h3 id="ve-fr-h">' + esc(t("series_head", { n: series.length })) + "</h3>" +
          (info.series_file ? '<p class="ve-muted ve-dd-hint">' + esc(t("td_hint")) + "</p>" : "") + '<div data-role="figrev"></div></section>';
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
    if (!isFig) {
      var snipShot = info.screenshot_path || info.screenshot;
      var mShot = snipShot ? /([0-9a-f]{12})\/page_(\d+)\.webp/.exec(snipShot) : null;
      if (mShot) {
        var sHash = mShot[1];
        var sPage = mShot[2];
        var fullCls = "snipfull-" + sHash + "-" + sPage;
        h += '<div class="ve-snipbig" id="ve-snipbig-' + esc(info.id) + '">' +
          '<div class="ve-snipbig-bar">' +
          '<button type="button" class="ve-btn ve-snipbig-toggle" data-act="snip-zoom" aria-expanded="false">🔍 Zoom</button>' +
          '<a href="#" target="_blank" rel="noopener noreferrer" class="ve-linkbtn ve-linkbtn-small ' + fullCls + '" hidden>↗ ' + esc(t("open_image")) + '</a>' +
          '</div>' +
          '<div class="ve-snipbig-frame">' +
          '<div data-snip-hash="' + esc(sHash) + '" data-snip-page="' + esc(sPage) + '" data-fig-alt="' + esc(info.caption || info.id) + '" data-fig-size="big" data-fig-img-class="ve-snipbig-img" data-full-target=".' + fullCls + '"></div>' +
          '</div></div>';
      }
    }
    if (info.text) {
      h += '<section class="ve-sect"><h3>' + esc(t(isFig ? "fig_text_head" : "text_head")) + '</h3><div class="ve-fulltext">' + linkIds(esc(info.text), null) + "</div></section>";
    }
    if (!isFig) {
      h += '<section class="ve-sect ve-revsect" aria-labelledby="ve-sr-h"><h3 id="ve-sr-h">' + esc(t("v_ver")) + '</h3><div data-role="sniprev"></div></section>';
    }
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

  // ------------------------------------------------------------------ Fragen-Viewer
  // Detail je Frage (versions/explorer/questions/<Q-…>.json, export_questions.py): Wortlaut in der Quellsprache,
  // englische Normalform als Zweitzeile, Art, Status, Ausgang, Anker mit Seiten-Links (Release bleibt), Verlauf aus
  // Erzeugung (Lauf, Prompt-Hash), abgeleiteten Ereignissen (Aufräumen) und Live-Ereignissen (Issues, Diskussionen).
  function loadQuestion(id, userAction) {
    var r = ui.q;
    var my = ++token.q;
    var signal = newSignal("q");
    shown.q = null;
    r.vbody.innerHTML = '<div class="ve-placeholder">' + esc(t("loading_detail", { id: id })) + "</div>";
    if (!/^Q-[0-9a-f]{16}$/.test(id)) { r.vbody.innerHTML = errorHtml(new Error(t("not_found", { id: id }))); return; }
    fetchJson(ROOT + "versions/explorer/questions/" + encodeURIComponent(id) + ".json", signal).then(function (info) {
      if (my !== token.q) return;
      if (!info || !info.ok) throw new Error(t("not_found", { id: id }));
      shown.q = id;
      r.vbody.innerHTML = questionHtml(info);
      r.vbody.parentNode.scrollTop = 0;
      if (userAction && !narrowMQ.matches) r.list.focus({ preventScroll: true });
    }).catch(function (err) {
      if (my !== token.q || C.isAbortError(err) || pageHidden) return;
      shown.q = null;
      r.vbody.innerHTML = err && err.status === 404 ? '<div class="ve-error" role="alert"><p>' + esc(t("not_found", { id: id })) + "</p></div>"
        : errorHtml(err);
    });
  }

  function shortHash(h) { return String(h || "").slice(0, 12); }
  function srcLink(src) {
    if (!src || !src.url || !/^https:\/\//.test(src.url)) return src && src.type ? esc(t("qsrc_" + src.type)) : "";
    var m = /github\.com\/[^/]+\/[^/]+\/(issues|discussions|pull)\/(\d+)/.exec(src.url);
    var label = m ? (m[1] === "discussions" ? t("q_discussion_n", { n: m[2] }) : t("q_issue_n", { n: m[2] })) : t("qsrc_" + (src.type || "manual"));
    return '<a href="' + esc(src.url) + '" target="_blank" rel="noopener noreferrer">' + esc(label) + "</a>";
  }
  function evidenceLinks(list) {
    list = (list || []).filter(function (e) { return e && /^https:\/\//.test(e.url || ""); });
    if (!list.length) return "";
    return '<ul class="ve-q-evidence">' + list.map(function (e) {
      return '<li><a href="' + esc(e.url) + '" target="_blank" rel="noopener noreferrer">' + esc(e.label || e.url) + "</a></li>";
    }).join("") + "</ul>";
  }
  function historyHtml(info) {
    var hist = info.history || [];
    if (!hist.length) return '<p class="ve-muted">' + esc(t("q_hist_none")) + "</p>";
    return '<ol class="ve-q-hist">' + hist.map(function (h) {
      var by = h.by || {}, op = h.op || "", body = [];
      if (op === "generated") {
        body.push(esc(t("qh_generated_text", { model: by.name || "–", run: by.run ? String(by.run).slice(0, 8) : "–" })));
        body.push('<span class="ve-muted">' + esc(t("q_prompt")) + " <code>" + esc(shortHash(h.prompt_hash)) + "</code>" +
          (h.recipe ? " · " + esc(h.recipe) : "") + "</span>");
        var o = h.original;
        if (o && (o.assumption || o.text)) {
          body.push('<span class="ve-q-orig"><span class="ve-muted">' + esc(t("qh_original", { lang: o.lang || "" })) + ":</span> " +
            '<span lang="' + esc(o.lang || "") + '">' + esc(o.assumption || o.text) +
            (o.rationale ? " — " + esc(o.rationale) : "") + "</span></span>");
        }
      } else if (op === "normalise") {
        var pv = h.provenance || {};
        body.push('<span lang="en">' + esc(h.assumption_en || h.text_en || "") + "</span>");
        if (h.rationale_en) body.push('<span class="ve-muted">' + esc(t("q_rationale")) + ":</span> " + '<span lang="en">' + esc(h.rationale_en) + "</span>");
        body.push('<span class="ve-muted">' + esc(t("qh_normalise_text", { model: pv.model || "–" })) + "</span>");
      } else if (h.origin === "derived") {
        if (op === "resolve") {
          body.push(esc(t("qh_unused_text")));
          (h.last_seen || []).forEach(function (ls, k) {
            var rb = (h.replaced_by || [])[k] || {};
            body.push('<span class="ve-muted">' + esc(t("qh_unused_prompts", { from: shortHash(ls.prompt_hash) || "–",
              to: rb.prompt_hash ? shortHash(rb.prompt_hash) : t("qh_fragment_gone") })) + "</span>");
          });
        } else if (op === "reappear") body.push(esc(t("qh_reappear_text")));
        else if (op === "continue") body.push(esc(t("qh_continue_text")));
        if (h.harvest) body.push('<span class="ve-muted">' + esc(t("qh_harvest", { id: h.harvest })) + "</span>");
      } else {
        if (h.outcome) body.push("<strong>" + esc(t("qo_" + h.outcome)) + "</strong>");
        if (h.explanation) body.push(esc(h.explanation));
        if (h.text) body.push(esc(h.text));
        if (h.reason) body.push('<span class="ve-muted">' + esc(t("q_reason", { r: h.reason })) + "</span>");
        if (h.evidence && h.evidence.length) body.push(evidenceLinks(h.evidence));
      }
      var who = op === "generated" ? t("qby_guide") : h.origin === "derived" ? t("qby_harvest") : op === "normalise" ? t("qby_worker")
        : (by.name ? by.name + " (" + t("qby_" + (by.kind || "curator")) + ")" : t("qby_" + (by.kind || "curator")));
      var src = h.source && op !== "normalise" ? srcLink(h.source) : "";
      return '<li class="ve-q-ev ve-q-ev-' + esc(op) + '"><div class="ve-q-evhead"><span class="ve-q-evop">' + esc(t("qh_" + op)) +
        "</span>" + (h.at ? ' <time datetime="' + esc(h.at) + '">' + esc(fmtDate(h.at)) + "</time>" : "") +
        ' <span class="ve-muted">' + esc(who) + "</span>" + (src ? " · " + src : "") + "</div>" +
        (body.length ? '<div class="ve-q-evbody">' + body.join("<br>") + "</div>" : "") + "</li>";
    }).join("") + "</ol>";
  }
  function anchorHtml(a) {
    var label, kind;
    if (a.type === "fragment") {
      kind = t("qa_" + (a.subject_type || "fragment"));
      label = a.subject_type === "element" ? a.subject : t("qsub_" + a.subject_type, { name: a.subject });
    } else if (a.type === "element" || a.type === "pair") {
      kind = t("qa_element"); label = a.element_id || a.target_element;
    } else if (a.type === "snippet") {
      kind = t("qa_snippet"); label = a.snippet_id;
    } else { kind = t("qa_" + a.type); label = a.cluster || a.fragment || ""; }
    var links = [];
    if (a.page) links.push('<a class="ve-linkbtn ve-linkbtn-primary" href="' + esc(a.page) + '">' + esc(t("q_open_page")) + "</a>");
    var eid = a.type === "fragment" && a.subject_type === "element" ? a.subject : (a.element_id || a.target_element);
    if (eid) links.push('<button type="button" class="ve-linkbtn" data-open-el="' + esc(eid) + '">' + esc(t("q_in_el_browser")) + "</button>");
    var sid = a.snippet_id;
    if (sid) links.push('<a class="ve-linkbtn" href="' + esc(C.figureHref(ROOT, sid, stems("item"))) + '">' +
      esc(t(/^FIG-/.test(sid) ? "page_fig" : "page_snip")) + "</a>");
    var meta = [];
    if (a.platform) meta.push(esc(platLabel(a.platform)));
    if (a.module) meta.push(esc(a.module));
    if (a.releases && a.releases.length) meta.push(esc(a.releases.join(", ")));
    if (a.guide_kind) meta.push(esc(t("qgk_" + a.guide_kind)));
    if (a.recipe) meta.push(esc(a.recipe));
    if (a.prompt_hash) meta.push(esc(t("q_prompt")) + " <code>" + esc(shortHash(a.prompt_hash)) + "</code>");
    return '<li class="ve-q-anchor"><div><span class="ve-mini">' + esc(kind) + "</span> <strong>" + esc(label) + "</strong>" +
      (a.name ? ' <span class="ve-muted">' + esc(a.name) + "</span>" : "") + "</div>" +
      (meta.length ? '<div class="ve-cardmeta">' + meta.join('<span aria-hidden="true"> · </span>') + "</div>" : "") +
      (a.fragment ? '<div class="ve-cardmeta"><code>' + esc(a.fragment.replace(/^content\/ai\//, "")) + "</code></div>" : "") +
      (links.length ? '<div class="ve-cardlinks">' + links.join("") + "</div>" : "") + "</li>";
  }
  // Vorschlag für eine Antwort als GitHub-Issue (Kurationseingang, curation_ingest.py übernimmt den JSON-Block)
  function proposeHref(info) {
    var m = document.querySelector('meta[name="review-github-repo"]');
    var repo = (m && m.content) || "2b-rs/autodocs";
    var tmpl = { schema: "question-event@1", op: "answer", qid: info.id, outcome: "confirmed | refuted | partially_confirmed",
                 explanation: "", evidence: [{ url: "https://…" }] };
    var body = t("q_propose_body", { q: info.text }) + "\n\n```json\n" + JSON.stringify(tmpl, null, 1) + "\n```\n";
    return "https://github.com/" + repo + "/issues/new?title=" + encodeURIComponent(t("q_propose_title", { id: info.id })) +
      "&body=" + encodeURIComponent(body);
  }
  function questionHtml(info) {
    var st = info.status || "", reason = info.status_reason;
    var chips = '<span class="ve-mini ve-qk ve-qk-' + esc(info.kind) + '">' + esc(t("qk_" + info.kind)) + "</span>" +
      '<span class="ve-qstat ve-qst-' + esc(st) + '">' + esc(t("qs_" + st)) + "</span>" +
      (info.outcome ? '<span class="ve-mini ve-qoc">' + esc(t("qo_" + info.outcome)) + "</span>" : "") +
      (reason ? '<span class="ve-mini ve-qreason">' + esc(t("qr_" + reason) !== "qr_" + reason ? t("qr_" + reason) : reason) + "</span>" : "");
    var en = info.lang !== "en" ? (info.text_en
      ? '<p class="ve-q-en" lang="en"><span class="ve-muted">EN:</span> ' + esc(info.text_en) + "</p>"
      : '<p class="ve-q-en ve-muted">' + esc(t("q_en_none")) + "</p>") : "";
    var meta = [[t("lbl_q_id"), info.id], [t("f_qkind"), t("qk_" + info.kind)], [t("f_qstatus"), t("qs_" + st)]];
    if (info.platform) meta.push([t("lbl_plat"), platLabel(info.platform)]);
    if ((info.modules || []).length) meta.push([t("lbl_module"), info.modules.join(", ")]);
    meta.push([t("lbl_q_lang"), info.lang || "–"]);
    if (info.kind === "assumption") meta.push([t("lbl_q_asserted"), t(info.asserted ? "q_asserted_yes" : "q_asserted_no")]);
    var h = '<div class="ve-vh"><div class="ve-vh-top"><h2 class="ve-vh-id ve-vh-title ve-q-title" lang="' + esc(info.lang || "") + '">' +
      esc(info.text) + '</h2></div><div class="ve-vh-name ve-q-chips">' + chips + "</div>" + en +
      '<dl class="ve-meta">' + meta.map(function (m) { return "<div><dt>" + esc(m[0]) + "</dt><dd>" + esc(m[1]) + "</dd></div>"; }).join("") + "</dl>" +
      '<div class="ve-links"><button type="button" class="ve-linkbtn" data-act="copy">' + esc(t("copy_link")) + "</button>" +
      '<a class="ve-linkbtn" target="_blank" rel="noopener noreferrer" href="' + esc(proposeHref(info)) + '">' + esc(t("q_propose")) + "</a></div></div>";
    if (info.kind === "assumption") {
      h += '<section class="ve-sect ve-q-assumption"><h3>' + esc(t("q_assumption_head")) + '</h3><p lang="' + esc(info.lang || "") + '">' +
        esc(info.assumption || "") + "</p>" + (info.rationale ? '<p class="ve-q-why" lang="' + esc(info.lang || "") + '"><span>' +
        esc(t("q_rationale")) + ":</span> " + esc(info.rationale) + "</p>" : "") +
        '<p class="ve-muted ve-q-motto">' + esc(t("q_motto")) + "</p></section>";
    }
    var resolvedBy = info.resolved_by;
    if (info.outcome || info.explanation || (info.evidence || []).length || reason) {
      h += '<section class="ve-sect ve-q-result"><h3>' + esc(t("q_result_head")) + "</h3>" +
        (info.outcome ? "<p><strong>" + esc(t("qo_" + info.outcome)) + "</strong></p>" : "") +
        (info.explanation ? "<p>" + esc(info.explanation) + "</p>" : "") +
        (reason === "assumption_no_longer_used" ? '<p class="ve-muted">' + esc(t("q_unused_note")) +
          (resolvedBy && resolvedBy.at ? " " + esc(t("q_since", { d: fmtDate(resolvedBy.at) })) : "") + "</p>" : "") +
        evidenceLinks(info.evidence) +
        (info.status === "answered" || info.status === "resolved" ? '<p class="ve-q-normnote">' + esc(t("q_not_normative")) + "</p>" : "") +
        "</section>";
    }
    h += '<section class="ve-sect"><h3>' + esc(t("q_anchors_head", { n: num((info.anchors || []).length) })) + '</h3><ul class="ve-q-anchors">' +
      (info.anchors || []).map(anchorHtml).join("") + "</ul></section>";
    h += '<section class="ve-sect ve-q-history"><h3>' + esc(t("q_history_head")) + "</h3>" + historyHtml(info) + "</section>";
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
    [EL.rev, FR.ctl, SR.ctl].forEach(function (c) { if (c) c.redraw(); });
    TABS.forEach(function (tab) { if (ui[tab]) setDetailMode(tab, !!selectedKey(tab) && narrowMQ.matches); });
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
  if (restoreOrder()) {
    try { window.history.replaceState(window.history.state, "", window.location.pathname + C.serializeState(state) + window.location.hash); }
    catch (e) { /* ignore */ }
  }
  TABS.forEach(function (tab) {
    renderOrderPanel(tab);
    if (C.orderActive(state, tab)) setOrderOpen(tab, true);
  });
  // Katalog (Liste) und Filterliste starten in allen drei Reitern sichtbar, auch bei einem Deep-Link.
  TABS.forEach(function (tab) {
    if (C.catalogCollapsedOnLoad(tab, state)) setCollapsed(tab, true);
  });
  try { window.scrollTo(0, 0); } catch (e) { /* ignore */ }
  TABS.forEach(function (tab) { ui[tab].q.value = state[tab].q || ""; });
  var started = switchTab(state.tab, false);
  // Elementindex erst nach dem ersten Zeichnen des aktiven Reiters (Ziele, Verweise und Zähler im Viewer);
  // der dritte Index lädt beim Wechsel in seinen Reiter
  if (state.tab !== "el") {
    started.then(function () {
      whenIdle(function () { ensureLoaded("el").then(function () { refresh("el"); syncViewer("el"); }); });
    });
  }
  layout();
})();
