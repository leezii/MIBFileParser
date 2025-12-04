"""
Data models for MIB parsing.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class MibNode:
    """Represents a single node in the MIB tree."""

    name: str
    oid: str
    description: Optional[str] = None
    syntax: Optional[str] = None
    access: Optional[str] = None
    status: Optional[str] = None
    parent_name: Optional[str] = None
    children: List[str] = field(default_factory=list)
    module: Optional[str] = None
    text_convention: Optional[str] = None
    units: Optional[str] = None
    max_access: Optional[str] = None
    reference: Optional[str] = None
    defval: Optional[Any] = None
    hint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            "name": self.name,
            "oid": self.oid,
            "description": self.description,
            "syntax": self.syntax,
            "access": self.access,
            "status": self.status,
            "parent_name": self.parent_name,
            "children": self.children,
            "module": self.module,
            "text_convention": self.text_convention,
            "units": self.units,
            "max_access": self.max_access,
            "reference": self.reference,
            "defval": self.defval,
            "hint": self.hint,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MibNode":
        """Create node from dictionary representation."""
        return cls(**data)


@dataclass
class MibData:
    """Container for all MIB data including metadata and nodes."""

    name: str
    nodes: Dict[str, MibNode] = field(default_factory=dict)
    imports: List[str] = field(default_factory=list)
    module_dependencies: List[str] = field(default_factory=list)
    description: Optional[str] = None
    last_updated: Optional[datetime] = None
    root_oids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert MIB data to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "imports": self.imports,
            "module_dependencies": self.module_dependencies,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "root_oids": self.root_oids,
            "nodes": {name: node.to_dict() for name, node in self.nodes.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MibData":
        """Create MIB data from dictionary representation."""
        nodes = {name: MibNode.from_dict(node_data)
                for name, node_data in data.get("nodes", {}).items()}

        last_updated = None
        if data.get("last_updated"):
            last_updated = datetime.fromisoformat(data["last_updated"])

        return cls(
            name=data["name"],
            nodes=nodes,
            imports=data.get("imports", []),
            module_dependencies=data.get("module_dependencies", []),
            description=data.get("description"),
            last_updated=last_updated,
            root_oids=data.get("root_oids", []),
        )

    def add_node(self, node: MibNode) -> None:
        """Add a node to the MIB data."""
        self.nodes[node.name] = node
        if node.parent_name and node.parent_name in self.nodes:
            parent = self.nodes[node.parent_name]
            if node.name not in parent.children:
                parent.children.append(node.name)

    def get_node_by_oid(self, oid: str) -> Optional[MibNode]:
        """Find a node by its OID."""
        for node in self.nodes.values():
            if node.oid == oid:
                return node
        return None

    def get_node_by_name(self, name: str) -> Optional[MibNode]:
        """Find a node by its name."""
        return self.nodes.get(name)

    def get_root_nodes(self) -> List[MibNode]:
        """Get all root nodes (nodes without parents)."""
        return [node for node in self.nodes.values() if node.parent_name is None]

    def get_children(self, node_name: str) -> List[MibNode]:
        """Get all direct children of a node."""
        if node_name not in self.nodes:
            return []
        node = self.nodes[node_name]
        return [self.nodes[child_name] for child_name in node.children if child_name in self.nodes]

    def get_descendants(self, node_name: str) -> List[MibNode]:
        """Get all descendants of a node (recursive)."""
        if node_name not in self.nodes:
            return []

        descendants = []
        children = self.get_children(node_name)
        for child in children:
            descendants.append(child)
            descendants.extend(self.get_descendants(child.name))

        return descendants