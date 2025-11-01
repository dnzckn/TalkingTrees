"""State snapshot capture using py_trees visitors."""

from datetime import datetime
from typing import Any
from uuid import UUID

from py_trees import behaviour, blackboard, trees, visitors

from py_forest.models.execution import (
    ExecutionSnapshot,
    NodeState,
    Status,
)


class SnapshotVisitor(visitors.VisitorBase):
    """Visitor that captures complete tree state into ExecutionSnapshot.

    Walks the tree and collects:
    - Node statuses and feedback messages
    - Current child markers
    - Tip node identification
    """

    def __init__(self):
        """Initialize the visitor."""
        super().__init__(full=True)  # Visit all nodes, not just traversed
        self.node_states: dict[str, NodeState] = {}
        self.tip_node_id: UUID | None = None

    def initialise(self) -> None:
        """Reset state before tree traversal."""
        self.node_states = {}
        self.tip_node_id = None

    def run(self, node: behaviour.Behaviour) -> None:
        """Visit a node and capture its state.

        Args:
            node: Node being visited
        """
        # Get the PyForest UUID for this node
        node_uuid = getattr(node, "_pyforest_uuid", None)
        if node_uuid is None:
            # Skip nodes without PyForest UUID
            return

        # Capture node state
        state = NodeState(
            status=Status(node.status.value),
            feedback_message=node.feedback_message,
        )

        # Check if this is a current child of its parent
        if hasattr(node, "parent") and node.parent is not None:
            if hasattr(node.parent, "current_child"):
                state.is_current_child = node.parent.current_child == node

        self.node_states[str(node_uuid)] = state

    def finalise(self) -> None:
        """Finalize after tree traversal."""
        pass


def capture_snapshot(
    execution_id: UUID,
    tree_id: UUID,
    tree_version: str,
    tree: trees.BehaviourTree,
    serializer: Any,  # TreeSerializer
    mode: str,
    is_running: bool,
) -> ExecutionSnapshot:
    """Capture a complete execution snapshot.

    Args:
        execution_id: Execution instance ID
        tree_id: Tree definition ID
        tree_version: Tree version
        tree: py_trees BehaviourTree instance
        serializer: TreeSerializer with UUID mappings
        mode: Execution mode
        is_running: Whether execution is active

    Returns:
        Complete execution snapshot
    """
    # Create visitor and visit tree
    visitor = SnapshotVisitor()
    visitor.initialise()

    # Visit all nodes
    for node in tree.root.iterate():
        node.visit(visitor)

    visitor.finalise()

    # Get tip node
    tip = tree.tip()
    tip_node_id = None
    if tip is not None:
        tip_uuid = serializer.get_node_uuid(tip)
        if tip_uuid:
            tip_node_id = tip_uuid
            # Mark tip in node states
            tip_str = str(tip_uuid)
            if tip_str in visitor.node_states:
                visitor.node_states[tip_str].is_tip = True

    # Capture blackboard state
    bb_storage = {}
    bb_metadata = {}

    # Get all blackboard keys and values
    for key in blackboard.Blackboard.keys():
        try:
            value = blackboard.Blackboard.get(key)
            bb_storage[key] = value
        except KeyError:
            pass

        # Get metadata (readers, writers)
        if key in blackboard.Blackboard.metadata:
            metadata = blackboard.Blackboard.metadata[key]
            bb_metadata[key] = {
                "readers": [str(uid) for uid in metadata.read],
                "writers": [str(uid) for uid in metadata.write],
                "exclusive": [str(uid) for uid in metadata.exclusive],
            }

    # Create snapshot
    snapshot = ExecutionSnapshot(
        execution_id=execution_id,
        tree_id=tree_id,
        tree_version=tree_version,
        tick_count=tree.count,
        root_status=Status(tree.root.status.value),
        tip_node_id=tip_node_id,
        node_states=visitor.node_states,
        blackboard=bb_storage,
        blackboard_metadata=bb_metadata,
        timestamp=datetime.utcnow(),
        mode=mode,
        is_running=is_running,
    )

    return snapshot
