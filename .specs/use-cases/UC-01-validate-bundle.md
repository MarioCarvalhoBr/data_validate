# UC-01 · Validate a bundle from the command line

- Primary actor: sector analyst
- Goal: know whether the bundle complies with Protocol v1.13 and what to fix

## Preconditions
- The bundle folder contains `descricao`, `composicao`, `valores`, `referencia_temporal`
  (`.csv` with `|` or `.xlsx`) and optionally `proporcionalidades`, `cenarios`, `legenda`,
  `dicionario`.
- Python ≥ 3.12 and `canoa-data-validate` installed (`pipx install canoa-data-validate`).

## Main flow
1. Analyst runs `canoa-data-validate --input ./bundle --output ./out --locale pt_BR`
   (today: `--input_folder ./bundle --output_folder ./out -l pt_BR`).
2. The tool loads the sheets, normalises them, runs all rules in category order.
3. The tool writes `out/bundle_report.html` (and `.pdf` when requested/available).
4. The tool prints the JSON summary on stdout and exits with `1` if there are errors, `0`
   otherwise (today: always 0).
5. Analyst opens the HTML report, fixes the listed rows/columns, re-runs.

## Alternative flows
- 2a. A required file is missing → `STRUCT-002` error; rules that need that sheet are listed as
  skipped with reason; exit 1.
- 2b. A file cannot be read (encoding, merged cells) → `STRUCT-004` error with the parser
  detail; exit 1.
- 2c. Spell dictionary unavailable → spelling rules skipped with reason
  `engine.skipped.backend_unavailable`; a stderr warning; exit code unaffected.
- 3a. PDF backend missing → HTML only; stderr warning.
- 1a. Invalid arguments or unreadable folder → usage error on stderr, exit 2.

## Postconditions
- Output folder contains the report(s); nothing else on disk is modified (target: no
  `.config/`, no logs unless `--debug`).

## Related
- Rules: all (`../business-rules/`)
- CLI: `../api/cli-contract.md`
- Backlog: SEC-008, ARC-011, BUG-004

Last synced with code: 09279f4
