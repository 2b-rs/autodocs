#!/usr/bin/env bash
# Hermetic regression tests for provision_worker_clone.sh.
#
# Every fixture is a local Git repository under one mktemp directory. No test
# contacts a remote, and the trap removes only the directory created here.

set -u
set -o pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P) || {
    printf '%s\n' 'FATAL: cannot determine the test script directory.' >&2
    exit 2
}
PROVISIONER="$SCRIPT_DIR/provision_worker_clone.sh"

if ! command -v git >/dev/null 2>&1; then
    printf '%s\n' 'FATAL: git is required to run this test.' >&2
    exit 2
fi
if ! command -v bash >/dev/null 2>&1; then
    printf '%s\n' 'FATAL: bash is required to run the provisioner.' >&2
    exit 2
fi
if [ ! -f "$PROVISIONER" ]; then
    printf 'FATAL: provisioner not found: %s\n' "$PROVISIONER" >&2
    exit 2
fi

TMP_PARENT=${TMPDIR:-/tmp}
TMP_PARENT=${TMP_PARENT%/}
if [ -z "$TMP_PARENT" ]; then
    TMP_PARENT=/tmp
fi
TEST_ROOT=$(mktemp -d "$TMP_PARENT/provision-worker-clone-test.XXXXXX") || {
    printf '%s\n' 'FATAL: could not create a temporary test directory.' >&2
    exit 2
}

REGISTERED_WORKTREE=
REGISTERED_CANONICAL=
PASS_COUNT=0
FAIL_COUNT=0
CASE_DIR=
CANONICAL=
TARGET=

cleanup() {
    status=$?
    trap - EXIT HUP INT TERM

    if [ -n "$REGISTERED_WORKTREE" ] && [ -n "$REGISTERED_CANONICAL" ]; then
        git -C "$REGISTERED_CANONICAL" worktree remove --force "$REGISTERED_WORKTREE" >/dev/null 2>&1 || :
    fi

    case "$TEST_ROOT" in
        "$TMP_PARENT"/provision-worker-clone-test.*)
            rm -rf "$TEST_ROOT"
            ;;
        *)
            printf 'FATAL: refusing to remove unexpected temporary path: %s\n' "$TEST_ROOT" >&2
            status=2
            ;;
    esac

    exit "$status"
}
trap cleanup EXIT HUP INT TERM

fatal() {
    printf 'FATAL: %s\n' "$*" >&2
    exit 2
}

setup() {
    "$@" || fatal "fixture setup command failed: $*"
}

pass() {
    PASS_COUNT=$((PASS_COUNT + 1))
    printf 'PASS: %s\n' "$1"
}

fail() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf 'FAIL: %s\n' "$1" >&2
}

assert_equal() {
    description=$1
    expected=$2
    actual=$3

    if [ "$expected" = "$actual" ]; then
        pass "$description"
    else
        fail "$description"
        printf '  expected: <%s>\n  actual:   <%s>\n' "$expected" "$actual" >&2
    fi
}

assert_path_exists() {
    description=$1
    path=$2

    if [ -e "$path" ] || [ -L "$path" ]; then
        pass "$description"
    else
        fail "$description (missing: $path)"
    fi
}

assert_path_absent() {
    description=$1
    path=$2

    if [ ! -e "$path" ] && [ ! -L "$path" ]; then
        pass "$description"
    else
        fail "$description (unexpected path: $path)"
    fi
}

assert_file_text() {
    description=$1
    path=$2
    expected=$3

    if [ ! -f "$path" ]; then
        fail "$description (missing regular file: $path)"
        return
    fi
    actual=$(cat "$path") || fatal "cannot read fixture file: $path"
    assert_equal "$description" "$expected" "$actual"
}

assert_log_contains() {
    description=$1
    needle=$2
    log=$3

    if grep -F "$needle" "$log" >/dev/null 2>&1; then
        pass "$description"
    else
        fail "$description (did not find <$needle> in $log)"
        sed -n '1,20p' "$log" >&2 || :
    fi
}

