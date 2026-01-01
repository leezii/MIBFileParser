"""
标注页面路由 - 管理MIB叶子节点的字符串标注
"""

from pathlib import Path
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_app.services.annotation_service import AnnotationService

annotation_bp = Blueprint('annotation', __name__, url_prefix='/annotation')

# 全局标注服务实例（延迟初始化）
annotation_service = None


@annotation_bp.before_app_request
def initialize_annotation_service():
    """初始化标注服务"""
    global annotation_service
    if annotation_service is None:
        from flask import current_app
        storage_dir = current_app.config.get('STORAGE_DIR')
        # Use configured storage directory or default to user home
        if storage_dir:
            annotation_service = AnnotationService(str(storage_dir))
        else:
            # Fallback to user home directory
            default_storage = Path.home() / '.mibparser' / 'storage'
            annotation_service = AnnotationService(str(default_storage))


@annotation_bp.route('/')
def index():
    """标注页面首页"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        device_name = request.args.get('device', None)

        # 获取节点数据
        data = annotation_service.get_nodes_for_annotation_page(
            device_name=device_name,
            page=page,
            per_page=per_page
        )

        # 获取统计信息
        stats = annotation_service.get_annotation_statistics()

        # 获取设备列表
        leaf_nodes = annotation_service.leaf_extractor.get_leaf_nodes_for_annotation()
        devices = sorted(list(set(node.get('device_name', 'Unknown') for node in leaf_nodes)))

        return render_template('annotation.html',
                             nodes=data['nodes'],
                             pagination=data['pagination'],
                             stats=stats,
                             devices=devices,
                             current_device=device_name,
                             current_per_page=per_page)

    except Exception as e:
        flash(f'加载标注页面失败: {str(e)}', 'error')
        return render_template('annotation.html',
                             nodes=[],
                             pagination={'current_page': 1, 'per_page': 50, 'total': 0, 'pages': 0},
                             stats={'total_nodes': 0, 'annotated_count': 0, 'completion_rate': 0},
                             devices=[],
                             current_device=None,
                             current_per_page=50)


@annotation_bp.route('/api/annotations')
def api_get_annotations():
    """API: 获取标注数据"""
    try:
        device_name = request.args.get('device')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        data = annotation_service.get_nodes_for_annotation_page(
            device_name=device_name,
            page=page,
            per_page=per_page
        )

        return jsonify({
            'success': True,
            'data': data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@annotation_bp.route('/api/annotation/<oid>', methods=['GET'])
def api_get_annotation(oid):
    """API: 获取指定OID的标注"""
    try:
        annotation = annotation_service.get_annotation_for_oid(oid)
        return jsonify({
            'success': True,
            'annotation': annotation
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@annotation_bp.route('/api/annotation', methods=['POST'])
def api_set_annotation():
    """API: 设置标注"""
    try:
        data = request.get_json()
        oid = data.get('oid')
        annotation = data.get('annotation', '')
        node_info = data.get('node_info', {})

        if not oid:
            return jsonify({
                'success': False,
                'error': 'OID is required'
            }), 400

        annotation_service.set_annotation(oid, annotation, node_info)

        return jsonify({
            'success': True,
            'message': 'Annotation saved successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@annotation_bp.route('/api/annotation/<oid>', methods=['DELETE'])
def api_delete_annotation(oid):
    """API: 删除标注"""
    try:
        success = annotation_service.delete_annotation(oid)
        return jsonify({
            'success': success,
            'message': 'Annotation deleted successfully' if success else 'Annotation not found'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@annotation_bp.route('/api/statistics')
def api_get_statistics():
    """API: 获取统计信息"""
    try:
        stats = annotation_service.get_annotation_statistics()
        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@annotation_bp.route('/api/extract')
def api_extract_leaf_nodes():
    """API: 重新提取叶子节点"""
    try:
        result = annotation_service.leaf_extractor.extract_all_leaf_nodes()
        return jsonify({
            'success': True,
            'message': 'Leaf nodes extracted successfully',
            'data': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@annotation_bp.route('/export')
def export_annotations():
    """导出标注数据"""
    try:
        annotations = annotation_service.get_annotated_nodes()
        return jsonify({
            'success': True,
            'annotations': annotations,
            'exported_at': annotation_service.get_all_annotations().get('_metadata', {}).get('last_updated')
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@annotation_bp.route('/api/index-field-oid')
def api_find_index_field_oid():
    """API: 根据索引字段名称查找对应的OID"""
    try:
        index_name = request.args.get('index_name')
        table_name = request.args.get('table_name')

        if not index_name:
            return jsonify({
                'success': False,
                'error': 'index_name is required'
            }), 400

        # 确保叶子节点已提取
        annotation_service.ensure_leaf_nodes_extracted()

        # 查找匹配的叶子节点
        leaf_nodes = annotation_service.leaf_extractor.get_leaf_nodes_for_annotation()

        for node in leaf_nodes:
            # 检查节点名称是否匹配索引字段名称
            if node.get('name') == index_name:
                # 如果提供了表名，进一步检查是否在同一个表中
                if table_name:
                    # 这里可以根据需要添加更复杂的匹配逻辑
                    # 目前只检查节点名称匹配
                    pass

                return jsonify({
                    'success': True,
                    'oid': node.get('oid'),
                    'node_info': {
                        'name': node.get('name'),
                        'device_name': node.get('device_name'),
                        'mib_name': node.get('mib_name'),
                        'description': node.get('description')
                    }
                })

        # 如果没有找到精确匹配，尝试模糊匹配
        for node in leaf_nodes:
            node_name = node.get('name', '').lower()
            index_name_lower = index_name.lower()

            # 检查是否包含索引字段名称
            if index_name_lower in node_name or node_name in index_name_lower:
                return jsonify({
                    'success': True,
                    'oid': node.get('oid'),
                    'node_info': {
                        'name': node.get('name'),
                        'device_name': node.get('device_name'),
                        'mib_name': node.get('mib_name'),
                        'description': node.get('description')
                    },
                    'match_type': 'partial'
                })

        return jsonify({
            'success': False,
            'error': 'No matching leaf node found for index field'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500