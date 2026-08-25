# Packaging

| Item | Value |
|---|---|
| Distribution name | `canoa_data_validate` (PyPI: `canoa-data-validate`) |
| Import package | `data_validate` |
| Build system | Poetry (`poetry-core`), `pyproject.toml` `[project]` table (PEP 621) |
| Console script | `canoa-data-validate = data_validate.main:main` (target: `data_validate.cli:main`) |
| Python | `>=3.12,<4.0` (drop the `!=3.14.1` exclusion once verified — TOOL-003) |
| Licence | MIT, © INPE |
| Version source | `pyproject.toml` only; runtime via `importlib.metadata.version("canoa_data_validate")` (TOOL-005) |

## Runtime dependencies

`pandas`, `chardet`, `pyenchant`, `pdfkit`, `babel`, `jinja2`, `networkx`, `python-calamine`.
`pandas-stubs` moves to the dev group (TOOL-003).

### Target extras

| Extra | Adds | Enables |
|---|---|---|
| `pdf` | `weasyprint` | PDF rendering (`--format pdf`) |
| `spell` | `pyenchant` | hunspell-backed spell-check; without it the pure-Python fallback is used |
| `fast` | `pyarrow` | Arrow-backed strings for large bundles |

Core install then has no C-extension system requirements beyond pandas.

## Package data

`data_validate/static/**` (locales, report template + CSS, hunspell dictionaries,
`extra-words.dic`) ships inside the wheel (Poetry includes package data by default). The package
must be treated as **read-only at runtime** (BUG-022): personal spell dictionaries go to a
`tempfile` directory; locale is never persisted.

## System dependencies (documented in README)

| Feature | Linux (apt) | Windows | macOS |
|---|---|---|---|
| Spell-check (enchant backend) | `enchant-2 hunspell-pt-br hunspell-en-us` | `pyenchant` wheels bundle enchant; dictionaries from `static/dictionaries/hunspell` | `brew install enchant` |
| PDF (current) | `wkhtmltopdf` | installer / `choco install wkhtmltopdf` | `brew install wkhtmltopdf` |
| PDF (target) | `libpango` (WeasyPrint) | GTK runtime | `brew install pango` |

## Build & verify

```
make build          # poetry build → dist/*.whl, *.tar.gz
twine check dist/*
pipx run --spec dist/*.whl canoa-data-validate --version
```

Artefacts are produced by CI (`build` job) and published only by `release.yml`.

Last synced with code: 3dcfdb1
