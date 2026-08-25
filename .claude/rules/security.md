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

## Never do

- Never disable autoescape to make a template render "prettier" HTML.
- Never add a bare `except:` or `except Exception:` to make a test pass.
- Never write output, logs, or cache files inside `data_validate/`.
