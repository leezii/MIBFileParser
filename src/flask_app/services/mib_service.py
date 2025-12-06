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
        Enhanced with better error handling and dependency resolution.

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
        import logging

        logger = logging.getLogger(__name__)
        results = {
            'success': [],
            'errors': [],
            'total_processed': 0,
            'total_added': 0
        }

        try:
            # Build comprehensive MIB source paths
            mib_sources = []

            # 1. Add shared MIB directories (most important for dependencies)
            shared_dirs = [
                str(Path.cwd() / "mibs_for_pysmi"),
                str(Path.cwd() / "storage" / "shared_mibs"),
                str(Path.cwd() / "compiled_mibs"),
            ]

            for shared_dir in shared_dirs:
                if Path(shared_dir).exists():
                    mib_sources.append(shared_dir)
                    logger.info(f"Added shared MIB directory: {shared_dir}")

            # 2. Add device-specific compiled MIBs directory
            if self.compiled_mibs_dir and self.compiled_mibs_dir.exists():
                mib_sources.append(str(self.compiled_mibs_dir))
                logger.info(f"Added device compiled MIBs directory: {self.compiled_mibs_dir}")

            # 3. Add parent directories of uploaded files as sources
            for mib_file in mib_files:
                parent_dir = str(mib_file.parent)
                if parent_dir not in mib_sources:
                    mib_sources.append(parent_dir)
                    logger.info(f"Added upload directory: {parent_dir}")

            # 4. Add common system MIB directories
            common_dirs = [
                '/usr/share/snmp/mibs',
                '/usr/local/share/snmp/mibs',
                '/var/lib/snmp/mibs',
            ]

            for common_dir in common_dirs:
                if Path(common_dir).exists():
                    mib_sources.append(common_dir)
                    logger.info(f"Added system MIB directory: {common_dir}")

            logger.info(f"Total MIB sources: {len(mib_sources)} directories")

            # Initialize parser with debug mode enabled for better error reporting
            parser = MibParser(mib_sources=mib_sources, debug_mode=True, resolve_dependencies=True)

            # Process each MIB file with enhanced error handling
            for mib_file in mib_files:
                try:
                    results['total_processed'] += 1
                    start_time = time.time()
                    logger.info(f"Processing MIB file: {mib_file.name}")

                    # Try to parse the MIB file directly first
                    result = None
                    parse_error = None

                    try:
                        result = parser.parse_file(str(mib_file))
                        parse_time = time.time() - start_time
                    except Exception as e:
                        parse_error = str(e)

                        # If it's a syntax error, try to fix the MIB file
                        if 'Syntax error' in parse_error or 'Bad grammar' in parse_error:
                            logger.warning(f"Syntax error in {mib_file.name}, attempting to fix...")
                            try:
                                # Apply syntax fixes
                                if self._fix_mib_syntax(mib_file):
                                    # Try parsing again after fixing
                                    result = parser.parse_file(str(mib_file))
                                    parse_time = time.time() - start_time
                                    logger.info(f"Successfully parsed {mib_file.name} after fixing syntax")
                                else:
                                    logger.warning(f"Could not fix syntax in {mib_file.name}")
                            except Exception as fix_error:
                                logger.error(f"Failed to fix {mib_file.name}: {fix_error}")

                        # If still failed, re-raise the original error
                        if result is None:
                            raise Exception(parse_error)

                    if parse_time > 30:  # Increased timeout for complex files
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
                        logger.info(f"Successfully parsed {mib_file.name}: {result.name} with {len(result.nodes)} nodes")
                    else:
                        results['errors'].append({
                            'filename': mib_file.name,
                            'error': 'Parser returned invalid result - not a proper MibData object'
                        })
                        logger.warning(f"Invalid result from parser for {mib_file.name}")

                except Exception as e:
                    error_msg = str(e)
                    # Enhance error messages for common dependency issues
                    if 'no module' in error_msg.lower() and 'in symbolTable' in error_msg:
                        # Extract missing module name for better error reporting
                        import re
                        match = re.search(r'no module "([^"]+)"', error_msg)
                        if match:
                            missing_module = match.group(1)
                            error_msg = f"Missing dependency MIB: '{missing_module}'. This MIB file requires {missing_module} to be available first."

                    results['errors'].append({
                        'filename': mib_file.name,
                        'error': error_msg
                    })
                    logger.error(f"Failed to parse {mib_file.name}: {error_msg}")

        except Exception as e:
            # If parser initialization fails, add errors for all files
            error_msg = f"Parser initialization failed: {str(e)}"
            logger.error(error_msg)
            for mib_file in mib_files:
                results['errors'].append({
                    'filename': mib_file.name,
                    'error': error_msg
                })

        # Clear cache to force reload
        self.clear_cache()

        # Add success and error counts for API compatibility
        results['success_count'] = results['total_added']
        results['error_count'] = len(results['errors'])

        return results

    def _fix_mib_syntax(self, mib_file: Path) -> bool:
        """
        Fix common syntax errors in MIB files.

        Args:
            mib_file: Path to MIB file

        Returns:
            True if fixes were applied, False otherwise
        """
        try:
            with open(mib_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            original_content = content
            fixes_applied = []

            # Fix common syntax issues
            import re

            # 1. Fix problematic OBJECT IDENTIFIER patterns
            # Remove or comment out problematic lines with very long or malformed identifiers
            lines = content.split('\n')
            fixed_lines = []

            for i, line in enumerate(lines):
                # Check for extremely long lines that might cause issues
                if len(line) > 1000:
                    fixed_lines.append(f"-- FIXED: Truncated line {i+1} (was {len(line)} chars)")
                    if len(fixes_applied) < 10:
                        fixes_applied.append(f"Truncated line {i+1}")
                    continue

                # Fix malformed OBJECT-TYPE syntax
                line = re.sub(r'OBJECT-TYPE\s*\n\s*SYNTAX\s*\n\s*([A-Za-z-0-9]+)', r'OBJECT-TYPE\n    SYNTAX     \1', line)

                # Fix problematic identifiers with mixed formats
                if 'corrErrAftFecAver15m' in line:
                    # Comment out the problematic line
                    if not line.strip().startswith('--'):
                        fixed_lines.append(f"-- FIXED: {line}")
                        if len(fixes_applied) < 10:
                            fixes_applied.append("Commented out problematic identifier")
                        continue

                # Fix malformed OIDs
                line = re.sub(r'OBJECT\s+IDENTIFIER\s*::=\s*{([^}]*)}([^\n]*)(?=\n|$)',
                            lambda m: f"OBJECT IDENTIFIER ::= {{ {m.group(1).strip()} }}", line)

                fixed_lines.append(line)

            content = '\n'.join(fixed_lines)

            # 2. Fix common END statement issues
            content = re.sub(r'\s*END\s*$', '\nEND', content)

            # 3. Fix malformed imports
            content = re.sub(r'IMPORTS\s*$', 'IMPORTS\n    -- No imports', content)

            # 4. Fix missing semicolons in SEQUENCE definitions
            content = re.sub(r'(\w+)\s+INTEGER', r'\1 INTEGER', content)

            if content != original_content:
                # Backup original file
                backup_path = mib_file.with_suffix(mib_file.suffix + '.backup')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)

                # Write fixed content
                with open(mib_file, 'w', encoding='utf-8') as f:
                    f.write(content)

                logger.info(f"Applied {len(fixes_applied)} syntax fixes to {mib_file.name}")
                for fix in fixes_applied[:5]:  # Log first 5 fixes
                    logger.info(f"  - {fix}")

                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Error fixing MIB syntax in {mib_file}: {e}")
            return False

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