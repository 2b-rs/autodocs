// 0008-09: renders a generated HTML page with its real page-level JS
// (review.js, todo-graph-embed.js, etc.) through headless WebKit, waits for
// client-side DOM mutations to settle, then dumps the resulting body text.
// This is the client-side counterpart to validate.py's
// check_no_hardcoded_german(), which only ever sees the pre-JS static HTML
// and therefore cannot catch bugs like 0008-08 (review.js unconditionally
// overwriting #page-review-title with a hardcoded German string on every
// language page after load).
//
// Usage: node check_client_rendered_german.cjs <absolute-path-to-html-file>
// Prints a single JSON object to stdout: { url, bodyText, pageErrors }.
// Non-zero exit code on navigation/launch failure; callers should treat a
// non-empty pageErrors array as a soft warning, not a hard failure, since
// it may reflect unrelated console noise rather than the check's target.

const { webkit } = require('playwright');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

(async () => {
  const target = process.argv[2];
  if (!target) {
    console.error('usage: node check_client_rendered_german.cjs <html-file>');
    process.exit(2);
  }

  const browser = await webkit.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    const pageErrors = [];
    page.on('pageerror', (error) => pageErrors.push(String(error && error.stack || error)));

    await page.goto(pathToFileURL(path.resolve(target)).href, { waitUntil: 'load' });
    // review.js (and similar chrome scripts) run their DOM rewrites
    // synchronously on DOMContentLoaded/load; a short settle window covers
    // any microtask-deferred follow-up without materially slowing the check.
    await page.waitForTimeout(500);

    const bodyText = await page.evaluate(() => document.body.innerText);
    console.log(JSON.stringify({ url: target, bodyText, pageErrors }));
  } finally {
    await browser.close();
  }
})().catch((err) => {
  console.error(String(err && err.stack || err));
  process.exit(1);
});
