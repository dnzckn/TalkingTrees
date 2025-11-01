#!/usr/bin/env python
"""Test security hardening features (cycle detection, depth limits)."""

from datetime import datetime
from uuid import uuid4

from py_forest.core.serializer import TreeSerializer
from py_forest.models.tree import (
    TreeDefinition,
    TreeMetadata,
    TreeNodeDefinition,
    TreeStatus,
)


def test_cycle_detection():
    """Test that circular subtree references are detected."""
    print("=" * 70)
    print("TEST 1: Cycle Detection in Subtree References")
    print("=" * 70)

    # Create subtree definitions with circular reference
    subtree_a = TreeNodeDefinition(
        node_type="Sequence",
        node_id=uuid4(),
        name="SubtreeA",
        children=[
            TreeNodeDefinition(
                node_type="Success", node_id=uuid4(), name="Task1", children=[]
            ),
            TreeNodeDefinition(
                node_type="Sequence",  # This will reference SubtreeB
                node_id=uuid4(),
                name="RefToB",
                ref="#/subtrees/subtree_b",
                children=[],
            ),
        ],
    )

    subtree_b = TreeNodeDefinition(
        node_type="Selector",
        node_id=uuid4(),
        name="SubtreeB",
        children=[
            TreeNodeDefinition(
                node_type="Sequence",  # This references back to SubtreeA
                node_id=uuid4(),
                name="RefToA",
                ref="#/subtrees/subtree_a",
                children=[],
            )
        ],
    )

    # Create root that references subtree_a
    root = TreeNodeDefinition(
        node_type="Sequence",
        node_id=uuid4(),
        name="Root",
        ref="#/subtrees/subtree_a",
        children=[],
    )

    # Create tree definition
    tree_def = TreeDefinition(
        tree_id=uuid4(),
        metadata=TreeMetadata(
            name="Circular Test",
            version="1.0.0",
            description="Test circular references",
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
            status=TreeStatus.DRAFT,
        ),
        root=root,
        subtrees={"subtree_a": subtree_a, "subtree_b": subtree_b},
    )

    # Try to deserialize (should detect cycle)
    serializer = TreeSerializer()

    try:
        _tree = serializer.deserialize(tree_def)
        print("✗ FAILED: Cycle was not detected!")
        return False
    except ValueError as e:
        if "circular" in str(e).lower():
            print(f"✓ PASSED: Cycle detected correctly: {e}")
            return True
        else:
            print(f"✗ FAILED: Different error raised: {e}")
            return False


def test_depth_limit():
    """Test that excessive tree depth is prevented."""
    print("\n" + "=" * 70)
    print("TEST 2: Depth Limit Enforcement")
    print("=" * 70)

    # Create a very deep tree (deeper than default limit of 100)
    MAX_DEPTH = 10  # Use small depth for faster test

    # Build chain from leaf up
    current = TreeNodeDefinition(
        node_type="Success", node_id=uuid4(), name="Leaf", children=[]
    )

    # Wrap in sequences to create depth
    for i in range(MAX_DEPTH + 5):  # Exceed limit by 5
        current = TreeNodeDefinition(
            node_type="Sequence", node_id=uuid4(), name=f"Level{i}", children=[current]
        )

    # Create tree definition
    tree_def = TreeDefinition(
        tree_id=uuid4(),
        metadata=TreeMetadata(
            name="Deep Test",
            version="1.0.0",
            description="Test depth limits",
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
            status=TreeStatus.DRAFT,
        ),
        root=current,
        subtrees={},
        blackboard_schema={},
    )

    # Try to deserialize with small max_depth
    serializer = TreeSerializer(max_depth=MAX_DEPTH)

    try:
        _tree = serializer.deserialize(tree_def)
        print("✗ FAILED: Depth limit was not enforced!")
        return False
    except ValueError as e:
        if "depth exceeded" in str(e).lower():
            print(f"✓ PASSED: Depth limit enforced correctly: {e}")
            return True
        else:
            print(f"✗ FAILED: Different error raised: {e}")
            return False


