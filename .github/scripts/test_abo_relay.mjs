// Prüft abo_relay.mjs ohne Netz und ohne echtes agy: gefälschtes agy im PATH, echtes agy_switch.py,
// gefälschter Worker über HTTP auf 127.0.0.1, echte Profilverzeichnisse aus dem Schritt "Profile anlegen"
// von setup-agy (mit Werkzeugsperre). Aufruf: node .github/scripts/test_abo_relay.mjs  (Exit 0 = alles bestanden)
import { createServer } from "node:http";
import { mkdtemp, mkdir, writeFile, readFile, readdir, chmod, stat, rm } from "node:fs/promises";
import { existsSync, readFileSync } from "node:fs";
import { execFileSync, spawnSync } from "node:child_process";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { relayKeys, seal, unseal, parseAgy, scrubHome, agyEnv, main, KEEP } from "./abo_relay.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..", "..");
const results = [];
function t(name, ok, info) { results.push([ok ? "PASS" : "FAIL", name, ok ? "" : String(info === undefined ? "" : JSON.stringify(info)).slice(0, 300)]); }

// --- 1. Verschlüsselung: fester Prüfvektor, identisch in _src/tests/abo_relay_check.mjs (Quell-Repo, Worker-Seite).
const VECTOR = {
  key: Buffer.from(Array.from({ length: 32 }, (_, i) => i + 1)).toString("base64"),
  iv: Uint8Array.from(Array.from({ length: 12 }, (_, i) => 0xa0 + i)),
  aad: "job:vector",
  obj: { prompt: "Prüfe SWS_Com_00001 ✓", model: "gemini-3.8-flash-medium" },
  ct: "d+1xrJutN2/Zi7CuQCm6zecMKL1SKRBzcvQ9hPt6bVBEdOaBu9okHcSJpoMUMVcvYNGtd4EjwmsscKB6IMAKavHKWERPYcdgrgwVRSaduTng8JK5JccV",
  runnerToken: "jR6jKMF_z3xeM-ulu-8iJbyQbpkGAggvCKhQLH-mrz8"
};
const vk = await relayKeys(VECTOR.key);
const vbox = await seal(vk.aes, VECTOR.obj, VECTOR.aad, VECTOR.iv);
t("Prüfvektor: Chiffrat wie im Worker", vbox.ct === VECTOR.ct, vbox.ct);
t("Prüfvektor: Läufer-Token wie im Worker", vk.runnerToken === VECTOR.runnerToken, vk.runnerToken);
t("Rundreise", JSON.stringify(await unseal(vk.aes, vbox, VECTOR.aad)) === JSON.stringify(VECTOR.obj));
let wrongAad = false;
try { await unseal(vk.aes, vbox, "result:vector"); } catch (e) { wrongAad = true; }
t("falsche Zuordnung (aad) wird abgelehnt", wrongAad);
let shortKey = false;
try { await relayKeys(Buffer.from("zu kurz").toString("base64")); } catch (e) { shortKey = true; }
t("zu kurzer Schlüssel wird abgelehnt", shortKey);
t("Schlüssel mit Zeilenende (gh secret set < datei) funktioniert", (await relayKeys(VECTOR.key + "\n")).runnerToken === VECTOR.runnerToken);

// --- 2. Auswertung der agy-Ausgabe
const ok = '{"event":"init","init":{"model":"gemini-3.8-flash-medium"}}\n{"event":"result","result":{"status":"SUCCESS","response":"Hallo","num_turns":1}}\n';
t("Erfolg", JSON.stringify(parseAgy(ok, 'agy-switch: {"profile": "leo", "result": "ok", "tried": []}\n', 0)) ===
  JSON.stringify({ ok: true, answer: "Hallo", profile: "leo" }));
