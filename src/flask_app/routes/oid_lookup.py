"""
OID lookup routes for MIB table interface.

This module provides web interface and API endpoints for looking up MIB tables
by OID and extracting index field information.
"""

from flask import Blueprint, render_template, request, jsonify, session, g
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Create Blueprint
oid_lookup_bp = Blueprint('oid_lookup', __name__)


@oid_lookup_bp.before_request
def setup_device_context():
    """Setup device context for the request."""
    from ..services.device_service import DeviceService

    device_service = DeviceService()

    # Get device from session or use default
    device_name = session.get('current_device') or device_service.get_current_device()

    # Override with URL parameter if provided
    url_device = request.args.get('device')
    if url_device and device_service.device_exists(url_device):
        device_name = url_device
        session['current_device'] = device_name
        device_service.set_current_device(device_name)

    # Store device context in Flask's g object
    g.device_name = device_name
    g.device_service = device_service
    g.mib_service = device_service.get_device_mib_service(device_name)


@oid_lookup_bp.route('/oid-lookup')
def oid_lookup_page():
    """
    Main OID lookup interface page.

    Returns:
        Rendered HTML template with OID lookup interface
    """
    try:
        # Get device context
        device_name = g.device_name
        device_service = g.device_service

        # Get device info
        device_info = device_service.get_device_info(device_name)
        all_devices = device_service.list_devices()

        return render_template(
            'oid_lookup.html',
            title='MIB OID Lookup',
            current_device=device_name,
            device_info=device_info,
            all_devices=all_devices
        )

    except Exception as e:
        logger.error(f"Error loading OID lookup page: {e}")
        return render_template(
            'oid_lookup.html',
            title='MIB OID Lookup',
            error=str(e)
        )


@oid_lookup_bp.route('/api/lookup-table', methods=['POST'])
def api_lookup_table():
    """
    AJAX API endpoint to look up table by OID.

    Request JSON:
        {
            "oid": "1.3.6.1.2.1.2.2"  # OID to lookup
        }

    Returns:
        JSON response with table information and index fields
    """
    try:
        # Get request data
        data = request.get_json()
        if not data or 'oid' not in data:
            return jsonify({
                'success': False,
                'error': 'OID is required'
            }), 400

        oid = data['oid'].strip()
        if not oid:
            return jsonify({
                'success': False,
                'error': 'OID cannot be empty'
            }), 400

        # Get device context
        device_name = g.device_name
        mib_service = g.mib_service

        # Initialize MibTableService
        from ..services.mib_table_service import MibTableService
        table_service = MibTableService(mib_service, g.device_service)

        # Find table by OID
        result = table_service.find_table_by_oid(oid, device_name)

        if not result:
            return jsonify({
                'success': False,
                'error': f'No table found for OID: {oid}',
                'suggestions': 'Please check the OID and try again. Note: The system can automatically search for tables within 2 levels of your OID.'
            }), 404

        # Get table structure
        table_structure = table_service.get_table_structure(result.table_name, device_name)

        # Extract index fields if we have an entry
        indexes = []
        if table_structure and table_structure.get('index_fields'):
            for index_field in table_structure['index_fields']:
                # Format for frontend display
                display_field = {
                    'name': index_field.get('name', ''),
                    'type': index_field.get('type', 'Unknown'),
                    'display_type': _get_display_type(index_field.get('type', '')),
                    'syntax': index_field.get('syntax', ''),
                    'required': not index_field.get('is_optional', False),
                    'description': index_field.get('description', ''),
                    'placeholder': _generate_placeholder(index_field),
                    'validation_pattern': index_field.get('validation_pattern'),
                    'constraints': index_field.get('constraints', {})
                }
                indexes.append(display_field)

        # Format response
        response_data = {
            'success': True,
            'table': {
                'name': result.table_name,
                'oid': result.table_oid,
                'description': result.description or '',
                'mib_name': result.mib_name or '',
                'match_type': result.match_type,
                'confidence': result.confidence
            },
            'indexes': indexes,
            'entry_info': {
                'name': table_structure.get('entry_name') if table_structure else None,
                'oid': table_structure.get('entry_oid') if table_structure else None
            }
        }

        # Add entry info if available
        if result.entry_name and result.entry_oid:
            response_data['entry'] = {
                'name': result.entry_name,
                'oid': result.entry_oid
            }

        # Add smart search notice if this was found via nearby search
        if result.match_type in ['downward_1', 'downward_2', 'upward_1', 'upward_2']:
            search_direction = "downward" if 'downward' in result.match_type else "upward"
            search_level = result.match_type.split('_')[1]
            response_data['smart_search_notice'] = (
                f"Table found {search_direction} (level {search_level}) from your OID: {oid} → {result.table_oid}. "
                f"The system searched within 2 levels of your input."
            )

        logger.info(f"Successfully looked up table {result.table_name} for OID {oid} (match: {result.match_type})")
        return jsonify(response_data)

    except ValueError as e:
        logger.warning(f"Invalid OID format: {e}")
        return jsonify({
            'success': False,
            'error': f'Invalid OID format: {str(e)}'
        }), 400

    except Exception as e:
        logger.error(f"Error looking up table: {e}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while looking up the table',
            'details': str(e)
        }), 500


