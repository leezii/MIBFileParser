"""
MIB tree traversal and manipulation utilities.
"""

from typing import List, Optional, Dict, Generator, Tuple, Set
from collections import deque

from src.mib_parser.models import MibData, MibNode


class MibTree:
    """Utilities for traversing and manipulating MIB tree structures."""

    def __init__(self, mib_data: MibData):
        """
        Initialize MIB tree utilities.

        Args:
            mib_data: MibData object containing the MIB structure
        """
        self.mib_data = mib_data
        self._build_oid_cache()

    def _build_oid_cache(self) -> None:
        """Build a cache for fast OID lookups."""
        self._oid_cache = {node.oid: node for node in self.mib_data.nodes.values()}

    def find_node_by_oid(self, oid: str) -> Optional[MibNode]:
        """
        Find a node by its OID.

        Args:
            oid: OID string to search for

        Returns:
            MibNode if found, None otherwise
        """
        # Exact match
        if oid in self._oid_cache:
            return self._oid_cache[oid]

        # Partial match (check if any node starts with this OID)
        for node in self.mib_data.nodes.values():
            if node.oid.endswith(oid):
                return node

        return None

    def find_node_by_name(self, name: str) -> Optional[MibNode]:
        """
        Find a node by its name.

        Args:
            name: Node name to search for

        Returns:
            MibNode if found, None otherwise
        """
        return self.mib_data.get_node_by_name(name)

    def find_nodes_by_pattern(self, pattern: str, search_names: bool = True,
                            search_descriptions: bool = False) -> List[MibNode]:
        """
        Find nodes matching a pattern.

        Args:
            pattern: Pattern to match (supports wildcards)
            search_names: Whether to search in node names
            search_descriptions: Whether to search in descriptions

        Returns:
            List of matching MibNode objects
        """
        matching_nodes = []
        pattern_lower = pattern.lower()

        for node in self.mib_data.nodes.values():
            if search_names and pattern_lower in node.name.lower():
                matching_nodes.append(node)
                continue

            if search_descriptions and node.description and pattern_lower in node.description.lower():
                matching_nodes.append(node)

        return matching_nodes

    def get_path_to_root(self, node_name: str) -> List[MibNode]:
        """
        Get the path from a node to the root of the tree.

        Args:
            node_name: Starting node name

        Returns:
            List of nodes from the starting node to the root
        """
        path = []
        current_node = self.mib_data.get_node_by_name(node_name)

        while current_node:
            path.append(current_node)
            if current_node.parent_name:
                current_node = self.mib_data.get_node_by_name(current_node.parent_name)
            else:
                break

        return path  # Path is from node to root

    def get_path_from_root(self, node_name: str) -> List[MibNode]:
        """
        Get the path from the root to a node.

        Args:
            node_name: Target node name

        Returns:
            List of nodes from the root to the target node
        """
        path_to_root = self.get_path_to_root(node_name)
        return list(reversed(path_to_root))

    def get_subtree(self, root_node_name: str, include_root: bool = True) -> List[MibNode]:
        """
        Get all nodes in the subtree rooted at the specified node.

        Args:
            root_node_name: Root node of the subtree
            include_root: Whether to include the root node in results

        Returns:
            List of nodes in the subtree
        """
        root_node = self.mib_data.get_node_by_name(root_node_name)
        if not root_node:
            return []

        subtree_nodes = []
        if include_root:
            subtree_nodes.append(root_node)

        # Use BFS to get all descendants
        queue = deque([root_node_name])

        while queue:
            current_name = queue.popleft()
            children = self.mib_data.get_children(current_name)

            for child in children:
                subtree_nodes.append(child)
                queue.append(child.name)

        return subtree_nodes

    def traverse_breadth_first(self, start_node: Optional[str] = None) -> Generator[MibNode, None, None]:
        """
        Traverse the MIB tree in breadth-first order.

        Args:
            start_node: Starting node name (None for all root nodes)

        Yields:
            MibNode objects in BFS order
        """
        visited = set()

        if start_node:
            start = self.mib_data.get_node_by_name(start_node)
            if not start:
                return
            root_nodes = [start]
        else:
            root_nodes = self.mib_data.get_root_nodes()

        queue = deque(root_nodes)

        while queue:
            node = queue.popleft()
            if node.name in visited:
                continue

            visited.add(node.name)
            yield node

            # Add children to queue
            children = self.mib_data.get_children(node.name)
            queue.extend(children)

    def traverse_depth_first(self, start_node: Optional[str] = None) -> Generator[MibNode, None, None]:
        """
        Traverse the MIB tree in depth-first order.

        Args:
            start_node: Starting node name (None for all root nodes)

        Yields:
            MibNode objects in DFS order
        """
        visited = set()

        if start_node:
            start = self.mib_data.get_node_by_name(start_node)
            if not start:
                return
            root_nodes = [start]
        else:
            root_nodes = self.mib_data.get_root_nodes()

        stack = list(reversed(root_nodes))

        while stack:
            node = stack.pop()
            if node.name in visited:
                continue

            visited.add(node.name)
            yield node

            # Add children to stack (reverse order for correct DFS)
            children = self.mib_data.get_children(node.name)
            stack.extend(reversed(children))

    def get_tree_levels(self) -> Dict[int, List[MibNode]]:
        """
        Get nodes grouped by their depth in the tree.

        Returns:
            Dictionary mapping depth level to list of nodes at that level
        """
        levels = {}

        for root_node in self.mib_data.get_root_nodes():
            self._get_tree_levels_recursive(root_node, 0, levels)

        return levels

    def _get_tree_levels_recursive(self, node: MibNode, level: int, levels: Dict[int, List[MibNode]]) -> None:
        """Recursive helper to build tree levels."""
        if level not in levels:
            levels[level] = []
        levels[level].append(node)

        children = self.mib_data.get_children(node.name)
        for child in children:
            self._get_tree_levels_recursive(child, level + 1, levels)

    def find_common_ancestor(self, node_names: List[str]) -> Optional[MibNode]:
        """
        Find the common ancestor of multiple nodes.

        Args:
            node_names: List of node names

        Returns:
            Common ancestor node, or None if no common ancestor
        """
        if not node_names:
            return None

        # Get paths from root for all nodes
        paths = []
        for node_name in node_names:
            path = self.get_path_from_root(node_name)
            if not path:
                return None
            paths.append(path)

        # Find common prefix of all paths
        common_ancestor = None
        min_length = min(len(path) for path in paths)

        for i in range(min_length):
            first_node = paths[0][i]
            if all(path[i].name == first_node.name for path in paths):
                common_ancestor = first_node
            else:
                break

        return common_ancestor

    def get_oid_distance(self, node1_name: str, node2_name: str) -> Optional[int]:
        """
        Calculate the distance (number of edges) between two nodes.

        Args:
            node1_name: First node name
            node2_name: Second node name

        Returns:
            Distance in edges, or None if nodes are not connected
        """
        # Find common ancestor
        ancestor = self.find_common_ancestor([node1_name, node2_name])
        if not ancestor:
            return None

        # Get paths from ancestor to each node
        path1 = []
        path2 = []

        # Build path from ancestor to node1
        current = self.mib_data.get_node_by_name(node1_name)
        while current and current.name != ancestor.name:
            path1.append(current)
            current = self.mib_data.get_node_by_name(current.parent_name)

        # Build path from ancestor to node2
        current = self.mib_data.get_node_by_name(node2_name)
        while current and current.name != ancestor.name:
            path2.append(current)
            current = self.mib_data.get_node_by_name(current.parent_name)

        return len(path1) + len(path2)

    def get_node_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the MIB tree structure.

        Returns:
            Dictionary with tree statistics
        """
        stats = {
            "total_nodes": len(self.mib_data.nodes),
            "root_nodes": len(self.mib_data.get_root_nodes()),
            "max_depth": 0,
            "nodes_with_children": 0,
            "leaf_nodes": 0,
        }

        # Calculate max depth
        levels = self.get_tree_levels()
        if levels:
            stats["max_depth"] = max(levels.keys())

        # Count nodes with children and leaf nodes
        for node in self.mib_data.nodes.values():
            if node.children:
                stats["nodes_with_children"] += 1
            else:
                stats["leaf_nodes"] += 1

        return stats

    def validate_tree_structure(self) -> List[str]:
        """
        Validate the MIB tree structure for consistency.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        for node_name, node in self.mib_data.nodes.items():
            # Check if parent exists
            if node.parent_name and node.parent_name not in self.mib_data.nodes:
                errors.append(f"Node '{node_name}' references non-existent parent '{node.parent_name}'")

            # Check if children reference this node
            for child_name in node.children:
                if child_name not in self.mib_data.nodes:
                    errors.append(f"Node '{node_name}' references non-existent child '{child_name}'")
                else:
                    child = self.mib_data.nodes[child_name]
                    if child.parent_name != node_name:
                        errors.append(f"Inconsistent parent-child relationship: '{node_name}' -> '{child_name}'")

        return errors