"""
测试 IndexField 模型

测试 MIB 表格索引字段的数据结构和序列化功能。
"""

from src.mib_parser.models import IndexField


class TestIndexField:
    """IndexField 模型测试类"""

    def test_create_index_field_basic(self):
        """测试创建基本的索引字段"""
        field = IndexField(name="ifIndex")

        assert field.name == "ifIndex"
        assert field.type is None
        assert field.syntax is None

    def test_create_index_field_with_type(self):
        """测试创建带有类型的索引字段"""
        field = IndexField(name="ifIndex", type="Integer32")

        assert field.name == "ifIndex"
        assert field.type == "Integer32"
        assert field.syntax is None

    def test_create_index_field_with_syntax(self):
        """测试创建带有语法的索引字段"""
        field = IndexField(
            name="ipAdEntAddr", type="IpAddress", syntax="IpAddress (SIZE (4))"
        )

        assert field.name == "ipAdEntAddr"
        assert field.type == "IpAddress"
        assert field.syntax == "IpAddress (SIZE (4))"

    def test_create_index_field_all_attributes(self):
        """测试创建包含所有属性的索引字段"""
        field = IndexField(
            name="ifIndex", type="Integer32", syntax="Integer32 (1..2147483647)"
        )

        assert field.name == "ifIndex"
        assert field.type == "Integer32"
        assert field.syntax == "Integer32 (1..2147483647)"

    def test_to_dict_basic(self):
        """测试序列化基本索引字段到字典"""
        field = IndexField(name="ifIndex")
        data = field.to_dict()

        assert data == {"name": "ifIndex", "type": None, "syntax": None}

    def test_to_dict_with_all_fields(self):
        """测试序列化完整索引字段到字典"""
        field = IndexField(
            name="ifIndex", type="Integer32", syntax="Integer32 (1..2147483647)"
        )
        data = field.to_dict()

        assert data == {
            "name": "ifIndex",
            "type": "Integer32",
            "syntax": "Integer32 (1..2147483647)",
        }

    def test_from_dict_basic(self):
        """测试从字典反序列化基本索引字段"""
        data = {"name": "ifIndex", "type": None, "syntax": None}
        field = IndexField.from_dict(data)

        assert field.name == "ifIndex"
        assert field.type is None
        assert field.syntax is None

    def test_from_dict_with_all_fields(self):
        """测试从字典反序列化完整索引字段"""
        data = {
            "name": "ifIndex",
            "type": "Integer32",
            "syntax": "Integer32 (1..2147483647)",
        }
        field = IndexField.from_dict(data)

        assert field.name == "ifIndex"
        assert field.type == "Integer32"
        assert field.syntax == "Integer32 (1..2147483647)"

    def test_serialization_roundtrip(self):
        """测试序列化和反序列化往返"""
        original = IndexField(
            name="ipAdEntAddr", type="IpAddress", syntax="IpAddress (SIZE (4))"
        )

        # 序列化
        data = original.to_dict()

        # 反序列化
        restored = IndexField.from_dict(data)

        # 验证
        assert restored.name == original.name
        assert restored.type == original.type
        assert restored.syntax == original.syntax

    def test_from_dict_with_missing_optional_fields(self):
        """测试从缺少可选字段的字典反序列化"""
        data = {"name": "ifIndex"}
        field = IndexField.from_dict(data)

        assert field.name == "ifIndex"
        assert field.type is None
        assert field.syntax is None

    def test_special_characters_in_name(self):
        """测试特殊字符在索引字段名称中"""
        # 虽然不常见，但测试边界情况
        field = IndexField(name="if-Index")
        assert field.name == "if-Index"

    def test_empty_string_fields(self):
        """测试空字符串字段"""
        field = IndexField(name="", type="", syntax="")

        assert field.name == ""
        assert field.type == ""
        assert field.syntax == ""

    def test_to_dict_empty_fields(self):
        """测试序列化空字段"""
        field = IndexField(name="test", type="", syntax=None)
        data = field.to_dict()

        assert data["name"] == "test"
        assert data["type"] == ""
        assert data["syntax"] is None
