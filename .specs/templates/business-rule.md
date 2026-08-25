# <SHEET-NNN> · <Short title>

| Field | Value |
|---|---|
| Rule ID | `<SHEET-NNN>` |
| Sheet | `<stem>` (+ related sheets) |
| Category (NamesEnum today) | `<NamesEnum member>` → `<verification_name_*>` |
| Severity | `error` \| `warning` |
| Protocol | §<section> (v1.13) or `—` (implementation rule, see open-questions) |
| Implemented by (today) | `<file>::<Class.method>` |
| Target module | `rules/<sheet>/<SHEET-NNN>.py` |
| Tested by | `<tests path>` or `none — TST-001` |
| Requires | `{ "<sheet>": ["<col>", …] }` |
| Depends on | `<rule IDs>` |
| Option | `--no-…` flag that disables it, if any |

## Statement
<One or two imperative sentences: what must be true of the data.>

## Detection
<Precise algorithm or vectorised condition; how row/column are determined; edge cases (empty,
`DI`, scenarios absent, double header).>

## Messages
| Key | pt_BR | en_US | Placeholders |
|---|---|---|---|
| `rule.<SHEET-NNN>.<severity>` | `<current pt-BR text>` | `<English text>` | `{sheet}, {row}, …` |

## Examples
| Input | Expected issue |
|---|---|
| `<minimal example>` | `<row/column/params>` |

## Notes
<Known deviations from the protocol, history, backlog links.>
