(function () {
  "use strict";

  var TOKEN = "ara-review-github-token-v1";
  var IDENT = "ara-review-identity";
  var REPO = document.querySelector('meta[name="review-github-repo"]')?.getAttribute('content') || '2b-rs/autodocs';
  var CATEGORIES = [
    ["", "Choose category"],
    ["factual-accuracy", "Factual accuracy"],
    ["outdated-source", "Outdated source"],
    ["missing-context", "Missing context"],
    ["ai-hallucination-suspected", "AI hallucination suspected"],
    ["other", "Other"]
  ];

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
  function cleanName(v) { return String(v == null ? "" : v).replace(/\s+/g, " ").trim().slice(0, 80); }
  function validName(v) { return cleanName(v).length >= 2; }
  function selfName() { try { return cleanName(localStorage.getItem(IDENT) || ""); } catch (_) { return ""; } }
  function setSelfName(v) { try { localStorage.setItem(IDENT, cleanName(v)); } catch (_) {} }
  function activeToken() { try { return String(localStorage.getItem(TOKEN) || "").trim(); } catch (_) { return ""; } }
  async function verify(token) {
    var r = await fetch("https://api.github.com/user", { headers: { Accept: "application/vnd.github+json", Authorization: "Bearer " + token, "X-GitHub-Api-Version": "2022-11-28" } });
    if (!r.ok) throw new Error("GitHub: " + r.status);
    return await r.json();
  }
  function uuid7Like() {
    var a = new Uint8Array(16);
    (self.crypto || window.crypto).getRandomValues(a);
    a[6] = (a[6] & 0x0f) | 0x70;
    a[8] = (a[8] & 0x3f) | 0x80;
    var hex = Array.from(a, function (b) { return b.toString(16).padStart(2, "0"); }).join("");
    return hex.slice(0, 8) + "-" + hex.slice(8, 12) + "-" + hex.slice(12, 16) + "-" + hex.slice(16, 20) + "-" + hex.slice(20);
  }
  function requestId() { return "review-request:" + uuid7Like(); }
  function knownIdentity() {
    var s = selfName();
    if (activeToken()) return { name: null, mode: "github_authenticated" };
    if (validName(s)) return { name: s, mode: "self_declared" };
    return null;
  }
  function setState(root, message, kind) {
    var el = root.querySelector("[data-review-request-state]");
    if (!el) return;
    el.hidden = !message;
    el.className = "review-request-state" + (kind ? " is-" + kind : "");
    el.textContent = message || "";
  }
  function openIdentityModal() {
    return new Promise(function (resolve, reject) {
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
    dlg.innerHTML = '<div class="rv-modal-scrim" data-close></div><div class="rv-modal-card review-request-dialog" role="dialog" aria-modal="true" aria-labelledby="rr-title"><header class="rv-modal-head"><h2 id="rr-title">' + esc(data.has_open_review_request ? 'Review request already open' : 'Flag for review') + '</h2><button type="button" class="rv-icon-btn" data-close aria-label="Cancel">×</button></header><div class="rv-modal-body"><div class="review-request-context" tabindex="-1"><p><strong>This creates a review request only.</strong> The record is not changed immediately.</p><dl><dt>Record</dt><dd><code>' + esc(data.canonical_id) + '</code></dd><dt>Status</dt><dd>' + esc(data.status) + '</dd>' + (data.version_id ? '<dt>Version</dt><dd><code>' + esc(data.version_id) + '</code></dd>' : '') + (data.content_hash ? '<dt>Content hash</dt><dd><code>' + esc(data.content_hash) + '</code></dd>' : '') + (data.source_url ? '<dt>Source</dt><dd><a href="' + esc(data.source_url) + '">' + esc(data.source_url) + '</a></dd>' : '') + '</dl><p class="review-request-trust">If you continue without GitHub authentication, your identity will be recorded as self-declared and may carry lower trust.</p></div><form class="review-request-form"><label class="review-request-field"><span>Category</span><select data-category required>' + CATEGORIES.map(function (c) { return '<option value="' + esc(c[0]) + '"' + (c[0] === (data.category_default || '') ? ' selected' : '') + '>' + esc(c[1]) + '</option>'; }).join('') + '</select></label><label class="review-request-field review-request-field-wide"><span>Rationale</span><textarea data-rationale required></textarea></label><fieldset class="review-request-evidence"><legend>Evidence references (optional)</legend><div data-evidence-list></div><button type="button" class="rv-btn rv-btn-quiet" data-evidence-add>Add another reference</button></fieldset><div class="review-request-errors" data-errors hidden></div></form><section class="review-request-confirm" data-confirm hidden><h3 tabindex="-1">Confirm request</h3><div data-confirm-body></div></section></div><footer class="rv-modal-foot"><button type="button" class="rv-btn rv-btn-quiet" data-close>Cancel</button><button type="button" class="rv-btn rv-btn-quiet" data-edit hidden>Edit</button><button type="button" class="rv-btn rv-btn-primary" data-next>Review request</button><button type="button" class="rv-btn rv-btn-primary" data-submit hidden>Submit</button><button type="button" class="rv-btn rv-btn-quiet" data-export hidden>Export JSON</button></footer></div>';
    document.body.appendChild(dlg);
    return dlg;
  }
  function serializeEvidence(dialog) {
    return Array.from(dialog.querySelectorAll('.review-request-evidence-row')).map(function (row) {
      var kind = row.querySelector('[data-evidence-kind]').value.trim();
      var value = row.querySelector('[data-evidence-value]').value.trim();
      var note = row.querySelector('[data-evidence-note]').value.trim();
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
  async function buildPackage(root, data, transport) {
    var who = await resolveIdentity();
    return {
      schema: 'review-request-package@v1',
      client_schema_version: 1,
      request_id: requestId(),
      target_canonical_id: data.canonical_id,
      target_version_id: data.version_id,
      target_content_hash: data.content_hash,
      target_status_snapshot: data.status,
      source_url: data.source_url || window.location.href,
      category: root._rrDialog.querySelector('[data-category]').value,
      rationale: root._rrDialog.querySelector('[data-rationale]').value.trim(),
      actor_claim: { display_name: who.name, identity_kind: who.mode },
      evidence_refs: serializeEvidence(root._rrDialog),
      created_at: new Date().toISOString(),
      transport: transport
    };
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
    if (!root._rrDialog) return;
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
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-review-request-root]').forEach(init);
  });
})();
