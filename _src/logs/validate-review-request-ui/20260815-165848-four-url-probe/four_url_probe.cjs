const { webkit } = require('playwright');
const { pathToFileURL } = require('node:url');
const path = require('node:path');
const tiny = process.argv[2], review = process.argv[3];
if (!tiny || !review) { console.error('usage: four_url_probe.cjs <tiny-html> <review-html>'); process.exit(2); }
const LIMIT=7000, CLOSE_LIMIT=5000;
const cases=[
  ['about_blank','about:blank'],
  ['data_html','data:text/html,%3C!doctype%20html%3E%3Ctitle%3EData%20probe%3C%2Ftitle%3E%3Cp%20id%3Dok%3Edata-ok%3C%2Fp%3E'],
  ['file_tiny',pathToFileURL(path.resolve(tiny)).href],
  ['file_review',pathToFileURL(path.resolve(review)).href],
];
function raced(label, promise, ms=LIMIT) {
  let timer; const started=Date.now();
  return Promise.race([promise,new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error(`STEP_TIMEOUT ${label} after ${ms}ms`)),ms)})])
    .then(v=>{clearTimeout(timer);return {v,ms:Date.now()-started}})
    .catch(e=>{clearTimeout(timer);throw e});
}
async function runOne(name,url,waitUntil){
  const rec={name,url,waitUntil,events:{console:[],pageErrors:[],failedRequests:[],requests:[],finished:[]}};
  let browser;
  try {
    rec.launch=await raced('webkit.launch',webkit.launch({headless:true})); browser=rec.launch.v; delete rec.launch.v;
    rec.newPage=await raced('browser.newPage',browser.newPage({viewport:{width:390,height:844}})); const page=rec.newPage.v; delete rec.newPage.v;
    page.on('console',m=>rec.events.console.push(`${m.type()}: ${m.text()}`));
    page.on('pageerror',e=>rec.events.pageErrors.push(String(e&&e.stack||e)));
    page.on('requestfailed',r=>rec.events.failedRequests.push(`${r.url()} — ${r.failure()?.errorText||'failed'}`));
    page.on('request',r=>rec.events.requests.push(r.url()));
    page.on('requestfinished',r=>rec.events.finished.push(r.url()));
    console.error(`START ${name} / ${waitUntil} / ${url}`);
    const got=await raced(`goto ${name} ${waitUntil}`,page.goto(url,{waitUntil,timeout:LIMIT}));
    rec.goto={ok:true,ms:got.ms,status:got.v&&got.v.status&&got.v.status()};
    console.error(`DONE  ${name} / ${waitUntil} (${got.ms}ms)`);
    try {
      const snap=await raced(`snapshot ${name}`,page.evaluate(()=>({href:location.href,readyState:document.readyState,title:document.title,bodyText:document.body&&document.body.innerText.slice(0,200),htmlBytes:document.documentElement.outerHTML.length})),2000);
      rec.snapshot={ok:true,ms:snap.ms,value:snap.v};
    } catch(e) { rec.snapshot={ok:false,error:String(e&&e.stack||e)}; }
  } catch(e) {
    rec.goto=rec.goto||{ok:false,error:String(e&&e.stack||e)};
    console.error(`FAIL  ${name} / ${waitUntil}: ${rec.goto.error}`);
  } finally {
    if(browser) { try { const c=await raced('browser.close',browser.close(),CLOSE_LIMIT); rec.close={ok:true,ms:c.ms}; } catch(e){rec.close={ok:false,error:String(e&&e.stack||e)};} }
  }
  return rec;
}
(async()=>{
  const results=[];
  for(const [name,url] of cases) for(const waitUntil of ['domcontentloaded','load']) results.push(await runOne(name,url,waitUntil));
  console.log(JSON.stringify({limitMs:LIMIT,results},null,2));
})().catch(e=>{console.error(String(e&&e.stack||e));process.exit(1)});
