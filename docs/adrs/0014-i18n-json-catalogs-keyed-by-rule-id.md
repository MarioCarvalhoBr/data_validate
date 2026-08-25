# ADR-0014: i18n via JSON catalogs keyed by rule ID; pt_BR default, en_US required parity

- Status: Accepted (partially implemented)
- Date: 2026-08-25
- Deciders: Mário de Araújo Carvalho (INPE) with the AI orchestrator

## Context

A JSON-catalog i18n mechanism already exists and is partially adopted. `LanguageManager`
(`helpers/tools/locale/language_manager.py`) loads `static/locales/<lang>/messages.json` via
`_load_translations` (lines 53-66) and exposes `text(key, **kwargs)` (lines 101-125), which looks up
`self.translations.get(key)`, expects a `{"message": "..."}` object, and does `str.format(**kwargs)`
for placeholder interpolation, with a fallback string (`f"<Message for '{key}' missing in
'{self.current_language}'>"`, line 114) when a key or its structure is missing. In practice, though,
ARC-005 finds this mechanism used almost nowhere: only `FileSystemUtils` and
`FileStructureValidator` call `language_manager.text()`; every other user-facing message — in
`models/sp_*.py`, every `validators/spreadsheets/*_validator.py`, `helpers/common/**`,
`helpers/tools/spellchecker/**`, the labels built in `controllers/report/file_report_generator.py`
(e.g. `_get_optional_field_text`'s hard-coded `"Setor estrat&eacute;gico"`, `"Protocolo"`,
`"Usu&aacute;rio"`, `"Arquivo submetido"` defaults), and
`spreadsheet_processor.py:98`'s `"Tempo total de execução: " + ...` — is an f-string written
directly in Portuguese. Confirmed by direct inspection: `static/locales/pt_BR/messages.json` has 76
`"message"` entries versus `static/locales/en_US/messages.json`'s 72 — a 4-key gap matching BUG-016's
finding that `en_US` is missing
`validator_structure_error_conflicting_files`,
`validator_structure_error_files_not_in_folder`,
`validator_structure_error_missing_file`, and
`validator_structure_error_unexpected_folder`; both catalogs also carry leftover keys from an
unrelated calculator demo (`welcome`, `menu_title`, `add_option`, per BUG-016), meaning the catalog
mechanism itself works but is neither complete (missing keys) nor clean (dead keys) nor adopted
(≈ 95 % of real messages bypass it entirely).

## Decision

Keep the JSON-catalog approach as the accepted foundation — it is a working, dependency-free
mechanism already wired into `LanguageManager`/`AppContext` — and commit to completing it rather
than replacing it. Two tracks: (1) an **immediate** fix, ahead of the full rule-ID rekey, adds the
4 missing `en_US` keys (BUG-016) and purges the demo leftover keys (`welcome`, `menu_title`,
`add_option`, and any others found by `tools/i18n_check.py`) so pt_BR/en_US parity holds today,
enforced from this point forward by a parity test (`tests/unit/i18n/test_catalog_parity.py` or
equivalent) run in CI; (2) the **structural** completion, carried out per sheet during Phase 3-4
(`08-migration-roadmap.md`) alongside the `Issue`/rule porting (ADR-0004, ADR-0006): every message
key is renamed to the convention `<area>.<rule_id>.<kind>` (e.g. `rule.DESC-004.error`), every
f-string message in `models/`, `validators/`, `helpers/common/**`, `spellchecker/**`, and the report
labels is replaced by a `MessageCatalog` lookup keyed by the `Issue.message_key` the rule produces
(ARC-004/ARC-005 close together), and the report template itself becomes locale-aware rather than
hard-coding `&eacute;`-escaped Portuguese labels. `pt_BR` remains the default locale (matching the
platform's primary audience); `en_US` parity is a hard requirement enforced by CI, not best-effort.

## Consequences

### Positive
- Once complete, adding a new locale or fixing a wording issue is a JSON edit, not a code change —
  no validator needs to be touched to correct a translation.
- The parity test turns "en_US silently drifts behind pt_BR" from an undetected bug (as BUG-016 was
  until this audit) into a CI failure the moment a new pt_BR-only key is added.
- Keying messages by rule ID (`rule.DESC-004.error`) gives `Issue.message_key` a stable, traceable
  link from protocol section → business rule → catalog entry → rendered text (DOC-002's rule-ID
  traceability goal), which the current ad hoc snake_case keys (`validator_structure_error_missing_file`)
  do not provide.

### Negative
- Rekeying every message to `<area>.<rule_id>.<kind>` is a breaking change to the catalog's key
  namespace; must happen in lockstep with the `Issue`/`Rule` porting per sheet (Phase 3-4), not as a
  separate pass, to avoid a period where keys and rule IDs disagree.
- Until the structural track completes, the majority of messages remain hard-coded Portuguese
  f-strings — the golden harness (ADR-0002) is relied upon to keep behaviour stable while this
  large, incremental rewrite proceeds sheet by sheet, and en_US will not have real translations for
  business-rule messages until each sheet's rules are ported.

## Alternatives considered

### Switch to `gettext`/`.po` files instead of JSON
Rejected: `gettext` is a heavier, more specialised i18n toolchain (`.po`/`.mo` compilation, plural-
form rules) than this project needs; the JSON catalog already integrates with the planned
`Issue.params` structured-placeholder model (ADR-0004) more directly — `str.format(**kwargs)`-style
substitution maps cleanly onto `Issue.params`, and the team already has working JSON-catalog code
and tooling (`LanguageManager`) to build on rather than replace.

### Drop the catalog and hard-code messages per rule module, abandon i18n
Rejected: the platform's audience explicitly spans pt_BR (sector teams) and en_US (documented as a
supported locale, with `--locale` accepting both since the current `DataArgs._create_parser`), and
`ARC-005`/`DOC-003` both treat i18n completion as required, not optional; hard-coding would also
permanently block any future locale beyond these two.

### Embed message text directly in `Issue.params`, skip `message_key` lookup entirely
Rejected: this collapses the separation between "what happened" (structured rule output) and "how
it's phrased in a given locale" (translation), which is exactly the separation ADR-0004 introduces
`Issue`/`MessageCatalog` to achieve; it would also make adding or fixing a translation require
touching rule code again, reintroducing the coupling this ADR exists to remove.

## Links

- Backlog: `ARC-005` (`03-architecture.md`); `BUG-016` (`01-bugs.md`); `DOC-003` (`07-docs-i18n.md`);
  `08-migration-roadmap.md` Phase 3 item 2, Phase 4 item 2
- Specs: `.specs/i18n/catalog.md`, `.specs/business-rules/README.md` (rule ID ↔ `NamesEnum` map)
- Related ADRs: ADR-0004 (`Issue.message_key`/`params`), ADR-0005 (unified `Locale` in `AppContext`)

---
Last synced with code: a4f76c7
