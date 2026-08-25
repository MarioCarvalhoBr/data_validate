# 07 · Documentation & internationalisation

### DOC-001 · Root documents are outdated and partly generated
- Priority: P1 · Effort: M · Status: open
- Where: `README.md` (27 kB generated from `static/templates/README.TEMPLATE.md`, badge version
  hard-coded), `HOW_IT_WORKS.md` (mentions `controllers/processor.py`, `ModelListReport`),
  `TESTING.md` (threshold 4 % vs 50 %), `.github/copilot-instructions.md` (4 % / 100 % contradiction,
  legacy), `data_validate/__init__.py` docstring ("Adapta Parser … you can add information").
- Proposed fix: rewrite README (concise, accurate, links into `.specs/`), turn HOW_IT_WORKS/TESTING
  into short pointers to `.specs/architecture` and `.specs/quality`, delete copilot-instructions in
  favour of `AGENTS.md`/`CLAUDE.md`, keep the template generator only if README stays templated.

### DOC-002 · Business rules exist only in code and a PDF
- Priority: P1 · Effort: L · Status: open
- Where: `assets/protocolo-v-1.13.pdf`, `config/names_enum.py` (35 verification names), validators.
- Proposed fix: `.specs/business-rules/` — one file per sheet with a table `rule_id · NamesEnum key ·
  severity · description · protocol section · implemented by · tested by`; rule IDs
  (`DESC-001`, `COMP-003`, …) become the `Issue.rule_id` (ARC-004) and the test IDs.

### DOC-003 · i18n catalog quality
- Priority: P1 · Effort: M · Status: open
- Where: `static/locales/{pt_BR,en_US}/messages.json` — missing keys in en_US, demo leftovers, no
  naming convention, no placeholders documentation, no parity test, messages hard-coded in code
  (ARC-005).
- Proposed fix: key convention `<area>.<rule_id>.<kind>` (e.g. `rule.DESC-004.error`), one JSON per
  locale generated/validated by `tools/i18n_check.py` (parity, unused, placeholders), CI job.
- Related: BUG-016

### DOC-004 · API docs
- Priority: P2 · Effort: S · Status: open
- Where: `docs/**` pdoc output committed; docstring styles mixed (NumPy in validators, Google in
  helpers, Sphinx `:ivar:` in `facade.py`), several docstrings in Portuguese (`facade.py`,
  `scanner.py`, `spellchecker*.py`).
- Proposed fix: Google style everywhere (documented in `coding-standards.md`), English only, pdoc in
  CI to Pages.

### DOC-005 · Changelog
- Priority: P2 · Effort: S · Status: open
- Where: `CHANGELOG.md` has `[0.7.XX] - 2026-02-20` placeholder and duplicated bullets.
- Proposed fix: Keep-a-Changelog with an `Unreleased` section maintained per PR; automation in the
  release workflow (TOOL-005).

### DOC-006 · Protocol versioning
- Priority: P2 · Effort: S · Status: open
- Where: `assets/protocolo-1.0.pdf`, `assets/protocolo-v-1.13.pdf`; the validator does not know
  which protocol version it implements; `--protocol` CLI flag is free text.
- Proposed fix: `PROTOCOL_VERSION = "1.13"` constant surfaced in reports and `--version`;
  `.specs/business-rules/protocol-changelog.md`.

### DOC-007 · Portuguese/English mix in code comments
- Priority: P3 · Effort: S · Status: open
- Where: `helpers/tools/data_loader/**`, `helpers/tools/spellchecker/**`, `scripts/*.sh`,
  `pyproject.toml` (black comments in Portuguese).
- Proposed fix: English for code, comments, docs and commit messages; Portuguese only inside message
  catalogs and user-facing report text.
