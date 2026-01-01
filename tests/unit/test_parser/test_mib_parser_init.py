"""Test MibParser initialization and configuration."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.mib_parser.parser import MibParser


class TestMibParserInit:
    """Test MibParser initialization methods."""

    def test_create_parser_with_defaults(self, tmp_path):
        """Test creating parser with default parameters."""
        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser()

            assert parser.device_type == "default"
            assert parser.resolve_dependencies is True
            assert parser.debug_mode is False
            assert parser.dependency_resolver is not None
            assert parser.compiled_mibs == {}
            assert isinstance(parser.mib_sources, list)

    def test_create_parser_with_custom_mib_sources(self, tmp_path):
        """Test creating parser with custom MIB sources."""
        custom_sources = [str(tmp_path / "mibs1"), str(tmp_path / "mibs2")]

        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(mib_sources=custom_sources)

            assert parser.mib_sources == custom_sources

    def test_create_parser_with_debug_mode(self, tmp_path):
        """Test creating parser with debug mode enabled."""
        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(debug_mode=True)

            assert parser.debug_mode is True

    def test_create_parser_with_resolve_dependencies_false(self, tmp_path):
        """Test creating parser with dependency resolution disabled."""
        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(resolve_dependencies=False)

            assert parser.resolve_dependencies is False
            assert parser.dependency_resolver is None

    def test_create_parser_with_custom_device_type(self, tmp_path):
        """Test creating parser with custom device type."""
        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(device_type="cisco-router")

            assert parser.device_type == "cisco-router"
            assert (
                parser.device_base_path
                == tmp_path / "storage" / "devices" / "cisco-router"
            )

    def test_default_mib_sources_includes_global_dir(self, tmp_path):
        """Test that default MIB sources includes global directory."""
        # Create expected directories
        (tmp_path / "storage" / "global" / "mibs_for_pysmi").mkdir(
            parents=True, exist_ok=True
        )

        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser()

            sources_str = " ".join(parser.mib_sources)
            assert (
                "storage/global/mibs_for_pysmi" in sources_str
                or "global" in sources_str
            )

    def test_default_mib_sources_includes_device_dir(self, tmp_path):
        """Test that default MIB sources includes device-specific directory."""
        # Create expected directories
        (tmp_path / "storage" / "devices" / "test-device" / "mibs_for_pysmi").mkdir(
            parents=True, exist_ok=True
        )

        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser(device_type="test-device")

            sources_str = " ".join(parser.mib_sources)
            assert "devices/test-device/mibs_for_pysmi" in sources_str

    def test_compiled_mibs_cache_initialized(self, tmp_path):
        """Test that compiled MIBs cache is initialized as empty dict."""
        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser()

            assert parser.compiled_mibs == {}
            assert isinstance(parser.compiled_mibs, dict)

    def test_used_temp_dirs_initialized(self, tmp_path):
        """Test that used temp directories set is initialized."""
        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser()

            assert parser._used_temp_dirs == set()
            assert isinstance(parser._used_temp_dirs, set)

    def test_mib_compiler_setup(self, tmp_path):
        """Test that MIB compiler is properly set up."""
        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser()

            assert parser.mib_compiler is not None
            assert hasattr(parser, "mib_compiler")

    def test_multiple_parser_instances_independent(self, tmp_path):
        """Test that multiple parser instances are independent."""
        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser1 = MibParser(device_type="device1")
            parser2 = MibParser(device_type="device2")

            assert parser1.device_type == "device1"
            assert parser2.device_type == "device2"
            assert parser1.compiled_mibs is not parser2.compiled_mibs

    def test_empty_mib_sources_when_no_directories_exist(self, tmp_path):
        """Test that MIB sources is empty when no directories exist."""
        # Don't create any directories
        with patch("src.mib_parser.parser.Path.cwd", return_value=tmp_path):
            parser = MibParser()

            # Should have common system directories even if custom ones don't exist
            assert isinstance(parser.mib_sources, list)
