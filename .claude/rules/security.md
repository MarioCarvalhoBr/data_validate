# Security

Input is untrusted. Every spreadsheet this tool validates comes from an
external contributor, is parsed before it is judged safe, and can be
malformed or adversarial — treat it accordingly.

## Rules

- **Untrusted input**: never assume a workbook/CSV is well-formed. Validate
  structure before reading business data from it; fail with a clear
  message rather than crashing or silently coercing.
- **HTML output**: Jinja2 templates keep autoescape on. Only wrap a value in
  `Markup`/`|safe` when it is a template-authored HTML fragment, never for
  data that originated in a spreadsheet cell.
- **No dynamic execution**: never call `eval`, `exec`, or unpickle
  (`pickle.load`) on data that came from a file or the network.
- **XML**: if any code path parses XML, use `defusedxml`, never the stdlib
  `xml` modules directly (XXE/entity-expansion risk).
- **Size limits**: enforce a maximum input size (file size and row/column
  count) before processing a bundle; reject oversized input with a specific
  error instead of letting the process exhaust memory.
- **Exceptions**: catch specific exception types at the boundary where you
  can act on them; a bare/generic `except Exception` that swallows the
  original error is a bug, not error handling.
- **Exit codes**: the CLI's exit code must reflect what happened (0 = clean,
  non-zero + distinct code per failure class) — the platform integration
  depends on it. See `.specs/api/cli-contract.md`.
- **No writes inside the package**: the installed package directory is
  read-only in principle; all output (reports, logs, temp files) goes under
  the user-specified output folder, never under `data_validate/`.
- **Secrets**: never commit credentials, tokens, or `.env` files; they are
  denied from `Read` in `.claude/settings.json` for a reason — don't work
  around that.
- **Supply chain**: `bandit` and `pip-audit` must run clean (or with a
  justified, documented suppression) before a change is considered done;
  new dependencies get a one-line justification in the PR/commit.

## Hooks are defence in depth

`.claude/hooks/guard-bash.sh` and the `permissions.deny`/`allow` globs in
`.claude/settings.json` are string/token matchers over a shell command line.
They cannot reason about what an interpreter does with a string handed to
it — `python -c "..."`, `poetry run python -c "..."`, a script read from a
file, a base64-decoded payload — so treat them as a speed bump against
mistakes and obviously destructive one-liners, never as proof that a
session cannot exfiltrate a secret or rewrite history. The controls that
actually hold that line are:

- **No credentials in the environment/`.env`**: nothing that grants push,
  publish, or cloud access is ever exported into the shell this session
  runs in; `.env*` is git-ignored and denied from `Read`.
- **`persist-credentials: false`** on every `actions/checkout` step in CI
  (`.github/workflows/*.yml`), so a compromised job step can't reuse the
  checkout's token to push or open PRs.
- **Branch protection on `main`**: required reviews and status checks, no
  direct pushes — enforced by GitHub, not by anything running locally.
- **Human review of the diff before push**: the human runs `git push`
  (Claude never does, and the hook blocks it), and reviews what a commit
  actually contains before that push happens.

## Never do

- Never disable autoescape to make a template render "prettier" HTML.
- Never add a bare `except:` or `except Exception:` to make a test pass.
- Never write output, logs, or cache files inside `data_validate/`.
