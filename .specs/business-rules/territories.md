# Territories — optional server registry `spd_data.json`

Source: **maintainer decision, 2026-09-12** (authoritative), example file
`local_data/ULTIMA_IMPLEMENTACAO/spd_data.json`. The Canoa **server** generates this file and may
pass it alongside the bundle; it is **optional by design** — when absent, the TERR rules are
skipped (recorded as skipped-with-reason in the target engine, ADR-0006).

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
- Severity: error
- NamesEnum: to be assigned when implemented (new verification title; register in both catalogs)
- Protocol: v1.16 §2.6 p.11 (relationship); artefact by maintainer decision 2026-09-12
- Statement: when `spd_data.json` is present, every value in the `id` column of `valores` must
  equal the `id` of some entry in the registry's `values` list. Unknown ids are reported per id
  with the row number. When the file is absent, the rule is skipped.
- Current message (pt-BR): none — new rule; key `rule.TERR-001.error` in both catalogs
- Implemented by: none yet (PROTO-013)
- Covered by tests: none yet — unit + golden fixtures with and without the file

### TERR-002 · Every `proporcionalidades.id` exists in the territory registry
- Severity: error
- NamesEnum: same title as TERR-001
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
