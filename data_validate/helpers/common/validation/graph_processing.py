#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Graph data validation utilities for hierarchical structure validation."""

import networkx as nx
import pandas as pd


class GraphProcessing:
    """
    Graph processing utilities for hierarchical data structure validation.

    This class provides methods for creating, analyzing, and validating
    directed graphs from hierarchical data structures such as parent-child
    relationships in spreadsheet data.

    Attributes:
        graph: The directed graph structure created from input data
    """

    def __init__(
        self,
        dataframe: pd.DataFrame | None = None,
        parent_column: str | None = None,
        child_column: str | None = None,
    ) -> None:
        """
        Initialize GraphProcessing with optional DataFrame.

        Args:
            dataframe: DataFrame containing hierarchical data
            parent_column: Name of the parent column
            child_column: Name of the child column
        """
        self.graph: nx.DiGraph | None = None

        # If columns are in the dataframe, create the graph
        if (
            dataframe is not None
            and not dataframe.empty
            and parent_column is not None
            and child_column is not None
            and parent_column in dataframe.columns
            and child_column in dataframe.columns
        ):
            self.graph = self.create_graph_structure(dataframe, parent_column, child_column)

    def create_graph_structure(self, dataframe: pd.DataFrame, parent_column: str, child_column: str) -> nx.DiGraph:
        """
        Create a directed graph from DataFrame with parent-child relationships.

        Vectorised (PERF-001) via `nx.from_pandas_edgelist`: the whole edge list is built in
        one call instead of an `iterrows()` loop calling `add_edge` per row. Node ids are
        still produced with `str(value)` per cell (via `.map(str)`, not `.astype(str)` — the
        latter leaves a `NaN` cell as `float('nan')` instead of stringifying it), preserving
        the exact string coercion the old per-row `str(row[column])` used, including for
        `NaN`/mixed-type columns and for `parent_column == child_column` (self-loops).

        Args:
            dataframe: DataFrame containing the data
            parent_column: Name of the column containing parent nodes
            child_column: Name of the column containing child nodes

        Returns:
            Directed graph representing the hierarchical structure
        """
        edges = pd.DataFrame(
            {
                "source": dataframe[parent_column].map(str),
                "target": dataframe[child_column].map(str),
            }
        )
        directed_graph: nx.DiGraph = nx.from_pandas_edgelist(
            edges, source="source", target="target", create_using=nx.DiGraph
        )
        self.graph = directed_graph
        return directed_graph

    def detect_cycles(self, graph: nx.DiGraph | None = None) -> tuple[bool, list[tuple[str, str]] | None]:
        """
        Detect cycles in the directed graph.

        Args:
            graph: Optional graph to analyze. Uses instance graph if not provided

        Returns:
            Tuple containing (has_cycle, cycle_edges)
        """
        target_graph = graph if graph is not None else self.graph
        if target_graph is None:
            raise ValueError("No graph available for cycle detection")

        try:
            cycle = nx.find_cycle(target_graph)
            return True, cycle
        except nx.NetworkXNoCycle:
            return False, None

    def detect_disconnected_components(self, graph: nx.DiGraph | None = None) -> list[nx.DiGraph]:
        """
        Detect disconnected components in the graph.

        Args:
            graph: Optional graph to analyze. Uses instance graph if not provided

        Returns:
            List of disconnected subgraphs (excluding the main component)
        """
        target_graph = graph if graph is not None else self.graph
        if target_graph is None:
            raise ValueError("No graph available for disconnected component detection")

        sub_graphs = [target_graph.subgraph(c).copy() for c in nx.weakly_connected_components(target_graph)]
        sub_graphs.sort(key=len, reverse=True)
        return sub_graphs[1:] if len(sub_graphs) > 1 else []

    def generate_graph_report(self, graph: nx.DiGraph | None = None) -> str:
        """
        Generate a formatted string report of graph edges.

        Args:
            graph: Optional graph to analyze. Uses instance graph if not provided

        Returns:
            String representation of all edges in the graph
        """
        target_graph = graph if graph is not None else self.graph
        if target_graph is None:
            raise ValueError("No graph available for report generation")

        text_graph = []
        for source, target in target_graph.edges():
            source_val = float(source)
            target_val = float(target)
            source_val = int(source_val) if source_val.is_integer() else source_val
            target_val = int(target_val) if target_val.is_integer() else target_val

            text_graph.append(f"{source_val} -> {target_val}")

        return ", ".join(sorted(text_graph, key=lambda x: x, reverse=False))

    def get_leaf_nodes(self, graph: nx.DiGraph | None = None) -> list[str]:
        """
        Get all leaf nodes (nodes with no outgoing edges) from the graph.

        Args:
            graph: Optional graph to analyze. Uses instance graph if not provided

        Returns:
            List of leaf node identifiers
        """
        target_graph = graph if graph is not None else self.graph
        if target_graph is None:
            raise ValueError("No graph available for leaf node detection")

        leaf_nodes = []

        for node in target_graph.nodes():
            if target_graph.out_degree(node) == 0:
                leaf_nodes.append(node)
        return leaf_nodes

    def convert_to_tree(self, root_node: str, graph: nx.DiGraph | None = None) -> nx.DiGraph:
        """
        Convert the directed graph to a tree structure starting from root node.

        Args:
            root_node: The root node to start the tree from
            graph: Optional graph to analyze. Uses instance graph if not provided

        Returns:
            Tree structure as a directed graph

        Raises:
            ValueError: If root node is not found in the graph
        """
        target_graph = graph if graph is not None else self.graph
        if target_graph is None:
            raise ValueError("No graph available for tree conversion")

        if root_node not in target_graph.nodes:
            raise ValueError(f"Root node '{root_node}' not found in the graph nodes.")

        tree = nx.bfs_tree(target_graph, root_node)
        return tree

    def breadth_first_search_from_node(self, start_node: str, graph: nx.DiGraph | None = None) -> nx.DiGraph:
        """
        Perform breadth-first search from a starting node.

        Args:
            start_node: The node to start BFS from
            graph: Optional graph to analyze. Uses instance graph if not provided

        Returns:
            BFS tree as a directed graph

        Raises:
            ValueError: If start node is not found in the graph
        """
        target_graph = graph if graph is not None else self.graph
        if target_graph is None:
            raise ValueError("No graph available for BFS")

        if start_node not in target_graph.nodes:
            raise ValueError(f"Start node '{start_node}' not found in the graph nodes.")

        bfs_tree = nx.bfs_tree(target_graph, start_node)
        return bfs_tree