const ex = parseAgy("", 'agy-switch: {"result": "exhausted", "tried": [], "needs_login": [], "cooldown_s": {"leo": 3720, "neo": 1200}}\n', 75);
t("rc 75 = erschöpft, kürzeste Sperre", ex.code === "exhausted" && ex.wait_s === 1200, ex);
t("rc 77 = keine Anmeldung", parseAgy("", 'agy-switch: {"result": "needs_login"}\n', 77).code === "login");
t("Werkzeug verweigert", parseAgy("", "a tool required the read_file permission that headless mode cannot prompt for, so it was auto-denied\n", 0).code === "denied");
t("leere Antwort", parseAgy('{"event":"result","result":{"status":"SUCCESS","response":"  "}}\n', "", 0).code === "empty");
t("anderer Fehler", parseAgy("", "boom", 2).code === "agy");
t("--output-format json", parseAgy('{"status":"SUCCESS","response":"Json"}', "", 0).answer === "Json");

// --- 3. Umgebung für agy ohne Geheimnisse
const envOut = agyEnv({ profiles: ["/x/agy-profile-leo"] }, { PATH: "/bin", ABO_RELAY_KEY: "k", GITHUB_TOKEN: "g", ACTIONS_RUNTIME_TOKEN: "a", RUNNER_TEMP: "/r" });
t("agy bekommt keinen ABO_RELAY_KEY/GITHUB_TOKEN", !("ABO_RELAY_KEY" in envOut) && !("GITHUB_TOKEN" in envOut) && !("ACTIONS_RUNTIME_TOKEN" in envOut) && envOut.RUNNER_TEMP === "/r", envOut);

// --- 4. setup-agy: Schritt "Profile anlegen" wirklich ausführen (bash), mit Werkzeugsperre
const tmp = await mkdtemp(path.join(os.tmpdir(), "abo-relay-test-"));
const runnerTemp = path.join(tmp, "runner");
await mkdir(runnerTemp, { recursive: true });
const action = readFileSync(path.join(ROOT, ".github/actions/setup-agy/action.yml"), "utf8");
function runBlock(yml, stepName) {
  const lines = yml.split("\n");
  let i = lines.findIndex((l) => l.includes("- name: " + stepName));
  while (i < lines.length && !/^\s+run: \|\s*$/.test(lines[i])) i++;
  const ind = lines[i].indexOf("run:");
  const out = [];
  for (let j = i + 1; j < lines.length; j++) {
    const l = lines[j];
    if (l.trim() && l.search(/\S/) <= ind) break;
    out.push(l.slice(ind + 2));
  }
  return out.join("\n");
}
const ghEnv = path.join(tmp, "github_env"), ghOut = path.join(tmp, "github_output");
await writeFile(ghEnv, ""); await writeFile(ghOut, "");
const lockdown = path.join(runnerTemp, "agy-call");
const setup = spawnSync("bash", ["-c", runBlock(action, "Profile anlegen")], { encoding: "utf8", env: Object.assign({}, process.env, {
  T1: "token-leo-geheim", T2: "token-neo-geheim", N1: "leo", N2: "neo", LOCK: lockdown, RUNNER_TEMP: runnerTemp,
  GITHUB_ENV: ghEnv, GITHUB_OUTPUT: ghOut }) });
t("setup-agy: Schritt läuft", setup.status === 0, setup.stderr);
t("setup-agy: Log ohne Token", !(setup.stdout + setup.stderr).includes("geheim"), setup.stdout);
const ghEnvText = readFileSync(ghEnv, "utf8");
const profiles = (/AUTODOCS_AGY_PROFILES=(.*)/.exec(ghEnvText) || [])[1].split(",");
const lockReal = (/AUTODOCS_AGY_LOCKDOWN_DIR=(.*)/.exec(ghEnvText) || [])[1];
t("setup-agy: zwei Profile leo, neo", profiles.map((p) => path.basename(p)).join(",") === "agy-profile-leo,agy-profile-neo", profiles);
const settings = JSON.parse(readFileSync(path.join(profiles[0], ".gemini/antigravity-cli/settings.json"), "utf8"));
t("setup-agy: Sperre erlaubt nur Lesen im Aufrufverzeichnis", JSON.stringify(settings) === JSON.stringify({ permissions: {
  allow: ["read_file(" + lockReal + "/*)"], deny: ["command(*)", "command(regex:.*)"] } }), settings);
