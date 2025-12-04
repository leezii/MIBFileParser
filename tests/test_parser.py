"""
Tests for MIB parser functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.mib_parser.parser import MibParser
from src.mib_parser.models import MibData, MibNode


class TestMibParser:
    """Test cases for MibParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = MibParser()
        self.temp_dir = Path("temp_test")
        self.temp_dir.mkdir(exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_parser_initialization_default_sources(self):
        """Test parser initialization with default MIB sources."""
        parser = MibParser()
        assert parser.mib_sources is not None
        assert isinstance(parser.mib_sources, list)
        assert parser.mib_compiler is not None

    def test_parser_initialization_custom_sources(self):
        """Test parser initialization with custom MIB sources."""
        custom_sources = ["/custom/mib/path1", "/custom/mib/path2"]
        parser = MibParser(mib_sources=custom_sources)
        assert parser.mib_sources == custom_sources

    def test_parser_initialization_debug_mode(self):
        """Test parser initialization with debug mode enabled."""
        parser = MibParser(debug_mode=True)
        # Debug mode mainly affects pysmi logger setup
        assert parser.mib_compiler is not None

    def test_parse_mib_file_not_found(self):
        """Test parsing a non-existent MIB file."""
        with pytest.raises(FileNotFoundError):
            self.parser.parse_mib_file("nonexistent_file.mib")

    @patch('src.mib_parser.parser.MibCompiler')
    def test_parse_mib_file_success(self, mock_compiler_class):
        """Test successful MIB file parsing."""
        # Mock the compiler and compilation result
        mock_compiler = Mock()
        mock_compiler_class.return_value = mock_compiler

        # Create mock compilation result
        mock_result = Mock()
        mock_compiler.compile.return_value = mock_result

        parser = MibParser()

        # Mock the _extract_mib_data method
        expected_mib_data = MibData(name="TEST-MIB")
        parser._extract_mib_data = Mock(return_value=expected_mib_data)

        # Create a test MIB file
        test_file = self.temp_dir / "test.mib"
        test_file.write_text("TEST-MIB DEFINITIONS ::= BEGIN\nEND")

        result = parser.parse_mib_file(str(test_file))
        assert result == expected_mib_data
        mock_compiler.compile.assert_called_once_with(str(test_file))

    @patch('src.mib_parser.parser.MibCompiler')
    def test_parse_mib_file_compilation_failure(self, mock_compiler_class):
        """Test MIB file parsing when compilation fails."""
        mock_compiler = Mock()
        mock_compiler_class.return_value = mock_compiler
        mock_compiler.compile.return_value = None

        parser = MibParser()

        test_file = self.temp_dir / "test.mib"
        test_file.write_text("INVALID MIB CONTENT")

        with pytest.raises(Exception, match="Failed to compile MIB file"):
            parser.parse_mib_file(str(test_file))

    @patch('src.mib_parser.parser.MibCompiler')
    def test_parse_mib_file_smi_error(self, mock_compiler_class):
        """Test MIB file parsing with SMI error."""
        from pysmi import error

        mock_compiler = Mock()
        mock_compiler_class.return_value = mock_compiler
        mock_compiler.compile.side_effect = error.SmiError("SMI parsing error")

        parser = MibParser()

        test_file = self.temp_dir / "test.mib"
        test_file.write_text("MALFORMED MIB")

        with pytest.raises(Exception, match="SMI error while parsing"):
            parser.parse_mib_file(str(test_file))

    def test_parse_mib_directory_not_found(self):
        """Test parsing a non-existent directory."""
        with pytest.raises(FileNotFoundError):
            self.parser.parse_mib_directory("nonexistent_directory")

    def test_parse_mib_directory_success(self):
        """Test successful directory parsing."""
        # Create test MIB files
        mib1 = self.temp_dir / "test1.mib"
        mib2 = self.temp_dir / "test2.my"
        mib3 = self.temp_dir / "README.txt"  # Not a MIB file
        sub_dir = self.temp_dir / "subdir"
        sub_dir.mkdir()
        mib4 = sub_dir / "test3.txt"

        mib1.write_text("TEST1-MIB DEFINITIONS ::= BEGIN\nEND")
        mib2.write_text("TEST2-MIB DEFINITIONS ::= BEGIN\nEND")
        mib3.write_text("This is not a MIB file")
        mib4.write_text("TEST3-MIB DEFINITIONS ::= BEGIN\nEND")

        # Mock the parse_mib_file method
        parser = MibParser()
        parser.parse_mib_file = Mock(side_effect=[
            MibData(name="TEST1-MIB"),
            MibData(name="TEST2-MIB"),
            MibData(name="TEST3-MIB")
        ])

        # Test non-recursive
        results = parser.parse_mib_directory(str(self.temp_dir), recursive=False)
        assert len(results) == 2
        assert parser.parse_mib_file.call_count == 2

        # Reset mock for recursive test
        parser.parse_mib_file.reset_mock()
        parser.parse_mib_file.side_effect = [
            MibData(name="TEST1-MIB"),
            MibData(name="TEST2-MIB"),
            MibData(name="TEST3-MIB")
        ]

        # Test recursive
        results = parser.parse_mib_directory(str(self.temp_dir), recursive=True)
        assert len(results) == 3
        assert parser.parse_mib_file.call_count == 3

    def test_parse_multiple_files(self):
        """Test parsing multiple MIB files."""
        # Create test MIB files
        file1 = self.temp_dir / "test1.mib"
        file2 = self.temp_dir / "test2.mib"
        file3 = self.temp_dir / "nonexistent.mib"

        file1.write_text("TEST1-MIB DEFINITIONS ::= BEGIN\nEND")
        file2.write_text("TEST2-MIB DEFINITIONS ::= BEGIN\nEND")

        # Mock the parse_mib_file method
        parser = MibParser()
        parser.parse_mib_file = Mock(side_effect=[
            MibData(name="TEST1-MIB"),
            MibData(name="TEST2-MIB")
        ])

        files = [str(file1), str(file2), str(file3)]
        results = parser.parse_multiple_files(files)

        assert len(results) == 2  # Only 2 successful parses
        assert results[0].name == "TEST1-MIB"
        assert results[1].name == "TEST2-MIB"

    def test_find_mib_files(self):
        """Test finding MIB files in directory."""
        # Create test files
        (self.temp_dir / "test.mib").touch()
        (self.temp_dir / "test2.my").touch()
        (self.temp_dir / "test3.txt").touch()
        (self.temp_dir / "test.py").touch()
        (self.temp_dir / "README.md").touch()

        sub_dir = self.temp_dir / "subdir"
        sub_dir.mkdir()
        (sub_dir / "subtest.mib").touch()

        # Test non-recursive
        files = parser._find_mib_files(self.temp_dir, recursive=False)
        extensions = {f.suffix.lower() for f in files}
        expected_extensions = {'.mib', '.my', '.txt'}
        assert extensions == expected_extensions
        assert len(files) == 3

        # Test recursive
        files = parser._find_mib_files(self.temp_dir, recursive=True)
        assert len(files) == 4  # Includes file in subdirectory

    def test_extract_mib_data(self):
        """Test extracting MIB data from compiled output."""
        parser = MibParser()

        # Create mock compiled data
        mock_data = Mock()
        mock_data.imports = ["SNMPv2-SMI", "SNMPv2-TC"]
        mock_data.dependencies = ["IF-MIB"]
        mock_data.description = "Test MIB module"

        # Create mock nodes
        mock_node1 = Mock()
        mock_node1.name = "testNode1"
        mock_node1.oid = "1.3.6.1.4.1.9999.1"
        mock_node1.description = "Test node 1"
        mock_node1.syntax = "INTEGER"
        mock_node1.access = "read-only"
        mock_node1.status = "current"
        mock_node1.parent = None
        mock_node1.text_convention = None
        mock_node1.units = None
        mock_node1.max_access = None
        mock_node1.reference = None
        mock_node1.defval = None
        mock_node1.hint = None

        mock_node2 = Mock()
        mock_node2.name = "testNode2"
        mock_node2.oid = "1.3.6.1.4.1.9999.1.1"
        mock_node2.description = "Test node 2"
        mock_node2.syntax = "OCTET STRING"
        mock_node2.access = "read-write"
        mock_node2.status = "current"
        mock_node2.parent = "testNode1"
        mock_node2.text_convention = "DisplayString"
        mock_node2.units = "seconds"
        mock_node2.max_access = "read-write"
        mock_node2.reference = None
        mock_node2.defval = None
        mock_node2.hint = None

        mock_data.nodes = {
            "testNode1": mock_node1,
            "testNode2": mock_node2
        }

        # Mock the _extract_node_data method
        parser._extract_node_data = Mock(side_effect=lambda name, data, module: MibNode(
            name=name,
            oid=data.oid,
            description=data.description,
            syntax=data.syntax,
            access=data.access,
            status=data.status,
            parent_name=data.parent if hasattr(data, 'parent') and data.parent else None,
            module=module,
            text_convention=data.text_convention,
            units=data.units,
            max_access=data.max_access,
            reference=data.reference,
            defval=data.defval,
            hint=data.hint,
        ))

        result = parser._extract_mib_data(mock_data, "TEST-MIB")

        assert result.name == "TEST-MIB"
        assert result.description == "Test MIB module"
        assert result.imports == ["SNMPv2-SMI", "SNMPv2-TC"]
        assert result.module_dependencies == ["IF-MIB"]
        assert len(result.nodes) == 2
        assert "testNode1" in result.nodes
        assert "testNode2" in result.nodes

        # Check that parent-child relationships are established
        node1 = result.nodes["testNode1"]
        node2 = result.nodes["testNode2"]
        assert "testNode2" in node1.children
        assert node2.parent_name == "testNode1"

    def test_extract_node_data(self):
        """Test extracting data for a single node."""
        parser = MibParser()

        # Create mock node data
        mock_node = Mock()
        mock_node.oid = "1.3.6.1.4.1.9999.1"
        mock_node.description = "Test node description"
        mock_node.syntax = "INTEGER { range(0..100) }"
        mock_node.access = "read-only"
        mock_node.status = "current"
        mock_node.parent = "parentNode"
        mock_node.text_convention = "DisplayString"
        mock_node.units = "seconds"
        mock_node.max_access = "read-only"
        mock_node.reference = "RFC1213"
        mock_node.defval = "0"
        mock_node.hint = "255a"

        result = parser._extract_node_data("testNode", mock_node, "TEST-MIB")

        assert result.name == "testNode"
        assert result.oid == "1.3.6.1.4.1.9999.1"
        assert result.description == "Test node description"
        assert result.syntax == "INTEGER { range(0..100) }"
        assert result.access == "read-only"
        assert result.status == "current"
        assert result.parent_name == "parentNode"
        assert result.module == "TEST-MIB"
        assert result.text_convention == "DisplayString"
        assert result.units == "seconds"
        assert result.max_access == "read-only"
        assert result.reference == "RFC1213"
        assert result.defval == "0"
        assert result.hint == "255a"

    def test_get_default_mib_sources(self):
        """Test getting default MIB source directories."""
        sources = self.parser._get_default_mib_sources()
        assert isinstance(sources, list)
        assert len(sources) > 0

        # Should include current working directory if it exists
        import os
        if os.path.exists('.'):
            assert os.getcwd() in sources

    def test_setup_compiler(self):
        """Test compiler setup."""
        parser = MibParser()
        parser._setup_compiler()

        assert parser.mib_compiler is not None
        # The compiler should have sources, codegen, and borrower configured