(function () {
  "use strict";

  var TOKEN = "ara-review-github-token-v1";
  var IDENT = "ara-review-identity";
  var STORE = "ara-review-package-v1";
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
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function cleanName(v) { return String(v == null ? "" : v).replace(/\s+/g, " ").trim().slice(0, 80); }
  function validName(v) { return cleanName(v).length >= 2; }
  function selfName() { try { return cleanName(localStorage.getItem(IDENT) || ""); } catch (_) { return ""; } }
  function setSelfName(v) { try { localStorage.setItem(IDENT, cleanName(v)); } catch (_) {} }
  function activeToken() { try { return String(localStorage.getItem(TOKEN) || "").trim(); } catch (_) { return ""; } }

  async function verify(token) {
    var r = await fetch("https://api.github.com/user", {
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: "Bearer " + token,
        "X-GitHub-Api-Version": "2022-11-28"
      }
    });
    if (!r.ok) throw new Error("GitHub: " + r.status);
    return await r.json();
  }

  /**
   * Standards-correct UUIDv7 generation (RFC 9562).
   * High 48 bits = timestamp (ms), version 7 in bits 48-51, variant 10 in bits 64-65.
   */
  function generateUUIDv7(customTimeMs) {
    var now = typeof customTimeMs === "number" ? customTimeMs : Date.now();
    var bytes = new Uint8Array(16);
    var cryptoObj = (typeof self !== "undefined" && (self.crypto || window.crypto)) || (typeof crypto !== "undefined" ? crypto : null);
    if (cryptoObj && cryptoObj.getRandomValues) {
      cryptoObj.getRandomValues(bytes);
    } else {
      for (var i = 0; i < 16; i++) {
        bytes[i] = Math.floor(Math.random() * 256);
      }
    }
    // 48-bit timestamp in milliseconds
    bytes[0] = Math.floor(now / 0x10000000000) & 0xff;
    bytes[1] = Math.floor(now / 0x100000000) & 0xff;
    bytes[2] = Math.floor(now / 0x1000000) & 0xff;
    bytes[3] = Math.floor(now / 0x10000) & 0xff;
    bytes[4] = Math.floor(now / 0x100) & 0xff;
    bytes[5] = now & 0xff;
    // Version 7 in 4 high bits of byte 6 (0x70..0x7f)
    bytes[6] = (bytes[6] & 0x0f) | 0x70;
    // Variant 10xx in 2 high bits of byte 8 (0x80..0xbf)
    bytes[8] = (bytes[8] & 0x3f) | 0x80;

    var hex = Array.from(bytes, function (b) { return b.toString(16).padStart(2, "0"); }).join("");
    return hex.slice(0, 8) + "-" + hex.slice(8, 12) + "-" + hex.slice(12, 16) + "-" + hex.slice(16, 20) + "-" + hex.slice(20);
  }

  function requestId(customTimeMs) {
    return "review-request:" + generateUUIDv7(customTimeMs);
  }

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
      modal.innerHTML =
        '<div class="rv-modal-scrim"></div>' +
        '<div class="rv-modal-card" role="dialog" aria-modal="true" aria-labelledby="rr-id-title">' +
          '<header class="rv-modal-head">' +
            '<h2 id="rr-id-title">Who is requesting review?</h2>' +
            '<button type="button" class="rv-icon-btn" data-cancel aria-label="Cancel">×</button>' +
          '</header>' +
          '<div class="rv-modal-body">' +
            '<p class="rv-modal-lead">Your identity is attached to the request. Self-declared requests may carry lower trust than GitHub-authenticated requests.</p>' +
            '<label class="rv-field"><span>Name or handle</span><input type="text" data-input maxlength="80" required></label>' +
            '<p class="rv-modal-note">At least 2 characters. Stored locally in this browser only.</p>' +
          '</div>' +
          '<footer class="rv-modal-foot">' +
            '<span class="rv-spacer"></span>' +
            '<button type="button" class="rv-btn rv-btn-quiet" data-cancel>Cancel</button>' +
            '<button type="button" class="rv-btn rv-btn-primary" data-ok disabled>Use this name</button>' +
          '</footer>' +
        '</div>';
      document.body.appendChild(modal);
      var input = modal.querySelector("[data-input]");
      var ok = modal.querySelector("[data-ok]");
      input.value = selfName();
      ok.disabled = !validName(input.value);

      function close() { modal.remove(); }
      function onInput() { ok.disabled = !validName(input.value); }
      function onOk() {
        if (!validName(input.value)) return;
        var name = cleanName(input.value);
        setSelfName(name);
        close();
        resolve({ name: name, mode: "self_declared" });
      }
      function onCancel() { close(); reject(new Error("cancelled")); }

      input.addEventListener("input", onInput);
      input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") { e.preventDefault(); onOk(); }
        if (e.key === "Escape") onCancel();
      });
      ok.addEventListener("click", onOk);
      modal.querySelectorAll("[data-cancel]").forEach(function (el) { el.addEventListener("click", onCancel); });
      input.focus();
      input.select();
    });
  }

  async function resolveIdentity() {
    var known = knownIdentity();
    if (known && known.mode === "self_declared") return known;
    if (activeToken()) {
      try {
        var user = await verify(activeToken());
        return { name: user.login, mode: "github_authenticated" };
      } catch (_) {}
    }
    return await openIdentityModal();
  }

  function buildEvidenceSection() {
    return '<fieldset class="review-request-evidence">' +
      '<legend>Evidence (optional)</legend>' +
      '<label class="review-request-field review-request-field-wide">' +
        '<span>Supporting Link (optional)</span>' +
        '<input type="url" data-evidence-url placeholder="https://example.org/spec/errata.pdf#page=12">' +
      '</label>' +
      '<label class="review-request-field review-request-field-wide">' +
        '<span>Quote or Note (optional)</span>' +
        '<input type="text" data-evidence-text placeholder="Quoted requirement sentence or errata reference">' +
      '</label>' +
      '<p class="review-request-note">Optional URL and/or quoted excerpt from authoritative specification errata.</p>' +
      '</fieldset>';
  }

  function buildDialog(root, data) {
    var dlg = document.createElement("div");
    dlg.className = "rv-modal";
    dlg.hidden = true;
    dlg.innerHTML =
      '<div class="rv-modal-scrim" data-close></div>' +
      '<div class="rv-modal-card review-request-dialog" role="dialog" aria-modal="true" aria-labelledby="rr-title">' +
        '<header class="rv-modal-head">' +
          '<h2 id="rr-title">' + esc(data.has_open_review_request ? "Review request already open" : "Flag for review") + '</h2>' +
          '<button type="button" class="rv-icon-btn" data-close aria-label="Cancel">×</button>' +
        '</header>' +
        '<div class="rv-modal-body">' +
          '<div class="review-request-context" tabindex="-1">' +
            '<p><strong>This creates a review request only.</strong> The record is not changed immediately. <a href="' + esc(processDocHref("flag-for-review-protocol")) + '" class="rv-process-doc-link" target="_blank" rel="noopener">How review requests work ↗</a></p>' +
            '<dl>' +
              '<dt>Record</dt><dd><code>' + esc(data.canonical_id) + '</code></dd>' +
              '<dt>Status</dt><dd>' + esc(data.status) + '</dd>' +
              (data.version_id ? '<dt>Version</dt><dd><code>' + esc(data.version_id) + '</code></dd>' : '') +
              (data.content_hash ? '<dt>Content hash</dt><dd><code>' + esc(data.content_hash) + '</code></dd>' : '') +
              (data.source_url ? '<dt>Source</dt><dd><a href="' + esc(data.source_url) + '" target="_blank">' + esc(data.source_url) + '</a></dd>' : '') +
            '</dl>' +
            '<p class="review-request-trust">If you continue without GitHub authentication, your identity will be recorded as self-declared and may carry lower trust. <a href="' + esc(processDocHref("storage-and-privacy")) + '" class="rv-process-doc-link" target="_blank" rel="noopener">Learn about storage and privacy ↗</a></p>' +
          '</div>' +
          '<form class="review-request-form">' +
            '<label class="review-request-field">' +
              '<span>Category</span>' +
              '<select data-category required>' +
                CATEGORIES.map(function (c) {
                  return '<option value="' + esc(c[0]) + '"' + (c[0] === (data.category_default || '') ? ' selected' : '') + '>' + esc(c[1]) + '</option>';
                }).join('') +
              '</select>' +
            '</label>' +
            '<label class="review-request-field review-request-field-wide">' +
              '<span>Rationale</span>' +
              '<textarea data-rationale required placeholder="Describe why this record needs review (e.g. outdated reference, missing context, or factual conflict)."></textarea>' +
            '</label>' +
            buildEvidenceSection() +
            '<div class="review-request-errors" data-errors role="alert" hidden></div>' +
          '</form>' +
          '<section class="review-request-confirm" data-confirm hidden>' +
            '<h3 tabindex="-1">Confirm review request</h3>' +
            '<div data-confirm-body></div>' +
          '</section>' +
        '</div>' +
        '<footer class="rv-modal-foot">' +
          '<button type="button" class="rv-btn rv-btn-quiet" data-close>Cancel</button>' +
          '<button type="button" class="rv-btn rv-btn-quiet" data-edit hidden>Edit</button>' +
          '<button type="button" class="rv-btn rv-btn-primary" data-next>Review request</button>' +
          '<button type="button" class="rv-btn rv-btn-quiet" data-save-local hidden>Save to local package</button>' +
          '<button type="button" class="rv-btn rv-btn-quiet" data-export hidden>Export JSON</button>' +
          '<button type="button" class="rv-btn rv-btn-primary" data-submit hidden>Submit to GitHub</button>' +
        '</footer>' +
      '</div>';
    document.body.appendChild(dlg);
    return dlg;
  }

  function serializeEvidence(dialog) {
    var list = [];
    var urlInput = dialog ? dialog.querySelector("[data-evidence-url]") : null;
    var textInput = dialog ? dialog.querySelector("[data-evidence-text]") : null;
    var urlVal = urlInput ? urlInput.value.trim() : "";
    var textVal = textInput ? textInput.value.trim() : "";
    if (urlVal) {
      list.push({ kind: "url", value: urlVal });
    }
    if (textVal) {
      list.push({ kind: "quote", value: textVal });
    }
    return list;
  }

  function validate(dialog) {
    var errors = [];
    var cat = dialog.querySelector("[data-category]").value;
    var rat = dialog.querySelector("[data-rationale]").value.trim();
    if (!cat) errors.push("Category is required.");
    if (!rat) errors.push("Rationale is required.");

    var urlInput = dialog.querySelector("[data-evidence-url]");
    if (urlInput) {
      var urlVal = urlInput.value.trim();
      if (urlVal) {
        if (!/^https?:\/\/[^\s]+$/i.test(urlVal)) {
          errors.push("Evidence URL must be a valid http:// or https:// link.");
        }
        if (/^(javascript|data):/i.test(urlVal)) {
          errors.push("Evidence URL cannot use javascript: or data: scheme.");
        }
      }
    }

    var errBox = dialog.querySelector("[data-errors]");
    errBox.hidden = !errors.length;
    errBox.textContent = errors.join(" ");
    if (errors.length) {
      if (!cat) dialog.querySelector("[data-category]").focus();
      else if (!rat) dialog.querySelector("[data-rationale]").focus();
      else if (urlInput && urlInput.value.trim()) urlInput.focus();
      return false;
    }
    return true;
  }

  function buildConfirmedPackage(root, data, who) {
    var dialog = root._rrDialog;
    var category = dialog ? dialog.querySelector("[data-category]").value : (data.category || "factual-accuracy");
    var rationale = dialog ? dialog.querySelector("[data-rationale]").value.trim() : (data.rationale || "");
    var evidence = dialog ? serializeEvidence(dialog) : (data.evidence_refs || []);
    var nowIso = new Date().toISOString();

    return {
      schema: "review-request-package@v1",
      client_schema_version: "1.0.0",
      request_id: requestId(),
      target_canonical_id: data.canonical_id,
      target_version_id: data.version_id || null,
      target_content_hash: data.content_hash || null,
      target_status_snapshot: data.status || "unspecified",
      source_url: data.source_url || (typeof window !== "undefined" ? window.location.href : ""),
      category: category,
      rationale: rationale,
      evidence_refs: evidence,
      actor_claim: {
        display_name: (who && who.name) || "anonymous-reader",
        identity_kind: (who && who.mode) || "self_declared"
      },
      created_at: nowIso,
      transport: (who && who.mode === "github_authenticated") ? "github_issue" : "json_export"
    };
  }

  function closeDialog(root) {
    if (!root._rrDialog) return;
    var btn = root.querySelector("[data-review-request-open]");
    root._rrDialog.classList.remove("is-open");
    root._rrDialog.hidden = true;
    if (btn) {
      btn.setAttribute("aria-expanded", "false");
      btn.focus();
    }
  }

  function openDialog(root, data) {
    if (!root._rrDialog) root._rrDialog = buildDialog(root, data);
    var dlg = root._rrDialog;
    dlg.hidden = false;
    requestAnimationFrame(function () { dlg.classList.add("is-open"); });
    dlg.querySelector("[data-category]").focus();
    var btn = root.querySelector("[data-review-request-open]");
    if (btn) btn.setAttribute("aria-expanded", "true");

    dlg.addEventListener("click", function (e) {
      if (e.target.closest("[data-close]")) closeDialog(root);
    });
    dlg.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeDialog(root);
    });

    dlg.querySelector("[data-next]").onclick = async function () {
      if (!validate(dlg)) return;
      var who = await resolveIdentity();
      var pkg = buildConfirmedPackage(root, data, who);
      dlg._confirmedPackage = pkg;

      dlg.querySelector("[data-confirm-body]").innerHTML =
        '<dl class="review-request-bound">' +
          '<dt>Record</dt><dd><code>' + esc(pkg.target_canonical_id) + '</code></dd>' +
          '<dt>Status</dt><dd>' + esc(pkg.target_status_snapshot) + '</dd>' +
          (pkg.target_version_id ? '<dt>Version</dt><dd><code>' + esc(pkg.target_version_id) + '</code></dd>' : '') +
          (pkg.target_content_hash ? '<dt>Content hash</dt><dd><code>' + esc(pkg.target_content_hash) + '</code></dd>' : '') +
          (pkg.source_url ? '<dt>Source</dt><dd><a href="' + esc(pkg.source_url) + '" target="_blank">' + esc(pkg.source_url) + '</a></dd>' : '') +
          '<dt>Category</dt><dd>' + esc(pkg.category) + '</dd>' +
          '<dt>Rationale</dt><dd>' + esc(pkg.rationale) + '</dd>' +
          '<dt>Identity</dt><dd>' + esc(pkg.actor_claim.display_name + " (" + pkg.actor_claim.identity_kind + ")") + '</dd>' +
          '<dt>Request ID</dt><dd><code>' + esc(pkg.request_id) + '</code></dd>' +
        '</dl>';

      dlg.querySelector("[data-confirm]").hidden = false;
      dlg.querySelector(".review-request-form").hidden = true;
      dlg.querySelector("[data-next]").hidden = true;
      dlg.querySelector("[data-edit]").hidden = false;
      dlg.querySelector("[data-submit]").hidden = !activeToken();
      dlg.querySelector("[data-export]").hidden = false;
      dlg.querySelector("[data-save-local]").hidden = false;
      dlg.querySelector("[data-confirm] h3").focus();
    };

    dlg.querySelector("[data-edit]").onclick = function () {
      dlg._confirmedPackage = null;
      dlg.querySelector("[data-confirm]").hidden = true;
      dlg.querySelector(".review-request-form").hidden = false;
      dlg.querySelector("[data-next]").hidden = false;
      dlg.querySelector("[data-edit]").hidden = true;
      dlg.querySelector("[data-submit]").hidden = true;
      dlg.querySelector("[data-export]").hidden = true;
      dlg.querySelector("[data-save-local]").hidden = true;
      dlg.querySelector("[data-category]").focus();
    };

    dlg.querySelector("[data-export]").onclick = function () {
      if (!dlg._confirmedPackage) return;
      // Exact confirmed package reuse with safe JSON export downgrade
      var exportPkg = Object.assign({}, dlg._confirmedPackage, {
        transport: "json_export",
        actor_claim: {
          display_name: dlg._confirmedPackage.actor_claim.display_name,
          identity_kind: "self_declared"
        }
      });
      var blob = new Blob([JSON.stringify(exportPkg, null, 2) + "\n"], { type: "application/json" });
      var a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "review-request-" + exportPkg.created_at.replace(/[:.]/g, "-") + ".json";
      a.click();
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
      setState(root, "Downloaded — not yet submitted.", "exported");
      closeDialog(root);
    };

    dlg.querySelector("[data-save-local]").onclick = function () {
      if (!dlg._confirmedPackage) return;
      var storeKey = "ara-review-package-v1";
      var items = [];
      try {
        items = JSON.parse(localStorage.getItem(storeKey) || "[]");
      } catch (_) {
        items = [];
      }
      var entry = {
        item_kind: "review-request",
        id: dlg._confirmedPackage.request_id,
        canonical_id: dlg._confirmedPackage.target_canonical_id,
        target_version_id: dlg._confirmedPackage.target_version_id,
        category: dlg._confirmedPackage.category,
        rationale: dlg._confirmedPackage.rationale,
        evidence_refs: dlg._confirmedPackage.evidence_refs,
        actor_claim: dlg._confirmedPackage.actor_claim,
        created_at: dlg._confirmedPackage.created_at,
        package: dlg._confirmedPackage,
        status: "local-only"
      };
      items = items.filter(function (x) { return x.id !== entry.id; });
      items.push(entry);
      try {
        localStorage.setItem(storeKey, JSON.stringify(items));
      } catch (_) {}
      setState(root, "Saved to local review package (local-only, not yet submitted).", "saved");
      closeDialog(root);
    };

    dlg.querySelector("[data-submit]").onclick = async function () {
      if (!dlg._confirmedPackage) return;
      if (!activeToken()) {
        var errBox = dlg.querySelector("[data-errors]");
        errBox.hidden = false;
        errBox.textContent = "GitHub connection required for direct submission.";
        return;
      }
      var submitPkg = Object.assign({}, dlg._confirmedPackage, {
        transport: "github_issue"
      });
      try {
        var r = await fetch("https://api.github.com/repos/" + REPO + "/issues", {
          method: "POST",
          headers: {
            Accept: "application/vnd.github+json",
            Authorization: "Bearer " + activeToken(),
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            title: "Review request for " + submitPkg.target_canonical_id,
            body: "```json\n" + JSON.stringify(submitPkg, null, 2) + "\n```"
          })
        });
        if (!r.ok) {
          throw new Error("GitHub submission failed (" + r.status + "): " + (await r.text()).slice(0, 150));
        }
        var issue = await r.json();
        setState(root, "Submitted as GitHub issue #" + issue.number + " — awaiting review.", "submitted");
        closeDialog(root);
      } catch (err) {
        var errBox = dlg.querySelector("[data-errors]");
        errBox.hidden = false;
        errBox.textContent = err.message || "Submission failed.";
        errBox.focus();
      }
    };
  }

  function init(root) {
    var dataEl = root.querySelector(".review-request-data");
    if (!dataEl) return;
    var data = JSON.parse(dataEl.textContent);
    var btn = root.querySelector("[data-review-request-open]");
    if (btn) {
      btn.addEventListener("click", function () { openDialog(root, data); });
    }
  }

  // Export functions for testing environments (Node.js / CommonJS)
  if (typeof module !== "undefined" && module.exports) {
    module.exports = {
      generateUUIDv7: generateUUIDv7,
      requestId: requestId,
      cleanName: cleanName,
      validName: validName,
      buildConfirmedPackage: buildConfirmedPackage
    };
  }

  if (typeof document !== "undefined") {
    document.addEventListener("DOMContentLoaded", function () {
      document.querySelectorAll("[data-review-request-root]").forEach(init);
    });
  }
})();
