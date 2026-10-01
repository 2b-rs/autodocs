#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_src/tools/agent_feedback_form.py -- Controlled agent/profile feedback UX & API validation (Task 0046-01.01).

Implements:
- REQ-0046-01: Bounded feedback text, target agent pinning, observed baseline pinning,
  category hint, consent/visibility selection, and safe preview generation.
- REQ-0046-02: Submitter attribution & anonymous submission policy enforcement.
  Identified submitters retain actor identity/digest; anonymous submissions forbid actor,
  force approval_authority=False, and receive a non-identifying abuse-control token.
- REQ-0046-03: Deterministic content digest, idempotency key handling, and schema-valid envelope.
- REQ-0046-14 & REQ-0046-15: Injection-safe rendering, bounds checking, and data minimization.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import html
import json
import re
import secrets
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

SCHEMA_VERSION: str = "agent-profile-feedback@v1"
MAX_FEEDBACK_LENGTH: int = 4000
MIN_FEEDBACK_LENGTH: int = 1
MAX_AGENT_NAME_LENGTH: int = 120
MAX_BASELINE_LENGTH: int = 128
MAX_SUBMITTER_LENGTH: int = 120

ALLOWED_CATEGORIES: Tuple[str, ...] = (
    "factual_correction",
    "persona_preference",
    "role_process",
    "capability",
    "safety",
    "abuse_noise",
    "general",
)

ALLOWED_ATTRIBUTIONS: Tuple[str, ...] = (
    "identified",
    "anonymous",
)

ALLOWED_VISIBILITIES: Tuple[str, ...] = (
    "public",
    "private",
    "redacted",
    "team_only",
)

AGENT_NAME_REGEX: re.Pattern = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,119}$")
BASELINE_REGEX: re.Pattern = re.compile(r"^[a-zA-Z0-9_\-\.\:\@]{1,128}$")


class FeedbackValidationError(ValueError):
    """Raised when feedback input fails validation constraints before any processing."""
    pass