new_standard_repo() {
    name=$1
    CASE_DIR="$TEST_ROOT/$name"
    CANONICAL="$CASE_DIR/canonical"
    mkdir -p "$CASE_DIR" || fatal "cannot create fixture directory: $CASE_DIR"

    setup git init -q "$CANONICAL"
    setup git -C "$CANONICAL" config user.name 'Provisioner test'
    setup git -C "$CANONICAL" config user.email 'provisioner-test@example.invalid'

    printf 'main baseline\n' > "$CANONICAL/README" || fatal 'cannot write main fixture file'
    printf 'original modified file\n' > "$CANONICAL/tracked-modified.txt" || fatal 'cannot write fixture file'
    printf 'original deleted file\n' > "$CANONICAL/tracked-deleted.txt" || fatal 'cannot write fixture file'
    printf 'original staged file\n' > "$CANONICAL/tracked-staged.txt" || fatal 'cannot write fixture file'
    setup git -C "$CANONICAL" add README tracked-modified.txt tracked-deleted.txt tracked-staged.txt
    setup git -C "$CANONICAL" commit -qm 'main baseline'
    setup git -C "$CANONICAL" branch -M main

    setup git -C "$CANONICAL" checkout -qb 0041
    printf 'exact feature parent\n' > "$CANONICAL/feature-parent-marker.txt" || fatal 'cannot write feature fixture file'
    setup git -C "$CANONICAL" add feature-parent-marker.txt
    setup git -C "$CANONICAL" commit -qm 'feature parent'
    setup git -C "$CANONICAL" checkout -q main
}

run_provisioner() {
    item=$1
    log=$2

    AUTODOCS_DEVEL="$CANONICAL" AUTODOCS_WORKER_TARGET="$TARGET" \
        bash "$PROVISIONER" "$item" >"$log" 2>&1
}

expect_provisioner_success() {
    description=$1
    item=$2
    log=$3

    if run_provisioner "$item" "$log"; then
        pass "$description"
        return 0
    fi

    fail "$description (provisioner exited non-zero)"
    sed -n '1,20p' "$log" >&2 || :
    return 1
}

expect_provisioner_failure() {
    description=$1
    item=$2
    log=$3

    if run_provisioner "$item" "$log"; then
        fail "$description (provisioner unexpectedly succeeded)"
        sed -n '1,20p' "$log" >&2 || :
        return 1
    fi

    pass "$description"
    return 0
}

