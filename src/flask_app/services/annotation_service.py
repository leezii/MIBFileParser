"""
标注服务 - 管理MIB叶子节点的字符串标注
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from mib_parser.leaf_extractor import LeafNodeExtractor


class AnnotationService:
    """标注服务类，管理叶子节点的字符串标注"""

    def __init__(self, storage_path: str = "storage"):
        """
        初始化标注服务

        Args:
            storage_path: 存储目录路径
        """
        self.storage_path = Path(storage_path)
        self.annotations_path = self.storage_path / "annotations"
        self.annotations_path.mkdir(parents=True, exist_ok=True)
        self.leaf_extractor = LeafNodeExtractor(storage_path)

        # 标注数据文件
        self.annotations_file = self.annotations_path / "leaf_annotations.json"

    def ensure_leaf_nodes_extracted(self):
        """确保叶子节点已提取"""
        extracted_file = self.storage_path / "leaf_nodes" / "extracted_leaf_nodes.json"
        demo_file = self.storage_path / "leaf_nodes" / "demo_leaf_nodes.json"

        # 如果没有标准提取数据，但有演示数据，使用演示数据
        if not extracted_file.exists() and demo_file.exists():
            print("使用演示数据...")
            return
        elif not extracted_file.exists() and not demo_file.exists():
            print("正在提取叶子节点...")
            self.leaf_extractor.extract_all_leaf_nodes()

    def get_all_annotations(self) -> Dict[str, Dict]:
        """
        获取所有标注数据

        Returns:
            标注数据字典，键为节点OID，值为标注信息
        """
        if not self.annotations_file.exists():
            return {}

        try:
            with open(self.annotations_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载标注文件失败: {e}")
            return {}

    def save_annotations(self, annotations: Dict[str, Dict]):
        """
        保存标注数据

        Args:
            annotations: 标注数据
        """
        # 添加保存时间戳
        annotations['_metadata'] = {
            'last_updated': datetime.now().isoformat(),
            'total_annotations': len([k for k in annotations.keys() if k != '_metadata'])
        }

        try:
            with open(self.annotations_file, 'w', encoding='utf-8') as f:
                json.dump(annotations, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存标注文件失败: {e}")

    def get_annotation_for_oid(self, oid: str) -> Optional[str]:
        """
        获取指定OID的标注

        Args:
            oid: 节点OID

        Returns:
            标注字符串，如果没有标注则返回None
        """
        annotations = self.get_all_annotations()
        annotation_info = annotations.get(oid)
        if annotation_info:
            return annotation_info.get('annotation')
        return None

    def set_annotation(self, oid: str, annotation: str, node_info: Dict = None):
        """
        设置标注

        Args:
            oid: 节点OID
            annotation: 标注字符串
            node_info: 节点信息（可选）
        """
        annotations = self.get_all_annotations()

        annotations[oid] = {
            'oid': oid,
            'annotation': annotation.strip(),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        # 添加节点信息
        if node_info:
            annotations[oid].update({
                'node_name': node_info.get('name'),
                'device_name': node_info.get('device_name'),
                'mib_name': node_info.get('mib_name'),
                'description': node_info.get('description')
            })
        else:
            # 如果没有提供节点信息，尝试从叶子节点数据中查找
            leaf_nodes = self.leaf_extractor.get_leaf_nodes_for_annotation()
            for node in leaf_nodes:
                if node.get('oid') == oid:
                    annotations[oid].update({
                        'node_name': node.get('name'),
                        'device_name': node.get('device_name'),
                        'mib_name': node.get('mib_name'),
                        'description': node.get('description')
                    })
                    break

        self.save_annotations(annotations)

    def delete_annotation(self, oid: str) -> bool:
        """
        删除标注

        Args:
            oid: 节点OID

        Returns:
            是否成功删除
        """
        annotations = self.get_all_annotations()
        if oid in annotations:
            del annotations[oid]
            self.save_annotations(annotations)
            return True
        return False

    def get_annotated_nodes(self) -> List[Dict]:
        """
        获取所有已标注的节点

        Returns:
            已标注节点列表
        """
        annotations = self.get_all_annotations()
        result = []

        for oid, annotation_info in annotations.items():
            if oid == '_metadata':
                continue

            if annotation_info.get('annotation'):
                result.append({
                    'oid': oid,
                    'annotation': annotation_info['annotation'],
                    'node_name': annotation_info.get('node_name'),
                    'device_name': annotation_info.get('device_name'),
                    'mib_name': annotation_info.get('mib_name'),
                    'description': annotation_info.get('description'),
                    'updated_at': annotation_info.get('updated_at')
                })

        return result

    def get_nodes_for_annotation_page(self, device_name: Optional[str] = None, page: int = 1, per_page: int = 50) -> Dict:
        """
        获取标注页面需要的节点数据

        Args:
            device_name: 设备名称过滤
            page: 页码
            per_page: 每页数量

        Returns:
            包含节点数据和分页信息的字典
        """
        # 确保叶子节点已提取
        self.ensure_leaf_nodes_extracted()

        # 获取所有叶子节点
        leaf_nodes = self.leaf_extractor.get_leaf_nodes_for_annotation()

        # 获取现有标注
        annotations = self.get_all_annotations()

        # 过滤设备
        if device_name:
            leaf_nodes = [node for node in leaf_nodes if node.get('device_name') == device_name]

        # 添加标注信息到节点
        for node in leaf_nodes:
            oid = node.get('oid')
            if oid in annotations:
                node['annotation'] = annotations[oid].get('annotation', '')
                node['annotated'] = bool(node['annotation'].strip())
                node['updated_at'] = annotations[oid].get('updated_at')
            else:
                node['annotation'] = ''
                node['annotated'] = False

        # 按设备名称和节点名称排序
        leaf_nodes.sort(key=lambda x: (x.get('device_name', ''), x.get('name', '')))

        # 分页
        total = len(leaf_nodes)
        start = (page - 1) * per_page
        end = start + per_page
        page_nodes = leaf_nodes[start:end]

        return {
            'nodes': page_nodes,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }

    def get_annotation_statistics(self) -> Dict:
        """
        获取标注统计信息

        Returns:
            统计信息字典
        """
        annotations = self.get_all_annotations()
        leaf_nodes = self.leaf_extractor.get_leaf_nodes_for_annotation()

        total_nodes = len(leaf_nodes)
        annotated_count = len([a for a in annotations.values() if a.get('annotation') and a.get('oid') != '_metadata'])

        # 按设备统计
        device_stats = {}
        for node in leaf_nodes:
            device = node.get('device_name', 'Unknown')
            if device not in device_stats:
                device_stats[device] = {'total': 0, 'annotated': 0}
            device_stats[device]['total'] += 1

        for oid, annotation_info in annotations.items():
            if oid == '_metadata':
                continue
            if annotation_info.get('annotation'):
                device = annotation_info.get('device_name', 'Unknown')
                if device in device_stats:
                    device_stats[device]['annotated'] += 1

        return {
            'total_nodes': total_nodes,
            'annotated_count': annotated_count,
            'unannotated_count': total_nodes - annotated_count,
            'completion_rate': round((annotated_count / total_nodes * 100) if total_nodes > 0 else 0, 2),
            'device_stats': device_stats
        }