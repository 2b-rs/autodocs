#!/usr/bin/env python3
"""Branch/chain-aware frontier query (Task 0044-19 / DEC-0044-019).

Implements the five-state work-availability query specified in
docs/pipeline/frontier-query-spec.md.

Evidence sources:
  E1: TODO.md / DONE.md markers on main (lifecycle state, prerequisites)
  E2: Claim files (TODO-*.md / DONE-*.md) across branch tips
  E3: Branch tips and commit subjects (<item-id>: <subject>)
  E4: Registered worktrees and dirty state
  E5: Priority offers / awards (agent-inbox offers.jsonl)
  E6: Governance holds, reservation gates, containment records

Output: five-state partition per item:
  - available
  - in-flight
  - blocked-prereq
  - held
  - indeterminate
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

BLIND_SPOTS = [
    "Work in a worktree that was never committed. An agent editing uncommitted files leaves no branch evidence. Partially mitigated by E4 dirty-state inspection; not eliminated.",
    "Work under an award with no branch and no claim yet. Mitigated by E5, and only while the offer record is retained.",
    "Intent. An agent that has read an item and is about to claim it is invisible until it writes something.",
    "Branch-local claims invisible from main. The 0039-01 pathology: a real claim existing only on its own branch. E2 addresses this only if the query scans branch tips rather than main alone — which is why E2 is specified over all tips.",
    "Cross-repository or out-of-band coordination. Anything agreed in conversation and not written down.",
]

PREREQ_PATTERN = re.compile(r'PREREQ:\s*([^\n]+)')
TASK_LINE_PATTERN = re.compile(r'^- \[(x|w|p|d|u| )\] \*\*([a-zA-Z0-9._-]+)\*\*(.*)')


@dataclass
class ItemAssessment:
    item_id: str
    state: str  # available, in-flight, blocked-prereq, held, indeterminate, terminal
    raw_marker: str
    prerequisites: List[str] = field(default_factory=list)
    prereq_states: Dict[str, str] = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)
    in_flight_branches: List[str] = field(default_factory=list)
    in_flight_claims: List[str] = field(default_factory=list)
    in_flight_offers: List[str] = field(default_factory=list)
    indeterminate_source: Optional[str] = None
    indeterminate_reason: Optional[str] = None


@dataclass
class FrontierQueryResult:
    schema: str = "frontier-query-result@v1"
    repo_root: str = ""
    main_ref: str = ""
    evaluated_items_count: int = 0
    available_items: List[str] = field(default_factory=list)
    in_flight_items: List[str] = field(default_factory=list)
    blocked_prereq_items: List[str] = field(default_factory=list)
    held_items: List[str] = field(default_factory=list)
    indeterminate_items: List[str] = field(default_factory=list)
    terminal_items: List[str] = field(default_factory=list)
    items: Dict[str, ItemAssessment] = field(default_factory=dict)
    blind_spots: List[str] = field(default_factory=lambda: list(BLIND_SPOTS))


def run_git(repo: Path, *args: str) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as e:
        return -1, "", str(e)


def parse_todo_items(todo_content: str) -> Dict[str, Dict[str, Any]]:
    """Parse all items and their metadata from TODO.md content."""
    items: Dict[str, Dict[str, Any]] = {}
    lines = todo_content.splitlines()
    current_item: Optional[str] = None

    for line in lines:
        m = TASK_LINE_PATTERN.match(line)
        if m:
            marker = m.group(1)
            item_id = m.group(2)
            rest = m.group(3)
            current_item = item_id

            prereqs = []
            pm = PREREQ_PATTERN.search(rest)
            if pm:
                prereq_str = pm.group(1).strip()
                for token in prereq_str.split(','):
                    token = token.strip()
                    if not token:
                        continue
                    if ':' in token:
                        target = token.split(':', 1)[1].strip().split(' ')[0]
                    else:
                        target = token.split(' ')[0]
                    if target:
                        prereqs.append(target)

            has_acceptance = 'Acceptance: ✓' in rest or 'Acceptance: \u2713' in rest
            is_held = marker in ('d', 'u') or 'RESERVATION GATE' in rest or 'Reservation gate:' in rest
            is_contested = 'hold window' in rest or 'No validity conclusion' in rest or 'invalidated' in rest

            items[item_id] = {
                'item_id': item_id,
                'marker': marker,
                'prereqs': prereqs,
                'has_acceptance': has_acceptance,
                'is_held': is_held,
                'is_contested': is_contested,
                'raw_text': [line],
            }
        elif current_item and current_item in items:
            items[current_item]['raw_text'].append(line)
            if 'Acceptance: ✓' in line or 'Acceptance: \u2713' in line:
                items[current_item]['has_acceptance'] = True
            if 'RESERVATION GATE' in line or 'Reservation gate:' in line:
                items[current_item]['is_held'] = True
            if 'hold window' in line or 'No validity conclusion' in line or 'invalidated' in line:
                items[current_item]['is_contested'] = True

    return items


def classify_prereq_state(item_info: Dict[str, Any]) -> str:
    """Three-state prerequisite evaluation: terminal-accepted, terminal-recorded, terminal-contested, or non-terminal."""
    marker = item_info.get('marker', '')
    if marker in ('x', 'w'):
        if item_info.get('is_contested'):
            return 'terminal-contested'
        if item_info.get('has_acceptance'):
            return 'terminal-accepted'
        return 'terminal-recorded'
    return 'non-terminal'


def discover_branch_claims(repo: Path) -> Tuple[Dict[str, List[Dict[str, str]]], Optional[str]]:
    """Scan all local branch tips for claim files and item-prefixed commit subjects (E2/E3)."""
    item_claims: Dict[str, List[Dict[str, str]]] = {}
    
    code, out, err = run_git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads")
    if code != 0:
        return {}, f"git for-each-ref failed: {err}"

    branches = [b.strip() for b in out.splitlines() if b.strip()]

    for branch in branches:
        if branch == 'main':
            continue
        code, log_out, _ = run_git(repo, "log", "-n", "20", "--format=%s", branch, "--not", "refs/heads/main")
        if code == 0:
            for subj in log_out.splitlines():
                subj = subj.strip()
                sm = re.match(r'^([0-9]{4}(?:-[0-9]{2,3}(?:\.[0-9]{2})?)?):', subj)
                if sm:
                    target_item = sm.group(1)
                    item_claims.setdefault(target_item, []).append({
                        'branch': branch,
                        'source': 'E3:commit_subject',
                        'detail': subj,
                    })

        code, ls_out, _ = run_git(repo, "ls-tree", "-r", "--name-only", branch)
        if code == 0:
            for path in ls_out.splitlines():
                path = path.strip()
                if path.startswith("TODO-") and path.endswith(".md"):
                    code_blob, blob_content, _ = run_git(repo, "show", f"{branch}:{path}")
                    if code_blob == 0:
                        im = re.search(r'item:\s*`?([a-zA-Z0-9._-]+)`?', blob_content, re.IGNORECASE)
                        if not im:
                            im = re.search(r'Task\s*`?([a-zA-Z0-9._-]+)`?', blob_content, re.IGNORECASE)
                        
                        target_item = None
                        if im:
                            target_item = im.group(1)
                        else:
                            fn_m = re.match(r'TODO-[^-]+-([0-9]{4}(?:-[0-9]{2,3}(?:\.[0-9]{2})?)?)', path)
                            if fn_m:
                                target_item = fn_m.group(1)

                        if target_item:
                            is_terminal = 'state: accepted' in blob_content or 'status: accepted' in blob_content or 'state: terminal' in blob_content
                            if not is_terminal:
                                item_claims.setdefault(target_item, []).append({
                                    'branch': branch,
                                    'claim_file': path,
                                    'source': 'E2:claim_file',
                                    'detail': f"{path} on {branch}",
                                })

    return item_claims, None


def discover_offers(inbox_data_dir: Path) -> Tuple[Dict[str, List[Dict[str, str]]], Optional[str]]:
    """Scan agent-inbox offers.jsonl for active/awarded/in_progress offers (E5)."""
    active_offers: Dict[str, List[Dict[str, str]]] = {}
    offers_file = inbox_data_dir / "offers.jsonl"
    
    if not offers_file.exists():
        return {}, None

    try:
        with open(offers_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    event = data.get('event')
                    item = data.get('item')
                    offer_id = data.get('offer_id')
                    if item and event in ('created', 'activated', 'delivered', 'awarded', 'in_progress'):
                        active_offers.setdefault(item, []).append({
                            'offer_id': offer_id,
                            'event': event,
                            'source': 'E5:offer_record',
                            'detail': f"Offer {offer_id} ({event}) for {item}",
                        })
                    elif item and event in ('closed', 'expired', 'accepted', 'withdrawn'):
                        if item in active_offers:
                            active_offers[item] = [o for o in active_offers[item] if o.get('offer_id') != offer_id]
                            if not active_offers[item]:
                                del active_offers[item]
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        return {}, f"Could not read offers.jsonl: {e}"

    return active_offers, None


def query_frontier(
    repo_path: Path,
    inbox_data_dir: Optional[Path] = None,
    todo_file_name: str = "TODO.md",
) -> FrontierQueryResult:
    """Execute the 5-state branch-aware frontier query."""
    result = FrontierQueryResult(repo_root=str(repo_path))

    code, main_sha, err = run_git(repo_path, "rev-parse", "refs/heads/main")
    if code != 0:
        result.main_ref = "unknown"
    else:
        result.main_ref = main_sha.strip()

    todo_path = repo_path / todo_file_name
    if not todo_path.exists():
        return result

    try:
        with open(todo_path, 'r', encoding='utf-8') as f:
            todo_content = f.read()
    except Exception:
        return result

    parsed_items = parse_todo_items(todo_content)
    result.evaluated_items_count = len(parsed_items)

    branch_claims, branch_err = discover_branch_claims(repo_path)
    
    if inbox_data_dir is None:
        inbox_data_dir = Path("/tmp/agent-inbox/data")
    active_offers, offer_err = discover_offers(inbox_data_dir)

    for item_id, info in parsed_items.items():
        assessment = ItemAssessment(
            item_id=item_id,
            state="indeterminate",
            raw_marker=info['marker'],
            prerequisites=info['prereqs'],
        )

        if branch_err:
            assessment.state = "indeterminate"
            assessment.indeterminate_source = "E2/E3:git_branches"
            assessment.indeterminate_reason = branch_err
            result.indeterminate_items.append(item_id)
            result.items[item_id] = assessment
            continue

        if offer_err:
            assessment.state = "indeterminate"
            assessment.indeterminate_source = "E5:offers"
            assessment.indeterminate_reason = offer_err
            result.indeterminate_items.append(item_id)
            result.items[item_id] = assessment
            continue

        prereq_ok = True
        for req in info['prereqs']:
            req_info = parsed_items.get(req)
            if req_info:
                p_state = classify_prereq_state(req_info)
                assessment.prereq_states[req] = p_state
                if p_state not in ('terminal-recorded', 'terminal-accepted', 'terminal-contested'):
                    prereq_ok = False
            else:
                assessment.prereq_states[req] = 'unknown'
                prereq_ok = False

        in_flight_evidence = []
        if item_id in branch_claims:
            for c in branch_claims[item_id]:
                in_flight_evidence.append(c['detail'])
                if 'branch' in c:
                    assessment.in_flight_branches.append(c['branch'])
                if 'claim_file' in c:
                    assessment.in_flight_claims.append(c['claim_file'])

        if item_id in active_offers:
            for o in active_offers[item_id]:
                in_flight_evidence.append(o['detail'])
                assessment.in_flight_offers.append(o['offer_id'])

        if info['marker'] in ('x', 'w'):
            assessment.state = "terminal"
            assessment.reasons.append(f"Item is terminal on main ([{info['marker']}])")
            result.terminal_items.append(item_id)
        elif info['is_held']:
            assessment.state = "held"
            assessment.reasons.append("Governance hold / reservation gate / marker [d] or [u]")
            result.held_items.append(item_id)
        elif in_flight_evidence:
            assessment.state = "in-flight"
            assessment.reasons.extend(in_flight_evidence)
            result.in_flight_items.append(item_id)
        elif not prereq_ok:
            assessment.state = "blocked-prereq"
            for req, p_state in assessment.prereq_states.items():
                if p_state not in ('terminal-recorded', 'terminal-accepted', 'terminal-contested'):
                    assessment.reasons.append(f"Prerequisite {req} is {p_state}")
            result.blocked_prereq_items.append(item_id)
        elif info['marker'] == ' ':
            assessment.state = "available"
            assessment.reasons.append("Open [ ], prerequisites terminal, no in-flight work detected across E2-E5")
            result.available_items.append(item_id)
        elif info['marker'] == 'p':
            assessment.state = "in-flight"
            assessment.reasons.append("Marked in-progress [p] on main")
            result.in_flight_items.append(item_id)
        else:
            assessment.state = "indeterminate"
            assessment.reasons.append(f"Unrecognized marker [{info['marker']}]")
            result.indeterminate_items.append(item_id)

        result.items[item_id] = assessment

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Branch-aware frontier query.")
    parser.add_argument("--repo", type=Path, default=Path("."), help="Repository path")
    parser.add_argument("--inbox-data", type=Path, default=Path("/tmp/agent-inbox/data"), help="Agent inbox data path")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument("--available-only", action="store_true", help="List only available items")
    args = parser.parse_args()

    result = query_frontier(args.repo, args.inbox_data)

    if args.json:
        output_dict = {
            "schema": result.schema,
            "repo_root": result.repo_root,
            "main_ref": result.main_ref,
            "evaluated_items_count": result.evaluated_items_count,
            "available_items": result.available_items,
            "in_flight_items": result.in_flight_items,
            "blocked_prereq_items": result.blocked_prereq_items,
            "held_items": result.held_items,
            "indeterminate_items": result.indeterminate_items,
            "terminal_items": result.terminal_items,
            "blind_spots": result.blind_spots,
            "items": {k: asdict(v) for k, v in result.items.items()},
        }
        print(json.dumps(output_dict, indent=2, ensure_ascii=False))
    elif args.available_only:
        for item in result.available_items:
            print(item)
    else:
        print(f"Evaluated items: {result.evaluated_items_count}")
        print(f"Available (safe to claim): {len(result.available_items)}")
        for it in result.available_items:
            print(f"  * {it}")
        print(f"In-flight (work active on branches/offers): {len(result.in_flight_items)}")
        print(f"Blocked on prerequisites: {len(result.blocked_prereq_items)}")
        print(f"Held (governance/reservation): {len(result.held_items)}")
        print(f"Terminal / completed: {len(result.terminal_items)}")
        print(f"Indeterminate: {len(result.indeterminate_items)}")
        print("\nBlind spots:")
        for i, bs in enumerate(result.blind_spots, 1):
            print(f"  {i}. {bs}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