test_new_task_branch_uses_exact_feature_parent_and_preserves_canonical() {
    printf '\n== new Task branch is isolated from canonical ==\n'
    new_standard_repo 'exact-parent'
    TARGET="$CASE_DIR/worker"
    log="$CASE_DIR/provision.log"

    printf 'canonical unstaged edit\n' >> "$CANONICAL/README" || fatal 'cannot dirty canonical fixture'
    before_status=$(git -C "$CANONICAL" status --porcelain) || fatal 'cannot capture canonical status'
    before_head=$(git -C "$CANONICAL" rev-parse --verify HEAD) || fatal 'cannot capture canonical HEAD'
    before_head_ref=$(git -C "$CANONICAL" symbolic-ref -q HEAD) || fatal 'cannot capture canonical HEAD ref'
    before_index_bytes=$(cksum < "$CANONICAL/.git/index") || fatal 'cannot capture canonical index bytes'
    before_index_entries=$(git -C "$CANONICAL" ls-files --stage) || fatal 'cannot capture canonical index entries'
    feature_sha=$(git -C "$CANONICAL" rev-parse --verify 0041) || fatal 'cannot capture feature parent SHA'

    expect_provisioner_success 'new Task provision succeeds' '0041-01' "$log" || return

    item_sha=$(git -C "$CANONICAL" rev-parse --verify 0041-01) || fatal 'missing item branch after successful provision'
    worker_sha=$(git -C "$TARGET" rev-parse --verify HEAD) || fatal 'cannot capture worker HEAD'
    after_status=$(git -C "$CANONICAL" status --porcelain) || fatal 'cannot capture canonical status after provision'
    after_head=$(git -C "$CANONICAL" rev-parse --verify HEAD) || fatal 'cannot capture canonical HEAD after provision'
    after_head_ref=$(git -C "$CANONICAL" symbolic-ref -q HEAD) || fatal 'cannot capture canonical HEAD ref after provision'
    after_index_bytes=$(cksum < "$CANONICAL/.git/index") || fatal 'cannot capture canonical index bytes after provision'
    after_index_entries=$(git -C "$CANONICAL" ls-files --stage) || fatal 'cannot capture canonical index entries after provision'
    worker_git_dir=$(git -C "$TARGET" rev-parse --git-dir) || fatal 'cannot inspect worker git directory'

    setup git -C "$TARGET" config user.name "Worker clone test"
    setup git -C "$TARGET" config user.email "worker-clone-test@example.invalid"
    printf "worker-only commit\n" > "$TARGET/worker-only-commit.txt" || fatal "cannot write worker commit fixture"
    setup git -C "$TARGET" add worker-only-commit.txt
    setup git -C "$TARGET" commit -qm "worker-only commit"
    worker_commit=$(git -C "$TARGET" rev-parse --verify HEAD) || fatal "cannot capture worker-only commit"
    after_worker_status=$(git -C "$CANONICAL" status --porcelain) || fatal "cannot capture canonical status after worker commit"
    after_worker_head=$(git -C "$CANONICAL" rev-parse --verify HEAD) || fatal "cannot capture canonical HEAD after worker commit"
    after_worker_index=$(cksum < "$CANONICAL/.git/index") || fatal "cannot capture canonical index after worker commit"
    after_worker_item_ref=$(git -C "$CANONICAL" rev-parse --verify 0041-01) || fatal "cannot capture canonical item ref after worker commit"

    assert_equal "worker local commit advances only worker HEAD" "$worker_commit" "$(git -C "$TARGET" rev-parse --verify HEAD)"
    assert_equal "canonical status remains unchanged after worker commit" "$before_status" "$after_worker_status"
    assert_equal "canonical HEAD remains unchanged after worker commit" "$before_head" "$after_worker_head"
    assert_equal "canonical index remains unchanged after worker commit" "$before_index_bytes" "$after_worker_index"
    assert_equal "canonical item ref is not moved by worker commit" "$item_sha" "$after_worker_item_ref"
    if git -C "$CANONICAL" cat-file -e "${worker_commit}^{commit}" 2>/dev/null; then
        fail "worker commit is absent from the canonical object store before push"
    else
        pass "worker commit is absent from the canonical object store before push"
    fi

    assert_equal 'item branch points at the exact Feature parent commit' "$feature_sha" "$item_sha"
    assert_equal 'worker HEAD points at the exact Feature parent commit' "$feature_sha" "$worker_sha"
    assert_equal 'worker is checked out on its Task branch' '0041-01' "$(git -C "$TARGET" rev-parse --abbrev-ref HEAD)"
    assert_equal 'worker has its own .git directory' '.git' "$worker_git_dir"
    assert_equal 'canonical porcelain status is unchanged' "$before_status" "$after_status"
    assert_equal 'canonical HEAD commit is unchanged' "$before_head" "$after_head"
    assert_equal 'canonical HEAD ref is unchanged' "$before_head_ref" "$after_head_ref"
    assert_equal 'canonical index bytes are unchanged' "$before_index_bytes" "$after_index_bytes"
    assert_equal 'canonical index entries are unchanged' "$before_index_entries" "$after_index_entries"
}

test_missing_exact_parent_fails_without_item_branch() {
    printf '\n== missing exact parent is rejected ==\n'
    new_standard_repo 'missing-parent'
    TARGET="$CASE_DIR/worker"
    log="$CASE_DIR/provision.log"

    expect_provisioner_failure 'missing Feature parent makes Task provision fail' '0042-01' "$log" || :
    if git -C "$CANONICAL" show-ref --verify --quiet refs/heads/0042-01; then
        fail 'missing Feature parent does not create the Task branch'
    else
        pass 'missing Feature parent does not create the Task branch'
    fi
    assert_path_absent 'missing Feature parent does not create a worker checkout' "$TARGET"
}

test_git_symlink_target_is_refused() {
    printf '\n== .git symlink target is rejected ==\n'
    new_standard_repo 'git-symlink'
    TARGET="$CASE_DIR/worker"
    log="$CASE_DIR/provision.log"

    mkdir -p "$TARGET" "$CASE_DIR/shared-git" || fatal 'cannot create symlink fixture'
    ln -s "$CASE_DIR/shared-git" "$TARGET/.git" || fatal 'cannot create .git symlink fixture'

    expect_provisioner_failure '.git symlink target is refused' '0041-02' "$log" || :
    if git -C "$CANONICAL" show-ref --verify --quiet refs/heads/0041-02; then
        fail "git symlink refusal does not create an item branch"
    else
        pass "git symlink refusal does not create an item branch"
    fi
    assert_log_contains '.git symlink refusal identifies the symlink' 'is a symlink' "$log"
    if [ -L "$TARGET/.git" ]; then
        pass '.git symlink is left in place'
    else
        fail '.git symlink is left in place'
    fi
}

