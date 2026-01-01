"""Test TreeService class."""

import pytest
from src.flask_app.services.tree_service import TreeService


class TestTreeService:
    """Test TreeService class."""

    def test_build_tree_structure_empty_nodes(self):
        """Test building tree with no nodes."""
        service = TreeService()
        mib_data = {"name": "TEST-MIB", "nodes": {}}

        result = service.build_tree_structure(mib_data)

        assert result["name"] == "TEST-MIB"
        assert result["children"] == []

    def test_build_tree_structure_simple(self):
        """Test building tree with simple node hierarchy."""
        service = TreeService()
        mib_data = {
            "name": "TEST-MIB",
            "nodes": {
                "root": {"oid": "1.3.6.1", "name": "root"},
                "child": {"oid": "1.3.6.1.1", "name": "child"}
            }
        }

        result = service.build_tree_structure(mib_data)

        assert result["name"] == "TEST-MIB"
        assert len(result["children"]) > 0
        assert "statistics" in result

    def test_build_tree_structure_filters_tc_nodes(self):
        """Test that textual convention nodes are filtered out."""
        service = TreeService()
        mib_data = {
            "name": "TEST-MIB",
            "nodes": {
                "normalNode": {"oid": "1.3.6.1", "name": "normalNode"},
                "tcNode": {
                    "oid": "1.3.6.1.1",
                    "name": "tcNode",
                    "class": "textualconvention"
                }
            }
        }

        result = service.build_tree_structure(mib_data)

        # TC node should be filtered out
        total_nodes = result["statistics"]["total_nodes"]
        assert total_nodes == 1  # Only normalNode

    def test_build_tree_structure_with_metadata(self):
        """Test that node metadata is preserved."""
        service = TreeService()
        mib_data = {
            "name": "TEST-MIB",
            "description": "Test MIB",
            "nodes": {
                "node1": {
                    "oid": "1.3.6.1",
                    "name": "node1",
                    "description": "Test node",
                    "syntax": "Integer32",
                    "access": "read-only"
                }
            }
        }

        result = service.build_tree_structure(mib_data)

        assert result["description"] == "Test MIB"
        assert result["module"] == "TEST-MIB"

        # Check child node has metadata
        if result["children"]:
            child = result["children"][0]
            assert child["oid"] == "1.3.6.1"
            assert child["description"] == "Test node"
            assert child["syntax"] == "Integer32"

    def test_find_parent_by_oid_exact_match(self):
        """Test finding parent with exact OID match."""
        service = TreeService()
        node_map = {
            "parent": {"oid": "1.3.6.1", "name": "parent"},
            "child": {"oid": "1.3.6.1.1", "name": "child"}
        }

        parent = service._find_parent_by_oid("1.3.6.1.1", node_map)

        assert parent is not None
        assert parent["name"] == "parent"

    def test_find_parent_by_oid_no_parent(self):
        """Test finding parent when node is at root level."""
        service = TreeService()
        node_map = {
            "root": {"oid": "1.3", "name": "root"}
        }

        parent = service._find_parent_by_oid("1.3", node_map)

        assert parent is None

    def test_find_parent_by_oid_short_oid(self):
        """Test finding parent with very short OID."""
        service = TreeService()
        node_map = {
            "node1": {"oid": "1", "name": "node1"}
        }

        parent = service._find_parent_by_oid("1", node_map)

        assert parent is None  # Too short to have parent

    def test_calculate_tree_statistics(self):
        """Test tree statistics calculation."""
        service = TreeService()
        node_map = {
            "root": {"oid": "1", "name": "root", "children": []},
            "leaf": {"oid": "1.1", "name": "leaf", "children": []}
        }
        root_nodes = [{"oid": "1", "name": "root", "children": []}]

        stats = service._calculate_tree_statistics(node_map, root_nodes)

        assert "total_nodes" in stats
        assert "root_nodes" in stats
        assert "leaf_nodes" in stats
        assert "max_depth" in stats
        assert "average_children" in stats
        assert stats["total_nodes"] == 2

    def test_calculate_depth_leaf_node(self):
        """Test depth calculation for leaf node."""
        service = TreeService()
        node = {"name": "leaf", "children": []}

        depth = service._calculate_depth(node, current_depth=0)

        assert depth == 1  # Leaf has depth 1

    def test_calculate_depth_with_children(self):
        """Test depth calculation for node with children."""
        service = TreeService()
        node = {
            "name": "root",
            "children": [
                {"name": "child1", "children": []},
                {"name": "child2", "children": []}
            ]
        }

        depth = service._calculate_depth(node, current_depth=0)

        assert depth == 2  # Root -> child

    def test_build_breadth_first_tree_empty(self):
        """Test breadth-first tree with empty nodes."""
        service = TreeService()
        mib_data = {"name": "TEST-MIB", "nodes": {}}

        result = service.build_breadth_first_tree(mib_data)

        assert result == []

    def test_build_breadth_first_tree_simple(self):
        """Test building breadth-first tree."""
        service = TreeService()
        mib_data = {
            "name": "TEST-MIB",
            "nodes": {
                "node1": {"oid": "1.3.6.1", "name": "node1"},
                "node2": {"oid": "1.3.6.1.1", "name": "node2"}
            }
        }

        result = service.build_breadth_first_tree(mib_data)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_flatten_tree_without_paths(self):
        """Test flattening tree without paths."""
        service = TreeService()
        tree = {
            "name": "root",
            "children": [
                {"name": "child1", "children": []},
                {"name": "child2", "children": []}
            ]
        }

        result = service.flatten_tree(tree, include_paths=False)

        assert len(result) == 3  # root + 2 children
        # Children should not have 'children' key
        assert "children" not in result[1]

    def test_flatten_tree_with_paths(self):
        """Test flattening tree with paths."""
        service = TreeService()
        tree = {
            "name": "root",
            "children": [
                {"name": "child1", "children": []}
            ]
        }

        result = service.flatten_tree(tree, include_paths=True)

        assert len(result) == 2
        assert "path" in result[0]
        assert "path_string" in result[0]
        assert result[0]["path"] == ["root"]
        assert result[1]["path"] == ["root", "child1"]

    def test_flatten_tree_path_string_format(self):
        """Test path string formatting."""
        service = TreeService()
        tree = {
            "name": "root",
            "children": [
                {"name": "child", "children": []}
            ]
        }

        result = service.flatten_tree(tree, include_paths=True)

        assert result[1]["path_string"] == "root -> child"

    def test_build_tree_structure_with_mib_origin(self):
        """Test building tree with nodes that have mib_origin."""
        service = TreeService()
        mib_data = {
            "name": "ALL-MIBS",
            "nodes": {
                "mib1.node": {
                    "oid": "1.3.6.1",
                    "name": "mib1.node",
                    "original_name": "node",
                    "mib_origin": "mib1"
                }
            }
        }

        result = service.build_tree_structure(mib_data)

        if result["children"]:
            child = result["children"][0]
            assert child["name"] == "node"  # Should use original_name
            assert child["mib_origin"] == "mib1"

    def test_build_tree_structure_preserves_all_attributes(self):
        """Test that all node attributes are preserved."""
        service = TreeService()
        mib_data = {
            "name": "TEST-MIB",
            "nodes": {
                "testNode": {
                    "oid": "1.3.6.1",
                    "name": "testNode",
                    "description": "Test",
                    "syntax": "Integer32",
                    "access": "read-only",
                    "status": "current",
                    "units": "seconds",
                    "max_access": "read-only",
                    "reference": "RFC1234",
                    "defval": "0",
                    "hint": "1"
                }
            }
        }

        result = service.build_tree_structure(mib_data)

        if result["children"]:
            node = result["children"][0]
            # Check all attributes are preserved
            assert node["oid"] == "1.3.6.1"
            assert node["syntax"] == "Integer32"
            assert node["access"] == "read-only"
            assert node["status"] == "current"
            assert node["units"] == "seconds"
            assert node["max_access"] == "read-only"
            assert node["reference"] == "RFC1234"
            assert node["defval"] == "0"
            assert node["hint"] == "1"

    def test_calculate_depth_nested_tree(self):
        """Test depth calculation for deeply nested tree."""
        service = TreeService()
        node = {
            "name": "l1",
            "children": [
                {
                    "name": "l2",
                    "children": [
                        {
                            "name": "l3",
                            "children": [
                                {"name": "l4", "children": []}
                            ]
                        }
                    ]
                }
            ]
        }

        depth = service._calculate_depth(node, current_depth=0)

        assert depth == 4