t("setup-agy: Aufrufverzeichnis ist echt und leer", lockReal && existsSync(lockReal) && (await readdir(lockReal)).length === 0, lockReal);
t("setup-agy: Token nur für den Eigentümer lesbar", ((await stat(path.join(profiles[0], ".gemini/antigravity-cli/antigravity-oauth-token"))).mode & 0o077) === 0);
const noLock = path.join(tmp, "github_env2");
await writeFile(noLock, "");
const setup2 = spawnSync("bash", ["-c", runBlock(action, "Profile anlegen")], { encoding: "utf8", env: Object.assign({}, process.env, {
  T1: "x", T2: "", N1: "smoke", N2: "neo", LOCK: "", RUNNER_TEMP: path.join(tmp, "runner2"), GITHUB_ENV: noLock, GITHUB_OUTPUT: ghOut }) });
t("setup-agy ohne lockdown_dir (Rauchtest) unverändert ohne settings.json", setup2.status === 0 &&
  !existsSync(path.join(tmp, "runner2/agy-profile-smoke/.gemini/antigravity-cli/settings.json")) && !readFileSync(noLock, "utf8").includes("LOCKDOWN"), setup2.stderr);

// --- 5. Aufräumen der Profile
const scrubHomeDir = path.join(tmp, "scrub");
await mkdir(path.join(scrubHomeDir, ".gemini/antigravity-cli/conversations"), { recursive: true });
await mkdir(path.join(scrubHomeDir, ".gemini/antigravity-cli/bin"), { recursive: true });
await mkdir(path.join(scrubHomeDir, ".cache"), { recursive: true });
for (const f of ["antigravity-oauth-token", "settings.json", "history.jsonl", "conversation_summaries.db", "installation_id"]) {
  await writeFile(path.join(scrubHomeDir, ".gemini/antigravity-cli", f), "x");
}
await scrubHome(scrubHomeDir);
const left = (await readdir(path.join(scrubHomeDir, ".gemini/antigravity-cli"))).sort();
t("Profil aufgeräumt: nur Anmeldung, Sperre, Programmteile", JSON.stringify(left) === JSON.stringify(["antigravity-oauth-token", "bin", "installation_id", "settings.json"]) &&
  !existsSync(path.join(scrubHomeDir, ".cache")), left);
t("Aufbewahrungsliste enthält kein Verlaufsverzeichnis", !KEEP.cli.some((k) => /conversation|brain|history|log/.test(k)));

