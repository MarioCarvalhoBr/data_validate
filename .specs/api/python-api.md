# Python API (target)

Today the package can only be driven through `main()` because every step runs inside a
constructor and reads `sys.argv`. The target exposes a small, typed, side-effect-free API so the
platform, notebooks and tests can call the validator in-process.

## Public surface (`data_validate/__init__.py`)

```python
from data_validate import validate, Options, ValidationResult, Issue, Severity, list_rules, __version__

result = validate(
    folder="data/input/data_ground_truth_01",
    options=Options(locale="pt_BR", spellcheck=True, warn_title_length=True),
)
result.has_errors          # bool
result.errors, result.warnings
for outcome in result.outcomes:
    outcome.rule_id, outcome.status, outcome.issues
```

### `Options`

Frozen dataclass mirroring the CLI: `locale`, `spellcheck`, `warn_title_length`, `rules`,
`skip_rules`, `max_file_size`, `max_rows`, `parallel`, `clock` (injectable), `report_metadata`
(`sector`, `protocol`, `user`, `file`), `show_time`, `show_version`.

### `validate(folder, options) -> ValidationResult`

- Never writes files, never prints, never mutates process state (no `os.environ`, no CWD
  changes, no `.config`).
- Raises `data_validate.errors.InputFolderError` for an unreadable folder and
  `RuleCrashError` when a rule raises; all other findings are `Issue`s inside the result.

### Rendering

```python
from data_validate.reporting import render_html, render_json, render_pdf
html_path = render_html(result, output_dir=Path("out"), locale="pt_BR")
payload = render_json(result, locale="pt_BR")          # dict
```

### Rule introspection

```python
from data_validate import list_rules
for rule in list_rules():        # RuleInfo(rule_id, category, severity, requires, depends_on, doc)
    ...
```

### Stability

- Semantic versioning applies to this surface from 1.0.0; anything under `data_validate.rules.*`
  internals is private.
- `Issue`, `Severity`, `ValidationResult`, `RuleOutcome`, `Options` are the only dataclasses
  exported; their fields are documented in `../architecture/error-model.md`.

### Usage in tests

`tests/factories.py` builds in-memory bundles (`BundleBuilder().with_description(...).build()`)
that can be passed to `validate_frames(frames, options)` — the same function the pipeline calls
after loading — so rule tests never touch the filesystem.

Last synced with code: 09279f4
