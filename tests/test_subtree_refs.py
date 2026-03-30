"""Tests for WP1: Subtree References & Composability."""

import json
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

from talking_trees.core.serializer import TreeSerializer
from talking_trees.models.tree import (
    TreeDefinition,
    TreeMetadata,
    TreeNodeDefinition,
    TreeStatus,
)
from talking_trees.sdk import TalkingTrees


def _make_tree(name, root, subtrees=None):
    """Helper to create a TreeDefinition."""
    return TreeDefinition(
        tree_id=uuid4(),
        metadata=TreeMetadata(
            name=name,
            version="1.0.0",
            status=TreeStatus.DRAFT,
        ),
        root=root,
        subtrees=subtrees or {},
    )


def _ref_node(name, ref, **kwargs):
    """Helper to create a TreeNodeDefinition with a $ref field.

    Since $ref is an alias and TreeNodeDefinition does not have
    populate_by_name enabled, we must use model_validate with the alias.
    """
    data = {"node_type": "SubTreeRef", "name": name, "$ref": ref}
    data.update(kwargs)
    return TreeNodeDefinition.model_validate(data)


def test_inline_subtree_ref_round_trip():
    """Test existing inline $ref subtree round-trip."""
    subtree = TreeNodeDefinition(
        node_type="Sequence",
        name="sub_seq",
        config={"memory": True},
        children=[
            TreeNodeDefinition(node_type="Success", name="sub_step"),
        ],
    )
    root = TreeNodeDefinition(
        node_type="Sequence",
        name="main",
        config={"memory": True},
        children=[
            _ref_node("ref_node", "#/subtrees/my_sub"),
        ],
    )
    tree = _make_tree("RefTest", root, subtrees={"my_sub": subtree})

    serializer = TreeSerializer()
    py_tree = serializer.deserialize(tree)
    assert py_tree.root.name == "main"


def test_cycle_detection_inline():
    """Test that circular inline refs raise ValueError."""
    # subtree_a refs subtree_b, subtree_b refs subtree_a
    sub_a = TreeNodeDefinition(
        node_type="Sequence", name="a",
        children=[_ref_node("ref_b", "#/subtrees/subtree_b")],
    )
    sub_b = TreeNodeDefinition(
        node_type="Sequence", name="b",
        children=[_ref_node("ref_a", "#/subtrees/subtree_a")],
    )
    root = _ref_node("root_ref", "#/subtrees/subtree_a")
    tree = _make_tree("CycleTest", root, subtrees={"subtree_a": sub_a, "subtree_b": sub_b})

    serializer = TreeSerializer()
    with pytest.raises(ValueError, match="Circular"):
        serializer.deserialize(tree)


def test_file_based_subtree_ref():
    """Test tree_file reference loads from filesystem."""
    # Create a subtree file
    sub_root = TreeNodeDefinition(node_type="Success", name="external_step")
    sub_tree = _make_tree("ExternalSub", sub_root)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sub_tree.model_dump(mode="json", by_alias=True), f, default=str)
        sub_path = f.name

    try:
        # Create main tree with file ref
        root = TreeNodeDefinition(
            node_type="Sequence",
            name="main_with_file_ref",
            config={"memory": True},
            children=[
                TreeNodeDefinition(
                    node_type="SubTreeRef",
                    name="file_ref",
                    tree_file=sub_path,
                ),
            ],
        )
        tree = _make_tree("FileRefTest", root)

        serializer = TreeSerializer()
        py_tree = serializer.deserialize(tree)
        assert py_tree.root.name == "main_with_file_ref"
    finally:
        Path(sub_path).unlink()


def test_resolver_based_subtree_ref():
    """Test tree_id reference resolved via callback."""
    sub_root = TreeNodeDefinition(node_type="Success", name="resolved_step")
    sub_tree = _make_tree("ResolvedSub", sub_root)

    def my_resolver(tree_id: str) -> TreeDefinition:
        if tree_id == "abc-123":
            return sub_tree
        raise ValueError(f"Unknown tree: {tree_id}")

    root = TreeNodeDefinition(
        node_type="Sequence",
        name="main_with_id_ref",
        config={"memory": True},
        children=[
            TreeNodeDefinition(
                node_type="SubTreeRef",
                name="id_ref",
                tree_id="abc-123",
            ),
        ],
    )
    tree = _make_tree("IDRefTest", root)

    serializer = TreeSerializer()
    py_tree = serializer.deserialize(tree, resolver=my_resolver)
    assert py_tree.root.name == "main_with_id_ref"


def test_flatten_tree():
    """Test flatten_tree inlines all subtree refs."""
    subtree = TreeNodeDefinition(
        node_type="Success",
        name="inlined_step",
    )
    root = TreeNodeDefinition(
        node_type="Sequence",
        name="main",
        config={"memory": True},
        children=[
            _ref_node("ref_node", "#/subtrees/my_sub"),
        ],
    )
    tree = _make_tree("FlattenTest", root, subtrees={"my_sub": subtree})

    tt = TalkingTrees()
    flat = tt.flatten_tree(tree)

    assert flat.subtrees == {}
    assert flat.root.children[0].node_type == "Success"
    assert flat.root.children[0].name == "ref_node"


def test_nested_subtree_refs():
    """Test 3-level deep nested subtree refs."""
    level3 = TreeNodeDefinition(node_type="Success", name="deep_leaf")
    level2 = TreeNodeDefinition(
        node_type="Sequence", name="mid",
        children=[_ref_node("ref3", "#/subtrees/l3")],
    )
    level1 = TreeNodeDefinition(
        node_type="Sequence", name="top",
        children=[_ref_node("ref2", "#/subtrees/l2")],
    )
    tree = _make_tree("NestedTest", level1, subtrees={"l2": level2, "l3": level3})

    serializer = TreeSerializer()
    py_tree = serializer.deserialize(tree)
    assert py_tree.root.name == "top"