test_registered_worktree_target_is_refused() {
    printf '\n== canonical registered worktree target is rejected ==\n'
    new_standard_repo 'registered-worktree'
    TARGET="$CASE_DIR/worker"
    log="$CASE_DIR/provision.log"

    setup git -C "$CANONICAL" worktree add -q -b 0041-worktree "$TARGET" 0041
    REGISTERED_WORKTREE=$TARGET
    REGISTERED_CANONICAL=$CANONICAL

    expect_provisioner_failure 'canonical registered worktree target is refused' '0041-03' "$log" || :
    if git -C "$CANONICAL" show-ref --verify --quiet refs/heads/0041-03; then
        fail "registered worktree refusal does not create an item branch"
    else
        pass "registered worktree refusal does not create an item branch"
    fi
    assert_log_contains 'registered worktree refusal identifies the worktree' "registered git worktree" "$log"
    assert_path_exists 'registered worktree remains in place' "$TARGET/.git"
}

test_idempotent_rerun_preserves_all_worker_edits() {
    printf '\n== idempotent rerun preserves worker edits ==\n'
    new_standard_repo 'preserve-edits'
    TARGET="$CASE_DIR/worker"
    log_first="$CASE_DIR/provision-first.log"
    log_second="$CASE_DIR/provision-second.log"

    expect_provisioner_success 'initial worker provision succeeds' '0041-04' "$log_first" || return

    printf 'modified but unstaged\n' > "$TARGET/tracked-modified.txt" || fatal 'cannot create modified fixture file'
    rm "$TARGET/tracked-deleted.txt" || fatal 'cannot create intentional deletion fixture'
    printf 'staged change\n' > "$TARGET/tracked-staged.txt" || fatal 'cannot create staged fixture file'
    setup git -C "$TARGET" add tracked-staged.txt
    printf 'untracked survivor\n' > "$TARGET/untracked-survivor.txt" || fatal 'cannot create untracked fixture file'

    before_status=$(git -C "$TARGET" status --porcelain) || fatal 'cannot capture worker status before rerun'
    expect_provisioner_success 'idempotent rerun succeeds with worker edits' '0041-04' "$log_second" || return
    after_status=$(git -C "$TARGET" status --porcelain) || fatal 'cannot capture worker status after rerun'

    assert_equal 'idempotent rerun preserves exact worker index and worktree status' "$before_status" "$after_status"
    assert_file_text 'idempotent rerun preserves modified tracked file' "$TARGET/tracked-modified.txt" 'modified but unstaged'
    assert_path_absent 'idempotent rerun preserves intentional unstaged tracked deletion' "$TARGET/tracked-deleted.txt"
    assert_file_text 'idempotent rerun preserves staged tracked content' "$TARGET/tracked-staged.txt" 'staged change'
    assert_file_text 'idempotent rerun preserves untracked file' "$TARGET/untracked-survivor.txt" 'untracked survivor'
    if git -C "$TARGET" diff --cached --quiet -- tracked-staged.txt; then
        fail 'idempotent rerun preserves staged change'
    else
        pass 'idempotent rerun preserves staged change'
    fi
}

test_missing_git_with_surviving_worker_content_is_refused() {
    printf '\n== surviving worker content without .git is rejected ==\n'
    new_standard_repo 'missing-git'
    TARGET="$CASE_DIR/worker"
    log_first="$CASE_DIR/provision-first.log"
    log_second="$CASE_DIR/provision-second.log"

    expect_provisioner_success 'initial worker provision succeeds before .git loss' '0041-05' "$log_first" || return
    printf 'do not delete this surviving worker content\n' > "$TARGET/surviving-worker-file.txt" || fatal 'cannot create surviving worker content'
    rm -rf "$TARGET/.git" || fatal 'cannot remove fixture .git directory'

    expect_provisioner_failure 'target without .git but with worker content is refused' '0041-05' "$log_second" || :
    assert_log_contains 'missing .git refusal is explicit' 'refusing' "$log_second"
    assert_file_text 'refusal preserves surviving worker content' "$TARGET/surviving-worker-file.txt" 'do not delete this surviving worker content'
    assert_path_exists 'refusal preserves tracked worker content' "$TARGET/feature-parent-marker.txt"
}

