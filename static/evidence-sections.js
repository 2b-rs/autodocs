/*
 * evidence-sections.js — Abschnitte des Versions-Explorers auf den kanonischen Belegseiten
 * (spec/snippets/<stamm>.html, spec/figures/FIG-*.html).
 *
 * Gleiche Daten wie der Explorer-Viewer: versions/explorer/items/<stamm>.json (export_explorer.py), für
 * Snippets ergänzt um den Wortlaut je Release aus dem Pack (static/frozen-pack.js, Felder rv/rt/rk).
 *   Snippet:   „Versionen & Provenienz“ (Zeitachse über die Releases mit Vergleich zweier Fassungen,
 *              VersionsExplorerCore.snippetTimeline + TextDiff.revisions wie im Explorer) und
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
  function pills(rels) {
    return '<div class="ve-epoch-subreleases">' + (rels || []).map(function (r) {
      return '<span class="ve-epoch-rel-pill">' + esc(r) + "</span>";
    }).join(" ") + "</div>";
  }
  function epochStatus(seg, rel) {
    if (seg.isChange) return { text: t("ep_changed", { rel: rel }), cls: "ve-status-changed" };
    if (seg.isRevert) return { text: t("ep_revert", { rel: rel }), cls: "ve-status-revert" };
    if (!seg.isInitial) return { text: t("ep_unchanged"), cls: "ve-status-stable" };
    return { text: t("ep_baseline"), cls: "ve-status-initial" };
  }
  function revLabels() {
    return {
      tl_title: t("tl_title"), tl_hint: t("tl_hint"), cmp: t("cmp"), left: t("ep_left"), right: t("ep_right"),
      right_drop: t("ep_right_drop"), swap: t("swap"), swap_title: t("swap_title"), base_side: t("base"), target_side: t("target"),
      mode_side: t("mode_side"), mode_unified: t("mode_unified"), mode_raw: t("mode_raw"), identical: t("identical"),
      no_data: t("no_data"), loading: t("td_loading"), stats: t("td_stats"), err: t("err_diff"), same: t("td_same"),
      single: t("tl_single")
    };
  }
  function recordHref(id) { return ROOT + "spec/record.html?id=" + encodeURIComponent(id); }   // Trampolin → Sprache

  // Abschnitte der Snippet-Zeitachse (wie snippetSegments im Explorer, ohne geschützte Seitenbilder)
  function segments(info, segs) {
    return segs.map(function (seg) {
      var span = spanText(seg.releases), p = pills(seg.releases);
      var page = seg.page ? "<div>" + esc(t("page_n", { p: seg.page })) + "</div>" : "";
      if (seg.type === "dropped") {
        return { key: seg.from, keys: seg.releases, pick: "right", cls: "ve-epoch-dropped", span: t("ep_from", { rel: seg.from }),
                 status: { text: t("st_removed"), cls: "ve-status-dropped" }, body: "<div><strong>" + esc(t("snip_dropped")) + "</strong></div>" };
      }
      if (seg.type === "presence") {
        return { span: span, cls: "ve-epoch-absent ve-epoch-presence", status: { text: t("snip_presence"), cls: "ve-status-presence" },
                 body: "<div>" + esc(t("ep_presence_text")) + "</div>" + p };
      }
      if (seg.type === "nocapture") {
        return { span: span, cls: "ve-epoch-absent ve-epoch-unchecked", status: { text: t("snip_nf_status"), cls: "ve-status-unchecked" },
                 body: "<div>" + esc(t(seg.reason === "page_excerpt" ? "snip_nf_page" : "snip_nf_none")) + "</div>" + page + p };
      }
      var st = epochStatus(seg, seg.releases[0]);
      if (seg.type === "other") {
        return { span: span, cls: "ve-epoch-absent", status: st, body: "<div>" + esc(t("snip_other")) + "</div>" + page + p };
      }
      if (seg.entries) {
        var sub = seg.releases.length === 1 ? "" : "<strong>" + esc(t("ep_many", { n: seg.releases.length })) + "</strong>";
        if (seg.texts.length > 1) sub += '<div class="ve-epoch-variants">' + esc(t("ep_variants", { n: seg.texts.length })) + "</div>";
        var ncl = 0, cut = false;
        seg.entries.forEach(function (v) { ncl += v.cl || 0; cut = cut || !!v.cut; });
        if (ncl) sub += '<div class="ve-epoch-cleaned">' + esc(t("ep_cleaned", { n: ncl })) + "</div>";
        if (cut) sub += '<div class="ve-epoch-cleaned">' + esc(t("snip_cut")) + "</div>";
        return { key: seg.releases[0], keys: seg.releases, span: span, status: st, body: (sub ? "<div>" + sub + "</div>" : "") + page + p };
      }
      var own = info.trel && seg.releases.indexOf(info.trel) >= 0;
      return { key: seg.releases[0], keys: seg.releases, span: span, status: st,
               body: "<div>" + esc(own ? t("snip_captured_rel", { rel: info.trel }) : t("snip_captured_same")) + "</div>" + page + p };
    });
  }

  function mountVersions(box, info, C, TD) {
    var gsegs = segments(info, C.snippetTimeline(info));
    if (!gsegs.length) { box.innerHTML = '<p class="ev-muted">' + esc(t("snip_notext")) + "</p>"; return; }
    var contents = gsegs.filter(function (g) { return g.key != null && g.pick !== "right"; });
    var drop = gsegs.filter(function (g) { return g.pick === "right"; })[0] || null;
    var from = null, to = null;
    if (contents.length > 1) { from = contents[0].key; to = contents[contents.length - 1].key; }
    else if (contents.length === 1) { from = contents[0].key; to = drop ? drop.key : contents[0].key; }
    var perRel = !!(info.rv && info.rv.length), byRel = {};
    (info.rv || []).forEach(function (v) { byRel[v.r] = v; });
    function textOf(k) {
      if (!perRel) return C.decodeFully(info.text || "");
      var v = byRel[k];
      var relText = (v && v.t != null && info.rt) ? C.decodeFully(info.rt[v.t] || "") : "";
      return relText || C.decodeFully(info.text || "");
    }
    function linesOf(k) { return TD.splitLong([textOf(k).replace(/\s*\n\s*/g, " ")]); }
    function isDrop(k) { return !!drop && k === drop.key; }
    function pageTag(k) { var v = byRel[k]; return v && v.p ? t("page_n", { p: v.p }) : ""; }
    function raw(k) {
      return { head: esc(t("raw_version")) + " " + esc(k) + (isDrop(k) ? " (" + esc(t("st_removed")) + ")" : (pageTag(k) ? " · " + esc(pageTag(k)) : "")),
               html: "<pre>" + esc(isDrop(k) ? t("snip_dropped") : textOf(k)) + "</pre>" };
    }
    TD.revisions(box, {
      segments: gsegs, from: from, to: to, hint: perRel ? null : t("snip_rev_hint"),
      emptyText: t("snip_notext"),
      singleText: !contents.length ? (info.text ? t("snip_rev_single") : t("snip_notext")) : (perRel ? t("tl_single") : t("snip_rev_single")),
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
      }
    }, { labels: revLabels(), mode: "side" });
  }

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
      if (rev && TD) mountVersions(rev, info, C, TD);
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run);
  else run();
})();
