#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Immutable data model consumed by the HTML/PDF report template (ARC-016).

`ReportModel`/`ReportSection` replace the ad hoc `Dict[str, Any]` built by
`FileReportGenerator._build_template_variables` (now deleted): every value the
Jinja2 template needs is a plain Python value (`str`/`int`/`bool`/a tuple of
`ReportSection`), never a pre-built HTML string. The template itself loops
over `sections`/`skipped_tests` and renders each field through `{{ }}`, so
Jinja2's `autoescape=True` (SEC-001) escapes every value that came from
untrusted spreadsheet content or CLI metadata -- nothing here is ever marked
`|safe`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReportSection:
    """One verification's messages, as shown in both the "Erros" and "Avisos" cards.

    Attributes:
        title: The localized verification/category name (e.g. "Códigos sequenciais").
        errors: Error messages for this verification, already truncated
            (`ValidationReport.flatten`) to the configured per-category limit.
        warnings: Warning messages for this verification, same truncation rule.
    """

    title: str
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ReportModel:
    """Everything the report template needs to render one validation run.

    Every field is a plain value the template reads with `{{ }}`/`{% for %}`; none of them
    are pre-formatted HTML fragments. `sector`/`protocol`/`user`/`file` are the raw
    `--sector`/`--protocol`/`--user`/`--file` CLI values (or `None`), `sections` carries the
    raw, untrusted spreadsheet-derived messages -- both are escaped by the template's
    `autoescape=True`, not by this model.

    Attributes:
        name: The project name shown in the header (e.g. "Canoa").
        error_count: Total error count, pre-formatted with the locale's thousands separator.
        warning_count: Total warning count, pre-formatted the same way.
        total_tests: Number of verifications executed.
        sections: One `ReportSection` per verification, in execution order.
        skipped_tests: Localized names of verifications that were not executed.
        show_date: Whether the run date/time line should be rendered (`--no-time` hides it).
        date_now: The run's date/time, formatted `dd/mm/yyyy HH:MM:SS`.
        show_version: Whether the version/OS/protocol line should be rendered
            (`--no-version` hides it).
        version: The validator's own version string.
        os_name: The host OS name (`platform.system()`).
        protocol_version: The AdaptaBrasil protocol version the validator implements.
        sector: The `--sector` CLI value, or `None` when not given.
        protocol: The `--protocol` CLI value, or `None` when not given.
        user: The `--user` CLI value, or `None` when not given.
        file: The `--file` CLI value, or `None` when not given.
    """

    name: str
    error_count: str
    warning_count: str
    total_tests: int
    sections: tuple[ReportSection, ...]
    skipped_tests: tuple[str, ...]
    show_date: bool
    date_now: str
    show_version: bool
    version: str
    os_name: str
    protocol_version: str
    sector: str | None
    protocol: str | None
    user: str | None
    file: str | None
