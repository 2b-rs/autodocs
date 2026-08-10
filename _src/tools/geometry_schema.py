"""Structural schema for pypdf geometry observation artifacts.

Validates the shape of emitted observations without external dependencies so
new geometry fields cannot silently change the artifact contract.
"""
from __future__ import annotations

NUMBER = (int, float)

SPAN_FIELDS = {
    "id": str, "text": str, "current_matrix": (list, tuple), "text_matrix": (list, tuple),
    "position": (list, tuple), "font": (str, type(None)), "font_size": NUMBER,
    "operation_index": int, "inferred_spacing": bool, "inferred_line_break": bool,
}

LINE_FIELDS = {
    "id": str, "baseline_y": NUMBER, "x_range": (list, tuple), "span_ids": (list, tuple),
    "ordered_span_ids": (list, tuple), "tolerance": NUMBER, "operation_index": int,
    "layout": dict, "same_origin_groups": (list, tuple),
    "margin_band": (str, type(None)), "margin_band_support": int,
    "margin_span_roles": dict, "bullet": (dict, type(None)),
    "indent_level": (int, type(None)), "flow": (str, type(None)),
    "flow_gap": (NUMBER + (type(None),)),
    "column_index": (int, type(None)),
    "reading_position": (int, type(None)),
}

PAGE_FIELDS = {
    "page_number": int, "raw_text": str, "backend": str, "spans": (list, tuple),
    "lines": (list, tuple), "warnings": (list, tuple), "columns": (list, tuple),
    "reading_order": (list, tuple),
}

MARGIN_BANDS = {None, "header", "footer"}
FLOWS = {None, "wrap", "block-start"}


def _check(container: dict, fields: dict, label: str, errors: list[str]) -> None:
    for key, expected in fields.items():
        if key not in container:
            errors.append(f"{label}: missing field {key}")
            continue
        if not isinstance(container[key], expected):
            errors.append(f"{label}: field {key} has type {type(container[key]).__name__}")
    for key in container:
        if key not in fields:
            errors.append(f"{label}: unexpected field {key}")


def validate_page(page: dict) -> list[str]:
    errors: list[str] = []
    label = f"page {page.get('page_number', '?')}"
    _check(page, PAGE_FIELDS, label, errors)
    span_ids = set()
    for span in page.get("spans", []):
        _check(span, SPAN_FIELDS, f"{label} span {span.get('id', '?')}", errors)
        if len(span.get("position", [])) != 2:
            errors.append(f"{label} span {span.get('id')}: position must hold two numbers")
        span_ids.add(span.get("id"))
    for line in page.get("lines", []):
        line_label = f"{label} line {line.get('id', '?')}"
        _check(line, LINE_FIELDS, line_label, errors)
        if line.get("margin_band") not in MARGIN_BANDS:
            errors.append(f"{line_label}: invalid margin_band {line.get('margin_band')}")
        if line.get("flow") not in FLOWS:
            errors.append(f"{line_label}: invalid flow {line.get('flow')}")
        if len(line.get("x_range", [])) != 2:
            errors.append(f"{line_label}: x_range must hold two numbers")
        for span_id in line.get("ordered_span_ids", []):
            if span_id not in span_ids:
                errors.append(f"{line_label}: unknown span {span_id}")
        if sorted(line.get("ordered_span_ids", [])) != sorted(line.get("span_ids", [])):
            errors.append(f"{line_label}: ordered_span_ids must permute span_ids")
    return errors


def validate_document(pages: list[dict]) -> list[str]:
    errors: list[str] = []
    for page in pages:
        errors.extend(validate_page(page))
    return errors
