"""Test MibService advanced methods."""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock pysmi modules before importing anything
sys.modules['pysmi'] = MagicMock()
sys.modules['pysmi.compiler'] = MagicMock()
sys.modules['pysmi.parser'] = MagicMock()
sys.modules['pysmi.writer'] = MagicMock()
sys.modules['pysmi.codegen'] = MagicMock()
sys.modules['pysmi.reader'] = MagicMock()
sys.modules['pysmi.error'] = MagicMock()
sys.modules['pysmi.borrower'] = MagicMock()

# Mock mib_parser modules
sys.modules['mib_parser'] = MagicMock()
sys.modules['mib_parser.parser'] = MagicMock()
sys.modules['mib_parser.serializer'] = MagicMock()
sys.modules['mib_parser.leaf_extractor'] = MagicMock()

# Add to src namespace
import src
src.mib_parser = sys.modules['mib_parser']

from src.flask_app.services.mib_service import MibService


class TestMibServiceAdvanced:
    """Test MibService advanced methods."""

    def test_get_all_mibs_tree_data(self, tmp_path):
        """Test getting tree data for all MIBs combined."""
        # Create test MIB files
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create mock MIB data files
        mib1_data = {
            "name": "MIB1",
            "nodes": {
                "node1": {"oid": "1.3.6.1.2.1.1.1", "name": "node1"}
            }
        }

        mib2_data = {
            "name": "MIB2",
            "nodes": {
                "node2": {"oid": "1.3.6.1.2.1.1.2", "name": "node2"}
            }
        }

        with open(output_dir / "MIB1.json", 'w') as f:
            json.dump(mib1_data, f)
        with open(output_dir / "MIB2.json", 'w') as f:
            json.dump(mib2_data, f)

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=output_dir)

            with patch("src.flask_app.services.tree_service.TreeService") as mock_tree_svc:
                mock_tree_service = MagicMock()
                mock_tree_service.build_tree_structure.return_value = {
                    "name": "All MIBs",
                    "children": []
                }
                mock_tree_svc.return_value = mock_tree_service

                result = service.get_all_mibs_tree_data()

                assert result is not None
                assert result["name"] == "All MIBs"
                mock_tree_service.build_tree_structure.assert_called_once()

    def test_get_all_mibs_tree_data_empty(self, tmp_path):
        """Test getting all MIBs tree data when no MIBs exist."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=output_dir)

            with patch("src.flask_app.services.tree_service.TreeService") as mock_tree_svc:
                mock_tree_service = MagicMock()
                mock_tree_service.build_tree_structure.return_value = {
                    "name": "All MIBs",
                    "children": []
                }
                mock_tree_svc.return_value = mock_tree_service

                result = service.get_all_mibs_tree_data()

                assert result is not None

    def test_fix_mib_syntax_with_common_issues(self, tmp_path):
        """Test fixing common MIB syntax issues."""
        mib_file = tmp_path / "TEST.mib"
        # Write MIB with common syntax issues
        mib_file.write_text("""
