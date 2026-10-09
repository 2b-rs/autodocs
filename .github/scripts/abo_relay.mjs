#!/usr/bin/env node
// abo_relay.mjs — Läufer für das Projektkontingent über das Gemini-Abo (Workflow .github/workflows/agy-relay.yml).
//
// Holt Aufträge beim Worker (POST /abo/runner/next, Long-Poll), entschlüsselt sie, ruft die offizielle
// Antigravity-CLI über agy_switch.py auf (Profil leo, bei erschöpftem Kontingent neo), verschlüsselt die
// Antwort und gibt sie zurück (POST /abo/runner/result). Meldet sich alle 20 s (Herzschlag), solange ein
// Auftrag läuft, und beendet sich nach 15 Minuten ohne Auftrag oder nach 5 Stunden.
//
// Das Repository ist öffentlich: Prompt, Antwort und Auftrags-IDs erscheinen nie im Log. Das Log nennt nur
// Anzahl, Modell, Profilname (leo/neo), Dauer und Fehlerart. agy läuft gesperrt: HOME aus setup-agy mit
// settings.json (nur Lesen im leeren Aufrufverzeichnis, jeder Befehl verboten), Aufruf in diesem leeren
// Verzeichnis, nie --dangerously-skip-permissions, eine Umgebung ohne ABO_RELAY_KEY und ohne GitHub-Token.
// Nach jedem Auftrag werden Verläufe, Transkripte und Logs von agy aus den Profilen gelöscht.
//
// Umgebung: ABO_RELAY_URL (Worker), ABO_RELAY_KEY (Actions-Secret der Umgebung agy, derselbe Wert wie
// das Worker-Secret), AUTODOCS_AGY_PROFILES und AUTODOCS_AGY_LOCKDOWN_DIR (aus setup-agy), optional
// ABO_IDLE_S, ABO_MAX_S, AGY_STATE.
import { spawn } from "node:child_process";
import { readdir, rm, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const te = new TextEncoder(), td = new TextDecoder();
const HERE = path.dirname(fileURLToPath(import.meta.url));

// ------------------------------------------------- Verschlüsselung (wie proxy/abo-relay.mjs im Quell-Repo)
export function b64(bytes) {
  let s = "";
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
  return btoa(s);
}
export function unb64(s) {
  s = String(s || "").trim().replace(/-/g, "+").replace(/_/g, "/");
  while (s.length % 4) s += "=";
  const bin = atob(s);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}
function b64url(bytes) { return b64(bytes).replace(/=+$/, "").replace(/\+/g, "-").replace(/\//g, "_"); }
export async function relayKeys(secret) {
  const raw = unb64(secret);
  if (raw.length < 32) throw new Error("ABO_RELAY_KEY must decode to at least 32 bytes");
  const ikm = await crypto.subtle.importKey("raw", raw, "HKDF", false, ["deriveKey", "deriveBits"]);
  const salt = te.encode("autodocs-abo-relay");
  const aes = await crypto.subtle.deriveKey({ name: "HKDF", hash: "SHA-256", salt, info: te.encode("aes-256-gcm v1") },
    ikm, { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
  const bits = await crypto.subtle.deriveBits({ name: "HKDF", hash: "SHA-256", salt, info: te.encode("runner-token v1") }, ikm, 256);
  return { aes, runnerToken: b64url(new Uint8Array(bits)) };
}
export async function seal(aes, obj, aad, iv = crypto.getRandomValues(new Uint8Array(12))) {
  const ct = await crypto.subtle.encrypt({ name: "AES-GCM", iv, additionalData: te.encode(aad) }, aes, te.encode(JSON.stringify(obj)));
  return { v: 1, iv: b64(iv), ct: b64(new Uint8Array(ct)) };
}
export async function unseal(aes, box, aad) {
  if (!box || box.v !== 1) throw new Error("envelope");
  const pt = await crypto.subtle.decrypt({ name: "AES-GCM", iv: unb64(box.iv), additionalData: te.encode(aad) }, aes, unb64(box.ct));
  return JSON.parse(td.decode(pt));
}

// ------------------------------------------------------------------ agy
// Was in einem Profil-HOME bleiben darf: Anmeldung, Werkzeugsperre, Programmteile. Alles andere
// (conversations/, brain/, history.jsonl, log/, Zusammenfassungen) kann Prompts enthalten und wird gelöscht.
export const KEEP = {
  home: [".gemini"],
  gemini: ["antigravity-cli"],
  cli: ["antigravity-oauth-token", "installation_id", "settings.json", "bin", "builtin", "updater", "last_check.timestamp"]
};
async function prune(dir, keep) {
  let names = [];
  try { names = await readdir(dir); } catch (e) { return; }
  for (const n of names) if (!keep.includes(n)) await rm(path.join(dir, n), { recursive: true, force: true });
}
export async function scrubHome(home) {
  await prune(home, KEEP.home);
  await prune(path.join(home, ".gemini"), KEEP.gemini);
  await prune(path.join(home, ".gemini", "antigravity-cli"), KEEP.cli);
}
export function profileNames(homes) {
  return homes.map((h) => path.basename(h.replace(/\/+$/, "")).replace(/^agy-profile-/, ""));
}

const DENIED = /auto-denied|cannot prompt for/i;
// Ergebnis eines agy_switch.py-Aufrufs: stream-json von agy auf stdout, Statuszeile "agy-switch: {...}" auf stderr.
export function parseAgy(stdout, stderr, rc) {
  let sw = {};
  for (const line of String(stderr || "").split("\n")) {
    if (line.startsWith("agy-switch: ")) { try { sw = JSON.parse(line.slice(12)); } catch (e) { sw = {}; } }
  }
  let result = null;
  for (const raw of String(stdout || "").split("\n")) {
    const line = raw.trim();
    if (!line.startsWith("{")) continue;
    let ev;
    try { ev = JSON.parse(line); } catch (e) { continue; }
    if (ev.event === "result" && ev.result && typeof ev.result === "object") result = ev.result;
    else if (!ev.event && typeof ev.response === "string") result = ev;        // --output-format json
  }
  const profile = String(sw.profile || "");
  if (rc === 75) {
    const waits = Object.values(sw.cooldown_s || {}).map(Number).filter((n) => n > 0);
    return { ok: false, code: "exhausted", profile, wait_s: waits.length ? Math.min(...waits) : 3600 };
  }
  if (rc === 77) return { ok: false, code: "login", profile };
  const answer = result && typeof result.response === "string" ? result.response : "";
  if (DENIED.test(String(stdout) + "\n" + String(stderr)) && !answer.trim()) return { ok: false, code: "denied", profile };
  if (rc !== 0) return { ok: false, code: "agy", profile, rc };
  if (result && result.status && result.status !== "SUCCESS" && !answer.trim()) return { ok: false, code: "agy", profile, rc };
  if (!answer.trim()) return { ok: false, code: "empty", profile };
  return { ok: true, answer, profile };
}

// Umgebung für agy: nur, was die CLI braucht. Kein ABO_RELAY_KEY, kein GITHUB_TOKEN, keine ACTIONS_*-Werte.
export function agyEnv(cfg, src = process.env) {
  const env = { PATH: src.PATH || "/usr/bin:/bin", LANG: src.LANG || "C.UTF-8", AUTODOCS_AGY_PROFILES: cfg.profiles.join(",") };
  for (const k of ["RUNNER_TEMP", "TMPDIR", "AGY_STATE", "TZ"]) if (src[k]) env[k] = src[k];
  return env;
}

function runProcess(cmd, args, opts, timeoutMs) {
  return new Promise((resolve) => {
    const child = spawn(cmd, args, Object.assign({ stdio: ["ignore", "pipe", "pipe"] }, opts));
    let out = "", errText = "", timedOut = false;
    child.stdout.on("data", (d) => { out += d; });
    child.stderr.on("data", (d) => { errText += d; });
    const t = setTimeout(() => { timedOut = true; child.kill("SIGKILL"); }, timeoutMs);
    child.on("error", (e) => { clearTimeout(t); resolve({ rc: 127, stdout: out, stderr: errText + String(e), timedOut }); });
    child.on("close", (code) => { clearTimeout(t); resolve({ rc: code == null ? 1 : code, stdout: out, stderr: errText, timedOut }); });
  });
}

// Modelle, die das installierte agy anbietet (`agy models`, erste Spalte); leer = nicht prüfbar.
export async function agyModels(cfg) {
  if (!cfg.profiles.length) return [];
  const r = await runProcess(cfg.agy, ["models"], { cwd: cfg.callDir, env: Object.assign(agyEnv(cfg), { HOME: cfg.profiles[0] }) }, 60_000);
  if (r.rc !== 0) return [];
  return r.stdout.split("\n").map((l) => l.trim().split(/\s+/)[0]).filter((id) => /^[a-z0-9][a-z0-9.\-]+$/.test(id || ""));
}

const PREFACE = "Antworte direkt und nur aus dem folgenden Text. Benutze keine Werkzeuge, lies keine Dateien und führe nichts aus.\n\n";
export async function runAgy(cfg, prompt, model) {
  const once = async (text) => {
    const args = [cfg.switchScript, "--state", cfg.state, "--",
      "--model", model, "--output-format", "stream-json", "--disable-slash-commands", "--print-timeout", cfg.agyTimeoutS + "s",
      "-p", text];
    const r = await runProcess(cfg.python, args, { cwd: cfg.callDir, env: agyEnv(cfg) }, (cfg.agyTimeoutS + 60) * 1000);
    if (r.timedOut) return { ok: false, code: "timeout", profile: "" };
    return parseAgy(r.stdout, r.stderr, r.rc);
  };
  let res = await once(prompt);
  // Wollte agy trotz Sperre ein Werkzeug benutzen, endet der Aufruf ohne Text (die Meldung „auto-denied“ steht
  // auf stderr, das agy_switch.py bei Erfolg nicht weitergibt): einmal mit ausdrücklichem Verbot wiederholen.
  if (!res.ok && (res.code === "denied" || res.code === "empty")) {
    const again = await once(PREFACE + prompt);
    res = again.ok || again.code !== "empty" ? again : Object.assign(again, { code: res.code });
  }
  return res;
}

// ------------------------------------------------------------------ Schleife
export function configFromEnv(env = process.env) {
  const profiles = String(env.AUTODOCS_AGY_PROFILES || "").split(",").filter(Boolean);
  return {
    url: String(env.ABO_RELAY_URL || "").replace(/\/+$/, ""),
    key: env.ABO_RELAY_KEY || "",
    profiles,
    callDir: env.AUTODOCS_AGY_LOCKDOWN_DIR || "",
    state: env.AGY_STATE || path.join(env.RUNNER_TEMP || "/tmp", "agy-state.json"),
    switchScript: env.ABO_SWITCH_SCRIPT || path.join(HERE, "agy_switch.py"),
    python: env.ABO_PYTHON || "python3",
    agy: env.ABO_AGY || "agy",
    idleMs: (parseInt(env.ABO_IDLE_S || "", 10) || 900) * 1000,
    maxMs: (parseInt(env.ABO_MAX_S || "", 10) || 5 * 3600) * 1000,
    pollWaitMs: parseInt(env.ABO_POLL_WAIT_MS || "", 10) || 25_000,
    heartbeatMs: parseInt(env.ABO_HEARTBEAT_MS || "", 10) || 20_000,
    agyTimeoutS: parseInt(env.ABO_AGY_TIMEOUT_S || "", 10) || 600
  };
}

export async function main(cfg = configFromEnv(), log = (m) => console.log("abo-relay: " + m)) {
  if (!cfg.url || !cfg.key) { log("ABO_RELAY_URL oder ABO_RELAY_KEY fehlt"); return 1; }
  if (!cfg.profiles.length) { log("keine agy-Profile (setup-agy)"); return 1; }
  if (!cfg.callDir) { log("keine Werkzeugsperre (setup-agy lockdown_dir) – Abbruch"); return 1; }
  for (const h of cfg.profiles) {
    try { await stat(path.join(h, ".gemini", "antigravity-cli", "settings.json")); }
    catch (e) { log("Profil " + profileNames([h])[0] + " ohne settings.json (Werkzeugsperre) – Abbruch"); return 1; }
  }
  const keys = await relayKeys(cfg.key);
  const auth = { Authorization: "Bearer " + keys.runnerToken, "Content-Type": "application/json" };
  const post = (p, body, timeoutMs) => fetch(cfg.url + p, { method: "POST", headers: auth, body: JSON.stringify(body || {}),
                                                             signal: AbortSignal.timeout(timeoutMs || 30_000) });
  const offered = await agyModels(cfg).catch(() => []);
  log("bereit · Profile " + profileNames(cfg.profiles).join(", ") + " · agy-Modelle " + (offered.length || "ungeprüft"));
  const start = Date.now();
  let lastJob = Date.now(), done = 0, failures = 0;
  for (;;) {
    const now = Date.now();
    if (now - start > cfg.maxMs || now - lastJob > cfg.idleMs) {
      const why = now - start > cfg.maxMs ? "Höchstlaufzeit" : "Leerlauf";
      let queued = 0;
      try { queued = (await (await post("/abo/runner/heartbeat", { state: "leaving" })).json()).queued || 0; } catch (e) { queued = 0; }
      // Warten noch Aufträge, bleibt der Läufer, solange die Höchstlaufzeit es erlaubt.
      if (queued > 0 && now - start <= cfg.maxMs) { lastJob = Date.now(); continue; }
      log("Ende (" + why + ") · " + done + " Aufträge");
      return 0;
    }
    let res;
    try { res = await post("/abo/runner/next", { wait_ms: cfg.pollWaitMs }, cfg.pollWaitMs + 15_000); }
    catch (e) {
      if (++failures > 20) { log("Worker nicht erreichbar – Abbruch"); return 1; }
      await new Promise((r) => setTimeout(r, Math.min(30_000, 1000 * failures)));
      continue;
    }
    if (res.status === 401) { log("Läufer-Token abgelehnt: ABO_RELAY_KEY von Worker und Umgebung agy stimmen nicht überein"); return 1; }
    if (res.status === 503) { log("Gemini-Abo am Worker nicht eingerichtet – Abbruch"); return 1; }
    if (res.status === 204) { failures = 0; continue; }
    if (!res.ok) {
      if (++failures > 20) { log("Worker antwortet mit HTTP " + res.status + " – Abbruch"); return 1; }
      await new Promise((r) => setTimeout(r, Math.min(30_000, 1000 * failures)));
      continue;
    }
    failures = 0;
    const job = await res.json();
    lastJob = Date.now();
    const t0 = Date.now();
    const hb = setInterval(() => { post("/abo/runner/heartbeat", { state: "busy" }).catch(() => {}); }, cfg.heartbeatMs);
    let outcome;
    try {
      let payload = null;
      try { payload = await unseal(keys.aes, job.job, "job:" + job.id); } catch (e) { payload = null; }
      if (!payload || typeof payload.prompt !== "string") outcome = { ok: false, code: "decrypt", profile: "" };
      else if (offered.length && !offered.includes(String(payload.model))) outcome = { ok: false, code: "model_unavailable", profile: "" };
      else outcome = await runAgy(cfg, payload.prompt, String(payload.model));
      const body = { id: job.id, profile: outcome.profile || "", error: outcome.ok ? null : outcome.code,
                     detail: outcome.wait_s ? { wait_s: outcome.wait_s } : null,
                     result: outcome.ok ? await seal(keys.aes, { answer: outcome.answer }, "result:" + job.id) : null };
      try { await post("/abo/runner/result", body); } catch (e) { log("Ergebnis konnte nicht zugestellt werden"); }
    } finally {
      clearInterval(hb);
      for (const h of cfg.profiles) await scrubHome(h).catch(() => {});
    }
    done++;
    log("Auftrag " + done + ": " + (outcome.ok ? "beantwortet" : outcome.code) + " · " + (job.model || "?") +
        (outcome.profile ? " · " + outcome.profile : "") + " · " + Math.round((Date.now() - t0) / 1000) + " s");
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  main().then((code) => process.exit(code), (e) => { console.log("abo-relay: Fehler " + (e && e.name)); process.exit(1); });
}
