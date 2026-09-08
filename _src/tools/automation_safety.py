#!/usr/bin/env python3
"""Static fail-closed checks for tracked automation scripts.

The checker intentionally uses only the Python standard library.  Python files
are inspected with :mod:`ast`; shell files use conservative command-oriented
line checks.  Live discovery comes from Git's tracked index, while explicit
``--path``/``--fixture`` scans make extensionless fixture bytes testable.
"""
import argparse
import ast
import datetime as _datetime
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


SCHEMA_VERSION = 1
POLICY_SCHEMA_VERSION = 1
DEFAULT_POLICY = "_src/tools/automation_safety_policy.json"

RULES = {
    "AUTO000": ("critical", "Automation source could not be inspected"),
    "AUTO001": ("critical", "Unchecked mutating subprocess"),
    "AUTO002": ("critical", "False-success or unconditional PASS"),
    "AUTO003": ("critical", "Broad or wildcard mutation/staging"),
    "AUTO004": ("critical", "Protected-ref force update"),
    "AUTO005": ("high", "Hard-coded integration target or identity"),
    "AUTO006": ("high", "Shell interpreter execution"),
    "AUTO007": ("critical", "Validation mixed with repair"),
    "AUTO008": ("critical", "Mutation before required gate"),
    "AUTO009": ("critical", "Ignored VCS publication result"),
    "AUTO010": ("high", "Missing durable outcome or recovery state"),
}

_MUTATING_GIT = {
    "add", "am", "apply", "branch", "checkout", "clean", "commit", "config",
    "fetch", "merge", "mv", "pull", "push", "rebase", "remote", "reset",
    "restore", "rm", "stash", "switch", "tag", "update-ref", "worktree",
}
_PUBLICATION_GIT = {"commit", "push", "update-ref"}
_SUBPROCESS_APIS = {
    "subprocess.call", "subprocess.check_call", "subprocess.check_output",
    "subprocess.getoutput", "subprocess.getstatusoutput", "subprocess.Popen", "subprocess.run",
}
_MUTATING_COMMANDS = {
    "chmod", "chown", "cp", "install", "ln", "mkdir", "mv", "rm", "sed",
    "tee", "touch", "truncate",
}
_GATE_WORDS = ("validate", "pytest", "unittest", "test", "check", "ls-tree")
_WILDCARD_RE = re.compile(r"[*?\[]")
_TASK_ID_RE = re.compile(r"^[0-9]{4}-[0-9]{2}(?:\.[0-9]{2})?$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DISPOSITION_KINDS = ("blocking-task", "narrow-suppression", "proven-closed")
_PASS_RE = re.compile(r"\bPASS(?:ED)?\b", re.IGNORECASE)
_FUNCTION_START_RE = re.compile(
    r"^\s*(?:(?:function\s+)([-A-Za-z0-9_:.+@%]+)(?:\s*\(\s*\))?"
    r"|([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\))\s*\{"
)
_FUNCTION_PENDING_RE = re.compile(
    r"^\s*(?:(?:function\s+)([-A-Za-z0-9_:.+@%]+)(?:\s*\(\s*\))?"
    r"|([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\))\s*$"
)
_FUNCTION_ANY_DECL_RE = re.compile(
    r"(?:^|[\s;|&(){}!])\s*(?:(?:function\s+)[-A-Za-z0-9_:.+@%]+(?:\s*\(\s*\))?"
    r"|[A-Za-z_][A-Za-z0-9_]*\s*\(\s*\))(?=\s|\{|\(|$)"
)
_UNKNOWN_COMMAND = "{unknown-command}"
_MAX_COMMAND_VARIANTS = 64


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    path: str
    line: int
    symbol: str
    evidence: str
    evidence_sha256: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def _evidence_digest(evidence: str) -> Tuple[str, str]:
    return evidence, hashlib.sha256(evidence.encode("utf-8")).hexdigest()


def _source_evidence(lines: Sequence[str], line: int) -> Tuple[str, str]:
    evidence = lines[line - 1] if 1 <= line <= len(lines) else ""
    return _evidence_digest(evidence)


def _finding(
    rule: str,
    path: str,
    line: int,
    symbol: str,
    lines: Sequence[str],
    severity: Optional[str] = None,
    evidence_text: Optional[str] = None,
) -> Finding:
    evidence, digest = (
        _evidence_digest(evidence_text)
        if evidence_text is not None
        else _source_evidence(lines, line)
    )
    return Finding(
        rule=rule,
        severity=severity or RULES[rule][0],
        path=path,
        line=max(1, int(line or 1)),
        symbol=symbol or "<module>",
        evidence=evidence,
        evidence_sha256=digest,
    )


def _python_finding(
    rule: str,
    path: str,
    node: ast.AST,
    symbol: str,
    lines: Sequence[str],
    severity: Optional[str] = None,
) -> Finding:
    start = max(1, int(getattr(node, "lineno", 1) or 1))
    end = max(start, int(getattr(node, "end_lineno", start) or start))
    evidence = "\n".join(lines[start - 1:end])
    return _finding(
        rule,
        path,
        start,
        symbol,
        lines,
        severity=severity,
        evidence_text=evidence,
    )


def _dedupe(findings: Iterable[Finding]) -> List[Finding]:
    unique = {}
    for finding in findings:
        key = (finding.path, finding.line, finding.rule, finding.symbol, finding.evidence_sha256)
        unique[key] = finding
    return sorted(unique.values(), key=lambda item: (item.path, item.line, item.rule))


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_name(node.value)
        return (prefix + "." if prefix else "") + node.attr
    return ""


def _import_call_aliases(tree: ast.AST) -> Dict[str, str]:
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for imported in node.names:
                if imported.name in ("os", "subprocess"):
                    aliases[imported.asname or imported.name] = imported.name
        elif isinstance(node, ast.ImportFrom) and node.module in ("os", "subprocess"):
            if any(imported.name == "*" for imported in node.names):
                names = _SUBPROCESS_APIS if node.module == "subprocess" else {"os.popen", "os.system"}
                for qualified in names:
                    aliases[qualified.rsplit(".", 1)[-1]] = qualified
                continue
            for imported in node.names:
                aliases[imported.asname or imported.name] = "%s.%s" % (node.module, imported.name)

    assignments = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
    ]
    changed = True
    while changed:
        changed = False
        for assignment in assignments:
            value = assignment.value
            if value is None:
                continue
            resolved = _resolved_call_name(value, aliases)
            if resolved not in _SUBPROCESS_APIS and resolved not in ("os.popen", "os.system"):
                continue
            targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
            for target in targets:
                if isinstance(target, ast.Name) and aliases.get(target.id) != resolved:
                    aliases[target.id] = resolved
                    changed = True
    return aliases


def _resolved_call_name(node: ast.AST, aliases: Dict[str, str]) -> str:
    name = _call_name(node)
    if name in aliases:
        return aliases[name]
    prefix, separator, suffix = name.partition(".")
    if separator and prefix in aliases:
        return aliases[prefix] + "." + suffix
    return name


