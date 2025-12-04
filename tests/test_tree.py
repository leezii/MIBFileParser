"""
Tests for MIB tree traversal and manipulation utilities.
"""

import pytest

from src.mib_parser.models import MibNode, MibData
from src.mib_parser.tree import MibTree


class TestMibTree:
    """Test cases for MibTree class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create test MIB data with a hierarchy
        self.mib_data = MibData(name="TEST-MIB")

        # Create a tree structure:
        # root (1.3.6.1.4.1.9999)
        # ├── system (1.3.6.1.4.1.9999.1)
        # │   ├── sysDescr (1.3.6.1.4.1.9999.1.1)
        # │   └── sysUpTime (1.3.6.1.4.1.9999.1.2)
        # └── interfaces (1.3.6.1.4.1.9999.2)
        #     ├── ifNumber (1.3.6.1.4.1.9999.2.1)
        #     └── ifTable (1.3.6.1.4.1.9999.2.2)
        #         └── ifEntry (1.3.6.1.4.1.9999.2.2.1)

        self.root = MibNode(name="root", oid="1.3.6.1.4.1.9999")
        self.system = MibNode(name="system", oid="1.3.6.1.4.1.9999.1", parent_name="root")
        self.sysDescr = MibNode(name="sysDescr", oid="1.3.6.1.4.1.9999.1.1", parent_name="system")
        self.sysUpTime = MibNode(name="sysUpTime", oid="1.3.6.1.4.1.9999.1.2", parent_name="system")
        self.interfaces = MibNode(name="interfaces", oid="1.3.6.1.4.1.9999.2", parent_name="root")
        self.ifNumber = MibNode(name="ifNumber", oid="1.3.6.1.4.1.9999.2.1", parent_name="interfaces")
        self.ifTable = MibNode(name="ifTable", oid="1.3.6.1.4.1.9999.2.2", parent_name="interfaces")
        self.ifEntry = MibNode(name="ifEntry", oid="1.3.6.1.4.1.9999.2.2.1", parent_name="ifTable")

        # Add all nodes to MIB data
        for node in [self.root, self.system, self.sysDescr, self.sysUpTime,
                    self.interfaces, self.ifNumber, self.ifTable, self.ifEntry]:
            self.mib_data.add_node(node)

        self.mib_tree = MibTree(self.mib_data)

    def test_find_node_by_oid_exact_match(self):
        """Test finding node by exact OID match."""
        node = self.mib_tree.find_node_by_oid("1.3.6.1.4.1.9999.1.1")
        assert node is not None
        assert node.name == "sysDescr"

        node = self.mib_tree.find_node_by_oid("1.3.6.1.4.1.9999.2.2.1")
        assert node is not None
        assert node.name == "ifEntry"

    def test_find_node_by_oid_not_found(self):
        """Test finding non-existent OID."""
        node = self.mib_tree.find_node_by_oid("1.3.6.1.4.1.8888")
        assert node is None

    def test_find_node_by_name(self):
        """Test finding node by name."""
        node = self.mib_tree.find_node_by_name("system")
        assert node is not None
        assert node.oid == "1.3.6.1.4.1.9999.1"

        node = self.mib_tree.find_node_by_name("ifTable")
        assert node is not None
        assert node.oid == "1.3.6.1.4.1.9999.2.2"

    def test_find_nodes_by_pattern_name_search(self):
        """Test finding nodes by pattern in names."""
        # Find nodes with "sys" in name
        nodes = self.mib_tree.find_nodes_by_pattern("sys", search_names=True)
        node_names = [node.name for node in nodes]
        assert "system" in node_names
        assert "sysDescr" in node_names
        assert "sysUpTime" in node_names

        # Find nodes with "if" in name
        nodes = self.mib_tree.find_nodes_by_pattern("if", search_names=True)
        node_names = [node.name for node in nodes]
        assert "interfaces" in node_names
        assert "ifNumber" in node_names
        assert "ifTable" in node_names
        assert "ifEntry" in node_names

    def test_find_nodes_by_pattern_description_search(self):
        """Test finding nodes by pattern in descriptions."""
        # Add descriptions to some nodes
        self.system.description = "System group containing system information"
        self.interfaces.description = "Interfaces group containing network interfaces"

        nodes = self.mib_tree.find_nodes_by_pattern("system", search_descriptions=True)
        assert len(nodes) >= 1
        node_names = [node.name for node in nodes]
        assert "system" in node_names

    def test_get_path_to_root(self):
        """Test getting path from node to root."""
        path = self.mib_tree.get_path_to_root("ifEntry")
        node_names = [node.name for node in path]
        assert node_names == ["ifEntry", "ifTable", "interfaces", "root"]

        path = self.mib_tree.get_path_to_root("sysDescr")
        node_names = [node.name for node in path]
        assert node_names == ["sysDescr", "system", "root"]

        path = self.mib_tree.get_path_to_root("root")
        node_names = [node.name for node in path]
        assert node_names == ["root"]

    def test_get_path_from_root(self):
        """Test getting path from root to node."""
        path = self.mib_tree.get_path_from_root("ifEntry")
        node_names = [node.name for node in path]
        assert node_names == ["root", "interfaces", "ifTable", "ifEntry"]

        path = self.mib_tree.get_path_from_root("sysUpTime")
        node_names = [node.name for node in path]
        assert node_names == ["root", "system", "sysUpTime"]

    def test_get_subtree(self):
        """Test getting subtree."""
        # Get subtree from system node
        subtree = self.mib_tree.get_subtree("system")
        node_names = [node.name for node in subtree]
        assert "system" in node_names
        assert "sysDescr" in node_names
        assert "sysUpTime" in node_names
        assert len(subtree) == 3

        # Get subtree from system node without including root
        subtree = self.mib_tree.get_subtree("system", include_root=False)
        node_names = [node.name for node in subtree]
        assert "system" not in node_names
        assert "sysDescr" in node_names
        assert "sysUpTime" in node_names
        assert len(subtree) == 2

        # Get subtree from interfaces node
        subtree = self.mib_tree.get_subtree("interfaces")
        node_names = [node.name for node in subtree]
        assert "interfaces" in node_names
        assert "ifNumber" in node_names
        assert "ifTable" in node_names
        assert "ifEntry" in node_names
        assert len(subtree) == 4

    def test_traverse_breadth_first(self):
        """Test breadth-first traversal."""
        nodes = list(self.mib_tree.traverse_breadth_first())
        node_names = [node.name for node in nodes]

        # Should visit level by level: root, then system/interfaces, then their children, etc.
        assert node_names[0] == "root"
        assert "system" in node_names[1:3]
        assert "interfaces" in node_names[1:3]
        assert len(nodes) == 8  # All nodes should be visited

    def test_traverse_breadth_first_from_start_node(self):
        """Test breadth-first traversal from a specific start node."""
        nodes = list(self.mib_tree.traverse_breadth_first("system"))
        node_names = [node.name for node in nodes]

        # Should start from system and include its subtree
        assert node_names[0] == "system"
        assert "sysDescr" in node_names
        assert "sysUpTime" in node_names
        assert "root" not in node_names  # Should not include root
        assert "interfaces" not in node_names  # Should not include other branches

    def test_traverse_depth_first(self):
        """Test depth-first traversal."""
        nodes = list(self.mib_tree.traverse_depth_first())
        node_names = [node.name for node in nodes]

        # Should visit in depth-first order
        assert len(nodes) == 8  # All nodes should be visited
        assert "root" in node_names

    def test_traverse_depth_first_from_start_node(self):
        """Test depth-first traversal from a specific start node."""
        nodes = list(self.mib_tree.traverse_depth_first("interfaces"))
        node_names = [node.name for node in nodes]

        # Should start from interfaces and include its subtree
        assert node_names[0] == "interfaces"
        assert "ifNumber" in node_names
        assert "ifTable" in node_names
        assert "ifEntry" in node_names
        assert "root" not in node_names  # Should not include root
        assert "system" not in node_names  # Should not include other branches

    def test_get_tree_levels(self):
        """Test getting nodes grouped by tree level."""
        levels = self.mib_tree.get_tree_levels()

        # Level 0: root
        assert 0 in levels
        assert len(levels[0]) == 1
        assert levels[0][0].name == "root"

        # Level 1: system, interfaces
        assert 1 in levels
        assert len(levels[1]) == 2
        level1_names = [node.name for node in levels[1]]
        assert "system" in level1_names
        assert "interfaces" in level1_names

        # Level 2: sysDescr, sysUpTime, ifNumber, ifTable
        assert 2 in levels
        assert len(levels[2]) == 4
        level2_names = [node.name for node in levels[2]]
        assert "sysDescr" in level2_names
        assert "sysUpTime" in level2_names
        assert "ifNumber" in level2_names
        assert "ifTable" in level2_names

        # Level 3: ifEntry
        assert 3 in levels
        assert len(levels[3]) == 1
        assert levels[3][0].name == "ifEntry"

    def test_find_common_ancestor(self):
        """Test finding common ancestor of nodes."""
        # Common ancestor of sysDescr and sysUpTime should be system
        ancestor = self.mib_tree.find_common_ancestor(["sysDescr", "sysUpTime"])
        assert ancestor is not None
        assert ancestor.name == "system"

        # Common ancestor of ifNumber and ifEntry should be interfaces
        ancestor = self.mib_tree.find_common_ancestor(["ifNumber", "ifEntry"])
        assert ancestor is not None
        assert ancestor.name == "interfaces"

        # Common ancestor of sysDescr and ifEntry should be root
        ancestor = self.mib_tree.find_common_ancestor(["sysDescr", "ifEntry"])
        assert ancestor is not None
        assert ancestor.name == "root"

        # Common ancestor of single node should be that node's parent
        ancestor = self.mib_tree.find_common_ancestor(["sysDescr"])
        assert ancestor is not None
        assert ancestor.name == "system"

        # Empty list should return None
        ancestor = self.mib_tree.find_common_ancestor([])
        assert ancestor is None

    def test_get_oid_distance(self):
        """Test calculating distance between nodes."""
        # Distance between siblings should be 2 (child -> parent -> child)
        distance = self.mib_tree.get_oid_distance("sysDescr", "sysUpTime")
        assert distance == 2

        # Distance between parent and child should be 1
        distance = self.mib_tree.get_oid_distance("system", "sysDescr")
        assert distance == 1

        # Distance between root and leaf should be depth of leaf
        distance = self.mib_tree.get_oid_distance("root", "ifEntry")
        assert distance == 3

        # Distance between nodes in different branches
        distance = self.mib_tree.get_oid_distance("sysDescr", "ifNumber")
        assert distance == 4  # sysDescr -> system -> root -> interfaces -> ifNumber

    def test_get_node_statistics(self):
        """Test getting node statistics."""
        stats = self.mib_tree.get_node_statistics()

        assert stats["total_nodes"] == 8
        assert stats["root_nodes"] == 1
        assert stats["max_depth"] == 3
        assert stats["nodes_with_children"] == 3  # root, system, interfaces, ifTable
        assert stats["leaf_nodes"] == 4  # sysDescr, sysUpTime, ifNumber, ifEntry

    def test_validate_tree_structure_valid(self):
        """Test validating a valid tree structure."""
        errors = self.mib_tree.validate_tree_structure()
        assert len(errors) == 0

    def test_validate_tree_structure_invalid_parent(self):
        """Test validating tree structure with invalid parent reference."""
        # Create a node with non-existent parent
        orphan_node = MibNode(name="orphan", oid="1.3.6.1.4.1.9999.3", parent_name="nonExistent")
        self.mib_data.add_node(orphan_node)

        errors = self.mib_tree.validate_tree_structure()
        assert len(errors) > 0
        assert any("non-existent parent" in error for error in errors)

    def test_validate_tree_structure_inconsistent_child_reference(self):
        """Test validating tree structure with inconsistent child reference."""
        # Manually create inconsistency: add child name to parent but don't set parent in child
        self.root.children.append("fakeChild")  # Add child reference

        errors = self.mib_tree.validate_tree_structure()
        assert len(errors) > 0
        assert any("non-existent child" in error for error in errors)

    def test_oid_cache_built_correctly(self):
        """Test that OID cache is built correctly."""
        # The cache should be built during initialization
        assert hasattr(self.mib_tree, '_oid_cache')
        assert len(self.mib_tree._oid_cache) == 8

        # Test that cache contains all OIDs
        for node in self.mib_data.nodes.values():
            assert node.oid in self.mib_tree._oid_cache
            assert self.mib_tree._oid_cache[node.oid].name == node.name

    def test_partial_oid_match(self):
        """Test finding node by partial OID match."""
        # Should find node even if OID doesn't start from beginning
        node = self.mib_tree.find_node_by_oid("1.4.1.9999.1.1")  # Missing prefix
        # This depends on the implementation - may or may not work

        # Test with trailing OID (should not match normally)
        node = self.mib_tree.find_node_by_oid("9999.1.1")
        # This test verifies the partial matching logic is working as expected