#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""Unit tests for graph_processing module."""

from typing import List, Tuple
import pytest
import pandas as pd
import networkx as nx

from src.helpers.common.validation.graph_processing import GraphProcessing


class TestGraphProcessing:
    """Test suite for GraphProcessing class."""

    @pytest.fixture
    def sample_dataframe(self) -> pd.DataFrame:
        """Create sample DataFrame for testing."""
        return pd.DataFrame({"parent": [1, 1, 2, 2, 3], "child": [2, 3, 4, 5, 6]})

    @pytest.fixture
    def empty_dataframe(self) -> pd.DataFrame:
        """Create empty DataFrame for testing."""
        return pd.DataFrame()

    @pytest.fixture
    def cyclic_dataframe(self) -> pd.DataFrame:
        """Create DataFrame that creates a cyclic graph."""
        return pd.DataFrame({"parent": [1, 2, 3], "child": [2, 3, 1]})

    @pytest.fixture
    def disconnected_dataframe(self) -> pd.DataFrame:
        """Create DataFrame with disconnected components."""
        return pd.DataFrame({"parent": [1, 2, 10, 11], "child": [2, 3, 11, 12]})

    @pytest.fixture
    def single_node_dataframe(self) -> pd.DataFrame:
        """Create DataFrame with single edge."""
        return pd.DataFrame({"parent": [1], "child": [2]})

    @pytest.fixture
    def graph_processor(self, sample_dataframe: pd.DataFrame) -> GraphProcessing:
        """Create GraphProcessing instance with sample data."""
        return GraphProcessing(sample_dataframe, "parent", "child")

    @pytest.fixture
    def empty_graph_processor(self) -> GraphProcessing:
        """Create GraphProcessing instance without data."""
        return GraphProcessing()

    def test_init_with_valid_data(self, sample_dataframe: pd.DataFrame) -> None:
        """Test initialization with valid DataFrame and columns."""
        processor = GraphProcessing(sample_dataframe, "parent", "child")

        assert processor.graph is not None
        assert isinstance(processor.graph, nx.DiGraph)
        assert processor.node_count > 0
        assert processor.edge_count > 0

    def test_init_with_empty_dataframe(self, empty_dataframe: pd.DataFrame) -> None:
        """Test initialization with empty DataFrame."""
        processor = GraphProcessing(empty_dataframe, "parent", "child")

        assert processor.graph is None

    def test_init_with_missing_columns(self, sample_dataframe: pd.DataFrame) -> None:
        """Test initialization with missing columns."""
        processor = GraphProcessing(sample_dataframe, "parent", "missing_column")

        assert processor.graph is None

    def test_init_without_parameters(self) -> None:
        """Test initialization without parameters."""
        processor = GraphProcessing()

        assert processor.graph is None

    def test_create_graph_structure_basic(self, graph_processor: GraphProcessing, sample_dataframe: pd.DataFrame) -> None:
        """Test basic graph creation from DataFrame."""
        graph = graph_processor.create_graph_structure(sample_dataframe, "parent", "child")

        assert isinstance(graph, nx.DiGraph)
        assert graph.number_of_nodes() == 6  # nodes: 1, 2, 3, 4, 5, 6
        assert graph.number_of_edges() == 5  # edges from sample data
        assert graph.has_edge("1", "2")
        assert graph.has_edge("1", "3")
        assert graph.has_edge("2", "4")
        assert graph.has_edge("2", "5")
        assert graph.has_edge("3", "6")

    def test_create_graph_structure_with_duplicates(self) -> None:
        """Test graph creation with duplicate edges."""
        df = pd.DataFrame({"parent": [1, 1, 2, 2], "child": [2, 2, 3, 3]})
        processor = GraphProcessing()
        graph = processor.create_graph_structure(df, "parent", "child")

        assert graph.number_of_edges() == 2  # duplicates should be merged
        assert graph.has_edge("1", "2")
        assert graph.has_edge("2", "3")

    def test_create_graph_structure_with_numeric_values(self) -> None:
        """Test graph creation with various numeric types."""
        df = pd.DataFrame({"parent": [1.0, 2, 3.5], "child": [2, 3.0, 4]})
        processor = GraphProcessing()
        graph = processor.create_graph_structure(df, "parent", "child")

        assert graph.number_of_nodes() == 5  # 1.0, 2.0, 3.0, 3.5, 4.0
        assert graph.has_edge("1.0", "2.0")
        assert graph.has_edge("2.0", "3.0")
        assert graph.has_edge("3.5", "4.0")

    def test_detect_cycles_no_cycle(self, graph_processor: GraphProcessing) -> None:
        """Test cycle detection on acyclic graph."""
        has_cycle, cycle_edges = graph_processor.detect_cycles()

        assert has_cycle is False
        assert cycle_edges is None

    def test_detect_cycles_with_cycle(self, cyclic_dataframe: pd.DataFrame) -> None:
        """Test cycle detection on cyclic graph."""
        processor = GraphProcessing(cyclic_dataframe, "parent", "child")
        has_cycle, cycle_edges = processor.detect_cycles()

        assert has_cycle is True
        assert cycle_edges is not None
        assert len(cycle_edges) == 3  # cycle of length 3

    def test_detect_cycles_with_external_graph(self, empty_graph_processor: GraphProcessing) -> None:
        """Test cycle detection with external graph parameter."""
        # Create a cyclic graph
        graph = nx.DiGraph()
        graph.add_edges_from([("1", "2"), ("2", "3"), ("3", "1")])

        has_cycle, cycle_edges = empty_graph_processor.detect_cycles(graph)

        assert has_cycle is True
        assert cycle_edges is not None

    def test_detect_cycles_no_graph_raises_error(self, empty_graph_processor: GraphProcessing) -> None:
        """Test cycle detection without graph raises ValueError."""
        with pytest.raises(ValueError, match="No graph available for cycle detection"):
            empty_graph_processor.detect_cycles()

    def test_detect_disconnected_components_connected_graph(self, graph_processor: GraphProcessing) -> None:
        """Test disconnected components detection on connected graph."""
        disconnected_components = graph_processor.detect_disconnected_components()

        assert len(disconnected_components) == 0

    def test_detect_disconnected_components_with_disconnected_graph(self, disconnected_dataframe: pd.DataFrame) -> None:
        """Test disconnected components detection on disconnected graph."""
        processor = GraphProcessing(disconnected_dataframe, "parent", "child")
        disconnected_components = processor.detect_disconnected_components()

        assert len(disconnected_components) == 1  # One smaller component
        smaller_component = disconnected_components[0]
        assert smaller_component.number_of_nodes() == 3  # nodes 10, 11, 12

    def test_detect_disconnected_components_with_external_graph(self, empty_graph_processor: GraphProcessing) -> None:
        """Test disconnected components detection with external graph."""
        graph = nx.DiGraph()
        graph.add_edges_from([("1", "2"), ("3", "4")])  # Two disconnected components

        components = empty_graph_processor.detect_disconnected_components(graph)

        assert len(components) == 1  # One smaller component

    def test_detect_disconnected_components_no_graph_raises_error(self, empty_graph_processor: GraphProcessing) -> None:
        """Test disconnected components detection without graph raises ValueError."""
        with pytest.raises(ValueError, match="No graph available for disconnected component detection"):
            empty_graph_processor.detect_disconnected_components()

    def test_generate_graph_report_basic(self, graph_processor: GraphProcessing) -> None:
        """Test graph report generation with basic data."""
        report = graph_processor.generate_graph_report()

        assert isinstance(report, str)
        assert "1 -> 2" in report
        assert "1 -> 3" in report
        assert "2 -> 4" in report
        assert "2 -> 5" in report
        assert "3 -> 6" in report

    def test_generate_graph_report_with_float_conversion(self) -> None:
        """Test graph report with float values that should be converted to integers."""
        df = pd.DataFrame({"parent": [1.0, 2.0], "child": [2.0, 3.0]})
        processor = GraphProcessing(df, "parent", "child")
        report = processor.generate_graph_report()

        assert "1 -> 2" in report
        assert "2 -> 3" in report

    def test_generate_graph_report_with_actual_floats(self) -> None:
        """Test graph report with actual float values."""
        df = pd.DataFrame({"parent": [1.5, 2.7], "child": [2.3, 3.8]})
        processor = GraphProcessing(df, "parent", "child")
        report = processor.generate_graph_report()

        assert "1.5 -> 2.3" in report
        assert "2.7 -> 3.8" in report

    def test_generate_graph_report_sorted_output(self) -> None:
        """Test that graph report output is sorted."""
        df = pd.DataFrame({"parent": [3, 1, 2], "child": [6, 4, 5]})
        processor = GraphProcessing(df, "parent", "child")
        report = processor.generate_graph_report()

        # Check that the output is sorted
        edges = report.split(", ")
        sorted_edges = sorted(edges)
        assert edges == sorted_edges

    def test_generate_graph_report_with_external_graph(self, empty_graph_processor: GraphProcessing) -> None:
        """Test graph report generation with external graph."""
        graph = nx.DiGraph()
        graph.add_edges_from([("1", "2"), ("2", "3")])

        report = empty_graph_processor.generate_graph_report(graph)

        assert "1 -> 2" in report
        assert "2 -> 3" in report

    def test_generate_graph_report_no_graph_raises_error(self, empty_graph_processor: GraphProcessing) -> None:
        """Test graph report generation without graph raises ValueError."""
        with pytest.raises(ValueError, match="No graph available for report generation"):
            empty_graph_processor.generate_graph_report()

    def test_get_leaf_nodes_basic(self, graph_processor: GraphProcessing) -> None:
        """Test leaf nodes detection with basic graph."""
        leaf_nodes = graph_processor.get_leaf_nodes()

        assert len(leaf_nodes) == 3  # nodes 4, 5, 6 are leaf nodes
        assert set(leaf_nodes) == {"4", "5", "6"}

    def test_get_leaf_nodes_single_node(self, single_node_dataframe: pd.DataFrame) -> None:
        """Test leaf nodes detection with single edge graph."""
        processor = GraphProcessing(single_node_dataframe, "parent", "child")
        leaf_nodes = processor.get_leaf_nodes()

        assert len(leaf_nodes) == 1
        assert leaf_nodes[0] == "2"

    def test_get_leaf_nodes_cyclic_graph(self, cyclic_dataframe: pd.DataFrame) -> None:
        """Test leaf nodes detection with cyclic graph."""
        processor = GraphProcessing(cyclic_dataframe, "parent", "child")
        leaf_nodes = processor.get_leaf_nodes()

        assert len(leaf_nodes) == 0  # No leaf nodes in a cycle

    def test_get_leaf_nodes_with_external_graph(self, empty_graph_processor: GraphProcessing) -> None:
        """Test leaf nodes detection with external graph."""
        graph = nx.DiGraph()
        graph.add_edges_from([("1", "2"), ("1", "3")])

        leaf_nodes = empty_graph_processor.get_leaf_nodes(graph)

        assert len(leaf_nodes) == 2
        assert set(leaf_nodes) == {"2", "3"}

    def test_get_leaf_nodes_no_graph_raises_error(self, empty_graph_processor: GraphProcessing) -> None:
        """Test leaf nodes detection without graph raises ValueError."""
        with pytest.raises(ValueError, match="No graph available for leaf node detection"):
            empty_graph_processor.get_leaf_nodes()

    def test_convert_to_tree_basic(self, graph_processor: GraphProcessing) -> None:
        """Test tree conversion with valid root node."""
        tree = graph_processor.convert_to_tree("1")

        assert isinstance(tree, nx.DiGraph)
        assert tree.number_of_nodes() == 6
        assert nx.is_tree(tree)

    def test_convert_to_tree_with_external_graph(self, empty_graph_processor: GraphProcessing) -> None:
        """Test tree conversion with external graph."""
        graph = nx.DiGraph()
        graph.add_edges_from([("1", "2"), ("1", "3"), ("2", "4")])

        tree = empty_graph_processor.convert_to_tree("1", graph)

        assert isinstance(tree, nx.DiGraph)
        assert nx.is_tree(tree)

    def test_convert_to_tree_invalid_root_raises_error(self, graph_processor: GraphProcessing) -> None:
        """Test tree conversion with invalid root node raises ValueError."""
        with pytest.raises(ValueError, match="Root node 'invalid' not found in the graph nodes"):
            graph_processor.convert_to_tree("invalid")

    def test_convert_to_tree_no_graph_raises_error(self, empty_graph_processor: GraphProcessing) -> None:
        """Test tree conversion without graph raises ValueError."""
        with pytest.raises(ValueError, match="No graph available for tree conversion"):
            empty_graph_processor.convert_to_tree("1")

    def test_breadth_first_search_from_node_basic(self, graph_processor: GraphProcessing) -> None:
        """Test BFS from valid start node."""
        bfs_tree = graph_processor.breadth_first_search_from_node("1")

        assert isinstance(bfs_tree, nx.DiGraph)
        assert bfs_tree.number_of_nodes() == 6
        assert nx.is_tree(bfs_tree)

    def test_breadth_first_search_from_node_with_external_graph(self, empty_graph_processor: GraphProcessing) -> None:
        """Test BFS with external graph."""
        graph = nx.DiGraph()
        graph.add_edges_from([("1", "2"), ("1", "3"), ("2", "4")])

        bfs_tree = empty_graph_processor.breadth_first_search_from_node("1", graph)

        assert isinstance(bfs_tree, nx.DiGraph)
        assert nx.is_tree(bfs_tree)

    def test_breadth_first_search_from_node_invalid_start_raises_error(self, graph_processor: GraphProcessing) -> None:
        """Test BFS with invalid start node raises ValueError."""
        with pytest.raises(ValueError, match="Start node 'invalid' not found in the graph nodes"):
            graph_processor.breadth_first_search_from_node("invalid")

    def test_breadth_first_search_from_node_no_graph_raises_error(self, empty_graph_processor: GraphProcessing) -> None:
        """Test BFS without graph raises ValueError."""
        with pytest.raises(ValueError, match="No graph available for BFS"):
            empty_graph_processor.breadth_first_search_from_node("1")

    def test_node_count_property(self, graph_processor: GraphProcessing) -> None:
        """Test node count property."""
        assert graph_processor.node_count == 6

    def test_node_count_property_no_graph(self, empty_graph_processor: GraphProcessing) -> None:
        """Test node count property with no graph."""
        assert empty_graph_processor.node_count == 0

    def test_edge_count_property(self, graph_processor: GraphProcessing) -> None:
        """Test edge count property."""
        assert graph_processor.edge_count == 5

    def test_edge_count_property_no_graph(self, empty_graph_processor: GraphProcessing) -> None:
        """Test edge count property with no graph."""
        assert empty_graph_processor.edge_count == 0

    def test_is_empty_property_with_graph(self, graph_processor: GraphProcessing) -> None:
        """Test is_empty property with graph."""
        assert graph_processor.is_empty is False

    def test_is_empty_property_no_graph(self, empty_graph_processor: GraphProcessing) -> None:
        """Test is_empty property with no graph."""
        assert empty_graph_processor.is_empty is True

    def test_is_empty_property_empty_graph(self) -> None:
        """Test is_empty property with empty graph."""
        processor = GraphProcessing()
        processor.graph = nx.DiGraph()  # Empty graph

        assert processor.is_empty is True


