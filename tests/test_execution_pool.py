"""Tests for WP-12: Multi-Instance Execution Pool."""

from uuid import uuid4

import pytest

from talking_trees.execution.pool import ExecutionPool
from talking_trees.models.tree import (
    TreeDefinition, TreeMetadata, TreeNodeDefinition, TreeStatus,
)


def _make_tree(root):
    return TreeDefinition(
        tree_id=uuid4(),
        metadata=TreeMetadata(name="PoolTest", version="1.0.0", status=TreeStatus.DRAFT),
        root=root,
    )


def test_spawn_and_tick_all():
    tree = _make_tree(TreeNodeDefinition(node_type="Success", name="leaf"))
    pool = ExecutionPool(tree)
    ids = [pool.spawn() for _ in range(5)]
    assert pool.active_count() == 5
    results = pool.tick_all()
    assert len(results) == 5
    assert all(s == "SUCCESS" for s in results.values())


def test_max_instances_cap():
    tree = _make_tree(TreeNodeDefinition(node_type="Success", name="leaf"))
    pool = ExecutionPool(tree, max_instances=3)
    for _ in range(3):
        pool.spawn()
    with pytest.raises(RuntimeError, match="Max instances"):
        pool.spawn()


def test_gc_removes_completed():
    tree = _make_tree(TreeNodeDefinition(node_type="Success", name="leaf"))
    pool = ExecutionPool(tree, gc_ttl_seconds=0)
    pool.spawn()
    pool.tick_all()
    assert pool.collect_garbage() == 1
    assert pool.total_count() == 0


def test_kill_single():
    tree = _make_tree(TreeNodeDefinition(node_type="Success", name="leaf"))
    pool = ExecutionPool(tree)
    id1 = pool.spawn()
    id2 = pool.spawn()
    pool.kill(id1)
    assert pool.total_count() == 1
    results = pool.tick_all()
    assert id2 in results


def test_query_by_status():
    tree = _make_tree(TreeNodeDefinition(node_type="Success", name="leaf"))
    pool = ExecutionPool(tree)
    pool.spawn()
    pool.spawn()
    pool.tick_all()
    assert len(pool.query(status="SUCCESS")) == 2


def test_pool_stats():
    tree = _make_tree(TreeNodeDefinition(node_type="Success", name="leaf"))
    pool = ExecutionPool(tree)
    pool.spawn()
    pool.spawn()
    pool.tick_all()
    s = pool.stats()
    assert s["total"] == 2
    assert s["completed"] == 2