def _literal_string(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            else:
                parts.append("{value}")
        return "".join(parts)
    return None


def _statement_ancestor(node: ast.AST, parents: Dict[ast.AST, ast.AST]) -> Optional[ast.stmt]:
    current = node
    while current is not None:
        if isinstance(current, ast.stmt):
            return current
        current = parents.get(current)
    return None


def _statement_container(
    node: ast.AST,
    parents: Dict[ast.AST, ast.AST],
) -> Optional[Tuple[ast.AST, str, Sequence[ast.stmt], ast.stmt]]:
    statement = _statement_ancestor(node, parents)
    if statement is None:
        return None
    parent = parents.get(statement)
    if parent is None:
        return None
    for field, value in ast.iter_fields(parent):
        if isinstance(value, list) and any(item is statement for item in value):
            return parent, field, value, statement
    return None


def _assignment_dominates_use(
    assignment: ast.AST,
    use_node: ast.AST,
    parents: Dict[ast.AST, ast.AST],
) -> bool:
    assignment_statement = _statement_ancestor(assignment, parents)
    current = _statement_ancestor(use_node, parents)
    if assignment_statement is None or current is None:
        return False
    visited = set()
    while current is not None and current not in visited:
        visited.add(current)
        container = _statement_container(current, parents)
        if container is not None:
            _parent, _field, statements, current_statement = container
            assignment_index = next(
                (index for index, item in enumerate(statements) if item is assignment_statement),
                None,
            )
            current_index = next(
                (index for index, item in enumerate(statements) if item is current_statement),
                None,
            )
            if assignment_index is not None and current_index is not None:
                return assignment_index < current_index
        parent = parents.get(current)
        current = _statement_ancestor(parent, parents) if parent is not None else None
    return False


def _name_mutated_before_use(
    name: str,
    scope: ast.AST,
    parents: Dict[ast.AST, ast.AST],
    tree: ast.AST,
    before_line: int,
) -> bool:
    mutator_methods = {"append", "clear", "extend", "insert", "pop", "remove", "reverse", "sort"}
    for candidate in ast.walk(scope):
        line = getattr(candidate, "lineno", before_line)
        if line >= before_line or _enclosing_scope(candidate, parents, tree) is not scope:
            continue
        if isinstance(candidate, ast.AugAssign) and isinstance(candidate.target, ast.Name):
            if candidate.target.id == name:
                return True
        if isinstance(candidate, (ast.Assign, ast.AnnAssign)):
            targets = candidate.targets if isinstance(candidate, ast.Assign) else [candidate.target]
            for target in targets:
                if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
                    if target.value.id == name:
                        return True
        if isinstance(candidate, ast.Call) and isinstance(candidate.func, ast.Attribute):
            if candidate.func.attr in mutator_methods and isinstance(candidate.func.value, ast.Name):
                if candidate.func.value.id == name:
                    return True
    return False


def _dedupe_command_variants(variants: Iterable[Sequence[str]]) -> List[List[str]]:
    unique = []
    seen = set()
    for variant in variants:
        value = tuple(variant)
        if value in seen:
            continue
        seen.add(value)
        unique.append(list(value))
        if len(unique) >= _MAX_COMMAND_VARIANTS:
            break
    return unique


def _combine_command_variants(
    left: Sequence[Sequence[str]],
    right: Sequence[Sequence[str]],
) -> List[List[str]]:
    combined = []
    for left_variant in left:
        for right_variant in right:
            combined.append(list(left_variant) + list(right_variant))
            if len(combined) >= _MAX_COMMAND_VARIANTS:
                return _dedupe_command_variants(combined)
    return _dedupe_command_variants(combined)


def _static_command_variants(
    node: ast.AST,
    scope: ast.AST,
    parents: Dict[ast.AST, ast.AST],
    tree: ast.AST,
    before_line: int,
    use_node: Optional[ast.AST] = None,
    seen: Optional[Set[str]] = None,
) -> List[List[str]]:
    seen = set(seen or set())
    use_node = use_node or node
    if isinstance(node, (ast.List, ast.Tuple)):
        variants = [[]]
        for item in node.elts:
            if isinstance(item, ast.Starred):
                nested = _static_command_variants(
                    item.value, scope, parents, tree, before_line, use_node, seen
                ) or [["{value}"]]
            else:
                value = _literal_string(item)
                nested = [[value if value is not None else "{value}"]]
            variants = _combine_command_variants(variants, nested)
        return variants
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _static_command_variants(
            node.left, scope, parents, tree, before_line, use_node, seen
        ) or [["{value}"]]
        right = _static_command_variants(
            node.right, scope, parents, tree, before_line, use_node, seen
        ) or [["{value}"]]
        return _combine_command_variants(left, right)
    if isinstance(node, ast.IfExp):
        return _dedupe_command_variants(
            _static_command_variants(node.body, scope, parents, tree, before_line, use_node, seen)
            + _static_command_variants(node.orelse, scope, parents, tree, before_line, use_node, seen)
        )
    if isinstance(node, ast.Call) and _call_name(node.func) in ("list", "tuple") and node.args:
        return _static_command_variants(
            node.args[0], scope, parents, tree, before_line, use_node, seen
        )
    if isinstance(node, ast.Name):
        if node.id in seen:
            return [[_UNKNOWN_COMMAND]]
        seen.add(node.id)
        assignments = []
        for candidate in ast.walk(scope):
            if getattr(candidate, "lineno", before_line) >= before_line:
                continue
            if _enclosing_scope(candidate, parents, tree) is not scope:
                continue
            if isinstance(candidate, ast.Assign):
                if any(isinstance(target, ast.Name) and target.id == node.id for target in candidate.targets):
                    assignments.append(candidate)
            elif isinstance(candidate, ast.AnnAssign):
                if isinstance(candidate.target, ast.Name) and candidate.target.id == node.id and candidate.value is not None:
                    assignments.append(candidate)
        variants = []
        for assignment in assignments:
            variants.extend(
                _static_command_variants(
                    assignment.value,
                    scope,
                    parents,
                    tree,
                    assignment.lineno,
                    assignment,
                    seen,
                ) or [[_UNKNOWN_COMMAND]]
            )
        if not any(_assignment_dominates_use(item, use_node, parents) for item in assignments):
            variants.append([_UNKNOWN_COMMAND])
        if _name_mutated_before_use(node.id, scope, parents, tree, before_line):
            variants.append([_UNKNOWN_COMMAND])
        return _dedupe_command_variants(variants or [[_UNKNOWN_COMMAND]])
    value = _literal_string(node)
    if value is None:
        return []
    try:
        return [shlex.split(value)]
    except ValueError:
        return [value.split()]


def _is_unknown_command(tokens: Optional[Sequence[str]]) -> bool:
    return bool(not tokens or tokens[0] in (_UNKNOWN_COMMAND, "{value}"))


def _command_risk(tokens: Sequence[str]) -> int:
    if _is_force_protected_push(tokens):
        return 6
    if _git_subcommand(tokens) in _PUBLICATION_GIT:
        return 5
    if _is_unknown_command(tokens):
        return 4
    if _is_mutating_tokens(tokens):
        return 3
    if _contains_gate(tokens):
        return 2
    return 1


def _command_variants(
    call: ast.Call,
    scope: ast.AST,
    parents: Dict[ast.AST, ast.AST],
    tree: ast.AST,
) -> List[List[str]]:
    if not call.args:
        return [[_UNKNOWN_COMMAND]]
    variants = _static_command_variants(
        call.args[0], scope, parents, tree, call.lineno, call
    )
    return _dedupe_command_variants(variants or [[_UNKNOWN_COMMAND]])


def _command_tokens(
    call: ast.Call,
    scope: ast.AST,
    parents: Dict[ast.AST, ast.AST],
    tree: ast.AST,
) -> Optional[List[str]]:
    variants = _command_variants(call, scope, parents, tree)
    return max(variants, key=_command_risk) if variants else None


_COMMAND_PREFIXES = {"builtin", "command", "env", "nohup", "time"}
_ENV_OPTIONS_WITH_VALUE = {"-C", "--chdir", "-S", "--split-string", "-u", "--unset"}
_TIME_OPTIONS_WITH_VALUE = {"-f", "--format", "-o", "--output"}
_SHELL_INTERPRETERS = {"bash", "dash", "ksh", "sh", "zsh"}


def _effective_command_tokens(tokens: Optional[Sequence[str]]) -> List[str]:
    values = list(tokens or [])
    index = 0
    while index < len(values) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", values[index]):
        index += 1
    while index < len(values):
        prefix = os.path.basename(values[index]).lower()
        if prefix not in _COMMAND_PREFIXES:
            break
        index += 1
        while index < len(values):
            token = values[index]
            if token == "--":
                index += 1
                break
            options_with_value = (
                _ENV_OPTIONS_WITH_VALUE if prefix == "env"
                else _TIME_OPTIONS_WITH_VALUE if prefix == "time"
                else set()
            )
            if prefix == "env" and (
                token in ("-S", "--split-string")
                or token.startswith("-S")
                or token.startswith("--split-string=")
            ):
                if token in ("-S", "--split-string"):
                    split_value = values[index + 1] if index + 1 < len(values) else ""
                    consumed = 2
                else:
                    split_value = token[2:] if token.startswith("-S") else token.split("=", 1)[1]
                    consumed = 1
                try:
                    split_tokens = shlex.split(split_value, comments=False, posix=True)
                except ValueError:
                    split_tokens = [_UNKNOWN_COMMAND]
                values[index:index + consumed] = split_tokens or [_UNKNOWN_COMMAND]
                continue
            if token in options_with_value:
                index += 2
                continue
            if token.startswith("--") and "=" in token:
                index += 1
                continue
            if token.startswith("-"):
                index += 1
                continue
            if prefix == "env" and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", token):
                index += 1
                continue
            break
    return values[index:]


def _shell_script_from_tokens(tokens: Optional[Sequence[str]]) -> Optional[str]:
    effective = _effective_command_tokens(tokens)
    if not effective or os.path.basename(effective[0]).lower() not in _SHELL_INTERPRETERS:
        return None
    for index, token in enumerate(effective[1:], 1):
        if token == "-c" and index + 1 < len(effective):
            return effective[index + 1]
        if token.startswith("-") and "c" in token[1:] and index + 1 < len(effective):
            return effective[index + 1]
    return None


def _git_subcommand(tokens: Optional[Sequence[str]]) -> Optional[str]:
    effective = _effective_command_tokens(tokens)
    if not effective or os.path.basename(effective[0]).lower() != "git":
        return None
    index = 1
    tokens = effective
    while index < len(tokens):
        token = tokens[index]
        if token in ("-C", "-c", "--git-dir", "--work-tree"):
            index += 2
            continue
        if token.startswith("-"):
            index += 1
            continue
        return token.lower()
    return None


def _is_mutating_tokens(tokens: Optional[Sequence[str]]) -> bool:
    effective = _effective_command_tokens(tokens)
    if not effective:
        return False
    command = os.path.basename(effective[0]).lower()
    if command == "git":
        return _git_subcommand(effective) in _MUTATING_GIT
    if command in _SHELL_INTERPRETERS:
        return True
    return command in _MUTATING_COMMANDS


def _is_effectively_unknown_command(tokens: Optional[Sequence[str]]) -> bool:
    effective = _effective_command_tokens(tokens)
    return not effective or effective[0] == _UNKNOWN_COMMAND


def _is_publication_tokens(tokens: Optional[Sequence[str]]) -> bool:
    if _git_subcommand(tokens) in _PUBLICATION_GIT:
        return True
    script = _shell_script_from_tokens(tokens)
    if script is None:
        return False
    commands = _shell_simple_commands(_shell_command_words(script))
    return any(_git_subcommand(command) in _PUBLICATION_GIT for command in commands)


def _invokes_shell_interpreter(tokens: Optional[Sequence[str]]) -> bool:
    effective = _effective_command_tokens(tokens)
    return bool(effective and os.path.basename(effective[0]).lower() in _SHELL_INTERPRETERS)


def _contains_gate(tokens: Optional[Sequence[str]]) -> bool:
    if not tokens:
        return False
    text = " ".join(tokens).lower()
    return any(word in text for word in _GATE_WORDS)


def _is_broad_git_add(tokens: Optional[Sequence[str]]) -> bool:
    effective = _effective_command_tokens(tokens)
    if _git_subcommand(effective) != "add":
        return False
    try:
        start = effective.index("add") + 1
    except ValueError:
        return False
    for token in effective[start:]:
        if token in ("-A", "--all", ".", "./"):
            return True
        if _WILDCARD_RE.search(token) or token.endswith("/"):
            return True
    return False


def _is_protected_ref_token(token: str) -> bool:
    value = token.lower().lstrip("+")
    if value.startswith("--force-with-lease="):
        value = value.split("=", 1)[1]
    return re.search(r"(?:^|[:/])(?:refs/heads/)?(?:main|master)$", value) is not None


def _is_force_protected_push(tokens: Optional[Sequence[str]]) -> bool:
    effective = _effective_command_tokens(tokens)
    if _git_subcommand(effective) != "push":
        script = _shell_script_from_tokens(tokens)
        return bool(script and _shell_force_protected(script))
    force = any(
        token == "-f" or token.startswith("--force") or token.startswith("+")
        for token in effective
    )
    return force and any(_is_protected_ref_token(token) for token in effective)


def _has_hardcoded_integration(tokens: Optional[Sequence[str]]) -> bool:
    effective = _effective_command_tokens(tokens)
    if not effective or os.path.basename(effective[0]).lower() != "git":
        script = _shell_script_from_tokens(tokens)
        return bool(script and _shell_hardcoded_integration(script))
    text = " ".join(effective)
    subcommand = _git_subcommand(effective)
    if "user.name=" in text or "user.email=" in text:
        return True
    if subcommand == "remote" and ("git@" in text or "https://" in text or "ssh://" in text):
        return True
    if subcommand == "push" and any(_is_protected_ref_token(token) for token in effective):
        return True
    return False


def _assigned_name(call: ast.Call, parents: Dict[ast.AST, ast.AST]) -> Optional[str]:
    parent = parents.get(call)
    if isinstance(parent, ast.Assign) and len(parent.targets) == 1 and isinstance(parent.targets[0], ast.Name):
        return parent.targets[0].id
    if isinstance(parent, ast.AnnAssign) and isinstance(parent.target, ast.Name):
        return parent.target.id
    return None


def _enclosing_scope(node: ast.AST, parents: Dict[ast.AST, ast.AST], tree: ast.AST) -> ast.AST:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current
    return tree


def _recovery_scope(node: ast.AST, parents: Dict[ast.AST, ast.AST], tree: ast.AST) -> ast.AST:
    function_scope = None
    current = node
    while current in parents:
        current = parents[current]
        if function_scope is None and isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_scope = current
        if isinstance(current, ast.ClassDef):
            return current
    if isinstance(function_scope, (ast.FunctionDef, ast.AsyncFunctionDef)) and function_scope.name.startswith("_"):
        return tree
    return function_scope or tree


def _symbol_for(node: ast.AST, parents: Dict[ast.AST, ast.AST]) -> str:
    names = []
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(current.name)
    return ".".join(reversed(names)) if names else "<module>"


def _references_result_returncode(node: ast.AST, result_name: Optional[str], call: ast.Call) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Attribute) or child.attr != "returncode":
            continue
        if result_name and isinstance(child.value, ast.Name) and child.value.id == result_name:
            return True
        if child.value is call:
            return True
    return False


def _references_result_object(node: ast.AST, result_name: Optional[str], call: ast.Call) -> bool:
    if node is call:
        return True
    if result_name and isinstance(node, ast.Name):
        return node.id == result_name
    if isinstance(node, (ast.List, ast.Set, ast.Tuple)):
        return any(_references_result_object(item, result_name, call) for item in node.elts)
    if isinstance(node, ast.Dict):
        return any(
            _references_result_object(value, result_name, call)
            for value in node.values
        )
    return False


def _collection_truth_when_nonempty(node: ast.AST, name: str) -> Optional[bool]:
    if isinstance(node, ast.Name) and node.id == name:
        return True
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        value = _collection_truth_when_nonempty(node.operand, name)
        return None if value is None else not value
    if isinstance(node, ast.Call) and _call_name(node.func) in ("bool", "len") and node.args:
        if isinstance(node.args[0], ast.Name) and node.args[0].id == name:
            return True
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and len(node.comparators) == 1:
        left = node.left
        right = node.comparators[0]
        if isinstance(left, ast.Call) and _call_name(left.func) == "len" and left.args:
            if isinstance(left.args[0], ast.Name) and left.args[0].id == name:
                if isinstance(right, ast.Constant) and right.value == 0:
                    if isinstance(node.ops[0], (ast.Gt, ast.NotEq)):
                        return True
                    if isinstance(node.ops[0], ast.Eq):
                        return False
    return None


def _collection_failure_expression(node: ast.AST, name: str) -> bool:
    if isinstance(node, ast.Name):
        return node.id == name
    if isinstance(node, ast.Constant):
        return bool(
            isinstance(node.value, int)
            and not isinstance(node.value, bool)
            and node.value != 0
        )
    if isinstance(node, (ast.List, ast.Set, ast.Tuple)):
        return any(_collection_failure_expression(item, name) for item in node.elts)
    if isinstance(node, ast.Dict):
        return any(_collection_failure_expression(value, name) for value in node.values)
    if isinstance(node, ast.IfExp):
        truth = _collection_truth_when_nonempty(node.test, name)
        if truth is None:
            return False
        selected = node.body if truth else node.orelse
        return _collection_failure_expression(selected, name)
    if isinstance(node, ast.Call) and _call_name(node.func) in ("bool", "len") and node.args:
        return isinstance(node.args[0], ast.Name) and node.args[0].id == name
    return False


def _return_is_guaranteed_zero(value: Optional[ast.AST]) -> bool:
    if isinstance(value, ast.Constant):
        return bool(
            isinstance(value.value, int)
            and not isinstance(value.value, bool)
            and value.value == 0
        )
    if isinstance(value, ast.IfExp):
        return _return_is_guaranteed_zero(value.body) and _return_is_guaranteed_zero(value.orelse)
    return False


def _failure_collections_returned(
    scope: ast.AST,
    parents: Dict[ast.AST, ast.AST],
    tree: ast.AST,
) -> Set[str]:
    returned = set()
    for node in ast.walk(scope):
        if not isinstance(node, ast.Return) or node.value is None:
            continue
        if _enclosing_scope(node, parents, tree) is not scope:
            continue
        candidates = {
            child.id
            for child in ast.walk(node.value)
            if isinstance(child, ast.Name)
            and child.id.lower() in ("errors", "failures", "fehler", "failed")
        }
        returned.update(
            name for name in candidates
            if _collection_failure_expression(node.value, name)
        )
    return returned


