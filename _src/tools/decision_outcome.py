"""Decision-outcome classes and post-decision hooks (Feature 0006-07).

A curator decision (curation_flags.py) or review decision (review_flags.py)
is not always "just" a data overwrite. extraction_report.py's RESIDUAL list
already shows this: some decisions require a code change (a new exception
rule), not a record edit. But RESIDUAL is a flat, hand-edited Python list --
it does not scale, and there is no generalized way to say, in the decision
itself, WHICH kind of follow-up work it implies.

This module gives every completed decision an explicit, machine-readable
``outcome_class`` (one of OUTCOME_CLASSES) plus free-form ``outcome_detail``,
and a small in-process hook registry so future tooling can react to a
specific outcome class without curation_flags.py/review_flags.py needing to
know about that tooling. No concrete hook is registered by this task --
registering real hooks (e.g. one that actually writes a migration script) is
left to whichever future feature needs that automation, matching how
hypothesis_store.py (0006-05) shipped promote/reject primitives before any
real caller existed.
"""
from __future__ import annotations
from collections import defaultdict
from typing import Callable

# The five outcome kinds named explicitly in the 0006-07 task text, plus
# "no_action": a decision can legitimately require nothing beyond closing
# the flag itself (e.g. "reject, the record was already correct").
OUTCOME_CLASSES = (
    "db_value_update",       # the decision changes a record's persisted value
    "migration",              # the decision requires a one-shot migration script
    "parser_change",          # the decision requires editing spec_scrape.py logic
    "allowlist_exception",   # the decision adds a RESIDUAL-style exception/allowlist entry
    "new_fixture",           # the decision should spawn a new benchmark/test fixture
    "no_action",             # the decision needs no follow-up beyond the flag record
)

_HOOKS: dict[str, list[Callable[[dict], None]]] = defaultdict(list)


def register_hook(outcome_class: str, fn: Callable[[dict], None]) -> None:
    """Register a callable to run whenever a decision with this
    outcome_class is completed. fn receives the full flag payload dict
    (post-completion, i.e. already carrying completed_at/outcome_class/
    outcome_detail). Raises ValueError for an unknown outcome_class so typos
    fail loudly at registration time, not silently at run time."""
    if outcome_class not in OUTCOME_CLASSES:
        raise ValueError("unknown outcome_class: %r (must be one of %s)" % (outcome_class, OUTCOME_CLASSES))
    _HOOKS[outcome_class].append(fn)


def registered_hooks(outcome_class: str) -> tuple:
    """Read-only view of hooks currently registered for an outcome_class,
    mainly for tests."""
    return tuple(_HOOKS.get(outcome_class, ()))


def run_hooks(outcome_class: str, payload: dict) -> list:
    """Run every hook registered for outcome_class, in registration order.
    A hook's exception does NOT stop the others from running (a broken
    future hook must never be able to make a curator's decision un-
    completable) -- exceptions are collected and returned instead, letting
    the caller (e.g. complete_flag()) decide whether/how to surface them.
    Returns a list of exceptions raised, in the same order as the hooks that
    raised them; an empty list means every hook ran cleanly."""
    if outcome_class not in OUTCOME_CLASSES:
        raise ValueError("unknown outcome_class: %r (must be one of %s)" % (outcome_class, OUTCOME_CLASSES))
    errors = []
    for fn in _HOOKS.get(outcome_class, ()):
        try:
            fn(payload)
        except Exception as exc:  # noqa: BLE001 -- intentionally broad, see docstring
            errors.append(exc)
    return errors
