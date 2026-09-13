# Golden harness changelog

Every regeneration of `tests/e2e/golden/*.json` is recorded here: date, fixture(s), reason, and
the commit/PR it shipped with. See `.claude/skills/golden-harness/SKILL.md` for the update
process — regenerate only via `make harness-update`, with the diff reviewed.

## 2026-09-13

- **Fixtures re-baselined**: `data_errors_01` (one line changed, everything else byte-identical).
- **Fixture added**: `data_errors_xss` (new, additive — a `data_ground_truth_01` copy with one
  cell mutated: `descricao`'s row-1 `nome_simples` gets ` <Script>Alert(1)</Script>` appended,
  which breaks `DESC-004`'s ABNT-capitalisation check and surfaces the raw payload verbatim in
  that rule's "Encontrado: '...'" warning text).
- **Reason**: SEC-001 (Phase 4) rebuilt `FileReportGenerator`/`report_template.html` on
  `Environment(loader=PackageLoader(...), autoescape=select_autoescape(["html"]))` (ADR-0007):
  every message/CLI-metadata value is now escaped before being written to the saved HTML report,
  instead of being concatenated as a raw string in Python
  (`FileReportGenerator._format_messages_as_html`, deleted). The golden harness's own extractor
  (`_ReportSectionParser`, an `HTMLParser` with `convert_charrefs=True`) unescapes entities back
  to plain text before comparison, so this change is invisible to the stored JSON goldens **except**
  where a message previously contained a literal `<`/`>` that the pre-fix, non-escaping renderer
  emitted raw into the HTML — the naive `HTMLParser` misread that raw `<...>` as a bogus tag and
  silently dropped its contents from the extracted text. `data_errors_01`'s
  "Estrutura dos arquivos da pasta de entrada" section carries exactly one such case: a corrupt
  `legenda.xlsx` raises `python_calamine.CalamineError`, and the abort message embeds
  `str(type(exc))` (`"...Detalhes: Cannot detect file format (<class 'python_calamine.CalamineError'>)"`).
  Pre-fix, the raw `<class 'python_calamine.CalamineError'>` in the saved HTML was parsed as a
  (bogus) tag and its text silently disappeared, so the *previous* golden recorded the mangled
  `"...format ()"`. Post-fix, the same content is written as
  `&lt;class &#39;python_calamine.CalamineError&#39;&gt;`, which `HTMLParser` correctly unescapes
  back to the full, undamaged message — this is the one and only content diff in
  `data_errors_01.json`, reviewed line-by-line above; no other fixture's extracted section content
  changed at all (`exit_code`, already excluded from the comparison per the 2026-09-12 entry below,
  is the only other field that differs, an artefact of re-running the harness rather than of this
  change).
- **XSS regression evidence** (not itself part of the golden, verified manually and via
  `tests/unit/controllers/report/test_file_report_generator.py::TestXssEscaping`): the raw HTML
  report generated for `data_errors_xss` contains `&lt;Script&gt;Alert(1)&lt;/Script&gt;`, never a
  literal `<Script>` tag.

## 2026-09-12

- **Fixtures**: none regenerated — every `tests/e2e/golden/*.json` file is byte-identical to the
  previous baseline.
- **Reason**: ARC-011/SEC-008 landed the documented exit-code contract (`0` = no errors, `1` =
  validation errors found, `2` = a runtime failure — `.specs/api/cli-contract.md`,
  `docs/adrs/0005-cli-contract-flags-exit-codes-json.md`), replacing the previous "always 0".
  `tests/e2e/test_golden.py::test_golden_report` now asserts the CLI's real exit code against the
  expected value derived from the run's own parsed JSON summary (`0` for `data_ground_truth_01`,
  `1` for every `data_errors_*` fixture) as a dedicated assertion, instead of hardcoding
  `result.returncode == 0` for every fixture.
- **Notes**: every stored golden file still carries `"exit_code": 0` from before this change (the
  field was never meaningful before SEC-008, since the CLI always exited 0). Re-baselining every
  golden purely to update that one stale field was judged unnecessary churn for a value the
  content diff no longer needs: the golden equality comparison now excludes the `exit_code` key
  (the real contract check happens via the dedicated assertion described above, not via the
  golden diff), so the stale `0` values are harmless and require no action until the next
  deliberate `make harness-update`.

## 2026-08-25

- **Fixtures**: all (`data_errors_01`, `data_errors_09`, `data_errors_11`, `data_errors_13`,
  `data_errors_14`, `data_errors_15`, `data_ground_truth_01`).
- **Reason**: initial baseline for the golden harness, generated from v0.7.65 @ d1ae7c1. No prior
  golden existed; this is the safety net the migration (Phase 1 onward) will be diffed against.
- **Notes**: `spell_skipped: true` in every golden — this development environment has `pyenchant`
  installed but no `pt_BR` hunspell word list, so the `SPELL-*` rules were not exercised. Re-running
  `make harness-update` on a machine with `hunspell-pt-br` installed will exercise spelling and
  should be reviewed as a deliberate, separate golden update.
- **Non-determinism found and normalised (harness-side, not a golden change)**: three consecutive
  `make test-e2e` runs showed `data_errors_11` flapping — two "missing required column" messages
  from `value_validator.py` (built from a Python `set` difference) swapped order between process
  runs. `tests/e2e/test_golden.py` now sorts the `errors`/`warnings` lists within each section
  before storing/comparing, so message *order* is not part of the golden's signal — only message
  *presence/text* is. The underlying `set`-ordering issue in the pipeline is unchanged (out of
  scope here; see backlog for a vectorised-columns fix).
