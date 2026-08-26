# Open questions

Questions that need a maintainer/protocol decision. Each entry: context, options, who decides,
and the default assumed until answered. Resolved questions move to an ADR or a spec and are
removed here.

### OQ-1 · Is QML (QGIS style) input part of the protocol?
- Context: `helpers/tools/data_loader/readers/qml_reader.py` reads `.qml` files and
  `DataLoaderFacade` stores them under `data["qmls"]`, but nothing consumes them and
  `SpreadsheetInfo.ALLOWED_EXTENSIONS` excludes `.qml`; `FileStructureValidator` reports `.qml`
  files as unexpected. Older fixtures in `local_data/` contain `legenda.qml`.
- Options: (a) drop QML entirely; (b) keep as an optional legend source with its own rules.
- Decides: INPE maintainers (Mário Carvalho, Pedro Andrade).
- Default until answered: (a) — reader removed in Phase 2 (`deprecations.md`).

### OQ-2 · Exact protocol section numbers for each rule
- Context: `business-rules/*.md` cite protocol sections extracted from `assets/protocolo-v-1.13.pdf`.
  Some rules found in code (e.g. level-2/scenario-0 exclusions, `unnamed` column tolerance,
  `Fontes:` stripping in spell-check) have no explicit protocol text.
- Options: document them as "implementation rules" (protocol gap) or add them to protocol v1.14.
- Decides: protocol owners.
- Default: documented as implementation rules with `protocol: —`.

### OQ-3 · Should warnings ever block ingestion?
- Context: today exit code is always 0; the platform decides using counts. Target proposes
  `--fail-on error` default.
- Options: platform keeps deciding from JSON counts (tool exits 1 only on errors) or the platform
  passes `--fail-on warning` for strict sectors.
- Decides: Canoa platform team.
- Default: exit 1 on errors only.

### OQ-4 · Report visual re-baseline timing
- Context: Phase 4 changes message ordering (sorted) and escaping; goldens must be re-baselined
  once. Sector teams may compare reports across versions.
- Options: re-baseline in a single minor release with a CHANGELOG note; or keep insertion order
  forever.
- Decides: maintainers.
- Default: single re-baseline in 0.9.0.

### OQ-5 · PDF backend on the platform server
- Context: WeasyPrint needs pango; wkhtmltopdf is archived. Does the platform actually consume
  the PDF or only the HTML?
- Decides: Canoa platform team.
- Default: HTML primary; PDF optional extra.

### OQ-6 · en_US audience
- Context: en_US catalog exists but is incomplete and no known user runs in English.
- Options: keep parity as a hard CI gate (current plan) or mark en_US best-effort.
- Decides: maintainers.
- Default: parity gate kept (ADR-0014).

### OQ-7 · Minimum supported pandas
- Context: `pandas>=3.0.1` is very recent; some deployment images may pin 2.x.
- Options: support 2.2+ and 3.x (CoW explicitly enabled), or 3.x only.
- Decides: maintainers with the platform ops team.
- Default: 3.x only (ADR-0013).

Last synced with code: 09279f4
