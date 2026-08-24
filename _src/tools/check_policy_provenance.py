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

Since the 2026-08-21 management decision recorded at
`2026-08-21T11:20:51+02:00` for `DEC-0044-008`/`DEC-0044-011`, each later
policy-path commit must carry exactly one `Policy-Origin-Branch:` trailer with
a non-empty valid Git branch name naming the branch where the commit originated.
The checker reports a missing or malformed required trailer as a finding and
exits nonzero; it does not require or judge trailers on earlier history. The
trailer records introducer evidence; it does not make an otherwise foreign merge
eligible.

Scope and honesty note (read this before trusting a verdict): Git does not
record a commit's "originating branch" as a first-class fact. Earlier
revisions of this tool tried to approximate provenance from branch
*containment* (`git branch --contains <sha>`) and were repeatedly fooled by
routine repository states this project actually produces (a reviewer's own
detached-HEAD worktree; an old, retained review/Task branch built on top of
source; an old, retained branch sitting at an earlier point on source's own
line) — see `docs/dossiers/0044-01-branch-workflow-prose-scope-review.md` and
the two `[u]` integration-review verdicts beneath Task `0044-01` in
`TODO.md` for the reproduction history. Branch *names* are therefore used
only as an informational annotation in each finding's `containing_branches`
field, never as the classification signal.

**Classification is instead driven purely by the topology of the commit
itself relative to `source_commit`'s own first-parent ("mainline") history**
— the actual, exhaustively enumerated set of relationships a policy-path
commit `sha` (already known, by construction, to be an ancestor-or-equal of
`source_commit` and not reachable from `target_commit`) can have to
`source_commit`:

| Relationship of `sha` to `source_commit` | Classification | Why |
|---|---|---|
| `sha` reachable via `source_commit`'s first-parent chain (authored directly on source, including `sha == source_commit`) | `source-origin` | It is source's own mainline history. Which *other* branches also happen to contain `sha` — a detached worktree, an old review branch built on top, an old branch sitting at an earlier mainline point, or nothing at all if those refs were deleted — is irrelevant: none of that changes where `sha` was actually authored. |
| `sha`'s only path into `source_commit` is through a merge commit, and the merged-in content at the touched policy path(s) matches `target_commit`'s current content | `target-pull-in-eligible` | Legitimate pull-in of the target's own policy (`DEC-0044-001`). |
| `sha`'s only path into `source_commit` is through a merge commit, and the content does **not** match `target_commit` | `foreign-branch` | `sha` was authored on some branch other than source/target and merged in — the `DEC-0044-002` violation shape this tool exists to catch. This holds even if the branch that originally carried `sha` has since been deleted; the merge-commit topology itself is the evidence, not a surviving branch name. |

Note what this table does **not** use as a signal: whether any *other* named
branch/worktree also contains `sha`, and whether that other ref is upstream,
downstream, or unrelated to `source_commit`. Those all failed as decision
signals in practice (see the reproduction history above) precisely because
routine repository hygiene in this project — retaining branches, running
reviews from separate worktrees, chaining Task branches — produces exactly
that shape without any foreign-origin implication. `containing_branches` is
reported for human orientation only.

Residual known limitations (unchanged from earlier revisions): history
rewrites (rebase/filter-repo) invalidate first-parent-chain reasoning same as
any git-log-based tool; a foreign commit cherry-picked with an identical tree
directly onto source (new SHA, no merge involved) is indistinguishable from a
commit genuinely authored on source, and is correctly *not* flagged, since
nothing about that SHA's own history links it to a foreign branch anymore.
It is a mechanical aid for an integrator/reviewer, not a substitute for
review, and it makes no accept/reject decision itself.

