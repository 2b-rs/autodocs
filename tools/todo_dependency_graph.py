#!/usr/bin/env python3
"""
todo_dependency_graph.py

Parses a TODO.md following the Feature/Task/Subtask ID scheme and renders a
Graphviz dependency graph where each Feature is drawn as a cluster ("box")
containing its open (non-"[x]") Tasks/Subtasks as nodes.

No third-party Python packages are required. The script emits raw DOT and then
invokes the Graphviz `dot` binary directly.
"""

import argparse
import re
import shlex
import subprocess
import sys
from pathlib import Path

FEATURE_RE = re.compile(r'^##\s*Feature:\s*(\d{4})\s*(?:\u2014|--|-)?\s*(.*)$')
TASK_RE = re.compile(
    r'^-\s*\[(?P<mark>[ xup?])\]\s*'
    r'(?:\*\*)?(?P<id>\d+-\d+(?:\.\d+)?)(?:\*\*)?\s*'
    r'(?P<text>.*)$'
)
PREREQ_BLOCK_RE = re.compile(r'PREREQ:\s*(?P<body>.+?)(?:\s*(?:\u2014|--)\s|\s*$)')
PREREQ_ITEM_RE = re.compile(r'(\d{4}(?:-\d+(?:\.\d+)?)?)\s*:\s*(\d{4}(?:-\d+(?:\.\d+)?)?)')
SOFT_RE = re.compile(r'\(soft\b', re.IGNORECASE)

FEATURE_COLORS = [
    '#cfe8ff', '#d6ecff', '#d9f2d9', '#ffe0cc',
    '#ffd6d6', '#ffe680', '#ffe9cc', '#e6dcff',
    '#c9f7f5', '#f7d9e3', '#e3f7c9', '#d9d9f7',
]


def dot_quote(s: str) -> str:
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


class Task:
    __slots__ = ('id', 'feature_id', 'mark', 'text', 'prereqs')

    def __init__(self, id_, feature_id, mark, text):
        self.id = id_
        self.feature_id = feature_id
        self.mark = mark
        self.text = text
        self.prereqs = []

    @property
    def done(self):
        return self.mark == 'x'


class Feature:
    __slots__ = ('id', 'name', 'tasks')

    def __init__(self, id_, name):
        self.id = id_
        self.name = name
        self.tasks = []

    @property
    def done(self):
        return len(self.tasks) > 0 and all(t.done for t in self.tasks)


def parse_todo(path: Path):
    features = {}
    order = []
    current_feature = None

    with path.open(encoding='utf-8') as fh:
        for raw_line in fh:
            line = raw_line.rstrip('\n')

            m_feat = FEATURE_RE.match(line.strip())
            if m_feat:
                fid, name = m_feat.group(1), m_feat.group(2).strip()
                if fid not in features:
                    features[fid] = Feature(fid, name)
                    order.append(fid)
                current_feature = features[fid]
                continue

            m_task = TASK_RE.match(line.strip())
            if m_task and current_feature is not None:
                tid = m_task.group('id')
                mark = m_task.group('mark')
                text = m_task.group('text')
                tid_feature = tid.split('-', 1)[0]
                feature = features.get(tid_feature, current_feature)
                task = Task(tid, feature.id, mark, text)

                m_block = PREREQ_BLOCK_RE.search(text)
                if m_block:
                    body = m_block.group('body')
                    is_soft = bool(SOFT_RE.search(text))
                    for m_item in PREREQ_ITEM_RE.finditer(body):
                        _src, dst = m_item.group(1), m_item.group(2)
                        task.prereqs.append((dst, is_soft))

                feature.tasks.append(task)

    return [features[fid] for fid in order]


def classify_edge(src_task: Task, dst_id: str):
    is_soft = any(dst == dst_id and soft for dst, soft in src_task.prereqs)
    dst_is_feature_only = '-' not in dst_id
    same_feature = dst_id.split('-', 1)[0] == src_task.feature_id

    if is_soft:
        return 'soft_cross'
    if same_feature and not dst_is_feature_only:
        return 'explicit_same'
    if dst_is_feature_only:
        return 'implicit_cross'
    return 'explicit_cross'


