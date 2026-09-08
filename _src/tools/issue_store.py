#!/usr/bin/env python3
"""Strict reader for canonical ``issues/**/index.md`` issue items.

The module deliberately has no writer.  Until the Feature 0037 cutover, it is a
side-effect-free parser for the shadow issue store.
"""

from dataclasses import asdict, dataclass
import argparse
import datetime as _datetime
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
import unicodedata

from ruamel.yaml import YAML
from ruamel.yaml.constructor import DuplicateKeyError
from ruamel.yaml.error import YAMLError
from ruamel.yaml.parser import ParserError
from ruamel.yaml.reader import ReaderError
from ruamel.yaml.scanner import ScannerError

MAX_DOCUMENT_BYTES = 1024 * 1024
MAX_DEPTH = 20
MAX_CRITERION_BYTES = 4096
SCHEMA_PATH = Path("issues/_schema/issue-item-v1.schema.json")
TOOL_PATH = Path("_src/tools/issue_store.py")
ID_PATTERN = re.compile(r"^[0-9]{4}(?:-[0-9]{2}(?:\.[0-9]{2})?)?$")
AC_PATTERN = re.compile(r"^- \*\*(AC-[0-9]{3})\*\*\s+(.+)$")
NORMATIVE = ("Goal", "Scope", "Acceptance criteria", "Definition of Done")
FIELD_ORDER = (
    "schema_version", "id", "level", "parent", "state", "visibility",
    "created_at", "updated_at", "prerequisites", "labels", "work_type",
    "origin", "relations", "authority", "criteria", "limits",
)


class IssueStoreError(ValueError):
    """Stable, actionable parser failure."""

    def __init__(self, rule_id, message, *, path=None, line=None, field=None):
        self.rule_id = rule_id
        self.path = str(path) if path is not None else None
        self.line = line
        self.field = field
        detail = message
        if self.path:
            detail = f"{self.path}: {detail}"
        if line is not None:
            detail += f" (line {line})"
        if field is not None:
            detail += f" [field {field}]"
        super().__init__(f"{rule_id}: {detail}")


@dataclass(frozen=True)
class Locator:
    line_start: int
    line_end: int
    byte_start: int
    byte_end: int


def _error(rule, message, **context):
    raise IssueStoreError(rule, message, **context)


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")) + "\n"


def derive_identity(path, issues_root="issues"):
    """Return ``(id, level, parent)`` derived solely from a canonical path."""
    candidate = PurePosixPath(str(path).replace("\\", "/"))
    root = PurePosixPath(str(issues_root).replace("\\", "/"))
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        _error("IS0801", "path is outside the issue-store root", path=candidate)
    parts = relative.parts
    if any(part.startswith("_") for part in parts):
        _error("IS0802", "generated/policy/schema paths are never issue-item input", path=candidate)
    if len(parts) == 2 and parts[1] == "index.md" and re.fullmatch(r"[0-9]{4}", parts[0]):
        return parts[0], "feature", None
    if len(parts) == 3 and parts[2] == "index.md" and re.fullmatch(r"[0-9]{4}", parts[0]):
        item = parts[1]
        if re.fullmatch(parts[0] + r"-[0-9]{2}", item):
            return item, "task", parts[0]
        if re.fullmatch(parts[0] + r"-[0-9]{2}\.[0-9]{2}", item):
            return item, "subtask", item.rsplit(".", 1)[0]
    _error("IS0803", "non-canonical issue-item path", path=candidate)


def discover(issues_root):
    """Discover canonical items; reject item-like non-canonical ``index.md`` files."""
    root = Path(issues_root)
    found = []
    for path in sorted(root.rglob("index.md"), key=lambda value: value.as_posix().encode("utf-8")):
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0].startswith("_"):
            continue
        derive_identity(path.as_posix(), root.as_posix())
        found.append(path)
    return found