class TestGraphProcessingDataDrivenTests:
    """Data-driven tests for GraphProcessing class."""

    @pytest.mark.parametrize(
        "parent_values,child_values,expected_nodes,expected_edges",
        [
            ([1, 2], [2, 3], 3, 2),
            ([1, 1, 2], [2, 3, 4], 4, 3),
            ([1], [2], 2, 1),
            ([], [], 0, 0),
            ([1, 2, 3, 4], [2, 3, 4, 5], 5, 4),
        ],
    )
    def test_graph_creation_data_driven(
        self,
        parent_values: List[int],
        child_values: List[int],
        expected_nodes: int,
        expected_edges: int,
    ) -> None:
        """Test graph creation with various data configurations."""
        if not parent_values:  # Empty case
            df = pd.DataFrame({"parent": [], "child": []})
            processor = GraphProcessing(df, "parent", "child")
            assert processor.graph is None
            return

        df = pd.DataFrame({"parent": parent_values, "child": child_values})
        processor = GraphProcessing(df, "parent", "child")

        assert processor.node_count == expected_nodes
        assert processor.edge_count == expected_edges

    @pytest.mark.parametrize(
        "edges,has_cycle",
        [
            ([("1", "2"), ("2", "3")], False),
            ([("1", "2"), ("2", "3"), ("3", "1")], True),
            ([("1", "2")], False),
            ([("1", "2"), ("2", "3"), ("3", "4"), ("4", "2")], True),
            ([], False),
        ],
    )
    def test_cycle_detection_data_driven(self, edges: List[Tuple[str, str]], has_cycle: bool) -> None:
        """Test cycle detection with various graph configurations."""
        processor = GraphProcessing()
        graph = nx.DiGraph()
        graph.add_edges_from(edges)

        detected_cycle, _ = processor.detect_cycles(graph)
        assert detected_cycle == has_cycle

    @pytest.mark.parametrize(
        "edges,expected_leaf_count",
        [
            ([("1", "2"), ("1", "3")], 2),  # 2 and 3 are leaves
            ([("1", "2"), ("2", "3")], 1),  # 3 is leaf
            ([("1", "2"), ("2", "1")], 0),  # cycle, no leaves
            ([("1", "2")], 1),  # 2 is leaf
            ([], 0),  # empty graph
        ],
    )
    def test_leaf_nodes_detection_data_driven(self, edges: List[Tuple[str, str]], expected_leaf_count: int) -> None:
        """Test leaf nodes detection with various graph configurations."""
        processor = GraphProcessing()
        graph = nx.DiGraph()
        graph.add_edges_from(edges)

        leaf_nodes = processor.get_leaf_nodes(graph)
        assert len(leaf_nodes) == expected_leaf_count

    @pytest.mark.parametrize(
        "edges,disconnected_components_count",
        [
            ([("1", "2"), ("3", "4")], 1),  # Two components, one smaller
            ([("1", "2"), ("2", "3")], 0),  # One connected component
            ([("1", "2"), ("3", "4"), ("5", "6")], 2),  # Three components, two smaller
            ([], 0),  # Empty graph
        ],
    )
    def test_disconnected_components_data_driven(self, edges: List[Tuple[str, str]], disconnected_components_count: int) -> None:
        """Test disconnected components detection with various configurations."""
        processor = GraphProcessing()
        graph = nx.DiGraph()
        graph.add_edges_from(edges)

        components = processor.detect_disconnected_components(graph)
        assert len(components) == disconnected_components_count


