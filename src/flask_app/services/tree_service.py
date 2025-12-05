"""
Service for building and managing tree structures from MIB data.
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TreeService:
    """Service for building tree structures from MIB data."""

    def build_tree_structure(self, mib_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a hierarchical tree structure from flat MIB node data.

        Args:
            mib_data: MIB data dictionary with nodes

        Returns:
            Tree-structured data suitable for D3.js visualization
        """
        nodes = mib_data.get('nodes', {})
        if not nodes:
            return {'name': mib_data.get('name', 'Unknown'), 'children': []}

        # Create a mapping from node name to node data, filtering out TC nodes
        node_map = {}
        original_nodes = {}  # Store reference to original data
        for name, data in nodes.items():
            # Skip Textual Convention (TC) nodes - they shouldn't appear in the tree
            if data.get('class') == 'textualconvention':
                continue

            # Use display name for combined MIBs, otherwise use original name
            display_name = data.get('original_name', name)
            mib_origin = data.get('mib_origin', '')

            node_map[name] = {
                'name': display_name,
                'full_name': name,  # Keep the full name for uniqueness
                'oid': data.get('oid', ''),
                'description': data.get('description', ''),
                'syntax': data.get('syntax', ''),
                'access': data.get('access', ''),
                'status': data.get('status', ''),
                'module': mib_origin or data.get('module', mib_data.get('name', '')),
                'text_convention': data.get('text_convention', ''),
                'units': data.get('units', ''),
                'max_access': data.get('max_access', ''),
                'reference': data.get('reference', ''),
                'defval': data.get('defval', ''),
                'hint': data.get('hint', ''),
                'mib_origin': mib_origin,
                'children': []
            }
            original_nodes[name] = data  # Keep reference to original data

        # Build parent-child relationships based on OID hierarchy
        root_nodes = []
        processed_nodes = set()

        # First, sort nodes by OID length to process parents before children
        # Note: We need to filter out TC nodes here as well
        filtered_nodes = {name: data for name, data in nodes.items()
                         if data.get('class') != 'textualconvention'}

        sorted_nodes = sorted(
            filtered_nodes.items(),
            key=lambda x: len(x[1].get('oid', '').split('.')) if x[1].get('oid') else 0
        )

        for node_name, node_data in sorted_nodes:
            if node_name in processed_nodes:
                continue

            # Try to find parent by OID
            oid = node_data.get('oid', '')
            parent_node = self._find_parent_by_oid(oid, node_map) if oid else None

            if parent_node:
                # Add this node as child of parent
                parent_node['children'].append(node_map[node_name])
                processed_nodes.add(node_name)
            else:
                # No parent found, treat as root
                root_nodes.append(node_map[node_name])
                processed_nodes.add(node_name)

        # Process any remaining nodes
        for node_name in node_map:
            if node_name not in processed_nodes:
                root_nodes.append(node_map[node_name])

        # Build the tree structure
        tree_data = {
            'name': mib_data.get('name', 'Unknown MIB'),
            'description': mib_data.get('description', ''),
            'module': mib_data.get('name', ''),
            'oid': 'root',
            'children': root_nodes,
            'statistics': self._calculate_tree_statistics(node_map, root_nodes)
        }

        return tree_data

    def _build_subtree(self, node_name: str, node_map: Dict[str, Any], processed_nodes: set):
        """
        Recursively build subtree starting from given node.

        Args:
            node_name: Name of the root node for this subtree
            node_map: Mapping of all nodes
            processed_nodes: Set of already processed nodes (to avoid cycles)
        """
        if node_name in processed_nodes or node_name not in node_map:
            return

        processed_nodes.add(node_name)
        node = node_map[node_name]

        # Get children from the original data structure
        # This would be in the MibData nodes, not our node_map
        # So we need to get it differently
        original_node_data = self._get_original_node_data(node_name, node_map)
        if original_node_data:
            children_names = original_node_data.get('children', [])

            for child_name in children_names:
                if child_name in node_map and child_name not in processed_nodes:
                    child_node = node_map[child_name]
                    node['children'].append(child_node)
                    self._build_subtree(child_name, node_map, processed_nodes)

    def _get_original_node_data(self, node_name: str, node_map: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get the original node data structure that might contain children information.

        This is a helper method since we don't have direct access to the original
        nodes data structure in this service.
        """
        # In the actual implementation, this might be passed in or stored
        # For now, we'll return None and children will be built differently
        return None

    def build_breadth_first_tree(self, mib_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build tree structure using breadth-first approach.

        This alternative method organizes nodes by OID hierarchy.

        Args:
            mib_data: MIB data dictionary

        Returns:
            List of root nodes with their children
        """
        nodes = mib_data.get('nodes', {})
        if not nodes:
            return []

        # Filter out TC nodes first
        filtered_nodes = {name: data for name, data in nodes.items()
                         if data.get('class') != 'textualconvention'}

        # Sort nodes by OID length (shorter OIDs are likely closer to root)
        sorted_nodes = sorted(
            filtered_nodes.items(),
            key=lambda x: len(x[1].get('oid', '').split('.')) if x[1].get('oid') else 0
        )

        node_map = {}
        for name, data in sorted_nodes:
            node_map[name] = {
                'name': name,
                'oid': data.get('oid', ''),
                'description': data.get('description', ''),
                'syntax': data.get('syntax', ''),
                'access': data.get('access', ''),
                'status': data.get('status', ''),
                'module': data.get('module', mib_data.get('name', '')),
                'text_convention': data.get('text_convention', ''),
                'units': data.get('units', ''),
                'max_access': data.get('max_access', ''),
                'reference': data.get('reference', ''),
                'defval': data.get('defval', ''),
                'hint': data.get('hint', ''),
                'children': []
            }

        # Build relationships based on OID hierarchy
        root_nodes = []

        for node_name, node_data in sorted_nodes:
            node = node_map[node_name]
            oid = node_data.get('oid', '')

            if not oid:
                # No OID, treat as root
                root_nodes.append(node)
                continue

            # Try to find parent by OID
            parent_node = self._find_parent_by_oid(oid, node_map)

            if parent_node:
                parent_node['children'].append(node)
            else:
                # No parent found, treat as root
                root_nodes.append(node)

        return root_nodes

    def _find_parent_by_oid(self, child_oid: str, node_map: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find parent node based on OID hierarchy.

        Args:
            child_oid: OID of the child node
            node_map: Mapping of all nodes

        Returns:
            Parent node if found, None otherwise
        """
        child_parts = child_oid.split('.')
        if len(child_parts) <= 2:  # Need at least 2 parts to have a meaningful parent
            return None

        # Try to find a parent with OID that's exactly one level higher
        # For child like 1.3.6.1.4.1.2011.2.25.3.40.50.20, look for 1.3.6.1.4.1.2011.2.25.3.40.50
        parent_oid = '.'.join(child_parts[:-1])  # Remove last part

        # Look for exact OID match first
        for node in node_map.values():
            if node['oid'] == parent_oid:
                return node

        # If no exact match, try to find the closest parent by checking prefixes
        for i in range(len(child_parts) - 2, 0, -1):
            potential_parent_oid = '.'.join(child_parts[:i])

            for node in node_map.values():
                if node['oid'] == potential_parent_oid:
                    return node

        return None

    def _calculate_tree_statistics(self, node_map: Dict[str, Any], root_nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics about the tree structure.

        Args:
            node_map: All nodes in the tree
            root_nodes: Root nodes of the tree

        Returns:
            Statistics dictionary
        """
        total_nodes = len(node_map)
        root_count = len(root_nodes)

        # Calculate maximum depth
        max_depth = 0
        for root in root_nodes:
            depth = self._calculate_depth(root)
            max_depth = max(max_depth, depth)

        # Count leaf nodes
        leaf_count = sum(1 for node in node_map.values() if not node['children'])

        # Calculate average children per node
        total_children = sum(len(node['children']) for node in node_map.values())
        avg_children = total_children / total_nodes if total_nodes > 0 else 0

        return {
            'total_nodes': total_nodes,
            'root_nodes': root_count,
            'leaf_nodes': leaf_count,
            'max_depth': max_depth,
            'average_children': round(avg_children, 2),
            'branching_nodes': total_nodes - leaf_count
        }

    def _calculate_depth(self, node: Dict[str, Any], current_depth: int = 0) -> int:
        """
        Recursively calculate the maximum depth from a given node.

        Args:
            node: Node to calculate depth from
            current_depth: Current depth in the recursion

        Returns:
            Maximum depth from this node
        """
        if not node['children']:
            return current_depth + 1

        max_child_depth = 0
        for child in node['children']:
            child_depth = self._calculate_depth(child, current_depth + 1)
            max_child_depth = max(max_child_depth, child_depth)

        return max_child_depth

    def flatten_tree(self, node: Dict[str, Any], include_paths: bool = True) -> List[Dict[str, Any]]:
        """
        Flatten a tree structure into a list of nodes with optional path information.

        Args:
            node: Root node of the tree
            include_paths: Whether to include full OID paths for each node

        Returns:
            List of flattened node data
        """
        flat_list = []
        self._flatten_node(node, flat_list, path=[] if include_paths else None)
        return flat_list

    def _flatten_node(self, node: Dict[str, Any], flat_list: List[Dict[str, Any]], path: Optional[List[str]] = None):
        """
        Recursively flatten a node and its children.

        Args:
            node: Node to flatten
            flat_list: List to add flattened nodes to
            path: Current path for this node (if include_paths is True)
        """
        node_data = dict(node)

        if path is not None:
            current_path = path + [node['name']]
            node_data['path'] = current_path
            node_data['path_string'] = ' -> '.join(current_path)
        else:
            del node_data['children']  # Remove children from flattened version

        flat_list.append(node_data)

        # Process children
        for child in node.get('children', []):
            if path is not None:
                self._flatten_node(child, flat_list, current_path)
            else:
                self._flatten_node(child, flat_list, None)