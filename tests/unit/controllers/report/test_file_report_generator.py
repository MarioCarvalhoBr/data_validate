#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Unit tests for `data_validate.controllers.report.file_report_generator`.

Covers BUG-010: the JSON summary printed to stdout must be built with
`json.dumps`, not `str(dict).replace("'", '"')`, so it stays valid JSON even
when a value contains a quote or a non-ASCII character.

Covers SEC-001: the report template is loaded exclusively from the package
(`PackageLoader`), autoescape is always on, and both untrusted spreadsheet
content and CLI metadata are rendered through `{{ }}` (never pre-built HTML
strings), so a `<script>` payload renders as inert, escaped text.

Covers ARC-016: `ReportModel`/`ReportSection` (plain values) replace the old
`Dict[str, Any]` built by the now-deleted `_build_template_variables`.

Covers SEC-002: PDF generation tries WeasyPrint first, falls back to the
legacy `pdfkit`/`wkhtmltopdf` path, and skips (without failing the run) when
neither backend is available.
"""

from __future__ import annotations

import builtins
import json
import subprocess
import sys

import jinja2
import pytest
from jinja2 import Environment, PackageLoader, select_autoescape

from data_validate.controllers.report import file_report_generator as file_report_generator_module
from data_validate.controllers.report.file_report_generator import FileReportGenerator
from data_validate.controllers.report.report_model import ReportModel, ReportSection


def _build_generator(
    mocker,
    error_count: int,
    warning_count: int,
    total_tests: int,
    spatial_data_validated: bool = False,
) -> FileReportGenerator:
    """Build a `FileReportGenerator` without running its I/O-heavy `__init__`."""
    generator = FileReportGenerator.__new__(FileReportGenerator)
    generator.context = mocker.MagicMock()
    generator.context.spatial_data_validated = spatial_data_validated
    generator.error_count = error_count
    generator.warning_count = warning_count
    generator.total_tests = total_tests
    return generator


def _real_environment() -> Environment:
    """Build the same `Environment` `FileReportGenerator.__init__` builds (SEC-001)."""
    return Environment(
        loader=PackageLoader("data_validate", "static/report"),
        autoescape=select_autoescape(["html"]),
    )


class TestPrintJsonSummary:
    """Test suite for `FileReportGenerator._print_json_summary`."""

    def test_print_json_summary_is_valid_json_with_quote_and_non_ascii_version(self, mocker, capsys) -> None:
        """BUG-010: a version containing a quote/non-ASCII char must still yield parseable JSON."""
        generator = _build_generator(mocker, error_count=2, warning_count=1, total_tests=10)

        fake_metadata = mocker.MagicMock()
        fake_metadata.__version__ = '1.0.0"-café'
        mocker.patch.object(file_report_generator_module, "METADATA", fake_metadata)

        generator._print_json_summary()

        captured = capsys.readouterr()
        fragment = captured.out.strip()
        assert fragment.startswith("<") and fragment.endswith(">")

        payload = json.loads(fragment[1:-1])
        assert payload == {
            "data_validate": {
                "version": '1.0.0"-café',
                "spatial_data_validated": False,
                "report": {"errors": 2, "warnings": 1, "tests": 10},
            }
        }

    def test_print_json_summary_matches_previous_fragment_shape_for_plain_version(self, mocker, capsys) -> None:
        """The printed fragment keeps the same shape/spacing for a version with no special characters."""
        generator = _build_generator(mocker, error_count=0, warning_count=3, total_tests=34)

        fake_metadata = mocker.MagicMock()
        fake_metadata.__version__ = "1.2.3"
        mocker.patch.object(file_report_generator_module, "METADATA", fake_metadata)

        generator._print_json_summary()

        captured = capsys.readouterr()
        fragment = captured.out.strip()

        summary = {
            "data_validate": {
                "version": "1.2.3",
                "spatial_data_validated": False,
                "report": {"errors": 0, "warnings": 3, "tests": 34},
            }
        }
        # `str(dict).replace("'", '"')` (the original BUG-010 regression-test trick) renders a
        # Python bool as `False`/`True`, not the lowercase `false`/`true` JSON requires, now that
        # `spatial_data_validated` is a bool field (PROTO-018) -- `json.dumps` (the same
        # serialisation `_print_json_summary` itself uses) is the correct way to build the
        # expected fragment for a summary that is no longer string/int leaves only.
        expected = f"<{json.dumps(summary, ensure_ascii=False)}>"

        assert fragment == expected


class TestBuildReportModel:
    """Test suite for `FileReportGenerator._build_report_model` (ARC-016, DOC-006)."""

    @staticmethod
    def _build_generator_for_model(mocker) -> FileReportGenerator:
        generator = _build_generator(mocker, error_count=0, warning_count=0, total_tests=0)
        generator.context.data_args.data_action.no_time = True
        generator.context.data_args.data_report.sector = None
        generator.context.data_args.data_report.protocol = None
        generator.context.data_args.data_report.user = None
        generator.context.data_args.data_report.file = None
        return generator

    def test_version_line_includes_validator_version_and_protocol_version(self, mocker) -> None:
        """DOC-006: the report header surfaces both the validator and the protocol version."""
        generator = self._build_generator_for_model(mocker)
        generator.context.data_args.data_action.no_version = False

        fake_metadata = mocker.MagicMock()
        fake_metadata.__version__ = "0.7.65"
        fake_metadata.__protocol_version__ = "1.16"
        fake_metadata.__project_name__ = "Canoa"
        mocker.patch.object(file_report_generator_module, "METADATA", fake_metadata)

        report_model = generator._build_report_model([], [])

        assert isinstance(report_model, ReportModel)
        assert report_model.show_version is True
        assert report_model.version == "0.7.65"
        assert report_model.protocol_version == "1.16"

    def test_show_version_false_when_no_version_flag_set(self, mocker) -> None:
        """`--no-version` sets `show_version=False`; the template hides the whole line."""
        generator = self._build_generator_for_model(mocker)
        generator.context.data_args.data_action.no_version = True

        fake_metadata = mocker.MagicMock()
        fake_metadata.__version__ = "0.7.65"
        fake_metadata.__protocol_version__ = "1.16"
        fake_metadata.__project_name__ = "Canoa"
        mocker.patch.object(file_report_generator_module, "METADATA", fake_metadata)

        report_model = generator._build_report_model([], [])

        assert report_model.show_version is False

    def test_sections_carry_test_name_errors_and_warnings(self, mocker) -> None:
        """Every report becomes one `ReportSection`, in iteration order."""
        generator = self._build_generator_for_model(mocker)
        generator.context.data_args.data_action.no_version = True

        report_a = mocker.MagicMock(test_name="Categoria A", errors=["erro 1"], warnings=[])
        report_b = mocker.MagicMock(test_name="Categoria B", errors=[], warnings=["aviso 1", "aviso 2"])

        report_model = generator._build_report_model([report_a, report_b], [])

        assert report_model.sections == (
            ReportSection(title="Categoria A", errors=("erro 1",), warnings=()),
            ReportSection(title="Categoria B", errors=(), warnings=("aviso 1", "aviso 2")),
        )

    def test_optional_metadata_fields_pass_through_as_plain_values(self, mocker) -> None:
        """`sector`/`protocol`/`user`/`file` are raw values, not pre-built HTML fragments."""
        generator = self._build_generator_for_model(mocker)
        generator.context.data_args.data_action.no_version = True
        generator.context.data_args.data_report.sector = "Setor A"
        generator.context.data_args.data_report.user = "<img src=x onerror=alert(1)>"

        report_model = generator._build_report_model([], [])

        assert report_model.sector == "Setor A"
        assert report_model.user == "<img src=x onerror=alert(1)>"
        assert report_model.protocol is None
        assert report_model.file is None


class TestBuildReportEndToEnd:
    """Exercises `__init__`/`build_report`'s full success path against a real filesystem.

    Every other test in this module bypasses `__init__` (`FileReportGenerator.__new__`) to
    avoid its I/O; this class builds a real instance instead, so the `PackageLoader`
    wiring (SEC-001) and the HTML-writing/JSON-summary happy path are exercised end to end,
    not just their exception branches.
    """

    def test_build_report_writes_html_and_prints_summary(self, mocker, tmp_path, capsys) -> None:
        from data_validate.controllers.report.validation_report import ReportItem, ValidationReport

        context = mocker.MagicMock()
        context.language_manager.current_language = "pt_BR"
        context.data_args.data_file.input_folder = str(tmp_path / "input")
        context.data_args.data_file.output_folder = str(tmp_path / "output")
        context.data_args.data_action.no_spellchecker = True
        context.data_args.data_action.no_warning_titles_length = False
        context.data_args.data_report.sector = None
        context.data_args.data_report.protocol = None
        context.data_args.data_report.user = None
        context.data_args.data_report.file = None
        context.config.REPORT_LIMIT_N_MESSAGES = 20
        context.config.REPORT_OUTPUT_REPORT_HTML = "_report.html"
        context.config.get_verify_names.return_value = {"verification_name_spelling": "Ortografia"}
        context.file_system_utils.get_last_directory_name.return_value = "bundle"
        (tmp_path / "output").mkdir(parents=True, exist_ok=True)

        report_list = ValidationReport(context=context)
        report_list.add_report(ReportItem(test_name="Categoria A", errors=["<script>alert(1)</script>"]))

        generator = FileReportGenerator(context=context)
        mocker.patch.object(generator, "_save_pdf_file")

        generator.build_report(report_list)

        output_html_path = tmp_path / "output" / "bundle_report.html"
        assert output_html_path.is_file()
        html_content = output_html_path.read_text(encoding="utf-8")
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html_content
        assert "Ortografia" in html_content  # --no-spellchecker's skipped-test label

        captured = capsys.readouterr()
        assert '"errors": 1' in captured.out


class TestResolveReportPath:
    """SEC-010: `_resolve_report_path` builds the output path with `pathlib` and refuses to
    write outside the resolved output directory (defence in depth)."""

    @staticmethod
    def _build_generator_with_output_folder(mocker, output_folder: str) -> FileReportGenerator:
        generator = FileReportGenerator.__new__(FileReportGenerator)
        generator.context = mocker.MagicMock()
        generator.output_folder = output_folder
        return generator

    def test_resolve_report_path_builds_expected_path_inside_output_dir(self, mocker, tmp_path) -> None:
        """The happy path: `file_name + suffix` under the output directory."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        generator = self._build_generator_with_output_folder(mocker, str(output_dir))

        result = generator._resolve_report_path("bundle", "_report.html")

        assert result == str((output_dir / "bundle_report.html").resolve())

    def test_resolve_report_path_raises_when_file_name_escapes_output_dir(self, mocker, tmp_path) -> None:
        """A `file_name` containing `..` that would land outside the output dir is refused."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        generator = self._build_generator_with_output_folder(mocker, str(output_dir))

        with pytest.raises(ValueError, match="output directory"):
            generator._resolve_report_path("../escape", "_report.html")

    def test_build_report_propagates_containment_guard_failure(self, mocker, tmp_path) -> None:
        """`build_report` surfaces the guard's `ValueError` when `get_last_directory_name`
        (the source of `file_name`) returns a value crafted to escape the output directory.

        Not caught by `build_report`'s `except (OSError, TemplateError)` clause (SEC-004): a
        `ValueError` here is treated as an unexpected programming/security-relevant error and
        propagates to `main()`'s boundary.
        """
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        generator = FileReportGenerator.__new__(FileReportGenerator)
        generator.context = mocker.MagicMock()
        generator.error_count = 0
        generator.warning_count = 0
        generator.total_tests = 0
        generator.locale = "pt_BR"
        generator.input_folder = "/input"
        generator.output_folder = str(output_dir)
        generator.context.file_system_utils.get_last_directory_name.return_value = "../escape"
        generator.context.config.REPORT_OUTPUT_REPORT_HTML = "_report.html"
        generator.context.data_args.data_action.no_spellchecker = False
        generator.context.data_args.data_action.no_warning_titles_length = False

        report_list = mocker.MagicMock()
        report_list.get_total_errors.return_value = 0
        report_list.get_total_warnings.return_value = 0
        report_list.flatten.return_value = mocker.MagicMock()
        report_list.reports = {}

        mocker.patch.object(generator, "_render_html", return_value="<html></html>")

        with pytest.raises(ValueError, match="output directory"):
            generator.build_report(report_list)


class TestXssEscaping:
    """SEC-001: untrusted spreadsheet content and CLI metadata must render as inert text."""

    def _render(self, report_model: ReportModel) -> str:
        template = _real_environment().get_template("report_template.html")
        return template.render(report=report_model)

    def _base_model(self, **overrides) -> ReportModel:
        defaults: dict = {
            "name": "Canoa",
            "error_count": "0",
            "warning_count": "0",
            "total_tests": 1,
            "sections": (),
            "skipped_tests": (),
            "show_date": False,
            "date_now": "",
            "show_version": False,
            "version": "",
            "os_name": "",
            "protocol_version": "",
            "sector": None,
            "protocol": None,
            "user": None,
            "file": None,
        }
        defaults.update(overrides)
        return ReportModel(**defaults)

    def test_script_tag_in_a_message_is_escaped(self) -> None:
        """A cell-derived message containing `<script>` renders escaped, never as a raw tag."""
        payload = "<script>alert(1)</script>"
        model = self._base_model(
            sections=(ReportSection(title="Descrição", errors=(payload,), warnings=()),),
        )

        html = self._render(model)

        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
        assert "<script>alert(1)</script>" not in html

    def test_cli_user_metadata_is_escaped(self) -> None:
        """`--user`/`--sector`/`--protocol`/`--file` are escaped exactly like cell content."""
        model = self._base_model(
            user="<img src=x onerror=alert(1)>",
            sector="<b>Setor</b>",
            protocol="Protocolo",
            file="arquivo.xlsx",
        )

        html = self._render(model)

        assert "&lt;img src=x onerror=alert(1)&gt;" in html
        assert "<img src=x onerror=alert(1)>" not in html
        assert "&lt;b&gt;Setor&lt;/b&gt;" in html
        assert "<b>Setor</b>" not in html

    def test_skipped_test_name_is_escaped(self) -> None:
        """A skipped-test label (also localized-string-derived) is escaped like any other value."""
        model = self._base_model(skipped_tests=("<script>alert(2)</script>",))

        html = self._render(model)

        assert "&lt;script&gt;alert(2)&lt;/script&gt;" in html
        assert "<script>alert(2)</script>" not in html

    def test_template_loads_only_from_the_package_directory(self) -> None:
        """SEC-001: the loader is a `PackageLoader`, never a `FileSystemLoader` over the output dir."""
        env = _real_environment()

        assert isinstance(env.loader, PackageLoader)


class TestBuildReportExceptionHandling:
    """SEC-004: `build_report`'s except clause narrows to `(OSError, jinja2.TemplateError)`."""

    @staticmethod
    def _build_generator_for_build_report(mocker) -> FileReportGenerator:
        generator = _build_generator(mocker, error_count=0, warning_count=0, total_tests=0)
        generator.input_folder = "/input"
        generator.output_folder = "/output"
        generator.locale = "pt_BR"
        generator.context.file_system_utils.get_last_directory_name.return_value = "bundle"
        generator.context.config.REPORT_OUTPUT_REPORT_HTML = "_report.html"
        generator.context.data_args.data_action.no_spellchecker = False
        generator.context.data_args.data_action.no_warning_titles_length = False
        return generator

    @staticmethod
    def _fake_report_list(mocker):
        report_list = mocker.MagicMock()
        report_list.get_total_errors.return_value = 0
        report_list.get_total_warnings.return_value = 0
        report_list.flatten.return_value = mocker.MagicMock()
        report_list.reports = {}
        return report_list

    def test_build_report_catches_template_error(self, mocker, capsys) -> None:
        """A template-rendering failure is reported, not raised."""
        generator = self._build_generator_for_build_report(mocker)
        report_list = self._fake_report_list(mocker)
        mocker.patch.object(generator, "_render_html", side_effect=jinja2.TemplateError("bad template"))

        generator.build_report(report_list)

        captured = capsys.readouterr()
        assert "Error creating HTML report" in captured.err
        generator.context.logger.info.assert_called_once()

    def test_build_report_catches_os_error(self, mocker, capsys) -> None:
        """A filesystem failure surfacing from the report pipeline is reported, not raised."""
        generator = self._build_generator_for_build_report(mocker)
        report_list = self._fake_report_list(mocker)
        mocker.patch.object(generator, "_render_html", side_effect=OSError("disk full"))

        generator.build_report(report_list)

        captured = capsys.readouterr()
        assert "Error creating HTML report" in captured.err

    def test_build_report_propagates_unexpected_error(self, mocker) -> None:
        """A programming error that is neither `OSError` nor `jinja2.TemplateError` propagates."""
        generator = self._build_generator_for_build_report(mocker)
        report_list = self._fake_report_list(mocker)
        mocker.patch.object(generator, "_render_html", side_effect=ValueError("boom"))

        with pytest.raises(ValueError, match="boom"):
            generator.build_report(report_list)


