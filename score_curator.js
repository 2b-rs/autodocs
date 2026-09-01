// score_curator.js — Client-side Curator Decision UI and Durable GitHub Contract
// Part of Feature 0045 (S-Core/AUTOSAR Feedback Loop, Task 0045-05)
(function (root, factory) {
  if (typeof define === "function" && define.amd) {
    define([], factory);
  } else if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.ScoreCurator = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var ENVELOPE_SCHEMA = "curator-decision-envelope@v1";
  var CONTRACT_VERSION = "v1.0.0";
  var VALID_OUTCOMES = ["accept", "reject", "request_revision"];

  /**
   * Build an exact, replay-safe decision key: decision:<proposal-id>:<revision>
   */
  function buildDecisionKey(proposalId, revision) {
    var rev = revision !== undefined && revision !== null ? revision : 1;
    return "decision:" + String(proposalId).trim() + ":" + String(rev).trim();
  }

  /**
   * Validate a curator decision input payload.
   */
  function validateDecisionInput(input) {
    var errors = [];
    if (!input || typeof input !== "object") {
      return ["Decision input must be a non-null object"];
    }
    if (!input.proposal_id || !String(input.proposal_id).trim()) {
      errors.push("Missing required field: proposal_id");
    }
    if (!input.baseline_digest || !String(input.baseline_digest).trim()) {
      errors.push("Missing required field: baseline_digest");
    }
    if (!input.curator_id || !String(input.curator_id).trim()) {
      errors.push("Missing required field: curator_id");
    }
    if (!input.outcome || VALID_OUTCOMES.indexOf(input.outcome) === -1) {
      errors.push("Invalid outcome: must be one of " + VALID_OUTCOMES.join(", "));
    }
    if (!input.rationale || !String(input.rationale).trim()) {
      errors.push("Missing required field: rationale");
    }
    return errors;
  }

  /**
   * Construct a durable curator decision arrival envelope.
   * This is an arrival envelope for minimum safe routing, not an apply authority.
   */
  function createDecisionEnvelope(params) {
    var errors = validateDecisionInput(params);
    if (errors.length > 0) {
      throw new Error("Invalid curator decision: " + errors.join("; "));
    }

    var revision = params.revision || 1;
    var decisionKey = buildDecisionKey(params.proposal_id, revision);
    var timestamp = params.timestamp || new Date().toISOString();

    var envelope = {
      schema: ENVELOPE_SCHEMA,
      contract_version: CONTRACT_VERSION,
      decision_key: decisionKey,
      proposal_id: String(params.proposal_id).trim(),
      proposal_revision: revision,
      baseline_digest: String(params.baseline_digest).trim(),
      evidence_digest: params.evidence_digest ? String(params.evidence_digest).trim() : null,
      target_canonical_id: params.target_canonical_id ? String(params.target_canonical_id).trim() : null,
      curator: {
        identity: String(params.curator_id).trim(),
        role: "Curator",
        auth_mode: params.auth_mode || "github_authenticated",
        auth_evidence: params.auth_evidence || null
      },
      decision: {
        outcome: params.outcome,
        rationale: String(params.rationale).trim(),
        decided_at: timestamp,
        revision_instructions: params.revision_instructions || null,
        conditions: params.conditions || []
      },
      routing: {
        requires_pl_offer: true,
        downstream_recipe: "curator_decision_routing",
        status: "pending_safe_routing"
      }
    };

    return envelope;
  }

  /**
   * Render Curator Decision Widget into a DOM container.
   */
  function renderCuratorWidget(container, options) {
    if (!container) return;
    options = options || {};

    var proposal = options.proposal || {};
    var baseline = options.baseline || {};
    var onSubmit = options.onSubmit || function () {};

    container.innerHTML = "";
    container.setAttribute("role", "region");
    container.setAttribute("aria-label", "Curator Decision Console");
    container.className = "curator-decision-console";

    var header = document.createElement("header");
    header.className = "curator-header";
    header.innerHTML = "<h3>S-Core Curator Decision Console</h3>" +
      "<p class='curator-sub'>Bound to pinned baseline <code>" + (baseline.digest || "unspecified") + "</code></p>";
    container.appendChild(header);

    // Diff / Evidence summary panel
    var diffPanel = document.createElement("section");
    diffPanel.className = "curator-diff-panel";
    diffPanel.setAttribute("aria-label", "Proposal Diff and Evidence");
    diffPanel.innerHTML = "<h4>Proposal Summary (" + (proposal.id || "N/A") + ")</h4>" +
      "<pre class='curator-diff-view' tabindex='0' aria-label='Unified Diff View'>" +
      (proposal.diff || "(No diff attached)") +
      "</pre>";
    container.appendChild(diffPanel);

    // Form
    var form = document.createElement("form");
    form.className = "curator-decision-form";
    form.setAttribute("novalidate", "true");

    var outcomeFieldset = document.createElement("fieldset");
    outcomeFieldset.className = "curator-outcome-fieldset";
    outcomeFieldset.innerHTML = "<legend>Decision Outcome <span aria-hidden='true'>*</span></legend>" +
      "<label><input type='radio' name='outcome' value='accept' required /> Approve & Accept Proposal</label><br/>" +
      "<label><input type='radio' name='outcome' value='reject' required /> Reject Proposal</label><br/>" +
      "<label><input type='radio' name='outcome' value='request_revision' required /> Request Revision</label>";
    form.appendChild(outcomeFieldset);

    var rationaleGroup = document.createElement("div");
    rationaleGroup.className = "form-group";
    rationaleGroup.innerHTML = "<label for='curator-rationale'>Curator Rationale <span aria-hidden='true'>*</span></label>" +
      "<textarea id='curator-rationale' name='rationale' rows='4' required aria-required='true' aria-describedby='rationale-hint'></textarea>" +
      "<small id='rationale-hint' class='form-hint'>Provide verifiable reasoning for this decision.</small>";
    form.appendChild(rationaleGroup);

    var liveStatus = document.createElement("div");
    liveStatus.id = "curator-live-status";
    liveStatus.className = "curator-status-region";
    liveStatus.setAttribute("role", "status");
    liveStatus.setAttribute("aria-live", "polite");
    form.appendChild(liveStatus);

    var buttonGroup = document.createElement("div");
    buttonGroup.className = "curator-actions";
    var submitBtn = document.createElement("button");
    submitBtn.type = "submit";
    submitBtn.className = "btn btn-primary";
    submitBtn.textContent = "Submit Curator Decision";
    buttonGroup.appendChild(submitBtn);

    var exportBtn = document.createElement("button");
    exportBtn.type = "button";
    exportBtn.className = "btn btn-secondary";
    exportBtn.textContent = "Export JSON Envelope";
    exportBtn.addEventListener("click", function () {
      try {
        var envelope = getFormDataAsEnvelope();
        var blob = new Blob([JSON.stringify(envelope, null, 2)], { type: "application/json" });
        var url = URL.createObjectURL(blob);
        var a = document.createElement("a");
        a.href = url;
        a.download = "curator-decision-" + (proposal.id || "draft") + ".json";
        a.click();
        URL.revokeObjectURL(url);
        liveStatus.textContent = "Envelope exported as JSON.";
      } catch (err) {
        liveStatus.textContent = "Export failed: " + err.message;
      }
    });
    buttonGroup.appendChild(exportBtn);
    form.appendChild(buttonGroup);

    function getFormDataAsEnvelope() {
      var selectedOutcome = form.querySelector("input[name='outcome']:checked");
      var outcomeVal = selectedOutcome ? selectedOutcome.value : null;
      var rationaleVal = form.querySelector("#curator-rationale").value;

      return createDecisionEnvelope({
        proposal_id: proposal.id || "proposal-default",
        revision: proposal.revision || 1,
        baseline_digest: baseline.digest || "0000000000000000000000000000000000000000000000000000000000000000",
        evidence_digest: proposal.evidence_digest || null,
        target_canonical_id: proposal.target_canonical_id || null,
        curator_id: options.curatorId || "curator-session",
        auth_mode: options.authMode || "github_authenticated",
        auth_evidence: options.authEvidence || null,
        outcome: outcomeVal,
        rationale: rationaleVal
      });
    }

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      try {
        var envelope = getFormDataAsEnvelope();
        liveStatus.textContent = "Curator decision envelope created successfully.";
        onSubmit(envelope);
      } catch (err) {
        liveStatus.textContent = "Validation error: " + err.message;
      }
    });

    container.appendChild(form);
  }

  return {
    ENVELOPE_SCHEMA: ENVELOPE_SCHEMA,
    CONTRACT_VERSION: CONTRACT_VERSION,
    VALID_OUTCOMES: VALID_OUTCOMES,
    buildDecisionKey: buildDecisionKey,
    validateDecisionInput: validateDecisionInput,
    createDecisionEnvelope: createDecisionEnvelope,
    renderCuratorWidget: renderCuratorWidget
  };
});
