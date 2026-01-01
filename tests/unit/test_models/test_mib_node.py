"""
测试 MibNode 模型

测试 MIB 树节点的数据结构和序列化功能。
"""

from src.mib_parser.models import IndexField, MibNode


class TestMibNodeCreation:
    """MibNode 创建测试"""

    def test_create_basic_node(self):
        """测试创建基本的 MIB 节点"""
        node = MibNode(oid="1.3.6.1.2.1.1.1", name="sysDescr")

        assert node.name == "sysDescr"
        assert node.oid == "1.3.6.1.2.1.1.1"
        assert node.description is None
        assert node.syntax is None

    def test_create_node_with_all_optional_fields(self):
        """测试创建包含所有可选字段的节点"""
        node = MibNode(
            oid="1.3.6.1.2.1.1.1",
            name="sysDescr",
            description="System description",
            syntax="DisplayString",
            access="read-only",
            status="current",
            parent_name="system",
            children=["child1", "child2"],
            module="SNMPv2-MIB",
            text_convention="DisplayString",
            units="seconds",
            max_access="read-only",
            reference="RFC1213",
            defval="0",
            hint="255a",
            node_class="scalar",
            is_entry=False,
            is_table=False,
        )

        assert node.name == "sysDescr"
        assert node.oid == "1.3.6.1.2.1.1.1"
        assert node.description == "System description"
        assert node.syntax == "DisplayString"
        assert node.access == "read-only"
        assert node.status == "current"
        assert node.parent_name == "system"
        assert len(node.children) == 2
        assert node.module == "SNMPv2-MIB"

    def test_create_node_with_index_fields(self):
        """测试创建包含索引字段的节点（表格条目）"""
        index_fields = [
            IndexField(name="ifIndex", type="Integer32"),
            IndexField(name="ifDescr", type="DisplayString"),
        ]

        node = MibNode(
            oid="1.3.6.1.2.1.2.2.1",
            name="ifEntry",
            is_entry=True,
            table_name="ifTable",
            index_fields=index_fields,
        )

        assert node.name == "ifEntry"
        assert node.is_entry is True
        assert node.table_name == "ifTable"
        assert len(node.index_fields) == 2
        assert node.index_fields[0].name == "ifIndex"

    def test_create_node_with_empty_children_list(self):
        """测试创建空子节点列表的节点"""
        node = MibNode(oid="1.3.6.1.2.1.1.1", name="sysDescr", children=[])

        assert node.children == []
        assert isinstance(node.children, list)


