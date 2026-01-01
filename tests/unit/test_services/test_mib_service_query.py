"""Test MibService query and search methods."""

import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime
from src.flask_app.services.mib_service import MibService


class TestMibServiceQuery:
    """Test MibService query and search methods."""

    def test_list_mibs_empty(self, tmp_path):
        """Test list_mibs with no MIB files."""
        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            result = service.list_mibs()

            assert result == []

    def test_list_mibs_single_file(self, tmp_path):
        """Test list_mibs with one MIB file."""
        mib_data = {
            "name": "TEST-MIB",
            "module": "TEST",
            "description": "Test MIB",
            "nodes": {
                "sysDescr": {"oid": "1.3.6.1.2.1.1.1", "name": "sysDescr"}
            },
            "imports": ["SNMPv2-TC"]
        }
        mib_file = tmp_path / "TEST-MIB.json"
        mib_file.write_text(json.dumps(mib_data))

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            result = service.list_mibs()

            assert len(result) == 1
            assert result[0]["name"] == "TEST-MIB"
            assert result[0]["description"] == "Test MIB"
            assert result[0]["nodes_count"] == 1
            assert result[0]["imports_count"] == 1

    def test_list_mibs_multiple_files(self, tmp_path):
        """Test list_mibs with multiple MIB files."""
        mib1_data = {"name": "MIB1", "module": "M1", "nodes": {}}
        mib2_data = {"name": "MIB2", "module": "M2", "nodes": {}}

        (tmp_path / "MIB1.json").write_text(json.dumps(mib1_data))
        (tmp_path / "MIB2.json").write_text(json.dumps(mib2_data))

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            result = service.list_mibs()

            assert len(result) == 2
            mib_names = {mib["name"] for mib in result}
            assert "MIB1" in mib_names
            assert "MIB2" in mib_names

    def test_list_mibs_sorted(self, tmp_path):
        """Test that list_mibs returns sorted results."""
        # Create files with specific names to test sorting
        for name in ["Z-MIB", "A-MIB", "M-MIB"]:
            mib_data = {"name": name, "module": name, "nodes": {}}
            (tmp_path / f"{name}.json").write_text(json.dumps(mib_data))

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            result = service.list_mibs()

            # Should be sorted alphabetically
            assert result[0]["name"] == "A-MIB"
            assert result[1]["name"] == "M-MIB"
            assert result[2]["name"] == "Z-MIB"

    def test_list_mibs_skips_auxiliary_files(self, tmp_path):
        """Test that auxiliary files are skipped."""
        mib_data = {"name": "VALID-MIB", "module": "VALID", "nodes": {}}
        (tmp_path / "VALID-MIB.json").write_text(json.dumps(mib_data))
        (tmp_path / "_oids.json").write_text('{"oids": {}}')
        (tmp_path / "_tree.json").write_text('{"tree": {}}')
        (tmp_path / "all_mibs.json").write_text('{"all": {}}')
        (tmp_path / "statistics.json").write_text('{"stats": {}}')

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            result = service.list_mibs()

            # Should only include VALID-MIB, not auxiliary files
            assert len(result) == 1
            assert result[0]["name"] == "VALID-MIB"

    def test_search_nodes_by_name(self, tmp_path):
        """Test search_nodes finding nodes by name."""
        mib_data = {
            "name": "TEST-MIB",
            "nodes": {
                "sysDescr": {
                    "oid": "1.3.6.1.2.1.1.1",
                    "name": "sysDescr",
                    "description": "System description"
                },
                "sysContact": {
                    "oid": "1.3.6.1.2.1.1.4",
                    "name": "sysContact",
                    "description": "System contact"
                }
            }
        }
        (tmp_path / "TEST-MIB.json").write_text(json.dumps(mib_data))

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            result = service.search_nodes("sysDescr")

            assert len(result) == 1
            assert result[0]["node_name"] == "sysDescr"
            assert result[0]["mib_name"] == "TEST-MIB"

    def test_search_nodes_by_oid(self, tmp_path):
        """Test search_nodes finding nodes by OID."""
        mib_data = {
            "name": "TEST-MIB",
            "nodes": {
                "sysDescr": {
                    "oid": "1.3.6.1.2.1.1.1",
                    "name": "sysDescr"
                }
            }
        }
        (tmp_path / "TEST-MIB.json").write_text(json.dumps(mib_data))

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            result = service.search_nodes("1.3.6.1.2.1.1.1")

            assert len(result) == 1
            assert result[0]["node_name"] == "sysDescr"

    def test_search_nodes_by_description(self, tmp_path):
        """Test search_nodes finding nodes by description."""
        mib_data = {
            "name": "TEST-MIB",
            "nodes": {
                "sysDescr": {
                    "oid": "1.3.6.1.2.1.1.1",
                    "name": "sysDescr",
                    "description": "System description text"
                }
            }
        }
        (tmp_path / "TEST-MIB.json").write_text(json.dumps(mib_data))

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            result = service.search_nodes("description")

            assert len(result) == 1

    def test_search_nodes_case_insensitive(self, tmp_path):
        """Test search_nodes is case insensitive."""
        mib_data = {
            "name": "TEST-MIB",
            "nodes": {
                "sysDescr": {
                    "oid": "1.3.6.1.2.1.1.1",
                    "name": "sysDescr"
                }
            }
        }
        (tmp_path / "TEST-MIB.json").write_text(json.dumps(mib_data))

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            # Search with different cases
            result1 = service.search_nodes("sysdescr")
            result2 = service.search_nodes("SYSDESCR")
            result3 = service.search_nodes("SySdEsCr")

            assert len(result1) == 1
            assert len(result2) == 1
            assert len(result3) == 1

    def test_search_nodes_empty_query(self, tmp_path):
        """Test search_nodes with empty query."""
        mib_data = {
            "name": "TEST-MIB",
            "nodes": {
                "sysDescr": {
                    "oid": "1.3.6.1.2.1.1.1",
                    "name": "sysDescr"
                }
            }
        }
        (tmp_path / "TEST-MIB.json").write_text(json.dumps(mib_data))

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            result = service.search_nodes("")

            # Empty query should match everything
            assert len(result) == 1

    def test_get_node_by_oid_found(self, tmp_path):
        """Test get_node_by_oid when node exists."""
        mib_data = {
            "name": "TEST-MIB",
            "nodes": {
                "sysDescr": {
                    "oid": "1.3.6.1.2.1.1.1",
                    "name": "sysDescr"
                }
            }
        }
        (tmp_path / "TEST-MIB.json").write_text(json.dumps(mib_data))

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            result = service.get_node_by_oid("1.3.6.1.2.1.1.1")

            assert result is not None
            assert result["node_name"] == "sysDescr"
            assert result["mib_name"] == "TEST-MIB"
            assert "node_data" in result

    def test_get_node_by_oid_not_found(self, tmp_path):
        """Test get_node_by_oid when node doesn't exist."""
        mib_data = {
            "name": "TEST-MIB",
            "nodes": {}
        }
        (tmp_path / "TEST-MIB.json").write_text(json.dumps(mib_data))

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            result = service.get_node_by_oid("1.2.3.4.5")

            assert result is None

    def test_get_statistics(self, tmp_path):
        """Test get_statistics method."""
        mib_data = {
            "name": "TEST-MIB",
            "nodes": {"node1": {"oid": "1.1"}},
            "imports": ["MIB1", "MIB2"]
        }
        (tmp_path / "TEST-MIB.json").write_text(json.dumps(mib_data))

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            stats = service.get_statistics()

            assert stats["total_mibs"] == 1
            assert stats["total_nodes"] == 1
            assert stats["mibs_with_data"] == 1
            assert "largest_mib" in stats
            assert "newest_mib" in stats
            assert "oldest_mib" in stats

    def test_get_statistics_empty(self, tmp_path):
        """Test get_statistics with no MIBs."""
        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path)

            stats = service.get_statistics()

            assert stats["total_mibs"] == 0
            assert stats["total_nodes"] == 0
            assert stats["mibs_with_data"] == 0
