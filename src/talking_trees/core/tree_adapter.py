"""TreeAdapter protocol and topology operations for dynamic tree modification."""

import logging
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

import py_trees
from py_trees import behaviour

logger = logging.getLogger(__name__)


@runtime_checkable
class TreeAdapter(Protocol):
    """Protocol for pre/post-tick tree modification hooks.

    Adapters can modify tree topology before each tick (e.g., disable
    subtrees when sensors go offline) and react to tick results.
    Lower priority values execute first.
    """

    priority: int

    def before_tick(self, tree: py_trees.trees.BehaviourTree, blackboard: dict[str, Any]) -> None:
        """Called before each tick. May modify tree topology."""
        ...

    def after_tick(
        self,
        tree: py_trees.trees.BehaviourTree,
        blackboard: dict[str, Any],
        root_status: py_trees.common.Status,
    ) -> None:
        """Called after each tick with the result."""
        ...


class TopologyManager:
    """Manages dynamic topology changes on a live py_trees tree.

    Supports disabling/enabling subtrees and hot-swapping branches
    while preserving the ability to restore original state.
    """

    def __init__(self, tree: py_trees.trees.BehaviourTree):
        self._tree = tree
        self._stashed: dict[UUID, tuple[behaviour.Behaviour, behaviour.Behaviour]] = {}
        # Maps node UUID -> (original_node, parent_node)

    def disable_subtree(self, node_id_or_name: UUID | str) -> None:
        """Replace a subtree with a Failure stub.

        The original subtree is stashed for later restoration.

        Args:
            node_id_or_name: UUID or name of the node to disable
        """
        node = self._find_node(node_id_or_name)
        if node is None:
            raise ValueError(f"Node not found: {node_id_or_name}")

        node_uuid = getattr(node, "_talkingtrees_uuid", None)
        parent = node.parent
        if parent is None:
            raise ValueError("Cannot disable root node")

        # Create stub
        stub = py_trees.behaviours.Failure(name=f"[disabled] {node.name}")
        if node_uuid:
            stub._talkingtrees_uuid = node_uuid

        # Stash original
        stash_key = node_uuid or id(node)
        self._stashed[stash_key] = (node, parent)

        # Replace in parent
        idx = parent.children.index(node)
        parent.remove_child(node)
        parent.insert_child(stub, idx)

        logger.info("Disabled subtree: %s", node.name)

    def enable_subtree(self, node_id: UUID) -> None:
        """Restore a previously disabled subtree.

        Args:
            node_id: UUID of the node to re-enable
        """
        if node_id not in self._stashed:
            raise ValueError(f"Node not stashed (not disabled): {node_id}")

        original, parent = self._stashed.pop(node_id)

        # Find and replace the stub
        for i, child in enumerate(parent.children):
            if getattr(child, "_talkingtrees_uuid", None) == node_id:
                parent.remove_child(child)
                parent.insert_child(original, i)
                break

        logger.info("Re-enabled subtree: %s", original.name)

    def swap_subtree(self, node_id_or_name: UUID | str, replacement: behaviour.Behaviour) -> None:
        """Hot-swap a subtree with a replacement.

        The original is stashed for later restoration via enable_subtree().

        Args:
            node_id_or_name: UUID or name of the node to replace
            replacement: New behaviour to insert
        """
        node = self._find_node(node_id_or_name)
        if node is None:
            raise ValueError(f"Node not found: {node_id_or_name}")

        node_uuid = getattr(node, "_talkingtrees_uuid", None)
        parent = node.parent
        if parent is None:
            raise ValueError("Cannot swap root node")

        # Stash original
        stash_key = node_uuid or id(node)
        self._stashed[stash_key] = (node, parent)

        # Tag replacement with UUID
        if node_uuid:
            replacement._talkingtrees_uuid = node_uuid

        # Replace
        idx = parent.children.index(node)
        parent.remove_child(node)
        parent.insert_child(replacement, idx)

        logger.info("Swapped subtree %s with %s", node.name, replacement.name)

    def get_disabled_subtrees(self) -> list[UUID]:
        """Get list of currently disabled/swapped subtree UUIDs."""
        return list(self._stashed.keys())

    def is_subtree_disabled(self, node_id: UUID) -> bool:
        """Check if a subtree is currently disabled/swapped."""
        return node_id in self._stashed

    def _find_node(self, node_id_or_name: UUID | str) -> behaviour.Behaviour | None:
        """Find a node in the tree by UUID or name.

        Args:
            node_id_or_name: UUID or string name of the node
        """
        for node in self._tree.root.iterate():
            if isinstance(node_id_or_name, UUID):
                if getattr(node, "_talkingtrees_uuid", None) == node_id_or_name:
                    return node
            elif node.name == node_id_or_name:
                return node
        # Also check root
        if isinstance(node_id_or_name, UUID):
            if getattr(self._tree.root, "_talkingtrees_uuid", None) == node_id_or_name:
                return self._tree.root
        elif self._tree.root.name == node_id_or_name:
            return self._tree.root
        return None
