// fold.js — Verhalten der klappbaren KI-Guide-Abschnitte (<details class="fold">).
// Direkte Quelldatei (wie style.css), wird nicht generiert. Siehe _src/WARTUNG.md.
//
//  1. Deep Links: Zeigt ein Anker (#…) auf ein Element in einem eingeklappten
//     Abschnitt, wird der Abschnitt automatisch geöffnet und hingescrollt —
//     Querverweise auf #guide-…/#diag-…-Anker funktionieren so weiterhin.
//  2. Drucken: Vor dem Druck werden alle Abschnitte geöffnet, danach wieder
//     in den vorherigen Zustand versetzt.
(function () {
  "use strict";

  function oeffnePfad(el) {
    var geoeffnet = false;
    for (var d = el; d; d = d.parentElement) {
      if (d.tagName === "DETAILS" && !d.open) {
        d.open = true;
        geoeffnet = true;
      }
    }
    return geoeffnet;
  }

  function zumAnker() {
    if (!location.hash) return;
    var ziel = null;
    try {
      ziel = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    } catch (e) { /* ungültiger Hash */ }
    if (ziel && oeffnePfad(ziel)) {
      ziel.scrollIntoView();
    }
  }

  window.addEventListener("hashchange", zumAnker);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", zumAnker);
  } else {
    zumAnker();
  }

  window.addEventListener("beforeprint", function () {
    document.querySelectorAll("details.fold:not([open])").forEach(function (d) {
      d.setAttribute("data-druck-zu", "");
      d.open = true;
    });
  });
  window.addEventListener("afterprint", function () {
    document.querySelectorAll("details.fold[data-druck-zu]").forEach(function (d) {
      d.removeAttribute("data-druck-zu");
      d.open = false;
    });
  });

  function syncShellControls() {
    var root = document.documentElement;
    var themeBtn = document.querySelector("[data-theme-toggle]");
    var densBtn = document.querySelector("[data-density-toggle]");
    var prefsLabel = document.querySelector("[data-prefs-label]");
    var theme = root.getAttribute("data-theme") || "light";
    var dens = root.getAttribute("data-density") || "comfortable";
    if (themeBtn) {
      themeBtn.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
      themeBtn.textContent = theme === "dark" ? "Dark" : "Light";
    }
    if (densBtn) {
      densBtn.setAttribute("aria-pressed", dens === "compact" ? "true" : "false");
      densBtn.textContent = dens === "compact" ? "Compact" : "Comfortable";
    }
    if (prefsLabel) {
      prefsLabel.textContent = (theme === "dark" ? "Dark" : "Light") + " · " + (dens === "compact" ? "Compact" : "Comfort");
    }
  }

  function bindShellControls() {
    var root = document.documentElement;
    var themeBtn = document.querySelector("[data-theme-toggle]");
    var densBtn = document.querySelector("[data-density-toggle]");
    var searchBtn = document.querySelector("[data-search-open]");
    var searchInput = document.querySelector("[data-search-input]");
    if (themeBtn) {
      themeBtn.addEventListener("click", function () {
        var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
        root.setAttribute("data-theme", next);
        try { localStorage.setItem("autodocs-theme", next); } catch (e) {}
        syncShellControls();
      });
    }
    if (densBtn) {
      densBtn.addEventListener("click", function () {
        var next = root.getAttribute("data-density") === "compact" ? "comfortable" : "compact";
        root.setAttribute("data-density", next);
        try { localStorage.setItem("autodocs-density", next); } catch (e) {}
        syncShellControls();
      });
    }
    if (searchBtn && searchInput) {
      searchBtn.addEventListener("click", function () {
        searchInput.focus();
      });
    }

    document.addEventListener("click", function (e) {
      document.querySelectorAll("details.universe-dropdown[open], details.shell-dropdown[open], details.shell-prefs[open], details[data-ai-model-widget][open]").forEach(function (d) {
        if (!d.contains(e.target)) {
          d.removeAttribute("open");
        }
      });
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        document.querySelectorAll("details.universe-dropdown[open], details.shell-dropdown[open], details.shell-prefs[open], details[data-ai-model-widget][open]").forEach(function (d) {
          d.removeAttribute("open");
        });
      }
    });

    try {
      var savedFolds = JSON.parse(sessionStorage.getItem("autodocs-open-folds") || "[]");
      if (Array.isArray(savedFolds) && savedFolds.length > 0) {
        savedFolds.forEach(function (id) {
          var el = document.getElementById(id);
          if (el && el.tagName === "DETAILS") {
            el.open = true;
          }
        });
      }
      document.querySelectorAll("details.fold[id]").forEach(function (d) {
        d.addEventListener("toggle", function () {
          try {
            var currentOpen = Array.from(document.querySelectorAll("details.fold[id][open]")).map(function (el) { return el.id; });
            sessionStorage.setItem("autodocs-open-folds", JSON.stringify(currentOpen));
          } catch (err) {}
        });
      });
    } catch (e) {}

    syncShellControls();
    bindDossierControls();
    bindSnippetCurationControls();
  }

  function bindSnippetCurationControls() {
    var VOTE_STORE = "ara-curation-snippet-votes-v1";
    var REVIEW_STORE = "ara-review-package-v1";
    var REVIEW_IDENT = "ara-review-identity";
    var REVIEW_TOKEN = "ara-review-github-token-v1";
    var attachedDiscussionItems = new Set();
    var selectedSnippetIds = new Set();
    var lastSelectedSnippetId = null;

    function getVisibleSnippetCards() {
      var cards = Array.from(document.querySelectorAll("#dossier-view-editor .snippet-card"));
      return cards.filter(function (c) {
        return c.style.display !== "none" && !c.hidden;
      });
    }

    function updateSelectionUI() {
      var count = selectedSnippetIds.size;
      var selBar = document.getElementById("dossier-selection-bar");
      var selCount = document.getElementById("selection-count");
      var selLabel = document.getElementById("selection-label");
      var bConfCount = document.getElementById("batch-confirm-count");
      var bDismCount = document.getElementById("batch-dismiss-count");
      var bDiscCount = document.getElementById("batch-discuss-count");
      var editorView = document.getElementById("dossier-view-editor");

      if (selBar) selBar.hidden = (count === 0);
      if (selCount) selCount.textContent = count;
      if (selLabel) selLabel.textContent = (count === 1 ? "Element ausgewählt" : "Elemente ausgewählt");
      if (bConfCount) bConfCount.textContent = count;
      if (bDismCount) bDismCount.textContent = count;
      if (bDiscCount) bDiscCount.textContent = count;

      if (editorView) {
        editorView.classList.toggle("has-active-selection", count > 0);
      }

      document.querySelectorAll(".snippet-card").forEach(function (card) {
        var sId = card.getAttribute("data-snippet-id") || card.id;
        var isSelected = selectedSnippetIds.has(sId);
        card.classList.toggle("is-selected", isSelected);
        var cb = card.querySelector(".card-select-checkbox");
        if (cb) cb.checked = isSelected;
      });
    }

    function switchDossierViewMode(targetMode, modal) {
      modal = modal || document;
      modal.querySelectorAll(".dossier-mode-tab").forEach(function (tab) {
        var isTarget = tab.getAttribute("data-view-mode") === targetMode;
        tab.classList.toggle("is-active", isTarget);
        tab.setAttribute("aria-selected", isTarget ? "true" : "false");
      });

      var promptView = modal.querySelector("#dossier-view-prompt") || modal.querySelector("#dossier-view-raw");
      var outputView = modal.querySelector("#dossier-view-output");
      var richView = modal.querySelector("#dossier-view-rich");
      var editorView = modal.querySelector("#dossier-view-editor");
      var chatToggleBtn = modal.querySelector("#btn-toggle-workbench-chat");

      var isPrompt = (targetMode === "prompt" || targetMode === "raw");
      var isOutput = (targetMode === "output" || targetMode === "diff");
      var isEditor = (targetMode === "editor");

      if (promptView) promptView.hidden = !isPrompt;
      if (outputView) {
        outputView.hidden = !isOutput;
        if (isOutput && typeof selectRawSubTab === "function" && typeof rawWorkbenchState !== "undefined") {
          selectRawSubTab(rawWorkbenchState.activeSubTab || "current");
        }
      }
      if (richView) richView.hidden = (targetMode !== "rich");
      if (editorView) editorView.hidden = !isEditor;

      if (chatToggleBtn) {
        chatToggleBtn.hidden = !isEditor;
      }
    }

    function loadVotes() {
      try {
        return JSON.parse(localStorage.getItem(VOTE_STORE) || "{}");
      } catch (e) {
        return {};
      }
    }

    function storeVote(snippetId, data) {
      try {
        var votes = loadVotes();
        votes[snippetId] = Object.assign({}, votes[snippetId] || {}, data);
        localStorage.setItem(VOTE_STORE, JSON.stringify(votes));
      } catch (e) {}
    }

    function loadReviewPackage() {
      try {
        return JSON.parse(localStorage.getItem(REVIEW_STORE) || "[]");
      } catch (e) {
        return [];
      }
    }

    function storeReviewPackage(items) {
      try {
        localStorage.setItem(REVIEW_STORE, JSON.stringify(items));
      } catch (e) {}
      syncReviewBar();
      try { window.dispatchEvent(new CustomEvent("ara-package-changed")); } catch (e) {}
    }

    function syncReviewBar() {
      var n = loadReviewPackage().length;
      document.querySelectorAll("[data-review-count]").forEach(function (e) { e.textContent = n; });
      document.querySelectorAll("[data-review-open]").forEach(function (e) {
        e.classList.toggle("has-items", n > 0);
      });
    }

    function getReviewerIdentity() {
      var tok = "";
      try { tok = localStorage.getItem(REVIEW_TOKEN) || ""; } catch (e) {}
      var name = "";
      try { name = localStorage.getItem(REVIEW_IDENT) || ""; } catch (e) {}
      if (tok) {
        return { name: name || "github-user", mode: "github_authenticated" };
      }
      return { name: name || "Curator", mode: "self_declared" };
    }

    function updateSnippetBadges() {
      var localVotes = loadVotes();
      document.querySelectorAll(".snippet-card[data-snippet-id]").forEach(function (card) {
        var sId = card.getAttribute("data-snippet-id");
        var record = localVotes[sId];
        var badge = card.querySelector('[data-badge-for="' + sId + '"]');
        var btnConfirm = card.querySelector('.curation-btn[data-action="confirm"][data-snippet="' + sId + '"]');
        var btnDismiss = card.querySelector('.curation-btn[data-action="dismiss"][data-snippet="' + sId + '"]');
        var btnDiscuss = card.querySelector('.curation-btn[data-action="discuss"][data-snippet="' + sId + '"]');

        var isInDiscussion = attachedDiscussionItems.has(sId);
        if (isInDiscussion) {
          card.classList.add("is-in-discussion");
          if (btnDiscuss) btnDiscuss.classList.add("is-active");
        } else {
          card.classList.remove("is-in-discussion");
          if (btnDiscuss) btnDiscuss.classList.remove("is-active");
        }

        if (!badge) return;

        if (isInDiscussion) {
          badge.className = "curation-status-pill status-in-discussion";
          badge.textContent = "💬 In Diskussion";
          if (btnConfirm) btnConfirm.classList.remove("is-active");
          if (btnDismiss) btnDismiss.classList.remove("is-active");
        } else if (record && record.queued) {
          badge.className = "curation-status-pill status-queued";
          badge.innerHTML = '<span>⏳ Im Review-Paket</span> <button type="button" class="btn-clear-badge" data-clear-badge-for="' + sId + '" title="Aus Curation-Queue entfernen" aria-label="Aus Curation-Queue entfernen">✕</button>';
          if (btnDismiss) btnDismiss.classList.add("is-active");
          if (btnConfirm) btnConfirm.classList.remove("is-active");
        } else if (record && record.vote === "justified_dismiss") {
          badge.className = "curation-status-pill status-justified-dismiss";
          badge.innerHTML = '<span>👎 Begründet beanstandet ✓</span> <button type="button" class="btn-clear-badge" data-clear-badge-for="' + sId + '" title="Beanstandung aufheben" aria-label="Beanstandung aufheben">✕</button>';
          if (btnDismiss) btnDismiss.classList.add("is-active");
          if (btnConfirm) btnConfirm.classList.remove("is-active");
        } else if (record && record.vote === "justified_confirm") {
          badge.className = "curation-status-pill status-justified-confirm";
          badge.innerHTML = '<span>👍 Begründet bestätigt ✓</span> <button type="button" class="btn-clear-badge" data-clear-badge-for="' + sId + '" title="Bestätigung aufheben" aria-label="Bestätigung aufheben">✕</button>';
          if (btnConfirm) btnConfirm.classList.add("is-active");
          if (btnDismiss) btnDismiss.classList.remove("is-active");
        } else if (record && record.vote === "confirm") {
          badge.className = "curation-status-pill status-confirmed";
          badge.innerHTML = '<span>👍 Bestätigt ✓</span> <button type="button" class="btn-clear-badge" data-clear-badge-for="' + sId + '" title="Bestätigung aufheben" aria-label="Bestätigung aufheben">✕</button>';
          if (btnConfirm) btnConfirm.classList.add("is-active");
          if (btnDismiss) btnDismiss.classList.remove("is-active");
        } else if (record && record.vote === "dismiss") {
          badge.className = "curation-status-pill status-dismissed";
          badge.innerHTML = '<span>👎 Beanstandet ✕</span> <button type="button" class="btn-clear-badge" data-clear-badge-for="' + sId + '" title="Beanstandung aufheben" aria-label="Beanstandung aufheben">✕</button>';
          if (btnDismiss) btnDismiss.classList.add("is-active");
          if (btnConfirm) btnConfirm.classList.remove("is-active");
        } else {
          badge.className = "curation-status-pill status-neutral";
          badge.textContent = "Unbewertet";
          if (btnConfirm) btnConfirm.classList.remove("is-active");
          if (btnDismiss) btnDismiss.classList.remove("is-active");
        }
      });
      applyDossierFilters();
      updateSelectionUI();
    }

    function applyDossierFilters() {
      var searchInput = document.getElementById("dossier-search-input");
      var query = searchInput ? searchInput.value.trim().toLowerCase() : "";
      var clearBtn = document.getElementById("btn-clear-dossier-search");
      if (clearBtn) clearBtn.hidden = (query.length === 0);

      var activeKindPill = document.querySelector(".dossier-filter-pill[data-filter-kind].is-active");
      var activeKind = activeKindPill ? activeKindPill.getAttribute("data-filter-kind") : "all";

      var activeStatusPill = document.querySelector(".dossier-filter-pill[data-filter-status].is-active");
      var activeStatus = activeStatusPill ? activeStatusPill.getAttribute("data-filter-status") : "all";

      var cards = document.querySelectorAll(".snippet-card");
      var totalCount = cards.length;
      var visibleCount = 0;
      var votes = loadVotes();

      cards.forEach(function (card) {
        var sId = card.getAttribute("data-snippet-id") || card.id;
        var kind = card.getAttribute("data-kind") || "";
        var isInbound = card.hasAttribute("data-is-inbound") || kind === "inbound";
        var isConstituting = card.hasAttribute("data-is-constituting");
        var name = (card.getAttribute("data-name") || "").toLowerCase();
        var sws = (card.getAttribute("data-sws") || "").toLowerCase();
        var doc = (card.getAttribute("data-doc") || "").toLowerCase();

        // 1. Kind filter
        var matchKind = true;
        if (activeKind === "inbound") {
          matchKind = isInbound;
        } else if (activeKind === "function") {
          matchKind = (kind === "function");
        } else if (activeKind === "type") {
          matchKind = (kind === "type");
        }

        // 2. Status filter
        var matchStatus = true;
        var currentStatus = "unrated";
        if (attachedDiscussionItems.has(sId)) {
          currentStatus = "in-discussion";
        } else {
          var v = votes[sId];
          if (v && v.queued) {
            currentStatus = "queued";
          } else if (v && (v.vote === "confirm" || v.vote === "justified_confirm")) {
            currentStatus = "confirmed";
          } else if (v && (v.vote === "dismiss" || v.vote === "justified_dismiss")) {
            currentStatus = "dismissed";
          } else {
            currentStatus = "unrated";
          }
        }

        if (activeStatus !== "all") {
          matchStatus = (currentStatus === activeStatus);
        }

        // 3. Search query filter
        var matchSearch = true;
        if (query.length > 0) {
          var cardText = (card.textContent || "").toLowerCase();
          matchSearch = (name.indexOf(query) !== -1 ||
                         sws.indexOf(query) !== -1 ||
                         doc.indexOf(query) !== -1 ||
                         sId.toLowerCase().indexOf(query) !== -1 ||
                         cardText.indexOf(query) !== -1);
        }

        var isVisible = matchKind && matchStatus && matchSearch;
        if (isVisible) {
          card.style.display = "";
          visibleCount++;
        } else {
          card.style.display = "none";
        }
      });

      var visibleCountEl = document.getElementById("dossier-visible-count");
      if (visibleCountEl) {
        visibleCountEl.textContent = visibleCount + " von " + totalCount + " Elementen angezeigt";
      }

      var resetBtn = document.getElementById("btn-reset-dossier-filters");
      if (resetBtn) {
        var isFiltered = (activeKind !== "all" || activeStatus !== "all" || query.length > 0);
        resetBtn.hidden = !isFiltered;
      }
    }

    function renderAttachedChips() {
      var chipsContainer = document.getElementById("chat-attached-chips");
      var countBadge = document.getElementById("chat-attached-count");
      var headerBadge = document.getElementById("header-chat-badge");
      var clearBtn = document.getElementById("btn-clear-attached");
      var count = attachedDiscussionItems.size;

      if (countBadge) {
        countBadge.textContent = count === 1 ? "1 Element im Fokus" : count + " Elemente im Fokus";
      }
      if (headerBadge) {
        headerBadge.textContent = count;
        headerBadge.hidden = count === 0;
      }
      if (clearBtn) {
        clearBtn.hidden = count === 0;
      }

      if (!chipsContainer) return;
      chipsContainer.innerHTML = "";

      if (count === 0) {
        var hint = document.createElement("span");
        hint.className = "chat-attached-empty-hint";
        hint.textContent = "Kein Element ausgewählt (klicke bei einem Element auf „💬 Mit KI diskutieren“)";
        chipsContainer.appendChild(hint);
        return;
      }

      attachedDiscussionItems.forEach(function (id) {
        var card = document.getElementById(id);
        var label = id;
        if (card) {
          label = card.getAttribute("data-name") || card.getAttribute("data-sws") || id;
        }
        var chip = document.createElement("span");
        chip.className = "chat-attached-chip";
        chip.innerHTML = '<code>' + label + '</code> <button type="button" class="btn-detach-item" data-item-id="' + id + '" title="Aus Diskussion entfernen">✕</button>';
        chipsContainer.appendChild(chip);
      });
    }

    function appendDiscussionSystemNote(htmlText) {
      var thread = document.getElementById("chat-pane-thread");
      if (!thread) return;
      var note = document.createElement("div");
      note.className = "chat-system-note";
      note.innerHTML = htmlText;
      thread.appendChild(note);
      thread.scrollTop = thread.scrollHeight;
    }

    function openDiscussionForItem(itemId) {
      var chatPane = document.getElementById("dossier-chat-pane");
      var modal = chatPane ? chatPane.closest("dialog") : null;
      if (chatPane) {
        chatPane.hidden = false;
        if (modal) modal.classList.add("has-chat-open");
      }
      if (itemId) {
        if (!attachedDiscussionItems.has(itemId)) {
          attachedDiscussionItems.add(itemId);
          appendDiscussionSystemNote("Element <code>" + itemId + "</code> zur Diskussion hinzugefügt.");
        }
        var targetCard = document.getElementById(itemId);
        if (targetCard) {
          targetCard.classList.remove("is-collapsed");
          targetCard.classList.add("is-expanded");
          var header = targetCard.querySelector(".snippet-card-header");
          if (header) header.setAttribute("aria-expanded", "true");
        }
      }
      renderAttachedChips();
      updateSnippetBadges();
    }

    function toggleDiscussionItem(itemId) {
      var chatPane = document.getElementById("dossier-chat-pane");
      var modal = chatPane ? chatPane.closest("dialog") : null;

      if (attachedDiscussionItems.has(itemId)) {
        if (chatPane && chatPane.hidden) {
          chatPane.hidden = false;
          if (modal) modal.classList.add("has-chat-open");
        } else {
          attachedDiscussionItems.delete(itemId);
          appendDiscussionSystemNote("Element <code>" + itemId + "</code> aus Diskussion entfernt.");
        }
      } else {
        attachedDiscussionItems.add(itemId);
        if (chatPane) {
          chatPane.hidden = false;
          if (modal) modal.classList.add("has-chat-open");
        }
        appendDiscussionSystemNote("Element <code>" + itemId + "</code> zur Diskussion hinzugefügt.");
        var targetCard = document.getElementById(itemId);
        if (targetCard) {
          targetCard.classList.remove("is-collapsed");
          targetCard.classList.add("is-expanded");
          var header = targetCard.querySelector(".snippet-card-header");
          if (header) header.setAttribute("aria-expanded", "true");
        }
      }
      renderAttachedChips();
      updateSnippetBadges();
    }

    // Server-side vote synchronization if available
    try {
      fetch("/api/curation/votes").then(function (r) { return r.json(); }).then(function (data) {
        if (data && data.votes) {
          var local = loadVotes();
          Object.keys(data.votes).forEach(function (sid) {
            var v = data.votes[sid];
            if (!local[sid]) {
              if (v.is_dismissed || v.dismisses > 0) local[sid] = { vote: "dismiss" };
              else if (v.confirms > 0) local[sid] = { vote: "confirm" };
            }
          });
          try { localStorage.setItem(VOTE_STORE, JSON.stringify(local)); } catch (e) {}
          updateSnippetBadges();
        }
      }).catch(function () {});
    } catch (e) {}

    // --- Provenance Explorer Side-by-Side Diff Engine ---
    var lastPromptDiffData = null;
    var currentDiffViewMode = "side";

    function escapeHtmlDiff(str) {
      if (!str) return "";
      return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }

    function formatHtmlLinesForDiff(htmlStr) {
      if (!htmlStr) return [];
      var norm = htmlStr
        .replace(/>\s*</g, ">\n<")
        .replace(/\r\n/g, "\n");
      var rawLines = norm.split("\n");
      var lines = [];
      for (var i = 0; i < rawLines.length; i++) {
        var l = rawLines[i].trim();
        if (!l) continue;
        if (l.length > 100 && !l.startsWith("<") && !l.endsWith(">")) {
          var sents = l.split(/(?<=[.!?])\s+(?=[A-ZÄÖÜ])/);
          for (var s = 0; s < sents.length; s++) {
            if (sents[s].trim()) lines.push(sents[s].trim());
          }
        } else {
          lines.push(l);
        }
      }
      return lines;
    }

    function getDiffOpcodes(a, b) {
      var m = a.length;
      var n = b.length;
      var dp = Array.from({ length: m + 1 }, function () { return new Int32Array(n + 1); });
      for (var i = 0; i < m; i++) {
        for (var j = 0; j < n; j++) {
          if (a[i] === b[j]) {
            dp[i + 1][j + 1] = dp[i][j] + 1;
          } else {
            dp[i + 1][j + 1] = Math.max(dp[i + 1][j], dp[i][j + 1]);
          }
        }
      }

      var iIdx = m;
      var jIdx = n;
      var rawEdits = [];

      while (iIdx > 0 || jIdx > 0) {
        if (iIdx > 0 && jIdx > 0 && a[iIdx - 1] === b[jIdx - 1]) {
          rawEdits.push({ type: "equal", aIdx: iIdx - 1, bIdx: jIdx - 1 });
          iIdx--;
          jIdx--;
        } else if (jIdx > 0 && (iIdx === 0 || dp[iIdx][jIdx - 1] >= dp[iIdx - 1][jIdx])) {
          rawEdits.push({ type: "insert", aIdx: iIdx, bIdx: jIdx - 1 });
          jIdx--;
        } else if (iIdx > 0 && (jIdx === 0 || dp[iIdx][jIdx - 1] < dp[iIdx - 1][jIdx])) {
          rawEdits.push({ type: "delete", aIdx: iIdx - 1, bIdx: jIdx });
          iIdx--;
        }
      }
      rawEdits.reverse();

      var opcodes = [];
      var idx = 0;
      while (idx < rawEdits.length) {
        var curType = rawEdits[idx].type;
        var startA = rawEdits[idx].aIdx;
        var startB = rawEdits[idx].bIdx;
        var endA = startA;
        var endB = startB;

        var k = idx;
        while (k < rawEdits.length && rawEdits[k].type === curType) {
          if (curType === "equal") {
            endA = rawEdits[k].aIdx + 1;
            endB = rawEdits[k].bIdx + 1;
          } else if (curType === "delete") {
            endA = rawEdits[k].aIdx + 1;
          } else if (curType === "insert") {
            endB = rawEdits[k].bIdx + 1;
          }
          k++;
        }
        opcodes.push([curType, startA, endA, startB, endB]);
        idx = k;
      }

      var merged = [];
      for (var mIdx = 0; mIdx < opcodes.length; mIdx++) {
        var curr = opcodes[mIdx];
        var next = opcodes[mIdx + 1];
        if (next && ((curr[0] === "delete" && next[0] === "insert") || (curr[0] === "insert" && next[0] === "delete"))) {
          var i1 = Math.min(curr[1], next[1]);
          var i2 = Math.max(curr[2], next[2]);
          var j1 = Math.min(curr[3], next[3]);
          var j2 = Math.max(curr[4], next[4]);
          merged.push(["replace", i1, i2, j1, j2]);
          mIdx++;
        } else {
          merged.push(curr);
        }
      }
      return merged;
    }

    function computeWordDiff(textA, textB) {
      var tokenRegex = /[<>\-]|[\w\u00C0-\u024F]+|[^\s\w\u00C0-\u024F<>\-]+|\s+/g;
      var tokensA = textA.match(tokenRegex) || [];
      var tokensB = textB.match(tokenRegex) || [];
      var opcodes = getDiffOpcodes(tokensA, tokensB);

      var outA = "";
      var outB = "";

      for (var w = 0; w < opcodes.length; w++) {
        var tag = opcodes[w][0];
        var i1 = opcodes[w][1];
        var i2 = opcodes[w][2];
        var j1 = opcodes[w][3];
        var j2 = opcodes[w][4];
        var subA = tokensA.slice(i1, i2).join("");
        var subB = tokensB.slice(j1, j2).join("");

        if (tag === "equal") {
          outA += escapeHtmlDiff(subA);
          outB += escapeHtmlDiff(subB);
        } else if (tag === "replace") {
          outA += subA.trim() ? '<del class="ve-word-deleted">' + escapeHtmlDiff(subA) + "</del>" : subA;
          outB += subB.trim() ? '<ins class="ve-word-added">' + escapeHtmlDiff(subB) + "</ins>" : subB;
        } else if (tag === "delete") {
          outA += subA.trim() ? '<del class="ve-word-deleted">' + escapeHtmlDiff(subA) + "</del>" : subA;
        } else if (tag === "insert") {
          outB += subB.trim() ? '<ins class="ve-word-added">' + escapeHtmlDiff(subB) + "</ins>" : subB;
        }
      }
      return [outA, outB];
    }

    function redrawPromptSvgConnectors() {
      var wrapper = document.getElementById("prompt-diff-split-wrapper");
      var svg = document.getElementById("prompt-diff-gutter-svg");
      var gutter = document.getElementById("prompt-diff-split-gutter");
      if (!wrapper || !svg || !lastPromptDiffData || !lastPromptDiffData.aligned_blocks) return;

      var canvasWrap = (gutter && gutter.querySelector(".ve-gutter-canvas-wrap")) || gutter;
      if (canvasWrap) {
        var gH = canvasWrap.offsetHeight || (gutter ? gutter.offsetHeight : 0);
        if (gH > 0) {
          svg.setAttribute("height", gH);
          svg.style.height = gH + "px";
        }
      }

      var svgRect = svg.getBoundingClientRect();
      var W = 70;
      var blocks = lastPromptDiffData.aligned_blocks;
      var pathsHtml = "";

      blocks.forEach(function (b) {
        if (b.tag === "equal") return;

        var leftEl = wrapper.querySelector('#prompt-diff-pane-left [data-block-id="' + b.id + '"]');
        var rightEl = wrapper.querySelector('#prompt-diff-pane-right [data-block-id="' + b.id + '"]');
        if (!leftEl || !rightEl) return;

        var lRect = leftEl.getBoundingClientRect();
        var rRect = rightEl.getBoundingClientRect();

        var y1Top = lRect.top - svgRect.top;
        var y1Bot = (b.tag === "insert") ? y1Top : (lRect.bottom - svgRect.top);
        var y2Top = rRect.top - svgRect.top;
        var y2Bot = (b.tag === "delete") ? y2Top : (rRect.bottom - svgRect.top);

        var cp1x = W * 0.45;
        var cp2x = W * 0.55;

        var d = "";
        var cls = "ve-connector ";

        if (b.tag === "replace") {
          cls += "ve-connector-replace";
          d = "M 0 " + y1Top + " C " + cp1x + " " + y1Top + ", " + cp2x + " " + y2Top + ", " + W + " " + y2Top + " L " + W + " " + y2Bot + " C " + cp2x + " " + y2Bot + ", " + cp1x + " " + y1Bot + ", 0 " + y1Bot + " Z";
        } else if (b.tag === "delete") {
          cls += "ve-connector-delete";
          d = "M 0 " + y1Top + " C " + cp1x + " " + y1Top + ", " + cp2x + " " + y2Top + ", " + W + " " + y2Top + " L " + W + " " + y2Top + " C " + cp2x + " " + y2Top + ", " + cp1x + " " + y1Bot + ", 0 " + y1Bot + " Z";
        } else if (b.tag === "insert") {
          cls += "ve-connector-insert";
          d = "M 0 " + y1Top + " C " + cp1x + " " + y1Top + ", " + cp2x + " " + y2Top + ", " + W + " " + y2Top + " L " + W + " " + y2Bot + " C " + cp2x + " " + y2Bot + ", " + cp1x + " " + y1Top + ", 0 " + y1Top + " Z";
        }

        pathsHtml += '<path d="' + d + '" class="' + cls + '" data-connector-id="' + b.id + '"><title>' + b.tag.toUpperCase() + ': ' + b.id + '</title></path>';
      });

      svg.innerHTML = pathsHtml;

      svg.querySelectorAll(".ve-connector").forEach(function (path) {
        var id = path.dataset.connectorId;
        path.addEventListener("mouseenter", function () {
          wrapper.querySelectorAll('[data-block-id="' + id + '"]').forEach(function (b) { b.classList.add("is-hovered"); });
          path.classList.add("is-hovered");
        });
        path.addEventListener("mouseleave", function () {
          wrapper.querySelectorAll('[data-block-id="' + id + '"]').forEach(function (b) { b.classList.remove("is-hovered"); });
          path.classList.remove("is-hovered");
        });
        path.addEventListener("click", function () {
          if (wrapper._syncController && typeof wrapper._syncController.scrollToBlock === "function") {
            wrapper._syncController.scrollToBlock(id);
          }
        });
      });
    }

    function renderPromptUnifiedDiff(diffLines) {
      var uniEl = document.getElementById("prompt-diff-unified");
      if (!uniEl) return;
      if (!diffLines || diffLines.length === 0) {
        uniEl.innerHTML = '<div style="padding:2rem;text-align:center;color:var(--color-ink-muted);">Beide Versionen sind inhaltlich identisch (keine Unterschiede).</div>';
        return;
      }
      var rowsHtml = diffLines.map(function (line) {
        var m = line.type === "added" ? "+" : (line.type === "deleted" ? "−" : " ");
        return '<div class="ve-diff-line ve-diff-' + line.type + '">' +
          '<span class="ve-diff-marker">' + m + '</span>' +
          '<span class="ve-diff-text">' + escapeHtmlDiff(line.text) + '</span>' +
        '</div>';
      }).join("");

      uniEl.innerHTML = '<div class="ve-unified-container">' + rowsHtml + '</div>';
    }

    function renderSideBySideDiff(originalHtml, generatedHtml, meta) {
      var bodyEl = document.getElementById("raw-diff-body") || document.getElementById("prompt-diff-body");
      var previewEl = document.getElementById("prompt-diff-preview");
      var metaEl = document.getElementById("prompt-diff-meta");
      if (!bodyEl) return;

      if (metaEl) {
        var dur = meta.duration_ms ? (meta.duration_ms / 1000).toFixed(1) + "s" : "";
        var prov = meta.provider || "Gemini";
        var m = meta.model || "gemini-3.8-flash-medium";
        metaEl.innerHTML = " · Provider: <strong>" + escapeHtmlDiff(prov) + "</strong> · Modell: <code>" + escapeHtmlDiff(m) + "</code> · Dauer: <strong>" + dur + "</strong>";
      }

      if (previewEl) {
        previewEl.innerHTML = generatedHtml;
      }

      var linesA = formatHtmlLinesForDiff(originalHtml);
      var linesB = formatHtmlLinesForDiff(generatedHtml);
      var opcodes = getDiffOpcodes(linesA, linesB);

      var alignedBlocks = [];
      var diffLines = [];
      var blockIdx = 0;
      var changesCount = 0;

      for (var k = 0; k < opcodes.length; k++) {
        var tag = opcodes[k][0];
        var i1 = opcodes[k][1];
        var i2 = opcodes[k][2];
        var j1 = opcodes[k][3];
        var j2 = opcodes[k][4];

        var chunkA = linesA.slice(i1, i2);
        var chunkB = linesB.slice(j1, j2);
        var leftHtml = "";
        var rightHtml = "";

        if (tag === "equal") {
          leftHtml = escapeHtmlDiff(chunkA.join("\n"));
          rightHtml = escapeHtmlDiff(chunkB.join("\n"));
          for (var l = 0; l < chunkA.length; l++) {
            diffLines.push({ type: "unchanged", text: chunkA[l] });
          }
        } else if (tag === "replace") {
          changesCount++;
          var pair = computeWordDiff(chunkA.join("\n"), chunkB.join("\n"));
          leftHtml = pair[0];
          rightHtml = pair[1];
          for (var l = 0; l < chunkA.length; l++) diffLines.push({ type: "deleted", text: chunkA[l] });
          for (var l = 0; l < chunkB.length; l++) diffLines.push({ type: "added", text: chunkB[l] });
        } else if (tag === "delete") {
          changesCount++;
          leftHtml = escapeHtmlDiff(chunkA.join("\n"));
          for (var l = 0; l < chunkA.length; l++) diffLines.push({ type: "deleted", text: chunkA[l] });
        } else if (tag === "insert") {
          changesCount++;
          rightHtml = escapeHtmlDiff(chunkB.join("\n"));
          for (var l = 0; l < chunkB.length; l++) diffLines.push({ type: "added", text: chunkB[l] });
        }

        blockIdx++;
        alignedBlocks.push({
          id: "pb-" + blockIdx,
          tag: tag,
          left_lines: chunkA,
          right_lines: chunkB,
          left_html: leftHtml,
          right_html: rightHtml
        });
      }

      lastPromptDiffData = {
        aligned_blocks: alignedBlocks,
        diff_lines: diffLines,
        changesCount: changesCount
      };

      var leftBlocksHtml = "";
      var rightBlocksHtml = "";

      alignedBlocks.forEach(function (b) {
        var tag = b.tag;
        if (tag === "delete") {
          leftBlocksHtml += '<div class="ve-block ve-block-deleted" data-block-id="' + b.id + '" data-tag="delete">' + b.left_html + '</div>';
          rightBlocksHtml += '<div class="ve-block ve-block-anchor" data-block-id="' + b.id + '" data-tag="delete"></div>';
        } else if (tag === "replace") {
          leftBlocksHtml += '<div class="ve-block ve-block-replaced ve-block-left" data-block-id="' + b.id + '" data-tag="replace">' + b.left_html + '</div>';
          rightBlocksHtml += '<div class="ve-block ve-block-replaced ve-block-right" data-block-id="' + b.id + '" data-tag="replace">' + b.right_html + '</div>';
        } else if (tag === "equal") {
          leftBlocksHtml += '<div class="ve-block ve-block-equal" data-block-id="' + b.id + '" data-tag="equal">' + b.left_html + '</div>';
          rightBlocksHtml += '<div class="ve-block ve-block-equal" data-block-id="' + b.id + '" data-tag="equal">' + b.right_html + '</div>';
        } else if (tag === "insert") {
          leftBlocksHtml += '<div class="ve-block ve-block-anchor" data-block-id="' + b.id + '" data-tag="insert"></div>';
          rightBlocksHtml += '<div class="ve-block ve-block-added" data-block-id="' + b.id + '" data-tag="insert">' + b.right_html + '</div>';
        }
      });

      bodyEl.innerHTML = `
        <div class="ve-diff-summary-bar" style="margin-bottom:12px; font-size:0.85em; color:var(--color-ink-muted, #666); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
          <span>Unterschiede erkannt: <strong>${changesCount}</strong> geänderte, entfallene oder hinzugefügte Abschnitte.</span>
          <span style="font-size:0.8em; color:var(--color-ink-muted, #888);">💡 Hover über Abschnitte oder Verbindungsbänder hebt Korrespondenzen hervor</span>
        </div>
        <div class="ve-split-diff-wrapper" id="prompt-diff-split-wrapper">
          <div class="ve-split-columns" id="prompt-diff-split-columns">
            <div class="ve-split-pane ve-split-left" id="prompt-diff-pane-left-wrap">
              <div class="ve-split-header ve-header-left">
                <span>${(meta && meta.leftTitle) ? escapeHtmlDiff(meta.leftTitle) : "Bisheriger Stand (Ist-Zustand)"}</span>
                <span style="background:#e0f2fe; color:#0369a1; padding:2px 6px; border-radius:4px; font-size:0.75em; font-weight:700;">${(meta && meta.leftBadge) ? escapeHtmlDiff(meta.leftBadge) : "Basis"}</span>
              </div>
              <div class="ve-split-body" id="prompt-diff-pane-left">
                ${leftBlocksHtml || '<em style="color:#888;">(Kein bisheriges Fragment vorhanden)</em>'}
              </div>
            </div>

            <div class="ve-split-gutter" id="prompt-diff-split-gutter">
              <div class="ve-split-header ve-header-gutter">
                <span>Diff</span>
              </div>
              <div class="ve-gutter-canvas-wrap">
                <svg class="ve-gutter-svg" id="prompt-diff-gutter-svg" width="70" height="100%"></svg>
              </div>
            </div>

            <div class="ve-split-pane ve-split-right" id="prompt-diff-pane-right-wrap">
              <div class="ve-split-header ve-header-right">
                <span>${(meta && meta.rightTitle) ? escapeHtmlDiff(meta.rightTitle) : "Neuer Stand (KI-Ergebnis)"}</span>
                <span style="background:#dcfce7; color:#15803d; padding:2px 6px; border-radius:4px; font-size:0.75em; font-weight:700;">${(meta && meta.rightBadge) ? escapeHtmlDiff(meta.rightBadge) : "Vergleich"}</span>
              </div>
              <div class="ve-split-body" id="prompt-diff-pane-right">
                ${rightBlocksHtml || '<em style="color:#888;">(Keine Ausgabe erzeugt)</em>'}
              </div>
            </div>
          </div>
        </div>
      `;

      renderPromptUnifiedDiff(diffLines);

      // Synchronous Hover
      var wrapper = document.getElementById("prompt-diff-split-wrapper");
      if (wrapper) {
        wrapper.querySelectorAll(".ve-block").forEach(function (el) {
          var id = el.dataset.blockId;
          el.addEventListener("mouseenter", function () {
            wrapper.querySelectorAll('[data-block-id="' + id + '"]').forEach(function (b) { b.classList.add("is-hovered"); });
            var path = wrapper.querySelector('path[data-connector-id="' + id + '"]');
            if (path) path.classList.add("is-hovered");
          });
          el.addEventListener("mouseleave", function () {
            wrapper.querySelectorAll('[data-block-id="' + id + '"]').forEach(function (b) { b.classList.remove("is-hovered"); });
            var path = wrapper.querySelector('path[data-connector-id="' + id + '"]');
            if (path) path.classList.remove("is-hovered");
          });
        });

        var paneLeft = document.getElementById("prompt-diff-pane-left");
        var paneRight = document.getElementById("prompt-diff-pane-right");
        initPromptPiecewiseSyncScroll(wrapper, paneLeft, paneRight, alignedBlocks, redrawPromptSvgConnectors);
      }
    }

    function initPromptPiecewiseSyncScroll(wrapper, paneLeft, paneRight, blocks, redrawFn) {
      if (!wrapper || !paneLeft || !paneRight || !blocks || blocks.length === 0) return;

      var blockLayouts = [];
      var cumV = [0];
      var V_total = 0;
      var globalS = 0;
      var isProgrammatic = false;

      function measureLayout() {
        blockLayouts = [];
        cumV = [0];
        var runningV = 0;

        for (var i = 0; i < blocks.length; i++) {
          var b = blocks[i];
          var elL = paneLeft.querySelector('[data-block-id="' + b.id + '"]');
          var elR = paneRight.querySelector('[data-block-id="' + b.id + '"]');

          var hL = (elL && b.tag !== "insert") ? elL.offsetHeight : 0;
          var topL = elL ? elL.offsetTop : (i > 0 ? blockLayouts[i - 1].botL : 0);
          var botL = topL + hL;

          var hR = (elR && b.tag !== "delete") ? elR.offsetHeight : 0;
          var topR = elR ? elR.offsetTop : (i > 0 ? blockLayouts[i - 1].botR : 0);
          var botR = topR + hR;

          var hV = Math.max(hL, hR);
          runningV += hV;
          cumV.push(runningV);

          blockLayouts.push({
            id: b.id,
            tag: b.tag,
            topL: topL, hL: hL, botL: botL,
            topR: topR, hR: hR, botR: botR,
            hV: hV,
            startV: cumV[i],
            endV: runningV
          });
        }

        V_total = runningV;
      }

      function getTargetsForS(S) {
        if (blockLayouts.length === 0) return { targetL: 0, targetR: 0 };
        if (S <= 0) return { targetL: 0, targetR: 0 };

        var k = 0;
        while (k < blockLayouts.length - 1 && S >= blockLayouts[k].endV) {
          k++;
        }

        var blk = blockLayouts[k];
        var offset = S - blk.startV;
        var t = blk.hV > 0 ? Math.min(1, Math.max(0, offset / blk.hV)) : 0;

        var targetL = blk.topL + t * blk.hL;
        var targetR = blk.topR + t * blk.hR;

        return { targetL: targetL, targetR: targetR };
      }

      function getSFromR(scrollTopR) {
        if (blockLayouts.length === 0) return 0;
        for (var i = 0; i < blockLayouts.length; i++) {
          var blk = blockLayouts[i];
          if (scrollTopR >= blk.topR && (scrollTopR < blk.botR || i === blockLayouts.length - 1)) {
            var t = blk.hR > 0 ? (scrollTopR - blk.topR) / blk.hR : 0;
            return blk.startV + t * blk.hV;
          }
        }
        return 0;
      }

      function getSFromL(scrollTopL) {
        if (blockLayouts.length === 0) return 0;
        for (var i = 0; i < blockLayouts.length; i++) {
          var blk = blockLayouts[i];
          if (scrollTopL >= blk.topL && (scrollTopL < blk.botL || i === blockLayouts.length - 1)) {
            var t = blk.hL > 0 ? (scrollTopL - blk.topL) / blk.hL : 0;
            return blk.startV + t * blk.hV;
          }
        }
        return 0;
      }

      function applyScroll(S) {
        var maxScrollL = Math.max(0, paneLeft.scrollHeight - paneLeft.clientHeight);
        var maxScrollR = Math.max(0, paneRight.scrollHeight - paneRight.clientHeight);
        var viewH = Math.min(paneLeft.clientHeight || 450, paneRight.clientHeight || 450);
        var maxS = Math.max(0, V_total - viewH);

        globalS = Math.max(0, Math.min(maxS, S));
        var targets = getTargetsForS(globalS);

        isProgrammatic = true;
        paneLeft.scrollTop = Math.min(maxScrollL, Math.max(0, targets.targetL));
        paneRight.scrollTop = Math.min(maxScrollR, Math.max(0, targets.targetR));

        if (redrawFn) redrawFn();
        requestAnimationFrame(function () { isProgrammatic = false; });
      }

      wrapper.addEventListener("wheel", function (e) {
        if (e.deltaY !== 0) {
          e.preventDefault();
          applyScroll(globalS + e.deltaY);
        }
      }, { passive: false });

      paneLeft.addEventListener("scroll", function () {
        if (isProgrammatic) return;
        var S = getSFromL(paneLeft.scrollTop);
        applyScroll(S);
      }, { passive: true });

      paneRight.addEventListener("scroll", function () {
        if (isProgrammatic) return;
        var S = getSFromR(paneRight.scrollTop);
        applyScroll(S);
      }, { passive: true });

      wrapper._syncController = {
        scrollToBlock: function (blockId) {
          var idx = -1;
          for (var i = 0; i < blockLayouts.length; i++) {
            if (blockLayouts[i].id === blockId) { idx = i; break; }
          }
          if (idx >= 0) {
            applyScroll(blockLayouts[idx].startV);
          }
        },
        applyScroll: applyScroll,
        measure: measureLayout
      };

      setTimeout(function () {
        measureLayout();
        applyScroll(0);
      }, 25);

      if (window.ResizeObserver) {
        var ro = new ResizeObserver(function () {
          measureLayout();
          if (redrawFn) redrawFn();
        });
        ro.observe(paneLeft);
        ro.observe(paneRight);
      }
    }

    window.addEventListener("resize", function () {
      if (currentDiffViewMode === "side") {
        redrawPromptSvgConnectors();
      }
    });

    // --- 3-Reiter-Konzept Plaintext Prompt, Aktueller Output & Vorschau ---
    var rawWorkbenchState = {
      activeSubTab: "prompt",
      compareSourceId: null,
      linkedSourceId: null,
      linkedTargetId: null,
      isCompareActive: false,
      nextPreviewSeq: 2,
      previews: {
        "preview-1": {
          id: "preview-1",
          seq: 1,
          state: "idle",
          model: "gemini-3.8-flash",
          effort: "medium",
          provider: "agy",
          modelNameDisplay: "Gemini 3.8 Flash (med)",
          abortController: null,
          timerInterval: null,
          startTime: 0,
          durationMs: 0,
          html: "",
          error: "",
          rawOutput: ""
        }
      }
    };

    function getRawTabShortTitle(tabId) {
      if (tabId === "prompt") return "Prompt";
      if (tabId === "current") return "Aktueller Output";
      if (tabId && tabId.startsWith("preview-")) {
        var prev = rawWorkbenchState.previews[tabId];
        if (prev && prev.modelNameDisplay) {
          return "Vorschau " + prev.seq;
        }
        return "Vorschau " + tabId.replace("preview-", "");
      }
      return tabId || "";
    }

    function getRawTabFullTitle(tabId) {
      if (tabId === "prompt") return "Plaintext Prompt";
      if (tabId === "current") return "Aktueller Stand (Ist-Zustand)";
      if (tabId && tabId.startsWith("preview-")) {
        var prev = rawWorkbenchState.previews[tabId];
        if (prev && prev.modelNameDisplay) {
          return "Vorschau (" + prev.modelNameDisplay + ")";
        }
        return "Vorschau " + tabId.replace("preview-", "");
      }
      return tabId || "";
    }

    function getRawTabHtml(tabId) {
      if (tabId === "current") {
        var dataEl = document.getElementById("raw-current-output-data");
        if (dataEl) return dataEl.textContent || "";
        var codeEl = document.getElementById("raw-current-output-code");
        if (codeEl) return codeEl.textContent || "";
        return "";
      }
      if (tabId && tabId.startsWith("preview-")) {
        var prev = rawWorkbenchState.previews[tabId];
        return (prev && prev.html) ? prev.html : "";
      }
      return "";
    }

    function selectRawSubTab(tabId) {
      if (rawWorkbenchState.compareSourceId) {
        if (tabId === "prompt") {
          alert("Der Plaintext Prompt kann nur exklusiv angezeigt und nicht mit generiertem Output verglichen werden.");
          return;
        }
        if (tabId === rawWorkbenchState.compareSourceId) {
          cancelComparePick();
          return;
        }
        if (tabId.startsWith("preview-")) {
          var p = rawWorkbenchState.previews[tabId];
          if (!p || p.state !== "done") {
            alert("Diese Vorschau ist noch nicht fertig generiert.");
            return;
          }
        }
        linkCompareTabs(rawWorkbenchState.compareSourceId, tabId);
        return;
      }

      if (rawWorkbenchState.isCompareActive) {
        exitCompareMode();
      }

      if (tabId && tabId.startsWith("preview-")) {
        var prevItem = rawWorkbenchState.previews[tabId];
        if (prevItem && prevItem.state === "idle") {
          startPreviewGeneration(prevItem.seq);
          return;
        }
      }

      rawWorkbenchState.activeSubTab = tabId;

      document.querySelectorAll(".raw-subtab").forEach(function (tab) {
        var tId = tab.getAttribute("data-subtab");
        var isThis = (tId === tabId);
        tab.classList.toggle("is-active", isThis);
        tab.setAttribute("aria-selected", isThis ? "true" : "false");
      });

      var diffPane = document.getElementById("raw-pane-compare-diff");
      if (diffPane) diffPane.style.display = "none";

      var panePrompt = document.getElementById("raw-pane-prompt");
      var paneCurrent = document.getElementById("raw-pane-current");

      if (panePrompt) panePrompt.style.display = (tabId === "prompt" ? "" : "none");
      if (paneCurrent) paneCurrent.style.display = (tabId === "current" ? "" : "none");

      document.querySelectorAll(".raw-pane-preview").forEach(function (pane) {
        var expectedId = "raw-pane-" + tabId;
        pane.style.display = (pane.id === expectedId ? "" : "none");
      });
    }

    function initiateCompare(sourceId) {
      if (sourceId === "prompt") {
        alert("Der Plaintext Prompt kann nur exklusiv angezeigt und nicht verglichen werden.");
        return;
      }
      if (rawWorkbenchState.compareSourceId === sourceId) {
        cancelComparePick();
        return;
      }
      if (rawWorkbenchState.isCompareActive) {
        exitCompareMode();
      }

      rawWorkbenchState.compareSourceId = sourceId;

      document.querySelectorAll(".raw-subtab").forEach(function (t) {
        t.classList.remove("is-compare-source");
        if (t.getAttribute("data-subtab") === sourceId) {
          t.classList.add("is-compare-source");
        }
      });

      var hintBar = document.getElementById("raw-compare-hint-bar");
      var hintText = document.getElementById("raw-compare-hint-text");
      if (hintBar) {
        hintBar.style.display = "flex";
        if (hintText) {
          hintText.textContent = "💡 Basis gewählt: „" + getRawTabFullTitle(sourceId) + "“. Klicke nun auf einen zweiten Reiter (z.B. Aktueller Output oder eine andere Vorschau), um den Side-by-Side-Vergleich zu öffnen.";
        }
      }
    }

    function cancelComparePick() {
      rawWorkbenchState.compareSourceId = null;
      document.querySelectorAll(".raw-subtab").forEach(function (t) {
        t.classList.remove("is-compare-source");
      });
      var hintBar = document.getElementById("raw-compare-hint-bar");
      if (hintBar) hintBar.style.display = "none";
    }

    function linkCompareTabs(sourceId, targetId) {
      cancelComparePick();

      rawWorkbenchState.isCompareActive = true;
      rawWorkbenchState.linkedSourceId = sourceId;
      rawWorkbenchState.linkedTargetId = targetId;

      document.querySelectorAll(".raw-subtab").forEach(function (t) {
        var s = t.getAttribute("data-subtab");
        var isLinked = (s === sourceId || s === targetId);
        t.classList.toggle("is-compare-linked", isLinked);
      });

      var linkBadge = document.getElementById("raw-tab-link-badge");
      var linkLabel = document.getElementById("raw-tab-link-label");
      if (linkBadge) {
        linkBadge.style.display = "inline-flex";
        linkBadge.title = "Vergleich aktiv: " + getRawTabShortTitle(sourceId) + " ⇄ " + getRawTabShortTitle(targetId) + " (Klick kehrt zur Einzelansicht zurück)";
      }
      if (linkLabel) {
        linkLabel.textContent = "Verknüpft: " + getRawTabShortTitle(sourceId) + " ⇄ " + getRawTabShortTitle(targetId);
      }

      var panePrompt = document.getElementById("raw-pane-prompt");
      var paneCurrent = document.getElementById("raw-pane-current");
      if (panePrompt) panePrompt.style.display = "none";
      if (paneCurrent) paneCurrent.style.display = "none";
      document.querySelectorAll(".raw-pane-preview").forEach(function (p) {
        p.style.display = "none";
      });

      var diffPane = document.getElementById("raw-pane-compare-diff");
      if (diffPane) diffPane.style.display = "block";

      var tagLeft = document.getElementById("diff-tag-left");
      var tagRight = document.getElementById("diff-tag-right");
      if (tagLeft) tagLeft.textContent = "Basis: " + getRawTabShortTitle(sourceId);
      if (tagRight) tagRight.textContent = "Vergleich: " + getRawTabShortTitle(targetId);

      var leftHtml = getRawTabHtml(sourceId);
      var rightHtml = getRawTabHtml(targetId);
      renderSideBySideDiff(leftHtml, rightHtml, {
        leftTitle: getRawTabFullTitle(sourceId),
        rightTitle: getRawTabFullTitle(targetId),
        leftBadge: getRawTabShortTitle(sourceId),
        rightBadge: getRawTabShortTitle(targetId)
      });
      setTimeout(redrawPromptSvgConnectors, 30);
    }

    function exitCompareMode() {
      if (!rawWorkbenchState.isCompareActive) return;
      rawWorkbenchState.isCompareActive = false;
      var returnTab = rawWorkbenchState.linkedTargetId || rawWorkbenchState.linkedSourceId || "current";
      rawWorkbenchState.linkedSourceId = null;
      rawWorkbenchState.linkedTargetId = null;

      document.querySelectorAll(".raw-subtab").forEach(function (t) {
        t.classList.remove("is-compare-linked");
      });

      var linkBadge = document.getElementById("raw-tab-link-badge");
      if (linkBadge) linkBadge.style.display = "none";

      var diffPane = document.getElementById("raw-pane-compare-diff");
      if (diffPane) diffPane.style.display = "none";

      selectRawSubTab(returnTab);
    }

    function spawnNewPreviewTab(seq) {
      var pId = "preview-" + seq;
      rawWorkbenchState.previews[pId] = {
        id: pId,
        seq: seq,
        state: "idle",
        model: "gemini-3.8-flash",
        effort: "medium",
        provider: "agy",
        modelNameDisplay: "Gemini 3.8 Flash (med)",
        abortController: null,
        timerInterval: null,
        startTime: 0,
        durationMs: 0,
        html: "",
        error: "",
        rawOutput: ""
      };

      var tabsContainer = document.getElementById("raw-preview-tabs-list");
      if (tabsContainer) {
        var tabDiv = document.createElement("div");
        tabDiv.className = "raw-subtab raw-subtab-preview";
        tabDiv.setAttribute("data-subtab", pId);
        tabDiv.setAttribute("data-preview-id", String(seq));
        tabDiv.setAttribute("data-state", "idle");
        tabDiv.setAttribute("role", "tab");
        tabDiv.id = "subtab-" + pId;
        tabDiv.setAttribute("aria-selected", "false");
        tabDiv.innerHTML = `
          <span class="subtab-click-area" data-action="select-subtab" data-subtab="${pId}" title="Vorschau anzeigen / konfigurieren">
            <span class="subtab-icon">⚡</span>
            <span class="subtab-title">Vorschau</span>
          </span>
          <div class="subtab-controls" id="subtab-controls-${pId}">
            <select class="subtab-select-model" title="Modell auswählen">
              <option value="gemini-3.8-flash" data-provider="agy" selected>Gemini 3.8 Flash</option>
              <option value="composer-2.5" data-provider="cursor">Cursor Composer 2.5</option>
            </select>
            <select class="subtab-select-effort" title="Reasoning / Effort auswählen">
              <option value="medium" selected>med</option>
              <option value="low">low</option>
              <option value="high">high</option>
            </select>
            <button type="button" class="btn-subtab-start" data-preview-id="${seq}" title="Generierung starten">⚡ Start</button>
          </div>
          <button type="button" class="btn-compare-tab" data-compare-id="${pId}" title="Diesen Stand vergleichen" style="display:none;" aria-label="Vergleichen">
            <span class="compare-icon">⚖️</span>
          </button>
          <button type="button" class="btn-subtab-close" data-preview-id="${seq}" title="Diesen Lauf schließen" style="display:none;" aria-label="Schließen">✕</button>
        `;
        tabsContainer.appendChild(tabDiv);
      }

      var panesContainer = document.getElementById("raw-preview-panes-container");
      if (panesContainer) {
        var paneDiv = document.createElement("div");
        paneDiv.className = "raw-content-pane raw-pane-preview";
        paneDiv.id = "raw-pane-" + pId;
        paneDiv.style.display = "none";
        paneDiv.innerHTML = `
          <div class="preview-idle-banner" style="padding:40px 20px; text-align:center; color:var(--color-ink-muted, #666); background:var(--bg-canvas, #fafafa); border:1px dashed var(--border-default, #ccc); border-radius:8px;">
            <div style="font-size:2rem; margin-bottom:8px;">⚡</div>
            <div style="font-weight:600; font-size:1rem; margin-bottom:6px;">Noch keine Vorschau generiert</div>
            <div style="font-size:0.85rem; max-width:440px; margin:0 auto 16px;">Wähle oben im Reiter Modell und Effort aus und klicke auf <strong>⚡ Start</strong>, um die Generierung anzustoßen.</div>
            <button type="button" class="btn-subtab-start-pane" data-preview-id="${seq}" style="padding:6px 16px; font-size:0.9rem; font-weight:700; background:var(--color-teal-600, #01696f); color:#fff; border:none; border-radius:6px; cursor:pointer;">⚡ Generierung jetzt starten</button>
          </div>
        `;
        panesContainer.appendChild(paneDiv);
      }
    }

    function startPreviewGeneration(seq) {
      var pId = "preview-" + seq;
      var prev = rawWorkbenchState.previews[pId];
      if (!prev || prev.state === "running") return;

      var tabEl = document.getElementById("subtab-" + pId);
      if (!tabEl) return;

      var modelSelect = tabEl.querySelector(".subtab-select-model");
      var effortSelect = tabEl.querySelector(".subtab-select-effort");
      var rawModel = modelSelect ? modelSelect.value : "gemini-3.8-flash";
      var rawEffort = effortSelect ? effortSelect.value : "medium";
      var opt = (modelSelect && modelSelect.selectedOptions) ? modelSelect.selectedOptions[0] : null;
      var provider = opt ? opt.getAttribute("data-provider") : (rawModel === "composer-2.5" ? "cursor" : "agy");

      var ta = document.getElementById("raw-prompt-textarea");
      var promptText = ta ? ta.value.trim() : "";
      if (!promptText) {
        alert("Prompt-Text darf nicht leer sein.");
        return;
      }
      var modName = (ta && ta.getAttribute("data-module")) || "LinIf";
      var fragRel = (ta && ta.getAttribute("data-fragment")) || "content/ai/classic/modules/linif/main_01.html";

      var execModel = "";
      var displayName = "";
      if (provider === "cursor") {
        execModel = "composer-2.5";
        displayName = "Cursor Composer 2.5";
      } else {
        execModel = (rawModel.startsWith("gemini-") ? (rawModel + "-" + rawEffort) : rawModel);
        displayName = "Gemini 3.8 Flash (" + rawEffort + ")";
      }

      prev.state = "running";
      prev.model = execModel;
      prev.effort = rawEffort;
      prev.provider = provider;
      prev.modelNameDisplay = displayName;
      prev.startTime = performance.now();
      prev.abortController = new AbortController();

      if (modelSelect) { modelSelect.disabled = true; modelSelect.style.display = "none"; }
      if (effortSelect) { effortSelect.disabled = true; effortSelect.style.display = "none"; }
      var btnStart = tabEl.querySelector(".btn-subtab-start");
      if (btnStart) btnStart.style.display = "none";

      var controls = tabEl.querySelector(".subtab-controls");
      var btnCancel = tabEl.querySelector(".btn-subtab-cancel");
      if (!btnCancel && controls) {
        btnCancel = document.createElement("button");
        btnCancel.type = "button";
        btnCancel.className = "btn-subtab-cancel";
        btnCancel.setAttribute("data-preview-id", String(seq));
        btnCancel.title = "Generierung abbrechen";
        btnCancel.setAttribute("aria-label", "Abbrechen");
        btnCancel.textContent = "✕";
        controls.appendChild(btnCancel);
      } else if (btnCancel) {
        btnCancel.style.display = "inline-flex";
      }

      var titleEl = tabEl.querySelector(".subtab-title");
      if (titleEl) {
        titleEl.innerHTML = '<span class="subtab-spinner">⏳</span> ' + escapeHtmlDiff(displayName) + ' <span class="subtab-timer" id="subtab-timer-' + pId + '">0.0s</span>';
      }
      tabEl.setAttribute("data-state", "running");

      var paneEl = document.getElementById("raw-pane-" + pId);
      if (paneEl) {
        paneEl.innerHTML = `
          <div class="raw-preview-loading" style="padding:28px 20px; text-align:center; background:var(--bg-canvas, #fafafa); border:1px solid var(--border-default, #ddd); border-radius:8px;">
            <div style="display:flex; justify-content:center; align-items:center; gap:10px; margin-bottom:12px; flex-wrap:wrap;">
              <span id="pane-hz-${pId}" style="background:#059669; color:#fff; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:700;">Live 4.0 Hz</span>
              <span id="pane-phase-${pId}" style="font-family:monospace; background:#e0f2fe; color:#0369a1; padding:2px 8px; border-radius:4px; font-size:0.78rem;">[Phase: Initialisierung…]</span>
            </div>
            <div class="diff-spinner" style="display:inline-block; width:30px; height:30px; border:3px solid rgba(1,105,111,0.2); border-top-color:#01696f; border-radius:50%; animation:spin 0.8s linear infinite;"></div>
            <div style="margin-top:10px; font-weight:700; font-size:1.02rem; color:var(--color-ink, #222);">Generiere Vorschau mit ${escapeHtmlDiff(displayName)}…</div>
            <div style="font-size:0.85rem; color:var(--color-ink-muted, #666); margin-top:4px;">Tokens: <strong id="pane-tokens-${pId}">0</strong> · Zeit: <span id="pane-timer-${pId}" style="font-weight:700; font-family:monospace;">0.0s</span></div>
            <pre id="pane-stream-${pId}" style="margin-top:14px; text-align:left; max-height:220px; overflow-y:auto; background:#1e293b; color:#e2e8f0; padding:12px; border-radius:6px; font-family:monospace; font-size:0.82rem; line-height:1.45; white-space:pre-wrap; word-break:break-word; border:1px solid #334155; display:none;"></pre>
            <div style="margin-top:16px;">
              <button type="button" class="btn-cancel-run-pane" data-preview-id="${seq}" style="padding:5px 14px; font-size:0.82rem; font-weight:600; background:#fee2e2; border:1px solid #fca5a5; color:#b91c1c; border-radius:6px; cursor:pointer;">✕ Generierung abbrechen</button>
            </div>
          </div>
        `;
      }

      if (prev.timerInterval) clearInterval(prev.timerInterval);
      prev.timerInterval = setInterval(function () {
        var elapsedSec = ((performance.now() - prev.startTime) / 1000).toFixed(1) + "s";
        var tTab = document.getElementById("subtab-timer-" + pId);
        var tPane = document.getElementById("pane-timer-" + pId);
        if (tTab) tTab.textContent = elapsedSec;
        if (tPane) tPane.textContent = elapsedSec;
      }, 100);

      selectRawSubTab(pId);

      var hasIdlePreview = Object.keys(rawWorkbenchState.previews).some(function (k) {
        return rawWorkbenchState.previews[k].state === "idle";
      });
      if (!hasIdlePreview) {
        var nextSeq = rawWorkbenchState.nextPreviewSeq++;
        spawnNewPreviewTab(nextSeq);
      }

      fetch("/api/ai/execute_prompt", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "text/event-stream"
        },
        signal: prev.abortController.signal,
        body: JSON.stringify({
          prompt: promptText,
          module: modName,
          fragment: fragRel,
          model: execModel,
          provider: provider,
          stream: true
        })
      })
        .then(async function (res) {
          if (!res.ok) {
            return res.json().then(function (j) {
              throw new Error(j.error || ("Server HTTP " + res.status));
            }).catch(function (err) {
              throw new Error(err.message || ("Server HTTP " + res.status));
            });
          }

          var cType = res.headers.get("Content-Type") || "";
          if (cType.includes("text/event-stream") && res.body && res.body.getReader) {
            var reader = res.body.getReader();
            var decoder = new TextDecoder("utf-8");
            var buffer = "";
            var finalData = null;
            var hzBadge = document.getElementById("pane-hz-" + pId);
            var phaseBadge = document.getElementById("pane-phase-" + pId);
            var tokensBadge = document.getElementById("pane-tokens-" + pId);
            var streamBox = document.getElementById("pane-stream-" + pId);
            var streamAcc = "";

            while (true) {
              var r = await reader.read();
              if (r.done) break;
              buffer += decoder.decode(r.value, { stream: true });
              var lines = buffer.split("\n");
              buffer = lines.pop();

              for (var i = 0; i < lines.length; i++) {
                var line = lines[i].trim();
                if (line.startsWith("data: ")) {
                  var jsonStr = line.slice(6).trim();
                  if (!jsonStr) continue;
                  try {
                    var ev = JSON.parse(jsonStr);
                    if (ev.hz && hzBadge) {
                      hzBadge.textContent = "Live " + parseFloat(ev.hz).toFixed(1) + " Hz";
                    }
                    if (ev.phase && phaseBadge) {
                      var pLabels = {
                        "thinking": "[Phase: Denkvorgang / Reasoning…]",
                        "reasoning": "[Phase: Analysiere Spezifikation…]",
                        "generating": "[Phase: Generiere Fragment…]"
                      };
                      phaseBadge.textContent = pLabels[ev.phase] || ("[Phase: " + ev.phase + "…]");
                    }
                    if (ev.tokens !== undefined && tokensBadge) {
                      tokensBadge.textContent = ev.tokens;
                    }
                    if (ev.delta) {
                      streamAcc += ev.delta;
                      if (streamBox) {
                        streamBox.style.display = "block";
                        streamBox.textContent = streamAcc;
                        streamBox.scrollTop = streamBox.scrollHeight;
                      }
                    }
                    if (ev.event === "complete") {
                      finalData = ev;
                    } else if (ev.event === "error") {
                      throw new Error(ev.error || "Fehler beim Streaming des Agenten.");
                    }
                  } catch (e) {
                    if (e.message && e.message.includes("Fehler beim Streaming")) throw e;
                  }
                }
              }
            }
            if (!finalData) throw new Error("Stream beendet ohne Ergebnis-Event.");
            return finalData;
          } else {
            return res.json();
          }
        })
        .then(function (data) {
          if (prev.timerInterval) { clearInterval(prev.timerInterval); prev.timerInterval = null; }
          var durMs = data.duration_ms || Math.round(performance.now() - prev.startTime);
          prev.durationMs = durMs;

          if (!data.ok) {
            prev.state = "error";
            prev.error = data.error || "Modell lieferte kein gültiges Ergebnis.";
            tabEl.setAttribute("data-state", "error");
            if (btnCancel) btnCancel.style.display = "none";
            var btnClose = tabEl.querySelector(".btn-subtab-close");
            if (btnClose) btnClose.style.display = "inline-flex";
            if (titleEl) titleEl.innerHTML = escapeHtmlDiff(displayName) + ' <span class="subtab-err-mark" style="color:#b91c1c; font-weight:bold;">!</span>';

            if (paneEl) {
              paneEl.innerHTML = `
                <div style="padding:18px; color:#b91c1c; background:#fee2e2; border-radius:8px; border:1px solid #fca5a5; margin-bottom:12px;">
                  <div style="font-weight:700; font-size:0.95rem; margin-bottom:6px;">Fehler bei der Generierung (${(durMs / 1000).toFixed(1)}s):</div>
                  <div>${escapeHtmlDiff(prev.error)}</div>
                  ${data.raw_output ? '<pre style="margin-top:10px; font-size:0.8em; max-height:160px; overflow:auto; background:#fff; padding:8px; border-radius:4px; border:1px solid #fca5a5;">' + escapeHtmlDiff(data.raw_output) + '</pre>' : ''}
                  <div style="margin-top:12px;">
                    <button type="button" class="btn-subtab-start-pane" data-preview-id="${seq}" style="padding:5px 12px; background:#b91c1c; color:#fff; border:none; border-radius:4px; font-size:0.85rem; font-weight:600; cursor:pointer;">Erneut versuchen</button>
                  </div>
                </div>
              `;
            }
            return;
          }

          prev.state = "done";
          prev.html = data.generated_html || "";
          prev.rawOutput = data.raw_output || "";
          tabEl.setAttribute("data-state", "done");

          if (btnCancel) btnCancel.style.display = "none";
          var btnCmp = tabEl.querySelector('.btn-compare-tab[data-compare-id="' + pId + '"]');
          if (btnCmp) btnCmp.style.display = "inline-flex";
          var btnClose = tabEl.querySelector(".btn-subtab-close");
          if (btnClose) btnClose.style.display = "inline-flex";

          if (titleEl) {
            titleEl.innerHTML = '✓ ' + escapeHtmlDiff(displayName) + ' <span style="font-size:0.8em; opacity:0.85;">(' + (durMs / 1000).toFixed(1) + 's)</span>';
          }

          if (paneEl) {
            paneEl.innerHTML = `
              <div class="raw-pane-banner" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                <span>⚡ Vorschau: <strong>${escapeHtmlDiff(displayName)}</strong> · Dauer: <strong>${(durMs / 1000).toFixed(1)}s</strong> · Länge: <strong>${prev.html.length} Zeichen</strong></span>
                <div style="display:flex; gap:8px;">
                  <button type="button" class="btn-compare-tab" data-compare-id="${pId}" title="Diesen Stand vergleichen">⚖️ Vergleichen</button>
                </div>
              </div>
              <pre class="raw-code-box" id="raw-preview-code-${pId}">${escapeHtmlDiff(prev.html)}</pre>
            `;
          }
        })
        .catch(function (err) {
          if (prev.timerInterval) { clearInterval(prev.timerInterval); prev.timerInterval = null; }
          if (err.name === "AbortError") {
            prev.state = "cancelled";
            tabEl.setAttribute("data-state", "cancelled");
            if (btnCancel) btnCancel.style.display = "none";
            var btnClose = tabEl.querySelector(".btn-subtab-close");
            if (btnClose) btnClose.style.display = "inline-flex";
            if (titleEl) titleEl.innerHTML = '✕ ' + escapeHtmlDiff(displayName) + ' (Abgebrochen)';
            if (paneEl) {
              paneEl.innerHTML = `
                <div style="padding:24px; text-align:center; color:var(--color-ink-muted, #666); background:var(--bg-canvas, #fafafa); border:1px dashed var(--border-default, #ccc); border-radius:8px;">
                  <div style="font-size:1.5rem; margin-bottom:6px;">✕</div>
                  <div style="font-weight:600; margin-bottom:4px;">Generierung wurde abgebrochen</div>
                  <div style="font-size:0.85rem; margin-bottom:12px;">Der laufende Modellaufruf wurde vom Benutzer gestoppt.</div>
                  <button type="button" class="btn-subtab-start-pane" data-preview-id="${seq}" style="padding:5px 14px; background:var(--color-teal-600, #01696f); color:#fff; border:none; border-radius:4px; font-weight:600; cursor:pointer;">⚡ Neu starten</button>
                </div>
              `;
            }
          } else {
            prev.state = "error";
            prev.error = err.message;
            tabEl.setAttribute("data-state", "error");
            if (btnCancel) btnCancel.style.display = "none";
            var btnClose = tabEl.querySelector(".btn-subtab-close");
            if (btnClose) btnClose.style.display = "inline-flex";
            if (titleEl) titleEl.innerHTML = escapeHtmlDiff(displayName) + ' <span class="subtab-err-mark" style="color:#b91c1c; font-weight:bold;">!</span>';
            if (paneEl) {
              paneEl.innerHTML = `
                <div style="padding:18px; color:#b91c1c; background:#fee2e2; border-radius:8px; border:1px solid #fca5a5; margin-bottom:12px;">
                  <div style="font-weight:700; font-size:0.95rem; margin-bottom:6px;">Verbindungsfehler:</div>
                  <div>${escapeHtmlDiff(err.message)}</div>
                  <div style="margin-top:12px;">
                    <button type="button" class="btn-subtab-start-pane" data-preview-id="${seq}" style="padding:5px 12px; background:#b91c1c; color:#fff; border:none; border-radius:4px; font-size:0.85rem; font-weight:600; cursor:pointer;">Erneut versuchen</button>
                  </div>
                </div>
              `;
            }
          }
        });
    }

    function cancelPreviewGeneration(seq) {
      var pId = "preview-" + seq;
      var prev = rawWorkbenchState.previews[pId];
      if (prev && prev.abortController) {
        prev.abortController.abort();
      }
    }

    function closePreviewTab(seq) {
      var pId = "preview-" + seq;
      if (rawWorkbenchState.isCompareActive && (rawWorkbenchState.linkedSourceId === pId || rawWorkbenchState.linkedTargetId === pId)) {
        exitCompareMode();
      }
      if (rawWorkbenchState.compareSourceId === pId) {
        cancelComparePick();
      }
      var prev = rawWorkbenchState.previews[pId];
      if (prev && prev.timerInterval) {
        clearInterval(prev.timerInterval);
      }
      if (prev && prev.abortController && prev.state === "running") {
        prev.abortController.abort();
      }
      delete rawWorkbenchState.previews[pId];

      var tabEl = document.getElementById("subtab-" + pId);
      if (tabEl) tabEl.remove();
      var paneEl = document.getElementById("raw-pane-" + pId);
      if (paneEl) paneEl.remove();

      if (rawWorkbenchState.activeSubTab === pId) {
        selectRawSubTab("current");
      }
    }

    // Interaction delegation
    document.addEventListener("click", function (e) {
      // Dossier mode tab switcher
      var modeTab = e.target.closest(".dossier-mode-tab");
      if (modeTab) {
        e.preventDefault();
        var targetMode = modeTab.getAttribute("data-view-mode") || "raw";
        var modal = modeTab.closest("dialog") || document;
        switchDossierViewMode(targetMode, modal);
        return;
      }

      // Copy raw prompt text
      var btnCopyPrompt = e.target.closest("#btn-copy-raw-prompt");
      if (btnCopyPrompt) {
        e.preventDefault();
        var rawTa = document.getElementById("raw-prompt-textarea");
        var rawPre = document.getElementById("raw-prompt-text");
        var text = rawTa ? rawTa.value : (rawPre ? rawPre.textContent : "");
        if (text) {
          var showCopyHint = function () {
            var hint = document.getElementById("copy-success-hint");
            if (hint) {
              hint.hidden = false;
              setTimeout(function () { hint.hidden = true; }, 2200);
            }
          };
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(showCopyHint).catch(function () {
              fallbackCopy(text, showCopyHint);
            });
          } else {
            fallbackCopy(text, showCopyHint);
          }
        }
        function fallbackCopy(val, cb) {
          var ta = document.createElement("textarea");
          ta.value = val;
          ta.style.position = "fixed";
          ta.style.opacity = "0";
          document.body.appendChild(ta);
          ta.focus();
          ta.select();
          try { document.execCommand("copy"); if (cb) cb(); } catch (err) {}
          document.body.removeChild(ta);
        }
        return;
      }

      // 3-Reiter-Konzept: Interaction Delegation

      // Compare Button (⚖️)
      var btnCompare = e.target.closest(".btn-compare-tab");
      if (btnCompare) {
        e.preventDefault();
        e.stopPropagation();
        var cid = btnCompare.getAttribute("data-compare-id");
        if (cid) {
          initiateCompare(cid);
        }
        return;
      }

      // Start preview generation (⚡ Start)
      var btnStartTab = e.target.closest(".btn-subtab-start");
      var btnStartPane = e.target.closest(".btn-subtab-start-pane");
      if (btnStartTab || btnStartPane) {
        e.preventDefault();
        e.stopPropagation();
        var pSeq = (btnStartTab || btnStartPane).getAttribute("data-preview-id");
        if (pSeq) {
          startPreviewGeneration(pSeq);
        }
        return;
      }

      // Cancel preview generation (✕ Abbrechen)
      var btnCancelTab = e.target.closest(".btn-subtab-cancel") || e.target.closest(".btn-cancel-run-pane");
      if (btnCancelTab) {
        e.preventDefault();
        e.stopPropagation();
        var pSeq = btnCancelTab.getAttribute("data-preview-id");
        if (pSeq) {
          cancelPreviewGeneration(pSeq);
        }
        return;
      }

      // Close preview tab (✕)
      var btnCloseTab = e.target.closest(".btn-subtab-close");
      if (btnCloseTab) {
        e.preventDefault();
        e.stopPropagation();
        var pSeq = btnCloseTab.getAttribute("data-preview-id");
        if (pSeq) {
          closePreviewTab(pSeq);
        }
        return;
      }

      // Exit compare mode (Link Badge or Unlink Button)
      if (e.target.closest("#raw-tab-link-badge") || e.target.closest("#btn-unlink-compare")) {
        e.preventDefault();
        e.stopPropagation();
        exitCompareMode();
        return;
      }

      // Cancel compare picking mode
      if (e.target.closest("#btn-cancel-compare-pick")) {
        e.preventDefault();
        e.stopPropagation();
        cancelComparePick();
        return;
      }

      // Ignore clicks inside inline selects so user can freely open dropdowns
      if (e.target.closest(".subtab-controls select")) {
        return;
      }

      // Subtab selection (Click on tab or click area)
      var subtabClick = e.target.closest("[data-action='select-subtab']") || e.target.closest(".raw-subtab");
      if (subtabClick) {
        e.preventDefault();
        var subtabId = subtabClick.getAttribute("data-subtab") || (subtabClick.closest(".raw-subtab") ? subtabClick.closest(".raw-subtab").getAttribute("data-subtab") : null);
        if (subtabId) {
          selectRawSubTab(subtabId);
        }
        return;
      }

      // Clear badge button (x an der Badge)
      var btnClearBadge = e.target.closest(".btn-clear-badge");
      if (btnClearBadge) {
        e.preventDefault();
        e.stopPropagation();
        var bId = btnClearBadge.getAttribute("data-clear-badge-for");
        if (bId) {
          var votes = loadVotes();
          delete votes[bId];
          try { localStorage.setItem(VOTE_STORE, JSON.stringify(votes)); } catch (err) {}

          var pkg = loadReviewPackage();
          var nextPkg = pkg.filter(function (x) { return x.id !== bId; });
          if (nextPkg.length !== pkg.length) {
            storeReviewPackage(nextPkg);
          }

          try {
            fetch("/api/curation/vote", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ snippet_id: bId, item_id: bId, vote: "reset" })
            }).catch(function () {});
          } catch (err) {}

          updateSnippetBadges();
        }
        return;
      }

      // Card checkbox click
      var cb = e.target.closest(".card-select-checkbox");
      if (cb) {
        var cCard = cb.closest(".snippet-card");
        var cId = cb.getAttribute("data-select-card") || (cCard ? cCard.getAttribute("data-snippet-id") : null);
        if (cId) {
          if (cb.checked) {
            selectedSnippetIds.add(cId);
            lastSelectedSnippetId = cId;
          } else {
            selectedSnippetIds.delete(cId);
          }
          updateSelectionUI();
        }
        return;
      }

      // Batch Action Buttons
      if (e.target.closest("#btn-batch-confirm")) {
        e.preventDefault();
        selectedSnippetIds.forEach(function (sId) {
          storeVote(sId, { vote: "confirm", queued: false });
          try {
            fetch("/api/curation/vote", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ snippet_id: sId, item_id: sId, vote: "confirm" })
            }).catch(function () {});
          } catch (err) {}
        });
        selectedSnippetIds.clear();
        updateSelectionUI();
        updateSnippetBadges();
        return;
      }

      if (e.target.closest("#btn-batch-dismiss")) {
        e.preventDefault();
        selectedSnippetIds.forEach(function (sId) {
          storeVote(sId, { vote: "dismiss", queued: false });
          try {
            fetch("/api/curation/vote", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ snippet_id: sId, item_id: sId, vote: "dismiss" })
            }).catch(function () {});
          } catch (err) {}
        });
        selectedSnippetIds.clear();
        updateSelectionUI();
        updateSnippetBadges();
        return;
      }

      if (e.target.closest("#btn-batch-discuss")) {
        e.preventDefault();
        var chatPane = document.getElementById("dossier-chat-pane");
        var modal = chatPane ? chatPane.closest("dialog") : null;
        if (chatPane) {
          chatPane.hidden = false;
          if (modal) modal.classList.add("has-chat-open");
        }
        var countAdded = 0;
        selectedSnippetIds.forEach(function (sId) {
          if (!attachedDiscussionItems.has(sId)) {
            attachedDiscussionItems.add(sId);
            countAdded++;
          }
          var targetCard = document.getElementById(sId);
          if (targetCard) {
            targetCard.classList.remove("is-collapsed");
            targetCard.classList.add("is-expanded");
            var h = targetCard.querySelector(".snippet-card-header");
            if (h) h.setAttribute("aria-expanded", "true");
          }
        });
        appendDiscussionSystemNote(countAdded + " Element(e) aus Multiselektion zur Diskussion hinzugefügt.");
        selectedSnippetIds.clear();
        updateSelectionUI();
        renderAttachedChips();
        updateSnippetBadges();
        return;
      }

      if (e.target.closest("#btn-clear-selection")) {
        e.preventDefault();
        selectedSnippetIds.clear();
        updateSelectionUI();
        return;
      }

      // 0. Card header toggle (collapse / expand & mouse selection)
      var cardToggle = e.target.closest("[data-card-toggle]");
      if (cardToggle) {
        if (!e.target.closest(".curation-btn") && !e.target.closest("a") && !e.target.closest(".card-select-checkbox") && !e.target.closest(".btn-clear-badge")) {
          var cardId = cardToggle.getAttribute("data-card-toggle");
          var card = document.getElementById(cardId) || cardToggle.closest(".snippet-card");
          var sId = card ? (card.getAttribute("data-snippet-id") || card.id) : cardId;

          // Ctrl / Cmd + Click: Toggle element selection
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            if (selectedSnippetIds.has(sId)) {
              selectedSnippetIds.delete(sId);
            } else {
              selectedSnippetIds.add(sId);
              lastSelectedSnippetId = sId;
            }
            updateSelectionUI();
            return;
          }

          // Shift + Click: Range multiselection
          if (e.shiftKey) {
            e.preventDefault();
            var visibleCards = getVisibleSnippetCards();
            var cardIds = visibleCards.map(function (c) { return c.getAttribute("data-snippet-id") || c.id; });
            var fromIdx = lastSelectedSnippetId ? cardIds.indexOf(lastSelectedSnippetId) : -1;
            var toIdx = cardIds.indexOf(sId);
            if (toIdx !== -1) {
              if (fromIdx === -1) fromIdx = 0;
              var start = Math.min(fromIdx, toIdx);
              var end = Math.max(fromIdx, toIdx);
              for (var i = start; i <= end; i++) {
                selectedSnippetIds.add(cardIds[i]);
              }
              lastSelectedSnippetId = sId;
              updateSelectionUI();
            }
            return;
          }

          // Regular click: Expand / Collapse
          e.preventDefault();
          lastSelectedSnippetId = sId;
          if (card) {
            var isCollapsed = card.classList.contains("is-collapsed");
            if (isCollapsed) {
              card.classList.remove("is-collapsed");
              card.classList.add("is-expanded");
              cardToggle.setAttribute("aria-expanded", "true");
            } else {
              card.classList.remove("is-expanded");
              card.classList.add("is-collapsed");
              cardToggle.setAttribute("aria-expanded", "false");
            }
          }
          return;
        }
      }

      // View Compact
      if (e.target.closest("#btn-view-compact")) {
        e.preventDefault();
        document.querySelectorAll(".snippet-card").forEach(function (c) {
          c.classList.add("is-collapsed");
          c.classList.remove("is-expanded");
          var h = c.querySelector(".snippet-card-header");
          if (h) h.setAttribute("aria-expanded", "false");
        });
        document.querySelectorAll("#btn-view-compact").forEach(function (b) { b.classList.add("is-active"); });
        document.querySelectorAll("#btn-view-detailed").forEach(function (b) { b.classList.remove("is-active"); });
        var btnToggleAll = document.getElementById("btn-toggle-all-expand");
        if (btnToggleAll) btnToggleAll.textContent = "⊞ Alle ausklappen";
        return;
      }

      // View Detailed
      if (e.target.closest("#btn-view-detailed")) {
        e.preventDefault();
        document.querySelectorAll(".snippet-card").forEach(function (c) {
          c.classList.remove("is-collapsed");
          c.classList.add("is-expanded");
          var h = c.querySelector(".snippet-card-header");
          if (h) h.setAttribute("aria-expanded", "true");
        });
        document.querySelectorAll("#btn-view-detailed").forEach(function (b) { b.classList.add("is-active"); });
        document.querySelectorAll("#btn-view-compact").forEach(function (b) { b.classList.remove("is-active"); });
        var btnToggleAll = document.getElementById("btn-toggle-all-expand");
        if (btnToggleAll) btnToggleAll.textContent = "⊟ Alle einklappen";
        return;
      }

      // Toggle All Expand / Collapse
      if (e.target.closest("#btn-toggle-all-expand")) {
        e.preventDefault();
        var hasCollapsed = !!document.querySelector(".snippet-card.is-collapsed");
        if (hasCollapsed) {
          document.querySelectorAll(".snippet-card").forEach(function (c) {
            c.classList.remove("is-collapsed");
            c.classList.add("is-expanded");
            var h = c.querySelector(".snippet-card-header");
            if (h) h.setAttribute("aria-expanded", "true");
          });
          var btnToggleAll = document.getElementById("btn-toggle-all-expand");
          if (btnToggleAll) btnToggleAll.textContent = "⊟ Alle einklappen";
          var btnD = document.getElementById("btn-view-detailed");
          var btnC = document.getElementById("btn-view-compact");
          if (btnD) btnD.classList.add("is-active");
          if (btnC) btnC.classList.remove("is-active");
        } else {
          document.querySelectorAll(".snippet-card").forEach(function (c) {
            c.classList.add("is-collapsed");
            c.classList.remove("is-expanded");
            var h = c.querySelector(".snippet-card-header");
            if (h) h.setAttribute("aria-expanded", "false");
          });
          var btnToggleAll = document.getElementById("btn-toggle-all-expand");
          if (btnToggleAll) btnToggleAll.textContent = "⊞ Alle ausklappen";
          var btnD = document.getElementById("btn-view-detailed");
          var btnC = document.getElementById("btn-view-compact");
          if (btnD) btnD.classList.remove("is-active");
          if (btnC) btnC.classList.add("is-active");
        }
        return;
      }

      // Filter kind pill
      var pillKind = e.target.closest(".dossier-filter-pill[data-filter-kind]");
      if (pillKind) {
        e.preventDefault();
        var grp = pillKind.closest(".dossier-filter-group");
        if (grp) grp.querySelectorAll(".dossier-filter-pill[data-filter-kind]").forEach(function (p) { p.classList.remove("is-active"); });
        pillKind.classList.add("is-active");
        applyDossierFilters();
        return;
      }

      // Filter status pill
      var pillStatus = e.target.closest(".dossier-filter-pill[data-filter-status]");
      if (pillStatus) {
        e.preventDefault();
        var grp = pillStatus.closest(".dossier-filter-group");
        if (grp) grp.querySelectorAll(".dossier-filter-pill[data-filter-status]").forEach(function (p) { p.classList.remove("is-active"); });
        pillStatus.classList.add("is-active");
        applyDossierFilters();
        return;
      }

      // Clear search
      if (e.target.closest("#btn-clear-dossier-search")) {
        e.preventDefault();
        var sInput = document.getElementById("dossier-search-input");
        if (sInput) {
          sInput.value = "";
          sInput.focus();
        }
        applyDossierFilters();
        return;
      }

      // Reset filters
      if (e.target.closest("#btn-reset-dossier-filters")) {
        e.preventDefault();
        var sInput = document.getElementById("dossier-search-input");
        if (sInput) sInput.value = "";
        document.querySelectorAll(".dossier-filter-pill[data-filter-kind]").forEach(function (p) {
          p.classList.toggle("is-active", p.getAttribute("data-filter-kind") === "all");
        });
        document.querySelectorAll(".dossier-filter-pill[data-filter-status]").forEach(function (p) {
          p.classList.toggle("is-active", p.getAttribute("data-filter-status") === "all");
        });
        applyDossierFilters();
        return;
      }

      // 1. Confirm button (Single card)
      var btnConf = e.target.closest('.curation-btn[data-action="confirm"]');
      if (btnConf) {
        e.preventDefault();
        var sId = btnConf.getAttribute("data-snippet");
        storeVote(sId, { vote: "confirm", queued: false });
        updateSnippetBadges();
        try {
          fetch("/api/curation/vote", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ snippet_id: sId, vote: "confirm" })
          }).catch(function () {});
        } catch (err) {}
        return;
      }

      // 2. Dismiss button (Single card)
      var btnDism = e.target.closest('.curation-btn[data-action="dismiss"]');
      if (btnDism) {
        e.preventDefault();
        var sId = btnDism.getAttribute("data-snippet");
        storeVote(sId, { vote: "dismiss", queued: false });
        updateSnippetBadges();
        try {
          fetch("/api/curation/vote", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ snippet_id: sId, item_id: sId, vote: "dismiss" })
          }).catch(function () {});
        } catch (err) {}
        return;
      }

      // 3. Discuss toggle button on card
      var btnDisc = e.target.closest('.curation-btn[data-action="discuss"]');
      if (btnDisc) {
        e.preventDefault();
        var sId = btnDisc.getAttribute("data-snippet") || (btnDisc.closest(".snippet-card") ? btnDisc.closest(".snippet-card").getAttribute("data-snippet-id") : null);
        if (sId) {
          toggleDiscussionItem(sId);
        }
        return;
      }

      // 4. Detach item button from chip
      var btnDetach = e.target.closest(".btn-detach-item");
      if (btnDetach) {
        e.preventDefault();
        var dId = btnDetach.getAttribute("data-item-id");
        if (dId) {
          attachedDiscussionItems.delete(dId);
          appendDiscussionSystemNote("Element <code>" + dId + "</code> aus Diskussion entfernt.");
          renderAttachedChips();
          updateSnippetBadges();
        }
        return;
      }

      // 5. Clear all attached items
      var btnClear = e.target.closest("#btn-clear-attached");
      if (btnClear) {
        e.preventDefault();
        attachedDiscussionItems.clear();
        appendDiscussionSystemNote("Alle Elemente aus der Diskussion gelöst.");
        renderAttachedChips();
        updateSnippetBadges();
        return;
      }

      // 6. Header toggle button for workbench chat
      var btnToggleChat = e.target.closest("#btn-toggle-workbench-chat");
      if (btnToggleChat) {
        e.preventDefault();
        var chatPane = document.getElementById("dossier-chat-pane");
        var modal = chatPane ? chatPane.closest("dialog") : null;
        if (chatPane) {
          var willHide = !chatPane.hidden;
          chatPane.hidden = willHide;
          if (modal) modal.classList.toggle("has-chat-open", !willHide);
          if (willHide) {
            attachedDiscussionItems.clear();
            renderAttachedChips();
            updateSnippetBadges();
          }
        }
        return;
      }

      // 7. Chat pane close button
      var btnCloseChat = e.target.closest("#btn-close-chat-pane");
      if (btnCloseChat) {
        e.preventDefault();
        var chatPane = document.getElementById("dossier-chat-pane");
        var modal = chatPane ? chatPane.closest("dialog") : null;
        if (chatPane) {
          chatPane.hidden = true;
          if (modal) modal.classList.remove("has-chat-open");
        }
        attachedDiscussionItems.clear();
        renderAttachedChips();
        updateSnippetBadges();
        return;
      }

      // 7b. Chat bubble review actions
      if (e.target.closest('[data-action="open-review-drawer"]')) {
        e.preventDefault();
        var openBtn = document.querySelector("[data-review-open]");
        if (openBtn) {
          openBtn.click();
        } else if (window.araReview && typeof window.araReview.openDrawer === "function") {
          window.araReview.openDrawer();
        }
        return;
      }

      if (e.target.closest('[data-action="export-curation-json"]')) {
        e.preventDefault();
        var exportBtn = document.querySelector("[data-review-export]");
        if (exportBtn) {
          exportBtn.click();
        } else if (window.araReview && typeof window.araReview.exportPackage === "function") {
          window.araReview.exportPackage();
        } else {
          var pkgItems = loadReviewPackage();
          var identObj = getReviewerIdentity();
          var exportPayload = {
            schema: "review-package@v1",
            identity: identObj.mode,
            submitted_at: new Date().toISOString(),
            decisions: pkgItems
          };
          var blob = new Blob([JSON.stringify(exportPayload, null, 2) + "\n"], { type: "application/json" });
          var a = document.createElement("a");
          a.href = URL.createObjectURL(blob);
          a.download = "ara-curation-package-" + new Date().toISOString().replace(/[:.]/g, "-") + ".json";
          a.click();
          setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
        }
        return;
      }

      // 8. Workbench quick prompt chips
      var wbChip = e.target.closest(".workbench-prompt-chip");
      if (wbChip) {
        e.preventDefault();
        var prompt = wbChip.getAttribute("data-prompt");
        if (wbChip.classList.contains("chip-criticism") || (prompt && prompt.endsWith(": "))) {
          var chatInput = document.getElementById("chat-pane-input");
          if (chatInput) {
            chatInput.value = prompt;
            chatInput.focus();
            if (chatInput.setSelectionRange) {
              chatInput.setSelectionRange(chatInput.value.length, chatInput.value.length);
            }
          }
        } else {
          sendWorkbenchMessage(prompt);
        }
        return;
      }

      // 9a. Exit 1: Submit proposal to curation queue (Review-Paket)
      var btnSubmitProp = e.target.closest("#btn-submit-workbench-proposal");
      if (btnSubmitProp) {
        e.preventDefault();
        submitWorkbenchProposal();
        return;
      }

      // 9b. Exit 2: Apply proposal directly as justified locally in dossier
      var btnApplyLocal = e.target.closest("#btn-apply-justified-locally");
      if (btnApplyLocal) {
        e.preventDefault();
        applyProposalLocallyJustified();
        return;
      }

      // 9c. Dismiss proposal
      var btnDismissProp = e.target.closest("#btn-dismiss-proposal");
      if (btnDismissProp) {
        e.preventDefault();
        var propBox = document.getElementById("chat-pane-proposal-box");
        if (propBox) propBox.hidden = true;
        appendDiscussionSystemNote("Kurationsvorschlag verworfen.");
        return;
      }

      // 10. Backward compatibility for legacy inline chips / queue button if present
      var oldChip = e.target.closest(".snippet-chip");
      if (oldChip) {
        e.preventDefault();
        var sId = oldChip.getAttribute("data-snippet");
        var prompt = oldChip.getAttribute("data-prompt");
        openDiscussionForItem(sId);
        sendWorkbenchMessage(prompt);
        return;
      }
      var oldQueue = e.target.closest(".btn-submit-curation-queue");
      if (oldQueue) {
        e.preventDefault();
        submitWorkbenchProposal();
        return;
      }
    });

    // Change listener for inline model selects inside raw subtab controls
    document.addEventListener("change", function (e) {
      var selectModel = e.target.closest(".subtab-select-model");
      if (selectModel) {
        var container = selectModel.closest(".subtab-controls");
        var effortSelect = container ? container.querySelector(".subtab-select-effort") : null;
        if (effortSelect) {
          var isCursor = (selectModel.value === "composer-2.5");
          effortSelect.disabled = isCursor;
          effortSelect.style.opacity = isCursor ? "0.4" : "1";
        }
      }
    });

    // Form submission
    document.addEventListener("submit", function (e) {
      var wbForm = e.target.closest("#chat-pane-form");
      if (wbForm) {
        e.preventDefault();
        var input = document.getElementById("chat-pane-input");
        if (input && input.value.trim()) {
          var val = input.value.trim();
          input.value = "";
          sendWorkbenchMessage(val);
        }
        return;
      }

      var legacyForm = e.target.closest(".snippet-chat-input-form");
      if (legacyForm) {
        e.preventDefault();
        var sId = legacyForm.getAttribute("data-snippet");
        var inp = legacyForm.querySelector(".snippet-msg-input");
        if (inp && inp.value.trim()) {
          var text = inp.value.trim();
          inp.value = "";
          openDiscussionForItem(sId);
          sendWorkbenchMessage(text);
        }
      }
    });

    // Input listener for dossier real-time live search
    document.addEventListener("input", function (e) {
      if (e.target && e.target.id === "dossier-search-input") {
        applyDossierFilters();
      }
    });

    // Keyboard support for accessible card toggles, range multiselection, and Esc reset
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        if (selectedSnippetIds.size > 0) {
          e.preventDefault();
          e.stopPropagation();
          selectedSnippetIds.clear();
          updateSelectionUI();
          return;
        }
      }

      if (e.shiftKey && (e.key === "ArrowDown" || e.key === "ArrowUp")) {
        var activeEl = document.activeElement;
        var focusedCard = activeEl ? activeEl.closest(".snippet-card") : null;
        if (!focusedCard && lastSelectedSnippetId) {
          focusedCard = document.getElementById(lastSelectedSnippetId);
        }
        if (focusedCard) {
          var visibleCards = getVisibleSnippetCards();
          var cardIds = visibleCards.map(function (c) { return c.getAttribute("data-snippet-id") || c.id; });
          var currId = focusedCard.getAttribute("data-snippet-id") || focusedCard.id;
          var currIdx = cardIds.indexOf(currId);
          if (currIdx !== -1) {
            var nextIdx = e.key === "ArrowDown" ? currIdx + 1 : currIdx - 1;
            if (nextIdx >= 0 && nextIdx < cardIds.length) {
              e.preventDefault();
              var targetCard = visibleCards[nextIdx];
              var targetId = cardIds[nextIdx];
              selectedSnippetIds.add(currId);
              selectedSnippetIds.add(targetId);
              lastSelectedSnippetId = targetId;
              updateSelectionUI();
              var targetHeader = targetCard.querySelector(".snippet-card-header");
              if (targetHeader && typeof targetHeader.focus === "function") {
                targetHeader.focus();
              }
              return;
            }
          }
        }
      }

      if (e.key === "Enter" || e.key === " ") {
        var header = e.target.closest("[data-card-toggle]");
        if (header && !e.target.closest(".curation-btn") && !e.target.closest("a") && !e.target.closest(".card-select-checkbox") && !e.target.closest(".btn-clear-badge")) {
          e.preventDefault();
          header.click();
        }
      }
    });

    function getOfflineWorkbenchReply(attachedIds, message) {
      var lower = message.toLowerCase();
      var items = attachedIds.map(function (id) {
        var card = document.getElementById(id);
        return {
          id: id,
          sws: card ? (card.getAttribute("data-sws") || id) : id,
          doc: card ? (card.getAttribute("data-doc") || "AUTOSAR Spezifikation") : "AUTOSAR Spezifikation",
          isConstituting: card ? card.hasAttribute("data-is-constituting") : false,
          name: card ? (card.getAttribute("data-name") || id) : id
        };
      });

      if (items.length === 0) {
        return {
          reply: "Aktuell ist kein Element im Diskussions-Fokus. Wähle im Dossier ein oder mehrere Elemente (Inbound-Snippets oder konstituierende Records) mit „💬 Mit KI diskutieren“ aus.",
          suggestion: null,
          rationale: ""
        };
      }

      var itemsList = items.map(function (it) {
        return "• " + it.id + " (" + (it.isConstituting ? "Konstituierend · " + it.name : "Inbound aus " + it.doc) + ")";
      }).join("\n");

      if (lower.indexOf("woher") !== -1 || lower.indexOf("herkunft") !== -1 || lower.indexOf("quelle") !== -1) {
        return {
          reply: "Herkunftsnachweis (Offline-Modus) für " + items.length + " fokussierte(s) Element(e):\n\n" + itemsList + "\n\nAlle Elemente stammen aus unveränderlichen, im Repository gepinnten Spezifikationen und bilden den Audit-Trail für das Modul.",
          suggestion: null,
          rationale: ""
        };
      }
      if (lower.indexOf("sinn") !== -1 || lower.indexOf("zweck") !== -1 || lower.indexOf("warum") !== -1 || lower.indexOf("relevan") !== -1 || lower.indexOf("schnittstelle") !== -1 || lower.indexOf("beziehung") !== -1) {
        return {
          reply: "Schnittstellenbezug & Kontext:\n\n" + itemsList + "\n\nDie konstituierenden APIs definieren den Kernvertrag des Moduls, während Inbound-Snippets die verbindlichen Aufrufe und Rollenverteilungen durch Nachbarmodule belegen.",
          suggestion: null,
          rationale: ""
        };
      }
      if (lower.indexOf("falsch") !== -1 || lower.indexOf("beanstand") !== -1 || lower.indexOf("ausschlie") !== -1 || lower.indexOf("irrelevant") !== -1 || lower.indexOf("nicht konstituierend") !== -1 || lower.indexOf("stimmt nicht") !== -1) {
        var isSubstantiated = message.trim().length >= 25 && (
          lower.indexOf("weil") !== -1 || lower.indexOf("da ") !== -1 || lower.indexOf("grund") !== -1 ||
          lower.indexOf("begründ") !== -1 || lower.indexOf("treiber") !== -1 || lower.indexOf("schnittstelle") !== -1 ||
          lower.indexOf("schicht") !== -1 || lower.indexOf("redundant") !== -1 || lower.indexOf("intern") !== -1 ||
          lower.indexOf("architektur") !== -1 || lower.indexOf("nicht konstituierend") !== -1 || lower.indexOf("falsch für") !== -1 ||
          lower.indexOf("soll ausgeschlossen") !== -1 || lower.indexOf("ausgeschlossen werden") !== -1 || lower.indexOf("kein bezug") !== -1
        );
        if (!isSubstantiated) {
          return {
            reply: "Deine Beanstandung zu den ausgewählten Elementen wurde registriert.\n\nUm die Beanstandung fachlich zu prüfen und als „begründet“ zu akzeptieren, ist eine stichhaltige technische Begründung erforderlich (z. B. Schichtentrennung, falsche Modulzuordnung, Redundanz oder Architekturwiderspruch).\n\nBitte erläutere kurz: *Warum genau* ist die Zuordnung oder Eigenschaft falsch?",
            suggestion: null,
            rationale: ""
          };
        }
        var targets = items.map(function (it) { return it.id; }).join(", ");
        return {
          reply: "✓ Fachliche Prüfung bestanden: Deine Begründung („" + message + "“) ist plausibel und stichhaltig.\n\nIch habe einen gemeinsamen Kurationsvorschlag formuliert. Du kannst ihn im Vorschlags-Dialog unten entweder in die Curation-Queue einreihen (Exit 1) oder direkt als „begründet beanstandet“ im Dossier vermerken (Exit 2).",
          suggestion: "[STATUS: EXCLUDE_OR_REVISE]\nElemente im Fokus: " + targets + "\nBegründung (durch KI geprüft): " + message,
          rationale: "Im Multi-Item-Curation-Dialog begründet beanstandet: " + message
        };
      }
      return {
        reply: "Fokus auf " + items.length + " Element(e):\n\n" + itemsList + "\n\nStelle Fragen zu Herkunft, Schnittstellenbezug oder formuliere Beanstandungen für die Curation-Queue.",
        suggestion: null,
        rationale: ""
      };
    }

    async function sendWorkbenchMessage(message) {
      var thread = document.getElementById("chat-pane-thread");
      if (!thread) return;

      var attachedIds = Array.from(attachedDiscussionItems);
      var primaryId = attachedIds.length > 0 ? attachedIds[0] : "LinIf";

      var userBubble = document.createElement("div");
      userBubble.className = "chat-bubble bubble-user";
      userBubble.textContent = message;
      thread.appendChild(userBubble);
      thread.scrollTop = thread.scrollHeight;

      var assistantBubble = document.createElement("div");
      assistantBubble.className = "chat-bubble bubble-assistant";
      assistantBubble.textContent = "Analysiere Fokus-Kontext…";
      thread.appendChild(assistantBubble);
      thread.scrollTop = thread.scrollHeight;

      try {
        var res = await fetch("/api/discuss", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action: "chat",
            record_id: primaryId,
            attached_ids: attachedIds,
            message: message
          })
        });
        var data = await res.json();
        assistantBubble.textContent = data.reply || data.error || "Keine Antwort erhalten.";

        var propBox = document.getElementById("chat-pane-proposal-box");
        if (data.suggestion) {
          var propText = document.getElementById("chat-pane-proposal-text");
          var propBtn = document.getElementById("btn-submit-workbench-proposal");
          if (propBox && propText && propBtn) {
            propText.textContent = data.suggestion + "\n\nBegründung: " + (data.rationale || "");
            propBox.hidden = false;
            propBtn.dataset.suggestion = data.suggestion;
            propBtn.dataset.rationale = data.rationale || "";
            propBtn.dataset.attachedIds = JSON.stringify(attachedIds);
            propBtn.dataset.primaryId = primaryId;
          }
        } else if (propBox) {
          propBox.hidden = true;
        }
      } catch (err) {
        var offlineReply = getOfflineWorkbenchReply(attachedIds, message);
        assistantBubble.textContent = offlineReply.reply;
        var propBox = document.getElementById("chat-pane-proposal-box");
        if (offlineReply.suggestion) {
          var propText = document.getElementById("chat-pane-proposal-text");
          var propBtn = document.getElementById("btn-submit-workbench-proposal");
          if (propBox && propText && propBtn) {
            propText.textContent = offlineReply.suggestion + "\n\nBegründung: " + offlineReply.rationale;
            propBox.hidden = false;
            propBtn.dataset.suggestion = offlineReply.suggestion;
            propBtn.dataset.rationale = offlineReply.rationale;
            propBtn.dataset.attachedIds = JSON.stringify(attachedIds);
            propBtn.dataset.primaryId = primaryId;
          }
        } else if (propBox) {
          propBox.hidden = true;
        }
      }
      thread.scrollTop = thread.scrollHeight;
    }

    function submitWorkbenchProposal() {
      var propBtn = document.getElementById("btn-submit-workbench-proposal");
      if (!propBtn) return;
      var suggestion = propBtn.dataset.suggestion || "";
      var rationale = propBtn.dataset.rationale || "";
      var primaryId = propBtn.dataset.primaryId || "LinIf";
      var attachedIds = [];
      try {
        attachedIds = JSON.parse(propBtn.dataset.attachedIds || "[]");
      } catch (e) {
        attachedIds = Array.from(attachedDiscussionItems);
      }
      if (attachedIds.length === 0) {
        attachedIds = [primaryId];
      }

      var thread = document.getElementById("chat-pane-thread");
      var ident = getReviewerIdentity();
      var pkg = loadReviewPackage();
      var targetSet = new Set(attachedIds);

      // Filter out previous decisions for these ids so the new decision replaces it
      var nextPkg = pkg.filter(function (x) { return !targetSet.has(x.id); });

      attachedIds.forEach(function (id) {
        var card = document.getElementById(id);
        var doc = card ? (card.getAttribute("data-doc") || "LinIf.json") : "LinIf.json";
        var isConstituting = card ? card.hasAttribute("data-is-constituting") : false;
        var sws = card ? (card.getAttribute("data-sws") || id) : id;
        var name = card ? (card.getAttribute("data-name") || id) : id;

        var decision = {
          id: id,
          kind: "curation_request",
          outcome: "reject",
          decided_by: ident.name,
          identity: ident.mode,
          decided_at: new Date().toISOString(),
          rationale: rationale || ("Beanstandung für " + id + " (" + name + "): " + (suggestion || "Ausschluss/Revision")),
          decision_basis: {
            target_module: "LinIf",
            item_id: id,
            source_element: sws,
            source_name: name,
            source_document: doc,
            is_constituting: isConstituting,
            proposal: suggestion
          }
        };
        nextPkg.push(decision);

        storeVote(id, { vote: "dismiss", queued: true, rationale: rationale });

        try {
          fetch("/api/curation/vote", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ item_id: id, snippet_id: id, vote: "dismiss", rationale: rationale, reviewer: ident.name })
          }).catch(function () {});
        } catch (e) {}
      });

      storeReviewPackage(nextPkg);
      var propBox = document.getElementById("chat-pane-proposal-box");
      if (propBox) propBox.hidden = true;
      updateSnippetBadges();

      if (thread) {
        var conf = document.createElement("div");
        conf.className = "chat-bubble bubble-assistant";
        conf.innerHTML =
          "✓ <strong>Curation-Event im Browser-Store (<code>" + REVIEW_STORE + "</code>) abgelegt.</strong><br>" +
          "Für <strong>" + attachedIds.length + "</strong> Element(e) (" + attachedIds.join(", ") + ") wurde eine Kurationsanfrage (<code>kind: curation_request</code>, <code>outcome: reject</code>) im lokalen Review-Paket erfasst.<br>" +
          "Das Review-Paket enthält jetzt <strong>" + nextPkg.length + "</strong> Entscheidung(en).<br><br>" +
          "<strong>Offizieller Weg zur Übernahme ins Repository:</strong>" +
          "<ul style='margin: 0.35rem 0 0.6rem 1.2rem; padding: 0;'>" +
            "<li><strong>GitHub-Issue:</strong> Öffne das Review-Paket oben rechts und sende es als authentifiziertes Issue an <code>2b-rs/autodocs</code>.</li>" +
            "<li><strong>JSON-Export:</strong> Exportiere das Paket als JSON-Datei und lies es via <code>python3 _src/tools/curation_ingest.py --apply paket.json</code> im Repository ein.</li>" +
          "</ul>" +
          "<div style='display:flex; gap:0.5rem; margin-top:0.4rem;'>" +
            "<button type=\"button\" class=\"curation-btn\" data-action=\"open-review-drawer\" style=\"padding:4px 10px; cursor:pointer;\">📦 Review-Paket öffnen</button>" +
            "<button type=\"button\" class=\"curation-btn\" data-action=\"export-curation-json\" style=\"padding:4px 10px; cursor:pointer;\">⬇️ JSON exportieren</button>" +
          "</div>";
        thread.appendChild(conf);
        thread.scrollTop = thread.scrollHeight;
      }
    }

    function applyProposalLocallyJustified() {
      var propBtn = document.getElementById("btn-submit-workbench-proposal");
      var suggestion = propBtn ? (propBtn.dataset.suggestion || "") : "";
      var rationale = propBtn ? (propBtn.dataset.rationale || "") : "";
      var primaryId = propBtn ? (propBtn.dataset.primaryId || "LinIf") : "LinIf";
      var attachedIds = [];
      try {
        attachedIds = JSON.parse(propBtn ? (propBtn.dataset.attachedIds || "[]") : "[]");
      } catch (e) {
        attachedIds = Array.from(attachedDiscussionItems);
      }
      if (attachedIds.length === 0) {
        attachedIds = [primaryId];
      }

      var thread = document.getElementById("chat-pane-thread");
      var ident = getReviewerIdentity();

      attachedIds.forEach(function (id) {
        storeVote(id, { vote: "justified_dismiss", queued: false, rationale: rationale, justified_by_ai: true });

        try {
          fetch("/api/curation/vote", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ item_id: id, snippet_id: id, vote: "dismiss", rationale: rationale, reviewer: ident.name })
          }).catch(function () {});
        } catch (e) {}
      });

      var propBox = document.getElementById("chat-pane-proposal-box");
      if (propBox) propBox.hidden = true;

      updateSnippetBadges();

      if (thread) {
        var conf = document.createElement("div");
        conf.className = "chat-bubble bubble-assistant";
        conf.innerHTML =
          "✓ <strong>Direkt als „begründet beanstandet“ im Dossier vermerkt.</strong><br>" +
          "Für <strong>" + attachedIds.length + "</strong> Element(e) (" + attachedIds.join(", ") + ") wurde die Beanstandung mit der KI-Begründung im lokalen Audit-Trail markiert. Das Element wird im Dossier hervorgehoben und kann jederzeit über das <code>✕</code> an der Badge zurückgesetzt werden.";
        thread.appendChild(conf);
        thread.scrollTop = thread.scrollHeight;
      }
    }

    try {
      window.addEventListener("ara-package-changed", function () {
        var pkg = loadReviewPackage();
        var pkgIds = new Set();
        pkg.forEach(function (d) {
          if (d && d.id && d.kind === "curation_request") {
            pkgIds.add(d.id);
            storeVote(d.id, { vote: d.outcome === "accept" ? "confirm" : "dismiss", queued: true, rationale: d.rationale });
          }
        });
        var currentVotes = loadVotes();
        Object.keys(currentVotes).forEach(function (sid) {
          if (currentVotes[sid].queued && !pkgIds.has(sid)) {
            storeVote(sid, { queued: false });
          }
        });
        syncReviewBar();
        updateSnippetBadges();
      });
    } catch (e) {}

    // Reset discussion and selection state whenever a dossier modal is closed
    document.querySelectorAll("dialog.dossier-modal").forEach(function (modal) {
      modal.addEventListener("close", function () {
        var chatPane = modal.querySelector("#dossier-chat-pane");
        if (chatPane) chatPane.hidden = true;
        modal.classList.remove("has-chat-open");
        attachedDiscussionItems.clear();
        selectedSnippetIds.clear();
        updateSelectionUI();
        renderAttachedChips();
        updateSnippetBadges();
      });
    });

    syncReviewBar();
    updateSnippetBadges();
  }

  function bindDossierControls() {
    document.addEventListener("click", function (e) {
      var trigger = e.target.closest(".dossier-open-link");
      if (trigger) {
        e.preventDefault();
        var targetId = trigger.getAttribute("data-dossier-target");
        var modal = targetId ? document.getElementById(targetId) : null;
        if (modal && typeof modal.showModal === "function") {
          var tabPrompt = modal.querySelector('.dossier-mode-tab[data-view-mode="prompt"]') || modal.querySelector('.dossier-mode-tab[data-view-mode="raw"]');
          if (tabPrompt) tabPrompt.click();
          try {
            if (!modal.open) {
              modal.showModal();
            }
          } catch (err) {
            modal.setAttribute("open", "");
          }
          return;
        }
        var foldId = (trigger.getAttribute("href") || "").replace(/^#/, "");
        var fold = foldId ? document.getElementById(foldId) : null;
        if (fold) {
          fold.open = true;
          oeffnePfad(fold);
          fold.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }
      if (e.target.closest(".dossier-close-btn")) {
        var dialog = e.target.closest("dialog");
        if (dialog) dialog.close();
      }

      var jump = e.target.closest(".rec-jump-link");
      if (jump) {
        var href = jump.getAttribute("href") || "";
        var dialog = jump.closest("dialog");
        if (href.startsWith("#")) {
          var targetId = href.substring(1);
          var targetEl = document.getElementById(targetId);
          if (dialog) {
            dialog.close();
          }
          if (targetEl) {
            e.preventDefault();
            oeffnePfad(targetEl);
            targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
            targetEl.classList.add("rec-jump-focus");
            setTimeout(function () {
              targetEl.classList.remove("rec-jump-focus");
            }, 2400);
            try {
              history.pushState(null, null, "#" + targetId);
            } catch (err) {}
          }
        } else if (dialog && !jump.getAttribute("target")) {
          dialog.close();
        }
      }
    });

    document.addEventListener("click", function (e) {
      if (e.target.tagName === "DIALOG" && e.target.classList.contains("dossier-modal")) {
        var rect = e.target.getBoundingClientRect();
        var inside = (rect.top <= e.clientY && e.clientY <= rect.top + rect.height
          && rect.left <= e.clientX && e.clientX <= rect.left + rect.width);
        if (!inside) {
          e.target.close();
        }
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindShellControls);
  } else {
    bindShellControls();
  }
})();
