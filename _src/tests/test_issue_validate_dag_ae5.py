"""AE-5 property evidence for DAG acyclicity (IV0935) and writer uniqueness (IV0937).

DEC-0038-004 AE-5: bounded-exhaustive checks against named reference oracles.
Does not restamp 0037-09.01–.03 product tests; Chapel DAG product is unchanged.
"""
from __future__ import annotations

import importlib.util
import itertools
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "issue_validate", ROOT / "_src/tools/issue_validate.py")
VALIDATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATE)

# Finite enumeration boundary (n labeled stages, all simple directed graphs
# including self-loops): 2^(n*n) graphs for n in {1,2,3}.
ACYCLICITY_N_MAX = 3
# Writer maps: each of n stages writes exactly one of n output labels: n^n.
WRITER_N_MAX = 3
AE5_SEED = None  # deterministic exhaustive enumeration; no RNG

INVARIANT_IV0935 = (
    "A stage graph is IV0935-clean iff every depends_on target exists, no stage "
    "depends on itself, and the directed depends_on graph is acyclic."
)
INVARIANT_IV0937 = (
    "A stage list is IV0937-clean iff stage ids are unique and each output path "
    "has at most one distinct writer stage id."
)


def reference_dfs_cycle_oracle(nodes, depends_on):
    """Independent DFS back-edge oracle (not the product visitor).

    ``depends_on[node]`` is an iterable of successor ids (dependency targets).
    Returns True iff a back edge exists among ``nodes``.
    """
    node_set = set(nodes)
    color = {}

    def visit(node):
        color[node] = 1
        for nxt in depends_on.get(node, ()):
            if nxt not in node_set:
                continue
            if color.get(nxt) == 1:
                return True
            if color.get(nxt, 0) == 0 and visit(nxt):
                return True
        color[node] = 2
        return False

    for node in nodes:
        if color.get(node, 0) == 0 and visit(node):
            return True
    return False


def oracle_iv0935(stage_ids, depends_map):
    """Named reference oracle for IV0935 applicability."""
    known = set(stage_ids)
    for sid in stage_ids:
        for dep in depends_map.get(sid, ()):
            if dep == sid:
                return True
            if dep not in known:
                return True
    return reference_dfs_cycle_oracle(stage_ids, depends_map)


def oracle_iv0937(stages):
    """Named reference oracle for IV0937 applicability (ids and output owners)."""
    seen = set()
    owners = {}
    for stage in stages:
        sid = stage["id"]
        if sid in seen:
            return True
        seen.add(sid)
        for output in stage.get("outputs") or []:
            previous = owners.get(output)
            if previous is not None and previous != sid:
                return True
            owners[output] = sid
    return False


def _stage(stage_id, depends, outputs):
    return {
        "id": stage_id,
        "argv": ["python3", "-c", "pass"],
        "depends_on": list(depends),
        "inputs": [{"glob": "issues/**/*.md", "kind": "canonical"}],
        "outputs": list(outputs),
        "sole_writer": stage_id,
        "required": False,
        "retention": "committed",
        "privacy": "internal",
        "determinism": "byte",
        "promotion_group": "ae5",
        "cleanup": "none",
        "validator": "ae5-oracle",
    }


def _manifest(stages):
    return {"schema": VALIDATE.DAG_SCHEMA, "stages": stages}


def _rules(manifest):
    diagnostics, _, _ = VALIDATE._dag_structural_diagnostics(
        manifest, "ae5-synthetic.json", required_ids=())
    return {item.rule for item in diagnostics}


def _graphs_n(n):
    labels = tuple(f"s{i}" for i in range(n))
    bits = n * n
    for mask in range(1 << bits):
        depends = {label: [] for label in labels}
        bit = 0
        for src in range(n):
            for dst in range(n):
                if mask & (1 << bit):
                    depends[labels[src]].append(labels[dst])
                bit += 1
        yield labels, depends, mask


