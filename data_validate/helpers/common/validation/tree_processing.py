#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""Tree data validation utilities for hierarchical structure validation."""

from typing import List, Tuple, Dict, Any, Set

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

        Args:
            dataframe: DataFrame containing parent-child relationships
            parent_column: Name of the parent code column
            child_column: Name of the child code column

        Returns:
            Dictionary mapping parent codes to lists of child codes
        """
        tree: Dict[str, List[str]] = {}

        for _, row in dataframe.iterrows():
            parent = str(row[parent_column])
            child = str(row[child_column])

            if parent not in tree:
                tree[parent] = []
            tree[parent].append(child)

        return tree

    @staticmethod
    def validate_level_hierarchy(
        composition_df: pd.DataFrame,
        description_df: pd.DataFrame,
        code_column: str,
        level_column: str,
        parent_column: str,
        child_column: str,
    ) -> List[Tuple[Any, Any]]:
        """
        Validate that parent nodes have lower levels than their children.

        Args:
            composition_df: DataFrame with parent-child relationships
            description_df: DataFrame with code-level mappings
            code_column: Name of the code column in description
            level_column: Name of the level column in description
            parent_column: Name of the parent code column in composition
            child_column: Name of the child code column in composition

        Returns:
            List of tuples containing (parent, child) pairs with level errors
        """
        errors: List[Tuple[Any, Any]] = []

        # Create level mapping
        levels = {row[code_column]: row[level_column] for _, row in description_df.iterrows()}

        for _, row in composition_df.iterrows():
            parent = row[parent_column]
            child = row[child_column]
            parent_level = levels.get(parent, None)
            child_level = levels.get(child, None)

            if parent_level is None:
                errors.append((parent, None))
            elif child_level is None:
                errors.append((None, child))
            elif parent_level >= child_level:
                errors.append((parent, child))

        return errors

    @staticmethod
    def validate_missing_codes_in_description(
        composition_df: pd.DataFrame,
        description_df: pd.DataFrame,
        code_column: str,
        parent_column: str,
        child_column: str,
    ) -> List[Tuple[str, Any]]:
        """
        Validate that all parent and child codes exist in description.

        Args:
            composition_df: DataFrame with parent-child relationships
            description_df: DataFrame with code-level mappings
            code_column: Name of the code column in description
            parent_column: Name of the parent code column in composition
            child_column: Name of the child code column in composition

        Returns:
            List of tuples containing (error_type, code) pairs for missing codes
        """
        errors: List[Tuple[str, Any]] = []

        # Get all codes from description
        description_codes = set(description_df[code_column].values)

        # Check for missing parent codes
        for _, row in composition_df.iterrows():
            parent = row[parent_column]
            child = row[child_column]

            if parent not in description_codes:
                errors.append(("parent", parent))
            if child not in description_codes:
                errors.append(("child", child))

        return errors

    @staticmethod
    def detect_cycles_dfs(tree: Dict[str, List[str]], node: str, visited: Set[str], current_path: List[str]) -> Tuple[bool, List[str]]:
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