def _now_iso_utc() -> str:
    """Current UTC timestamp in RFC3339 / ISO 8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_envelope_id() -> str:
    """Sortable unique id: <13-digit millisecond timestamp>-<8 hex chars>."""
    ms = int(time.time() * 1000)
    rand_hex = secrets.token_hex(4)
    return f"{ms:013d}-{rand_hex}"


def compute_actor_digest(actor: str) -> str:
    """Compute non-reversible SHA-256 actor digest prefix for audit identity survival."""
    return hashlib.sha256(actor.strip().encode("utf-8")).hexdigest()[:16]


def compute_abuse_control_token(target_agent: str, baseline: str, salt: Optional[str] = None) -> str:
    """Generate a non-identifying abuse-control token for anonymous submissions (REQ-0046-02)."""
    effective_salt = salt or secrets.token_hex(8)
    raw = f"abuse-control:{target_agent}:{baseline}:{effective_salt}:{int(time.time())}"
    token_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"abt_{token_hash}"


def compute_content_digest(payload: Dict[str, Any]) -> str:
    """Deterministic SHA-256 digest over normalized JSON payload bytes."""
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def validate_target_agent(target: Any) -> str:
    """Validate target agent identifier."""
    if not isinstance(target, str):
        raise FeedbackValidationError(f"Target agent must be a string, got {type(target).__name__}")
    cleaned = target.strip()
    if not cleaned:
        raise FeedbackValidationError("Target agent cannot be empty")
    if len(cleaned) > MAX_AGENT_NAME_LENGTH:
        raise FeedbackValidationError(f"Target agent name exceeds max length {MAX_AGENT_NAME_LENGTH}")
    if not AGENT_NAME_REGEX.match(cleaned):
        raise FeedbackValidationError(
            f"Target agent name contains invalid characters: '{cleaned}'. "
            "Allowed: alphanumeric, underscores, hyphens, and dots."
        )
    return cleaned


def validate_observed_baseline(baseline: Any) -> str:
    """Validate observed authoritative baseline/revision identifier."""
    if not isinstance(baseline, str):
        raise FeedbackValidationError(f"Observed baseline must be a string, got {type(baseline).__name__}")
    cleaned = baseline.strip()
    if not cleaned:
        raise FeedbackValidationError("Observed baseline cannot be empty")
    if len(cleaned) > MAX_BASELINE_LENGTH:
        raise FeedbackValidationError(f"Observed baseline exceeds max length {MAX_BASELINE_LENGTH}")
    if not BASELINE_REGEX.match(cleaned):
        raise FeedbackValidationError(
            f"Observed baseline contains invalid characters: '{cleaned}'"
        )
    return cleaned


def validate_feedback_text(text: Any, max_length: int = MAX_FEEDBACK_LENGTH) -> str:
    """Validate bounded feedback body text."""
    if not isinstance(text, str):
        raise FeedbackValidationError(f"Feedback text must be a string, got {type(text).__name__}")
    cleaned = text.strip()
    if len(cleaned) < MIN_FEEDBACK_LENGTH:
        raise FeedbackValidationError("Feedback text cannot be empty or solely whitespace")
    if len(cleaned) > max_length:
        raise FeedbackValidationError(
            f"Feedback text length ({len(cleaned)}) exceeds maximum allowed ({max_length} characters)"
        )
    if "\x00" in cleaned:
        raise FeedbackValidationError("Feedback text contains illegal null byte")
    return cleaned


def normalize_category(category: Any) -> str:
    """Normalize and validate category hint."""
    if not isinstance(category, str):
        raise FeedbackValidationError(f"Category must be a string, got {type(category).__name__}")
    normalized = category.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in ALLOWED_CATEGORIES:
        raise FeedbackValidationError(
            f"Invalid category '{category}'. Allowed categories: {', '.join(ALLOWED_CATEGORIES)}"
        )
    return normalized


def normalize_consent_visibility(visibility: Any) -> str:
    """Normalize and validate consent / visibility policy choice."""
    if visibility is None:
        return "private"
    if not isinstance(visibility, str):
        raise FeedbackValidationError(f"Consent/visibility must be a string, got {type(visibility).__name__}")
    normalized = visibility.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in ALLOWED_VISIBILITIES:
        raise FeedbackValidationError(
            f"Invalid consent/visibility '{visibility}'. Allowed: {', '.join(ALLOWED_VISIBILITIES)}"
        )
    return normalized


def validate_attribution_policy(
    attribution: Any,
    submitter: Optional[Any] = None,
) -> Tuple[str, Optional[str], Optional[str], Dict[str, Any]]:
    """Enforce REQ-0046-02 identity and anonymous policy.

    Returns: (normalized_attribution, clean_submitter, actor_digest, policy_result)
    """
    if attribution is None:
        attribution = "identified" if submitter else "anonymous"

    if not isinstance(attribution, str):
        raise FeedbackValidationError(f"Attribution must be a string, got {type(attribution).__name__}")

    norm_attr = attribution.strip().lower()
    if norm_attr not in ALLOWED_ATTRIBUTIONS:
        raise FeedbackValidationError(
            f"Invalid attribution '{attribution}'. Allowed: {', '.join(ALLOWED_ATTRIBUTIONS)}"
        )

    if norm_attr == "anonymous":
        if submitter is not None and str(submitter).strip() != "":
            raise FeedbackValidationError(
                "Anonymous submission must not carry an actor or submitter identifier"
            )
        policy_result = {
            "approval_authority": False,
            "basis": "anonymous submissions never carry approval authority (REQ-0046-02 / I5)",
        }
        return norm_attr, None, None, policy_result

    if submitter is None or not str(submitter).strip():
        raise FeedbackValidationError("Identified submission requires a non-empty submitter actor")

    clean_submitter = str(submitter).strip()
    if len(clean_submitter) > MAX_SUBMITTER_LENGTH:
        raise FeedbackValidationError(
            f"Submitter name exceeds maximum length {MAX_SUBMITTER_LENGTH}"
        )
    if not AGENT_NAME_REGEX.match(clean_submitter):
        raise FeedbackValidationError(
            f"Submitter identifier contains invalid characters: '{clean_submitter}'"
        )

    digest = compute_actor_digest(clean_submitter)
    policy_result = {
        "approval_authority": True,
        "basis": "identified submitter; authority still subject to separate human decision policy",
    }
    return norm_attr, clean_submitter, digest, policy_result


@dataclass(frozen=True)
class FeedbackInput:
    """Raw structured feedback input before validation."""
    target_agent: str
    observed_baseline: str
    feedback_text: str
    category: str = "general"
    attribution: str = "identified"
    submitter: Optional[str] = None
    consent_visibility: str = "private"
    idempotency_key: Optional[str] = None
    abuse_control_token: Optional[str] = None


@dataclass(frozen=True)
class FeedbackEnvelope:
    """Validated, schema-conforming feedback envelope (REQ-0046-01, REQ-0046-03)."""
    schema: str
    envelope_id: str
    recorded_at: str
    target_agent: str
    observed_baseline: str
    category: str
    attribution: str
    submitter: Optional[str]
    actor_digest: Optional[str]
    abuse_control_token: Optional[str]
    feedback_text: str
    consent_visibility: str
    policy_result: Dict[str, Any]
    content_digest: str
    idempotency_key: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert envelope to dictionary."""
        return dataclasses.asdict(self)

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Serialize envelope to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass(frozen=True)
class PreviewData:
    """Safe presentation model for target/baseline preview (REQ-0046-01)."""
    target_agent: str
    observed_baseline: str
    category: str
    attribution: str
    submitter_display: str
    consent_visibility: str
    text_preview: str
    text_length: int
    approval_authority: bool
    is_anonymous: bool
    content_digest: str
    idempotency_key: str
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


