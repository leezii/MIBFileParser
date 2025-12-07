"""
Service for handling MIB table OID lookups and index field extraction.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TableMatchResult:
    """Result of a table lookup operation."""
    table_name: str
    table_oid: str
    entry_name: Optional[str] = None
    entry_oid: Optional[str] = None
    match_type: str = "exact"  # exact, partial, parent
    confidence: float = 1.0
    mib_name: Optional[str] = None
    description: Optional[str] = None


@dataclass
class IndexFieldInfo:
    """Enhanced information about an index field."""
    name: str
    type: Optional[str] = None
    syntax: Optional[str] = None
    description: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None
    is_optional: bool = False
    display_hint: Optional[str] = None
    validation_pattern: Optional[str] = None


@dataclass
class ValidationError:
    """Validation error for index input."""
    field_name: str
    error_message: str
    provided_value: Any
    expected_type: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of index input validation."""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[str] = None
    normalized_values: Dict[str, Any] = None


class MibTableService:
    """
    Service for processing MIB table OID lookups and index field extraction.

    This service provides functionality to:
    - Find tables by OID with device-aware lookup
    - Extract and analyze table index fields
    - Validate user input against index constraints
    - Build complete OIDs from index values
    - Provide suggestions for table names
    """

    def __init__(self, mib_service, device_service=None):
        """
        Initialize MIB table service.

        Args:
            mib_service: An instance of MibService for accessing MIB data
            device_service: Optional DeviceService for device context
        """
        self.mib_service = mib_service
        self.device_service = device_service
        self._oid_cache = {}  # Cache for OID lookups
        self._table_structure_cache = {}  # Cache for table structures

        logger.info(f"Initialized MibTableService with device_type: {mib_service.device_type}")

    def find_table_by_oid(self, oid: str, device_type: str = None) -> Optional[TableMatchResult]:
        """
        Find a table that matches the given OID.

        This method supports various matching strategies:
        - Exact OID match for table nodes
        - Partial OID match (find parent table)
        - Entry OID match (find table from entry)

        Args:
            oid: The OID to search for
            device_type: Optional device type to limit search scope

        Returns:
            TableMatchResult if found, None otherwise

        Raises:
            ValueError: If OID format is invalid
        """
        if not oid or not isinstance(oid, str):
            raise ValueError("OID must be a non-empty string")

        # Normalize OID format
        oid = oid.strip()
        if not oid:
            raise ValueError("OID must be a non-empty string")

        if not re.match(r'^[\d\.]+$', oid):
            # Remove any non-numeric characters (except dots)
            cleaned_oid = re.sub(r'[^\d\.]', '', oid)
            if cleaned_oid != oid:
                logger.warning(f"OID format cleaned from '{oid}' to '{cleaned_oid}'")
                oid = cleaned_oid

        if not oid:
            raise ValueError("Invalid OID format")

        device_type = device_type or self.mib_service.device_type

        # Check cache first
        cache_key = f"{oid}:{device_type}"
        if cache_key in self._oid_cache:
            return self._oid_cache[cache_key]

        logger.debug(f"Searching for table matching OID: {oid} (device: {device_type})")

        try:
            # Strategy 1: Exact OID match - look for table nodes
            result = self._find_exact_table_match(oid, device_type)
            if result:
                self._oid_cache[cache_key] = result
                return result

            # Strategy 2: Entry OID match - check if OID is an entry and find its table
            result = self._find_table_from_entry(oid, device_type)
            if result:
                self._oid_cache[cache_key] = result
                return result

            # Strategy 3: Smart search - look for tables within 2 levels up or down (priority: down first)
            result = self._find_nearby_tables(oid, device_type)
            if result:
                self._oid_cache[cache_key] = result
                return result

            # Strategy 4: Partial OID match - find parent table by walking up the OID tree
            result = self._find_parent_table(oid, device_type)
            if result:
                self._oid_cache[cache_key] = result
                return result

            logger.info(f"No table found for OID: {oid}")
            return None

        except Exception as e:
            logger.error(f"Error finding table for OID {oid}: {e}")
            return None

    def get_table_structure(self, table_name: str, device_type: str = None) -> Optional[Dict[str, Any]]:
        """
        Get detailed structure information for a table.

        Args:
            table_name: Name of the table
            device_type: Optional device type for context

        Returns:
            Dictionary containing table structure information or None if not found
        """
        if not table_name:
            return None

        device_type = device_type or self.mib_service.device_type
        cache_key = f"{table_name}:{device_type}"

        # Check cache
        if cache_key in self._table_structure_cache:
            return self._table_structure_cache[cache_key]

        logger.debug(f"Getting table structure for: {table_name} (device: {device_type})")

        try:
            # Find the table node
            table_result = self._find_table_by_name(table_name, device_type)
            if not table_result:
                logger.warning(f"Table not found: {table_name}")
                return None

            # Get MIB data
            mib_data = self.mib_service.get_mib_data(table_result.mib_name)
            if not mib_data:
                logger.error(f"Could not load MIB data for: {table_result.mib_name}")
                return None

            # Build table structure
            structure = self._build_table_structure(table_result, mib_data)

            # Cache the result
            self._table_structure_cache[cache_key] = structure

            return structure

        except Exception as e:
            logger.error(f"Error getting table structure for {table_name}: {e}")
            return None

    def extract_index_fields(self, entry_name: str, device_type: str = None) -> List[IndexFieldInfo]:
        """
        Extract index fields from a table entry.

        Args:
            entry_name: Name of the table entry
            device_type: Optional device type for context

        Returns:
            List of IndexFieldInfo objects

        Raises:
            ValueError: If entry_name is invalid
        """
        if not entry_name:
            raise ValueError("Entry name cannot be empty")

        device_type = device_type or self.mib_service.device_type
        logger.debug(f"Extracting index fields for entry: {entry_name} (device: {device_type})")

        try:
            # Find the entry node
            entry_result = self._find_entry_by_name(entry_name, device_type)
            if not entry_result:
                logger.warning(f"Entry not found: {entry_name}")
                return []

            # Get MIB data
            mib_data = self.mib_service.get_mib_data(entry_result.mib_name)
            if not mib_data:
                logger.error(f"Could not load MIB data for: {entry_result.mib_name}")
                return []

            # Get the entry node from MIB data
            if 'nodes' not in mib_data:
                logger.error(f"Invalid MIB data structure for {entry_result.mib_name}: missing 'nodes' key")
                return []
            entry_node = mib_data['nodes'].get(entry_name)
            if not entry_node:
                logger.error(f"Entry node not found in MIB data: {entry_name}")
                return []

            # Extract index fields from entry
            index_fields = []
            if 'index_fields' in entry_node and entry_node['index_fields']:
                for idx_field in entry_node['index_fields']:
                    field_info = self._create_index_field_info(idx_field, mib_data)
                    index_fields.append(field_info)
            else:
                logger.info(f"No index fields found for entry: {entry_name}")

            return index_fields

        except Exception as e:
            logger.error(f"Error extracting index fields for {entry_name}: {e}")
            return []

    def validate_index_input(self, index_fields: List[IndexFieldInfo], user_input: Dict[str, Any]) -> ValidationResult:
        """
        Validate user input against index field constraints.

        Args:
            index_fields: List of index fields to validate against
            user_input: Dictionary of user-provided values

        Returns:
            ValidationResult with validation details
        """
        if not index_fields:
            return ValidationResult(is_valid=True, errors=[], warnings=["No index fields to validate"])

        errors = []
        warnings = []
        normalized_values = {}

        logger.debug(f"Validating index input against {len(index_fields)} fields")

        try:
            # Check for missing required fields
            provided_fields = set(user_input.keys())
            required_fields = {field.name for field in index_fields if not field.is_optional}

            missing_fields = required_fields - provided_fields
            for field_name in missing_fields:
                errors.append(ValidationError(
                    field_name=field_name,
                    error_message="Required field is missing",
                    provided_value=None,
                    expected_type="Required"
                ))

            # Validate each provided field
            for field in index_fields:
                field_name = field.name
                if field_name not in user_input:
                    if field.is_optional:
                        continue
                    # Missing required field already handled above
                    continue

                value = user_input[field_name]

                # Type validation
                validation_result = self._validate_field_type(field, value)
                if not validation_result['is_valid']:
                    errors.append(ValidationError(
                        field_name=field_name,
                        error_message=validation_result['error'],
                        provided_value=value,
                        expected_type=field.type
                    ))
                else:
                    # Normalized value for OID building
                    normalized_values[field_name] = validation_result['normalized_value']

                # Pattern validation if specified
                if field.validation_pattern and value is not None:
                    if not re.match(field.validation_pattern, str(value)):
                        errors.append(ValidationError(
                            field_name=field_name,
                            error_message=f"Value does not match required pattern: {field.validation_pattern}",
                            provided_value=value,
                            expected_type=f"Pattern: {field.validation_pattern}"
                        ))

            # Check for unexpected fields
            unexpected_fields = provided_fields - {field.name for field in index_fields}
            for field_name in unexpected_fields:
                warnings.append(f"Unexpected field provided: {field_name}")

            is_valid = len(errors) == 0
            result = ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings if warnings else [],
                normalized_values=normalized_values if is_valid else {}
            )

            logger.debug(f"Validation result: valid={is_valid}, errors={len(errors)}, warnings={len(warnings)}")
            return result

        except Exception as e:
            logger.error(f"Error during index input validation: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError(
                    field_name="validation",
                    error_message=f"Validation error: {str(e)}",
                    provided_value=user_input
                )],
                warnings=[]
            )

    def get_table_suggestions(self, query: str, device_type: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get table name suggestions for autocomplete.

        Args:
            query: Partial query string
            device_type: Optional device type for context
            limit: Maximum number of suggestions to return

        Returns:
            List of suggestion dictionaries
        """
        if not query:
            return []

        device_type = device_type or self.mib_service.device_type
        query_lower = query.lower()
        suggestions = []

        logger.debug(f"Getting table suggestions for query: '{query}' (device: {device_type})")

        try:
            # Search through all MIBs
            mibs = self.mib_service.list_mibs()
            for mib_info in mibs:
                mib_name = mib_info['name']
                mib_data = self.mib_service.get_mib_data(mib_name)

                if not mib_data:
                    continue

                # Look for table nodes
                for node_name, node_data in mib_data['nodes'].items():
                    if node_data.get('is_table', False):
                        # Check if node name matches query
                        if query_lower in node_name.lower():
                            suggestion = {
                                'name': node_name,
                                'mib_name': mib_name,
                                'description': node_data.get('description', ''),
                                'oid': node_data.get('oid', ''),
                                'match_score': self._calculate_match_score(node_name, query)
                            }
                            suggestions.append(suggestion)

            # Sort by match score and limit results
            suggestions.sort(key=lambda x: x['match_score'], reverse=True)
            return suggestions[:limit]

        except Exception as e:
            logger.error(f"Error getting table suggestions: {e}")
            return []

    def format_index_fields_for_display(self, index_fields: List[IndexFieldInfo]) -> List[Dict[str, Any]]:
        """
        Format index fields for frontend display.

        Args:
            index_fields: List of index field information

        Returns:
            List of display-ready dictionaries
        """
        display_fields = []

        for field in index_fields:
            display_field = {
                'name': field.name,
                'label': self._format_field_label(field.name),
                'type': field.type or 'Unknown',
                'description': field.description or '',
                'syntax': field.syntax or '',
                'is_required': not field.is_optional,
                'display_hint': field.display_hint or self._generate_display_hint(field),
                'validation_pattern': field.validation_pattern,
                'constraints': field.constraints or {}
            }
            display_fields.append(display_field)

        return display_fields

    def build_complete_oid(self, table_oid: str, index_values: List[Union[str, int]]) -> str:
        """
        Build a complete OID from table OID and index values.

        Args:
            table_oid: The base OID of the table
            index_values: List of index values

        Returns:
            Complete OID string

        Raises:
            ValueError: If inputs are invalid
        """
        if not table_oid:
            raise ValueError("Table OID cannot be empty")

        if not index_values:
            return table_oid

        try:
            # Build OID components
            oid_parts = [table_oid.rstrip('.')]

            for value in index_values:
                if value is None:
                    raise ValueError("Index value cannot be None")

                # Convert to appropriate OID format
                if isinstance(value, int):
                    oid_parts.append(str(value))
                else:
                    # Handle string values - convert to numeric if possible
                    str_value = str(value)
                    if str_value.isdigit():
                        oid_parts.append(str_value)
                    else:
                        # For non-numeric strings, convert each character to ASCII
                        ascii_parts = [str(ord(c)) for c in str_value]
                        oid_parts.extend(ascii_parts)

            # Join with dots and ensure no trailing dot
            complete_oid = '.'.join(oid_parts).rstrip('.')

            logger.debug(f"Built complete OID: {table_oid} + {index_values} = {complete_oid}")
            return complete_oid

        except Exception as e:
            logger.error(f"Error building complete OID: {e}")
            raise ValueError(f"Failed to build OID: {str(e)}")

    def clear_cache(self):
        """Clear all internal caches."""
        self._oid_cache.clear()
        self._table_structure_cache.clear()
        logger.info("MibTableService caches cleared")

    # Private helper methods

    def _find_exact_table_match(self, oid: str, device_type: str) -> Optional[TableMatchResult]:
        """Find exact table OID match."""
        # Search through all MIBs for table nodes with matching OID
        mibs = self.mib_service.list_mibs()

        for mib_info in mibs:
            mib_data = self.mib_service.get_mib_data(mib_info['name'])
            if not mib_data or 'nodes' not in mib_data:
                continue

            for node_name, node_data in mib_data['nodes'].items():
                if (node_data.get('is_table', False) and
                    node_data.get('oid') == oid):
                    return TableMatchResult(
                        table_name=node_name,
                        table_oid=oid,
                        match_type="exact",
                        confidence=1.0,
                        mib_name=mib_info['name'],
                        description=node_data.get('description')
                    )

        return None

    def _find_table_from_entry(self, oid: str, device_type: str) -> Optional[TableMatchResult]:
        """Find table from entry OID."""
        # Look for entry nodes and then find their associated table
        mibs = self.mib_service.list_mibs()

        for mib_info in mibs:
            mib_data = self.mib_service.get_mib_data(mib_info['name'])
            if not mib_data or 'nodes' not in mib_data:
                continue

            for node_name, node_data in mib_data['nodes'].items():
                if (node_data.get('is_entry', False) and
                    node_data.get('oid') == oid):
                    # Found the entry, now find its table
                    table_name = node_data.get('table_name')
                    if table_name and table_name in mib_data['nodes']:
                        table_data = mib_data['nodes'][table_name]
                        return TableMatchResult(
                            table_name=table_name,
                            table_oid=table_data.get('oid', ''),
                            entry_name=node_name,
                            entry_oid=oid,
                            match_type="entry",
                            confidence=0.9,
                            mib_name=mib_info['name'],
                            description=table_data.get('description')
                        )

        return None

    def _find_parent_table(self, oid: str, device_type: str) -> Optional[TableMatchResult]:
        """Find parent table by walking up OID hierarchy."""
        oid_parts = oid.split('.')

        # Try removing trailing parts to find parent table
        for i in range(len(oid_parts) - 1, 0, -1):
            parent_oid = '.'.join(oid_parts[:i])
            result = self._find_exact_table_match(parent_oid, device_type)
            if result:
                result.match_type = "parent"
                result.confidence = 0.7 - (len(oid_parts) - i) * 0.1
                return result

        return None

    def _find_table_by_name(self, table_name: str, device_type: str) -> Optional[TableMatchResult]:
        """Find table by name."""
        mibs = self.mib_service.list_mibs()

        for mib_info in mibs:
            mib_data = self.mib_service.get_mib_data(mib_info['name'])
            if not mib_data:
                continue

            if table_name in mib_data['nodes']:
                node_data = mib_data['nodes'][table_name]
                if node_data.get('is_table', False):
                    return TableMatchResult(
                        table_name=table_name,
                        table_oid=node_data.get('oid', ''),
                        match_type="name",
                        confidence=1.0,
                        mib_name=mib_info['name'],
                        description=node_data.get('description')
                    )

        return None

    def _find_entry_by_name(self, entry_name: str, device_type: str) -> Optional[TableMatchResult]:
        """Find entry by name."""
        mibs = self.mib_service.list_mibs()

        for mib_info in mibs:
            mib_data = self.mib_service.get_mib_data(mib_info['name'])
            if not mib_data:
                continue

            if entry_name in mib_data['nodes']:
                node_data = mib_data['nodes'][entry_name]
                if node_data.get('is_entry', False):
                    return TableMatchResult(
                        table_name=node_data.get('table_name', ''),
                        table_oid='',
                        entry_name=entry_name,
                        entry_oid=node_data.get('oid', ''),
                        match_type="name",
                        confidence=1.0,
                        mib_name=mib_info['name'],
                        description=node_data.get('description')
                    )

        return None

    def _build_table_structure(self, table_result: TableMatchResult, mib_data: Dict) -> Dict[str, Any]:
        """Build detailed table structure information."""
        structure = {
            'table_name': table_result.table_name,
            'table_oid': table_result.table_oid,
            'mib_name': table_result.mib_name,
            'description': table_result.description,
            'entry_name': None,
            'entry_oid': None,
            'index_fields': [],
            'columns': [],
            'row_count': None  # Could be populated with actual data if available
        }

        # Find the entry and extract information
        table_node = mib_data['nodes'][table_result.table_name]

        # Look for entries in this table
        for node_name, node_data in mib_data['nodes'].items():
            if (node_data.get('is_entry', False) and
                node_data.get('table_name') == table_result.table_name):

                structure['entry_name'] = node_name
                structure['entry_oid'] = node_data.get('oid', '')

                # Extract index fields
                if 'index_fields' in node_data:
                    for idx_field in node_data['index_fields']:
                        field_info = self._create_index_field_info(idx_field, mib_data)
                        structure['index_fields'].append(field_info.__dict__)

        # Find column definitions (non-index fields in entries)
        for node_name, node_data in mib_data['nodes'].items():
            # Check if node is a child of the entry (by OID or parent relationship)
            is_column = False
            if structure['entry_oid']:
                # Check if node OID starts with entry OID and has more components
                node_oid = node_data.get('oid', '')
                if node_oid and (node_oid.startswith(structure['entry_oid'] + '.') or node_oid == structure['entry_oid']):
                    # Exclude the entry itself and other entries/tables
                    if not node_data.get('is_entry', False) and not node_data.get('is_table', False):
                        is_column = True

            # Alternative check using parent relationship
            if not is_column and node_data.get('parent') == structure['entry_name']:
                is_column = True

            if is_column:
                # Extract type information from syntax or node type
                column_type = node_data.get('type') or self._extract_type_from_syntax(node_data.get('syntax', {}))

                column = {
                    'name': node_name,
                    'oid': node_data.get('oid', ''),
                    'syntax': str(node_data.get('syntax', {})),
                    'description': node_data.get('description', ''),
                    'access': node_data.get('access', 'read-only') or node_data.get('max_access', 'read-only'),
                    'type': column_type
                }
                structure['columns'].append(column)

        return structure

    def _create_index_field_info(self, idx_field_data: Dict, mib_data: Dict) -> IndexFieldInfo:
        """Create IndexFieldInfo from raw data."""
        field_name = idx_field_data.get('name', '')

        # Look up field definition in MIB data
        field_node = mib_data['nodes'].get(field_name, {})

        return IndexFieldInfo(
            name=field_name,
            type=idx_field_data.get('type') or self._extract_type_from_syntax(field_node.get('syntax', {})),
            syntax=idx_field_data.get('syntax') or str(field_node.get('syntax', '')),
            description=field_node.get('description', ''),
            constraints=self._extract_constraints(field_node.get('syntax', {})),
            display_hint=self._extract_display_hint(field_node),
            validation_pattern=self._generate_validation_pattern(field_node)
        )

    def _validate_field_type(self, field: IndexFieldInfo, value: Any) -> Dict[str, Any]:
        """Validate a field value against its type."""
        try:
            if value is None and field.is_optional:
                return {'is_valid': True, 'normalized_value': None}

            if field.type:
                field_type_lower = field.type.lower()

                if 'integer' in field_type_lower or 'int' in field_type_lower:
                    if isinstance(value, str) and value.isdigit():
                        normalized_value = int(value)
                        return {'is_valid': True, 'normalized_value': normalized_value}
                    elif isinstance(value, int):
                        return {'is_valid': True, 'normalized_value': value}
                    else:
                        return {
                            'is_valid': False,
                            'error': f'Expected integer value, got {type(value).__name__}'
                        }

                elif 'string' in field_type_lower or 'octetstring' in field_type_lower:
                    normalized_value = str(value)
                    return {'is_valid': True, 'normalized_value': normalized_value}

                elif 'oid' in field_type_lower:
                    # Validate OID format
                    if isinstance(value, str) and re.match(r'^[\d\.]+$', value):
                        return {'is_valid': True, 'normalized_value': value}
                    else:
                        return {
                            'is_valid': False,
                            'error': f'Expected OID format (numeric dots), got {value}'
                        }

            # Default validation - accept as string
            return {'is_valid': True, 'normalized_value': str(value)}

        except Exception as e:
            return {
                'is_valid': False,
                'error': f'Validation error: {str(e)}'
            }

    def _calculate_match_score(self, name: str, query: str) -> float:
        """Calculate match score for suggestions."""
        name_lower = name.lower()
        query_lower = query.lower()

        # Exact match gets highest score
        if name_lower == query_lower:
            return 1.0

        # Starts with query gets high score
        if name_lower.startswith(query_lower):
            return 0.9

        # Contains query gets medium score
        if query_lower in name_lower:
            return 0.7

        # Partial matches get lower scores based on character similarity
        score = 0.0
        for i, char in enumerate(query_lower):
            if i < len(name_lower) and name_lower[i] == char:
                score += 0.1

        return min(score, 0.5)

    def _format_field_label(self, field_name: str) -> str:
        """Format field name for display."""
        # Convert camelCase or snake_case to Title Case
        label = re.sub(r'([A-Z])', r' \1', field_name)
        label = re.sub(r'[_-]+', ' ', label)
        return label.strip().title()

    def _generate_display_hint(self, field: IndexFieldInfo) -> str:
        """Generate display hint for field."""
        if field.type:
            type_lower = field.type.lower()
            if 'integer' in type_lower:
                return "Enter a whole number (e.g., 1, 42, 100)"
            elif 'string' in type_lower:
                return "Enter text value"
            elif 'oid' in type_lower or 'object identifier' in type_lower:
                return "Enter OID in numeric format (e.g., 1.3.6.1.2.1)"

        return "Enter value"

    def _extract_type_from_syntax(self, syntax: Dict) -> str:
        """Extract type from syntax dictionary."""
        if syntax is None:
            return "Unknown"
        if isinstance(syntax, dict):
            return syntax.get('type', str(syntax))
        return str(syntax) or "Unknown"

    def _extract_constraints(self, syntax: Dict) -> Dict[str, Any]:
        """Extract constraints from syntax."""
        constraints = {}
        if isinstance(syntax, dict):
            for key in ['range', 'size', 'enumeration']:
                if key in syntax:
                    constraints[key] = syntax[key]
        return constraints

    def _extract_display_hint(self, field_node: Dict) -> Optional[str]:
        """Extract display hint from field node."""
        # Look for common display hint patterns
        description = field_node.get('description', '') or ''
        if description:
            description = description.lower()
        if 'port' in description:
            return "Enter port number (1-65535)"
        elif 'ip' in description or 'address' in description:
            return "Enter IP address (e.g., 192.168.1.1)"
        return None

    def _generate_validation_pattern(self, field_node: Dict) -> Optional[str]:
        """Generate validation pattern for field."""
        # This could be enhanced with more sophisticated pattern generation
        field_type = self._extract_type_from_syntax(field_node.get('syntax', {}))

        if field_type and 'integer' in field_type.lower():
            return r'^\d+$'
        elif field_type and 'oid' in field_type.lower():
            return r'^[\d\.]+$'

    def _find_nearby_tables(self, oid: str, device_type: str) -> Optional[TableMatchResult]:
        """
        Smart search for tables within 2 levels up or down from the given OID.
        Priority: downward search first, then upward search.

        Args:
            oid: The OID to search around
            device_type: Device type for context

        Returns:
            TableMatchResult if a nearby table is found, None otherwise
        """
        logger.debug(f"Starting smart search for tables near OID: {oid}")

        try:
            # Convert OID to list of integers for easier manipulation
            oid_parts = [int(x) for x in oid.split('.') if x.isdigit()]

            # Strategy 3a: Search downward (add 1-2 levels)
            downward_results = self._search_downward(oid_parts, device_type)
            if downward_results:
                logger.info(f"Found table downward from {oid}: {downward_results.table_name}")
                return downward_results

            # Strategy 3b: Search upward (remove 1-2 levels)
            upward_results = self._search_upward(oid_parts, device_type)
            if upward_results:
                logger.info(f"Found table upward from {oid}: {upward_results.table_name}")
                return upward_results

            logger.debug(f"No nearby tables found for OID: {oid}")
            return None

        except Exception as e:
            logger.error(f"Error in smart search for OID {oid}: {e}")
            return None

    def _search_downward(self, oid_parts: List[int], device_type: str) -> Optional[TableMatchResult]:
        """Search for tables by adding 1-2 levels to the OID."""

        # Level 1: Add .1, .2, ..., .9
        for i in range(1, 10):
            test_oid = '.'.join(map(str, oid_parts + [i]))
            result = self._find_exact_table_match(test_oid, device_type)
            if result:
                result.match_type = "downward_1"
                result.confidence = 0.9
                return result

        # Level 2: Add .10, .20, ..., .90 (common table pattern)
        for i in range(1, 10):
            test_oid = '.'.join(map(str, oid_parts + [i * 10]))
            result = self._find_exact_table_match(test_oid, device_type)
            if result:
                result.match_type = "downward_2"
                result.confidence = 0.8
                return result

        return None

    def get_table_columns_with_oids(self, table_name: str, device_type: str = None, index_values: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get all table columns with their complete OIDs including index values.

        Args:
            table_name: Name of the table
            device_type: Device type for context
            index_values: List of index values to build complete OIDs

        Returns:
            List of dictionaries with column information and complete OIDs
        """
        table_structure = self.get_table_structure(table_name, device_type)
        if not table_structure:
            return []

        columns = table_structure.get('columns', [])
        if not columns:
            return []

        # If no index values provided, return column info without complete OIDs
        if not index_values:
            return [
                {
                    'name': col['name'],
                    'oid': col['oid'],
                    'syntax': col.get('syntax', ''),
                    'access': col.get('access', ''),
                    'description': col.get('description', ''),
                    'type': col.get('type', 'Unknown'),
                    'is_index': False
                }
                for col in columns
            ]

        # Build complete OIDs with index values
        complete_oids = []
        for col in columns:
            col_oid = col['oid']
            complete_oid = self.build_complete_oid(col_oid, index_values)

            complete_oids.append({
                'name': col['name'],
                'oid': col_oid,
                'complete_oid': complete_oid,
                'syntax': col.get('syntax', ''),
                'access': col.get('access', ''),
                'description': col.get('description', ''),
                'type': col.get('type', 'Unknown'),
                'is_index': False
            })

        return complete_oids

    def _search_upward(self, oid_parts: List[int], device_type: str) -> Optional[TableMatchResult]:
        """Search for tables by removing 1-2 levels from the OID."""

        # Level 1: Remove last level
        if len(oid_parts) > 1:
            test_oid = '.'.join(map(str, oid_parts[:-1]))
            result = self._find_exact_table_match(test_oid, device_type)
            if result:
                result.match_type = "upward_1"
                result.confidence = 0.7
                return result

        # Level 2: Remove last 2 levels
        if len(oid_parts) > 2:
            test_oid = '.'.join(map(str, oid_parts[:-2]))
            result = self._find_exact_table_match(test_oid, device_type)
            if result:
                result.match_type = "upward_2"
                result.confidence = 0.6
                return result

        return None