#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
import pandas as pd
import pytest

from data_validate.helpers.common.validation.tree_processing import TreeProcessing


class TestCreateTreeStructure:
    """Test suite for create_tree_structure function."""

    @pytest.fixture
    def sample_composition_df(self) -> pd.DataFrame:
        """Create sample composition DataFrame for testing."""
        return pd.DataFrame(
            {
                "codigo_pai": ["A", "A", "B", "B", "C"],
                "codigo_filho": ["B", "C", "D", "E", "F"],
            }
        )

    def test_create_tree_structure_basic(self, sample_composition_df: pd.DataFrame) -> None:
        """Test create_tree_structure with basic parent-child relationships."""
        tree = TreeProcessing.create_tree_structure(sample_composition_df, "codigo_pai", "codigo_filho")

        expected_tree = {
            "A": ["B", "C"],
            "B": ["D", "E"],
            "C": ["F"],
        }

        assert tree == expected_tree

    def test_create_tree_structure_empty_dataframe(self) -> None:
        """Test create_tree_structure with empty DataFrame."""
        df = pd.DataFrame({"parent": [], "child": []})
        tree = TreeProcessing.create_tree_structure(df, "parent", "child")

        assert tree == {}

    def test_create_tree_structure_single_relationship(self) -> None:
        """Test create_tree_structure with single parent-child relationship."""
        df = pd.DataFrame({"parent": ["A"], "child": ["B"]})
        tree = TreeProcessing.create_tree_structure(df, "parent", "child")

        assert tree == {"A": ["B"]}

    def test_create_tree_structure_duplicate_relationships(self) -> None:
        """Test create_tree_structure with duplicate parent-child relationships."""
        df = pd.DataFrame(
            {
                "parent": ["A", "A", "A", "B"],
                "child": ["B", "B", "C", "D"],
            }
        )
        tree = TreeProcessing.create_tree_structure(df, "parent", "child")

        expected_tree = {
            "A": ["B", "B", "C"],
            "B": ["D"],
        }

        assert tree == expected_tree

    def test_create_tree_structure_numeric_codes(self) -> None:
        """Test create_tree_structure with numeric parent-child codes."""
        df = pd.DataFrame(
            {
                "codigo_pai": [1, 1, 2, 3],
                "codigo_filho": [2, 3, 4, 5],
            }
        )
        tree = TreeProcessing.create_tree_structure(df, "codigo_pai", "codigo_filho")

        expected_tree = {
            "1": ["2", "3"],
            "2": ["4"],
            "3": ["5"],
        }

        assert tree == expected_tree

    def test_create_tree_structure_mixed_types(self) -> None:
        """Test create_tree_structure with mixed data types."""
        df = pd.DataFrame(
            {
                "parent": ["A", 1, "B", 2.5],
                "child": [1, "B", 2.5, "C"],
            }
        )
        tree = TreeProcessing.create_tree_structure(df, "parent", "child")

        expected_tree = {
            "A": ["1"],
            "1": ["B"],
            "B": ["2.5"],
            "2.5": ["C"],
        }

        assert tree == expected_tree


