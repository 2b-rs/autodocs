const { webkit } = require('playwright');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

(async () => {
  const browser = await webkit.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1200 },
    colorScheme: 'light'
  });
  const consoleMessages = [];
  const pageErrors = [];
  const failedRequests = [];
  page.on('console', message => consoleMessages.push(`${message.type()}: ${message.text()}`));
  page.on('pageerror', error => pageErrors.push(String(error.stack || error)));
  page.on('requestfailed', request => failedRequests.push(`${request.url()} — ${request.failure()?.errorText || 'failed'}`));

  await page.goto(pathToFileURL(path.join(process.cwd(), 'index.html')).href, { waitUntil: 'load' });
  await page.waitForTimeout(7000);
  await page.screenshot({ path: 'homepage-webkit.png', fullPage: true });

  const report = await page.evaluate(() => {
    const box = element => {
      if (!element) return null;
      const r = element.getBoundingClientRect();
      return { x: Math.round(r.x), y: Math.round(r.y), width: Math.round(r.width), height: Math.round(r.height) };
    };
    const stage = document.querySelector('.component-graph-stage');
    const host = document.querySelector('[data-component-graph]');
    return {
      title: document.title,
      viewport: { width: innerWidth, height: innerHeight },
      document: { width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight },
      headings: [...document.querySelectorAll('h1,h2')].map(e => `${e.tagName}: ${e.innerText.trim()}`),
      graph: {
        present: Boolean(host),
        box: box(host),
        stagePresent: Boolean(stage),
        stageBox: box(stage),
        canvases: stage?.querySelectorAll('canvas').length || 0,
        error: stage?.querySelector('.graph-error')?.innerText || null
      },
      horizontalOverflow: document.documentElement.scrollWidth > innerWidth + 2,
      bodyText: document.body.innerText.slice(0, 3500)
    };
  });

  const output = { ...report, consoleMessages, pageErrors, failedRequests };
  require('node:fs').writeFileSync('homepage-webkit-report.json', JSON.stringify(output, null, 2));
  console.log(JSON.stringify(output, null, 2));
  await browser.close();
})().catch(error => {
  console.error(error.stack || error);
  process.exit(1);
});
