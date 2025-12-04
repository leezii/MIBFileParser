#!/usr/bin/env python3
"""
MIB 查询工具 - 演示如何使用解析出的 MIB 数据
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from mib_parser import JsonSerializer, MibTree
from mib_parser.models import MibData


class MIBQueryTool:
    """MIB 查询工具"""

    def __init__(self, output_dir="output"):
        self.output_dir = Path(output_dir)
        self.mib_data_list = []
        self.load_all_mibs()

    def load_all_mibs(self):
        """加载所有解析的 MIB 数据"""
        serializer = JsonSerializer()

        # 尝试加载 all_mibs.json 文件
        all_mibs_file = self.output_dir / "all_mibs.json"
        if all_mibs_file.exists():
            try:
                self.mib_data_list = serializer.deserialize(str(all_mibs_file))
                if isinstance(self.mib_data_list, list):
                    print(f"✓ 加载了 {len(self.mib_data_list)} 个 MIB 文件")
                else:
                    self.mib_data_list = [self.mib_data_list]
                    print(f"✓ 加载了 1 个 MIB 文件")
            except Exception as e:
                print(f"✗ 加载 MIB 数据失败: {e}")
                return

        # 如果没有汇总文件，尝试加载单个文件
        else:
            json_files = list(self.output_dir.glob("*.json"))
            if not json_files:
                print("✗ 没有找到 MIB 数据文件")
                return

            for json_file in json_files:
                try:
                    mib_data = serializer.deserialize(str(json_file))
                    self.mib_data_list.append(mib_data)
                except Exception as e:
                    print(f"✗ 加载 {json_file} 失败: {e}")

        print(f"总共加载了 {len(self.mib_data_list)} 个 MIB 文件")

    def search_by_name(self, pattern, limit=10):
        """根据名称模式搜索节点"""
        results = []
        pattern_lower = pattern.lower()

        for mib_data in self.mib_data_list:
            for node_name, node in mib_data.nodes.items():
                if pattern_lower in node_name.lower():
                    results.append({
                        'mib': mib_data.name,
                        'name': node_name,
                        'oid': node.oid,
                        'description': node.description or "无描述",
                        'syntax': node.syntax or "未知",
                        'access': node.access or "未知"
                    })

        print(f"\n搜索包含 '{pattern}' 的节点 (显示前 {min(limit, len(results))} 个结果):")
        print("-" * 80)

        for i, result in enumerate(results[:limit]):
            print(f"{i+1:2d}. {result['name']}")
            print(f"    OID: {result['oid']}")
            print(f"    MIB: {result['mib']}")
            print(f"    描述: {result['description'][:60]}...")
            print(f"    语法: {result['syntax']}")
            print(f"    访问: {result['access']}")
            print()

        if len(results) > limit:
            print(f"... 还有 {len(results) - limit} 个结果未显示")

        return results

    def search_by_oid(self, oid_pattern):
        """根据 OID 模式搜索节点"""
        results = []

        for mib_data in self.mib_data_list:
            for node_name, node in mib_data.nodes.items():
                if oid_pattern in node.oid:
                    results.append({
                        'mib': mib_data.name,
                        'name': node_name,
                        'oid': node.oid,
                        'description': node.description or "无描述",
                        'syntax': node.syntax or "未知"
                    })

        print(f"\n搜索包含 OID '{oid_pattern}' 的节点:")
        print("-" * 80)

        for i, result in enumerate(results):
            print(f"{i+1:2d}. {result['name']} ({result['oid']})")
            print(f"    MIB: {result['mib']}")
            print(f"    描述: {result['description'][:60]}...")
            print(f"    语法: {result['syntax']}")
            print()

        return results

    def show_mib_summary(self):
        """显示 MIB 文件汇总信息"""
        print("\nMIB 文件汇总:")
        print("=" * 80)

        total_nodes = 0
        for mib_data in self.mib_data_list:
            node_count = len(mib_data.nodes)
            total_nodes += node_count
            print(f"MIB: {mib_data.name}")
            print(f"  节点数: {node_count}")
            if mib_data.description:
                print(f"  描述: {mib_data.description[:60]}...")
            print(f"  最后更新: {mib_data.last_updated}")
            print()

        print(f"总计: {len(self.mib_data_list)} 个 MIB 文件, {total_nodes} 个节点")

    def show_mib_tree_structure(self, mib_name, max_depth=3):
        """显示指定 MIB 的树形结构"""
        # 找到指定的 MIB
        target_mib = None
        for mib_data in self.mib_data_list:
            if mib_data.name.lower() == mib_name.lower():
                target_mib = mib_data
                break

        if not target_mib:
            print(f"未找到 MIB: {mib_name}")
            return

        print(f"\n{mib_name} 的树形结构 (最大深度 {max_depth}):")
        print("=" * 80)

        tree = MibTree(target_mib)
        root_nodes = target_mib.get_root_nodes()

        if not root_nodes:
            print("未找到根节点")
            return

        def print_node(node, level=0):
            if level > max_depth:
                return

            indent = "  " * level
            print(f"{indent}{node.name} ({node.oid})")
            if node.description and len(node.description) < 60:
                print(f"{indent}  # {node.description}")
            elif node.description:
                print(f"{indent}  # {node.description[:57]}...")

            # 递归打印子节点
            children = tree.get_children(node.name)
            for child in sorted(children, key=lambda x: x.oid):
                print_node(child, level + 1)

        for root_node in root_nodes:
            print_node(root_node)

    def export_search_results(self, results, filename):
        """导出搜索结果"""
        output_file = self.output_dir / filename
        serializer = JsonSerializer()
        serializer.serialize(results, str(output_file))
        print(f"搜索结果已导出到: {output_file}")


def main():
    """主函数 - 演示查询工具的使用"""
    print("MIB 数据查询工具")
    print("=" * 50)

    # 初始化查询工具
    query_tool = MIBQueryTool()

    if not query_tool.mib_data_list:
        print("没有可用的 MIB 数据")
        return

    # 显示汇总信息
    query_tool.show_mib_summary()

    # 演示各种查询功能
    print("\n" + "=" * 50)
    print("查询演示")
    print("=" * 50)

    # 1. 按名称搜索
    print("\n1. 按名称搜索包含 'port' 的节点:")
    port_results = query_tool.search_by_name("port", limit=5)

    # 2. 按 OID 搜索
    print("\n2. 搜索 OID 包含 '1.2.3' 的节点:")
    oid_results = query_tool.search_by_oid("1.2.3")

    # 3. 按名称搜索 'ne' 相关节点
    print("\n3. 搜索网络设备相关节点:")
    ne_results = query_tool.search_by_name("ne", limit=3)

    # 4. 显示一个 MIB 的树形结构
    print("\n4. 显示 OPTIX-OID-MIB 的树形结构:")
    query_tool.show_mib_tree_structure("OPTIX-OID-MIB", max_depth=3)

    # 导出搜索结果
    print("\n" + "=" * 50)
    print("导出结果")
    print("=" * 50)

    query_tool.export_search_results(port_results, "port_nodes_search_results.json")
    query_tool.export_search_results(ne_results, "ne_nodes_search_results.json")

    print("\n查询演示完成!")
    print("您可以在 output 目录中查看导出的搜索结果文件。")


if __name__ == "__main__":
    main()