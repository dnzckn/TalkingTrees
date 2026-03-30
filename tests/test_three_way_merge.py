"""Tests for WP6: Tree-Aware Diffing & Three-Way Merge."""

from uuid import uuid4

from talking_trees.core.diff import three_way_merge
from talking_trees.models.tree import (
    TreeDefinition,
    TreeMetadata,
    TreeNodeDefinition,
    TreeStatus,
)


def _make_tree(name, root, subtrees=None):
    return TreeDefinition(
        tree_id=uuid4(),
        metadata=TreeMetadata(name=name, version="1.0.0", status=TreeStatus.DRAFT),
        root=root,
        subtrees=subtrees or {},
    )


def test_no_conflicts():
    """Merge with non-overlapping changes succeeds."""
    # Shared node IDs
    nid_root = uuid4()
    nid_a = uuid4()
    nid_b = uuid4()

    base_root = TreeNodeDefinition(
        node_type="Sequence",
        node_id=nid_root,
        name="root",
        children=[
            TreeNodeDefinition(
                node_type="Success", node_id=nid_a, name="a", config={"x": 1}
            ),
            TreeNodeDefinition(
                node_type="Success", node_id=nid_b, name="b", config={"y": 2}
            ),
        ],
    )

    # Ours changes node a's config
    ours_root = TreeNodeDefinition(
        node_type="Sequence",
        node_id=nid_root,
        name="root",
        children=[
            TreeNodeDefinition(
                node_type="Success", node_id=nid_a, name="a", config={"x": 10}
            ),
            TreeNodeDefinition(
                node_type="Success", node_id=nid_b, name="b", config={"y": 2}
            ),
        ],
    )

    # Theirs changes node b's config
    theirs_root = TreeNodeDefinition(
        node_type="Sequence",
        node_id=nid_root,
        name="root",
        children=[
            TreeNodeDefinition(
                node_type="Success", node_id=nid_a, name="a", config={"x": 1}
            ),
            TreeNodeDefinition(
                node_type="Success", node_id=nid_b, name="b", config={"y": 20}
            ),
        ],
    )

    base = _make_tree("base", base_root)
    ours = _make_tree("ours", ours_root)
    theirs = _make_tree("theirs", theirs_root)

    result = three_way_merge(base, ours, theirs)

    assert not result.has_conflicts
    assert result.merged_tree is not None
    # Ours' change to x
    assert result.merged_tree.root.children[0].config["x"] == 10
    # Theirs' change to y
    assert result.merged_tree.root.children[1].config["y"] == 20


def test_conflict_detection():
    """Merge with conflicting changes produces conflicts."""
    nid_root = uuid4()
    nid_a = uuid4()

    base = _make_tree(
        "base",
        TreeNodeDefinition(
            node_type="Sequence",
            node_id=nid_root,
            name="root",
            children=[
                TreeNodeDefinition(
                    node_type="Success", node_id=nid_a, name="a", config={"x": 1}
                )
            ],
        ),
    )
    ours = _make_tree(
        "ours",
        TreeNodeDefinition(
            node_type="Sequence",
            node_id=nid_root,
            name="root",
            children=[
                TreeNodeDefinition(
                    node_type="Success", node_id=nid_a, name="a", config={"x": 10}
                )
            ],
        ),
    )
    theirs = _make_tree(
        "theirs",
        TreeNodeDefinition(
            node_type="Sequence",
            node_id=nid_root,
            name="root",
            children=[
                TreeNodeDefinition(
                    node_type="Success", node_id=nid_a, name="a", config={"x": 99}
                )
            ],
        ),
    )

    result = three_way_merge(base, ours, theirs)

    assert result.has_conflicts
    assert len(result.conflicts) == 1
    assert result.conflicts[0].property_name == "config.x"


def test_theirs_only_change_applied():
    """When only theirs changes a property, it's applied to merged tree."""
    nid = uuid4()

    base_node = TreeNodeDefinition(node_type="Success", node_id=nid, name="orig")
    ours_node = TreeNodeDefinition(node_type="Success", node_id=nid, name="orig")
    theirs_node = TreeNodeDefinition(node_type="Success", node_id=nid, name="renamed")

    result = three_way_merge(
        _make_tree("b", base_node),
        _make_tree("o", ours_node),
        _make_tree("t", theirs_node),
    )

    assert not result.has_conflicts
    assert result.merged_tree.root.name == "renamed"


def test_identical_changes_no_conflict():
    """When both make the same change, no conflict."""
    nid = uuid4()

    base = _make_tree(
        "b",
        TreeNodeDefinition(
            node_type="Success", node_id=nid, name="old", config={"v": 1}
        ),
    )
    ours = _make_tree(
        "o",
        TreeNodeDefinition(
            node_type="Success", node_id=nid, name="new", config={"v": 2}
        ),
    )
    theirs = _make_tree(
        "t",
        TreeNodeDefinition(
            node_type="Success", node_id=nid, name="new", config={"v": 2}
        ),
    )

    result = three_way_merge(base, ours, theirs)

    assert not result.has_conflicts
