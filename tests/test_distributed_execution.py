"""Tests for WP5: Distributed Execution / Remote Subtree Proxy."""

from uuid import uuid4

import py_trees
import pytest

from talking_trees.behaviors.remote_subtree import RemoteSubtreeBehaviour
from talking_trees.core.partition import partition_tree
from talking_trees.core.serializer import TreeSerializer
from talking_trees.models.tree import (
    TreeDefinition,
    TreeMetadata,
    TreeNodeDefinition,
    TreeStatus,
)


def _make_tree(name, root):
    return TreeDefinition(
        tree_id=uuid4(),
        metadata=TreeMetadata(name=name, version="1.0.0", status=TreeStatus.DRAFT),
        root=root,
    )


def test_remote_subtree_timeout():
    """RemoteSubtree returns fallback status on timeout."""
    remote = RemoteSubtreeBehaviour(
        name="test_remote",
        endpoint="http://192.0.2.1:9999",  # RFC 5737 TEST-NET, will timeout
        remote_execution_id="fake-id",
        timeout_ms=100,  # Very short timeout
        fallback_status=py_trees.common.Status.FAILURE,
    )

    status = remote.update()
    assert status == py_trees.common.Status.FAILURE
    assert remote.last_error is not None


def test_remote_subtree_connection_error():
    """RemoteSubtree returns fallback on connection error."""
    remote = RemoteSubtreeBehaviour(
        name="test_remote",
        endpoint="http://localhost:1",  # Port 1 - connection refused
        remote_execution_id="fake-id",
        timeout_ms=500,
    )

    status = remote.update()
    assert status == py_trees.common.Status.FAILURE
    assert remote.last_error is not None


def test_partition_tree():
    """partition_tree splits tree and creates RemoteSubtree proxies."""
    child_a = TreeNodeDefinition(node_type="Success", name="local_step")
    child_b = TreeNodeDefinition(
        node_type="Sequence",
        name="remote_branch",
        children=[TreeNodeDefinition(node_type="Success", name="remote_step")],
    )
    root = TreeNodeDefinition(
        node_type="Sequence",
        name="root",
        children=[child_a, child_b],
    )
    tree = _make_tree("PartitionTest", root)

    partition_map = {
        str(child_b.node_id): "http://remote-host:8000",
    }

    result = partition_tree(tree, partition_map)

    assert "main" in result
    main = result["main"]

    # Main tree should have RemoteSubtree proxy for child_b
    assert main.root.children[1].node_type == "RemoteSubtree"
    assert main.root.children[1].config["endpoint"] == "http://remote-host:8000"

    # Should have a partition tree for the remote branch
    partition_keys = [k for k in result if k != "main"]
    assert len(partition_keys) == 1

    remote_tree = result[partition_keys[0]]
    assert remote_tree.root.name == "remote_branch"


def test_partition_preserves_local_nodes():
    """Nodes not in partition_map remain unchanged."""
    child_a = TreeNodeDefinition(node_type="Success", name="stays_local")
    child_b = TreeNodeDefinition(node_type="Success", name="goes_remote")
    root = TreeNodeDefinition(
        node_type="Sequence",
        name="root",
        children=[child_a, child_b],
    )
    tree = _make_tree("Test", root)

    result = partition_tree(tree, {str(child_b.node_id): "http://host:8000"})

    main = result["main"]
    assert main.root.children[0].node_type == "Success"
    assert main.root.children[0].name == "stays_local"


def test_remote_subtree_builder():
    """RemoteSubtree can be built from tree definition via serializer."""
    root = TreeNodeDefinition(
        node_type="RemoteSubtree",
        name="remote_node",
        config={
            "endpoint": "http://remote:8000",
            "timeout_ms": 3000,
        },
    )
    tree = _make_tree("BuilderTest", root)

    serializer = TreeSerializer()
    py_tree = serializer.deserialize(tree)

    assert isinstance(py_tree.root, RemoteSubtreeBehaviour)
    assert py_tree.root.endpoint == "http://remote:8000"
    assert py_tree.root.timeout_s == 3.0
