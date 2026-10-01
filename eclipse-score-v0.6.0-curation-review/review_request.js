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

  var SCHEMA = "user-feedback-envelope@v1";
  var QUEUE_KEY = "ara-user-feedback-queue-v1";
  var MAX_QUEUE = 50;
  var CATEGORIES = [
    ["", "Kategorie wählen"],
    ["inhaltlich", "Inhaltlich"],
    ["fehlende_information", "Fehlende Information"],
    ["uebersetzungsfehler", "Übersetzungsfehler"],
    ["unklarheit", "Unklarheit"],
    ["typo", "Typo"]
  ];
  var SEVERITIES = [
    ["", "Schweregrad wählen"],
    ["blocker", "Blocker"],
    ["major", "Major"],
    ["minor", "Minor"],
    ["editorial", "Editorial"]
  ];
  var CATEGORY_KEYS = { inhaltlich: 1, fehlende_information: 1, uebersetzungsfehler: 1, unklarheit: 1, typo: 1 };
  var SEVERITY_KEYS = { blocker: 1, major: 1, minor: 1, editorial: 1 };

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function canonicalJson(value) {
    if (value === null) return "null";
    var t = typeof value;
    if (t === "number" || t === "boolean") return JSON.stringify(value);
    if (t === "string") return JSON.stringify(value);
    if (Array.isArray(value)) {
      return "[" + value.map(canonicalJson).join(",") + "]";
    }
    if (t === "object") {
      return "{" + Object.keys(value).sort().map(function (key) {
        return JSON.stringify(key) + ":" + canonicalJson(value[key]);
      }).join(",") + "}";
    }
    return JSON.stringify(String(value));
  }

  function sha256HexSync(text) {
    if (typeof require === "function") {
      try {
        return require("crypto").createHash("sha256").update(text, "utf8").digest("hex");
      } catch (_) {}
    }
    throw new Error("SHA-256 sync hash requires Node crypto");
  }

  function sha256HexAsync(text) {
    try {
      return Promise.resolve(sha256HexSync(text));
    } catch (_) {}
    if (typeof crypto !== "undefined" && crypto.subtle && typeof TextEncoder !== "undefined") {
      return crypto.subtle.digest("SHA-256", new TextEncoder().encode(text)).then(function (buf) {
        return Array.from(new Uint8Array(buf)).map(function (b) {
          return b.toString(16).padStart(2, "0");
        }).join("");
      });
    }
    return Promise.reject(new Error("SHA-256 unavailable (use http://localhost or https)"));
  }

  function newFeedbackId() {
    var id;
    if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
      id = crypto.randomUUID();
    } else if (typeof require === "function") {
      id = require("crypto").randomUUID();
    } else {
      id = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0;
        return (c === "x" ? r : (r & 0x3 | 0x8)).toString(16);
      });
    }
    return "uf-" + id;
  }

  function nowIso() {
    return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
  }

  function cleanText(value, field, maxLen, required) {
    var text = value == null ? "" : String(value);
    text = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();
    if (/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/.test(text)) {
      throw new Error(field + ": control characters are not allowed");
    }
    if (required && !text) throw new Error(field + ": required");
    if (text.length > maxLen) throw new Error(field + ": exceeds " + maxLen + " characters");
    return text;
  }

  function validateFeedbackForm(payload) {
    var target = cleanText(payload && payload.target_id, "target_id", 256, true);
    var title = cleanText(payload && payload.title, "title", 200, true);
    if (title.length < 3) throw new Error("title: at least 3 characters");
    var description = cleanText(payload && payload.description, "description", 20000, true);
    if (description.length < 10) throw new Error("description: at least 10 characters");
    var proposed = cleanText(payload && payload.proposed_change, "proposed_change", 20000, false);
    var submitter = cleanText(payload && payload.submitter, "submitter", 120, false);
    var category = cleanText(payload && payload.category, "category", 64, true);
    var severity = cleanText(payload && payload.severity, "severity", 32, true).toLowerCase();
    category = category.toLowerCase().replace(/ /g, "_").replace(/-/g, "_");
    if (!CATEGORY_KEYS[category]) throw new Error("category: invalid");
    if (!SEVERITY_KEYS[severity]) throw new Error("severity: invalid");
    return {
      target_id: target,
      category: category,
      severity: severity,
      title: title,
      description: description,
      proposed_change: proposed,
      submitter: submitter
    };
  }

  function envelopeBody(fields, meta) {
    return {
      schema: SCHEMA,
      feedback_id: meta.feedback_id,
      submitted_at: meta.submitted_at,
      target_id: fields.target_id,
      category: fields.category,
      severity: fields.severity,
      title: fields.title,
      description: fields.description,
      proposed_change: fields.proposed_change,
      submitter: fields.submitter,
      status: meta.status || "queued"
    };
  }

  function attachReceiptSync(body) {
    var hash = sha256HexSync(canonicalJson(body));
    var out = {};
    Object.keys(body).forEach(function (k) { out[k] = body[k]; });
    out.receipt_hash = hash;
    return out;
  }

  function buildFeedbackEnvelope(payload, opts) {
    opts = opts || {};
    var fields = validateFeedbackForm(payload);
    var body = envelopeBody(fields, {
      feedback_id: opts.feedback_id || newFeedbackId(),
      submitted_at: opts.submitted_at || nowIso(),
      status: opts.status || "queued"
    });
    return attachReceiptSync(body);
  }

  function buildFeedbackEnvelopeAsync(payload, opts) {
    opts = opts || {};
    try {
      return Promise.resolve(buildFeedbackEnvelope(payload, opts));
    } catch (syncErr) {
      if (String(syncErr.message || syncErr).indexOf("SHA-256 sync") === -1) {
        return Promise.reject(syncErr);
      }
    }
    var fields;
    try {
      fields = validateFeedbackForm(payload);
    } catch (err) {
      return Promise.reject(err);
    }
    var body = envelopeBody(fields, {
      feedback_id: opts.feedback_id || newFeedbackId(),
      submitted_at: opts.submitted_at || nowIso(),
      status: opts.status || "queued"
    });
    return sha256HexAsync(canonicalJson(body)).then(function (hash) {
      var out = {};
      Object.keys(body).forEach(function (k) { out[k] = body[k]; });
      out.receipt_hash = hash;
      return out;
    });
  }

  function readLocalQueue() {
    try {
      if (typeof localStorage === "undefined") return [];
      var raw = localStorage.getItem(QUEUE_KEY);
      if (!raw) return [];
      var parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (_) {
      return [];
    }
  }

  function writeLocalQueue(items) {
    if (typeof localStorage === "undefined") return;
    localStorage.setItem(QUEUE_KEY, JSON.stringify(items.slice(-MAX_QUEUE)));
  }

  function enqueueLocal(envelope) {
    var items = readLocalQueue();
    items.push(envelope);
    writeLocalQueue(items);
    return envelope;
  }

  function ingestUrl() {
    if (typeof document === "undefined") return "/api/user-feedback";
    var meta = document.querySelector('meta[name="feedback-ingest-url"]');
    var fromMeta = meta && meta.getAttribute("content");
    if (fromMeta) return fromMeta;
    if (typeof window !== "undefined" && window.ARA_FEEDBACK_INGEST_URL) {
      return window.ARA_FEEDBACK_INGEST_URL;
    }
    return "/api/user-feedback";
  }

  function postEnvelope(envelope) {
    if (typeof fetch !== "function") return Promise.reject(new Error("fetch unavailable"));
    return fetch(ingestUrl(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(envelope)
    }).then(function (res) {
      return res.json().then(function (data) {
        if (!res.ok || !data || !data.ok) {
          throw new Error((data && data.error) || ("HTTP " + res.status));
        }
        return data;
      }, function () {
        throw new Error("HTTP " + res.status);
      });
    });
  }

  function detectTargetId() {
    if (typeof document === "undefined") return "";
    var dataEl = document.querySelector(".review-request-data");
    if (dataEl) {
      try {
        var data = JSON.parse(dataEl.textContent);
        if (data && data.canonical_id) return String(data.canonical_id);
      } catch (_) {}
    }
    var attr = document.querySelector("[data-canonical-id]");
    if (attr && attr.getAttribute("data-canonical-id")) return attr.getAttribute("data-canonical-id");
    var rec = document.querySelector("article.rec[id], section.rec[id]");
    if (rec && rec.id) return rec.id;
    var h1 = document.querySelector("h1");
    if (h1 && h1.textContent) return h1.textContent.replace(/\s+/g, " ").trim().slice(0, 256);
    return typeof location !== "undefined" ? location.pathname : "";
  }

  function optionHtml(pairs) {
    return pairs.map(function (pair) {
      return '<option value="' + esc(pair[0]) + '">' + esc(pair[1]) + "</option>";
    }).join("");
  }

  function statusLabel(status) {
    if (status === "submitted") return "Eingereicht";
    return "In Warteschlange";
  }

  function showReceipt(envelope, opener) {
    var modal = document.createElement("div");
    modal.className = "rv-modal is-open";
    modal.innerHTML =
      '<div class="rv-modal-scrim" data-receipt-close></div>' +
      '<div class="rv-modal-card" role="dialog" aria-modal="true" aria-labelledby="fb-receipt-title">' +
      '<header class="rv-modal-head"><h2 id="fb-receipt-title">Eingereicht / In Warteschlange</h2>' +
      '<button type="button" class="rv-icon-btn" data-receipt-close aria-label="Schließen">×</button></header>' +
      '<div class="rv-modal-body feedback-receipt">' +
      '<p class="rv-modal-lead" aria-live="polite">Status: <strong data-receipt-status></strong></p>' +
      "<dl class=\"rv-facts\">" +
      "<dt>Feedback-ID</dt><dd><code data-receipt-id></code></dd>" +
      "<dt>Receipt-Hash</dt><dd><code data-receipt-hash></code></dd>" +
      "</dl>" +
      '<p class="rv-modal-note">Bewahren Sie ID und Hash auf, um diese Meldung später zuzuordnen. Es wird kein Browser-Token verwendet.</p>' +
      "</div>" +
      '<footer class="rv-modal-foot"><span class="rv-spacer"></span>' +
      '<button type="button" class="rv-btn rv-btn-primary" data-receipt-close>Schließen</button></footer></div>';
    document.body.appendChild(modal);
    modal.querySelector("[data-receipt-status]").textContent = statusLabel(envelope.status);
    modal.querySelector("[data-receipt-id]").textContent = envelope.feedback_id;
    modal.querySelector("[data-receipt-hash]").textContent = envelope.receipt_hash;
    function close() {
      modal.remove();
      if (opener && opener.focus) opener.focus();
    }
    modal.querySelectorAll("[data-receipt-close]").forEach(function (el) {
      el.addEventListener("click", close);
    });
    modal.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { e.preventDefault(); close(); }
    });
    modal.querySelector("[data-receipt-close].rv-btn").focus();
  }

  function ensureTrigger() {
    if (typeof document === "undefined") return null;
    var existing = document.querySelector("[data-feedback-open]");
    if (existing) return existing;
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "feedback-open is-floating";
    btn.setAttribute("data-feedback-open", "");
    btn.setAttribute("aria-haspopup", "dialog");
    btn.setAttribute("aria-expanded", "false");
    btn.setAttribute("aria-controls", "feedback-dialog");
    btn.textContent = "Feedback / Mangel melden";
    document.body.appendChild(btn);
    return btn;
  }

  function openFeedbackDialog(opener) {
    var dlg = document.createElement("div");
    dlg.className = "rv-modal is-open";
    dlg.innerHTML =
      '<div class="rv-modal-scrim" data-fb-close></div>' +
      '<div class="rv-modal-card" id="feedback-dialog" role="dialog" aria-modal="true" aria-labelledby="fb-title">' +
      '<header class="rv-modal-head"><h2 id="fb-title">Feedback / Mangel melden</h2>' +
      '<button type="button" class="rv-icon-btn" data-fb-close aria-label="Abbrechen">×</button></header>' +
      '<div class="rv-modal-body"><p class="rv-modal-lead">Die Meldung ändert die Dokumentation nicht sofort. Es wird kein GitHub-Token aus dem Browser verwendet.</p>' +
      '<form class="feedback-form" novalidate>' +
      '<label class="rv-field"><span>Ziel-Spezifikation / Komponenten-ID</span>' +
      '<input type="text" name="target_id" maxlength="256" required data-fb-target></label>' +
      '<label class="rv-field"><span>Kategorie</span>' +
      '<select name="category" required data-fb-category>' + optionHtml(CATEGORIES) + "</select></label>" +
      '<label class="rv-field"><span>Titel / Kurzfassung</span>' +
      '<input type="text" name="title" maxlength="200" required data-fb-title></label>' +
      '<label class="rv-field"><span>Ausführliche Beschreibung</span>' +
      '<textarea name="description" maxlength="20000" required data-fb-description></textarea></label>' +
      '<label class="rv-field"><span>Änderungsvorschlag (optional, Text oder Diff)</span>' +
      '<textarea name="proposed_change" maxlength="20000" data-fb-proposed></textarea></label>' +
      '<label class="rv-field"><span>Schweregrad</span>' +
      '<select name="severity" required data-fb-severity>' + optionHtml(SEVERITIES) + "</select></label>" +
      '<label class="rv-field"><span>Handle / E-Mail (optional, auch pseudonym)</span>' +
      '<input type="text" name="submitter" maxlength="120" autocomplete="nickname" data-fb-submitter></label>' +
      '<p class="feedback-errors" data-fb-errors hidden></p>' +
      "</form></div>" +
      '<footer class="rv-modal-foot"><button type="button" class="rv-btn rv-btn-quiet" data-fb-close>Abbrechen</button>' +
      '<span class="rv-spacer"></span>' +
      '<button type="button" class="rv-btn rv-btn-primary" data-fb-submit>Absenden</button></footer></div>';
    document.body.appendChild(dlg);
    if (opener) opener.setAttribute("aria-expanded", "true");
    var target = dlg.querySelector("[data-fb-target]");
    target.value = detectTargetId();
    target.focus();
    target.select();

    function close() {
      dlg.remove();
      if (opener) {
        opener.setAttribute("aria-expanded", "false");
        opener.focus();
      }
    }

    function showError(message) {
      var box = dlg.querySelector("[data-fb-errors]");
      box.hidden = !message;
      box.textContent = message || "";
      if (message) box.focus();
    }

    dlg.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { e.preventDefault(); close(); }
      if (e.key !== "Tab") return;
      var nodes = dlg.querySelectorAll("button, [href], input, select, textarea");
      var list = Array.prototype.filter.call(nodes, function (n) { return !n.disabled && n.offsetParent !== null; });
      if (!list.length) return;
      var first = list[0];
      var last = list[list.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
    dlg.querySelectorAll("[data-fb-close]").forEach(function (el) {
      el.addEventListener("click", close);
    });
    dlg.querySelector("[data-fb-submit]").addEventListener("click", function () {
      var submitBtn = dlg.querySelector("[data-fb-submit]");
      submitBtn.disabled = true;
      var payload = {
        target_id: dlg.querySelector("[data-fb-target]").value,
        category: dlg.querySelector("[data-fb-category]").value,
        title: dlg.querySelector("[data-fb-title]").value,
        description: dlg.querySelector("[data-fb-description]").value,
        proposed_change: dlg.querySelector("[data-fb-proposed]").value,
        severity: dlg.querySelector("[data-fb-severity]").value,
        submitter: dlg.querySelector("[data-fb-submitter]").value
      };
      buildFeedbackEnvelopeAsync(payload).then(function (envelope) {
        var fields = validateFeedbackForm(payload);
        return postEnvelope(fields).then(function (res) {
          return {
            schema: SCHEMA,
            feedback_id: res.feedback_id,
            receipt_hash: res.receipt_hash,
            status: res.status || "submitted"
          };
        }).catch(function () {
          enqueueLocal(envelope);
          return envelope;
        });
      }).then(function (receipt) {
        close();
        showReceipt(receipt, opener);
      }).catch(function (err) {
        showError(err && err.message ? err.message : String(err));
        submitBtn.disabled = false;
      });
    });
  }

  function bindTriggers() {
    document.querySelectorAll("[data-feedback-open]").forEach(function (btn) {
      if (btn.getAttribute("data-feedback-bound")) return;
      btn.setAttribute("data-feedback-bound", "1");
      btn.addEventListener("click", function () { openFeedbackDialog(btn); });
    });
  }

  var api = {
    SCHEMA: SCHEMA,
    canonicalJson: canonicalJson,
    validateFeedbackForm: validateFeedbackForm,
    buildFeedbackEnvelope: buildFeedbackEnvelope,
    buildFeedbackEnvelopeAsync: buildFeedbackEnvelopeAsync,
    enqueueLocal: enqueueLocal,
    readLocalQueue: readLocalQueue,
    detectTargetId: detectTargetId
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
    });
  }
})();
