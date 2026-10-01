"""Unified curation/review lifecycle (Feature 0006-06).

Before this module, the docs described two partially disconnected paths:
queue-based (review-queue/curation-queue -> AI agent -> curator, via
review_flags.py/curation_flags.py) and browser-based (review.js -> GitHub
issue/JSON -> review_ingest.py/curation_ingest.py). 0006-05 added a third
entry point (hypothesis_store.py) that touches neither queue. This module
gives all three ONE shared vocabulary of states and transitions, and
documents -- as data, not just prose -- which existing tool function
performs which transition.

States (curation-item@v1's status enum from 0006-03, plus the two states
that schema deliberately left to the docs layer -- 'discovered' and
'published' -- since they describe pipeline position, not a curation-item's
own persisted status field):
    discovered -> queued -> claimed -> proposed -> accepted/rejected
                                                 -> applied -> published
                                                 -> superseded

This module does NOT change how any existing tool persists state (queue
file existence remains each queue tool's own state representation) -- it is
a shared reference vocabulary and a transition validator other tools/tests
can call, consistent with how 0006-03/05/15/16/17 were scoped.
"""
from __future__ import annotations

STATES = (
    "discovered", "queued", "claimed", "proposed", "accepted",
    "rejected", "applied", "published", "superseded",
)

VALID_TRANSITIONS: dict[str, tuple[str, ...]] = {
    # applied: browser-ingest path (review_ingest.ingest) can skip the queue
    # entirely and write a decision straight into the record. proposed:
    # hypothesis_store.record_hypothesis (0006-05) has no queue of its own --
    # an AI proposing a brand-new spec element goes straight from "nothing
    # exists yet" to "proposed, awaiting curator decision".
    "discovered": ("queued", "applied", "proposed"),
    "queued": ("claimed",),
    "claimed": ("proposed", "queued", "applied"),  # queued: release_flag(); applied: direct curator decision
    # "applied" is included here (not just "accepted"/"rejected") because
    # review_flags.py (unlike curation_flags.py) has no separate curator-accept
    # step: review_flags.complete_flag() completes the flag directly once an AI
    # agent has written its decision, whether or not the caller first passed
    # through a conceptual "proposed" state -- accept-and-apply happen in one call.
    "proposed": ("accepted", "rejected", "applied"),
    "accepted": ("applied",),
    "rejected": (),  # terminal; never deleted, per 0006-16's never-delete precedent
    "applied": ("published", "superseded"),
    "published": ("superseded",),
    "superseded": (),  # terminal
}

# Maps "module.function" -> (from_states, to_state, notes). from_states is a
# tuple because some functions are reachable from more than one prior state
# depending on which path produced the item.
TOOL_TRANSITIONS: dict[str, dict] = {
    "review_flags.write_review_flag": {
        "from": ("discovered",), "to": "queued",
        "notes": "Extraction finds an ambiguity it can't auto-resolve; writes a flag to review-queue/open/.",
    },
    "review_flags.claim_flag": {
        "from": ("queued",), "to": "claimed",
        "notes": "Atomic os.rename into review-queue/claimed/; exactly one concurrent agent wins.",
    },
    "review_flags.release_flag": {
        "from": ("claimed",), "to": "queued",
        "notes": "Agent aborts; flag moves back to open/ for another agent to claim.",
    },
    "review_flags.complete_flag": {
        "from": ("claimed", "proposed"), "to": "applied",
        "notes": "Decision already written into the record before this call; flag file is DELETED (job control only, not the source of truth).",
    },
    "curation_flags.write_curation_flag": {
        "from": ("discovered",), "to": "queued",
        "notes": "curation_ingest.py writes this after a browser-submitted curation_request package is accepted for queuing.",
    },
    "curation_flags.claim_flag": {
        "from": ("queued",), "to": "claimed",
        "notes": "AI agent claims a curation-queue item to propose a concrete change.",
    },
    "curation_flags.release_flag": {
        "from": ("claimed",), "to": "queued",
        "notes": "Agent aborts; same semantics as review_flags.release_flag.",
    },
    "curation_flags.complete_flag": {
        "from": ("claimed", "proposed", "accepted"), "to": "applied",
        "notes": "Only the human operating the extraction scripts calls this, after merging/discarding the AI's proposed diff or RESIDUAL entry.",
    },
    "review_ingest.ingest": {
        "from": ("discovered", "claimed"), "to": "applied",
        "notes": "Browser path: a review.js decision package writes text_hash-checked decisions directly into the record. Can skip queued/claimed entirely for a requirement the reader decided on unprompted.",
    },
    "curation_ingest.ingest": {
        "from": ("discovered",), "to": "queued",
        "notes": "Browser path for curation_request items: writes a new curation-queue flag (via curation_flags.write_curation_flag) rather than applying directly -- curation decisions need an AI-proposed concrete change first.",
    },
    "hypothesis_store.record_hypothesis": {
        "from": ("discovered",), "to": "proposed",
        "notes": "AI proposes a brand-new spec element; skips queued/claimed (there is no queue for hypotheses -- see 0006-05's own store) and starts directly at proposed, awaiting curator decision.",
    },
    "hypothesis_store.promote_hypothesis": {
        "from": ("proposed",), "to": "applied",
        "notes": "Curator accepts; mints a real canonical id and writes into _src/spec/records/ with a source_hypothesis history link.",
    },
    "hypothesis_store.reject_hypothesis": {
        "from": ("proposed",), "to": "rejected",
        "notes": "Curator rejects; hypothesis file is marked rejected in place, never deleted.",
    },
    "generate.py (publish step)": {
        "from": ("applied",), "to": "published",
        "notes": "Not a curation-queue tool; the regular HTML build makes an applied change visible in the published tree. Documented here because 'published' is otherwise an undocumented implicit state.",
    },
    "version_store.record_version / spec_scrape.py (next release import)": {
        "from": ("published",), "to": "superseded",
        "notes": "A later AUTOSAR release changes the same requirement; per 0006-15/0006-18, supersession is an explicit edge, never inferred from timestamps.",
    },
}


def validate_transition(from_state: str, to_state: str) -> bool:
    if from_state not in VALID_TRANSITIONS:
        raise ValueError(f"unknown state: {from_state!r}")
    if to_state not in STATES:
        raise ValueError(f"unknown state: {to_state!r}")
    return to_state in VALID_TRANSITIONS[from_state]
