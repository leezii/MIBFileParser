"""Test MibFile class."""

import pytest
from src.mib_parser.dependency_resolver import MibFile


class TestMibFile:
    """Test MibFile dataclass."""

    def test_create_mib_file(self):
        """Test creating a MibFile instance."""
        mib_file = MibFile(
            name="TEST-MIB",
            file_path="/path/to/TEST-MIB.mib",
            imports={"RFC1213-MIB", "SNMPv2-TC"},
            exports={"sysDescr", "sysObjectID"},
        )

        assert mib_file.name == "TEST-MIB"
        assert mib_file.file_path == "/path/to/TEST-MIB.mib"
        assert "RFC1213-MIB" in mib_file.imports
        assert "sysDescr" in mib_file.exports

    def test_create_mib_file_with_defaults(self):
        """Test creating MibFile with default level."""
        mib_file = MibFile(
            name="TEST-MIB",
            file_path="/path/to/TEST-MIB.mib",
            imports=set(),
            exports=set(),
        )

        assert mib_file.level == 0  # Default level

    def test_mib_file_immutable_attributes(self):
        """Test that MibFile attributes can be modified."""
        mib_file = MibFile(
            name="TEST-MIB",
            file_path="/path/to/TEST-MIB.mib",
            imports=set(),
            exports=set(),
        )

        # Modify attributes
        mib_file.level = 1
        assert mib_file.level == 1

        mib_file.imports.add("NEW-MIB")
        assert "NEW-MIB" in mib_file.imports