def _failure_value_is_propagated(
    value: Optional[ast.AST],
    result_name: Optional[str],
    call: ast.Call,
) -> bool:
    if value is None:
        return False
    if isinstance(value, ast.Constant):
        return bool(
            isinstance(value.value, int)
            and not isinstance(value.value, bool)
            and value.value != 0
        )
    return bool(
        _references_result_returncode(value, result_name, call)
        or _references_result_object(value, result_name, call)
    )


def _exit_value_is_failure(
    value: Optional[ast.AST],
    result_name: Optional[str],
    call: ast.Call,
) -> bool:
    if value is None:
        return False
    if isinstance(value, ast.Constant):
        if value.value is None or value.value is False:
            return False
        if isinstance(value.value, int) and not isinstance(value.value, bool):
            return value.value != 0
        return True
    return _failure_value_is_propagated(value, result_name, call)


def _raise_is_failure(
    statement: ast.Raise,
    result_name: Optional[str],
    call: ast.Call,
) -> bool:
    exception = statement.exc
    if exception is None:
        return True
    if isinstance(exception, ast.Call) and _call_name(exception.func) in (
        "SystemExit", "builtins.SystemExit",
    ):
        value = exception.args[0] if exception.args else None
        return _exit_value_is_failure(value, result_name, call)
    if _call_name(exception) in ("SystemExit", "builtins.SystemExit"):
        return False
    return True


def _failure_append_collection(
    node: ast.AST,
    returned_failure_collections: Set[str],
) -> Optional[str]:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return None
    if node.func.attr != "append" or not isinstance(node.func.value, ast.Name):
        return None
    name = node.func.value.id
    return name if name in returned_failure_collections else None


def _branch_statement_outcomes(
    statement: ast.stmt,
    recorded: bool,
    result_name: Optional[str],
    call: ast.Call,
    returned_failure_collections: Set[str],
) -> Set[Tuple[str, bool]]:
    if isinstance(statement, ast.Raise):
        status = "failure" if _raise_is_failure(statement, result_name, call) else "other-exit"
        return {(status, recorded)}
    if isinstance(statement, ast.Return):
        status = "failure" if _failure_value_is_propagated(statement.value, result_name, call) else "other-exit"
        return {(status, recorded)}
    if isinstance(statement, (ast.Break, ast.Continue)):
        return {("other-exit", recorded)}
    if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
        expression_call = statement.value
        call_name = _call_name(expression_call.func)
        if call_name in ("sys.exit", "os._exit"):
            value = expression_call.args[0] if expression_call.args else None
            status = "failure" if _failure_value_is_propagated(value, result_name, call) else "other-exit"
            return {(status, recorded)}
        if _failure_append_collection(expression_call, returned_failure_collections):
            return {("flow", True)}
    if isinstance(statement, ast.If):
        body = _branch_block_outcomes(
            statement.body,
            recorded,
            result_name,
            call,
            returned_failure_collections,
        )
        otherwise = _branch_block_outcomes(
            statement.orelse,
            recorded,
            result_name,
            call,
            returned_failure_collections,
        ) if statement.orelse else {("flow", recorded)}
        return body | otherwise
    if isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
        body = _branch_block_outcomes(
            statement.body,
            recorded,
            result_name,
            call,
            returned_failure_collections,
        )
        return body | {("flow", recorded)}
    return {("flow", recorded)}


def _branch_block_outcomes(
    statements: Sequence[ast.stmt],
    recorded: bool,
    result_name: Optional[str],
    call: ast.Call,
    returned_failure_collections: Set[str],
) -> Set[Tuple[str, bool]]:
    outcomes = {("flow", recorded)}
    for statement in statements:
        revised = set()
        for status, current_recorded in outcomes:
            if status != "flow":
                revised.add((status, current_recorded))
                continue
            revised.update(
                _branch_statement_outcomes(
                    statement,
                    current_recorded,
                    result_name,
                    call,
                    returned_failure_collections,
                )
            )
        outcomes = revised
    return outcomes


def _branch_propagates_failure(
    statements: Sequence[ast.stmt],
    result_name: Optional[str],
    call: ast.Call,
    returned_failure_collections: Set[str],
) -> bool:
    outcomes = _branch_block_outcomes(
        statements,
        False,
        result_name,
        call,
        returned_failure_collections,
    )
    return bool(outcomes) and all(
        status == "failure" or (status == "flow" and recorded)
        for status, recorded in outcomes
    )


def _direct_nonzero_branch(
    test: ast.AST,
    body: Sequence[ast.stmt],
    orelse: Sequence[ast.stmt],
    result_name: Optional[str],
    call: ast.Call,
) -> Optional[Sequence[ast.stmt]]:
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        return _direct_nonzero_branch(test.operand, orelse, body, result_name, call)
    if isinstance(test, ast.Attribute) and _references_result_returncode(test, result_name, call):
        return body
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or len(test.comparators) != 1:
        return None
    left = test.left
    right = test.comparators[0]
    left_result = _references_result_returncode(left, result_name, call)
    right_result = _references_result_returncode(right, result_name, call)
    left_zero = isinstance(left, ast.Constant) and left.value == 0
    right_zero = isinstance(right, ast.Constant) and right.value == 0
    if not ((left_result and right_zero) or (right_result and left_zero)):
        return None
    if isinstance(test.ops[0], ast.NotEq):
        return body
    if isinstance(test.ops[0], ast.Eq):
        return orelse
    return None


def _nonzero_branch(
    node: ast.If,
    result_name: Optional[str],
    call: ast.Call,
) -> Optional[Sequence[ast.stmt]]:
    return _direct_nonzero_branch(node.test, node.body, node.orelse, result_name, call)


def _same_block_after(
    earlier: ast.AST,
    later: ast.AST,
    parents: Dict[ast.AST, ast.AST],
) -> Optional[Sequence[ast.stmt]]:
    later_container = _statement_container(later, parents)
    current = _statement_ancestor(earlier, parents)
    if later_container is None or current is None:
        return None
    later_parent, later_field, later_statements, later_statement = later_container
    intervening = []
    visited = set()
    while current is not None and current not in visited:
        visited.add(current)
        container = _statement_container(current, parents)
        if container is None:
            return None
        parent, field, statements, current_statement = container
        current_index = next(index for index, item in enumerate(statements) if item is current_statement)
        if parent is later_parent and field == later_field and statements is later_statements:
            later_index = next(index for index, item in enumerate(statements) if item is later_statement)
            if later_index <= current_index:
                return None
            intervening.extend(statements[current_index + 1:later_index])
            return intervening
        intervening.extend(statements[current_index + 1:])
        if isinstance(parent, ast.Try):
            if field == "body":
                intervening.extend(parent.orelse)
            if field in ("body", "orelse") or field.startswith("handlers"):
                intervening.extend(parent.finalbody)
        elif isinstance(parent, (ast.For, ast.AsyncFor, ast.While)) and field == "body":
            intervening.extend(parent.orelse)
        current = parent if isinstance(parent, ast.stmt) else _statement_ancestor(parent, parents)
    return None


def _intervening_paths_preserve_failure(
    statements: Sequence[ast.stmt],
    result_name: Optional[str],
    call: ast.Call,
    scope: ast.AST,
    parents: Dict[ast.AST, ast.AST],
    tree: ast.AST,
) -> bool:
    for statement in statements:
        for node in ast.walk(statement):
            if _enclosing_scope(node, parents, tree) is not scope:
                continue
            if isinstance(node, ast.Raise) and not _raise_is_failure(node, result_name, call):
                return False
            if isinstance(node, (ast.Break, ast.Continue)):
                target = parents.get(node)
                while target is not None and not isinstance(target, (ast.For, ast.AsyncFor, ast.While)):
                    target = parents.get(target)
                if target is None or not any(
                    target is statement or any(child is target for child in ast.walk(statement))
                    for statement in statements
                ):
                    return False
            if isinstance(node, ast.Return) and not _failure_value_is_propagated(node.value, result_name, call):
                return False
            if isinstance(node, ast.Call) and _call_name(node.func) in ("sys.exit", "os._exit"):
                value = node.args[0] if node.args else None
                if not _failure_value_is_propagated(value, result_name, call):
                    return False
    return True


def _result_reassigned_between(
    scope: ast.AST,
    result_name: Optional[str],
    start_line: int,
    end_line: int,
    parents: Dict[ast.AST, ast.AST],
    tree: ast.AST,
) -> bool:
    if not result_name:
        return False
    for node in ast.walk(scope):
        line = getattr(node, "lineno", 0)
        if not start_line < line < end_line or _enclosing_scope(node, parents, tree) is not scope:
            continue
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == result_name for target in node.targets):
                return True
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            if isinstance(node.target, ast.Name) and node.target.id == result_name:
                return True
    return False


def _direct_status_nonzero_branch(
    node: ast.If,
    status_name: str,
) -> Optional[Sequence[ast.stmt]]:
    test = node.test
    body = node.body
    orelse = node.orelse
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        test = test.operand
        body, orelse = orelse, body
    if isinstance(test, ast.Name) and test.id == status_name:
        return body
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or len(test.comparators) != 1:
        return None
    left = test.left
    right = test.comparators[0]
    left_status = isinstance(left, ast.Name) and left.id == status_name
    right_status = isinstance(right, ast.Name) and right.id == status_name
    left_zero = isinstance(left, ast.Constant) and left.value == 0
    right_zero = isinstance(right, ast.Constant) and right.value == 0
    if not ((left_status and right_zero) or (right_status and left_zero)):
        return None
    if isinstance(test.ops[0], ast.NotEq):
        return body
    if isinstance(test.ops[0], ast.Eq):
        return orelse
    return None


def _popen_failure_is_propagated(
    call: ast.Call,
    process_name: str,
    scope: ast.AST,
    parents: Dict[ast.AST, ast.AST],
    tree: ast.AST,
) -> bool:
    wait_results = set()
    wait_lines = []
    for node in ast.walk(scope):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "wait" or not isinstance(node.func.value, ast.Name):
            continue
        if node.func.value.id != process_name or getattr(node, "lineno", 0) <= call.lineno:
            continue
        status_name = _assigned_name(node, parents)
        if status_name:
            wait_results.add(status_name)
            wait_lines.append(int(getattr(node, "lineno", call.lineno) or call.lineno))
    if not wait_results:
        return False
    for node in ast.walk(scope):
        node_line = int(getattr(node, "lineno", 0) or 0)
        if not isinstance(node, ast.If) or node_line <= max(wait_lines):
            continue
        if _enclosing_scope(node, parents, tree) is not scope:
            continue
        intervening = _same_block_after(call, node, parents)
        if intervening is None or not _intervening_paths_preserve_failure(
            intervening,
            process_name,
            call,
            scope,
            parents,
            tree,
        ):
            continue
        for status_name in wait_results:
            branch = _direct_status_nonzero_branch(node, status_name)
            if branch is not None and _branch_propagates_failure(
                branch,
                status_name,
                call,
                set(),
            ):
                return True
    return False


def _subprocess_failure_is_propagated(
    call: ast.Call,
    parents: Dict[ast.AST, ast.AST],
    tree: ast.AST,
    call_name: Optional[str] = None,
) -> bool:
    result_name = _assigned_name(call, parents)
    scope = _enclosing_scope(call, parents, tree)
    returned_failure_collections = _failure_collections_returned(scope, parents, tree)
    parent = parents.get(call)
    if isinstance(parent, ast.Return) and parent.value is call:
        return True
    if (call_name or _call_name(call.func)) == "subprocess.Popen" and result_name:
        if _popen_failure_is_propagated(call, result_name, scope, parents, tree):
            return True

    for node in ast.walk(scope):
        node_line = int(getattr(node, "lineno", 0) or 0)
        if node_line <= call.lineno:
            continue
        if _enclosing_scope(node, parents, tree) is not scope:
            continue
        intervening = _same_block_after(call, node, parents)
        if intervening is None or not _intervening_paths_preserve_failure(
            intervening,
            result_name,
            call,
            scope,
            parents,
            tree,
        ):
            continue
        if _result_reassigned_between(scope, result_name, call.lineno, node_line, parents, tree):
            continue
        if result_name and isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (
                node.func.attr == "check_returncode"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == result_name
            ):
                return True
        if isinstance(node, ast.If) and _references_result_returncode(node.test, result_name, call):
            branch = _nonzero_branch(node, result_name, call)
            if branch is not None and _branch_propagates_failure(
                branch,
                result_name,
                call,
                returned_failure_collections,
            ):
                return True
        if isinstance(node, ast.Return) and _failure_value_is_propagated(node.value, result_name, call):
            return True
    return False


