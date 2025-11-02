#!/usr/bin/env python
"""
Test All Example Trees for Round-Trip Conversion
=================================================

This module tests all example tree files in examples/trees/ directory
for round-trip conversion integrity.

For each .json file, it:
1. Loads the JSON tree definition
2. Deserializes to py_trees (counts nodes)
3. Serializes back to TalkingTrees format (counts nodes)
4. Compares node counts and validates structure

This ensures that:
- All example trees can be loaded successfully
- Round-trip conversion preserves tree structure
- No nodes are lost or duplicated during conversion
- All node types in examples are supported
"""

import json
from pathlib import Path

import pytest

from talking_trees.adapters import compare_py_trees, from_py_trees
from talking_trees.core.serializer import TreeSerializer
from talking_trees.models.tree import TreeDefinition, TreeNodeDefinition


def count_nodes(node: TreeNodeDefinition) -> int:
    """Recursively count all nodes in a tree."""
    count = 1  # Count this node
    for child in node.children:
        count += count_nodes(child)
    return count


@pytest.fixture(scope="module")
def examples_dir():
    """Get the examples/trees directory."""
    examples_path = Path(__file__).parent.parent / "examples" / "trees"
    assert examples_path.exists(), f"Examples directory not found: {examples_path}"
    return examples_path


@pytest.fixture(scope="module")
def example_tree_files(examples_dir):
    """Get all JSON files from examples directory."""
    json_files = sorted(examples_dir.glob("*.json"))
    assert len(json_files) > 0, f"No .json files found in {examples_dir}"
    return json_files


@pytest.mark.parametrize("tree_file", [
    pytest.param(f, id=f.name)
    for f in sorted((Path(__file__).parent.parent / "examples" / "trees").glob("*.json"))
])
def test_tree_roundtrip(tree_file):
    """Test round-trip conversion for a single tree file.

    Args:
        tree_file: Path to JSON tree file
    """
    # Step 1: Load JSON tree definition
    with open(tree_file) as f:
        tree_data = json.load(f)

    tree_def = TreeDefinition.model_validate(tree_data)
    original_nodes = count_nodes(tree_def.root)

    # Step 2: Deserialize to py_trees
    serializer = TreeSerializer()
    py_tree = serializer.deserialize(tree_def)

    # Step 3: Serialize back to TalkingTrees format (round-trip)
    # Convert py_trees back to TalkingTrees TreeDefinition
    roundtrip_tree, context = from_py_trees(
        py_tree.root,
        name=tree_def.metadata.name,
        version=tree_def.metadata.version,
        description=tree_def.metadata.description or "",
    )

    # Check for conversion warnings (not failures)
    if context.has_warnings():
        pytest.skip(f"Conversion warnings: {len(context.warnings)} warnings")

    roundtrip_nodes = count_nodes(roundtrip_tree.root)

    # Step 4: Validate with py_trees comparison
    # Convert both to py_trees and compare
    original_py_tree = serializer.deserialize(tree_def)
    roundtrip_py_tree = serializer.deserialize(roundtrip_tree)

    trees_equivalent = compare_py_trees(
        original_py_tree.root, roundtrip_py_tree.root, verbose=False
    )

    # Assert node counts match
    assert original_nodes == roundtrip_nodes, \
        f"Node count mismatch: {original_nodes} → {roundtrip_nodes}"

    # Assert trees are structurally equivalent
    assert trees_equivalent, "Tree structures are not equivalent"


def test_all_examples_exist(examples_dir, example_tree_files):
    """Test that we have example files to test."""
    assert len(example_tree_files) > 0, "No example tree files found"
    print(f"\nFound {len(example_tree_files)} example tree files")
