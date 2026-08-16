#!/usr/bin/env bash
set -euo pipefail

# Publish the public site by creating a clean export of public paths inside output/
# and pushing that commit to origin/main.
#
# Included: generated/public artefacts (HTML/JS/CSS/assets/language dirs/issues/_schema/etc.)
# Excluded: source tree (_src), internal docs (docs/), issues/_policy, agent files,
#           run scripts, logs, output, and package/preview developer files.
#
# Usage:
#   _src/tools/publish_public_site.sh            # export HEAD and push to origin/main
#   _src/tools/publish_public_site.sh --dry-run  # build export locally, no push
#   _src/tools/publish_public_site.sh <rev>      # export a different revision

REVISION="HEAD"
DRY_RUN=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    *)
      REVISION="$1"
      shift
      ;;
  esac
done

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

EXPORT_BASE="$REPO_ROOT/output/publish-export"
EXPORT_DIR="$EXPORT_BASE/tree"

# Clean export target directory inside output/
rm -rf "$EXPORT_BASE"
mkdir -p "$EXPORT_DIR"

# Collect list of paths to export from git tree at REVISION
# Get all tracked files, filter out excluded paths, and export only permitted items
TRACKED_FILES=$(git ls-tree -r --name-only "$REVISION")

# Filter files: exclude _src/, docs/, issues/_policy/, logs/, AGENTS.md, SANDBOX.md, etc.
EXPORT_LIST="$EXPORT_BASE/files_to_export.txt"
: > "$EXPORT_LIST"

while IFS= read -r file; do
  # Exclude directories
  case "$file" in
    _src/*|docs/*|issues/_policy/*|logs/*|output/*|node_modules/*)
      continue
      ;;
  esac

  # Exclude specific files and patterns
  case "$file" in
    AGENTS.md|SANDBOX.md|PRIVILEGED.md|SCRIPTING.md|SENTINEL.md|SENTINTEL.md|DONE.md|TODO.md|TODO-*.md|TODO-perplexity.md)
      continue
      ;;
    agent-workflow.json|fs-test-manual.sh|run.sh|run-*.sh)
      continue
      ;;
    package.json|package-lock.json|playwright-webkit-preview.cjs)
      continue
      ;;
    *.log|*.out)
      continue
      ;;
    .git*|.DS_Store)
      continue
      ;;
  esac

  echo "$file" >> "$EXPORT_LIST"
done <<< "$TRACKED_FILES"

# Extract only allowed files into EXPORT_DIR via tar
tar -cf - -C "$REPO_ROOT" -T "$EXPORT_LIST" | tar -xf - -C "$EXPORT_DIR"

# Initialize git repository inside EXPORT_DIR and commit
cd "$EXPORT_DIR"
git init -q
git checkout -q -b publish-main
git add -A
if git diff --cached --quiet; then
  echo "Nothing to publish after filtering."
  exit 1
fi

git -c user.name='publish-bot' -c user.email='tobias.anton@accenture.com' commit -q -m "publish: public site from ${REVISION}"

echo "=== Prepared filtered publish tree at: $EXPORT_DIR ==="
echo "Top-level contents to publish:"
ls -1

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "=== Dry run only; not pushing ==="
  echo "Retained export dir: $EXPORT_DIR"
  exit 0
fi

git remote add origin git@github.com:2b-rs/autodocs.git
git push --force origin publish-main:main

echo "Publish push complete: origin main now contains only the filtered public tree."
