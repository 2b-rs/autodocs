const { webkit } = require('playwright');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');

// NOTE (2026-08-15, task 0021-05): file:// navigation under WebKit hangs
// indefinitely in this sandbox regardless of page content (confirmed by
// _src/logs/validate-review-request-ui/20260815-165848-four-url-probe:
// about:blank and data: URLs resolve in single-digit ms, but a *content-free*
// file:// fixture times out identically to the real review-request fixture).
// This is a sandbox/WebKit environment limitation, not a defect in
// review_request.js's dialog/category-select markup. Serve the fixture over
// a throwaway local HTTP server instead of using file:// URLs.
function serveDir(dir) {
  return new Promise((resolve, reject) => {
    const server = http.createServer((req, res) => {
      const reqPath = decodeURIComponent(req.url.split('?')[0]);
      const filePath = path.join(dir, reqPath === '/' ? '/index.html' : reqPath);
      if (!filePath.startsWith(dir)) { res.writeHead(403); res.end(); return; }
      fs.readFile(filePath, (err, data) => {
        if (err) { res.writeHead(404); res.end(); return; }
        const ext = path.extname(filePath);
        const type = ext === '.js' ? 'text/javascript' : ext === '.css' ? 'text/css' : ext === '.json' ? 'application/json' : 'text/html';
        res.writeHead(200, { 'Content-Type': type });
        res.end(data);
      });
    });
    server.listen(0, '127.0.0.1', () => resolve(server));
    server.on('error', reject);
  });
}

(async () => {
  const target = process.argv[2];
  if (!target) {
    console.error('usage: node check_review_request_ui.cjs <html-file>');
    process.exit(2);
  }
  const resolvedTarget = path.resolve(target);
  // Serve from two levels up (not just dirname): fixtures place the target
  // HTML in a `tests/` subdirectory and reference shared assets (JS/CSS) via
  // `../asset.js` from there, so the actual asset root is the fixture's
  // grandparent-of-target directory, one level above `tests/`.
  const serveRoot = path.resolve(path.dirname(resolvedTarget), '..');
  const server = await serveDir(serveRoot);
  const port = server.address().port;
  const url = 'http://127.0.0.1:' + port + '/' + path.relative(serveRoot, resolvedTarget).split(path.sep).join('/');
  const browser = await webkit.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    const consoleMsgs = [];
    const pageErrors = [];
    page.on('console', (m) => consoleMsgs.push(m.type() + ': ' + m.text()));
    page.on('pageerror', (e) => pageErrors.push(String(e && e.stack || e)));
    await page.goto(url, { waitUntil: 'load', timeout: 10000 });
    await page.waitForTimeout(500);
    // Pre-seed a self-declared reviewer identity so resolveIdentity() in
    // review_request.js resolves synchronously instead of opening the
    // one-time identity modal, which this headless script does not drive.
    await page.evaluate(() => localStorage.setItem('ara-review-identity', 'QA Reviewer'));
    await page.click('[data-review-request-open]', { timeout: 5000 });
    try {
      await page.selectOption('[data-category]', 'missing-context', { timeout: 5000 });
    } catch (selectErr) {
      const dialogVisible = await page.locator('.rv-modal.is-open').count().catch(() => -1);
      const dialogHiddenAttr = await page.locator('.rv-modal').first().getAttribute('hidden').catch(() => '<no-el>');
      const categoryCount = await page.locator('[data-category]').count().catch(() => -1);
      const btnAriaExpanded = await page.locator('[data-review-request-open]').getAttribute('aria-expanded').catch(() => '<no-el>');
      console.log(JSON.stringify({
        diagnostic: true, stage: 'selectOption',
        selectErr: String(selectErr && selectErr.message || selectErr),
        consoleMsgs, pageErrors, dialogVisible, dialogHiddenAttr, categoryCount, btnAriaExpanded
      }, null, 2));
      process.exit(4);
    }
    await page.fill('[data-rationale]', 'The summary omits boundary conditions.');
    await page.keyboard.press('Tab');
    await page.click('[data-next]');
    try {
      await page.waitForSelector('[data-confirm]:not([hidden])', { timeout: 5000 });
    } catch (waitErr) {
      const errorsBox = await page.locator('[data-errors]').innerText().catch(() => '<no-errors-el>');
      const categoryVal = await page.locator('[data-category]').inputValue().catch(() => '<no-category>');
      const rationaleVal = await page.locator('[data-rationale]').inputValue().catch(() => '<no-rationale>');
      const dialogVisible = await page.locator('.rv-modal.is-open').count().catch(() => -1);
      console.log(JSON.stringify({
        diagnostic: true,
        waitError: String(waitErr && waitErr.message || waitErr),
        consoleMsgs, pageErrors, errorsBox, categoryVal, rationaleVal, dialogVisible
      }, null, 2));
      process.exit(3);
    }
    const confirmText = await page.locator('[data-confirm-body]').innerText();
    await page.click('[data-export]');
    await page.waitForTimeout(300);
    const stateText = await page.locator('[data-review-request-state]').innerText();
    const payload = await page.locator('.review-request-data').innerText();
    console.log(JSON.stringify({ confirmText, stateText, payload: JSON.parse(payload) }));
  } finally {
    await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }
})().catch((err) => {
  console.error(String(err && err.stack || err));
  process.exit(1);
});
