# Client-Rendered UI Text Validation (Feature 0008-09)

Status: implemented 2026-08-14. Companion to 0008-08 and 0008-04.

## Purpose

Static HTML validation (`check_no_hardcoded_german()`) verifies that generated HTML source files do not contain un-extracted German strings. However, client-side scripts like `review.js` dynamically mutate DOM nodes at runtime (e.g. updating review count notices and badge states).

`check_client_rendered_german()` (and `_src/tools/check_client_rendered_german.cjs`) launches headless WebKit via Playwright, renders representative pages across each non-German language tree, allows client-side DOM mutations to settle, and scans the final `document.body.innerText` against `_german_chrome_strings()`.

## Architecture

- **CJS Renderer (`_src/tools/check_client_rendered_german.cjs`)**:
  - Uses `playwright` (WebKit) to load file URLs.
  - Waits for microtask settlement (`500ms`).
  - Serializes `{ url, bodyText, pageErrors }` to stdout.
- **Python Validator (`validate.py::check_client_rendered_german`)**:
  - Dispatches checks concurrently via `ThreadPoolExecutor`.
  - Scans `bodyText` for banned German chrome patterns (`_german_chrome_strings()`).
  - Emits `client-rendered-german-leak` findings on violations.
- **Unit Testing (`_src/tests/test_client_rendered_german.py`)**:
  - Validates language filtering, subprocess mock execution, pattern detection, and clean passing states.
