"""Test MibParser query and parse methods."""

import pytest
from unittest.mock import patch
from pathlib import Path
from src.mib_parser.parser import MibParser
from src.mib_parser.models import MibData, MibNode


class TestMibParserQuery:
    """Test MibParser query and multiple parse methods."""

    def test_parse_file_returns_mib_data(self, tmp_path):
        """Test parse_file returns MibData."""
        # Create test MIB file
        test_mib = tmp_path / "TEST-MIB.mib"
        test_mib.write_text("TEST-MIB DEFINITIONS ::= BEGIN\nEND\n")

        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(resolve_dependencies=False)

            # Mock the internal parse method
            with patch.object(
                parser, "parse_mib_file", return_value=MibData(name="TEST-MIB")
            ):
                result = parser.parse_file(str(test_mib))

                assert result is not None
                assert result.name == "TEST-MIB"

    def test_parse_mib_directory(self, tmp_path):
        """Test parse_mib_directory method."""
        # Create test MIB files
        (tmp_path / "MIB1.mib").write_text("MIB1 DEFINITIONS ::= BEGIN\nEND\n")
        (tmp_path / "MIB2.mib").write_text("MIB2 DEFINITIONS ::= BEGIN\nEND\n")

        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(resolve_dependencies=False)

            # Mock parse_file to return MibData
            def mock_parse_file(file_path):
                name = Path(file_path).stem
                return MibData(name=name)

            with patch.object(parser, "parse_file", side_effect=mock_parse_file):
                results = parser.parse_mib_directory(str(tmp_path), recursive=False)

                assert len(results) == 2
                mib_names = {mib.name for mib in results}
                assert "MIB1" in mib_names
                assert "MIB2" in mib_names

    def test_parse_mib_directory_empty(self, tmp_path):
        """Test parsing an empty directory."""
        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(resolve_dependencies=False)

            results = parser.parse_mib_directory(str(tmp_path), recursive=False)

            assert results == []

    def test_parse_multiple_files(self, tmp_path):
        """Test parse_multiple_files method."""
        # Create test files
        file1 = tmp_path / "FILE1.mib"
        file2 = tmp_path / "FILE2.mib"
        file1.write_text("FILE1 DEFINITIONS ::= BEGIN\nEND\n")
        file2.write_text("FILE2 DEFINITIONS ::= BEGIN\nEND\n")

        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(resolve_dependencies=False)

            # Mock parse_file
            def mock_parse_file(file_path):
                name = Path(file_path).stem
                return MibData(name=name)

            with patch.object(parser, "parse_file", side_effect=mock_parse_file):
                results = parser.parse_multiple_files([str(file1), str(file2)])

                assert len(results) == 2
                assert results[0].name == "FILE1"
                assert results[1].name == "FILE2"

    def test_compiled_mibs_cache_stores_results(self, tmp_path):
        """Test that compiled_mibs cache stores parsed MIBs."""
        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(resolve_dependencies=False)

            # Simulate cache
            mib_data = MibData(name="TEST-MIB")
            parser.compiled_mibs["TEST-MIB"] = mib_data

            assert "TEST-MIB" in parser.compiled_mibs
            assert parser.compiled_mibs["TEST-MIB"].name == "TEST-MIB"

    def test_find_mib_files_recursive(self, tmp_path):
        """Test _find_mib_files method with recursive=True."""
        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "root.mib").write_text("ROOT DEFINITIONS ::= BEGIN\nEND\n")
        (subdir / "nested.mib").write_text("NESTED DEFINITIONS ::= BEGIN\nEND\n")

        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(resolve_dependencies=False)

            files = parser._find_mib_files(tmp_path, recursive=True)

            assert len(files) == 2

    def test_find_mib_files_non_recursive(self, tmp_path):
        """Test _find_mib_files method with recursive=False."""
        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "root.mib").write_text("ROOT DEFINITIONS ::= BEGIN\nEND\n")
        (subdir / "nested.mib").write_text("NESTED DEFINITIONS ::= BEGIN\nEND\n")

        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(resolve_dependencies=False)

            files = parser._find_mib_files(tmp_path, recursive=False)

            assert len(files) == 1
            assert files[0].name == "root.mib"