class TestMibNodeSerialization:
    """MibNode 序列化测试"""

    def test_to_dict_basic(self):
        """测试序列化基本节点到字典"""
        node = MibNode(oid="1.3.6.1.2.1.1.1", name="sysDescr")

        data = node.to_dict()

        assert data["name"] == "sysDescr"
        assert data["oid"] == "1.3.6.1.2.1.1.1"
        assert data["description"] is None
        assert data["syntax"] is None

    def test_to_dict_with_all_fields(self):
        """测试序列化完整节点到字典"""
        node = MibNode(
            oid="1.3.6.1.2.1.1.1",
            name="sysDescr",
            description="System description",
            syntax="DisplayString",
            module="SNMPv2-MIB",
            children=["child1"],
        )

        data = node.to_dict()

        assert data["name"] == "sysDescr"
        assert data["oid"] == "1.3.6.1.2.1.1.1"
        assert data["description"] == "System description"
        assert data["syntax"] == "DisplayString"
        assert data["module"] == "SNMPv2-MIB"
        assert data["children"] == ["child1"]

    def test_to_dict_with_index_fields(self):
        """测试序列化包含索引字段的节点"""
        index_fields = [IndexField(name="ifIndex", type="Integer32")]

        node = MibNode(
            oid="1.3.6.1.2.1.2.2.1",
            name="ifEntry",
            is_entry=True,
            index_fields=index_fields,
        )

        data = node.to_dict()

        assert data["is_entry"] is True
        assert len(data["index_fields"]) == 1
        assert data["index_fields"][0]["name"] == "ifIndex"

    def test_from_dict_basic(self):
        """测试从字典反序列化基本节点"""
        data = {"name": "sysDescr", "oid": "1.3.6.1.2.1.1.1"}

        node = MibNode.from_dict(data)

        assert node.name == "sysDescr"
        assert node.oid == "1.3.6.1.2.1.1.1"
        assert node.description is None

    def test_from_dict_with_all_fields(self):
        """测试从字典反序列化完整节点"""
        data = {
            "name": "sysDescr",
            "oid": "1.3.6.1.2.1.1.1",
            "description": "System description",
            "syntax": "DisplayString",
            "access": "read-only",
            "status": "current",
            "module": "SNMPv2-MIB",
            "children": ["child1", "child2"],
        }

        node = MibNode.from_dict(data)

        assert node.name == "sysDescr"
        assert node.oid == "1.3.6.1.2.1.1.1"
        assert node.description == "System description"
        assert node.syntax == "DisplayString"
        assert node.access == "read-only"
        assert node.status == "current"
        assert node.module == "SNMPv2-MIB"
        assert len(node.children) == 2

    def test_from_dict_with_index_fields(self):
        """测试从字典反序列化包含索引字段的节点"""
        data = {
            "name": "ifEntry",
            "oid": "1.3.6.1.2.1.2.2.1",
            "is_entry": True,
            "table_name": "ifTable",
            "index_fields": [
                {"name": "ifIndex", "type": "Integer32", "syntax": None},
                {"name": "ifDescr", "type": "DisplayString", "syntax": None},
            ],
        }

        node = MibNode.from_dict(data)

        assert node.is_entry is True
        assert node.table_name == "ifTable"
        assert len(node.index_fields) == 2
        assert node.index_fields[0].name == "ifIndex"
        assert node.index_fields[1].name == "ifDescr"

    def test_serialization_roundtrip(self):
        """测试序列化和反序列化往返"""
        original = MibNode(
            oid="1.3.6.1.2.1.1.1",
            name="sysDescr",
            description="System description",
            syntax="DisplayString",
            module="SNMPv2-MIB",
        )

        # 序列化
        data = original.to_dict()

        # 反序列化
        restored = MibNode.from_dict(data)

        # 验证所有关键字段
        assert restored.name == original.name
        assert restored.oid == original.oid
        assert restored.description == original.description
        assert restored.syntax == original.syntax
        assert restored.module == original.module


class TestMibNodeSpecialCases:
    """MibNode 特殊情况测试"""

    def test_long_oid(self):
        """测试长 OID 处理"""
        long_oid = "1.3.6.1.2.1.1.1.1.1.1.1.1.1.1.1.1"
        node = MibNode(oid=long_oid, name="test")

        assert node.oid == long_oid
        assert len(node.oid.split(".")) == 17

    def test_oid_with_leading_zeros(self):
        """测试包含前导零的 OID"""
        node = MibNode(oid="1.03.6.01", name="test")

        # OID 应该保持原样
        assert node.oid == "1.03.6.01"

    def test_empty_string_optional_fields(self):
        """测试空字符串可选字段"""
        node = MibNode(oid="1.3.6.1.2.1.1.1", name="test", description="", syntax="")

        assert node.description == ""
        assert node.syntax == ""

    def test_special_characters_in_description(self):
        """测试描述中的特殊字符"""
        special_desc = "System description: \"test\" with 'quotes' and\nnewlines"
        node = MibNode(oid="1.3.6.1.2.1.1.1", name="test", description=special_desc)

        assert node.description == special_desc

    def test_node_with_table_and_entry_flags(self):
        """测试表格和条目标记"""
        table_node = MibNode(
            oid="1.3.6.1.2.1.2.2", name="ifTable", is_table=True, entry_name="ifEntry"
        )

        entry_node = MibNode(
            oid="1.3.6.1.2.1.2.2.1", name="ifEntry", is_entry=True, table_name="ifTable"
        )

        assert table_node.is_table is True
        assert table_node.entry_name == "ifEntry"
        assert entry_node.is_entry is True
        assert entry_node.table_name == "ifTable"

    def test_from_dict_with_missing_optional_fields(self):
        """测试从缺少可选字段的字典反序列化"""
        data = {"name": "sysDescr", "oid": "1.3.6.1.2.1.1.1"}

        node = MibNode.from_dict(data)

        # 验证可选字段都是 None
        assert node.description is None
        assert node.syntax is None
        assert node.access is None
        assert node.status is None
        assert node.parent_name is None
        assert node.module is None
