# UC-02 · Generate and read the validation report

- Primary actors: sector analyst (reads), Canoa platform (stores/links)
- Goal: a self-contained, localised document listing every finding with sheet, row and column

## Preconditions
- UC-01 ran (validation result available).

## Main flow
1. The report model groups issues by category in the fixed protocol order, errors before
   warnings, sorted by sheet/row/column.
2. Each category shows at most 20 errors and 20 warnings; extra ones are summarised as
   "N erros omitidos" (`report.omitted.errors`).
3. Header shows project name, optional metadata (`--user`, `--sector`, `--protocol`, `--file`),
   date/time (unless `--no-time`), validator version and OS (unless `--no-version`).
4. Summary shows total errors, total warnings, number of rules executed and the list of skipped
   rules with reasons.
5. HTML is written to `<output>/<bundle-name>_report.html`; PDF to `.pdf` when `--format`
   includes `pdf` and the backend is available.
6. The platform stores the HTML path from the JSON summary (`outputs.html`) and shows it to the
   analyst.

## Alternative flows
- 2a. A cell contains HTML/JS → it is displayed escaped, never executed (SEC-001).
- 5a. Output folder not writable → exit 2 with a clear stderr message.

## Postconditions
- Report is deterministic for the same input (goldens rely on this with `--no-time --no-version`).

## Related
- `../api/report-format.md`, `../frontend/report-ui.md`, `../architecture/error-model.md`
- Backlog: SEC-001, SEC-002, ARC-016, BUG-010

Last synced with code: 09279f4
