#!/usr/bin/env python3
"""
基本使用示例 - 演示 MIB Parser 的基本功能
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from mib_parser import MibParser, JsonSerializer, MibTree


def main():
    """主函数演示基本用法"""
    print("MIB Parser 基本使用示例")
    print("=" * 50)

    # 创建输出目录
    output_dir = Path("examples/output")
    output_dir.mkdir(exist_ok=True)

    # 1. 创建解析器
    parser = MibParser(debug_mode=False)
    print("✓ MIB 解析器已创建")

    # 2. 创建一些示例 MIB 数据用于演示
    print("\n创建示例 MIB 数据...")

    # 由于可能没有实际的 MIB 文件，我们创建示例数据
    from mib_parser.models import MibData, MibNode
    from datetime import datetime

    # 创建 SNMPv2-MIB 示例数据
    mib_data = MibData(
        name="SNMPv2-MIB",
        description="SNMPv2 MIB module",
        imports=["SNMPv2-SMI", "SNMPv2-TC"],
        module_dependencies=["IF-MIB"],
        last_updated=datetime.now()
    )

    # 添加一些示例节点
    root_node = MibNode(
        name="snmp",
        oid="1.3.6.1.6.3",
        description="SNMP group",
        syntax="OBJECT IDENTIFIER",
        access="read-only",
        status="current"
    )

    system_node = MibNode(
        name="system",
        oid="1.3.6.1.2.1.1",
        description="System group",
        syntax="OBJECT IDENTIFIER",
        access="read-only",
        status="current",
        parent_name="iso"
    )

    sys_descr_node = MibNode(
        name="sysDescr",
        oid="1.3.6.1.2.1.1.1",
        description="A textual description of the entity",
        syntax="DisplayString (SIZE (0..255))",
        access="read-only",
        status="current",
        parent_name="system",
        text_convention="DisplayString",
        max_access="read-only"
    )

    sys_up_time_node = MibNode(
        name="sysUpTime",
        oid="1.3.6.1.2.1.1.3",
        description="The time (in hundredths of a second) since the network management portion of the system was last re-initialized.",
        syntax="TimeTicks",
        access="read-only",
        status="current",
        parent_name="system",
        units="hundredths of a second",
        max_access="read-only"
    )

    # 添加节点到 MIB 数据
    mib_data.add_node(root_node)
    mib_data.add_node(system_node)
    mib_data.add_node(sys_descr_node)
    mib_data.add_node(sys_up_time_node)

    print(f"✓ 创建了 {len(mib_data.nodes)} 个示例节点")

    # 3. 使用 JSON 序列化器
    print("\n序列化数据...")
    serializer = JsonSerializer(indent=2)

    # 保存为 JSON
    output_file = output_dir / "snmpv2_mib.json"
    serializer.serialize(mib_data, str(output_file))
    print(f"✓ MIB 数据已保存到: {output_file}")

    # 保存 OID 映射
    oid_mapping_file = output_dir / "oid_mapping.json"
    serializer.export_oid_mapping(mib_data, str(oid_mapping_file))
    print(f"✓ OID 映射已保存到: {oid_mapping_file}")

    # 保存树形结构
    tree_file = output_dir / "tree_structure.json"
    serializer.serialize_tree(mib_data, str(tree_file))
    print(f"✓ 树形结构已保存到: {tree_file}")

    # 4. 使用 MibTree 进行树形操作
    print("\n树形操作演示...")
    tree = MibTree(mib_data)

    # 查找节点
    sys_descr = tree.find_node_by_name("sysDescr")
    if sys_descr:
        print(f"✓ 找到节点: {sys_descr.name} ({sys_descr.oid})")
        print(f"  描述: {sys_descr.description}")

    # 按OID查找
    node_by_oid = tree.find_node_by_oid("1.3.6.1.2.1.1.3")
    if node_by_oid:
        print(f"✓ 按OID找到节点: {node_by_oid.name}")

    # 模式匹配搜索
    matching_nodes = tree.find_nodes_by_pattern("sys", search_names=True)
    print(f"✓ 找到 {len(matching_nodes)} 个包含 'sys' 的节点")

    # 获取统计信息
    stats = tree.get_node_statistics()
    print(f"✓ 树统计信息:")
    print(f"  总节点数: {stats['total_nodes']}")
    print(f"  根节点数: {stats['root_nodes']}")
    print(f"  叶节点数: {stats['leaf_nodes']}")

    # 遍历演示
    print(f"\n广度优先遍历:")
    for i, node in enumerate(tree.traverse_breadth_first()):
        print(f"  {i+1}. {node.name} ({node.oid})")

    print(f"\n深度优先遍历:")
    for i, node in enumerate(tree.traverse_depth_first()):
        print(f"  {i+1}. {node.name} ({node.oid})")

    # 5. 反序列化演示
    print(f"\n反序列化演示...")
    restored_mib = serializer.deserialize(str(output_file))
    print(f"✓ 成功反序列化 MIB: {restored_mib.name}")
    print(f"✓ 节点数量: {len(restored_mib.nodes)}")

    # 验证数据一致性
    if restored_mib.name == mib_data.name and len(restored_mib.nodes) == len(mib_data.nodes):
        print("✓ 数据一致性验证通过")
    else:
        print("✗ 数据一致性验证失败")

    print(f"\n演示完成！请查看 {output_dir} 目录中的输出文件。")


if __name__ == "__main__":
    main()