def validate_feedback(data: Union[Dict[str, Any], FeedbackInput]) -> FeedbackEnvelope:
    """Validate input payload and produce an immutable FeedbackEnvelope."""
    if isinstance(data, FeedbackInput):
        raw_target = data.target_agent
        raw_baseline = data.observed_baseline
        raw_text = data.feedback_text
        raw_cat = data.category
        raw_attr = data.attribution
        raw_sub = data.submitter
        raw_vis = data.consent_visibility
        raw_idem = data.idempotency_key
        raw_abt = data.abuse_control_token
    elif isinstance(data, dict):
        raw_target = data.get("target_agent")
        raw_baseline = data.get("observed_baseline")
        raw_text = data.get("feedback_text")
        raw_cat = data.get("category", "general")
        raw_attr = data.get("attribution", "identified" if data.get("submitter") else "anonymous")
        raw_sub = data.get("submitter")
        raw_vis = data.get("consent_visibility", "private")
        raw_idem = data.get("idempotency_key")
        raw_abt = data.get("abuse_control_token")
    else:
        raise FeedbackValidationError(f"Expected dict or FeedbackInput, got {type(data).__name__}")

    clean_target = validate_target_agent(raw_target)
    clean_baseline = validate_observed_baseline(raw_baseline)
    clean_text = validate_feedback_text(raw_text)
    clean_cat = normalize_category(raw_cat)
    clean_vis = normalize_consent_visibility(raw_vis)
    clean_attr, clean_sub, actor_dig, policy_res = validate_attribution_policy(raw_attr, raw_sub)

    abuse_tok: Optional[str] = None
    if clean_attr == "anonymous":
        if raw_abt and isinstance(raw_abt, str) and raw_abt.startswith("abt_"):
            abuse_tok = raw_abt.strip()
        else:
            abuse_tok = compute_abuse_control_token(clean_target, clean_baseline)

    envelope_id = _new_envelope_id()
    timestamp = _now_iso_utc()

    if raw_idem and isinstance(raw_idem, str) and raw_idem.strip():
        idempotency_key = raw_idem.strip()
    else:
        actor_part = clean_sub if clean_sub else "anon"
        seed = f"{clean_target}:{clean_baseline}:{actor_part}:{clean_text}"
        idempotency_key = f"idem_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:20]}"

    core_payload = {
        "target_agent": clean_target,
        "observed_baseline": clean_baseline,
        "category": clean_cat,
        "attribution": clean_attr,
        "submitter": clean_sub,
        "feedback_text": clean_text,
        "consent_visibility": clean_vis,
        "idempotency_key": idempotency_key,
    }
    content_dig = compute_content_digest(core_payload)

    return FeedbackEnvelope(
        schema=SCHEMA_VERSION,
        envelope_id=envelope_id,
        recorded_at=timestamp,
        target_agent=clean_target,
        observed_baseline=clean_baseline,
        category=clean_cat,
        attribution=clean_attr,
        submitter=clean_sub,
        actor_digest=actor_dig,
        abuse_control_token=abuse_tok,
        feedback_text=clean_text,
        consent_visibility=clean_vis,
        policy_result=policy_res,
        content_digest=content_dig,
        idempotency_key=idempotency_key,
    )


