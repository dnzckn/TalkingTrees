"""Tests for WP7: Production Observability."""

from uuid import uuid4

from talking_trees.core.observability import (
    CompositeCollector,
    InMemoryCollector,
    LogCollector,
)
from talking_trees.core.serializer import TreeSerializer
from talking_trees.models.tree import (
    TreeDefinition,
    TreeMetadata,
    TreeNodeDefinition,
    TreeStatus,
)


def _make_execution():
    """Create a tree and execution instance for testing."""
    from talking_trees.core.execution import ExecutionInstance
    from talking_trees.models.execution import ExecutionConfig, ExecutionMode

    root = TreeNodeDefinition(
        node_type="Sequence", name="root",
        children=[
            TreeNodeDefinition(node_type="Success", name="step1"),
            TreeNodeDefinition(node_type="Success", name="step2"),
        ],
    )
    tree_def = TreeDefinition(
        tree_id=uuid4(),
        metadata=TreeMetadata(name="ObsTest", version="1.0.0", status=TreeStatus.DRAFT),
        root=root,
    )
    serializer = TreeSerializer()
    py_tree = serializer.deserialize(tree_def)
    py_tree.setup()

    config = ExecutionConfig(tree_id=tree_def.tree_id, mode=ExecutionMode.MANUAL)
    instance = ExecutionInstance(
        execution_id=uuid4(), tree_def=tree_def, tree=py_tree,
        serializer=serializer, config=config,
    )
    return instance


def test_in_memory_collector():
    """InMemoryCollector records tick metrics."""
    collector = InMemoryCollector()
    instance = _make_execution()
    instance.add_collector(collector)

    # Run 5 ticks
    for _ in range(5):
        instance.tick()

    metrics = collector.get_metrics(instance.execution_id)
    assert metrics is not None
    assert metrics.total_ticks == 5


def test_log_collector(caplog):
    """LogCollector outputs structured JSON logs."""
    import logging
    collector = LogCollector()

    with caplog.at_level(logging.INFO, logger="talking_trees.observability"):
        collector.on_tick(uuid4(), uuid4(), 1, 0.5)

    assert "tick" in caplog.text


def test_composite_collector():
    """CompositeCollector dispatches to multiple collectors."""
    c1 = InMemoryCollector()
    c2 = InMemoryCollector()
    composite = CompositeCollector([c1, c2])

    instance = _make_execution()
    instance.add_collector(composite)
    instance.tick()

    assert c1.get_metrics(instance.execution_id) is not None
    assert c2.get_metrics(instance.execution_id) is not None


def test_zero_overhead_no_collector():
    """No collector means no overhead (no errors)."""
    instance = _make_execution()
    # No collector added
    instance.tick()
    # Should just work without errors


def test_all_summaries():
    """get_all_summaries returns all tracked executions."""
    collector = InMemoryCollector()

    exec1_id = uuid4()
    exec2_id = uuid4()
    tree_id = uuid4()

    collector.on_tick(exec1_id, tree_id, 1, 1.0)
    collector.on_tick(exec2_id, tree_id, 1, 2.0)

    summaries = collector.get_all_summaries()
    assert len(summaries) == 2
