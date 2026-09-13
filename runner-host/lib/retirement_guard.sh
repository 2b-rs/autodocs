#!/usr/bin/env bash
# Shared singleton-retirement admission guard.  This file is sourced by the
# host loop; it neither invokes nor imports the rollback executor.

RETIREMENT_GUARD_ALLOW=0
RETIREMENT_GUARD_RETIRED=64
RETIREMENT_GUARD_FAILOVER_REQUIRED=65

retirement_guard_is_sentinel() {
  local request_path="$1" sentinel_text="$2"
  grep -Fq -- "$sentinel_text" "$request_path"
}

retirement_guard_protocol() {
  local selector_path="$1" protocol
  [[ -f "$selector_path" ]] || return 1
  protocol="$(sed -nE 's/.*"runner_protocol"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p' "$selector_path")"
  [[ -n "$protocol" && "$(printf '%s\n' "$protocol" | wc -l | tr -d ' ')" == 1 ]] || return 1
  [[ "$protocol" == "runner-request@v1" || "$protocol" == "runner-queue@v1" ]] || return 1
  printf '%s\n' "$protocol"
}

retirement_guard_archive_rejection() {
  local request_path="$1" archive_dir="$2" outcome="$3" detail="$4" stamp candidate result_path
  stamp="$(date -u '+%Y-%m-%d_%H-%M-%S')"
  mkdir -p "$archive_dir" || return 1
  candidate="$archive_dir/${outcome}-${stamp}-run.sh"
  # noclobber makes same-second outcomes collision-safe without overwriting a
  # prior request.  The bounded suffix also makes the evidence discoverable.
  local suffix=0
  while ! (set -o noclobber; : > "$candidate") 2>/dev/null; do
    suffix=$((suffix + 1))
    candidate="$archive_dir/${outcome}-${stamp}-${suffix}-run.sh"
  done
  rm -f "$candidate"
  mv "$request_path" "$candidate" || return 1
  result_path="${candidate%.sh}.result.txt"
  printf 'result_code=%s\nmessage=%s\n' "$outcome" "$detail" > "$result_path" || return 1
  RETIREMENT_GUARD_ARCHIVE_PATH="$candidate"
}

# Arguments: root request archive sentinel [test-only callback].  The optional
# callback is deliberately unavailable to run-loop production wiring; tests
# use it only to assert exactly-once future FAILOVER_REQUIRED mapping.
retirement_guard_admit() {
  local root_dir="$1" request_path="$2" archive_dir="$3" sentinel_text="$4" callback="${5:-}"
  local protocol detail
  RETIREMENT_GUARD_ARCHIVE_PATH=""
  if retirement_guard_is_sentinel "$request_path" "$sentinel_text"; then
    return "$RETIREMENT_GUARD_ALLOW"
  fi
  if ! protocol="$(retirement_guard_protocol "$root_dir/agent-workflow.json")"; then
    detail='FAILOVER_REQUIRED: selector is missing, malformed, or unsupported; singleton request parked without execution.'
    retirement_guard_archive_rejection "$request_path" "$archive_dir" "FAILOVER_REQUIRED" "$detail" || return 1
    if [[ -n "$callback" ]]; then "$callback" "FAILOVER_REQUIRED" "$RETIREMENT_GUARD_ARCHIVE_PATH"; fi
    return "$RETIREMENT_GUARD_FAILOVER_REQUIRED"
  fi
  if [[ "$protocol" == "runner-queue@v1" ]]; then
    detail='SINGLETON_RETIRED: selector declares runner-queue@v1; publish via .runner/ queue instead.'
    retirement_guard_archive_rejection "$request_path" "$archive_dir" "SINGLETON_RETIRED" "$detail" || return 1
    return "$RETIREMENT_GUARD_RETIRED"
  fi
  return "$RETIREMENT_GUARD_ALLOW"
}
