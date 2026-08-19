#!/usr/bin/env bash
# SUPERSEDED — this shared-worktree provisioner is intentionally disabled.
# Use _src/tools/provision_worker_clone.sh instead; see
# docs/pipeline/worker-clone-provisioning.md.
#
# A git worktree shares the canonical repository's object store, refs, HEAD,
# and index. It can therefore move the canonical HEAD without changing that
# working tree. Feature 0041 replaces this unsafe mechanism with an isolated
# clone, whose commits become durable only after an explicit push.
set -euo pipefail

echo "provision_tmp_worktree: refused: shared git worktrees are superseded by isolated worker clones; use _src/tools/provision_worker_clone.sh <item-id>." >&2
exit 1
