#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Render `Engine` outcomes into the legacy `ValidationReport` (ARC-017 Phase 3b, ADR-0006).

The legacy pipeline (`controllers/spreadsheet_processor.py`, `controllers/report/
validation_report.py`) still groups messages by a `NamesEnum`-keyed, localized title string, not
by `Issue`/`RuleOutcome`. `extend_report_from_outcomes` is the one, reusable seam between the two:
every future validator port (description, composition, …) reuses this same function instead of
re-deriving its own rendering loop, so the mapping from `Issue.category`/`Issue.severity` to a
report bucket is defined exactly once.

Depends only on `data_validate.rules`, `data_validate.specs`, and
`data_validate.controllers.report.validation_report`, per
`.claude/rules/architecture-boundaries.md` (an adapter module, not `rules` proper — it is the one
place allowed to bridge `rules`' structured output into `reporting`'s current, pre-migration shape).

`ValidationReport` is imported only under `TYPE_CHECKING`: `controllers/__init__.py` eagerly
imports `spreadsheet_processor.py`, which (since ARC-017 Phase 3b) imports this module — a real
runtime import of `data_validate.controllers.report.validation_report` here would make that a
genuine import cycle. `report`'s only use is this function's `report` parameter's type hint, which
`from __future__ import annotations` already turns into a lazily-evaluated string, so the
type-only import is enough and costs nothing at runtime.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import TYPE_CHECKING

from data_validate.rules.engine import RuleOutcome
from data_validate.specs.issues import Severity

if TYPE_CHECKING:  # pragma: no cover
    from data_validate.controllers.report.validation_report import ValidationReport


def extend_report_from_outcomes(
    outcomes: Iterable[RuleOutcome],
    translate: Callable[..., str],
    report: ValidationReport,
    titles: Mapping[str, str],
) -> None:
    """Render every issue from `outcomes` and append it to its legacy report bucket, in order.

    Args:
        outcomes: Rule outcomes to render, in the order `Engine.run` produced them (only
            `RuleStatus.ISSUES` outcomes carry any `Issue`; `PASSED`/`SKIPPED`/`FAILED` outcomes
            contribute nothing).
        translate: Renders a catalog key plus named parameters into localised text — the same
            shape as `RuleContext.translate`/`context.lm.text` (`.claude/rules/i18n.md`).
        report: The legacy `ValidationReport` to extend in place.
        titles: `NamesEnum.value -> localized title` map (`ApplicationConfig.get_verify_names()`),
            used to resolve which report bucket an issue's `category` belongs to.

    Notes:
        An issue whose `category` is `None` (no legacy report bucket to map to yet) is skipped
        rather than raising — every rule ported so far always sets `category`, but a future rule
        with no legacy equivalent is expected to leave it unset (see `Issue.category`'s docstring).
    """
    for outcome in outcomes:
        for issue in outcome.issues:
            if issue.category is None:
                continue
            rendered = translate(issue.message_key, **issue.params)
            title = titles[issue.category]
            if issue.severity is Severity.ERROR:
                report.extend(title, errors=[rendered])
            else:
                report.extend(title, warnings=[rendered])
