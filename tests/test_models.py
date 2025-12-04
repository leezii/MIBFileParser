"""
Tests for MIB data models.
"""

import pytest
from datetime import datetime

from src.mib_parser.models import MibNode, MibData


class TestMibNode:
    """Test cases for MibNode class."""

    def test_mib_node_creation(self):
        """Test creating a MibNode."""
        node = MibNode(
            name="testNode",
            oid="1.3.6.1.2.1.1.1",
            description="Test node description",
            syntax="INTEGER",
            access="read-only",
            status="current"
        )

        assert node.name == "testNode"
        assert node.oid == "1.3.6.1.2.1.1.1"
        assert node.description == "Test node description"
        assert node.syntax == "INTEGER"
        assert node.access == "read-only"
        assert node.status == "current"
        assert node.parent_name is None
        assert node.children == []

    def test_mib_node_with_parent(self):
        """Test creating a MibNode with parent and children."""
        node = MibNode(
            name="childNode",
            oid="1.3.6.1.2.1.1.1.1",
            parent_name="parentNode",
            children=["grandChild1", "grandChild2"]
        )

        assert node.parent_name == "parentNode"
        assert node.children == ["grandChild1", "grandChild2"]

    def test_mib_node_to_dict(self):
        """Test converting MibNode to dictionary."""
        node = MibNode(
            name="testNode",
            oid="1.3.6.1.2.1.1.1",
            description="Test description",
            syntax="INTEGER",
            access="read-only"
        )

        node_dict = node.to_dict()

        assert isinstance(node_dict, dict)
        assert node_dict["name"] == "testNode"
        assert node_dict["oid"] == "1.3.6.1.2.1.1.1"
        assert node_dict["description"] == "Test description"
        assert node_dict["syntax"] == "INTEGER"
        assert node_dict["access"] == "read-only"

    def test_mib_node_from_dict(self):
        """Test creating MibNode from dictionary."""
        data = {
            "name": "testNode",
            "oid": "1.3.6.1.2.1.1.1",
            "description": "Test description",
            "syntax": "INTEGER",
            "access": "read-only",
            "status": "current",
            "parent_name": None,
            "children": [],
            "module": "TEST-MIB",
            "text_convention": None,
            "units": None,
            "max_access": None,
            "reference": None,
            "defval": None,
            "hint": None,
        }

        node = MibNode.from_dict(data)

        assert node.name == "testNode"
        assert node.oid == "1.3.6.1.2.1.1.1"
        assert node.description == "Test description"
        assert node.syntax == "INTEGER"
        assert node.access == "read-only"
        assert node.status == "current"


