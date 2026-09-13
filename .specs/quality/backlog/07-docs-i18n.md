# 07 · Documentation & internationalisation

### DOC-001 · Root documents are outdated and partly generated
- Priority: P1 · Effort: M · Status: done
- Where: `README.md` (27 kB generated from `static/templates/README.TEMPLATE.md`, badge version
  hard-coded), `HOW_IT_WORKS.md` (mentions `controllers/processor.py`, `ModelListReport`),
  `TESTING.md` (threshold 4 % vs 50 %), `.github/copilot-instructions.md` (4 % / 100 % contradiction,
  legacy), `data_validate/__init__.py` docstring ("Adapta Parser … you can add information").
- Proposed fix: rewrite README (concise, accurate, links into `.specs/`), turn HOW_IT_WORKS/TESTING
  into short pointers to `.specs/architecture` and `.specs/quality`, delete copilot-instructions in
  favour of `AGENTS.md`/`CLAUDE.md`, keep the template generator only if README stays templated.
- Done: (4b801ae); note `tools/check_links.py` found a broken anchor `#-features` in `data_validate/static/templates/README.TEMPLATE.md` (generator retired by ADR-0009; file removed in Phase 5)

### DOC-002 · Business rules exist only in code and a PDF
- Priority: P1 · Effort: L · Status: done
- Where: `assets/protocolo-v-1.13.pdf`, `config/names_enum.py` (34 verification names), validators.
- Proposed fix: `.specs/business-rules/` — one file per sheet with a table `rule_id · NamesEnum key ·
  severity · description · protocol section · implemented by · tested by`; rule IDs
  (`DESC-001`, `COMP-003`, …) become the `Issue.rule_id` (ARC-004) and the test IDs.
- Done: (c67f983: `.specs/business-rules/` with 81 rules and 27 protocol/code gaps; note the `desc_simples` trailing-period contradiction G-07 as an open decision)

### DOC-003 · i18n catalog quality
- Priority: P1 · Effort: M · Status: open
- Where: `static/locales/{pt_BR,en_US}/messages.json` — missing keys in en_US, demo leftovers, no
  naming convention, no placeholders documentation, no parity test, messages hard-coded in code
  (ARC-005).
- Proposed fix: key convention `<area>.<rule_id>.<kind>` (e.g. `rule.DESC-004.error`), one JSON per
  locale generated/validated by `tools/i18n_check.py` (parity, unused, placeholders), CI job.
- Related: BUG-016
- Done (partial, via BUG-016): parity restored (`en_US` no longer missing the 4
  `validator_structure_error_*` keys) and the 18 unused calculator-demo keys purged from both
  catalogs; `tests/unit/i18n/test_catalog_parity.py` now guards key-set, placeholder, and
  `{"message": str}`-shape parity in CI. Still open: the `<area>.<rule_id>.<kind>` naming
  convention/migration, the mixed-prefix cleanup (`fs_utils_*`, `validator_structure_*`,
  `verification_name_*`, `model_report_*`), and moving hard-coded pt-BR strings into the catalog
  (ARC-005) — this item stays `open`.
- Note (Phase 3 Port 2 slice, ARC-017): the `rule.<rule-id>.<kind>` naming convention (the
  `rule.` variant of this item's proposed `<area>.<rule_id>.<kind>`, already used by
  `.specs/business-rules/README.md`'s "Target message keys follow `rule.<RULE-ID>.<error|
  warning>`" line) is now in actual use, not just documented: DESC-001…010 (`rules/
  description.py`) added 16 keys — one `rule.description.missing_required_column` shared by
  every rule's "required column is missing" abort case (one message template, several rules and
  severities), and one-or-more `rule.DESC-0XX.<slug>` keys per rule for each distinct message
  template that rule emits (e.g. DESC-002's `non_numeric`/`must_start_at_one`/
  `must_be_sequential`; DESC-008's `end`/`start`/`anywhere`). Every key added to both
  `pt_BR`/`en_US` in the same change, pt-BR text copied verbatim from the deleted
  `description_validator.py`'s f-strings. This item stays `open` — every other domain
  (composition, values, temporal reference, scenarios, legend, proportionality) still hard-codes
  its messages.

### DOC-004 · API docs
- Priority: P2 · Effort: S · Status: open
- Where: `docs/**` pdoc output committed; docstring styles mixed (NumPy in validators, Google in
  helpers, Sphinx `:ivar:` in `facade.py`), several docstrings in Portuguese (`facade.py`,
  `scanner.py`, `spellchecker*.py`).
- Proposed fix: Google style everywhere (documented in `coding-standards.md`), English only, pdoc in
  CI to Pages.

### DOC-005 · Changelog
- Priority: P2 · Effort: S · Status: done
- Where: `CHANGELOG.md` has `[0.7.XX] - 2026-02-20` placeholder and duplicated bullets.
- Proposed fix: Keep-a-Changelog with an `Unreleased` section maintained per PR; automation in the
  release workflow (TOOL-005).
- Done: CHANGELOG rewritten, Unreleased section

### DOC-006 · Protocol versioning
- Priority: P2 · Effort: S · Status: done
- Where: `assets/protocolo-1.0.pdf`, `assets/protocolo-v-1.13.pdf`; the validator does not know
  which protocol version it implements; `--protocol` CLI flag is free text.
- Proposed fix: `PROTOCOL_VERSION = "1.13"` constant surfaced in reports and `--version`;
  `.specs/business-rules/protocol-changelog.md`.
- Done: `MetadataInfo.PROTOCOL_VERSION`/`__protocol_version__ = "1.16"` (matching the current
  protocol document per `.specs/business-rules/protocol-changelog.md`, not the historical v1.13
  baseline); surfaced in the HTML report's version line (`&ndash; Protocolo {protocol_version}`,
  suppressed together with the rest of the line by `--no-version`). The `--protocol` CLI
  flag/`--version` output are unrelated free-text/tool-version fields and are unchanged — see the
  spec for the distinction and the "how to version the protocol in the tool" section.

### DOC-007 · Portuguese/English mix in code comments
- Priority: P3 · Effort: S · Status: open
- Where: `helpers/tools/data_loader/**`, `helpers/tools/spellchecker/**`, `scripts/*.sh`,
  `pyproject.toml` (black comments in Portuguese).
- Proposed fix: English for code, comments, docs and commit messages; Portuguese only inside message
  catalogs and user-facing report text.
