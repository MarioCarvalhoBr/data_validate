#!/usr/bin/env bash
# Stop hook.
#
# Guards against ending a turn with broken unit tests or with production
# code changed but no matching spec update. Reads the hook payload from
# stdin; if `stop_hook_active` is true this is already a retry after a
# block, so it exits immediately to avoid looping.
set -euo pipefail

stdin_json="$(cat)"

stop_hook_active="$(printf '%s' "$stdin_json" | python3 -c '
import json, sys

try:
    payload = json.load(sys.stdin)
except (json.JSONDecodeError, ValueError):
    payload = {}

print("true" if payload.get("stop_hook_active") else "false")
')"

if [[ "$stop_hook_active" == "true" ]]; then
  exit 0
fi

changed_tracked="$(git diff --name-only HEAD -- 2>/dev/null || true)"
changed_untracked="$(git ls-files --others --exclude-standard 2>/dev/null || true)"
all_changed="$(printf '%s\n%s\n' "$changed_tracked" "$changed_untracked")"

py_changed="$(printf '%s\n' "$all_changed" | grep -E '\.py$' || true)"

if [[ -n "$py_changed" ]]; then
  set +e
  test_output="$(poetry run pytest -q --no-cov -x -p no:cacheprovider tests/unit 2>&1)"
  test_status=$?
  set -e

  if [[ "$test_status" -ne 0 ]]; then
    last_lines="$(printf '%s\n' "$test_output" | tail -n 5)"
    printf '%s' "$last_lines" | python3 -c '
import json, sys

reason = "unit tests failing: " + sys.stdin.read()
print(json.dumps({"decision": "block", "reason": reason}))
'
    exit 0
  fi
fi

data_validate_changed="$(printf '%s\n' "$all_changed" | grep -E '^data_validate/' || true)"
specs_or_rules_changed="$(printf '%s\n' "$all_changed" | grep -E '^(\.specs/|\.claude/rules/)' || true)"

if [[ -n "$data_validate_changed" && -z "$specs_or_rules_changed" ]]; then
  echo "warning: data_validate/ changed but nothing under .specs/ or .claude/rules/ was touched — see .claude/rules/spec-sync.md" >&2
fi

exit 0
