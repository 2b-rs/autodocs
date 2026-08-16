#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""link_verification_evidence.py — Clean scratchpads, validate, and commit evidence logs."""

import glob
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def cleanup_ephemeral():
    print("--- 1. Cleaning ephemeral scratchpads ---")
    ephemeral_dirs = [
        os.path.join(ROOT, "_review_request_bisect_tmp"),
        os.path.join(ROOT, "_review_request_four_url_probe"),
    ]
    for d in ephemeral_dirs:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)
            print(f"Removed directory: {os.path.relpath(d, ROOT)}")

    for f in glob.glob(os.path.join(ROOT, ".perplexity-cpu-loop-recovery*")):
        if os.path.isfile(f):
            try:
                os.remove(f)
                print(f"Removed file: {os.path.basename(f)}")
            except Exception as e:
                print(f"Could not remove {f}: {e}")

def sanitize_and_check_models():
    print("--- 2. Validating page models ---")
    process_json_path = os.path.join(ROOT, "_src", "sources", "pages", "process.json")
    try:
        with open(process_json_path, "r", encoding="utf-8") as f:
            raw = f.read()
        data = json.loads(raw)
        print("process.json: Valid JSON structure.")
    except Exception as e:
        print(f"Fixing process.json formatting: {e}")
        # Repair unescaped backslashes or invalid escapes
        fixed = raw.replace('\\"', '"').replace('\\\\', '\\')
        # Re-encode standard
        try:
            data = json.loads(fixed)
            with open(process_json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=1, ensure_ascii=False)
            print("process.json repaired.")
        except Exception as e2:
            print(f"Could not automatically repair: {e2}")

def run_build_and_validate():
    print("--- 3. Running site generation and validation ---")
    res_gen = subprocess.run([sys.executable, "_src/generate.py"], cwd=ROOT, capture_output=True, text=True)
    if res_gen.returncode != 0:
        print("ERROR in generate.py:\n", res_gen.stderr)
        print("stdout:\n", res_gen.stdout)
        sys.exit(res_gen.returncode)
    print("generate.py: OK")

    res_val = subprocess.run([sys.executable, "_src/validate.py"], cwd=ROOT, capture_output=True, text=True)
    if res_val.returncode != 0:
        print("ERROR in validate.py:\n", res_val.stderr)
        print("stdout:\n", res_val.stdout)
        sys.exit(res_val.returncode)
    print("validate.py: OK (all link & schema checks passed)")

def execute_commits():
    print("--- 4. Performing structured Git commits ---")
    # Commit 1: Evidence logs
    subprocess.run(["git", "add", "logs/", "_src/logs/"], cwd=ROOT, check=False)
    diff_cached = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, capture_output=True, text=True)
    if diff_cached.stdout.strip():
        c1 = subprocess.run(
            ["git", "commit", "-m", "evidence: record verification logs, qualification runs, and audit trails"],
            cwd=ROOT, capture_output=True, text=True
        )
        print("Commit 1 (Evidence Logs):", c1.stdout.strip().split("\n")[0])
    else:
        print("Commit 1: Nothing to commit for evidence logs.")

    # Commit 2: Task Claims
    subprocess.run(["git", "add", "TODO-perplexity-*.md"], cwd=ROOT, check=False)
    diff_claims = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, capture_output=True, text=True)
    if diff_claims.stdout.strip():
        c2 = subprocess.run(
            ["git", "commit", "-m", "claims: record task coordination logs and session closure files"],
            cwd=ROOT, capture_output=True, text=True
        )
        print("Commit 2 (Claims):", c2.stdout.strip().split("\n")[0])
    else:
        print("Commit 2: Nothing to commit for claims.")

    # Commit 3: Tooling, page model updates, and generated html
    subprocess.run(["git", "add", "_src/tools/link_verification_evidence.py", "_src/sources/pages/", "*.html"], cwd=ROOT, check=False)
    diff_cached3 = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, capture_output=True, text=True)
    if diff_cached3.stdout.strip():
        c3 = subprocess.run(
            ["git", "commit", "-m", "tools, docs: automate evidence linking in report page models and rebuild site"],
            cwd=ROOT, capture_output=True, text=True
        )
        print("Commit 3 (Tools & Models):", c3.stdout.strip().split("\n")[0])
    else:
        print("Commit 3: Nothing to commit for tools/models.")

def main():
    cleanup_ephemeral()
    sanitize_and_check_models()
    run_build_and_validate()
    execute_commits()
    print("\n=== SUMMARY VERDICT ===")
    status = subprocess.run(["git", "status", "--short"], cwd=ROOT, capture_output=True, text=True)
    print("Git Short Status:")
    print(status.stdout if status.stdout.strip() else "Working tree clean!")
    print("\nPASS: link_verification_evidence completed successfully.")

if __name__ == "__main__":
    main()
