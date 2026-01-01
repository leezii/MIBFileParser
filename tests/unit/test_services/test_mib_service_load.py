"""Test MibService MIB loading methods."""

import pytest
import json
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from src.flask_app.services.mib_service import MibService


class TestMibServiceLoad:
    """Test MibService MIB loading and caching methods."""

    def test_get_mib_data_from_file(self, tmp_path):
        """Test loading MIB data from JSON file."""
        # Create test MIB JSON file
        mib_data = {
            "name": "TEST-MIB",
            "module": "TEST",
            "description": "Test MIB",
            "nodes": {
                "sysDescr": {
                    "oid": "1.3.6.1.2.1.1.1",
                    "name": "sysDescr",
                    "syntax": "DisplayString"
                }
            },
            "imports": ["SNMPv2-TC"]
        }
        mib_file = tmp_path / "TEST-MIB.json"
        mib_file.write_text(json.dumps(mib_data))

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            result = service.get_mib_data("TEST-MIB", use_cache=False)

            assert result is not None
            assert result["name"] == "TEST-MIB"
            assert result["module"] == "TEST"
            assert "sysDescr" in result["nodes"]

    def test_get_mib_data_caches_results(self, tmp_path):
        """Test that get_mib_data caches results."""
        mib_data = {
            "name": "CACHE-MIB",
            "module": "CACHE",
            "nodes": {}
        }
        mib_file = tmp_path / "CACHE-MIB.json"
        mib_file.write_text(json.dumps(mib_data))

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            # First call with cache
            result1 = service.get_mib_data("CACHE-MIB", use_cache=True)
            assert "CACHE-MIB" in service._mib_cache

            # Second call should use cache
            result2 = service.get_mib_data("CACHE-MIB", use_cache=True)
            assert result1 == result2

    def test_get_mib_data_not_found(self, tmp_path):
        """Test get_mib_data with non-existent MIB."""
        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            result = service.get_mib_data("NON-EXISTENT", use_cache=False)

            assert result is None

    def test_get_mib_data_invalid_json(self, tmp_path):
        """Test get_mib_data with invalid JSON file."""
        # Create invalid JSON file
        mib_file = tmp_path / "INVALID-MIB.json"
        mib_file.write_text("{invalid json content")

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            result = service.get_mib_data("INVALID-MIB", use_cache=False)

            assert result is None

    def test_get_mib_data_with_mib_extension(self, tmp_path):
        """Test get_mib_data with .mib.json extension."""
        mib_data = {"name": "EXT-MIB", "module": "EXT", "nodes": {}}
        mib_file = tmp_path / "EXT-MIB.mib.json"
        mib_file.write_text(json.dumps(mib_data))

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            result = service.get_mib_data("EXT-MIB", use_cache=False)

            assert result is not None
            assert result["name"] == "EXT-MIB"

    def test_get_mib_data_from_global_dir(self, tmp_path):
        """Test get_mib_data loads from global directory first."""
        # Create global and device directories
        global_dir = tmp_path / "storage" / "global" / "output"
        device_dir = tmp_path / "storage" / "devices" / "test-device" / "output"
        global_dir.mkdir(parents=True)
        device_dir.mkdir(parents=True)

        # Create same MIB in both directories
        global_mib = {"name": "SHARED-MIB", "source": "global", "nodes": {}}
        device_mib = {"name": "SHARED-MIB", "source": "device", "nodes": {}}

        (global_dir / "SHARED-MIB.json").write_text(json.dumps(global_mib))
        (device_dir / "SHARED-MIB.json").write_text(json.dumps(device_mib))

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=device_dir)

            result = service.get_mib_data("SHARED-MIB", use_cache=False)

            # Should load from global directory first
            assert result is not None
            assert result["source"] == "global"

    def test_clear_cache_specific_mib(self, tmp_path):
        """Test clearing cache for specific MIB."""
        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            # Add to cache
            service._mib_cache["TEST-MIB"] = {"name": "TEST"}
            service._last_cache_update["TEST-MIB"] = 12345

            # Clear specific MIB
            service.clear_cache("TEST-MIB")

            assert "TEST-MIB" not in service._mib_cache
            assert "TEST-MIB" not in service._last_cache_update

    def test_clear_cache_all(self, tmp_path):
        """Test clearing all cache."""
        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            # Add multiple MIBs to cache
            service._mib_cache["MIB1"] = {"name": "MIB1"}
            service._mib_cache["MIB2"] = {"name": "MIB2"}
            service._last_cache_update["MIB1"] = 12345
            service._last_cache_update["MIB2"] = 67890

            # Clear all cache
            service.clear_cache()

            assert service._mib_cache == {}
            assert service._last_cache_update == {}

    def test_load_mib_data_from_file_directly(self, tmp_path):
        """Test _load_mib_data_from_file method."""
        mib_data = {"name": "DIRECT-MIB", "module": "DIRECT", "nodes": {}}
        mib_file = tmp_path / "DIRECT-MIB.json"
        mib_file.write_text(json.dumps(mib_data))

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            result = service._load_mib_data_from_file("DIRECT-MIB")

            assert result is not None
            assert result["name"] == "DIRECT-MIB"

    def test_load_mib_data_from_file_not_found(self, tmp_path):
        """Test _load_mib_data_from_file with non-existent file."""
        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            result = service._load_mib_data_from_file("NOT-FOUND")

            assert result is None
