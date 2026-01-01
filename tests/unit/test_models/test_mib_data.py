"""
测试 MibData 模型

测试 MIB 数据容器的功能和节点管理。
"""

from datetime import datetime

from src.mib_parser.models import MibData, MibNode


class TestMibDataCreation:
    """MibData 创建测试"""

    def test_create_empty_mib_data(self):
        """测试创建空的 MIB 数据容器"""
        mib_data = MibData(name="TEST-MIB")

        assert mib_data.name == "TEST-MIB"
        assert len(mib_data.nodes) == 0
        assert mib_data.imports == []
        assert mib_data.module_dependencies == []
        assert mib_data.description is None
        assert mib_data.last_updated is None

    def test_create_mib_data_with_module_name(self):
        """测试创建指定模块名的 MIB 数据"""
        # MibData 使用 name 属性作为模块名
        mib_data = MibData(name="TEST-MIB")

        assert mib_data.name == "TEST-MIB"
        # 名称既用于标识也用作模块名
        assert isinstance(mib_data.name, str)

    def test_create_mib_data_with_description(self):
        """测试创建带描述的 MIB 数据"""
        mib_data = MibData(name="TEST-MIB", description="Test MIB for unit testing")

        assert mib_data.description == "Test MIB for unit testing"

    def test_create_mib_data_with_imports(self):
        """测试创建带导入的 MIB 数据"""
        imports = ["SNMPv2-SMI", "SNMPv2-TC"]
        mib_data = MibData(name="TEST-MIB", imports=imports)

        assert mib_data.imports == imports
        assert len(mib_data.imports) == 2


class TestMibDataAddNode:
    """MibData 添加节点测试"""

    def test_add_single_node(self):
        """测试添加单个节点"""
        mib_data = MibData(name="TEST-MIB")
        node = MibNode(oid="1.3.6.1.2.1.1.1", name="sysDescr")

        mib_data.add_node(node)

        assert "sysDescr" in mib_data.nodes
        assert mib_data.nodes["sysDescr"] == node

    def test_add_multiple_nodes(self):
        """测试添加多个节点"""
        mib_data = MibData(name="TEST-MIB")

        nodes = [
            MibNode(oid="1.3.6.1.2.1.1.1", name="sysDescr"),
            MibNode(oid="1.3.6.1.2.1.1.2", name="sysObjectID"),
            MibNode(oid="1.3.6.1.2.1.1.3", name="sysUpTime"),
        ]

        for node in nodes:
            mib_data.add_node(node)

        assert len(mib_data.nodes) == 3
        assert "sysDescr" in mib_data.nodes
        assert "sysObjectID" in mib_data.nodes
        assert "sysUpTime" in mib_data.nodes

    def test_add_node_with_parent(self):
        """测试添加带父节点的子节点"""
        mib_data = MibData(name="TEST-MIB")

        # 先添加父节点
        parent = MibNode(oid="1.3.6.1.2.1.1", name="system")
        mib_data.add_node(parent)

        # 添加子节点
        child = MibNode(oid="1.3.6.1.2.1.1.1", name="sysDescr", parent_name="system")
        mib_data.add_node(child)

        # 验证父子关系
        assert "sysDescr" in parent.children

    def test_add_duplicate_node(self):
        """测试添加重复节点（替换）"""
        mib_data = MibData(name="TEST-MIB")

        node1 = MibNode(
            oid="1.3.6.1.2.1.1.1", name="sysDescr", description="First description"
        )
        node2 = MibNode(
            oid="1.3.6.1.2.1.1.1", name="sysDescr", description="Second description"
        )

        mib_data.add_node(node1)
        mib_data.add_node(node2)

        # 应该只有一个节点，被第二个替换
        assert len(mib_data.nodes) == 1
        assert mib_data.nodes["sysDescr"].description == "Second description"


