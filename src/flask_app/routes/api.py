"""
API routes for MIB data access.
"""

from flask import Blueprint, jsonify, request
import logging

from ..services.mib_service import MibService

logger = logging.getLogger(__name__)

# Create Blueprint
api_bp = Blueprint('api', __name__)

# Initialize service (will be configured with app context later)
mib_service = None


@api_bp.before_app_request
def initialize_service():
    """Initialize MIB service on first request."""
    global mib_service
    if mib_service is None:
        from flask import current_app
        output_dir = current_app.config.get('OUTPUT_DIR')
        mib_service = MibService(output_dir)


@api_bp.route('/mibs', methods=['GET'])
def list_mibs():
    """
    List all available MIB files with metadata.

    Query Parameters:
        - include_data: If 'true', include basic node counts for each MIB

    Returns:
        JSON array of MIB metadata
    """
    try:
        include_data = request.args.get('include_data', 'false').lower() == 'true'
        mibs = mib_service.list_mibs()

        if include_data:
            # Already included by the service
            return jsonify({
                'success': True,
                'data': mibs,
                'count': len(mibs)
            })
        else:
            # Return minimal info
            minimal_mibs = [
                {
                    'name': mib['name'],
                    'filename': mib['filename'],
                    'last_modified': mib['last_modified']
                }
                for mib in mibs
            ]
            return jsonify({
                'success': True,
                'data': minimal_mibs,
                'count': len(minimal_mibs)
            })

    except Exception as e:
        logger.error(f"Error listing MIBs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/mibs/<mib_name>', methods=['GET'])
def get_mib_data(mib_name):
    """
    Get detailed data for a specific MIB.

    Path Parameters:
        - mib_name: Name of the MIB

    Returns:
        JSON object with MIB data
    """
    try:
        data = mib_service.get_mib_data(mib_name)

        if data is None:
            return jsonify({
                'success': False,
                'error': f'MIB "{mib_name}" not found'
            }), 404

        return jsonify({
            'success': True,
            'data': data
        })

    except Exception as e:
        logger.error(f"Error getting MIB data for {mib_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/mibs/<mib_name>/tree', methods=['GET'])
def get_mib_tree(mib_name):
    """
    Get tree-structured data for a specific MIB.

    Path Parameters:
        - mib_name: Name of the MIB

    Query Parameters:
        - format: 'd3' (default) or 'flat' for different output formats
        - include_stats: If 'true', include tree statistics

    Returns:
        JSON object with tree structure
    """
    try:
        format_type = request.args.get('format', 'd3').lower()
        include_stats = request.args.get('include_stats', 'true').lower() == 'true'

        if format_type == 'flat':
            # Get flat list of nodes
            mib_data = mib_service.get_mib_data(mib_name)
            if mib_data is None:
                return jsonify({
                    'success': False,
                    'error': f'MIB "{mib_name}" not found'
                }), 404

            from ..services.tree_service import TreeService
            tree_service = TreeService()
            root_nodes = tree_service.build_breadth_first_tree(mib_data)

            result_data = {
                'mib_name': mib_name,
                'nodes': root_nodes,
                'total_nodes': len(mib_data.get('nodes', {}))
            }

            if include_stats:
                from ..services.tree_service import TreeService
                ts = TreeService()
                tree_data = ts.build_tree_structure(mib_data)
                result_data['statistics'] = tree_data.get('statistics', {})

        else:  # default d3 format
            result_data = mib_service.get_mib_tree_data(mib_name)
            if result_data is None:
                return jsonify({
                    'success': False,
                    'error': f'MIB "{mib_name}" not found'
                }), 404

            if not include_stats:
                result_data.pop('statistics', None)

        return jsonify({
            'success': True,
            'data': result_data
        })

    except Exception as e:
        logger.error(f"Error getting tree data for {mib_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/search', methods=['GET'])
def search_nodes():
    """
    Search for nodes across MIBs.

    Query Parameters:
        - q: Search query (required)
        - mib: Limit search to specific MIB (optional)
        - limit: Maximum number of results (default: 50)
        - match_type: Filter by match type ('name', 'oid', 'description', 'all')

    Returns:
        JSON array of search results
    """
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400

        mib_name = request.args.get('mib')
        limit = int(request.args.get('limit', 50))
        match_type = request.args.get('match_type', 'all').lower()

        results = mib_service.search_nodes(query, mib_name)

        # Filter by match type if specified
        if match_type != 'all':
            results = [r for r in results if r.get('match_type') == match_type]

        # Apply limit
        results = results[:limit]

        return jsonify({
            'success': True,
            'data': results,
            'query': query,
            'mib_filter': mib_name,
            'match_type': match_type,
            'total_found': len(results)
        })

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid parameter: {e}'
        }), 400
    except Exception as e:
        logger.error(f"Error searching nodes: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/node/<path:oid>', methods=['GET'])
def get_node_by_oid(oid):
    """
    Find a node by its OID across all MIBs.

    Path Parameters:
        - oid: OID to search for

    Returns:
        JSON object with node data and MIB context
    """
    try:
        result = mib_service.get_node_by_oid(oid)

        if result is None:
            return jsonify({
                'success': False,
                'error': f'Node with OID "{oid}" not found'
            }), 404

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        logger.error(f"Error getting node by OID {oid}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """
    Get overall statistics about all MIBs.

    Returns:
        JSON object with statistics
    """
    try:
        stats = mib_service.get_statistics()

        return jsonify({
            'success': True,
            'data': stats
        })

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/mibs/<mib_name>/refresh', methods=['POST'])
def refresh_mib_cache(mib_name):
    """
    Refresh cache for a specific MIB.

    Path Parameters:
        - mib_name: Name of the MIB to refresh

    Returns:
        JSON response
    """
    try:
        mib_service.clear_cache(mib_name)

        # Try to reload the data to verify it exists
        data = mib_service.get_mib_data(mib_name, use_cache=False)

        if data is None:
            return jsonify({
                'success': False,
                'error': f'MIB "{mib_name}" not found'
            }), 404

        return jsonify({
            'success': True,
            'message': f'Cache refreshed for {mib_name}',
            'nodes_count': len(data.get('nodes', {}))
        })

    except Exception as e:
        logger.error(f"Error refreshing cache for {mib_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/cache/clear', methods=['POST'])
def clear_all_cache():
    """
    Clear all cached MIB data.

    Returns:
        JSON response
    """
    try:
        mib_service.clear_cache()

        return jsonify({
            'success': True,
            'message': 'All cache cleared'
        })

    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Error handlers
@api_bp.errorhandler(404)
def api_not_found(error):
    """Handle 404 errors for API routes."""
    return jsonify({
        'success': False,
        'error': 'API endpoint not found'
    }), 404


@api_bp.errorhandler(500)
def api_internal_error(error):
    """Handle 500 errors for API routes."""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500