def _validate_bytes(data, path):
    if len(data) > MAX_DOCUMENT_BYTES:
        _error("IS0804", f"document exceeds {MAX_DOCUMENT_BYTES} bytes", path=path)
    if data.startswith(b"\xef\xbb\xbf"):
        _error("IS0805", "UTF-8 BOM is forbidden", path=path)
    if b"\r" in data:
        _error("IS0806", "only LF line endings are allowed", path=path)
    if b"\t" in data:
        _error("IS0847", "tabs are forbidden; use two-space indentation", path=path)
    if not data.endswith(b"\n") or data.endswith(b"\n\n"):
        _error("IS0807", "file must end with exactly one newline", path=path)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        _error("IS0805", f"invalid UTF-8: {exc}", path=path)
    for index, character in enumerate(text):
        codepoint = ord(character)
        if codepoint == 0 or (codepoint < 32 and character not in "\n\t") or codepoint == 127:
            line = text.count("\n", 0, index) + 1
            _error("IS0808", "NUL/control character is forbidden", path=path, line=line)
    return text


def _split_frontmatter(text, path):
    lines = text.splitlines(keepends=True)
    if not lines or lines[0] != "---\n":
        _error("IS0809", "opening frontmatter delimiter must be exact", path=path, line=1)
    closing = [index for index, line in enumerate(lines[1:], 1) if line == "---\n"]
    if len(closing) != 1:
        _error("IS0810", "exactly one closing frontmatter delimiter is required", path=path)
    boundary = closing[0]
    return "".join(lines[1:boundary]), "".join(lines[boundary + 1:]), boundary + 2


def _reject_yaml_syntax(source, path):
    # Profile-forbidden constructs are rejected before construction, including
    # constructs a safe YAML 1.2 loader might otherwise normalize harmlessly.
    rules = (
        (r"(^|[\s\[{,])(?:&|\*)[A-Za-z0-9_-]+", "IS0811", "anchors and aliases are forbidden"),
        (r"(?m)^\s*<<\s*:", "IS0812", "merge keys are forbidden"),
        (r"(^|[\s\[{,])![A-Za-z!]", "IS0813", "custom YAML tags are forbidden"),
        (r"(?m)^---\s*$", "IS0814", "multiple YAML documents are forbidden"),
        (r"(?m):\s*(?:yes|no|on|off|~)\s*(?:#.*)?$", "IS0815", "ambiguous YAML 1.1 scalar is forbidden"),
        (r"(?im):\s*[+-]?\.(?:inf|nan)\s*(?:#.*)?$", "IS0816", "non-finite number is forbidden"),
    )
    for pattern, rule, message in rules:
        match = re.search(pattern, source)
        if match:
            _error(rule, message, path=path, line=source.count("\n", 0, match.start()) + 2)


