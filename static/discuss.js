/**
 * Discuss with AI — dockable panel, context inspector, proposal-only submission.
 *
 * Live mode posts to /api/discuss. Offline mode answers from the page context
 * and does not claim that the curation queue was written.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.AiDiscuss = api;
  if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", api.init);
    else api.init();
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  // Lokaler Dienst: relativ auf localhost, sonst über die geprüfte localhost-Adresse (ai-access.js).
  function localApi(path) { var a = typeof window !== "undefined" && window.AiAccess; return a && a.localUrl ? a.localUrl(path) : path; }

  var PRIVACY_BADGE = "Keine internen Geheimnisse übertragen";
  var CONTEXT_TEXT_LIMIT = 6000;
  var TRUNCATION_MARK = "\n…[Kontext gekürzt]";
  var REDACTION = "[REDACTED]";
  var PROMPT_EXPLAIN = "Erkläre diese Anforderung einfach";
  var PROMPT_DEPS = "Gibt es Abhängigkeiten?";
  var PROMPT_IMPROVE = "Formuliere einen Verbesserungsvorschlag";
  var QUICK_PROMPTS = [PROMPT_EXPLAIN, PROMPT_DEPS, PROMPT_IMPROVE];
  var PANEL = {
    title: "Discuss with AI",
    sendLabel: "Send",
    inspectorLabel: "Kontext-Inspektor (Was die KI sieht)",
    privacyBadge: PRIVACY_BADGE,
    deriveLabel: "Vorschlag ableiten",
    submitLabel: "In Curation übergeben",
    dockLabel: "Andocken",
    closeLabel: "Schließen",
    authority: "Vorschläge werden nicht selbst freigegeben."
  };
  var SECRET_SOURCES = [
    /-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/g,
    /\b(api[_-]?key|secret|password|passwd|bearer)\b\s*[:=]\s*\S+/gi,
    /\b(ghp_|github_pat_|sk-|xai-|AKIA)[A-Za-z0-9_\-]{8,}/g
  ];
  var REQ_ID = /^[A-Z][A-Z0-9_]{1,63}$/;

  function estimateTokens(text) {
    if (!text) return 0;
    var bytes = typeof TextEncoder !== "undefined"
      ? new TextEncoder().encode(text).length
      : unescape(encodeURIComponent(text)).length;
    return Math.floor((bytes + 3) / 4);
  }

  function redactSecrets(text) {
    var count = 0;
    var value = String(text == null ? "" : text);
    SECRET_SOURCES.forEach(function (source) {
      var pattern = new RegExp(source.source, source.flags);
      value = value.replace(pattern, function () {
        count += 1;
        return REDACTION;
      });
    });
    return { text: value, count: count };
  }

  function transmittedText(context) {
    var citations = (context.cited_references || []).map(function (item) {
      return [item.id || "", item.document || "", item.href || ""].join(" ");
    });
    return [
      context.record_id || "",
      context.universe || "",
      context.module || "",
      context.requirement_text || "",
      (context.parent_ids || []).join(" "),
      citations.join(" ")
    ].join("\n");
  }

  function packageContextFromFields(fields) {
    fields = fields || {};
    var redacted = redactSecrets(fields.requirementText || "");
    var requirement = redacted.text;
    var originalChars = requirement.length;
    var truncated = false;
    var diffBasis = "full-record";
    if (requirement.length > CONTEXT_TEXT_LIMIT) {
      requirement = requirement.slice(0, CONTEXT_TEXT_LIMIT).replace(/\s+$/, "") + TRUNCATION_MARK;
      truncated = true;
      diffBasis = "truncated-context";
    }
    var parents = [];
    (fields.parentIds || []).forEach(function (id) {
      if (REQ_ID.test(id) && parents.indexOf(id) === -1 && id !== fields.recordId) parents.push(id);
    });
    var cited = [];
    var seen = {};
    (fields.citedReferences || []).forEach(function (item) {
      if (!item) return;
      var href = item.href && /^https?:\/\//.test(item.href) ? item.href : "";
      var entry = {
        id: item.id || "",
        document: item.document || "",
        page: typeof item.page === "number" ? item.page : null,
        href: href
      };
      var key = [entry.id, entry.document, entry.href, entry.page].join("|");
      if (seen[key] || (!entry.id && !entry.document && !entry.href)) return;
      seen[key] = true;
      cited.push(entry);
    });
    var context = {
      record_id: fields.recordId || "",
      canonical_id: fields.canonicalId || "",
      universe: fields.universe || "",
      module: fields.module || "",
      requirement_text: requirement,
      parent_ids: parents,
      cited_references: cited,
      found: fields.found !== false && !!fields.recordId,
      truncated: truncated,
      original_chars: originalChars,
      omitted_reason: fields.found === false ? "record-not-found" : "",
      redaction_count: redacted.count,
      privacy_badge: PRIVACY_BADGE,
      diff_basis: diffBasis
    };
    context.token_count = estimateTokens(transmittedText(context));
    return context;
  }

  function textList(rootNode, selector) {
    if (!rootNode || !rootNode.querySelectorAll) return [];
    return Array.prototype.map.call(rootNode.querySelectorAll(selector), function (node) {
      return (node.textContent || "").replace(/\s+/g, " ").trim();
    }).filter(Boolean);
  }

  function packageContextFromArticle(article, page) {
    page = page || {};
    var desc = textList(article, ".desc, .syntax, .recname, .ai p, .ai h3, .ai h4, .ai li, .diagram-note").join("\n");
    var props = [];
    if (article && article.querySelectorAll) {
      Array.prototype.forEach.call(article.querySelectorAll("table.props tr"), function (row) {
        var cells = row.querySelectorAll("th, td");
        if (!cells.length) return;
        var parts = Array.prototype.map.call(cells, function (cell) {
          return (cell.textContent || "").replace(/\s+/g, " ").trim();
        }).filter(Boolean);
        if (parts.length) props.push(parts.join(": "));
      });
    }
    var parents = [];
    var cited = [];
    if (article && article.querySelectorAll) {
      Array.prototype.forEach.call(article.querySelectorAll("a"), function (link) {
        var label = (link.textContent || "").replace(/\s+/g, " ").trim().replace(/^\[|\]$/g, "");
        var href = link.getAttribute("href") || "";
        if (link.closest(".ups") && REQ_ID.test(label)) parents.push(label);
        if (/^https?:\/\//.test(href)) cited.push({ id: REQ_ID.test(label) ? label : "", href: href });
      });
    }
    return packageContextFromFields({
      recordId: (article && article.id) || page.recordId || "",
      universe: page.universe || "",
      module: page.module || "",
      requirementText: [desc, props.join("\n")].filter(Boolean).join("\n"),
      parentIds: parents,
      citedReferences: cited,
      found: !!((article && article.id) || page.recordId)
    });
  }

  function suggestionFor(context) {
    var text = String(context.requirement_text || "").trim();
    if (!text) return null;
    return text + "\n\nPrüfungshinweis: Gültigkeits- und Fehlerbedingungen sind im Anforderungstext nicht ausdrücklich genannt und sollen nur ergänzt werden, wenn die zitierten Verweise sie decken.";
  }

  function rationaleFor(context, source) {
    var basis = context.truncated ? "dem gekürzten Kontext" : "dem vollständigen Kontext";
    return "Abgeleitet aus " + basis + " von " + (context.record_id || "dem Datensatz") + " (" + source + "). Der bestehende Text bleibt erhalten; ergänzt wird nur ein Prüfungshinweis. Keine automatische Freigabe.";
  }

  function contextualReply(message, context) {
    var folded = String(message || "").trim();
    if (!folded) return { error: "empty-message" };
    var recordId = context.record_id || "(kein Datensatz)";
    if (!context.found) {
      return {
        reply: "Für " + recordId + " liegt kein lesbarer Datensatz im Kontext. Es wird kein Anforderungstext ergänzt.",
        suggestion: null,
        rationale: "",
        mode: "offline"
      };
    }
    var text = String(context.requirement_text || "").trim();
    var lower = folded.toLowerCase();
    if (folded === PROMPT_EXPLAIN || lower.indexOf("erklär") !== -1 || lower.indexOf("explain") !== -1) {
      return {
        reply: recordId + " gehört zum Modul " + (context.module || "ohne Modul") + " im Universum " + (context.universe || "") + ". Einfach gesagt steht dort: " + (text || "(kein Anforderungstext im Kontext)"),
        suggestion: null,
        rationale: "",
        mode: "offline"
      };
    }
    if (folded === PROMPT_DEPS || lower.indexOf("abhäng") !== -1 || lower.indexOf("depend") !== -1) {
      var parents = context.parent_ids || [];
      var cites = (context.cited_references || []).map(function (item) {
        return item.id || item.document || item.href;
      }).filter(Boolean);
      return {
        reply: "Für " + recordId + " nennt der Kontext als Eltern-IDs: " + (parents.length ? parents.join(", ") : "keine Eltern-IDs") + ". Zitierte Verweise: " + (cites.length ? cites.join(", ") : "keine zitierten Verweise") + ".",
        suggestion: null,
        rationale: "",
        mode: "offline"
      };
    }
    if (folded === PROMPT_IMPROVE || lower.indexOf("verbesser") !== -1 || lower.indexOf("vorschlag") !== -1) {
      var suggestion = suggestionFor(context);
      if (!suggestion) {
        return {
          reply: "Für " + recordId + " fehlt der Anforderungstext. Ein Änderungsvorschlag wird nicht erfunden.",
          suggestion: null,
          rationale: "",
          mode: "offline"
        };
      }
      var rationale = rationaleFor(context, "Verbesserungsvorschlag");
      return { reply: suggestion + "\n\nBegründung: " + rationale, suggestion: suggestion, rationale: rationale, mode: "offline" };
    }
    if (lower.indexOf("falsch") !== -1 || lower.indexOf("fehler") !== -1 || lower.indexOf("korrektur") !== -1 || lower.indexOf("beanstand") !== -1) {
      var guideSuggestion = "[KORREKTUR für " + recordId + "]\n" + (text ? text.slice(0, 300) : "") + "\n\nBeanstandung: " + folded;
      var guideRationale = "Benutzer-Feedback zur Prüfung vorgemerkt: " + folded;
      return {
        reply: "Deine Beanstandung zu " + recordId + " wurde registriert:\n\n„" + folded + "“\n\nDu kannst über die Schaltfläche „Änderungsvorschlag ableiten“ einen Prüfvorschlag generieren und in die Curation-Queue einreichen oder das Feedback über „Feedback melden“ absenden.",
        suggestion: guideSuggestion,
        rationale: guideRationale,
        mode: "offline"
      };
    }
    return {
      reply: "Zum Datensatz " + recordId + " verwendet die Antwort nur den Inspektor-Kontext: " + (text || "(kein Anforderungstext im Kontext)"),
      suggestion: null,
      rationale: "",
      mode: "offline"
    };
  }

  function makeDiff(recordId, original, suggested) {
    function linesOf(value) {
      var lines = String(value || "").split("\n");
      if (lines.length && lines[lines.length - 1] === "") lines.pop();
      return lines;
    }
    var before = linesOf(original);
    var after = linesOf(suggested);
    var out = ["--- " + recordId + ":current", "+++ " + recordId + ":proposed"];
    var changed = false;
    var max = Math.max(before.length, after.length);
    for (var i = 0; i < max; i += 1) {
      if (before[i] === after[i]) {
        if (before[i] != null) out.push(" " + before[i]);
      } else {
        changed = true;
        if (before[i] != null) out.push("-" + before[i]);
        if (after[i] != null) out.push("+" + after[i]);
      }
    }
    return changed ? out.join("\n") + "\n" : "";
  }

  function newProposalId(recordId) {
    var stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d+Z$/, "Z");
    var tail = Math.random().toString(16).slice(2, 10);
    return "discuss-" + recordId + "-" + stamp + "-" + tail;
  }

  function buildProposal(context, suggestion, rationale, proposalId) {
    if (!context || !context.found) return { error: "record-not-found" };
    var cleanSuggestion = redactSecrets(suggestion || "").text.trim();
    var cleanRationale = redactSecrets(rationale || "").text.trim();
    if (!cleanSuggestion) return { error: "empty-suggestion" };
    if (!cleanRationale) return { error: "empty-rationale" };
    var diff = makeDiff(context.record_id, context.requirement_text || "", cleanSuggestion);
    if (!diff.trim()) return { error: "suggestion-unchanged" };
    return {
      proposal_id: proposalId || newProposalId(context.record_id),
      target_record: context.record_id,
      proposed_diff: diff,
      rationale: cleanRationale,
      suggested_text: cleanSuggestion,
      authority: "proposal-only",
      auto_accepted: false,
      status: "proposed",
      diff_basis: context.diff_basis || "full-record"
    };
  }

  function submissionResult(response, networkError) {
    if (networkError || !response || response.ok !== true || !response.path) {
      return {
        queued: false,
        message: "Die Curation-Queue wurde nicht beschrieben. Der Vorschlag bleibt im Panel."
      };
    }
    return {
      queued: true,
      path: response.path,
      created: response.created !== false,
      message: response.created === false
        ? "Dieser Vorschlag liegt bereits in der Curation-Queue (" + response.path + "). Er wurde nicht überschrieben und nicht freigegeben."
        : "In der Curation-Queue abgelegt (" + response.path + "). Ein Mensch prüft den Vorschlag; er ist nicht freigegeben."
    };
  }

  function threadResetNeeded(previousId, nextId) {
    return !!(previousId && previousId !== nextId);
  }

  function panelContract() {
    return {
      title: PANEL.title,
      sendLabel: PANEL.sendLabel,
      inspectorLabel: PANEL.inspectorLabel,
      privacyBadge: PANEL.privacyBadge,
      deriveLabel: PANEL.deriveLabel,
      submitLabel: PANEL.submitLabel,
      prompts: QUICK_PROMPTS.slice(),
      authority: PANEL.authority
    };
  }

  function currentArticle() {
    var hash = (location.hash || "").replace(/^#/, "");
    if (hash) {
      var byHash = document.getElementById(hash);
      if (byHash && byHash.classList.contains("rec")) return byHash;
    }
    return document.querySelector("article.rec");
  }

  function pageMeta() {
    // Universum aus dem Pfad (classic/…, adaptive/…), Modul aus der Seitenüberschrift;
    // der erste Brotkrumen ist „Start“ und taugt dafür nicht.
    var path = (typeof location !== "undefined" && location.pathname) || "";
    var rel = document.querySelector("header .rel");
    var h1 = document.querySelector("main h1");
    var universe = /\/classic\//.test(path) ? "AUTOSAR Classic Platform"
      : /\/adaptive\//.test(path) ? "AUTOSAR Adaptive Platform"
      : (rel ? rel.textContent.replace(/\s+/g, " ").trim() : "AUTOSAR Adaptive Platform");
    return {
      universe: universe,
      module: h1 ? h1.textContent.replace(/\s+/g, " ").trim() : ""
    };
  }

  function field(label, value) {
    var row = document.createElement("div");
    row.className = "discuss-field";
    var name = document.createElement("dt");
    name.textContent = label;
    var cell = document.createElement("dd");
    cell.textContent = value || "—";
    row.appendChild(name);
    row.appendChild(cell);
    return row;
  }

  function init() {
    if (!document.body || document.getElementById("discuss-panel")) return;
    var style = document.createElement("style");
    style.textContent = [
      ".discuss-panel button:focus-visible,.discuss-panel textarea:focus-visible,.discuss-panel select:focus-visible{outline:3px solid #01696F;outline-offset:2px}",
      ".discuss-panel{position:fixed;z-index:81;right:16px;bottom:64px;width:min(440px,calc(100vw - 16px));max-height:min(78vh,760px);display:flex;flex-direction:column;background:#F9F8F5;color:#28251D;border:1px solid #D4D1CA;border-radius:14px;box-shadow:0 16px 40px rgba(28,27,25,.2);font:15px/1.45 -apple-system,Segoe UI,sans-serif}",
      ".discuss-panel[hidden]{display:none}",
      ".discuss-panel[data-dock='right'],.discuss-panel[data-dock='left']{top:0;bottom:0;max-height:none;height:100vh;border-radius:0;width:min(440px,100vw)}",
      ".discuss-panel[data-dock='right']{right:0}",
      ".discuss-panel[data-dock='left']{left:0;right:auto}",
      ".discuss-panel[data-dock='inline']{position:static;width:100%;max-height:none;margin:12px 0;box-shadow:0 4px 16px rgba(28,27,25,.08);border:1px solid #D4D1CA;border-radius:10px}",
      ".discuss-panel[data-dock='inline'] .discuss-head{border-radius:10px 10px 0 0}",
      ".discuss-head,.discuss-toolbar,.discuss-compose{display:flex;gap:8px;align-items:center}",
      ".discuss-head{padding:10px 12px;background:#01696F;color:#fff;border-radius:14px 14px 0 0}",
      ".discuss-panel[data-dock='right'] .discuss-head,.discuss-panel[data-dock='left'] .discuss-head{border-radius:0}",
      ".discuss-head h2{margin:0;font-size:16px;flex:1}",
      ".discuss-head button,.discuss-toolbar button,.discuss-compose button,.discuss-quick button{background:#fff;color:#01696F;border:1px solid #D4D1CA;border-radius:8px;padding:8px 10px;cursor:pointer;font:inherit}",
      ".discuss-head button{background:transparent;color:#fff;border-color:rgba(255,255,255,.45)}",
      ".discuss-mode{font-size:12px;padding:2px 8px;border-radius:999px;background:#E7F3F4;color:#0C4E54}",
      ".discuss-thread{flex:1;overflow:auto;padding:12px;display:flex;flex-direction:column;gap:8px;min-height:120px}",
      ".discuss-bubble{max-width:92%;padding:8px 10px;border-radius:12px;white-space:pre-wrap;overflow-wrap:anywhere}",
      ".discuss-bubble.user{align-self:flex-end;background:#01696F;color:#fff}",
      ".discuss-bubble.assistant{align-self:flex-start;background:#fff;border:1px solid #D4D1CA}",
      ".discuss-bubble.pending{opacity:.65;font-style:italic;background:#f0f8f8;border:1px dashed #01696F}",
      ".discuss-bubble.error{align-self:flex-start;background:#fdecea;color:#7a1f14;border:1px solid #f1b0a7;font-style:normal;opacity:1}",
      ".discuss-quick,.discuss-toolbar,.discuss-compose,.discuss-inspector,.discuss-proposal{padding:8px 12px}",
      ".discuss-quick{display:flex;flex-wrap:wrap;gap:6px}",
      ".discuss-compose textarea{flex:1;min-height:64px;resize:vertical;border:1px solid #D4D1CA;border-radius:8px;padding:8px;font:inherit;background:#fff;color:#28251D}",
      ".discuss-inspector{border-top:1px solid #D4D1CA;background:#FBFBF9}",
      ".discuss-inspector summary{cursor:pointer;font-weight:650}",
      ".discuss-fields{margin:8px 0}",
      ".discuss-field{display:grid;grid-template-columns:9.5rem 1fr;gap:6px;margin:4px 0}",
      ".discuss-field dt{color:#7A7974}",
      ".discuss-field dd{margin:0;overflow-wrap:anywhere}",
      ".discuss-privacy{display:inline-block;margin:4px 0 0;padding:4px 8px;border-radius:999px;background:#E5F4EA;color:#135C2F;font-size:13px}",
      ".discuss-proposal pre{max-height:160px;overflow:auto;background:#1C1B19;color:#F4F1EA;padding:8px;border-radius:8px;white-space:pre-wrap}",
      ".discuss-note{margin:6px 12px 12px;color:#7A7974;font-size:13px}",
      ".discuss-warn{color:#7A3418}",
      "@media (max-width:700px){.discuss-panel{left:0;right:0;width:100vw;bottom:0;border-radius:14px 14px 0 0}.discuss-field{grid-template-columns:1fr}}"
    ].join("");
    document.head.appendChild(style);

    var panel = document.createElement("aside");
    panel.id = "discuss-panel";
    panel.className = "discuss-panel";
    panel.hidden = true;
    var storedDock = "float";
    try { storedDock = sessionStorage.getItem("ai-discuss-dock") || "float"; } catch (error) { storedDock = "float"; }
    panel.dataset.dock = storedDock;
    panel.setAttribute("role", "complementary");
    panel.setAttribute("aria-labelledby", "discuss-title");

    var head = document.createElement("div");
    head.className = "discuss-head";
    var title = document.createElement("h2");
    title.id = "discuss-title";
    title.textContent = PANEL.title;
    var mode = document.createElement("span");
    mode.className = "discuss-mode";
    mode.textContent = "Live";
    var dock = document.createElement("button");
    dock.type = "button";
    dock.textContent = PANEL.dockLabel;
    var close = document.createElement("button");
    close.type = "button";
    close.textContent = PANEL.closeLabel;
    head.appendChild(title);
    head.appendChild(mode);
    head.appendChild(dock);
    head.appendChild(close);

    var thread = document.createElement("div");
    thread.className = "discuss-thread";
    thread.setAttribute("role", "log");
    thread.setAttribute("aria-live", "polite");

    var quick = document.createElement("div");
    quick.className = "discuss-quick";
    QUICK_PROMPTS.forEach(function (prompt) {
      var button = document.createElement("button");
      button.type = "button";
      button.textContent = prompt;
      button.addEventListener("click", function () { send(prompt); });
      quick.appendChild(button);
    });

    var compose = document.createElement("form");
    compose.className = "discuss-compose";
    var input = document.createElement("textarea");
    input.setAttribute("aria-label", "Nachricht an die KI");
    input.maxLength = 4000;
    var sendButton = document.createElement("button");
    sendButton.type = "submit";
    sendButton.textContent = PANEL.sendLabel;
    compose.appendChild(input);
    compose.appendChild(sendButton);

    var inspector = document.createElement("details");
    inspector.className = "discuss-inspector";
    inspector.open = true;
    var summary = document.createElement("summary");
    summary.textContent = PANEL.inspectorLabel;
    var picker = document.createElement("select");
    picker.setAttribute("aria-label", "Spezifikationseintrag");
    var fields = document.createElement("dl");
    fields.className = "discuss-fields";
    var badge = document.createElement("p");
    badge.className = "discuss-privacy";
    badge.textContent = PANEL.privacyBadge;
    inspector.appendChild(summary);
    inspector.appendChild(picker);
    inspector.appendChild(fields);
    inspector.appendChild(badge);

    var proposalBox = document.createElement("div");
    proposalBox.className = "discuss-proposal";
    proposalBox.hidden = true;
    var derive = document.createElement("button");
    derive.type = "button";
    derive.textContent = PANEL.deriveLabel;
    var diff = document.createElement("pre");
    diff.hidden = true;
    var submit = document.createElement("button");
    submit.type = "button";
    submit.textContent = PANEL.submitLabel;
    submit.disabled = true;
    var warning = document.createElement("p");
    warning.className = "discuss-warn";
    proposalBox.appendChild(derive);
    proposalBox.appendChild(diff);
    proposalBox.appendChild(submit);
    proposalBox.appendChild(warning);

    var note = document.createElement("p");
    note.className = "discuss-note";
    note.textContent = PANEL.authority;

    panel.appendChild(head);
    if (typeof window !== "undefined" && window.AiAccess) {
      var accessRow = document.createElement("div");
      accessRow.className = "discuss-access";
      accessRow.appendChild(window.AiAccess.chip());
      panel.appendChild(accessRow);
    }
    panel.appendChild(thread);
    panel.appendChild(quick);
    panel.appendChild(compose);
    panel.appendChild(inspector);
    panel.appendChild(proposalBox);
    panel.appendChild(note);
    document.body.appendChild(panel);
    document.body.dataset.discussReady = "true";

    var state = { context: null, proposal: null, busy: false, messages: [] };

    function setOpen(open) {
      panel.hidden = !open;
      if (open) input.focus();
    }

    function renderInspector() {
      var context = state.context || packageContextFromFields({ found: false });
      fields.textContent = "";
      [
        ["Current Record ID", context.record_id],
        ["Universe", context.universe],
        ["Module", context.module],
        ["Requirement text", context.requirement_text],
        ["Parent IDs", (context.parent_ids || []).join(", ")],
        ["Cited references", (context.cited_references || []).map(function (item) {
          return item.id || item.document || item.href;
        }).filter(Boolean).join(", ")],
        ["Token count", String(context.token_count || 0)]
      ].forEach(function (pair) {
        fields.appendChild(field(pair[0], pair[1]));
      });
      badge.textContent = context.privacy_badge || PRIVACY_BADGE;
      if (context.redaction_count) badge.textContent += " · " + context.redaction_count + " geschwärzt";
      if (context.truncated) warning.textContent = "Der Diff basiert auf dem gekürzten Kontext, nicht auf dem vollständigen Datensatz.";
    }

    function selectArticle(article) {
      var nextId = (article && article.id) || "";
      if (threadResetNeeded(state.context && state.context.record_id, nextId)) {
        persist();
        thread.textContent = "";
        state.messages = [];
        state.proposal = null;
      }
      state.context = packageContextFromArticle(article, pageMeta());
      if (!state.proposal) {
        diff.hidden = true;
        submit.disabled = true;
      }
      proposalBox.hidden = false;
      renderInspector();
      if (state.context.record_id && !thread.childNodes.length) {
        try {
          var saved = JSON.parse(sessionStorage.getItem("ai-discuss:" + state.context.record_id) || "null");
          if (saved && saved.messages) restore(saved);
        } catch (error) { /* session storage is optional */ }
      }
    }

    function fillPicker() {
      picker.textContent = "";
      var articles = document.querySelectorAll("article.rec, details.fold[id^='ai-']");
      if (!articles.length) {
        var option = document.createElement("option");
        option.value = "";
        option.textContent = "Kein Spezifikationseintrag auf dieser Seite";
        picker.appendChild(option);
        selectArticle(null);
        return;
      }
      Array.prototype.forEach.call(articles, function (article) {
        var option = document.createElement("option");
        option.value = article.id;
        var summary = article.querySelector ? article.querySelector("summary") : null;
        var label = (summary ? summary.textContent.replace(/\s+/g, " ").trim() : "") || article.id || "Eintrag";
        option.textContent = label;
        picker.appendChild(option);
      });
      var initial = currentArticle();
      if (initial && initial.id) picker.value = initial.id;
      selectArticle(initial);
    }

    function bubble(role, text) {
      var node = document.createElement("div");
      node.className = "discuss-bubble " + role;
      node.textContent = text;
      thread.appendChild(node);
      thread.scrollTop = thread.scrollHeight;
      return node;
    }

    function persist() {
      if (!state.context || !state.context.record_id) return;
      try {
        sessionStorage.setItem("ai-discuss:" + state.context.record_id, JSON.stringify({
          messages: state.messages.slice(-40),
          proposal: state.proposal
        }));
      } catch (error) { /* keep the visible thread if storage is full */ }
    }

    function restore(saved) {
      state.messages = saved.messages || [];
      state.messages.forEach(function (item) { bubble(item.role, item.text); });
      if (saved.proposal) showProposal(saved.proposal);
    }

    function showProposal(proposal) {
      state.proposal = proposal;
      proposalBox.hidden = false;
      diff.hidden = false;
      diff.textContent = proposal.proposed_diff || "";
      submit.disabled = !proposal.proposal_id;
      if (proposal.diff_basis === "truncated-context") {
        warning.textContent = "Der Diff basiert auf dem gekürzten Kontext, nicht auf dem vollständigen Datensatz.";
      }
      persist();
    }

    function applyServerContext(context) {
      if (!context) return;
      state.context = context;
      renderInspector();
    }

    function isNetworkError(error) {
      return error instanceof TypeError || /Failed to fetch|NetworkError|Load failed|Unexpected token|JSON/i.test(String(error && error.message));
    }

    // Kleine Zeile unter der Antwort: welcher Zugang und welches Modell geantwortet haben.
    function addAnswerMeta(bubbleEl, text) {
      if (!text || !bubbleEl) return;
      var meta = document.createElement("div");
      meta.className = "discuss-answer-meta";
      meta.textContent = text;
      bubbleEl.appendChild(meta);
    }

    async function postDiscuss(payload) {
      var response = await fetch(localApi("/api/discuss"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      var data = await response.json();
      if (!response.ok || !data.ok) {
        var error = new Error((data && data.error) || "discuss-failed");
        error.payload = data;
        throw error;
      }
      mode.textContent = "Live";
      applyServerContext(data.context);
      return data;
    }

    async function send(message) {
      var text = String(message || input.value || "").trim();
      if (!text || state.busy) return;
      state.busy = true;
      sendButton.disabled = true;
      input.value = "";
      bubble("user", text);
      state.messages.push({ role: "user", text: text });

      var assistantBubble = bubble("assistant pending", "");
      var hzBadge = document.createElement("span");
      hzBadge.className = "discuss-hz-badge";
      hzBadge.style.cssText = "display:inline-block; font-size:0.7em; background:#059669; color:#fff; border-radius:3px; padding:1px 5px; margin-right:6px; font-weight:700; font-variant-numeric:tabular-nums;";
      hzBadge.textContent = "Live";
      var streamTextEl = document.createElement("span");
      streamTextEl.className = "discuss-stream-text";
      streamTextEl.textContent = "Verbinde mit KI-Backend…";
      assistantBubble.appendChild(hzBadge);
      assistantBubble.appendChild(streamTextEl);

      var answer = null;
      var accumulated = "";
      var updateCount = 0;
      var tStart = performance.now();
      var failure = null;

      function showFailure(msg) {
        failure = msg;
        assistantBubble.classList.remove("pending");
        assistantBubble.classList.add("error");
        hzBadge.style.display = "none";
        streamTextEl.textContent = "⚠️ Keine KI-Antwort: " + msg;
      }

      // Route: eigener Schlüssel (BYOK, direkt beim Anbieter), lokale CLI über /api/discuss
      // oder – ohne Anmeldung/Modell – eine Einladungskarte statt eines Fehlers.
      var access = typeof window !== "undefined" ? window.AiAccess : null;
      var aiRoute = access ? await access.route() : { kind: "local" };
      if (aiRoute.kind === "none") {
        assistantBubble.classList.remove("pending");
        assistantBubble.textContent = "";
        assistantBubble.appendChild(access.gate(aiRoute.reason));
        state.messages.pop();
        input.value = text;
        state.busy = false;
        sendButton.disabled = false;
        return;
      }
      if (aiRoute.kind === "byok") {
        hzBadge.textContent = access.routeLabel(aiRoute);
        streamTextEl.textContent = "KI überlegt…";
        try {
          answer = await access.discuss({
            route: aiRoute,
            message: text,
            context: state.context,
            onDelta: function (delta, all) {
              accumulated = all;
              streamTextEl.textContent = all;
              assistantBubble.classList.remove("pending");
            },
            // Gemini-Abo ohne Streaming: „Wartet auf Läufer …“ / „Modell denkt …“ mit Wartezeit.
            onStatus: function (status) { streamTextEl.textContent = status; }
          });
          streamTextEl.textContent = answer.reply;
          assistantBubble.classList.remove("pending");
          hzBadge.style.display = "none";
          mode.textContent = aiRoute.provider === "abo" ? "Gemini-Abo" : aiRoute.provider === "project" ? "Projektkontingent" : "Eigener Schlüssel";
          addAnswerMeta(assistantBubble, access.answerLabel(answer, aiRoute));
        } catch (error) {
          mode.textContent = "Fehler";
          showFailure(String((error && error.message) || error));
          answer = null;
        }
      } else try {
        var response = await fetch(localApi("/api/discuss"), {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
          },
          body: JSON.stringify({
            action: "chat",
            stream: true,
            record_id: state.context && state.context.record_id,
            message: text,
            context: state.context,
            provider: aiRoute.cli || undefined,
            // Ausweich-CLIs aus „Dein KI-Zugang“: nur bei erschöpftem Kontingent oder nicht erreichbarer CLI.
            fallback: aiRoute.fallback || undefined
          })
        });

        if (!response.ok) {
          var errText = "HTTP " + response.status;
          try { var errJson = await response.json(); if (errJson && errJson.error) errText += " – " + errJson.error; } catch (e) { /* not json */ }
          throw new Error(errText);
        }

        var contentType = response.headers.get("Content-Type") || "";
        if (contentType.includes("text/event-stream") && response.body && response.body.getReader) {
          var reader = response.body.getReader();
          var decoder = new TextDecoder("utf-8");
          var buffer = "";

          while (true) {
            var res = await reader.read();
            if (res.done) break;
            buffer += decoder.decode(res.value, { stream: true });
            var lines = buffer.split("\n");
            buffer = lines.pop();

            for (var i = 0; i < lines.length; i++) {
              var line = lines[i].trim();
              if (!line.startsWith("data: ")) continue;
              var jsonStr = line.slice(6).trim();
              if (!jsonStr) continue;
              var ev = null;
              try { ev = JSON.parse(jsonStr); } catch (e) { ev = null; }
              if (!ev) continue;
              updateCount++;
              var elapsedSec = ((performance.now() - tStart) / 1000).toFixed(1);
              var currentHz = (updateCount / Math.max(0.1, (performance.now() - tStart) / 1000)).toFixed(1);
              hzBadge.textContent = "Live " + currentHz + " Hz";

              if (ev.event === "delta") {
                accumulated += (ev.delta || "");
                streamTextEl.textContent = accumulated;
                assistantBubble.classList.remove("pending");
              } else if (ev.event === "fallback" && !accumulated) {
                streamTextEl.textContent = access && access.fallbackText ? access.fallbackText(ev) : (ev.to_name || ev.to || "") + " …";
              } else if (ev.event === "thinking" && !accumulated) {
                streamTextEl.textContent = "Denkvorgang läuft… (" + elapsedSec + " s)";
              } else if ((ev.event === "tick" || ev.event === "start") && !accumulated) {
                streamTextEl.textContent = "KI überlegt… (" + elapsedSec + " s)";
              } else if (ev.event === "complete") {
                if (ev.ok === false) throw new Error(ev.error || "Modell lieferte keine Antwort.");
                answer = ev;
                accumulated = ev.reply || accumulated;
                streamTextEl.textContent = accumulated;
                assistantBubble.classList.remove("pending");
                hzBadge.style.display = "none";
              } else if (ev.event === "error") {
                throw new Error(ev.error || "Der KI-Agent hat einen Fehler gemeldet.");
              }
            }
          }
          if (!answer) throw new Error("Verbindung beendet, bevor das Modell eine Antwort geliefert hat.");
          mode.textContent = "Live";
        } else {
          var data = await response.json();
          if (!data || data.ok === false || !data.reply) throw new Error((data && data.error) || "Leere Antwort vom Server.");
          answer = data;
          streamTextEl.textContent = answer.reply;
          assistantBubble.classList.remove("pending");
          hzBadge.style.display = "none";
          mode.textContent = "Live";
        }
      } catch (error) {
        var isOffline = error instanceof TypeError || /Failed to fetch|NetworkError|Load failed/i.test(String(error && error.message));
        mode.textContent = isOffline ? "Offline" : "Fehler";
        showFailure(isOffline
          ? "Kein lokales KI-Backend erreichbar. Die Diskussion benötigt den lokalen Server (_src/serve.py); auf der statischen Website ist sie nicht verfügbar."
          : String((error && error.message) || error));
        answer = null;
      }

      if (!failure && answer && aiRoute.kind !== "byok" && access) addAnswerMeta(assistantBubble, access.answerLabel(answer, aiRoute));
      state.messages.push(failure ? {
        role: "assistant error",
        text: "⚠️ Keine KI-Antwort: " + failure,
        suggestion: null,
        rationale: ""
      } : {
        role: "assistant",
        text: (answer && answer.reply) || accumulated || "",
        suggestion: (answer && answer.suggestion) || null,
        rationale: (answer && answer.rationale) || "",
        provider: (answer && answer.provider) || "",
        model: (answer && answer.model) || ""
      });
      persist();
      state.busy = false;
      sendButton.disabled = false;
    }

    async function deriveProposal() {
      var last = null;
      for (var i = state.messages.length - 1; i >= 0; i -= 1) {
        if (state.messages[i].role === "assistant") { last = state.messages[i]; break; }
      }
      var suggestion = last && last.suggestion;
      var rationale = last && last.rationale;
      if (!suggestion || !rationale) {
        warning.textContent = "Kein Änderungsvorschlag vorhanden: Die letzte KI-Antwort enthielt keinen konkreten Vorschlag. Bitte die KI ausdrücklich um einen Änderungsvorschlag bitten.";
        return;
      }
      try {
        var data = await postDiscuss({
          action: "propose",
          record_id: state.context && state.context.record_id,
          suggestion: suggestion,
          rationale: rationale
        });
        showProposal(data.proposal);
      } catch (error) {
        if (isNetworkError(error) && window.AiAccess) {
          // Ohne Backend (öffentliche Seite): Vorschlag geht als GitHub-Issue an den Kurationseingang.
          showProposal({
            proposal_id: "github-issue",
            via: "github-issue",
            target_record: state.context && state.context.record_id,
            suggested_text: suggestion,
            rationale: rationale,
            proposed_diff: suggestion
          });
          return;
        }
        mode.textContent = "Offline";
        warning.textContent = "Änderungsvorschlag nicht abgeleitet: Server nicht erreichbar oder Fehler (" + String((error && error.message) || error) + ").";
      }
    }

    async function submitProposal() {
      if (!state.proposal) {
        await deriveProposal();
      }
      if (!state.proposal || state.busy) return;
      state.busy = true;
      submit.disabled = true;
      var result;
      if (state.proposal.via === "github-issue") {
        var last = null;
        for (var j = state.messages.length - 1; j >= 0; j -= 1) {
          if (state.messages[j].role === "assistant") { last = state.messages[j]; break; }
        }
        var issue = window.AiAccess.proposalIssue({
          record_id: state.proposal.target_record,
          suggestion: state.proposal.suggested_text,
          rationale: state.proposal.rationale,
          provider: last && last.provider,
          model: last && last.model
        });
        await window.AiAccess.openIssue(issue.title, issue.body);
        warning.textContent = "Vorschlag als GitHub-Issue vorbereitet. Nach dem Absenden prüft ihn ein Mensch; er ist nicht freigegeben.";
        bubble("assistant", warning.textContent);
        state.busy = false;
        submit.disabled = false;
        persist();
        return;
      }
      try {
        var data = await postDiscuss({
          action: "submit",
          record_id: state.proposal.target_record,
          proposal_id: state.proposal.proposal_id,
          suggestion: state.proposal.suggested_text,
          rationale: state.proposal.rationale
        });
        if (data.proposal) showProposal(Object.assign({}, state.proposal, data.proposal));
        result = submissionResult(data, false);
      } catch (error) {
        mode.textContent = "Offline";
        result = submissionResult(null, true);
      }
      warning.textContent = result.message;
      bubble("assistant", result.message);
      state.busy = false;
      submit.disabled = !state.proposal;
      persist();
    }

    close.addEventListener("click", function () { setOpen(false); });
    dock.addEventListener("click", function () {
      if (panel.dataset.dock === "inline") {
        document.body.appendChild(panel);
      }
      var order = ["float", "right", "left"];
      var current = panel.dataset.dock === "inline" ? "float" : panel.dataset.dock;
      var next = order[(order.indexOf(current) + 1) % order.length];
      panel.dataset.dock = next;
      try { sessionStorage.setItem("ai-discuss-dock", next); } catch (error) { /* ignore */ }
    });
    compose.addEventListener("submit", function (event) {
      event.preventDefault();
      send();
    });
    input.addEventListener("keydown", function (event) {
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault();
        send();
      }
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && !panel.hidden) setOpen(false);
    });
    picker.addEventListener("change", function () {
      selectArticle(document.getElementById(picker.value));
    });
    derive.addEventListener("click", deriveProposal);
    submit.addEventListener("click", submitProposal);
    document.addEventListener("click", function (event) {
      var trigger = event.target && event.target.closest ? event.target.closest("[data-open-discuss]") : null;
      if (trigger) {
        event.preventDefault();
        var recId = trigger.getAttribute("data-open-discuss");
        var actions = trigger.closest(".ai-commentary-actions") || trigger.parentElement;
        var isCurrentInline = (panel.dataset.dock === "inline" && panel.previousElementSibling === actions);
        if (isCurrentInline && !panel.hidden) {
          setOpen(false);
          return;
        }
        if (actions && actions.parentNode) {
          actions.parentNode.insertBefore(panel, actions.nextSibling);
          panel.dataset.dock = "inline";
        }
        if (recId && document.getElementById(recId)) {
          selectArticle(document.getElementById(recId));
          if (picker) picker.value = recId;
        }
        setOpen(true);
        try { panel.scrollIntoView({ behavior: "smooth", block: "nearest" }); } catch (e) { /* ignore */ }
      }
    });
    window.addEventListener("hashchange", fillPicker);
    fillPicker();
  }

  return {
    PRIVACY_BADGE: PRIVACY_BADGE,
    QUICK_PROMPTS: QUICK_PROMPTS,
    PANEL: PANEL,
    estimateTokens: estimateTokens,
    redactSecrets: redactSecrets,
    packageContextFromFields: packageContextFromFields,
    packageContextFromArticle: packageContextFromArticle,
    contextualReply: contextualReply,
    suggestionFor: suggestionFor,
    buildProposal: buildProposal,
    submissionResult: submissionResult,
    panelContract: panelContract,
    threadResetNeeded: threadResetNeeded,
    init: init
  };
});
