#!/usr/bin/env python3
"""Publish one assigned item branch with fail-closed Git guards.

The command deliberately accepts only an already-configured remote *name*.
It never discovers credentials, chooses an identity, infers assignment or
review authority, force-updates a protected ref, or changes the worktree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import signal
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


SCHEMA = "item-branch-publication-outcome@v1"
ITEM_RE = re.compile(r"^[0-9]{4}(?:-[0-9]{2}(?:\.[0-9]{2})?)?$")
REMOTE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
HEX_RE = re.compile(r"^[0-9a-f]+$")
PROTECTED_EXACT = {
    "HEAD",
    "develop",
    "development",
    "gh-pages",
    "main",
    "master",
    "prod",
    "production",
    "release",
    "trunk",
}
PROTECTED_PREFIXES = ("hotfix/", "release/", "releases/")


@dataclass(frozen=True)
class Config:
    repo: Path
    item: str
    source: str
    target: str
    remote: str
    expected_old: str
    dry_run: bool = False


@dataclass(frozen=True)
class WorktreeSnapshot:
    head: str
    branch: str
    status_sha256: str


class PublicationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class PublicationInterrupted(Exception):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise PublicationError("PUB-ARGUMENT", message)


def _run_git(repo: Path, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _git(repo: Path, args: Sequence[str], code: str, message: str) -> str:
    result = _run_git(repo, args)
    if result.returncode != 0:
        raise PublicationError(code, message)
    return result.stdout.strip()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _outcome(config: Optional[Config] = None) -> Dict[str, Any]:
    return {
        "schema": SCHEMA,
        "ok": False,
        "status": "refused",
        "code": "PUB-UNKNOWN",
        "item": config.item if config else None,
        "source": config.source if config else None,
        "target": config.target if config else None,
        "remote": config.remote if config else None,
        "expected_old": config.expected_old if config else None,
        "observed_old": None,
        "source_oid": None,
        "observed_after": None,
        "dry_run": bool(config.dry_run) if config else False,
        "push_attempted": False,
        "source_worktree_preserved": None,
        "message": "publication did not complete",
        "recovery": {
            "action": "inspect_refusal",
            "expected_old": config.expected_old if config else None,
        },
    }


def _ref_name(target: str) -> str:
    return "refs/heads/" + target


def _is_protected(target: str) -> bool:
    lowered = target.lower()
    return lowered in {value.lower() for value in PROTECTED_EXACT} or lowered.startswith(
        tuple(value.lower() for value in PROTECTED_PREFIXES)
    )


def _snapshot(repo: Path) -> WorktreeSnapshot:
    head = _git(repo, ["rev-parse", "--verify", "HEAD"], "PUB-REPO-INVALID", "HEAD is unavailable")
    branch = _git(
        repo,
        ["symbolic-ref", "--quiet", "--short", "HEAD"],
        "PUB-CHECKOUT-DETACHED",
        "repository HEAD is detached",
    )
    status = _git(
        repo,
        ["status", "--porcelain=v1", "--untracked-files=all"],
        "PUB-REPO-INVALID",
        "repository status is unavailable",
    )
    return WorktreeSnapshot(head=head, branch=branch, status_sha256=_sha256(status))


def _push_url(repo: Path, remote: str) -> str:
    listed = _run_git(repo, ["remote"])
    if listed.returncode != 0:
        raise PublicationError("PUB-REMOTE-MISSING", "remote inventory is unavailable")
    names = [line for line in listed.stdout.splitlines() if line]
    if remote not in names:
        raise PublicationError("PUB-REMOTE-MISSING", "named remote does not exist")
    urls = _run_git(repo, ["remote", "get-url", "--push", "--all", remote])
    if urls.returncode != 0:
        raise PublicationError("PUB-REMOTE-MISSING", "named remote has no push URL")
    values = [line for line in urls.stdout.splitlines() if line]
    if len(values) != 1:
        raise PublicationError("PUB-REMOTE-AMBIGUOUS", "named remote must resolve to exactly one push URL")
    return values[0]


def _remote_oid(repo: Path, push_url: str, target: str) -> Optional[str]:
    result = _run_git(repo, ["ls-remote", "--refs", "--", push_url, _ref_name(target)])
    if result.returncode != 0:
        raise PublicationError("PUB-REMOTE-QUERY", "remote target could not be queried")
    lines = [line for line in result.stdout.splitlines() if line]
    if not lines:
        return None
    if len(lines) != 1:
        raise PublicationError("PUB-REMOTE-AMBIGUOUS", "remote target query returned multiple exact refs")
    fields = lines[0].split()
    if len(fields) != 2 or fields[1] != _ref_name(target) or not HEX_RE.fullmatch(fields[0]):
        raise PublicationError("PUB-REMOTE-AMBIGUOUS", "remote target response was not an exact branch ref")
    return fields[0]


def _validate_static(config: Config) -> Tuple[WorktreeSnapshot, str, str, str, Optional[str]]:
    repo = config.repo.resolve()
    if not repo.is_dir():
        raise PublicationError("PUB-REPO-INVALID", "repository path is not a directory")
    inside = _run_git(repo, ["rev-parse", "--is-inside-work-tree"])
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        raise PublicationError("PUB-REPO-INVALID", "repository path is not a Git worktree")

    if not ITEM_RE.fullmatch(config.item):
        raise PublicationError("PUB-ITEM-INVALID", "assigned item is not a canonical item ID")
    if _is_protected(config.target):
        raise PublicationError("PUB-TARGET-PROTECTED", "protected target refs are never publishable")
    if not ITEM_RE.fullmatch(config.target):
        raise PublicationError("PUB-TARGET-NONCANONICAL", "target must be a canonical bare item branch")
    if config.target != config.item:
        raise PublicationError("PUB-TARGET-MISMATCH", "target does not match assigned item")
    if config.source != config.item:
        raise PublicationError("PUB-SOURCE-MISMATCH", "source does not match assigned item")
    if not REMOTE_RE.fullmatch(config.remote):
        raise PublicationError("PUB-REMOTE-INVALID", "remote must be an explicit configured remote name")

    before = _snapshot(repo)
    if before.branch != config.source:
        raise PublicationError("PUB-CHECKOUT-MISMATCH", "checked-out branch does not match explicit source")
    status = _git(
        repo,
        ["status", "--porcelain=v1", "--untracked-files=all"],
        "PUB-REPO-INVALID",
        "repository status is unavailable",
    )
    if status:
        raise PublicationError("PUB-WORKTREE-DIRTY", "tracked, staged, or untracked candidate state is present")

    source_oid = _git(
        repo,
        ["rev-parse", "--verify", config.source + "^{commit}"],
        "PUB-SOURCE-MISSING",
        "source branch does not resolve to a commit",
    )
    if before.head != source_oid:
        raise PublicationError("PUB-CHECKOUT-MISMATCH", "checked-out HEAD does not equal source branch")
    if not HEX_RE.fullmatch(source_oid):
        raise PublicationError("PUB-SOURCE-MISSING", "source object ID is malformed")

    if len(config.expected_old) != len(source_oid) or not HEX_RE.fullmatch(config.expected_old):
        raise PublicationError("PUB-EXPECTED-INVALID", "expected old value must be one full lowercase object ID")
    zero_oid = "0" * len(source_oid)
    if config.expected_old != zero_oid:
        expected_object = _run_git(repo, ["cat-file", "-e", config.expected_old + "^{commit}"])
        if expected_object.returncode != 0:
            raise PublicationError("PUB-EXPECTED-INVALID", "expected old commit is unavailable locally")

    push_url = _push_url(repo, config.remote)
    observed_old = _remote_oid(repo, push_url, config.target)
    if observed_old == source_oid:
        return before, source_oid, zero_oid, push_url, observed_old
    expected_observed = None if config.expected_old == zero_oid else config.expected_old
    if observed_old != expected_observed:
        raise PublicationError("PUB-EXPECTED-STALE", "remote target differs from expected old object")
    if config.expected_old != zero_oid:
        ancestry = _run_git(repo, ["merge-base", "--is-ancestor", config.expected_old, source_oid])
        if ancestry.returncode != 0:
            raise PublicationError("PUB-NON-FAST-FORWARD", "source is not a fast-forward of expected old object")
    return before, source_oid, zero_oid, push_url, observed_old


def _preserved(repo: Path, before: WorktreeSnapshot) -> bool:
    try:
        return _snapshot(repo) == before
    except PublicationError:
        return False


def publish(
    config: Config,
    before_push: Optional[Callable[[], None]] = None,
) -> Dict[str, Any]:
    outcome = _outcome(config)
    before: Optional[WorktreeSnapshot] = None
    push_url: Optional[str] = None
    try:
        before, source_oid, zero_oid, push_url, observed_old = _validate_static(config)
        outcome.update(
            {
                "observed_old": observed_old,
                "source_oid": source_oid,
            }
        )
        if observed_old == source_oid:
            outcome.update(
                {
                    "ok": True,
                    "status": "already_published",
                    "code": "PUB-ALREADY-PUBLISHED",
                    "message": "remote target already equals source commit",
                    "source_worktree_preserved": _preserved(config.repo, before),
                    "recovery": {"action": "none", "expected_old": source_oid},
                }
            )
            return outcome
        if config.dry_run:
            outcome.update(
                {
                    "ok": True,
                    "status": "dry_run",
                    "code": "PUB-DRY-RUN",
                    "message": "all guards passed; no push attempted",
                    "source_worktree_preserved": _preserved(config.repo, before),
                    "recovery": {"action": "rerun_without_dry_run", "expected_old": config.expected_old},
                }
            )
            return outcome

        if before_push is not None:
            before_push()
        if not _preserved(config.repo, before):
            outcome.update(
                {
                    "status": "refused",
                    "code": "PUB-LOCAL-RACE",
                    "message": "source HEAD, branch, or worktree changed after preflight",
                    "source_worktree_preserved": False,
                    "recovery": {"action": "inspect_local_state_and_restart", "expected_old": config.expected_old},
                }
            )
            return outcome
        outcome["push_attempted"] = True
        lease_expectation = "" if config.expected_old == zero_oid else config.expected_old
        push = _run_git(
            config.repo,
            [
                "push",
                "--porcelain",
                "--force-with-lease=" + _ref_name(config.target) + ":" + lease_expectation,
                "--",
                config.remote,
                source_oid + ":" + _ref_name(config.target),
            ],
        )
        try:
            observed_after = _remote_oid(config.repo, push_url, config.target)
        except PublicationError:
            observed_after = None
        outcome["observed_after"] = observed_after
        outcome["push_result_sha256"] = _sha256(push.stdout + "\0" + push.stderr)
        outcome["push_returncode"] = push.returncode
        outcome["source_worktree_preserved"] = _preserved(config.repo, before)

        if observed_after == source_oid:
            outcome.update(
                {
                    "ok": True,
                    "status": "published",
                    "code": "PUB-OK",
                    "message": "remote target equals source commit after CAS-bound push",
                    "recovery": {"action": "none", "expected_old": source_oid},
                }
            )
            return outcome

        expected_observed = None if config.expected_old == zero_oid else config.expected_old
        if observed_after != expected_observed:
            outcome.update(
                {
                    "status": "refused",
                    "code": "PUB-CAS-LOST",
                    "message": "remote target changed before the lease-bound push completed",
                    "recovery": {
                        "action": "inspect_remote_and_repin",
                        "expected_old": observed_after,
                    },
                }
            )
            return outcome
        outcome.update(
            {
                "status": "failed",
                "code": "PUB-PUSH-FAILED",
                "message": "push failed and remote target remains unchanged",
                "recovery": {"action": "retry_same_command", "expected_old": config.expected_old},
            }
        )
        return outcome
    except PublicationInterrupted as exc:
        outcome.update(
            {
                "status": "interrupted",
                "code": "PUB-INTERRUPTED",
                "message": str(exc) or "publication interrupted before push",
                "source_worktree_preserved": _preserved(config.repo, before) if before else None,
                "recovery": {"action": "query_remote_then_retry", "expected_old": config.expected_old},
            }
        )
        return outcome
    except KeyboardInterrupt:
        outcome.update(
            {
                "status": "interrupted",
                "code": "PUB-INTERRUPTED",
                "message": "publication interrupted",
                "source_worktree_preserved": _preserved(config.repo, before) if before else None,
                "recovery": {"action": "query_remote_then_retry", "expected_old": config.expected_old},
            }
        )
        return outcome
    except PublicationError as exc:
        outcome.update({"status": "refused", "code": exc.code, "message": exc.message})
        if before is not None:
            outcome["source_worktree_preserved"] = _preserved(config.repo, before)
        if push_url is None and REMOTE_RE.fullmatch(config.remote):
            try:
                push_url = _push_url(config.repo, config.remote)
            except PublicationError:
                push_url = None
        if push_url is not None:
            try:
                outcome["observed_old"] = _remote_oid(config.repo, push_url, config.target)
            except PublicationError:
                pass
        return outcome


def _parser() -> JsonArgumentParser:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("--repo")
    parser.add_argument("--item")
    parser.add_argument("--source")
    parser.add_argument("--target")
    parser.add_argument("--remote")
    parser.add_argument("--expected-old")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _argument_outcome(message: str) -> Dict[str, Any]:
    outcome = _outcome()
    outcome.update({"code": "PUB-ARGUMENT", "message": message})
    return outcome


def _install_signal_handlers() -> None:
    def interrupted(signum: int, _frame: Any) -> None:
        raise PublicationInterrupted("publication interrupted by signal " + str(signum))

    signal.signal(signal.SIGTERM, interrupted)


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = _parser().parse_args(argv)
        missing = [
            name
            for name in ("repo", "item", "source", "target", "remote", "expected_old")
            if not getattr(args, name)
        ]
        if missing:
            raise PublicationError("PUB-ARGUMENT", "missing required arguments: " + ", ".join(missing))
        config = Config(
            repo=Path(args.repo),
            item=args.item,
            source=args.source,
            target=args.target,
            remote=args.remote,
            expected_old=args.expected_old,
            dry_run=args.dry_run,
        )
        _install_signal_handlers()
        outcome = publish(config)
    except PublicationError as exc:
        outcome = _argument_outcome(exc.message) if exc.code == "PUB-ARGUMENT" else _outcome()
        outcome.update({"code": exc.code, "message": exc.message})
    print(json.dumps(outcome, sort_keys=True, separators=(",", ":")))
    return 0 if outcome.get("ok") else (3 if outcome.get("status") in {"failed", "interrupted"} else 2)


if __name__ == "__main__":
    raise SystemExit(main())
