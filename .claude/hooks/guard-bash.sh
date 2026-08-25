#!/usr/bin/env bash
# PreToolUse hook for the Bash tool.
#
# Reads the hook payload (JSON) from stdin, extracts `tool_input.command`,
# and blocks (exit 2, reason on stderr) a short list of destructive or
# irreversible commands: `git push`, `git reset --hard`, `git clean -f`,
# `poetry publish`, `twine upload`, and `rm -rf` outside a safe allowlist of
# regenerable directories. Everything else is allowed (exit 0).
set -euo pipefail

python3 -c '
import json, re, shlex, sys

try:
    payload = json.load(sys.stdin)
except (json.JSONDecodeError, ValueError):
    sys.exit(0)

command = payload.get("tool_input", {}).get("command", "") or ""
if not command:
    sys.exit(0)

ALLOWED_RM_DIRS = {"dev-reports", "dist", ".pytest_cache", ".ruff_cache", ".mypy_cache", "build", "htmlcov"}

DENY_PATTERNS = [
    (re.compile(r"\bgit\s+push\b"), "git push is forbidden in this session: the user pushes, Claude never does."),
    (re.compile(r"\bgit\s+reset\s+--hard\b"), "git reset --hard is destructive and forbidden; stash or commit instead."),
    (re.compile(r"\bgit\s+clean\s+(?:-\w*f\w*|--force)\b"), "git clean -f is destructive and forbidden."),
    (re.compile(r"\bpoetry\s+publish\b"), "poetry publish is forbidden; releases go through release.yml."),
    (re.compile(r"\btwine\s+upload\b"), "twine upload is forbidden; releases go through release.yml."),
]

for pattern, reason in DENY_PATTERNS:
    if pattern.search(command):
        print(reason, file=sys.stderr)
        sys.exit(2)


def rm_rf_target_lists(cmd):
    try:
        tokens = shlex.split(cmd)
    except ValueError:
        return []

    calls = []
    i = 0
    while i < len(tokens):
        if tokens[i] != "rm":
            i += 1
            continue

        j = i + 1
        has_r = False
        has_f = False
        targets = []
        while j < len(tokens) and tokens[j] not in (";", "&&", "||", "|"):
            tok = tokens[j]
            if tok.startswith("--"):
                has_r = has_r or tok == "--recursive"
                has_f = has_f or tok == "--force"
            elif tok.startswith("-") and tok != "-":
                has_r = has_r or "r" in tok[1:] or "R" in tok[1:]
                has_f = has_f or "f" in tok[1:]
            else:
                targets.append(tok)
            j += 1

        if has_r and has_f:
            calls.append(targets)
        i = j

    return calls


for targets in rm_rf_target_lists(command):
    if not targets:
        print("rm -rf with no explicit target is forbidden.", file=sys.stderr)
        sys.exit(2)
    for target in targets:
        clean = target.lstrip("./")
        top = clean.split("/")[0] if clean else ""
        if top not in ALLOWED_RM_DIRS:
            print(
                "rm -rf on " + repr(target) + " is forbidden; only " + ", ".join(sorted(ALLOWED_RM_DIRS)) + " may be removed this way.",
                file=sys.stderr,
            )
            sys.exit(2)

sys.exit(0)
'
