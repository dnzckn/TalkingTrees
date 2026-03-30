"""Tests for WP3: Macro Nodes."""

import tempfile
from pathlib import Path
from uuid import uuid4

from talking_trees.models.tree import (
    MacroMetadata,
    TreeDefinition,
    TreeMetadata,
    TreeNodeDefinition,
    TreeStatus,
)
from talking_trees.sdk import TalkingTrees


def _make_tree(name, root):
    return TreeDefinition(
        tree_id=uuid4(),
        metadata=TreeMetadata(name=name, version="1.0.0", status=TreeStatus.DRAFT),
        root=root,
    )


def test_create_macro():
    """Creating a macro adds MacroMetadata to the target node."""
    child1 = TreeNodeDefinition(node_type="Success", name="s1")
    child2 = TreeNodeDefinition(node_type="Success", name="s2")
    root = TreeNodeDefinition(
        node_type="Sequence",
        name="seq",
        children=[child1, child2],
    )
    tree = _make_tree("MacroTest", root)

    tt = TalkingTrees()
    result = tt.create_macro(tree, "MyMacro", [child1.node_id, child2.node_id])

    # The root should now have macro metadata since it's the LCA
    assert result.root.macro is not None
    assert result.root.macro.name == "MyMacro"


def test_expand_macro():
    """Expanding a macro removes its MacroMetadata."""
    root = TreeNodeDefinition(
        node_type="Sequence",
        name="seq",
        macro=MacroMetadata(name="TestMacro"),
        children=[TreeNodeDefinition(node_type="Success", name="s1")],
    )
    tree = _make_tree("ExpandTest", root)

    tt = TalkingTrees()
    result = tt.expand_macro(tree, root.node_id)

    assert result.root.macro is None
    assert result.root.name == "seq"


def test_macro_round_trip_json():
    """Macro metadata survives JSON serialization."""
    root = TreeNodeDefinition(
        node_type="Sequence",
        name="seq",
        macro=MacroMetadata(name="TestMacro", description="A test"),
        children=[TreeNodeDefinition(node_type="Success", name="s1")],
    )
    tree = _make_tree("RoundTrip", root)

    tt = TalkingTrees()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tt.save_tree(tree, f.name)
        loaded = tt.load_tree(f.name)

    assert loaded.root.macro is not None
    assert loaded.root.macro.name == "TestMacro"
    Path(f.name).unlink()


def test_extract_to_subtree():
    """Extracting a macro creates a file and replaces with tree_file ref."""
    child = TreeNodeDefinition(
        node_type="Sequence",
        name="group",
        macro=MacroMetadata(name="ExtractMe"),
        children=[TreeNodeDefinition(node_type="Success", name="s1")],
    )
    root = TreeNodeDefinition(
        node_type="Sequence",
        name="root",
        children=[child],
    )
    tree = _make_tree("ExtractTest", root)

    tt = TalkingTrees()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        filepath = f.name

    try:
        modified, extracted = tt.extract_to_subtree(tree, child.node_id, filepath)

        # Modified tree should have a SubTreeRef
        assert modified.root.children[0].tree_file == filepath
        assert modified.root.children[0].node_type == "SubTreeRef"

        # Extracted tree should be valid
        assert extracted.root.node_type == "Sequence"
        assert extracted.root.macro is None
        assert extracted.metadata.name == "ExtractMe"
    finally:
        Path(filepath).unlink(missing_ok=True)
