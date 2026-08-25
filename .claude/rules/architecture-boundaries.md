# Architecture boundaries

Target layering for the migrated code (see
`.specs/architecture/target-architecture.md` for the full picture and the
module-by-module mapping). Respect the dependency direction below even
while the legacy tree still exists alongside it.

## Layers and allowed dependencies

```
cli → app → rules → {loading, normalizing, reporting, i18n, specs}
                              ↓
                            util
```

- `cli`: argument parsing, exit codes, wiring. Depends on `app` only.
- `app`: orchestrates a run (`AppContext`, the pipeline). Depends on
  `rules`, `loading`, `normalizing`, `reporting`, `i18n`, `specs`.
- `rules`: pure validation logic (the `Rule` protocol + registry). Depends
  on `specs` (for `SheetSpec`) and `util`; never on `loading`,
  `normalizing`, or `reporting`.
- `loading` / `normalizing` / `reporting` / `i18n`: single-purpose layers,
  each depending only on `specs` and `util`, never on each other or on
  `rules`.
- `specs`: the `SheetSpec` registry and domain types (`Issue`, `Severity`).
  Depends on nothing else in the package.
- `util`: pure helpers with **no** internal dependencies — if a "util"
  module needs another `data_validate` module, it is not a util module.

A lower layer never imports a higher one. `rules` never imports `reporting`
to format a message; it returns structured `Issue` objects and lets
`reporting` render them.

## Single source of truth

- `SheetSpec` is the only place that defines a sheet's columns, types, and
  required/optional status. No validator or model re-declares column names
  or patterns locally — it imports the spec.
- Every validation rule has a stable rule ID (`DESC-001`, `COMP-003`, …)
  registered in `.specs/business-rules/README.md`; a rule with no ID is not
  ready to merge.

## Test and tooling boundaries

- Nothing under `data_validate/` imports from `tests/` — test-only helpers
  live in `tests/`, not in production modules.
- `tools/` scripts may depend on `data_validate`'s public API
  (`data_validate.validate(...)`, the CLI entry point) only, never on
  internal modules — they are consumers, not part of the package.

## Never do

- Never let `rules` import from `reporting`, `loading`, or `normalizing`.
- Never duplicate a `SheetSpec` column definition outside `specs`.
- Never import from `tests/` in production code.
