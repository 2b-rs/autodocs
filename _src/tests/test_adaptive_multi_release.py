"""Adaptive multi-release version integrity.

The live corpus at spec/versions/AUTOSAR/AP/record is read-only here.
record_version() runs against a temporary VERSIONS_ROOT. Tests that write
check that the live files keep their names, sizes, and mtimes.
"""
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SRC / "tools"))

import asof_view as av  # noqa: E402
import lib_docmodel as dm  # noqa: E402
import version_store as vs  # noqa: E402
from version_id import parse_version_id, requirement_version_id  # noqa: E402

RECORD_DIR = SRC / "spec" / "versions" / "AUTOSAR" / "AP" / "record"
REAL_VERSIONS_ROOT = vs.VERSIONS_ROOT
REQUIRED_FIELDS = ("version_id", "canonical_id", "release", "content", "recorded_at")
NAMED_RECORDS = ("SWS_CORE_00017", "SWS_AIDSM_10706")


def corpus_fingerprint(record_dir: Path) -> tuple:
    """Name, size, and mtime of every live JSONL file.

    record_version() replaces the file, so a write changes mtime even when
    the byte count stays the same. The schema test reads the bytes itself.
    """
    rows = []
    for path in sorted(p for p in record_dir.glob("*.jsonl") if p.is_file()):
        stat = path.stat()
        rows.append((path.name, stat.st_size, stat.st_mtime_ns))
    return tuple(rows)


def raw_versions(stem: str) -> list[dict]:
    path = RECORD_DIR / f"{stem}.jsonl"
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def release_hit(rows: list[dict], release: str) -> dict | None:
    eligible = [row for row in rows if row["release"] <= release]
    if not eligible:
        return None
    return max(eligible, key=lambda row: row["release"])


def date_hit(rows: list[dict], date: str) -> dict | None:
    eligible = [row for row in rows if row["recorded_at"] <= date]
    if not eligible:
        return None
    return max(eligible, key=lambda row: row["recorded_at"])


def audit_ap_record_jsonl(record_dir: Path) -> list[str]:
    """Return contract violations. An empty list means every line is a version object."""
    problems: list[str] = []
    if not record_dir.is_dir():
        return [f"{record_dir}: missing directory"]
    files = sorted(path for path in record_dir.glob("*.jsonl") if path.is_file())
    if not files:
        problems.append(f"{record_dir}: no jsonl files")
    seen_ids: dict[str, str] = {}
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            problems.append(f"{path.name}: not utf-8 ({exc.reason})")
            continue
        if text and not text.endswith("\n"):
            problems.append(f"{path.name}: missing trailing newline")
        seen_in_file: set[str] = set()
        for lineno, line in enumerate(text.splitlines(), 1):
            where = f"{path.name}:{lineno}"
            if not line.strip():
                problems.append(f"{where}: blank line")
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                problems.append(f"{where}: invalid json ({exc.msg})")
                continue
            if not isinstance(obj, dict):
                problems.append(f"{where}: expected object, got {type(obj).__name__}")
                continue
            missing = [key for key in REQUIRED_FIELDS if key not in obj]
            if missing:
                problems.append(f"{where}: missing {', '.join(missing)}")
            for key in REQUIRED_FIELDS:
                if key in obj and not isinstance(obj[key], str):
                    problems.append(
                        f"{where}: {key} is {type(obj[key]).__name__}, expected str"
                    )
            if "meta" in obj and not isinstance(obj["meta"], dict):
                problems.append(
                    f"{where}: meta is {type(obj['meta']).__name__}, expected object"
                )
            if "provenance" in obj and not isinstance(obj["provenance"], dict):
                problems.append(
                    f"{where}: provenance is {type(obj['provenance']).__name__}, expected object"
                )
            canonical_id = obj.get("canonical_id")
            expected_cid = f"AUTOSAR/AP/record/{path.stem}"
            if isinstance(canonical_id, str) and canonical_id != expected_cid:
                problems.append(f"{where}: canonical_id {canonical_id} != {expected_cid}")
            version_id = obj.get("version_id")
            release = obj.get("release")
            content = obj.get("content")
            if isinstance(version_id, str):
                if version_id in seen_in_file:
                    problems.append(f"{where}: duplicate version_id")
                seen_in_file.add(version_id)
                previous = seen_ids.get(version_id)
                if previous is not None and previous != path.name:
                    problems.append(f"{where}: version_id already used in {previous}")
                seen_ids.setdefault(version_id, path.name)
                if parse_version_id(version_id) is None:
                    problems.append(f"{where}: unparsable version_id")
                elif (
                    isinstance(canonical_id, str)
                    and isinstance(release, str)
                    and isinstance(content, str)
                    and version_id != requirement_version_id(canonical_id, release, content)
                ):
                    problems.append(f"{where}: version_id does not match release and content")
            recorded_at = obj.get("recorded_at")
            if isinstance(recorded_at, str):
                try:
                    datetime.fromisoformat(recorded_at)
                except ValueError:
                    problems.append(f"{where}: recorded_at is not ISO-8601")
    return problems


