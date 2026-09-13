#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Tree data validation utilities for hierarchical structure validation."""

from typing import List, Tuple, Dict, Set

import pandas as pd


class TreeProcessing:
    """
    Utility class for processing and validating tree structures.

    Provides static methods to build tree representations from flat data,
    validate hierarchical constraints (levels), check code consistency,
    and detect cycles within the tree.
    """

    def __init__(self) -> None:
        """Initialize the TreeProcessing class."""
        pass

    @staticmethod
    def create_tree_structure(dataframe: pd.DataFrame, parent_column: str, child_column: str) -> Dict[str, List[str]]:
        """
        Create a tree structure from parent-child relationships.

        Vectorised (PERF-001) via `groupby(..., sort=False)` + `.apply(list)` instead of an
        `iterrows()` loop appending to a dict: `sort=False` preserves each parent's
        first-seen order (matching the old loop's insertion order), and each group's
        `.apply(list)` keeps that parent's children in their original row order, including
        duplicates. Distinct temporary column names are used so `parent_column ==
        child_column` (self-referencing edges) still works.

        Args:
            dataframe: DataFrame containing parent-child relationships
            parent_column: Name of the parent code column
            child_column: Name of the child code column

        Returns:
            Dictionary mapping parent codes to lists of child codes
        """
        if dataframe.empty:
            return {}

        edges = pd.DataFrame(
            {
                "__parent__": dataframe[parent_column].map(str),
                "__child__": dataframe[child_column].map(str),
            }
        )
        grouped = edges.groupby("__parent__", sort=False)["__child__"].apply(list)
        return grouped.to_dict()

    @staticmethod
    def detect_cycles_dfs(
        tree: Dict[str, List[str]], node: str, visited: Set[str], current_path: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Detect cycles in tree using depth-first search.

        Args:
            tree: Tree structure as adjacency list
            node: Current node being processed
            visited: Set of already visited nodes
            current_path: Current path in the traversal

        Returns:
            Tuple of (cycle_found, cycle_path)
        """
        if node in visited:
            if node in current_path:
                cycle_start = current_path.index(node)
                return True, current_path[cycle_start:] + [node]
            return False, []

        visited.add(node)
        current_path.append(node)

        for child in tree.get(node, []):
            cycle_found, cycle = TreeProcessing.detect_cycles_dfs(tree, child, visited, current_path)
            if cycle_found:
                return True, cycle

        current_path.pop()
        return False, []

    @staticmethod
    def detect_tree_cycles(tree: Dict[str, List[str]]) -> Tuple[bool, List[str]]:
        """
        Detect cycles in a tree structure.

        Args:
            tree: Tree structure as adjacency list

        Returns:
            Tuple of (cycle_found, cycle_path)
        """
        visited: Set[str] = set()

        for node in tree:
            cycle_found, cycle = TreeProcessing.detect_cycles_dfs(tree, node, visited, [])
            if cycle_found:
                return True, cycle

        return False, []
