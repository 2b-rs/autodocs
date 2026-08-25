#!/usr/bin/env python3
"""Shared byte-path policy for the DEC-0044-021 hygiene exception."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

AGENT_MEMORY_PREFIX = b"logs/agent-memory/"


def split_nul_paths(payload: bytes) -> tuple[bytes, ...]:
    """Parse Git ``-z`` path output and reject malformed non-terminated data."""
    if not payload:
        return ()
    if not payload.endswith(b"\0"):
        raise ValueError("NUL-delimited Git path output is not terminated")
    paths = tuple(payload[:-1].split(b"\0"))
    if any(not path for path in paths):
        raise ValueError("NUL-delimited Git path output contains an empty path")
    return paths


def is_agent_memory_child(path: bytes) -> bool:
    """Return true only for an exact, case-sensitive child of agent-memory/."""
    return path.startswith(AGENT_MEMORY_PREFIX) and len(path) > len(AGENT_MEMORY_PREFIX)


@dataclass(frozen=True)
class RootDivergence:
    paths: tuple[bytes, ...]
    allowed_memory_paths: tuple[bytes, ...]
    blocking_paths: tuple[bytes, ...]

    @property
    def is_clean(self) -> bool:
        return not self.paths

    @property
    def is_allowed_memory_only(self) -> bool:
        return bool(self.paths) and not self.blocking_paths


def classify_unstaged_paths(paths: Iterable[bytes]) -> RootDivergence:
    ordered = tuple(paths)
    allowed = tuple(path for path in ordered if is_agent_memory_child(path))
    blocking = tuple(path for path in ordered if not is_agent_memory_child(path))
    return RootDivergence(ordered, allowed, blocking)


def candidate_memory_overlap(
    allowed_memory_paths: Iterable[bytes], candidate_changed_paths: Iterable[bytes]
) -> tuple[bytes, ...]:
    """Return deterministic exact-path overlap; byte equality is irrelevant."""
    candidate = set(candidate_changed_paths)
    return tuple(path for path in allowed_memory_paths if path in candidate)


def display_path(path: bytes) -> str:
    """Render arbitrary Git path bytes without embedding control characters."""
    return path.decode("utf-8", "backslashreplace").encode("unicode_escape").decode("ascii")
