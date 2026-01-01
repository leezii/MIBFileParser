"""Test DeviceService class."""

import pytest
import json
from pathlib import Path
from src.flask_app.services.device_service import DeviceService, DeviceInfo


class TestDeviceService:
    """Test DeviceService class."""

    def test_service_initialization(self, tmp_path):
        """Test DeviceService initialization."""
        service = DeviceService(storage_root=tmp_path)

        assert service.storage_root == tmp_path
        assert service.devices_dir == tmp_path / "devices"
        assert service.uploads_dir == tmp_path / "uploads"
        assert service.temp_dir == tmp_path / "uploads" / "temp"
        assert service.registry_file == tmp_path / "device_registry.json"

    def test_directories_created_on_init(self, tmp_path):
        """Test that required directories are created."""
        service = DeviceService(storage_root=tmp_path)

        assert service.devices_dir.exists()
        assert service.uploads_dir.exists()
        assert service.temp_dir.exists()

    def test_registry_file_created(self, tmp_path):
        """Test that registry file is created if it doesn't exist."""
        service = DeviceService(storage_root=tmp_path)

        assert service.registry_file.exists()

        # Check default content
        registry = service._load_registry()
        assert registry["devices"] == []
        assert registry["current_device"] == "default"
        assert registry["version"] == "1.0"

    def test_list_devices_empty(self, tmp_path):
        """Test list_devices with no devices."""
        service = DeviceService(storage_root=tmp_path)

        devices = service.list_devices()

        assert devices == []

    def test_create_device_success(self, tmp_path):
        """Test successful device creation."""
        service = DeviceService(storage_root=tmp_path)

        result = service.create_device("test-device", "Test Device", "Test Description")

        assert result is True

        # Check device directory was created
        device_dir = tmp_path / "devices" / "test-device"
        assert device_dir.exists()
        assert (device_dir / "compiled_mibs").exists()
        assert (device_dir / "mibs_for_pysmi").exists()
        assert (device_dir / "output").exists()

        # Check registry
        devices = service.list_devices()
        assert len(devices) == 1
        assert devices[0].name == "test-device"
        assert devices[0].display_name == "Test Device"
        assert devices[0].description == "Test Description"

    def test_create_device_defaults(self, tmp_path):
        """Test device creation with default values."""
        service = DeviceService(storage_root=tmp_path)

        result = service.create_device("default-device")

        assert result is True

        devices = service.list_devices()
        assert len(devices) == 1
        assert devices[0].display_name == "default-device"
        assert devices[0].description == "MIB files for default-device"

    def test_create_duplicate_device(self, tmp_path):
        """Test creating duplicate device fails."""
        service = DeviceService(storage_root=tmp_path)

        # Create first device
        service.create_device("test-device")

        # Try to create duplicate
        result = service.create_device("test-device")

        assert result is False

    def test_create_device_invalid_name(self, tmp_path):
        """Test creating device with invalid name."""
        service = DeviceService(storage_root=tmp_path)

        with pytest.raises(ValueError, match="Invalid device name"):
            service.create_device("")

        with pytest.raises(ValueError, match="Invalid device name"):
            service.create_device("   ")

    def test_delete_device_success(self, tmp_path):
        """Test successful device deletion."""
        service = DeviceService(storage_root=tmp_path)

        # Create device
        service.create_device("test-device")
        assert len(service.list_devices()) == 1

        # Delete device
        result = service.delete_device("test-device")

        assert result is True
        assert len(service.list_devices()) == 0

        # Check directory was deleted
        assert not (tmp_path / "devices" / "test-device").exists()

    def test_delete_default_device_forbidden(self, tmp_path):
        """Test that default device cannot be deleted."""
        service = DeviceService(storage_root=tmp_path)

        with pytest.raises(ValueError, match="Cannot delete default device"):
            service.delete_device("default")

    def test_delete_nonexistent_device(self, tmp_path):
        """Test deleting non-existent device."""
        service = DeviceService(storage_root=tmp_path)

        result = service.delete_device("nonexistent")

        assert result is False

    def test_get_device_info_found(self, tmp_path):
        """Test getting info for existing device."""
        service = DeviceService(storage_root=tmp_path)

        service.create_device("test-device", "Test Device")

        info = service.get_device_info("test-device")

        assert info is not None
        assert info.name == "test-device"
        assert info.display_name == "Test Device"

    def test_get_device_info_not_found(self, tmp_path):
        """Test getting info for non-existent device."""
        service = DeviceService(storage_root=tmp_path)

        info = service.get_device_info("nonexistent")

        assert info is None

    def test_device_mib_count_updates(self, tmp_path):
        """Test that mib_count reflects actual files."""
        service = DeviceService(storage_root=tmp_path)

        service.create_device("test-device")

        # Initially 0 MIBs
        devices = service.list_devices()
        assert devices[0].mib_count == 0

        # Add MIB files to output directory
        output_dir = tmp_path / "devices" / "test-device" / "output"
        (output_dir / "MIB1.json").write_text('{"name": "MIB1"}')
        (output_dir / "MIB2.json").write_text('{"name": "MIB2"}')
        # Add auxiliary files that should be excluded
        (output_dir / "_oids.json").write_text('{"oids": {}}')
        (output_dir / "_tree.json").write_text('{"tree": {}}')

        # Check count
        devices = service.list_devices()
        assert devices[0].mib_count == 2

    def test_get_current_device_default(self, tmp_path):
        """Test getting current device defaults to 'default'."""
        service = DeviceService(storage_root=tmp_path)

        current = service.get_current_device()

        assert current == "default"

    def test_set_current_device(self, tmp_path):
        """Test setting current device."""
        service = DeviceService(storage_root=tmp_path)

        # Create a device
        service.create_device("test-device")

        # Set as current
        result = service.set_current_device("test-device")

        assert result is True
        assert service.get_current_device() == "test-device"

    def test_set_current_nonexistent_device(self, tmp_path):
        """Test setting non-existent device as current fails."""
        service = DeviceService(storage_root=tmp_path)

        result = service.set_current_device("nonexistent")

        assert result is False

    def test_device_exists(self, tmp_path):
        """Test device_exists method."""
        service = DeviceService(storage_root=tmp_path)

        assert not service.device_exists("test-device")

        service.create_device("test-device")

        assert service.device_exists("test-device")

    def test_get_device_paths(self, tmp_path):
        """Test getting device paths."""
        service = DeviceService(storage_root=tmp_path)

        service.create_device("test-device")

        paths = service.get_device_paths("test-device")

        assert "device_dir" in paths
        assert "compiled_mibs" in paths
        assert "output" in paths
        assert "metadata" in paths
        assert paths["device_dir"] == tmp_path / "devices" / "test-device"

    def test_get_device_paths_default(self, tmp_path):
        """Test getting device paths for current device."""
        service = DeviceService(storage_root=tmp_path)

        service.create_device("test-device")
        service.set_current_device("test-device")

        paths = service.get_device_paths()

        assert paths["device_dir"] == tmp_path / "devices" / "test-device"

    def test_update_device_metadata(self, tmp_path):
        """Test updating device metadata."""
        service = DeviceService(storage_root=tmp_path)

        service.create_device("test-device")

        # Update MIB count
        result = service.update_device_metadata("test-device", mib_count=5)

        assert result is True

        # Check that updated_at timestamp was changed
        # Note: mib_count is recalculated from filesystem by list_devices()
        # so we verify the registry was updated by checking updated_at changed
        registry = service._load_registry()
        device = [d for d in registry["devices"] if d["name"] == "test-device"][0]
        assert device["mib_count"] == 5
        assert "updated_at" in device

    def test_update_nonexistent_device_metadata(self, tmp_path):
        """Test updating metadata for non-existent device."""
        service = DeviceService(storage_root=tmp_path)

        result = service.update_device_metadata("nonexistent", mib_count=5)

        assert result is False

    def test_delete_current_device_switches_to_default(self, tmp_path):
        """Test that deleting current device switches to default."""
        service = DeviceService(storage_root=tmp_path)

        # Create and set current device
        service.create_device("test-device")
        service.set_current_device("test-device")

        # Delete it
        service.delete_device("test-device")

        # Should switch back to default
        assert service.get_current_device() == "default"

    def test_get_device_mib_service(self, tmp_path):
        """Test getting MibService for a device."""
        service = DeviceService(storage_root=tmp_path)

        service.create_device("test-device")

        mib_service = service.get_device_mib_service("test-device")

        assert mib_service is not None
        assert mib_service.device_type == "test-device"
        assert str(mib_service.output_dir) == str(tmp_path / "devices" / "test-device" / "output")