def _version_line(canonical_id: str, release: str, content: str, **extra) -> str:
    obj = {
        "version_id": requirement_version_id(canonical_id, release, content),
        "canonical_id": canonical_id,
        "release": release,
        "content": content,
        "recorded_at": "2026-01-01T00:00:00+00:00",
    }
    obj.update(extra)
    return json.dumps(obj, ensure_ascii=False) + "\n"


def render_history(record_id, status=None, history=None, **kwargs) -> str:
    if status is None and "status" not in kwargs:
        status = {"state": "valid/auto-approved", "reason": "verified"}
    if history is None and "history" not in kwargs:
        history = [{
            "date": "2026-08-13",
            "actor": "tool",
            "to": "valid/auto-approved",
            "reason": "baseline",
        }]
    return dm._render_rec_history_html(record_id, status, history, **kwargs)


class _CorpusGuard(unittest.TestCase):
    def setUp(self):
        self.assertEqual(REAL_VERSIONS_ROOT, SRC / "spec" / "versions")


class _TempStore(_CorpusGuard):
    def setUp(self):
        super().setUp()
        self._live_fp = corpus_fingerprint(RECORD_DIR)
        self._tmp = tempfile.TemporaryDirectory(dir="/tmp")
        self.addCleanup(self._tmp.cleanup)
        redirected = Path(self._tmp.name) / "versions"
        self.assertFalse(redirected.resolve().is_relative_to(REAL_VERSIONS_ROOT.resolve()))
        self._orig_now = vs._now
        vs.VERSIONS_ROOT = redirected
        self.addCleanup(setattr, vs, "VERSIONS_ROOT", REAL_VERSIONS_ROOT)
        self.addCleanup(setattr, vs, "_now", self._orig_now)

    def tearDown(self):
        vs.VERSIONS_ROOT = REAL_VERSIONS_ROOT
        vs._now = self._orig_now
        self.assertEqual(
            corpus_fingerprint(RECORD_DIR),
            self._live_fp,
            "live adaptive version store was modified",
        )


