"""
Core MIB parser using pysmi.
"""

import os
from pathlib import Path
from typing import List, Optional, Set, Dict, Any
from pysmi.parser import SmiStarParser
from pysmi.compiler import MibCompiler
from pysmi.codegen import JsonCodeGen
from pysmi.borrower import MibBorrower
from pysmi import debug
from pysmi import error

from .models import MibData, MibNode


class MibParser:
    """Main class for parsing MIB files using pysmi."""

    def __init__(self, mib_sources: Optional[List[str]] = None, debug_mode: bool = False):
        """
        Initialize the MIB parser.

        Args:
            mib_sources: List of directories to search for MIB files
            debug_mode: Enable debug output
        """
        if debug_mode:
            debug.setLogger(debug.Debug('reader', 'compiler'))

        self.mib_sources = mib_sources or self._get_default_mib_sources()
        self.mib_compiler = MibCompiler()
        self._setup_compiler()

    def _get_default_mib_sources(self) -> List[str]:
        """Get default MIB source directories."""
        sources = []

        # Add current directory
        if os.path.exists('.'):
            sources.append(os.getcwd())

        # Add common MIB directories
        common_dirs = [
            '/usr/share/snmp/mibs',
            '/usr/local/share/snmp/mibs',
            '/var/lib/snmp/mibs',
        ]

        for dir_path in common_dirs:
            if os.path.exists(dir_path):
                sources.append(dir_path)

        return sources

    def _setup_compiler(self) -> None:
        """Setup the MIB compiler with sources and destinations."""
        # Add MIB sources
        for source in self.mib_sources:
            self.mib_compiler.add_sources(source)

        # Setup JSON code generation
        json_codegen = JsonCodeGen()
        self.mib_compiler.add_codegen(json_codegen)

        # Setup MIB borrower for dependency resolution
        borrower = MibBorrower()
        self.mib_compiler.add_borrower(borrower)

    def parse_mib_file(self, file_path: str) -> MibData:
        """
        Parse a single MIB file.

        Args:
            file_path: Path to the MIB file

        Returns:
            MibData object containing parsed information

        Raises:
            Exception: If parsing fails
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"MIB file not found: {file_path}")

        try:
            # Compile MIB file
            mib_name = file_path.stem
            result = self.mib_compiler.compile(str(file_path))

            if result:
                return self._extract_mib_data(result, mib_name)
            else:
                raise Exception(f"Failed to compile MIB file: {file_path}")

        except error.SmiError as e:
            raise Exception(f"SMI error while parsing {file_path}: {e}")
        except Exception as e:
            raise Exception(f"Error parsing MIB file {file_path}: {e}")

    def parse_mib_directory(self, directory_path: str, recursive: bool = True) -> List[MibData]:
        """
        Parse all MIB files in a directory.

        Args:
            directory_path: Path to the directory containing MIB files
            recursive: Whether to search subdirectories

        Returns:
            List of MibData objects

        Raises:
            Exception: If parsing fails for any file
        """
        directory_path = Path(directory_path)
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        mib_files = self._find_mib_files(directory_path, recursive)
        mib_data_list = []

        for mib_file in mib_files:
            try:
                mib_data = self.parse_mib_file(str(mib_file))
                mib_data_list.append(mib_data)
            except Exception as e:
                print(f"Warning: Failed to parse {mib_file}: {e}")
                continue

        return mib_data_list

    def parse_multiple_files(self, file_paths: List[str]) -> List[MibData]:
        """
        Parse multiple MIB files.

        Args:
            file_paths: List of MIB file paths

        Returns:
            List of MibData objects
        """
        mib_data_list = []
        for file_path in file_paths:
            try:
                mib_data = self.parse_mib_file(file_path)
                mib_data_list.append(mib_data)
            except Exception as e:
                print(f"Warning: Failed to parse {file_path}: {e}")
                continue

        return mib_data_list

    def _find_mib_files(self, directory: Path, recursive: bool) -> List[Path]:
        """Find all MIB files in a directory."""
        extensions = {'.mib', '.my', '.txt', '.py'}
        mib_files = []

        if recursive:
            for file_path in directory.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in extensions:
                    mib_files.append(file_path)
        else:
            for file_path in directory.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in extensions:
                    mib_files.append(file_path)

        return mib_files

    def _extract_mib_data(self, compiled_data: Any, mib_name: str) -> MibData:
        """Extract MIB data from compiled pysmi output."""
        mib_data = MibData(name=mib_name)

        # Extract imports and dependencies
        if hasattr(compiled_data, 'imports'):
            mib_data.imports = list(compiled_data.imports)

        if hasattr(compiled_data, 'dependencies'):
            mib_data.module_dependencies = list(compiled_data.dependencies)

        # Extract description if available
        if hasattr(compiled_data, 'description'):
            mib_data.description = compiled_data.description

        # Process nodes from compiled data
        if hasattr(compiled_data, 'nodes'):
            for node_name, node_data in compiled_data.nodes.items():
                mib_node = self._extract_node_data(node_name, node_data, mib_name)
                mib_data.add_node(mib_node)

        # Identify root OIDs
        root_nodes = mib_data.get_root_nodes()
        mib_data.root_oids = [node.oid for node in root_nodes]

        return mib_data

    def _extract_node_data(self, node_name: str, node_data: Any, module: str) -> MibNode:
        """Extract data for a single MIB node."""
        # Extract OID
        oid = getattr(node_data, 'oid', '')

        # Extract description
        description = getattr(node_data, 'description', None)

        # Extract syntax information
        syntax = None
        if hasattr(node_data, 'syntax'):
            syntax = str(node_data.syntax)

        # Extract access information
        access = getattr(node_data, 'access', None)
        max_access = getattr(node_data, 'max_access', None)

        # Extract status
        status = getattr(node_data, 'status', None)

        # Extract parent information
        parent_name = None
        if hasattr(node_data, 'parent'):
            parent_name = str(node_data.parent)

        # Extract text convention
        text_convention = getattr(node_data, 'text_convention', None)

        # Extract units
        units = getattr(node_data, 'units', None)

        # Extract reference
        reference = getattr(node_data, 'reference', None)

        # Extract default value
        defval = getattr(node_data, 'defval', None)

        # Extract hint
        hint = getattr(node_data, 'hint', None)

        return MibNode(
            name=node_name,
            oid=oid,
            description=description,
            syntax=syntax,
            access=access,
            status=status,
            parent_name=parent_name,
            module=module,
            text_convention=text_convention,
            units=units,
            max_access=max_access,
            reference=reference,
            defval=defval,
            hint=hint,
        )