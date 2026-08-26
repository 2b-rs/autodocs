#!/usr/bin/env python3
"""Conformance checker for adversarial completion evidence (`DEC-0038-004`).

Implements the decision procedure of the normative block
`adversarial-completion-evidence@v1`, which is projected byte-identically into
the `TODO.md` header contract and the completion section of `AGENTS.md`.

Two modes:

  --evidence <path.json>   check one `completion-evidence@v1` record against AE-1..AE-7
  --projection <repo>      check AE-8: both operative projections present and identical

Exit codes: 0 conforming, 1 findings, 2 failure (unreadable/malformed input).

The checker is deliberately mechanical. It cannot judge whether a generation
domain "meaningfully exercises the claim" (AE-5 reserves that to the reviewer),
nor whether a named neighbor is genuinely adjacent. It checks that the required
evidence is present, internally consistent, and of the required shape, so that a
reviewer spends attention on the judgement calls rather than on absence.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCHEMA = "completion-evidence@v1"

#: AE-1 enumerated in-scope behavior classes.
IN_SCOPE_KINDS = {
    "counting-cardinality",
    "identity-matching",
    "serialization-shape",
    "gate-classification",
    "set-sequence-invariant",
}

#: AE-7 enumerated exclusion classes.
EXCLUDED_KINDS = {
    "documentation-only",
    "bookkeeping-only",
    "generated-output-refresh",
    "authority-baseline-independence",
}

BLOCK_RE = re.compile(
    r"<!-- BEGIN adversarial-completion-evidence@v1 -->"
    r".*?"
    r"<!-- END adversarial-completion-evidence@v1 -->",
    re.S,
)

PROJECTION_FILES = ("AGENTS.md", "TODO.md")


class Finding:
    __slots__ = ("code", "rule", "detail")

    def __init__(self, code: str, rule: str, detail: str) -> None:
        self.code = code
        self.rule = rule
        self.detail = detail

    def as_dict(self) -> dict:
        return {"code": self.code, "rule": self.rule, "detail": self.detail}

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"{self.code} [{self.rule}] {self.detail}"


def _nonempty(value) -> bool:
    return isinstance(value, str) and value.strip() != ""


def check_evidence(record: dict) -> list[Finding]:
    """Apply AE-1..AE-7 to one `completion-evidence@v1` record."""
    out: list[Finding] = []

    if record.get("schema") != SCHEMA:
        return [Finding("AE-SCHEMA", "schema", f"expected schema {SCHEMA!r}")]

    kinds = record.get("change_kinds")
    if not isinstance(kinds, list):
        return [Finding("AE-1-MALFORMED", "AE-1", "change_kinds must be a list")]

    unknown = [k for k in kinds if k not in IN_SCOPE_KINDS | EXCLUDED_KINDS]
    if unknown:
        out.append(
            Finding("AE-1-UNKNOWN-KIND", "AE-1", f"unrecognized change kinds: {sorted(unknown)}")
        )

    in_scope = sorted(set(kinds) & IN_SCOPE_KINDS)

    # AE-1 / AE-7: an entirely excluded change carries no additional obligation.
    if not in_scope:
        if not set(kinds) & EXCLUDED_KINDS:
            out.append(
                Finding(
                    "AE-1-UNCLASSIFIED",
                    "AE-1",
                    "record declares neither an in-scope behavior class nor an exclusion class",
                )
            )
        return out

    # AE-2: exact baselines.
    baselines = record.get("baselines") or {}
    pre = baselines.get("pre_change")
    cand = baselines.get("candidate")
    if not _nonempty(pre) or not _nonempty(cand):
        out.append(
            Finding("AE-2-MISSING-BASELINE", "AE-2", "pre_change and candidate baselines required")
        )
    elif pre.strip() == cand.strip():
        out.append(
            Finding(
                "AE-2-IDENTICAL-BASELINE",
                "AE-2",
                "pre_change and candidate baselines are the same revision",
            )
        )

    # AE-3: at least one falsification case, red on baseline and green on candidate.
    cases = record.get("falsification_cases")
    cases = cases if isinstance(cases, list) else []
    if not cases:
        out.append(
            Finding("AE-3-NO-FALSIFICATION-CASE", "AE-3", "at least one falsification case required")
        )
    conforming_cases = 0
    for i, case in enumerate(cases):
        if not isinstance(case, dict):
            out.append(Finding("AE-3-MALFORMED-CASE", "AE-3", f"case {i} is not an object"))
            continue
        label = case.get("name") or f"case {i}"
        pre_r = case.get("result_pre_change")
        cand_r = case.get("result_candidate")
        if not _nonempty(case.get("derived_from_claim")):
            out.append(
                Finding(
                    "AE-3-NOT-CLAIM-DERIVED",
                    "AE-3",
                    f"{label}: derived_from_claim not stated",
                )
            )
        if not _nonempty(case.get("command")):
            out.append(Finding("AE-3-NO-COMMAND", "AE-3", f"{label}: real command not recorded"))
        if not (_nonempty(case.get("output")) or _nonempty(case.get("output_ref"))):
            out.append(
                Finding(
                    "AE-3-NO-OUTPUT",
                    "AE-3",
                    f"{label}: bounded output or immutable output reference required",
                )
            )
        if case.get("mocked_changed_path") is True:
            out.append(
                Finding(
                    "AE-3-MOCK-BYPASS",
                    "AE-3",
                    f"{label}: assertion bypasses the changed path via mocking",
                )
            )
        if pre_r == "green":
            out.append(
                Finding(
                    "AE-3-ALWAYS-GREEN",
                    "AE-3",
                    f"{label}: green on the pre-change baseline, so it falsifies nothing",
                )
            )
        elif pre_r != "red":
            out.append(
                Finding(
                    "AE-3-NO-RED-BASELINE",
                    "AE-3",
                    f"{label}: result_pre_change must be recorded as 'red' (got {pre_r!r})",
                )
            )
        if cand_r != "green":
            out.append(
                Finding(
                    "AE-3-CANDIDATE-NOT-GREEN",
                    "AE-3",
                    f"{label}: result_candidate must be 'green' (got {cand_r!r})",
                )
            )
        if pre_r == "red" and cand_r == "green":
            conforming_cases += 1
    if cases and conforming_cases == 0:
        out.append(
            Finding(
                "AE-3-NO-CONFORMING-CASE",
                "AE-3",
                "no case is red on the pre-change baseline and green on the candidate",
            )
        )

    # AE-4: at least two distinct adjacent cases, fully described.
    neighbors = record.get("adjacent_cases")
    neighbors = neighbors if isinstance(neighbors, list) else []
    described = []
    for i, nb in enumerate(neighbors):
        if not isinstance(nb, dict):
            out.append(Finding("AE-4-MALFORMED-CASE", "AE-4", f"neighbor {i} is not an object"))
            continue
        label = nb.get("name") or f"neighbor {i}"
        missing = [
            f
            for f in ("dimension", "expected", "observed", "why_adjacent")
            if not _nonempty(nb.get(f))
        ]
        if missing:
            out.append(
                Finding(
                    "AE-4-INCOMPLETE-CASE",
                    "AE-4",
                    f"{label}: missing {', '.join(missing)}",
                )
            )
        else:
            described.append(nb.get("dimension", "").strip())
    if len(described) < 2:
        out.append(
            Finding(
                "AE-4-TOO-FEW-NEIGHBORS",
                "AE-4",
                f"at least two fully described adjacent cases required, found {len(described)}",
            )
        )
    elif len(set(described)) < 2:
        out.append(
            Finding(
                "AE-4-NOT-DISTINCT",
                "AE-4",
                "adjacent cases must probe distinct neighboring dimensions",
            )
        )

    # AE-5: property evidence for claimed set/sequence invariants.
    if "set-sequence-invariant" in in_scope:
        prop = record.get("property_evidence")
        if not isinstance(prop, dict) or not prop:
            out.append(
                Finding(
                    "AE-5-NO-PROPERTY-EVIDENCE",
                    "AE-5",
                    "set or sequence invariant claimed but no property evidence supplied",
                )
            )
        else:
            for field, code in (
                ("invariant", "AE-5-NO-ORACLE"),
                ("domain", "AE-5-NO-DOMAIN"),
            ):
                if not _nonempty(prop.get(field)):
                    out.append(
                        Finding(code, "AE-5", f"property evidence does not state its {field}")
                    )
            count = prop.get("executed_cases")
            if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
                out.append(
                    Finding(
                        "AE-5-NO-CASE-COUNT",
                        "AE-5",
                        f"actual executed case count required (got {count!r})",
                    )
                )
            if prop.get("generative") is True and not _nonempty(prop.get("seed")):
                out.append(
                    Finding(
                        "AE-5-NO-REPLAY",
                        "AE-5",
                        "generative property evidence requires a seed or replay input",
                    )
                )

    return out


def check_projection(repo: Path) -> list[Finding]:
    """AE-8: the block must be present and identical in both operative files."""
    blocks: dict[str, str | None] = {}
    for name in PROJECTION_FILES:
        path = repo / name
        if not path.is_file():
            return [Finding("AE-8-MISSING-FILE", "AE-8", f"{name} not found under {repo}")]
        found = BLOCK_RE.findall(path.read_text(encoding="utf-8"))
        if len(found) == 0:
            blocks[name] = None
        elif len(found) > 1:
            return [
                Finding("AE-8-DUPLICATE-BLOCK", "AE-8", f"{name} contains {len(found)} blocks")
            ]
        else:
            blocks[name] = found[0]

    absent = sorted(n for n, b in blocks.items() if b is None)
    if len(absent) == len(PROJECTION_FILES):
        return [
            Finding(
                "AE-8-NOT-PROJECTED",
                "AE-8",
                "block absent from both operative locations; requirement is not active policy",
            )
        ]
    if absent:
        return [
            Finding(
                "AE-8-PARTIAL-PROJECTION",
                "AE-8",
                f"block missing from {', '.join(absent)}; partial projection is nonconforming",
            )
        ]
    if blocks[PROJECTION_FILES[0]] != blocks[PROJECTION_FILES[1]]:
        return [
            Finding(
                "AE-8-DIVERGENT-PROJECTION",
                "AE-8",
                "operative projections differ; divergent projection is nonconforming",
            )
        ]
    return []


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--evidence", type=Path, help="completion-evidence@v1 JSON record")
    ap.add_argument("--projection", type=Path, help="repository root to check AE-8 against")
    ap.add_argument("--json", action="store_true", help="emit findings as JSON")
    args = ap.parse_args(argv)

    if not args.evidence and not args.projection:
        ap.error("one of --evidence or --projection is required")

    findings: list[Finding] = []
    try:
        if args.evidence:
            record = json.loads(args.evidence.read_text(encoding="utf-8"))
            if not isinstance(record, dict):
                raise ValueError("evidence record must be a JSON object")
            findings.extend(check_evidence(record))
        if args.projection:
            findings.extend(check_projection(args.projection))
    except (OSError, ValueError) as exc:
        print(f"FAILURE: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps([f.as_dict() for f in findings], indent=2, sort_keys=True))
    else:
        for f in findings:
            print(f"{f.code} [{f.rule}] {f.detail}")
        print("PASS" if not findings else f"FINDINGS: {len(findings)}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
