#!/usr/bin/env node
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');

const root = path.resolve(__dirname, '..', '..');
const out = path.join(root, 'output', 'visual-qa');
const input = process.argv.slice(2);
const defaults = [
  'zh/classes/cl_ara_per_FileAccessor_efe7d0.html',
  'zh/namespaces/ns_per_ara_per_d9a3e9.html',
  'zh/namespaces/ns_shwa_ara_shwa_59c3fa.html',
  'zh/classes/cl_ara_com_e2e_ComE2EErrorDomain_fb2892.html'
];
const pages = input.length ? input : defaults;
const viewports = [
  { name: 'desktop', width: 1280, height: 900 },
  { name: 'mobile', width: 375, height: 812 }
];

(async () => {
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const report = { generatedAt: new Date().toISOString(), pages: [] };
  for (const rel of pages) {
    const file = path.resolve(root, rel);
    if (!fs.existsSync(file)) throw new Error(`Not found: ${rel}`);
    const entry = { file: rel, checks: [] };
    for (const vp of viewports) {
      const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: 1 });
      const consoleErrors = [];
      const pageErrors = [];
      page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
      page.on('pageerror', err => pageErrors.push(err.message));
      await page.goto(pathToFileURL(file).href, { waitUntil: 'load' });
      await page.evaluate(() => document.fonts && document.fonts.ready);
      const metrics = await page.evaluate(() => ({
        title: document.title,
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        bodyWidth: document.body.scrollWidth,
        overflowing: document.documentElement.scrollWidth > document.documentElement.clientWidth,
        h4: [...document.querySelectorAll('h4')].map(e => e.textContent.trim()),
        brokenImages: [...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.src)
      }));
      const stem = rel.replace(/[\\/]/g, '__').replace(/\.html$/, '');
      const image = path.join(out, `${stem}--${vp.name}.png`);
      await page.screenshot({ path: image, fullPage: true });
      entry.checks.push({ viewport: vp.name, ...metrics, consoleErrors, pageErrors, screenshot: path.relative(root, image) });
      await page.close();
    }
    report.pages.push(entry);
  }
  await browser.close();
  const reportPath = path.join(out, 'report.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2) + '\n');
  for (const p of report.pages) for (const c of p.checks) {
    console.log(`${p.file} [${c.viewport}] overflow=${c.overflowing} brokenImages=${c.brokenImages.length} consoleErrors=${c.consoleErrors.length} pageErrors=${c.pageErrors.length} screenshot=${c.screenshot}`);
  }
  console.log(`report=${path.relative(root, reportPath)}`);
})().catch(err => { console.error(err.stack || err); process.exit(1); });