class AdaptiveApRecordJsonlTests(_CorpusGuard):
    def test_live_ap_record_jsonl_matches_version_contract(self):
        problems = audit_ap_record_jsonl(RECORD_DIR)
        self.assertEqual(problems, [])
        self.assertGreaterEqual(len(list(RECORD_DIR.glob("*.jsonl"))), 1)
        for stem in NAMED_RECORDS:
            rows = raw_versions(stem)
            self.assertGreaterEqual(len(rows), 1, stem)
            self.assertEqual(vs.list_versions(f"AUTOSAR/AP/record/{stem}"), rows)
            for row in rows:
                self.assertEqual(
                    row["version_id"],
                    requirement_version_id(row["canonical_id"], row["release"], row["content"]),
                )

    def test_audit_flags_corrupt_lines_and_accepts_a_valid_line(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            root = Path(tmp)
            good_cid = "AUTOSAR/AP/record/SWS_GOOD"
            (root / "SWS_GOOD.jsonl").write_text(
                _version_line(good_cid, "R25-11", "body", meta={}),
                encoding="utf-8",
            )
            (root / "SWS_BADJSON.jsonl").write_text("{,\n", encoding="utf-8")
            (root / "SWS_ARRAY.jsonl").write_text("[]\n", encoding="utf-8")
            (root / "SWS_MISSING.jsonl").write_text(
                json.dumps({
                    "version_id": "AUTOSAR/AP/record/SWS_MISSING@rel:R25-11#00000000",
                    "canonical_id": "AUTOSAR/AP/record/SWS_MISSING",
                    "release": "R25-11",
                    "content": "body",
                }) + "\n",
                encoding="utf-8",
            )
            (root / "SWS_TYPE.jsonl").write_text(
                json.dumps({
                    "version_id": "AUTOSAR/AP/record/SWS_TYPE@rel:R25-11#00000000",
                    "canonical_id": "AUTOSAR/AP/record/SWS_TYPE",
                    "release": "R25-11",
                    "content": 5,
                    "recorded_at": "2026-01-01T00:00:00+00:00",
                }) + "\n",
                encoding="utf-8",
            )
            dup = _version_line("AUTOSAR/AP/record/SWS_DUP", "R25-11", "same")
            (root / "SWS_DUP.jsonl").write_text(dup + dup, encoding="utf-8")
            forged = json.loads(_version_line("AUTOSAR/AP/record/SWS_FORGED", "R25-11", "body"))
            suffix = "00000000" if not forged["version_id"].endswith("00000000") else "ffffffff"
            forged["version_id"] = forged["version_id"][:-8] + suffix
            (root / "SWS_FORGED.jsonl").write_text(
                json.dumps(forged) + "\n",
                encoding="utf-8",
            )
            (root / "SWS_NAME.jsonl").write_text(
                _version_line("AUTOSAR/AP/record/SWS_OTHER", "R25-11", "body"),
                encoding="utf-8",
            )
            (root / "SWS_BLANK.jsonl").write_text(
                _version_line("AUTOSAR/AP/record/SWS_BLANK", "R25-11", "body") + "\n",
                encoding="utf-8",
            )
            (root / "SWS_NONEWLINE.jsonl").write_text(
                _version_line("AUTOSAR/AP/record/SWS_NONEWLINE", "R25-11", "body").rstrip("\n"),
                encoding="utf-8",
            )
            (root / "SWS_META.jsonl").write_text(
                _version_line("AUTOSAR/AP/record/SWS_META", "R25-11", "body", meta=["nope"]),
                encoding="utf-8",
            )
            (root / "SWS_BADTIME.jsonl").write_text(
                _version_line("AUTOSAR/AP/record/SWS_BADTIME", "R25-11", "body", recorded_at="yesterday"),
                encoding="utf-8",
            )
            (root / "SWS_BYTES.jsonl").write_bytes(b"\xff\xfe\n")

            problems = audit_ap_record_jsonl(root)
            joined = "\n".join(problems)
            self.assertNotIn("SWS_GOOD.jsonl", joined)
            for fragment in (
                "SWS_BADJSON.jsonl:1: invalid json",
                "SWS_ARRAY.jsonl:1: expected object, got list",
                "SWS_MISSING.jsonl:1: missing recorded_at",
                "SWS_TYPE.jsonl:1: content is int, expected str",
                "SWS_DUP.jsonl:2: duplicate version_id",
                "SWS_FORGED.jsonl:1: version_id does not match release and content",
                "SWS_NAME.jsonl:1: canonical_id AUTOSAR/AP/record/SWS_OTHER != AUTOSAR/AP/record/SWS_NAME",
                "SWS_BLANK.jsonl:2: blank line",
                "SWS_NONEWLINE.jsonl: missing trailing newline",
                "SWS_META.jsonl:1: meta is list, expected object",
                "SWS_BADTIME.jsonl:1: recorded_at is not ISO-8601",
                "SWS_BYTES.jsonl: not utf-8",
            ):
                self.assertIn(fragment, joined, fragment)


class AdaptiveVersionWriteSafetyTests(_TempStore):
    def test_identical_recordings_do_not_duplicate_or_rewrite(self):
        cid = "AUTOSAR/AP/record/SWS_IDEMPOTENT_AUDIT"
        first = vs.record_version(cid, "R25-11", "same-body")
        path = vs._store_path(cid)
        original = path.read_bytes()
        self.assertEqual(vs.record_version(cid, "R25-11", "same-body"), first)
        self.assertEqual(
            vs.record_version(cid, "R25-11", "same-body", meta={"ignored": True}),
            first,
        )
        self.assertEqual(path.read_bytes(), original)
        versions = vs.list_versions(cid)
        self.assertEqual(len(versions), 1)
        self.assertEqual(versions[0]["version_id"], first)
        self.assertEqual(versions[0]["content"], "same-body")
        self.assertEqual(versions[0]["meta"], {})
        self.assertEqual(vs.get_version(first)["content"], "same-body")
        self.assertEqual(vs.record_version(cid, "R20-11", ""), vs.record_version(cid, "R20-11", ""))
        self.assertEqual(
            [row["content"] for row in vs.list_versions(cid) if row["release"] == "R20-11"],
            [""],
        )

    def test_changed_content_appends_without_rewriting_earlier_lines(self):
        cid = "AUTOSAR/AP/record/SWS_APPEND_AUDIT"
        first = vs.record_version(cid, "R25-11", "alpha", meta={"k": "first"})
        path = vs._store_path(cid)
        original = path.read_bytes()
        second = vs.record_version(cid, "R25-11", "größe")
        self.assertNotEqual(first, second)
        updated = path.read_bytes()
        self.assertTrue(updated.startswith(original))
        self.assertGreater(len(updated), len(original))
        after_second = path.read_bytes()
        self.assertEqual(vs.record_version(cid, "R25-11", "größe"), second)
        self.assertEqual(path.read_bytes(), after_second)
        spaced = vs.record_version(cid, "R25-11", "alpha ")
        self.assertNotEqual(spaced, first)
        rows = vs.list_versions(cid)
        self.assertEqual([row["content"] for row in rows], ["alpha", "größe", "alpha "])
        self.assertEqual(rows[0]["meta"], {"k": "first"})
        self.assertEqual(vs.get_version(first)["content"], "alpha")
        self.assertEqual(vs.get_version(second)["content"], "größe")
        self.assertIsNone(vs.get_version(requirement_version_id(cid, "R25-11", "missing")))
        self.assertIsNone(vs.get_version("not-a-version"))

    def test_non_canonical_id_writes_nothing(self):
        def files():
            if not vs.VERSIONS_ROOT.exists():
                return []
            return sorted(
                path.relative_to(vs.VERSIONS_ROOT).as_posix()
                for path in vs.VERSIONS_ROOT.rglob("*")
                if path.is_file()
            )

        before = files()
        for record_id in ("SWS_CORE_00017", "", "AUTOSAR/record/SWS_CORE_00017"):
            with self.assertRaises(ValueError):
                vs.record_version(record_id, "R25-11", "nope")
        self.assertEqual(files(), before)


class AdaptiveHistoryRenderTests(_CorpusGuard):
    def test_renderer_stays_empty_without_status_history_or_meta(self):
        self.assertEqual(dm._render_rec_history_html("SWS_CORE_00017", None, None), "")
        self.assertEqual(dm._render_rec_history_html("SWS_CORE_00017", {}, []), "")
        self.assertEqual(
            dm._render_rec_history_html("", {"state": "valid"}, [{"date": "2026-08-13"}]),
            "",
        )

    def test_live_records_render_badge_and_timeline_from_stored_ids(self):
        for stem in NAMED_RECORDS:
            rows = raw_versions(stem)
            canonical_id = f"AUTOSAR/AP/record/{stem}"
            for record_id in (stem, canonical_id):
                html = render_history(record_id)
                active = rows[-1]
                short = active["version_id"].split("@", 1)[-1]
                self.assertIn("rec-version-badge", html)
                self.assertIn(f"<code>{dm.esc(short)}</code>", html)
                self.assertIn(f"<code>{dm.esc(active['version_id'])}</code>", html)
                self.assertIn(f'data-canonical-id="{canonical_id}"', html)
                if len(rows) > 1:
                    self.assertIn("rec-version-timeline", html)
                    self.assertIn(f"Recorded Revisions ({len(rows)})", html)
                    for row in rows:
                        vid = row["version_id"]
                        self.assertIn(f'data-version-id="{dm.esc_attr(vid)}"', html)
                        self.assertIn(f'data-inspect-version="{dm.esc_attr(vid)}"', html)
                else:
                    self.assertNotIn("rec-version-timeline", html)

    def test_stored_versions_override_synthetic_rec_meta(self):
        rows = raw_versions("SWS_CORE_00017")
        canonical_id = "AUTOSAR/AP/record/SWS_CORE_00017"
        decoy_text = "decoy body that must not replace the stored snapshot"
        decoy_id = requirement_version_id(canonical_id, "R19-11", decoy_text)
        html = dm._render_rec_history_html(
            "SWS_CORE_00017",
            None,
            None,
            rec_meta={"release": "R19-11", "content_text": decoy_text},
        )
        self.assertIn("rec-version-badge", html)
        self.assertIn(rows[-1]["version_id"], html)
        self.assertNotIn(decoy_id, html)
        for row in rows:
            self.assertIn(row["version_id"], html)


class AdaptiveHistoryMarkupTests(_TempStore):
    def test_timeline_and_badge_use_recorded_version_ids(self):
        cid = "AUTOSAR/AP/record/SWS_RENDER_AUDIT"
        first = vs.record_version(cid, "R20-11", "one")
        second = vs.record_version(cid, "R25-11", "two")
        html = render_history(cid)
        self.assertIn("rec-version-badge", html)
        self.assertIn("rec-version-timeline", html)
        self.assertIn("Recorded Revisions (2)", html)
        self.assertIn(f"<code>{second.split('@', 1)[1]}</code>", html)
        self.assertIn(f"<code>{second}</code>", html)
        for vid in (first, second):
            self.assertIn(f'data-version-id="{vid}"', html)
            self.assertIn(f'data-inspect-version="{vid}"', html)
        self.assertIn('class="rec-version-entry is-active"', html)
        self.assertEqual(html.count('class="rec-version-entry'), 2)

        only = "AUTOSAR/AP/record/SWS_RENDER_ONE"
        only_id = vs.record_version(only, "R25-11", "solo")
        solo = render_history(only)
        self.assertIn("rec-version-badge", solo)
        self.assertIn(only_id, solo)
        self.assertNotIn("rec-version-timeline", solo)

    def test_release_markup_cannot_inject_a_tag(self):
        cid = "AUTOSAR/AP/record/SWS_ESCAPE_AUDIT"
        evil = 'R25-11"><img>'
        vs.record_version(cid, "R20-11", "safe")
        vs.record_version(cid, evil, "marked")
        html = render_history(cid)
        self.assertIn("rec-version-timeline", html)
        self.assertIn("rec-version-badge", html)
        self.assertNotIn("<img>", html)
        self.assertNotIn('"><img>', html)
        self.assertIn('value="R25-11&quot;&gt;&lt;img&gt;"', html)
        self.assertIn("&lt;img&gt;", html)


class AdaptiveAsOfViewTests(_CorpusGuard):
    def _assert_release(self, record_id: str, rows: list[dict], release: str):
        view = av.as_of_release(record_id, release)
        self.assertEqual(view["canonical_id"], rows[0]["canonical_id"])
        self.assertEqual(view["as_of"], {"kind": "release", "value": release})
        self.assertEqual(view["version"], release_hit(rows, release))
        self.assertIsInstance(view["decisions"], list)
        self.assertIsInstance(view["artifact_graph"], dict)
        for node, flags in view["artifact_graph"].items():
            self.assertIsInstance(node, str)
            self.assertIsInstance(flags["invalidated"], bool)
            self.assertIsInstance(flags["dismissed"], bool)
        if view["version"] is None:
            self.assertEqual(view["decisions"], [])
        else:
            self.assertIn(view["version"], rows)
        return view

    def _assert_date(self, record_id: str, rows: list[dict], date: str):
        view = av.as_of_date(record_id, date)
        self.assertEqual(view["canonical_id"], rows[0]["canonical_id"])
        self.assertEqual(view["as_of"], {"kind": "date", "value": date})
        self.assertEqual(view["version"], date_hit(rows, date))
        if view["version"] is None:
            self.assertEqual(view["decisions"], [])
        else:
            self.assertIn(view["version"], rows)
        return view

    def test_as_of_release_and_date_follow_stored_adaptive_lines(self):
        for stem in NAMED_RECORDS:
            rows = raw_versions(stem)
            canonical_id = rows[0]["canonical_id"]
            self.assertEqual(vs.list_versions(canonical_id), rows)
            self.assertTrue(all(row["release"] > "R01-01" for row in rows))
            early = self._assert_release(stem, rows, "R01-01")
            self.assertIsNone(early["version"])
            self.assertEqual(
                av.as_of_release(canonical_id, "R01-01"),
                early,
            )
            for release in ("R25-11", "R32-11"):
                legacy = self._assert_release(stem, rows, release)
                self.assertEqual(av.as_of_release(canonical_id, release), legacy)
            stamp = min(row["recorded_at"] for row in rows)
            self.assertIn("T", stamp)
            self._assert_date(stem, rows, "2000-01-01T00:00:00+00:00")
            self.assertIsNone(av.as_of_date(stem, stamp[:10])["version"])
            if stamp.endswith("+00:00"):
                self.assertIsNone(av.as_of_date(stem, stamp[:-6])["version"])
            exact = self._assert_date(stem, rows, stamp)
            self.assertEqual(av.as_of_date(canonical_id, stamp), exact)
            self.assertIsNotNone(exact["version"])
            latest = self._assert_date(stem, rows, "9999-12-31T23:59:59+00:00")
            self.assertEqual(latest["version"], max(rows, key=lambda row: row["recorded_at"]))
            for row in rows:
                self._assert_date(stem, rows, row["recorded_at"])


class AdaptiveAsOfOrderingTests(_TempStore):
    def test_multi_release_view_keeps_older_snapshot_and_same_release_revision(self):
        stamps = iter((
            "2020-01-01T00:00:00+00:00",
            "2022-01-01T00:00:00+00:00",
            "2024-01-01T00:00:00+00:00",
            "2023-01-01T00:00:00+00:00",
            "2021-06-01T00:00:00+00:00",
        ))
        vs._now = lambda: next(stamps)
        cid = "AUTOSAR/AP/record/SWS_MULTI_REL_AUDIT"
        vs.record_version(cid, "R20-11", "c20")
        vs.record_version(cid, "R25-11", "c25")
        vs.record_version(cid, "R32-11", "c32")
        vs.record_version(cid, "R25-11", "c25b")

        self.assertIsNone(av.as_of_release(cid, "R19-11")["version"])
        self.assertEqual(av.as_of_release(cid, "R19-11")["decisions"], [])
        self.assertEqual(av.as_of_release(cid, "R20-11")["version"]["content"], "c20")
        # Same release tag: the first stored line wins, not the later revision.
        self.assertEqual(av.as_of_release(cid, "R25-11")["version"]["content"], "c25")
        self.assertEqual(av.as_of_release(cid, "R32-11")["version"]["content"], "c32")
        self.assertEqual(av.as_of_release(cid, "R99-11")["version"]["content"], "c32")

        self.assertIsNone(av.as_of_date(cid, "1970-01-01T00:00:00+00:00")["version"])
        # A calendar date sorts before every timestamp on that day.
        self.assertEqual(av.as_of_date(cid, "2022-01-01")["version"]["content"], "c20")
        self.assertEqual(
            av.as_of_date(cid, "2022-01-01T00:00:00+00:00")["version"]["content"],
            "c25",
        )
        self.assertEqual(
            av.as_of_date(cid, "2023-01-01T00:00:00+00:00")["version"]["content"],
            "c25b",
        )
        self.assertEqual(
            av.as_of_date(cid, "2024-01-01T00:00:00+00:00")["version"]["content"],
            "c32",
        )
        # Append order is not recorded_at order: the last line is c25b.
        self.assertEqual(vs.latest_version(cid)["content"], "c25b")
        release_view = av.as_of_release(cid, "R25-11")
        date_view = av.as_of_date(cid, "2023-01-01T00:00:00+00:00")
        self.assertEqual(release_view["version"]["content"], "c25")
        self.assertEqual(date_view["version"]["content"], "c25b")
        self.assertNotEqual(
            release_view["version"]["version_id"],
            date_view["version"]["version_id"],
        )
        self.assertEqual(release_view["as_of"], {"kind": "release", "value": "R25-11"})
        self.assertEqual(
            date_view["as_of"],
            {"kind": "date", "value": "2023-01-01T00:00:00+00:00"},
        )
        for view in (release_view, date_view):
            got = view["version"]
            self.assertEqual(
                got["version_id"],
                requirement_version_id(got["canonical_id"], got["release"], got["content"]),
            )

        # Fixed-width tags are required: "R9-11" sorts after "R25-11".
        other = "AUTOSAR/AP/record/SWS_SHORT_REL_AUDIT"
        vs.record_version(other, "R9-11", "nine")
        self.assertIsNone(av.as_of_release(other, "R25-11")["version"])
        self.assertEqual(av.as_of_release(other, "R9-11")["version"]["content"], "nine")


if __name__ == "__main__":
    unittest.main()
