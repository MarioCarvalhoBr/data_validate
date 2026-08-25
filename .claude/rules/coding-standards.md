# Coding standards

Applies to all new and touched Python code in `data_validate/`. Legacy code
being migrated may fall short until its backlog item lands — do not use
that as an excuse to write new code below this bar.

## Clean Code

- **Boy Scout Rule**: leave every file you touch cleaner than you found it;
  fix small smells inline instead of filing a ticket for them.
- **Single responsibility**: functions do one thing; keep them small
  (roughly 5–20 lines, never past 50) and split when they grow reasons to
  change.
- **Names reveal intent**: no `d`, `tmp`, `x1`, `Manager`, `Handler`. Verbs
  for functions, nouns for classes, `is_`/`has_`/`can_`/`should_` for
  booleans, `UPPER_CASE` for constants.
- **Comments are a last resort**: prefer code that doesn't need one. Keep
  only license headers, Google-style docstrings, and comments that explain
  *why* something non-obvious was necessary.
- **DRY**: one source of truth per piece of logic; extract instead of
  copy-pasting a second call site into existence.
- **KISS**: the simplest solution that is correct; no speculative
  generality, no premature optimisation.
- **Fail fast**: validate inputs at the top of a function and raise
  immediately; do not let bad state travel deeper into the call stack.
- **No magic numbers**: name the constant.
- **Long parameter lists** (more than ~4 positional args): replace with a
  frozen `dataclass` or explicit keyword-only arguments.

## Python 3.12+

- `from __future__ import annotations` at the top of every module.
- Generic builtins (`list[str]`, `dict[str, int]`), not `typing.List`/`Dict`.
- `pathlib.Path`, never raw `os.path` string joining, for new code.
- `@dataclass(frozen=True)` for value objects; `typing.Protocol` for
  structural interfaces instead of ABCs when you only need a shape.
- Type hints on every new function signature; `ruff` clean and
  `mypy --strict` clean for new/modified modules (see `pyproject.toml`
  overrides for the legacy exemption list).

## Discipline

- Docstrings in English, Google style, on every public class/function.
- Line length 120 (`ruff` enforces it — not the legacy 150).
- No global/module-level mutable state; pass dependencies through the
  constructor.
- No work in `__init__` beyond assigning what was passed in — no I/O, no
  calling `run()`, no side effects. Callers explicitly invoke behaviour
  (see backlog ARC-001).
- No `print()` for anything but the CLI's own final user-facing output;
  everything else goes through the injected logger.
- Catch specific exception types; never a bare or generic
  `except Exception` that hides the real failure.