@oid_lookup_bp.route('/api/suggest-tables', methods=['GET'])
def api_suggest_tables():
    """
    AJAX API endpoint to get table name suggestions for autocomplete.

    Query Parameters:
        - q: Partial query string
        - limit: Maximum number of suggestions (default: 10)

    Returns:
        JSON response with suggestions list
    """
    try:
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 10)), 50)  # Cap at 50

        if not query or len(query) < 2:
            return jsonify({
                'success': True,
                'suggestions': []
            })

        # Get device context
        device_name = g.device_name
        mib_service = g.mib_service

        # Initialize MibTableService
        from ..services.mib_table_service import MibTableService
        table_service = MibTableService(mib_service, g.device_service)

        # Get suggestions
        suggestions = table_service.get_table_suggestions(query, device_name, limit)

        # Format suggestions for frontend
        formatted_suggestions = []
        for suggestion in suggestions:
            formatted_suggestion = {
                'name': suggestion['name'],
                'mib_name': suggestion['mib_name'],
                'description': suggestion['description'][:100] + '...' if len(suggestion['description']) > 100 else suggestion['description'],
                'oid': suggestion['oid'],
                'match_score': suggestion['match_score'],
                'display_text': f"{suggestion['name']} ({suggestion['mib_name']})"
            }
            formatted_suggestions.append(formatted_suggestion)

        return jsonify({
            'success': True,
            'suggestions': formatted_suggestions
        })

    except Exception as e:
        logger.error(f"Error getting table suggestions: {e}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while getting suggestions',
            'details': str(e)
        }), 500


