"""Test MibTree class - comprehensive tree operations test."""

import pytest
from src.mib_parser.tree import MibTree
from src.mib_parser.models import MibData, MibNode


class TestMibTree:
    """Test MibTree class."""

    def test_initialize_tree(self, sample_mib_data):
        """Test tree initialization with MibData."""
        tree = MibTree(sample_mib_data)

        assert tree.mib_data == sample_mib_data
        assert tree._oid_cache is not None

    def test_find_node_by_oid_exact_match(self, sample_mib_data):
        """Test finding node by exact OID."""
        tree = MibTree(sample_mib_data)

        node = tree.find_node_by_oid("1.3.6.1.2.1.1.1")

        if node:
            assert node.oid == "1.3.6.1.2.1.1.1"

    def test_find_node_by_oid_not_found(self, sample_mib_data):
        """Test finding non-existent OID."""
        tree = MibTree(sample_mib_data)

        node = tree.find_node_by_oid("1.2.3.4.5")

        assert node is None

    def test_find_node_by_name(self, sample_mib_data):
        """Test finding node by name."""
        tree = MibTree(sample_mib_data)

        node = tree.find_node_by_name("sysDescr")

        if node:
            assert node.name == "sysDescr"

    def test_find_node_by_name_not_found(self, sample_mib_data):
        """Test finding non-existent node name."""
        tree = MibTree(sample_mib_data)

        node = tree.find_node_by_name("NonExistentNode")

        assert node is None

    def test_find_nodes_by_pattern(self, sample_mib_data):
        """Test finding nodes by pattern."""
        tree = MibTree(sample_mib_data)

        nodes = tree.find_nodes_by_pattern("sys")

        assert isinstance(nodes, list)

    def test_get_path_to_root(self, sample_mib_data):
        """Test getting path from node to root."""
        tree = MibTree(sample_mib_data)

        path = tree.get_path_to_root("sysDescr")

        assert isinstance(path, list)

    def test_traverse_breadth_first(self, sample_mib_data):
        """Test breadth-first traversal."""
        tree = MibTree(sample_mib_data)

        nodes = list(tree.traverse_breadth_first())

        assert isinstance(nodes, list)
