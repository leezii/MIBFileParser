"""
MIB 依赖关系解析器
"""

import re
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque


@dataclass
class MibFile:
    """MIB 文件信息"""
    name: str
    file_path: str
    imports: Set[str]
    exports: Set[str]
    level: int = 0


class MibDependencyResolver:
    """MIB 依赖关系解析器"""

    def __init__(self):
        self.mib_files: Dict[str, MibFile] = {}
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_dependency_graph: Dict[str, Set[str]] = defaultdict(set)

    def parse_mib_dependencies(self, mib_directory: str) -> Dict[str, MibFile]:
        """解析 MIB 目录中的所有文件的依赖关系"""
        mib_dir = Path(mib_directory)
        mib_files = list(mib_dir.glob("*.mib"))

        # 首先解析所有文件的基本信息
        for mib_file in mib_files:
            mib_name = self._extract_mib_name(mib_file)
            imports, exports = self._extract_imports_exports(mib_file)

            mib_obj = MibFile(
                name=mib_name,
                file_path=str(mib_file),
                imports=imports,
                exports=exports
            )
            self.mib_files[mib_name] = mib_obj

        # 构建依赖图
        self._build_dependency_graph()

        return self.mib_files

    def _extract_mib_name(self, file_path: Path) -> str:
        """从文件路径提取 MIB 名称"""
        # 从文件名提取（去掉前缀数字和扩展名）
        stem = file_path.stem
        # 如果以数字开头，去掉数字前缀
        if stem and stem[0].isdigit():
            # 找到第一个非数字字符
            for i, char in enumerate(stem):
                if not char.isdigit():
                    return stem[i:]
        return stem

    def _extract_imports_exports(self, file_path: Path) -> Tuple[Set[str], Set[str]]:
        """从 MIB 文件中提取导入和导出"""
        imports = set()
        exports = set()

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # 解析 IMPORTS 部分
            imports_match = re.search(r'IMPORTS\s+(.*?)\s*FROM', content, re.DOTALL | re.IGNORECASE)
            if imports_match:
                imports_section = imports_match.group(1)
                # 提取所有导入的标识符
                import_names = re.findall(r'(\w+(?:-\w+)*)\s*\n', imports_section)
                for name in import_names:
                    name = name.strip()
                    if name and name.upper() != 'FROM':
                        imports.add(name)

            # 解析定义的 OBJECT IDENTIFIER 和其他标识符
            # 简化版本：查找所有 OBJECT IDENTIFIER 定义
            oid_matches = re.findall(r'(\w+(?:-\w+)*)\s+OBJECT\s+IDENTIFIER', content, re.IGNORECASE)
            for match in oid_matches:
                exports.add(match)

            # 查找 MODULE-IDENTITY 导出
            module_matches = re.findall(r'(\w+(?:-\w+)*)\s+MODULE-IDENTITY', content, re.IGNORECASE)
            for match in module_matches:
                exports.add(match)

            # 查找 TEXTUAL-CONVENTION 导出
            tc_matches = re.findall(r'(\w+(?:-\w+)*)\s+TEXTUAL-CONVENTION', content, re.IGNORECASE)
            for match in tc_matches:
                exports.add(match)

        except Exception as e:
            print(f"Warning: Failed to parse dependencies from {file_path}: {e}")

        return imports, exports

    def _build_dependency_graph(self):
        """构建依赖关系图"""
        for mib_name, mib_file in self.mib_files.items():
            for imported_module in mib_file.imports:
                # 标准库依赖不需要处理
                if imported_module.upper() in ['SNMPV2-SMI', 'SNMPV2-TC', 'SNMPV2-CONF']:
                    continue

                # 如果依赖的模块也在我们的 MIB 文件中，则添加依赖关系
                if imported_module in self.mib_files:
                    self.dependency_graph[mib_name].add(imported_module)
                    self.reverse_dependency_graph[imported_module].add(mib_name)

    def get_compilation_order(self) -> List[str]:
        """获取编译顺序（拓扑排序）"""
        in_degree = {mib_name: len(dependencies) for mib_name, dependencies in self.dependency_graph.items()}

        # 添加没有依赖的 MIB
        all_mibs = set(self.mib_files.keys())
        dependent_mibs = set(self.dependency_graph.keys())
        independent_mibs = all_mibs - dependent_mibs
        for mib in independent_mibs:
            in_degree[mib] = 0

        # 使用 Kahn 算法进行拓扑排序
        queue = deque([mib for mib, degree in in_degree.items() if degree == 0])
        compilation_order = []

        while queue:
            current = queue.popleft()
            compilation_order.append(current)

            # 更新依赖当前 MIB 的其他 MIB 的入度
            for dependent in self.reverse_dependency_graph[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # 检查是否存在循环依赖
        if len(compilation_order) != len(self.mib_files):
            # 如果有循环依赖，尝试手动处理
            remaining = set(self.mib_files.keys()) - set(compilation_order)
            print(f"Warning: Circular dependencies detected among: {remaining}")
            # 将剩余的 MIB 添加到末尾
            compilation_order.extend(remaining)

        return compilation_order

    def print_dependency_info(self):
        """打印依赖关系信息"""
        print("MIB 依赖关系分析:")
        print("=" * 50)

        for mib_name, mib_file in self.mib_files.items():
            print(f"\n{mib_name}:")
            print(f"  文件: {Path(mib_file.file_path).name}")
            if mib_file.imports:
                print(f"  导入: {', '.join(sorted(mib_file.imports))}")
            if mib_file.exports:
                print(f"  导出: {', '.join(sorted(mib_file.exports)[:5])}{'...' if len(mib_file.exports) > 5 else ''}")

        print(f"\n编译顺序:")
        order = self.get_compilation_order()
        for i, mib_name in enumerate(order, 1):
            dependencies = self.dependency_graph.get(mib_name, set())
            if dependencies:
                print(f"  {i:2d}. {mib_name} (依赖: {', '.join(dependencies)})")
            else:
                print(f"  {i:2d}. {mib_name} (无依赖)")