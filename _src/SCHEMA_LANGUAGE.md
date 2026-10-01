# Schema Language

This document defines the canonical schema vocabulary for Spec-DB records and
related process artifacts. The goal is to use **one language for schema keys,
state values, and machine-facing field names** while still permitting German and
English source content in rendered text.

## Rule

Machine-facing schema language is **English only**.

This applies to:

- JSON keys
- enum/state values
- internal field labels in process artifacts
- validator and migration rule names
- report bucket names produced by tools

It does **not** force English prose in authored documentation or rendered page
content. Human-facing explanatory text may remain German or bilingual.

## Why

The current repository mixes English and German in machine-facing terms, for
example:

- English PDF field labels such as `Kind`, `Header file`, `Scope`, `Symbol`,
  `Underlying type` in `spec_scrape.py` [cite:63]
- German DB property labels mapped back to English, such as `Header-Datei`,
  `Geltungsbereich`, `Basistyp`, `Rückgabewert`, `Ausnahmesicherheit`,
  `Thread-Sicherheit` [cite:63]
- German metadata keys in `ns`, such as `quelle`, `generiert`, `abweichung`,
  `modul` documented in `KONVENTIONEN.md` and present in records [cite:63][cite:62]

This mixture makes migrations, traceability, validation, and AI-assisted
processing harder than necessary.

## Canonical vocabulary

### Record envelope

| Current | Canonical |
|---|---|
| `id` | `id` |
| `attrs` | `attrs` |
| `lead` | `lead` |
| `blocks` | `blocks` |
| `ns` | `namespace_meta` |

### Namespace metadata

| Current | Canonical | Meaning |
|---|---|---|
| `modul` | `module` | owning AUTOSAR module slug |
| `quelle` | `source` | derivation source for namespace assignment |
| `generiert` | `generated` | generated rather than directly sourced |
| `abweichung` | `deviation` | catalogued deviation kind |
| `namespace` | `namespace` | true namespace |
| `enclosing` | `enclosing` | fully qualified enclosing type |

### Property labels

Canonical machine labels remain the English AUTOSAR/PDF-oriented names already
used by `spec_scrape.py`: `Kind`, `Header file`, `Forwarding header file`,
`Scope`, `Symbol`, `Underlying type`, `Syntax`, `Return value`, `Exception
Safety`, `Thread Safety`, `Description`, `Notes`, `Type`, `Default value`,
`Errors`. [cite:63]

German HTML table headings remain supported as legacy input aliases only.

### Process and status fields

Use English-only keys and values:

- `status.state`
- `status.reason`
- `history[]`
- `campaign`
- `trace`
- `evidence`
- `counter_evidence`
- `decision`
- `confidence`

State values should stay slash-separated but English, e.g.:

- `invalid/obsolete`
- `valid/auto-approved`
- `valid/corrected`
- `invalid/to-be-confirmed`
- `valid/ai-decided`
- `valid/curator-decided`
- `hypothesized/unconfirmed`

## Migration policy

Schema language must be unified in two stages.

### Stage 1 — Canonicalize new structures immediately

All newly introduced structures for traceability, campaign handling, status,
AI decisions, and evidence use canonical English names only.

### Stage 2 — Migrate legacy record metadata

The current `ns` object is legacy language. It should be migrated to
`namespace_meta` with English subkeys.

Target shape:

```json
"namespace_meta": {
  "namespace": "std",
  "module": "core",
  "source": "scope",
  "generated": false,
  "deviation": "std-specialization",
  "enclosing": "std::hash"
}
```

During migration, retain read compatibility for legacy names only in tooling,
not in newly written records.

## Compatibility rules

Until the migration is complete:

1. Readers must accept both legacy and canonical forms.
2. Writers must emit canonical forms only.
3. Reports must label buckets in English only.
4. New migration rules must use English identifiers.

## Deviation vocabulary

Deviation kinds should also be normalized to English. Recommended mapping:

| Current | Canonical |
|---|---|
| `std-spezialisierung` | `std-specialization` |
| `modulfremder-namensraum` | `foreign-module-namespace` |
| `dienst-namensraum` | `service-namespace` |
| `modellgenerierter-namensraum` | `model-generated-namespace` |

## Implementation order

1. Adopt this language policy for all new traceability/status/evidence schema.
2. Update validators and generators to read canonical names first.
3. Add compatibility reads for legacy `ns` keys.
4. Migrate stored records from `ns` to `namespace_meta`.
5. Remove legacy writes.
6. Remove legacy reads only after the repository is fully migrated.
