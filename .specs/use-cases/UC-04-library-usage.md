# UC-04 · Use the validator as a Python library

- Primary actor: researcher / integrator (e.g. the platform's ingestion service, a notebook)
- Goal: validate in-process and consume structured results without files or subprocesses

## Preconditions
- `canoa-data-validate` installed in the caller's environment (Phase 1 API, `../api/python-api.md`).

## Main flow
1. Caller builds `Options(locale="en_US", spellcheck=False)`.
2. Caller invokes `result = validate(Path("bundle"), options)`.
3. Caller inspects `result.has_errors`, iterates `result.outcomes` and filters `Issue`s by
   `rule_id`, `sheet`, `severity`.
4. Optionally the caller renders `render_json(result)` or `render_html(result, out_dir)`.

## Alternative flows
- 2a. Folder unreadable → `InputFolderError` raised (not an issue).
- 2b. A rule crashes → `RuleCrashError` raised with the rule ID and traceback; partial results
  are attached to the exception.
- 3a. Caller passes in-memory DataFrames (`validate_frames`) to validate data that never touched
  disk.

## Postconditions
- No side effects on the filesystem, environment variables or global interpreter state; two
  concurrent calls in the same process do not interfere (BUG-002, BUG-004, BUG-022 fixed).

## Related
- Backlog: ARC-001, ARC-002, ARC-004; roadmap Phase 1

Last synced with code: 09279f4
