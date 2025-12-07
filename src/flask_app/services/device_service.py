import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class DeviceInfo:
    name: str
    display_name: str
    description: str
    created_at: str
    updated_at: str
    mib_count: int
    is_active: bool = True


class DeviceService:
    def __init__(self, storage_root: Path = None, registry_file: Path = None):
        if storage_root is None:
            storage_root = Path(__file__).parent.parent.parent.parent / "storage"
        if registry_file is None:
            registry_file = Path(__file__).parent.parent.parent.parent / "device_registry.json"

        self.storage_root = storage_root
        self.devices_dir = storage_root / "devices"
        self.uploads_dir = storage_root / "uploads"
        self.temp_dir = self.uploads_dir / "temp"
        self.registry_file = registry_file

        # Ensure directories exist
        self.devices_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Load or initialize registry
        self._ensure_registry_exists()

    def _ensure_registry_exists(self):
        """Create registry file if it doesn't exist"""
        if not self.registry_file.exists():
            self._save_registry({
                "devices": [],
                "current_device": "default",
                "version": "1.0"
            })

    def _load_registry(self) -> Dict[str, Any]:
        """Load device registry from file"""
        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "devices": [],
                "current_device": "default",
                "version": "1.0"
            }

    def _save_registry(self, registry: Dict[str, Any]):
        """Save device registry to file"""
        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)

    def list_devices(self) -> List[DeviceInfo]:
        """Get list of all devices"""
        registry = self._load_registry()
        devices = []

        for device_data in registry.get("devices", []):
            # Update mib_count from actual filesystem
            device_name = device_data["name"]
            device_output_dir = self.devices_dir / device_name / "output"

            if device_output_dir.exists():
                mib_count = len([f for f in device_output_dir.glob("*.json")
                               if not f.name.endswith("_oids.json") and not f.name.endswith("_tree.json")
                               and f.name not in ["all_mibs.json", "all_oids_mapping.json", "statistics_report.json"]])
            else:
                mib_count = 0

            device_data["mib_count"] = mib_count
            devices.append(DeviceInfo(**device_data))

        return devices

    def get_device_info(self, device_name: str) -> Optional[DeviceInfo]:
        """Get specific device info"""
        devices = self.list_devices()
        for device in devices:
            if device.name == device_name:
                return device
        return None

    def create_device(self, device_name: str, display_name: str = None, description: str = None) -> bool:
        """Create a new device"""
        # Use user-provided name as both directory name and display name
        # This allows for user-friendly naming with spaces and special characters
        if not device_name or not device_name.strip():
            raise ValueError("Invalid device name")

        # Use the original device name as provided by user
        device_name = device_name.strip()

        registry = self._load_registry()

        # Check if device already exists (both by name and display_name)
        existing_devices = [d["name"] for d in registry.get("devices", [])]
        existing_display_names = [d["display_name"] for d in registry.get("devices", [])]
        if device_name in existing_devices or device_name in existing_display_names:
            return False

        # Create device directories using user-friendly name
        device_dir = self.devices_dir / device_name
        device_dir.mkdir(parents=True, exist_ok=True)
        (device_dir / "compiled_mibs").mkdir(exist_ok=True)
        (device_dir / "mibs_for_pysmi").mkdir(exist_ok=True)
        (device_dir / "output").mkdir(exist_ok=True)

        # Add to registry
        if display_name is None:
            display_name = device_name

        new_device = {
            "name": device_name,
            "display_name": display_name,
            "description": description or f"MIB files for {display_name}",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "mib_count": 0,
            "is_active": True
        }

        registry["devices"].append(new_device)
        self._save_registry(registry)

        return True

    def delete_device(self, device_name: str) -> bool:
        """Delete a device and all its files"""
        if device_name == "default":
            raise ValueError("Cannot delete default device")

        registry = self._load_registry()
        devices = registry.get("devices", [])

        # Remove from registry
        devices = [d for d in devices if d["name"] != device_name]
        if len(devices) == len(registry.get("devices", [])):
            return False  # Device not found

        # Delete files
        device_dir = self.devices_dir / device_name
        if device_dir.exists():
            shutil.rmtree(device_dir)

        # Update registry
        registry["devices"] = devices

        # If this was the current device, switch to default
        if registry.get("current_device") == device_name:
            registry["current_device"] = "default"

        self._save_registry(registry)
        return True

    def get_current_device(self) -> str:
        """Get the currently selected device"""
        registry = self._load_registry()
        return registry.get("current_device", "default")

    def set_current_device(self, device_name: str) -> bool:
        """Set the current device"""
        registry = self._load_registry()
        devices = [d["name"] for d in registry.get("devices", [])]

        if device_name not in devices:
            return False

        registry["current_device"] = device_name
        self._save_registry(registry)
        return True

    def get_device_paths(self, device_name: str = None) -> Dict[str, Path]:
        """Get paths for a specific device"""
        if device_name is None:
            device_name = self.get_current_device()

        device_dir = self.devices_dir / device_name
        return {
            "device_dir": device_dir,
            "compiled_mibs": device_dir / "compiled_mibs",
            "output": device_dir / "output",
            "metadata": device_dir / "metadata.json"
        }

    def update_device_metadata(self, device_name: str, mib_count: int = None) -> bool:
        """Update device metadata after file operations"""
        registry = self._load_registry()
        devices = registry.get("devices", [])

        for device in devices:
            if device["name"] == device_name:
                if mib_count is not None:
                    device["mib_count"] = mib_count
                device["updated_at"] = datetime.utcnow().isoformat() + "Z"
                self._save_registry(registry)
                return True

        return False

    def get_device_mib_service(self, device_name: str = None):
        """Get a MibService instance for a specific device"""
        from .mib_service import MibService

        if device_name is None:
            device_name = self.get_current_device()

        paths = self.get_device_paths(device_name)
        return MibService(
            output_dir=str(paths["output"]),
            compiled_mibs_dir=str(paths["compiled_mibs"]),
            device_type=device_name
        )

    def device_exists(self, device_name: str) -> bool:
        """Check if a device exists"""
        registry = self._load_registry()
        devices = [d["name"] for d in registry.get("devices", [])]
        return device_name in devices