class TestDetectCyclesDfs:
    """Test suite for detect_cycles_dfs function."""

    def test_detect_cycles_dfs_no_cycle(self) -> None:
        """Test detect_cycles_dfs with tree structure (no cycles)."""
        tree = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["E"],
            "D": [],
            "E": [],
        }

        cycle_found, cycle = TreeProcessing.detect_cycles_dfs(tree, "A", set(), [])

        assert cycle_found is False
        assert cycle == []

    def test_detect_cycles_dfs_simple_cycle(self) -> None:
        """Test detect_cycles_dfs with simple cycle."""
        tree = {
            "A": ["B"],
            "B": ["C"],
            "C": ["A"],  # Creates cycle A -> B -> C -> A
        }

        cycle_found, cycle = TreeProcessing.detect_cycles_dfs(tree, "A", set(), [])

        assert cycle_found is True
        assert "A" in cycle
        assert len(cycle) > 1

    def test_detect_cycles_dfs_self_loop(self) -> None:
        """Test detect_cycles_dfs with self-loop."""
        tree = {
            "A": ["A"],  # Self-loop
        }

        cycle_found, cycle = TreeProcessing.detect_cycles_dfs(tree, "A", set(), [])

        assert cycle_found is True
        assert cycle == ["A", "A"]

    def test_detect_cycles_dfs_complex_cycle(self) -> None:
        """Test detect_cycles_dfs with complex cycle in larger tree."""
        tree = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["E"],
            "D": ["F"],
            "E": ["F"],
            "F": ["B"],  # Creates cycle B -> D -> F -> B
        }

        cycle_found, cycle = TreeProcessing.detect_cycles_dfs(tree, "A", set(), [])

        assert cycle_found is True
        assert "B" in cycle and "D" in cycle and "F" in cycle

    def test_detect_cycles_dfs_node_not_in_tree(self) -> None:
        """Test detect_cycles_dfs with node not in tree."""
        tree = {
            "A": ["B"],
            "B": ["C"],
        }

        cycle_found, cycle = TreeProcessing.detect_cycles_dfs(tree, "Z", set(), [])

        assert cycle_found is False
        assert cycle == []

    def test_detect_cycles_dfs_empty_tree(self) -> None:
        """Test detect_cycles_dfs with empty tree."""
        tree = {}

        cycle_found, cycle = TreeProcessing.detect_cycles_dfs(tree, "A", set(), [])

        assert cycle_found is False
        assert cycle == []

    def test_detect_cycles_dfs_already_visited_no_cycle(self) -> None:
        """Test detect_cycles_dfs with already visited node (no cycle)."""
        tree = {
            "A": ["B"],
            "B": ["C"],
            "C": ["D"],
            "D": [],
        }

        visited = {"B", "C", "D"}
        cycle_found, cycle = TreeProcessing.detect_cycles_dfs(tree, "A", visited, [])

        assert cycle_found is False
        assert cycle == []