def test_normal_deep_tree():
    """Test that normal (within limits) deep trees work fine."""
    print("\n" + "=" * 70)
    print("TEST 3: Normal Deep Tree (Within Limits)")
    print("=" * 70)

    # Create a tree that's deep but within limits
    MAX_DEPTH = 100
    ACTUAL_DEPTH = 50  # Half the limit

    # Build chain from leaf up
    current = TreeNodeDefinition(
        node_type="Success", node_id=uuid4(), name="Leaf", children=[]
    )

    # Wrap in sequences
    for i in range(ACTUAL_DEPTH):
        current = TreeNodeDefinition(
            node_type="Sequence", node_id=uuid4(), name=f"Level{i}", children=[current]
        )

    # Create tree definition
    tree_def = TreeDefinition(
        tree_id=uuid4(),
        metadata=TreeMetadata(
            name="Normal Deep Test",
            version="1.0.0",
            description="Test normal depth",
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
            status=TreeStatus.DRAFT,
        ),
        root=current,
        subtrees={},
        blackboard_schema={},
    )

    # Should succeed
    serializer = TreeSerializer(max_depth=MAX_DEPTH)

    try:
        _tree = serializer.deserialize(tree_def)
        print(f"✓ PASSED: Deep tree (depth={ACTUAL_DEPTH}) deserialized successfully")
        return True
    except Exception as e:
        print(f"✗ FAILED: Normal deep tree failed: {e}")
        return False


def test_subtree_depth_limit():
    """Test that depth limits work with subtree resolution."""
    print("\n" + "=" * 70)
    print("TEST 4: Depth Limit with Subtrees")
    print("=" * 70)

    MAX_DEPTH = 10

    # Create a subtree
    subtree = TreeNodeDefinition(
        node_type="Sequence",
        node_id=uuid4(),
        name="Subtree",
        children=[
            TreeNodeDefinition(
                node_type="Success", node_id=uuid4(), name="Task", children=[]
            )
        ],
    )

    # Create root that uses subtree many times (exceeding depth)
    current = TreeNodeDefinition(
        node_type="Sequence",
        node_id=uuid4(),
        name="Leaf",
        ref="#/subtrees/my_subtree",
        children=[],
    )

    for i in range(MAX_DEPTH + 2):
        current = TreeNodeDefinition(
            node_type="Sequence", node_id=uuid4(), name=f"Level{i}", children=[current]
        )

    # Create tree definition
    tree_def = TreeDefinition(
        tree_id=uuid4(),
        metadata=TreeMetadata(
            name="Subtree Depth Test",
            version="1.0.0",
            description="Test depth limits with subtrees",
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
            status=TreeStatus.DRAFT,
        ),
        root=current,
        subtrees={"my_subtree": subtree},
        blackboard_schema={},
    )

    # Should fail due to depth limit
    serializer = TreeSerializer(max_depth=MAX_DEPTH)

    try:
        _tree = serializer.deserialize(tree_def)
        print("✗ FAILED: Depth limit was not enforced with subtrees!")
        return False
    except ValueError as e:
        if "depth exceeded" in str(e).lower():
            print(f"✓ PASSED: Depth limit enforced with subtrees: {e}")
            return True
        else:
            print(f"✗ FAILED: Different error raised: {e}")
            return False


if __name__ == "__main__":
    print("\n🔒 Testing Security Hardening Features\n")

    results = []
    results.append(("Cycle Detection", test_cycle_detection()))
    results.append(("Depth Limit", test_depth_limit()))
    results.append(("Normal Deep Tree", test_normal_deep_tree()))
    results.append(("Subtree Depth Limit", test_subtree_depth_limit()))

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n✅ All security tests passed!")
    else:
        print("\n❌ Some security tests failed.")

    print()
