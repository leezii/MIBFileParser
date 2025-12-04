"""
Main web page routes for MIB visualization.
"""

from flask import Blueprint, render_template, request, redirect, url_for
import logging

logger = logging.getLogger(__name__)

# Create Blueprint
main_bp = Blueprint('main', __name__)

# Initialize service (will be configured with app context later)
mib_service = None


@main_bp.before_app_request
def initialize_service():
    """Initialize MIB service on first request."""
    global mib_service
    if mib_service is None:
        from flask import current_app
        output_dir = current_app.config.get('OUTPUT_DIR')
        from ..services.mib_service import MibService
        mib_service = MibService(output_dir)


@main_bp.route('/')
def index():
    """
    Home page - list all available MIB files.

    Returns:
        Rendered HTML template with MIB list
    """
    try:
        # Get MIB list with basic info
        mibs = mib_service.list_mibs()

        # Get statistics for overview
        stats = mib_service.get_statistics()

        return render_template(
            'index.html',
            mibs=mibs,
            stats=stats,
            title='MIB Viewer - Home'
        )

    except Exception as e:
        logger.error(f"Error loading index page: {e}")
        return render_template(
            'index.html',
            mibs=[],
            stats={'total_mibs': 0, 'total_nodes': 0},
            title='MIB Viewer - Home',
            error=str(e)
        )


@main_bp.route('/mib/<mib_name>')
def view_mib(mib_name):
    """
    View a specific MIB in tree format.

    Args:
        mib_name: Name of the MIB to view

    Returns:
        Rendered HTML template with tree visualization
    """
    try:
        # Get MIB data
        mib_data = mib_service.get_mib_data(mib_name)

        if mib_data is None:
            return render_template(
                'error.html',
                error_message=f'MIB "{mib_name}" not found',
                title='MIB Not Found'
            ), 404

        # Get tree data
        tree_data = mib_service.get_mib_tree_data(mib_name)

        return render_template(
            'tree_view.html',
            mib_name=mib_name,
            mib_data=mib_data,
            tree_data=tree_data,
            title=f'MIB Viewer - {mib_name}'
        )

    except Exception as e:
        logger.error(f"Error viewing MIB {mib_name}: {e}")
        return render_template(
            'error.html',
            error_message=f'Error loading MIB "{mib_name}": {e}',
            title='Error'
        ), 500


@main_bp.route('/search')
def search_page():
    """
    Search page for searching across all MIBs.

    Query Parameters:
        - q: Search query
        - mib: MIB to search within

    Returns:
        Rendered HTML template with search results
    """
    try:
        query = request.args.get('q', '').strip()
        mib_filter = request.args.get('mib', '')
        results = []

        if query:
            results = mib_service.search_nodes(query, mib_filter if mib_filter else None)

        # Get MIB list for filter dropdown
        mibs = mib_service.list_mibs()

        return render_template(
            'search.html',
            query=query,
            mib_filter=mib_filter,
            results=results,
            mibs=mibs,
            title=f'MIB Viewer - Search{" Results" if query else ""}'
        )

    except Exception as e:
        logger.error(f"Error in search page: {e}")
        return render_template(
            'search.html',
            query=request.args.get('q', ''),
            mib_filter=request.args.get('mib', ''),
            results=[],
            mibs=[],
            title='MIB Viewer - Search',
            error=str(e)
        )


@main_bp.route('/node/<path:oid>')
def view_node(oid):
    """
    View details of a specific node by OID.

    Args:
        oid: OID of the node to view

    Returns:
        Rendered HTML template with node details
    """
    try:
        node_data = mib_service.get_node_by_oid(oid)

        if node_data is None:
            return render_template(
                'error.html',
                error_message=f'Node with OID "{oid}" not found',
                title='Node Not Found'
            ), 404

        return render_template(
            'node_details.html',
            oid=oid,
            node_data=node_data,
            title=f'Node Details - {oid}'
        )

    except Exception as e:
        logger.error(f"Error viewing node {oid}: {e}")
        return render_template(
            'error.html',
            error_message=f'Error loading node "{oid}": {e}',
            title='Error'
        ), 500


@main_bp.route('/statistics')
def statistics_page():
    """
    Statistics page showing overall MIB statistics.

    Returns:
        Rendered HTML template with statistics
    """
    try:
        stats = mib_service.get_statistics()
        mibs = mib_service.list_mibs()

        # Add additional statistics
        mib_sizes = [(mib['name'], mib.get('nodes_count', 0), mib.get('size', 0)) for mib in mibs]
        mib_sizes.sort(key=lambda x: x[1], reverse=True)  # Sort by node count

        # Top 10 largest MIBs
        top_mibs = mib_sizes[:10]

        return render_template(
            'statistics.html',
            stats=stats,
            top_mibs=top_mibs,
            mibs=mibs,
            title='MIB Viewer - Statistics'
        )

    except Exception as e:
        logger.error(f"Error loading statistics page: {e}")
        return render_template(
            'statistics.html',
            stats={},
            top_mibs=[],
            mibs=[],
            title='MIB Viewer - Statistics',
            error=str(e)
        )


@main_bp.route('/about')
def about_page():
    """
    About page with information about the MIB viewer.

    Returns:
        Rendered HTML template
    """
    return render_template(
        'about.html',
        title='MIB Viewer - About'
    )


# Helper functions
@main_bp.context_processor
def inject_global_vars():
    """Inject global variables into all templates."""
    return {
        'app_name': 'MIB Viewer',
        'version': '1.0.0'
    }


# Error handlers
@main_bp.app_errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template(
        'error.html',
        error_message='Page not found',
        title='Page Not Found'
    ), 404


@main_bp.app_errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return render_template(
        'error.html',
        error_message='Internal server error',
        title='Error'
    ), 500