class TestGraphProcessingEdgeCases:
    """Edge cases and boundary condition tests for GraphProcessing."""

    def test_large_graph_performance(self) -> None:
        """Test with large graph to ensure performance."""
        # Create a large graph
        size = 1000
        parent_values = list(range(size))
        child_values = list(range(1, size + 1))

        df = pd.DataFrame({"parent": parent_values, "child": child_values})
        processor = GraphProcessing(df, "parent", "child")

        assert processor.node_count == size + 1
        assert processor.edge_count == size

    def test_self_loop_handling(self) -> None:
        """Test graph with self-loops."""
        df = pd.DataFrame({"parent": [1, 2, 2], "child": [1, 2, 3]})
        processor = GraphProcessing(df, "parent", "child")

        assert processor.graph.has_edge("1", "1")
        assert processor.graph.has_edge("2", "2")
        assert processor.graph.has_edge("2", "3")

    def test_string_node_values(self) -> None:
        """Test graph with string node values."""
        df = pd.DataFrame({"parent": ["A", "B", "C"], "child": ["B", "C", "D"]})
        processor = GraphProcessing(df, "parent", "child")

        assert processor.node_count == 4
        assert processor.graph.has_edge("A", "B")
        assert processor.graph.has_edge("B", "C")
        assert processor.graph.has_edge("C", "D")

    def test_mixed_type_node_values(self) -> None:
        """Test graph with mixed type node values."""
        df = pd.DataFrame({"parent": [1, "B", 3.0], "child": ["A", 2, "C"]})
        processor = GraphProcessing(df, "parent", "child")

        assert processor.node_count == 6  # All nodes are converted to strings
        assert processor.graph.has_edge("1", "A")
        assert processor.graph.has_edge("B", "2")
        assert processor.graph.has_edge("3.0", "C")

    def test_none_values_handling(self) -> None:
        """Test graph with None values."""
        df = pd.DataFrame({"parent": [1, None, 3], "child": [2, 3, None]})
        processor = GraphProcessing(df, "parent", "child")

        # NetworkX should handle None values as string "nan"
        assert processor.graph.has_edge("1.0", "2.0")
        assert processor.graph.has_edge("nan", "3.0")
        assert processor.graph.has_edge("3.0", "nan")

    def test_duplicate_column_names(self) -> None:
        """Test handling when parent and child columns are the same."""
        df = pd.DataFrame({"node": [1, 2, 3], "value": [2, 3, 4]})
        processor = GraphProcessing(df, "node", "node")

        # Should create self-loops
        assert processor.graph.has_edge("1", "1")
        assert processor.graph.has_edge("2", "2")
        assert processor.graph.has_edge("3", "3")

    def test_very_long_node_names(self) -> None:
        """Test graph with very long node names."""
        long_name_1 = "a" * 1000
        long_name_2 = "b" * 1000

        df = pd.DataFrame({"parent": [long_name_1], "child": [long_name_2]})
        processor = GraphProcessing(df, "parent", "child")

        assert processor.node_count == 2
        assert processor.graph.has_edge(long_name_1, long_name_2)

    def test_unicode_node_values(self) -> None:
        """Test graph with Unicode node values."""
        df = pd.DataFrame({"parent": ["αβγ", "测试", "🌟"], "child": ["δεζ", "试验", "⭐"]})
        processor = GraphProcessing(df, "parent", "child")

        assert processor.node_count == 6
        assert processor.graph.has_edge("αβγ", "δεζ")
        assert processor.graph.has_edge("测试", "试验")
        assert processor.graph.has_edge("🌟", "⭐")