class TestMibData:
    """Test cases for MibData class."""

    def test_mib_data_creation(self):
        """Test creating MibData."""
        mib_data = MibData(name="TEST-MIB")

        assert mib_data.name == "TEST-MIB"
        assert len(mib_data.nodes) == 0
        assert len(mib_data.imports) == 0
        assert len(mib_data.module_dependencies) == 0
        assert len(mib_data.root_oids) == 0
        assert mib_data.description is None
        assert mib_data.last_updated is None

    def test_mib_data_with_initial_values(self):
        """Test creating MibData with initial values."""
        mib_data = MibData(
            name="TEST-MIB",
            description="Test MIB module",
            imports=["SNMPv2-SMI"],
            module_dependencies=["SNMPv2-TC"],
            root_oids=["1.3.6.1.4.1.9999"]
        )

        assert mib_data.name == "TEST-MIB"
        assert mib_data.description == "Test MIB module"
        assert mib_data.imports == ["SNMPv2-SMI"]
        assert mib_data.module_dependencies == ["SNMPv2-TC"]
        assert mib_data.root_oids == ["1.3.6.1.4.1.9999"]

    def test_add_node(self):
        """Test adding nodes to MibData."""
        mib_data = MibData(name="TEST-MIB")

        # Create parent node
        parent = MibNode(
            name="parentNode",
            oid="1.3.6.1.4.1.9999.1"
        )

        # Create child node
        child = MibNode(
            name="childNode",
            oid="1.3.6.1.4.1.9999.1.1",
            parent_name="parentNode"
        )

        # Add nodes
        mib_data.add_node(parent)
        mib_data.add_node(child)

        assert len(mib_data.nodes) == 2
        assert "parentNode" in mib_data.nodes
        assert "childNode" in mib_data.nodes
        assert "childNode" in parent.children

    def test_get_node_by_oid(self):
        """Test finding node by OID."""
        mib_data = MibData(name="TEST-MIB")
        node = MibNode(name="testNode", oid="1.3.6.1.4.1.9999.1")
        mib_data.add_node(node)

        found_node = mib_data.get_node_by_oid("1.3.6.1.4.1.9999.1")
        assert found_node is not None
        assert found_node.name == "testNode"

        not_found = mib_data.get_node_by_oid("1.3.6.1.4.1.9999.2")
        assert not_found is None

    def test_get_node_by_name(self):
        """Test finding node by name."""
        mib_data = MibData(name="TEST-MIB")
        node = MibNode(name="testNode", oid="1.3.6.1.4.1.9999.1")
        mib_data.add_node(node)

        found_node = mib_data.get_node_by_name("testNode")
        assert found_node is not None
        assert found_node.oid == "1.3.6.1.4.1.9999.1"

        not_found = mib_data.get_node_by_name("nonExistentNode")
        assert not_found is None

    def test_get_root_nodes(self):
        """Test getting root nodes."""
        mib_data = MibData(name="TEST-MIB")

        # Add root node
        root = MibNode(name="rootNode", oid="1.3.6.1.4.1.9999.1")
        mib_data.add_node(root)

        # Add child node
        child = MibNode(name="childNode", oid="1.3.6.1.4.1.9999.1.1", parent_name="rootNode")
        mib_data.add_node(child)

        root_nodes = mib_data.get_root_nodes()
        assert len(root_nodes) == 1
        assert root_nodes[0].name == "rootNode"

    def test_get_children(self):
        """Test getting children of a node."""
        mib_data = MibData(name="TEST-MIB")

        # Create parent node
        parent = MibNode(name="parentNode", oid="1.3.6.1.4.1.9999.1")
        mib_data.add_node(parent)

        # Create child nodes
        child1 = MibNode(name="child1", oid="1.3.6.1.4.1.9999.1.1", parent_name="parentNode")
        child2 = MibNode(name="child2", oid="1.3.6.1.4.1.9999.1.2", parent_name="parentNode")

        mib_data.add_node(child1)
        mib_data.add_node(child2)

        children = mib_data.get_children("parentNode")
        assert len(children) == 2
        child_names = [child.name for child in children]
        assert "child1" in child_names
        assert "child2" in child_names

    def test_get_descendants(self):
        """Test getting all descendants of a node."""
        mib_data = MibData(name="TEST-MIB")

        # Create hierarchy: root -> child -> grandchild
        root = MibNode(name="root", oid="1.3.6.1.4.1.9999.1")
        child = MibNode(name="child", oid="1.3.6.1.4.1.9999.1.1", parent_name="root")
        grandchild = MibNode(name="grandchild", oid="1.3.6.1.4.1.9999.1.1.1", parent_name="child")

        mib_data.add_node(root)
        mib_data.add_node(child)
        mib_data.add_node(grandchild)

        descendants = mib_data.get_descendants("root")
        assert len(descendants) == 2
        descendant_names = [desc.name for desc in descendants]
        assert "child" in descendant_names
        assert "grandchild" in descendant_names

    def test_to_dict_and_from_dict(self):
        """Test converting MibData to and from dictionary."""
        # Create original MibData
        mib_data = MibData(
            name="TEST-MIB",
            description="Test MIB",
            imports=["SNMPv2-SMI"],
            module_dependencies=["SNMPv2-TC"],
            last_updated=datetime(2023, 1, 1, 12, 0, 0),
            root_oids=["1.3.6.1.4.1.9999"]
        )

        node = MibNode(
            name="testNode",
            oid="1.3.6.1.4.1.9999.1",
            description="Test node"
        )
        mib_data.add_node(node)

        # Convert to dict
        mib_dict = mib_data.to_dict()
        assert isinstance(mib_dict, dict)
        assert mib_dict["name"] == "TEST-MIB"
        assert mib_dict["description"] == "Test MIB"
        assert mib_dict["imports"] == ["SNMPv2-SMI"]
        assert mib_dict["module_dependencies"] == ["SNMPv2-TC"]
        assert mib_dict["root_oids"] == ["1.3.6.1.4.1.9999"]
        assert mib_dict["last_updated"] == "2023-01-01T12:00:00"
        assert "testNode" in mib_dict["nodes"]

        # Convert back from dict
        restored_mib = MibData.from_dict(mib_dict)
        assert restored_mib.name == "TEST-MIB"
        assert restored_mib.description == "Test MIB"
        assert restored_mib.imports == ["SNMPv2-SMI"]
        assert restored_mib.module_dependencies == ["SNMPv2-TC"]
        assert restored_mib.root_oids == ["1.3.6.1.4.1.9999"]
        assert len(restored_mib.nodes) == 1
        assert "testNode" in restored_mib.nodes