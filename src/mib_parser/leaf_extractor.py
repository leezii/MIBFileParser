"""
MIB叶子节点提取器 - 提取符合条件的叶子节点用于标注
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

from src.mib_parser.models import MibNode, MibData
from src.mib_parser.parser import MibParser


class LeafNodeExtractor:
    """MIB叶子节点提取器，提取符合条件的叶子节点"""

    def __init__(self, storage_path: str = "storage"):
        """
        初始化提取器

        Args:
            storage_path: 存储目录路径
        """
        self.storage_path = Path(storage_path)
        self.devices_path = self.storage_path / "devices"
        self.global_path = self.storage_path / "global"
        self.leaf_nodes_path = self.storage_path / "leaf_nodes"
        self.leaf_nodes_path.mkdir(parents=True, exist_ok=True)

    def extract_all_leaf_nodes(self) -> Dict[str, List[Dict]]:
        """
        从所有设备中提取符合条件的叶子节点

        Returns:
            包含所有设备叶子节点的字典
        """
        result = {}

        # 处理所有设备
        if self.devices_path.exists():
            for device_dir in self.devices_path.iterdir():
                if device_dir.is_dir():
                    device_name = device_dir.name
                    leaf_nodes = self._extract_device_leaf_nodes(device_name)
                    if leaf_nodes:
                        result[device_name] = leaf_nodes

        # 保存结果到文件
        self._save_leaf_nodes(result)

        return result

    def _extract_device_leaf_nodes(self, device_name: str) -> List[Dict]:
        """
        从指定设备提取叶子节点

        Args:
            device_name: 设备名称

        Returns:
            符合条件的叶子节点列表
        """
        device_path = self.devices_path / device_name
        output_path = device_path / "output"

        if not output_path.exists():
            return []

        leaf_nodes = []

        # 遍历所有MIB文件
        for mib_file in output_path.glob("*.json"):
            try:
                with open(mib_file, 'r', encoding='utf-8') as f:
                    mib_data = json.load(f)

                # 提取叶子节点
                extracted_nodes = self._extract_leaf_nodes_from_mib(mib_data, device_name, mib_file.stem)
                leaf_nodes.extend(extracted_nodes)

            except Exception as e:
                print(f"处理MIB文件 {mib_file} 时出错: {e}")
                continue

        return leaf_nodes

    def _extract_leaf_nodes_from_mib(self, mib_data: Dict, device_name: str, mib_name: str) -> List[Dict]:
        """
        从MIB数据中提取符合条件的叶子节点

        Args:
            mib_data: MIB数据
            device_name: 设备名称
            mib_name: MIB名称

        Returns:
            符合条件的叶子节点列表
        """
        leaf_nodes = []
        nodes = mib_data.get('nodes', {})

        # 构建OID到节点的映射
        oid_to_node = {}
        name_to_node = {}

        for node_name, node_info in nodes.items():
            node = MibNode.from_dict(node_info)
            oid_to_node[node.oid] = node
            name_to_node[node_name] = node

        # 基于OID结构构建父子关系
        parent_to_children = {}
        for oid, node in oid_to_node.items():
            # 查找父节点：去掉最后一个OID段
            oid_parts = oid.split('.')
            if len(oid_parts) > 1:
                parent_oid = '.'.join(oid_parts[:-1])
                # 查找父节点
                for potential_parent_oid, potential_parent_node in oid_to_node.items():
                    if potential_parent_oid == parent_oid:
                        # 找到父节点，建立关系
                        if potential_parent_node.name not in parent_to_children:
                            parent_to_children[potential_parent_node.name] = []
                        parent_to_children[potential_parent_node.name].append(node)
                        # 设置节点的父节点名称
                        node.parent_name = potential_parent_node.name
                        break

        # 查找符合条件的叶子节点
        for node_name, node_info in nodes.items():
            node = MibNode.from_dict(node_info)

            # 检查是否为叶子节点（没有子节点）
            children = parent_to_children.get(node_name, [])
            if children:  # 有子节点，不是叶子节点
                continue

            # 检查是否为OCTET STRING类型
            if not self._is_octet_string(node):
                continue

            # 检查名称是否包含"para"
            if not self._name_contains_para(node_name):
                continue

            # 检查是否有兄弟节点是Count64或PerformanceEventType类型
            parent_name = node.parent_name
            siblings = parent_to_children.get(parent_name, [])
            if not self._has_required_sibling(node_name, siblings, name_to_node):
                continue

            # 创建叶子节点数据
            leaf_node_data = {
                "name": node_name,
                "oid": node.oid,
                "description": node.description,
                "syntax": self._get_syntax_string(node.syntax),
                "access": node.max_access or node.access,
                "module": node.module,
                "mib_name": mib_name,
                "device_name": device_name,
                "parent_name": node.parent_name,
                "extracted_at": datetime.now().isoformat()
            }

            leaf_nodes.append(leaf_node_data)

        return leaf_nodes

    def _is_octet_string(self, node: MibNode) -> bool:
        """
        检查节点是否为OCTET STRING类型

        Args:
            node: MIB节点

        Returns:
            是否为OCTET STRING类型
        """
        syntax = self._get_syntax_string(node.syntax)
        if syntax:
            return "OCTET STRING" in syntax.upper()
        return False

    def _name_contains_para(self, node_name: str) -> bool:
        """
        检查节点名称是否包含"para"

        Args:
            node_name: 节点名称

        Returns:
            是否包含"para"
        """
        return "para" in node_name.lower()

    def _has_required_sibling(self, node_name: str, siblings: List[MibNode], name_to_node: Dict[str, MibNode]) -> bool:
        """
        检查是否有兄弟节点是Count64或PerformanceEventType类型

        Args:
            node_name: 当前节点名称
            siblings: 兄弟节点列表
            name_to_node: 名称到节点的映射

        Returns:
            是否有符合要求的兄弟节点
        """
        # 检查直接兄弟节点
        for sibling in siblings:
            sibling_syntax = self._get_syntax_string(sibling.syntax)
            if sibling_syntax:
                sibling_syntax_upper = sibling_syntax.upper()
                if "COUNTER64" in sibling_syntax_upper or "PERFORMANCEEVENTTYPE" in sibling_syntax_upper:
                    return True

        # 如果当前节点有父节点，基于OID前缀查找可能的兄弟节点
        current_node = name_to_node.get(node_name)
        if current_node and current_node.oid:
            # 获取当前节点的OID前缀（去掉最后一个数字）
            oid_parts = current_node.oid.split('.')
            if len(oid_parts) > 1:
                base_oid = '.'.join(oid_parts[:-1])

                # 查找所有具有相同前缀的节点
                for sibling_name, sibling_node in name_to_node.items():
                    if sibling_name == node_name:
                        continue

                    if sibling_node.oid and sibling_node.oid.startswith(base_oid + '.'):
                        # 检查这个节点的类型
                        sibling_syntax = self._get_syntax_string(sibling_node.syntax)
                        if sibling_syntax:
                            sibling_syntax_upper = sibling_syntax.upper()
                            if "COUNTER64" in sibling_syntax_upper or "PERFORMANCEEVENTTYPE" in sibling_syntax_upper:
                                return True

        return False

    def _get_syntax_string(self, syntax) -> str:
        """
        获取语法字符串表示

        Args:
            syntax: 语法信息

        Returns:
            语法字符串
        """
        if syntax is None:
            return ""

        if isinstance(syntax, str):
            return syntax

        if isinstance(syntax, dict):
            syntax_type = syntax.get('type', '')
            if syntax_type:
                return syntax_type

        return str(syntax)

    def _save_leaf_nodes(self, leaf_nodes_data: Dict[str, List[Dict]]):
        """
        保存叶子节点数据到文件

        Args:
            leaf_nodes_data: 叶子节点数据
        """
        # 保存完整数据
        output_file = self.leaf_nodes_path / "extracted_leaf_nodes.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(leaf_nodes_data, f, ensure_ascii=False, indent=2)

        # 保存按设备分组的文件
        for device_name, nodes in leaf_nodes_data.items():
            device_file = self.leaf_nodes_path / f"{device_name}_leaf_nodes.json"
            with open(device_file, 'w', encoding='utf-8') as f:
                json.dump(nodes, f, ensure_ascii=False, indent=2)

        print(f"叶子节点数据已保存到: {output_file}")
        print(f"总计提取到 {sum(len(nodes) for nodes in leaf_nodes_data.values())} 个符合条件的叶子节点")

    def load_leaf_nodes(self, device_name: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        加载已提取的叶子节点数据

        Args:
            device_name: 设备名称，如果为None则加载所有设备的数据

        Returns:
            叶子节点数据
        """
        if device_name:
            device_file = self.leaf_nodes_path / f"{device_name}_leaf_nodes.json"
            if device_file.exists():
                with open(device_file, 'r', encoding='utf-8') as f:
                    return {device_name: json.load(f)}
            return {}
        else:
            output_file = self.leaf_nodes_path / "extracted_leaf_nodes.json"
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}

    def get_leaf_nodes_for_annotation(self) -> List[Dict]:
        """
        获取所有需要标注的叶子节点

        Returns:
            扁平化的叶子节点列表
        """
        # 尝试加载标准提取数据
        all_leaf_nodes = self.load_leaf_nodes()

        # 如果没有标准数据，尝试加载演示数据
        if not all_leaf_nodes:
            demo_file = self.leaf_nodes_path / "demo_leaf_nodes.json"
            if demo_file.exists():
                with open(demo_file, 'r', encoding='utf-8') as f:
                    all_leaf_nodes = json.load(f)

        result = []

        for device_name, nodes in all_leaf_nodes.items():
            for node in nodes:
                # 添加标注信息
                node_with_annotation = node.copy()
                node_with_annotation['annotation'] = ""
                node_with_annotation['annotated'] = False
                result.append(node_with_annotation)

        return result