"""
pytest 配置和共享 fixtures

此文件包含 pytest 的全局配置和所有测试共享的 fixture。
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture
def temp_directory() -> Generator[Path, None, None]:
    """
    提供临时目录的 fixture

    自动创建和清理临时目录，确保测试隔离性。

    Yields:
        Path: 临时目录路径对象

    Example:
        def test_something(temp_directory):
            file_path = temp_directory / "test.txt"
            file_path.write_text("content")
    """
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        # 清理临时目录
        import shutil

        if temp_dir.exists():
            shutil.rmtree(temp_dir)


@pytest.fixture
def sample_mib_node():
    """
    提供示例 MIB 节点的 fixture

    返回一个简单的 MIB 节点对象用于测试。

    Returns:
        MibNode: 示例 MIB 节点

    Example:
        def test_node_property(sample_mib_node):
            assert sample_mib_node.oid == "1.3.6.1.2.1.1.1"
    """
    from src.mib_parser.models import MibNode

    return MibNode(
        oid="1.3.6.1.2.1.1.1",
        name="sysDescr",
        module="SNMPv2-MIB",
        description="System description",
    )


@pytest.fixture
def sample_index_field():
    """
    提供示例索引字段的 fixture

    返回一个简单的索引字段对象用于测试。

    Returns:
        IndexField: 示例索引字段

    Example:
        def test_index_field(sample_index_field):
            assert sample_index_field.name == "ifIndex"
    """
    from src.mib_parser.models import IndexField

    return IndexField(
        name="ifIndex",
        type="Integer32",
        description="Interface index",
    )


@pytest.fixture
def sample_mib_data():
    """
    提供示例 MIB 数据的 fixture

    返回一个包含示例节点的 MIB 数据容器。

    Returns:
        MibData: 包含示例节点的 MIB 数据

    Example:
        def test_mib_data(sample_mib_data):
            nodes = sample_mib_data.get_root_nodes()
            assert len(nodes) > 0
    """
    from src.mib_parser.models import MibData, MibNode

    mib_data = MibData(name="TEST-MIB")

    # 添加一些示例节点
    nodes = [
        MibNode(
            oid="1.3.6.1.2.1.1.1",
            name="sysDescr",
            module="TEST-MIB",
            description="System description",
        ),
        MibNode(
            oid="1.3.6.1.2.1.1.2",
            name="sysObjectID",
            module="TEST-MIB",
            description="System object ID",
        ),
        MibNode(
            oid="1.3.6.1.2.1.1.3",
            name="sysUpTime",
            module="TEST-MIB",
            description="System uptime",
        ),
    ]

    for node in nodes:
        mib_data.add_node(node)

    return mib_data


@pytest.fixture
def fixtures_dir() -> Path:
    """
    返回测试夹具目录的路径

    Returns:
        Path: tests/fixtures 目录路径

    Example:
        def test_load_mib(fixtures_dir):
            mib_path = fixtures_dir / "mibs" / "simple.mib"
    """
    return Path(__file__).parent / "fixtures"


# Flask API 测试 fixtures
@pytest.fixture
def app(tmp_path):
    """Create Flask app for testing."""
    from unittest.mock import MagicMock, patch

    # Mock pysmi modules and Flask extensions before importing Flask app
    mock_pysmi = MagicMock()
    sys.modules['pysmi'] = mock_pysmi
    sys.modules['pysmi.compiler'] = MagicMock()
    sys.modules['pysmi.parser'] = MagicMock()
    sys.modules['pysmi.writer'] = MagicMock()
    sys.modules['pysmi.codegen'] = MagicMock()
    sys.modules['pysmi.reader'] = MagicMock()
    sys.modules['pysmi.error'] = MagicMock()
    sys.modules['pysmi.borrower'] = MagicMock()
    sys.modules['mib_parser'] = MagicMock()
    sys.modules['mib_parser.leaf_extractor'] = MagicMock()
    sys.modules['flask_cors'] = MagicMock()
    sys.modules['flask_cors.CORS'] = MagicMock()

    from src.flask_app.app import create_app

    app = create_app('testing')

    # Override configuration for testing
    app.config['TESTING'] = True
    app.config['OUTPUT_DIR'] = str(tmp_path / "output")
    app.config['MIB_DIR'] = str(tmp_path / "mibs")
    app.config['SECRET_KEY'] = 'test-secret-key'

    # Create necessary directories
    (tmp_path / "output").mkdir(exist_ok=True)
    (tmp_path / "mibs").mkdir(exist_ok=True)

    return app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create Flask CLI test runner."""
    return app.test_cli_runner()
