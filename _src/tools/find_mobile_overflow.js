#!/usr/bin/env node
const { chromium } = require('playwright');
const path = require('path');
const { pathToFileURL } = require('url');
const root = path.resolve(__dirname, '..', '..');
const defaults = [
  'zh/classes/cl_ara_per_FileAccessor_efe7d0.html',
  'zh/namespaces/ns_per_ara_per_d9a3e9.html',
  'zh/classes/cl_ara_com_e2e_ComE2EErrorDomain_fb2892.html'
];
(async () => {
  const browser = await chromium.launch({ headless: true });
  for (const rel of (process.argv.slice(2).length ? process.argv.slice(2) : defaults)) {
    const page = await browser.newPage({ viewport: { width: 375, height: 812 } });
    await page.goto(pathToFileURL(path.resolve(root, rel)).href, { waitUntil: 'load' });
    const items = await page.evaluate(() => {
      const vw = document.documentElement.clientWidth;
      return [...document.querySelectorAll('body *')]
        .map(el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el); return { tag: el.tagName, id: el.id, cls: el.className, left: Math.round(r.left), right: Math.round(r.right), width: Math.round(r.width), scrollWidth: el.scrollWidth, clientWidth: el.clientWidth, display: cs.display, whiteSpace: cs.whiteSpace, overflowX: cs.overflowX, text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 100) }; })
        .filter(x => x.width > 0 && (x.right > vw + 1 || x.left < -1 || x.scrollWidth > x.clientWidth + 1))
        .sort((a,b) => Math.max(b.width, b.scrollWidth) - Math.max(a.width, a.scrollWidth)).slice(0, 40);
    });
    console.log('\n### ' + rel);
    console.log(JSON.stringify(items, null, 2));
    await page.close();
  }
  await browser.close();
})().catch(err => { console.error(err.stack || err); process.exit(1); });
