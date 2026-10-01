# Record Status & Curation History Rendering (Feature 0006-11)

Status: defined and implemented 2026-08-14 for **0006-11**.

## Why

Prior to this feature, specification records carried rich `status` metadata and `history[]` audit logs in their JSON definitions under `_src/spec/records/`, but these were not exposed on published record pages in HTML. Users and curators reviewing specification items had to inspect source files directly or cross-reference separate reports to see whether a record was auto-approved, corrected, curator-decided, or obsolete.

## Schema & DOM Representation

When `_src/lib_docmodel.py` renders `rec` blocks (`<article class="rec" id="...">`), it inspects the record's `status` and `history[]` fields:

```html
<details class="rec-history-panel">
  <summary>
    <span class="rec-status-badge rec-status-valid">Status: valid/auto-approved</span>
    <span class="rec-version-badge" title="Active requirement version">Version: <code>3391383e</code></span>
    <span class="rec-history-summary-text">History & Versions (2 transitions)</span>
  </summary>
  <div class="rec-history-body">
    <dl class="rec-status-details">
      <dt>Current State</dt><dd><code>valid/auto-approved</code></dd>
      <dt>Reason</dt><dd>unchanged</dd>
      <dt>Campaign</dt><dd><code>2026-08-sws-log-pilot-after-tool-improvement</code></dd>
      <dt>Active Version</dt><dd><code>AUTOSAR/AP/record/SWS_LOG_00046@rel:R25-11#3391383e</code></dd>
    </dl>
    <div class="rec-version-nav" data-canonical-id="AUTOSAR/AP/record/SWS_LOG_00046">
      <div class="rec-version-nav-bar">
        <span class="rec-version-nav-title">Point-in-Time History:</span>
        <div class="rec-version-controls">
          <label class="rec-asof-label">Release:
            <select class="rec-asof-select" data-asof-select>
              <option value="R25-11" selected>R25-11 (Current / Active)</option>
              <option value="R20-11">R20-11</option>
            </select>
          </label>
          <button type="button" class="rec-asof-btn">View Snapshot</button>
        </div>
      </div>
      <div class="rec-asof-display" hidden>
        ...
      </div>
    </div>
    <table class="rec-history-table">
      <thead>
        <tr><th>Date</th><th>Actor</th><th>Transition</th><th>Reason / Rationale</th><th>Campaign</th></tr>
      </thead>
      <tbody>
        ...
      </tbody>
    </table>
    <p class="rec-curation-link"><a href="../curation-report.html#SWS_LOG_00046">View in Curation Report &rarr;</a></p>
  </div>
</details>
```

## Lifecycle States Supported

- `valid/auto-approved`, `valid/corrected`, `valid/curator-decided`, `valid/ai-decided`, `valid/unmigrated`: highlighted with green valid badge (`rec-status-valid`).
- `invalid/obsolete`, `rejected`: highlighted with red badge (`rec-status-invalid`).
- `invalid/to-be-confirmed`, `invalid/hypothesized`, `proposed`, `pending`: highlighted with yellow badge (`rec-status-proposed`).
- Other states: neutral badge (`rec-status-neutral`).