def _is_subprocess_invocation(name: str) -> bool:
    return name in _SUBPROCESS_APIS or name in ("os.popen", "os.system")


def _subprocess_is_checked(call: ast.Call, name: str, parents: Dict[ast.AST, ast.AST], tree: ast.AST) -> bool:
    if name in ("subprocess.check_call", "subprocess.check_output"):
        return True
    for keyword in call.keywords:
        if keyword.arg == "check" and isinstance(keyword.value, ast.Constant):
            if keyword.value.value is True:
                return True
    return _subprocess_failure_is_propagated(call, parents, tree, name)


def _is_unconditional(node: ast.AST, parents: Dict[ast.AST, ast.AST], scope: ast.AST) -> bool:
    current = node
    while current is not scope and current in parents:
        current = parents[current]
        if isinstance(current, (ast.If, ast.While, ast.For, ast.Try, ast.ExceptHandler)):
            return False
    return True


def _string_arguments(call: ast.Call) -> str:
    values = []
    for arg in call.args:
        value = _literal_string(arg)
        if value is not None:
            values.append(value)
    return " ".join(values)


def _is_write_call(call: ast.Call) -> bool:
    name = _call_name(call.func)
    if name in ("open", "io.open"):
        mode = None
        if len(call.args) > 1:
            mode = _literal_string(call.args[1])
        for keyword in call.keywords:
            if keyword.arg == "mode":
                mode = _literal_string(keyword.value)
        return bool(mode and any(flag in mode for flag in ("w", "a", "+", "x")))
    tail = name.rsplit(".", 1)[-1]
    return tail in {
        "chmod", "mkdir", "rmdir", "symlink_to", "touch", "unlink",
        "write_bytes", "write_text",
    }


def _is_destructive_call(call: ast.Call, tokens: Optional[Sequence[str]]) -> bool:
    name = _call_name(call.func)
    if _is_mutating_tokens(tokens):
        return True
    return name in {
        "os.remove", "os.unlink", "shutil.rmtree",
    } or name.endswith((".unlink", "_unlink_nofollow"))


def _is_narrow_ephemeral_cleanup(call: ast.Call, symbol: str, text: str) -> bool:
    name = _call_name(call.func)
    if name not in ("os.remove", "os.unlink", "shutil.rmtree") and not name.endswith(".unlink"):
        return False
    segment = (ast.get_source_segment(text, call) or "").lower()
    return bool(
        (symbol.endswith("_atomic_write") and "tempor" in segment)
        or (symbol.endswith("_unlink_nofollow") and name == "os.unlink")
        or (symbol.endswith("release_lock") and "lock" in segment)
        or (
            symbol.endswith("_worktree")
            and name == "shutil.rmtree"
            and "tempor" in segment
        )
        or (
            symbol.endswith(("rollback_outputs", "discard_promotion_backups", "execute"))
            and name == "shutil.rmtree"
            and "promotion_backup_root" in segment
        )
        or (
            symbol.endswith("candidate_worktree")
            and name.endswith(".unlink")
            and "destination" in segment
        )
    )


def _is_authoritative_write(call: ast.Call, text: str) -> bool:
    if not _is_write_call(call):
        return False
    segment = (ast.get_source_segment(text, call) or "").lower()
    if re.search(r"\b(?:candidate|scratch|temporary)[a-z0-9_]*", segment):
        return False
    return any(name in segment for name in ("todo", "done", "claim", "authorit"))


def _dict_durable_keys(node: ast.Dict, durable_terms: Sequence[str]) -> Set[str]:
    found = set()
    for key in node.keys:
        value = _literal_string(key) if key is not None else None
        if value and any(term in value.lower() for term in durable_terms):
            found.add(value.lower())
    return found


def _write_target_node(call: ast.Call) -> Optional[ast.AST]:
    name = _call_name(call.func)
    tail = name.rsplit(".", 1)[-1]
    if tail in {"write_bytes", "write_text"} and isinstance(call.func, ast.Attribute):
        return call.func.value
    if name in ("open", "io.open", "_atomic_write") and call.args:
        return call.args[0]
    return None


def _write_payload_nodes(call: ast.Call) -> Sequence[ast.AST]:
    name = _call_name(call.func)
    tail = name.rsplit(".", 1)[-1]
    if tail in {"write_bytes", "write_text"}:
        return call.args[:1]
    if name == "_atomic_write":
        return call.args[1:2]
    return []


def _expanded_payload_nodes(
    node: ast.AST,
    scope: ast.AST,
    parents: Dict[ast.AST, ast.AST],
    tree: ast.AST,
    before_line: int,
    seen: Optional[Set[str]] = None,
) -> List[ast.AST]:
    seen = set(seen or set())
    expanded = [node]
    if isinstance(node, ast.Name) and node.id not in seen:
        seen.add(node.id)
        for candidate in ast.walk(scope):
            if getattr(candidate, "lineno", before_line) >= before_line:
                continue
            if _enclosing_scope(candidate, parents, tree) is not scope:
                continue
            value = None
            if isinstance(candidate, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == node.id for target in candidate.targets
            ):
                value = candidate.value
            elif isinstance(candidate, ast.AnnAssign) and isinstance(candidate.target, ast.Name):
                if candidate.target.id == node.id:
                    value = candidate.value
            if value is not None:
                expanded.extend(
                    _expanded_payload_nodes(
                        value,
                        scope,
                        parents,
                        tree,
                        int(getattr(candidate, "lineno", before_line) or before_line),
                        seen,
                    )
                )
    elif isinstance(node, ast.Call):
        for argument in list(node.args) + [keyword.value for keyword in node.keywords]:
            expanded.extend(
                _expanded_payload_nodes(
                    argument,
                    scope,
                    parents,
                    tree,
                    before_line,
                    seen,
                )
            )
    return expanded


def _payload_records_operation_state(nodes: Sequence[ast.AST]) -> bool:
    state_terms = ("journal", "recovery", "rollback", "result", "outcome", "exit_code", "status")
    link_terms = (
        "action", "argv", "backup", "command", "commit", "entries", "operation",
        "path", "phase", "previous", "promoted", "ref", "request_id", "target", "task_id",
    )
    literals = []
    runtime_outcome = False
    for node in nodes:
        for child in ast.walk(node):
            value = _literal_string(child)
            if value is not None:
                literals.append(value.lower())
            if isinstance(child, ast.Attribute) and child.attr == "returncode":
                runtime_outcome = True
            if isinstance(child, ast.Name) and child.id.lower() in ("exit_code", "returncode"):
                runtime_outcome = True
    content = " ".join(literals)
    has_state = runtime_outcome or any(term in content for term in state_terms)
    has_link = runtime_outcome or any(term in content for term in link_terms)
    return has_state and has_link


_IDENTITY_WORD_RE = re.compile(r"[A-Za-z0-9_.:/+-]+")
_GENERIC_IDENTITY_WORDS = {
    "action", "add", "argv", "backup", "check", "command", "commit", "deleted",
    "entries", "failed", "git", "journal", "operation", "outcome", "path", "phase",
    "previous", "promoted", "published", "push", "recovery", "ref", "request_id",
    "result", "rollback", "status", "success", "target", "task_id",
}
_GENERIC_IDENTITY_NAMES = {
    "bool", "bytes", "dict", "json", "len", "list", "os", "self", "shutil", "str",
    "subprocess", "tuple",
}


def _identity_literal_words(value: str) -> Set[str]:
    return {
        word.lower()
        for word in _IDENTITY_WORD_RE.findall(value)
        if len(word) > 1
        and not word.startswith("-")
        and word.lower() not in _GENERIC_IDENTITY_WORDS
    }


def _python_identity_tokens(nodes: Sequence[ast.AST]) -> Set[str]:
    identity = set()
    for node in nodes:
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and child.id.lower() not in _GENERIC_IDENTITY_NAMES:
                identity.add(child.id.lower())
            value = _literal_string(child)
            if value is not None:
                identity.update(_identity_literal_words(value))
    return identity


def _strong_recovery_payload(nodes: Sequence[ast.AST]) -> bool:
    words = set()
    for node in nodes:
        for child in ast.walk(node):
            value = _literal_string(child)
            if value is not None:
                words.update(word.lower() for word in _IDENTITY_WORD_RE.findall(value))
    recovery_fields = {"entries", "previous", "promoted", "backup"}
    identity_fields = {"task_id", "request_id", "path"}
    return len(words & recovery_fields) >= 3 and bool(words & identity_fields)


def _write_operation_state_profile(
    call: ast.Call,
    text: str,
    parents: Dict[ast.AST, ast.AST],
    tree: ast.AST,
) -> Optional[Tuple[Set[str], bool]]:
    target = _write_target_node(call)
    payload = _write_payload_nodes(call)
    if target is None or not payload:
        return None
    target_text = (ast.get_source_segment(text, target) or "").lower()
    if not any(
        term in target_text
        for term in ("journal", "recovery", "rollback", "result", "outcome", "status", "log", "evidence")
    ):
        return None
    scope = _enclosing_scope(call, parents, tree)
    expanded = []
    for node in payload:
        expanded.extend(
            _expanded_payload_nodes(node, scope, parents, tree, call.lineno)
        )
    if not _payload_records_operation_state(expanded):
        return None
    return _python_identity_tokens(expanded), _strong_recovery_payload(expanded)


def _statement_list_positions(
    node: ast.AST,
    parents: Dict[ast.AST, ast.AST],
) -> List[Tuple[ast.AST, str, int, Sequence[ast.stmt]]]:
    positions = []
    current = node
    while current in parents:
        parent = parents[current]
        if isinstance(current, ast.stmt):
            for field, value in ast.iter_fields(parent):
                if not isinstance(value, list):
                    continue
                for index, statement in enumerate(value):
                    if statement is current:
                        positions.append((parent, field, index, value))
                        break
        current = parent
    return positions


def _statement_list_position(
    node: ast.AST,
    parents: Dict[ast.AST, ast.AST],
) -> Optional[Tuple[ast.AST, str, int, Sequence[ast.stmt]]]:
    positions = _statement_list_positions(node, parents)
    return positions[0] if positions else None


def _statement_may_bypass(statement: ast.stmt) -> bool:
    def visit(node: ast.AST, root: bool = False) -> bool:
        if not root and isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda),
        ):
            return False
        if isinstance(
            node,
            (ast.Return, ast.Raise, ast.Break, ast.Continue, ast.Yield, ast.YieldFrom),
        ):
            return True
        if isinstance(node, ast.Call) and _call_name(node.func) in (
            "exit", "quit", "builtins.exit", "builtins.quit",
            "os._exit", "os.abort", "sys.exit",
        ):
            return True
        return any(visit(child) for child in ast.iter_child_nodes(node))

    return visit(statement, root=True)


def _node_is_direct_in_statement(
    node: ast.AST,
    statement: ast.stmt,
    parents: Dict[ast.AST, ast.AST],
) -> bool:
    current = node
    while current is not statement and current in parents:
        current = parents[current]
        if isinstance(
            current,
            (
                ast.BoolOp,
                ast.IfExp,
                ast.comprehension,
                ast.DictComp,
                ast.GeneratorExp,
                ast.ListComp,
                ast.SetComp,
                ast.Lambda,
            ),
        ):
            return False
    return current is statement


def _node_postdominates_operation(
    operation_node: ast.AST,
    outcome_node: ast.AST,
    parents: Dict[ast.AST, ast.AST],
) -> bool:
    operation_positions = _statement_list_positions(operation_node, parents)
    outcome_position = _statement_list_position(outcome_node, parents)
    if not operation_positions or outcome_position is None:
        return False
    outcome_owner, outcome_field, outcome_index, statements = outcome_position
    outcome_statement = statements[outcome_index]
    if not _node_is_direct_in_statement(outcome_node, outcome_statement, parents):
        return False

    shared_index = None
    for index, (owner, field, _position, _statements) in enumerate(operation_positions):
        if owner is outcome_owner and field == outcome_field:
            shared_index = index
            break
    if shared_index is None:
        return False

    for _owner, _field, operation_index, operation_statements in operation_positions[:shared_index]:
        if any(
            _statement_may_bypass(statement)
            for statement in operation_statements[operation_index + 1:]
        ):
            return False

    _owner, _field, operation_index, operation_statements = operation_positions[shared_index]
    if outcome_index <= operation_index:
        return False
    return not any(
        _statement_may_bypass(statement)
        for statement in operation_statements[operation_index + 1:outcome_index]
    )


