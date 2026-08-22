#!/usr/bin/env python3
"""Validate the pre-activation legacy handoff manifest (Task `0038-16.01`).

The manifest at ``docs/pipeline/legacy-handoff-manifest-v1.json`` is the single
machine/human-readable hand-over record between the surviving legacy execution
bridge (Feature `0038`) and the versioned runner queue that Task `0037-46.01`
implements and Task `0037-46.02` activates.

This checker is read-only and stdlib-only. It never writes, never touches Git
refs, never activates a queue and never changes authority. It proves the four
properties Task `0038-16.01`'s Definition of Done requires:

1. **Bound review package** — the manifest binds the exact `0037-37` review
   package (file digest, base commit and all contract digests), and every bound
   contract still recomputes to the recorded digest in the working tree.
2. **Zero unmapped primitives** — every primitive carries exactly one
   disposition, and every mechanism enumerated by the living
   ``## Skript-Ausführungs-Infrastruktur`` table of ``docs/pipeline/tools.md``
   is either covered by a primitive or explicitly excluded with a reason.
3. **Zero multiply authoritative primitives** — no two primitives declare the
   same authority key, and no typed action ID is owned by more than one
   primitive.
4. **Singleton preserved / authority unchanged** — the manifest declares the
   legacy singleton active and the queue inactive, and the repository agrees:
   no ``.runner/`` runtime root exists, and the live bootstrap selector
   ``agent-workflow.json`` still declares the pre-activation runner protocol.

   The presence of the ``_src/runner/`` typed-action **registry** is explicitly
   *not* an activation signal — see ``_check_queue_liveness`` below and Task
   ``0038-30``.

Usage::

    python3 _src/tools/legacy_handoff_manifest.py --check
    python3 _src/tools/legacy_handoff_manifest.py --check --json
    python3 _src/tools/legacy_handoff_manifest.py --check --root /path/to/repo

Exit status is 0 only when zero findings are reported.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

SCHEMA = "legacy-handoff-manifest@v1"
DEFAULT_MANIFEST = "docs/pipeline/legacy-handoff-manifest-v1.json"
DEFAULT_TOOLS_DOC = "docs/pipeline/tools.md"
TOOLS_SECTION = "## Skript-Ausführungs-Infrastruktur"

CATEGORIES = (
    "action",
    "approval-readiness",
    "context",
    "evidence",
    "recovery",
    "result",
    "schema",
    "scope",
    "validation",
)
DISPOSITION_KINDS = ("typed-action", "retirement-trigger")
CONSUMERS = ("0037-46.01", "0037-46.02")

PRIMITIVE_ID_RE = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")
TYPED_ACTION_RE = re.compile(r"^[a-z][a-z0-9-]*(?:\.[a-z0-9-]+)+@v[0-9]+$")
ITEM_ID_RE = re.compile(r"^[0-9]{4}(?:-[0-9]{2}(?:\.[0-9]{2})?)?$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
BACKTICK_RE = re.compile(r"`([^`]+)`")

REQUIRED_PRIMITIVE_KEYS = (
    "id",
    "category",
    "title",
    "owner_task",
    "authority_key",
    "sources",
    "compatibility",
    "test_fixtures",
    "disposition",
)

# --- Queue liveness, narrowed by Task `0038-30` -----------------------------
#
# `0038-16.01` originally treated *either* `.runner/` or `_src/runner/` as proof
# that the queue had been activated. That conflated two different things, and
# the manifest's own text says so:
#
#   * The manifest's consumer obligation for Task `0037-46.01` reads: "Register
#     every `typed-action` disposition's action IDs in the permanent typed-action
#     registry (`_src/runner/actions-v1.json`) ... implement no generic shell
#     action; *do not activate*." The manifest therefore commissions
#     `_src/runner/` itself and, in the same sentence, states that creating it is
#     not activation. Its existence cannot be the activation signal without the
#     manifest contradicting its own consumer obligation.
#   * `singleton.note` reads: "The singleton remains the only mechanism that
#     accepts mutating requests *until `0037-46.02` bumps the protocol epoch*",
#     and `docs/pipeline/legacy-handoff-manifest.md` spells out where: "`0037-46.02`
#     bumps the runner protocol epoch *in the live bootstrap selector* after queue
#     health, round-trip, concurrency, restart and mutation-isolation tests pass
#     durably."
#
# So the manifest's own definition of activation is liveness — a dispatcher that
# actually runs, or a bumped protocol epoch in the live selector — not a source
# file on disk. `LHM035` fires only on that.

# Git-ignored *runtime* root of the versioned queue. It comes into being only
# when a dispatcher actually runs, so its presence is liveness.
QUEUE_RUNTIME_ROOT = ".runner"

# Versioned typed-action *registry* source, created by `0037-46.01` under its own
# declared write scope. Present-but-inactive is the expected pre-activation state
# once that Task lands; it is deliberately **not** an activation marker.
QUEUE_REGISTRY_ROOT = "_src/runner"

# The live bootstrap selector (`docs/pipeline/agent-workflow.md`: "root
# `agent-workflow.json` as the canonical machine selector") and the runner
# protocol it declares before activation. `0037-46.02` activates by bumping this.
BOOTSTRAP_SELECTOR = "agent-workflow.json"
PREACTIVATION_RUNNER_PROTOCOL = "runner-request@v1"


class Finding(Dict[str, str]):
    pass


def _finding(rule: str, message: str, where: str = "") -> Dict[str, str]:
    out = {"rule": rule, "message": message}
    if where:
        out["where"] = where
    return out


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(manifest: Dict[str, Any]) -> bytes:
    """Deterministic serialization used for the manifest self-digest."""
    return (
        json.dumps(manifest, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")


def tools_doc_mechanisms(tools_doc: Path) -> List[str]:
    """Extract the first-column mechanism tokens of the living tools.md table."""
    if not tools_doc.exists():
        return []
    mechanisms: List[str] = []
    in_section = False
    for line in tools_doc.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_section = line.strip() == TOOLS_SECTION
            continue
        if not in_section or not line.startswith("|"):
            continue
        first = line.split("|")[1].strip()
        if not first or set(first) <= {"-", " ", ":"}:
            continue
        for token in BACKTICK_RE.findall(first):
            token = token.strip()
            if token and token != "Mechanismus":
                mechanisms.append(token)
    return mechanisms


def _check_structure(manifest: Dict[str, Any]) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    if manifest.get("schema") != SCHEMA:
        findings.append(
            _finding("LHM001", f"schema must be {SCHEMA!r}, got {manifest.get('schema')!r}")
        )
    version = manifest.get("manifest_version")
    if not isinstance(version, int) or version < 1:
        findings.append(_finding("LHM002", "manifest_version must be a positive integer"))
    for key in ("review_package", "singleton", "consumers", "primitives", "coverage"):
        if key not in manifest:
            findings.append(_finding("LHM003", f"missing top-level key {key!r}"))
    return findings


def _check_review_package(root: Path, manifest: Dict[str, Any]) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    pkg = manifest.get("review_package")
    if not isinstance(pkg, dict):
        return [_finding("LHM010", "review_package must be an object")]

    if pkg.get("producer_task") != "0037-37":
        findings.append(_finding("LHM011", "review_package.producer_task must be '0037-37'"))
    if not COMMIT_RE.match(str(pkg.get("producer_ref", ""))):
        findings.append(_finding("LHM012", "review_package.producer_ref must be a full commit SHA"))

    rel = pkg.get("path")
    if not isinstance(rel, str) or not rel:
        return findings + [_finding("LHM013", "review_package.path is required")]
    path = root / rel
    if not path.exists():
        return findings + [_finding("LHM014", f"review package missing: {rel}", rel)]

    actual = sha256_file(path)
    if actual != pkg.get("sha256"):
        findings.append(
            _finding("LHM015", f"review package digest drift: recorded {pkg.get('sha256')}, actual {actual}", rel)
        )

    try:
        package = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        return findings + [_finding("LHM016", f"review package is not valid JSON: {exc}", rel)]

    if package.get("base_commit") != pkg.get("base_commit"):
        findings.append(
            _finding("LHM017", "review_package.base_commit does not match the bound package", rel)
        )

    bound = pkg.get("contracts")
    if not isinstance(bound, list) or not bound:
        return findings + [_finding("LHM018", "review_package.contracts must be a non-empty list")]

    package_contracts = {c["path"]: c["sha256"] for c in package.get("contracts", [])}
    bound_map: Dict[str, str] = {}
    for entry in bound:
        if not isinstance(entry, dict) or "path" not in entry or "sha256" not in entry:
            findings.append(_finding("LHM019", "each bound contract needs path and sha256"))
            continue
        bound_map[entry["path"]] = entry["sha256"]

    if set(bound_map) != set(package_contracts):
        missing = sorted(set(package_contracts) - set(bound_map))
        extra = sorted(set(bound_map) - set(package_contracts))
        findings.append(
            _finding(
                "LHM020",
                f"bound contract set differs from the review package (missing={missing}, extra={extra})",
                rel,
            )
        )

    for cpath, digest in sorted(bound_map.items()):
        if package_contracts.get(cpath) not in (None, digest):
            findings.append(
                _finding("LHM021", f"bound digest for {cpath} disagrees with the review package", cpath)
            )
        target = root / cpath
        if not target.exists():
            findings.append(_finding("LHM022", f"bound contract file is missing: {cpath}", cpath))
            continue
        if not SHA256_RE.match(str(digest)):
            findings.append(_finding("LHM023", f"malformed digest for {cpath}", cpath))
            continue
        actual_digest = sha256_file(target)
        if actual_digest != digest:
            findings.append(
                _finding(
                    "LHM024",
                    f"contract drift: {cpath} now hashes to {actual_digest}, bound digest {digest}",
                    cpath,
                )
            )
    return findings


def _check_singleton(root: Path, manifest: Dict[str, Any]) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    singleton = manifest.get("singleton")
    if not isinstance(singleton, dict):
        return [_finding("LHM030", "singleton must be an object")]
    if singleton.get("state") != "active":
        findings.append(_finding("LHM031", "singleton.state must remain 'active' before activation"))
    if singleton.get("queue_activated") is not False:
        findings.append(_finding("LHM032", "singleton.queue_activated must be false in a pre-activation manifest"))
    if manifest.get("activates_queue") is not False:
        findings.append(_finding("LHM033", "activates_queue must be false"))
    if manifest.get("changes_authority") is not False:
        findings.append(_finding("LHM034", "changes_authority must be false"))
    findings.extend(_check_queue_liveness(root))
    return findings


def _check_queue_liveness(root: Path) -> List[Dict[str, str]]:
    """Report `LHM035` only when the queue is *live*, never when it merely exists.

    Two independent liveness signals, both taken from the manifest's own
    definition of activation (see the constants above):

    1. the git-ignored ``.runner/`` runtime root exists — a dispatcher has run;
    2. the live bootstrap selector declares a ``runner_protocol`` other than the
       pre-activation one — ``0037-46.02`` has bumped the protocol epoch.

    ``_src/runner/`` — the typed-action registry ``0037-46.01`` is obliged to
    create *without activating* — is not a signal and never fires this rule.

    A missing or unparsable selector is deliberately not treated as activation:
    activation requires the selector to positively *declare* the new protocol,
    and selector corruption is the fail-closed responsibility of the bootstrap
    path (``docs/pipeline/agent-workflow.md``), not of this read-only checker.
    """
    findings: List[Dict[str, str]] = []

    if (root / QUEUE_RUNTIME_ROOT).exists():
        findings.append(
            _finding(
                "LHM035",
                f"queue runtime root {QUEUE_RUNTIME_ROOT!r} exists — a dispatcher has run, "
                "but the manifest claims the queue is inactive",
                QUEUE_RUNTIME_ROOT,
            )
        )

    selector_path = root / BOOTSTRAP_SELECTOR
    if selector_path.is_file():
        try:
            selector = json.loads(selector_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            selector = None
        if isinstance(selector, dict):
            protocol = selector.get("runner_protocol")
            if isinstance(protocol, str) and protocol != PREACTIVATION_RUNNER_PROTOCOL:
                findings.append(
                    _finding(
                        "LHM035",
                        f"live bootstrap selector declares runner_protocol {protocol!r}, bumped past "
                        f"the pre-activation {PREACTIVATION_RUNNER_PROTOCOL!r} — the queue is live, "
                        "but the manifest claims the queue is inactive",
                        BOOTSTRAP_SELECTOR,
                    )
                )

    return findings


def _check_primitives(manifest: Dict[str, Any]) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    findings: List[Dict[str, str]] = []
    primitives = manifest.get("primitives")
    stats = {
        "primitives": 0,
        "by_category": {},
        "typed_action": 0,
        "retirement_trigger": 0,
        "typed_actions": 0,
    }
    if not isinstance(primitives, list) or not primitives:
        return [_finding("LHM040", "primitives must be a non-empty list")], stats

    ids: Dict[str, int] = {}
    authority_keys: Dict[str, str] = {}
    typed_actions: Dict[str, str] = {}
    order: List[str] = []

    for index, prim in enumerate(primitives):
        where = f"primitives[{index}]"
        if not isinstance(prim, dict):
            findings.append(_finding("LHM041", "primitive must be an object", where))
            continue
        pid = prim.get("id", "")
        where = pid or where
        for key in REQUIRED_PRIMITIVE_KEYS:
            if key not in prim:
                findings.append(_finding("LHM042", f"missing required key {key!r}", where))
        if not PRIMITIVE_ID_RE.match(str(pid)):
            findings.append(_finding("LHM043", f"malformed primitive id {pid!r}", where))
        if pid in ids:
            findings.append(_finding("LHM044", f"duplicate primitive id {pid!r}", where))
        ids[pid] = index
        order.append(str(pid))

        category = prim.get("category")
        if category not in CATEGORIES:
            findings.append(_finding("LHM045", f"unknown category {category!r}", where))
        else:
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

        owner = prim.get("owner_task")
        if not ITEM_ID_RE.match(str(owner)):
            findings.append(_finding("LHM046", f"owner_task {owner!r} is not a backlog item ID", where))

        akey = prim.get("authority_key")
        if not isinstance(akey, str) or not akey:
            findings.append(_finding("LHM047", "authority_key is required", where))
        elif akey in authority_keys:
            findings.append(
                _finding(
                    "LHM048",
                    f"multiply authoritative: authority_key {akey!r} is already owned by {authority_keys[akey]!r}",
                    where,
                )
            )
        else:
            authority_keys[akey] = str(pid)

        sources = prim.get("sources")
        if not isinstance(sources, list) or not sources:
            findings.append(_finding("LHM049", "sources must be a non-empty list", where))
        if not isinstance(prim.get("compatibility"), str) or not prim.get("compatibility"):
            findings.append(_finding("LHM050", "compatibility must be a non-empty string", where))
        fixtures = prim.get("test_fixtures")
        if not isinstance(fixtures, list) or not fixtures:
            findings.append(_finding("LHM051", "test_fixtures must be a non-empty list", where))

        disp = prim.get("disposition")
        if not isinstance(disp, dict):
            findings.append(_finding("LHM052", "disposition must be an object", where))
            continue
        kind = disp.get("kind")
        if kind not in DISPOSITION_KINDS:
            findings.append(_finding("LHM053", f"disposition.kind must be one of {DISPOSITION_KINDS}", where))
            continue
        consumer = disp.get("consumer")
        if consumer not in CONSUMERS:
            findings.append(_finding("LHM054", f"disposition.consumer must be one of {CONSUMERS}", where))
        if not isinstance(disp.get("removal_condition"), str) or not disp.get("removal_condition"):
            findings.append(_finding("LHM055", "disposition.removal_condition is required", where))

        has_actions = "typed_actions" in disp
        has_trigger = "retirement_trigger" in disp
        if has_actions == has_trigger:
            findings.append(
                _finding(
                    "LHM056",
                    "disposition must carry exactly one of typed_actions or retirement_trigger",
                    where,
                )
            )
            continue

        if kind == "typed-action":
            if not has_actions:
                findings.append(_finding("LHM057", "kind 'typed-action' requires typed_actions", where))
                continue
            if consumer != "0037-46.01":
                findings.append(_finding("LHM058", "typed-action dispositions are consumed by 0037-46.01", where))
            actions = disp.get("typed_actions")
            if not isinstance(actions, list) or not actions:
                findings.append(_finding("LHM059", "typed_actions must be a non-empty list", where))
                continue
            stats["typed_action"] += 1
            for action in actions:
                if not isinstance(action, str) or not TYPED_ACTION_RE.match(action):
                    findings.append(_finding("LHM060", f"malformed typed action id {action!r}", where))
                    continue
                if action in typed_actions:
                    findings.append(
                        _finding(
                            "LHM061",
                            f"multiply authoritative typed action {action!r}: already owned by {typed_actions[action]!r}",
                            where,
                        )
                    )
                    continue
                typed_actions[action] = str(pid)
        else:
            if not has_trigger:
                findings.append(_finding("LHM062", "kind 'retirement-trigger' requires retirement_trigger", where))
                continue
            if consumer != "0037-46.02":
                findings.append(_finding("LHM063", "retirement triggers are consumed by 0037-46.02", where))
            trigger = disp.get("retirement_trigger")
            if not isinstance(trigger, str) or not trigger:
                findings.append(_finding("LHM064", "retirement_trigger must be a non-empty string", where))
            stats["retirement_trigger"] += 1

    # superseded_by references must resolve to a typed action owned somewhere.
    for prim in primitives:
        if not isinstance(prim, dict):
            continue
        disp = prim.get("disposition")
        if not isinstance(disp, dict):
            continue
        for action in disp.get("superseded_by", []) or []:
            if action not in typed_actions:
                findings.append(
                    _finding(
                        "LHM065",
                        f"superseded_by references unknown typed action {action!r}",
                        str(prim.get("id", "")),
                    )
                )

    if order != sorted(order):
        findings.append(_finding("LHM066", "primitives must be sorted by id for deterministic output"))

    missing_categories = sorted(set(CATEGORIES) - set(stats["by_category"]))
    if missing_categories:
        findings.append(
            _finding("LHM067", f"no primitive mapped for required categories: {missing_categories}")
        )

    stats["primitives"] = len(primitives)
    stats["typed_actions"] = len(typed_actions)
    return findings, stats


def _check_coverage(root: Path, manifest: Dict[str, Any], tools_doc: Path) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    coverage = manifest.get("coverage")
    if not isinstance(coverage, dict):
        return [_finding("LHM070", "coverage must be an object")]

    declared_source = coverage.get("inventory_source")
    if declared_source != DEFAULT_TOOLS_DOC:
        findings.append(
            _finding("LHM071", f"coverage.inventory_source must be {DEFAULT_TOOLS_DOC!r}")
        )

    covered: set = set()
    for prim in manifest.get("primitives", []):
        if isinstance(prim, dict):
            for source in prim.get("sources", []) or []:
                if isinstance(source, str):
                    covered.add(source)

    excluded: Dict[str, str] = {}
    for entry in coverage.get("excluded", []) or []:
        if not isinstance(entry, dict) or not entry.get("mechanism") or not entry.get("reason"):
            findings.append(_finding("LHM072", "each coverage.excluded entry needs mechanism and reason"))
            continue
        excluded[entry["mechanism"]] = entry["reason"]

    mechanisms = tools_doc_mechanisms(tools_doc)
    if not mechanisms:
        findings.append(_finding("LHM073", f"could not read the mechanism table from {tools_doc}"))
        return findings

    for mechanism in mechanisms:
        if mechanism in covered or mechanism in excluded:
            continue
        findings.append(
            _finding("LHM074", f"unmapped legacy mechanism {mechanism!r} has no primitive and no exclusion", mechanism)
        )

    for mechanism in sorted(excluded):
        if mechanism not in mechanisms:
            findings.append(
                _finding("LHM075", f"coverage.excluded names {mechanism!r}, which the inventory source does not list", mechanism)
            )

    # Every declared file source must actually exist (a "surviving" primitive).
    for prim in manifest.get("primitives", []):
        if not isinstance(prim, dict):
            continue
        if prim.get("ephemeral") is True:
            # A consumable one-use slot (root `run.sh`); its expected steady state
            # is *absent*, so existence must not be asserted. See SANDBOX.md.
            continue
        for source in prim.get("sources", []) or []:
            if not isinstance(source, str) or "<" in source or source.endswith("/"):
                continue  # path template, not a concrete file
            if source.startswith("output/"):
                continue  # git-ignored runtime evidence root
            if not (root / source).exists():
                findings.append(
                    _finding("LHM076", f"primitive source does not exist: {source}", str(prim.get("id", "")))
                )
    return findings


def _check_consumers(manifest: Dict[str, Any]) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    consumers = manifest.get("consumers")
    if not isinstance(consumers, list) or not consumers:
        return [_finding("LHM080", "consumers must be a non-empty list")]
    ids = []
    for entry in consumers:
        if not isinstance(entry, dict):
            findings.append(_finding("LHM081", "consumer entries must be objects"))
            continue
        cid = entry.get("task")
        if cid not in CONSUMERS:
            findings.append(_finding("LHM082", f"unknown consumer task {cid!r}"))
        if not entry.get("obligation"):
            findings.append(_finding("LHM083", f"consumer {cid!r} needs an obligation"))
        ids.append(cid)
    for required in CONSUMERS:
        if required not in ids:
            findings.append(_finding("LHM084", f"required queue consumer {required} is not named"))
    return findings


def validate(root: Path, manifest_path: Path, tools_doc: Path) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "schema": "legacy-handoff-manifest-check@v1",
        "manifest": str(manifest_path.relative_to(root)) if manifest_path.is_relative_to(root) else str(manifest_path),
        "findings": [],
        "stats": {},
    }
    if not manifest_path.exists():
        report["findings"].append(_finding("LHM000", f"manifest not found: {manifest_path}"))
        report["verdict"] = "FAIL"
        return report
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report["findings"].append(_finding("LHM000", f"manifest is not valid JSON: {exc}"))
        report["verdict"] = "FAIL"
        return report

    findings: List[Dict[str, str]] = []
    findings += _check_structure(manifest)
    findings += _check_review_package(root, manifest)
    findings += _check_singleton(root, manifest)
    prim_findings, stats = _check_primitives(manifest)
    findings += prim_findings
    findings += _check_coverage(root, manifest, tools_doc)
    findings += _check_consumers(manifest)

    report["findings"] = findings
    stats["unmapped"] = sum(1 for f in findings if f["rule"] in ("LHM056", "LHM074"))
    stats["multiply_authoritative"] = sum(1 for f in findings if f["rule"] in ("LHM048", "LHM061"))
    report["stats"] = stats
    report["verdict"] = "PASS" if not findings else "FAIL"
    return report


def _summary_lines(report: Dict[str, Any]) -> Iterable[str]:
    stats = report.get("stats", {})
    yield f"legacy-handoff-manifest: {report['verdict']}"
    yield f"  manifest:               {report['manifest']}"
    yield f"  primitives:             {stats.get('primitives', 0)}"
    yield f"  typed-action mappings:  {stats.get('typed_action', 0)} owning {stats.get('typed_actions', 0)} action IDs"
    yield f"  retirement triggers:    {stats.get('retirement_trigger', 0)}"
    yield f"  unmapped primitives:    {stats.get('unmapped', 0)}"
    yield f"  multiply authoritative: {stats.get('multiply_authoritative', 0)}"
    findings = report.get("findings", [])
    yield f"  findings:               {len(findings)}"
    for finding in findings[:3]:
        yield f"    {finding['rule']} {finding.get('where', '-')}: {finding['message']}"
    if len(findings) > 3:
        yield f"    ... {len(findings) - 3} more (use --json)"


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="run the validation (default)")
    parser.add_argument("--json", action="store_true", help="emit the full JSON report")
    parser.add_argument("--root", default=".", help="repository root (default: .)")
    parser.add_argument("--manifest", default=None, help="manifest path (default: %s)" % DEFAULT_MANIFEST)
    parser.add_argument("--tools-doc", default=None, help="inventory source (default: %s)" % DEFAULT_TOOLS_DOC)
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    manifest_path = Path(args.manifest).resolve() if args.manifest else root / DEFAULT_MANIFEST
    tools_doc = Path(args.tools_doc).resolve() if args.tools_doc else root / DEFAULT_TOOLS_DOC

    report = validate(root, manifest_path, tools_doc)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        for line in _summary_lines(report):
            print(line)
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
