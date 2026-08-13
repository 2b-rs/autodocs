"""Cross-check between curation-item@v1's status vocabulary (0006-03,
curation_item.VALID_STATUSES) and the unified lifecycle's state vocabulary
(0006-06, workflow_lifecycle.STATES). Feature 0006-13.

The two modules describe the same concept from two angles -- curation_item.py
is the payload-shape validator, workflow_lifecycle.py is the state-machine
vocabulary -- and were written independently. This module gives validate.py a
single place to assert they have not silently drifted apart, and gives
curation-item payloads a way to have their 'status' field checked against
lifecycle-valid states, not just against curation_item.py's own enum.

Note the two vocabularies are NOT identical by design: curation-item@v1's
status values are "open"/"claimed"/"proposed"/"accepted"/"rejected"/
"superseded"/"applied" (7 values, no "discovered" or "published" -- those
describe pipeline POSITION before a curation-item exists or after a build
has run, not a persisted item's own status field) plus "open" is
curation-item@v1's synonym for workflow_lifecycle's "queued" (both mean
"written to a queue, not yet claimed" -- curation-item@v1 predates
workflow_lifecycle and named it before the shared vocabulary existed).
"""
from __future__ import annotations
import sys
from pathlib import Path

_TOOLS_DIR = str(Path(__file__).resolve().parent)
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
import curation_item as ci  # noqa: E402
import workflow_lifecycle as wl  # noqa: E402

# curation-item@v1 status -> workflow_lifecycle state it corresponds to.
# Every curation_item.VALID_STATUSES entry MUST have an entry here, and the
# right-hand side MUST be a real workflow_lifecycle.STATES member; this dict
# itself is asserted against both vocabularies by validate_vocabularies().
STATUS_TO_LIFECYCLE_STATE = {
    "open": "queued",
    "claimed": "claimed",
    "proposed": "proposed",
    "accepted": "accepted",
    "rejected": "rejected",
    "superseded": "superseded",
    "applied": "applied",
}


def validate_vocabularies() -> list[str]:
    """Returns a list of human-readable problems; empty list means the two
    vocabularies are consistent. Never raises -- callers (validate.py,
    tests) decide how to react to a non-empty result."""
    problems = []
    mapped_statuses = set(STATUS_TO_LIFECYCLE_STATE)
    schema_statuses = set(ci.VALID_STATUSES)
    if mapped_statuses != schema_statuses:
        missing = schema_statuses - mapped_statuses
        extra = mapped_statuses - schema_statuses
        if missing:
            problems.append(
                "curation_item.VALID_STATUSES has status(es) not mapped here: %s" % sorted(missing))
        if extra:
            problems.append(
                "STATUS_TO_LIFECYCLE_STATE maps status(es) curation_item.py no longer declares: %s" % sorted(extra))
    for status, state in STATUS_TO_LIFECYCLE_STATE.items():
        if state not in wl.STATES:
            problems.append(
                "STATUS_TO_LIFECYCLE_STATE['%s'] = '%s' is not a workflow_lifecycle.STATES member" % (status, state))
    return problems


def item_lifecycle_state(item: dict) -> str | None:
    """Given a curation-item@v1 payload, return the corresponding
    workflow_lifecycle state name, or None if the item's status is not a
    known curation-item status (caller should treat that as a conformance
    failure via curation_item.is_conformant() first)."""
    return STATUS_TO_LIFECYCLE_STATE.get(item.get("status"))
