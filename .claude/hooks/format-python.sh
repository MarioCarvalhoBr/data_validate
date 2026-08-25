#!/usr/bin/env bash
# PostToolUse hook for Edit|Write|MultiEdit.
#
# If the touched file is a `.py` file that exists on disk, formats and
# auto-fixes it with ruff. Never fails the hook — a formatting error must
# not block the agent's turn, so every command below is best-effort.
set -euo pipefail

file_path="$(python3 -c '
import json, sys

try:
    payload = json.load(sys.stdin)
except (json.JSONDecodeError, ValueError):
    print("")
    sys.exit(0)

print(payload.get("tool_input", {}).get("file_path", "") or "")
')"

if [[ "$file_path" == *.py && -f "$file_path" ]]; then
  poetry run ruff format "$file_path" || true
  poetry run ruff check --fix --quiet "$file_path" || true
fi

exit 0
