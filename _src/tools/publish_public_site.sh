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

# No publication identity is embedded here: the reviewed operator/service
# commit identity must be supplied explicitly. There is no default identity.
: "${PUBLISH_IDENTITY_NAME:?PUBLISH_IDENTITY_NAME is required: the reviewed operator/service commit author/committer name.}"
: "${PUBLISH_IDENTITY_EMAIL:?PUBLISH_IDENTITY_EMAIL is required: the reviewed operator/service commit author/committer email.}"
export GIT_AUTHOR_NAME="$PUBLISH_IDENTITY_NAME"
export GIT_AUTHOR_EMAIL="$PUBLISH_IDENTITY_EMAIL"
export GIT_COMMITTER_NAME="$PUBLISH_IDENTITY_NAME"
export GIT_COMMITTER_EMAIL="$PUBLISH_IDENTITY_EMAIL"
git commit -q -m "publish: public site from ${REVISION}"

echo "=== Prepared filtered publish tree at: $EXPORT_DIR ==="
echo "Top-level contents to publish:"
ls -1

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "=== Dry run only; not pushing ==="
  echo "Retained export dir: $EXPORT_DIR"
  exit 0
fi

# No publication destination is embedded here: the exact reviewed remote
# must be supplied explicitly. There is no default that resolves to the
# public repository.
: "${PUBLISH_REMOTE:?PUBLISH_REMOTE is required: the exact reviewed publish destination URL. There is no default; it must never silently resolve to the public repository.}"
: "${PUBLISH_TARGET_BRANCH:=main}"
PUBLISH_LOCAL_BRANCH="publish-main"

git remote add origin "$PUBLISH_REMOTE"

# This history-rewriting update overwrites the destination branch outright
# (an orphan export, not a fast-forward). It is not performed unconditionally:
# an operator/service caller must opt in explicitly and name the recorded
# approval evidence authorizing this specific force-update. The pre-update
# remote tip is captured first as the recovery point.
if [[ "${PUBLISH_ALLOW_FORCE_PUSH:-0}" == "1" ]]; then
  : "${PUBLISH_FORCE_APPROVAL_REF:?PUBLISH_FORCE_APPROVAL_REF is required when PUBLISH_ALLOW_FORCE_PUSH=1: name the recorded approval evidence authorizing this force-update.}"
  PRE_FORCE_REMOTE_SHA="$(git ls-remote "$PUBLISH_REMOTE" "refs/heads/$PUBLISH_TARGET_BRANCH" 2>/dev/null | cut -f1)"
  echo "publish_public_site.sh: force-updating refs/heads/$PUBLISH_TARGET_BRANCH; approval=$PUBLISH_FORCE_APPROVAL_REF pre_force_sha=${PRE_FORCE_REMOTE_SHA:-<none>} (recovery: reset refs/heads/$PUBLISH_TARGET_BRANCH to pre_force_sha if this update must be reverted)" >&2
  git push --force origin "$PUBLISH_LOCAL_BRANCH:$PUBLISH_TARGET_BRANCH"
else
  git push origin "$PUBLISH_LOCAL_BRANCH:$PUBLISH_TARGET_BRANCH"
fi

echo "Publish push complete: $PUBLISH_TARGET_BRANCH now contains only the filtered public tree (destination from explicit configuration)."
