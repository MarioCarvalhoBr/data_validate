# Territories — optional server registry `spd_data.json`

Source: **maintainer decisions, 2026-09-12** (authoritative), example file
`local_data/ULTIMA_IMPLEMENTACAO/spd_data.json`. The Canoa **server** generates this file and may
pass it alongside the bundle. Three decisions define the semantics:

1. **Own verification category** — the territory check is a first-class verification with its own
   report title (a new `NamesEnum`-style member, working name `TERR` /
   `verification_name_territory_registry`) and its own title + message keys in **both** locale
   catalogs. It is never folded into an existing category.
2. **Triggered only when `spd_data.json` is present** in the input folder. When the file is
   absent, the verification appears in the report as **skipped / not executed** — never as an
   error, never silently missing (skipped-with-reason in the target engine, ADR-0006).
3. **Findings are always errors** (`Severity.ERROR`), never warnings: a `valores` or
   `proporcionalidades` id that does not exist in the registry is an error.

Protocol basis: v1.16 §2.6 (p.11) requires the `id` column of `valores` to reference the spatial
representation ("deverão ter todos os objetos descritos no shapefile ou, no caso de dados para
todo o Brasil, todos os municípios brasileiros"); §3.2 delivers the spatial data itself to the
platform administrator and §3 states those deliverables are not used in validation. The registry
JSON artefact is therefore **not specified in the protocol PDF** — it is the server-side bridge
the maintainer defined so Canoa can enforce the §2.6 relationship. Note the direction: the TERR
rules below check the spreadsheets' ids are a **subset** of the registry; full **completeness**
(every registry id present in `valores`) remains an open owner decision (gap G-13).

## Artefact

| Property | Value |
|---|---|
| File name | `spd_data.json` (input folder, alongside the sheets) |
| Required | no — optional, server-generated |
| Format | JSON, UTF-8: `{"values": [{"id": int, "name": str, "region": str}, …]}` |
| Loading | through the loading layer only (never parsed ad hoc); untrusted input — size-limited, stdlib `json`, specific exceptions |
| File-structure impact | must be whitelisted so STRUCT-004 does not flag it as "arquivo não esperado" (code change — PROTO-013) |

## Rules

### TERR-001 · Every `valores.id` exists in the territory registry
- Severity: error (maintainer decision — never a warning)
- NamesEnum: new dedicated member `TERR` (`verification_name_territory_registry`) — own report
  category, title registered in both catalogs
- Protocol: v1.16 §2.6 p.11 (relationship); artefact by maintainer decision 2026-09-12
- Statement: when `spd_data.json` is present, every value in the `id` column of `valores` must
  equal the `id` of some entry in the registry's `values` list. Unknown ids are reported per id
  with the row number. When the file is absent, the whole `TERR` verification is reported as
  skipped / not executed.
- Current message (pt-BR): none — new rule; key `rule.TERR-001.error` in both catalogs
- Implemented by: none yet (PROTO-013)
- Covered by tests: none yet — unit + golden fixtures with and without the file

### TERR-002 · Every `proporcionalidades.id` exists in the territory registry
- Severity: error (maintainer decision — never a warning)
- NamesEnum: same dedicated `TERR` category as TERR-001
- Protocol: v1.16 §2.7 pp.12–13 (the first columns carry the spatial representation); artefact by
  maintainer decision 2026-09-12
- Statement: when `spd_data.json` is present, every value in the `id` column (level-2 header) of
  `proporcionalidades` must exist among the registry ids; skipped when the file or the sheet is
  absent.
- Current message (pt-BR): none — new rule; key `rule.TERR-002.error` in both catalogs
- Implemented by: none yet (PROTO-013)
- Covered by tests: none yet — unit + golden fixtures with and without the file

## Registry integrity (pre-checks before the rules run)

Malformed registry (invalid JSON, missing `values`, non-int `id`, duplicate ids) is reported as a
loading error for `spd_data.json` and both TERR rules are skipped — never a crash. Duplicate
registry ids are a registry defect (server-side) and reported as a warning.

Last synced with code: 344fef7

## JSON summary flag: `spatial_data_validated`

Maintainer requirement (2026-09-12): the machine-readable stdout summary
(`<{"data_validate": {...}}>`) gains a boolean field named `spatial_data_validated`
(the English name chosen for "dados_espaciais_validados"):

- `true` — `spd_data.json` was provided, loaded successfully, the TERR verification ran
  and produced **zero errors** (every `valores.id` and `proporcionalidades.id` found in
  the registry).
- `false` — every other case: file absent, file malformed/unreadable, or TERR errors found.

Interpretation note: "passado e validado" is read as "provided AND validation passed";
if the maintainer instead means merely "provided and the check executed", flip the
malformed/errors cases — confirm before implementing PROTO-018. The field sits inside
the `data_validate` object next to `report` (`{"data_validate": {"version": ...,
"spatial_data_validated": false, "report": {...}}}`) and is ALWAYS present so the
platform can rely on its shape. The `--json` file output carries the same field.
Implementation: PROTO-018 (Phase 6, after PROTO-013). Contract change must be mirrored
in `.specs/api/cli-contract.md` (JSON schema) and the golden harness summary parser.
