"""Tests for WP-17: Conditional Tick Rates."""

import time
from uuid import uuid4

import py_trees

from talking_trees.core.serializer import TreeSerializer
from talking_trees.execution.tick_scheduler import TickScheduler
from talking_trees.models.tree import (
    TreeDefinition, TreeMetadata, TreeNodeDefinition, TreeStatus,
)


def _make_py_tree(root_def):
    tree_def = TreeDefinition(
        tree_id=uuid4(),
        metadata=TreeMetadata(name="SchedTest", version="1.0.0", status=TreeStatus.DRAFT),
        root=root_def,
    )
    serializer = TreeSerializer()
    py_tree = serializer.deserialize(tree_def)
    py_tree.setup()
    return py_tree


def test_basic_tick():
    py_tree = _make_py_tree(TreeNodeDefinition(node_type="Success", name="leaf"))
    scheduler = TickScheduler(py_tree, default_hz=10.0)

    status = scheduler.tick()
    assert status == py_trees.common.Status.SUCCESS


def test_should_tick_respects_rate():
    py_tree = _make_py_tree(TreeNodeDefinition(node_type="Success", name="leaf"))
    scheduler = TickScheduler(py_tree, default_hz=10.0)

    scheduler.set_rate("slow_node", 2.0)  # 2 Hz = 0.5s interval

    # First call should allow
    assert scheduler.should_tick("slow_node")
    # Immediate second call should not
    assert not scheduler.should_tick("slow_node")
    # After interval
    time.sleep(0.55)
    assert scheduler.should_tick("slow_node")


def test_default_rate_applies():
    py_tree = _make_py_tree(TreeNodeDefinition(node_type="Success", name="leaf"))
    scheduler = TickScheduler(py_tree, default_hz=100.0)

    # No explicit rate set, uses default (100 Hz = 10ms interval)
    assert scheduler.should_tick("any_node")


def test_run_with_duration():
    py_tree = _make_py_tree(TreeNodeDefinition(node_type="Success", name="leaf"))
    scheduler = TickScheduler(py_tree, default_hz=100.0)

    start = time.monotonic()
    scheduler.run(duration_seconds=0.1)
    elapsed = time.monotonic() - start

    assert elapsed >= 0.1
    assert elapsed < 0.5  # shouldn't take too long
    assert py_tree.count > 0  # at least some ticks happened


def test_stop():
    py_tree = _make_py_tree(TreeNodeDefinition(node_type="Success", name="leaf"))
    scheduler = TickScheduler(py_tree, default_hz=10.0)

    scheduler.stop()
    assert not scheduler._running
