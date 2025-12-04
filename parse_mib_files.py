#!/usr/bin/env python3
"""
MIB 文件解析脚本
解析 MIB 文件夹中的所有 MIB 文件并将结果输出到 output 文件夹
"""

import sys
from pathlib import Path
import traceback

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from mib_parser import MibParser, JsonSerializer, MibTree


def parse_mib_directory(mib_dir_path, output_dir_path):
    """解析 MIB 目录中的所有文件"""
    print(f"开始解析 MIB 文件目录: {mib_dir_path}")
    print("=" * 60)

    mib_dir = Path(mib_dir_path)
    output_dir = Path(output_dir_path)
    output_dir.mkdir(exist_ok=True)

    # 创建解析器
    parser = MibParser(debug_mode=False)  # 关闭调试模式
    serializer = JsonSerializer(indent=2)

    # 查找所有 MIB 文件 (包括 .mib 和 .MIB 扩展名)
    mib_files = list(mib_dir.glob("*.mib")) + list(mib_dir.glob("*.MIB"))
    print(f"找到 {len(mib_files)} 个 MIB 文件")

    # 使用依赖解析器确定正确的解析顺序
    print("\n正在分析 MIB 文件依赖关系...")
    try:
        dependency_resolver = parser.dependency_resolver
        if dependency_resolver:
            dependency_resolver.parse_mib_dependencies(str(mib_dir))

            # 打印依赖信息
            dependency_resolver.print_dependency_info()

            # 获取编译顺序
            compilation_order = dependency_resolver.get_compilation_order()

            # 按照依赖顺序重新排列文件
            ordered_mib_files = []
            mib_file_map = {str(f): f for f in mib_files}

            for mib_name in compilation_order:
                # 查找包含此 MIB 名称的文件
                found_file = None
                for file_path in mib_files:
                    try:
                        file_mib_name = parser._extract_mib_name_from_content(file_path)
                        if file_mib_name == mib_name:
                            found_file = file_path
                            break
                    except:
                        pass

                if found_file:
                    ordered_mib_files.append(found_file)
                else:
                    print(f"Warning: Could not find file for MIB {mib_name}")

            # 添加未在依赖图中的文件
            for mib_file in mib_files:
                if mib_file not in ordered_mib_files:
                    ordered_mib_files.append(mib_file)

            mib_files = ordered_mib_files
        else:
            print("依赖解析器未启用，使用文件名排序")
            mib_files.sort()
    except Exception as e:
        print(f"依赖分析失败，使用文件名排序: {e}")
        mib_files.sort()

    print(f"\n将按以下顺序解析 MIB 文件:")
    for i, f in enumerate(mib_files, 1):
        try:
            mib_name = parser._extract_mib_name_from_content(f)
            print(f"  {i}. {f.name} -> {mib_name}")
        except:
            print(f"  {i}. {f.name}")

    # 存储所有解析结果
    all_mib_data = []
    failed_files = []

    # 逐个解析 MIB 文件
    for i, mib_file in enumerate(mib_files, 1):
        print(f"\n[{i}/{len(mib_files)}] 正在解析: {mib_file.name}")

        try:
            # 解析 MIB 文件
            mib_data = parser.parse_mib_file(str(mib_file))
            all_mib_data.append(mib_data)

            # 基本统计信息
            print(f"  ✓ MIB 名称: {mib_data.name}")
            print(f"  ✓ 节点数量: {len(mib_data.nodes)}")
            print(f"  ✓ 导入模块: {len(mib_data.imports)}")

            # 保存单个 MIB 的 JSON 文件
            output_file = output_dir / f"{mib_file.stem}.json"
            serializer.serialize(mib_data, str(output_file))
            print(f"  ✓ 已保存到: {output_file.name}")

            # 保存树形结构
            tree_file = output_dir / f"{mib_file.stem}_tree.json"
            serializer.serialize_tree(mib_data, str(tree_file))
            print(f"  ✓ 树形结构已保存到: {tree_file.name}")

            # 如果有节点，保存 OID 映射
            if mib_data.nodes:
                oid_file = output_dir / f"{mib_file.stem}_oids.json"
                serializer.export_oid_mapping(mib_data, str(oid_file))
                print(f"  ✓ OID 映射已保存到: {oid_file.name}")

                # 显示根节点信息
                root_nodes = mib_data.get_root_nodes()
                if root_nodes:
                    print(f"  ✓ 根节点: {[node.name for node in root_nodes]}")

        except Exception as e:
            failed_files.append((mib_file.name, str(e)))
            print(f"  ✗ 解析失败: {e}")
            print(f"  详细错误: {traceback.format_exc()}")

    # 生成汇总报告
    print("\n" + "=" * 60)
    print("解析汇总报告")
    print("=" * 60)

    print(f"\n成功解析: {len(all_mib_files) if 'all_mib_files' in locals() else 0} 个文件")
    print(f"解析失败: {len(failed_files)} 个文件")

    if failed_files:
        print("\n解析失败的文件:")
        for filename, error in failed_files:
            print(f"  ✗ {filename}: {error}")

    # 保存所有 MIB 数据的汇总文件
    if all_mib_data:
        try:
            # 保存所有 MIB 数据到一个文件
            all_data_file = output_dir / "all_mibs.json"
            serializer.serialize(all_mib_data, str(all_data_file))
            print(f"\n✓ 所有 MIB 数据已保存到: {all_data_file.name}")

            # 生成完整的 OID 映射
            all_oids_file = output_dir / "all_oids_mapping.json"
            serializer.export_oid_mapping(all_mib_data, str(all_oids_file))
            print(f"✓ 完整 OID 映射已保存到: {all_oids_file.name}")

            # 生成统计报告
            generate_statistics_report(all_mib_data, output_dir)

        except Exception as e:
            print(f"\n✗ 保存汇总文件时出错: {e}")

    return all_mib_data, failed_files


