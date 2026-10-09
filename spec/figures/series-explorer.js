
(function () {
  "use strict";
  var box = document.querySelector(".fig-explorer[data-series]");
  if (!box || !window.FIG_SERIES || !window.FIG_SERIES[box.dataset.series]) return;
  var S = window.FIG_SERIES[box.dataset.series], cur = box.dataset.current;
  var byId = {}; S.versions.forEach(function (v) { byId[v.id] = v; });
  // Zeitachse: Folge der Fassungen entlang der Übergänge (eine Fassung kann bei Rückkehr mehrfach vorkommen)
  var seq = S.trans.length ? [S.trans[0].from].concat(S.trans.map(function (t) { return t.to; })) : [cur];
  function positions(id) { var r = []; seq.forEach(function (x, i) { if (x === id) r.push(i); }); return r; }
  function rel(v) { return (v.releases || []).join(", "); }
  function stack(a, b) {
    var pa = positions(a), pb = positions(b), best = null;
    pa.forEach(function (i) { pb.forEach(function (j) { if (!best || Math.abs(i - j) < Math.abs(best[0] - best[1])) best = [i, j]; }); });
    if (!best) return [];
    var lo = Math.min(best[0], best[1]), hi = Math.max(best[0], best[1]);
    return S.trans.slice(lo, hi);
  }
  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]; }); }
  function render(other) {
    box.innerHTML = "";
    box.appendChild(el("h4", null, "Versionen dieser Bildreihe <span class=\"ai-model\">KI-generiert</span>"));
    var chips = el("div", "fx-chips");
    S.versions.forEach(function (v) {
      var c = el(v.id === cur ? "span" : "button", "fx-chip" + (v.id === cur ? " fx-cur" : "") + (v.id === other ? " fx-sel" : ""),
                 "<b>" + esc(rel(v)) + "</b><small>" + esc(v.id) + "</small>");
      if (v.id !== cur) { c.type = "button"; c.title = "Mit dieser Fassung vergleichen"; c.addEventListener("click", function () { render(v.id); }); }
      chips.appendChild(c);
    });
    box.appendChild(chips);
    if (!other) return;
    var a = byId[cur], b = byId[other], st = stack(cur, other);
    var head = el("div", "fx-head", "Vergleich <b>" + esc(rel(a)) + "</b> ↔ <b>" + esc(rel(b)) + "</b> · " + st.length +
                  " Delta" + (st.length === 1 ? "" : "s") + " · <a href=\"" + esc(other) + ".html\">Seite der Vergleichsfassung</a>");
    box.appendChild(head);
    var ds = el("div", "fx-stack");
    st.forEach(function (t) {
      var d = el("div", "fig-delta fig-delta-" + t.change);
      d.appendChild(el("div", "fig-delta-head", "<span class=\"release-tag\">" + esc(t.fr) + " → " + esc(t.tr) +
                    "</span><span class=\"fig-delta-kind\">" + esc(t.label) + "</span>"));
      d.appendChild(el("div", "fig-delta-body", t.html));
      ds.appendChild(d);
    });
    if (!st.length) ds.appendChild(el("p", "fx-none", "Für diesen Abstand liegen noch keine Deltas vor."));
    box.appendChild(ds);
    var two = el("div", "fx-two");
    [a, b].forEach(function (v, i) {
      var col = el("div", "fx-col" + (i === 0 ? " fx-col-cur" : ""));
      col.appendChild(el("div", "fx-col-h", (i === 0 ? "Diese Fassung · " : "Vergleichsfassung · ") + esc(rel(v))));
      col.appendChild(el("div", "fx-col-b", v.html || "<p class=\"fx-none\">Noch keine KI-Beschreibung.</p>"));
      two.appendChild(col);
    });
    box.appendChild(two);
  }
  var i = S.versions.map(function (v) { return v.id; }).indexOf(cur);
  var p = positions(cur), dflt = null;
  if (p.length && p[0] > 0) dflt = seq[p[0] - 1]; else if (p.length && p[0] < seq.length - 1) dflt = seq[p[0] + 1];
  render(dflt && dflt !== cur ? dflt : null);
})();