class TestMibDataQuery:
    """MibData 查询测试"""

    def test_get_node_by_oid_found(self):
        """测试通过 OID 查找存在的节点"""
        mib_data = MibData(name="TEST-MIB")
        node = MibNode(oid="1.3.6.1.2.1.1.1", name="sysDescr")
        mib_data.add_node(node)

        found = mib_data.get_node_by_oid("1.3.6.1.2.1.1.1")

        assert found is not None
        assert found.name == "sysDescr"
        assert found.oid == "1.3.6.1.2.1.1.1"

    def test_get_node_by_oid_not_found(self):
        """测试通过 OID 查找不存在的节点"""
        mib_data = MibData(name="TEST-MIB")

        found = mib_data.get_node_by_oid("1.3.6.1.2.1.1.1")

        assert found is None

    def test_get_node_by_name_found(self):
        """测试通过名称查找存在的节点"""
        mib_data = MibData(name="TEST-MIB")
        node = MibNode(oid="1.3.6.1.2.1.1.1", name="sysDescr")
        mib_data.add_node(node)

        found = mib_data.get_node_by_name("sysDescr")

        assert found is not None
        assert found.name == "sysDescr"

    def test_get_node_by_name_not_found(self):
        """测试通过名称查找不存在的节点"""
        mib_data = MibData(name="TEST-MIB")

        found = mib_data.get_node_by_name("sysDescr")

        assert found is None

    def test_get_root_nodes(self):
        """测试获取根节点"""
        mib_data = MibData(name="TEST-MIB")

        # 添加根节点
        root1 = MibNode(oid="1.3.6.1.2.1.1", name="system")
        root2 = MibNode(oid="1.3.6.1.2.1.2", name="interfaces")
        mib_data.add_node(root1)
        mib_data.add_node(root2)

        # 添加子节点
        child = MibNode(oid="1.3.6.1.2.1.1.1", name="sysDescr", parent_name="system")
        mib_data.add_node(child)

        # 获取根节点
        roots = mib_data.get_root_nodes()

        assert len(roots) == 2
        root_names = {node.name for node in roots}
        assert root_names == {"system", "interfaces"}

    def test_get_root_nodes_empty(self):
        """测试空 MIB 数据获取根节点"""
        mib_data = MibData(name="TEST-MIB")

        roots = mib_data.get_root_nodes()

        assert roots == []

    def test_get_children(self):
        """测试获取子节点"""
        mib_data = MibData(name="TEST-MIB")

        # 添加父节点
        parent = MibNode(oid="1.3.6.1.2.1.1", name="system")
        mib_data.add_node(parent)

        # 添加子节点
        child1 = MibNode(oid="1.3.6.1.2.1.1.1", name="sysDescr", parent_name="system")
        child2 = MibNode(
            oid="1.3.6.1.2.1.1.2", name="sysObjectID", parent_name="system"
        )
        mib_data.add_node(child1)
        mib_data.add_node(child2)

        # 获取子节点
        children = mib_data.get_children("system")

        assert len(children) == 2
        child_names = {child.name for child in children}
        assert child_names == {"sysDescr", "sysObjectID"}

    def test_get_children_nonexistent_parent(self):
        """测试获取不存在的父节点的子节点"""
        mib_data = MibData(name="TEST-MIB")

        children = mib_data.get_children("nonexistent")

        assert children == []

    def test_get_descendants(self):
        """测试获取所有后代节点（递归）"""
        mib_data = MibData(name="TEST-MIB")

        # 构建三层树结构
        # root
        root = MibNode(oid="1.3.6.1.2.1.1", name="system")
        mib_data.add_node(root)

        # level 1
        child1 = MibNode(oid="1.3.6.1.2.1.1.1", name="sysDescr", parent_name="system")
        child2 = MibNode(
            oid="1.3.6.1.2.1.1.2", name="sysObjectID", parent_name="system"
        )
        mib_data.add_node(child1)
        mib_data.add_node(child2)

        # level 2 (child of child1)
        grandchild = MibNode(
            oid="1.3.6.1.2.1.1.1.1", name="sysDescrDetail", parent_name="sysDescr"
        )
        mib_data.add_node(grandchild)

        # 获取后代
        descendants = mib_data.get_descendants("system")

        descendant_names = {d.name for d in descendants}
        assert descendant_names == {"sysDescr", "sysObjectID", "sysDescrDetail"}

    def test_get_descendants_nonexistent_node(self):
        """测试获取不存在节点的后代"""
        mib_data = MibData(name="TEST-MIB")

        descendants = mib_data.get_descendants("nonexistent")

        assert descendants == []


