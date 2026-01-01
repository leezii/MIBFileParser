"""Test AnnotationService class."""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

# Mock pysmi and mib_parser before importing AnnotationService
import sys
sys.modules['pysmi'] = MagicMock()
sys.modules['pysmi.compiler'] = MagicMock()
sys.modules['pysmi.parser'] = MagicMock()
sys.modules['pysmi.writer'] = MagicMock()
sys.modules['pysmi.codegen'] = MagicMock()
sys.modules['pysmi.reader'] = MagicMock()
sys.modules['pysmi.error'] = MagicMock()
sys.modules['pysmi.borrower'] = MagicMock()
sys.modules['mib_parser'] = MagicMock()
sys.modules['mib_parser.leaf_extractor'] = MagicMock()

from src.flask_app.services.annotation_service import AnnotationService


class TestAnnotationService:
    """Test AnnotationService class."""

    def test_service_initialization(self, tmp_path):
        """Test service initialization."""
        with patch('src.flask_app.services.annotation_service.LeafNodeExtractor'):
            service = AnnotationService(storage_path=str(tmp_path))

            assert service.storage_path == tmp_path
            assert service.annotations_path == tmp_path / "annotations"
            assert service.annotations_file == tmp_path / "annotations" / "leaf_annotations.json"

    def test_annotations_directory_created(self, tmp_path):
        """Test that annotations directory is created."""
        with patch('src.flask_app.services.annotation_service.LeafNodeExtractor'):
            service = AnnotationService(storage_path=str(tmp_path))

            assert service.annotations_path.exists()

    def test_get_all_annotations_empty(self, tmp_path):
        """Test getting annotations when none exist."""
        with patch('src.flask_app.services.annotation_service.LeafNodeExtractor'):
            service = AnnotationService(storage_path=str(tmp_path))

            annotations = service.get_all_annotations()

            assert annotations == {}

    def test_set_and_get_annotation(self, tmp_path):
        """Test setting and getting an annotation."""
        with patch('src.flask_app.services.annotation_service.LeafNodeExtractor') as mock_extractor:
            service = AnnotationService(storage_path=str(tmp_path))

            # Mock leaf extractor to return no nodes
            mock_extractor.return_value.get_leaf_nodes_for_annotation.return_value = []

            # Set annotation
            service.set_annotation("1.3.6.1.2.1.1.1", "System description")

            # Get annotation
            annotation = service.get_annotation_for_oid("1.3.6.1.2.1.1.1")

            assert annotation == "System description"

    def test_set_annotation_with_node_info(self, tmp_path):
        """Test setting annotation with node info."""
        with patch('src.flask_app.services.annotation_service.LeafNodeExtractor'):
            service = AnnotationService(storage_path=str(tmp_path))

            node_info = {
                "name": "sysDescr",
                "device_name": "default",
                "mib_name": "SNMPv2-MIB",
                "description": "System description"
            }

            service.set_annotation("1.3.6.1.2.1.1.1", "Test annotation", node_info)

            annotations = service.get_all_annotations()
            assert "1.3.6.1.2.1.1.1" in annotations
            assert annotations["1.3.6.1.2.1.1.1"]["node_name"] == "sysDescr"
            assert annotations["1.3.6.1.2.1.1.1"]["device_name"] == "default"

    def test_get_annotation_not_found(self, tmp_path):
        """Test getting annotation that doesn't exist."""
        with patch('src.flask_app.services.annotation_service.LeafNodeExtractor'):
            service = AnnotationService(storage_path=str(tmp_path))

            annotation = service.get_annotation_for_oid("1.2.3.4")

            assert annotation is None

    def test_delete_annotation(self, tmp_path):
        """Test deleting an annotation."""
        with patch('src.flask_app.services.annotation_service.LeafNodeExtractor') as mock_extractor:
            service = AnnotationService(storage_path=str(tmp_path))
            mock_extractor.return_value.get_leaf_nodes_for_annotation.return_value = []

            # Set annotation
            service.set_annotation("1.3.6.1.2.1.1.1", "Test")

            # Delete annotation
            result = service.delete_annotation("1.3.6.1.2.1.1.1")

            assert result is True
            assert service.get_annotation_for_oid("1.3.6.1.2.1.1.1") is None

    def test_delete_nonexistent_annotation(self, tmp_path):
        """Test deleting annotation that doesn't exist."""
        with patch('src.flask_app.services.annotation_service.LeafNodeExtractor'):
            service = AnnotationService(storage_path=str(tmp_path))

            result = service.delete_annotation("1.2.3.4")

            assert result is False

    def test_get_annotated_nodes(self, tmp_path):
        """Test getting all annotated nodes."""
        with patch('src.flask_app.services.annotation_service.LeafNodeExtractor') as mock_extractor:
            service = AnnotationService(storage_path=str(tmp_path))
            mock_extractor.return_value.get_leaf_nodes_for_annotation.return_value = []

            # Set multiple annotations
            service.set_annotation("1.3.6.1.2.1.1.1", "Desc1", {"name": "node1"})
            service.set_annotation("1.3.6.1.2.1.1.2", "Desc2", {"name": "node2"})

            annotated = service.get_annotated_nodes()

            assert len(annotated) == 2
            assert annotated[0]["oid"] in ["1.3.6.1.2.1.1.1", "1.3.6.1.2.1.1.2"]

    def test_save_annotations_adds_metadata(self, tmp_path):
        """Test that save_annotations adds metadata."""
        with patch('src.flask_app.services.annotation_service.LeafNodeExtractor'):
            service = AnnotationService(storage_path=str(tmp_path))

            annotations = {"1.3.6.1": {"annotation": "test"}}
            service.save_annotations(annotations)

            # Load and check metadata
            loaded = service.get_all_annotations()
            assert "_metadata" in loaded
            assert "last_updated" in loaded["_metadata"]
            assert "total_annotations" in loaded["_metadata"]

    def test_get_annotation_statistics(self, tmp_path):
        """Test getting annotation statistics."""
        with patch('src.flask_app.services.annotation_service.LeafNodeExtractor') as mock_extractor:
            service = AnnotationService(storage_path=str(tmp_path))

            # Mock leaf nodes
            mock_extractor.return_value.get_leaf_nodes_for_annotation.return_value = [
                {"oid": "1.3.6.1.2.1.1.1", "device_name": "device1", "name": "node1"},
                {"oid": "1.3.6.1.2.1.1.2", "device_name": "device1", "name": "node2"},
                {"oid": "1.3.6.1.2.1.1.3", "device_name": "device2", "name": "node3"}
            ]

            # Add annotations for 2 nodes
            service.set_annotation("1.3.6.1.2.1.1.1", "Annotation1", {"device_name": "device1"})
            service.set_annotation("1.3.6.1.2.1.1.2", "Annotation2", {"device_name": "device1"})

            stats = service.get_annotation_statistics()

            assert stats["total_nodes"] == 3
            assert stats["annotated_count"] == 2
            assert stats["unannotated_count"] == 1
            assert "completion_rate" in stats
            assert "device_stats" in stats

    def test_get_nodes_for_annotation_page(self, tmp_path):
        """Test getting nodes for annotation page."""
        with patch('src.flask_app.services.annotation_service.LeafNodeExtractor') as mock_extractor:
            service = AnnotationService(storage_path=str(tmp_path))

            # Mock leaf nodes
            mock_leaf_nodes = [
                {"oid": "1.3.6.1.2.1.1.1", "device_name": "device1", "name": "node1"},
                {"oid": "1.3.6.1.2.1.1.2", "device_name": "device1", "name": "node2"},
                {"oid": "1.3.6.1.2.1.1.3", "device_name": "device2", "name": "node3"}
            ]
            mock_extractor.return_value.get_leaf_nodes_for_annotation.return_value = mock_leaf_nodes
            mock_extractor.return_value.extract_all_leaf_nodes.return_value = None

            # Add an annotation
            service.set_annotation("1.3.6.1.2.1.1.1", "Test annotation", {"device_name": "device1"})

            result = service.get_nodes_for_annotation_page(page=1, per_page=2)

            assert "nodes" in result
            assert "pagination" in result
            assert len(result["nodes"]) <= 2
            assert result["pagination"]["current_page"] == 1
            assert result["pagination"]["per_page"] == 2

    def test_get_nodes_for_annotation_page_filters_by_device(self, tmp_path):
        """Test filtering nodes by device."""
        with patch('src.flask_app.services.annotation_service.LeafNodeExtractor') as mock_extractor:
            service = AnnotationService(storage_path=str(tmp_path))

            # Mock leaf nodes from different devices
            mock_leaf_nodes = [
                {"oid": "1.3.6.1.2.1.1.1", "device_name": "device1", "name": "node1"},
                {"oid": "1.3.6.1.2.1.1.2", "device_name": "device2", "name": "node2"}
            ]
            mock_extractor.return_value.get_leaf_nodes_for_annotation.return_value = mock_leaf_nodes
            mock_extractor.return_value.extract_all_leaf_nodes.return_value = None

            result = service.get_nodes_for_annotation_page(device_name="device1")

            assert len(result["nodes"]) == 1
            assert result["nodes"][0]["device_name"] == "device1"

    def test_annotation_trimmed_on_save(self, tmp_path):
        """Test that annotations are trimmed when saved."""
        with patch('src.flask_app.services.annotation_service.LeafNodeExtractor') as mock_extractor:
            service = AnnotationService(storage_path=str(tmp_path))
            mock_extractor.return_value.get_leaf_nodes_for_annotation.return_value = []

            # Set annotation with extra whitespace
            service.set_annotation("1.3.6.1.2.1.1.1", "  Test annotation  ")

            annotation = service.get_annotation_for_oid("1.3.6.1.2.1.1.1")

            assert annotation == "Test annotation"

    def test_get_annotated_nodes_excludes_metadata(self, tmp_path):
        """Test that _metadata is excluded from annotated nodes."""
        with patch('src.flask_app.services.annotation_service.LeafNodeExtractor'):
            service = AnnotationService(storage_path=str(tmp_path))

            service.set_annotation("1.3.6.1.2.1.1.1", "Test")

            annotated = service.get_annotated_nodes()

            # Should not include _metadata entry
            assert all(node.get("oid") != "_metadata" for node in annotated)

    def test_multiple_annotations_persisted(self, tmp_path):
        """Test that multiple annotations are persisted correctly."""
        with patch('src.flask_app.services.annotation_service.LeafNodeExtractor') as mock_extractor:
            service = AnnotationService(storage_path=str(tmp_path))
            mock_extractor.return_value.get_leaf_nodes_for_annotation.return_value = []

            # Add multiple annotations
            oids = ["1.3.6.1.2.1.1.1", "1.3.6.1.2.1.1.2", "1.3.6.1.2.1.1.3"]
            for oid in oids:
                service.set_annotation(oid, f"Annotation for {oid}")

            # Verify all are persisted
            annotations = service.get_all_annotations()
            for oid in oids:
                assert oid in annotations
                assert f"Annotation for {oid}" in annotations[oid]["annotation"]
