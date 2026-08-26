#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br).
#  Documentation, source code, and more details about the AdaptaBrasil project are available at:
#  https://github.com/AdaptaBrasil/.

"""
Check i18n message catalog parity, unused keys, and placeholder consistency.

Loads every `data_validate/static/locales/<locale>/messages.json` catalog and reports:

- Keys present in one locale but missing from another (a parity error — exit code 1).
- Keys never referenced from `data_validate/**/*.py` via `<something>.text("key", ...)` (reported,
  does not fail the check — a key can be reserved for a message not yet wired up).
- Keys whose message template has different named placeholders across locales (a parity error).

See `.claude/rules/i18n.md` and `.specs/i18n/catalog.md`. Used by `make i18n-check` and the
`i18n-guardian` agent; this script only reports, it never edits a catalog.
"""

from __future__ import annotations

import argparse
import json
import re
import string
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LOCALES_DIR = _REPO_ROOT / "data_validate" / "static" / "locales"
_SOURCE_DIR = _REPO_ROOT / "data_validate"
_TEXT_CALL_KEY_RE = re.compile(r"""\.text\(\s*["']([^"']+)["']""")


def _load_catalog(locale_dir: Path) -> dict[str, Any]:
    """Load one locale's `messages.json`.

    Args:
        locale_dir: Directory containing `messages.json` for one locale.

    Returns:
        dict[str, Any]: The parsed catalog (key -> `{"message": "..."}`).
    """
    return json.loads((locale_dir / "messages.json").read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def _discover_locales() -> dict[str, dict[str, Any]]:
    """Load every locale catalog under `_LOCALES_DIR`.

    Returns:
        dict[str, dict[str, Any]]: Locale name -> catalog. A locale whose catalog fails to load
            is included with an empty catalog and a warning on stderr, so parity checks still
            report it as fully missing rather than crashing.
    """
    catalogs: dict[str, dict[str, Any]] = {}
    if not _LOCALES_DIR.is_dir():
        return catalogs
    for locale_dir in sorted(p for p in _LOCALES_DIR.iterdir() if p.is_dir()):
        try:
            catalogs[locale_dir.name] = _load_catalog(locale_dir)
        except (OSError, json.JSONDecodeError) as error:
            print(f"warning: failed to load {locale_dir.name}/messages.json: {error}", file=sys.stderr)
            catalogs[locale_dir.name] = {}
    return catalogs


def _find_used_keys() -> set[str]:
    """Find every catalog key referenced as a literal in a `.text("key")` call.

    Returns:
        set[str]: The set of keys found. Dynamically built keys (f-strings, variables) are not
            detected — this is a best-effort static scan, not a guarantee of unused-ness.
    """
    used: set[str] = set()
    for path in _SOURCE_DIR.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        used.update(_TEXT_CALL_KEY_RE.findall(text))
    return used


def _message_placeholders(message: str) -> set[str]:
    """Extract named `str.format` placeholders from a message template.

    Args:
        message: The message template (e.g. `"Missing {count} items"`).

    Returns:
        set[str]: The set of named fields (positional/empty fields are ignored, since the project
            convention forbids them — see `.claude/rules/i18n.md`).
    """
    return {field_name for _, field_name, _, _ in string.Formatter().parse(message) if field_name}


def check_catalogs() -> dict[str, Any]:
    """Run the full parity/unused-key/placeholder check.

    Returns:
        dict[str, Any]: A JSON-serialisable report with keys `locales`, `total_keys`,
            `missing_per_locale`, `unused_keys`, `placeholder_mismatches`, and `ok`.
    """
    catalogs = _discover_locales()
    locales = sorted(catalogs)

    all_keys: set[str] = set()
    for catalog in catalogs.values():
        all_keys.update(catalog)

    missing_per_locale = {locale: sorted(all_keys - set(catalogs[locale])) for locale in locales}

    unused_keys = sorted(all_keys - _find_used_keys())

    placeholder_mismatches: dict[str, dict[str, list[str]]] = {}
    for key in sorted(all_keys):
        per_locale_placeholders: dict[str, set[str]] = {}
        for locale in locales:
            entry = catalogs[locale].get(key)
            if isinstance(entry, dict) and isinstance(entry.get("message"), str):
                per_locale_placeholders[locale] = _message_placeholders(entry["message"])
        distinct = {frozenset(placeholders) for placeholders in per_locale_placeholders.values()}
        if len(distinct) > 1:
            placeholder_mismatches[key] = {
                locale: sorted(placeholders) for locale, placeholders in per_locale_placeholders.items()
            }

    has_parity_errors = any(missing_per_locale[locale] for locale in locales) or bool(placeholder_mismatches)

    return {
        "locales": locales,
        "total_keys": len(all_keys),
        "missing_per_locale": missing_per_locale,
        "unused_keys": unused_keys,
        "placeholder_mismatches": placeholder_mismatches,
        "ok": not has_parity_errors,
    }


def _print_report(report: dict[str, Any]) -> None:
    """Print the report as human-readable text.

    Args:
        report: The report produced by `check_catalogs`.
    """
    print(f"Locales checked: {', '.join(report['locales'])} ({report['total_keys']} distinct keys)")

    for locale, missing in report["missing_per_locale"].items():
        if missing:
            print(f"\nMissing in {locale} ({len(missing)}):")
            for key in missing:
                print(f"  - {key}")

    if report["unused_keys"]:
        print(f'\nUnused keys ({len(report["unused_keys"])}) — not referenced via `.text("...")`:')
        for key in report["unused_keys"]:
            print(f"  - {key}")

    if report["placeholder_mismatches"]:
        print(f"\nPlaceholder mismatches ({len(report['placeholder_mismatches'])}):")
        for key, per_locale in report["placeholder_mismatches"].items():
            print(f"  - {key}: {per_locale}")

    print("\nOK" if report["ok"] else "\nFAILED (missing keys and/or placeholder mismatches found)")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser.

    Returns:
        argparse.ArgumentParser: The configured parser.
    """
    parser = argparse.ArgumentParser(description="Check i18n catalog parity, unused keys, and placeholder consistency.")
    parser.add_argument("--json", action="store_true", help="Print the report as JSON instead of text.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point: run the check and print the report.

    Args:
        argv: Command-line arguments, or None to use `sys.argv[1:]`.

    Returns:
        int: 0 when there are no parity errors, 1 otherwise.
    """
    args = build_parser().parse_args(argv)
    report = check_catalogs()

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _print_report(report)

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
