/*
 * spec-text-i18n.js — Übersetzte Spezifikationstexte auf der Record-Seite (<lang>/spec/record.html).
 *
 * Quelle der Übersetzungen: versions/spec-i18n/<lang>/<xx>.json (spec_text_i18n.py export), Teil <xx> aus FNV-1a
 * der Kennung (256 Teile je Sprache, ein Abruf je Seite). Eintrag r[<id>][<text_key>][<feld>] = [HTML,
 * Provenienz-Index, TM-Glieder]; <text_key> ist der Inhaltsschlüssel der Versionszeile (spec-text-key@1), <feld>
 * die Kennung des Felds (description, return_value, notes, note, rationale; Wiederholung _2 …).
 *
 * Anzeige: Übersetzung in der Seitensprache, Original im Tooltip (title), Schalter „Original anzeigen“ /
 * „Übersetzung anzeigen“, Hinweis „Maschinell übersetzt · Modell … · Stand …“. Die Wahl bleibt je Betrachter in
 * localStorage (autodocs_spec_text_mode); ohne Speicher gilt die Übersetzung. Fehlt eine Übersetzung, ist der Teil
 * nicht ladbar oder die Fassung unzulässig (nur p, br, code.spec-code), bleibt das Original ohne Schalter stehen.
 * Englisch ist die Quellsprache: dort nichts.
 *
 * Die Felder liest die Record-Seite aus dem Vermerk „fields“ (api-fields@1); spec_text_i18n.py liest sie ebenso
 * (span_text, note_fields). Kennungen, Teile und Entitäten vergleicht test_spec_text_i18n.py über Node.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.SpecTextI18n = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  var SOURCE_LANG = "en";
  var STORE_KEY = "autodocs_spec_text_mode";
  var BASE = "versions/spec-i18n/";

  // Übersetzte Angaben der API-Tabelle (Vermerk „fields“, api-fields@1): Beschriftung -> Kennung; ab dem zweiten
  // Vorkommen derselben Beschriftung mit Zusatz _2, _3 … (PROSE_FIELDS/field_id in spec_text_i18n.py). Alle übrigen
  // Angaben (Syntax, Symbol, Header file, Kind, Scope, Untertabellen …) bleiben Original.
  var PROSE_FIELDS = { "Return value": "return_value", "Notes": "notes", "Note": "note", "Rationale": "rationale" };

  function fieldId(key, nth) {
    if (!Object.prototype.hasOwnProperty.call(PROSE_FIELDS, key)) return null;
    return nth > 1 ? PROSE_FIELDS[key] + "_" + nth : PROSE_FIELDS[key];
  }

  // Normalisierter Anzeigetext (text_rejoin.py, wie shownContent im Versions-Explorer)
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

  // HTML-Entitäten der gespeicherten Wortlaute bis zum Fixpunkt auflösen (höchstens dreimal), wie decodeFully im
  // Versions-Explorer: nur &lt; &gt; &amp; &quot; &apos; &nbsp; und numerische. Das Ergebnis ist Text, kein HTML.
  var ENTITY = /&(?:([A-Za-z]+)|#(\d+)|#x([0-9A-Fa-f]+));/g;
  var NAMED = { lt: "<", gt: ">", amp: "&", quot: '"', apos: "'", nbsp: "\u00a0" };
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

  function fnv1a32(s) {
    var h = 0x811c9dc5;
    s = String(s);
    for (var i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = Math.imul(h, 0x01000193) >>> 0;
    }
    return h >>> 0;
  }

  function shardOf(id) {
    return ("0" + (fnv1a32(id) & 0xff).toString(16)).slice(-2);
  }

  // Nur die Bausteine, die spec_text_i18n.desc_html erzeugt; alles andere: keine Übersetzung zeigen.
  var TAG_OK = /^<\/?(?:p|br|code)(?: class="spec-code")?>$/;
  function sanitize(html) {
    if (typeof html !== "string" || !html) return null;
    var tags = html.match(/<[^>]*>/g) || [];
    for (var i = 0; i < tags.length; i++) if (!TAG_OK.test(tags[i])) return null;
    if (/<(?![^<>]*>)/.test(html) || /javascript:/i.test(html)) return null;
    return html;
  }

  function getMode() {
    try {
      var v = window.localStorage.getItem(STORE_KEY);
      return v === "original" ? "original" : "translated";
    } catch (e) {
      return "translated";
    }
  }

  function setMode(mode) {
    try { window.localStorage.setItem(STORE_KEY, mode === "original" ? "original" : "translated"); } catch (e) { /* ohne Speicher */ }
  }

  var shards = {};
  function loadShard(root, lang, shard) {
    var url = String(root || "") + BASE + encodeURIComponent(lang) + "/" + shard + ".json";
    if (!shards[url]) {
      shards[url] = fetch(url).then(function (res) {
        return res.ok ? res.json() : null;
      }).then(function (d) {
        return d && d.schema === "spec-text-i18n@1" && d.r ? d : null;
      }).catch(function () {
        delete shards[url];      // Netzfehler: beim nächsten Mal erneut versuchen
        return null;
      });
    }
    return shards[url];
  }

  // Übersetzungen einer Versionszeile: { feld: {html, prov, tm} } oder null
  function lookup(root, lang, id, textKey) {
    if (!lang || lang === SOURCE_LANG || !id || !textKey || typeof fetch !== "function") return Promise.resolve(null);
    return loadShard(root, lang, shardOf(id)).then(function (d) {
      var rec = d && d.r[id] && d.r[id][textKey];
      if (!rec) return null;
      var out = {}, n = 0;
      Object.keys(rec).forEach(function (field) {
        var row = rec[field], html = sanitize(row && row[0]);
        if (!html) return;
        out[field] = { html: html, prov: (d.prov || [])[row[1]] || {}, tm: row[2] || "" };
        n++;
      });
      return n ? out : null;
    });
  }

  var STRINGS = {
    de: { note: "Maschinell übersetzt", model: "Modell", asof: "Stand", show_original: "Original anzeigen",
      show_translation: "Übersetzung anzeigen", original: "Original (Englisch)", heading: "Spezifikations-Text",
      original_note: "Original (Englisch) angezeigt" },
    en: { note: "Machine-translated", model: "Model", asof: "as of", show_original: "Show original",
      show_translation: "Show translation", original: "Original (English)", heading: "Specification Text",
      original_note: "Showing the original (English)" },
    es: { note: "Traducción automática", model: "Modelo", asof: "estado", show_original: "Mostrar original",
      show_translation: "Mostrar traducción", original: "Original (inglés)", heading: "Texto de la especificación",
      original_note: "Se muestra el original (inglés)" },
    pt: { note: "Tradução automática", model: "Modelo", asof: "versão de", show_original: "Mostrar original",
      show_translation: "Mostrar tradução", original: "Original (inglês)", heading: "Texto da especificação",
      original_note: "Exibindo o original (inglês)" },
    fr: { note: "Traduction automatique", model: "Modèle", asof: "état au", show_original: "Afficher l’original",
      show_translation: "Afficher la traduction", original: "Original (anglais)", heading: "Texte de la spécification",
      original_note: "Original (anglais) affiché" },
    ru: { note: "Машинный перевод", model: "Модель", asof: "по состоянию на", show_original: "Показать оригинал",
      show_translation: "Показать перевод", original: "Оригинал (английский)", heading: "Текст спецификации",
      original_note: "Показан оригинал (английский)" },
    ar: { note: "ترجمة آلية", model: "النموذج", asof: "بتاريخ", show_original: "عرض النص الأصلي",
      show_translation: "عرض الترجمة", original: "النص الأصلي (بالإنجليزية)", heading: "نص المواصفة",
      original_note: "يُعرض النص الأصلي (بالإنجليزية)" },
    hi: { note: "मशीनी अनुवाद", model: "मॉडल", asof: "स्थिति", show_original: "मूल दिखाएँ",
      show_translation: "अनुवाद दिखाएँ", original: "मूल (अंग्रेज़ी)", heading: "विनिर्देश पाठ",
      original_note: "मूल (अंग्रेज़ी) दिखाया जा रहा है" },
    ko: { note: "기계 번역", model: "모델", asof: "기준", show_original: "원문 보기", show_translation: "번역 보기",
      original: "원문(영어)", heading: "사양 텍스트", original_note: "원문(영어) 표시 중" },
    zh: { note: "机器翻译", model: "模型", asof: "截至", show_original: "显示原文", show_translation: "显示译文",
      original: "原文（英文）", heading: "规范文本", original_note: "正在显示原文（英文）" },
    nl: { note: "Machinaal vertaald", model: "Model", asof: "stand", show_original: "Origineel tonen",
      show_translation: "Vertaling tonen", original: "Origineel (Engels)", heading: "Specificatietekst",
      original_note: "Origineel (Engels) getoond" }
  };

  function strings(lang) {
    return STRINGS[lang] || STRINGS.en;
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function noteHtml(lang, prov, mode) {
    var S = strings(lang), models = (prov.models || []).join(", ");
    var head = mode === "original" ? S.original_note : S.note;
    return esc(head) + (models ? " · " + esc(S.model) + " <code>" + esc(models) + "</code>" : "") +
      (prov.at ? " · " + esc(S.asof) + " " + esc(prov.at) : "");
  }

  function show(t, mode, lang) {
    var el = t.el;
    if (!el) return;
    if (mode === "original") {
      el.innerHTML = t.originalHtml;
      el.setAttribute("lang", SOURCE_LANG);
      el.setAttribute("dir", "ltr");          // englisches Original auch auf RTL-Seiten links beginnend
      el.removeAttribute("title");
      el.setAttribute("data-spec-text", "original");
    } else {
      el.innerHTML = t.tr.html;
      el.setAttribute("lang", lang);
      el.removeAttribute("dir");
      el.setAttribute("title", strings(lang).original + ": " + t.text);
      el.setAttribute("data-spec-text", "translated");
    }
  }

  function ensureBar(anchor) {
    var bar = anchor && anchor.ownerDocument && anchor.ownerDocument.getElementById("rec-desc-tr-bar");
    if (bar || !anchor || !anchor.parentNode) return bar;
    bar = anchor.ownerDocument.createElement("div");
    bar.id = "rec-desc-tr-bar";
    bar.className = "spec-tr-bar";
    bar.hidden = true;
    bar.innerHTML = '<span class="spec-tr-note"></span> <button type="button" class="spec-tr-toggle" aria-pressed="false"></button>';
    anchor.parentNode.insertBefore(bar, anchor);
    return bar;
  }

  // opts: { root, lang, id, textKey, bar: Element vor dem die Leiste steht, targets: [{field, el, text}] }
  // Ziele zeigen zunächst das Original (originalHtml = aktueller Inhalt). Rückgabe: Promise<Zahl übersetzter Ziele>.
  var seq = 0;
  function apply(opts) {
    var targets = (opts.targets || []).filter(function (t) { return t && t.el; });
    var bar = ensureBar(opts.bar || (targets[0] && targets[0].el));
    var my = ++seq;
    targets.forEach(function (t) {
      t.originalHtml = t.el.innerHTML;
      t.el.removeAttribute("title");
      t.el.removeAttribute("dir");
      t.el.removeAttribute("data-spec-text");
    });
    if (bar) bar.hidden = true;
    var lang = opts.lang;
    if (!lang || lang === SOURCE_LANG) return Promise.resolve(0);
    return lookup(opts.root, lang, opts.id, opts.textKey).then(function (fields) {
      if (my !== seq || !fields) return 0;
      var live = targets.filter(function (t) { t.tr = fields[t.field]; return !!t.tr; });
      if (!live.length) return 0;
      var prov = live[0].tr.prov;
      var mode = getMode();
      live.forEach(function (t) { show(t, mode, lang); });
      if (bar) {
        var note = bar.querySelector(".spec-tr-note"), btn = bar.querySelector(".spec-tr-toggle");
        var S = strings(lang);
        var paint = function () {
          note.innerHTML = noteHtml(lang, prov, mode);
          note.setAttribute("title", "translate-spec-segments@1 · " + (live[0].tr.tm ? "TM " + live[0].tr.tm : "") +
            ((prov.runs || []).length ? " · " + prov.runs.join(", ") : ""));
          btn.textContent = mode === "original" ? S.show_translation : S.show_original;
          btn.setAttribute("aria-pressed", mode === "original" ? "true" : "false");
          bar.setAttribute("data-mode", mode);
        };
        btn.onclick = function () {
          mode = mode === "original" ? "translated" : "original";
          setMode(mode);
          live.forEach(function (t) { show(t, mode, lang); });
          paint();
        };
        paint();
        bar.hidden = false;
      }
      return live.length;
    }).catch(function () { return 0; });
  }

  return {
    fieldId: fieldId,
    shownContent: shownContent,
    decodeFully: decodeFully,
    fnv1a32: fnv1a32,
    shardOf: shardOf,
    sanitize: sanitize,
    lookup: lookup,
    apply: apply,
    strings: strings,
    getMode: getMode,
    setMode: setMode,
    STORE_KEY: STORE_KEY
  };
});
