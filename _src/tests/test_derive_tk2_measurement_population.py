#!/usr/bin/env python3
"""Tests for `_src/tools/derive_tk2_measurement_population.py`.

Two rules this repository learned the hard way are applied to this suite itself:

* The tool is loaded **by compiling its source**, never from a `.pyc` cache
  (`0038-34` / Tom-Georgiou: CPython validates a cached `.pyc` only against
  `(mtime, size)`, so an in-process import can silently measure stale bytecode
  while reporting on "the current source").
* Every case runs against a **hermetic fixture repository** built here, never
  against the live repository, so a result cannot depend on today's backlog.

The population contract under test: exactly the first 20 Task-level items
(`XXXX-YY`; Features `XXXX` and Subtasks `XXXX-YY.ZZ` excluded) whose
authoritative disposition first becomes `[x]`/`[w]` after the activation
reference, ordered by terminal-transition event with the Task ID as the
deterministic tie-breaker.
"""
import importlib.util
import os
import subprocess
import tempfile
import types
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2] / "_src" / "tools" / "derive_tk2_measurement_population.py"
ACTIVATION = "2026-08-20T08:02:27+00:00"


def load_tool_from_source() -> types.ModuleType:
    """Compile the tool from its source file; never load a cached `.pyc`."""
    source = TOOL.read_text(encoding="utf-8")
    module = types.ModuleType("tk2_tool_under_test")
    module.__file__ = str(TOOL)
    exec(compile(source, str(TOOL), "exec"), module.__dict__)  # noqa: S102 - deliberate
    return module