class TestDetectTreeCycles:
    """Test suite for detect_tree_cycles function."""

    def test_detect_tree_cycles_no_cycle(self) -> None:
        """Test detect_tree_cycles with valid tree structure."""
        tree = {
            "A": ["B", "C"],
            "B": ["D", "E"],
            "C": ["F"],
            "D": [],
            "E": [],
            "F": [],
        }

        cycle_found, cycle = TreeProcessing.detect_tree_cycles(tree)

        assert cycle_found is False
        assert cycle == []

    def test_detect_tree_cycles_simple_cycle(self) -> None:
        """Test detect_tree_cycles with simple cycle."""
        tree = {
            "A": ["B"],
            "B": ["C"],
            "C": ["A"],
        }

        cycle_found, cycle = TreeProcessing.detect_tree_cycles(tree)

        assert cycle_found is True
        assert len(cycle) >= 3
        assert "A" in cycle

    def test_detect_tree_cycles_multiple_components_with_cycle(self) -> None:
        """Test detect_tree_cycles with multiple components where one has cycle."""
        tree = {
            "A": ["B"],
            "B": ["C"],
            "C": [],  # Valid component
            "X": ["Y"],
            "Y": ["Z"],
            "Z": ["X"],  # Cycle in second component
        }

        cycle_found, cycle = TreeProcessing.detect_tree_cycles(tree)

        assert cycle_found is True
        assert any(node in cycle for node in ["X", "Y", "Z"])

    def test_detect_tree_cycles_self_loop(self) -> None:
        """Test detect_tree_cycles with self-loop."""
        tree = {
            "A": ["A"],
        }

        cycle_found, cycle = TreeProcessing.detect_tree_cycles(tree)

        assert cycle_found is True
        assert cycle == ["A", "A"]

    def test_detect_tree_cycles_empty_tree(self) -> None:
        """Test detect_tree_cycles with empty tree."""
        tree = {}

        cycle_found, cycle = TreeProcessing.detect_tree_cycles(tree)

        assert cycle_found is False
        assert cycle == []

    def test_detect_tree_cycles_disconnected_valid_components(self) -> None:
        """Test detect_tree_cycles with multiple disconnected valid components."""
        tree = {
            "A": ["B"],
            "B": ["C"],
            "C": [],
            "X": ["Y"],
            "Y": [],
            "Z": ["W"],
            "W": [],
        }

        cycle_found, cycle = TreeProcessing.detect_tree_cycles(tree)

        assert cycle_found is False
        assert cycle == []

    def test_detect_tree_cycles_complex_cycle(self) -> None:
        """Test detect_tree_cycles with complex cycle involving multiple nodes."""
        tree = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["E"],
            "D": ["F"],
            "E": ["F"],
            "F": ["G"],
            "G": ["B"],  # Creates long cycle B -> D -> F -> G -> B
        }

        cycle_found, cycle = TreeProcessing.detect_tree_cycles(tree)

        assert cycle_found is True
        assert all(node in cycle for node in ["B", "D", "F", "G"])

    def test_detect_tree_cycles_single_node(self) -> None:
        """Test detect_tree_cycles with single node (no children)."""
        tree = {
            "A": [],
        }

        cycle_found, cycle = TreeProcessing.detect_tree_cycles(tree)

        assert cycle_found is False
        assert cycle == []


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple functions."""

    def test_complete_validation_workflow_valid(self) -> None:
        """Test complete validation workflow with valid data."""
        composition_df = pd.DataFrame(
            {
                "codigo_pai": [1, 1, 2],
                "codigo_filho": [2, 3, 4],
            }
        )

        # Test tree creation
        tree = TreeProcessing.create_tree_structure(composition_df, "codigo_pai", "codigo_filho")
        assert tree == {"1": ["2", "3"], "2": ["4"]}

        # Test cycles
        cycle_found, cycle = TreeProcessing.detect_tree_cycles(tree)
        assert cycle_found is False

    def test_complete_validation_workflow_with_errors(self) -> None:
        """Test complete validation workflow with various errors."""
        composition_df = pd.DataFrame(
            {
                "codigo_pai": [1, 2, 3, 4],
                "codigo_filho": [2, 3, 4, 1],  # Creates cycle
            }
        )

        # Test tree creation
        tree = TreeProcessing.create_tree_structure(composition_df, "codigo_pai", "codigo_filho")

        # Test cycles
        cycle_found, cycle = TreeProcessing.detect_tree_cycles(tree)
        assert cycle_found is True


class TestEdgeCasesAndBoundaryConditions:
    """Test edge cases and boundary conditions."""

    def test_large_tree_structure(self) -> None:
        """Test with large tree structure to check performance."""
        # Create a large balanced tree
        composition_data = []
        for i in range(1, 100):
            composition_data.append({"parent": i, "child": i * 2})
            composition_data.append({"parent": i, "child": i * 2 + 1})

        df = pd.DataFrame(composition_data)
        tree = TreeProcessing.create_tree_structure(df, "parent", "child")

        # Should handle large tree without issues
        assert len(tree) > 0
        cycle_found, cycle = TreeProcessing.detect_tree_cycles(tree)
        assert cycle_found is False

    def test_very_long_cycle(self) -> None:
        """Test detection of very long cycle."""
        # Create a long chain that cycles back
        tree = {}
        for i in range(100):
            tree[str(i)] = [str((i + 1) % 100)]

        cycle_found, cycle = TreeProcessing.detect_tree_cycles(tree)
        assert cycle_found is True

    def test_mixed_data_types_in_tree(self) -> None:
        """Test tree operations with mixed data types."""
        composition_df = pd.DataFrame(
            {
                "parent": [1, "A", 2.5, "True"],  # Changed True to "True" string
                "child": ["A", 2.5, "True", "B"],  # Changed True to "True" string
            }
        )

        # Should handle mixed types by converting to strings
        tree = TreeProcessing.create_tree_structure(composition_df, "parent", "child")
        assert "1" in tree
        assert "A" in tree

    def test_create_tree_structure_self_referencing_columns(self) -> None:
        """`parent_column == child_column` still works (temp column names avoid collisions)."""
        composition_df = pd.DataFrame({"node": [1, 2, 2]})

        tree = TreeProcessing.create_tree_structure(composition_df, "node", "node")

        assert tree == {"1": ["1"], "2": ["2", "2"]}
