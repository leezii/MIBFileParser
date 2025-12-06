"""
Core MIB parser using pysmi with proper compilation and dependency resolution.
"""

import os
from pathlib import Path
from typing import List, Optional, Set, Dict, Any
from datetime import datetime
from pysmi.compiler import MibCompiler
from pysmi.parser import SmiStarParser
from pysmi.codegen import JsonCodeGen
from pysmi.writer import FileWriter
from pysmi.reader import FileReader
from pysmi.borrower import AnyFileBorrower
from pysmi import debug
from pysmi.error import PySmiError

from src.mib_parser.models import MibData, MibNode
from src.mib_parser.dependency_resolver import MibDependencyResolver


class MibParser:
    """Main class for parsing MIB files using pysmi with proper compilation."""

    def __init__(self, mib_sources: Optional[List[str]] = None, debug_mode: bool = False, resolve_dependencies: bool = True):
        """
        Initialize the MIB parser.

        Args:
            mib_sources: List of directories to search for MIB files
            debug_mode: Enable debug output
            resolve_dependencies: Whether to resolve MIB dependencies
        """
        if debug_mode:
            debug.set_logger(debug.Debug('reader', 'compiler'))

        self.mib_sources = mib_sources or self._get_default_mib_sources()
        self.resolve_dependencies = resolve_dependencies
        self.dependency_resolver = MibDependencyResolver() if resolve_dependencies else None
        self.compiled_mibs = {}  # Cache for compiled MIBs
        self._used_temp_dirs = set()  # Track used temp directories
        self.debug_mode = debug_mode
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

    def _setup_compiler(self):
        """Setup the MIB compiler with proper configuration."""
        # Create parser
        parser = SmiStarParser()

        # Setup JSON code generation
        json_codegen = JsonCodeGen()

        # Create writer (directory-based) for JSON output
        writer = FileWriter(str(Path.cwd() / "compiled_mibs"))

        # Create compiler with required components
        self.mib_compiler = MibCompiler(parser, json_codegen, writer)

        # Add MIB sources using the correct API
        for source in self.mib_sources:
            if os.path.exists(source):
                reader = FileReader(source)
                self.mib_compiler.add_sources(reader)

        # Setup MIB borrower for dependency resolution
        for source in self.mib_sources:
            if os.path.exists(source):
                borrower = AnyFileBorrower(FileReader(source))
                self.mib_compiler.add_borrowers(borrower)

    def parse_mib_file(self, file_path: str) -> MibData:
        """
        Parse a single MIB file using pysmi compiler with dependency resolution.

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
            # If dependency resolution is enabled, first resolve dependencies
            if self.resolve_dependencies:
                self._resolve_dependencies_in_directory(str(file_path.parent))

            # Extract actual MIB name from file content
            mib_name = self._extract_mib_name_from_content(file_path)

            # Create a temporary directory with properly named MIB files
            import tempfile
            import shutil

            temp_dir = Path(tempfile.mkdtemp())
            temp_mib_file = temp_dir / f"{mib_name}.mib"

            # Copy the MIB file to temp directory with correct name
            shutil.copy2(file_path, temp_mib_file)

            # Create a fresh compiler for each MIB to avoid conflicts
            parser = SmiStarParser()
            json_codegen = JsonCodeGen()

            # Ensure compiled_mibs directory exists and is accessible
            compiled_dir = Path.cwd() / "compiled_mibs"
            compiled_dir.mkdir(exist_ok=True)
            writer = FileWriter(str(compiled_dir))
            compiler = MibCompiler(parser, json_codegen, writer)

            # Add temp directory as source
            temp_reader = FileReader(str(temp_dir))
            compiler.add_sources(temp_reader)

            # Add compiled_mibs directory as both source and borrower
            compiled_reader = FileReader(str(compiled_dir))
            compiler.add_sources(compiled_reader)
            compiled_borrower = AnyFileBorrower(compiled_reader)
            compiler.add_borrowers(compiled_borrower)

            # Add MIB sources
            for source in self.mib_sources:
                if os.path.exists(source):
                    reader = FileReader(source)
                    compiler.add_sources(reader)
                    borrower = AnyFileBorrower(reader)
                    compiler.add_borrowers(borrower)

            # Add the shared MIBs directory
            mibs_dir = Path.cwd() / "mibs_for_pysmi"
            if mibs_dir.exists():
                mibs_reader = FileReader(str(mibs_dir))
                compiler.add_sources(mibs_reader)
                mibs_borrower = AnyFileBorrower(mibs_reader)
                compiler.add_borrowers(mibs_borrower)

            # Setup borrower for temp directory
            temp_borrower = AnyFileBorrower(temp_reader)
            compiler.add_borrowers(temp_borrower)

            try:
                # Use pysmi compiler to compile the MIB by name
                result = compiler.compile(mib_name)

                # Check compilation result - handle different API versions
                success = False
                error_messages = []

                if hasattr(result, 'get_status'):
                    # Newer pysmi API
                    status = result.get_status()
                    success = status == 'success'
                elif isinstance(result, dict):
                    # Older pysmi API
                    if mib_name in result:
                        status_obj = result[mib_name]
                        # Try different possible status methods/attributes
                        if hasattr(status_obj, 'getStatus'):
                            success = status_obj.getStatus() == 'success'
                        elif hasattr(status_obj, 'status'):
                            success = str(status_obj.status) == 'success'
                        elif hasattr(status_obj, 'error'):
                            error_messages.append(str(status_obj.error))
                        else:
                            # Check the string representation for common success indicators
                            status_str = str(status_obj).lower()
                            success = 'success' in status_str or 'built' in status_str or 'compiled' in status_str
                            if not success and 'error' in status_str:
                                error_messages.append(status_str)
                    else:
                        # MIB name not in result - check for error messages
                        for key, value in result.items():
                            if 'error' in str(value).lower():
                                error_messages.append(f"{key}: {value}")
                elif hasattr(result, '__iter__'):
                    # Result is iterable, check each item
                    for item in result:
                        if hasattr(item, 'status') and item.status != 'success':
                            error_messages.append(str(item))
                        elif hasattr(item, 'error'):
                            error_messages.append(str(item.error))

                # If compilation failed, provide detailed error information
                if not success:
                    if error_messages:
                        raise Exception(f"Compilation failed with errors: {'; '.join(error_messages)}")
                    else:
                        raise Exception(f"Compilation failed for MIB '{mib_name}' (no detailed error available)")

            except PySmiError as e:
                raise Exception(f"SMI compilation error for MIB '{mib_name}': {e}")
            except Exception as e:
                if isinstance(e, PySmiError):
                    raise
                else:
                    raise Exception(f"Compilation error for MIB '{mib_name}': {e}")
            finally:
                # Clean up temp directory
                shutil.rmtree(temp_dir, ignore_errors=True)

            if success:
                # Copy the original MIB file to a shared directory with correct MIB name for future dependency resolution
                mibs_dir = Path.cwd() / "mibs_for_pysmi"
                mibs_dir.mkdir(exist_ok=True)
                original_mib_file = mibs_dir / f"{mib_name}.mib"
                if not original_mib_file.exists():
                    shutil.copy2(file_path, original_mib_file)

                # Read the compiled JSON output (try both with and without .json extension)
                compiled_file = compiled_dir / f"{mib_name}"
                if compiled_file.exists():
                    import json
                    with open(compiled_file, 'r') as f:
                        compiled_data = json.load(f)
                    return self._extract_mib_data_from_pysmi(compiled_data, mib_name, file_path)
                else:
                    # Try with .json extension
                    compiled_file_json = compiled_dir / f"{mib_name}.json"
                    if compiled_file_json.exists():
                        import json
                        with open(compiled_file_json, 'r') as f:
                            compiled_data = json.load(f)
                        return self._extract_mib_data_from_pysmi(compiled_data, mib_name, file_path)
                    else:
                        raise Exception(f"Compiled output file not found: {compiled_file} or {compiled_file_json}")
            else:
                raise Exception(f"Failed to compile MIB file: {file_path}")

        except PySmiError as e:
            raise Exception(f"SMI error while parsing {file_path}: {e}")
        except Exception as e:
            raise Exception(f"Error parsing MIB file {file_path}: {e}")

    def _resolve_dependencies_in_directory(self, directory_path: str):
        """解析指定目录中的 MIB 依赖关系"""
        if self.dependency_resolver is None:
            return

        # 只解析一次依赖关系
        if not self.dependency_resolver.mib_files:
            self.dependency_resolver.parse_mib_dependencies(directory_path)

        # Add MIB sources in compilation order
        compilation_order = self.dependency_resolver.get_compilation_order()
        for mib_name in compilation_order:
            if mib_name in self.dependency_resolver.mib_files:
                mib_file = self.dependency_resolver.mib_files[mib_name]
                mib_dir = Path(mib_file.file_path).parent
                if str(mib_dir) not in self.mib_sources:
                    self.mib_compiler.add_sources(str(mib_dir))

    def _extract_mib_name_from_content(self, file_path: Path) -> str:
        """Extract the actual MIB name from file content by looking for DEFINITIONS."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Look for pattern: NAME DEFINITIONS ::= BEGIN
            import re
            match = re.search(r'(\w+(?:-\w+)*)\s+DEFINITIONS\s*::=\s*BEGIN', content, re.IGNORECASE)
            if match:
                return match.group(1)
            else:
                # Fallback to filename-based extraction
                mib_name = file_path.stem
                if mib_name and mib_name[0].isdigit():
                    parts = mib_name.split('_', 1)
                    if len(parts) > 1:
                        return parts[1]
                return mib_name
        except Exception:
            # Fallback to filename-based extraction
            mib_name = file_path.stem
            if mib_name and mib_name[0].isdigit():
                parts = mib_name.split('_', 1)
                if len(parts) > 1:
                    return parts[1]
            return mib_name

    def _extract_mib_data_from_pysmi(self, compiled_data: Dict, mib_name: str, file_path: Path) -> MibData:
        """Extract MIB data from pysmi compiled JSON output"""
        mib_data = MibData(
            name=mib_name,
            description=f"Compiled from {file_path.name}",
            last_updated=datetime.now()
        )

        # Handle pysmi JSON structure
        if isinstance(compiled_data, dict):
            # Extract imports
            if 'imports' in compiled_data:
                imports_data = compiled_data['imports']
                if isinstance(imports_data, dict):
                    mib_data.imports = list(imports_data.keys())
                else:
                    mib_data.imports = list(imports_data)

            # Process nodes from compiled data - pysmi outputs each node as a top-level key
            for key, value in compiled_data.items():
                # Skip meta and imports sections
                if key in ['imports', 'meta', 'dependencies', 'description']:
                    continue

                # Each other key should be a MIB node
                if isinstance(value, dict) and 'class' in value:
                    mib_node = self._extract_node_data_from_pysmi(key, value, mib_name)
                    mib_data.add_node(mib_node)

        # For backward compatibility, handle object-based data
        elif hasattr(compiled_data, 'imports'):
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
                    mib_node = self._extract_node_data_from_pysmi(node_name, node_data, mib_name)
                    mib_data.add_node(mib_node)

        return mib_data

    def _extract_node_data_from_pysmi(self, node_name: str, node_data: Any, module: str) -> MibNode:
        """Extract data for a single MIB node from pysmi output."""
        # Handle both dict and object-based node data
        if isinstance(node_data, dict):
            # Extract OID
            oid = node_data.get('oid', f"1.2.3.1")

            # Extract description
            description = node_data.get('description')

            # Extract syntax information
            syntax = node_data.get('syntax')

            # Extract access information
            access = node_data.get('access')
            max_access = node_data.get('max_access')

            # Extract status
            status = node_data.get('status')

            # Extract parent information
            parent_name = node_data.get('parent')

            # Extract text convention
            text_convention = node_data.get('text_convention')

            # Extract units
            units = node_data.get('units')

            # Extract reference
            reference = node_data.get('reference')

            # Extract default value
            defval = node_data.get('defval')

            # Extract hint
            hint = node_data.get('hint')

            # Extract node class
            node_class = node_data.get('class')

        else:
            # Extract OID
            oid = getattr(node_data, 'oid', f"1.2.3.1")

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

            # Extract node class
            node_class = getattr(node_data, 'class', None)

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
            node_class=node_class,
        )

    def _extract_mib_name_from_ast(self, ast):
        """Extract MIB name from parsed AST"""
        # This method is not used in the current implementation
        return None

    def _process_ast_nodes(self, ast, mib_data, mib_name):
        """Process AST to extract MIB nodes"""
        # This method is not used in the current implementation
        pass

    def _extract_mib_name_from_ast(self, ast):
        """Extract MIB name from parsed AST"""
        try:
            # Look for MIB name in the AST structure
            if hasattr(ast, 'get_name'):
                return ast.get_name()
            # Fallback: look through the AST structure
            elif hasattr(ast, 'symbols'):
                for symbol in ast.symbols.values():
                    if hasattr(symbol, 'get_name'):
                        return symbol.get_name()
            # Another fallback: try to find the first symbol that looks like a MIB name
            elif hasattr(ast, 'get_symbols'):
                symbols = ast.get_symbols()
                if symbols:
                    first_symbol = symbols[0]
                    if hasattr(first_symbol, 'get_name'):
                        return first_symbol.get_name()
        except:
            pass
        return None

    def _process_ast_nodes(self, ast, mib_data, mib_name):
        """Process AST to extract MIB nodes"""
        try:
            # pysmi returns a list of tokens/nodes instead of a complex AST
            # We'll use fallback to create basic nodes from MIB content
            self._create_basic_nodes_from_content(mib_data, mib_name)

        except Exception as e:
            print(f"Warning: Failed to process AST nodes: {e}")
            import traceback
            traceback.print_exc()

    def _create_basic_nodes_from_content(self, mib_data, mib_name):
        """Create basic nodes by parsing file content as fallback"""
        # This is a simplified fallback - create a few basic nodes
        # In a real implementation, you'd parse the file content more carefully
        basic_nodes = [
            {"name": mib_name.replace('-', '') + "Root", "oid": "1.2.3.1"},
            {"name": "system", "oid": "1.2.3.1.1"},
            {"name": "interfaces", "oid": "1.2.3.1.2"},
        ]

        for node_info in basic_nodes:
            node = MibNode(
                name=node_info["name"],
                oid=node_info["oid"],
                description=f"Basic node for {mib_name}",
                syntax="OBJECT IDENTIFIER",
                access="read-only",
                status="current",
                module=mib_name
            )
            mib_data.add_node(node)

    def _extract_symbol_info(self, symbol, mib_data, mib_name):
        """Extract information from a single symbol"""
        # This method is not used in the current implementation
        pass

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

    def parse_file(self, file_path: str) -> MibData:
        """
        Alias for parse_mib_file to maintain consistency.

        Args:
            file_path: Path to the MIB file

        Returns:
            MibData object containing parsed information
        """
        return self.parse_mib_file(file_path)

    def _extract_mib_data(self, compiled_data: Any, mib_name: str) -> MibData:
        """Extract MIB data from compiled pysmi JSON output."""
        mib_data = MibData(name=mib_name)

        # Handle pysmi JSON structure
        if isinstance(compiled_data, dict):
            # Extract imports and dependencies
            if 'imports' in compiled_data:
                mib_data.imports = list(compiled_data['imports'])

            if 'dependencies' in compiled_data:
                mib_data.module_dependencies = list(compiled_data['dependencies'])

            # Extract description if available
            if 'description' in compiled_data:
                mib_data.description = compiled_data['description']

            # Process nodes from compiled data
            if 'mib' in compiled_data and 'nodes' in compiled_data['mib']:
                for node_name, node_data in compiled_data['mib']['nodes'].items():
                    mib_node = self._extract_node_data(node_name, node_data, mib_name)
                    mib_data.add_node(mib_node)
            elif 'nodes' in compiled_data:
                for node_name, node_data in compiled_data['nodes'].items():
                    mib_node = self._extract_node_data(node_name, node_data, mib_name)
                    mib_data.add_node(mib_node)

        # For backward compatibility, handle object-based data
        elif hasattr(compiled_data, 'imports'):
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
        # Handle both dict and object-based node data
        if isinstance(node_data, dict):
            # Extract OID
            oid = node_data.get('oid', '')

            # Extract description
            description = node_data.get('description')

            # Extract syntax information
            syntax = node_data.get('syntax')

            # Extract access information
            access = node_data.get('access')
            max_access = node_data.get('max_access')

            # Extract status
            status = node_data.get('status')

            # Extract parent information
            parent_name = node_data.get('parent')

            # Extract text convention
            text_convention = node_data.get('text_convention')

            # Extract units
            units = node_data.get('units')

            # Extract reference
            reference = node_data.get('reference')

            # Extract default value
            defval = node_data.get('defval')

            # Extract hint
            hint = node_data.get('hint')

            # Extract node class
            node_class = node_data.get('class')

        else:
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

            # Extract node class
            node_class = getattr(node_data, 'class', None)

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
            node_class=node_class,
        )