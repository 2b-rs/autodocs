# Website Review-Request Process

This document reconciles the authoritative process for submitting, validating, and deciding on website review requests, governing eligibility, exclusions, abuse handling, role authority, closure, privacy, and retention.

## 1. Scope and Eligibility
- **Scope**: Covers all formal review requests submitted via the website interface.
- **Eligibility**: A request is eligible for review only if it provides:
  - An identifiable, exact baseline (e.g., commit hash or version tag).
  - The specific component or document under review.
  - Explicit acceptance criteria to be evaluated against.
- Submissions lacking these minimum criteria are strictly invalid.

## 2. Exclusions
- **Out-of-Band Requests**: Submissions via email, chat, or other informal channels are excluded and will not be processed.
- **Informal Queries**: General questions or feedback without a concrete baseline or criteria are excluded from this formal review pipeline.
- **Duplicate Requests**: Submissions that duplicate an active or recently closed review without introducing new evidence or changes are excluded.

## 3. Abuse Handling and Moderation
- **Rate Limiting**: Automated or high-frequency submissions will be throttled.
- **Rejection of Abuse**: Submissions containing malicious payloads, spam, or abusive language will be immediately rejected.
- **Escalation**: Repeatedly submitting without addressing prior review feedback or attempting to bypass the validation model will result in operator-mediated quarantine.
- **Bans**: The Project Lead holds the authority to enact temporary or permanent bans for sustained abuse of the review system.

## 4. Role Authority
- **Requester**: The actor initiating the review. Responsible for providing necessary context, baseline, and criteria, and for addressing inquiries or feedback.
- **Reviewer**: Evaluates the submission strictly against the provided baseline and acceptance criteria. Can transition the request to accepted or rejected.
- **Operator/Moderator**: Handles abuse reports, quarantine queues, and applies quota controls.
- **Project Lead**: Mediates disputes, manages escalation controls, signs off on controversial closures, and holds the ultimate authority for system remediation.

## 5. Closure Transitions
- **Accepted**: The review criteria have been met and verified. Must be signed off by an authorized Reviewer.
- **Rejected**: The submission failed to meet the criteria, contained substandard quality, lacked prerequisites, or failed to address feedback. Terminally rejected and no-apply.
- **Withdrawn**: Retracted by the Requester prior to a formal decision.

## 6. Privacy and Retention
- **Privacy**: Personal Data (PII) submitted within a review request is processed strictly for the duration of the review lifecycle. Explicit consent is required if external issue linkage occurs.
- **Redaction and Expiry**: Any attached artifacts, envelopes, or logs containing sensitive data must be redacted or expunged in accordance with retention limits.
- **Retention**: Metadata, lifecycle transitions, and the formal review outcome (accepted/rejected) are retained indefinitely as part of the immutable project history. Associated PII or transient attachments are permanently expunged 30 days after closure, subject to limitation handling where external deletion cannot be guaranteed.
