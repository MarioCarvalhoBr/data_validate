#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""Graph data validation utilities for hierarchical structure validation."""

from typing import List, Tuple
import pandas as pd
import networkx as nx


def create_graph_structure(dataframe: pd.DataFrame, parent_column: str, child_column: str) -> nx.DiGraph:
    directed_graph: nx.DiGraph = nx.DiGraph()
    for _, row in dataframe.iterrows():
        directed_graph.add_edge(str(row[parent_column]), str(row[child_column]))
    return directed_graph


def detect_cycles_in_graph(directed_graph: nx.DiGraph) -> Tuple[bool, List[Tuple[str, str]] | None]:
    try:
        cycle = nx.find_cycle(directed_graph)
        return True, cycle
    except nx.NetworkXNoCycle:
        return False, None


def detect_graphs_disconnected(directed_graph: nx.DiGraph) -> List[nx.DiGraph]:
    sub_graphs = [directed_graph.subgraph(c).copy() for c in nx.weakly_connected_components(directed_graph)]
    sub_graphs.sort(key=len, reverse=True)
    return sub_graphs[1:] if len(sub_graphs) > 1 else []


def get_graph_report(directed_graph: nx.DiGraph) -> str:
    text_graph = []
    for source, target in directed_graph.edges():
        source = float(source)
        target = float(target)
        source = int(source) if source.is_integer() else source
        target = int(target) if target.is_integer() else target

        text_graph.append(f"{source} -> {target}")

    return ", ".join(sorted(text_graph, key=lambda x: x, reverse=False))


def get_nodes_leafs(directed_graph: nx.DiGraph) -> List[str]:
    leafs = []
    for node in directed_graph.nodes():
        if directed_graph.out_degree(node) == 0:
            leafs.append(node)
    return leafs


def convert_graph_to_tree(directed_graph: nx.DiGraph, root_node: str) -> nx.DiGraph:
    if root_node not in directed_graph.nodes:
        raise ValueError(f"Root node '{root_node}' not found in the graph nodes.")
    tree = nx.bfs_tree(directed_graph, root_node)
    return tree


def bsf_from_node(directed_graph: nx.DiGraph, start_node: str) -> nx.DiGraph:
    if start_node not in directed_graph.nodes:
        raise ValueError(f"Start node '{start_node}' not found in the graph nodes.")
    bfs_tree = nx.bfs_tree(directed_graph, start_node)
    return bfs_tree