Residual known limitation — fast-forward absorption blind spot (`DEC-0044-007`):
this tool's `source-origin` classification cannot distinguish a commit that
was genuinely authored directly on the source branch from a commit that was
authored on an entirely different, foreign branch and then absorbed onto
source's tip via a **fast-forward** (`git merge --ff-only` or `git
update-ref`, i.e. any operation that advances a branch pointer without
creating a merge commit). Both cases produce a plain, single-parent commit
sitting on `source_commit`'s own first-parent chain — topologically there is
nothing left to distinguish them; Git itself does not record "which branch a
commit was first authored on" once no merge commit marks the join. This is
not a hypothetical edge case: fast-forward absorption is a routine, everyday
git operation (this project's own integrator workflow advances `main` this
way), so a foreign commit could in principle enter a source branch through
exactly this path and be silently classified `source-origin` instead of
`foreign-branch`. No purely local-history signal closes this gap; see
`docs/dossiers/0044-01-branch-workflow-prose-scope-review.md` §5 (the third
`[u]` integration-review verdict beneath Task `0044-01` in `TODO.md`, and the
Architect's `DEC-0044-007` disposition of it) for the full reproduction and
analysis. `DEC-0044-007` accepts this as a documented residual limitation of
the mechanical check rather than a defect to code around, and pairs it with a
binding process control instead: `docs/pipeline/branch-workflow.md`
("Integration policy precedence" section) now requires an explicit `--no-ff`
merge commit for any absorption of content from a branch other than an
item's own direct predecessor/successor chain or its own prior tip — so that
when foreign content genuinely is pulled in, it leaves the merge-commit
topology this tool's `target-pull-in-eligible`/`foreign-branch`
classification already relies on, and the blind spot cannot silently fire in
a policy-sanctioned workflow.

This module is deliberately read-only: it never mutates the repository, never
writes files, and only shells out to `git` in ways that cannot mutate refs or
the working tree (`rev-parse`, `merge-base`, `log`, `rev-list --first-parent`,
`branch --contains`, `diff`).

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
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence

DEFAULT_POLICY_PATHS = ("docs/pipeline/branch-workflow.md",)

REPORT_SCHEMA = "policy-provenance-report@v2"
POLICY_ORIGIN_TRAILER = "Policy-Origin-Branch"
POLICY_PROVENANCE_EFFECTIVE_AT = datetime.fromisoformat("2026-08-21T11:20:51+02:00")


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


def _first_parent_chain(repo: Path, commit: str) -> set:
    """SHAs reachable from `commit` by following only first parents.

    This is `source_commit`'s own "mainline": the commit itself plus every
    ancestor reached by always taking the first parent, i.e. exactly the
    commits that were directly authored on (or fast-forwarded onto) the
    source branch's own line, as opposed to pulled in as the *second* (or
    later) parent of a merge commit. This is the sole classification signal
    `check_policy_provenance` uses to decide `source-origin` vs. everything
    else — see the module docstring's relationship table.
    """
    out = _run_git(repo, ["rev-list", "--first-parent", commit])
    return {line.strip() for line in out.splitlines() if line.strip()}


def _parent_count(repo: Path, sha: str) -> int:
    """Number of parents of `sha` (0 for a root commit, >=2 for a merge)."""
    out = _run_git(repo, ["rev-list", "--parents", "-n", "1", sha]).strip()
    tokens = out.split()
    return max(len(tokens) - 1, 0)


def _commit_timestamp(repo: Path, sha: str) -> datetime:
    """Return the commit timestamp used for the non-retroactive trailer rule."""
    value = _run_git(repo, ["show", "-s", "--format=%cI", sha]).strip()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GitError(f"could not parse commit date for {sha}: {value!r}") from exc


def _policy_origin_trailers(repo: Path, sha: str) -> List[str]:
    """Return every exact Policy-Origin-Branch line value, preserving order.

    Parse the commit message directly so duplicate and empty occurrences remain
    observable. Git's ``%(trailers)`` formatter discards an empty occurrence and
    may ignore a syntactically exact trailer line when another paragraph follows
    it, which would turn malformed evidence into an undetectable absence.
    """
    message = _run_git(repo, ["show", "-s", "--format=%B", sha])
    prefix = f"{POLICY_ORIGIN_TRAILER}:"
    return [line[len(prefix) :].strip() for line in message.splitlines() if line.startswith(prefix)]


def _has_valid_policy_origin_trailer(repo: Path, sha: str) -> tuple[bool, Optional[str]]:
    """Validate the exactly-one, non-empty branch-name trailer convention."""
    trailers = _policy_origin_trailers(repo, sha)
    if len(trailers) != 1:
        return False, None
    value = trailers[0]
    proc = subprocess.run(
        ["git", "-C", str(repo), "check-ref-format", "--branch", value],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return (True, value) if proc.returncode == 0 else (False, None)


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
    """Real branch names (local and remote-tracking) containing `sha`.

    `git branch --all --contains` also lists a synthetic `(no branch)` entry
    whenever `sha` is (or is an ancestor of) a **detached HEAD** somewhere —
    including any other local worktree of this same repository checked out
    at or below that commit. That is not a branch, has no name, and proves
    nothing about a foreign branch of origin: a reviewer's own isolated
    worktree, or any other detached checkout of the very same commit, is
    exactly this shape and is routine, policy-sanctioned repository state
    (worktrees/branches are retained, not deleted, after merge). Filter it
    out here so callers never see it as a branch candidate.
    """
    out = _run_git(repo, ["branch", "--all", "--contains", sha, "--format=%(refname:short)"])
    names = []
    for line in out.splitlines():
        name = line.strip()
        if not name:
            continue
        if name == "(no branch)" or (name.startswith("(") and name.endswith(")")):
            # Synthetic git-branch placeholder for a detached HEAD (this
            # repo's or another worktree's), never a real ref. Also guards
            # future synonymous placeholders git may emit in this shape.
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
    policy_origin_branch: Optional[str]
    missing_policy_origin_trailer: bool
    note: str

    def to_dict(self) -> dict:
        return {
            "sha": self.sha,
            "changed_policy_paths": self.changed_policy_paths,
            "containing_branches": self.containing_branches,
            "classification": self.classification,
            "policy_origin_branch": self.policy_origin_branch,
            "missing_policy_origin_trailer": self.missing_policy_origin_trailer,
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

    @property
    def missing_policy_origin_trailer_findings(self) -> List[PolicyCommitFinding]:
        return [f for f in self.findings if f.missing_policy_origin_trailer]

    @property
    def has_missing_policy_origin_trailer(self) -> bool:
        return bool(self.missing_policy_origin_trailer_findings)

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
            "has_missing_policy_origin_trailer": self.has_missing_policy_origin_trailer,
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

    # Computed once: source_commit's own first-parent ("mainline") history —
    # see `_first_parent_chain`'s docstring and the module docstring's
    # relationship table. This, not branch containment, is the sole
    # classification signal.
    source_mainline = _first_parent_chain(repo, source_commit)

    findings: List[PolicyCommitFinding] = []
    for sha in source_only:
        changed = _touches_policy_path(repo, sha, paths)
        if not changed:
            continue

        # containing_branches is informational only (human orientation in
        # the report/CLI output) and never feeds the classification below —
        # see the module docstring for why branch-containment signals were
        # abandoned as the decision criterion.
        containing = _branches_containing(repo, sha)

        # `rev-list --first-parent source_commit` always lists source_commit
        # itself as the first entry regardless of whether source_commit is
        # itself a merge commit — that membership is trivial and tells us
        # nothing about where a *merge* commit's own diff came from (it came
        # from a non-first parent by definition of what we're testing here).
        # So the mainline shortcut only applies to a non-merge commit: for
        # those, first-parent-chain membership is exactly "authored directly
        # on (or fast-forwarded onto) source's own line". A merge commit
        # always falls through to the content-based check below, even when
        # it is source_commit itself (e.g. the tip is a merge that just
        # pulled the target's policy in).
        is_merge_commit = _parent_count(repo, sha) > 1

        if not is_merge_commit and sha in source_mainline:
            classification = "source-origin"
            note = (
                "Commit is a non-merge commit on source_branch's own "
                "first-parent (mainline) history: authored directly on (or "
                "fast-forwarded onto) the source branch itself. Which other "
                "branches/worktrees also happen to contain this commit does "
                "not change that."
            )
        else:
            # Either sha is a merge commit (so its own diff came from a
            # non-first parent by construction), or sha is a non-merge
            # commit that is an ancestor-or-equal of source_commit (by
            # construction of `source_only`) but not on its first-parent
            # chain — i.e. it entered source only via some merge commit's
            # non-first parent further up the chain.
            # Content-based pull-in check: compare the changed path's blob
            # at this commit against its blob on the target tip directly.
            content_matches_target = bool(changed) and all(
                _blob_at(repo, sha, p) == _blob_at(repo, target_commit, p) for p in changed
            )
            # A merge performed on source may retain source-local policy edits,
            # so its resulting blob need not equal the target tip byte-for-byte.
            # It is nevertheless a target pull-in when a non-first parent is
            # reachable from the target. This topology is stronger evidence than
            # comparing the combined merge result to either parent's blob.
            parents = _run_git(repo, ["rev-list", "--parents", "-n", "1", sha]).split()[1:]
            pulls_target_parent = is_merge_commit and any(
                subprocess.run(
                    ["git", "-C", str(repo), "merge-base", "--is-ancestor", parent, target_commit],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                ).returncode
                == 0
                for parent in parents[1:]
            )
            if content_matches_target or pulls_target_parent:
                classification = "target-pull-in-eligible"
                note = (
                    "Commit entered source_branch via a merge and its changed "
                    "policy content matches target_branch's current content or "
                    "the merge pulls a non-first parent reachable from target: "
                    "a legitimate pull-in of the target's own policy "
                    "(DEC-0044-001), not a foreign-branch commit."
                )
            else:
                classification = "foreign-branch"
                other_note = (
                    f" Other branches currently containing it: {', '.join(containing)}."
                    if containing
                    else " No surviving branch currently names it; the merge-commit "
                    "topology is the evidence regardless."
                )
                note = (
                    "Commit changes a declared policy path, is unique to the "
                    "source branch relative to the target, entered source_branch "
                    "only via a merge (not source's own first-parent history), "
                    "and its content does not match target_branch's current "
                    "policy." + other_note + " Flag for review under DEC-0044-002 "
                    "(no agent commits policy changes onto a branch other than "
                    "the one they originated on or the integration target)."
                )

        trailer_required = _commit_timestamp(repo, sha) > POLICY_PROVENANCE_EFFECTIVE_AT
        trailer_valid, policy_origin_branch = _has_valid_policy_origin_trailer(repo, sha)
        missing_policy_origin_trailer = trailer_required and not trailer_valid
        if missing_policy_origin_trailer:
            note += (
                f" Missing required {POLICY_ORIGIN_TRAILER}: trailer: policy-path commits "
                f"after {POLICY_PROVENANCE_EFFECTIVE_AT.isoformat()} must carry exactly "
                "one non-empty, valid branch-name value."
            )

        findings.append(
            PolicyCommitFinding(
                sha=sha,
                changed_policy_paths=changed,
                containing_branches=containing,
                classification=classification,
                policy_origin_branch=policy_origin_branch,
                missing_policy_origin_trailer=missing_policy_origin_trailer,
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
        trailer = f.policy_origin_branch or "MISSING OR MALFORMED"
        lines.append(f"       {POLICY_ORIGIN_TRAILER}: {trailer}")
        lines.append(f"       {f.note}")
    if report.has_foreign_branch_policy_commit or report.has_missing_policy_origin_trailer:
        reasons = []
        if report.has_foreign_branch_policy_commit:
            reasons.append("foreign-branch policy commit(s)")
        if report.has_missing_policy_origin_trailer:
            reasons.append("missing or malformed Policy-Origin-Branch trailer(s)")
        lines.append("VERDICT: " + "; ".join(reasons) + " found — review required.")
    else:
        lines.append("VERDICT: no foreign-branch policy commits or missing required trailers found.")
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

    return 1 if (report.has_foreign_branch_policy_commit or report.has_missing_policy_origin_trailer) else 0


if __name__ == "__main__":
    raise SystemExit(main())
