#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""ARC-011: `list_all_rules()` backs the CLI's `--list-rules` flag."""

from __future__ import annotations

from data_validate.rules import ALL_REGISTRIES, RuleSummary, list_all_rules


class TestListAllRules:
    def test_returns_a_summary_per_registered_rule(self):
        total_registered = sum(len(registry) for registry in ALL_REGISTRIES)

        rows = list_all_rules()

        assert len(rows) == total_registered
        assert total_registered > 0

    def test_rows_are_sorted_by_rule_id(self):
        rows = list_all_rules()

        assert [row.rule_id for row in rows] == sorted(row.rule_id for row in rows)

    def test_every_row_is_a_rule_summary_with_populated_fields(self):
        rows = list_all_rules()

        for row in rows:
            assert isinstance(row, RuleSummary)
            assert row.rule_id
            assert row.category
            assert row.severity in ("error", "warning")

    def test_no_duplicate_rule_ids_across_registries(self):
        rows = list_all_rules()

        rule_ids = [row.rule_id for row in rows]

        assert len(rule_ids) == len(set(rule_ids))
