"""Test MibService file upload and complex methods."""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Mock pysmi modules before importing anything
sys.modules['pysmi'] = MagicMock()
sys.modules['pysmi.compiler'] = MagicMock()
sys.modules['pysmi.parser'] = MagicMock()
sys.modules['pysmi.writer'] = MagicMock()
sys.modules['pysmi.codegen'] = MagicMock()
sys.modules['pysmi.reader'] = MagicMock()
sys.modules['pysmi.error'] = MagicMock()
sys.modules['pysmi.borrower'] = MagicMock()

# Mock mib_parser modules before importing MibService
sys.modules['mib_parser'] = MagicMock()
sys.modules['mib_parser.parser'] = MagicMock()
sys.modules['mib_parser.serializer'] = MagicMock()
sys.modules['mib_parser.leaf_extractor'] = MagicMock()

# Also add to src namespace
import src
src.mib_parser = sys.modules['mib_parser']

from src.flask_app.services.mib_service import MibService


class TestMibServiceUpload:
    """Test MibService file upload and complex methods."""

    def test_add_uploaded_files_success(self, tmp_path):
        """Test successful file upload with mock parser."""
        # Create test MIB file
        test_mib = tmp_path / "TEST-MIB.mib"
        test_mib.write_text("TEST-MIB DEFINITIONS ::= BEGIN\nEND\n")

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path / "output")

            # Mock parser and its components (MibParser is imported inside add_uploaded_files)
            with patch("src.mib_parser.parser.MibParser") as mock_parser_class:
                mock_parser = MagicMock()
                mock_parser_class.return_value = mock_parser

                # Mock parse result
                mock_mib_data = MagicMock()
                mock_mib_data.name = "TEST-MIB"
                mock_mib_data.nodes = {"node1": {"oid": "1.1"}}
                mock_parser.parse_file.return_value = mock_mib_data

                # Mock serializer
                with patch("src.mib_parser.serializer.JsonSerializer") as mock_serializer:
                    result = service.add_uploaded_files([test_mib], device_type="test")

                    assert result["total_added"] == 1
                    assert len(result["success"]) == 1
                    assert result["success"][0]["mib_name"] == "TEST-MIB"

    def test_add_uploaded_files_with_parsing_error(self, tmp_path):
        """Test handling of parsing errors."""
        test_mib = tmp_path / "INVALID-MIB.mib"
        test_mib.write_text("INVALID CONTENT")

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path / "output")

            with patch("src.mib_parser.parser.MibParser") as mock_parser_class:
                mock_parser = MagicMock()
                mock_parser_class.return_value = mock_parser

                # Mock parser to raise exception
                mock_parser.parse_file.side_effect = Exception("Syntax error")

                result = service.add_uploaded_files([test_mib])

                assert result["total_added"] == 0
                assert len(result["errors"]) == 1

    def test_add_uploaded_files_multiple_files(self, tmp_path):
        """Test uploading multiple files."""
        test_mibs = [
            tmp_path / "MIB1.mib",
            tmp_path / "MIB2.mib"
        ]
        for mib in test_mibs:
            mib.write_text(f"{mib.stem}-MIB DEFINITIONS ::= BEGIN\nEND\n")

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path / "output")

            with patch("src.mib_parser.parser.MibParser") as mock_parser_class:
                mock_parser = MagicMock()
                mock_parser_class.return_value = mock_parser

                def mock_parse(file_path):
                    name = Path(file_path).stem
                    mib_data = MagicMock()
                    mib_data.name = name
                    mib_data.nodes = {}
                    return mib_data

                mock_parser.parse_file.side_effect = mock_parse

                with patch("src.mib_parser.serializer.JsonSerializer"):
                    result = service.add_uploaded_files(test_mibs)

                    assert result["total_added"] == 2

    def test_clear_cache_all(self, tmp_path):
        """Test clearing all cache."""
        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            # Add some cache data
            service._mib_cache["MIB1"] = {"name": "MIB1"}
            service._mib_cache["MIB2"] = {"name": "MIB2"}
            service._last_cache_update["MIB1"] = 12345
            service._last_cache_update["MIB2"] = 67890

            service.clear_cache()

            assert service._mib_cache == {}
            assert service._last_cache_update == {}

    def test_clear_cache_specific_mib(self, tmp_path):
        """Test clearing cache for specific MIB."""
        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            service._mib_cache["MIB1"] = {"name": "MIB1"}
            service._mib_cache["MIB2"] = {"name": "MIB2"}
            service._last_cache_update["MIB1"] = 12345

            service.clear_cache("MIB1")

            assert "MIB1" not in service._mib_cache
            assert "MIB2" in service._mib_cache

    def test_get_device_context(self, tmp_path):
        """Test getting device context."""
        compiled_dir = tmp_path / "compiled"
        compiled_dir.mkdir()

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(
                output_dir=tmp_path / "output",
                compiled_mibs_dir=compiled_dir,
                device_type="test-device"
            )

            context = service.get_device_context()

            assert context["device_type"] == "test-device"
            assert context["output_dir"] == str(tmp_path / "output")
            assert context["compiled_mibs_dir"] == str(compiled_dir)

    def test_get_statistics_empty(self, tmp_path):
        """Test statistics with no MIBs."""
        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            stats = service.get_statistics()

            assert stats["total_mibs"] == 0
            assert stats["total_nodes"] == 0
            assert stats["mibs_with_data"] == 0


class TestMibServiceTreeData:
    """Test MIB tree data methods."""

    def test_get_mib_tree_data(self, tmp_path):
        """Test getting tree-structured MIB data."""
        mib_data = {
            "name": "TEST-MIB",
            "nodes": {
                "root": {"oid": "1.3.6.1", "name": "root"}
            }
        }

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            with patch.object(service, "get_mib_data", return_value=mib_data):
                with patch("src.flask_app.services.tree_service.TreeService") as mock_tree_svc:
                    mock_tree_service = MagicMock()
                    mock_tree_service.build_tree_structure.return_value = {
                        "name": "TEST-MIB",
                        "children": []
                    }
                    mock_tree_svc.return_value = mock_tree_service

                    result = service.get_mib_tree_data("TEST-MIB")

                    assert result is not None
                    assert "children" in result

    def test_get_mib_tree_data_not_found(self, tmp_path):
        """Test getting tree data for non-existent MIB."""
        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            with patch.object(service, "get_mib_data", return_value=None):
                result = service.get_mib_tree_data("NON-EXISTENT")

                assert result is None
