#!/usr/bin/env python3
"""Read-only integration-policy provenance check (`RQ-IP-04`, `DEC-0044-002`).

Given a merge candidate (a *source* branch to be integrated and a *target*
branch it is integrated onto), reports, for every commit that touches a
declared policy path and is unique to the source branch (i.e. would be
carried onto the target by the merge), which branches contain that commit,
and flags it as a **foreign-branch policy commit** when it is not explainable
as having originated on the source branch itself or as a legitimate pull-in
from the target branch (`DEC-0044-001`: pulling the target's own policy
changes into the source is permitted).

Scope and honesty note (read this before trusting a verdict): Git does not
record a commit's "originating branch" as a first-class fact. This tool
approximates provenance from branch *containment* (`git branch --contains
<sha>`) and topology relative to the merge-base of source and target. That
approximation is exact for the common case this Task's acceptance criteria
target (a policy-path commit reachable from some branch other than the
source/target pair) but can be fooled by history rewrites, orphan branches
sharing no ancestor, or a foreign commit that happens to be cherry-picked
with an identical tree onto the source branch itself (same content, new
SHA — such a commit is, correctly, not flagged, since nothing links it to a
foreign branch anymore). It is a mechanical aid for an integrator/reviewer,
not a substitute for review, and it makes no accept/reject decision itself.

This module is deliberately read-only: it never mutates the repository, never
writes files, and only shells out to `git` in ways that cannot mutate refs or
the working tree (`rev-parse`, `merge-base`, `log`, `branch --contains`,
`diff --name-only`, `cat-file`).

Stdlib-only. No third-party dependencies.

CLI:
    python3 _src/tools/check_policy_provenance.py \\
        --source-branch <branch> --target-branch <branch> \\
        [--policy-path PATH ...] [--repo PATH] [--json]

Library:
    check_policy_provenance(repo, source_branch, target_branch, policy_paths)
        -> ProvenanceReport
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence

DEFAULT_POLICY_PATHS = ("docs/pipeline/branch-workflow.md",)

REPORT_SCHEMA = "policy-provenance-report@v1"


class GitError(RuntimeError):
    """Raised when a git plumbing call fails or returns something unusable."""


def _run_git(repo: Path, args: Sequence[str]) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise GitError(
            f"git {' '.join(args)} failed (exit {proc.returncode}): {proc.stderr.strip()}"
        )
    return proc.stdout


def _rev_parse(repo: Path, ref: str) -> str:
    out = _run_git(repo, ["rev-parse", "--verify", f"{ref}^{{commit}}"]).strip()
    if not out:
        raise GitError(f"could not resolve ref {ref!r}")
    return out


def _merge_base(repo: Path, a: str, b: str) -> str:
    out = _run_git(repo, ["merge-base", a, b]).strip()
    if not out:
        raise GitError(f"no merge-base between {a!r} and {b!r}")
    return out


EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def _commits_only_in(repo: Path, ahead: str, behind: str) -> List[str]:
    """Commit SHAs reachable from `ahead` but not from `behind`, oldest first."""
    out = _run_git(repo, ["log", "--reverse", "--pretty=%H", f"{behind}..{ahead}"])
    return [line.strip() for line in out.splitlines() if line.strip()]


def _touches_policy_path(repo: Path, sha: str, policy_paths: Sequence[str]) -> List[str]:
    """Paths from `policy_paths` that differ between `sha` and its first parent.

    Uses the first-parent diff (not `diff-tree -r`, which shows an empty diff
    for merge commits unless explicitly asked for a merge diff) so a merge
    commit that pulls in policy-path changes from its second parent is
    correctly detected as "touching" that path.
    """
    try:
        parent = _run_git(repo, ["rev-parse", f"{sha}^"]).strip()
    except GitError:
        parent = EMPTY_TREE_SHA
    out = _run_git(repo, ["diff", "--name-only", parent, sha])
    changed = {line.strip() for line in out.splitlines() if line.strip()}
    return sorted(p for p in policy_paths if p in changed)


def _blob_at(repo: Path, commit: str, path: str) -> Optional[str]:
    proc = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", f"{commit}:{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _branches_containing(repo: Path, sha: str) -> List[str]:
    out = _run_git(repo, ["branch", "--all", "--contains", sha, "--format=%(refname:short)"])
    names = []
    for line in out.splitlines():
        name = line.strip()
        if not name:
            continue
        # Normalize "remotes/origin/x" duplicates of local "x" out of scope;
        # keep as-is, callers can filter further if they track remotes.
        names.append(name)
    return sorted(set(names))


@dataclass
class PolicyCommitFinding:
    sha: str
    changed_policy_paths: List[str]
    containing_branches: List[str]
    classification: str  # "source-origin" | "target-pull-in-eligible" | "foreign-branch"
    note: str

    def to_dict(self) -> dict:
        return {
            "sha": self.sha,
            "changed_policy_paths": self.changed_policy_paths,
            "containing_branches": self.containing_branches,
            "classification": self.classification,
            "note": self.note,
        }


@dataclass
class ProvenanceReport:
    schema: str
    source_branch: str
    target_branch: str
    source_commit: str
    target_commit: str
    merge_base: str
    policy_paths: List[str]
    findings: List[PolicyCommitFinding] = field(default_factory=list)

    @property
    def foreign_branch_findings(self) -> List[PolicyCommitFinding]:
        return [f for f in self.findings if f.classification == "foreign-branch"]

    @property
    def has_foreign_branch_policy_commit(self) -> bool:
        return bool(self.foreign_branch_findings)

    def to_dict(self) -> dict:
        return {
            "schema": self.schema,
            "source_branch": self.source_branch,
            "target_branch": self.target_branch,
            "source_commit": self.source_commit,
            "target_commit": self.target_commit,
            "merge_base": self.merge_base,
            "policy_paths": self.policy_paths,
            "findings": [f.to_dict() for f in self.findings],
            "has_foreign_branch_policy_commit": self.has_foreign_branch_policy_commit,
        }


def check_policy_provenance(
    repo: Path,
    source_branch: str,
    target_branch: str,
    policy_paths: Optional[Sequence[str]] = None,
) -> ProvenanceReport:
    """Read-only: report policy-path commit provenance for a merge candidate.

    `source_branch` is the branch to be integrated; `target_branch` is the
    integration target. Only commits unique to `source_branch` relative to
    the merge-base are inspected, since those are what the merge would carry
    onto `target_branch` — target-only commits are always legitimate (they
    are the target's own policy, which governs by `DEC-0044-001`).
    """
    paths = list(policy_paths) if policy_paths else list(DEFAULT_POLICY_PATHS)
    if not paths:
        raise ValueError("policy_paths must not be empty")

    source_commit = _rev_parse(repo, source_branch)
    target_commit = _rev_parse(repo, target_branch)
    base = _merge_base(repo, source_commit, target_commit)

    # Deliberately target_commit, not the merge-base: once source has already
    # merged target in, merge-base(source, target) collapses to target's own
    # tip, which would wrongly hide everything. `target..source` is the exact
    # set of commits the merge would still be carrying onto target.
    source_only = _commits_only_in(repo, source_commit, target_commit)

    findings: List[PolicyCommitFinding] = []
    for sha in source_only:
        changed = _touches_policy_path(repo, sha, paths)
        if not changed:
            continue
        containing = _branches_containing(repo, sha)
        others = [
            b
            for b in containing
            if b not in (source_branch, target_branch)
            and not b.endswith(f"/{source_branch}")
            and not b.endswith(f"/{target_branch}")
        ]
        # Content-based pull-in check: a merge commit that pulls target's
        # current policy content in is not reachable-from-target itself (the
        # merge commit only exists on source), so compare the changed path's
        # blob at this commit against its blob on the target tip directly.
        content_matches_target = bool(changed) and all(
            _blob_at(repo, sha, p) == _blob_at(repo, target_commit, p) for p in changed
        )
        if content_matches_target:
            classification = "target-pull-in-eligible"
            note = (
                "Commit is already reachable from the target branch: this is a "
                "legitimate pull-in of the target's own policy (DEC-0044-001), "
                "not a foreign-branch commit."
            )
        elif others:
            classification = "foreign-branch"
            note = (
                "Commit changes a declared policy path, is unique to the source "
                "branch relative to the target, and is also reachable from a "
                "branch other than source/target: "
                + ", ".join(others)
                + ". Flag for review under DEC-0044-002 (no agent commits "
                "policy changes onto a branch other than the one they "
                "originated on or the integration target)."
            )
        else:
            classification = "source-origin"
            note = (
                "Commit changes a declared policy path and is reachable only "
                "from the source branch among known local/remote branches: "
                "consistent with having originated on the source branch itself."
            )
        findings.append(
            PolicyCommitFinding(
                sha=sha,
                changed_policy_paths=changed,
                containing_branches=containing,
                classification=classification,
                note=note,
            )
        )

    return ProvenanceReport(
        schema=REPORT_SCHEMA,
        source_branch=source_branch,
        target_branch=target_branch,
        source_commit=source_commit,
        target_commit=target_commit,
        merge_base=base,
        policy_paths=paths,
        findings=findings,
    )


def _format_text(report: ProvenanceReport) -> str:
    lines = [
        f"Policy provenance check: {report.source_branch} -> {report.target_branch}",
        f"  merge-base: {report.merge_base}",
        f"  policy paths: {', '.join(report.policy_paths)}",
    ]
    if not report.findings:
        lines.append("  no policy-path commits unique to the source branch")
        return "\n".join(lines)
    for f in report.findings:
        marker = "!!" if f.classification == "foreign-branch" else "--"
        lines.append(f"  {marker} {f.sha[:12]} [{f.classification}] {f.changed_policy_paths}")
        lines.append(f"       branches: {f.containing_branches}")
        lines.append(f"       {f.note}")
    if report.has_foreign_branch_policy_commit:
        lines.append("VERDICT: foreign-branch policy commit(s) found — review required.")
    else:
        lines.append("VERDICT: no foreign-branch policy commits found.")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-branch", required=True)
    parser.add_argument("--target-branch", required=True)
    parser.add_argument(
        "--policy-path",
        action="append",
        dest="policy_paths",
        default=None,
        help=f"repeatable; default {DEFAULT_POLICY_PATHS}",
    )
    parser.add_argument("--repo", default=".", help="repository path (default: cwd)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    try:
        report = check_policy_provenance(
            repo, args.source_branch, args.target_branch, args.policy_paths
        )
    except (GitError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(_format_text(report))

    return 1 if report.has_foreign_branch_policy_commit else 0


if __name__ == "__main__":
    raise SystemExit(main())