class TestGraphProcessingIntegration:
    """Integration tests combining multiple GraphProcessing features."""

    def test_complete_workflow_tree_analysis(self) -> None:
        """Test complete workflow for tree analysis."""
        # Create hierarchical tree data
        df = pd.DataFrame({"parent": [1, 1, 2, 2, 3, 3], "child": [2, 3, 4, 5, 6, 7]})
        processor = GraphProcessing(df, "parent", "child")

        # Verify it's acyclic
        has_cycle, _ = processor.detect_cycles()
        assert has_cycle is False

        # Check if connected
        disconnected = processor.detect_disconnected_components()
        assert len(disconnected) == 0

        # Get leaf nodes
        leaves = processor.get_leaf_nodes()
        assert set(leaves) == {"4", "5", "6", "7"}

        # Convert to tree from root
        tree = processor.convert_to_tree("1")
        assert nx.is_tree(tree)

        # Generate report
        report = processor.generate_graph_report()
        assert "1 -> 2" in report
        assert "1 -> 3" in report

    def test_complete_workflow_cyclic_analysis(self) -> None:
        """Test complete workflow for cyclic graph analysis."""
        # Create cyclic graph
        df = pd.DataFrame({"parent": [1, 2, 3, 4], "child": [2, 3, 4, 1]})
        processor = GraphProcessing(df, "parent", "child")

        # Verify it has cycle
        has_cycle, cycle_edges = processor.detect_cycles()
        assert has_cycle is True
        assert cycle_edges is not None
        assert len(cycle_edges) == 4

        # Should have no leaf nodes
        leaves = processor.get_leaf_nodes()
        assert len(leaves) == 0

        # Should still be able to do BFS from any node
        bfs_tree = processor.breadth_first_search_from_node("1")
        assert isinstance(bfs_tree, nx.DiGraph)

    def test_complete_workflow_disconnected_analysis(self) -> None:
        """Test complete workflow for disconnected graph analysis."""
        # Create disconnected components
        df = pd.DataFrame({"parent": [1, 2, 10, 11, 20], "child": [2, 3, 11, 12, 21]})
        processor = GraphProcessing(df, "parent", "child")

        # Should have disconnected components
        components = processor.detect_disconnected_components()
        assert len(components) == 2  # Two smaller components

        # Should be able to analyze each component separately
        for component in components:
            component_processor = GraphProcessing()
            has_cycle, _ = component_processor.detect_cycles(component)
            assert has_cycle is False  # Each component is acyclic

            leaves = component_processor.get_leaf_nodes(component)
            assert len(leaves) >= 1  # Each component should have at least one leaf
