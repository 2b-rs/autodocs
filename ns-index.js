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
(function () {
  "use strict";
  var SVGNS = "http://www.w3.org/2000/svg";
  var ORDER_KEY = "nsx-fold-order", BY_KEY = "nsx-group-by", W_KEY = "nsx-aside-w", TDOCK_KEY = "nsx-titledock";
  var ICON_DOCK = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2.5v7M5 6.5l3 3 3-3M2.5 13h11"/></svg>';
  var ICON_CLOSE = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 4l8 8M12 4l-8 8"/></svg>';

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
  var reduceMotion = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  var behavior = reduceMotion ? "auto" : "smooth";

  function init(root) {
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
        if (rel && (words(r, "data-releases").indexOf(rel) >= 0 || gone)) any = true;
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
    root.querySelectorAll(".nsx-row .nsx-sig").forEach(function (sg) {
      var code = sg.querySelector("code"), go = sg.querySelector("a.nsx-go");
      var m = code && go && /(operator\s*[^\s(]+|[A-Za-z_~][\w:]*)\s*\(/.exec(code.textContent);
      if (!m) return;
      var fname = m[1].replace(/\s+/g, "").split("::").pop();
      (fnIndex[fname] = fnIndex[fname] || []).push({ id: go.getAttribute("href").slice(1), code: code });
    });

    // ---- Clusterseiten: die Modulkarten stehen als Zeile über der Überschrift und scrollen
    // mit der Seite heraus (Aufnahme 13:03); ihre Überschrift „Module im Cluster“ entfällt
    var cluCards = isClu && document.querySelector("main > div.cards"), mainH1 = document.querySelector("main > h1");
    if (cluCards && mainH1) {
      var ch2 = cluCards.previousElementSibling;
      if (ch2 && ch2.matches("h2.sect")) ch2.hidden = true;
      cluCards.classList.add("nsx-clucards");
      mainH1.parentNode.insertBefore(cluCards, mainH1);
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

    // ---- Dokumentationsabschnitte: Inhalt erscheint nur noch in der Detailansicht
    document.querySelectorAll("details.nsx-doc").forEach(function (d) { d.hidden = true; });

    // ---- User Guide und Implementer's Guide der Seite als erste Folds der Mitte (Dokumentreihenfolge)
    var guideFold = null, seenKinds = {};
    for (var p = root.previousElementSibling, prevP; p; p = prevP) {
      prevP = p.previousElementSibling;   // vor dem Umhängen merken
      if (p.tagName === "DETAILS" && p.classList.contains("fold") && !p.classList.contains("nsx-doc") && p.querySelector(".ai")) {
        var gkind = p.classList.contains("impl-fold") ? "impl" : "guide";
        if (seenKinds[gkind]) continue;
        seenKinds[gkind] = true;
        p.classList.add("nsx-fold");
        p.setAttribute("data-fold", gkind);
        if (gkind === "guide" || !guideFold) guideFold = p;
        var sm = p.querySelector("summary");
        if (sm && !sm.querySelector(".nsx-grip")) {
          var gr = document.createElement("span");
          gr.className = "nsx-grip";
          gr.setAttribute("role", "button");
          gr.setAttribute("tabindex", "0");
          sm.insertBefore(gr, sm.firstChild);
        }
        folds.insertBefore(p, folds.firstChild);
      }
    }

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

    // ---- Weitere Abschnitte vor der Übersicht (z.B. Synopsis, Ablauf- oder Lebenszyklus-
    // diagramm einer Klassenseite): je Überschrift ein Fold der Mitte hinter den Guides
    (function () {
      var kids = [], cur = null, n = 0;
      var at = Array.prototype.filter.call(folds.children, function (x) { return !/^(guide|impl)$/.test(x.getAttribute("data-fold") || ""); })[0] || null;
      for (var q = root.previousElementSibling; q; q = q.previousElementSibling) kids.unshift(q);
      kids.forEach(function (k) {
        if (k.matches("h2.sect")) {
          cur = document.createElement("details");
          cur.className = "fold nsx-fold nsx-secfold";
          cur.open = true;
          cur.setAttribute("data-fold", "sec" + (++n));
          var sm = document.createElement("summary"), gr = document.createElement("span");
          gr.className = "nsx-grip";
          gr.setAttribute("role", "button");
          gr.setAttribute("tabindex", "0");
          sm.appendChild(gr);
          sm.appendChild(k);
          cur.appendChild(sm);
          folds.insertBefore(cur, at);
        } else if (cur && !k.matches("details, dialog, script, article.rec")) cur.appendChild(k);
        else cur = null;
      });
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
    function foldList() { return Array.prototype.filter.call(folds.children, function (x) { return x.matches("details[data-fold]"); }); }
    function applyOrder() {
      var order = (load(ORDER_KEY) || "").split(",").filter(Boolean);
      if (!order.length) return;
      var fl = foldList();
      fl.slice().sort(function (a, b) {
        var ia = order.indexOf(a.getAttribute("data-fold")), ib = order.indexOf(b.getAttribute("data-fold"));
        if (ia < 0) ia = 99 + fl.indexOf(a);
        if (ib < 0) ib = 99 + fl.indexOf(b);
        return ia - ib;
      }).forEach(function (f) { folds.appendChild(f); });
    }
    function saveOrder() { save(ORDER_KEY, foldList().map(function (f) { return f.getAttribute("data-fold"); }).join(",")); }
    applyOrder();
    var dragging = null;
    folds.querySelectorAll(".nsx-grip").forEach(function (g) {
      var gl = (canTitleDock(g.closest("details")) ? labels.gripdock : labels.grip) || "";
      g.setAttribute("title", gl);
      g.setAttribute("aria-label", gl);
      g.addEventListener("click", function (ev) { ev.preventDefault(); ev.stopPropagation(); });
      g.addEventListener("pointerdown", function () { g.closest("details").draggable = true; });
      g.addEventListener("keydown", function (ev) {
        if (ev.key !== "ArrowUp" && ev.key !== "ArrowDown") return;
        ev.preventDefault();
        var f = g.closest("details"), fl = foldList().filter(function (x) { return !x.classList.contains("nsx-tdocked"); }), i = fl.indexOf(f);
        if (ev.key === "ArrowUp" && i === 0 && canTitleDock(f)) { dockTitle(f); return; }
        if (ev.key === "ArrowUp" && i > 0) folds.insertBefore(f, fl[i - 1]);
        else if (ev.key === "ArrowDown" && i < fl.length - 1) folds.insertBefore(fl[i + 1], f);
        else return;
        g.focus();
        saveOrder();
      });
    });
    folds.addEventListener("dragstart", function (ev) {
      var f = ev.target.closest && ev.target.closest("details[data-fold]");
      if (!f || !f.draggable) return;
      dragging = f;
      f._fromTitle = false;
      f._dropped = false;
      f.classList.add("nsx-dragging");
      root.classList.add("nsx-dnd");
      if (canTitleDock(f)) title.classList.add("nsx-drop-zone");
      ev.dataTransfer.effectAllowed = "move";
      try { ev.dataTransfer.setData("text/plain", f.getAttribute("data-fold")); } catch (e) { /* alte Browser */ }
    });
    // Ablagefläche ist die ganze mittlere Spalte, nicht nur die Folds: Ist die Mitte leer
    // (alles angedockt, nichts ausgewählt), war sie nur so hoch wie der Hinweis, und ein
    // Reiter, der darunter losgelassen wurde, dockte wieder an (Aufnahme 12:24)
    var dropZone = folds.parentNode;
    dropZone.addEventListener("dragover", function (ev) {
      if (!dragging) return;
      ev.preventDefault();
      try { ev.dataTransfer.dropEffect = "move"; } catch (e) { /* alte Browser */ }
      if (dragging.classList.contains("nsx-tdocked")) {
        undockTitle(dragging, undefined, true);     // Vorschau; endgültig erst beim Ablegen
        dragging.classList.add("nsx-dragging");
      }
      var t = ev.target.closest && ev.target.closest("details[data-fold]");
      if (t && t !== dragging && t.parentNode === folds) {
        var r = t.getBoundingClientRect();
        folds.insertBefore(dragging, ev.clientY < r.top + Math.min(r.height / 2, 60) ? t : t.nextSibling);
        return;
      }
      if (t) return;
      // Freie Fläche: über dem ersten sichtbaren Fold an den Anfang, sonst ans Ende
      var vis = foldList().filter(function (x) { return x !== dragging && docked(x); });
      if (!vis.length) return;
      if (ev.clientY < vis[0].getBoundingClientRect().top) folds.insertBefore(dragging, vis[0]);
      else if (ev.clientY > vis[vis.length - 1].getBoundingClientRect().bottom) folds.insertBefore(dragging, vis[vis.length - 1].nextSibling);
    });
    dropZone.addEventListener("drop", function (ev) { if (dragging) { ev.preventDefault(); dragging._dropped = true; } });
    // Ablage nicht allein am drop-Ereignis festmachen: Manche Browser (Aufnahme 13:02, Safari)
    // liefern es nicht zuverlässig, der Fold flog dann kommentarlos zurück. Maßgeblich ist die
    // letzte Zeigerposition während des Zugs: Titelleiste (mit 16 px Toleranz) oder mittlere
    // Spalte; außerhalb erscheint ein Hinweis statt eines stillen Zurückspringens.
    var lastDrag = null;
    document.addEventListener("dragover", function (ev) { if (dragging) lastDrag = { x: ev.clientX, y: ev.clientY }; });
    function inRect(p, r, tol) { return p.x >= r.left - tol && p.x <= r.right + tol && p.y >= r.top - tol && p.y <= r.bottom + tol; }
    function dropZoneAt(p) {
      if (!p) return null;
      if (title && inRect(p, title.getBoundingClientRect(), 16)) return "title";
      var z = dropZone.getBoundingClientRect();
      if (p.x >= z.left && p.x <= z.right && p.y >= z.top) return "center";
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
      if (!dragging) return;
      root.classList.remove("nsx-dnd");
      if (title) title.classList.remove("nsx-drop-zone", "nsx-drop-over");
      var at = lastDrag, zone = dropZoneAt(at);
      lastDrag = null;
      if (!dragging._dropped) {
        if (zone === "title" && !dragging._fromTitle && canTitleDock(dragging)) {
          dragging._dropped = true;
          dockTitle(dragging);
        } else if (zone === "center") {
          dragging._dropped = true;
          if (dragging._fromTitle && dragging.classList.contains("nsx-tdocked")) undockTitle(dragging, undefined, true);
        } else if (!zone && (dragging._fromTitle || canTitleDock(dragging))) showDropHint(at);
      }
      // Aus der Titelleiste gezogen: in der Mitte abgelegt → endgültig gelöst,
      // sonst (abgebrochen, auf der Leiste losgelassen) bleibt der Reiter angedockt
      if (dragging._fromTitle) {
        saveTitleDock();
        if (dragging._dropped && !dragging.classList.contains("nsx-tdocked")) {
          var tb = tdock.querySelector('[data-fold="' + dragging.getAttribute("data-fold") + '"]');
          if (tb) tb.remove();
          saveTitleDock();
        } else dockTitle(dragging);
        dragging._fromTitle = false;
      }
      dragging.classList.remove("nsx-dragging");
      dragging.draggable = false;
      dragging = null;
      saveOrder();
      if (selected) drawArrows(selected);
    });
    document.addEventListener("pointerup", function () { foldList().forEach(function (f) { if (f !== dragging) f.draggable = false; }); });

    function isClassRow(r) { return r.getAttribute("data-kind") === "class"; }
    // Einträge mit eigener Seite (Klassen, Service-Interfaces): Detailansicht lädt die ganze Seite
    function isPageRow(r) {
      var h = r.getAttribute("data-href") || "";
      return !!h && h.charAt(0) !== "#" && !r.getAttribute("data-recs");
    }
    // Kennzahlen eines KI-Texts: Prüfstatus, Release, Abschnitte, Lesezeit, SWS-Verweise, Diagramme
    function statsHtml(scope) {
      var rel = currentRelease(), all = scope.querySelectorAll(".ai-guide-release-variant");
      var v = Array.prototype.filter.call(all, function (x) { return rel && words(x, "data-applicable-releases").indexOf(rel) >= 0; })[0] || all[0] || scope;
      var ai = v.matches && v.matches(".ai") ? v : (v.querySelector(".ai") || v);
      var c = ai.cloneNode(true);
      c.querySelectorAll(".ai-trace-badge, .ai-note, .ai-commentary-actions, script, style, svg").forEach(function (x) { x.remove(); });
      var txt = c.textContent, nw = (txt.match(/\S+/g) || []).length;
      if (/[\u3040-\u9fff\uac00-\ud7af]/.test(txt)) nw = Math.max(nw, txt.replace(/\s/g, "").length / 2.5);
      var refs = {};
      ai.querySelectorAll(".spec-record-ref[data-req]").forEach(function (a) { refs[a.getAttribute("data-req")] = 1; });
      var rev = ai.querySelector(".ai-review-state"), parts = [];
      if (rev) parts.push('<span class="nsx-st nsx-st-rev nsx-st-' + esc(ai.getAttribute("data-trace-review") || "") + '">' + esc(rev.textContent.trim()) + "</span>");
      var asof = v.getAttribute && v.getAttribute("data-asof-release");
      if (asof) parts.push('<span class="nsx-st">' + esc(asof) + "</span>");
      function st(k, n) { if (n) parts.push('<span class="nsx-st">' + esc(labels[k] || "") + " <b>" + n + "</b></span>"); }
      st("secs", ai.querySelectorAll("h4").length);
      if (nw) parts.push('<span class="nsx-st">' + esc(labels.read || "") + " <b>≈" + Math.max(1, Math.round(nw / 200)) + " min</b></span>");
      st("refs", Object.keys(refs).length);
      st("diag", ai.querySelectorAll(".diagram").length);
      return parts.join("");
    }

    // ---- Kennzahlen des User Guide in seiner Titelzeile
    function guideStats() {
      if (!guideFold) return;
      var sm = guideFold.querySelector("summary"), box = sm.querySelector(".nsx-stats");
      if (!box) {
        box = document.createElement("span");
        box.className = "nsx-stats";
        sm.insertBefore(box, sm.querySelector(".nsx-hbtn"));
      }
      box.innerHTML = statsHtml(guideFold);
      if (typeof fillTab === "function" && guideFold.classList.contains("nsx-tdocked")) fillTab(guideFold);
    }

    // ---- Andocken von User Guide und Themenkarte in die Titelleiste
    // Griff auf die Titelleiste ziehen: Der Fold wird dort zum Reiter, der ihn als
    // Panel unter der Leiste aufklappt. Reiter zurück in die Mitte ziehen (oder der
    // Knopf im Panel, Pfeil-ab am Reiter) löst ihn wieder. Tastatur: Pfeil-auf am
    // Griff des obersten Folds dockt an.
    var tdock = null, popFold = null;
    function canTitleDock(f) { return !!(title && f && /^(guide|impl|map|uml)$/.test(f.getAttribute("data-fold") || "")); }
    function foldLabel(f) {
      var h = f.querySelector("summary > h2");
      if (!h) return f.getAttribute("data-fold");
      var c = h.cloneNode(true);
      c.querySelectorAll(".ai-badge").forEach(function (x) { x.remove(); });
      return c.textContent.trim();
    }
    if (title) {
      tdock = document.createElement("span");
      tdock.className = "nsx-tdock";
      title.appendChild(tdock);
    }
    var isCls = root.classList.contains("nsx-cls");
    var tdockKey = TDOCK_KEY + (isCls ? "-cls" : "");
    function saveTitleDock() {
      var keys = tdock ? Array.prototype.filter.call(tdock.children, function (b) { return !b.hidden; })
        .map(function (b) { return b.getAttribute("data-fold"); }) : [];
      save(tdockKey, keys.join(","));          // auch leer speichern: sonst gälte wieder die Vorgabe
    }
    // Das Panel hängt bündig unter seinem Reiter; der Reiter ist sein Titel
    function placePop() {
      if (!popFold) return;
      var b = tdock.querySelector('[data-fold="' + popFold.getAttribute("data-fold") + '"]');
      if (!b) return;
      var t = b.getBoundingClientRect(), c = folds.getBoundingClientRect();
      var rtl = getComputedStyle(root).direction === "rtl";
      // Breite wie die Mitte (mindestens 480 px); steht der Reiter weit rechts (links bei
      // RTL), rückt das Panel zurück ins Fenster, statt schmal zu werden
      var w = Math.max(t.width, Math.min(Math.max(c.width, 480), innerWidth - 24));
      var left = rtl ? Math.max(12, Math.min(t.right - w, innerWidth - 12 - w)) : Math.max(12, Math.min(t.left, innerWidth - 12 - w));
      var tabx = rtl ? left + w - t.right : t.left - left;
      popFold.style.top = t.bottom - 1 + "px";
      popFold.style.left = left + "px";
      popFold.style.width = w + "px";
      popFold.style.setProperty("--nsx-tabw", t.width + "px");
      popFold.style.setProperty("--nsx-tabx", Math.max(0, tabx) + "px");
      popFold.classList.toggle("nsx-pop-shift", tabx > 1);
    }
    function setPop(f) {
      if (popFold && popFold !== f) {
        popFold.classList.remove("nsx-pop", "nsx-pop-shift");
        ["top", "left", "width"].forEach(function (k) { popFold.style[k] = ""; });
        var ob = tdock.querySelector('[data-fold="' + popFold.getAttribute("data-fold") + '"]');
        if (ob) ob.setAttribute("aria-expanded", "false");
      }
      popFold = f;
      if (!f) return;
      f.classList.add("nsx-pop");
      f.open = true;
      placePop();
      var b = tdock.querySelector('[data-fold="' + f.getAttribute("data-fold") + '"]');
      if (b) b.setAttribute("aria-expanded", "true");
      if (selected) drawArrows(selected);
    }
    // Der Reiter zeigt dieselbe Zeile wie der Fold in der Mitte: Griff, Titel samt
    // Badge und Kennzahlen (ohne Knöpfe)
    function fillTab(f) {
      var b = tdock && tdock.querySelector('[data-fold="' + f.getAttribute("data-fold") + '"]');
      if (!b) return;
      var c = f.querySelector("summary").cloneNode(true);
      c.querySelectorAll(".nsx-hbtn, .nsx-canon-link").forEach(function (x) { x.remove(); });
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
    function dockTitle(f) {
      if (!canTitleDock(f) || f.classList.contains("nsx-tdocked")) return;
      var key = f.getAttribute("data-fold");
      var old = tdock.querySelector('[data-fold="' + key + '"]');
      if (old) {
        // Reiter aus einer abgebrochenen Ziehvorschau wieder zeigen
        old.hidden = false;
        f.classList.add("nsx-tdocked");
        f.classList.remove("nsx-dragging");
        updateEmpty();
        return;
      }
      var b = document.createElement("button");
      b.type = "button";
      b.className = "nsx-tab";
      b.draggable = true;
      b.setAttribute("data-fold", key);
      b.setAttribute("aria-expanded", "false");
      b.title = labels.tundock || "";
      tdock.appendChild(b);
      fillTab(f);
      f.classList.add("nsx-tdocked");
      saveTitleDock();
      updateEmpty();
    }
    // preview: während des Ziehens nur in der Mitte zeigen; der Reiter bleibt (versteckt)
    // im DOM, damit dragend an ihm ankommt
    function undockTitle(f, before, preview) {
      if (!f || !f.classList.contains("nsx-tdocked")) return;
      if (popFold === f) setPop(null);
      f.classList.remove("nsx-tdocked");
      var b = tdock.querySelector('[data-fold="' + f.getAttribute("data-fold") + '"]');
      if (b) { if (preview) b.hidden = true; else b.remove(); }
      if (before !== undefined) folds.insertBefore(f, before);
      if (preview) { updateEmpty(); return; }
      saveTitleDock();
      updateEmpty();
      saveOrder();
      if (selected) drawArrows(selected);
    }
    // Ist die Mitte leer (alles angedockt, nichts ausgewählt), steht dort der Hinweis
    var emptyHint = detBody && detBody.querySelector(".nsx-hint");
    if (emptyHint) folds.setAttribute("data-empty", emptyHint.textContent.trim());
    function updateEmpty() { folds.classList.toggle("nsx-empty", !foldList().some(function (f) { return !f.hidden && !f.classList.contains("nsx-tdocked"); })); }
    function foldByKey(k) { return folds.querySelector('details[data-fold="' + k + '"]'); }
    if (tdock) {
      tdock.addEventListener("click", function (ev) {
        var b = ev.target.closest(".nsx-tab");
        if (!b) return;
        var f = foldByKey(b.getAttribute("data-fold"));
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
          saveTitleDock();
          return;
        }
        if (ev.key !== "ArrowDown") return;
        ev.preventDefault();
        undockTitle(foldByKey(b.getAttribute("data-fold")), folds.firstChild);
      });
      // Reiter zurück in die Mitte ziehen
      tdock.addEventListener("dragstart", function (ev) {
        var b = ev.target.closest && ev.target.closest(".nsx-tab");
        if (!b) return;
        dragging = foldByKey(b.getAttribute("data-fold"));
        dragging._fromTitle = true;
        dragging._dropped = false;
        root.classList.add("nsx-dnd");
        setPop(null);
        ev.dataTransfer.effectAllowed = "move";
        try { ev.dataTransfer.setData("text/plain", b.getAttribute("data-fold")); } catch (e) { /* alte Browser */ }
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
        if (dragging && dragging._fromTitle) { ev.preventDefault(); dragging._dropped = false; return; }
        if (!dragging || !canTitleDock(dragging)) return;
        ev.preventDefault();
        dragging._dropped = true;
        dockTitle(dragging);
      });
      document.addEventListener("keydown", function (ev) { if (ev.key === "Escape" && popFold) setPop(null); });
      document.addEventListener("click", function (ev) {
        if (popFold && !popFold.contains(ev.target) && !tdock.contains(ev.target)) setPop(null);
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
    foldList().forEach(function (f) { if (canTitleDock(f)) addButton(f, "nsx-backbtn", ICON_DOCK, labels.tundock); });
    guideStats();
    window.addEventListener("hashchange", guideStats);

    // ---- Gruppierung der Gliederung
    function setBy(mode) {
      var btn = outline.querySelector('.nsx-by button[data-by="' + mode + '"]');
      if (!btn) return false;
      outline.querySelectorAll(".nsx-by button").forEach(function (b) { b.setAttribute("aria-pressed", String(b === btn)); });
      outline.querySelectorAll(".nsx-ol").forEach(function (o) { o.hidden = o.getAttribute("data-by") !== mode; });
      revealSelected();
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
      });
      split.addEventListener("dblclick", function () { root.style.removeProperty("--nsx-aside-w"); save(W_KEY, null); });
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
      var desc = main ? main.querySelector(":scope > .desc") : (recs[0] && recs[0].querySelector(".desc"));
      if (!desc) desc = r.querySelector(".nsx-desc");
      if (desc) {
        var d = desc.cloneNode(true);
        d.removeAttribute("id");
        d.className = "nsx-idesc";
        relBox.appendChild(d);
      }
      // Signatur (Funktionen, Typen, Enumerationen)
      if (!isClass) {
        var sigs = recs.map(function (rec) { return rec.querySelector("pre.syntax"); }).filter(Boolean);
        if (sigs.length) {
          var ss = section(labels.sig, sigs.length > 1 ? sigs.length : 0);
          sigs.forEach(function (sg) { var c = sg.cloneNode(true); c.removeAttribute("id"); c.className = "nsx-isig"; ss.appendChild(c); });
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
          if (code && go) fl.insertAdjacentHTML("beforeend", '<li class="nsx-ifn"><a class="nsx-fname" href="' + esc(go.getAttribute("href")) + '">' + esc(fname) + '</a><code class="nsx-isig">' + code.innerHTML + "</code></li>");
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
    function setTitle(name, info) {
      if (!detTitle) return;
      var r = rows[name];
      info = info || {};
      var k = info.kind || (r.querySelector(".nsx-nm > .kind") || {}).textContent || "";
      var href = info.href || "";
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
      dTab.innerHTML = '<span class="nsx-tab-h">' + label + '</span><span class="nsx-stats">' + statsHtml(statsRoot || dPanel) + "</span>";
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
    function markAi() {
      root.querySelectorAll(".nsx-ai").forEach(function (s) {
        s.setAttribute("aria-pressed", String(!!selected && s.getAttribute("data-ai") === selected && aiOpen()));
      });
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
        detBody.style.minHeight = "";
      }
      function done() {
        if (my !== token) return;
        if (opts.ai && dPanel) { setDetailAi(true); toDetail(); return; }
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
    // opts.origin: "map" (Themenkarte), "side" (Gliederung, Inspektor), "nav" (Anker von außen)
    // opts.from: angeklicktes Element; opts.ai / opts.anchor: Sprungziel in der Detailansicht
    function select(name, opts) {
      if (!rows[name]) return;
      opts = opts || {};
      if (opts.from && popFold && popFold.contains(opts.from)) setPop(null);   // Auswahl im Panel schließt es
      var origin = opts.origin || "side", was = detailVisible();
      var jump = !!(opts.ai || opts.anchor);
      var go = !jump && (origin === "nav" || !was || (origin !== "map" && headerAbove()));
      anchorEl = opts.from && folds.contains(opts.from) ? opts.from : firstVisibleFold();
      if (anchorEl === detFold) anchorEl = null;
      selected = name;
      selAnchor = opts.anchor && recOwner[opts.anchor] === name ? opts.anchor : (rows[name].id || "");
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
        var an = ai.getAttribute("data-ai");
        if (an === selected && dTab) {
          var op = !aiOpen();
          setDetailAi(op);
          if (op) toDetail();
        } else select(an, { ai: true });
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
        else if (hb.classList.contains("nsx-backbtn")) undockTitle(hf, folds.firstChild);
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
        // wieder (Aufnahme 12:01), sonst springt er zur Detailansicht
        if (n === selected) { if (aiOpen()) setDetailAi(false); else toDetail(); }
        else select(n, { origin: a.classList.contains("nsx-chip") ? "map" : "side", from: a });
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
        if (row && rows[row.getAttribute("data-n")]) { ev.preventDefault(); select(row.getAttribute("data-n"), { from: link }); }
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
    root.querySelectorAll(".nsx-ai").forEach(function (s) { s.setAttribute("title", labels.ai || ""); s.setAttribute("aria-label", labels.ai || ""); });
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
    if (detFold) {
      addButton(detFold, "nsx-closebtn", ICON_CLOSE, labels.close);
      detFold.hidden = true;
    }
    updateEmpty();
    // Beim Öffnen sind User Guide (bzw. Cluster Guide), Karte und Klassendiagramm immer in
    // der Titelleiste (Klassenseiten: Mitgliederkarte, User Guide, Klassendiagramm). Gemerkt
    // wird nur die Reihenfolge der Reiter: Ein in einer früheren Sitzung oder auf einer
    // anderen Seite gelöster Reiter fehlt sonst dauerhaft (Aufnahme 12:02). Zusätzlich
    // angedockte Folds (Implementer's Guide) bleiben angedockt.
    var tdDefault = isCls ? ["map", "guide", "uml"] : ["guide", "map", "uml"];
    var td = (load(tdockKey) || "").split(",").filter(function (k) { return k && foldByKey(k); });
    tdDefault.forEach(function (k) { if (td.indexOf(k) < 0) td.push(k); });
    td.forEach(function (k) { dockTitle(foldByKey(k)); });

    // Klick auf eine leere Fläche löst die Auswahl; der Inspektor folgt dann wieder
    // dem Mauszeiger. Lesebereiche (Detailansicht, Guide-Text, Inspektor) und
    // Bedienelemente zählen nicht als leer.
    function release() {
      if (!selected) return;
      selected = null;
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
        ".nsx-detbody, .nsx-rel, details[data-fold=guide] > :not(summary), .nsx-tdock, .nsx-og")) return;
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
    function badge(rel, cls, tip) {
      return '<span class="nsx-hb ' + cls + '" role="button" tabindex="0" data-rel="' + esc(rel) + '" title="' + esc(tip + " · " + (labels.hsel || "")) + '">' + esc(rel) + "</span>";
    }
    function renderHistory() {
      var cur = currentRelease() || latestRel(), ck = relKey(cur);
      root.querySelectorAll("a.nsx-oi-h").forEach(function (a) {
        var ch = words(a, "data-changes").sort(function (x, y) { return relKey(x) - relKey(y); });
        var prev = ch.filter(function (r) { return relKey(r) <= ck; }).pop();
        var next = ch.filter(function (r) { return relKey(r) > ck; })[0];
        a.querySelectorAll(".nsx-hb").forEach(function (x) { x.remove(); });
        var n = a.querySelector(".nsx-oi-n");
        if (prev) n.insertAdjacentHTML("beforebegin", badge(prev, "nsx-hb-prev", labels.hprev || ""));
        if (next) n.insertAdjacentHTML("afterend", badge(next, "nsx-hb-next", labels.hnext || ""));
      });
      root.querySelectorAll('.nsx-ol[data-by="since"] .nsx-og').forEach(function (g) {
        var t = g.textContent.trim();
        if (relKey(t)) { g.setAttribute("data-rel", t); g.classList.add("nsx-hg"); g.classList.toggle("cur", t === cur); }
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
    root.addEventListener("mouseover", function (ev) {
      var h = ev.target.closest && ev.target.closest(".nsx-hb, .nsx-hg");
      relHighlight(h ? h.getAttribute("data-rel") : null);
    });
    root.addEventListener("click", function (ev) {
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
    document.querySelectorAll("section.nsx").forEach(init);
    if (window.MutationObserver && any) {
      var dens = document.documentElement.getAttribute("data-density");
      new MutationObserver(function () {
        if (document.documentElement.getAttribute("data-density") !== dens) location.reload();
      }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-density"] });
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