TEST-MIB DEFINITIONS ::= BEGIN
IMPORTS ObjectName FROM SNMPv2-TC;
testObjectName ::= ObjectName
END
""")

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path / "output")

            result = service._fix_mib_syntax(mib_file)

            # Should apply fixes and return True
            assert result is True

            # Verify backup was created
            backup_file = tmp_path / "TEST.mib.backup"
            assert backup_file.exists()

    def test_fix_mib_syntax_no_issues(self, tmp_path):
        """Test fix_mib_syntax when no issues exist."""
        mib_file = tmp_path / "TEST.mib"
        # Note: The fix_mib_syntax method always normalizes END statement
        # So it will return True even for clean files
        mib_file.write_text("TEST-MIB DEFINITIONS ::= BEGIN\nEND\n")

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path / "output")

            result = service._fix_mib_syntax(mib_file)

            # The method normalizes END statement, so it returns True
            # and creates a backup file
            assert result is True
            # Verify backup was created due to END normalization
            backup_file = tmp_path / "TEST.mib.backup"
            assert backup_file.exists()

    def test_fix_mib_syntax_handles_errors(self, tmp_path):
        """Test error handling in fix_mib_syntax."""
        mib_file = tmp_path / "TEST.mib"
        mib_file.write_text("TEST-MIB DEFINITIONS ::= BEGIN\nEND\n")

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=tmp_path / "output")

            # Mock to raise an exception during file operations
            with patch("builtins.open", side_effect=IOError("Permission denied")):
                result = service._fix_mib_syntax(mib_file)

                # Should return False on error
                assert result is False

    def test_replace_device_mibs_success(self, tmp_path):
        """Test replacing device MIBs successfully."""
        # Create existing MIB files
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        compiled_dir = tmp_path / "compiled"
        compiled_dir.mkdir()

        # Create some existing files
        (output_dir / "old_mib.json").write_text("{}")
        (compiled_dir / "old.mib").write_text("OLD-MIB DEFINITIONS ::= BEGIN\nEND\n")

        # Create new MIB files
        new_mib = tmp_path / "NEW.mib"
        new_mib.write_text("NEW-MIB DEFINITIONS ::= BEGIN\nEND\n")

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(
                output_dir=output_dir,
                compiled_mibs_dir=compiled_dir
            )

            # Mock add_uploaded_files to return success
            with patch.object(service, 'add_uploaded_files') as mock_add:
                mock_add.return_value = {
                    'total_added': 1,
                    'success': [{'filename': 'NEW.mib', 'mib_name': 'NEW-MIB'}],
                    'errors': []
                }

                result = service.replace_device_mibs([new_mib])

                assert result['success'] is True
                assert result['success_count'] == 1
                assert result['error_count'] == 0

    def test_replace_device_mibs_clear_failure(self, tmp_path):
        """Test replace_device_mibs when clearing fails."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        new_mib = tmp_path / "NEW.mib"
        new_mib.write_text("NEW-MIB DEFINITIONS ::= BEGIN\nEND\n")

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=output_dir)

            # Mock glob to raise an exception
            with patch.object(Path, 'glob', side_effect=IOError("Permission denied")):
                result = service.replace_device_mibs([new_mib])

                assert result['success'] is False
                assert 'error' in result

    def test_replace_device_mibs_empty_list(self, tmp_path):
        """Test replacing device MIBs with empty file list."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=output_dir)

            with patch.object(service, 'add_uploaded_files') as mock_add:
                mock_add.return_value = {
                    'total_added': 0,
                    'success': [],
                    'errors': []
                }

                result = service.replace_device_mibs([])

                assert result['success'] is True
                assert result['success_count'] == 0

    def test_replace_device_mibs_with_parse_errors(self, tmp_path):
        """Test replacing device MIBs when some files fail to parse."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        new_mib1 = tmp_path / "GOOD.mib"
        new_mib2 = tmp_path / "BAD.mib"
        new_mib1.write_text("GOOD-MIB DEFINITIONS ::= BEGIN\nEND\n")
        new_mib2.write_text("INVALID CONTENT")

        with patch("src.flask_app.services.mib_service.Path.cwd", return_value=tmp_path):
            service = MibService(output_dir=output_dir)

            # Mock add_uploaded_files to return mixed results
            with patch.object(service, 'add_uploaded_files') as mock_add:
                mock_add.return_value = {
                    'total_added': 1,
                    'success': [{'filename': 'GOOD.mib', 'mib_name': 'GOOD-MIB'}],
                    'errors': [
                        {
                            'filename': 'BAD.mib',
                            'error': 'Syntax error'
                        }
                    ]
                }

                result = service.replace_device_mibs([new_mib1, new_mib2])

                assert result['success'] is True
                assert result['success_count'] == 1
                assert result['error_count'] == 1
                assert len(result['errors']) == 1
