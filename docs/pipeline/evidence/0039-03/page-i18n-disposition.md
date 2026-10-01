# Page-i18n validator disposition

**Disposition:** Productized as the read-only candidate `_src/tools/validate_page_i18n.py`, owned by Feature `0039` Task `0039-03`. It is cataloged but not registered for production execution or integrated into `_src/validate.py`.

## Recovery and authority

The retained, tracked evidence is `logs/i18n-process-0036-06/20260816-9c4e7b2a/completeness.json` at substantive commit `c8788f6865feeef9cfbbece41c1d802d9cee9b8c`. It records the prototype contract: `i18n_complete` opt-in, 71 translation hits per locale, six stable anchors, two ARIA labels, and 18 inline-SVG labels. The suggested ignored `validate_process_i18n.py` is not a tracked authority source and was not promoted as-is. The reusable implementation reconstructs only the evidenced contract.

## Overlap assessment

`_src/i18n_extract.py` creates source registers and `lib_i18n.py` translates registered page material, including ARIA and inline-SVG labels. `_src/validate.py` checks generated-tree freshness and structural locale parity. Neither independently verifies an opted-in page's source-to-register coverage, rendered fallback/leak markers, or the combined anchor/ARIA/SVG page contract. Feature `0038` validation profiles consume declared validation results; they do not provide this i18n semantic check. The validator is therefore complementary, not a duplicate semantic core.

## Candidate contract and retirement

`page-i18n-families@v1` is an explicit opt-in manifest. Each active family identifies its source page model, source register root, rendered path, locales, protected identifiers, and leak/fallback markers. The validator is deterministic, read-only, local-only, and emits bounded `page-i18n-validation@v1` JSON (at most 100 findings). A family marked `retired` is retained in the manifest but deliberately not checked; this preserves history without granting execution or silently deleting the contract.

## Validation

Focused fixtures cover positive output, missing extraction, fallback/leak, protected identifier, anchor mismatch, ARIA coverage, inline-SVG coverage, stale/missing rendered output, and retirement. The live process-documentation family passed with zero findings.
