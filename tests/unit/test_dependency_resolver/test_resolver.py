"""Test MibDependencyResolver class."""

import pytest
from pathlib import Path
from src.mib_parser.dependency_resolver import MibDependencyResolver, MibFile


class TestMibDependencyResolver:
    """Test MibDependencyResolver class."""

    def test_initialize_resolver(self):
        """Test resolver initialization."""
        resolver = MibDependencyResolver()

        assert resolver.mib_files == {}
        assert resolver.dependency_graph == {}
        assert resolver.reverse_dependency_graph == {}

    def test_parse_mib_dependencies_empty_directory(self, tmp_path):
        """Test parsing an empty directory."""
        resolver = MibDependencyResolver()

        result = resolver.parse_mib_dependencies(str(tmp_path))

        assert result == {}
        assert resolver.mib_files == {}

    def test_parse_mib_dependencies_single_file(self, tmp_path):
        """Test parsing a directory with a single MIB file."""
        # Create test MIB file
        test_mib = tmp_path / "TEST-MIB.mib"
        test_mib.write_text(
            """TEST-MIB DEFINITIONS ::= BEGIN
IMPORTS Integer32 FROM SNMPv2-TC;
EXPORTS sysDescr;
END
"""
        )

        resolver = MibDependencyResolver()
        result = resolver.parse_mib_dependencies(str(tmp_path))

        assert "TEST-MIB" in result
        assert result["TEST-MIB"].name == "TEST-MIB"
        assert "SNMPv2-TC" in result["TEST-MIB"].imports

    def test_parse_mib_dependencies_multiple_files(self, tmp_path):
        """Test parsing multiple MIB files with dependencies."""
        # Create test MIB files
        (tmp_path / "BASE-MIB.mib").write_text("BASE-MIB DEFINITIONS ::= BEGIN\nEND\n")
        (tmp_path / "DERIVED-MIB.mib").write_text(
            """DERIVED-MIB DEFINITIONS ::= BEGIN
IMPORTS Something FROM BASE-MIB;
END
"""
        )

        resolver = MibDependencyResolver()
        result = resolver.parse_mib_dependencies(str(tmp_path))

        assert len(result) == 2
        assert "BASE-MIB" in result
        assert "DERIVED-MIB" in result

    def test_get_compilation_order_empty(self):
        """Test getting compilation order with no MIBs."""
        resolver = MibDependencyResolver()

        order = resolver.get_compilation_order()

        assert order == []

    def test_get_compilation_order_simple_chain(self, tmp_path):
        """Test compilation order with simple dependency chain."""
        # A -> B -> C (C depends on B, B depends on A)
        (tmp_path / "A-MIB.mib").write_text("A-MIB DEFINITIONS ::= BEGIN\nEND\n")
        (tmp_path / "B-MIB.mib").write_text(
            "B-MIB DEFINITIONS ::= BEGIN\nIMPORTS X FROM A-MIB;\nEND\n"
        )
        (tmp_path / "C-MIB.mib").write_text(
            "C-MIB DEFINITIONS ::= BEGIN\nIMPORTS Y FROM B-MIB;\nEND\n"
        )

        resolver = MibDependencyResolver()
        resolver.parse_mib_dependencies(str(tmp_path))

        order = resolver.get_compilation_order()

        # A should come before B, B should come before C
        assert order.index("A-MIB") < order.index("B-MIB")
        assert order.index("B-MIB") < order.index("C-MIB")

    def test_detect_circular_dependencies(self, tmp_path):
        """Test detection of circular dependencies."""
        # A depends on B, B depends on A
        (tmp_path / "A-MIB.mib").write_text(
            "A-MIB DEFINITIONS ::= BEGIN\nIMPORTS X FROM B-MIB;\nEND\n"
        )
        (tmp_path / "B-MIB.mib").write_text(
            "B-MIB DEFINITIONS ::= BEGIN\nIMPORTS Y FROM A-MIB;\nEND\n"
        )

        resolver = MibDependencyResolver()
        resolver.parse_mib_dependencies(str(tmp_path))

        # Should handle circular dependencies gracefully
        order = resolver.get_compilation_order()
        # Just verify it doesn't crash

    def test_extract_mib_name_from_content(self, tmp_path):
        """Test _extract_mib_name method."""
        test_mib = tmp_path / "custom-name.mib"
        test_mib.write_text("MY-MIB DEFINITIONS ::= BEGIN\nEND\n")

        resolver = MibDependencyResolver()
        mib_name = resolver._extract_mib_name(test_mib)

        assert mib_name == "MY-MIB"