def generate_statistics_report(mib_data_list, output_dir):
    """生成统计报告"""
    print("\n正在生成统计报告...")

    report = {
        "summary": {
            "total_mibs": len(mib_data_list),
            "total_nodes": sum(len(mib.nodes) for mib in mib_data_list),
            "total_imports": sum(len(mib.imports) for mib in mib_data_list),
        },
        "mib_details": []
    }

    for mib_data in mib_data_list:
        # 使用 MibTree 获取统计信息
        tree = MibTree(mib_data)
        stats = tree.get_node_statistics()

        mib_detail = {
            "name": mib_data.name,
            "description": mib_data.description,
            "nodes_count": len(mib_data.nodes),
            "imports_count": len(mib_data.imports),
            "root_nodes": stats["root_nodes"],
            "max_depth": stats["max_depth"],
            "leaf_nodes": stats["leaf_nodes"],
            "nodes_with_children": stats["nodes_with_children"],
            "root_oids": mib_data.root_oids,
            "sample_nodes": []
        }

        # 添加一些示例节点信息
        for i, (name, node) in enumerate(mib_data.nodes.items()):
            if i >= 5:  # 只显示前5个节点作为示例
                break
            mib_detail["sample_nodes"].append({
                "name": node.name,
                "oid": node.oid,
                "description": node.description[:100] + "..." if node.description and len(node.description) > 100 else node.description
            })

        report["mib_details"].append(mib_detail)

        print(f"  {mib_data.name}: {len(mib_data.nodes)} 节点, 深度 {stats['max_depth']}")

    # 保存统计报告
    import json
    stats_file = output_dir / "statistics_report.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"✓ 统计报告已保存到: {stats_file.name}")

    # 打印总体统计
    print(f"\n总体统计:")
    print(f"  MIB 文件数量: {report['summary']['total_mibs']}")
    print(f"  总节点数量: {report['summary']['total_nodes']}")
    print(f"  总导入数量: {report['summary']['total_imports']}")


def main():
    """主函数"""
    mib_dir = "MIB"
    output_dir = "output"

    print("MIB 文件批量解析工具")
    print("=" * 60)
    print(f"输入目录: {mib_dir}")
    print(f"输出目录: {output_dir}")
    print()

    # 检查 MIB 目录是否存在
    if not Path(mib_dir).exists():
        print(f"错误: MIB 目录 '{mib_dir}' 不存在!")
        return

    # 执行解析
    try:
        all_mib_data, failed_files = parse_mib_directory(mib_dir, output_dir)

        print("\n" + "=" * 60)
        print("解析完成!")
        print("=" * 60)

        if all_mib_data:
            print(f"✓ 成功解析了 {len(all_mib_data)} 个 MIB 文件")
            print(f"✓ 总共解析了 {sum(len(mib.nodes) for mib in all_mib_data)} 个节点")
            print(f"✓ 输出文件已保存到 '{output_dir}' 目录")

            # 列出生成的文件
            output_path = Path(output_dir)
            output_files = list(output_path.glob("*"))
            print(f"\n生成的文件 ({len(output_files)} 个):")
            for file in sorted(output_files):
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"  {file.name} ({size_mb:.2f} MB)")

        if failed_files:
            print(f"\n⚠️  有 {len(failed_files)} 个文件解析失败")

    except Exception as e:
        print(f"\n✗ 解析过程中出现错误: {e}")
        print(f"详细错误: {traceback.format_exc()}")


if __name__ == "__main__":
    main()