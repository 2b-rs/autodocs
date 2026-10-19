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
    composeHint: "Enter sendet · Shift+Enter fügt eine neue Zeile ein",
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

  var QUESTION_TEXT_MIN = 3;
  var QUESTION_TEXT_MAX = 4000;
  var QUESTION_DETAIL_MAX = 1500;
  var QUESTION_PROPOSAL_LEAD = "Kontextfrage (Vorschlag, nicht angenommen, nicht beantwortet).";
  var questionDialogState = {
    opener: null,
    offer: null,
    submitting: false,
    submitGen: 0,
    onSubmitted: null
  };

  function clipChars(text, max) {
    return Array.from(String(text == null ? "" : text)).slice(0, max).join("");
  }

  function questionProposalReceiptMessage(result) {
    var id = result && result.id ? String(result.id) : "";
    return "Vorschlag gespeichert" + (id ? " (Beleg " + id + ")" : "") +
      ". Erst der validierte Ingest kann daraus eine offene Kontextfrage machen. Das ist keine Annahme und keine Antwort.";
  }

  function questionDialogIsOpen(doc) {
    var root = doc || (typeof document !== "undefined" ? document : null);
    var dlg = root && root.getElementById ? root.getElementById("discuss-question-dialog") : null;
    return !!(dlg && (dlg.open || dlg.hasAttribute("open")));
  }

  function questionFeedbackRecord(fields) {
    fields = fields || {};
    var question = redactSecrets(String(fields.question == null ? "" : fields.question).replace(/\r\n?/g, "\n").trim()).text;
    var detail = redactSecrets(String(fields.detail == null ? "" : fields.detail).replace(/\r\n?/g, "\n").trim()).text;
    var assumption = redactSecrets(String(fields.assumption == null ? "" : fields.assumption).replace(/\s+/g, " ").trim()).text;
    var rationale = redactSecrets(String(fields.rationale == null ? "" : fields.rationale).replace(/\s+/g, " ").trim()).text;
    var recordId = clipChars(fields.record_id || "", 256);
    var page = clipChars(fields.page || "", 300);
    var kind = fields.kind === "gap" || fields.kind === "unclear" ? fields.kind : "";
    var questionChars = Array.from(question);
    if (questionChars.length < QUESTION_TEXT_MIN) return { error: "question-short" };
    if (questionChars.length > QUESTION_TEXT_MAX) return { error: "question-long" };
    if (Array.from(detail).length > QUESTION_DETAIL_MAX) return { error: "detail-long" };
    var parts = [QUESTION_PROPOSAL_LEAD, question];
    if (kind) parts.push("Art: " + kind);
    if (recordId) parts.push("Eintrag: " + recordId);
    if (assumption) parts.push("Annahme: " + clipChars(assumption, 1000));
    if (rationale) parts.push("Begründung: " + clipChars(rationale, 1500));
    if (detail) parts.push("Details: " + detail);
    var text = clipChars(parts.join("\n\n"), QUESTION_TEXT_MAX);
    var ctx = {};
    if (page) ctx.page = page;
    if (recordId) ctx.target = recordId;
    ctx.fold = "Discuss with AI: Kontextfrage";
    ctx.title = clipChars("Kontextfrage zu " + (recordId || "Eintrag"), 200);
    var selection = clipChars([assumption, rationale].filter(Boolean).join(" — "), 1000);
    if (selection) ctx.selection = selection;
    if (fields.release) ctx.release = clipChars(fields.release, 40);
    if (fields.lang) ctx.lang = clipChars(fields.lang, 8);
    return { art: "wunsch", text: text, ctx: ctx };
  }

  function ensureQuestionDialog(doc) {
    var root = doc || document;
    var existing = root.getElementById("discuss-question-dialog");
    if (existing) return existing;
    if (!root.getElementById("discuss-question-dialog-style")) {
      var style = root.createElement("style");
      style.id = "discuss-question-dialog-style";
      style.textContent = [
        ".discuss-question-dialog{max-width:min(36rem,calc(100vw - 24px));width:100%;padding:0;border:1px solid #D4D1CA;border-radius:12px;box-shadow:0 16px 40px rgba(28,27,25,.28);background:#F9F8F5;color:#28251D;font:15px/1.45 -apple-system,Segoe UI,sans-serif}",
        ".discuss-question-dialog::backdrop{background:rgba(28,27,25,.42)}",
        ".discuss-question-dialog form{display:flex;flex-direction:column;gap:8px;padding:16px}",
        ".discuss-question-dialog h2{margin:0;font-size:17px}",
        ".discuss-question-dialog p,.discuss-question-dialog dl{margin:0}",
        ".discuss-question-dialog dt{font-weight:650;margin-top:6px}",
        ".discuss-question-dialog dd{margin:0;overflow-wrap:anywhere}",
        ".discuss-question-dialog label{font-weight:650}",
        ".discuss-question-dialog textarea{width:100%;min-height:72px;resize:vertical;border:1px solid #D4D1CA;border-radius:8px;padding:8px;font:inherit;background:#fff;color:#28251D;box-sizing:border-box}",
        ".discuss-question-dialog [data-q-actions]{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px}",
        ".discuss-question-dialog button{background:#fff;color:#01696F;border:1px solid #B6B2A8;border-radius:8px;padding:8px 12px;cursor:pointer;font:inherit}",
        ".discuss-question-dialog [data-q-submit]{background:#01696F;color:#fff;border-color:#01696F}",
        ".discuss-question-dialog [data-q-submit][disabled],.discuss-question-dialog textarea[disabled]{opacity:.65;cursor:not-allowed}",
        ".discuss-question-dialog [data-q-status]{min-height:1.35em;color:#7A3418}",
        ".discuss-question-dialog [data-q-status][data-kind='ok']{color:#135C2F}",
        ".discuss-question-dialog button:focus-visible,.discuss-question-dialog textarea:focus-visible{outline:3px solid #01696F;outline-offset:2px}"
      ].join("");
      (root.head || root.documentElement || root.body).appendChild(style);
    }
    var dlg = root.createElement("dialog");
    dlg.id = "discuss-question-dialog";
    dlg.className = "discuss-question-dialog";
    dlg.setAttribute("aria-labelledby", "discuss-question-dialog-title");
    dlg.innerHTML = '<form data-q-form novalidate>' +
      '<h2 id="discuss-question-dialog-title">Kontextfrage vorschlagen</h2>' +
      '<p data-q-authority>Dieser Vorschlag ist nicht angenommen und keine Antwort. Erst der validierte Ingest kann daraus eine offene Kontextfrage machen.</p>' +
      '<dl>' +
      '<dt>Eintrag</dt><dd data-q-record></dd>' +
      '<dt>Seite</dt><dd data-q-page></dd>' +
      '<dt>Annahme</dt><dd data-q-assumption></dd>' +
      '<dt>Begründung</dt><dd data-q-rationale></dd>' +
      '</dl>' +
      '<label for="discuss-question-text">Prüffrage</label>' +
      '<textarea id="discuss-question-text" data-q-question required minlength="3" maxlength="4000"></textarea>' +
      '<label for="discuss-question-detail">Details (optional)</label>' +
      '<textarea id="discuss-question-detail" data-q-detail maxlength="1500"></textarea>' +
      '<p role="status" data-q-status></p>' +
      '<div data-q-actions>' +
      '<button type="submit" data-q-submit>Vorschlag senden</button>' +
      '<button type="button" data-q-cancel>Abbrechen</button>' +
      '</div></form>';
    (root.body || root.documentElement).appendChild(dlg);
    var form = dlg.querySelector("[data-q-form]");
    var cancel = dlg.querySelector("[data-q-cancel]");
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      submitQuestionProposal(dlg);
    });
    cancel.addEventListener("click", function () {
      closeQuestionProposalDialog(dlg);
    });
    dlg.addEventListener("cancel", function (event) {
      event.preventDefault();
      closeQuestionProposalDialog(dlg);
    });
    dlg.addEventListener("close", function () {
      restoreQuestionDialogFocus();
    });
    return dlg;
  }

  function restoreQuestionDialogFocus() {
    var opener = questionDialogState.opener;
    questionDialogState.opener = null;
    questionDialogState.submitting = false;
    if (opener && typeof opener.focus === "function" && (!opener.closest || opener.closest("body") || opener.isConnected !== false)) {
      try { opener.focus(); } catch (error) { /* opener may have been removed */ }
    }
  }

  function closeQuestionProposalDialog(dlg) {
    questionDialogState.submitGen += 1;
    questionDialogState.submitting = false;
    if (!dlg) return;
    if (typeof dlg.close === "function" && (dlg.open || dlg.hasAttribute("open"))) {
      try { dlg.close(); return; } catch (error) { /* fall through */ }
    }
    dlg.removeAttribute("open");
    restoreQuestionDialogFocus();
  }

  function setQuestionDialogBusy(dlg, busy) {
    var submit = dlg.querySelector("[data-q-submit]");
    var question = dlg.querySelector("[data-q-question]");
    var detail = dlg.querySelector("[data-q-detail]");
    questionDialogState.submitting = !!busy;
    if (submit) {
      submit.disabled = !!busy || !!(questionDialogState.offer && questionDialogState.offer.submitted);
      if (busy) submit.setAttribute("aria-busy", "true");
      else submit.removeAttribute("aria-busy");
    }
    if (question) question.disabled = !!busy;
    if (detail) detail.disabled = !!busy;
    if (busy) dlg.setAttribute("aria-busy", "true");
    else dlg.removeAttribute("aria-busy");
  }

  function showQuestionDialogStatus(dlg, kind, text) {
    var status = dlg.querySelector("[data-q-status]");
    if (!status) return;
    status.dataset.kind = kind || "";
    status.textContent = text || "";
  }

  function questionDialogCompletionIsCurrent(dlg, gen, offer) {
    if (gen !== questionDialogState.submitGen) return false;
    if (!offer || questionDialogState.offer !== offer) return false;
    if (!dlg || (!dlg.open && !dlg.hasAttribute("open"))) return false;
    var live = dlg.ownerDocument && dlg.ownerDocument.getElementById
      ? dlg.ownerDocument.getElementById("discuss-question-dialog") : null;
    return !live || live === dlg;
  }

  function submitQuestionProposal(dlg) {
    if (!dlg || questionDialogState.submitting) return;
    var offer = questionDialogState.offer || {};
    if (offer.submitted) return;
    var questionEl = dlg.querySelector("[data-q-question]");
    var detailEl = dlg.querySelector("[data-q-detail]");
    var record = questionFeedbackRecord({
      question: questionEl ? questionEl.value : "",
      detail: detailEl ? detailEl.value : "",
      assumption: offer.assumption,
      rationale: offer.rationale,
      record_id: offer.record_id,
      kind: offer.kind,
      page: questionDialogState.page,
      release: questionDialogState.release,
      lang: questionDialogState.lang
    });
    if (record.error === "question-short") {
      showQuestionDialogStatus(dlg, "err", "Bitte eine Prüffrage mit mindestens drei Zeichen eingeben.");
      if (questionEl && typeof questionEl.focus === "function") questionEl.focus();
      return;
    }
    if (record.error) {
      showQuestionDialogStatus(dlg, "err", "Die Eingabe ist unvollständig oder zu lang.");
      return;
    }
    var access = questionDialogState.access || (typeof window !== "undefined" ? window.AiAccess : null);
    if (!access || !access.feedback || typeof access.feedback.send !== "function") {
      showQuestionDialogStatus(dlg, "err", "Rückkanal nicht verfügbar. Der Vorschlag wurde nicht gespeichert.");
      return;
    }
    var gen = (questionDialogState.submitGen += 1);
    var submittedOffer = offer;
    var onSubmitted = questionDialogState.onSubmitted;
    setQuestionDialogBusy(dlg, true);
    showQuestionDialogStatus(dlg, "", "Vorschlag wird gesendet…");
    Promise.resolve(access.feedback.send(record)).then(function (result) {
      if (!questionDialogCompletionIsCurrent(dlg, gen, submittedOffer)) return;
      submittedOffer.submitted = true;
      if (typeof onSubmitted === "function") onSubmitted(result, record);
      setQuestionDialogBusy(dlg, false);
      var submit = dlg.querySelector("[data-q-submit]");
      if (submit) submit.disabled = true;
      showQuestionDialogStatus(dlg, "ok", questionProposalReceiptMessage(result));
      var cancel = dlg.querySelector("[data-q-cancel]");
      if (cancel) cancel.textContent = "Schließen";
    }).catch(function (error) {
      if (!questionDialogCompletionIsCurrent(dlg, gen, submittedOffer)) return;
      submittedOffer.submitted = false;
      setQuestionDialogBusy(dlg, false);
      showQuestionDialogStatus(dlg, "err",
        "Vorschlag konnte nicht gespeichert werden: " + String((error && error.message) || error) +
        " Du kannst es erneut versuchen.");
    });
  }

  function openQuestionProposalDialog(opts) {
    opts = opts || {};
    var offer = opts.offer || {};
    if (typeof document === "undefined") return { error: "no-document" };
    var dlg = ensureQuestionDialog(opts.document || document);
    if (questionDialogIsOpen(dlg.ownerDocument) && questionDialogState.offer === offer && offer.submitted) {
      return { error: "already-submitted" };
    }
    questionDialogState.submitGen += 1;
    questionDialogState.submitting = false;
    questionDialogState.offer = offer;
    questionDialogState.opener = opts.opener || null;
    questionDialogState.onSubmitted = opts.onSubmitted || null;
    questionDialogState.access = opts.access || (typeof window !== "undefined" ? window.AiAccess : null);
    questionDialogState.page = opts.page || (typeof location !== "undefined" ? String(location.pathname || "") : "");
    questionDialogState.release = opts.release || "";
    questionDialogState.lang = opts.lang || ((dlg.ownerDocument || document).documentElement || {}).lang || "";
    dlg.querySelector("[data-q-record]").textContent = offer.record_id || "—";
    dlg.querySelector("[data-q-page]").textContent = questionDialogState.page || "—";
    dlg.querySelector("[data-q-assumption]").textContent = offer.assumption || "—";
    dlg.querySelector("[data-q-rationale]").textContent = offer.rationale || "—";
    dlg.querySelector("[data-q-question]").value = String(offer.question || "");
    dlg.querySelector("[data-q-detail]").value = "";
    var cancel = dlg.querySelector("[data-q-cancel]");
    if (cancel) cancel.textContent = "Abbrechen";
    setQuestionDialogBusy(dlg, false);
    showQuestionDialogStatus(dlg, "", "");
    if (typeof dlg.showModal === "function") {
      try { dlg.showModal(); }
      catch (error) { dlg.setAttribute("open", ""); }
    } else {
      dlg.setAttribute("open", "");
    }
    var questionEl = dlg.querySelector("[data-q-question]");
    if (questionEl && typeof questionEl.focus === "function") {
      try { questionEl.focus(); } catch (error) { /* ignore */ }
    }
    return { ok: true, dialog: dlg };
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
    if (fields.viewedRelease) context.viewed_release = String(fields.viewedRelease);
    if (fields.guideRelease) context.guide_release = String(fields.guideRelease);
    if (fields.contextRelease) context.context_release = String(fields.contextRelease);
    if (fields.staleProjection) context.stale_projection = true;
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
      found: !!((article && article.id) || page.recordId),
      viewedRelease: page.viewed_release || "",
      guideRelease: page.guide_release || "",
      contextRelease: page.context_release || "",
      staleProjection: page.stale_projection === true
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

  function shouldSubmitMessage(event) {
    return !!(event && event.key === "Enter" && !event.shiftKey &&
      !event.isComposing && event.keyCode !== 229);
  }

  function preferredContextRecordId(selectedRecordId, triggerRecordId) {
    return String(selectedRecordId || triggerRecordId || "").trim();
  }

  function panelContract() {
    return {
      title: PANEL.title,
      sendLabel: PANEL.sendLabel,
      inspectorLabel: PANEL.inspectorLabel,
      privacyBadge: PANEL.privacyBadge,
      deriveLabel: PANEL.deriveLabel,
      submitLabel: PANEL.submitLabel,
      composeHint: PANEL.composeHint,
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

  function releaseFromLocation(search, hash) {
    var core = typeof window !== "undefined" && window.AutodocsReleaseCore;
    if (core && typeof core.releaseOf === "function") {
      var fromCore = core.releaseOf(search || "", hash || "");
      if (fromCore) return String(fromCore);
    }
    var blob = String(search || "") + "&" + String(hash || "").replace(/^#/, "");
    var match = /(?:^|[?&#])release=([^&#]+)/.exec(blob);
    if (!match || !match[1]) return "";
    try { return decodeURIComponent(match[1]); }
    catch (error) { return match[1]; }
  }

  var GUIDE_REFRESH_LANGS = ["de", "en", "id", "bn", "ja", "he"];
  var GUIDE_RELEASES = {
    classic: ["2.1", "3.0", "3.1", "3.2", "4.0", "4.1", "4.2", "4.3", "4.4"],
    adaptive: ["R19-11", "R20-11", "R21-11", "R22-11", "R23-11", "R24-11", "R25-11"]
  };
  var GUIDE_REFRESH_POINTER = "guide-refresh-operation-id";
  var RECORD_ID_RX = /^[A-Z][A-Z0-9_]{1,63}$/;
  var GUIDE_ID_RX = /^[A-Za-z0-9][A-Za-z0-9_./-]{0,159}$/;

  function canonicalRelease(raw) {
    var text = String(raw || "").trim();
    if (!text) return "";
    var adaptive = text.toUpperCase();
    if (GUIDE_RELEASES.adaptive.indexOf(adaptive) >= 0) return adaptive;
    if (GUIDE_RELEASES.classic.indexOf(text) >= 0) return text;
    return "";
  }

  function releaseFamily(canon) {
    if (GUIDE_RELEASES.adaptive.indexOf(canon) >= 0) return "adaptive";
    if (GUIDE_RELEASES.classic.indexOf(canon) >= 0) return "classic";
    return "";
  }

  function compareKnownReleases(left, right) {
    var family = releaseFamily(left);
    if (!family || family !== releaseFamily(right)) return null;
    return GUIDE_RELEASES[family].indexOf(left) - GUIDE_RELEASES[family].indexOf(right);
  }

  function guideRefreshLanguages(languages) {
    var requested = [];
    (languages || []).forEach(function (lang) {
      var code = String(lang || "").trim();
      if (code && requested.indexOf(code) < 0) requested.push(code);
    });
    if (!requested.length || requested.some(function (code) { return GUIDE_REFRESH_LANGS.indexOf(code) < 0; })) {
      return null;
    }
    return GUIDE_REFRESH_LANGS.filter(function (code) { return requested.indexOf(code) >= 0; });
  }

  function guideRefreshPlan(viewedRelease, guideRelease, languages, currentRelease, identity) {
    identity = identity || {};
    var viewedRaw = String(viewedRelease || "").trim();
    var guideRaw = String(guideRelease || "").trim();
    var currentRaw = String(currentRelease || "").trim();
    var viewed = canonicalRelease(viewedRaw);
    var guide = canonicalRelease(guideRaw);
    var current = canonicalRelease(currentRaw);
    var langs = guideRefreshLanguages(languages);
    var recordId = String(identity.record_id || "").trim();
    var guideId = String(identity.guide_id || "").trim();
    var plan = {
      viewed_release: viewed || viewedRaw,
      guide_release: guide || guideRaw,
      current_release: current || currentRaw,
      context_release: guide || guideRaw,
      source_release: guide || guideRaw,
      promoted_to_current: false,
      completed: false,
      record_id: recordId,
      guide_id: guideId,
      languages: langs || []
    };
    if (!viewedRaw || !guideRaw) return Object.assign({ ok: false, reason: "missing-release" }, plan);
    if (!currentRaw) return Object.assign({ ok: false, reason: "missing-current-release" }, plan, { current_release: "" });
    if (!viewed || !guide || !current) return Object.assign({ ok: false, reason: "unknown-release" }, plan);
    if (releaseFamily(viewed) !== releaseFamily(guide) || releaseFamily(current) !== releaseFamily(guide)) {
      return Object.assign({ ok: false, reason: "release-family" }, plan);
    }
    if (!recordId || !guideId) return Object.assign({ ok: false, reason: "missing-identity" }, plan);
    if (!RECORD_ID_RX.test(recordId) || !GUIDE_ID_RX.test(guideId)) {
      return Object.assign({ ok: false, reason: "invalid-identity" }, plan);
    }
    if (!langs) return Object.assign({ ok: false, reason: "invalid-languages" }, plan);
    if (viewed === guide) {
      return Object.assign({ ok: false, reason: "already-current", stale: false }, plan);
    }
    if (compareKnownReleases(guide, viewed) > 0) {
      return Object.assign({ ok: false, reason: "not-stale", stale: false }, plan);
    }
    return Object.assign({
      ok: true,
      action: "selective-guide-refresh",
      stale: true
    }, plan);
  }

  function guideRefreshNoteText(result) {
    var rec = (result && (result.receipt || result)) || {};
    if (result && result.ok && result.operation_id && result.completed !== true) {
      return "Guide refresh " + (result.status || "queued") + " (" + result.operation_id + "). Guide " +
        (rec.guide_release || "") + "; viewed " + (rec.viewed_release || "") + "; current " +
        (rec.current_release || "") + ". Not completed.";
    }
    var reason = (result && (result.reason || (result.error && (result.error.code || result.error.message)))) || "refresh-failed";
    return "Guide refresh was not queued (" + reason + "). Not completed.";
  }

  function renderGuideRefreshNote(note, result) {
    var rec = (result && (result.receipt || result)) || {};
    note.setAttribute("role", "status");
    if (result && result.ok && result.operation_id && result.completed !== true) {
      note.dataset.refreshStatus = result.status || "queued";
      note.dataset.operationId = result.operation_id;
    } else {
      note.dataset.refreshStatus = "failed";
      if (note.dataset) delete note.dataset.operationId;
    }
    note.textContent = guideRefreshNoteText(result && result.ok ? Object.assign({}, result, {
      guide_release: rec.guide_release,
      viewed_release: rec.viewed_release,
      current_release: rec.current_release
    }) : result);
  }

  function requestGuideRefresh(plan, deps) {
    deps = deps || {};
    var access = deps.access || (typeof window !== "undefined" ? window.AiAccess : null);
    var fetchImpl = deps.fetch || (typeof fetch !== "undefined" ? fetch : null);
    if (!plan || !plan.ok) {
      return Promise.resolve({
        ok: false, completed: false, status: "rejected",
        reason: plan && plan.reason || "invalid"
      });
    }
    if (!access || typeof access.service !== "function" || typeof access.idToken !== "function" || !fetchImpl) {
      return Promise.resolve({ ok: false, completed: false, status: "unauthenticated", reason: "sign-in-required" });
    }
    return Promise.all([access.service(), access.idToken()]).then(function (pair) {
      var base = String(pair[0] || "").replace(/\/$/, "");
      var token = pair[1];
      if (!base || !token) {
        return { ok: false, completed: false, status: "unauthenticated", reason: "sign-in-required" };
      }
      return fetchImpl(base + "/guide-refresh", {
        method: "POST",
        credentials: "omit",
        mode: "cors",
        headers: {
          Authorization: "Bearer " + token,
          Accept: "application/json",
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          guide_id: plan.guide_id,
          record_id: plan.record_id,
          current_release: plan.current_release,
          viewed_release: plan.viewed_release,
          guide_release: plan.guide_release,
          languages: plan.languages
        })
      }).then(function (response) {
        return response.json().catch(function () { return null; }).then(function (data) {
          data = data && typeof data === "object" ? data : {};
          if (!response.ok || data.completed === true || !data.operation_id) {
            return {
              ok: false,
              completed: false,
              status: "failed",
              http_status: response.status,
              error: data.error || { code: "refresh-failed" },
              operation_id: data.operation_id || ""
            };
          }
          return data;
        });
      }).catch(function (error) {
        return {
          ok: false, completed: false, status: "failed", reason: "network",
          error: { message: String((error && error.message) || error) }
        };
      });
    });
  }

  function rememberGuideRefresh(operationId, storage) {
    var store = storage || (typeof sessionStorage !== "undefined" ? sessionStorage : null);
    if (!store || !operationId) return;
    try { store.setItem(GUIDE_REFRESH_POINTER, String(operationId)); } catch (error) { /* ignore */ }
  }

  function readGuideRefreshPointer(storage) {
    var store = storage || (typeof sessionStorage !== "undefined" ? sessionStorage : null);
    if (!store) return "";
    try { return String(store.getItem(GUIDE_REFRESH_POINTER) || ""); } catch (error) { return ""; }
  }

  function guideRefreshContext(refresh) {
    var host = refresh.closest("[data-asof-release]");
    var guideIdNode = refresh.closest("[data-ai-guide-id]");
    var recordNode = refresh.closest("[data-record-id], [data-discuss-record-id]");
    var currentNode = document.querySelector("[data-current-release]");
    var recordId = "";
    if (recordNode) {
      recordId = recordNode.getAttribute("data-record-id") || recordNode.getAttribute("data-discuss-record-id") || "";
    }
    return {
      guideRelease: host ? (host.getAttribute("data-asof-release") || "") : "",
      guideId: guideIdNode ? (guideIdNode.getAttribute("data-ai-guide-id") || "") : "",
      recordId: recordId,
      currentRelease: currentNode ? (currentNode.getAttribute("data-current-release") || "") : ""
    };
  }

  function restoreGuideRefresh(anchor, deps) {
    deps = deps || {};
    var operationId = readGuideRefreshPointer(deps.storage);
    if (!operationId) return Promise.resolve(null);
    var access = deps.access || (typeof window !== "undefined" ? window.AiAccess : null);
    var fetchImpl = deps.fetch || (typeof fetch !== "undefined" ? fetch : null);
    if (!access || typeof access.service !== "function" || typeof access.idToken !== "function" || !fetchImpl) {
      return Promise.resolve(null);
    }
    return Promise.all([access.service(), access.idToken()]).then(function (pair) {
      var base = String(pair[0] || "").replace(/\/$/, "");
      if (!base || !pair[1]) return null;
      return fetchImpl(base + "/guide-refresh?operation_id=" + encodeURIComponent(operationId), {
        method: "GET",
        credentials: "omit",
        mode: "cors",
        headers: { Authorization: "Bearer " + pair[1], Accept: "application/json" }
      }).then(function (response) {
        return response.json().catch(function () { return null; }).then(function (data) {
          var note = document.getElementById("guide-refresh-live");
          if (!note && anchor && anchor.insertAdjacentElement) {
            note = document.createElement("p");
            note.id = "guide-refresh-live";
            anchor.insertAdjacentElement("afterend", note);
          }
          if (!note) return data;
          if (!response.ok || !data || !data.operation_id || data.completed === true) {
            renderGuideRefreshNote(note, {
              ok: false,
              completed: false,
              reason: (data && data.error && data.error.code) || "reload-failed"
            });
            return data;
          }
          renderGuideRefreshNote(note, data);
          return data;
        });
      });
    }).catch(function () { return null; });
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
    var search = (typeof location !== "undefined" && location.search) || "";
    var hash = (typeof location !== "undefined" && location.hash) || "";
    var viewed = releaseFromLocation(search, hash);
    var guideNode = document.querySelector("[data-asof-release]");
    var guide = guideNode ? (guideNode.getAttribute("data-asof-release") || "") : "";
    return {
      universe: universe,
      module: h1 ? h1.textContent.replace(/\s+/g, " ").trim() : "",
      viewed_release: viewed,
      guide_release: guide,
      context_release: guide || viewed,
      stale_projection: !!(viewed && guide && viewed !== guide)
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
      ".discuss-question-offer{margin-top:10px;padding:10px;border:1px solid #D8A928;border-radius:8px;background:#FFF8DF;white-space:normal}",
      ".discuss-question-offer h3{margin:0 0 6px;font-size:14px}",
      ".discuss-question-offer dl{margin:0}.discuss-question-offer dt{font-weight:650;margin-top:5px}.discuss-question-offer dd{margin:0;overflow-wrap:anywhere}",
      ".discuss-question-actions{display:flex;flex-wrap:wrap;gap:6px;margin-top:9px}.discuss-question-actions button{background:#fff;color:#01696F;border:1px solid #B6B2A8;border-radius:7px;padding:6px 8px;cursor:pointer}.discuss-question-actions button:first-child{background:#01696F;color:#fff;border-color:#01696F}",
      ".discuss-quick,.discuss-toolbar,.discuss-compose,.discuss-inspector,.discuss-proposal{padding:8px 12px}",
      ".discuss-quick{display:flex;flex-wrap:wrap;gap:6px}",
      ".discuss-compose textarea{flex:1;min-height:64px;resize:vertical;border:1px solid #D4D1CA;border-radius:8px;padding:8px;font:inherit;background:#fff;color:#28251D}",
      ".discuss-compose{flex-wrap:wrap}",
      ".discuss-compose-help{flex-basis:100%;margin:0;color:#5F5D58;font-size:12px}",
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
    input.setAttribute("aria-describedby", "discuss-compose-help");
    input.setAttribute("aria-keyshortcuts", "Enter");
    input.maxLength = 4000;
    var sendButton = document.createElement("button");
    sendButton.type = "submit";
    sendButton.textContent = PANEL.sendLabel;
    var composeHelp = document.createElement("p");
    composeHelp.id = "discuss-compose-help";
    composeHelp.className = "discuss-compose-help";
    composeHelp.textContent = PANEL.composeHint;
    compose.appendChild(input);
    compose.appendChild(sendButton);
    compose.appendChild(composeHelp);

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
    if (typeof window !== "undefined" && window.AiAccess && typeof window.AiAccess.chip === "function") {
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

    function selectRecordId(recordId, nsxRoot) {
      var article = document.getElementById(recordId);
      if (article && article.matches && article.matches("article.rec")) {
        selectArticle(article);
      } else {
        var previousId = state.context && state.context.record_id;
        if (threadResetNeeded(previousId, recordId)) {
          persist();
          thread.textContent = "";
          state.messages = [];
          state.proposal = null;
        }
        var row = null;
        if (nsxRoot && nsxRoot.querySelectorAll) {
          Array.prototype.some.call(nsxRoot.querySelectorAll("[data-recs], [data-fns]"), function (candidate) {
            var ids = ((candidate.getAttribute("data-recs") || "") + " " +
              (candidate.getAttribute("data-fns") || "")).split(/\s+/);
            if (ids.indexOf(recordId) === -1) return false;
            row = candidate;
            return true;
          });
        }
        var meta = pageMeta();
        state.context = packageContextFromFields({
          recordId: recordId,
          universe: meta.universe,
          module: meta.module,
          requirementText: row ? (row.textContent || "").replace(/\s+/g, " ").trim() : "",
          found: true
        });
        proposalBox.hidden = false;
        diff.hidden = true;
        submit.disabled = true;
        renderInspector();
      }
      var option = Array.prototype.find.call(picker.options || [], function (candidate) {
        return candidate.value === recordId;
      });
      if (!option) {
        option = document.createElement("option");
        option.value = recordId;
        option.textContent = recordId;
        picker.appendChild(option);
      }
      picker.value = recordId;
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
      state.messages.forEach(function (item) {
        var restoredBubble = bubble(item.role, item.text);
        if (item.question_offer) renderQuestionOffer(restoredBubble, item.question_offer, item.provider, item.model);
      });
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

    function renderQuestionOffer(bubbleEl, offer, provider, modelName) {
      if (!bubbleEl || !offer || offer.authority !== "proposal-only" || offer.dismissed) return;
      var card = document.createElement("section");
      card.className = "discuss-question-offer";
      card.setAttribute("aria-label", "Nicht belegte Annahme prüfen");
      var heading = document.createElement("h3");
      heading.textContent = "Nicht belegte Annahme prüfen";
      card.appendChild(heading);
      var facts = document.createElement("dl");
      [["Annahme", offer.assumption], ["Prüffrage", offer.question], ["Begründung", offer.rationale]].forEach(function (pair) {
        var dt = document.createElement("dt");
        var dd = document.createElement("dd");
        dt.textContent = pair[0];
        dd.textContent = pair[1] || "—";
        facts.appendChild(dt);
        facts.appendChild(dd);
      });
      card.appendChild(facts);
      var actions = document.createElement("div");
      actions.className = "discuss-question-actions";
      var propose = document.createElement("button");
      propose.type = "button";
      propose.textContent = "Als Spezifikationslücken-/Kontextfrage vorschlagen";
      var dismiss = document.createElement("button");
      dismiss.type = "button";
      dismiss.textContent = "Nicht jetzt";
      var status = document.createElement("p");
      status.setAttribute("role", "status");
      status.hidden = !offer.submitted;
      if (offer.submitted) {
        propose.disabled = true;
        status.textContent = "Vorschlag wurde bereits vorbereitet; er ist noch keine bestätigte Kontextfrage.";
      }
      propose.addEventListener("click", function () {
        if (propose.disabled) return;
        openQuestionProposalDialog({
          offer: offer,
          provider: provider,
          model: modelName,
          opener: propose,
          page: typeof location !== "undefined" ? String(location.pathname || "") : "",
          release: state.context && (state.context.viewed_release || state.context.guide_release || ""),
          lang: document.documentElement ? document.documentElement.lang : "",
          onSubmitted: function (receipt) {
            offer.submitted = true;
            propose.disabled = true;
            status.textContent = questionProposalReceiptMessage(receipt);
            status.hidden = false;
            persist();
          }
        });
      });
      dismiss.addEventListener("click", function () {
        offer.dismissed = true;
        persist();
        card.remove();
      });
      actions.appendChild(propose);
      actions.appendChild(dismiss);
      card.appendChild(actions);
      card.appendChild(status);
      bubbleEl.appendChild(card);
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
      if (!failure && answer && answer.question_offer) {
        renderQuestionOffer(assistantBubble, answer.question_offer, answer.provider, answer.model);
      }
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
        question_offer: (answer && answer.question_offer) || null,
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
      if (shouldSubmitMessage(event)) {
        event.preventDefault();
        send();
      }
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && !panel.hidden && !questionDialogIsOpen(document)) setOpen(false);
    });
    picker.addEventListener("change", function () {
      selectArticle(document.getElementById(picker.value));
    });
    derive.addEventListener("click", deriveProposal);
    submit.addEventListener("click", submitProposal);
    var guideRefreshBusy = false;
    document.addEventListener("click", function (event) {
      var refresh = event.target && event.target.closest ? event.target.closest("[data-guide-refresh]") : null;
      if (refresh) {
        event.preventDefault();
        if (guideRefreshBusy) return;
        var ctx = guideRefreshContext(refresh);
        var plan = guideRefreshPlan(
          releaseFromLocation(location.search, location.hash),
          ctx.guideRelease,
          ["de", "en", "id", "bn", "ja"],
          ctx.currentRelease,
          { record_id: ctx.recordId, guide_id: ctx.guideId }
        );
        var note = document.getElementById("guide-refresh-live");
        if (!note) {
          note = document.createElement("p");
          note.id = "guide-refresh-live";
          note.setAttribute("role", "status");
          refresh.insertAdjacentElement("afterend", note);
        }
        if (!plan.ok) {
          renderGuideRefreshNote(note, plan);
          return;
        }
        guideRefreshBusy = true;
        refresh.disabled = true;
        requestGuideRefresh(plan).then(function (result) {
          renderGuideRefreshNote(note, result);
          if (result && result.ok && result.operation_id && result.completed !== true) {
            rememberGuideRefresh(result.operation_id);
          }
        }).finally(function () {
          guideRefreshBusy = false;
          refresh.disabled = false;
        });
        return;
      }
      var trigger = event.target && event.target.closest ? event.target.closest("[data-open-discuss]") : null;
      if (trigger) {
        event.preventDefault();
        var recId = trigger.getAttribute("data-open-discuss");
        var nsxRoot = trigger.closest("section.nsx") || document.querySelector("section.nsx[data-discuss-record-id]");
        var selectedRecordId = nsxRoot && nsxRoot.getAttribute("data-discuss-record-id");
        var contextRecordId = preferredContextRecordId(selectedRecordId, recId);
        // Kopfzeile des Guides (.ai-guide-head): das Panel öffnet direkt darunter, nicht in der Zeile
        var actions = trigger.closest(".ai-guide-head") || trigger.closest(".ai-commentary-actions") || trigger.parentElement;
        var isCurrentInline = (panel.dataset.dock === "inline" && panel.previousElementSibling === actions);
        if (isCurrentInline && !panel.hidden) {
          setOpen(false);
          return;
        }
        if (actions && actions.parentNode) {
          actions.parentNode.insertBefore(panel, actions.nextSibling);
          panel.dataset.dock = "inline";
        }
        if (selectedRecordId) {
          selectRecordId(contextRecordId, nsxRoot);
        } else if (contextRecordId && document.getElementById(contextRecordId)) {
          selectArticle(document.getElementById(contextRecordId));
          picker.value = contextRecordId;
        }
        setOpen(true);
        try { panel.scrollIntoView({ behavior: "smooth", block: "nearest" }); } catch (e) { /* ignore */ }
      }
    });
    window.addEventListener("hashchange", fillPicker);
    fillPicker();
    try { sessionStorage.removeItem("guide-refresh-plan"); } catch (error) { /* ignore */ }
    var refreshAnchor = document.querySelector("[data-guide-refresh]");
    if (refreshAnchor) restoreGuideRefresh(refreshAnchor);
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
    shouldSubmitMessage: shouldSubmitMessage,
    preferredContextRecordId: preferredContextRecordId,
    releaseFromLocation: releaseFromLocation,
    guideRefreshPlan: guideRefreshPlan,
    guideRefreshNoteText: guideRefreshNoteText,
    requestGuideRefresh: requestGuideRefresh,
    rememberGuideRefresh: rememberGuideRefresh,
    readGuideRefreshPointer: readGuideRefreshPointer,
    questionFeedbackRecord: questionFeedbackRecord,
    questionProposalReceiptMessage: questionProposalReceiptMessage,
    openQuestionProposalDialog: openQuestionProposalDialog,
    closeQuestionProposalDialog: closeQuestionProposalDialog,
    init: init
  };
});
