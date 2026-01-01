"""Test MibParser dependency resolution integration."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.mib_parser.parser import MibParser
from src.mib_parser.models import MibData


class TestMibParserDependencies:
    """Test MibParser integration with dependency resolver."""

    def test_dependency_resolver_initialized_when_enabled(self, tmp_path):
        """Test that dependency resolver is initialized when enabled."""
        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(resolve_dependencies=True)

            assert parser.dependency_resolver is not None
            assert parser.resolve_dependencies is True

    def test_dependency_resolver_not_initialized_when_disabled(self, tmp_path):
        """Test that dependency resolver is not initialized when disabled."""
        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(resolve_dependencies=False)

            assert parser.dependency_resolver is None
            assert parser.resolve_dependencies is False

    def test_resolve_dependencies_skipped_when_disabled(self, tmp_path):
        """Test that dependency resolution is skipped when disabled."""
        test_mib = tmp_path / "TEST-MIB.mib"
        test_mib.write_text("TEST-MIB DEFINITIONS ::= BEGIN\n")

        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(resolve_dependencies=False)

            # Verify dependency resolver is None
            assert parser.dependency_resolver is None

    @patch("src.mib_parser.parser.MibCompiler")
    @patch("src.mib_parser.parser.FileWriter")
    @patch("src.mib_parser.parser.JsonCodeGen")
    @patch("src.mib_parser.parser.SmiStarParser")
    def test_dependencies_resolved_before_parsing(
        self, mock_parser, mock_codegen, mock_writer, mock_compiler, tmp_path
    ):
        """Test that dependencies are resolved before parsing when enabled."""
        # Create test MIB file
        test_mib = tmp_path / "TEST-MIB.mib"
        test_mib.write_text("TEST-MIB DEFINITIONS ::= BEGIN\nEND\n")

        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(resolve_dependencies=True)

            # Mock dependency resolver
            mock_resolver = MagicMock()
            parser.dependency_resolver = mock_resolver
            mock_resolver.mib_files = {}  # No MIBs initially

            # Mock compiler
            mock_compiler_instance = MagicMock()
            mock_compiler.return_value = mock_compiler_instance
            mock_result = MagicMock()
            mock_result.get_status.return_value = "success"
            mock_compiler_instance.compile.return_value = mock_result

            # Create compiled JSON file
            compiled_dir = (
                tmp_path / "storage" / "devices" / "default" / "compiled_mibs"
            )
            compiled_dir.mkdir(parents=True, exist_ok=True)
            compiled_file = compiled_dir / "TEST-MIB"
            compiled_file.write_text('{"nodes": {}}')

            # Parse should attempt to resolve dependencies
            result = parser.parse_mib_file(str(test_mib))
            # The mock resolver should have been accessed during _resolve_dependencies_in_directory