def _scope_has_durable_state(
    recovery_scope: ast.AST,
    execution_scope: ast.AST,
    text: str,
    operation_line: int,
    operation_node: ast.Call,
    operation_tokens: Optional[Sequence[str]],
    parents: Dict[ast.AST, ast.AST],
    tree: ast.AST,
) -> bool:
    state_terms = ("journal", "recovery", "rollback", "result", "outcome", "exit_code", "status")
    link_terms = (
        "action", "argv", "backup", "command", "commit", "entries", "operation",
        "path", "phase", "previous", "promoted", "ref", "request_id", "target", "task_id",
    )
    operation_identity = _python_identity_tokens([operation_node])
    if operation_tokens:
        operation_identity.update(_identity_literal_words(" ".join(operation_tokens)))
    assigned_operation = _assigned_name(operation_node, parents)
    if assigned_operation:
        operation_identity.add(assigned_operation.lower())

    structured_writers = {}
    for node in ast.walk(recovery_scope):
        if not isinstance(node, ast.Call):
            continue
        profile = _write_operation_state_profile(node, text, parents, tree)
        if profile is None:
            continue
        payload_identity, strong_recovery = profile
        writer_scope = _enclosing_scope(node, parents, tree)
        if (
            writer_scope is execution_scope
            and node.lineno >= operation_line
            and _node_postdominates_operation(operation_node, node, parents)
        ):
            if strong_recovery or bool(operation_identity & payload_identity):
                return True
        if isinstance(writer_scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
            structured_writers[writer_scope.name] = (payload_identity, strong_recovery)
    for node in ast.walk(execution_scope):
        if not isinstance(node, ast.Call) or _enclosing_scope(node, parents, tree) is not execution_scope:
            continue
        if node.lineno < operation_line:
            continue
        writer_name = _call_name(node.func).rsplit(".", 1)[-1]
        profile = structured_writers.get(writer_name)
        if profile is None:
            continue
        payload_identity, strong_recovery = profile
        if not _node_postdominates_operation(operation_node, node, parents):
            continue
        if strong_recovery or bool(operation_identity & payload_identity):
            return True

    execution_writes = []
    atomic_promotions = []
    outcome_returns = []
    for node in ast.walk(execution_scope):
        if isinstance(node, ast.Call):
            name = _call_name(node.func)
            if _is_write_call(node):
                execution_writes.append(node)
            if name in ("os.replace", "os.rename") or name.endswith((".replace", ".rename")):
                atomic_promotions.append(node)
        elif isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
            state_keys = _dict_durable_keys(node.value, state_terms)
            link_keys = _dict_durable_keys(node.value, link_terms)
            return_identity = _python_identity_tokens([node.value])
            if (
                state_keys & {"status", "outcome", "exit_code", "result"}
                and link_keys
                and operation_identity & return_identity
            ):
                outcome_returns.append(node)
    promotion_follows = any(
        node is operation_node
        or _node_postdominates_operation(operation_node, node, parents)
        for node in atomic_promotions
    )
    outcome_follows = any(
        _node_postdominates_operation(operation_node, node, parents)
        for node in outcome_returns
    )
    return bool(
        execution_writes
        and promotion_follows
        and outcome_follows
        and min(node.lineno for node in execution_writes) <= operation_line
    )


def scan_python(path: str, text: str) -> List[Finding]:
    lines = text.splitlines()
    try:
        tree = ast.parse(text, filename=path)
    except SyntaxError as exc:
        return [_finding("AUTO000", path, exc.lineno or 1, "<module>", lines)]

    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    aliases = _import_call_aliases(tree)
    findings = []
    subprocess_calls = []
    destructive = []
    gate_lines = []
    unsafe_subprocess = False
    unsafe_required_gate = False
    unsafe_scope_lines = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _resolved_call_name(node.func, aliases)
        symbol = _symbol_for(node, parents)
        enclosing = _enclosing_scope(node, parents, tree)
        is_subprocess = _is_subprocess_invocation(name)
        token_variants = _command_variants(node, enclosing, parents, tree) if is_subprocess else []
        tokens = max(token_variants, key=_command_risk) if token_variants else None
        checked = _subprocess_is_checked(node, name, parents, tree) if is_subprocess else False
        mutating_command = any(_is_mutating_tokens(variant) for variant in token_variants)
        unknown_command = any(
            _is_unknown_command(variant) or _is_effectively_unknown_command(variant)
            for variant in token_variants
        )
        publication_command = any(
            _is_publication_tokens(variant) for variant in token_variants
        )
        if is_subprocess:
            subprocess_calls.append((node, name, tokens, symbol))
            if any(_contains_gate(variant) for variant in token_variants):
                gate_lines.append((node.lineno, enclosing))
                if not checked:
                    unsafe_required_gate = True

        shell_keyword = any(
            keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True
            for keyword in node.keywords
        )
        shell_argv = any(_invokes_shell_interpreter(variant) for variant in token_variants)
        if name in ("os.popen", "os.system") or shell_keyword or shell_argv:
            severity = "critical" if "TODO" in (ast.get_source_segment(text, node) or "") else None
            findings.append(_python_finding("AUTO006", path, node, symbol, lines, severity=severity))

        if (mutating_command or unknown_command) and not checked:
            unsafe_subprocess = True
            unsafe_scope_lines.setdefault(enclosing, []).append(node.lineno)
            findings.append(_python_finding("AUTO001", path, node, symbol, lines))
        if publication_command and not checked:
            findings.append(_python_finding("AUTO009", path, node, symbol, lines))

        if any(_is_broad_git_add(variant) for variant in token_variants):
            findings.append(_python_finding("AUTO003", path, node, symbol, lines))
        if any(_is_force_protected_push(variant) for variant in token_variants):
            findings.append(_python_finding("AUTO004", path, node, symbol, lines))
        if any(_has_hardcoded_integration(variant) for variant in token_variants):
            findings.append(_python_finding("AUTO005", path, node, symbol, lines, severity="critical"))

        destructive_call = mutating_command or _is_destructive_call(node, tokens)
        if destructive_call and _is_narrow_ephemeral_cleanup(node, symbol, text):
            destructive_call = False
        if destructive_call or _is_authoritative_write(node, text):
            recovery_scope = _recovery_scope(node, parents, tree)
            destructive.append((node.lineno, symbol, node, tokens, enclosing, recovery_scope))

        if isinstance(enclosing, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lower_name = enclosing.name.lower()
            if any(word in lower_name for word in ("audit", "check", "sanitize", "validate")) and _is_write_call(node):
                findings.append(_python_finding("AUTO007", path, node, symbol, lines))

        if isinstance(node.func, ast.Attribute) and node.func.attr == "get" and len(node.args) >= 2:
            key = _literal_string(node.args[0])
            default = node.args[1]
            if key in ("overall_success", "success", "passed") and isinstance(default, ast.Constant) and default.value is True:
                findings.append(_python_finding("AUTO002", path, node, symbol, lines))

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        failure_names = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and child.func.attr == "append":
                if isinstance(child.func.value, ast.Name) and child.func.value.id.lower() in ("errors", "failures", "fehler"):
                    failure_names.add(child.func.value.id)
        if failure_names:
            for child in ast.walk(node):
                if isinstance(child, ast.Return) and _return_is_guaranteed_zero(child.value):
                    if _is_unconditional(child, parents, node):
                        findings.append(_python_finding("AUTO002", path, child, node.name, lines))

    for scope, unsafe_lines in unsafe_scope_lines.items():
        if not isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(scope):
            if not isinstance(node, ast.Return) or _enclosing_scope(node, parents, tree) is not scope:
                continue
            if not _return_is_guaranteed_zero(node.value):
                continue
            if node.lineno > min(unsafe_lines) and _is_unconditional(node, parents, scope):
                findings.append(_python_finding("AUTO002", path, node, scope.name, lines))

    if unsafe_subprocess or unsafe_required_gate or any(f.rule == "AUTO009" for f in findings):
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or _call_name(node.func) not in ("print", "logging.info", "logging.warning"):
                continue
            if not _PASS_RE.search(_string_arguments(node)):
                continue
            scope = _enclosing_scope(node, parents, tree)
            if _is_unconditional(node, parents, scope):
                findings.append(_python_finding("AUTO002", path, node, _symbol_for(node, parents), lines))

    if gate_lines and destructive:
        for scope in {item[4] for item in destructive}:
            scope_gates = [line for line, gate_scope in gate_lines if gate_scope is scope]
            if not scope_gates:
                continue
            earlier = [item for item in destructive if item[4] is scope and item[0] < max(scope_gates)]
            if earlier:
                _line, symbol, found_node, _tokens, _scope, _recovery = min(earlier, key=lambda item: item[0])
                findings.append(_python_finding("AUTO008", path, found_node, symbol, lines))

    for scope in {item[5] for item in destructive}:
        scoped = [item for item in destructive if item[5] is scope]
        missing = [
            item
            for item in scoped
            if not _scope_has_durable_state(
                scope,
                item[4],
                text,
                item[0],
                item[2],
                item[3],
                parents,
                tree,
            )
        ]
        for _line, symbol, found_node, tokens, _execution_scope, _recovery in missing:
            segment = (ast.get_source_segment(text, found_node) or "").lower()
            critical = any(name in segment for name in ("todo", "done", "claim", "authorit"))
            critical = critical or _is_publication_tokens(tokens)
            findings.append(
                _python_finding(
                    "AUTO010",
                    path,
                    found_node,
                    symbol,
                    lines,
                    severity="critical" if critical else "high",
                )
            )

    return _dedupe(findings)


def _skip_shell_expansion(text: str, start: int, opening: str, closing: str) -> int:
    depth = 1
    index = start + 2
    quote = None
    while index < len(text) and depth:
        character = text[index]
        following = text[index + 1] if index + 1 < len(text) else ""
        if character == "\\" and quote != "'":
            index += 2
            continue
        if quote is not None:
            if quote == '"' and character == "$" and following in ("(", "{"):
                index = _skip_shell_expansion(text, index, following, ")" if following == "(" else "}")
                continue
            if character == quote:
                quote = None
            index += 1
            continue
        if character in ("'", '"'):
            quote = character
            index += 1
            continue
        if character == "`":
            index += 1
            while index < len(text):
                if text[index] == "\\":
                    index += 2
                    continue
                if text[index] == "`":
                    index += 1
                    break
                index += 1
            continue
        if character == "$" and following in ("(", "{"):
            index = _skip_shell_expansion(text, index, following, ")" if following == "(" else "}")
            continue
        if character == opening:
            depth += 1
        elif character == closing:
            depth -= 1
        index += 1
    return index


def _shell_structural_text(line: str) -> str:
    visible = []
    index = 0
    quote = None
    while index < len(line):
        character = line[index]
        following = line[index + 1] if index + 1 < len(line) else ""
        if character == "\\" and quote != "'":
            visible.extend("  ")
            index += 2
            continue
        if quote is not None:
            if quote == '"' and character == "$" and following in ("(", "{"):
                end = _skip_shell_expansion(line, index, following, ")" if following == "(" else "}")
                visible.extend(" " * (end - index))
                index = end
                continue
            if character == quote:
                quote = None
            visible.append(" ")
            index += 1
            continue
        if character in ("'", '"'):
            quote = character
            visible.append(" ")
            index += 1
            continue
        if character == "$" and following in ("(", "{"):
            end = _skip_shell_expansion(line, index, following, ")" if following == "(" else "}")
            visible.extend(" " * (end - index))
            index = end
            continue
        if character == "`":
            end = index + 1
            while end < len(line):
                if line[end] == "\\":
                    end += 2
                    continue
                if line[end] == "`":
                    end += 1
                    break
                end += 1
            visible.extend(" " * (end - index))
            index = end
            continue
        if character == "#" and (
            index == 0 or line[index - 1].isspace() or line[index - 1] in ";|&()"
        ):
            break
        visible.append(character)
        index += 1
    return "".join(visible)


def _shell_symbol(lines: Sequence[str], target_line: int) -> str:
    symbol = "<module>"
    pending = None
    depth = 0
    for index, line in enumerate(lines, 1):
        structural = _shell_structural_text(line)
        stripped = structural.strip()
        if symbol == "<module>":
            start_match = _FUNCTION_START_RE.match(structural)
            pending_match = _FUNCTION_PENDING_RE.match(structural)
            if start_match:
                symbol = start_match.group(1) or start_match.group(2)
                pending = None
                depth = structural.count("{") - structural.count("}")
            elif pending_match:
                pending = pending_match.group(1) or pending_match.group(2)
            elif pending and stripped:
                if stripped.startswith("{"):
                    symbol = pending
                    pending = None
                    depth = structural.count("{") - structural.count("}")
                else:
                    pending = None
        else:
            depth += structural.count("{") - structural.count("}")

        current_symbol = symbol
        if index == target_line:
            return current_symbol
        if symbol != "<module>" and depth <= 0:
            symbol = "<module>"
    return symbol


def _shell_command_words(line: str) -> List[str]:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return []
    try:
        lexer = shlex.shlex(
            stripped,
            posix=True,
            punctuation_chars=";&|(){}",
        )
        lexer.whitespace_split = True
        lexer.commenters = "#"
        return list(lexer)
    except ValueError:
        return stripped.split()


def _shell_logical_command(lines: Sequence[str], target_line: int) -> str:
    index = target_line - 1
    start = index
    while start > 0 and lines[start - 1].endswith("\\"):
        start -= 1
    return "".join(
        line[:-1] if line.endswith("\\") else line
        for line in lines[start:index + 1]
    )


_SHELL_CONTROL_WORDS = {"!", "do", "elif", "else", "if", "then", "until", "while"}
_SHELL_NONCOMMAND_WORDS = {"case", "done", "esac", "fi", "for", "in", "select"}
_SHELL_REDIRECTION_RE = re.compile(r"^[0-9]*(?:<>|>>?|<<?|>\|)(.*)$")


def _shell_command_segments(words: Sequence[str]) -> List[List[str]]:
    segments = []
    current = []
    for word in words:
        if re.fullmatch(r"[;&|(){}]+", word):
            if current:
                segments.append(current)
                current = []
            continue
        current.append(word)
    if current:
        segments.append(current)
    return segments


def _shell_simple_commands(words: Sequence[str]) -> List[List[str]]:
    commands = []
    for original in _shell_command_segments(words):
        segment = list(original)
        if len(segment) >= 2 and segment[1] == "()":
            continue
        if segment and segment[0] == "function":
            continue
        while segment and segment[0].lower() in _SHELL_CONTROL_WORDS:
            segment.pop(0)
        if not segment or segment[0].lower() in _SHELL_NONCOMMAND_WORDS:
            continue
        index = 0
        while index < len(segment):
            token = segment[index]
            redirect = _SHELL_REDIRECTION_RE.match(token)
            if redirect:
                index += 1 if redirect.group(1) else 2
                continue
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", token):
                index += 1
                continue
            break
        command = _effective_command_tokens(segment[index:])
        if command:
            commands.append(command)
    return commands


def _shell_direct_command_tokens(words: Sequence[str]) -> List[str]:
    commands = _shell_simple_commands(words)
    return commands[0] if commands else []


def _shell_mutation(line: str, words: Sequence[str]) -> bool:
    lowered = line.lower()
    structural = _shell_structural_text(line).lower()
    for direct in _shell_simple_commands(words):
        command = os.path.basename(direct[0]).lower()
        if command in _MUTATING_COMMANDS - {"sed"}:
            return True
        if command == "sed" and any(
            token == "-i"
            or token.startswith("-i")
            or token == "--in-place"
            or token.startswith("--in-place=")
            for token in direct[1:]
        ):
            return True
        if command == "git" and _git_subcommand(direct) in _MUTATING_GIT:
            return True
    mutators = sorted(_MUTATING_COMMANDS - {"sed"}, key=len, reverse=True)
    mutator_pattern = r"(?:^|[\s;&|(){}])(?:[^\s;&|(){}]*/)?(?:%s)(?=$|[\s;&|(){}])" % "|".join(
        re.escape(command) for command in mutators
    )
    if re.search(mutator_pattern, structural):
        return True
    if re.search(
        r"(?:^|[\s;&|(){}])(?:[^\s;&|(){}]*/)?sed"
        r"(?:\s+-[^\s;&|(){}]+)*\s+(?:-i[^\s;&|(){}]*|--in-place(?:=[^\s;&|(){}]+)?)"
        r"(?=$|[\s;&|(){}])",
        structural,
    ):
        return True
    if re.search(r"\bgit\s+(?:-[^ ]+\s+)*(add|commit|push|reset|clean|checkout|switch|remote|update-ref|rm|mv)\b", lowered):
        return True
    if re.search(r">>?\s*[^&]", line) and any(name in line for name in ("TODO", "DONE", "claim", ".json")):
        return True
    return False


def _shell_gate(line: str) -> bool:
    lowered = line.lower().lstrip()
    if lowered.startswith("#"):
        return False
    return re.search(
        r"(?:\b(?:python[0-9.]*\s+)?[^;&|]*(?:validate[.]py|pytest|unittest)\b|"
        r"\bnpm\s+test\b|\bmake\s+test\b|\bgit\s+(?:ls-tree|ls-remote|diff\s+--cached)\b|"
        r"\bssh-keygen\b)",
        lowered,
    ) is not None


def _shell_pre_gate_mutation(line: str) -> bool:
    lowered = line.lower()
    if re.search(r"\brm\s+(?:-[^ ]*r[^ ]*\s+|-r[f]?\s+)", lowered):
        return True
    if re.search(r"\bgit\s+(?:-[^ ]+\s+)*(add|commit|push|reset|clean|checkout|switch|remote|update-ref|rm|mv)\b", lowered):
        return True
    if re.search(r"\b(?:sed\s+-i|mv)\b", lowered):
        return True
    if ">>" in line:
        return True
    if re.search(r">\s*[^&]", line) and any(name in line for name in ("TODO", "DONE", "KNOWN_HOSTS")):
        return True
    return False


def _shell_broad_mutation(line: str) -> bool:
    lowered = line.lower()
    if re.search(r"\bgit\s+add\s+([^#]*(?:-a\b|--all\b|(?:^|\s)\.\s*(?:$|[;&|])))", lowered):
        return True
    if re.search(r"\bgit\s+add\b[^#]*[*?\[]", line):
        return True
    if re.search(r"\brm\b[^#]*(?:TODO-[^ ]*\*|[*?\[]) ", line + " "):
        return True
    return False


def _shell_force_protected(line: str) -> bool:
    lowered = line.lower()
    if re.search(r"\bgit\s+push\b", lowered) is None:
        return False
    protected = re.search(r"(?:^|[/:=])(?:refs/heads/)?(?:main|master)\b", lowered) is not None
    explicit_force = re.search(r"(?:\s-f\b|--force(?:-with-lease)?(?:=\S+)?\b)", lowered) is not None
    plus_force = re.search(r"(?:^|\s)\+\S*(?:[:/])(?:refs/heads/)?(?:main|master)\b", lowered) is not None
    return protected and (explicit_force or plus_force)


def _shell_hardcoded_integration(line: str) -> bool:
    lowered = line.lower()
    if "user.name=" in lowered or "user.email=" in lowered:
        return True
    if re.search(r"\bgit\s+(?:remote|push)\b", lowered) and re.search(r"(?:git@|ssh://|https://|\b(?:main|master)\b)", line, re.IGNORECASE):
        return True
    if re.search(r"^(?:REMOTE|REPOSITORY|REPO|ORIGIN|IDENTITY|USER_EMAIL|GIT_EMAIL)[A-Z0-9_]*=", line.strip()) and re.search(r"(?:git@|ssh://|https://)[^ '\"]+", line):
        return True
    return False


def _shell_identity_tokens(text: str) -> Set[str]:
    identity = {
        match.group(1).lower()
        for match in re.finditer(r"\$(?:\{)?([A-Za-z_][A-Za-z0-9_]*)", text)
    }
    identity.update(_identity_literal_words(text))
    return identity


def _shell_runtime_status_is_immediate(
    lines: Sequence[str],
    operation_line: int,
    state_line: int,
) -> bool:
    if state_line < operation_line:
        return False
    for number in range(operation_line + 1, state_line):
        stripped = lines[number - 1].strip()
        if stripped and not stripped.startswith("#"):
            return False
    return True


def _shell_runtime_capture_is_direct(payload: str) -> bool:
    if "$(" in payload or "`" in payload:
        return False
    unquoted = _shell_unquoted_text(payload)
    return not (
        ";" in unquoted
        or "&&" in unquoted
        or "||" in unquoted
        or _shell_has_pipeline(unquoted)
        or re.search(r"(?<![&>])&(?![&>])", unquoted) is not None
    )


def _shell_state_postdominates_operation(
    lines: Sequence[str],
    operation_line: int,
    state_line: int,
    logical_line: str,
) -> bool:
    if not _shell_runtime_status_is_immediate(lines, operation_line, state_line):
        return False
    unquoted = _shell_unquoted_text(logical_line).strip()
    operation_unquoted = _shell_unquoted_text(
        _shell_logical_command(lines, operation_line)
    ).strip()
    if re.match(r"^(?:if|elif|while|until|for|case)\b", unquoted):
        return False
    if ";" in unquoted or ";" in operation_unquoted:
        return False
    if "&&" in unquoted or "||" in unquoted or _shell_has_pipeline(unquoted):
        return False
    bypass = re.compile(r"(?:^|[;&|(){}]\s*)(?:break|continue|exec|exit|return)\b")
    if bypass.search(unquoted) or bypass.search(operation_unquoted):
        return False
    return _shell_has_background_operator(unquoted) is False


def _shell_has_durable_state(
    lines: Sequence[str],
    symbol: str,
    operation_line: int,
    operation_text: str,
) -> bool:
    state_terms = ("journal", "recovery", "rollback", "result", "outcome", "exit_code", "status")
    link_terms = (
        "action", "argv", "backup", "command", "commit", "operation", "path", "phase",
        "previous", "promoted", "ref", "request", "target", "task",
    )
    runtime_outcome = re.compile(
        r"(?:\$\?|\$\{?PIPESTATUS(?:\[[0-9]+\])?\}?)",
        re.IGNORECASE,
    )
    operation_identity = _shell_identity_tokens(operation_text)
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if number < operation_line:
            continue
        if not stripped or stripped.startswith("#") or _shell_symbol(lines, number) != symbol:
            continue
        logical_line = _shell_logical_command(lines, number)
        if not _shell_state_postdominates_operation(
            lines,
            operation_line,
            number,
            logical_line,
        ):
            continue
        redirect = re.search(r"(?<![0-9])>>?\s*([^;&|]+)", logical_line)
        tee = re.search(r"\btee(?:\s+-[A-Za-z]+)*\s+([^;&|]+)", logical_line)
        match = redirect or tee
        if match is None:
            continue
        target = match.group(1).lower()
        if not any(
            term in target
            for term in ("journal", "recovery", "rollback", "result", "outcome", "status", "log", "evidence")
        ):
            continue
        payload = logical_line[:match.start()].lower()
        runtime_reference = runtime_outcome.search(payload) is not None
        runtime_link = bool(
            runtime_reference
            and _shell_runtime_status_is_immediate(lines, operation_line, number)
            and _shell_runtime_capture_is_direct(payload)
        )
        if runtime_reference and not runtime_link:
            continue
        has_state = any(term in payload for term in state_terms) or runtime_link
        has_link = any(term in payload for term in link_terms) or runtime_link
        payload_identity = _shell_identity_tokens(payload)
        recovery_fields = sum(
            term in payload for term in ("entries", "previous", "promoted", "backup")
        )
        strong_recovery = recovery_fields >= 3 and any(
            term in payload for term in ("path", "request", "task")
        )
        if has_state and has_link and (
            runtime_link
            or strong_recovery
            or bool(operation_identity & payload_identity)
        ):
            return True
    return False


def _shell_errexit_update(line: str, current: bool) -> bool:
    stripped = line.strip()
    if re.search(r"^set\s+\+[^#;]*e", stripped) or re.search(r"^set\s+\+o\s+errexit\b", stripped):
        return False
    if re.search(r"^set\s+-[^#;]*e", stripped) or re.search(r"^set\s+-o\s+errexit\b", stripped):
        return True
    return current


def _shell_pipefail_update(line: str, current: bool) -> bool:
    stripped = line.strip()
    if re.search(r"^set\s+\+o\s+pipefail\b", stripped):
        return False
    if re.search(r"^set\s+-o\s+pipefail\b", stripped):
        return True
    if re.search(r"^set\s+-[^#;]*\bpipefail\b", stripped):
        return True
    return current


def _shell_unquoted_text(line: str) -> str:
    visible = []
    quote = None
    escaped = False
    for character in line:
        if escaped:
            visible.append(" " if quote else character)
            escaped = False
            continue
        if character == "\\" and quote != "'":
            escaped = True
            visible.append(" ")
            continue
        if quote is not None:
            if character == quote:
                quote = None
            visible.append(" ")
            continue
        if character in ("'", '"'):
            quote = character
            visible.append(" ")
            continue
        visible.append(character)
    return "".join(visible)



def _shell_has_pipeline(line: str) -> bool:
    return re.search(r"(?<![>|])\|(?!\|)", _shell_unquoted_text(line)) is not None


def _shell_has_background_operator(line: str) -> bool:
    return re.search(r"(?<![&>])&(?![&>])", _shell_unquoted_text(line)) is not None


def _shell_explicit_failure_handler(line: str) -> bool:
    unquoted = _shell_unquoted_text(line)
    return re.search(
        r"\|\|\s*(?:exit|return)\s+(?:[1-9][0-9]*|\$\?)(?=\s|;|$)",
        unquoted,
    ) is not None


def _shell_errexit_suppressed(line: str, pipefail: bool) -> bool:
    stripped = _shell_unquoted_text(line).strip()
    if re.match(r"^(?:if|while|until)\b", stripped):
        return True
    if re.search(r"(?:^|[;&|]\s*)!\s*[^=]", stripped):
        return True
    if "&&" in stripped or "||" in stripped:
        return True
    if _shell_has_pipeline(stripped) and not pipefail:
        return True
    if _shell_has_background_operator(stripped):
        return True
    return False



def _status_consuming_shell_wrappers(lines: Sequence[str]) -> Set[str]:
    wrappers = set()
    for number, line in enumerate(lines, 1):
        if re.search(r"^\s*if\s+[\"']?\$@[\"']?(?:\s|;)", line):
            symbol = _shell_symbol(lines, number)
            if symbol != "<module>":
                wrappers.add(symbol)
    return wrappers




def _shell_failure_propagates(
    line: str,
    errexit: bool,
    pipefail: bool,
) -> bool:
    if _shell_has_pipeline(line) and not pipefail:
        return False
    if _shell_explicit_failure_handler(line):
        return True
    if _shell_errexit_suppressed(line, pipefail):
        return False
    return errexit


def _shell_aggregate_finding(
    rule: str,
    path: str,
    items: Sequence[Tuple[int, str, str]],
    lines: Sequence[str],
    severity: Optional[str] = None,
) -> Finding:
    ordered = sorted(items, key=lambda item: (item[0], item[2]))
    number, symbol, _logical_line = ordered[0]
    evidence = "\n".join(item[2] for item in ordered)
    return _finding(
        rule,
        path,
        number,
        symbol,
        lines,
        severity=severity,
        evidence_text=evidence,
    )


def scan_shell(path: str, text: str) -> List[Finding]:
    lines = text.splitlines()
    findings = []
    mutations = []
    pre_gate_mutations = []
    gates = []
    unsafe_failure = False
    unchecked_mutations = []
    unchecked_publications = []
    module_errexit = False
    module_pipefail = False
    function_declaration_seen = False
    status_consuming_wrappers = _status_consuming_shell_wrappers(lines)

    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        logical_line = _shell_logical_command(lines, number)
        structural_line = _shell_structural_text(logical_line)
        if _FUNCTION_ANY_DECL_RE.search(structural_line):
            function_declaration_seen = True
        symbol = _shell_symbol(lines, number)
        if symbol == "<module>":
            module_errexit = _shell_errexit_update(line, module_errexit)
            module_pipefail = _shell_pipefail_update(line, module_pipefail)
            errexit = module_errexit
            pipefail = module_pipefail
        else:
            errexit = False
            pipefail = False

        logical_stripped = logical_line.strip()
        words = _shell_command_words(logical_line)
        commands = _shell_simple_commands(words)
        direct_command = commands[0] if commands else []
        normalized_commands = "\n".join(" ".join(command) for command in commands)
        classification_line = logical_line + ("\n" + normalized_commands if normalized_commands else "")
        mutation = _shell_mutation(logical_line, words)
        gate = _shell_gate(classification_line)
        if mutation:
            mutations.append((number, symbol, logical_line))
        if _shell_pre_gate_mutation(classification_line):
            pre_gate_mutations.append((number, symbol, logical_line))
        if gate:
            gates.append((number, symbol))

        unquoted_logical = _shell_unquoted_text(logical_line)
        ignored = "|| true" in unquoted_logical or re.search(r"\|\|\s*:", unquoted_logical) is not None
        wrapper_consumes_status = bool(
            direct_command and direct_command[0] in status_consuming_wrappers
        )
        checked = (
            symbol == "<module>"
            and not function_declaration_seen
            and not wrapper_consumes_status
            and _shell_failure_propagates(
                logical_line,
                errexit,
                pipefail,
            )
            and not ignored
        )
        if (mutation or gate) and not checked:
            unsafe_failure = True
        if mutation and not checked:
            unchecked_mutations.append((number, symbol, logical_line))
            if (
                any(_git_subcommand(command) in _PUBLICATION_GIT for command in commands)
                or re.search(r"\bgit\s+(commit|push|update-ref)\b", classification_line)
            ):
                unchecked_publications.append((number, symbol, logical_line))
        if _shell_broad_mutation(classification_line):
            findings.append(_finding("AUTO003", path, number, symbol, lines))
        if _shell_force_protected(classification_line):
            findings.append(_finding("AUTO004", path, number, symbol, lines))
        if _shell_hardcoded_integration(classification_line):
            findings.append(_finding("AUTO005", path, number, symbol, lines, severity="critical"))
        if (
            any(os.path.basename(command[0]).lower() in _SHELL_INTERPRETERS for command in commands)
            or re.search(r"(^|[;&|]\s*)(bash|sh|zsh|dash)\s+[^-]", logical_stripped)
        ):
            severity = "critical" if "TODO" in logical_line or "run.sh" in logical_line else "high"
            findings.append(_finding("AUTO006", path, number, symbol, lines, severity=severity))

    for symbol in sorted({item[1] for item in unchecked_mutations}):
        scoped = [item for item in unchecked_mutations if item[1] == symbol]
        findings.append(_shell_aggregate_finding("AUTO001", path, scoped, lines))
    for symbol in sorted({item[1] for item in unchecked_publications}):
        scoped = [item for item in unchecked_publications if item[1] == symbol]
        findings.append(_shell_aggregate_finding("AUTO009", path, scoped, lines))

    if gates and pre_gate_mutations:
        for symbol in sorted({item[1] for item in pre_gate_mutations}):
            symbol_gates = [line for line, gate_symbol in gates if gate_symbol == symbol]
            if not symbol_gates:
                continue
            before = [item for item in pre_gate_mutations if item[1] == symbol and item[0] < max(symbol_gates)]
            if before:
                number, found_symbol, _line = min(before, key=lambda item: item[0])
                findings.append(_finding("AUTO008", path, number, found_symbol, lines))

    if unsafe_failure:
        for number, line in enumerate(lines, 1):
            symbol = _shell_symbol(lines, number)
            if re.match(r"^\s*(?:echo|printf)\b", line) and _PASS_RE.search(line):
                findings.append(_finding("AUTO002", path, number, symbol, lines))

    for symbol in sorted({item[1] for item in mutations}):
        scoped = [item for item in mutations if item[1] == symbol]
        missing = [
            item for item in scoped
            if not _shell_has_durable_state(lines, symbol, item[0], item[2])
        ]
        if not missing:
            continue
        mutation_text = "\n".join(item[2] for item in scoped)
        critical = "TODO" in mutation_text or "DONE" in mutation_text
        critical = critical or any(
            _git_subcommand(command) in _PUBLICATION_GIT
            for item in scoped
            for command in _shell_simple_commands(_shell_command_words(item[2]))
        )
        findings.append(
            _shell_aggregate_finding(
                "AUTO010",
                path,
                missing,
                lines,
                severity="critical" if critical else "high",
            )
        )

    return _dedupe(findings)


def detect_language(path: str, text: str, explicit: Optional[str] = None) -> Optional[str]:
    if explicit:
        return explicit
    lowered_path = path.lower()
    if lowered_path.endswith(".py.fixture"):
        return "python"
    if lowered_path.endswith((".sh.fixture", ".bash.fixture", ".zsh.fixture")):
        return "shell"
    suffix = Path(path).suffix.lower()
    if suffix == ".py":
        return "python"
    if suffix in (".sh", ".bash", ".zsh"):
        return "shell"
    first = text.splitlines()[0] if text.splitlines() else ""
    if first.startswith("#!") and "python" in first:
        return "python"
    if first.startswith("#!") and any(shell in first for shell in ("bash", "/sh", "zsh")):
        return "shell"
    return None


def scan_text(path: str, text: str, language: Optional[str] = None) -> List[Finding]:
    selected = detect_language(path, text, language)
    if selected == "python":
        return scan_python(path, text)
    if selected == "shell":
        return scan_shell(path, text)
    return []


def _excluded_live_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")
    if not parts:
        return True
    if parts[0] in ("logs", "output", "node_modules", ".git"):
        return True
    if any(part in ("logs", "output", "node_modules", "fixtures", "tests", "__pycache__") for part in parts):
        return True
    return Path(normalized).name.startswith("test_")


def tracked_automation_paths(root: Path) -> Tuple[List[str], List[Dict[str, object]]]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=str(root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        return [], [{"code": "POLICY_GIT", "message": "cannot execute git ls-files: %s" % exc}]
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        return [], [{"code": "POLICY_GIT", "message": "git ls-files failed: %s" % detail}]
    paths = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        try:
            path = raw.decode("utf-8")
        except UnicodeDecodeError:
            return [], [{"code": "POLICY_PATH", "message": "tracked path is not UTF-8"}]
        if _excluded_live_path(path):
            continue
        if Path(path).suffix.lower() in (".py", ".sh", ".bash", ".zsh"):
            paths.append(path)
    return sorted(paths), []


def _read_index_source(
    root: Path,
    path: str,
    required: bool = True,
) -> Tuple[Optional[str], Optional[Dict[str, object]]]:
    try:
        result = subprocess.run(
            ["git", "show", ":%s" % path],
            cwd=str(root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        return None, {"code": "POLICY_READ", "message": "%s: cannot read index blob: %s" % (path, exc)}
    if result.returncode != 0:
        if required:
            return None, {"code": "POLICY_READ", "message": "%s is missing from the Git index" % path}
        return None, None
    try:
        return result.stdout.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, {"code": "POLICY_READ", "message": "%s: index source is not UTF-8" % path}


def _read_tracked_sources(root: Path, path: str) -> Tuple[List[str], Optional[Dict[str, object]]]:
    index_text, index_error = _read_index_source(root, path)
    if index_error or index_text is None:
        return [], index_error
    variants = [index_text]
    candidate = root / path
    if candidate.is_symlink():
        return [], {"code": "POLICY_READ", "message": "%s: automation source may not be a symlink" % path}
    if candidate.is_file():
        try:
            worktree_text = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            return [], {"code": "POLICY_READ", "message": "%s: %s" % (path, exc)}
        if worktree_text != index_text:
            variants.append(worktree_text)
    return variants, None


def _task_states(root: Path) -> Dict[str, Set[str]]:
    states = {}
    pattern = re.compile(r"^- \[([ pxwu])\] \*\*([0-9]{4}-[0-9]{2}(?:\.[0-9]{2})?)\*\*", re.MULTILINE)
    for name in ("TODO.md", "DONE.md"):
        texts = []
        path = root / name
        if path.is_file():
            try:
                texts.append(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError):
                pass
        index_text, _index_error = _read_index_source(root, name, required=False)
        if index_text is not None and index_text not in texts:
            texts.append(index_text)
        for text in texts:
            for state, task_id in pattern.findall(text):
                states.setdefault(task_id, set()).add(state)
    return states


def _parse_policy_text(text: str, label: str) -> Tuple[Optional[Dict[str, object]], List[Dict[str, object]]]:
    try:
        value = json.loads(text)
    except ValueError as exc:
        return None, [{"code": "POLICY_LOAD", "message": "cannot load %s: %s" % (label, exc)}]
    if not isinstance(value, dict) or value.get("schema_version") != POLICY_SCHEMA_VERSION:
        return None, [{"code": "POLICY_SCHEMA", "message": "unsupported automation-safety policy schema"}]
    if not isinstance(value.get("dispositions"), list):
        return None, [{"code": "POLICY_SCHEMA", "message": "policy dispositions must be an array"}]
    return value, []


def load_policy(path: Path) -> Tuple[Optional[Dict[str, object]], List[Dict[str, object]]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return None, [{"code": "POLICY_LOAD", "message": "cannot load %s: %s" % (path, exc)}]
    return _parse_policy_text(text, str(path))


def _head_tracks_path(root: Path, path: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "cat-file", "-e", "HEAD:%s" % path],
            cwd=str(root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def _load_repository_policy(
    root: Path,
    path: Path,
) -> Tuple[Optional[Dict[str, object]], List[Dict[str, object]]]:
    try:
        relative = path.resolve().relative_to(root).as_posix()
    except ValueError:
        return load_policy(path)
    worktree_text = None
    if path.is_file() and not path.is_symlink():
        try:
            worktree_text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            return None, [{"code": "POLICY_LOAD", "message": "cannot load %s: %s" % (path, exc)}]
    index_text, index_error = _read_index_source(root, relative, required=False)
    errors = [index_error] if index_error else []
    if worktree_text is not None and index_text is not None and worktree_text != index_text:
        errors.append({
            "code": "POLICY_DIVERGENCE",
            "message": "%s differs between the Git index and worktree" % relative,
        })
    if worktree_text is not None and index_text is None and _head_tracks_path(root, relative):
        errors.append({
            "code": "POLICY_DIVERGENCE",
            "message": "%s is deleted from the Git index but restored in the worktree" % relative,
        })
    selected = worktree_text if worktree_text is not None else index_text
    if selected is None:
        errors.append({"code": "POLICY_LOAD", "message": "cannot load %s" % relative})
        return None, errors
    policy, parse_errors = _parse_policy_text(selected, relative)
    errors.extend(parse_errors)
    return policy, errors


def _commit_reachable(root: Path, sha: str, cache: Dict[str, bool]) -> bool:
    """Return True iff `sha` names a commit object reachable in `root`'s object database.

    Memoized per validation run (`cache`) since the same proof commit is
    typically cited by many `proven-closed` entries. Uses `git cat-file -e`
    with the `^{commit}` peel operator so a tag or blob with a matching
    hex prefix cannot be mistaken for a commit; DEC-0038-007 CON-03 requires
    this to remain a real mechanical check, never a rubber stamp.
    """
    if sha in cache:
        return cache[sha]
    try:
        result = subprocess.run(
            ["git", "cat-file", "-e", "%s^{commit}" % sha],
            cwd=str(root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        cache[sha] = False
        return False
    reachable = result.returncode == 0
    cache[sha] = reachable
    return reachable


def _validate_dispositions(
    root: Path,
    policy: Dict[str, object],
    findings: Sequence[Finding],
    today: Optional[_datetime.date] = None,
) -> Tuple[Dict[Tuple[str, str, int, str, str], Dict[str, object]], List[Dict[str, object]]]:
    errors: List[Dict[str, object]] = []
    valid: Dict[Tuple[str, str, int, str, str], Dict[str, object]] = {}
    states = _task_states(root)
    today = today or _datetime.date.today()
    finding_keys = {(item.path, item.rule, item.line, item.symbol, item.evidence_sha256) for item in findings}
    reachability_cache: Dict[str, bool] = {}

    raw_dispositions = policy.get("dispositions")
    if not isinstance(raw_dispositions, list):
        return {}, [{"code": "POLICY_SCHEMA", "message": "policy dispositions must be an array"}]
    for index, disposition in enumerate(raw_dispositions):
        prefix = "disposition[%d]" % index
        if not isinstance(disposition, dict):
            errors.append({"code": "POLICY_ENTRY", "message": "%s must be an object" % prefix})
            continue
        path = disposition.get("path")
        rule = disposition.get("rule")
        line = disposition.get("line")
        symbol = disposition.get("symbol")
        digest = disposition.get("evidence_sha256")
        owner = disposition.get("owner_task")
        rationale = disposition.get("rationale")
        invariant = disposition.get("expected_safe_invariant")
        kind = disposition.get("kind")
        expiry_task = disposition.get("expires_after_task")
        expires_on = disposition.get("expires_on")
        owner_ref = disposition.get("owner_ref")
        proof_summary = disposition.get("proof_summary")
        proven_closed = kind == "proven-closed"

        entry_errors = []
        if not isinstance(path, str) or path.startswith("/") or ".." in Path(path).parts or _WILDCARD_RE.search(path):
            entry_errors.append("path must be one exact repository-relative path without glob syntax")
        if rule not in RULES or rule == "AUTO000":
            entry_errors.append("rule must name one suppressible AUTO001-AUTO010 rule")
        if not isinstance(line, int) or line < 1:
            entry_errors.append("line must be a positive exact source line")
        if not isinstance(symbol, str) or not symbol:
            entry_errors.append("symbol must be the exact non-empty finding symbol")
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            entry_errors.append("evidence_sha256 must be a lowercase SHA-256")
        if kind not in _DISPOSITION_KINDS:
            entry_errors.append("kind must be blocking-task, narrow-suppression, or proven-closed")
        if not isinstance(owner, str) or _TASK_ID_RE.fullmatch(owner) is None:
            entry_errors.append("owner_task must be an exact Task ID")
        if not isinstance(rationale, str) or len(rationale.strip()) < 20:
            entry_errors.append("rationale must explain the narrow disposition")
        if not isinstance(invariant, str) or len(invariant.strip()) < 20:
            entry_errors.append("expected_safe_invariant must be independently testable")
        if not proven_closed and expiry_task is None and expires_on is None:
            entry_errors.append("expires_after_task and/or expires_on is required")
        if expiry_task is not None and (not isinstance(expiry_task, str) or _TASK_ID_RE.fullmatch(expiry_task) is None):
            entry_errors.append("expires_after_task must be an exact Task ID")
        if isinstance(owner, str) and owner not in states:
            entry_errors.append("owner_task %s is absent from TODO.md/DONE.md" % owner)
        elif isinstance(owner, str) and not proven_closed and states.get(owner, set()) & {"x", "w"}:
            entry_errors.append("owner_task %s is terminal; disposition expired" % owner)
        if isinstance(expiry_task, str):
            if expiry_task not in states:
                entry_errors.append("expires_after_task %s is absent from TODO.md/DONE.md" % expiry_task)
            elif not proven_closed and states.get(expiry_task, set()) & {"x", "w"}:
                entry_errors.append("expires_after_task %s is terminal; disposition expired" % expiry_task)
        # DEC-0038-007 CON-03: `proven-closed` requires immutable proof anchoring
        # (owner_ref + evidence_sha256 + proof_summary). evidence_sha256 is
        # already required/validated above for every kind and already drives
        # POLICY_STALE via the finding_keys membership check below -- that
        # digest-mismatch path is untouched and unweakened by this kind.
        if proven_closed:
            if not isinstance(owner_ref, str) or _COMMIT_SHA_RE.fullmatch(owner_ref) is None:
                entry_errors.append("owner_ref must be a full 40-character lowercase commit SHA")
            elif not _commit_reachable(root, owner_ref, reachability_cache):
                entry_errors.append("owner_ref %s is not a reachable commit" % owner_ref)
            if not isinstance(proof_summary, str) or len(proof_summary.strip()) < 30:
                entry_errors.append("proof_summary must be a substantive, independently reviewable explanation")
        elif owner_ref is not None or proof_summary is not None:
            entry_errors.append("owner_ref/proof_summary are only permitted for kind proven-closed")
        if expires_on is not None:
            if not isinstance(expires_on, str):
                entry_errors.append("expires_on must be an ISO-8601 date")
            else:
                try:
                    expiry_date = _datetime.date.fromisoformat(expires_on)
                    if expiry_date < today:
                        entry_errors.append("expires_on %s has passed" % expires_on)
                except ValueError:
                    entry_errors.append("expires_on must be an ISO-8601 date")

        if entry_errors:
            errors.extend({"code": "POLICY_ENTRY", "message": "%s: %s" % (prefix, message)} for message in entry_errors)
            continue
        assert isinstance(path, str)
        assert isinstance(rule, str)
        assert isinstance(line, int)
        assert isinstance(symbol, str)
        assert isinstance(digest, str)
        key = (path, rule, line, symbol, digest)
        if key in valid:
            errors.append({"code": "POLICY_DUPLICATE", "message": "%s duplicates an earlier exact disposition" % prefix})
            continue
        if key not in finding_keys:
            errors.append({"code": "POLICY_STALE", "message": "%s no longer matches an exact finding" % prefix})
            continue
        valid[key] = disposition
    return valid, errors


def _assemble_report(
    root: Path,
    findings: Sequence[Finding],
    scanned_paths: Sequence[str],
    policy: Optional[Dict[str, object]],
    errors: Sequence[Dict[str, object]],
    today: Optional[_datetime.date] = None,
) -> Dict[str, object]:
    policy_errors = list(errors)
    matches = {}
    if policy is not None:
        matches, disposition_errors = _validate_dispositions(root, policy, findings, today=today)
        policy_errors.extend(disposition_errors)

    rendered = []
    unresolved_critical = 0
    disposed_critical = 0
    advisory = 0
    for finding in findings:
        item = finding.to_dict()
        key = (finding.path, finding.rule, finding.line, finding.symbol, finding.evidence_sha256)
        disposition = matches.get(key)
        if disposition is not None:
            item["status"] = "disposed"
            item["disposition"] = {
                key: disposition.get(key)
                for key in (
                    "kind", "rationale", "owner_task", "expires_after_task", "expires_on",
                    "expected_safe_invariant",
                )
                if disposition.get(key) is not None
            }
            if finding.severity == "critical":
                disposed_critical += 1
        elif finding.severity == "critical":
            item["status"] = "unresolved"
            unresolved_critical += 1
        else:
            item["status"] = "advisory"
            advisory += 1
        rendered.append(item)

    failed = bool(policy_errors or unresolved_critical)
    return {
        "schema_version": SCHEMA_VERSION,
        "verdict": "FAIL" if failed else "PASS",
        "root": ".",
        "scanned_files": len(scanned_paths),
        "scanned_paths": list(scanned_paths),
        "counts": {
            "findings": len(rendered),
            "unresolved_critical": unresolved_critical,
            "disposed_critical": disposed_critical,
            "advisory": advisory,
            "policy_errors": len(policy_errors),
        },
        "findings": rendered,
        "policy_errors": policy_errors,
    }


def scan_repository(
    root: Path,
    policy_path: Optional[Path] = None,
    today: Optional[_datetime.date] = None,
) -> Dict[str, object]:
    root = root.resolve()
    paths, errors = tracked_automation_paths(root)
    findings = []
    scanned = []
    for path in paths:
        texts, read_error = _read_tracked_sources(root, path)
        if read_error:
            errors.append(read_error)
            continue
        scanned.append(path)
        for text in texts:
            findings.extend(scan_text(path, text))
    selected_policy = policy_path or (root / DEFAULT_POLICY)
    policy, load_errors = _load_repository_policy(root, selected_policy)
    errors.extend(load_errors)
    return _assemble_report(root, _dedupe(findings), scanned, policy, errors, today=today)


def scan_explicit_paths(
    root: Path,
    paths: Sequence[str],
    language: Optional[str] = None,
    policy_path: Optional[Path] = None,
    today: Optional[_datetime.date] = None,
) -> Dict[str, object]:
    root = root.resolve()
    findings = []
    scanned = []
    errors = []
    for path in paths:
        candidate = (root / path).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            errors.append({"code": "POLICY_PATH", "message": "%s escapes repository root" % path})
            continue
        try:
            text = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append({"code": "POLICY_READ", "message": "%s: %s" % (path, exc)})
            continue
        normalized = candidate.relative_to(root).as_posix()
        selected_language = detect_language(normalized, text, explicit=language)
        if selected_language is None:
            errors.append({
                "code": "POLICY_LANGUAGE",
                "message": "%s has no recognized language; pass --language" % normalized,
            })
            continue
        scanned.append(normalized)
        findings.extend(scan_text(normalized, text, language=selected_language))
    policy = None
    if policy_path is not None:
        policy, load_errors = load_policy(policy_path)
        errors.extend(load_errors)
    return _assemble_report(root, _dedupe(findings), scanned, policy, errors, today=today)


def _print_human(report: Dict[str, Any]) -> None:
    counts = report["counts"]
    assert isinstance(counts, dict)
    policy_errors = report["policy_errors"]
    findings = report["findings"]
    assert isinstance(policy_errors, list)
    assert isinstance(findings, list)
    print(
        "automation-safety %s: scanned=%d findings=%d unresolved-critical=%d disposed-critical=%d advisory=%d policy-errors=%d"
        % (
            report["verdict"],
            report["scanned_files"],
            counts["findings"],
            counts["unresolved_critical"],
            counts["disposed_critical"],
            counts["advisory"],
            counts["policy_errors"],
        )
    )
    for error in policy_errors:
        if not isinstance(error, dict):
            continue
        print("POLICY ERROR %s: %s" % (error.get("code", "POLICY"), error.get("message", "")))
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        if finding.get("status") == "disposed":
            continue
        print(
            "%s %s %s:%s %s: %s"
            % (
                finding["rule"], finding["severity"], finding["path"], finding["line"],
                finding["symbol"], finding["evidence"],
            )
        )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--policy", type=Path, help="policy path (default for live scans: %s)" % DEFAULT_POLICY)
    parser.add_argument("--path", action="append", default=[], help="explicit repository-relative path; repeatable")
    parser.add_argument("--fixture", action="append", default=[], help="explicit fixture path; repeatable")
    parser.add_argument("--language", choices=("python", "shell"), help="language for extensionless explicit paths")
    parser.add_argument("--json", action="store_true", help="emit stable JSON")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    explicit = list(args.path) + list(args.fixture)
    if explicit:
        policy_path = args.policy.resolve() if args.policy else None
        report = scan_explicit_paths(root, explicit, language=args.language, policy_path=policy_path)
    else:
        policy_path = args.policy.resolve() if args.policy else root / DEFAULT_POLICY
        report = scan_repository(root, policy_path=policy_path)

    if args.json:
        json.dump(report, sys.stdout, ensure_ascii=False, sort_keys=True, indent=2)
        sys.stdout.write("\n")
    else:
        _print_human(report)
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
