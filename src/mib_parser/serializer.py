"""
JSON serialization utilities for MIB data.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Union
from datetime import datetime

from src.mib_parser.models import MibData, MibNode


class JsonSerializer:
    """Handles serialization and deserialization of MIB data to/from JSON."""

    def __init__(self, indent: int = 2, ensure_ascii: bool = False):
        """
        Initialize JSON serializer.

        Args:
            indent: JSON indentation level
            ensure_ascii: Whether to ensure ASCII encoding
        """
        self.indent = indent
        self.ensure_ascii = ensure_ascii

    def serialize(self, mib_data: Union[MibData, List[MibData]], file_path: str) -> None:
        """
        Serialize MIB data to JSON file.

        Args:
            mib_data: Single MibData or list of MibData objects
            file_path: Output JSON file path
        """
        if isinstance(mib_data, MibData):
            data = mib_data.to_dict()
        else:
            data = [mib.to_dict() for mib in mib_data]

        # Add metadata
        if isinstance(data, dict):
            data["_metadata"] = {
                "exported_at": datetime.now().isoformat(),
                "version": "1.0",
                "type": "single_mib"
            }
        else:
            data = {
                "_metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "type": "multiple_mibs",
                    "count": len(data)
                },
                "mibs": data
            }

        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=self.indent, ensure_ascii=self.ensure_ascii)

    def serialize_to_string(self, mib_data: Union[MibData, List[MibData]]) -> str:
        """
        Serialize MIB data to JSON string.

        Args:
            mib_data: Single MibData or list of MibData objects

        Returns:
            JSON string representation
        """
        if isinstance(mib_data, MibData):
            data = mib_data.to_dict()
        else:
            data = [mib.to_dict() for mib in mib_data]

        # Add metadata
        if isinstance(data, dict):
            data["_metadata"] = {
                "exported_at": datetime.now().isoformat(),
                "version": "1.0",
                "type": "single_mib"
            }
        else:
            data = {
                "_metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "type": "multiple_mibs",
                    "count": len(data)
                },
                "mibs": data
            }

        return json.dumps(data, indent=self.indent, ensure_ascii=self.ensure_ascii)

    def deserialize(self, file_path: str) -> Union[MibData, List[MibData]]:
        """
        Deserialize MIB data from JSON file.

        Args:
            file_path: Input JSON file path

        Returns:
            Single MibData or list of MibData objects

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is malformed
        """
        input_path = Path(file_path)
        if not input_path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return self._deserialize_data(data)

    def deserialize_from_string(self, json_string: str) -> Union[MibData, List[MibData]]:
        """
        Deserialize MIB data from JSON string.

        Args:
            json_string: JSON string representation

        Returns:
            Single MibData or list of MibData objects
        """
        data = json.loads(json_string)
        return self._deserialize_data(data)

    def _deserialize_data(self, data: Dict[str, Any]) -> Union[MibData, List[MibData]]:
        """Deserialize data from JSON structure."""
        # Check if this is a single MIB or multiple MIBs
        metadata = data.pop("_metadata", {})
        data_type = metadata.get("type", "single_mib")

        if data_type == "single_mib":
            return MibData.from_dict(data)
        else:
            # Multiple MIBs format
            mibs_data = data.get("mibs", data)
            return [MibData.from_dict(mib_data) for mib_data in mibs_data]

    def serialize_tree(self, mib_data: MibData, file_path: str) -> None:
        """
        Serialize MIB data as a hierarchical tree structure.

        Args:
            mib_data: MibData object
            file_path: Output JSON file path
        """
        tree_data = self._build_tree_structure(mib_data)

        # Add metadata
        tree_data["_metadata"] = {
            "exported_at": datetime.now().isoformat(),
            "version": "1.0",
            "type": "tree_structure",
            "mib_name": mib_data.name
        }

        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tree_data, f, indent=self.indent, ensure_ascii=self.ensure_ascii)

    def _build_tree_structure(self, mib_data: MibData) -> Dict[str, Any]:
        """Build hierarchical tree structure from MIB data."""
        # Start with root nodes
        root_nodes = mib_data.get_root_nodes()
        tree = {}

        for root_node in root_nodes:
            tree[root_node.name] = self._build_node_tree(root_node, mib_data)

        return tree

    def _build_node_tree(self, node: MibNode, mib_data: MibData) -> Dict[str, Any]:
        """Build tree structure for a single node and its children."""
        node_dict = node.to_dict()

        # Add children if they exist
        if node.children:
            children_dict = {}
            for child_name in node.children:
                if child_name in mib_data.nodes:
                    child_node = mib_data.nodes[child_name]
                    children_dict[child_name] = self._build_node_tree(child_node, mib_data)

            if children_dict:
                node_dict["children"] = children_dict

        return node_dict

    def export_oid_mapping(self, mib_data: Union[MibData, List[MibData]], file_path: str) -> None:
        """
        Export OID to name mapping for quick lookup.

        Args:
            mib_data: Single MibData or list of MibData objects
            file_path: Output JSON file path
        """
        oid_mapping = {}
        name_mapping = {}

        if isinstance(mib_data, MibData):
            mib_list = [mib_data]
        else:
            mib_list = mib_data

        for mib in mib_list:
            for node in mib.nodes.values():
                oid_mapping[node.oid] = {
                    "name": node.name,
                    "module": mib.name,
                    "description": node.description
                }
                name_mapping[node.name] = {
                    "oid": node.oid,
                    "module": mib.name
                }

        mapping_data = {
            "_metadata": {
                "exported_at": datetime.now().isoformat(),
                "version": "1.0",
                "type": "oid_mapping",
                "mib_count": len(mib_list)
            },
            "oid_to_name": oid_mapping,
            "name_to_oid": name_mapping
        }

        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, indent=self.indent, ensure_ascii=self.ensure_ascii)