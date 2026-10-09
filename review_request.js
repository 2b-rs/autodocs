(function () {
  "use strict";

  var TOKEN = "ara-review-github-token-v1";
  var IDENT = "ara-review-identity";
  var REPO = (typeof document !== "undefined" && document.querySelector('meta[name="review-github-repo"]')?.getAttribute('content')) || '2b-rs/autodocs';
  var CATEGORIES = [
    ["", "Choose category"],
    ["factual-accuracy", "Factual accuracy"],
    ["outdated-source", "Outdated source"],
    ["missing-context", "Missing context"],
    ["ai-hallucination-suspected", "AI hallucination suspected"],
    ["other", "Other"]
  ];

  function processDocHref(anchor) {
    if (typeof document === "undefined") return "process.html#" + anchor;
    var sheet = document.querySelector('link[rel="stylesheet"]');
    var href = sheet && sheet.getAttribute("href");
    var marker = "style.css";
    var index = href ? href.lastIndexOf(marker) : -1;
    return (index >= 0 ? href.slice(0, index) : "") + "process.html#" + anchor;
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function cleanName(v) { return String(v == null ? "" : v).replace(/\s+/g, " ").trim().slice(0, 80); }
  function validName(v) { return cleanName(v).length >= 2; }
  function selfName() {
    try {
      if (typeof localStorage !== "undefined") return cleanName(localStorage.getItem(IDENT) || "");
    } catch (_) {}
    return "";
  }
  function setSelfName(v) {
    try {
      if (typeof localStorage !== "undefined") localStorage.setItem(IDENT, cleanName(v));
    } catch (_) {}
  }
  function activeToken() {
    try {
      if (typeof localStorage !== "undefined") return String(localStorage.getItem(TOKEN) || "").trim();
    } catch (_) {}
    return "";
  }

  async function verify(token) {
    var r = await fetch("https://api.github.com/user", { headers: { Accept: "application/vnd.github+json", Authorization: "Bearer " + token, "X-GitHub-Api-Version": "2022-11-28" } });
    if (!r.ok) throw new Error("GitHub: " + r.status);
    return await r.json();
  }

  function generateUUIDv7() {
    var now = Date.now();
    var bytes = new Uint8Array(16);
    if (typeof crypto !== "undefined" && crypto.getRandomValues) {
      crypto.getRandomValues(bytes);
    } else {
      try {
        var nodeCrypto = require("crypto");
        var buf = nodeCrypto.randomBytes(16);
        for (var i = 0; i < 16; i++) bytes[i] = buf[i];
      } catch (_) {
        for (var j = 0; j < 16; j++) bytes[j] = Math.floor(Math.random() * 256);
      }
    }
    bytes[0] = Math.floor(now / 0x10000000000) & 0xff;
    bytes[1] = Math.floor(now / 0x100000000) & 0xff;
    bytes[2] = Math.floor(now / 0x1000000) & 0xff;
    bytes[3] = Math.floor(now / 0x10000) & 0xff;
    bytes[4] = Math.floor(now / 0x100) & 0xff;
    bytes[5] = now & 0xff;
    bytes[6] = (bytes[6] & 0x0f) | 0x70;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    var hex = [];
    for (var k = 0; k < 16; k++) hex.push(bytes[k].toString(16).padStart(2, "0"));
    var h = hex.join("");
    return h.slice(0, 8) + "-" + h.slice(8, 12) + "-" + h.slice(12, 16) + "-" + h.slice(16, 20) + "-" + h.slice(20);
  }

  function requestId() { return "review-request:" + generateUUIDv7(); }

  function knownIdentity() {
    var s = selfName();
    if (activeToken()) return { name: null, mode: "github_authenticated" };
    if (validName(s)) return { name: s, mode: "self_declared" };
    return null;
  }

  function setState(root, message, kind) {
    if (!root) return;
    var el = root.querySelector("[data-review-request-state]");
    if (!el) return;
    el.hidden = !message;
    el.className = "review-request-state" + (kind ? " is-" + kind : "");
    el.textContent = message || "";
  }

  function openIdentityModal() {
    return new Promise(function (resolve, reject) {
      if (typeof document === "undefined") return reject(new Error("DOM not available"));
      var modal = document.createElement("div");
      modal.className = "rv-modal is-open";
      modal.innerHTML = '<div class="rv-modal-scrim"></div><div class="rv-modal-card" role="dialog" aria-modal="true" aria-labelledby="rr-id-title"><header class="rv-modal-head"><h2 id="rr-id-title">Who is requesting review?</h2><button type="button" class="rv-icon-btn" data-cancel aria-label="Cancel">×</button></header><div class="rv-modal-body"><p class="rv-modal-lead">Your identity is attached to the request. Self-declared requests may carry lower trust than GitHub-authenticated requests.</p><label class="rv-field"><span>Name or handle</span><input type="text" data-input maxlength="80" required></label><p class="rv-modal-note">At least 2 characters. Stored locally in this browser only.</p></div><footer class="rv-modal-foot"><span class="rv-spacer"></span><button type="button" class="rv-btn rv-btn-quiet" data-cancel>Cancel</button><button type="button" class="rv-btn rv-btn-primary" data-ok disabled>Use this name</button></footer></div>';
      document.body.appendChild(modal);
      var input = modal.querySelector('[data-input]');
      var ok = modal.querySelector('[data-ok]');
      input.value = selfName();
      ok.disabled = !validName(input.value);
      function close() { modal.remove(); }
      function onInput() { ok.disabled = !validName(input.value); }
      function onOk() { if (!validName(input.value)) return; var name = cleanName(input.value); setSelfName(name); close(); resolve({ name: name, mode: 'self_declared' }); }
      function onCancel() { close(); reject(new Error('cancelled')); }
      input.addEventListener('input', onInput);
      input.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); onOk(); } if (e.key === 'Escape') onCancel(); });
      ok.addEventListener('click', onOk);
      modal.querySelectorAll('[data-cancel]').forEach(function (el) { el.addEventListener('click', onCancel); });
      input.focus(); input.select();
    });
  }

  async function resolveIdentity() {
    var known = knownIdentity();
    if (known && known.mode === 'self_declared') return known;
    if (activeToken()) {
      try {
        var user = await verify(activeToken());
        return { name: user.login, mode: 'github_authenticated' };
      } catch (_) {}
    }
    return await openIdentityModal();
  }

  function buildEvidenceRows() {
    return '<div class="review-request-evidence-row">' +
      '<label class="review-request-field"><span>Kind</span><input type="text" data-evidence-kind placeholder="quote|url|note"></label>' +
      '<label class="review-request-field review-request-field-wide"><span>Value</span><input type="text" data-evidence-value></label>' +
      '<label class="review-request-field review-request-field-wide"><span>Note (optional)</span><input type="text" data-evidence-note></label>' +
      '<button type="button" class="review-request-remove" data-evidence-remove aria-label="Remove evidence reference">×</button>' +
      '</div>';
  }

  function buildDialog(root, data) {
    var dlg = document.createElement('div');
    dlg.className = 'rv-modal';
    dlg.hidden = true;
    dlg.innerHTML = '<div class="rv-modal-scrim" data-close></div><div class="rv-modal-card review-request-dialog" role="dialog" aria-modal="true" aria-labelledby="rr-title"><header class="rv-modal-head"><h2 id="rr-title">' + esc(data.has_open_review_request ? 'Review request already open' : 'Flag for review') + '</h2><button type="button" class="rv-icon-btn" data-close aria-label="Cancel">×</button></header><div class="rv-modal-body"><div class="review-request-context" tabindex="-1"><p><strong>This creates a review request only.</strong> The record is not changed immediately. <a href="' + esc(processDocHref('flag-for-review-protocol')) + '" class="rv-process-doc-link" target="_blank" rel="noopener">How review requests work ↗</a></p><dl><dt>Record</dt><dd><code>' + esc(data.canonical_id) + '</code></dd><dt>Status</dt><dd>' + esc(data.status) + '</dd>' + (data.version_id ? '<dt>Version</dt><dd><code>' + esc(data.version_id) + '</code></dd>' : '') + (data.content_hash ? '<dt>Content hash</dt><dd><code>' + esc(data.content_hash) + '</code></dd>' : '') + (data.source_url ? '<dt>Source</dt><dd><a href="' + esc(data.source_url) + '">' + esc(data.source_url) + '</a></dd>' : '') + '</dl><p class="review-request-trust">If you continue without GitHub authentication, your identity will be recorded as self-declared and may carry lower trust. <a href="' + esc(processDocHref('storage-and-privacy')) + '" class="rv-process-doc-link" target="_blank" rel="noopener">Learn about storage and privacy ↗</a></p></div><form class="review-request-form"><label class="review-request-field"><span>Category</span><select data-category required>' + CATEGORIES.map(function (c) { return '<option value="' + esc(c[0]) + '"' + (c[0] === (data.category_default || '') ? ' selected' : '') + '>' + esc(c[1]) + '</option>'; }).join('') + '</select></label><label class="review-request-field review-request-field-wide"><span>Rationale</span><textarea data-rationale required></textarea></label><fieldset class="review-request-evidence"><legend>Evidence references (optional)</legend><div data-evidence-list></div><button type="button" class="rv-btn rv-btn-quiet" data-evidence-add>Add another reference</button></fieldset><div class="review-request-errors" data-errors hidden></div></form><section class="review-request-confirm" data-confirm hidden><h3 tabindex="-1">Confirm request</h3><div data-confirm-body></div></section></div><footer class="rv-modal-foot"><button type="button" class="rv-btn rv-btn-quiet" data-close>Cancel</button><button type="button" class="rv-btn rv-btn-quiet" data-edit hidden>Edit</button><button type="button" class="rv-btn rv-btn-primary" data-next>Review request</button><button type="button" class="rv-btn rv-btn-primary" data-submit hidden>Submit</button><button type="button" class="rv-btn rv-btn-quiet" data-export hidden>Export JSON</button></footer></div>';
    document.body.appendChild(dlg);
    return dlg;
  }

  function serializeEvidence(dialog) {
    if (!dialog) return [];
    return Array.from(dialog.querySelectorAll('.review-request-evidence-row')).map(function (row) {
      var kind = row.querySelector('[data-evidence-kind]')?.value?.trim() || "";
      var value = row.querySelector('[data-evidence-value]')?.value?.trim() || "";
      var note = row.querySelector('[data-evidence-note]')?.value?.trim() || "";
      if (!kind || !value) return null;
      var out = { kind: kind, value: value };
      if (note) out.note = note;
      return out;
    }).filter(Boolean);
  }

  function validate(dialog) {
    var errors = [];
    if (!dialog.querySelector('[data-category]').value) errors.push('Category is required.');
    if (!dialog.querySelector('[data-rationale]').value.trim()) errors.push('Rationale is required.');
    var err = dialog.querySelector('[data-errors]');
    err.hidden = !errors.length;
    err.textContent = errors.join(' ');
    if (errors.length) {
      (dialog.querySelector('[data-category]').value ? dialog.querySelector('[data-rationale]') : dialog.querySelector('[data-category]')).focus();
      return false;
    }
    return true;
  }

  function buildConfirmedPackage(root, data, who, transport) {
    var mode = who && who.mode === "github_authenticated" ? "github_authenticated" : "self_declared";
    var tr = transport || (mode === "github_authenticated" ? "github_issue" : "json_export");
    var evidence = [];
    if (data && Array.isArray(data.evidence_refs)) {
      evidence = data.evidence_refs;
    } else if (root && root._rrDialog) {
      evidence = serializeEvidence(root._rrDialog);
    }
    var cat = (data && data.category) || (root && root._rrDialog && root._rrDialog.querySelector('[data-category]')?.value) || "factual-accuracy";
    var rat = (data && data.rationale) || (root && root._rrDialog && root._rrDialog.querySelector('[data-rationale]')?.value?.trim()) || "";
    var name = (who && who.name) || "Anonymous";

    return {
      schema: "review-request-package@v1",
      client_schema_version: "1.0.0",
      request_id: requestId(),
      target_canonical_id: (data && (data.canonical_id || data.target_canonical_id)) || "",
      target_version_id: (data && (data.version_id || data.target_version_id)) || "",
      target_content_hash: (data && (data.content_hash || data.target_content_hash)) || "",
      target_status_snapshot: (data && (data.status || data.target_status || data.target_status_snapshot)) || "valid/published",
      source_url: (data && (data.source_url || data.target_source_url)) || (typeof window !== "undefined" ? window.location.href : ""),
      category: cat,
      rationale: rat,
      evidence_refs: evidence,
      actor_claim: {
        display_name: name,
        identity_kind: mode
      },
      transport: tr,
      created_at: new Date().toISOString()
    };
  }

  async function buildPackage(root, data, transport) {
    var who = await resolveIdentity();
    return buildConfirmedPackage(root, data, who, transport);
  }

  async function exportJson(root, data) {
    var pkg = await buildPackage(root, data, 'json_export');
    var blob = new Blob([JSON.stringify(pkg, null, 2) + '\n'], { type: 'application/json' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'review-request-' + new Date().toISOString().replace(/[:.]/g, '-') + '.json';
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
    setState(root, 'Downloaded — not yet submitted.', 'exported');
    closeDialog(root);
  }

  async function submitGithub(root, data) {
    if (!activeToken()) throw new Error('GitHub connection required for direct submission.');
    var pkg = await buildPackage(root, data, 'github_issue');
    var r = await fetch('https://api.github.com/repos/' + REPO + '/issues', {
      method: 'POST',
      headers: { Accept: 'application/vnd.github+json', Authorization: 'Bearer ' + activeToken(), 'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'Review request for ' + data.canonical_id, body: '```json\n' + JSON.stringify(pkg, null, 2) + '\n```' })
    });
    if (!r.ok) throw new Error('GitHub submission failed: ' + r.status);
    var issue = await r.json();
    setState(root, 'Submitted as GitHub issue #' + issue.number + ' — awaiting review.', 'submitted');
    closeDialog(root);
  }

  function closeDialog(root) {
    if (!root || !root._rrDialog) return;
    var btn = root.querySelector('[data-review-request-open]');
    root._rrDialog.classList.remove('is-open');
    root._rrDialog.hidden = true;
    if (btn) { btn.setAttribute('aria-expanded', 'false'); btn.focus(); }
  }

  function openDialog(root, data) {
    if (!root._rrDialog) root._rrDialog = buildDialog(root, data);
    var dlg = root._rrDialog;
    dlg.hidden = false;
    requestAnimationFrame(function () { dlg.classList.add('is-open'); });
    dlg.querySelector('[data-category]').focus();
    var btn = root.querySelector('[data-review-request-open]');
    if (btn) btn.setAttribute('aria-expanded', 'true');

    dlg.querySelector('[data-evidence-add]').onclick = function () {
      dlg.querySelector('[data-evidence-list]').insertAdjacentHTML('beforeend', buildEvidenceRows());
      var last = dlg.querySelector('.review-request-evidence-row:last-child [data-evidence-kind]');
      if (last) last.focus();
    };
    dlg.addEventListener('click', function (e) {
      if (e.target.closest('[data-close]')) closeDialog(root);
      if (e.target.closest('[data-evidence-remove]')) e.target.closest('.review-request-evidence-row').remove();
    });
    dlg.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeDialog(root); });
    dlg.querySelector('[data-next]').onclick = async function () {
      if (!validate(dlg)) return;
      var pkg = await buildPackage(root, data, activeToken() ? 'github_issue' : 'json_export');
      dlg.querySelector('[data-confirm-body]').innerHTML = '<dl><dt>Record</dt><dd><code>' + esc(pkg.target_canonical_id) + '</code></dd><dt>Category</dt><dd>' + esc(pkg.category) + '</dd><dt>Rationale</dt><dd>' + esc(pkg.rationale) + '</dd><dt>Identity</dt><dd>' + esc(pkg.actor_claim.display_name + ' (' + pkg.actor_claim.identity_kind + ')') + '</dd><dt>Transport</dt><dd>' + esc(pkg.transport) + '</dd></dl>';
      dlg.querySelector('[data-confirm]').hidden = false;
      dlg.querySelector('.review-request-form').hidden = true;
      dlg.querySelector('[data-next]').hidden = true;
      dlg.querySelector('[data-edit]').hidden = false;
      dlg.querySelector('[data-submit]').hidden = false;
      dlg.querySelector('[data-export]').hidden = false;
      dlg.querySelector('[data-confirm] h3').focus();
    };
    dlg.querySelector('[data-edit]').onclick = function () {
      dlg.querySelector('[data-confirm]').hidden = true;
      dlg.querySelector('.review-request-form').hidden = false;
      dlg.querySelector('[data-next]').hidden = false;
      dlg.querySelector('[data-edit]').hidden = true;
      dlg.querySelector('[data-submit]').hidden = true;
      dlg.querySelector('[data-export]').hidden = true;
      dlg.querySelector('[data-category]').focus();
    };
    dlg.querySelector('[data-export]').onclick = function () { exportJson(root, data).catch(function (e) { dlg.querySelector('[data-errors]').hidden = false; dlg.querySelector('[data-errors]').textContent = e.message; }); };
    dlg.querySelector('[data-submit]').onclick = function () {
      submitGithub(root, data).catch(function (e) {
        dlg.querySelector('[data-errors]').hidden = false;
        dlg.querySelector('[data-errors]').textContent = e.message;
        dlg.querySelector('[data-errors]').focus();
      });
    };
  }

  function init(root) {
    var dataEl = root.querySelector('.review-request-data');
    if (!dataEl) return;
    var data = JSON.parse(dataEl.textContent);
    var btn = root.querySelector('[data-review-request-open]');
    if (btn) btn.addEventListener('click', function () { openDialog(root, data); });
  }

  if (typeof document !== "undefined") {
    document.addEventListener('DOMContentLoaded', function () {
      document.querySelectorAll('[data-review-request-root]').forEach(init);
    });
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = {
      generateUUIDv7: generateUUIDv7,
      uuid7Like: generateUUIDv7,
      requestId: requestId,
      buildConfirmedPackage: buildConfirmedPackage,
      buildPackage: buildPackage,
      cleanName: cleanName,
      validName: validName
    };
  }
})();