// --- 6. Ganze Schleife: gefälschtes agy, echtes agy_switch.py, gefälschter Worker
const bin = path.join(tmp, "bin");
await mkdir(bin);
const fakeAgy = path.join(bin, "agy");
await writeFile(fakeAgy, `#!/usr/bin/env node
const fs = require("fs"), path = require("path");
const a = process.argv.slice(2);
if (a[0] === "models") { console.log("gemini-3.8-flash-medium\\tGemini 3.8 Flash (Medium)\\ngemini-3.1-pro-high\\tGemini 3.1 Pro (High)"); console.error("Fetching available models..."); process.exit(0); }
const p = a[a.indexOf("-p") + 1] || "", model = a[a.indexOf("--model") + 1] || "";
const home = process.env.HOME, name = path.basename(home).replace("agy-profile-", "");
const cli = path.join(home, ".gemini/antigravity-cli");
let settings = null; try { settings = JSON.parse(fs.readFileSync(path.join(cli, "settings.json"), "utf8")); } catch (e) {}
fs.appendFileSync(path.join(process.env.RUNNER_TEMP, "fake-agy.log"), JSON.stringify({ name, model, cwd: process.cwd(),
  skip: a.includes("--dangerously-skip-permissions"), slash: a.includes("--disable-slash-commands"), key: "ABO_RELAY_KEY" in process.env,
  gh: "GITHUB_TOKEN" in process.env, deny: settings && settings.permissions.deny, allow: settings && settings.permissions.allow,
  preface: p.startsWith("Antworte direkt") }) + "\\n");
fs.mkdirSync(path.join(cli, "conversations"), { recursive: true });
fs.writeFileSync(path.join(cli, "conversations", "c1.pb"), p);
fs.appendFileSync(path.join(cli, "history.jsonl"), JSON.stringify({ p }) + "\\n");
const result = (r) => { console.log(JSON.stringify({ event: "init", init: { model } })); console.log(JSON.stringify({ event: "result", result: { status: "SUCCESS", response: r, num_turns: 1 } })); };
if (p.includes("EXHAUST-ALL") || (p.includes("EXHAUST-LEO") && name === "leo")) { console.error("Error: RESOURCE_EXHAUSTED: quota reached. Resets in 1h2m3s"); process.exit(3); }
if (p.includes("NO-LOGIN")) { console.error("Error: not logged in"); process.exit(1); }
if (p.includes("DENY-ONCE") && !p.startsWith("Antworte direkt")) { console.error("a tool required the read_file permission that headless mode cannot prompt for, so it was auto-denied"); result(""); process.exit(0); }
if (p.includes("CRASH")) { console.error("boom"); process.exit(2); }
result("Antwort von " + name + " auf " + p.length + " Zeichen");
`);
await chmod(fakeAgy, 0o755);