class DagAe5PropertyTest(unittest.TestCase):
    """Bounded-exhaustive AE-5 evidence; executed case counts are asserted."""

    def test_iv0935_acyclicity_exhaustive_small_dags(self):
        executed = 0
        planted_cycles = 0
        clean = 0
        for n in range(1, ACYCLICITY_N_MAX + 1):
            for labels, depends, _mask in _graphs_n(n):
                stages = [
                    _stage(sid, depends[sid], [f"out/{sid}.json"])
                    for sid in labels
                ]
                expect = oracle_iv0935(labels, depends)
                rules = _rules(_manifest(stages))
                has = "IV0935" in rules
                self.assertEqual(
                    has, expect,
                    msg=f"n={n} depends={depends} rules={rules}",
                )
                executed += 1
                if expect:
                    planted_cycles += 1
                else:
                    clean += 1
        # 2^(1^2)+2^(2^2)+2^(3^2) = 2+16+512
        self.assertEqual(executed, 530)
        self.assertGreater(planted_cycles, 0)
        self.assertGreater(clean, 0)
        self.assertEqual(planted_cycles + clean, executed)
        DagAe5PropertyTest.iv0935_executed = executed

    def test_iv0937_writer_uniqueness_exhaustive_maps(self):
        executed = 0
        planted_dup = 0
        unique = 0
        for n in range(1, WRITER_N_MAX + 1):
            labels = tuple(f"s{i}" for i in range(n))
            outputs = tuple(f"out/{i}.json" for i in range(n))
            for assignment in itertools.product(range(n), repeat=n):
                stages = [
                    _stage(labels[i], [], [outputs[assignment[i]]])
                    for i in range(n)
                ]
                expect = oracle_iv0937(stages)
                rules = _rules(_manifest(stages))
                has = "IV0937" in rules
                self.assertEqual(
                    has, expect,
                    msg=f"n={n} assignment={assignment} rules={rules}",
                )
                executed += 1
                if expect:
                    planted_dup += 1
                else:
                    unique += 1
        # 1^1 + 2^2 + 3^3 = 1+4+27
        self.assertEqual(executed, 32)
        self.assertGreater(planted_dup, 0)
        self.assertGreater(unique, 0)
        self.assertEqual(planted_dup + unique, executed)
        DagAe5PropertyTest.iv0937_map_executed = executed

    def test_iv0937_duplicate_stage_ids_and_multi_output_collision(self):
        """Adjacent contract cases (AE-4/AE-5 neighbors of the maps)."""
        executed = 0
        # Duplicate ids, distinct outputs: oracle and product must both fire IV0937.
        dup_ids = [
            _stage("same", [], ["out/a.json"]),
            _stage("same", [], ["out/b.json"]),
        ]
        self.assertTrue(oracle_iv0937(dup_ids))
        self.assertIn("IV0937", _rules(_manifest(dup_ids)))
        executed += 1
        # Two outputs on one stage vs two stages sharing one path.
        labels = ("s0", "s1")
        for a0, a1, b0, b1 in itertools.product(("x", "y"), repeat=4):
            stages = [
                _stage(labels[0], [], [f"out/{a0}.json", f"out/{a1}.json"]),
                _stage(labels[1], [], [f"out/{b0}.json", f"out/{b1}.json"]),
            ]
            expect = oracle_iv0937(stages)
            self.assertEqual("IV0937" in _rules(_manifest(stages)), expect)
            executed += 1
        # 1 + 16
        self.assertEqual(executed, 17)
        DagAe5PropertyTest.iv0937_adj_executed = executed

    def test_iv0935_unknown_dependency_neighbor(self):
        """Adjacent: unknown target is IV0935 even when the known subgraph is a DAG."""
        stages = [_stage("s0", ["ghost"], ["out/s0.json"])]
        self.assertTrue(oracle_iv0935(("s0",), {"s0": ("ghost",)}))
        self.assertIn("IV0935", _rules(_manifest(stages)))
        chain = [
            _stage("s0", [], ["out/s0.json"]),
            _stage("s1", ["s0"], ["out/s1.json"]),
        ]
        self.assertFalse(oracle_iv0935(("s0", "s1"), {"s0": (), "s1": ("s0",)}))
        self.assertNotIn("IV0935", _rules(_manifest(chain)))
        DagAe5PropertyTest.iv0935_adj_executed = 2

    def test_ae5_executed_case_count_is_named(self):
        """Replay/count record for DEC-0038-004 AE-5 (exhaustive, seed=None)."""
        self.test_iv0935_acyclicity_exhaustive_small_dags()
        self.test_iv0937_writer_uniqueness_exhaustive_maps()
        self.test_iv0937_duplicate_stage_ids_and_multi_output_collision()
        self.test_iv0935_unknown_dependency_neighbor()
        total = (
            DagAe5PropertyTest.iv0935_executed
            + DagAe5PropertyTest.iv0937_map_executed
            + DagAe5PropertyTest.iv0937_adj_executed
            + DagAe5PropertyTest.iv0935_adj_executed
        )
        # 530 + 32 + 17 + 2
        self.assertEqual(total, 581)
        self.assertIsNone(AE5_SEED)


if __name__ == "__main__":
    unittest.main()
