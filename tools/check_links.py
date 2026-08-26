#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br).
#  Documentation, source code, and more details about the AdaptaBrasil project are available at:
#  https://github.com/AdaptaBrasil/.

"""
Check that relative links and heading anchors in `*.md` files resolve.

Scans every `*.md` file in the repository (excluding `.venv`, `local_data`, `dev-reports`,
`node_modules`, and `.git`), extracts Markdown hyperlinks `[text](target)`, skips external links
(any `scheme:` URL, e.g. `https:`, `mailto:`), and verifies that:

- A relative file target resolves to an existing path.
- A `#anchor` on a Markdown target matches a heading in that file, GitHub-slugified.

Used by the final verification checklist (see `local_data/prompt-master.md`, section 8, Phase G)
and can be run standalone as `python tools/check_links.py`.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_EXCLUDED_DIR_NAMES = {".venv", "local_data", "dev-reports", "node_modules", ".git"}
_LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*$", re.MULTILINE)
_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
_INLINE_CODE_RE = re.compile(r"`([^`]*)`")
_EMPHASIS_RE = re.compile(r"[*_~]")
_NON_SLUG_RE = re.compile(r"[^\w\s-]")
_WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class BrokenLink:
    """One broken relative link or anchor found in a Markdown file.

    Attributes:
        source: The Markdown file the link was found in.
        target: The raw link target as written in the source.
        reason: A human-readable explanation of why the link is broken.
    """

    source: Path
    target: str
    reason: str


def _is_excluded(path: Path) -> bool:
    """Check whether any path component matches an excluded directory name.

    Args:
        path: The path to check.

    Returns:
        bool: True if the path should be skipped.
    """
    return any(part in _EXCLUDED_DIR_NAMES for part in path.parts)


def _discover_markdown_files(root: Path) -> list[Path]:
    """Find every `*.md` file under `root`, excluding generated/vendor directories.

    Args:
        root: Directory to scan recursively.

    Returns:
        list[Path]: Sorted list of Markdown file paths.
    """
    return sorted(path for path in root.rglob("*.md") if not _is_excluded(path))


def _slugify_heading(text: str) -> str:
    """Approximate GitHub's Markdown heading-to-anchor slug algorithm.

    Args:
        text: The heading text (without the leading `#` markers).

    Returns:
        str: The slug (lowercase, spaces to hyphens, punctuation stripped).
    """
    text = _INLINE_CODE_RE.sub(r"\1", text)
    text = _EMPHASIS_RE.sub("", text)
    slug = text.strip().lower()
    slug = _NON_SLUG_RE.sub("", slug)
    return _WHITESPACE_RE.sub("-", slug)


def _anchors_in_file(path: Path) -> set[str]:
    """Collect every heading anchor slug available in a Markdown file.

    Duplicate slugs are suffixed `-1`, `-2`, ... to match GitHub's disambiguation.

    Args:
        path: The Markdown file to scan.

    Returns:
        set[str]: The set of valid anchor slugs.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    anchors: set[str] = set()
    seen_counts: dict[str, int] = {}
    for match in _HEADING_RE.finditer(text):
        slug = _slugify_heading(match.group(2))
        count = seen_counts.get(slug, 0)
        seen_counts[slug] = count + 1
        anchors.add(slug if count == 0 else f"{slug}-{count}")
    return anchors


def _is_external(target: str) -> bool:
    """Check whether a link target is an external URL (has a scheme).

    Args:
        target: The raw link target.

    Returns:
        bool: True for `https://...`, `mailto:...`, protocol-relative `//...`, etc.
    """
    return bool(_SCHEME_RE.match(target)) or target.startswith("//")


def _check_file(path: Path, root: Path) -> list[BrokenLink]:
    """Check every relative link/anchor in one Markdown file.

    Args:
        path: The Markdown file to check.
        root: The repository root, used to resolve link targets.

    Returns:
        list[BrokenLink]: Every broken link found in this file.
    """
    broken: list[BrokenLink] = []
    text = path.read_text(encoding="utf-8", errors="replace")

    for match in _LINK_RE.finditer(text):
        target = match.group(2).strip()
        if not target or _is_external(target):
            continue

        file_part, _, anchor = target.partition("#")

        if not file_part:
            if anchor and anchor not in _anchors_in_file(path):
                broken.append(BrokenLink(path, target, f"anchor '#{anchor}' not found in {path.name}"))
            continue

        resolved = (path.parent / file_part).resolve()
        if not resolved.exists():
            broken.append(BrokenLink(path, target, f"target not found: {file_part}"))
            continue

        if anchor and resolved.suffix.lower() == ".md" and anchor not in _anchors_in_file(resolved):
            broken.append(BrokenLink(path, target, f"anchor '#{anchor}' not found in {resolved.name}"))

    return broken


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser.

    Returns:
        argparse.ArgumentParser: The configured parser.
    """
    parser = argparse.ArgumentParser(description="Check that relative links and anchors in *.md files resolve.")
    parser.add_argument(
        "--root",
        type=Path,
        default=_REPO_ROOT,
        help="Directory to scan for *.md files (default: repository root).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point: scan and report broken links.

    Args:
        argv: Command-line arguments, or None to use `sys.argv[1:]`.

    Returns:
        int: 0 if no broken links were found, 1 otherwise.
    """
    args = build_parser().parse_args(argv)
    root: Path = args.root.resolve()

    markdown_files = _discover_markdown_files(root)
    all_broken = [broken for path in markdown_files for broken in _check_file(path, root)]

    if not all_broken:
        print(f"Checked {len(markdown_files)} markdown file(s): no broken relative links found.")
        return 0

    print(f"Checked {len(markdown_files)} markdown file(s): {len(all_broken)} broken link(s):", file=sys.stderr)
    for broken in all_broken:
        try:
            rel_source = broken.source.relative_to(root)
        except ValueError:
            rel_source = broken.source
        print(f"  {rel_source}: [{broken.target}] -> {broken.reason}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
