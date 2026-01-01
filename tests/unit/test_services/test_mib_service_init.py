"""Test MibService initialization and configuration."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.flask_app.services.mib_service import MibService


class TestMibServiceInit:
    """Test MibService class initialization."""

    def test_service_initialization_with_defaults(self, tmp_path):
        """Test service initialization with default parameters."""
        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            assert service.output_dir == tmp_path
            assert service.compiled_mibs_dir is None
            assert service.device_type is None
            assert service._mib_cache == {}
            assert service._last_cache_update == {}
            assert service.global_output_dir == tmp_path / "storage" / "global" / "output"

    def test_service_initialization_with_compiled_mibs_dir(self, tmp_path):
        """Test service initialization with compiled_mibs_dir parameter."""
        compiled_dir = tmp_path / "compiled_mibs"
        compiled_dir.mkdir(parents=True, exist_ok=True)

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(
                output_dir=tmp_path, compiled_mibs_dir=compiled_dir
            )

            assert service.compiled_mibs_dir == compiled_dir

    def test_service_initialization_with_device_type(self, tmp_path):
        """Test service initialization with device_type parameter."""
        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path, device_type="test-device")

            assert service.device_type == "test-device"

    def test_service_initialization_path_conversion(self, tmp_path):
        """Test that string paths are converted to Path objects."""
        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=str(tmp_path))

            assert isinstance(service.output_dir, Path)
            assert service.output_dir == tmp_path

    def test_cache_initialization_empty(self, tmp_path):
        """Test that cache is initialized as empty dict."""
        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            assert service._mib_cache == {}
            assert service._last_cache_update == {}

    def test_global_output_dir_setup(self, tmp_path):
        """Test that global_output_dir is set correctly."""
        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            expected_global_dir = tmp_path / "storage" / "global" / "output"
            assert service.global_output_dir == expected_global_dir

    def test_all_parameters_combined(self, tmp_path):
        """Test initialization with all parameters provided."""
        compiled_dir = tmp_path / "compiled"
        compiled_dir.mkdir(parents=True)

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(
                output_dir=tmp_path,
                compiled_mibs_dir=compiled_dir,
                device_type="custom-device"
            )

            assert service.output_dir == tmp_path
            assert service.compiled_mibs_dir == compiled_dir
            assert service.device_type == "custom-device"
            assert service._mib_cache == {}
            assert service._last_cache_update == {}

    def test_output_dir_does_not_exist(self, tmp_path):
        """Test initialization when output_dir doesn't exist yet."""
        non_existent_dir = tmp_path / "non_existent"

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            # Should not raise error - service doesn't require output_dir to exist at init
            service = MibService(output_dir=non_existent_dir)

            assert service.output_dir == non_existent_dir

    def test_compiled_mibs_dir_path_conversion(self, tmp_path):
        """Test that compiled_mibs_dir string is converted to Path."""
        compiled_dir = tmp_path / "compiled"

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(
                output_dir=tmp_path,
                compiled_mibs_dir=str(compiled_dir)
            )

            assert isinstance(service.compiled_mibs_dir, Path)
            assert service.compiled_mibs_dir == compiled_dir

    def test_device_context_retrieval(self, tmp_path):
        """Test get_device_context method."""
        compiled_dir = tmp_path / "compiled"
        compiled_dir.mkdir(parents=True)

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(
                output_dir=tmp_path,
                compiled_mibs_dir=compiled_dir,
                device_type="test-device"
            )

            context = service.get_device_context()

            assert context['device_type'] == "test-device"
            assert context['output_dir'] == str(tmp_path)
            assert context['compiled_mibs_dir'] == str(compiled_dir)

    def test_device_context_with_none_compiled_dir(self, tmp_path):
        """Test get_device_context when compiled_mibs_dir is None."""
        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(
                output_dir=tmp_path,
                device_type="default-device"
            )

            context = service.get_device_context()

            assert context['device_type'] == "default-device"
            assert context['output_dir'] == str(tmp_path)
            assert context['compiled_mibs_dir'] is None