class Fixture:
    """A throwaway git repository with a scripted TODO.md/DONE.md history."""

    def __init__(self, tmp: str):
        self.path = Path(tmp)
        self._git("init", "-q", "-b", "main")
        self._git("config", "user.email", "fixture@example.invalid")
        self._git("config", "user.name", "fixture")
        (self.path / "DONE.md").write_text("# DONE\n", encoding="utf-8")

    def _git(self, *args: str) -> str:
        return subprocess.run(
            ["/usr/bin/git", "-C", str(self.path), *args],
            capture_output=True, text=True, check=True,
        ).stdout

    def commit(self, todo_body: str, when: str) -> str:
        (self.path / "TODO.md").write_text(todo_body, encoding="utf-8")
        self._git("add", "TODO.md", "DONE.md")
        env = {**os.environ, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
        subprocess.run(
            ["/usr/bin/git", "-C", str(self.path), "commit", "-q", "-m", f"state at {when}"],
            check=True, env=env, capture_output=True, text=True,
        )
        return self._git("rev-parse", "HEAD").strip()

    def run_tool(self):
        os.environ["TK2_GITDIR"] = str(self.path / ".git")
        os.environ["TK2_ACTIVATION"] = ACTIVATION
        try:
            return load_tool_from_source()
        finally:
            pass


def line(marker: str, task: str) -> str:
    return f"- [{marker}] **{task}** something\n"


class PopulationTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.fx = Fixture(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        for var in ("TK2_GITDIR", "TK2_ACTIVATION"):
            self.addCleanup(os.environ.pop, var, None)

    def _population(self):
        mod = self.fx.run_tool()
        hist = mod.commits()
        from datetime import datetime
        activation = datetime.fromisoformat(ACTIVATION)
        baseline = None
        for sha, ts in hist:
            if ts <= activation:
                baseline = sha
            else:
                break
        prev = mod.markers_at(baseline) if baseline else {}
        seen = {t for t, m in prev.items() if m in "xw"}
        out = []
        for sha, ts in hist:
            if ts <= activation:
                continue
            cur = mod.markers_at(sha)
            for tid in sorted(t for t, m in cur.items() if m in "xw" and t not in seen):
                seen.add(tid)
                out.append(tid)
                if len(out) == 20:
                    return out
        return out

    # --- object recognition -------------------------------------------------
    def test_marker_matches_task_level_item(self):
        mod = self.fx.run_tool()
        self.assertEqual(mod.MARKER.findall(line("x", "0038-14")), [("x", "0038-14")])

    def test_marker_rejects_subtask(self):
        """Neighbour case, red before the guard existed: 0038-14.01 must not match."""
        mod = self.fx.run_tool()
        self.assertEqual(mod.MARKER.findall(line("x", "0038-14.01")), [])

    def test_marker_rejects_feature(self):
        mod = self.fx.run_tool()
        self.assertEqual(mod.MARKER.findall(line("x", "0038")), [])

    def test_marker_ignores_non_terminal_markers(self):
        mod = self.fx.run_tool()
        found = {t for m, t in mod.MARKER.findall(
            line(" ", "0001-01") + line("p", "0001-02") + line("x", "0001-03"))}
        self.assertEqual(found, {"0001-01", "0001-02", "0001-03"})

    # --- population semantics ----------------------------------------------
    def test_items_terminal_before_activation_are_excluded(self):
        self.fx.commit(line("x", "0001-01") + line(" ", "0001-02"), "2026-08-19T00:00:00+00:00")
        self.fx.commit(line("x", "0001-01") + line("x", "0001-02"), "2026-08-21T00:00:00+00:00")
        self.assertEqual(self._population(), ["0001-02"])

    def test_tie_break_is_task_id_within_one_event(self):
        self.fx.commit(line(" ", "0002-03") + line(" ", "0002-01") + line(" ", "0002-02"),
                       "2026-08-19T00:00:00+00:00")
        self.fx.commit(line("x", "0002-03") + line("x", "0002-01") + line("x", "0002-02"),
                       "2026-08-21T00:00:00+00:00")
        self.assertEqual(self._population(), ["0002-01", "0002-02", "0002-03"])

    def test_order_follows_transition_event_not_id(self):
        self.fx.commit(line(" ", "0003-01") + line(" ", "0003-02"), "2026-08-19T00:00:00+00:00")
        self.fx.commit(line(" ", "0003-01") + line("x", "0003-02"), "2026-08-21T00:00:00+00:00")
        self.fx.commit(line("x", "0003-01") + line("x", "0003-02"), "2026-08-22T00:00:00+00:00")
        self.assertEqual(self._population(), ["0003-02", "0003-01"])

    def test_w_counts_as_terminal(self):
        self.fx.commit(line(" ", "0004-01"), "2026-08-19T00:00:00+00:00")
        self.fx.commit(line("w", "0004-01"), "2026-08-21T00:00:00+00:00")
        self.assertEqual(self._population(), ["0004-01"])

    def test_population_caps_at_twenty(self):
        ids = [f"0005-{i:02d}" for i in range(1, 26)]
        self.fx.commit("".join(line(" ", t) for t in ids), "2026-08-19T00:00:00+00:00")
        self.fx.commit("".join(line("x", t) for t in ids), "2026-08-21T00:00:00+00:00")
        pop = self._population()
        self.assertEqual(len(pop), 20)
        self.assertEqual(pop, sorted(ids)[:20])

    def test_fewer_than_twenty_is_reported_not_padded(self):
        """The not-yet-mature branch: the tool must under-report, never invent."""
        self.fx.commit(line(" ", "0006-01"), "2026-08-19T00:00:00+00:00")
        self.fx.commit(line("x", "0006-01"), "2026-08-21T00:00:00+00:00")
        self.assertEqual(len(self._population()), 1)

    def test_activation_boundary_is_exclusive_of_earlier_transitions(self):
        """A transition strictly before activation never enters the population."""
        self.fx.commit(line("x", "0007-01"), "2026-08-20T08:02:26+00:00")
        self.fx.commit(line("x", "0007-01") + line("x", "0007-02"), "2026-08-20T08:02:28+00:00")
        self.assertEqual(self._population(), ["0007-02"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