@oid_lookup_bp.route('/api/validate-indexes', methods=['POST'])
def api_validate_indexes():
    """
    AJAX API endpoint to validate index field input.

    Request JSON:
        {
            "table_name": "ifTable",
            "indexes": {
                "ifIndex": "1"
            }
        }

    Returns:
        JSON response with validation result and complete OID
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request data is required'
            }), 400

        table_name = data.get('table_name', '').strip()
        user_indexes = data.get('indexes', {})

        if not table_name:
            return jsonify({
                'success': False,
                'error': 'Table name is required'
            }), 400

        # Get device context
        device_name = g.device_name
        mib_service = g.mib_service

        # Initialize MibTableService
        from ..services.mib_table_service import MibTableService
        table_service = MibTableService(mib_service, g.device_service)

        # Get table structure first to find entry
        table_structure = table_service.get_table_structure(table_name, device_name)
        if not table_structure or not table_structure.get('entry_name'):
            return jsonify({
                'success': False,
                'error': f'Could not find entry information for table: {table_name}'
            }), 404

        # Extract index fields
        index_fields = table_service.extract_index_fields(table_structure['entry_name'], device_name)

        if not index_fields:
            return jsonify({
                'success': False,
                'error': 'No index fields found for this table'
            }), 404

        # Validate user input
        validation_result = table_service.validate_index_input(index_fields, user_indexes)

        # Build complete OID if validation is successful
        complete_oid = None
        if validation_result.is_valid and table_structure.get('table_oid'):
            try:
                # Get index values in correct order
                index_values = []
                for field in index_fields:
                    field_name = field.name
                    if field_name in validation_result.normalized_values:
                        index_values.append(validation_result.normalized_values[field_name])
                    elif not field.is_optional:
                        raise ValueError(f"Missing required index field: {field_name}")

                complete_oid = table_service.build_complete_oid(
                    table_structure['table_oid'],
                    index_values
                )

            except Exception as e:
                logger.warning(f"Error building complete OID: {e}")
                validation_result.errors.append(table_service.ValidationError(
                    field_name="oid_building",
                    error_message=f"Failed to build complete OID: {str(e)}",
                    provided_value=user_indexes
                ))
                validation_result.is_valid = False

        # Format response
        response_data = {
            'success': validation_result.is_valid,
            'is_valid': validation_result.is_valid,
            'errors': [
                {
                    'field': error.field_name,
                    'message': error.error_message,
                    'provided_value': error.provided_value,
                    'expected_type': error.expected_type
                }
                for error in validation_result.errors
            ],
            'warnings': validation_result.warnings or [],
            'complete_oid': complete_oid,
            'table_oid': table_structure.get('table_oid'),
            'entry_oid': table_structure.get('entry_oid')
        }

        # Add normalized values if validation succeeded
        if validation_result.is_valid:
            response_data['normalized_values'] = validation_result.normalized_values

            # Get all table columns with complete OIDs
            try:
                # Convert index values to list
                index_values_list = []
                for field in index_fields:
                    field_name = field.name
                    if field_name in validation_result.normalized_values:
                        index_values_list.append(str(validation_result.normalized_values[field_name]))

                # Get table columns with complete OIDs
                columns_with_oids = table_service.get_table_columns_with_oids(
                    table_name, device_name, index_values_list
                )

                response_data['table_columns'] = columns_with_oids

                # Format index display with clear separation
                index_display = {
                    'table_oid': table_structure.get('table_oid'),
                    'entry_oid': table_structure.get('entry_oid'),
                    'index_values': validation_result.normalized_values,
                    'index_display': f"{table_structure.get('entry_oid', '')}." + ".".join(index_values_list),
                    'complete_entry_oid': complete_oid,
                    'index_fields': [
                        {
                            'name': field.name,
                            'value': validation_result.normalized_values.get(field.name),
                            'type': field.type,
                            'display': f"{field.name} = {validation_result.normalized_values.get(field.name)}"
                        }
                        for field in index_fields
                    ]
                }
                response_data['index_display'] = index_display

            except Exception as e:
                logger.warning(f"Error getting table columns: {e}")
                response_data['table_columns'] = []
                response_data['index_display'] = None

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error validating indexes: {e}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while validating the indexes',
            'details': str(e)
        }), 500


# Helper functions

def _get_display_type(field_type: str) -> str:
    """
    Convert field type to display type for frontend input elements.

    Args:
        field_type: Raw field type from MIB

    Returns:
        Display type string (number, text, oid, etc.)
    """
    if not field_type:
        return 'text'

    type_lower = field_type.lower()

    if 'integer' in type_lower or 'int' in type_lower:
        return 'number'
    elif 'string' in type_lower or 'octetstring' in type_lower:
        return 'text'
    elif 'oid' in type_lower or 'object identifier' in type_lower:
        return 'oid'
    elif 'counter' in type_lower or 'gauge' in type_lower:
        return 'number'
    elif 'timeticks' in type_lower:
        return 'text'
    else:
        return 'text'


def _generate_placeholder(index_field: Dict[str, Any]) -> str:
    """
    Generate placeholder text for an index field input.

    Args:
        index_field: Index field information

    Returns:
        Placeholder string
    """
    field_name = index_field.get('name', '')
    field_type = index_field.get('type', '')
    description = index_field.get('description', '')

    # Use constraints to create specific placeholder
    constraints = index_field.get('constraints', {})

    if 'range' in constraints:
        range_info = constraints['range']
        if isinstance(range_info, (list, tuple)) and len(range_info) >= 2:
            return f"请输入 {field_name} ({range_info[0]}-{range_info[1]})"
        elif isinstance(range_info, dict):
            min_val = range_info.get('min')
            max_val = range_info.get('max')
            if min_val is not None and max_val is not None:
                return f"请输入 {field_name} ({min_val}-{max_val})"

    # Use type-specific placeholder
    if 'integer' in str(field_type).lower():
        return f"请输入 {field_name} (整数)"
    elif 'oid' in str(field_type).lower():
        return f"请输入 {field_name} (OID格式，如: 1.3.6.1.2.1)"
    else:
        return f"请输入 {field_name}"


# Error handlers
@oid_lookup_bp.app_errorhandler(404)
def not_found_error(error):
    """Handle 404 errors for OID lookup blueprint."""
    return jsonify({
        'success': False,
        'error': 'Resource not found'
    }), 404


@oid_lookup_bp.app_errorhandler(500)
def internal_error(error):
    """Handle 500 errors for OID lookup blueprint."""
    logger.error(f"Internal server error in OID lookup: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500