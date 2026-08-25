---
name: pytest-mock-patterns
description: Use when writing or reviewing tests that need mocking, fixtures, temp files, time control, or CLI subprocess testing. Recipes for pytest-mock (never unittest.mock) matching this project's existing test style.
---

# pytest-mock recipes for data_validate

This project forbids `unittest.mock` and `with patch(...)` context managers entirely — use the
`mocker` fixture (from `pytest-mock`) with direct assignment. See
`tests/unit/helpers/base/test_file_system_utils.py` for the house style this skill formalizes.

## `mocker.patch` vs `mocker.patch.object`

```python
# Patch a name imported into the module under test — patch where it is looked up, not where
# it is defined.
def test_uses_language_manager(self, mocker) -> None:
    mock_lm = mocker.patch("data_validate.helpers.base.file_system_utils.LanguageManager")
    mock_lm.return_value.text.return_value = "mocked_message"
    ...

# Patch one attribute of an already-constructed object (prefer this over re-patching the class
# when you only need to override one method's return value on an instance you built normally).
def test_overrides_one_method(self, mocker, fs_utils) -> None:
    mocker.patch.object(fs_utils, "detect_encoding", return_value=(True, "utf-8"))
    ...
```

## Fixtures that build a context double

```python
@pytest.fixture
def fs_utils(self, mocker) -> FileSystemUtils:
    """Instance with a mocked LanguageManager, matching the constructor's dependency."""
    mocker.patch("data_validate.helpers.base.file_system_utils.LanguageManager")
    fs_utils = FileSystemUtils()
    fs_utils.language_manager = mocker.MagicMock()
    fs_utils.language_manager.text.return_value = "mocked_message"
    return fs_utils
```

For validators, build a `mocker.MagicMock()` for `DataModelContext`/`ValidationReport` and set
only the attributes the method under test reads (`context.data_args.data_action....`,
`get_instance_of(...)`) — do not build a full real context unless testing integration.

## `tmp_path` over manual `tempfile`

Prefer the built-in `tmp_path` fixture for new tests; it needs no manual cleanup:

```python
def test_reads_file(self, tmp_path) -> None:
    file_path = tmp_path / "descricao.csv"
    file_path.write_text("codigo|nivel\n1|1\n", encoding="utf-8")
    ...
```

Use the manual `tempfile.NamedTemporaryFile`/`TemporaryDirectory` pattern (as in
`test_file_system_utils.py`) only when a test needs an existing file *before* the fixture body
runs, or needs to control the path outside `tmp_path`'s tree.

## Clock / time control

No `freezegun` dependency is assumed yet (add it as a dev dependency first if a test needs it).
For code that reads `datetime.now()` directly, prefer refactoring to accept an injected clock
(`Callable[[], datetime]`) over patching `datetime` — patching `datetime.now` requires
`mocker.patch("module.datetime")` with a `MagicMock(now=mocker.Mock(return_value=fixed_dt))`,
which is brittle; injection is simpler to test and matches `coding-standards.md` (explicit deps).

## `capsys` for CLI/stdout assertions

```python
def test_cli_prints_summary(self, capsys) -> None:
    run_cli(["--input_folder", "x", "--output_folder", "y"])
    captured = capsys.readouterr()
    assert "validation summary" in captured.out
```

## Subprocess testing for the CLI (used by `tests/e2e`)

```python
def test_main_exits_zero_on_valid_bundle(self, tmp_path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "data_validate.main", "--input_folder", str(fixture_dir),
         "--output_folder", str(tmp_path), "--no-time", "--no-version"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0
```

Mock only the boundary (network, filesystem outside `tmp_path`, `subprocess` for `wkhtmltopdf`) —
never mock the module under test itself.

## Parametrization

```python
@pytest.mark.parametrize(
    "raw_value, expected",
    [
        pytest.param("1.23", True, id="two_decimals_ok"),
        pytest.param("1.234", False, id="three_decimals_fails"),
        pytest.param("DI", True, id="di_marker_ok"),
    ],
)
def test_check_two_decimals_places(self, raw_value: str, expected: bool) -> None:
    assert NumberFormattingProcessing.check_two_decimals_places(raw_value) is expected
```

Always pass `id=` on non-trivial parameters so failures are readable in CI output.

## `hypothesis` strategies for cell-level parsers

For parsers that must hold an invariant across arbitrary input (e.g. "any string either parses to
a 2-decimal float or is rejected"), add a property-based test once `hypothesis` is a dev
dependency:

```python
from hypothesis import given, strategies as st

@given(st.one_of(st.floats(allow_nan=False), st.text()))
def test_check_numeric_value_never_raises(value) -> None:
    ValueProcessing.check_numeric_value(str(value), 0, "col", "file.csv")  # must not raise
```

Reserve `hypothesis` for pure parsing/formatting functions, not for validators that need a full
DataFrame/context fixture — table-driven `parametrize` is enough there.