test_shared_object_clone_is_refused() {
    printf "\n== shared-object clone is rejected ==\n"
    new_standard_repo "shared-object-clone"
    TARGET="$CASE_DIR/worker"
    log="$CASE_DIR/provision.log"

    setup git -C "$CANONICAL" branch 0041-06 0041
    setup git clone -q --shared --branch 0041-06 "$CANONICAL" "$TARGET"
    assert_path_exists "shared-object clone contains alternates metadata" "$TARGET/.git/objects/info/alternates"

    expect_provisioner_failure "shared-object clone is refused" "0041-06" "$log" || :
    assert_log_contains "shared-object refusal identifies unhealthy isolation" "healthy self-contained clone" "$log"
    assert_path_exists "shared-object clone remains in place" "$TARGET/.git/objects/info/alternates"
}

test_unrelated_or_linked_git_metadata_target_is_refused() {
    printf "\n== unrelated and linked Git metadata targets are rejected ==\n"
    new_standard_repo "unrelated-origin"
    TARGET="$CASE_DIR/worker"
    log="$CASE_DIR/provision.log"
    other="$CASE_DIR/other-source"

    setup git -C "$CANONICAL" branch 0041-07 0041
    setup git clone -q --branch 0041-07 "$CANONICAL" "$TARGET"
    setup git clone -q "$CANONICAL" "$other"
    setup git -C "$TARGET" remote set-url origin "$other"
    expect_provisioner_failure "unrelated origin clone is refused" "0041-07" "$log" || :
    assert_log_contains "unrelated origin refusal identifies clone source" "not a healthy self-contained clone" "$log"
    assert_path_exists "unrelated origin target remains in place" "$TARGET/.git"

    new_standard_repo "linked-git-metadata"
    TARGET="$CASE_DIR/worker"
    log="$CASE_DIR/provision.log"
    setup git -C "$CANONICAL" branch 0041-08 0041
    setup git clone -q --branch 0041-08 "$CANONICAL" "$TARGET"
    rm -rf "$TARGET/.git/objects" || fatal "cannot remove fixture object directory"
    ln -s "$CANONICAL/.git/objects" "$TARGET/.git/objects" || fatal "cannot create linked object fixture"
    expect_provisioner_failure "linked Git objects target is refused" "0041-08" "$log" || :
    assert_log_contains "linked Git objects refusal identifies unhealthy clone" "not a healthy self-contained clone" "$log"
    if [ -L "$TARGET/.git/objects" ]; then
        pass "linked Git objects remain in place"
    else
        fail "linked Git objects remain in place"
    fi

    new_standard_repo "linked-git-refs"
    TARGET="$CASE_DIR/worker"
    log="$CASE_DIR/provision.log"
    setup git -C "$CANONICAL" branch 0041-09 0041
    setup git clone -q --branch 0041-09 "$CANONICAL" "$TARGET"
    rm -rf "$TARGET/.git/refs/heads" || fatal "cannot remove fixture local heads"
    ln -s "$CANONICAL/.git/refs/heads" "$TARGET/.git/refs/heads" || fatal "cannot create linked heads fixture"
    expect_provisioner_failure "linked Git refs target is refused" "0041-09" "$log" || :
    assert_log_contains "linked Git refs refusal identifies unhealthy clone" "not a healthy self-contained clone" "$log"
    if [ -L "$TARGET/.git/refs/heads" ]; then
        pass "linked Git refs remain in place"
    else
        fail "linked Git refs remain in place"
    fi
}

test_new_task_branch_uses_exact_feature_parent_and_preserves_canonical
test_missing_exact_parent_fails_without_item_branch
test_git_symlink_target_is_refused
test_registered_worktree_target_is_refused
test_idempotent_rerun_preserves_all_worker_edits
test_missing_git_with_surviving_worker_content_is_refused
test_shared_object_clone_is_refused
test_unrelated_or_linked_git_metadata_target_is_refused

if [ "$FAIL_COUNT" -eq 0 ]; then
    printf '\nRESULT: PASS (%s checks)\n' "$PASS_COUNT"
    exit 0
fi

printf '\nRESULT: FAIL (%s failed, %s passed)\n' "$FAIL_COUNT" "$PASS_COUNT" >&2
exit 1
