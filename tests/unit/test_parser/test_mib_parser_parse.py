"""Test MibParser MIB file parsing methods."""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from pysmi.error import PySmiError
from src.mib_parser.parser import MibParser
from src.mib_parser.models import MibData, MibNode


class TestMibParserParse:
    """Test MibParser.parse_mib_file() method."""

    @patch("src.mib_parser.parser.MibCompiler")
    @patch("src.mib_parser.parser.FileWriter")
    @patch("src.mib_parser.parser.JsonCodeGen")
    @patch("src.mib_parser.parser.SmiStarParser")
    def test_parse_mib_file_success(
        self, mock_parser, mock_codegen, mock_writer, mock_compiler, tmp_path
    ):
        """Test successful parsing of a MIB file."""
        # Create test MIB file
        test_mib = tmp_path / "TEST-MIB.mib"
        test_mib.write_text(
            """TEST-MIB DEFINITIONS ::= BEGIN
END
"""
        )

        # Mock compiler instance
        mock_compiler_instance = MagicMock()
        mock_compiler.return_value = mock_compiler_instance

        # Mock compilation result
        mock_result = MagicMock()
        mock_result.get_status.return_value = "success"
        mock_compiler_instance.compile.return_value = mock_result

        # Create compiled JSON file
        compiled_dir = tmp_path / "storage" / "devices" / "default" / "compiled_mibs"
        compiled_dir.mkdir(parents=True, exist_ok=True)
        compiled_file = compiled_dir / "TEST-MIB"
        compiled_file.write_text('{"nodes": {}}')

        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(resolve_dependencies=False)

            result = parser.parse_mib_file(str(test_mib))

            assert result is not None

    def test_parse_mib_file_not_found(self, tmp_path):
        """Test parsing a non-existent file raises FileNotFoundError."""
        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(resolve_dependencies=False)

            with pytest.raises(FileNotFoundError, match="MIB file not found"):
                parser.parse_mib_file("/nonexistent/file.mib")

    @patch("src.mib_parser.parser.MibCompiler")
    @patch("src.mib_parser.parser.FileWriter")
    @patch("src.mib_parser.parser.JsonCodeGen")
    @patch("src.mib_parser.parser.SmiStarParser")
    def test_parse_mib_file_compilation_failure(
        self, mock_parser, mock_codegen, mock_writer, mock_compiler, tmp_path
    ):
        """Test handling of compilation failure."""
        # Create test MIB file
        test_mib = tmp_path / "INVALID-MIB.mib"
        test_mib.write_text("INVALID-MIB DEFINITIONS ::= BEGIN\n")

        # Mock compiler instance
        mock_compiler_instance = MagicMock()
        mock_compiler.return_value = mock_compiler_instance

        # Mock compiler to return failure
        mock_result = MagicMock()
        mock_result.get_status.return_value = "failed"
        mock_compiler_instance.compile.return_value = mock_result

        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(resolve_dependencies=False)

            with pytest.raises(Exception, match="Compilation failed"):
                parser.parse_mib_file(str(test_mib))

    @patch("src.mib_parser.parser.MibCompiler")
    @patch("src.mib_parser.parser.FileWriter")
    @patch("src.mib_parser.parser.JsonCodeGen")
    @patch("src.mib_parser.parser.SmiStarParser")
    def test_parse_mib_file_with_pysmi_error(
        self, mock_parser_class, mock_codegen, mock_writer, mock_compiler, tmp_path
    ):
        """Test handling of PySmiError during compilation."""
        # Create test MIB file
        test_mib = tmp_path / "TEST-MIB.mib"
        test_mib.write_text("TEST-MIB DEFINITIONS ::= BEGIN\n")

        # Mock compiler instance
        mock_compiler_instance = MagicMock()
        mock_compiler.return_value = mock_compiler_instance

        # Mock compiler to raise PySmiError
        mock_compiler_instance.compile.side_effect = PySmiError("SMI error")

        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(resolve_dependencies=False)

            # The error gets wrapped, so just check for any exception
            with pytest.raises(Exception):
                parser.parse_mib_file(str(test_mib))

    def test_extract_mib_name_from_content(self, tmp_path):
        """Test _extract_mib_name_from_content method."""
        # Create test MIB file with proper DEFINITIONS clause
        test_mib = tmp_path / "test-file.mib"
        test_mib.write_text(
            """MY-MIB DEFINITIONS ::= BEGIN
EXPORTS EVERYTHING;
END
"""
        )

        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(resolve_dependencies=False)

            mib_name = parser._extract_mib_name_from_content(test_mib)
            assert mib_name == "MY-MIB"

    def test_extract_mib_name_handles_whitespace(self, tmp_path):
        """Test _extract_mib_name_from_content with various whitespace."""
        test_mib = tmp_path / "test-file.mib"
        test_mib.write_text(
            """  WHITESPACE-MIB
DEFINITIONS
::=
BEGIN
END
"""
        )

        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(resolve_dependencies=False)

            mib_name = parser._extract_mib_name_from_content(test_mib)
            assert mib_name == "WHITESPACE-MIB"

    def test_extract_mib_name_fallback_to_filename(self, tmp_path):
        """Test _extract_mib_name_from_content falls back to filename."""
        test_mib = tmp_path / "test-file.mib"
        test_mib.write_text("This is not a valid MIB file")

        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(resolve_dependencies=False)

            # Should fall back to filename
            mib_name = parser._extract_mib_name_from_content(test_mib)
            assert mib_name == "test-file"
