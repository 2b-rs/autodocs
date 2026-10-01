const { webkit } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const target = process.argv[2];
if (!target) { console.error('usage: bisect_review_request_ui.cjs <html-file>'); process.exit(2); }
const LIMIT = Number(process.env.BISECT_STEP_TIMEOUT_MS || 7000);
const events = [], consoleMsgs = [], pageErrors = [], failedRequests = [];
function stamp(){ return new Date().toISOString(); }
async function step(name, fn) {
  const begun = Date.now();
  console.error(`[${stamp()}] START ${name}`);
  events.push({name, state:'start', at:stamp()});
  let timer;
  try {
    const value = await Promise.race([
      Promise.resolve().then(fn),
      new Promise((_, reject) => { timer = setTimeout(() => reject(new Error(`STEP_TIMEOUT ${name} after ${LIMIT}ms`)), LIMIT); })
    ]);
    clearTimeout(timer);
    console.error(`[${stamp()}] DONE  ${name} (${Date.now()-begun}ms)`);
    events.push({name, state:'done', ms:Date.now()-begun, at:stamp()});
    return value;
  } catch (err) {
    clearTimeout(timer);
    console.error(`[${stamp()}] FAIL  ${name} (${Date.now()-begun}ms): ${String(err && err.stack || err)}`);
    events.push({name, state:'fail', ms:Date.now()-begun, error:String(err && err.stack || err), at:stamp()});
    throw err;
  }
}
(async () => {
  let browser;
  try {
    browser = await step('01 webkit.launch', () => webkit.launch({headless:true}));
    const page = await step('02 browser.newPage', () => browser.newPage({viewport:{width:390,height:844}}));
    page.on('console', m => consoleMsgs.push(`${m.type()}: ${m.text()}`));
    page.on('pageerror', e => pageErrors.push(String(e && e.stack || e)));
    page.on('requestfailed', r => failedRequests.push(`${r.url()} — ${r.failure()?.errorText || 'failed'}`));
    await step('03 page.goto(file URL; waitUntil=load)', () => page.goto(pathToFileURL(path.resolve(target)).href, {waitUntil:'load', timeout:LIMIT}));
    await step('04 settle 500ms', () => page.waitForTimeout(500));
    await step('05 localStorage identity', () => page.evaluate(() => localStorage.setItem('ara-review-identity','QA Reviewer')));
    await step('06 click review-request open', () => page.click('[data-review-request-open]', {timeout:LIMIT}));
    await step('07 select category', () => page.selectOption('[data-category]','missing-context',{timeout:LIMIT}));
    await step('08 fill rationale', () => page.fill('[data-rationale]','The summary omits boundary conditions.',{timeout:LIMIT}));
    await step('09 keyboard Tab', () => page.keyboard.press('Tab'));
    await step('10 click next', () => page.click('[data-next]',{timeout:LIMIT}));
    await step('11 await confirmation', () => page.waitForSelector('[data-confirm]:not([hidden])',{timeout:LIMIT}));
    const confirmText = await step('12 read confirmation', () => page.locator('[data-confirm-body]').innerText({timeout:LIMIT}));
    await step('13 click export', () => page.click('[data-export]',{timeout:LIMIT}));
    await step('14 settle 300ms', () => page.waitForTimeout(300));
    const stateText = await step('15 read state', () => page.locator('[data-review-request-state]').innerText({timeout:LIMIT}));
    const payloadText = await step('16 read payload', () => page.locator('.review-request-data').innerText({timeout:LIMIT}));
    console.log(JSON.stringify({ok:true, target:path.resolve(target), events, confirmText, stateText, payload:JSON.parse(payloadText), consoleMsgs,pageErrors,failedRequests},null,2));
  } catch (err) {
    console.log(JSON.stringify({ok:false,target:path.resolve(target),limitMs:LIMIT,events,error:String(err && err.stack || err),consoleMsgs,pageErrors,failedRequests},null,2));
    process.exitCode = 3;
  } finally {
    if (browser) {
      try { await step('99 browser.close', () => browser.close()); }
      catch (closeErr) { console.error(`close failed: ${String(closeErr && closeErr.stack || closeErr)}`); process.exitCode = process.exitCode || 4; }
    }
  }
})();