def generate_preview(data: Union[Dict[str, Any], FeedbackInput, FeedbackEnvelope]) -> PreviewData:
    """Generate safe, projection-ready PreviewData without leaking private prompts or secrets."""
    if isinstance(data, FeedbackEnvelope):
        envelope = data
    else:
        envelope = validate_feedback(data)

    warnings: List[str] = []
    if len(envelope.feedback_text) > 2000:
        warnings.append("Feedback text is lengthy; ensure it is focused on specific behavioral or factual changes.")

    lower_text = envelope.feedback_text.lower()
    if "api_key" in lower_text or "token" in lower_text or "secret" in lower_text:
        warnings.append("Warning: text may contain sensitive credential keywords; verify no secrets are submitted.")

    submitter_display = envelope.submitter if envelope.attribution == "identified" else "[Anonymous Submitter]"

    return PreviewData(
        target_agent=envelope.target_agent,
        observed_baseline=envelope.observed_baseline,
        category=envelope.category,
        attribution=envelope.attribution,
        submitter_display=submitter_display,
        consent_visibility=envelope.consent_visibility,
        text_preview=envelope.feedback_text,
        text_length=len(envelope.feedback_text),
        approval_authority=envelope.policy_result.get("approval_authority", False),
        is_anonymous=(envelope.attribution == "anonymous"),
        content_digest=envelope.content_digest,
        idempotency_key=envelope.idempotency_key,
        warnings=warnings,
    )