def _depth_and_keys(value, path, depth=0):
    if depth > MAX_DEPTH:
        _error("IS0817", f"YAML nesting exceeds {MAX_DEPTH}", path=path)
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                _error("IS0818", "all mapping keys must be strings", path=path)
            _depth_and_keys(child, path, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _depth_and_keys(child, path, depth + 1)
    elif isinstance(value, (_datetime.date, _datetime.datetime)):
        _error("IS0819", "timestamps/dates must be quoted strings", path=path)
    elif isinstance(value, float) and not math.isfinite(value):
        _error("IS0816", "non-finite number is forbidden", path=path)


def parse_frontmatter(source, path="<memory>"):
    _reject_yaml_syntax(source, path)
    yaml = YAML(typ="safe")
    yaml.version = (1, 2)
    yaml.allow_duplicate_keys = False
    try:
        documents = list(yaml.load_all(source))
    except DuplicateKeyError as exc:
        _error("IS0820", f"duplicate mapping key: {exc.problem}", path=path)
    except (YAMLError, ParserError, ScannerError, ReaderError, UnicodeError) as exc:
        _error("IS0821", f"malformed YAML: {exc}", path=path)
    if len(documents) != 1 or not isinstance(documents[0], dict):
        _error("IS0822", "frontmatter must be exactly one mapping", path=path)
    value = documents[0]
    _depth_and_keys(value, path)
    return value


def _line_offsets(body, start_byte):
    offsets = []
    cursor = start_byte
    for line in body.splitlines(keepends=True):
        offsets.append(cursor)
        cursor += len(line.encode("utf-8"))
    return offsets, cursor


def _criterion_status(raw):
    lower = raw.lower()
    details = {}
    moved = re.search(r"moved to ([0-9]{4}(?:-[0-9]{2}(?:\.[0-9]{2})?)?#AC-[0-9]{3})", raw, re.I)
    superseded = re.search(r"superseded by (AC-[0-9]{3})", raw, re.I)
    supersedes = re.search(r"\(supersedes:\s*(AC-[0-9]{3})\)", raw, re.I)
    derived = re.search(r"\(derived-from:\s*([0-9]{4}(?:-[0-9]{2}(?:\.[0-9]{2})?)?#AC-[0-9]{3})\)", raw, re.I)
    if moved and "~~" in raw:
        status = "moved"
        details["moved_to"] = moved.group(1)
    elif superseded and "~~" in raw:
        status = "superseded"
        details["superseded_by"] = superseded.group(1)
    elif "~~" in raw and ("withdrawn" in lower or "zurückgezogen" in lower):
        status = "withdrawn"
    elif "~~" in raw:
        _error("IS0823", "tombstone lacks a recognized lifecycle annotation")
    else:
        status = "active"
    if supersedes:
        details["supersedes"] = supersedes.group(1)
    if derived:
        details["derived_from"] = derived.group(1)
    return status, details


def parse_markdown_body(body, *, body_start_line=1, body_start_byte=0,
                        path="<memory>", prior_ids=None):
    lines = body.splitlines(keepends=True)
    offsets, final_offset = _line_offsets(body, body_start_byte)
    headings = []
    for index, line in enumerate(lines):
        match = re.fullmatch(r"## ([^\n]+)\n", line)
        if match:
            headings.append((index, match.group(1)))
    normative = [(index, name) for index, name in headings if name in NORMATIVE]
    if tuple(name for _, name in normative) != NORMATIVE:
        _error("IS0824", "normative headings must appear exactly once in Goal/Scope/Acceptance criteria/Definition of Done order", path=path)
    if any(name not in NORMATIVE and index < normative[-1][0] for index, name in headings):
        _error("IS0825", "informative headings may appear only after Definition of Done", path=path)
    sections = {}
    for position, (heading_index, name) in enumerate(normative):
        later = [index for index, _ in headings if index > heading_index]
        end = min(later) if later else len(lines)
        content_start = heading_index + 1
        while content_start < end and lines[content_start] == "\n":
            content_start += 1
        content = "".join(lines[content_start:end]).rstrip("\n")
        byte_start = offsets[heading_index] if offsets else body_start_byte
        byte_end = offsets[end] if end < len(offsets) else final_offset
        sections[name] = {"text": content, "locator": asdict(Locator(
            body_start_line + heading_index, body_start_line + max(heading_index, end - 1),
            byte_start, byte_end))}
    acceptance_start = normative[2][0] + 1
    acceptance_end = normative[3][0]
    criteria = []
    index = acceptance_start
    while index < acceptance_end:
        line = lines[index]
        if line == "\n":
            index += 1
            continue
        match = AC_PATTERN.match(line.rstrip("\n"))
        if not match:
            _error("IS0826", "Acceptance criteria contains non-criterion content", path=path,
                   line=body_start_line + index)
        start = index
        chunks = [match.group(2)]
        index += 1
        while index < acceptance_end:
            continuation = lines[index]
            if AC_PATTERN.match(continuation.rstrip("\n")) or continuation == "\n":
                break
            if not continuation.startswith("  "):
                _error("IS0827", "criterion continuation must be indented by at least two spaces",
                       path=path, line=body_start_line + index)
            chunks.append(continuation[2:].rstrip("\n"))
            index += 1
        raw = "\n".join(chunks)
        normalized = unicodedata.normalize("NFC", raw)
        if normalized != raw:
            _error("IS0848", "criterion text must already be NFC-normalized", path=path,
                   line=body_start_line + start)
        if len(normalized.encode("utf-8")) > MAX_CRITERION_BYTES:
            _error("IS0828", f"criterion exceeds {MAX_CRITERION_BYTES} bytes", path=path,
                   line=body_start_line + start)
        status, details = _criterion_status(normalized)
        end = max(start, index - 1)
        byte_end = offsets[index] if index < len(offsets) else final_offset
        criteria.append({"id": match.group(1), "status": status, "text": normalized,
                         "raw": "".join(lines[start:index]).rstrip("\n"), **details,
                         "locator": asdict(Locator(body_start_line + start,
                                                    body_start_line + end,
                                                    offsets[start], byte_end))})
    ids = [criterion["id"] for criterion in criteria]
    if len(ids) != len(set(ids)):
        _error("IS0829", "duplicate/reused AC-NNN identifier", path=path)
    numeric = [int(value[3:]) for value in ids]
    if numeric and numeric != sorted(numeric):
        _error("IS0830", "AC-NNN identifiers must retain append-only numeric order", path=path)
    if prior_ids is not None and not set(prior_ids).issubset(ids):
        _error("IS0830", "previously allocated AC-NNN identifier is missing instead of tombstoned", path=path)
    return {"sections": sections, "criteria": criteria}


def _expect_type(value, expected, path, field):
    if not isinstance(value, expected) or (expected is int and isinstance(value, bool)):
        _error("IS0831", f"wrong value type; expected {expected.__name__}", path=path, field=field)


def validate_item(metadata, identity, markdown, path):
    unknown = set(metadata) - set(FIELD_ORDER)
    if unknown:
        _error("IS0832", f"unknown frontmatter fields: {sorted(unknown)}", path=path)
    for field in ("schema_version", "id", "level", "state"):
        if field not in metadata:
            _error("IS0833", "required field missing", path=path, field=field)
    if not re.fullmatch(r"1\.[0-9]+", str(metadata["schema_version"])):
        _error("IS0834", "unknown schema version; only issue-item major version 1 is supported", path=path,
               field="schema_version")
    item_id, level, parent = identity
    for field, expected in (("id", item_id), ("level", level)):
        if metadata.get(field) != expected:
            _error("IS0835", f"path-derived value must be {expected!r}", path=path, field=field)
    if parent is None and "parent" in metadata:
        _error("IS0836", "feature must not have parent", path=path, field="parent")
    if parent is not None and metadata.get("parent") != parent:
        _error("IS0836", f"parent must be {parent!r}", path=path, field="parent")
    enums = {"state": {"open", "in_progress", "blocked", "closed", "withdrawn"},
             "visibility": {"internal", "public-summary"},
             "work_type": {"design", "implementation", "migration", "tooling", "research", "documentation"},
             "authority": {"shadow", "authoritative"}}
    for field, allowed in enums.items():
        if field in metadata and metadata[field] not in allowed:
            _error("IS0837", f"invalid enum value {metadata[field]!r}", path=path, field=field)
    metadata.setdefault("visibility", "internal")
    for field in ("created_at", "updated_at"):
        if field in metadata:
            _expect_type(metadata[field], str, path, field)
            try:
                _datetime.date.fromisoformat(metadata[field])
            except ValueError:
                _error("IS0838", "date must be YYYY-MM-DD", path=path, field=field)
    for field in ("prerequisites", "labels"):
        if field in metadata:
            _expect_type(metadata[field], list, path, field)
            if len(metadata[field]) != len(set(metadata[field])) or not all(isinstance(value, str) for value in metadata[field]):
                _error("IS0839", "list must contain unique strings", path=path, field=field)
    if any(not ID_PATTERN.fullmatch(value) for value in metadata.get("prerequisites", [])):
        _error("IS0840", "malformed prerequisite ID", path=path, field="prerequisites")
    if metadata["id"] in metadata.get("prerequisites", []):
        _error("IS0840", "self prerequisite is forbidden", path=path, field="prerequisites")
    if any(not re.fullmatch(r"[a-z][a-z0-9-]*", value) for value in metadata.get("labels", [])):
        _error("IS0841", "malformed label", path=path, field="labels")
    if "origin" in metadata:
        origin = metadata["origin"]
        _expect_type(origin, dict, path, "origin")
        if set(origin) - {"kind", "source"} or origin.get("kind") not in {
                "authored", "migrated-from-legacy-todo", "split-from", "merged-from"}:
            _error("IS0844", "invalid origin object", path=path, field="origin")
        if "source" in origin and not isinstance(origin["source"], str):
            _error("IS0844", "origin source must be a string", path=path, field="origin")
    if "relations" in metadata:
        _expect_type(metadata["relations"], list, path, "relations")
        for relation in metadata["relations"]:
            if not isinstance(relation, dict) or set(relation) != {"type", "target"}:
                _error("IS0845", "relation must contain only type and target", path=path, field="relations")
            if relation["type"] not in {"supersedes", "superseded_by", "derived_from", "blocks", "blocked_by"}:
                _error("IS0845", "invalid relation type", path=path, field="relations")
            if not isinstance(relation["target"], str) or not re.fullmatch(
                    r"[0-9]{4}(?:-[0-9]{2}(?:\.[0-9]{2})?)?(?:#AC-[0-9]{3})?", relation["target"]):
                _error("IS0845", "invalid relation target", path=path, field="relations")
    declared = metadata.get("criteria")
    if declared is not None:
        _expect_type(declared, list, path, "criteria")
        declared_ids = []
        allowed = {"id", "status", "supersedes", "superseded_by", "derived_from", "moved_to", "source"}
        for criterion in declared:
            if not isinstance(criterion, dict) or set(criterion) - allowed or not {"id", "status"}.issubset(criterion):
                _error("IS0846", "invalid structured criterion", path=path, field="criteria")
            if not re.fullmatch(r"AC-[0-9]{3}", criterion["id"]):
                _error("IS0846", "invalid structured criterion ID", path=path, field="criteria")
            if criterion["status"] not in {"active", "withdrawn", "superseded", "moved"}:
                _error("IS0846", "invalid structured criterion status", path=path, field="criteria")
            declared_ids.append(criterion["id"])
        if len(declared_ids) != len(set(declared_ids)):
            _error("IS0846", "duplicate structured criterion ID", path=path, field="criteria")
        body_projection = [{key: value for key, value in criterion.items()
                            if key in {"id", "status", "supersedes", "superseded_by", "derived_from", "moved_to"}}
                           for criterion in markdown["criteria"]]
        if declared != body_projection:
            _error("IS0842", "frontmatter criteria mirror disagrees with Markdown", path=path, field="criteria")
    limits = metadata.get("limits", {})
    if not isinstance(limits, dict) or set(limits) - {"max_criterion_bytes"}:
        _error("IS0843", "invalid limits object", path=path, field="limits")
    limit = limits.get("max_criterion_bytes", MAX_CRITERION_BYTES)
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_CRITERION_BYTES:
        _error("IS0843", "max_criterion_bytes must be 1..4096", path=path, field="limits")
    for criterion in markdown["criteria"]:
        if len(criterion["text"].encode("utf-8")) > limit:
            _error("IS0828", f"criterion exceeds item limit {limit}", path=path)
    return metadata


def parse_issue(path, issues_root=None, repository_root=None):
    path = Path(path).resolve()
    repository_root = (Path(repository_root) if repository_root else Path.cwd()).resolve()
    if issues_root is None:
        issues_root = repository_root / "issues"
    issues_root = Path(issues_root).resolve()
    identity = derive_identity(path.as_posix(), issues_root.as_posix())
    data = path.read_bytes()
    text = _validate_bytes(data, path)
    frontmatter, body, body_line = _split_frontmatter(text, path)
    metadata = parse_frontmatter(frontmatter, path)
    front_bytes = len(("---\n" + frontmatter + "---\n").encode("utf-8"))
    markdown = parse_markdown_body(body, body_start_line=body_line,
                                   body_start_byte=front_bytes, path=path)
    validate_item(metadata, identity, markdown, path)
    schema_bytes = (repository_root / SCHEMA_PATH).read_bytes()
    tool_bytes = (repository_root / TOOL_PATH).read_bytes()
    normalized = {
        "schema": "issue-store-normalized@v1",
        "item": metadata,
        "sections": markdown["sections"],
        "markdown_raw": body,
        "criteria": markdown["criteria"],
        "source": {"path": path.relative_to(repository_root).as_posix(),
                   "sha256": _sha256(data), "bytes": len(data)},
        "digests": {"schema_sha256": _sha256(schema_bytes),
                    "tool_sha256": _sha256(tool_bytes)},
    }
    normalized["normalized_sha256"] = _sha256(_canonical_json(normalized).encode("utf-8"))
    return normalized


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--issues-root", default="issues")
    parser.add_argument("--discover", action="store_true")
    args = parser.parse_args(argv)
    try:
        paths = discover(args.issues_root) if args.discover else [Path(value) for value in args.paths]
        if not paths:
            parser.error("provide paths or --discover")
        values = [parse_issue(path, issues_root=args.issues_root) for path in paths]
        sys.stdout.write(_canonical_json(values[0] if len(values) == 1 else values))
        return 0
    except (IssueStoreError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
