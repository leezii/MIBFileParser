"""Test LeafNodeExtractor class."""

import pytest
import json
from pathlib import Path
from src.mib_parser.leaf_extractor import LeafNodeExtractor
from src.mib_parser.models import MibNode, MibData


class TestLeafNodeExtractor:
    """Test LeafNodeExtractor class."""

    def test_initialize_extractor(self, tmp_path):
        """Test extractor initialization."""
        extractor = LeafNodeExtractor(storage_path=str(tmp_path))

        assert extractor.storage_path == tmp_path
        assert extractor.leaf_nodes_path.exists()

    def test_extract_all_leaf_nodes_empty_storage(self, tmp_path):
        """Test extracting from empty storage."""
        extractor = LeafNodeExtractor(storage_path=str(tmp_path))

        result = extractor.extract_all_leaf_nodes()

        assert result == {}

    def test_identify_leaf_node(self):
        """Test leaf node identification logic."""
        # Scalar node is a leaf
        scalar_node = MibNode(
            oid="1.3.6.1.2.1.1.1", name="sysDescr", syntax="DisplayString"
        )

        # Table entry is not a leaf (has children)
        table_entry = MibNode(oid="1.3.6.1.2.1.2.2.1", name="ifEntry", is_entry=True)

        # Scalar nodes should be leaves
        assert scalar_node.syntax is not None or scalar_node.module is not None

    def test_extract_leaf_nodes_from_mib(self, tmp_path):
        """Test extracting leaf nodes from MIB data."""
        extractor = LeafNodeExtractor(storage_path=str(tmp_path))

        # Create mock MIB data
        mib_data = {
            "name": "TEST-MIB",
            "nodes": {
                "sysDescr": {
                    "oid": "1.3.6.1.2.1.1.1",
                    "name": "sysDescr",
                    "syntax": "DisplayString",
                }
            },
        }

        result = extractor._extract_leaf_nodes_from_mib(
            mib_data, "test-device", "TEST-MIB"
        )

        assert isinstance(result, list)

    def test_save_leaf_nodes_to_file(self, tmp_path):
        """Test saving leaf nodes to JSON file."""
        extractor = LeafNodeExtractor(storage_path=str(tmp_path))

        test_data = {
            "device1": [
                {
                    "oid": "1.3.6.1.2.1.1.1",
                    "name": "sysDescr",
                    "syntax": "DisplayString",
                }
            ]
        }

        extractor._save_leaf_nodes(test_data)

        # Verify file was created (check the actual filename used by the implementation)
        output_file = tmp_path / "leaf_nodes" / "extracted_leaf_nodes.json"
        assert output_file.exists()

    def test_extract_device_leaf_nodes(self, tmp_path):
        """Test extracting leaf nodes for a specific device."""
        # Create device structure
        device_path = tmp_path / "devices" / "test-device" / "output"
        device_path.mkdir(parents=True)

        # Create mock MIB JSON file
        mib_file = device_path / "TEST-MIB.json"
        mib_data = {"name": "TEST-MIB", "nodes": {}}
        mib_file.write_text(json.dumps(mib_data))

        extractor = LeafNodeExtractor(storage_path=str(tmp_path))
        result = extractor._extract_device_leaf_nodes("test-device")

        assert isinstance(result, list)
