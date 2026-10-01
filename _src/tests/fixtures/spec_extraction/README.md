# Extraction benchmark

Canonical regression oracle: `_src/tests/fixtures/spec_extraction/benchmark.json`.

This directory also keeps the approved freeze source
`benchmark-draft.json`. The draft is provenance, not the gate. Regeneration
must not overwrite the frozen oracle.

## Frozen oracle

- **Path:** `benchmark.json`
- **Status:** `frozen`
- **Cardinality:** 199 records, 199 unique IDs, 18 source documents
- **Excluded ID:** `RS_SAF_21101` (citation-only mention; Feature `0034-04`)
- **Source draft SHA-256:** recorded in `source_draft.sha256`
- **Record manifest:** `record_manifest[<id>]` is the SHA-256 of the oracle
  payload for that ID (`id`, `document`, `categories`, `backend_presence`,
  and `expected.{heading,fields,pages,complete_start,complete_end}`)
- **Content digest:** `content_sha256` is the SHA-256 of the sorted
  `[id, digest]` pairs from that manifest

The default CLI of `_src/tools/spec_extraction_benchmark.py` is **check the
frozen oracle**. A campaign argument still builds a review draft, but only
into `benchmark-draft.json` / `README.md` under `--output`, and the builder
refuses to write `benchmark.json`.

```bash
python3 _src/tools/spec_extraction_benchmark.py
python3 _src/tools/spec_extraction_benchmark.py --compare path/to/candidate.json
python3 -m unittest _src/tests/test_spec_extraction_benchmark.py
```

A clean compare of the frozen records against themselves reports no
heading/field/page/completeness drift. Changed, missing, duplicate, extra, or
unresolved candidate entries fail the compare.

## Known limits

Freezing pins the independently selected 199-record candidate. It does not
finish outstanding source-backed truthing: 179 frozen entries still have
`review.status = needs_review` and `expected.complete_start = null`. Those
bytes are now immutable oracle content; later truthing is a new reviewed
revision, not a silent rebuild.

Issue `0007-04` AC-002 still names 200 entries. The approved draft after
`0034-04` is 199 records. This freeze follows the 199-record draft rather
than restoring the excluded citation.

## Adversarial completion evidence (DEC-0038-004)

- **Baselines:** pre-change `3170be460` on `task-0007-04`; candidate is this
  freeze.
- **Falsification (red on baseline, green on candidate):**
  `python3 _src/tools/spec_extraction_benchmark.py` required `campaign` and
  `--output` and exited 2 with no oracle check; `benchmark.json` was absent.
  After the freeze the same command checks the frozen artifact and exits 0.
- **Adjacent cases:** missing ID fails; duplicate ID fails; heading change
  fails; unresolved `expected.fields` fails; extra unknown ID fails; review-note
  edits are not semantic drift.
- **Set/sequence property:** exhaustive bijection over all 199 frozen IDs
  between `records` and `record_manifest`, plus a per-record digest-break on
  page mutation (`test_manifest_bijection_property_over_all_frozen_records`,
  `test_expected_field_mutation_breaks_every_record_digest`; 199 executed
  cases each).
