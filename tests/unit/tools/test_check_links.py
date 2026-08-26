#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br).
#  Documentation, source code, and more details about the AdaptaBrasil project are available at:
#  https://github.com/AdaptaBrasil/.

"""Unit tests for tools/check_links.py."""

from __future__ import annotations

from pathlib import Path

from tools import check_links


class TestSlugifyHeading:
    """Test suite for _slugify_heading()."""

    def test_slugify_heading_lowercases_and_hyphenates(self) -> None:
        assert check_links._slugify_heading("Hello World") == "hello-world"

    def test_slugify_heading_strips_punctuation(self) -> None:
        assert check_links._slugify_heading("Section: Overview!") == "section-overview"

    def test_slugify_heading_strips_inline_code_backticks(self) -> None:
        assert check_links._slugify_heading("The `make check` target") == "the-make-check-target"


class TestCheckFile:
    """Test suite for _check_file()."""

    def test_check_file_reports_missing_target(self, tmp_path: Path) -> None:
        source = tmp_path / "a.md"
        source.write_text("[broken](./missing.md)\n", encoding="utf-8")

        broken = check_links._check_file(source, tmp_path)

        assert len(broken) == 1
        assert "missing.md" in broken[0].reason

    def test_check_file_accepts_existing_target(self, tmp_path: Path) -> None:
        (tmp_path / "b.md").write_text("# Target\n", encoding="utf-8")
        source = tmp_path / "a.md"
        source.write_text("[ok](./b.md)\n", encoding="utf-8")

        assert check_links._check_file(source, tmp_path) == []

    def test_check_file_reports_missing_anchor(self, tmp_path: Path) -> None:
        (tmp_path / "b.md").write_text("# Real Heading\n", encoding="utf-8")
        source = tmp_path / "a.md"
        source.write_text("[ok](./b.md#does-not-exist)\n", encoding="utf-8")

        broken = check_links._check_file(source, tmp_path)

        assert len(broken) == 1
        assert "does-not-exist" in broken[0].reason

    def test_check_file_accepts_valid_anchor(self, tmp_path: Path) -> None:
        (tmp_path / "b.md").write_text("# Real Heading\n", encoding="utf-8")
        source = tmp_path / "a.md"
        source.write_text("[ok](./b.md#real-heading)\n", encoding="utf-8")

        assert check_links._check_file(source, tmp_path) == []

    def test_check_file_skips_external_links(self, tmp_path: Path) -> None:
        source = tmp_path / "a.md"
        source.write_text("[ext](https://example.com/missing)\n", encoding="utf-8")

        assert check_links._check_file(source, tmp_path) == []

    def test_check_file_in_page_anchor_resolves(self, tmp_path: Path) -> None:
        source = tmp_path / "a.md"
        source.write_text("# My Section\n\n[here](#my-section)\n", encoding="utf-8")

        assert check_links._check_file(source, tmp_path) == []

    def test_check_file_in_page_anchor_missing(self, tmp_path: Path) -> None:
        source = tmp_path / "a.md"
        source.write_text("# My Section\n\n[here](#not-a-section)\n", encoding="utf-8")

        broken = check_links._check_file(source, tmp_path)

        assert len(broken) == 1

    def test_check_file_ignores_image_links(self, tmp_path: Path) -> None:
        source = tmp_path / "a.md"
        source.write_text("![alt](./missing.png)\n", encoding="utf-8")

        assert check_links._check_file(source, tmp_path) == []


class TestMain:
    """Test suite for main()."""

    def test_main_returns_1_when_broken_links_found(self, tmp_path: Path) -> None:
        (tmp_path / "a.md").write_text("[broken](./missing.md)\n", encoding="utf-8")

        assert check_links.main(["--root", str(tmp_path)]) == 1

    def test_main_returns_0_when_no_broken_links(self, tmp_path: Path) -> None:
        (tmp_path / "a.md").write_text("plain text, no links\n", encoding="utf-8")

        assert check_links.main(["--root", str(tmp_path)]) == 0

    def test_main_excludes_vendor_directories(self, tmp_path: Path) -> None:
        excluded = tmp_path / "node_modules"
        excluded.mkdir()
        (excluded / "a.md").write_text("[broken](./missing.md)\n", encoding="utf-8")

        assert check_links.main(["--root", str(tmp_path)]) == 0
