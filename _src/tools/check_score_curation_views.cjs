const fs = require('node:fs');
const path = require('node:path');
const { webkit } = require('playwright');
const { pathToFileURL } = require('node:url');

function htmlFiles(root) {
  return fs.readdirSync(root, { withFileTypes: true }).flatMap((entry) => {
    const item = path.join(root, entry.name);
    return entry.isDirectory() ? htmlFiles(item) : (entry.isFile() && entry.name.endsWith('.html') ? [item] : []);
  });
}

(async () => {
  const root = process.argv[2];
  if (!root) throw new Error('usage: check_score_curation_views.cjs <generated-view-directory>');
  const files = htmlFiles(root).sort();
  const traversal = process.env.CURATION_CLIENT_QUICK === '1' ? files.slice(0, 1) : files;
  const browser = await webkit.launch({ headless: true });
  try {
    const page = await browser.newPage();
    for (const file of traversal) {
      await page.goto(pathToFileURL(file).href, { waitUntil: 'load', timeout: 30000 });
      await page.waitForSelector('#client-render-state[data-client-render="verified"]', { timeout: 30000 });
      const marker = await page.locator('[data-unvalidated-marker="awaiting-curator-confirmation"]').count();
      if (!marker) throw new Error(`unvalidated marker missing after client render: ${file}`);
    }
    const record = files.find((file) => path.basename(path.dirname(file)) === 'records' && path.basename(file) !== 'index.html');
    if (!record) throw new Error('no record page available for interactive review-request check');
    const githubWrites = [];
    page.on('request', (request) => {
      if (request.method() !== 'GET' && request.url().startsWith('https://api.github.com/')) githubWrites.push(`${request.method()} ${request.url()}`);
    });
    await page.goto(pathToFileURL(record).href, { waitUntil: 'load', timeout: 30000 });
    await page.click('[data-review-request-open]');
    const links = await page.locator('.rv-process-doc-link').evaluateAll((nodes) => nodes.map((node) => node.href));
    const expected = ['flag-for-review-protocol', 'storage-and-privacy'];
    if (links.length !== expected.length) throw new Error(`expected two dynamic process links, found ${links.length}`);
    const processText = fs.readFileSync(path.join(root, 'process.html'), 'utf8');
    for (let index = 0; index < expected.length; index += 1) {
      const target = new URL(links[index]);
      if (target.href !== pathToFileURL(path.join(root, 'process.html')).href + `#${expected[index]}`) {
        throw new Error(`dynamic process link escaped assembled root: ${links[index]}`);
      }
      if (!processText.includes(`id="${expected[index]}"`)) throw new Error(`dynamic process anchor missing: ${expected[index]}`);
    }
    await page.fill('[data-rationale]', 'Local unauthenticated regression evidence.');
    await page.click('[data-next]');
    await page.fill('[data-input]', 'Local regression reviewer');
    await page.click('[data-ok]');
    await page.locator('[data-confirm]:not([hidden])').waitFor();
    if (await page.locator('[data-submit]').isHidden()) throw new Error('review confirmation did not expose guarded submit');
    if (await page.locator('[data-export]').isHidden()) throw new Error('unauthenticated route did not expose JSON export');
    await page.click('[data-submit]');
    await page.waitForFunction(() => document.querySelector('[data-errors]')?.textContent.includes('GitHub connection required'));
    if (githubWrites.length) throw new Error(`unauthenticated submit attempted GitHub write: ${githubWrites.join(', ')}`);
    const download = page.waitForEvent('download');
    await page.click('[data-export]');
    await download;
    if (githubWrites.length) throw new Error(`unauthenticated route attempted GitHub write: ${githubWrites.join(', ')}`);
    console.log(JSON.stringify({ checked: files.length, state: 'verified', dynamic_process_links: links.length, unauthenticated_github_writes: githubWrites.length }));
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error.stack || String(error)); process.exit(1); });
