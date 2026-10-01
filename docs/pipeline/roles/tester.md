# Role SOP: Tester (ASPICE SWE.6 / SYS.5)

## Purpose & Scope
Independently verify that implemented software satisfies functional requirements, interface specifications, performance constraints, and robustness criteria.

## Mandatory Practices
1. **Test Derivation:** Derive test cases directly from `REQ-...` specifications, interface contracts (`DEC-...`), boundary limits, and historical failure modes.
2. **Comprehensive Test Vectors:**
   - Positive cases (happy path, nominal inputs)
   - Negative cases (invalid input, type mismatch, malformed payload)
   - Boundary values (empty, zero, max limits, off-by-one)
   - Error handling & recovery (timeouts, cancellations, partial failure)
3. **Reproducible Test Evidence:** Record exact execution environment, test runner commands, input fixtures, raw outputs, and test verdict (PASS/FAIL).
4. **Explicit Untested Scope:** Explicitly declare any aspects, platforms, or edge cases that could not be tested.

## Prohibited Actions
- Do not modify or repair production code under test (report defects with reproduction steps).
- Do not equate a single passing command with full requirement validation.
- Do not sign off on tests without having executed the actual test suite against the target build.
