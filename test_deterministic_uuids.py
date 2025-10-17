#!/usr/bin/env python
"""Test deterministic UUID generation in serializer."""

import py_trees
from py_trees.composites import Sequence, Selector
from py_trees.behaviours import Success, Failure, Running
from py_forest.adapters.py_trees_adapter import from_py_trees


def test_uuid_stability():
    """Test that same tree produces same UUIDs."""
    print("=" * 70)
    print("TEST 1: UUID Stability (same tree → same UUIDs)")
    print("=" * 70)

    # Create a simple tree
    root = Sequence(
        name="Root",
        memory=True,
        children=[
            Success(name="Task1"),
            Selector(
                name="Choice",
                memory=False,
                children=[
                    Success(name="Option1"),
                    Failure(name="Option2"),
                ]
            ),
            Running(name="Task2"),
        ]
    )

    # Convert twice with deterministic UUIDs
    pf_tree1 = from_py_trees(root, name="Test Tree", use_deterministic_uuids=True)
    pf_tree2 = from_py_trees(root, name="Test Tree", use_deterministic_uuids=True)

    # Check root UUIDs match
    if pf_tree1.root.node_id == pf_tree2.root.node_id:
        print("✓ Root UUID is stable:", pf_tree1.root.node_id)
    else:
        print("✗ Root UUID changed!")
        print("  First:", pf_tree1.root.node_id)
        print("  Second:", pf_tree2.root.node_id)
        return False

    # Check all child UUIDs match
    def compare_nodes(node1, node2, path="root"):
        if node1.node_id != node2.node_id:
            print(f"✗ UUID mismatch at {path}")
            print(f"  First: {node1.node_id}")
            print(f"  Second: {node2.node_id}")
            return False

        if len(node1.children) != len(node2.children):
            print(f"✗ Different number of children at {path}")
            return False

        for i, (child1, child2) in enumerate(zip(node1.children, node2.children)):
            if not compare_nodes(child1, child2, f"{path}/{child1.name}"):
                return False

        return True

    if compare_nodes(pf_tree1.root, pf_tree2.root):
        print("✓ All node UUIDs are stable across conversions")
    else:
        return False

    print()
    return True


def test_uuid_determinism():
    """Test that different trees produce different UUIDs."""
    print("=" * 70)
    print("TEST 2: UUID Determinism (different tree → different UUIDs)")
    print("=" * 70)

    # Tree 1
    root1 = Sequence(
        name="Root",
        memory=True,
        children=[Success(name="Task1")]
    )

    # Tree 2 (different structure)
    root2 = Selector(
        name="Root",
        memory=False,
        children=[Success(name="Task1")]
    )

    pf_tree1 = from_py_trees(root1, name="Tree1", use_deterministic_uuids=True)
    pf_tree2 = from_py_trees(root2, name="Tree2", use_deterministic_uuids=True)

    if pf_tree1.root.node_id != pf_tree2.root.node_id:
        print("✓ Different structures produce different UUIDs")
        print("  Sequence UUID:", pf_tree1.root.node_id)
        print("  Selector UUID:", pf_tree2.root.node_id)
    else:
        print("✗ Same UUID for different structures!")
        return False

    print()
    return True


def test_random_uuids():
    """Test that random UUIDs are different each time."""
    print("=" * 70)
    print("TEST 3: Random UUIDs (non-deterministic mode)")
    print("=" * 70)

    root = Sequence(
        name="Root",
        memory=True,
        children=[Success(name="Task1")]
    )

    pf_tree1 = from_py_trees(root, name="Tree", use_deterministic_uuids=False)
    pf_tree2 = from_py_trees(root, name="Tree", use_deterministic_uuids=False)

    if pf_tree1.root.node_id != pf_tree2.root.node_id:
        print("✓ Random UUIDs are different each time")
        print("  First:", pf_tree1.root.node_id)
        print("  Second:", pf_tree2.root.node_id)
    else:
        print("✗ Random UUIDs are the same (unlikely but possible)")

    print()
    return True


def test_path_sensitivity():
    """Test that UUID depends on node path in tree."""
    print("=" * 70)
    print("TEST 4: Path Sensitivity (same name, different path → different UUID)")
    print("=" * 70)

    # Two tasks with same name at different positions
    root = Sequence(
        name="Root",
        memory=True,
        children=[
            Success(name="Task"),  # Path: Root/Task
            Sequence(
                name="SubSeq",
                memory=True,
                children=[
                    Success(name="Task"),  # Path: Root/SubSeq/Task
                ]
            )
        ]
    )

    pf_tree = from_py_trees(root, name="Tree", use_deterministic_uuids=True)

    task1_uuid = pf_tree.root.children[0].node_id
    task2_uuid = pf_tree.root.children[1].children[0].node_id

    if task1_uuid != task2_uuid:
        print("✓ Same name at different paths → different UUIDs")
        print("  Root/Task:", task1_uuid)
        print("  Root/SubSeq/Task:", task2_uuid)
    else:
        print("✗ Same UUID despite different paths!")
        return False

    print()
    return True


if __name__ == "__main__":
    print("\n🧪 Testing Deterministic UUID Generation\n")

    results = []
    results.append(("UUID Stability", test_uuid_stability()))
    results.append(("UUID Determinism", test_uuid_determinism()))
    results.append(("Random UUIDs", test_random_uuids()))
    results.append(("Path Sensitivity", test_path_sensitivity()))

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n✅ All tests passed! Deterministic UUIDs are working correctly.")
    else:
        print("\n❌ Some tests failed. Check output above.")

    print()
