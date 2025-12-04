"""
Tests for JSON serialization functionality.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime

from src.mib_parser.models import MibNode, MibData
from src.mib_parser.serializer import JsonSerializer


class TestJsonSerializer:
    """Test cases for JsonSerializer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.serializer = JsonSerializer()
        self.temp_dir = Path("temp_test")
        self.temp_dir.mkdir(exist_ok=True)

        # Create test MIB data
        self.test_mib_data = MibData(
            name="TEST-MIB",
            description="Test MIB module",
            imports=["SNMPv2-SMI", "SNMPv2-TC"],
            module_dependencies=["IF-MIB"],
            last_updated=datetime(2023, 12, 1, 10, 30, 0)
        )

        # Add test nodes
        root_node = MibNode(
            name="testRoot",
            oid="1.3.6.1.4.1.9999",
            description="Test root node",
            syntax="OBJECT IDENTIFIER",
            access="read-only",
            status="current"
        )

        child_node = MibNode(
            name="testChild",
            oid="1.3.6.1.4.1.9999.1",
            description="Test child node",
            syntax="INTEGER",
            access="read-write",
            status="current",
            parent_name="testRoot",
            units="seconds"
        )

        self.test_mib_data.add_node(root_node)
        self.test_mib_data.add_node(child_node)

    def teardown_method(self):
        """Clean up test fixtures."""
        # Remove temp files
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_serialize_single_mib_to_file(self):
        """Test serializing a single MIB to file."""
        output_file = self.temp_dir / "test_mib.json"
        self.serializer.serialize(self.test_mib_data, str(output_file))

        assert output_file.exists()

        # Verify file contents
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data["_metadata"]["type"] == "single_mib"
        assert data["name"] == "TEST-MIB"
        assert data["description"] == "Test MIB module"
        assert "testRoot" in data["nodes"]
        assert "testChild" in data["nodes"]

    def test_serialize_multiple_mibs_to_file(self):
        """Test serializing multiple MIBs to file."""
        # Create second MIB
        mib_data2 = MibData(
            name="TEST-MIB-2",
            description="Second test MIB"
        )
        node2 = MibNode(name="testNode2", oid="1.3.6.1.4.1.8888")
        mib_data2.add_node(node2)

        output_file = self.temp_dir / "multiple_mibs.json"
        self.serializer.serialize([self.test_mib_data, mib_data2], str(output_file))

        assert output_file.exists()

        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data["_metadata"]["type"] == "multiple_mibs"
        assert data["_metadata"]["count"] == 2
        assert len(data["mibs"]) == 2
        assert data["mibs"][0]["name"] == "TEST-MIB"
        assert data["mibs"][1]["name"] == "TEST-MIB-2"

    def test_serialize_to_string(self):
        """Test serializing to string."""
        json_string = self.serializer.serialize_to_string(self.test_mib_data)

        data = json.loads(json_string)
        assert data["_metadata"]["type"] == "single_mib"
        assert data["name"] == "TEST-MIB"
        assert "testRoot" in data["nodes"]

    def test_deserialize_single_mib_from_file(self):
        """Test deserializing a single MIB from file."""
        # First serialize
        output_file = self.temp_dir / "test_mib.json"
        self.serializer.serialize(self.test_mib_data, str(output_file))

        # Then deserialize
        deserialized_mib = self.serializer.deserialize(str(output_file))

        assert isinstance(deserialized_mib, MibData)
        assert deserialized_mib.name == "TEST-MIB"
        assert deserialized_mib.description == "Test MIB module"
        assert len(deserialized_mib.nodes) == 2
        assert "testRoot" in deserialized_mib.nodes
        assert "testChild" in deserialized_mib.nodes

        # Verify node data
        root_node = deserialized_mib.nodes["testRoot"]
        assert root_node.oid == "1.3.6.1.4.1.9999"
        assert root_node.description == "Test root node"
        assert root_node.syntax == "OBJECT IDENTIFIER"

    def test_deserialize_multiple_mibs_from_file(self):
        """Test deserializing multiple MIBs from file."""
        # Create and serialize multiple MIBs
        mib_data2 = MibData(name="TEST-MIB-2")
        node2 = MibNode(name="testNode2", oid="1.3.6.1.4.1.8888")
        mib_data2.add_node(node2)

        output_file = self.temp_dir / "multiple_mibs.json"
        self.serializer.serialize([self.test_mib_data, mib_data2], str(output_file))

        # Deserialize
        deserialized_mibs = self.serializer.deserialize(str(output_file))

        assert isinstance(deserialized_mibs, list)
        assert len(deserialized_mibs) == 2
        assert deserialized_mibs[0].name == "TEST-MIB"
        assert deserialized_mibs[1].name == "TEST-MIB-2"

    def test_deserialize_from_string(self):
        """Test deserializing from string."""
        # Serialize to string
        json_string = self.serializer.serialize_to_string(self.test_mib_data)

        # Deserialize from string
        deserialized_mib = self.serializer.deserialize_from_string(json_string)

        assert isinstance(deserialized_mib, MibData)
        assert deserialized_mib.name == "TEST-MIB"
        assert len(deserialized_mib.nodes) == 2

    def test_deserialize_nonexistent_file(self):
        """Test deserializing a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            self.serializer.deserialize("nonexistent_file.json")

    def test_serialize_tree_structure(self):
        """Test serializing tree structure."""
        output_file = self.temp_dir / "tree_structure.json"
        self.serializer.serialize_tree(self.test_mib_data, str(output_file))

        assert output_file.exists()

        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data["_metadata"]["type"] == "tree_structure"
        assert data["_metadata"]["mib_name"] == "TEST-MIB"
        assert "testRoot" in data
        assert "testChild" in data["testRoot"]["children"]

    def test_export_oid_mapping(self):
        """Test exporting OID mapping."""
        output_file = self.temp_dir / "oid_mapping.json"
        self.serializer.export_oid_mapping(self.test_mib_data, str(output_file))

        assert output_file.exists()

        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data["_metadata"]["type"] == "oid_mapping"
        assert data["_metadata"]["mib_count"] == 1
        assert "oid_to_name" in data
        assert "name_to_oid" in data

        # Check OID mapping
        oid_to_name = data["oid_to_name"]
        assert "1.3.6.1.4.1.9999" in oid_to_name
        assert oid_to_name["1.3.6.1.4.1.9999"]["name"] == "testRoot"
        assert oid_to_name["1.3.6.1.4.1.9999"]["module"] == "TEST-MIB"

        # Check name mapping
        name_to_oid = data["name_to_oid"]
        assert "testRoot" in name_to_oid
        assert name_to_oid["testRoot"]["oid"] == "1.3.6.1.4.1.9999"
        assert name_to_oid["testRoot"]["module"] == "TEST-MIB"

    def test_export_oid_mapping_multiple_mibs(self):
        """Test exporting OID mapping for multiple MIBs."""
        # Create second MIB
        mib_data2 = MibData(name="TEST-MIB-2")
        node2 = MibNode(name="testNode2", oid="1.3.6.1.4.1.8888")
        mib_data2.add_node(node2)

        output_file = self.temp_dir / "oid_mapping_multiple.json"
        self.serializer.export_oid_mapping([self.test_mib_data, mib_data2], str(output_file))

        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data["_metadata"]["mib_count"] == 2
        assert len(data["oid_to_name"]) == 3  # 2 nodes from first MIB + 1 from second
        assert len(data["name_to_oid"]) == 3

    def test_custom_serializer_settings(self):
        """Test serializer with custom settings."""
        custom_serializer = JsonSerializer(indent=4, ensure_ascii=True)
        json_string = custom_serializer.serialize_to_string(self.test_mib_data)

        # Check that indent is 4
        lines = json_string.split('\n')
        assert '    "testRoot"' in json_string  # 4 spaces for indentation

        # Test deserialization still works
        deserialized = custom_serializer.deserialize_from_string(json_string)
        assert deserialized.name == "TEST-MIB"

    def test_json_roundtrip_preserves_data(self):
        """Test that serialize->deserialize roundtrip preserves all data."""
        # Serialize
        json_string = self.serializer.serialize_to_string(self.test_mib_data)

        # Deserialize
        deserialized = self.serializer.deserialize_from_string(json_string)

        # Compare all attributes
        assert deserialized.name == self.test_mib_data.name
        assert deserialized.description == self.test_mib_data.description
        assert deserialized.imports == self.test_mib_data.imports
        assert deserialized.module_dependencies == self.test_mib_data.module_dependencies
        assert deserialized.root_oids == self.test_mib_data.root_oids
        assert len(deserialized.nodes) == len(self.test_mib_data.nodes)

        # Compare nodes
        for node_name in self.test_mib_data.nodes:
            original_node = self.test_mib_data.nodes[node_name]
            deserialized_node = deserialized.nodes[node_name]
            assert deserialized_node.name == original_node.name
            assert deserialized_node.oid == original_node.oid
            assert deserialized_node.description == original_node.description
            assert deserialized_node.syntax == original_node.syntax
            assert deserialized_node.access == original_node.access
            assert deserialized_node.status == original_node.status
            assert deserialized_node.parent_name == original_node.parent_name
            assert deserialized_node.children == original_node.children
            assert deserialized_node.units == original_node.units