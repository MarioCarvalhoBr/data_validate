#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""Graph data validation utilities for hierarchical structure validation."""

from typing import List, Tuple, Optional
import pandas as pd
import networkx as nx


class GraphProcessing:
    """
    Graph processing utilities for hierarchical data structure validation.

    This class provides methods for creating, analyzing, and validating
    directed graphs from hierarchical data structures such as parent-child
    relationships in spreadsheet data.

    Attributes:
        graph: The directed graph structure created from input data
    """

    def __init__(self, dataframe: Optional[pd.DataFrame] = None, parent_column: Optional[str] = None, child_column: Optional[str] = None) -> None:
        """
        Initialize GraphProcessing with optional DataFrame.

        Args:
            dataframe: DataFrame containing hierarchical data
            parent_column: Name of the parent column
            child_column: Name of the child column
        """
        self.graph: Optional[nx.DiGraph] = None

        # Se as colunas estiverem no dataframe, cria o grafo
        if not dataframe.empty and parent_column in dataframe.columns and child_column in dataframe.columns:
            self.graph = self.create_graph_structure(dataframe, parent_column, child_column)

    def create_graph_structure(self, dataframe: pd.DataFrame, parent_column: str, child_column: str) -> nx.DiGraph:
        """
        Create a directed graph from DataFrame with parent-child relationships.

        Args:
            dataframe: DataFrame containing the data
            parent_column: Name of the column containing parent nodes
            child_column: Name of the column containing child nodes

        Returns:
            Directed graph representing the hierarchical structure
        """
        directed_graph: nx.DiGraph = nx.DiGraph()
        for _, row in dataframe.iterrows():
            directed_graph.add_edge(str(row[parent_column]), str(row[child_column]))

        self.graph = directed_graph
        return directed_graph

    def detect_cycles(self, graph: Optional[nx.DiGraph] = None) -> Tuple[bool, Optional[List[Tuple[str, str]]]]:
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

    def detect_disconnected_components(self, graph: Optional[nx.DiGraph] = None) -> List[nx.DiGraph]:
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

    def generate_graph_report(self, graph: Optional[nx.DiGraph] = None) -> str:
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

    def get_leaf_nodes(self, graph: Optional[nx.DiGraph] = None) -> List[str]:
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

    def convert_to_tree(self, root_node: str, graph: Optional[nx.DiGraph] = None) -> nx.DiGraph:
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

    def breadth_first_search_from_node(self, start_node: str, graph: Optional[nx.DiGraph] = None) -> nx.DiGraph:
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

    @property
    def node_count(self) -> int:
        """Get the number of nodes in the graph."""
        if self.graph is None:
            return 0
        return self.graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        """Get the number of edges in the graph."""
        if self.graph is None:
            return 0
        return self.graph.number_of_edges()

    @property
    def is_empty(self) -> bool:
        """Check if the graph is empty."""
        return self.graph is None or self.graph.number_of_nodes() == 0
