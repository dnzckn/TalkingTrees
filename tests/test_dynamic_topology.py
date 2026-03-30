"""Tests for WP4: Dynamic Topology / TreeAdapter."""

from uuid import uuid4

import py_trees

from talking_trees.core.serializer import TreeSerializer
from talking_trees.core.tree_adapter import TopologyManager, TreeAdapter
from talking_trees.models.tree import (
    TreeDefinition,
    TreeMetadata,
    TreeNodeDefinition,
    TreeStatus,
)


def _make_tree_and_deserialize(root_def, subtrees=None):
    """Helper: create tree def, deserialize to py_trees, return both."""
    tree_def = TreeDefinition(
        tree_id=uuid4(),
        metadata=TreeMetadata(name="Test", version="1.0.0", status=TreeStatus.DRAFT),
        root=root_def,
        subtrees=subtrees or {},
    )
    serializer = TreeSerializer()
    py_tree = serializer.deserialize(tree_def)
    py_tree.setup()
    return tree_def, py_tree, serializer


def test_disable_enable_subtree():
    """Disabling a subtree replaces it with Failure, enabling restores it."""
    root_def = TreeNodeDefinition(
        node_type="Sequence", name="root",
        children=[
            TreeNodeDefinition(node_type="Success", name="step1"),
            TreeNodeDefinition(node_type="Success", name="step2"),
        ],
    )
    tree_def, py_tree, serializer = _make_tree_and_deserialize(root_def)

    topo = TopologyManager(py_tree)

    # Get UUID of step1
    step1_uuid = serializer.reverse_map[py_tree.root.children[0]]

    # Disable step1
    topo.disable_subtree(step1_uuid)
    assert len(topo.get_disabled_subtrees()) == 1

    # Tick should fail (Failure stub in Sequence)
    py_tree.tick()
    assert py_tree.root.status == py_trees.common.Status.FAILURE

    # Re-enable
    topo.enable_subtree(step1_uuid)
    assert len(topo.get_disabled_subtrees()) == 0

    # Tick should succeed again
    py_tree.tick()
    assert py_tree.root.status == py_trees.common.Status.SUCCESS


def test_swap_subtree():
    """Swapping a subtree replaces it with a custom behaviour."""
    root_def = TreeNodeDefinition(
        node_type="Selector", name="root",
        children=[
            TreeNodeDefinition(node_type="Failure", name="fail_branch"),
            TreeNodeDefinition(node_type="Success", name="fallback"),
        ],
    )
    tree_def, py_tree, serializer = _make_tree_and_deserialize(root_def)

    topo = TopologyManager(py_tree)
    fail_uuid = serializer.reverse_map[py_tree.root.children[0]]

    # Swap fail_branch with Success
    replacement = py_trees.behaviours.Success(name="swapped_in")
    topo.swap_subtree(fail_uuid, replacement)

    # Now first child succeeds, selector returns SUCCESS from first child
    py_tree.tick()
    assert py_tree.root.status == py_trees.common.Status.SUCCESS
    assert py_tree.root.children[0].name == "swapped_in"


def test_adapter_hooks():
    """TreeAdapter before_tick and after_tick are called."""
    root_def = TreeNodeDefinition(
        node_type="Success", name="root",
    )
    tree_def, py_tree, serializer = _make_tree_and_deserialize(root_def)

    calls = []

    class TestAdapter:
        def before_tick(self, tree, blackboard):
            calls.append("before")

        def after_tick(self, tree, blackboard, root_status):
            calls.append(("after", root_status))

    # Import ExecutionInstance to test adapter integration
    from talking_trees.core.execution import ExecutionInstance
    from talking_trees.models.execution import ExecutionConfig, ExecutionMode

    config = ExecutionConfig(
        tree_id=tree_def.tree_id,
        mode=ExecutionMode.MANUAL,
    )
    instance = ExecutionInstance(
        execution_id=uuid4(),
        tree_def=tree_def,
        tree=py_tree,
        serializer=serializer,
        config=config,
    )
    instance.add_adapter(TestAdapter())
    instance.tick()

    assert "before" in calls
    assert any(c[0] == "after" for c in calls if isinstance(c, tuple))


def test_multiple_adapters_ordered():
    """Multiple adapters execute in order."""
    root_def = TreeNodeDefinition(node_type="Success", name="root")
    tree_def, py_tree, serializer = _make_tree_and_deserialize(root_def)

    order = []

    class Adapter1:
        def before_tick(self, tree, bb): order.append(1)
        def after_tick(self, tree, bb, status): order.append(1)

    class Adapter2:
        def before_tick(self, tree, bb): order.append(2)
        def after_tick(self, tree, bb, status): order.append(2)

    from talking_trees.core.execution import ExecutionInstance
    from talking_trees.models.execution import ExecutionConfig, ExecutionMode

    config = ExecutionConfig(tree_id=tree_def.tree_id, mode=ExecutionMode.MANUAL)
    instance = ExecutionInstance(
        execution_id=uuid4(), tree_def=tree_def, tree=py_tree,
        serializer=serializer, config=config,
    )
    instance.add_adapter(Adapter1())
    instance.add_adapter(Adapter2())
    instance.tick()

    assert order == [1, 2, 1, 2]  # before1, before2, after1, after2