def render_preview_html(preview: PreviewData) -> str:
    """Render preview data into accessible, strictly escaped HTML (REQ-0046-01, REQ-0046-14)."""
    esc_target = html.escape(preview.target_agent)
    esc_baseline = html.escape(preview.observed_baseline)
    esc_category = html.escape(preview.category.replace("_", " ").title())
    esc_attr = html.escape(preview.attribution.title())
    esc_submitter = html.escape(preview.submitter_display)
    esc_visibility = html.escape(preview.consent_visibility.replace("_", " ").title())
    # Match the client renderer's decimal apostrophe entity while retaining
    # the same injection-safe escaped value.
    esc_text = html.escape(preview.text_preview).replace("&#x27;", "&#039;")
    esc_digest = html.escape(preview.content_digest[:16] + "…")
    esc_idempotency = html.escape(preview.idempotency_key)

    authority_badge = (
        '<span class="badge badge-success">Eligible for Review</span>'
        if preview.approval_authority
        else '<span class="badge badge-warning">No Approval Authority (Anonymous Policy)</span>'
    )

    warnings_html = ""
    if preview.warnings:
        warn_items = "".join(f"<li>{html.escape(w)}</li>" for w in preview.warnings)
        warnings_html = f'<div class="feedback-warnings" role="alert"><ul class="warning-list">{warn_items}</ul></div>'

    return f"""<div class="agent-feedback-preview" role="region" aria-label="Feedback Submission Preview">
  <div class="preview-header">
    <h3 class="preview-title">Submission Preview</h3>
    <div class="preview-authority-status">{authority_badge}</div>
  </div>
  {warnings_html}
  <dl class="preview-meta-grid">
    <div class="meta-item">
      <dt>Target Agent:</dt>
      <dd class="val-target"><code>{esc_target}</code></dd>
    </div>
    <div class="meta-item">
      <dt>Observed Baseline:</dt>
      <dd class="val-baseline"><code>{esc_baseline}</code></dd>
    </div>
    <div class="meta-item">
      <dt>Category:</dt>
      <dd class="val-category">{esc_category}</dd>
    </div>
    <div class="meta-item">
      <dt>Attribution:</dt>
      <dd class="val-attribution">{esc_attr} ({esc_submitter})</dd>
    </div>
    <div class="meta-item">
      <dt>Visibility:</dt>
      <dd class="val-visibility">{esc_visibility}</dd>
    </div>
    <div class="meta-item">
      <dt>Content Digest:</dt>
      <dd class="val-digest"><code>{esc_digest}</code></dd>
    </div>
    <div class="meta-item">
      <dt>Idempotency Key:</dt>
      <dd class="val-idempotency"><code>{esc_idempotency}</code></dd>
    </div>
    <div class="meta-item">
      <dt>Length:</dt>
      <dd class="val-length">{preview.text_length} characters</dd>
    </div>
  </dl>
  <div class="preview-body">
    <div class="preview-body-label">Feedback Content:</div>
    <pre class="preview-content-box" tabindex="0">{esc_text}</pre>
  </div>
</div>"""


def render_feedback_form(
    target_agent: str = "",
    observed_baseline: str = "",
    submitter: str = "",
    category: str = "general",
    attribution: str = "identified",
    consent_visibility: str = "private",
    action_url: str = "/api/feedback",
) -> str:
    """Render accessible HTML feedback form."""
    template_path = Path(__file__).resolve().parents[1] / "templates" / "agent_feedback.html"
    if template_path.exists():
        tmpl = template_path.read_text(encoding="utf-8")
        rendered = tmpl.replace("{{TARGET_AGENT}}", html.escape(target_agent))
        rendered = rendered.replace("{{OBSERVED_BASELINE}}", html.escape(observed_baseline))
        rendered = rendered.replace("{{SUBMITTER}}", html.escape(submitter))
        rendered = rendered.replace("{{ACTION_URL}}", html.escape(action_url))
        return rendered

    return f"""<form id="agentFeedbackForm" class="agent-feedback-form" method="POST" action="{html.escape(action_url)}">
  <input type="hidden" name="schema" value="{SCHEMA_VERSION}">
  <div class="form-group">
    <label for="target_agent">Target Agent (required):</label>
    <input type="text" id="target_agent" name="target_agent" value="{html.escape(target_agent)}" required maxlength="{MAX_AGENT_NAME_LENGTH}">
  </div>
  <div class="form-group">
    <label for="observed_baseline">Observed Revision / Baseline (required):</label>
    <input type="text" id="observed_baseline" name="observed_baseline" value="{html.escape(observed_baseline)}" required maxlength="{MAX_BASELINE_LENGTH}">
  </div>
  <div class="form-group">
    <label for="category">Category:</label>
    <select id="category" name="category">
      {"".join(f'<option value="{c}">{c.replace("_", " ").title()}</option>' for c in ALLOWED_CATEGORIES)}
    </select>
  </div>
  <fieldset class="form-group">
    <legend>Attribution Policy</legend>
    <label><input type="radio" name="attribution" value="identified" checked> Identified</label>
    <label><input type="radio" name="attribution" value="anonymous"> Anonymous</label>
  </fieldset>
  <div class="form-group" id="submitter_group">
    <label for="submitter">Submitter Name / ID:</label>
    <input type="text" id="submitter" name="submitter" value="{html.escape(submitter)}" maxlength="{MAX_SUBMITTER_LENGTH}">
  </div>
  <div class="form-group">
    <label for="consent_visibility">Visibility & Consent:</label>
    <select id="consent_visibility" name="consent_visibility">
      {"".join(f'<option value="{v}">{v.replace("_", " ").title()}</option>' for v in ALLOWED_VISIBILITIES)}
    </select>
  </div>
  <div class="form-group">
    <label for="feedback_text">Feedback Text (max {MAX_FEEDBACK_LENGTH} chars):</label>
    <textarea id="feedback_text" name="feedback_text" rows="6" maxlength="{MAX_FEEDBACK_LENGTH}" required></textarea>
    <div id="char_counter" class="char-counter">0 / {MAX_FEEDBACK_LENGTH}</div>
  </div>
  <div class="form-actions">
    <button type="button" id="btnPreview" class="btn btn-secondary">Preview Submission</button>
    <button type="submit" id="btnSubmit" class="btn btn-primary">Submit Feedback</button>
  </div>
  <div id="previewContainer" class="preview-container" aria-live="polite"></div>
</form>"""