class TestMibDataSerialization:
    """MibData 序列化测试"""

    def test_to_dict_basic(self):
        """测试序列化基本 MIB 数据到字典"""
        mib_data = MibData(name="TEST-MIB")

        data = mib_data.to_dict()

        assert data["name"] == "TEST-MIB"
        assert data["nodes"] == {}
        assert data["imports"] == []
        assert data["description"] is None

    def test_to_dict_with_nodes(self):
        """测试序列化包含节点的 MIB 数据"""
        mib_data = MibData(name="TEST-MIB")

        node = MibNode(
            oid="1.3.6.1.2.1.1.1", name="sysDescr", description="System description"
        )
        mib_data.add_node(node)

        data = mib_data.to_dict()

        assert data["name"] == "TEST-MIB"
        assert "sysDescr" in data["nodes"]
        assert data["nodes"]["sysDescr"]["name"] == "sysDescr"
        assert data["nodes"]["sysDescr"]["description"] == "System description"

    def test_to_dict_with_timestamp(self):
        """测试序列化包含时间戳的 MIB 数据"""
        timestamp = datetime(2026, 1, 1, 12, 0, 0)
        mib_data = MibData(name="TEST-MIB", last_updated=timestamp)

        data = mib_data.to_dict()

        assert data["last_updated"] == "2026-01-01T12:00:00"

    def test_from_dict_basic(self):
        """测试从字典反序列化基本 MIB 数据"""
        data = {
            "name": "TEST-MIB",
            "nodes": {},
            "imports": [],
            "module_dependencies": [],
            "description": None,
            "last_updated": None,
            "root_oids": [],
        }

        mib_data = MibData.from_dict(data)

        assert mib_data.name == "TEST-MIB"
        assert len(mib_data.nodes) == 0

    def test_from_dict_with_nodes(self):
        """测试从字典反序列化包含节点的 MIB 数据"""
        data = {
            "name": "TEST-MIB",
            "nodes": {
                "sysDescr": {
                    "name": "sysDescr",
                    "oid": "1.3.6.1.2.1.1.1",
                    "description": "System description",
                }
            },
            "imports": [],
            "module_dependencies": [],
            "description": None,
            "last_updated": None,
            "root_oids": [],
        }

        mib_data = MibData.from_dict(data)

        assert mib_data.name == "TEST-MIB"
        assert "sysDescr" in mib_data.nodes
        assert mib_data.nodes["sysDescr"].description == "System description"

    def test_from_dict_with_timestamp(self):
        """测试从字典反序列化包含时间戳的 MIB 数据"""
        data = {
            "name": "TEST-MIB",
            "nodes": {},
            "imports": [],
            "module_dependencies": [],
            "description": None,
            "last_updated": "2026-01-01T12:00:00",
            "root_oids": [],
        }

        mib_data = MibData.from_dict(data)

        assert mib_data.last_updated is not None
        assert mib_data.last_updated.year == 2026

    def test_serialization_roundtrip(self):
        """测试序列化和反序列化往返"""
        # 创建原始对象
        original = MibData(name="TEST-MIB", description="Test MIB")

        node = MibNode(
            oid="1.3.6.1.2.1.1.1", name="sysDescr", description="System description"
        )
        original.add_node(node)

        # 序列化
        data = original.to_dict()

        # 反序列化
        restored = MibData.from_dict(data)

        # 验证
        assert restored.name == original.name
        assert restored.description == original.description
        assert "sysDescr" in restored.nodes
        assert restored.nodes["sysDescr"].description == "System description"
