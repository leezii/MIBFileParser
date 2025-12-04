#!/usr/bin/env python3
"""
OID 查询工具示例 - 演示如何使用 MIB Parser 进行高效的 OID 查询和搜索
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from mib_parser import MibParser, JsonSerializer, MibTree
from mib_parser.models import MibData, MibNode
from datetime import datetime


class OIDLookupTool:
    """OID 查询工具类"""

    def __init__(self):
        self.mib_data_list = []
        self.trees = {}
        self.oid_cache = {}

    def load_mib_data(self, mib_files):
        """加载 MIB 文件"""
        parser = MibParser()

        for mib_file in mib_files:
            try:
                print(f"正在加载: {mib_file}")
                # 由于可能没有实际的 MIB 文件，这里创建示例数据
                mib_data = self._create_sample_mib(Path(mib_file).stem)
                self.mib_data_list.append(mib_data)
                self.trees[mib_data.name] = MibTree(mib_data)
                print(f"✓ 成功加载: {mib_data.name}")

                # 构建缓存
                for node in mib_data.nodes.values():
                    self.oid_cache[node.oid] = node

            except Exception as e:
                print(f"✗ 加载失败: {mib_file} - {e}")

    def _create_sample_mib(self, name):
        """创建示例 MIB 数据"""
        mib_data = MibData(
            name=name,
            description=f"Sample {name} module",
            imports=["SNMPv2-SMI"],
            module_dependencies=[],
            last_updated=datetime.now()
        )

        # 根据不同的 MIB 名称创建不同的示例数据
        if name == "SNMPv2-MIB":
            self._create_snmpv2_nodes(mib_data)
        elif name == "IF-MIB":
            self._create_if_mib_nodes(mib_data)
        elif name == "TCP-MIB":
            self._create_tcp_mib_nodes(mib_data)
        else:
            self._create_generic_nodes(mib_data, name)

        return mib_data

    def _create_snmpv2_nodes(self, mib_data):
        """创建 SNMPv2-MIB 的示例节点"""
        nodes = [
            MibNode("system", "1.3.6.1.2.1.1", "System group", "OBJECT IDENTIFIER", "read-only", "current"),
            MibNode("sysDescr", "1.3.6.1.2.1.1.1", "System description", "DisplayString", "read-only", "current", "system", text_convention="DisplayString"),
            MibNode("sysObjectID", "1.3.6.1.2.1.1.2", "System object ID", "OBJECT IDENTIFIER", "read-only", "current", "system"),
            MibNode("sysUpTime", "1.3.6.1.2.1.1.3", "System uptime", "TimeTicks", "read-only", "current", "system", units="hundredths of a second"),
            MibNode("sysContact", "1.3.6.1.2.1.1.4", "System contact", "DisplayString", "read-write", "current", "system", text_convention="DisplayString"),
            MibNode("sysName", "1.3.6.1.2.1.1.5", "System name", "DisplayString", "read-write", "current", "system", text_convention="DisplayString"),
            MibNode("sysLocation", "1.3.6.1.2.1.1.6", "System location", "DisplayString", "read-write", "current", "system", text_convention="DisplayString"),
            MibNode("sysServices", "1.3.6.1.2.1.1.7", "System services", "INTEGER", "read-only", "current", "system"),
        ]
        for node in nodes:
            mib_data.add_node(node)

    def _create_if_mib_nodes(self, mib_data):
        """创建 IF-MIB 的示例节点"""
        nodes = [
            MibNode("interfaces", "1.3.6.1.2.1.2", "Interfaces group", "OBJECT IDENTIFIER", "read-only", "current"),
            MibNode("ifNumber", "1.3.6.1.2.1.2.1", "Number of interfaces", "Integer32", "read-only", "current", "interfaces"),
            MibNode("ifTable", "1.3.6.1.2.1.2.2", "Interface table", "SEQUENCE OF IfEntry", "read-only", "current", "interfaces"),
            MibNode("ifEntry", "1.3.6.1.2.1.2.2.1", "Interface entry", "IfEntry", "read-only", "current", "ifTable"),
            MibNode("ifIndex", "1.3.6.1.2.1.2.2.1.1", "Interface index", "InterfaceIndex", "read-only", "current", "ifEntry"),
            MibNode("ifDescr", "1.3.6.1.2.1.2.2.1.2", "Interface description", "DisplayString", "read-only", "current", "ifEntry", text_convention="DisplayString"),
            MibNode("ifType", "1.3.6.1.2.1.2.2.1.3", "Interface type", "IANAifType", "read-only", "current", "ifEntry"),
            MibNode("ifMtu", "1.3.6.1.2.1.2.2.1.4", "Interface MTU", "Integer32", "read-only", "current", "ifEntry"),
            MibNode("ifSpeed", "1.3.6.1.2.1.2.2.1.5", "Interface speed", "Gauge32", "read-only", "current", "ifEntry", units="bits per second"),
            MibNode("ifOperStatus", "1.3.6.1.2.1.2.2.1.8", "Interface operational status", "INTEGER", "read-only", "current", "ifEntry"),
        ]
        for node in nodes:
            mib_data.add_node(node)

    def _create_tcp_mib_nodes(self, mib_data):
        """创建 TCP-MIB 的示例节点"""
        nodes = [
            MibNode("tcp", "1.3.6.1.2.1.6", "TCP group", "OBJECT IDENTIFIER", "read-only", "current"),
            MibNode("tcpRtoAlgorithm", "1.3.6.1.2.1.6.1", "TCP RTO algorithm", "INTEGER", "read-only", "current", "tcp"),
            MibNode("tcpRtoMin", "1.3.6.1.2.1.6.2", "TCP minimum RTO", "Integer32", "read-only", "current", "tcp", units="milliseconds"),
            MibNode("tcpRtoMax", "1.3.6.1.2.1.6.3", "TCP maximum RTO", "Integer32", "read-only", "current", "tcp", units="milliseconds"),
            MibNode("tcpMaxConn", "1.3.6.1.2.1.6.4", "TCP maximum connections", "Integer32", "read-only", "current", "tcp"),
            MibNode("tcpActiveOpens", "1.3.6.1.2.1.6.5", "TCP active opens", "Counter32", "read-only", "current", "tcp"),
            MibNode("tcpPassiveOpens", "1.3.6.1.2.1.6.6", "TCP passive opens", "Counter32", "read-only", "current", "tcp"),
            MibNode("tcpAttemptFails", "1.3.6.1.2.1.6.7", "TCP attempt failures", "Counter32", "read-only", "current", "tcp"),
            MibNode("tcpEstabResets", "1.3.6.1.2.1.6.8", "TCP established resets", "Counter32", "read-only", "current", "tcp"),
            MibNode("tcpCurrEstab", "1.3.6.1.2.1.6.9", "TCP current established", "Gauge32", "read-only", "current", "tcp"),
        ]
        for node in nodes:
            mib_data.add_node(node)

    def _create_generic_nodes(self, mib_data, name):
        """创建通用的示例节点"""
        root_node = MibNode(f"{name.lower()}Root", f"1.3.6.1.4.1.9999.1", f"{name} root node", "OBJECT IDENTIFIER", "read-only", "current")
        mib_data.add_node(root_node)

        for i in range(1, 4):
            node = MibNode(
                f"{name}Node{i}",
                f"1.3.6.1.4.1.9999.1.{i}",
                f"{name} node {i}",
                "INTEGER",
                "read-only",
                "current",
                root_node.name
            )
            mib_data.add_node(node)

    def lookup_by_oid(self, oid):
        """根据 OID 查找节点"""
        # 先从缓存查找
        if oid in self.oid_cache:
            node = self.oid_cache[oid]
            return f"找到: {node.name} ({node.oid}) - {node.description or '无描述'}"

        # 遍历所有 MIB 查找
        for mib_name, tree in self.trees.items():
            node = tree.find_node_by_oid(oid)
            if node:
                return f"在 {mib_name} 中找到: {node.name} - {node.description or '无描述'}"

        return f"未找到 OID: {oid}"

    def search_by_name(self, pattern):
        """根据名称模式搜索节点"""
        results = []
        for mib_data in self.mib_data_list:
            tree = MibTree(mib_data)
            matching_nodes = tree.find_nodes_by_pattern(pattern, search_names=True, search_descriptions=True)

            for node in matching_nodes:
                results.append({
                    'mib': mib_data.name,
                    'name': node.name,
                    'oid': node.oid,
                    'description': node.description or '无描述',
                    'syntax': node.syntax or '未知'
                })

        return results

    def search_by_description(self, pattern):
        """根据描述模式搜索节点"""
        results = []
        for mib_data in self.mib_data_list:
            tree = MibTree(mib_data)
            matching_nodes = tree.find_nodes_by_pattern(pattern, search_names=False, search_descriptions=True)

            for node in matching_nodes:
                results.append({
                    'mib': mib_data.name,
                    'name': node.name,
                    'oid': node.oid,
                    'description': node.description or '无描述',
                    'syntax': node.syntax or '未知'
                })

        return results

    def get_mib_tree(self, mib_name):
        """获取指定 MIB 的树形结构"""
        if mib_name in self.trees:
            tree = self.trees[mib_name]
            return tree.get_tree_levels()
        return None

    def export_search_results(self, results, filename):
        """导出搜索结果"""
        output_path = Path("examples/output") / filename
        output_path.parent.mkdir(exist_ok=True)

        serializer = JsonSerializer()
        serializer.serialize(results, str(output_path))
        return output_path


def main():
    """主函数演示 OID 查询工具"""
    print("OID 查询工具示例")
    print("=" * 50)

    # 创建 OID 查询工具
    lookup_tool = OIDLookupTool()

    # 示例 MIB 文件列表（这里使用示例数据）
    mib_files = ["SNMPv2-MIB", "IF-MIB", "TCP-MIB", "EXAMPLE-MIB"]
    lookup_tool.load_mib_data(mib_files)

    print(f"\n已加载 {len(lookup_tool.mib_data_list)} 个 MIB 模块")
    print(f"总节点数: {sum(len(mib.nodes) for mib in lookup_tool.mib_data_list)}")

    # OID 查询演示
    print("\n" + "=" * 50)
    print("OID 查询演示")
    print("=" * 50)

    test_oids = [
        "1.3.6.1.2.1.1.1",  # sysDescr
        "1.3.6.1.2.1.2.2.1.8",  # ifOperStatus
        "1.3.6.1.2.1.6.9",  # tcpCurrEstab
        "1.3.6.1.4.1.9999.1.2",  # 示例节点
        "1.3.6.1.2.1.99.99"  # 不存在的 OID
    ]

    for oid in test_oids:
        result = lookup_tool.lookup_by_oid(oid)
        print(f"{oid}: {result}")

    # 名称搜索演示
    print("\n" + "=" * 50)
    print("名称搜索演示")
    print("=" * 50)

    search_patterns = ["sys", "if", "tcp", "node"]
    for pattern in search_patterns:
        print(f"\n搜索包含 '{pattern}' 的节点:")
        results = lookup_tool.search_by_name(pattern)
        for result in results[:5]:  # 只显示前5个结果
            print(f"  {result['name']} ({result['oid']}) in {result['mib']}")
        if len(results) > 5:
            print(f"  ... 还有 {len(results) - 5} 个结果")

    # 描述搜索演示
    print("\n" + "=" * 50)
    print("描述搜索演示")
    print("=" * 50)

    desc_patterns = ["system", "interface", "connection", "node"]
    for pattern in desc_patterns:
        print(f"\n在描述中搜索 '{pattern}':")
        results = lookup_tool.search_by_description(pattern)
        for result in results[:3]:  # 只显示前3个结果
            print(f"  {result['name']}: {result['description'][:50]}...")
        if len(results) > 3:
            print(f"  ... 还有 {len(results) - 3} 个结果")

    # 树形结构演示
    print("\n" + "=" * 50)
    print("树形结构演示")
    print("=" * 50)

    for mib_data in lookup_tool.mib_data_list[:2]:  # 只显示前两个MIB的树形结构
        tree = MibTree(mib_data)
        levels = tree.get_tree_levels()
        print(f"\n{mib_data.name} 的树形结构:")

        for level in sorted(levels.keys()):
            nodes = levels[level]
            print(f"  Level {level}: {[node.name for node in nodes]}")

    # 导出搜索结果
    print("\n" + "=" * 50)
    print("导出搜索结果")
    print("=" * 50)

    # 导出所有系统相关节点
    sys_results = lookup_tool.search_by_name("sys")
    if sys_results:
        output_file = lookup_tool.export_search_results(sys_results, "system_nodes.json")
        print(f"系统相关节点已导出到: {output_file}")

    # 导出 OID 映射
    all_mibs = lookup_tool.mib_data_list
    if all_mibs:
        serializer = JsonSerializer()
        mapping_file = Path("examples/output") / "complete_oid_mapping.json"
        serializer.export_oid_mapping(all_mibs, str(mapping_file))
        print(f"完整 OID 映射已导出到: {mapping_file}")

    print("\n演示完成！")


if __name__ == "__main__":
    main()