def build_dot(features, include_done=False):
    live_features = [f for f in features if include_done or not f.done]

    all_task_ids = set()
    for f in live_features:
        for t in f.tasks:
            if include_done or not t.done:
                all_task_ids.add(t.id)
    live_feature_ids = {f.id for f in live_features}

    lines = []
    lines.append('digraph todo_dependency_graph {')
    lines.append('  rankdir=LR;')
    lines.append('  splines=true;')
    lines.append('  overlap=false;')
    lines.append('  bgcolor="white";')
    lines.append('  pad="0.3";')
    lines.append('  nodesep="0.25";')
    lines.append('  ranksep="0.8";')
    lines.append('  node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize="10", margin="0.08,0.05"];')
    lines.append('  edge [fontname="Helvetica", fontsize="9"];')

    edges = []

    for idx, feature in enumerate(live_features):
        color = FEATURE_COLORS[idx % len(FEATURE_COLORS)]
        open_tasks = [t for t in feature.tasks if include_done or not t.done]
        if not open_tasks:
            continue

        lines.append(f'  subgraph cluster_{feature.id} {{')
        label = f'{feature.id} — {feature.name}' if feature.name else feature.id
        lines.append(f'    label={dot_quote(label)};')
        lines.append('    style="rounded,filled";')
        lines.append('    color="#777777";')
        lines.append(f'    fillcolor={dot_quote(color)};')
        lines.append('    penwidth="1.2";')
        lines.append('    node [fillcolor="white"];')
        lines.append(f'    {dot_quote(feature.id)} [label={dot_quote(feature.id)}, shape=tab, fillcolor={dot_quote(color)}, style="filled,bold"];')
        for t in open_tasks:
            lines.append(f'    {dot_quote(t.id)} [label={dot_quote(t.id)}];')
        lines.append('  }')

        for t in open_tasks:
            for dst_id, _is_soft in t.prereqs:
                dst_is_feature_only = '-' not in dst_id
                target_alive = dst_id in all_task_ids or (dst_is_feature_only and dst_id in live_feature_ids)
                if not target_alive:
                    continue
                edges.append((t.id, dst_id, classify_edge(t, dst_id)))

    styles = {
        'explicit_same':  'color="black", penwidth="1.2"',
        'explicit_cross': 'color="#1f4e79", penwidth="1.4"',
        'implicit_cross': 'color="crimson", penwidth="1.5"',
        'soft_cross':     'color="gray50", penwidth="1.2", style="dashed"',
    }
    for src, dst, kind in edges:
        lines.append(f'  {dot_quote(src)} -> {dot_quote(dst)} [{styles[kind]}];')

    lines.append('  subgraph cluster_legend {')
    lines.append('    label="Legend";')
    lines.append('    style="rounded,dashed";')
    lines.append('    color="#999999";')
    lines.append('    "L1" [label="same-feature / explicit", fillcolor="white"];')
    lines.append('    "L2" [label="cross-feature / explicit", fillcolor="white"];')
    lines.append('    "L3" [label="cross-feature / implicit", fillcolor="white"];')
    lines.append('    "L4" [label="cross-feature / soft", fillcolor="white"];')
    lines.append('    "L1" -> "L1" [color="black", penwidth="1.2"];')
    lines.append('    "L2" -> "L2" [color="#1f4e79", penwidth="1.4"];')
    lines.append('    "L3" -> "L3" [color="crimson", penwidth="1.5"];')
    lines.append('    "L4" -> "L4" [color="gray50", penwidth="1.2", style="dashed"];')
    lines.append('  }')
    lines.append('}')

    node_count = len(all_task_ids)
    edge_count = len(edges)
    return '\n'.join(lines) + '\n', node_count, edge_count, len(live_features)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', default='TODO.md')
    ap.add_argument('--output', default='todo_dependency_graph')
    ap.add_argument('--format', default='png')
    ap.add_argument('--include-done', action='store_true')
    ap.add_argument('--dot-binary', default='dot')
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.is_file():
        print(f'ERROR: input file not found: {in_path}', file=sys.stderr)
        return 1

    features = parse_todo(in_path)
    if not features:
        print("ERROR: no '## Feature: XXXX — ...' headings found in input.", file=sys.stderr)
        return 2

    total_tasks = sum(len(f.tasks) for f in features)
    if total_tasks == 0:
        print("ERROR: features found, but no '- [ ] **XXXX-YY** ...' tasks parsed.", file=sys.stderr)
        return 2

    dot_text, n_nodes, n_edges, n_live_features = build_dot(features, include_done=args.include_done)
    out_base = Path(args.output)
    dot_path = out_base.with_suffix('.dot')
    out_path = out_base.with_suffix(f'.{args.format}')
    dot_path.write_text(dot_text, encoding='utf-8')

    cmd = [args.dot_binary, f'-T{args.format}', str(dot_path), '-o', str(out_path)]
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print(f"ERROR: Graphviz binary not found: {args.dot_binary}", file=sys.stderr)
        return 3
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Graphviz failed with exit code {e.returncode}: {' '.join(shlex.quote(x) for x in cmd)}", file=sys.stderr)
        return 4

    n_features_total = len(features)
    n_features_done = sum(1 for f in features if f.done)
    print(f"Parsed {n_features_total} feature(s) ({n_features_done} fully done), {total_tasks} task(s) total.")
    print(f"Rendered graph with {n_nodes} open task node(s), {n_live_features} live feature cluster(s), and {n_edges} dependency edge(s).")
    print(f"DOT written to: {dot_path}")
    print(f"Output written to: {out_path}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
