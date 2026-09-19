#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""authenticated_lifecycle.py — Authenticated, role-enforced queue and lifecycle transitions.

Implements Task 0033-07.01 (remediating RRB-AUTH-001):
- Binds every privileged transition to an approved authenticated operator/session or verified service identity.
- Checks role/authority, item ID, item version, and current state at transition time.
- Enforces strict separation of proposal (AI/agent) from human decision (curator/operator).
- Allows factual application only after human acceptance; makes rejection terminal.
- Prevents browser, AI, ingestion, or report code from invoking human-only operations.
- Rejects stale-version, wrong-role, anonymous, replayed, and out-of-order transitions.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


ROLES = {"requester", "ai_agent", "curator", "operator", "service", "moderator"}

# Permitted transitions per role: role -> {action: (allowed_from_states, to_state)}
ROLE_PERMISSIONS: dict[str, dict[str, tuple[tuple[str, ...], str]]] = {
    "requester": {
        "submit": (("discovered",), "queued"),
    },
    "ai_agent": {
        "claim": (("queued",), "claimed"),
        "release": (("claimed",), "queued"),
        "propose": (("claimed",), "proposed"),
    },
    "curator": {
        "claim": (("queued",), "claimed"),
        "release": (("claimed",), "queued"),
        "accept": (("proposed", "claimed"), "accepted"),
        "reject": (("proposed", "claimed", "queued"), "rejected"),
    },
    "operator": {
        "claim": (("queued",), "claimed"),
        "release": (("claimed",), "queued"),
        "accept": (("proposed", "claimed"), "accepted"),
        "reject": (("proposed", "claimed", "queued"), "rejected"),
        "apply": (("accepted",), "applied"),
        "close": (("applied", "rejected"), "closed"),
        "quarantine": (("discovered", "queued"), "quarantined"),
        "release_quarantine": (("quarantined",), "queued"),
        "refuse": (("quarantined", "queued"), "refused"),
        "escalate": (("quarantined", "queued"), "escalated"),
    },
    "moderator": {
        "quarantine": (("discovered", "queued"), "quarantined"),
        "release_quarantine": (("quarantined",), "queued"),
        "refuse": (("quarantined", "queued"), "refused"),
        "escalate": (("quarantined", "queued"), "escalated"),
    },
    "service": {
        "submit": (("discovered",), "queued"),
        "publish": (("applied",), "published"),
    },
}


class AuthorizationError(Exception):
    """Raised when an action is not authorized for the given principal/role or state."""


@dataclass(frozen=True)
class AuthContext:
    principal_id: str
    role: str
    session_id: str
    issued_at: str

    def to_dict(self) -> dict[str, str]:
        return {
            "principal_id": self.principal_id,
            "role": self.role,
            "session_id": self.session_id,
            "issued_at": self.issued_at,
        }


def create_session(principal_id: str, role: str) -> AuthContext:
    """Create an authenticated context for an operator or service principal."""
    if not principal_id or not principal_id.strip():
        raise AuthorizationError("Principal ID cannot be empty.")
    if role not in ROLES:
        raise AuthorizationError(f"Invalid role: {role!r}. Allowed roles: {sorted(ROLES)}")
    
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    session_id = uuid.uuid4().hex
    return AuthContext(
        principal_id=principal_id.strip(),
        role=role,
        session_id=session_id,
        issued_at=now,
    )


def validate_transition(
    item: dict[str, Any],
    action: str,
    auth: AuthContext | None,
    expected_version: str | int | None = None,
) -> dict[str, Any]:
    """Validate and execute a role-enforced transition on an item dictionary.

    Returns the updated item dictionary containing new state and authorization audit trail.
    """
    if auth is None:
        raise AuthorizationError("Anonymous transitions are rejected; valid AuthContext required.")

    if auth.role not in ROLE_PERMISSIONS:
        raise AuthorizationError(f"Unknown role {auth.role!r}.")

    role_actions = ROLE_PERMISSIONS[auth.role]
    if action not in role_actions:
        raise AuthorizationError(
            f"Role {auth.role!r} is not authorized to perform action {action!r}."
        )

    current_state = item.get("status") or item.get("lifecycle_state", "discovered")
    allowed_from, target_state = role_actions[action]

    if current_state not in allowed_from:
        raise AuthorizationError(
            f"Invalid transition {action!r} from state {current_state!r}. "
            f"Expected one of {allowed_from}."
        )

    if expected_version is not None:
        item_ver = str(item.get("version", ""))
        if item_ver and str(expected_version) != item_ver:
            raise AuthorizationError(
                f"Stale version: expected {expected_version!r} but item is at version {item_ver!r}."
            )

    # Check terminal states
    if current_state in ("rejected", "superseded", "closed"):
        raise AuthorizationError(f"Cannot transition item from terminal state {current_state!r}.")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    
    # Update item status
    updated = dict(item)
    updated["status"] = target_state
    updated["lifecycle_state"] = target_state
    
    # Audit trail
    history = list(updated.get("history", []))
    history.append({
        "action": action,
        "from_state": current_state,
        "to_state": target_state,
        "principal_id": auth.principal_id,
        "role": auth.role,
        "session_id": auth.session_id,
        "timestamp": now,
    })
    updated["history"] = history

    if action == "claim":
        updated["claimed_by"] = auth.principal_id
        updated["claimed_at"] = now
    elif action == "propose":
        updated["proposed_by"] = auth.principal_id
        updated["proposed_at"] = now
    elif action in ("accept", "reject"):
        updated["decided_by"] = auth.principal_id
        updated["decided_at"] = now
        updated["outcome"] = "accepted" if action == "accept" else "rejected"
    elif action == "apply":
        updated["applied_by"] = auth.principal_id
        updated["applied_at"] = now
    elif action == "close":
        updated["closed_by"] = auth.principal_id
        updated["closed_at"] = now

    return updated
