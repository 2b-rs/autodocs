# Process improvement studies

This directory contains informative analysis inputs for reserved Feature `0039 — Process improvement`.

These documents are **not** approved processes, implementation authorization, Automotive SPICE capability assessments, tool qualification decisions, or permission to claim a reserved Task. A current user must explicitly select a Feature `0039` Task and designate its owning session as privileged before work begins.

## Studies

### Feature definition and breakdown

- File: [`feature-definition-process-study.docx`](feature-definition-process-study.docx)
- SHA-256: `64d92db9ef693030696e62b158e4aa213f0c31154fb97b21e71eab8743d5bbe0`
- Extracted text size at creation: approximately 8,300 words
- Future owner: reserved Task `0039-01`
- Scope: Feature intake, contract, requirements/architecture impact, acceptance, decomposition, prerequisites, scopes, executability, risk, traceability, review/baseline/change control, closure, Automotive SPICE relationships, metrics, templates, and adoption.

### Reusable tool creation and continuous improvement

- File: [`tool-creation-improvement-process-study.docx`](tool-creation-improvement-process-study.docx)
- SHA-256: `3637ab710074ab7534f96d753e115e0dc817285cb0c8d4aee54ee88babe872fb`
- Extracted text size at creation: approximately 6,100 words
- Future owner: reserved Task `0039-02`
- Scope: reuse-before-create, candidate isolation, tool/action contracts, typed execution, qualification, safety, evidence, ownership, duplicate control, scheduling, deployment, metrics, Automotive SPICE relationships, third-party tools, emergency exceptions, and retirement.

The two topics intentionally remain distinct: the Feature process defines authorized outcomes and executable work; the tool process governs how recurring mechanics become qualified reusable capabilities after the outcome is known.

## Imported pilot suggestion

Reserved Task `0039-03` carries the previously unassigned Feature `0036` page-i18n completeness-validator suggestion into the authoritative backlog as a possible first tool-process pilot. Existing runner-transaction and approval-readiness suggestions already have authoritative coverage in Feature `0038` and are not duplicated.

## Creation and validation

The studies were authored as task-scoped HTML sources under ignored `output/logs/0039-studies/20260817-f3c9a7d2/`, converted with macOS `/usr/bin/textutil`, and validated by:

- source HTML parsing, unique IDs, internal-link targets, and no script/external-resource checks;
- `unzip -t` integrity checks;
- parsing every DOCX XML and relationship part;
- extraction back to UTF-8 text with `textutil`;
- required-section, disclaimer, topic-boundary, emergency-path, pilot, ASPICE-caution, and no-leaked-markup canaries.

The HTML conversion sources are generation evidence, not tracked authority. The DOCX files and this index are the retained study package.
