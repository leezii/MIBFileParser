"""
Service layer for MIB data handling.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MibService:
    """Service for reading and managing MIB data from JSON files."""

    def __init__(self, output_dir: Path):
        """
        Initialize MIB service.

        Args:
            output_dir: Path to the directory containing JSON output files
        """
        self.output_dir = Path(output_dir)
        self._mib_cache = {}  # Simple in-memory cache
        self._last_cache_update = {}

    def list_mibs(self) -> List[Dict[str, Any]]:
        """
        List all available MIB files with metadata.

        Returns:
            List of dictionaries containing MIB metadata
        """
        mibs = []

        try:
            for file_path in self.output_dir.glob("*.json"):
                # Skip auxiliary files like _oids.json, _tree.json
                if any(suffix in file_path.name for suffix in ['_oids', '_tree', 'all_', 'statistics']):
                    continue

                try:
                    # Try to get basic info from file name first
                    mib_name = file_path.stem

                    # Get file metadata
                    stat = file_path.stat()

                    mib_info = {
                        'name': mib_name,
                        'filename': file_path.name,
                        'file_path': str(file_path.relative_to(self.output_dir.parent)),
                        'size': stat.st_size,
                        'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'description': None,
                        'nodes_count': None,
                        'imports_count': None
                    }

                    # Try to get more detailed info from the JSON content
                    try:
                        mib_data = self.get_mib_data(mib_name)
                        if mib_data:
                            mib_info.update({
                                'description': mib_data.get('description'),
                                'nodes_count': len(mib_data.get('nodes', {})),
                                'imports_count': len(mib_data.get('imports', []))
                            })
                    except Exception as e:
                        logger.warning(f"Could not read detailed info for {mib_name}: {e}")

                    mibs.append(mib_info)

                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error listing MIB files: {e}")

        # Sort by name
        mibs.sort(key=lambda x: x['name'])
        return mibs

    def get_mib_data(self, mib_name: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get MIB data by name.

        Args:
            mib_name: Name of the MIB
            use_cache: Whether to use cached data

        Returns:
            MIB data dictionary or None if not found
        """
        # Check cache first
        if use_cache and mib_name in self._mib_cache:
            cache_time = self._last_cache_update.get(mib_name, 0)
            file_path = self.output_dir / f"{mib_name}.json"

            # Check if file is newer than cache
            if file_path.exists() and file_path.stat().st_mtime <= cache_time:
                return self._mib_cache[mib_name]

        # Try to find the file
        json_file = self.output_dir / f"{mib_name}.json"
        if not json_file.exists():
            # Try with .mib.json extension (if original was .mib file)
            json_file = self.output_dir / f"{mib_name}.mib.json"

        if not json_file.exists():
            logger.error(f"MIB file not found: {mib_name}")
            return None

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Cache the data
            if use_cache:
                self._mib_cache[mib_name] = data
                self._last_cache_update[mib_name] = json_file.stat().st_mtime

            return data

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {json_file}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading {json_file}: {e}")
            return None

    def get_mib_tree_data(self, mib_name: str) -> Optional[Dict[str, Any]]:
        """
        Get tree-structured data for a MIB.

        Args:
            mib_name: Name of the MIB

        Returns:
            Tree-structured MIB data
        """
        if mib_name == 'ALL_MIBS':
            return self.get_all_mibs_tree_data()

        mib_data = self.get_mib_data(mib_name)
        if not mib_data:
            return None

        # Import tree service to build tree structure
        from .tree_service import TreeService
        tree_service = TreeService()

        return tree_service.build_tree_structure(mib_data)

    def get_all_mibs_tree_data(self) -> Dict[str, Any]:
        """
        Get tree-structured data for ALL MIBs combined.

        Returns:
            Tree-structured data combining all MIBs
        """
        from .tree_service import TreeService
        tree_service = TreeService()

        # Get all MIB data
        all_mibs = self.list_mibs()
        combined_nodes = {}
        all_imports = set()

        # Combine all nodes from all MIBs
        for mib_info in all_mibs:
            mib_name = mib_info['name']
            mib_data = self.get_mib_data(mib_name)

            if mib_data and 'nodes' in mib_data:
                # Add nodes to combined structure
                for node_name, node_data in mib_data['nodes'].items():
                    # Ensure node name includes MIB origin to avoid conflicts
                    unique_name = f"{mib_name}.{node_name}"
                    combined_nodes[unique_name] = {
                        **node_data,
                        'original_name': node_name,
                        'mib_origin': mib_name
                    }

                # Collect all imports
                if 'imports' in mib_data:
                    all_imports.update(mib_data['imports'])

        # Create combined MIB data structure
        combined_mib_data = {
            'name': 'All MIBs',
            'description': 'Combined view of all MIB modules',
            'module': 'ALL_MIBS',
            'nodes': combined_nodes,
            'imports': list(all_imports)
        }

        # Build tree structure from combined data
        return tree_service.build_tree_structure(combined_mib_data)

    def search_nodes(self, query: str, mib_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for nodes matching the query.

        Args:
            query: Search query (matches name, OID, or description)
            mib_name: Optional MIB name to limit search to

        Returns:
            List of matching nodes
        """
        results = []
        query_lower = query.lower()

        # Determine which MIBs to search
        if mib_name:
            mibs_to_search = [mib_name]
        else:
            mib_list = self.list_mibs()
            mibs_to_search = [mib['name'] for mib in mib_list]

        for mib_name in mibs_to_search:
            mib_data = self.get_mib_data(mib_name)
            if not mib_data:
                continue

            nodes = mib_data.get('nodes', {})
            for node_name, node_data in nodes.items():
                # Search in name, OID, and description
                searchable_text = f"{node_name} {node_data.get('oid', '')} {node_data.get('description', '')}"
                if query_lower in searchable_text.lower():
                    result = {
                        'mib_name': mib_name,
                        'node_name': node_name,
                        'node_data': node_data,
                        'match_type': self._get_match_type(node_name, node_data, query_lower)
                    }
                    results.append(result)

        return results

    def get_node_by_oid(self, oid: str) -> Optional[Dict[str, Any]]:
        """
        Find a node by its OID across all MIBs.

        Args:
            oid: OID to search for

        Returns:
            Node data with MIB context or None if not found
        """
        mib_list = self.list_mibs()

        for mib_info in mib_list:
            mib_data = self.get_mib_data(mib_info['name'])
            if not mib_data:
                continue

            nodes = mib_data.get('nodes', {})
            for node_name, node_data in nodes.items():
                if node_data.get('oid') == oid:
                    return {
                        'mib_name': mib_info['name'],
                        'node_name': node_name,
                        'node_data': node_data,
                        'mib_info': mib_info
                    }

        return None

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics about all MIBs.

        Returns:
            Dictionary with statistics
        """
        mibs = self.list_mibs()

        stats = {
            'total_mibs': len(mibs),
            'total_nodes': 0,
            'total_size': 0,
            'mibs_with_data': 0,
            'largest_mib': None,
            'newest_mib': None,
            'oldest_mib': None
        }

        largest_size = 0
        newest_time = 0
        oldest_time = float('inf')

        for mib in mibs:
            stats['total_size'] += mib.get('size', 0)
            nodes_count = mib.get('nodes_count', 0)
            if nodes_count:
                stats['total_nodes'] += nodes_count
                stats['mibs_with_data'] += 1

            # Track extremes
            size = mib.get('size', 0)
            if size > largest_size:
                largest_size = size
                stats['largest_mib'] = mib['name']

            mtime = mib.get('last_modified', '')
            if mtime:
                try:
                    mtime_dt = datetime.fromisoformat(mtime.replace('Z', '+00:00') if mtime.endswith('Z') else mtime)
                    mtime_ts = mtime_dt.timestamp()

                    if mtime_ts > newest_time:
                        newest_time = mtime_ts
                        stats['newest_mib'] = mib['name']

                    if mtime_ts < oldest_time:
                        oldest_time = mtime_ts
                        stats['oldest_mib'] = mib['name']
                except:
                    pass

        return stats

    def clear_cache(self, mib_name: Optional[str] = None):
        """
        Clear cached data.

        Args:
            mib_name: Specific MIB to clear, or None to clear all
        """
        if mib_name:
            self._mib_cache.pop(mib_name, None)
            self._last_cache_update.pop(mib_name, None)
        else:
            self._mib_cache.clear()
            self._last_cache_update.clear()

    def _get_match_type(self, node_name: str, node_data: Dict, query_lower: str) -> str:
        """
        Determine what type of match this is.

        Args:
            node_name: Name of the node
            node_data: Node data
            query_lower: Lowercase search query

        Returns:
            String indicating match type
        """
        if query_lower in node_name.lower():
            return 'name'
        elif query_lower in node_data.get('oid', '').lower():
            return 'oid'
        elif query_lower in node_data.get('description', '').lower():
            return 'description'
        else:
            return 'other'