(function () {
  "use strict";

  // ------------------------------------------------------------------ Feedback melden
  // Kompakter Dialog (docs/concepts/fachkonzept-feedback-und-rollen.md): ein Beschreibungsfeld, die Art als kleine
  // Auswahl, der Bezug (Seite, Abschnitt, Element, markierter Text, Release, Sprache) als entfernbare Chips, Kontakt
  // nur auf Wunsch. Gespeichert wird über AiAccess.feedback (Firestore, lokal serve.py) oder – ohne beides – über
  // ein vorausgefülltes GitHub-Issue. Kein Browser-Token, keine stille Erhebung.
  var SCHEMA = "user-feedback@v2";
  var ARTS = ["hinweis", "fehler", "wunsch"];
  var CTX_ORDER = ["title", "fold", "target", "selection", "release", "lang"];
  var CTX_LIMIT = { page: 300, title: 200, target: 256, fold: 200, selection: 1000, release: 40, lang: 8 };
  var L = {
    de: {"title": "Feedback melden", "close": "Schließen", "lead": "Geht an die Kuratoren und den Prüf-Agenten. Den Stand siehst du unter „Feedback & Kuration“ → „Meine Meldungen“.", "leadLocal": "Lokaler Betrieb: Die Meldung landet als Datei in _src/spec/feedback-queue/user/.", "leadIssue": "Hier geht das Melden über GitHub: Es öffnet sich ein vorausgefülltes, öffentlich sichtbares Issue. Dafür brauchst du ein GitHub-Konto.", "artLabel": "Art", "art_hinweis": "Hinweis", "art_fehler": "Fehler", "art_wunsch": "Wunsch", "textLabel": "Was ist dir aufgefallen?", "ph_hinweis": "Was ist unklar oder könnte besser sein? Ein, zwei Sätze genügen.", "ph_fehler": "Was stimmt nicht, und was wäre richtig? Eine Fundstelle (z. B. SWS-ID) hilft.", "ph_wunsch": "Was fehlt dir hier, und wofür brauchst du es?", "ctxLabel": "Wird mitgeschickt", "ctxPage": "Seite", "ctxFold": "Abschnitt", "ctxTarget": "Element", "ctxSel": "Markierter Text", "ctxRelease": "Release", "ctxLang": "Sprache", "ctxRemove": "„%s“ nicht mitschicken", "ctxReset": "Alle Angaben wieder mitschicken", "whoKonto": "Gesendet als %s.", "whoAnon": "Du meldest ohne Anmeldung.", "whoAnonHint": "Mit Anmeldung findest du deine Meldungen auf allen Geräten wieder.", "signIn": "Anmelden", "reply": "Antwort erwünscht?", "contactLabel": "Wie erreichen wir dich?", "contactPh": "E-Mail oder GitHub-Name", "privacyTitle": "Was gespeichert wird und wer es sieht", "priv1": "Dein Text, die Art und die Angaben unter „Wird mitgeschickt“; bei „Antwort erwünscht?“ auch deine Kontaktangabe.", "priv2Anon": "Ohne Anmeldung legt Firebase (Google) für diesen Browser eine zufällige, anonyme Kennung an – kein Name, keine E-Mail.", "priv2Konto": "Dein Konto (Kennung und Name), damit die Meldung dir zugeordnet ist.", "priv3": "Lesen können nur du und die Verwalter. Der Prüf-Agent prüft Fehler und Hinweise; öffentlich erscheint höchstens ein daraus abgeleiteter Befund ohne Angaben zu dir.", "priv4": "Unter „Meine Meldungen“ kannst du jede Meldung jederzeit zurückziehen; sie wird dann gelöscht.", "privLocal": "Nur als Datei auf diesem Rechner; nichts verlässt ihn.", "privIssue": "Text und Angaben stehen öffentlich im Issue; als Autor erscheint dein GitHub-Konto.", "cancel": "Abbrechen", "send": "Senden", "sendIssue": "Weiter zu GitHub", "viaIssue": "Über GitHub melden", "sending": "Wird gesendet …", "doneTitle": "Danke – deine Meldung ist angekommen.", "doneText": "Sie wartet jetzt auf die Sichtung. Stand und Antwort findest du unter „Feedback & Kuration“ → „Meine Meldungen“.", "doneAnon": "Die Zuordnung gilt für diesen Browser.", "doneLocal": "Lokal abgelegt: %s", "doneIssue": "Das GitHub-Formular ist geöffnet. Mit „Submit new issue“ geht die Meldung ab.", "again": "Noch etwas melden", "status": "Stand ansehen", "e_text_short": "Bitte beschreibe kurz, worum es geht.", "e_text_long": "Bitte fasse dich kürzer (höchstens 4000 Zeichen).", "e_wait": "Du hast gerade erst etwas gemeldet. Bitte warte noch %s Sekunden.", "e_day": "Heute hast du schon 20 Meldungen geschickt – danke! Ab morgen geht es weiter.", "e_paused": "Das Melden über diese Seite ist gerade pausiert. Über GitHub geht es trotzdem.", "e_anon_off": "Ohne Anmeldung ist das Melden gerade abgeschaltet. Melde dich an oder melde über GitHub.", "e_rules": "Die Meldung wurde nicht angenommen. Bitte versuche es gleich noch einmal oder melde über GitHub.", "e_net": "Keine Verbindung zum Speicher. Bitte später noch einmal versuchen oder über GitHub melden.", "e_local": "Der lokale Dienst hat die Meldung nicht angenommen: %s", "issueTitle": "Feedback (%s)"},
    en: {"title": "Report feedback", "close": "Close", "lead": "Goes to the curators and the review agent. You can follow it under “Feedback & Curation” → “My reports”.", "leadLocal": "Local mode: the report is saved as a file in _src/spec/feedback-queue/user/.", "leadIssue": "Here, feedback goes through GitHub: a prefilled, publicly visible issue opens. You need a GitHub account for this.", "artLabel": "Type", "art_hinweis": "Note", "art_fehler": "Error", "art_wunsch": "Suggestion", "textLabel": "What did you notice?", "ph_hinweis": "What is unclear or could be better? One or two sentences are enough.", "ph_fehler": "What is wrong, and what would be right? A reference (e.g. an SWS ID) helps.", "ph_wunsch": "What are you missing here, and what do you need it for?", "ctxLabel": "Sent along", "ctxPage": "Page", "ctxFold": "Section", "ctxTarget": "Element", "ctxSel": "Selected text", "ctxRelease": "Release", "ctxLang": "Language", "ctxRemove": "Don't send “%s”", "ctxReset": "Send all details again", "whoKonto": "Sent as %s.", "whoAnon": "You are reporting without signing in.", "whoAnonHint": "Signed in, you find your reports again on every device.", "signIn": "Sign in", "reply": "Reply wanted?", "contactLabel": "How can we reach you?", "contactPh": "Email or GitHub name", "privacyTitle": "What is stored and who sees it", "priv1": "Your text, the type and the details under “Sent along”; with “Reply wanted?” also your contact.", "priv2Anon": "Without signing in, Firebase (Google) creates a random, anonymous ID for this browser – no name, no email.", "priv2Konto": "Your account (ID and name), so the report is linked to you.", "priv3": "Only you and the administrators can read it. The review agent checks errors and notes; publicly, at most a finding derived from it appears, without anything about you.", "priv4": "Under “My reports” you can withdraw any report at any time; it is then deleted.", "privLocal": "Only as a file on this computer; nothing leaves it.", "privIssue": "Text and details are public in the issue; your GitHub account appears as the author.", "cancel": "Cancel", "send": "Send", "sendIssue": "Continue to GitHub", "viaIssue": "Report via GitHub", "sending": "Sending …", "doneTitle": "Thank you – your report has arrived.", "doneText": "It is now waiting to be reviewed. You find its state and any reply under “Feedback & Curation” → “My reports”.", "doneAnon": "The link to you applies to this browser.", "doneLocal": "Saved locally: %s", "doneIssue": "The GitHub form is open. “Submit new issue” sends the report.", "again": "Report something else", "status": "View status", "e_text_short": "Please describe briefly what it is about.", "e_text_long": "Please keep it shorter (at most 4000 characters).", "e_wait": "You just sent a report. Please wait another %s seconds.", "e_day": "You have already sent 20 reports today – thank you! You can continue tomorrow.", "e_paused": "Reporting through this page is paused right now. GitHub still works.", "e_anon_off": "Reporting without signing in is switched off right now. Sign in or report via GitHub.", "e_rules": "The report was not accepted. Please try again in a moment or report via GitHub.", "e_net": "No connection to the storage. Please try again later or report via GitHub.", "e_local": "The local service did not accept the report: %s", "issueTitle": "Feedback (%s)"},
    es: {"title": "Enviar comentarios", "close": "Cerrar", "lead": "Llega a los curadores y al agente revisor. Puedes seguirlo en «Comentarios y curación» → «Mis avisos».", "leadLocal": "Modo local: el aviso se guarda como archivo en _src/spec/feedback-queue/user/.", "leadIssue": "Aquí los comentarios van por GitHub: se abre una incidencia rellenada y visible públicamente. Necesitas una cuenta de GitHub.", "artLabel": "Tipo", "art_hinweis": "Observación", "art_fehler": "Error", "art_wunsch": "Sugerencia", "textLabel": "¿Qué has notado?", "ph_hinweis": "¿Qué no está claro o podría mejorar? Bastan una o dos frases.", "ph_fehler": "¿Qué está mal y qué sería correcto? Una referencia (p. ej. un ID SWS) ayuda.", "ph_wunsch": "¿Qué te falta aquí y para qué lo necesitas?", "ctxLabel": "Se envía también", "ctxPage": "Página", "ctxFold": "Sección", "ctxTarget": "Elemento", "ctxSel": "Texto marcado", "ctxRelease": "Versión", "ctxLang": "Idioma", "ctxRemove": "No enviar «%s»", "ctxReset": "Volver a enviar todos los datos", "whoKonto": "Enviado como %s.", "whoAnon": "Envías sin iniciar sesión.", "whoAnonHint": "Con sesión iniciada encuentras tus avisos en todos tus dispositivos.", "signIn": "Iniciar sesión", "reply": "¿Quieres respuesta?", "contactLabel": "¿Cómo te contactamos?", "contactPh": "Correo o nombre de GitHub", "privacyTitle": "Qué se guarda y quién lo ve", "priv1": "Tu texto, el tipo y los datos de «Se envía también»; con «¿Quieres respuesta?» también tu contacto.", "priv2Anon": "Sin iniciar sesión, Firebase (Google) crea para este navegador un identificador aleatorio y anónimo: sin nombre ni correo.", "priv2Konto": "Tu cuenta (identificador y nombre), para que el aviso quede asociado a ti.", "priv3": "Solo tú y los administradores pueden leerlo. El agente revisor comprueba errores y observaciones; públicamente aparece como mucho un hallazgo derivado, sin datos sobre ti.", "priv4": "En «Mis avisos» puedes retirar cualquier aviso cuando quieras; entonces se elimina.", "privLocal": "Solo como archivo en este equipo; nada sale de él.", "privIssue": "El texto y los datos son públicos en la incidencia; tu cuenta de GitHub aparece como autora.", "cancel": "Cancelar", "send": "Enviar", "sendIssue": "Continuar en GitHub", "viaIssue": "Informar por GitHub", "sending": "Enviando…", "doneTitle": "Gracias: tu aviso ha llegado.", "doneText": "Ahora espera su revisión. Su estado y la respuesta están en «Comentarios y curación» → «Mis avisos».", "doneAnon": "La asociación vale para este navegador.", "doneLocal": "Guardado localmente: %s", "doneIssue": "El formulario de GitHub está abierto. «Submit new issue» envía el aviso.", "again": "Informar de otra cosa", "status": "Ver estado", "e_text_short": "Describe brevemente de qué se trata.", "e_text_long": "Resúmelo un poco (como máximo 4000 caracteres).", "e_wait": "Acabas de enviar un aviso. Espera %s segundos más.", "e_day": "Hoy ya has enviado 20 avisos, ¡gracias! Mañana puedes seguir.", "e_paused": "El envío desde esta página está en pausa. Por GitHub sigue funcionando.", "e_anon_off": "El envío sin iniciar sesión está desactivado. Inicia sesión o informa por GitHub.", "e_rules": "El aviso no se aceptó. Inténtalo de nuevo enseguida o informa por GitHub.", "e_net": "Sin conexión con el almacenamiento. Inténtalo más tarde o informa por GitHub.", "e_local": "El servicio local no aceptó el aviso: %s", "issueTitle": "Comentario (%s)"},
    pt: {"title": "Enviar feedback", "close": "Fechar", "lead": "Vai para os curadores e o agente revisor. Acompanhe em “Feedback e curadoria” → “Meus relatos”.", "leadLocal": "Modo local: o relato é salvo como arquivo em _src/spec/feedback-queue/user/.", "leadIssue": "Aqui o feedback vai pelo GitHub: abre-se uma issue pré-preenchida e pública. Você precisa de uma conta GitHub.", "artLabel": "Tipo", "art_hinweis": "Observação", "art_fehler": "Erro", "art_wunsch": "Sugestão", "textLabel": "O que você notou?", "ph_hinweis": "O que não está claro ou poderia melhorar? Uma ou duas frases bastam.", "ph_fehler": "O que está errado e o que seria correto? Uma referência (p. ex. um ID SWS) ajuda.", "ph_wunsch": "O que falta aqui e para que você precisa disso?", "ctxLabel": "Enviado junto", "ctxPage": "Página", "ctxFold": "Seção", "ctxTarget": "Elemento", "ctxSel": "Texto selecionado", "ctxRelease": "Versão", "ctxLang": "Idioma", "ctxRemove": "Não enviar “%s”", "ctxReset": "Enviar todos os dados novamente", "whoKonto": "Enviado como %s.", "whoAnon": "Você está relatando sem login.", "whoAnonHint": "Com login, você encontra seus relatos em todos os dispositivos.", "signIn": "Entrar", "reply": "Quer resposta?", "contactLabel": "Como podemos falar com você?", "contactPh": "E-mail ou nome no GitHub", "privacyTitle": "O que é salvo e quem vê", "priv1": "Seu texto, o tipo e os dados em “Enviado junto”; com “Quer resposta?” também seu contato.", "priv2Anon": "Sem login, o Firebase (Google) cria um identificador aleatório e anônimo para este navegador – sem nome, sem e-mail.", "priv2Konto": "Sua conta (identificador e nome), para que o relato fique associado a você.", "priv3": "Só você e os administradores podem ler. O agente revisor verifica erros e observações; publicamente aparece no máximo um achado derivado, sem dados sobre você.", "priv4": "Em “Meus relatos” você pode retirar qualquer relato a qualquer momento; ele é então excluído.", "privLocal": "Apenas como arquivo neste computador; nada sai dele.", "privIssue": "Texto e dados ficam públicos na issue; sua conta GitHub aparece como autora.", "cancel": "Cancelar", "send": "Enviar", "sendIssue": "Continuar no GitHub", "viaIssue": "Relatar pelo GitHub", "sending": "Enviando…", "doneTitle": "Obrigado – seu relato chegou.", "doneText": "Agora ele aguarda análise. Estado e resposta ficam em “Feedback e curadoria” → “Meus relatos”.", "doneAnon": "A associação vale para este navegador.", "doneLocal": "Salvo localmente: %s", "doneIssue": "O formulário do GitHub está aberto. “Submit new issue” envia o relato.", "again": "Relatar outra coisa", "status": "Ver estado", "e_text_short": "Descreva brevemente do que se trata.", "e_text_long": "Seja mais breve (no máximo 4000 caracteres).", "e_wait": "Você acabou de enviar um relato. Aguarde mais %s segundos.", "e_day": "Você já enviou 20 relatos hoje – obrigado! Amanhã pode continuar.", "e_paused": "Os relatos por esta página estão pausados. Pelo GitHub ainda funciona.", "e_anon_off": "Relatar sem login está desativado agora. Entre ou relate pelo GitHub.", "e_rules": "O relato não foi aceito. Tente de novo em instantes ou relate pelo GitHub.", "e_net": "Sem conexão com o armazenamento. Tente mais tarde ou relate pelo GitHub.", "e_local": "O serviço local não aceitou o relato: %s", "issueTitle": "Feedback (%s)"},
    fr: {"title": "Signaler un retour", "close": "Fermer", "lead": "Parvient aux curateurs et à l'agent de contrôle. Vous en suivez l'état sous « Avis et modération » → « Mes signalements ».", "leadLocal": "Mode local : le signalement est enregistré comme fichier dans _src/spec/feedback-queue/user/.", "leadIssue": "Ici, les avis passent par GitHub : un ticket prérempli et public s'ouvre. Il vous faut un compte GitHub.", "artLabel": "Type", "art_hinweis": "Remarque", "art_fehler": "Erreur", "art_wunsch": "Souhait", "textLabel": "Qu'avez-vous remarqué ?", "ph_hinweis": "Qu'est-ce qui n'est pas clair ou pourrait être mieux ? Une ou deux phrases suffisent.", "ph_fehler": "Qu'est-ce qui est faux, et que faudrait-il ? Une référence (p. ex. un ID SWS) aide.", "ph_wunsch": "Que vous manque-t-il ici, et pour quoi en avez-vous besoin ?", "ctxLabel": "Envoyé avec", "ctxPage": "Page", "ctxFold": "Section", "ctxTarget": "Élément", "ctxSel": "Texte sélectionné", "ctxRelease": "Version", "ctxLang": "Langue", "ctxRemove": "Ne pas envoyer « %s »", "ctxReset": "Renvoyer toutes les indications", "whoKonto": "Envoyé en tant que %s.", "whoAnon": "Vous signalez sans être connecté.", "whoAnonHint": "Connecté, vous retrouvez vos signalements sur tous vos appareils.", "signIn": "Se connecter", "reply": "Souhaitez-vous une réponse ?", "contactLabel": "Comment vous joindre ?", "contactPh": "E-mail ou nom GitHub", "privacyTitle": "Ce qui est enregistré et qui le voit", "priv1": "Votre texte, le type et les indications sous « Envoyé avec » ; avec « Souhaitez-vous une réponse ? » aussi votre contact.", "priv2Anon": "Sans connexion, Firebase (Google) crée pour ce navigateur un identifiant aléatoire et anonyme – ni nom, ni e-mail.", "priv2Konto": "Votre compte (identifiant et nom), pour que le signalement vous soit attribué.", "priv3": "Seuls vous et les administrateurs peuvent le lire. L'agent de contrôle vérifie erreurs et remarques ; publiquement n'apparaît au plus qu'un constat dérivé, sans rien sur vous.", "priv4": "Sous « Mes signalements », vous pouvez retirer un signalement à tout moment ; il est alors supprimé.", "privLocal": "Uniquement comme fichier sur cet ordinateur ; rien n'en sort.", "privIssue": "Le texte et les indications sont publics dans le ticket ; votre compte GitHub apparaît comme auteur.", "cancel": "Annuler", "send": "Envoyer", "sendIssue": "Continuer vers GitHub", "viaIssue": "Signaler via GitHub", "sending": "Envoi …", "doneTitle": "Merci – votre signalement est arrivé.", "doneText": "Il attend maintenant d'être examiné. État et réponse : « Avis et modération » → « Mes signalements ».", "doneAnon": "L'attribution vaut pour ce navigateur.", "doneLocal": "Enregistré localement : %s", "doneIssue": "Le formulaire GitHub est ouvert. « Submit new issue » envoie le signalement.", "again": "Signaler autre chose", "status": "Voir l'état", "e_text_short": "Décrivez brièvement de quoi il s'agit.", "e_text_long": "Soyez plus bref (4000 caractères au plus).", "e_wait": "Vous venez d'envoyer un signalement. Patientez encore %s secondes.", "e_day": "Vous avez déjà envoyé 20 signalements aujourd'hui – merci ! Vous pourrez continuer demain.", "e_paused": "Le signalement par cette page est en pause. GitHub fonctionne toujours.", "e_anon_off": "Le signalement sans connexion est désactivé. Connectez-vous ou signalez via GitHub.", "e_rules": "Le signalement n'a pas été accepté. Réessayez dans un instant ou signalez via GitHub.", "e_net": "Pas de connexion au stockage. Réessayez plus tard ou signalez via GitHub.", "e_local": "Le service local n'a pas accepté le signalement : %s", "issueTitle": "Avis (%s)"},
    ru: {"title": "Оставить отзыв", "close": "Закрыть", "lead": "Попадает к кураторам и агенту проверки. Статус — в «Отзывы и курация» → «Мои сообщения».", "leadLocal": "Локальный режим: сообщение сохраняется файлом в _src/spec/feedback-queue/user/.", "leadIssue": "Здесь отзывы идут через GitHub: откроется заполненный публичный issue. Нужен аккаунт GitHub.", "artLabel": "Тип", "art_hinweis": "Замечание", "art_fehler": "Ошибка", "art_wunsch": "Пожелание", "textLabel": "Что вы заметили?", "ph_hinweis": "Что непонятно или может быть лучше? Достаточно одного-двух предложений.", "ph_fehler": "Что неверно и как правильно? Ссылка (например, SWS-ID) поможет.", "ph_wunsch": "Чего здесь не хватает и для чего это нужно?", "ctxLabel": "Отправляется вместе", "ctxPage": "Страница", "ctxFold": "Раздел", "ctxTarget": "Элемент", "ctxSel": "Выделенный текст", "ctxRelease": "Релиз", "ctxLang": "Язык", "ctxRemove": "Не отправлять «%s»", "ctxReset": "Снова отправлять все данные", "whoKonto": "Отправлено как %s.", "whoAnon": "Вы отправляете без входа.", "whoAnonHint": "После входа ваши сообщения видны на всех устройствах.", "signIn": "Войти", "reply": "Нужен ответ?", "contactLabel": "Как с вами связаться?", "contactPh": "E-mail или имя на GitHub", "privacyTitle": "Что сохраняется и кто это видит", "priv1": "Ваш текст, тип и данные из «Отправляется вместе»; при «Нужен ответ?» также контакт.", "priv2Anon": "Без входа Firebase (Google) создаёт для этого браузера случайный анонимный идентификатор — без имени и e-mail.", "priv2Konto": "Ваш аккаунт (идентификатор и имя), чтобы сообщение было связано с вами.", "priv3": "Читать могут только вы и администраторы. Агент проверки проверяет ошибки и замечания; публично появляется не более чем производная находка без данных о вас.", "priv4": "В «Мои сообщения» вы можете в любой момент отозвать сообщение; тогда оно удаляется.", "privLocal": "Только файлом на этом компьютере; ничего не уходит наружу.", "privIssue": "Текст и данные публичны в issue; автором указан ваш аккаунт GitHub.", "cancel": "Отмена", "send": "Отправить", "sendIssue": "Перейти на GitHub", "viaIssue": "Сообщить через GitHub", "sending": "Отправка…", "doneTitle": "Спасибо — сообщение получено.", "doneText": "Теперь оно ждёт разбора. Статус и ответ — в «Отзывы и курация» → «Мои сообщения».", "doneAnon": "Привязка действует для этого браузера.", "doneLocal": "Сохранено локально: %s", "doneIssue": "Форма GitHub открыта. «Submit new issue» отправит сообщение.", "again": "Сообщить ещё что-то", "status": "Посмотреть статус", "e_text_short": "Опишите кратко, о чём речь.", "e_text_long": "Пожалуйста, короче (не более 4000 символов).", "e_wait": "Вы только что отправили сообщение. Подождите ещё %s с.", "e_day": "Сегодня вы уже отправили 20 сообщений — спасибо! Завтра можно продолжить.", "e_paused": "Отправка через эту страницу сейчас приостановлена. Через GitHub по-прежнему можно.", "e_anon_off": "Отправка без входа сейчас отключена. Войдите или сообщите через GitHub.", "e_rules": "Сообщение не принято. Попробуйте ещё раз чуть позже или сообщите через GitHub.", "e_net": "Нет связи с хранилищем. Попробуйте позже или сообщите через GitHub.", "e_local": "Локальный сервис не принял сообщение: %s", "issueTitle": "Отзыв (%s)"},
    ar: {"title": "إرسال ملاحظات", "close": "إغلاق", "lead": "تصل إلى المنسقين ووكيل المراجعة. تتابع حالتها في «الملاحظات والتقييم» ← «بلاغاتي».", "leadLocal": "وضع محلي: يُحفظ البلاغ ملفًا في _src/spec/feedback-queue/user/.", "leadIssue": "هنا تمر الملاحظات عبر GitHub: تُفتح مسألة معبأة مسبقًا ومرئية للعامة. تحتاج إلى حساب GitHub.", "artLabel": "النوع", "art_hinweis": "ملاحظة", "art_fehler": "خطأ", "art_wunsch": "اقتراح", "textLabel": "ماذا لاحظت؟", "ph_hinweis": "ما غير الواضح أو ما يمكن تحسينه؟ تكفي جملة أو جملتان.", "ph_fehler": "ما الخطأ وما الصحيح؟ يساعد ذكر مرجع (مثل معرّف SWS).", "ph_wunsch": "ما الذي ينقصك هنا ولماذا تحتاجه؟", "ctxLabel": "يُرسل معها", "ctxPage": "الصفحة", "ctxFold": "القسم", "ctxTarget": "العنصر", "ctxSel": "النص المحدد", "ctxRelease": "الإصدار", "ctxLang": "اللغة", "ctxRemove": "لا ترسل «%s»", "ctxReset": "أرسل كل البيانات مجددًا", "whoKonto": "أُرسل باسم %s.", "whoAnon": "أنت تبلّغ دون تسجيل الدخول.", "whoAnonHint": "عند تسجيل الدخول تجد بلاغاتك على جميع أجهزتك.", "signIn": "تسجيل الدخول", "reply": "هل تريد ردًا؟", "contactLabel": "كيف نتواصل معك؟", "contactPh": "البريد أو اسم GitHub", "privacyTitle": "ما الذي يُحفظ ومن يراه", "priv1": "نصّك والنوع والبيانات تحت «يُرسل معها»؛ ومع «هل تريد ردًا؟» أيضًا وسيلة التواصل.", "priv2Anon": "دون تسجيل الدخول ينشئ Firebase (Google) لهذا المتصفح معرّفًا عشوائيًا مجهول الهوية – بلا اسم ولا بريد.", "priv2Konto": "حسابك (المعرّف والاسم) ليُنسب البلاغ إليك.", "priv3": "لا يقرؤه إلا أنت والمسؤولون. يفحص وكيل المراجعة الأخطاء والملاحظات؛ ولا يظهر للعامة إلا نتيجة مشتقة على الأكثر دون بيانات عنك.", "priv4": "في «بلاغاتي» يمكنك سحب أي بلاغ في أي وقت؛ فيُحذف عندها.", "privLocal": "ملفًا على هذا الحاسوب فقط؛ لا يغادره شيء.", "privIssue": "النص والبيانات علنية في المسألة؛ ويظهر حسابك على GitHub كاتبًا لها.", "cancel": "إلغاء", "send": "إرسال", "sendIssue": "المتابعة إلى GitHub", "viaIssue": "الإبلاغ عبر GitHub", "sending": "جارٍ الإرسال…", "doneTitle": "شكرًا – وصل بلاغك.", "doneText": "ينتظر الآن المراجعة. الحالة والرد في «الملاحظات والتقييم» ← «بلاغاتي».", "doneAnon": "يسري الربط على هذا المتصفح.", "doneLocal": "حُفظ محليًا: %s", "doneIssue": "نموذج GitHub مفتوح. زر «Submit new issue» يرسل البلاغ.", "again": "الإبلاغ عن شيء آخر", "status": "عرض الحالة", "e_text_short": "صف باختصار ما الأمر.", "e_text_long": "اختصر من فضلك (4000 حرف على الأكثر).", "e_wait": "أرسلت بلاغًا للتو. انتظر %s ثانية أخرى.", "e_day": "أرسلت اليوم 20 بلاغًا – شكرًا! يمكنك المتابعة غدًا.", "e_paused": "الإبلاغ عبر هذه الصفحة متوقف مؤقتًا. ما زال GitHub متاحًا.", "e_anon_off": "الإبلاغ دون تسجيل الدخول معطّل الآن. سجّل الدخول أو أبلغ عبر GitHub.", "e_rules": "لم يُقبل البلاغ. حاول مجددًا بعد قليل أو أبلغ عبر GitHub.", "e_net": "لا اتصال بالتخزين. حاول لاحقًا أو أبلغ عبر GitHub.", "e_local": "لم تقبل الخدمة المحلية البلاغ: %s", "issueTitle": "ملاحظة (%s)"},
    hi: {"title": "फीडबैक दें", "close": "बंद करें", "lead": "यह क्यूरेटरों और समीक्षा एजेंट तक जाता है। स्थिति “प्रतिक्रिया और क्यूरेशन” → “मेरी रिपोर्टें” में देखें।", "leadLocal": "स्थानीय मोड: रिपोर्ट _src/spec/feedback-queue/user/ में फ़ाइल के रूप में सहेजी जाती है।", "leadIssue": "यहाँ फीडबैक GitHub से जाता है: पहले से भरा, सार्वजनिक issue खुलता है। इसके लिए GitHub खाता चाहिए।", "artLabel": "प्रकार", "art_hinweis": "टिप्पणी", "art_fehler": "त्रुटि", "art_wunsch": "सुझाव", "textLabel": "आपने क्या देखा?", "ph_hinweis": "क्या अस्पष्ट है या बेहतर हो सकता है? एक-दो वाक्य काफ़ी हैं।", "ph_fehler": "क्या गलत है और सही क्या होगा? कोई संदर्भ (जैसे SWS-ID) मदद करता है।", "ph_wunsch": "यहाँ आपको क्या कमी लगती है, और किसलिए चाहिए?", "ctxLabel": "साथ भेजा जाएगा", "ctxPage": "पेज", "ctxFold": "खंड", "ctxTarget": "तत्व", "ctxSel": "चुना गया पाठ", "ctxRelease": "रिलीज़", "ctxLang": "भाषा", "ctxRemove": "“%s” न भेजें", "ctxReset": "सभी जानकारी फिर से भेजें", "whoKonto": "%s के रूप में भेजा गया।", "whoAnon": "आप बिना साइन इन के रिपोर्ट कर रहे हैं।", "whoAnonHint": "साइन इन करने पर आपकी रिपोर्टें हर डिवाइस पर मिलेंगी।", "signIn": "साइन इन करें", "reply": "उत्तर चाहिए?", "contactLabel": "हम आपसे कैसे संपर्क करें?", "contactPh": "ईमेल या GitHub नाम", "privacyTitle": "क्या सहेजा जाता है और कौन देखता है", "priv1": "आपका पाठ, प्रकार और “साथ भेजा जाएगा” की जानकारी; “उत्तर चाहिए?” पर आपका संपर्क भी।", "priv2Anon": "बिना साइन इन के Firebase (Google) इस ब्राउज़र के लिए एक यादृच्छिक, गुमनाम पहचान बनाता है – न नाम, न ईमेल।", "priv2Konto": "आपका खाता (पहचान और नाम), ताकि रिपोर्ट आपसे जुड़ी रहे।", "priv3": "इसे केवल आप और प्रशासक पढ़ सकते हैं। समीक्षा एजेंट त्रुटियों और टिप्पणियों की जाँच करता है; सार्वजनिक रूप से अधिकतम एक व्युत्पन्न निष्कर्ष दिखता है, आपके बारे में कुछ नहीं।", "priv4": "“मेरी रिपोर्टें” में आप कभी भी कोई रिपोर्ट वापस ले सकते हैं; तब वह हटा दी जाती है।", "privLocal": "केवल इस कंप्यूटर पर फ़ाइल के रूप में; कुछ भी बाहर नहीं जाता।", "privIssue": "पाठ और जानकारी issue में सार्वजनिक हैं; लेखक के रूप में आपका GitHub खाता दिखता है।", "cancel": "रद्द करें", "send": "भेजें", "sendIssue": "GitHub पर जारी रखें", "viaIssue": "GitHub से रिपोर्ट करें", "sending": "भेजा जा रहा है…", "doneTitle": "धन्यवाद – आपकी रिपोर्ट मिल गई।", "doneText": "अब यह समीक्षा की प्रतीक्षा में है। स्थिति और उत्तर “प्रतिक्रिया और क्यूरेशन” → “मेरी रिपोर्टें” में मिलेंगे।", "doneAnon": "यह जुड़ाव इस ब्राउज़र के लिए है।", "doneLocal": "स्थानीय रूप से सहेजा गया: %s", "doneIssue": "GitHub फ़ॉर्म खुला है। “Submit new issue” रिपोर्ट भेजता है।", "again": "कुछ और रिपोर्ट करें", "status": "स्थिति देखें", "e_text_short": "कृपया संक्षेप में बताएँ कि बात क्या है।", "e_text_long": "कृपया छोटा लिखें (अधिकतम 4000 अक्षर)।", "e_wait": "आपने अभी-अभी रिपोर्ट भेजी है। कृपया %s सेकंड और रुकें।", "e_day": "आज आप 20 रिपोर्टें भेज चुके हैं – धन्यवाद! कल फिर से भेज सकते हैं।", "e_paused": "इस पेज से रिपोर्ट करना अभी रुका हुआ है। GitHub से अब भी हो सकता है।", "e_anon_off": "बिना साइन इन के रिपोर्ट करना अभी बंद है। साइन इन करें या GitHub से रिपोर्ट करें।", "e_rules": "रिपोर्ट स्वीकार नहीं हुई। थोड़ी देर में फिर कोशिश करें या GitHub से रिपोर्ट करें।", "e_net": "भंडार से कनेक्शन नहीं। बाद में फिर कोशिश करें या GitHub से रिपोर्ट करें।", "e_local": "स्थानीय सेवा ने रिपोर्ट स्वीकार नहीं की: %s", "issueTitle": "फीडबैक (%s)"},
    ko: {"title": "피드백 보내기", "close": "닫기", "lead": "큐레이터와 검토 에이전트에게 전달됩니다. 상태는 ‘피드백 및 큐레이션’ → ‘내 신고’에서 볼 수 있습니다.", "leadLocal": "로컬 모드: 신고는 _src/spec/feedback-queue/user/에 파일로 저장됩니다.", "leadIssue": "여기서는 피드백이 GitHub로 전달됩니다. 미리 채워진 공개 이슈가 열리며 GitHub 계정이 필요합니다.", "artLabel": "유형", "art_hinweis": "의견", "art_fehler": "오류", "art_wunsch": "제안", "textLabel": "무엇을 발견했나요?", "ph_hinweis": "무엇이 불명확하거나 개선될 수 있나요? 한두 문장이면 충분합니다.", "ph_fehler": "무엇이 틀렸고 무엇이 맞나요? 출처(예: SWS ID)가 도움이 됩니다.", "ph_wunsch": "여기서 무엇이 부족하고, 어디에 필요한가요?", "ctxLabel": "함께 전송", "ctxPage": "페이지", "ctxFold": "섹션", "ctxTarget": "요소", "ctxSel": "선택한 텍스트", "ctxRelease": "릴리스", "ctxLang": "언어", "ctxRemove": "‘%s’ 보내지 않기", "ctxReset": "모든 정보 다시 보내기", "whoKonto": "%s(으)로 전송합니다.", "whoAnon": "로그인하지 않고 신고합니다.", "whoAnonHint": "로그인하면 모든 기기에서 내 신고를 다시 볼 수 있습니다.", "signIn": "로그인", "reply": "답변을 원하시나요?", "contactLabel": "어떻게 연락드릴까요?", "contactPh": "이메일 또는 GitHub 이름", "privacyTitle": "저장되는 내용과 볼 수 있는 사람", "priv1": "내 텍스트, 유형, ‘함께 전송’의 정보. ‘답변을 원하시나요?’를 선택하면 연락처도 저장됩니다.", "priv2Anon": "로그인하지 않으면 Firebase(Google)가 이 브라우저에 무작위 익명 ID를 만듭니다. 이름과 이메일은 없습니다.", "priv2Konto": "신고가 나와 연결되도록 내 계정(ID와 이름).", "priv3": "나와 관리자만 읽을 수 있습니다. 검토 에이전트가 오류와 의견을 확인하며, 공개되는 것은 나에 관한 정보 없이 파생된 발견 사항뿐입니다.", "priv4": "‘내 신고’에서 언제든 신고를 철회할 수 있으며, 그러면 삭제됩니다.", "privLocal": "이 컴퓨터의 파일로만 저장되며 밖으로 나가지 않습니다.", "privIssue": "텍스트와 정보는 이슈에 공개되며, 작성자로 내 GitHub 계정이 표시됩니다.", "cancel": "취소", "send": "보내기", "sendIssue": "GitHub로 계속", "viaIssue": "GitHub로 신고", "sending": "보내는 중…", "doneTitle": "감사합니다. 신고가 접수되었습니다.", "doneText": "이제 검토를 기다립니다. 상태와 답변은 ‘피드백 및 큐레이션’ → ‘내 신고’에 있습니다.", "doneAnon": "연결은 이 브라우저에 적용됩니다.", "doneLocal": "로컬에 저장됨: %s", "doneIssue": "GitHub 양식이 열렸습니다. ‘Submit new issue’를 누르면 신고가 전송됩니다.", "again": "다른 내용 신고", "status": "상태 보기", "e_text_short": "무엇에 관한 것인지 간단히 적어 주세요.", "e_text_long": "조금 더 짧게 적어 주세요(최대 4000자).", "e_wait": "방금 신고하셨습니다. %s초만 더 기다려 주세요.", "e_day": "오늘 이미 20건을 신고하셨습니다. 감사합니다! 내일 다시 이용할 수 있습니다.", "e_paused": "이 페이지를 통한 신고는 잠시 중단되었습니다. GitHub는 계속 이용할 수 있습니다.", "e_anon_off": "로그인 없는 신고는 지금 꺼져 있습니다. 로그인하거나 GitHub로 신고하세요.", "e_rules": "신고가 접수되지 않았습니다. 잠시 후 다시 시도하거나 GitHub로 신고하세요.", "e_net": "저장소에 연결할 수 없습니다. 나중에 다시 시도하거나 GitHub로 신고하세요.", "e_local": "로컬 서비스가 신고를 받지 않았습니다: %s", "issueTitle": "피드백 (%s)"},
    zh: {"title": "提供反馈", "close": "关闭", "lead": "会发送给策展人和审查代理。可在“反馈与策展”→“我的报告”中查看进展。", "leadLocal": "本地模式：报告会作为文件保存在 _src/spec/feedback-queue/user/。", "leadIssue": "此处反馈通过 GitHub 提交：会打开一个预填的公开 issue，需要 GitHub 账号。", "artLabel": "类型", "art_hinweis": "意见", "art_fehler": "错误", "art_wunsch": "建议", "textLabel": "你注意到了什么？", "ph_hinweis": "哪里不清楚或可以改进？一两句话即可。", "ph_fehler": "哪里不对，正确的是什么？附上出处（如 SWS 编号）会有帮助。", "ph_wunsch": "这里缺少什么，你需要它做什么？", "ctxLabel": "一并发送", "ctxPage": "页面", "ctxFold": "章节", "ctxTarget": "元素", "ctxSel": "选中的文本", "ctxRelease": "版本", "ctxLang": "语言", "ctxRemove": "不发送“%s”", "ctxReset": "重新发送全部信息", "whoKonto": "以 %s 的身份发送。", "whoAnon": "你正在未登录状态下报告。", "whoAnonHint": "登录后，你可以在所有设备上找到自己的报告。", "signIn": "登录", "reply": "需要回复？", "contactLabel": "如何联系你？", "contactPh": "邮箱或 GitHub 用户名", "privacyTitle": "会保存什么，谁能看到", "priv1": "你的文本、类型以及“一并发送”中的信息；勾选“需要回复？”时还包括你的联系方式。", "priv2Anon": "未登录时，Firebase（Google）会为此浏览器创建一个随机的匿名标识——不含姓名和邮箱。", "priv2Konto": "你的账号（标识和姓名），以便报告与你关联。", "priv3": "只有你和管理员可以阅读。审查代理会核查错误和意见；公开显示的最多是由此得出的发现，不含任何关于你的信息。", "priv4": "你可以随时在“我的报告”中撤回任何报告，撤回后即被删除。", "privLocal": "仅作为文件保存在这台电脑上，不会外传。", "privIssue": "文本和信息会公开在 issue 中，作者显示为你的 GitHub 账号。", "cancel": "取消", "send": "发送", "sendIssue": "前往 GitHub", "viaIssue": "通过 GitHub 报告", "sending": "正在发送…", "doneTitle": "谢谢——你的报告已收到。", "doneText": "现在等待审阅。进展和回复见“反馈与策展”→“我的报告”。", "doneAnon": "此关联仅适用于此浏览器。", "doneLocal": "已在本地保存：%s", "doneIssue": "GitHub 表单已打开。点击“Submit new issue”即可提交报告。", "again": "再报告一项", "status": "查看进展", "e_text_short": "请简要说明是什么问题。", "e_text_long": "请写得短一些（最多 4000 个字符）。", "e_wait": "你刚刚提交过报告。请再等 %s 秒。", "e_day": "你今天已提交 20 条报告——谢谢！明天可以继续。", "e_paused": "通过本页报告暂时暂停。仍可通过 GitHub 报告。", "e_anon_off": "未登录报告目前已关闭。请登录或通过 GitHub 报告。", "e_rules": "报告未被接受。请稍后重试或通过 GitHub 报告。", "e_net": "无法连接到存储。请稍后重试或通过 GitHub 报告。", "e_local": "本地服务未接受报告：%s", "issueTitle": "反馈（%s）"},
    nl: {"title": "Feedback melden", "close": "Sluiten", "lead": "Gaat naar de curatoren en de controle-agent. De status zie je onder ‘Feedback & curatie’ → ‘Mijn meldingen’.", "leadLocal": "Lokale modus: de melding wordt als bestand opgeslagen in _src/spec/feedback-queue/user/.", "leadIssue": "Hier loopt feedback via GitHub: er opent een vooraf ingevuld, openbaar issue. Je hebt een GitHub-account nodig.", "artLabel": "Soort", "art_hinweis": "Opmerking", "art_fehler": "Fout", "art_wunsch": "Wens", "textLabel": "Wat viel je op?", "ph_hinweis": "Wat is onduidelijk of kan beter? Een of twee zinnen zijn genoeg.", "ph_fehler": "Wat klopt niet, en wat zou juist zijn? Een vindplaats (bijv. een SWS-ID) helpt.", "ph_wunsch": "Wat mis je hier, en waarvoor heb je het nodig?", "ctxLabel": "Wordt meegestuurd", "ctxPage": "Pagina", "ctxFold": "Sectie", "ctxTarget": "Element", "ctxSel": "Gemarkeerde tekst", "ctxRelease": "Release", "ctxLang": "Taal", "ctxRemove": "‘%s’ niet meesturen", "ctxReset": "Alle gegevens weer meesturen", "whoKonto": "Verzonden als %s.", "whoAnon": "Je meldt zonder aan te melden.", "whoAnonHint": "Aangemeld vind je je meldingen op al je apparaten terug.", "signIn": "Aanmelden", "reply": "Antwoord gewenst?", "contactLabel": "Hoe bereiken we je?", "contactPh": "E-mail of GitHub-naam", "privacyTitle": "Wat wordt opgeslagen en wie ziet het", "priv1": "Je tekst, de soort en de gegevens onder ‘Wordt meegestuurd’; bij ‘Antwoord gewenst?’ ook je contactgegeven.", "priv2Anon": "Zonder aanmelden maakt Firebase (Google) voor deze browser een willekeurige, anonieme ID aan – geen naam, geen e-mail.", "priv2Konto": "Je account (ID en naam), zodat de melding aan jou gekoppeld is.", "priv3": "Alleen jij en de beheerders kunnen het lezen. De controle-agent controleert fouten en opmerkingen; openbaar verschijnt hooguit een afgeleide bevinding, zonder gegevens over jou.", "priv4": "Onder ‘Mijn meldingen’ kun je elke melding op elk moment intrekken; ze wordt dan verwijderd.", "privLocal": "Alleen als bestand op deze computer; er gaat niets naar buiten.", "privIssue": "Tekst en gegevens staan openbaar in het issue; je GitHub-account verschijnt als auteur.", "cancel": "Annuleren", "send": "Versturen", "sendIssue": "Verder naar GitHub", "viaIssue": "Via GitHub melden", "sending": "Wordt verstuurd …", "doneTitle": "Bedankt – je melding is aangekomen.", "doneText": "Ze wacht nu op beoordeling. Status en antwoord vind je onder ‘Feedback & curatie’ → ‘Mijn meldingen’.", "doneAnon": "De koppeling geldt voor deze browser.", "doneLocal": "Lokaal opgeslagen: %s", "doneIssue": "Het GitHub-formulier is geopend. ‘Submit new issue’ verstuurt de melding.", "again": "Nog iets melden", "status": "Status bekijken", "e_text_short": "Beschrijf kort waar het om gaat.", "e_text_long": "Houd het korter (hooguit 4000 tekens).", "e_wait": "Je hebt net iets gemeld. Wacht nog %s seconden.", "e_day": "Je hebt vandaag al 20 meldingen gestuurd – bedankt! Morgen kun je verder.", "e_paused": "Melden via deze pagina is even gepauzeerd. Via GitHub kan het nog wel.", "e_anon_off": "Melden zonder aanmelden staat nu uit. Meld je aan of meld via GitHub.", "e_rules": "De melding is niet aangenomen. Probeer het zo meteen opnieuw of meld via GitHub.", "e_net": "Geen verbinding met de opslag. Probeer het later opnieuw of meld via GitHub.", "e_local": "De lokale dienst heeft de melding niet aangenomen: %s", "issueTitle": "Feedback (%s)"}
  };

  function lang() {
    var l = (typeof document !== "undefined" && document.documentElement.lang) || "en";
    l = l.split("-")[0];
    return L[l] ? l : "en";
  }
  function t(key, arg) {
    var d = L[lang()] || L.en;
    var s = d[key] != null ? d[key] : (L.en[key] != null ? L.en[key] : key);
    return arg == null ? s : s.replace("%s", arg);
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function clip(s, n) { s = String(s == null ? "" : s).replace(/\s+/g, " ").trim(); return Array.from(s).slice(0, n).join(""); }
  function access() { return typeof window !== "undefined" && window.AiAccess && window.AiAccess.feedback ? window.AiAccess : null; }

  // Eingaben normalisieren wie die Firestore-Regeln und feedback_ingest.validate_v2 (Paritätstest in
  // _src/tests/test_feedback_ingest.py): Text 3–4000 Zeichen, bekannte Bezugsfelder mit Längengrenzen.
  function buildFeedbackRecord(input) {
    input = input || {};
    var text = String(input.text == null ? "" : input.text).replace(/\r\n?/g, "\n")
      .replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/g, "").trim();
    if (Array.from(text).length < 3) { var e1 = new Error("text_short"); e1.code = "text_short"; throw e1; }
    if (Array.from(text).length > 4000) { var e2 = new Error("text_long"); e2.code = "text_long"; throw e2; }
    var out = { schema: SCHEMA, art: ARTS.indexOf(input.art) === -1 ? "hinweis" : input.art, text: text };
    var ctx = {};
    Object.keys(input.ctx || {}).forEach(function (k) {
      if (!CTX_LIMIT[k] || input.ctx[k] == null) return;
      var v = clip(input.ctx[k], CTX_LIMIT[k]);
      if (v) ctx[k] = v;
    });
    if (Object.keys(ctx).length) out.ctx = ctx;
    var contact = clip(input.contact, 120);
    if (contact) out.contact = contact;
    return out;
  }

  // ---- Bezug der Meldung aus der Seite
  function textOf(el) {
    if (!el) return "";
    var c = el.cloneNode(true);
    c.querySelectorAll(".ai-badge, .vis-tag, .ai-trace-badge, button, .sr-only, svg").forEach(function (x) { x.remove(); });
    return clip(c.textContent, 200);
  }
  function currentRelease() {
    var h = (typeof location !== "undefined" && location.hash) || "";
    try { h = decodeURIComponent(h); } catch (_) { /* unkodierter Hash */ }
    var m = /(?:^#|&)release=([^&]+)/.exec(h) || /[?&]release=([^&#]+)/.exec((typeof location !== "undefined" && location.search) || "");
    if (m) return clip(m[1], 40);
    var cur = document.querySelector(".release-dropdown .releases a.cur") || document.querySelector(".release-dropdown .releases a");
    return cur ? clip(cur.textContent, 40) : "";
  }
  function detectTargetId() {
    var dataEl = document.querySelector(".review-request-data");
    if (dataEl) {
      try { var data = JSON.parse(dataEl.textContent); if (data && data.canonical_id) return String(data.canonical_id); } catch (_) {}
    }
    var attr = document.querySelector("[data-canonical-id]");
    if (attr && attr.getAttribute("data-canonical-id")) return attr.getAttribute("data-canonical-id");
    var rec = document.querySelector("article.rec[id], section.rec[id]");
    return rec && rec.id ? rec.id : "";
  }
  // Auswahl beim Drücken des Knopfs merken (danach kann der Browser sie aufheben).
  var lastSelection = "";
  function rememberSelection(e) {
    var b = e.target && e.target.closest && e.target.closest("[data-feedback-open]");
    if (!b) return;
    var s = "";
    try { s = String(window.getSelection ? window.getSelection() : ""); } catch (_) { s = ""; }
    lastSelection = clip(s, 1000);
  }
  function gatherContext(opener) {
    var ctx = {};
    var h1 = document.querySelector("main h1, h1");
    ctx.title = textOf(h1) || clip(document.title, 200);
    ctx.page = clip(location.pathname + (location.hash && !/release=/.test(location.hash) ? location.hash : ""), 300);
    var fold = opener && opener.closest && opener.closest("details");
    var summary = fold && fold.querySelector(":scope > summary");
    if (summary) ctx.fold = textOf(summary);
    var target = (opener && opener.getAttribute && opener.getAttribute("data-target-id")) || detectTargetId();
    if (target && target !== ctx.title) ctx.target = clip(target, 256);
    if (lastSelection) ctx.selection = lastSelection;
    var rel = currentRelease();
    if (rel) ctx.release = rel;
    ctx.lang = clip(document.documentElement.lang || "", 8);
    Object.keys(ctx).forEach(function (k) { if (!ctx[k]) delete ctx[k]; });
    return ctx;
  }
  function chipText(k, v) {
    var label = { title: t("ctxPage"), fold: t("ctxFold"), target: t("ctxTarget"), selection: t("ctxSel"), release: t("ctxRelease"), lang: t("ctxLang") }[k];
    var shown = k === "selection" ? "„" + clip(v, 60) + (Array.from(v).length > 60 ? "…" : "") + "“" : k === "lang" ? String(v).toUpperCase() : clip(v, 48) + (Array.from(v).length > 48 ? "…" : "");
    return { label: label, shown: shown };
  }

  // ---- GitHub-Issue als Ausweg (ohne Firebase oder wenn das Melden pausiert ist)
  function issueText(rec) {
    var c = rec.ctx || {};
    var lines = [rec.text, ""];
    if (c.selection) lines.push(t("ctxSel") + ": „" + c.selection + "“");
    [["title", "ctxPage"], ["fold", "ctxFold"], ["target", "ctxTarget"], ["release", "ctxRelease"], ["lang", "ctxLang"]].forEach(function (p) {
      if (c[p[0]]) lines.push(t(p[1]) + ": " + c[p[0]]);
    });
    if (c.page) lines.push(location.origin + c.page);
    lines.push("", "<!-- " + SCHEMA + " " + JSON.stringify({ art: rec.art, ctx: c }) + " -->");
    return { title: t("issueTitle", t("art_" + rec.art)) + ": " + clip(rec.text, 60), body: lines.join("\n") };
  }
  function openIssue(rec) {
    var it = issueText(rec), a = access();
    if (a && typeof a.openIssue === "function") return a.openIssue(it.title, it.body);
    var m = document.querySelector('meta[name="review-github-repo"]');
    var url = "https://github.com/" + ((m && m.content) || "2b-rs/autodocs") + "/issues/new?title=" + encodeURIComponent(it.title) + "&body=" + encodeURIComponent(it.body);
    window.open(url.slice(0, 7900), "_blank", "noopener");
    return Promise.resolve({ mode: "url" });
  }

  // ---- Dialog
  var dlg = null, opener = null, state = null;
  function build() {
    dlg = document.createElement("div");
    dlg.className = "rv-modal fb-modal";
    dlg.hidden = true;
    dlg.innerHTML =
      '<div class="rv-modal-scrim" data-fb-close></div>' +
      '<div class="rv-modal-card fb-card" id="feedback-dialog" role="dialog" aria-modal="true" aria-labelledby="fb-title" aria-describedby="fb-lead">' +
        '<header class="rv-modal-head"><h2 id="fb-title">' + esc(t("title")) + '</h2>' +
        '<button type="button" class="rv-icon-btn" data-fb-close aria-label="' + esc(t("close")) + '">×</button></header>' +
        '<div class="rv-modal-body fb-body" data-fb-form>' +
          '<p class="fb-lead" id="fb-lead" data-fb-lead></p>' +
          '<p class="fb-notice" data-fb-notice hidden></p>' +
          '<div class="fb-seg" role="radiogroup" aria-label="' + esc(t("artLabel")) + '">' + ARTS.map(function (a) {
            return '<button type="button" role="radio" data-fb-art="' + a + '">' + esc(t("art_" + a)) + "</button>";
          }).join("") + "</div>" +
          '<label class="fb-label" for="fb-text">' + esc(t("textLabel")) + "</label>" +
          '<textarea id="fb-text" class="fb-text" rows="4" maxlength="4000" data-fb-text aria-describedby="fb-err"></textarea>' +
          '<p class="fb-err" id="fb-err" data-fb-err role="alert" hidden></p>' +
          '<div class="fb-ctx" data-fb-ctx-wrap><span class="fb-ctx-label">' + esc(t("ctxLabel")) + '</span>' +
            '<ul class="fb-chips" data-fb-chips></ul>' +
            '<button type="button" class="fb-link" data-fb-ctx-reset hidden>' + esc(t("ctxReset")) + "</button></div>" +
          '<p class="fb-who" data-fb-who></p>' +
          '<div data-fb-reply-wrap><label class="fb-check"><input type="checkbox" data-fb-reply><span>' + esc(t("reply")) + "</span></label>" +
          '<div class="fb-reply" data-fb-reply-box hidden><label class="fb-label" for="fb-contact">' + esc(t("contactLabel")) + "</label>" +
            '<input id="fb-contact" class="fb-input" type="text" maxlength="120" autocomplete="email" data-fb-contact placeholder="' + esc(t("contactPh")) + '"></div></div>' +
          '<details class="fb-privacy"><summary>' + esc(t("privacyTitle")) + '</summary><ul data-fb-privacy></ul></details>' +
        "</div>" +
        '<div class="rv-modal-body fb-body fb-done" data-fb-done hidden tabindex="-1">' +
          '<p class="fb-done-mark" aria-hidden="true">✓</p><h3 class="fb-done-title" data-fb-done-title></h3><p data-fb-done-text></p></div>' +
        '<footer class="rv-modal-foot fb-foot" data-fb-foot></footer>' +
      "</div>";
    document.body.appendChild(dlg);
    dlg.addEventListener("click", onClick);
    dlg.addEventListener("input", function (e) { if (e.target.matches("[data-fb-text]")) showError(""); });
    dlg.addEventListener("change", function (e) {
      if (e.target.matches("[data-fb-reply]")) {
        var box = dlg.querySelector("[data-fb-reply-box]");
        box.hidden = !e.target.checked;
        if (e.target.checked) { var c = dlg.querySelector("[data-fb-contact]"); if (!c.value && state.channel && state.channel.email) c.value = state.channel.email; c.focus(); }
      }
    });
    dlg.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { e.preventDefault(); close(); return; }
      if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && e.target.matches("[data-fb-text]")) { e.preventDefault(); submit(); return; }
      if (e.target.matches("[data-fb-art]") && (e.key === "ArrowRight" || e.key === "ArrowLeft")) {
        e.preventDefault();
        var i = ARTS.indexOf(state.art) + (e.key === "ArrowRight" ? 1 : -1);
        setArt(ARTS[(i + ARTS.length) % ARTS.length], true);
        return;
      }
      if (e.key !== "Tab") return;
      var list = Array.prototype.filter.call(dlg.querySelectorAll("button, [href], input, textarea, summary"), function (n) {
        return !n.disabled && n.offsetParent !== null && n.tabIndex !== -1;
      });
      if (!list.length) return;
      if (e.shiftKey && document.activeElement === list[0]) { e.preventDefault(); list[list.length - 1].focus(); }
      else if (!e.shiftKey && document.activeElement === list[list.length - 1]) { e.preventDefault(); list[0].focus(); }
    });
    if (typeof window !== "undefined") {
      window.addEventListener("aiaccess-change", function () { if (dlg && !dlg.hidden && state && !state.done) refreshChannel(); });
    }
  }
  function setArt(a, focus) {
    state.art = a;
    dlg.querySelectorAll("[data-fb-art]").forEach(function (b) {
      var on = b.getAttribute("data-fb-art") === a;
      b.setAttribute("aria-checked", on ? "true" : "false");
      b.tabIndex = on ? 0 : -1;
      if (on && focus) b.focus();
    });
    dlg.querySelector("[data-fb-text]").placeholder = t("ph_" + a);
  }
  function renderChips() {
    var ul = dlg.querySelector("[data-fb-chips]");
    var keys = CTX_ORDER.filter(function (k) { return state.ctx[k] && !state.removed[k]; });
    ul.innerHTML = keys.map(function (k) {
      var c = chipText(k, state.ctx[k]);
      return '<li class="fb-chip" data-fb-chip="' + k + '" title="' + esc(state.ctx[k]) + '"><span class="fb-chip-k">' + esc(c.label) + '</span> <span class="fb-chip-v">' + esc(c.shown) + "</span>" +
        '<button type="button" class="fb-chip-x" data-fb-chip-x="' + k + '" aria-label="' + esc(t("ctxRemove", c.label)) + '">×</button></li>';
    }).join("");
    dlg.querySelector("[data-fb-ctx-wrap]").hidden = !keys.length && !Object.keys(state.removed).length;
    dlg.querySelector("[data-fb-ctx-reset]").hidden = !Object.keys(state.removed).length;
  }
  function footer(buttons) {
    dlg.querySelector("[data-fb-foot]").innerHTML = buttons.map(function (b) {
      if (b === "|") return '<span class="rv-spacer"></span>';
      return '<button type="button" class="rv-btn' + (b.primary ? " rv-btn-primary" : b.quiet ? " rv-btn-quiet" : "") + '" data-fb-act="' + b.act + '"' +
        (b.disabled ? " disabled" : "") + ">" + esc(b.label) + "</button>";
    }).join("");
  }
  function privacy(kind, signedIn) {
    var items = kind === "local" ? [t("privLocal")] : kind === "issue" ? [t("privIssue")]
      : [t("priv1"), signedIn ? t("priv2Konto") : t("priv2Anon"), t("priv3"), t("priv4")];
    dlg.querySelector("[data-fb-privacy]").innerHTML = items.map(function (s) { return "<li>" + esc(s) + "</li>"; }).join("");
  }
  // Je nach Weg: Erklärung, Hinweise mit wirksamer Aktion, Fußzeile.
  function renderChannel() {
    // Solange der Weg noch ermittelt wird („pending“): Standardtext, Senden wartet darauf (submit).
    var ch = state.channel || { kind: "pending" };
    var lead = dlg.querySelector("[data-fb-lead]"), notice = dlg.querySelector("[data-fb-notice]"), who = dlg.querySelector("[data-fb-who]");
    lead.textContent = ch.kind === "local" ? t("leadLocal") : ch.kind === "issue" ? t("leadIssue") : t("lead");
    notice.hidden = true;
    who.innerHTML = "";
    var blockedAnon = ch.kind === "firestore" && ch.open && !ch.signedIn && !ch.anonym;
    var paused = ch.kind === "firestore" && !ch.open;
    if (ch.kind === "firestore") {
      if (ch.signedIn) who.innerHTML = esc(t("whoKonto", ch.name || "")) ;
      else who.innerHTML = esc(t("whoAnon")) + (ch.canSignIn ? ' <button type="button" class="fb-link" data-fb-act="signin">' + esc(t("signIn")) + "</button>" : "") +
        '<br><span class="fb-fine">' + esc(t("whoAnonHint")) + "</span>";
      if (paused || blockedAnon) { notice.hidden = false; notice.textContent = t(paused ? "e_paused" : "e_anon_off"); }
    }
    dlg.querySelector("[data-fb-reply-wrap]").hidden = ch.kind === "issue";
    privacy(ch.kind, !!ch.signedIn);
    var send = { act: "send", label: t("send"), primary: true };
    if (ch.kind === "issue" || paused) send = { act: "issue", label: t("sendIssue"), primary: true };
    var btns = [{ act: "cancel", label: t("cancel"), quiet: true }, "|"];
    if (blockedAnon) {
      btns.push({ act: "issue", label: t("viaIssue") });
      if (ch.canSignIn) btns.push({ act: "signin", label: t("signIn"), primary: true });
    } else {
      if (state.offerIssue && send.act !== "issue") btns.push({ act: "issue", label: t("viaIssue") });
      btns.push(send);
    }
    footer(btns);
  }
  function refreshChannel() {
    var a = access();
    var p = a ? a.feedback.channel() : Promise.resolve({ kind: "issue" });
    return p.catch(function () { return { kind: "issue" }; }).then(function (ch) {
      if (!state) return;
      state.channel = ch;
      if (!state.done) renderChannel();
    });
  }
  function showError(msg, offerIssue) {
    var box = dlg.querySelector("[data-fb-err]");
    box.hidden = !msg;
    box.textContent = msg || "";
    if (offerIssue != null && state.offerIssue !== offerIssue) { state.offerIssue = offerIssue; renderChannel(); }
  }
  function currentRecord() {
    var ctx = {};
    Object.keys(state.ctx).forEach(function (k) { if (!state.removed[k]) ctx[k] = state.ctx[k]; });
    if (state.removed.title) delete ctx.page;
    var reply = dlg.querySelector("[data-fb-reply]").checked;
    return buildFeedbackRecord({ art: state.art, text: dlg.querySelector("[data-fb-text]").value, ctx: ctx,
                                 contact: reply ? dlg.querySelector("[data-fb-contact]").value : "" });
  }
  function errorText(e) {
    var code = e && e.code;
    if (code === "wait") return [t("e_wait", String(e.wait || 30)), false];
    if (code === "day") return [t("e_day"), true];
    if (code === "paused") return [t("e_paused"), true];
    if (code === "anon_off") return [t("e_anon_off"), true];
    if (code === "rules") return [t("e_rules"), true];
    if (code === "local") return [t("e_local", e.detail || ""), false];
    if (code === "text_short") return [t("e_text_short"), false];
    if (code === "text_long") return [t("e_text_long"), false];
    return [t("e_net"), true];
  }
  function busy(on) {
    dlg.querySelectorAll("[data-fb-act]").forEach(function (b) { b.disabled = on; });
    var s = dlg.querySelector('[data-fb-act="send"]');
    if (s) s.textContent = on ? t("sending") : t("send");
  }
  function submit() {
    var rec;
    try { rec = currentRecord(); } catch (e) {
      showError(errorText(e)[0]);
      dlg.querySelector("[data-fb-text]").focus();
      return;
    }
    var a = access();
    if (!a) { viaIssue(rec); return; }
    var current = state;
    busy(true);
    // Weg noch unbekannt (Klick direkt nach dem Öffnen): erst ermitteln, dann senden.
    (state.channel ? Promise.resolve() : refreshChannel()).then(function () {
      if (state !== current) return null;
      if (!state.channel || state.channel.kind === "issue") { busy(false); viaIssue(rec); return null; }
      return a.feedback.send(rec).then(function (res) {
        if (state === current) done(res.kind === "local" ? "local" : "firestore", res);
      }, function (e) {
        if (state !== current) return;
        busy(false);
        var m = errorText(e);
        showError(m[0], m[1]);
      });
    });
  }
  function viaIssue(rec) {
    if (!rec) {
      try { rec = currentRecord(); } catch (e) { showError(errorText(e)[0]); dlg.querySelector("[data-fb-text]").focus(); return; }
    }
    var current = state;
    Promise.resolve(openIssue(rec)).then(function () { if (state === current) done("issue", {}); });
  }
  function done(kind, res) {
    state.done = true;
    dlg.querySelector("[data-fb-form]").hidden = true;
    var d = dlg.querySelector("[data-fb-done]");
    d.hidden = false;
    dlg.querySelector("[data-fb-done-title]").textContent = kind === "issue" ? t("sendIssue") : t("doneTitle");
    var txt = kind === "local" ? t("doneLocal", res.path || res.id || "") : kind === "issue" ? t("doneIssue")
      : t("doneText") + (res.auth === "anonym" ? " " + t("doneAnon") : "");
    dlg.querySelector("[data-fb-done-text]").textContent = txt;
    var btns = [{ act: "again", label: t("again"), quiet: true }, "|"];
    if (kind === "firestore") btns.push({ act: "status", label: t("status") });
    btns.push({ act: "close", label: t("close"), primary: true });
    footer(btns);
    d.focus();
  }
  function onClick(e) {
    if (e.target.closest("[data-fb-close]")) { close(); return; }
    var art = e.target.closest("[data-fb-art]");
    if (art) { setArt(art.getAttribute("data-fb-art")); return; }
    var x = e.target.closest("[data-fb-chip-x]");
    if (x) { state.removed[x.getAttribute("data-fb-chip-x")] = true; renderChips(); dlg.querySelector("[data-fb-text]").focus(); return; }
    if (e.target.closest("[data-fb-ctx-reset]")) { state.removed = {}; renderChips(); return; }
    var b = e.target.closest("[data-fb-act]");
    if (!b || b.disabled) return;
    var act = b.getAttribute("data-fb-act");
    var a = access();
    if (act === "cancel" || act === "close") close();
    else if (act === "send") submit();
    else if (act === "issue") viaIssue();
    else if (act === "signin") { if (a && a.feedback.signIn) a.feedback.signIn(); }
    else if (act === "again") { var o = opener; close(true); open(o); }
    else if (act === "status") {
      close();
      if (window.araReview && window.araReview.openDrawer) window.araReview.openDrawer("feedback");
    }
  }
  function open(from) {
    if (!dlg) build();
    opener = from || null;
    // Aus dem Panel „Feedback & Kuration“ heraus: das Panel schließen, der Dialog steht dann allein.
    if (opener && opener.closest && opener.closest(".rv-drawer") && window.araReview && window.araReview.closeDrawer) window.araReview.closeDrawer();
    state = { art: "hinweis", ctx: gatherContext(opener), removed: {}, channel: null, done: false, offerIssue: false };
    lastSelection = "";
    dlg.querySelector("[data-fb-form]").hidden = false;
    dlg.querySelector("[data-fb-done]").hidden = true;
    var ta = dlg.querySelector("[data-fb-text]");
    ta.value = "";
    dlg.querySelector("[data-fb-reply]").checked = false;
    dlg.querySelector("[data-fb-reply-box]").hidden = true;
    dlg.querySelector("[data-fb-contact]").value = "";
    dlg.querySelector(".fb-privacy").open = false;
    setArt("hinweis");
    renderChips();
    showError("");
    renderChannel();
    refreshChannel();
    dlg.hidden = false;
    requestAnimationFrame(function () { dlg.classList.add("is-open"); });
    if (opener) opener.setAttribute("aria-expanded", "true");
    setTimeout(function () { ta.focus(); }, 20);
  }
  function close(keepOpener) {
    if (!dlg) return;
    dlg.classList.remove("is-open");
    dlg.hidden = true;
    if (opener) {
      opener.setAttribute("aria-expanded", "false");
      if (!keepOpener && document.contains(opener) && opener.offsetParent !== null) opener.focus();
    }
    state = null;
  }

  // Ohne Auslöser auf der Seite (Seiten ohne Kopfleiste): schwebender Knopf.
  function ensureTrigger() {
    if (document.querySelector("[data-feedback-open]")) return null;
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "feedback-open is-floating";
    btn.setAttribute("data-feedback-open", "");
    btn.setAttribute("aria-haspopup", "dialog");
    btn.setAttribute("aria-expanded", "false");
    btn.setAttribute("aria-controls", "feedback-dialog");
    btn.textContent = t("title");
    document.body.appendChild(btn);
    return btn;
  }
  function bindTriggers() {
    document.addEventListener("pointerdown", rememberSelection, true);
    document.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") rememberSelection(e); }, true);
    document.addEventListener("click", function (e) {
      var b = e.target.closest && e.target.closest("[data-feedback-open]");
      if (!b) return;
      e.preventDefault();
      open(b);
    });
  }

  function initVersionNav() {
    document.querySelectorAll(".rec-version-nav").forEach(function (nav) {
      if (nav.getAttribute("data-vnav-bound")) return;
      nav.setAttribute("data-vnav-bound", "1");

      var canonicalId = nav.getAttribute("data-canonical-id");
      var select = nav.querySelector("[data-asof-select]");
      var btn = nav.querySelector("[data-asof-btn]");
      var display = nav.querySelector("[data-asof-display]");
      var closeBtn = nav.querySelector("[data-asof-close]");
      var labelEl = nav.querySelector("[data-asof-label]");
      var textEl = nav.querySelector("[data-asof-text]");
      var decisionsWrap = nav.querySelector("[data-asof-decisions-wrap]");
      var decisionsList = nav.querySelector("[data-asof-decisions]");
      var graphWrap = nav.querySelector("[data-asof-graph-wrap]");
      var graphList = nav.querySelector("[data-asof-graph]");

      function loadSnapshot(rel) {
        if (!rel) return;
        var url = "/api/asof?id=" + encodeURIComponent(canonicalId) + "&release=" + encodeURIComponent(rel);
        if (btn) btn.disabled = true;
        fetch(url)
          .then(function (res) {
            if (!res.ok) throw new Error("HTTP " + res.status);
            return res.json();
          })
          .then(function (data) {
            if (btn) btn.disabled = false;
            if (!data.ok) throw new Error(data.error || "Request failed");
            if (display) display.hidden = false;
            if (labelEl) labelEl.textContent = (data.as_of ? data.as_of.value : rel);
            if (textEl) {
              if (data.version && data.version.content) {
                textEl.textContent = data.version.content;
              } else {
                textEl.textContent = "(No active version recorded as of release " + rel + ")";
              }
            }

            // Decisions
            if (decisionsWrap && decisionsList) {
              if (data.decisions && data.decisions.length > 0) {
                decisionsWrap.hidden = false;
                decisionsList.innerHTML = data.decisions.map(function (d) {
                  return "<li>Decided on version: <code>" + esc(d.decided_on_version) + "</code></li>";
                }).join("");
              } else {
                decisionsWrap.hidden = true;
                decisionsList.innerHTML = "";
              }
            }

            // Artifact graph
            if (graphWrap && graphList) {
              var graphKeys = data.artifact_graph ? Object.keys(data.artifact_graph) : [];
              if (graphKeys.length > 0) {
                graphWrap.hidden = false;
                graphList.innerHTML = graphKeys.map(function (k) {
                  var node = data.artifact_graph[k];
                  var flags = [];
                  if (node.invalidated) flags.push('<span class="rec-status-invalid" style="padding:0.1rem 0.3rem;font-size:0.7rem;border-radius:3px;">invalidated</span>');
                  if (node.dismissed) flags.push('<span class="rec-status-neutral" style="padding:0.1rem 0.3rem;font-size:0.7rem;border-radius:3px;">dismissed</span>');
                  return "<li><code>" + esc(k) + "</code> " + flags.join(" ") + "</li>";
                }).join("");
              } else {
                graphWrap.hidden = true;
                graphList.innerHTML = "";
              }
            }
          })
          .catch(function (err) {
            if (btn) btn.disabled = false;
            if (display) display.hidden = false;
            if (labelEl) labelEl.textContent = rel;
            if (textEl) {
              textEl.textContent = "Snapshot view (preview query failed or running static): " + (err && err.message ? err.message : String(err)) + "\nTip: To query directly via CLI: rtk python3 _src/tools/asof_view.py " + canonicalId + " --release " + rel;
            }
            if (decisionsWrap) decisionsWrap.hidden = true;
            if (graphWrap) graphWrap.hidden = true;
          });
      }

      if (btn && select) {
        btn.addEventListener("click", function () {
          loadSnapshot(select.value);
        });
      }

      if (closeBtn && display) {
        closeBtn.addEventListener("click", function () {
          display.hidden = true;
        });
      }

      nav.querySelectorAll("[data-inspect-version]").forEach(function (inspectBtn) {
        inspectBtn.addEventListener("click", function () {
          var entry = inspectBtn.closest(".rec-version-entry");
          var rel = entry ? entry.querySelector(".rec-ver-rel").textContent.trim() : null;
          if (rel && select) {
            select.value = rel;
          }
          loadSnapshot(rel || (select ? select.value : ""));
        });
      });
    });
  }

  function initAIModelWidget() {
    if (typeof document === "undefined") return;
    var controls = document.querySelector(".shell-controls");
    if (!controls) return;
    if (controls.querySelector("[data-ai-model-widget]")) return;

    var widget = document.createElement("details");
    widget.className = "shell-dropdown ai-model-widget";
    widget.setAttribute("data-ai-model-widget", "");
    widget.innerHTML =
      '<summary class="shell-toggle ai-model-toggle" aria-haspopup="true" title="KI-Modell &amp; Backend-Status">' +
        '<span class="ai-status-dot" data-ai-dot aria-hidden="true"></span>' +
        '<span class="ai-model-icon" aria-hidden="true">🤖</span>' +
        '<span class="ai-model-label" data-ai-active-label>KI lädt...</span>' +
        '<span class="dropdown-caret" aria-hidden="true">▾</span>' +
      '</summary>' +
      '<div class="shell-dropdown-menu ai-model-menu">' +
        '<div class="ai-model-menu-title">KI-Modell &amp; Backend-Status</div>' +
        '<div class="ai-model-card active-card">' +
          '<div class="ai-model-badge-header">' +
            '<span class="ai-badge-pill" data-ai-active-pill>AKTIV</span>' +
            '<strong class="ai-model-heading" data-ai-active-name>Ermittle...</strong>' +
          '</div>' +
          '<div class="ai-model-details" data-ai-active-details>Initialisiere Provider...</div>' +
        '</div>' +
        '<div class="ai-model-card secondary-card">' +
          '<div class="ai-model-badge-header">' +
            '<span class="ai-badge-pill pill-sec">FALLBACK</span>' +
            '<strong class="ai-model-heading" data-ai-fallback-name>Cursor Composer</strong>' +
          '</div>' +
          '<div class="ai-model-details" data-ai-fallback-details>Bereit</div>' +
        '</div>' +
        '<div class="ai-model-menu-footer">' +
          '<span class="ai-last-check-text" data-ai-last-check>Status: prüfe...</span>' +
          '<button type="button" class="ai-recheck-btn" data-ai-recheck>↻ Prüfen</button>' +
        '</div>' +
      '</div>';

    var prefs = controls.querySelector(".shell-prefs");
    if (prefs) {
      controls.insertBefore(widget, prefs);
    } else {
      controls.appendChild(widget);
    }

    var dot = widget.querySelector("[data-ai-dot]");
    var activeLabel = widget.querySelector("[data-ai-active-label]");
    var activeName = widget.querySelector("[data-ai-active-name]");
    var activeDetails = widget.querySelector("[data-ai-active-details]");
    var activePill = widget.querySelector("[data-ai-active-pill]");
    var fallbackName = widget.querySelector("[data-ai-fallback-name]");
    var fallbackDetails = widget.querySelector("[data-ai-fallback-details]");
    var lastCheckText = widget.querySelector("[data-ai-last-check]");
    var recheckBtn = widget.querySelector("[data-ai-recheck]");

    function renderStatus(data) {
      if (!data || !data.ok) return;
      var active = data.active_model;
      var providers = data.providers || {};
      var agy = providers.agy || {};
      var cursor = providers.cursor || {};

      if (active) {
        var dispName = active.display_name || active.model || "Unbekannt";
        activeLabel.textContent = dispName.replace(/\s*\(High\)|\s*\(Low\)|\s*\(Medium\)/g, "");
        activeName.textContent = dispName;
        var lat = active.latency_ms ? " • " + active.latency_ms + "ms" : "";
        var cliVer = active.cli_version ? "v" + active.cli_version : (active.provider || "CLI");
        activeDetails.textContent = "CLI: " + cliVer + lat + " (" + (active.status || "bereit") + ")";

        dot.className = "ai-status-dot " + (active.status === "healthy" ? "healthy" : (active.status === "degraded" ? "degraded" : "error"));
        if (activePill) activePill.textContent = "AKTIV (" + (active.role || "Primär").toUpperCase() + ")";
      } else {
        activeLabel.textContent = "KI Offline";
        activeName.textContent = "Kein Modell erreichbar";
        activeDetails.textContent = "Prüfe CLI-Tokens und Verbindungen";
        dot.className = "ai-status-dot error";
      }

      var fallback = (data.active_provider === "agy") ? cursor : agy;
      var fbDisp = fallback.display_name || fallback.model || "Cursor Composer";
      fallbackName.textContent = fbDisp;
      var fbLat = fallback.latency_ms ? " • " + fallback.latency_ms + "ms" : "";
      var fbVer = fallback.cli_version ? "v" + fallback.cli_version : (fallback.name || "CLI");
      fallbackDetails.textContent = "CLI: " + fbVer + fbLat + " (" + (fallback.status || "bereit") + ")";

      if (lastCheckText) {
        if (data.last_updated) {
          var dt = new Date(data.last_updated);
          lastCheckText.textContent = "Check: " + dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        } else {
          lastCheckText.textContent = "Initialisiere...";
        }
      }

      if (active) {
        document.querySelectorAll(".ai-badge").forEach(function (badge) {
          badge.setAttribute("title", "Generiert mit " + (active.display_name || active.model));
        });
      }
    }

    function fetchAIStatus() {
      fetch("/api/ai/status")
        .then(function (r) { return r.json(); })
        .then(renderStatus)
        .catch(function () {
          activeLabel.textContent = "KI: Bereit";
          dot.className = "ai-status-dot healthy";
        });
    }

    if (recheckBtn) {
      recheckBtn.addEventListener("click", function () {
        recheckBtn.disabled = true;
        recheckBtn.textContent = "Prüfe...";
        fetch("/api/ai/check", { method: "POST" })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            renderStatus(data);
            setTimeout(fetchAIStatus, 1500);
          })
          .catch(function () {
            fetchAIStatus();
          })
          .finally(function () {
            setTimeout(function () {
              recheckBtn.disabled = false;
              recheckBtn.textContent = "↻ Prüfen";
            }, 2000);
          });
      });
    }

    fetchAIStatus();
    setInterval(fetchAIStatus, 60000);
  }

  var api = {
    SCHEMA: SCHEMA,
    buildFeedbackRecord: buildFeedbackRecord,
    gatherContext: gatherContext,
    detectTargetId: detectTargetId,
    openFeedbackDialog: open,
    initVersionNav: initVersionNav,
    initAIModelWidget: initAIModelWidget,
    _i18n: L
  };

  if (typeof module !== "undefined" && module.exports) {
    Object.assign(module.exports, api);
  }
  if (typeof window !== "undefined") {
    window.AraUserFeedback = api;
  }
  if (typeof document !== "undefined") {
    document.addEventListener("DOMContentLoaded", function () {
      ensureTrigger();
      bindTriggers();
      initVersionNav();
      initAIModelWidget();
    });
  }
})();