class TestSaveHtmlFileExceptionHandling:
    """SEC-004: `_save_html_file` catches only `OSError`."""

    def test_save_html_file_catches_os_error(self, mocker, capsys) -> None:
        mocker.patch("builtins.open", side_effect=OSError("disk full"))
        logger = mocker.MagicMock()

        FileReportGenerator._save_html_file("<html></html>", "/out/report.html", logger)

        captured = capsys.readouterr()
        assert "Error saving HTML report" in captured.err
        logger.error.assert_called_once()

    def test_save_html_file_propagates_unexpected_error(self, mocker) -> None:
        mocker.patch("builtins.open", side_effect=ValueError("boom"))
        logger = mocker.MagicMock()

        with pytest.raises(ValueError, match="boom"):
            FileReportGenerator._save_html_file("<html></html>", "/out/report.html", logger)


class TestSavePdfFileExceptionHandling:
    """SEC-002/SEC-004: `_save_pdf_file` tries WeasyPrint, then `pdfkit`, then skips."""

    def test_save_pdf_file_uses_weasyprint_when_available(self, mocker) -> None:
        """WeasyPrint is tried first; when it succeeds, `pdfkit` is never imported."""
        fake_html_instance = mocker.MagicMock()
        fake_html_class = mocker.MagicMock(return_value=fake_html_instance)
        fake_weasyprint = mocker.MagicMock(HTML=fake_html_class)
        mocker.patch.dict(sys.modules, {"weasyprint": fake_weasyprint})
        logger = mocker.MagicMock()

        FileReportGenerator._save_pdf_file("/out/report.html", logger)

        fake_html_class.assert_called_once_with(filename="/out/report.html")
        fake_html_instance.write_pdf.assert_called_once_with("/out/report.pdf")
        logger.info.assert_called_once()

    def test_save_pdf_file_catches_os_error_from_weasyprint(self, mocker, capsys) -> None:
        fake_html_instance = mocker.MagicMock()
        fake_html_instance.write_pdf.side_effect = OSError("bad font")
        fake_weasyprint = mocker.MagicMock(HTML=mocker.MagicMock(return_value=fake_html_instance))
        mocker.patch.dict(sys.modules, {"weasyprint": fake_weasyprint})
        logger = mocker.MagicMock()

        FileReportGenerator._save_pdf_file("/out/report.html", logger)

        captured = capsys.readouterr()
        assert "Error creating PDF report" in captured.err

    def test_save_pdf_file_falls_back_to_pdfkit_when_weasyprint_import_raises_os_error(self, mocker) -> None:
        """WeasyPrint installed but its native pango/cairo libs are missing: falls back to `pdfkit`."""
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "weasyprint":
                raise OSError("cannot load library 'libpango-1.0.so.0'")
            return real_import(name, *args, **kwargs)

        mocker.patch("builtins.__import__", side_effect=fake_import)
        fake_pdfkit = mocker.MagicMock()
        mocker.patch.dict(sys.modules, {"pdfkit": fake_pdfkit})
        logger = mocker.MagicMock()

        FileReportGenerator._save_pdf_file("/out/report.html", logger)

        fake_pdfkit.from_file.assert_called_once()

    def test_save_pdf_file_falls_back_to_pdfkit_when_weasyprint_missing(self, mocker) -> None:
        """No WeasyPrint installed: falls back to the legacy `pdfkit` compatibility path."""
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "weasyprint":
                raise ImportError("No module named 'weasyprint'")
            return real_import(name, *args, **kwargs)

        mocker.patch("builtins.__import__", side_effect=fake_import)
        fake_pdfkit = mocker.MagicMock()
        mocker.patch.dict(sys.modules, {"pdfkit": fake_pdfkit})
        logger = mocker.MagicMock()

        FileReportGenerator._save_pdf_file("/out/report.html", logger)

        fake_pdfkit.from_file.assert_called_once()

    def test_save_pdf_file_skips_when_no_backend_available(self, mocker, capsys) -> None:
        """Neither WeasyPrint nor `pdfkit` installed: PDF is skipped, not fatal."""
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name in ("weasyprint", "pdfkit"):
                raise ImportError(f"No module named '{name}'")
            return real_import(name, *args, **kwargs)

        mocker.patch("builtins.__import__", side_effect=fake_import)
        logger = mocker.MagicMock()

        FileReportGenerator._save_pdf_file("/out/report.html", logger)

        captured = capsys.readouterr()
        assert "PDF generation skipped" in captured.err
        assert "[pdf]" in captured.err

    def test_save_pdf_file_catches_os_error_from_pdfkit(self, mocker, capsys) -> None:
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "weasyprint":
                raise ImportError("No module named 'weasyprint'")
            return real_import(name, *args, **kwargs)

        mocker.patch("builtins.__import__", side_effect=fake_import)
        fake_pdfkit = mocker.MagicMock()
        fake_pdfkit.from_file.side_effect = OSError("wkhtmltopdf exited with non-zero code")
        mocker.patch.dict(sys.modules, {"pdfkit": fake_pdfkit})
        logger = mocker.MagicMock()

        FileReportGenerator._save_pdf_file("/out/report.html", logger)

        captured = capsys.readouterr()
        assert "Error creating PDF report" in captured.err

    def test_save_pdf_file_propagates_unexpected_error_from_pdfkit(self, mocker) -> None:
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "weasyprint":
                raise ImportError("No module named 'weasyprint'")
            return real_import(name, *args, **kwargs)

        mocker.patch("builtins.__import__", side_effect=fake_import)
        fake_pdfkit = mocker.MagicMock()
        fake_pdfkit.from_file.side_effect = TypeError("boom")
        mocker.patch.dict(sys.modules, {"pdfkit": fake_pdfkit})
        logger = mocker.MagicMock()

        with pytest.raises(TypeError, match="boom"):
            FileReportGenerator._save_pdf_file("/out/report.html", logger)


class TestLazyPdfImports:
    """PERF-008: `pdfkit`/`weasyprint` must not be imported by merely importing this module.

    Both are heavy/optional dependencies needed only by `_save_pdf_file`'s HTML→PDF
    conversion; HTML-only flows (or a process that never reaches PDF generation) must not
    pay their import cost.
    """

    def test_module_import_does_not_import_pdf_backends(self) -> None:
        """Importing the module alone, in a fresh subprocess, must not import either backend."""
        result = subprocess.run(  # noqa: S603
            [
                sys.executable,
                "-c",
                "import data_validate.controllers.report.file_report_generator; "
                "import sys; "
                "assert 'pdfkit' not in sys.modules, sys.modules.keys(); "
                "assert 'weasyprint' not in sys.modules, sys.modules.keys()",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