def main(argv: Optional[List[str]] = None) -> int:
    """CLI driver for validation, envelope generation, and preview rendering."""
    parser = argparse.ArgumentParser(description="Agent Profile Feedback Form Validation & Preview")
    parser.add_argument("--validate", action="store_true", help="Validate input JSON from stdin or file")
    parser.add_argument("--preview", action="store_true", help="Generate preview and print JSON")
    parser.add_argument("--render-preview-html", action="store_true", help="Render preview HTML")
    parser.add_argument("--input", "-i", type=str, help="Path to input JSON file (default: stdin)")
    parser.add_argument("--target", type=str, help="Target agent name")
    parser.add_argument("--baseline", type=str, help="Observed baseline revision")
    parser.add_argument("--text", type=str, help="Feedback text")
    parser.add_argument("--category", type=str, help="Feedback category")
    parser.add_argument("--attribution", type=str, help="identified or anonymous")
    parser.add_argument("--submitter", type=str, help="Submitter identifier (required if identified)")
    parser.add_argument("--visibility", type=str, help="Consent visibility")

    args = parser.parse_args(argv)

    input_data: Dict[str, Any] = {}
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            input_data = json.load(f)
    elif not sys.stdin.isatty() and not (args.target and args.baseline and args.text):
        try:
            content = sys.stdin.read().strip()
            if content:
                input_data = json.loads(content)
        except Exception as ex:
            sys.stderr.write(f"Error reading JSON from stdin: {ex}\n")
            return 1

    if args.target:
        input_data["target_agent"] = args.target
    if args.baseline:
        input_data["observed_baseline"] = args.baseline
    if args.text:
        input_data["feedback_text"] = args.text
    if args.category:
        input_data["category"] = args.category
    if args.attribution:
        input_data["attribution"] = args.attribution
    if args.submitter:
        input_data["submitter"] = args.submitter
    if args.visibility:
        input_data["consent_visibility"] = args.visibility

    try:
        envelope = validate_feedback(input_data)
    except FeedbackValidationError as err:
        sys.stderr.write(f"Validation Error: {err}\n")
        return 2

    if args.render_preview_html:
        preview = generate_preview(envelope)
        print(render_preview_html(preview))
    elif args.preview:
        preview = generate_preview(envelope)
        print(json.dumps(preview.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(envelope.to_json())

    return 0


if __name__ == "__main__":
    sys.exit(main())