const keySecret = Buffer.from(Array.from({ length: 32 }, (_, i) => 200 - i)).toString("base64");
const keys = await relayKeys(keySecret);
const statePath = path.join(runnerTemp, "agy-state.json");
const SECRET_WORD = "VERTRAULICH-7f3a";
const plan = [
  { name: "normal", prompt: SECRET_WORD + " Frage", model: "gemini-3.8-flash-medium" },
  { name: "leo erschöpft → neo", prompt: SECRET_WORD + " EXHAUST-LEO", model: "gemini-3.1-pro-high" },
  { name: "beide erschöpft", prompt: SECRET_WORD + " EXHAUST-ALL", model: "gemini-3.8-flash-medium" },
  { name: "keine Anmeldung", prompt: SECRET_WORD + " NO-LOGIN", model: "gemini-3.8-flash-medium" },
  { name: "Werkzeug verweigert, Wiederholung", prompt: SECRET_WORD + " DENY-ONCE", model: "gemini-3.8-flash-medium" },
  { name: "agy-Fehler", prompt: SECRET_WORD + " CRASH", model: "gemini-3.8-flash-medium" },
  { name: "Modell nicht angeboten", prompt: SECRET_WORD, model: "gemini-9-ultra" },
  { name: "falsch verschlüsselt", prompt: SECRET_WORD, model: "gemini-3.8-flash-medium", badAad: true }
];
const queue = [];
for (let i = 0; i < plan.length; i++) {
  const id = "job" + i + "abcdefgh";
  queue.push({ id, model: plan[i].model, job: await seal(keys.aes, { prompt: plan[i].prompt, model: plan[i].model }, plan[i].badAad ? "job:other" : "job:" + id) });
}
const got = {}, beats = [], unauth = [];
const server = createServer(async (req, res) => {
  let body = "";
  for await (const c of req) body += c;
  if (req.headers.authorization !== "Bearer " + keys.runnerToken) { unauth.push(req.url); res.writeHead(401); return res.end("{}"); }
  const b = body ? JSON.parse(body) : {};
  if (req.url === "/abo/runner/next") {
    const j = queue.shift();
    if (!j) { await new Promise((r) => setTimeout(r, 50)); res.writeHead(204); return res.end(); }
    res.writeHead(200, { "Content-Type": "application/json" }); return res.end(JSON.stringify(j));
  }
  if (req.url === "/abo/runner/heartbeat") { beats.push(b.state); res.writeHead(200); return res.end(JSON.stringify({ queued: 0 })); }
  if (req.url === "/abo/runner/result") {
    got[b.id] = b;
    await rm(statePath, { force: true });          // jeder Fall beginnt mit frischem Sperrzustand
    res.writeHead(200); return res.end("{}");
  }
  res.writeHead(404); res.end("{}");
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const logs = [];
const cfg = { url: "http://127.0.0.1:" + server.address().port, key: keySecret, profiles, callDir: lockReal, state: statePath,
              switchScript: path.join(HERE, "agy_switch.py"), python: "python3", agy: fakeAgy,
              idleMs: 1500, maxMs: 120_000, pollWaitMs: 100, heartbeatMs: 50, agyTimeoutS: 30 };
process.env.PATH = bin + path.delimiter + process.env.PATH;
process.env.RUNNER_TEMP = runnerTemp;
process.env.ABO_RELAY_KEY = keySecret;              // darf agy nicht erreichen
process.env.GITHUB_TOKEN = "ghs_should_not_leak";
const t0 = Date.now();
const rc = await main(cfg, (m) => logs.push(m));
server.close();
t("Schleife endet nach Leerlauf mit 0", rc === 0 && Date.now() - t0 < 60_000, { rc, logs });
t("Abmeldung beim Worker", beats.includes("leaving"), beats);
t("Herzschlag während eines Auftrags", beats.includes("busy"), beats);
t("kein Aufruf ohne Läufer-Token", unauth.length === 0, unauth);
const outcome = async (i) => {
  const r = got["job" + i + "abcdefgh"];
  if (!r) return null;
  const answer = r.result ? (await unseal(keys.aes, r.result, "result:" + r.id)).answer : null;
  return { error: r.error, profile: r.profile, detail: r.detail, answer };
};
const o = [];
for (let i = 0; i < plan.length; i++) o.push(await outcome(i));
t("normal: Antwort verschlüsselt zurück, Profil leo", o[0] && !o[0].error && o[0].profile === "leo" && /Antwort von leo/.test(o[0].answer), o[0]);
t("leo erschöpft → neo antwortet", o[1] && !o[1].error && o[1].profile === "neo" && /Antwort von neo/.test(o[1].answer), o[1]);
t("beide erschöpft → exhausted mit Wartezeit", o[2] && o[2].error === "exhausted" && o[2].detail && o[2].detail.wait_s > 3000, o[2]);
t("keine Anmeldung → login", o[3] && o[3].error === "login", o[3]);
t("Werkzeug verweigert → Wiederholung mit Verbot beantwortet", o[4] && !o[4].error && /Antwort von/.test(o[4].answer), o[4]);
t("agy-Fehler → agy", o[5] && o[5].error === "agy", o[5]);
t("Modell nicht angeboten → model_unavailable ohne agy-Aufruf", o[6] && o[6].error === "model_unavailable", o[6]);
t("falsch verschlüsselt → decrypt", o[7] && o[7].error === "decrypt", o[7]);
const calls = readFileSync(path.join(runnerTemp, "fake-agy.log"), "utf8").trim().split("\n").map((l) => JSON.parse(l));
t("agy nie mit --dangerously-skip-permissions", calls.length > 0 && calls.every((c) => !c.skip), calls.length);
t("agy immer mit --disable-slash-commands", calls.every((c) => c.slash));
t("agy läuft im leeren Aufrufverzeichnis", calls.every((c) => c.cwd === lockReal), calls.map((c) => c.cwd));
t("agy sieht weder ABO_RELAY_KEY noch GITHUB_TOKEN", calls.every((c) => !c.key && !c.gh));
t("agy läuft mit Werkzeugsperre (deny command)", calls.every((c) => JSON.stringify(c.deny) === '["command(*)","command(regex:.*)"]' &&
  c.allow.length === 1 && c.allow[0] === "read_file(" + lockReal + "/*)"));
t("Wiederholung nur für den verweigerten Fall", calls.filter((c) => c.preface).length === 1);
t("Modell aus dem Auftrag an agy", calls.some((c) => c.model === "gemini-3.1-pro-high"));
for (const h of profiles) {
  const names = (await readdir(path.join(h, ".gemini/antigravity-cli"))).sort();
  t("nach den Aufträgen keine Verläufe in " + path.basename(h), !names.includes("conversations") && !names.includes("history.jsonl") &&
    names.includes("antigravity-oauth-token") && names.includes("settings.json"), names);
}
const logText = logs.join("\n");
t("Log ohne Prompt, Antwort, Auftrags-ID, Schlüssel", !logText.includes(SECRET_WORD) && !logText.includes("Antwort von") &&
  !logText.includes("abcdefgh") && !logText.includes(keySecret) && !logText.includes(keys.runnerToken), logs);
t("Log nennt nur Profilnamen leo/neo", /leo/.test(logText) && /neo/.test(logText) && !logText.includes(tmp), logs);
t("Log zählt die Aufträge", logs.some((l) => l.startsWith("Ende (Leerlauf) · 8 Aufträge")), logs);

// Falscher Schlüssel am Worker: Abbruch mit klarer Meldung, ohne Endlosschleife.
const s401 = createServer((req, res) => { res.writeHead(401); res.end("{}"); });
await new Promise((r) => s401.listen(0, "127.0.0.1", r));
const logs401 = [];
const rc401 = await main(Object.assign({}, cfg, { url: "http://127.0.0.1:" + s401.address().port }), (m) => logs401.push(m));
s401.close();
t("abgelehntes Läufer-Token → Abbruch mit Hinweis", rc401 === 1 && logs401.some((l) => l.includes("ABO_RELAY_KEY")), logs401);
const rcNoLock = await main(Object.assign({}, cfg, { callDir: "" }), () => {});
t("ohne Werkzeugsperre kein Start", rcNoLock === 1);

// --- 7. Workflow: Struktur und Sperren
const wf = readFileSync(path.join(ROOT, ".github/workflows/agy-relay.yml"), "utf8");
t("Workflow: nur workflow_dispatch ohne Eingaben", /\non:\n {2}workflow_dispatch:\n\n/.test(wf) && !/^\s+inputs:/m.test(wf));
t("Workflow: Umgebung agy, ein Läufer gleichzeitig", /environment: agy/.test(wf) && /concurrency:\n {2}group: agy-relay\n {2}cancel-in-progress: false/.test(wf));
t("Workflow: Werkzeugsperre an, kein skip-permissions", /lockdown_dir: \$\{\{ runner\.temp \}\}\/agy-call/.test(wf) && !wf.includes("dangerously-skip-permissions"));
t("Workflow: keine Artefakte, nur der Sperrzustand im Cache", !/upload-artifact/.test(wf) && (wf.match(/path: \$\{\{ runner\.temp \}\}\/agy-state\.json/g) || []).length === 2);
t("Workflow: Profile werden entfernt", /rm -rf "\$RUNNER_TEMP"\/agy-profile-\*/.test(wf));
let lint = "actionlint nicht installiert";
try { execFileSync("actionlint", ["-version"], { stdio: "ignore" }); lint = null; } catch (e) { /* übersprungen */ }
if (!lint) {
  const r = spawnSync("actionlint", ["-no-color", path.join(ROOT, ".github/workflows/agy-relay.yml"), path.join(ROOT, ".github/workflows/agy-smoke.yml")], { encoding: "utf8", cwd: ROOT });
  t("actionlint ohne Befund", r.status === 0, r.stdout + r.stderr);
} else results.push(["SKIP", "actionlint", lint]);

await rm(tmp, { recursive: true, force: true });
for (const r of results) console.log(r.filter(Boolean).join("  "));
const fails = results.filter((r) => r[0] === "FAIL").length;
console.log(results.filter((r) => r[0] === "PASS").length + "/" + results.filter((r) => r[0] !== "SKIP").length);
process.exit(fails ? 1 : 0);
