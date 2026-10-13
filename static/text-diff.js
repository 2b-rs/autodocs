/*
 * text-diff.js — wortgenauer Textvergleich (Nebeneinander mit Verbindern, Unified, Volltext).
 *
 * Gemeinsam genutzt vom Versions- & Provenienz-Explorer (Spezifikationstexte und KI-Beschreibungen
 * der Fassungen einer Bildreihe) und den kanonischen Schaubild-Seiten spec/figures/FIG-*.html.
 * Kern (Zeilen, Opcodes, Wortdiff, Ausrichtung) ist unter Node als module.exports verfügbar.
 * Die Darstellung bringt ihre Stile selbst mit (ensureStyles), damit sie auf jeder Seite gleich aussieht;
 * sie überschreiben ältere globale Regeln aus style.css (z. B. .ve-split-columns{min-width:680px}).
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.TextDiff = api;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  function esc(str) {
    return String(str == null ? "" : str).replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  var NAMED = { lt: "<", gt: ">", amp: "&", quot: '"', apos: "'", nbsp: " ", "#39": "'" };
  function decode(s) {
    return String(s || "").replace(/&(#\d+|#x[0-9a-f]+|[a-z]+);/gi, function (m, n) {
      if (n[0] === "#") {
        var c = n[1] === "x" || n[1] === "X" ? parseInt(n.slice(2), 16) : parseInt(n.slice(1), 10);
        return c > 0 && c < 0x110000 ? String.fromCodePoint(c) : m;
      }
      return Object.prototype.hasOwnProperty.call(NAMED, n.toLowerCase()) ? NAMED[n.toLowerCase()] : m;
    });
  }

  // ------------------------------------------------------------------ Zeilen

  // Lange Zeilen an Satzgrenzen teilen, damit Änderungen nicht ganze Absätze markieren
  function splitLong(lines, max) {
    var out = [];
    (lines || []).forEach(function (l) {
      var s = String(l).trim();
      if (!s) return;
      if (s.length > (max || 160)) s.split(/(?<=[.!?;])\s+(?=[A-ZÄÖÜ0-9„"(•])/).forEach(function (x) { if (x.trim()) out.push(x.trim()); });
      else out.push(s);
    });
    return out;
  }

  // Markdown-Beschreibung -> lesbare Zeilen (Überschriften, Listenpunkte, Absätze, Tabellenzeilen)
  function mdLines(md) {
    var out = [];
    String(md || "").split(/\r?\n/).forEach(function (raw) {
      var s = raw.trim();
      if (!s || /^(-{3,}|\*{3,}|_{3,})$/.test(s)) return;
      if (/^\|?\s*:?-{3,}/.test(s)) return;                       // Trennzeile einer Tabelle
      s = s.replace(/^#{1,6}\s+/, "");                             // Überschrift
      s = s.replace(/^[-*+]\s+/, "• ");                             // Listenpunkt
      if (/^\|.*\|$/.test(s)) s = s.replace(/^\||\|$/g, "").split("|").map(function (c) { return c.trim(); }).join(" | ");
      s = s.replace(/\*\*([^*]+)\*\*/g, "$1").replace(/__([^_]+)__/g, "$1").replace(/`([^`]+)`/g, "$1");
      out.push(decode(s));
    });
    return splitLong(out);
  }

  // Erzeugtes HTML (format_markdown_to_html der Schaubild-Seiten) -> Zeilen, ohne DOM
  function htmlLines(html) {
    var s = String(html || "").replace(/<br\s*\/?>/gi, "\n")
      .replace(/<li[^>]*>/gi, "\n• ").replace(/<\/(p|li|h[1-6]|tr|div|ul|ol|table|blockquote)>/gi, "\n")
      .replace(/<(td|th)[^>]*>/gi, " | ").replace(/<hr[^>]*>/gi, "\n").replace(/<[^>]+>/g, "");
    return splitLong(decode(s).split("\n").map(function (l) { return l.replace(/^\s*\|\s*/, "").replace(/\s+/g, " ").trim(); })
      .filter(Boolean));
  }

  // ------------------------------------------------------------------ Vergleich

  function opcodes(a, b) {
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

  function wordDiff(ta, tb) {
    var re = /[<>\-]|[\wÀ-ɏ]+|[^\s\wÀ-ɏ<>\-]+|\s+/g;
    var A = ta.match(re) || [], B = tb.match(re) || [];
    var outA = "", outB = "";
    opcodes(A, B).forEach(function (op) {
      var sa = A.slice(op[1], op[2]).join(""), sb = B.slice(op[3], op[4]).join("");
      if (op[0] === "equal") { outA += esc(sa); outB += esc(sb); }
      else {
        if (op[0] !== "insert") outA += sa.trim() ? '<del class="ve-word-deleted">' + esc(sa) + "</del>" : esc(sa);
        if (op[0] !== "delete") outB += sb.trim() ? '<ins class="ve-word-added">' + esc(sb) + "</ins>" : esc(sb);
      }
    });
    return [outA, outB];
  }

  // Zeilenweise ausrichten, ersetzte Abschnitte wortgenau markieren
  function align(linesA, linesB) {
    var blocks = [], lines = [], bi = 0;
    opcodes(linesA, linesB).forEach(function (op) {
      var L = linesA.slice(op[1], op[2]), R = linesB.slice(op[3], op[4]), lh = "", rh = "";
      if (op[0] === "equal") { lh = esc(L.join("\n")); rh = esc(R.join("\n")); L.forEach(function (l) { lines.push({ type: "unchanged", text: l }); }); }
      else if (op[0] === "replace") {
        var w = wordDiff(L.join("\n"), R.join("\n")); lh = w[0]; rh = w[1];
        L.forEach(function (l) { lines.push({ type: "deleted", text: l }); });
        R.forEach(function (l) { lines.push({ type: "added", text: l }); });
      } else if (op[0] === "delete") { lh = esc(L.join("\n")); L.forEach(function (l) { lines.push({ type: "deleted", text: l }); }); }
      else { rh = esc(R.join("\n")); R.forEach(function (l) { lines.push({ type: "added", text: l }); }); }
      blocks.push({ id: "b-" + (++bi), tag: op[0], left_lines: L, right_lines: R, left_html: lh, right_html: rh });
    });
    return { blocks: blocks, lines: lines };
  }

  function stats(lines) {
    var s = { added: 0, deleted: 0, unchanged: 0 };
    (lines || []).forEach(function (l) { s[l.type] = (s[l.type] || 0) + 1; });
    return s;
  }

  // ------------------------------------------------------------------ Token-Strom (gerendertes, sicheres HTML)

  // Vergleich auf dem Token-Strom eines bereits sicher gerenderten Dokuments (renderMarkdown des Explorers
  // maskiert jeden Text, rohes HTML erscheint nie): Tags sind eigene Tokens, Text zerfällt in Wörter,
  // Satzzeichen und Leerraum. Leerraum vergleicht als ein Leerzeichen. Zuerst werden Blöcke (Absatz,
  // Listenpunkt, Tabellenzeile …) ausgerichtet, dann ersetzte Blockfolgen wortgenau. Die Ausgabe gibt die
  // Tags einer Seite unverändert in ihrer Reihenfolge aus; Markierungen umschließen nur Textläufe.
  var VOID_TAGS = { br: 1, hr: 1, img: 1, wbr: 1 };
  var BLOCK_END = /^<\/(p|li|h[1-6]|tr|pre|blockquote|div|table|ul|ol|thead|tbody)\s*>$|^<(hr|br)\b/i;
  var WORD_RE = /&#?\w+;|-|[\p{L}\p{N}_]+|\s+|[^\s\p{L}\p{N}_&\-]+|&/gu;

  function tokenize(html) {
    var out = [];
    String(html == null ? "" : html).split(/(<[^<>]*>)/).forEach(function (part) {
      if (!part) return;
      if (part[0] === "<" && part[part.length - 1] === ">") { out.push({ tag: true, s: part, k: part.replace(/\s+/g, " ") }); return; }
      (part.match(WORD_RE) || []).forEach(function (w) {
        var ws = !w.trim();
        out.push({ s: w, ws: ws, k: ws ? " " : w });
      });
    });
    return out;
  }
  function tagName(tok) { var m = /^<\/?\s*([a-z0-9]+)/i.exec(tok.s); return m ? m[1].toLowerCase() : ""; }
  function keysOfToks(toks) { return toks.map(function (t) { return t.k; }); }
  function blockUnits(toks) {
    var units = [], start = 0;
    toks.forEach(function (t, i) {
      if (t.tag && BLOCK_END.test(t.s)) { units.push({ s: start, e: i + 1 }); start = i + 1; }
    });
    if (start < toks.length) units.push({ s: start, e: toks.length });
    return units.map(function (u) { u.k = keysOfToks(toks.slice(u.s, u.e)).join(""); return u; });
  }
  function onlyWs(toks) { return toks.length > 0 && toks.every(function (t) { return !t.tag && t.ws; }); }
  function hasText(toks) { return toks.some(function (t) { return !t.tag && !t.ws; }); }

  /**
   * Segmente zweier HTML-Fassungen: [{op: "equal"|"insert"|"delete"|"replace", a: [Token], b: [Token]}].
   * Benachbarte Änderungen verschmelzen, auch über reinen Leerraum hinweg; eine Entfernung direkt vor einer
   * Ergänzung ist eine Ersetzung. Unterschiede nur im Leerraum gelten als gleich.
   */
  function segmentHtml(htmlA, htmlB) {
    var A = tokenize(htmlA), B = tokenize(htmlB);
    var ua = blockUnits(A), ub = blockUnits(B), ops = [];
    function at(units, i, total) { return i < units.length ? units[i].s : total; }
    opcodes(ua.map(function (u) { return u.k; }), ub.map(function (u) { return u.k; })).forEach(function (op) {
      var as = at(ua, op[1], A.length), ae = op[2] > op[1] ? ua[op[2] - 1].e : as;
      var bs = at(ub, op[3], B.length), be = op[4] > op[3] ? ub[op[4] - 1].e : bs;
      if (op[0] !== "replace" || (ae - as) * (be - bs) > 4e6) { ops.push([op[0], as, ae, bs, be]); return; }
      opcodes(keysOfToks(A.slice(as, ae)), keysOfToks(B.slice(bs, be))).forEach(function (o) {
        ops.push([o[0], as + o[1], as + o[2], bs + o[3], bs + o[4]]);
      });
    });
    var segs = [];
    ops.forEach(function (op) {
      var s = { op: op[0], a: A.slice(op[1], op[2]), b: B.slice(op[3], op[4]) };
      if (!s.a.length && !s.b.length) return;
      var last = segs[segs.length - 1];
      if (s.op === "equal") {
        if (last && last.op === "equal") { last.a = last.a.concat(s.a); last.b = last.b.concat(s.b); }
        else segs.push(s);
        return;
      }
      if (last && last.op !== "equal") { last.a = last.a.concat(s.a); last.b = last.b.concat(s.b); return; }
      var prev = segs[segs.length - 2];
      if (last && prev && prev.op !== "equal" && onlyWs(last.b)) {
        segs.pop();
        prev.a = prev.a.concat(last.a, s.a); prev.b = prev.b.concat(last.b, s.b);
        return;
      }
      segs.push(s);
    });
    segs.forEach(function (s) {
      if (s.op === "equal") return;
      s.op = s.a.length && s.b.length ? "replace" : (s.a.length ? "delete" : "insert");
    });
    return segs;
  }

  // Schreiber mit Stapel offener Tags: entfernter Text landet nur an Stellen, an denen Text stehen darf
  // Entfernte ganze Blöcke (Listenpunkt, Absatz, Tabellenzeile) warten auf das Ende des laufenden Blocks und
  // erscheinen dann als eigener Block an derselben Stelle (defer/flush).
  function Writer() {
    var w = { h: "", st: [], later: [] };
    w.tok = function (t) {
      w.h += t.s;
      if (!t.tag || /^<!/.test(t.s)) return;
      var n = tagName(t);
      if (/^<\//.test(t.s)) { var i = w.st.lastIndexOf(n); if (i >= 0) w.st.length = i; }
      else if (!VOID_TAGS[n] && !/\/>$/.test(t.s)) w.st.push(n);
      if (BLOCK_END.test(t.s)) w.flush();
    };
    w.defer = function (h) { w.later.push(h); };
    w.flush = function () { var x = w.later; w.later = []; x.forEach(function (h) { w.piece(h); }); };
    w.raw = function (h) { w.h += h; };
    w.piece = function (h) {
      var top = w.st[w.st.length - 1] || "";
      if (top === "ul" || top === "ol") w.h += '<li class="td-int-gone">' + h + "</li>";
      else if (/^(table|thead|tbody|tfoot)$/.test(top)) w.h += '<tr class="td-int-gone"><td colspan="99">' + h + "</td></tr>";
      else if (top === "tr") w.h += '<td class="td-int-gone">' + h + "</td>";
      else if (!top || top === "div" || top === "blockquote") w.h += '<p class="td-int-gone">' + h + "</p>";
      else w.h += h;
    };
    // Tokens ausgeben, Textläufe (ohne reinen Leerraum) in open/close
    w.runs = function (toks, open, close) {
      var run = [];
      function flush() {
        if (!run.length) return;
        var s = run.map(function (t) { return t.s; }).join("");
        var m = /^(\s*)([\s\S]*?)(\s*)$/.exec(s);
        w.h += m[2] ? m[1] + open + m[2] + close + m[3] : s;
        run = [];
      }
      toks.forEach(function (t) { if (t.tag) { flush(); w.tok(t); } else run.push(t); });
      flush();
    };
    return w;
  }
  // Tokenfolge an Blockgrenzen teilen (die Grenz-Tags selbst entfallen)
  function splitBlocks(toks) {
    var parts = [[]];
    toks.forEach(function (t) { if (t.tag && BLOCK_END.test(t.s)) parts.push([]); else parts[parts.length - 1].push(t); });
    return parts;
  }
  // Text einer Tokenfolge (bleibt maskiertes HTML), Blockgrenzen als Leerzeichen
  function tokText(toks) {
    return toks.map(function (t) { return t.tag ? (BLOCK_END.test(t.s) ? " " : "") : t.s; }).join("").replace(/\s+/g, " ").trim();
  }

  // Nebeneinander auf gerendertem HTML: links Entferntes in <del>, rechts Ergänztes in <ins>, Struktur bleibt
  function diffHtmlPair(htmlA, htmlB) {
    var L = Writer(), R = Writer();
    segmentHtml(htmlA, htmlB).forEach(function (s) {
      if (s.op === "equal") { s.a.forEach(L.tok); s.b.forEach(R.tok); return; }
      L.runs(s.a, '<del class="ve-word-deleted">', "</del>");
      R.runs(s.b, '<ins class="ve-word-added">', "</ins>");
    });
    return [L.h, R.h];
  }

  // Schlichter Text (Spezifikationswortlaut, Snippets) als sicheres HTML: eine Zeile je Absatz
  function plainHtml(lines) {
    return (lines || []).map(function (l) { return '<p class="td-int-line">' + esc(l) + "</p>"; }).join("");
  }

  /**
   * Integrierter Diff: die neue Fassung mit eingearbeiteten Änderungen.
   * o = {style: "a"|"b", labels}. Stil A: Entferntes als schmale Marke (Text im Tooltip), Ergänztes
   * hervorgehoben, Ersetztes hervorgehoben mit Tooltip „alt → neu“. Stil B: Entferntes durchgestrichen,
   * Ergänztes hervorgehoben, Ersetzung als ~~alt~~ → neu.
   * Rückgabe {html, counts: {add, del, rep}}; Tooltips stehen als verborgene role=tooltip-Elemente dabei.
   */
  function integratedHtml(htmlA, htmlB, o) {
    o = o || {};
    var Lb = labelsOf(o.labels), style = o.style === "b" ? "b" : "a";
    var w = Writer(), tips = [], n = { add: 0, del: 0, rep: 0 };
    function tip(head, body) {
      var id = "td-tip-" + (++tipSeq);
      tips.push('<div class="td-tip td-int-tip" role="tooltip" id="' + id + '" hidden><div class="td-tip-head"><strong>' + esc(head) +
        "</strong></div>" + body + "</div>");
      return id;
    }
    function removed(oldH) {
      if (style === "b") return '<del class="td-int-del">' + oldH + "</del>";
      var id = tip(Lb.int_removed, '<del class="td-int-old">' + oldH + "</del>");
      return '<button type="button" class="td-int-mark" data-td-tip="' + id + '" aria-describedby="' + id + '" aria-label="' + esc(Lb.int_removed) + '"></button>';
    }
    segmentHtml(htmlA, htmlB).forEach(function (s) {
      if (s.op === "equal") { s.b.forEach(w.tok); return; }
      // Entfernter Text bis zur ersten Blockgrenze gehört an diese Stelle, jeder weitere Block als eigener Block
      var parts = splitBlocks(s.a).map(tokText), oldH = parts[0], newText = hasText(s.b);
      if (oldH && newText && parts.length === 1 && !s.b.some(function (t) { return t.tag; })) {
        var m = /^(\s*)([\s\S]*?)(\s*)$/.exec(s.b.map(function (t) { return t.s; }).join(""));
        n.rep++;
        if (style === "b") {
          w.raw(m[1] + '<del class="td-int-del">' + oldH + '</del><span class="td-int-arrow" aria-hidden="true"> → </span><ins class="td-int-add">' +
            m[2] + "</ins>" + m[3]);
        } else {
          var id = tip(Lb.int_replaced, '<del class="td-int-old">' + oldH + '</del> <span class="td-int-arrow" aria-hidden="true">→</span> <ins class="td-int-new">' + m[2] + "</ins>");
          w.raw(m[1] + '<ins class="td-int-add td-int-rep" tabindex="0" data-td-tip="' + id + '" aria-describedby="' + id + '">' + m[2] + "</ins>" + m[3]);
        }
        return;
      }
      if (oldH) { n.del++; w.piece(removed(oldH)); }
      parts.slice(1).forEach(function (x) { if (x) { n.del++; w.defer(removed(x)); } });
      if (newText) n.add++;
      w.runs(s.b, '<ins class="td-int-add">', "</ins>");
    });
    w.flush();
    return { html: '<div class="td-int-doc td-int-' + style + '">' + w.h + "</div>" + (tips.length ? '<div class="td-tips">' + tips.join("") + "</div>" : ""),
             counts: n };
  }

  // Markdown-Quelle in Vergleichseinheiten: Zeile, ganzer Codeblock, ganze Tabelle (Leerzeilen entfallen)
  function mdUnits(md) {
    var lines = String(md == null ? "" : md).replace(/\r\n?/g, "\n").split("\n"), out = [], i = 0, j;
    function push(src) {
      var s = src.join("\n");
      out.push({ src: s, k: src.map(function (l) { return l.trim().replace(/\s+/g, " "); }).join("\n"),
                 indent: (/^\s*/.exec(src[0]) || [""])[0].replace(/\t/g, "    ").length });
    }
    while (i < lines.length) {
      var l = lines[i], fm = /^\s*(```|~~~)/.exec(l);
      if (!l.trim()) { i++; continue; }
      if (fm) {
        for (j = i + 1; j < lines.length && lines[j].trim().indexOf(fm[1]) !== 0; j++) { /* bis zum Ende des Codeblocks */ }
        push(lines.slice(i, j + 1)); i = j + 1; continue;
      }
      if (/^\s*\|.*\|\s*$/.test(l)) {
        for (j = i; j < lines.length && /^\s*\|.*\|\s*$/.test(lines[j]); j++) { /* ganze Tabelle */ }
        push(lines.slice(i, j)); i = j; continue;
      }
      push([l]); i++;
    }
    return out;
  }
  function renderUnits(units, renderMd) {
    return units.map(function (u) {
      var h = renderMd(u.src.replace(/^\s+/, "")), num = /^\s*(\d{1,3})[.)]\s/.exec(u.src);
      if (num && +num[1] !== 1) h = h.replace("<ol>", '<ol start="' + (+num[1]) + '">');
      var lvl = Math.min(3, Math.floor(u.indent / 2));
      return lvl ? '<div class="td-ind td-ind-' + lvl + '">' + h + "</div>" : h;
    }).join("");
  }
  // Ausrichtung zweier Markdown-Texte für „Nebeneinander“: Einheiten wie align, Inhalt gerendert, Wortmarken
  // innerhalb der gerenderten Struktur (Listen, Code, Hervorhebung, Tabellen bleiben erhalten)
  function alignMarkdown(mdA, mdB, renderMd) {
    var UA = mdUnits(mdA), UB = mdUnits(mdB), blocks = [], bi = 0;
    opcodes(UA.map(function (u) { return u.k; }), UB.map(function (u) { return u.k; })).forEach(function (op) {
      var L = UA.slice(op[1], op[2]), R = UB.slice(op[3], op[4]), lh = "", rh = "";
      if (op[0] === "equal") lh = rh = renderUnits(R, renderMd);
      else if (op[0] === "replace") { var p = diffHtmlPair(renderUnits(L, renderMd), renderUnits(R, renderMd)); lh = p[0]; rh = p[1]; }
      else if (op[0] === "delete") lh = renderUnits(L, renderMd);
      else rh = renderUnits(R, renderMd);
      blocks.push({ id: "b-" + (++bi), tag: op[0], rich: true, left_lines: L.map(function (u) { return u.src; }),
                    right_lines: R.map(function (u) { return u.src; }), left_html: lh, right_html: rh });
    });
    return blocks;
  }

  // ------------------------------------------------------------------ Darstellung

  var CSS = ".ve-split-diff-wrapper{border:1px solid var(--border-default);border-radius:10px;overflow:hidden;overscroll-behavior:contain;overflow-anchor:none;height:460px;max-height:calc(100vh - 240px);min-height:260px;background:var(--bg-canvas);display:flex;flex-direction:column}\n.ve-split-columns{display:grid;grid-template-columns:minmax(0,1fr) 56px minmax(0,1fr);position:relative;width:100%;min-width:0;flex:1;min-height:0;overflow:hidden}\n.ve-split-pane{background:var(--bg-canvas);overflow:hidden;display:flex;flex-direction:column;min-height:0;min-width:0}\n.ve-split-header{padding:.55rem .8rem;background:var(--bg-subtle);border-bottom:1px solid var(--border-default);font-size:.8rem;font-weight:700;display:flex;justify-content:space-between;align-items:center;gap:.4rem;flex-shrink:0;flex-wrap:wrap}\n.ve-header-left{border-top:3px solid #2563eb}\n.ve-header-gutter{border-top:3px solid var(--color-teal-600);justify-content:center;color:var(--color-ink-muted);font-size:.7rem;padding:.55rem .2rem}\n.ve-header-right{border-top:3px solid #16a34a}\n.ve-split-header code{font-size:.72rem;font-weight:600;background:transparent;padding:0;border:0;overflow-wrap:anywhere}\n.ve-split-body{padding:.8rem;font-family:var(--font-mono);font-size:.84rem;line-height:1.6;white-space:pre-wrap;word-break:break-word;flex:1;overflow-y:auto;overflow-x:hidden;position:relative;overscroll-behavior:contain;overflow-anchor:none}\n.ve-split-gutter{position:relative;width:auto;background:var(--bg-canvas);display:flex;flex-direction:column;min-height:0;min-width:0;overflow:hidden}\n.ve-gutter-canvas-wrap{position:relative;width:auto;flex:1;min-height:0;overflow:hidden}\n.ve-gutter-svg{position:absolute;top:0;left:0;width:100%;height:100%;overflow:visible}\n.ve-connector{cursor:pointer}\n.ve-connector-replace{fill:rgba(217,119,6,.18);stroke:#d97706;stroke-width:1}\n.ve-connector-delete{fill:rgba(220,38,38,.18);stroke:#dc2626;stroke-width:1}\n.ve-connector-insert{fill:rgba(22,163,74,.18);stroke:#16a34a;stroke-width:1}\n.ve-connector.is-hovered{opacity:.9;stroke-width:2}\n.ve-block{margin:.35rem 0;padding:.3rem .55rem;border-radius:6px;border-left:3px solid transparent}\n.ve-block-equal{color:var(--color-ink)}\n.ve-block-deleted{background:rgba(220,38,38,.12);border-left-color:#dc2626}\n.ve-block-added{background:rgba(22,163,74,.12);border-left-color:#16a34a}\n.ve-block-replaced.ve-block-left{background:rgba(220,38,38,.07);border-left-color:#dc2626}\n.ve-block-replaced.ve-block-right{background:rgba(22,163,74,.07);border-left-color:#16a34a}\n.ve-block.is-hovered{box-shadow:0 0 0 2px var(--color-teal-600)}\n.ve-block.ve-block-anchor{display:block;height:0;min-height:0;padding:0;margin:0;border:none;overflow:hidden;pointer-events:none}\ndel.ve-word-deleted{background:rgba(220,38,38,.28);color:#991b1b;border-radius:3px;padding:0 2px;text-decoration:line-through;font-weight:600}\nins.ve-word-added{background:rgba(22,163,74,.28);color:#14532d;border-radius:3px;padding:0 2px;font-weight:600;text-decoration:none}\nhtml[data-theme=dark] del.ve-word-deleted{background:rgba(239,68,68,.38);color:#fca5a5}\nhtml[data-theme=dark] ins.ve-word-added{background:rgba(34,197,94,.38);color:#86efac}\n.ve-block-tombstone{padding:1.4rem 1rem;border:2px dashed #f87171;background:rgba(239,68,68,.05);border-radius:10px;text-align:center;margin:.8rem 0;font-family:inherit;white-space:normal}\n.ve-block-tombstone h4{margin:0 0 .4rem;color:#b91c1c;text-transform:none;letter-spacing:0;font-size:1rem}\n.ve-tombstone-icon{font-size:2rem}\n.ve-unified-container{border:1px solid var(--border-default);border-radius:10px;overflow:hidden;overscroll-behavior:contain;overflow-anchor:none;background:var(--bg-canvas);font-family:var(--font-mono);font-size:.84rem}\n.ve-diff-line{display:flex;gap:.6rem;padding:.2rem .7rem;border-bottom:1px solid var(--border-subtle,var(--border-default));line-height:1.5}\n.ve-diff-added{background:rgba(22,163,74,.12)}\n.ve-diff-deleted{background:rgba(220,38,38,.12)}\n.ve-diff-unchanged{color:var(--color-ink-muted)}\n.ve-diff-marker{font-weight:700;user-select:none;width:1rem;flex-shrink:0}\n.ve-diff-text{flex:1;white-space:pre-wrap;word-break:break-word;min-width:0}\n.td-series{display:flex;flex-direction:column;gap:.6rem;min-width:0}\n.td-meta{font-size:.76rem;color:var(--color-ink-muted);margin:0;overflow-wrap:anywhere}\n.td-grid{display:grid;grid-template-columns:minmax(0,1fr);gap:.7rem;align-items:start}\n.td-chip{font-family:inherit;line-height:inherit;margin:0;white-space:normal;text-align:start;cursor:help;border:1px solid transparent;text-decoration:underline dotted;text-underline-offset:2px}\nbutton.td-chip:focus-visible,button.td-chip.is-open{outline:2px solid var(--color-teal-600);outline-offset:1px}\n.td-tip{position:fixed;z-index:1000;max-width:min(30rem,calc(100vw - 16px));overflow:auto;overscroll-behavior:contain;box-sizing:border-box;padding:.55rem .75rem;border:1px solid var(--border-default);border-inline-start:4px solid #d97706;border-radius:8px;background:var(--bg-surface);color:var(--color-ink);box-shadow:0 6px 20px rgba(0,0,0,.22);font-size:.8rem;line-height:1.45;font-weight:400;text-align:start;overflow-wrap:anywhere}\n.td-tip[hidden]{display:none}\n.td-tip-head{display:flex;flex-wrap:wrap;gap:.35rem;align-items:baseline;margin-bottom:.3rem;color:var(--color-ink)}\n.td-tip-head code{font-size:.74rem;background:transparent;padding:0;border:0}\n.td-tip-model{font-size:.72rem;color:var(--color-ink-muted)}\n.td-tip ul,.td-tip ol,.td-dl ul,.td-dl ol ol{margin:.25rem 0;padding-inline-start:1.1rem}\n.td-tip p,.td-dl p{margin:.25rem 0}\nhtml[data-theme=dark] .td-tip{box-shadow:0 6px 20px rgba(0,0,0,.6)}\n.td-dl{border:1px solid var(--border-default);border-radius:10px;background:var(--bg-canvas);padding:.6rem .8rem;font-size:.84rem;line-height:1.5;overflow-wrap:anywhere}\n.td-dl-list{list-style:none;margin:.3rem 0;padding:0}\n.td-dl-row{border-top:1px dashed var(--border-default);padding:.45rem 0}\n.td-dl-row:first-child{border-top:none}\n.td-dl-head{display:flex;flex-wrap:wrap;gap:.45rem;align-items:center}\n.td-dl-span{font-weight:700;font-family:var(--font-mono);font-size:.8rem;color:var(--color-ink)}\n.td-dl-count,.td-dl-model{font-size:.76rem;color:var(--color-ink-muted)}\n.td-dl-body,.td-dl-each{margin-top:.25rem}\n.td-dl-each summary{cursor:pointer;font-size:.78rem;color:var(--color-ink-muted)}\n.td-dl-each li code{font-size:.76rem}\n.ve-block.td-md-block{white-space:normal;font-family:inherit;line-height:1.5}\n.ve-block.td-md-block p,.ve-block.td-md-block ul,.ve-block.td-md-block ol,.ve-block.td-md-block pre,.td-int-doc p,.td-int-doc ul,.td-int-doc ol,.td-int-doc pre{margin:.2rem 0}\n.ve-block.td-md-block ul,.ve-block.td-md-block ol,.td-int-doc ul,.td-int-doc ol{padding-inline-start:1.2rem}\n.ve-block.td-md-block h4,.ve-block.td-md-block h5,.td-int-doc h4,.td-int-doc h5{text-transform:none;letter-spacing:normal;font-size:.9rem;margin:.3rem 0}\n.ve-block.td-md-block pre,.td-int-doc pre{white-space:pre-wrap;font-family:var(--font-mono)}\n.ve-block.td-md-block table,.td-int-doc table{border-collapse:collapse;font-size:.8rem}\n.ve-block.td-md-block td,.ve-block.td-md-block th,.td-int-doc td,.td-int-doc th{border:1px solid var(--border-default);padding:.15rem .35rem;vertical-align:top}\n.td-ind-1{margin-inline-start:1.2rem}.td-ind-2{margin-inline-start:2.4rem}.td-ind-3{margin-inline-start:3.6rem}\n.td-int-bar{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;font-size:.8rem;margin-bottom:.2rem}\n.td-int-label{font-weight:700;color:var(--color-ink-muted)}\n.td-int-target{color:var(--color-ink-muted)}\n.td-int{border:1px solid var(--border-default);border-top:3px solid #16a34a;border-radius:10px;background:var(--bg-canvas);padding:.6rem .8rem;font-size:.86rem;line-height:1.6;overflow-wrap:anywhere;max-height:560px;overflow:auto;overscroll-behavior:contain;overflow-anchor:none}\n.td-int-line{margin:.15rem 0}\nli.td-int-gone{list-style:none}\nins.td-int-add{background:rgba(22,163,74,.2);color:inherit;text-decoration:none;border-radius:3px;padding:0 1px;box-shadow:inset 0 -2px 0 #16a34a}\nhtml[data-theme=dark] ins.td-int-add{background:rgba(34,197,94,.28);box-shadow:inset 0 -2px 0 #4ade80}\nins.td-int-rep{background:rgba(217,119,6,.2);box-shadow:inset 0 -2px 0 #d97706;cursor:help}\nhtml[data-theme=dark] ins.td-int-rep{background:rgba(245,158,11,.28);box-shadow:inset 0 -2px 0 #fbbf24}\ndel.td-int-del,.td-tip del.td-int-old{background:rgba(220,38,38,.14);color:#991b1b;text-decoration:line-through;border-radius:3px;padding:0 1px}\nhtml[data-theme=dark] del.td-int-del,html[data-theme=dark] .td-tip del.td-int-old{background:rgba(239,68,68,.28);color:#fecaca}\n.td-tip ins.td-int-new{background:rgba(22,163,74,.2);color:inherit;text-decoration:none;border-radius:3px;padding:0 1px}\nhtml[data-theme=dark] .td-tip ins.td-int-new{background:rgba(34,197,94,.28)}\n.td-int-arrow{color:var(--color-ink-muted);font-weight:700}\n[dir=rtl] .td-int-arrow{display:inline-block;transform:scaleX(-1)}\n.td-int-mark{display:inline-block;width:12px;height:1.15em;vertical-align:-.2em;margin:0 1px;padding:0;border:0;border-radius:3px;background:linear-gradient(#dc2626,#dc2626) center/4px 100% no-repeat;cursor:help}\nhtml[data-theme=dark] .td-int-mark{background:linear-gradient(#f87171,#f87171) center/4px 100% no-repeat}\n.td-int-mark:focus-visible,.td-int-mark.is-open,ins.td-int-rep:focus-visible,ins.td-int-rep.is-open{outline:2px solid var(--color-teal-600);outline-offset:1px}\n.td-note,.td-none{font-size:.78rem;color:var(--color-ink-muted);margin:.2rem 0}\n.td-full{border:1px solid var(--border-default);border-radius:10px;background:var(--bg-canvas);padding:.6rem .8rem;font-size:.84rem;line-height:1.5;overflow-wrap:anywhere;max-height:520px;overflow:auto;overscroll-behavior:contain;overflow-anchor:none}\n.td-full-head{font-weight:700;font-size:.8rem;margin-bottom:.4rem;color:var(--color-ink-muted)}\n.ve-timeline-wrap{border:1px solid var(--border-default);border-radius:10px;background:var(--bg-surface);padding:.8rem 1rem}\n.ve-timeline-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:.7rem;flex-wrap:wrap;gap:.5rem}\n.ve-timeline-title{font-size:.8rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--color-ink-muted)}\n.ve-timeline-hint{font-size:.78rem;color:var(--color-teal-600)}\n.ve-timeline-epochs{display:flex;flex-wrap:wrap;gap:.5rem}\n.ve-epoch-card{flex:1 1 calc(25% - .5rem);min-width:125px;max-width:260px;border:1.5px solid var(--border-default);border-radius:8px;background:var(--bg-canvas);padding:.5rem .65rem;display:flex;flex-direction:column;gap:.35rem;cursor:pointer;transition:border-color .15s}\n.ve-epoch-card:hover,.ve-epoch-card:focus-visible{border-color:var(--color-teal-600);outline:none}\n.ve-epoch-card.is-left{border-color:#2563eb;background:rgba(37,99,235,.05);box-shadow:0 0 0 1px #2563eb}\n.ve-epoch-card.is-right{border-color:#16a34a;background:rgba(22,163,74,.05);box-shadow:0 0 0 1px #16a34a}\n.ve-epoch-card.is-left.is-right{border-color:#9333ea;background:rgba(147,51,234,.05);box-shadow:0 0 0 1px #9333ea}\n.ve-epoch-card.ve-epoch-dropped{border-style:dashed;border-color:#f87171;background:rgba(239,68,68,.04)}\n.ve-epoch-card.ve-epoch-absent{border-style:dashed;cursor:default;background:var(--bg-subtle)}\n.ve-epoch-header{display:flex;justify-content:space-between;align-items:center;gap:.4rem;flex-wrap:wrap}\n.ve-epoch-span{font-weight:700;font-size:.84rem;color:var(--color-ink)}\n.ve-epoch-status{font-size:.68rem;padding:.1rem .35rem;border-radius:4px;font-weight:600;white-space:nowrap}\n.ve-status-initial{background:#e0f2fe;color:#0369a1}\n.ve-status-stable{background:#f1f5f9;color:#475569}\n.ve-status-changed{background:#fef3c7;color:#b45309;border:1px solid #fde68a}\n.ve-status-revert{background:#fce7f3;color:#be185d}\n.ve-status-dropped{background:rgba(239,68,68,.15);color:#b91c1c;border:1px solid #fca5a5}\n.ve-status-absent{background:rgba(100,116,139,.15);color:#475569;border:1px solid #cbd5e1}\n.ve-status-presence{background:#ecfeff;color:#0e7490;border:1px solid #a5f3fc}\n.ve-status-unchecked{background:#fefce8;color:#854d0e;border:1px solid #fde68a}\n.ve-epoch-card.ve-epoch-presence{border-style:dotted;border-color:#67e8f9;background:rgba(6,182,212,.05)}\nhtml[data-theme=dark] .ve-status-presence{background:#083344;color:#a5f3fc}\nhtml[data-theme=dark] .ve-status-unchecked{background:#422006;color:#fde68a}\nhtml[data-theme=dark] .ve-status-dropped{color:#fca5a5}\nhtml[data-theme=dark] .ve-status-absent{color:#cbd5e1}\n.ve-epoch-body{font-size:.74rem;color:var(--color-ink-muted);line-height:1.3}\n.ve-epoch-variants{margin-top:.2rem;font-style:italic}.ve-epoch-cleaned{margin-top:.2rem;font-size:.85em;color:var(--muted,#6b7280);cursor:help}\n.ve-epoch-subreleases{display:flex;gap:.3rem;flex-wrap:wrap;margin-top:.35rem}\n.ve-epoch-rel-pill{font-size:.7rem;padding:.05rem .35rem;border-radius:4px;background:var(--bg-subtle);border:1px solid var(--border-default);font-family:var(--font-mono)}\n.ve-epoch-actions{display:flex;gap:.3rem;margin-top:auto;padding-top:.3rem;border-top:1px solid var(--border-default)}\n.ve-epoch-btn{flex:1;padding:.2rem .3rem;font-size:.7rem;border-radius:4px;border:1px solid var(--border-default);background:var(--bg-surface);color:var(--color-ink);cursor:pointer;font-weight:600}\n.ve-btn-set-left:hover{border-color:#2563eb;color:#2563eb}\n.ve-btn-set-right:hover{border-color:#16a34a;color:#16a34a}\n.ve-diff-toolbar{display:flex;justify-content:space-between;align-items:center;gap:.6rem;flex-wrap:wrap}\n.ve-compare-summary{display:flex;align-items:center;gap:.5rem;font-size:.88rem;flex-wrap:wrap}\n.ve-tag-left{padding:.2rem .55rem;border-radius:6px;background:#dbeafe;color:#1e40af;font-weight:700;border:1px solid #bfdbfe}\n.ve-tag-right{padding:.2rem .55rem;border-radius:6px;background:#dcfce7;color:#15803d;font-weight:700;border:1px solid #bbf7d0}\n.ve-tag-arrow{color:var(--color-ink-muted);font-weight:700}\n.ve-btn-swap{padding:.2rem .5rem;border-radius:6px;border:1px solid var(--border-default);background:var(--bg-subtle);color:var(--color-ink);cursor:pointer;font-size:.78rem}\n.ve-view-toggle{display:inline-flex;border:1px solid var(--border-default);border-radius:8px;overflow:hidden;background:var(--bg-subtle);flex-wrap:wrap}\n.ve-view-btn{padding:.35rem .7rem;border:none;background:transparent;color:var(--color-ink-muted);font-size:.8rem;font-weight:600;cursor:pointer}\n.ve-view-btn.is-active{background:var(--color-teal-600);color:#fff}\n.ve-raw{border:1px solid var(--border-default);border-radius:8px;padding:.9rem;background:var(--bg-canvas);font-family:var(--font-mono);font-size:.84rem;line-height:1.55}\n.ve-raw-head{font-weight:700;margin-bottom:.6rem;color:var(--color-ink-muted);overflow-wrap:anywhere}\n.ve-raw pre{white-space:pre-wrap;font-family:inherit;margin:0;overflow-wrap:anywhere}\n.td-rev{display:flex;flex-direction:column;gap:.8rem;min-width:0}\n.ve-epoch-card.td-nopick{cursor:default}\n.ve-epoch-card .ve-series-thumb{display:block;margin:.1rem 0 .3rem}\n.ve-epoch-card .ve-series-thumb .ve-thumb{width:100%;height:72px;border:1px solid var(--border-default);border-radius:4px}\n.td-ep-badge{font-weight:700;color:#7c3aed;font-size:.72rem;margin:.15rem 0}\nhtml[data-theme=dark] .td-ep-badge{color:#c4b5fd}\n.td-ep-none{font-style:italic}\n.ve-epoch-status{max-width:100%;overflow-wrap:anywhere}\n.td-ep-model{font-size:.7rem;overflow-wrap:anywhere}\n.td-ep-link{display:inline-block;margin-top:.3rem;font-size:.72rem}\n.td-status-editorial{background:#dbeafe;color:#1e40af;border:1px solid #bfdbfe}\nhtml[data-theme=dark] .td-status-editorial{background:#172554;color:#bfdbfe}\n.td-raw-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:.6rem}\n.td-raw-grid .ve-raw{min-width:0;max-height:560px;overflow:auto;overscroll-behavior:contain;overflow-anchor:none}\n.td-raw-left{border-top:3px solid #2563eb}.td-raw-right{border-top:3px solid #16a34a}\n.ve-raw.td-md{font-family:inherit;font-size:.84rem;line-height:1.5;overflow-wrap:anywhere}\n.ve-raw.td-md h4,.ve-raw.td-md h5{text-transform:none;letter-spacing:normal;font-size:.86rem;margin:.6rem 0 .25rem}\n.ve-raw.td-md pre{white-space:pre-wrap}\n.td-rev .ve-placeholder{padding:1rem;text-align:start;color:var(--color-ink-muted);font-size:.88rem}\n.td-rev .ve-error{padding:.6rem .8rem;border:1px solid #fca5a5;border-radius:8px;color:#b91c1c}\n.ve-split-diff-wrapper:focus-visible{outline:2px solid var(--color-teal-600);outline-offset:2px}\n@media (max-width:899px){\n  .ve-split-columns{grid-template-columns:minmax(0,1fr) 22px minmax(0,1fr)}\n  .ve-split-body{padding:.5rem;font-size:.78rem}\n  .ve-epoch-card{flex-basis:calc(50% - .5rem);max-width:none}\n  .td-raw-grid{grid-template-columns:minmax(0,1fr)}\n  .ve-epoch-status{white-space:normal}\n}";
  function ensureStyles(doc) {
    doc = doc || (typeof document !== "undefined" ? document : null);
    if (!doc || doc.getElementById("td-styles")) return;
    var st = doc.createElement("style");
    st.id = "td-styles";
    st.textContent = CSS;
    (doc.head || doc.documentElement).appendChild(st);
  }

  /**
   * Nebeneinander mit Verbindern und abschnittsweise synchronem Scrollen.
   * d = {blocks, left: {label, tag}, right: {label, tag}, tombstoneHtml?}; Rückgabe {redraw()}.
   */
  function renderSide(container, d, o) {
    o = o || {};
    ensureStyles(container.ownerDocument);
    var blocks = d.blocks || [];
    if (!blocks.length) {
      container.innerHTML = '<div class="ve-placeholder ve-placeholder-small">' + esc(o.emptyText || "–") + "</div>";
      return { redraw: function () {} };
    }
    var L = "", R = "";
    if (d.tombstoneHtml) {
      blocks.forEach(function (b) {
        var tx = b.left_html || esc(b.left_lines.join("\n"));
        if (tx.trim()) L += '<div class="ve-block ve-block-deleted" data-block-id="' + b.id + '" data-tag="delete">' + tx + "</div>";
      });
      R = d.tombstoneHtml;
    } else {
      blocks.forEach(function (b) {
        var lh = b.left_html || esc(b.left_lines.join("\n")), rh = b.right_html || esc(b.right_lines.join("\n"));
        var md = b.rich ? " td-md-block" : "";
        if (b.tag === "delete") { L += '<div class="ve-block ve-block-deleted' + md + '" data-block-id="' + b.id + '" data-tag="delete">' + lh + "</div>"; R += '<div class="ve-block ve-block-anchor" data-block-id="' + b.id + '" data-tag="delete"></div>'; }
        else if (b.tag === "replace") { L += '<div class="ve-block ve-block-replaced ve-block-left' + md + '" data-block-id="' + b.id + '" data-tag="replace">' + lh + "</div>"; R += '<div class="ve-block ve-block-replaced ve-block-right' + md + '" data-block-id="' + b.id + '" data-tag="replace">' + rh + "</div>"; }
        else if (b.tag === "equal") { L += '<div class="ve-block ve-block-equal' + md + '" data-block-id="' + b.id + '" data-tag="equal">' + lh + "</div>"; R += '<div class="ve-block ve-block-equal' + md + '" data-block-id="' + b.id + '" data-tag="equal">' + lh + "</div>"; }
        else { L += '<div class="ve-block ve-block-anchor" data-block-id="' + b.id + '" data-tag="insert"></div>'; R += '<div class="ve-block ve-block-added' + md + '" data-block-id="' + b.id + '" data-tag="insert">' + rh + "</div>"; }
      });
    }
    var lf = d.left || {}, rt = d.right || {};
    container.innerHTML = '<div class="ve-split-diff-wrapper"><div class="ve-split-columns">' +
      '<div class="ve-split-pane ve-split-left"><div class="ve-split-header ve-header-left"><span>' + (lf.label || "") +
      "</span>" + (lf.tag ? "<code>" + esc(lf.tag) + "</code>" : "") + '</div><div class="ve-split-body ve-pane-left">' + L + "</div></div>" +
      '<div class="ve-split-gutter"><div class="ve-split-header ve-header-gutter"><span>Diff</span></div>' +
      '<div class="ve-gutter-canvas-wrap"><svg class="ve-gutter-svg" width="100%" height="100%" aria-hidden="true"></svg></div></div>' +
      '<div class="ve-split-pane ve-split-right"><div class="ve-split-header ve-header-right"><span>' + (rt.label || "") +
      "</span>" + (rt.tag ? "<code>" + esc(rt.tag) + "</code>" : "") + '</div><div class="ve-split-body ve-pane-right">' + R + "</div></div>" +
      "</div></div>";
    var wrapper = container.querySelector(".ve-split-diff-wrapper");
    var svg = wrapper.querySelector(".ve-gutter-svg"), gutter = wrapper.querySelector(".ve-split-gutter");
    function redrawSvgConnectors() {
      var canvasWrap = gutter.querySelector(".ve-gutter-canvas-wrap") || gutter;
      var gH = canvasWrap.offsetHeight || gutter.offsetHeight;
      if (gH > 0) { svg.setAttribute("height", gH); svg.style.height = gH + "px"; }
      var svgRect = svg.getBoundingClientRect();
      var W = Math.round(svgRect.width) || 70, cp1x = W * 0.45, cp2x = W * 0.55, paths = "";
      blocks.forEach(function (b) {
        if (b.tag === "equal") return;
        var le = wrapper.querySelector('.ve-pane-left [data-block-id="' + b.id + '"]');
        var re = wrapper.querySelector('.ve-pane-right [data-block-id="' + b.id + '"]');
        if (!le || !re) return;
        var lr = le.getBoundingClientRect(), rr = re.getBoundingClientRect();
        var y1T = lr.top - svgRect.top, y1B = b.tag === "insert" ? y1T : lr.bottom - svgRect.top;
        var y2T = rr.top - svgRect.top, y2B = b.tag === "delete" ? y2T : rr.bottom - svgRect.top;
        var path;
        if (b.tag === "replace") path = "M 0 " + y1T + " C " + cp1x + " " + y1T + ", " + cp2x + " " + y2T + ", " + W + " " + y2T + " L " + W + " " + y2B + " C " + cp2x + " " + y2B + ", " + cp1x + " " + y1B + ", 0 " + y1B + " Z";
        else if (b.tag === "delete") path = "M 0 " + y1T + " C " + cp1x + " " + y1T + ", " + cp2x + " " + y2T + ", " + W + " " + y2T + " L " + W + " " + y2T + " C " + cp2x + " " + y2T + ", " + cp1x + " " + y1B + ", 0 " + y1B + " Z";
        else path = "M 0 " + y1T + " C " + cp1x + " " + y1T + ", " + cp2x + " " + y2T + ", " + W + " " + y2T + " L " + W + " " + y2B + " C " + cp2x + " " + y2B + ", " + cp1x + " " + y1T + ", 0 " + y1T + " Z";
        paths += '<path d="' + path + '" class="ve-connector ve-connector-' + b.tag + '" data-connector-id="' + b.id + '"></path>';
      });
      svg.innerHTML = paths;
    }
    svg.addEventListener("mouseover", function (e) {
      var p = e.target.closest ? e.target.closest(".ve-connector") : null;
      if (p === svg._hot) return;
      if (svg._hot) hover(svg._hot.getAttribute("data-connector-id"), false);
      svg._hot = p;
      if (p) hover(p.getAttribute("data-connector-id"), true);
    });
    svg.addEventListener("mouseout", function (e) {
      if (!svg._hot) return;
      var rel = e.relatedTarget;
      if (rel && svg.contains(rel) && rel.closest && rel.closest(".ve-connector") === svg._hot) return;
      hover(svg._hot.getAttribute("data-connector-id"), false);
      svg._hot = null;
    });
    svg.addEventListener("click", function (e) {
      var p = e.target.closest ? e.target.closest(".ve-connector") : null;
      if (!p || !wrapper._syncController) return;
      wrapper._syncController.scrollToBlock(p.getAttribute("data-connector-id"));
    });
    function hover(id, on) {
      wrapper.querySelectorAll('[data-block-id="' + id + '"]').forEach(function (x) { x.classList.toggle("is-hovered", on); });
      var p = svg.querySelector('path[data-connector-id="' + id + '"]');
      if (p) p.classList.toggle("is-hovered", on);
    }
    wrapper.querySelectorAll(".ve-block").forEach(function (el) {
      var id = el.getAttribute("data-block-id");
      el.addEventListener("mouseenter", function () { hover(id, true); });
      el.addEventListener("mouseleave", function () { hover(id, false); });
    });
    initPiecewiseSyncScroll(wrapper, wrapper.querySelector(".ve-pane-left"), wrapper.querySelector(".ve-pane-right"), blocks, redrawSvgConnectors);
    var firstChange = null;
    blocks.some(function (b) { if (b.tag !== "equal") { firstChange = b.id; return true; } return false; });
    return {
      redraw: redrawSvgConnectors,
      // zur ersten Änderung blättern (nach dem Ausmessen der Abschnitte durch die Scroll-Synchronisation)
      scrollToFirstChange: function () {
        if (!firstChange) return;
        setTimeout(function () {
          var c = wrapper._syncController;
          // Nutzer hat den Vergleich schon bewegt: nicht zurück zur ersten Änderung springen.
          if (!c || c.userMoved) return;
          c.measure();
          c.scrollToBlock(firstChange);
        }, 60);
      }
    };
  }

  // Virtuelle Scrollposition. Eine Margin-Lücke zwischen zwei Blöcken bleibt am Ende des
  // vorigen Blocks; früher lieferte sie 0 und der Vergleich sprang an den Anfang zurück.
  function progressFromScroll(layouts, scrollTop, side) {
    if (!layouts || !layouts.length) return 0;
    var topK = side === "R" ? "topR" : "topL";
    var botK = side === "R" ? "botR" : "botL";
    var hK = side === "R" ? "hR" : "hL";
    var last = layouts.length - 1;
    var y = scrollTop || 0;
    for (var i = 0; i < layouts.length; i++) {
      var blk = layouts[i];
      var top = blk[topK], bot = blk[botK], h = blk[hK];
      var nextTop = i < last ? layouts[i + 1][topK] : Infinity;
      if (y < top) return i === 0 ? 0 : layouts[i - 1].endV;
      if (y < bot || i === last) {
        var t = h > 0 ? (y - top) / h : 0;
        if (t < 0) t = 0;
        if (t > 1) t = 1;
        return blk.startV + t * blk.hV;
      }
      if (y < nextTop) return blk.endV;
    }
    return layouts[last].endV;
  }

  function wheelPixels(e, el) {
    var dy = e.deltaY || 0;
    if (e.deltaMode === 1) dy *= 16;
    else if (e.deltaMode === 2) dy *= (el && el.clientHeight) || 400;
    return dy;
  }

  // Volltext-Spalten: Fokus ohne Seitensprung, Rad bleibt im Kasten (auch am Rand).
  function isolateScroll(el) {
    if (!el || el.getAttribute("data-td-iso") === "1") return;
    el.setAttribute("data-td-iso", "1");
    if (!el.hasAttribute("tabindex")) el.tabIndex = -1;
    el.addEventListener("mousedown", function (e) {
      if (e.target.closest && e.target.closest("a,button,input,select,textarea,label")) return;
      el.focus({ preventScroll: true });
    });
    el.addEventListener("wheel", function (e) {
      if (!e.deltaY) return;
      var max = el.scrollHeight - el.clientHeight;
      if (max <= 1) return;
      e.preventDefault();
      e.stopPropagation();
      var next = el.scrollTop + wheelPixels(e, el);
      if (next < 0) next = 0;
      if (next > max) next = max;
      el.scrollTop = next;
    }, { passive: false });
  }

  // Abschnittsweise synchrones Scrollen (aus dem Versions-Explorer übernommen)
  function initPiecewiseSyncScroll(wrapper, paneLeft, paneRight, blocks, redrawFn) {
    if (!wrapper || !paneLeft || !paneRight || !blocks || blocks.length === 0) return;

    let blockLayouts = [];
    let cumV = [0];
    let V_total = 0;
    let globalS = 0;
    let lock = 0;
    let userMoved = false;

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

    function setTop(el, value) {
      var next = Math.max(0, value);
      if (Math.abs(el.scrollTop - next) < 0.5) return;
      el.scrollTop = next;
    }

    function applyScroll(S) {
      const maxScrollL = Math.max(0, paneLeft.scrollHeight - paneLeft.clientHeight);
      const maxScrollR = Math.max(0, paneRight.scrollHeight - paneRight.clientHeight);
      const viewH = Math.min(paneLeft.clientHeight || 500, paneRight.clientHeight || 500);
      const maxS = Math.max(0, V_total - viewH);

      globalS = Math.max(0, Math.min(maxS, S));
      const targets = getTargetsForS(globalS);

      lock++;
      try {
        setTop(paneLeft, Math.min(maxScrollL, Math.max(0, targets.targetL)));
        setTop(paneRight, Math.min(maxScrollR, Math.max(0, targets.targetR)));
        if (redrawFn) redrawFn();
      } finally {
        var token = lock;
        requestAnimationFrame(function () {
          requestAnimationFrame(function () {
            if (lock === token) lock = 0;
          });
        });
      }
    }

    function onUserScroll(side) {
      if (lock) return;
      if (!blockLayouts.length) measureLayout();
      if (!blockLayouts.length) return;
      userMoved = true;
      applyScroll(progressFromScroll(blockLayouts, side === "R" ? paneRight.scrollTop : paneLeft.scrollTop, side));
    }

    wrapper.tabIndex = -1;
    wrapper.addEventListener("mousedown", function (e) {
      if (e.target.closest && e.target.closest("a,button,input,select,textarea,label")) return;
      if (document.activeElement !== wrapper) wrapper.focus({ preventScroll: true });
    });
    // Rad über Text, Mittelspalte oder Kopf bleibt im Vergleich und scrollt nicht die Seite.
    wrapper.addEventListener("wheel", function (e) {
      if (!e.deltaY) return;
      e.preventDefault();
      e.stopPropagation();
      userMoved = true;
      if (!blockLayouts.length) measureLayout();
      applyScroll(globalS + wheelPixels(e, paneLeft));
    }, { passive: false, capture: true });
    wrapper.addEventListener("keydown", function (e) {
      if (e.target !== wrapper) return;
      var step = paneLeft.clientHeight || 240;
      var dy = null;
      if (e.key === "ArrowDown") dy = 48;
      else if (e.key === "ArrowUp") dy = -48;
      else if (e.key === "PageDown" || (e.key === " " && !e.shiftKey)) dy = step;
      else if (e.key === "PageUp" || (e.key === " " && e.shiftKey)) dy = -step;
      else if (e.key === "Home") dy = -1e15;
      else if (e.key === "End") dy = 1e15;
      else return;
      e.preventDefault();
      userMoved = true;
      applyScroll(globalS + dy);
    });

    paneLeft.addEventListener("scroll", function () { onUserScroll("L"); }, { passive: true });
    paneRight.addEventListener("scroll", function () { onUserScroll("R"); }, { passive: true });

    var ctrl = wrapper._syncController = {
      scrollToBlock: function (blockId) {
        var idx = -1;
        for (var i = 0; i < blockLayouts.length; i++) if (blockLayouts[i].id === blockId) { idx = i; break; }
        if (idx >= 0) applyScroll(blockLayouts[idx].startV);
      },
      applyScroll: applyScroll,
      measure: measureLayout,
      get userMoved() { return userMoved; }
    };

    setTimeout(function () {
      measureLayout();
      if (!ctrl.userMoved) applyScroll(globalS || 0);
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



  function renderUnified(container, lines, o) {
    o = o || {};
    ensureStyles(container.ownerDocument);
    var changed = (lines || []).some(function (l) { return l.type !== "unchanged"; });
    if (!lines || !lines.length || !changed) {
      container.innerHTML = '<div class="ve-placeholder ve-placeholder-small">' + esc(o.identicalText || "=") + "</div>";
      return;
    }
    container.innerHTML = '<div class="ve-unified-container">' + lines.map(function (l) {
      var m = l.type === "added" ? "+" : (l.type === "deleted" ? "−" : " ");
      return '<div class="ve-diff-line ve-diff-' + l.type + '"><span class="ve-diff-marker">' + m + '</span><span class="ve-diff-text">' + esc(l.text) + "</span></div>";
    }).join("") + "</div>";
  }

  // ------------------------------------------------------------------ Revisions-Zeitachse

  var LABELS_DE = {
    tl_title: "Revisions-Zeitachse", tl_hint: "Die beiden zuletzt angeklickten Fassungen werden verglichen (ältere links).",
    cmp: "Vergleich:", left: "◀ Links", right: "Rechts ▶", right_drop: "Rechts ▶ (Wegfall)",
    swap: "⇄ Tauschen", swap_title: "Seiten tauschen", base_side: "Basis:", target_side: "Ziel:",
    mode_side: "Nebeneinander (wortgenau)", mode_unified: "Unified Diff", mode_raw: "Volltext",
    mode_integrated: "Integrierter Diff", int_style: "Darstellung", int_style_a: "Marker", int_style_b: "Durchgestrichen",
    int_legend_a: "Neue Fassung mit eingearbeiteten Änderungen: Neues ist hervorgehoben, ▍ markiert entfernten Text, Ersetztes zeigt den alten Wortlaut als Tooltip.",
    int_legend_b: "Neue Fassung mit eingearbeiteten Änderungen: Neues ist hervorgehoben, Entferntes durchgestrichen, Ersetzungen erscheinen als alt → neu.",
    int_removed: "entfernt", int_replaced: "ersetzt (alt → neu)",
    identical: "Beide Fassungen sind identisch.", no_data: "Keine Daten vorhanden.", loading: "Lade …",
    stats: "{a} ergänzt · {d} entfernt · {u} gleich", err: "Vergleich fehlgeschlagen: {msg}",
    same: "Beide Seiten zeigen dieselbe Fassung.", single: "Nur eine vergleichbare Fassung vorhanden.",
    // Fassungen einer Bildreihe
    base: "Ausgangsfassung", new_version: "neue Fassung", current: "beschriebene Fassung",
    delta: "Delta laut KI", delta_none: "Für diesen Übergang liegt kein gespeichertes KI-Delta vor.",
    delta_note: "Gespeicherte KI-Aussagen zu den Übergängen – zum Abgleich mit dem berechneten Wortvergleich.",
    mode_deltas: "KI-Deltas", deltas_run: "{n} Übergänge", deltas_each: "Einzelne Übergänge",
    deltas_intro: "Alle Übergänge der Bildreihe in Release-Reihenfolge; aufeinanderfolgende Übergänge ohne inhaltliche Änderung sind zusammengefasst.",
    deltas_empty: "Für diese Bildreihe liegen keine Übergänge vor.",
    nodesc: "keine KI-Beschreibung", nodiff: "Fassung {rel} hat keine KI-Beschreibung – kein Wortvergleich möglich.",
    open_page: "Seite öffnen", summary: "Kurzfassung", raw_head: "Volltext {rel}", model: "Modell: {m}",
    change: { normativ: "normative Änderung", redaktionell: "redaktionell", keine: "keine inhaltliche Änderung",
              offen: "noch nicht analysiert" }
  };
  var CHANGE_CLS = { normativ: "ve-status-changed", redaktionell: "td-status-editorial", keine: "ve-status-stable",
                     offen: "ve-status-unchecked" };

  function fmt(s, vars) {
    s = String(s == null ? "" : s);
    Object.keys(vars || {}).forEach(function (k) { s = s.split("{" + k + "}").join(vars[k]); });
    return s;
  }

  function labelsOf(extra) {
    var L = {};
    Object.keys(LABELS_DE).forEach(function (k) { L[k] = LABELS_DE[k]; });
    Object.keys(extra || {}).forEach(function (k) { if (extra[k] != null) L[k] = extra[k]; });
    return L;
  }

  var tipSeq = 0;

  /**
   * Tooltips an den Status-Chips der Karten (z. B. KI-Delta eines Übergangs). Zeigen (Maus) und Tastaturfokus
   * öffnen ihn, Klick/Antippen hält ihn offen bzw. schließt ihn wieder, Esc oder ein Tipp daneben schließt.
   * Der Tooltip steht fest positioniert unter dem Chip (bei Platzmangel darüber), nie über dem Chip selbst;
   * man kann mit der Maus hineinfahren und darin scrollen. Immer nur einer offen.
   */
  function chipTips(root) {
    var doc = root.ownerDocument, win = doc.defaultView || {};
    var cur = null, pinned = false, timer = 0;
    function tipOf(chip) { return chip ? doc.getElementById(chip.getAttribute("data-td-tip")) : null; }
    function chipOf(node) { return node && node.closest ? node.closest("[data-td-tip]") : null; }
    function inTip(node) { return !!(node && node.closest && cur && node.closest(".td-tip") === tipOf(cur)); }
    function place() {
      var tip = tipOf(cur);
      if (!tip || tip.hidden) return;
      var r = cur.getBoundingClientRect();
      var vw = win.innerWidth || doc.documentElement.clientWidth, vh = win.innerHeight || doc.documentElement.clientHeight;
      var gap = 6, below = vh - r.bottom - gap - 8, above = r.top - gap - 8;
      var down = below >= 180 || below >= above;
      tip.style.maxHeight = Math.max(60, Math.min(vh * 0.6, down ? below : above)) + "px";
      tip.style.left = "0px"; tip.style.top = "0px";
      var w = tip.offsetWidth, h = tip.offsetHeight;
      var rtl = win.getComputedStyle && win.getComputedStyle(cur).direction === "rtl";
      var left = rtl ? r.right - w : r.left;
      tip.style.left = Math.round(Math.min(Math.max(8, left), Math.max(8, vw - w - 8))) + "px";
      tip.style.top = Math.round(down ? r.bottom + gap : r.top - gap - h) + "px";
    }
    function hide() {
      clearTimeout(timer);
      if (!cur) return;
      var tip = tipOf(cur);
      if (tip) tip.hidden = true;
      cur.classList.remove("is-open");
      cur = null; pinned = false;
    }
    function show(chip, pin) {
      clearTimeout(timer);
      if (cur !== chip) { hide(); cur = chip; }
      if (pin) pinned = true;
      var tip = tipOf(chip);
      if (!tip) return;
      tip.hidden = false;
      chip.classList.add("is-open");
      place();
    }
    function later() { clearTimeout(timer); if (!pinned) timer = setTimeout(hide, 160); }
    root.addEventListener("pointerover", function (e) {
      if (e.pointerType === "touch") return;
      var chip = chipOf(e.target);
      if (chip && root.contains(chip)) show(chip, false);
      else if (inTip(e.target)) clearTimeout(timer);
    });
    root.addEventListener("pointerout", function (e) {
      if (!cur || e.pointerType === "touch") return;
      var to = e.relatedTarget;
      if (to && (chipOf(to) === cur || inTip(to))) return;
      if (chipOf(e.target) === cur || inTip(e.target)) later();
    });
    root.addEventListener("focusin", function (e) {
      var chip = chipOf(e.target);
      if (chip && root.contains(chip) && cur !== chip) show(chip, false);
    });
    root.addEventListener("focusout", function (e) {
      if (!cur || chipOf(e.target) !== cur) return;
      var to = e.relatedTarget;
      if (to && (chipOf(to) === cur || inTip(to))) return;
      hide();
    });
    root.addEventListener("click", function (e) {
      var chip = chipOf(e.target);
      if (!chip || !root.contains(chip)) return;
      if (cur === chip && pinned) hide();
      else show(chip, true);
    });
    function onKey(e) {
      if (!root.isConnected) { off(); return; }
      if ((e.key === "Escape" || e.key === "Esc") && cur) { hide(); e.stopPropagation(); }
    }
    function onDown(e) {
      if (!root.isConnected) { off(); return; }
      if (cur && chipOf(e.target) !== cur && !inTip(e.target)) hide();
    }
    function onMove() { if (!root.isConnected) { off(); return; } if (cur) place(); }
    function off() {
      doc.removeEventListener("keydown", onKey, true);
      doc.removeEventListener("pointerdown", onDown, true);
      if (win.removeEventListener) { win.removeEventListener("scroll", onMove, true); win.removeEventListener("resize", onMove); }
    }
    doc.addEventListener("keydown", onKey, true);
    doc.addEventListener("pointerdown", onDown, true);
    if (win.addEventListener) { win.addEventListener("scroll", onMove, true); win.addEventListener("resize", onMove); }
    return { hide: hide };
  }

  /**
   * Übergänge einer Bildreihe für die Ansicht „KI-Deltas“: in gegebener (Release-)Reihenfolge, Läufe direkt
   * aufeinanderfolgender Übergänge der Klasse „keine“ zu einer Zeile zusammengefasst. Fehlende Klasse gilt als
   * „offen“ (noch nicht analysiert) und bleibt eigene Zeile, ebenso jede andere Klasse.
   * Rückgabe: [{change, from, to, fr, tr, count, items: [Übergang, …]}]
   */
  function consolidateDeltas(trans) {
    var rows = [];
    (trans || []).forEach(function (t) {
      if (!t) return;
      var ch = t.change || "offen", last = rows[rows.length - 1];
      if (ch === "keine" && last && last.change === "keine") {
        last.items.push(t); last.count++; last.to = t.to; last.tr = t.tr;
        return;
      }
      rows.push({ change: ch, from: t.from, to: t.to, fr: t.fr, tr: t.tr, count: 1, items: [t] });
    });
    return rows;
  }

  function placeholder(text) { return '<div class="ve-placeholder ve-placeholder-small">' + esc(text) + "</div>"; }

  // Reihenfolge zweier Klicks: die ältere Fassung links (wie der Element-Vergleich)
  function orderPair(a, b, order) { return order(a) <= order(b) ? [a, b] : [b, a]; }

  /**
   * Revisions-Zeitachse mit Vergleich: dieselbe Bedienung für Spezifikationselemente, Fassungen einer
   * Bildreihe (KI-Beschreibungen) und Snippets. Die beiden zuletzt angeklickten Fassungen werden
   * verglichen, die ältere links; „◀ Links“/„Rechts ▶“ setzen eine Seite gezielt.
   *
   * spec = {
   *   segments: [{key?, keys?, span, status?: {text, cls, tip?}, body?, cls?, pick?: "both"|"right"|"none"}],
   *             key = Auswahlschlüssel (fehlt: nicht wählbar), keys = alle Schlüssel des Abschnitts;
   *             status.tip = HTML eines Tooltips am Status-Chip (Zeigen, Fokus, Antippen; aria-describedby)
   *   from, to                       anfängliche Auswahl (Schlüssel)
   *   diff(from, to) -> {blocks, lines, left: {label, tag}, right: {label, tag}, tombstoneHtml?,
   *                      note?, raw?: {left: {head, html, cls?}, right: {...}}}
   *   deltas?(from, to) -> html      eigene Ansicht „KI-Deltas“ neben „Volltext“ (Liste der Übergänge)
   *   viewer?                        Schlüssel, unter dem der Stil des integrierten Diffs gespeichert wird
   *   diff(...).rich?: {left, right} sicher gerendertes HTML beider Fassungen für den integrierten Diff
   *                                  (fehlt: Zeilen der Blöcke als schlichter Text)
   *   meta?(from, to, d) -> text     Zusatz zur Zählzeile
   *   order?(key) -> Zahl            Reihenfolge (Standard: Lage in der Zeitachse)
   *   tagLabel?(key) -> text         Beschriftung der Vergleichsmarken
   *   onChange?(from, to)            nach einer Auswahl durch die Person (URL)
   *   onRender?(from, to, d)         nach jeder Darstellung (z. B. Prüfkasten)
   *   title?, hint?, wrapClass?, emptyText?, singleText? (Hinweis, wenn weniger als zwei Fassungen wählbar sind)
   * }
   * opts = {labels, mode, onMode(mode)}; Rückgabe {state, root, redraw(), set(from, to)}
   */
  function revisions(container, spec, opts) {
    opts = opts || {};
    ensureStyles(container.ownerDocument);
    var Lb = labelsOf(opts.labels);
    var segs = spec.segments || [];
    var st = { from: spec.from == null ? null : spec.from, to: spec.to == null ? null : spec.to, mode: opts.mode || "side" };
    var clicks = st.from != null && st.to != null && st.from !== st.to ? [st.from, st.to] : (st.from != null ? [st.from] : []);
    var side = null;
    function keysOf(s) { return s.keys || (s.key != null ? [s.key] : []); }
    function position(key) {
      for (var i = 0; i < segs.length; i++) {
        var k = keysOf(segs[i]).indexOf(key);
        if (k >= 0) return i * 1000 + k;
      }
      return -1;
    }
    var order = spec.order || position;
    var pickable = segs.filter(function (s) { return s.key != null && s.pick !== "none"; }).length;
    var compare = pickable >= 2;
    function tag(key) { return key == null ? "–" : String(spec.tagLabel ? spec.tagLabel(key) : key); }
    var tips = "";
    function statusHtml(s) {
      if (!s.status) return "";
      var st0 = s.status;
      if (st0.tip == null) return '<span class="ve-epoch-status ' + esc(st0.cls || "") + '">' + esc(st0.text) + "</span>";
      var id = "td-tip-" + (++tipSeq);
      tips += '<div class="td-tip" role="tooltip" id="' + id + '" hidden>' + st0.tip + "</div>";
      return '<button type="button" class="ve-epoch-status td-chip ' + esc(st0.cls || "") + '" data-td-tip="' + id +
        '" aria-describedby="' + id + '">' + esc(st0.text) + "</button>";
    }
    var cards = segs.map(function (s, i) {
      var pick = s.key == null ? "none" : (s.pick || "both");
      var attrs = ' data-epoch="' + i + '" data-keys="' + esc(keysOf(s).join(",")) + '"' +
        (pick !== "none" ? ' data-key="' + esc(s.key) + '" role="button" tabindex="0"' : "");
      var act = "";
      if (compare && pick === "both") {
        act = '<div class="ve-epoch-actions"><button type="button" class="ve-epoch-btn ve-btn-set-left" data-set-left="' + esc(s.key) + '">' +
          esc(Lb.left) + '</button><button type="button" class="ve-epoch-btn ve-btn-set-right" data-set-right="' + esc(s.key) + '">' +
          esc(Lb.right) + "</button></div>";
      } else if (compare && pick === "right") {
        act = '<div class="ve-epoch-actions"><button type="button" class="ve-epoch-btn ve-btn-set-right" data-set-right="' + esc(s.key) + '">' +
          esc(Lb.right_drop) + "</button></div>";
      }
      return '<div class="ve-epoch-card' + (s.cls ? " " + s.cls : "") + (pick === "none" ? " td-nopick" : "") + '"' + attrs +
        '><div class="ve-epoch-header"><span class="ve-epoch-span">' + esc(s.span) + "</span>" +
        statusHtml(s) +
        '</div><div class="ve-epoch-body">' + (s.body || "") + "</div>" + act + "</div>";
    }).join("");
    var modes = [["side", Lb.mode_side], ["unified", Lb.mode_unified], ["integrated", Lb.mode_integrated], ["raw", Lb.mode_raw]];
    if (spec.deltas) modes.push(["deltas", Lb.mode_deltas]);
    // Gemeinsamer Ansichtsmodus (Elemente, Bildreihen, Snippets): „KI-Deltas“ gibt es nur bei Bildreihen
    if (!modes.some(function (m) { return m[0] === st.mode; })) st.mode = "side";
    container.innerHTML = '<div class="td-rev">' +
      '<div class="ve-timeline-wrap' + (spec.wrapClass ? " " + spec.wrapClass : "") + '"><div class="ve-timeline-head"><span class="ve-timeline-title">' +
      esc(spec.title || Lb.tl_title) + '</span><span class="ve-timeline-hint">' + esc(compare ? (spec.hint || Lb.tl_hint) : (spec.singleText || Lb.single)) +
      '</span></div><div class="ve-timeline-epochs">' + cards + "</div></div>" +
      '<div class="ve-diff-toolbar"' + (compare ? "" : " hidden") + '><div class="ve-compare-summary"><span>' + esc(Lb.cmp) +
      '</span><span class="ve-tag-left" data-td="lt"></span><span class="ve-tag-arrow">➔</span><span class="ve-tag-right" data-td="rt"></span>' +
      '<button type="button" class="ve-btn-swap" data-td="swap" title="' + esc(Lb.swap_title) + '">' + esc(Lb.swap) + "</button></div>" +
      '<div class="ve-view-toggle" role="group">' + modes.map(function (m) {
        return '<button type="button" class="ve-view-btn" data-td-mode="' + m[0] + '" aria-pressed="false">' + esc(m[1]) + "</button>";
      }).join("") + '</div></div><p class="td-meta" data-td="meta" hidden></p>' +
      '<div class="td-grid"' + (compare ? "" : " hidden") + '><div class="ve-diff-output" data-td="out"></div></div>' +
      (tips ? '<div class="td-tips">' + tips + "</div>" : "") + "</div>";
    var root = container.querySelector(".td-rev");
    var out = root.querySelector('[data-td="out"]'), meta = root.querySelector('[data-td="meta"]');
    var tipsCtl = chipTips(root);
    var INT_KEY = "td-int-style:" + (spec.viewer || "default");
    var intStyle = "a";
    try { if (root.ownerDocument.defaultView.localStorage.getItem(INT_KEY) === "b") intStyle = "b"; } catch (e) { /* ohne Speicher: Stil A */ }

    function rawHtml(d) {
      var r = d.raw || {};
      return '<div class="td-raw-grid">' + [["left", r.left], ["right", r.right]].map(function (x) {
        var p = x[1] || {};
        return '<div class="ve-raw td-raw-' + x[0] + (p.cls ? " " + p.cls : "") + '"><div class="ve-raw-head">' + (p.head || "") + "</div>" +
          (p.html || '<p class="td-none">' + esc(Lb.no_data) + "</p>") + "</div>";
      }).join("") + "</div>";
    }

    function integratedView(d) {
      if (d.tombstoneHtml) return '<div class="td-int">' + d.tombstoneHtml + "</div>";
      var r = d.rich;
      if (!r) {
        var la = [], lb = [];
        (d.blocks || []).forEach(function (b) { la = la.concat(b.left_lines || []); lb = lb.concat(b.right_lines || []); });
        r = { left: plainHtml(la), right: plainHtml(lb) };
      }
      var res = integratedHtml(r.left, r.right, { style: intStyle, labels: Lb });
      var same = !res.counts.add && !res.counts.del && !res.counts.rep;
      return '<div class="td-int-bar"><span class="td-int-label">' + esc(Lb.int_style) + '</span><div class="ve-view-toggle td-int-toggle" role="group" aria-label="' +
        esc(Lb.int_style) + '">' + [["a", Lb.int_style_a], ["b", Lb.int_style_b]].map(function (x) {
          return '<button type="button" class="ve-view-btn' + (x[0] === intStyle ? " is-active" : "") + '" data-td-int="' + x[0] + '" aria-pressed="' +
            (x[0] === intStyle) + '">' + esc(x[1]) + "</button>";
        }).join("") + "</div>" + (d.right && d.right.label ? '<span class="td-int-target">' + d.right.label + "</span>" : "") + "</div>" +
        '<p class="td-note td-int-legend">' + esc(intStyle === "b" ? Lb.int_legend_b : Lb.int_legend_a) + "</p>" +
        (same ? '<p class="td-note">' + esc(st.from === st.to ? Lb.same : Lb.identical) + "</p>" : "") +
        '<div class="td-int">' + res.html + "</div>";
    }

    function renderOut(d) {
      var s = stats(d.lines);
      var line = d.note ? "" : fmt(Lb.stats, { a: s.added, d: s.deleted, u: s.unchanged });
      if (st.from === st.to) line = Lb.same + (line ? " " + line : "");
      var extra = spec.meta ? spec.meta(st.from, st.to, d) : "";
      meta.textContent = [line, extra].filter(Boolean).join(" · ");
      meta.hidden = !meta.textContent;
      if (st.mode === "raw") {
        out.innerHTML = rawHtml(d);
        out.querySelectorAll(".ve-raw").forEach(isolateScroll);
        return;
      }
      if (d.note) { out.innerHTML = placeholder(d.note); return; }
      if (st.mode === "integrated") { out.innerHTML = integratedView(d); return; }
      if (st.mode === "unified") { renderUnified(out, d.lines, { identicalText: Lb.identical }); return; }
      side = renderSide(out, { blocks: d.blocks || [], tombstoneHtml: d.tombstoneHtml, left: d.left, right: d.right }, { emptyText: Lb.no_data });
      if (side.scrollToFirstChange) side.scrollToFirstChange();
    }

    function update(byUser) {
      root.querySelectorAll(".ve-epoch-card").forEach(function (c) {
        var ks = (c.getAttribute("data-keys") || "").split(",");
        c.classList.toggle("is-left", compare && st.from != null && ks.indexOf(st.from) >= 0);
        c.classList.toggle("is-right", compare && st.to != null && ks.indexOf(st.to) >= 0);
      });
      root.querySelector('[data-td="lt"]').textContent = tag(st.from);
      root.querySelector('[data-td="rt"]').textContent = tag(st.to);
      root.querySelectorAll(".ve-view-btn").forEach(function (b) {
        var on = b.getAttribute("data-td-mode") === st.mode;
        b.classList.toggle("is-active", on);
        b.setAttribute("aria-pressed", on ? "true" : "false");
      });
      side = null;
      tipsCtl.hide();
      var d = null;
      if (st.mode === "deltas") {
        meta.hidden = true;
        out.innerHTML = spec.deltas(st.from, st.to) || "";
      } else if (st.from == null || st.to == null) {
        out.innerHTML = placeholder(spec.emptyText || Lb.no_data);
        meta.hidden = true;
      } else {
        try { d = spec.diff(st.from, st.to) || {}; renderOut(d); }
        catch (err) { d = null; out.innerHTML = '<div class="ve-error">' + esc(fmt(Lb.err, { msg: err && err.message })) + "</div>"; }
      }
      if (byUser && spec.onChange) spec.onChange(st.from, st.to);
      if (spec.onRender) spec.onRender(st.from, st.to, d);
    }

    function choose(key) {
      if (clicks.length && clicks[clicks.length - 1] === key) return;
      clicks.push(key);
      if (clicks.length > 2) clicks = clicks.slice(-2);
      if (clicks.length === 2) { var p = orderPair(clicks[0], clicks[1], order); st.from = p[0]; st.to = p[1]; }
      else if (st.from == null || order(key) >= order(st.from)) st.to = key;
      else st.from = key;
      update(true);
    }

    root.addEventListener("click", function (e) {
      var b = e.target.closest("[data-set-left],[data-set-right],[data-td=swap],[data-td-mode],[data-td-int]");
      if (b && root.contains(b)) {
        if (b.hasAttribute("data-td-int")) {
          intStyle = b.getAttribute("data-td-int") === "b" ? "b" : "a";
          try { root.ownerDocument.defaultView.localStorage.setItem(INT_KEY, intStyle); } catch (err) { /* nur für diese Ansicht */ }
          update(false);
          var again = root.querySelector('[data-td-int="' + intStyle + '"]');
          if (again) again.focus();
        } else if (b.hasAttribute("data-set-left")) { st.from = b.getAttribute("data-set-left"); clicks = [st.from, st.to]; update(true); }
        else if (b.hasAttribute("data-set-right")) { st.to = b.getAttribute("data-set-right"); clicks = [st.from, st.to]; update(true); }
        else if (b.hasAttribute("data-td-mode")) { st.mode = b.getAttribute("data-td-mode"); if (opts.onMode) opts.onMode(st.mode); update(false); }
        else { var x = st.from; st.from = st.to; st.to = x; clicks = [st.from, st.to]; update(true); }
        return;
      }
      // Bedienelemente in einer Karte (Seitenlink, Bildfreigabe) wählen keine Fassung
      if (e.target.closest("a,button,input,select,textarea,[data-fig-act]")) return;
      var c = e.target.closest(".ve-epoch-card[data-key]");
      if (c && root.contains(c) && compare) choose(c.getAttribute("data-key"));
    });
    root.addEventListener("keydown", function (e) {
      if (e.key !== "Enter" && e.key !== " ") return;
      var c = e.target;
      if (!c.classList || !c.classList.contains("ve-epoch-card") || !c.hasAttribute("data-key") || !compare) return;
      e.preventDefault();
      choose(c.getAttribute("data-key"));
    });
    update(false);
    return {
      state: st, root: root, compare: compare,
      redraw: function () { if (side) side.redraw(); },
      set: function (a, b) { st.from = a; st.to = b; clicks = [a, b]; update(false); }
    };
  }

  // ------------------------------------------------------------------ Fassungen einer Bildreihe

  // Fassungen in zeitlicher Reihenfolge: entlang der Übergänge (trans), sonst in gegebener Folge
  function chronology(S) {
    var ids = (S.versions || []).map(function (v) { return v.id; });
    var trans = S.trans || [];
    if (!trans.length) return ids;
    var seq = [trans[0].from].concat(trans.map(function (t) { return t.to; }));
    var out = [];
    seq.forEach(function (id) { if (out.indexOf(id) < 0 && ids.indexOf(id) >= 0) out.push(id); });
    ids.forEach(function (id) { if (out.indexOf(id) < 0) out.push(id); });
    return out;
  }

  // Gespeicherte Deltas zwischen zwei Fassungen: die Übergänge der Zeitachse von a nach b
  function deltasBetween(S, a, b) {
    var trans = S.trans || [];
    if (!trans.length || a === b) return [];
    var seq = [trans[0].from].concat(trans.map(function (t) { return t.to; }));
    var pa = [], pb = [], best = null;
    seq.forEach(function (x, i) { if (x === a) pa.push(i); if (x === b) pb.push(i); });
    pa.forEach(function (i) { pb.forEach(function (j) { if (!best || Math.abs(i - j) < Math.abs(best[0] - best[1])) best = [i, j]; }); });
    if (!best) return [];
    return trans.slice(Math.min(best[0], best[1]), Math.max(best[0], best[1]));
  }

  // Standardvergleich: gewählte Fassung (rechts) gegen ihre Vorgängerin; die erste gegen ihre Nachfolgerin
  function defaultPair(order, current) {
    var i = order.indexOf(current);
    if (i < 0) i = order.length - 1;
    if (i > 0) return [order[i - 1], order[i]];
    return [order[0], order[Math.min(1, order.length - 1)]];
  }

  function versionLines(S, v) {
    if (!v) return [];
    if (v.l && S.lines) return mdLines(v.l.map(function (k) { return S.lines[k]; }).join("\n"));
    if (v.md != null) return mdLines(v.md);
    if (v.html != null) return htmlLines(v.html);
    return [];
  }

  function versionMd(S, v) {
    if (!v || v.html != null) return null;
    if (v.l && S.lines) return v.l.map(function (k) { return S.lines[k]; }).join("\n");
    return v.md != null ? v.md : null;
  }

  function versionHtml(S, v, renderMd) {
    if (!v) return "";
    if (v.html != null) return v.html;
    var md = v.l && S.lines ? v.l.map(function (k) { return S.lines[k]; }).join("\n") : v.md;
    if (md == null) return "";
    return renderMd ? renderMd(md) : "<pre>" + esc(md) + "</pre>";
  }

  function spanOf(rels, fallback) {
    rels = rels || [];
    return rels.length > 1 ? rels[0] + " → " + rels[rels.length - 1] : (rels[0] || fallback || "–");
  }

  function relPills(rels) {
    return (rels || []).length ? '<div class="ve-epoch-subreleases">' + rels.map(function (r) {
      return '<span class="ve-epoch-rel-pill">' + esc(r) + "</span>";
    }).join(" ") + "</div>" : "";
  }

  /**
   * Fassungen einer Bildreihe als Revisions-Zeitachse: Vergleich der KI-Beschreibungen zweier Fassungen.
   * Das gespeicherte Delta eines Übergangs („Delta laut KI“) steht als Tooltip am Änderungsklassen-Chip der
   * Karte; die Ansicht „KI-Deltas“ listet alle Übergänge (Läufe ohne inhaltliche Änderung zusammengefasst).
   * Neben dem Wortvergleich steht kein Delta. Bilder bleiben Vorschaubilder je Fassung.
   * S = {versions: [{id, releases, md|html|l, model?, summary?}], trans: [{from, to, fr, tr, change, md|html, model?}], lines?}
   *     oder null (noch nicht geladen bzw. keine Beschreibungen; dann opts.pending bzw. opts.missingText)
   * opts = {current, labels, renderMarkdown(md), pageHref(id), members?: [{id, releases, sha?}], thumbHtml?(member),
   *         from?, to?, mode?, onMode?, onChange?(a, b), pending?, missingText?, title?, wrapClass?}
   */
  function seriesDiff(container, S, opts) {
    opts = opts || {};
    var Lb = labelsOf(opts.labels);
    var loaded = !!S;
    S = S || { versions: [], trans: [] };
    var byId = {}, memberOf = {};
    (S.versions || []).forEach(function (v) { byId[v.id] = v; });
    var order = [];
    (opts.members || []).forEach(function (m) { if (m && m.id && !memberOf[m.id]) { memberOf[m.id] = m; order.push(m.id); } });
    chronology(S).forEach(function (id) { if (!memberOf[id]) { memberOf[id] = byId[id]; order.push(id); } });
    function rels(id) { var v = memberOf[id] || byId[id] || {}; return v.releases || (byId[id] || {}).releases || []; }
    function rel(id) { return rels(id).join(", ") || id; }
    function hasText(id) { var v = byId[id]; return !!(v && (v.md != null || v.html != null || v.l)); }
    var into = {};
    (S.trans || []).forEach(function (t) { if (!into[t.to]) into[t.to] = t; });
    // Modell nur an der Karte nennen, wenn die Fassungen von verschiedenen Modellen beschrieben sind
    var models = {};
    (S.versions || []).forEach(function (v) { if (v.model) models[v.model] = 1; });
    var mixed = Object.keys(models).length > 1;
    function changeLabel(tr) { var ch = tr.change || "offen"; return (Lb.change || {})[ch] || tr.label || ch; }
    function transSpan(fr, tr, a, b) { return (fr || spanOf(rels(a), a)) + " → " + (tr || spanOf(rels(b), b)); }
    function deltaBody(tr) {
      var body = tr.html != null ? tr.html : (tr.md ? (opts.renderMarkdown ? opts.renderMarkdown(tr.md) : "<p>" + esc(tr.md) + "</p>") : "");
      return body || '<p class="td-none">' + esc(Lb.delta_none) + "</p>";
    }
    function tipHtml(tr) {
      return '<div class="td-tip-head"><strong>' + esc(Lb.delta) + "</strong> <code>" + esc(transSpan(tr.fr, tr.tr, tr.from, tr.to)) + "</code>" +
        (tr.model ? ' <span class="td-tip-model">' + esc(tr.model) + "</span>" : "") + '</div><div class="td-tip-body">' + deltaBody(tr) + "</div>";
    }
    var segments = order.map(function (id, i) {
      var m = memberOf[id] || {}, t = into[id], v = byId[id] || {};
      var status = null;
      if (i === 0) status = { text: Lb.base, cls: "ve-status-initial" };
      else if (t) status = { text: changeLabel(t), cls: CHANGE_CLS[t.change || "offen"] || "ve-status-unchecked", tip: tipHtml(t) };
      else if (loaded) status = { text: Lb.new_version, cls: "ve-status-stable" };
      var href = opts.pageHref ? opts.pageHref(id) : null;
      var body = (opts.thumbHtml && m.sha ? '<span class="ve-series-thumb">' + opts.thumbHtml(m) + "</span>" : "") +
        (id === opts.current ? '<div class="ve-ai-badge td-ep-badge">✦ ' + esc(Lb.current) + "</div>" : "") +
        (loaded && !hasText(id) ? '<div class="td-ep-none">' + esc(Lb.nodesc) + "</div>" : "") +
        (v.model && mixed ? '<div class="td-ep-model">' + esc(v.model) + "</div>" : "") +
        (v.summary ? '<div class="td-ep-model">' + esc(Lb.summary) + "</div>" : "") +
        relPills(rels(id)) +
        (href ? '<a class="td-ep-link" href="' + esc(href) + '" data-td-link="' + esc(id) + '">' + esc(opts.linkText ? opts.linkText(id) : Lb.open_page) + "</a>" : "");
      return { key: id, span: spanOf(rels(id), id), status: status, body: body };
    });
    var pair = defaultPair(order, opts.current);
    var from = order.indexOf(opts.from) >= 0 ? opts.from : pair[0];
    var to = order.indexOf(opts.to) >= 0 ? opts.to : pair[1];
    function side(id, which) {
      var v = byId[id];
      return { label: esc(which === "l" ? Lb.base_side : Lb.target_side) + " <strong>" + esc(spanOf(rels(id), id)) + "</strong>",
               tag: v && v.model && mixed ? v.model : "" };
    }
    return revisions(container, {
      segments: segments, from: from, to: to, title: opts.title, wrapClass: opts.wrapClass,
      tagLabel: function (id) { return spanOf(rels(id), id); }, viewer: opts.viewer || "fig",
      emptyText: loaded ? Lb.no_data : (opts.pending ? Lb.loading : (opts.missingText || Lb.no_data)),
      diff: function (a, b) {
        var miss = !hasText(a) ? a : (!hasText(b) ? b : null);
        var d = miss ? { blocks: [], lines: [] } : align(versionLines(S, byId[a]), versionLines(S, byId[b]));
        if (!miss) {
          // Markdown-Beschreibungen: Nebeneinander und integrierter Diff auf dem gerenderten Token-Strom
          var ma = versionMd(S, byId[a]), mb = versionMd(S, byId[b]);
          if (opts.renderMarkdown && ma != null && mb != null) d.blocks = alignMarkdown(ma, mb, opts.renderMarkdown);
          d.rich = { left: versionHtml(S, byId[a], opts.renderMarkdown), right: versionHtml(S, byId[b], opts.renderMarkdown) };
        }
        if (miss) d.note = loaded ? fmt(Lb.nodiff, { rel: rel(miss) }) : (opts.pending ? Lb.loading : (opts.missingText || Lb.no_data));
        d.left = side(a, "l"); d.right = side(b, "r");
        d.raw = {
          left: { head: esc(fmt(Lb.raw_head, { rel: rel(a) })), html: versionHtml(S, byId[a], opts.renderMarkdown), cls: "td-md" },
          right: { head: esc(fmt(Lb.raw_head, { rel: rel(b) })), html: versionHtml(S, byId[b], opts.renderMarkdown), cls: "td-md" }
        };
        return d;
      },
      meta: function (a, b) {
        var models = [byId[a], byId[b]].map(function (v) { return v && v.model ? v.model : ""; }).filter(Boolean);
        models = models.filter(function (m, i) { return models.indexOf(m) === i; });
        return models.length ? fmt(Lb.model, { m: models.join(" / ") }) : "";
      },
      deltas: function () {
        if (!loaded) return placeholder(opts.pending ? Lb.loading : (opts.missingText || Lb.no_data));
        var rows = consolidateDeltas(S.trans);
        if (!rows.length) return placeholder(Lb.deltas_empty);
        return '<div class="td-dl"><p class="td-note">' + esc(Lb.deltas_intro) + '</p><ol class="td-dl-list">' + rows.map(function (r) {
          var first = r.items[0], ch = r.change;
          var head = '<div class="td-dl-head"><span class="td-dl-span">' + esc(transSpan(r.fr, r.tr, r.from, r.to)) + "</span>" +
            '<span class="ve-epoch-status ' + esc(CHANGE_CLS[ch] || "ve-status-unchecked") + '">' + esc(changeLabel(first)) + "</span>" +
            (r.count > 1 ? '<span class="td-dl-count">(' + esc(fmt(Lb.deltas_run, { n: r.count })) + ")</span>" : "") +
            (first.model ? '<span class="td-dl-model">' + esc(first.model) + "</span>" : "") + "</div>";
          var body = r.count > 1
            ? '<details class="td-dl-each"><summary>' + esc(Lb.deltas_each) + "</summary><ol>" + r.items.map(function (tr) {
                return '<li><code>' + esc(transSpan(tr.fr, tr.tr, tr.from, tr.to)) + "</code>" + deltaBody(tr) + "</li>";
              }).join("") + "</ol></details>"
            : '<div class="td-dl-body">' + deltaBody(first) + "</div>";
          return '<li class="td-dl-row" data-change="' + esc(ch) + '" data-count="' + r.count + '">' + head + body + "</li>";
        }).join("") + '</ol><p class="td-note">' + esc(Lb.delta_note) + "</p></div>";
      },
      onChange: opts.onChange
    }, { labels: Lb, mode: opts.mode, onMode: opts.onMode });
  }

  return {
    esc: esc, decode: decode, fmt: fmt, splitLong: splitLong, mdLines: mdLines, htmlLines: htmlLines, opcodes: opcodes,
    wordDiff: wordDiff, align: align, stats: stats, ensureStyles: ensureStyles, renderSide: renderSide,
    renderUnified: renderUnified, revisions: revisions, orderPair: orderPair, chronology: chronology,
    deltasBetween: deltasBetween, defaultPair: defaultPair, seriesDiff: seriesDiff, spanOf: spanOf,
    consolidateDeltas: consolidateDeltas, CHANGE_CLS: CHANGE_CLS, tokenize: tokenize, segmentHtml: segmentHtml,
    diffHtmlPair: diffHtmlPair, integratedHtml: integratedHtml, plainHtml: plainHtml, mdUnits: mdUnits, alignMarkdown: alignMarkdown,
    progressFromScroll: progressFromScroll, LABELS_DE: LABELS_DE, CSS: CSS
  };
});
