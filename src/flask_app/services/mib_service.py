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

    def __init__(self, output_dir: Path, compiled_mibs_dir: Path = None, device_type: str = None):
        """
        Initialize MIB service.

        Args:
            output_dir: Path to the directory containing JSON output files
            compiled_mibs_dir: Path to compiled MIBs directory (for device context)
            device_type: Device type name for context
        """
        self.output_dir = Path(output_dir)
        self.compiled_mibs_dir = Path(compiled_mibs_dir) if compiled_mibs_dir else None
        self.device_type = device_type
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

    def get_device_context(self) -> Dict[str, Any]:
        """
        Get device context information.

        Returns:
            Device context dictionary
        """
        return {
            'device_type': self.device_type,
            'output_dir': str(self.output_dir),
            'compiled_mibs_dir': str(self.compiled_mibs_dir) if self.compiled_mibs_dir else None
        }

    def add_uploaded_files(self, mib_files: List[Path], device_type: str = None) -> Dict[str, Any]:
        """
        Parse and add uploaded MIB files to this device.
        Simplified version without complex timeout mechanisms to avoid threading issues.

        Args:
            mib_files: List of MIB file paths
            device_type: Device type for context

        Returns:
            Dictionary with parsing results
        """
        from src.mib_parser.parser import MibParser
        import tempfile
        import shutil
        import time

        results = {
            'success': [],
            'errors': [],
            'total_processed': 0,
            'total_added': 0
        }

        try:
            # Initialize parser once for all files
            mib_sources = [str(self.compiled_mibs_dir)] if self.compiled_mibs_dir else []
            if self.compiled_mibs_dir and self.compiled_mibs_dir.exists():
                mib_sources.append(str(self.compiled_mibs_dir))

            # Add parent directories of uploaded files as sources
            for mib_file in mib_files:
                parent_dir = str(mib_file.parent)
                if parent_dir not in mib_sources:
                    mib_sources.append(parent_dir)

            parser = MibParser(mib_sources=mib_sources, debug_mode=False)

            # Process each MIB file with simple time tracking
            for mib_file in mib_files:
                try:
                    results['total_processed'] += 1
                    start_time = time.time()

                    # Simple timeout check - if parsing takes too long, skip this file
                    result = parser.parse_file(str(mib_file))
                    parse_time = time.time() - start_time

                    if parse_time > 20:  # If a file takes more than 20 seconds, consider it problematic
                        results['errors'].append({
                            'filename': mib_file.name,
                            'error': f'Parsing took too long ({parse_time:.1f}s) - file may be too complex'
                        })
                        continue

                    # Check if result is a valid MibData object
                    if result and hasattr(result, 'name') and hasattr(result, 'nodes'):
                        results['success'].append({
                            'filename': mib_file.name,
                            'mib_name': result.name,
                            'nodes_count': len(result.nodes)
                        })
                        results['total_added'] += 1
                    else:
                        results['errors'].append({
                            'filename': mib_file.name,
                            'error': 'Parser returned invalid result - not a proper MibData object'
                        })

                except Exception as e:
                    results['errors'].append({
                        'filename': mib_file.name,
                        'error': str(e)
                    })

        except Exception as e:
            # If parser initialization fails, add errors for all files
            for mib_file in mib_files:
                results['errors'].append({
                    'filename': mib_file.name,
                    'error': f'Parser initialization failed: {str(e)}'
                })

        # Clear cache to force reload
        self.clear_cache()

        return results

    def replace_device_mibs(self, mib_files: List[Path], device_type: str = None) -> Dict[str, Any]:
        """
        Replace all MIB files for this device with new ones.

        Args:
            mib_files: List of MIB file paths
            device_type: Device type for context

        Returns:
            Dictionary with replacement results
        """
        try:
            # Clear existing files (no timeout needed for file operations)
            try:
                # Clear JSON output files
                for json_file in self.output_dir.glob("*.json"):
                    json_file.unlink()

                # Clear compiled MIB files
                if self.compiled_mibs_dir and self.compiled_mibs_dir.exists():
                    for compiled_file in self.compiled_mibs_dir.glob("*"):
                        if compiled_file.is_file():
                            compiled_file.unlink()

            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to clear existing files: {str(e)}',
                    'success_count': 0,
                    'error_count': len(mib_files),
                    'errors': [{'filename': f.name, 'error': 'Clear operation failed'} for f in mib_files]
                }

            # Add new files (this already has timeout handling)
            add_result = self.add_uploaded_files(mib_files, device_type)

            return {
                'success': True,
                'success_count': add_result['total_added'],
                'error_count': len(add_result['errors']),
                'errors': add_result['errors'],
                'success_files': add_result['success']
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Replacement failed: {str(e)}',
                'success_count': 0,
                'error_count': len(mib_files),
                'errors': [{'filename': f.name, 'error': str(e)} for f in mib_files]
            }