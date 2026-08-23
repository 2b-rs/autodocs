#!/usr/bin/env python3
"""Read-only pre-integration checkout hygiene check (Task 0044-14).

This check protects integrations from state that Git history cannot reveal. It
inspects every registered worktree sharing a repository common directory and
fails when:

* the integration worktree index differs from its `HEAD`;
* another worktree still has a staged tree after one bounded re-sample (a
  foreign staged tree); or
* tracked files in the worktree checking out `main` differ from its index; or
* a symbolic-branch worktree still has the index and files of the immediately
  preceding reflog tip after its branch ref advanced. This is the stale
  checkout signature produced by `git update-ref` on a checked-out branch.

The checker never writes files, refs, indexes, or object data. A persistent
foreign staged finding includes its index mtime and age; it remains blocking.
The checker reports the stale signature rather than claiming to prove a
particular command was used: the same observable state could be produced by an
equivalent low-level ref move. The required integration procedure decides
recovery.

Usage:
    python3 _src/tools/check_integration_hygiene.py --repo <worktree> [--json]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Optional

REPORT_SCHEMA = "integration-hygiene-report@v1"
FOREIGN_STAGED_RESAMPLE_SECONDS = 2.0


class GitError(RuntimeError):
    """A required read-only Git query failed."""


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if check and proc.returncode:
        raise GitError(f"git {' '.join(args)} failed ({proc.returncode}): {proc.stderr.strip()}")
    return proc


def _worktree_paths(repo: Path) -> list[Path]:
    output = _git(repo, "worktree", "list", "--porcelain").stdout
    paths: list[Path] = []
    for line in output.splitlines():
        if line.startswith("worktree "):
            paths.append(Path(line.removeprefix("worktree ")).resolve())
    if not paths:
        raise GitError("git worktree list returned no worktrees")
    return paths


def _symbolic_branch(repo: Path) -> Optional[str]:
    proc = _git(repo, "symbolic-ref", "-q", "--short", "HEAD", check=False)
    return proc.stdout.strip() if proc.returncode == 0 else None


def _index_equals(repo: Path, treeish: str) -> bool:
    return _git(repo, "diff", "--cached", "--quiet", treeish, check=False).returncode == 0


def _worktree_equals_index(repo: Path) -> bool:
    return _git(repo, "diff", "--quiet", check=False).returncode == 0


def _index_path(repo: Path) -> Path:
    path = Path(_git(repo, "rev-parse", "--git-path", "index").stdout.strip())
    return path if path.is_absolute() else (repo / path).resolve()


def _index_mtime(repo: Path) -> float:
    path = _index_path(repo)
    try:
        return path.stat().st_mtime
    except OSError as error:
        raise GitError(f"cannot stat index {path}: {error}") from error


def _previous_reflog_tip(repo: Path, branch: str) -> Optional[str]:
    tips = [
        line.strip()
        for line in _git(repo, "reflog", "show", "--format=%H", "-n", "2", branch, check=False).stdout.splitlines()
        if line.strip()
    ]
    return tips[1] if len(tips) == 2 else None


@dataclass(frozen=True)
class Finding:
    code: str
    worktree: str
    detail: str
    index_age_seconds: Optional[float] = None
    index_mtime_utc: Optional[str] = None
    resample_delay_seconds: Optional[float] = None


@dataclass(frozen=True)
class WorktreeState:
    path: str
    head: str
    branch: Optional[str]
    index_equals_head: bool
    worktree_equals_index: bool


@dataclass(frozen=True)
class HygieneReport:
    schema: str
    integration_worktree: str
    root_worktree: str
    worktrees: list[WorktreeState]
    findings: list[Finding]

    @property
    def ok(self) -> bool:
        return not self.findings

    def to_dict(self) -> dict:
        return {
            "schema": self.schema,
            "integration_worktree": self.integration_worktree,
            "root_worktree": self.root_worktree,
            "ok": self.ok,
            "worktrees": [asdict(state) for state in self.worktrees],
            "findings": [
                {key: value for key, value in asdict(finding).items() if value is not None}
                for finding in self.findings
            ],
        }


def check_integration_hygiene(
    repo: Path | str,
    *,
    foreign_resample_delay_seconds: float = FOREIGN_STAGED_RESAMPLE_SECONDS,
    sleeper: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.time,
) -> HygieneReport:
    """Inspect all registered worktrees without changing repository state."""
    if foreign_resample_delay_seconds < 0:
        raise ValueError("foreign re-sample delay must not be negative")
    integration = Path(repo).resolve()
    paths = _worktree_paths(integration)
    if integration not in paths:
        raise GitError(f"integration worktree {integration} is not registered")

    states: list[WorktreeState] = []
    findings: list[Finding] = []
    foreign_staged_candidates: list[Path] = []
    for path in paths:
        if not path.exists():
            findings.append(Finding("WORKTREE_UNAVAILABLE", str(path), "registered worktree path is absent"))
            continue
        head = _git(path, "rev-parse", "--verify", "HEAD^{commit}").stdout.strip()
        branch = _symbolic_branch(path)
        index_equals_head = _index_equals(path, "HEAD")
        worktree_equals_index = _worktree_equals_index(path)
        states.append(WorktreeState(str(path), head, branch, index_equals_head, worktree_equals_index))

        if path == integration and not index_equals_head:
            findings.append(Finding("INDEX_NOT_HEAD", str(path), "integration index differs from HEAD"))
        elif path != integration and not index_equals_head:
            foreign_staged_candidates.append(path)

        if branch == "main" and not worktree_equals_index:
            findings.append(
                Finding(
                    "MAIN_WORKTREE_DIRTY",
                    str(path),
                    "worktree checking out main has tracked files that differ from its index",
                )
            )

        previous = _previous_reflog_tip(path, branch) if branch else None
        if (
            branch
            and previous
            and not index_equals_head
            and worktree_equals_index
            and _index_equals(path, previous)
        ):
            findings.append(
                Finding(
                    "STALE_AFTER_REF_MOVE",
                    str(path),
                    f"branch {branch} HEAD advanced while index and worktree still match previous reflog tip {previous}",
                )
            )

    if foreign_staged_candidates:
        sleeper(foreign_resample_delay_seconds)
        for path in foreign_staged_candidates:
            if not path.exists():
                findings.append(
                    Finding("WORKTREE_UNAVAILABLE", str(path), "registered worktree path disappeared during re-sample")
                )
                continue
            if _index_equals(path, "HEAD"):
                continue
            index_mtime = _index_mtime(path)
            index_age_seconds = round(max(0.0, clock() - index_mtime), 3)
            index_mtime_utc = (
                datetime.fromtimestamp(index_mtime, timezone.utc)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z")
            )
            findings.append(
                Finding(
                    "FOREIGN_STAGED_TREE",
                    str(path),
                    (
                        "foreign worktree index still differs from HEAD after "
                        f"{foreign_resample_delay_seconds:.3f}s re-sample; "
                        f"index age {index_age_seconds:.3f}s; index mtime {index_mtime_utc}"
                    ),
                    index_age_seconds=index_age_seconds,
                    index_mtime_utc=index_mtime_utc,
                    resample_delay_seconds=foreign_resample_delay_seconds,
                )
            )

    return HygieneReport(REPORT_SCHEMA, str(integration), str(paths[0]), states, findings)


def _render_text(report: HygieneReport) -> str:
    lines = [f"integration hygiene: {'PASS' if report.ok else 'FAIL'}"]
    lines.append(f"integration worktree: {report.integration_worktree}")
    lines.append(f"registered worktrees: {len(report.worktrees)}")
    for finding in report.findings:
        lines.append(f"{finding.code}: {finding.worktree}: {finding.detail}")
    return "\n".join(lines)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="registered integration worktree")
    parser.add_argument("--json", action="store_true", help="emit integration-hygiene-report@v1 JSON")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        report = check_integration_hygiene(args.repo)
    except GitError as error:
        print(f"integration hygiene: ERROR: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(_render_text(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
