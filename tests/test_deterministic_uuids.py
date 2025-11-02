#!/usr/bin/env python
"""Test deterministic UUID generation in serializer."""

from py_trees.behaviours import Failure, Running, Success
from py_trees.composites import Selector, Sequence

from talking_trees.adapters.py_trees_adapter import from_py_trees


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
                ],
            ),
            Running(name="Task2"),
        ],
    )

    # Convert twice with deterministic UUIDs
    tt_tree1, _ = from_py_trees(root, name="Test Tree", use_deterministic_uuids=True)
    tt_tree2, _ = from_py_trees(root, name="Test Tree", use_deterministic_uuids=True)

    # Check root UUIDs match
    if tt_tree1.root.node_id == tt_tree2.root.node_id:
        print(" Root UUID is stable:", tt_tree1.root.node_id)
    else:
        print("[X] Root UUID changed!")
        print("  First:", tt_tree1.root.node_id)
        print("  Second:", tt_tree2.root.node_id)
        return False

    # Check all child UUIDs match
    def compare_nodes(node1, node2, path="root"):
        if node1.node_id != node2.node_id:
            print(f"[X] UUID mismatch at {path}")
            print(f"  First: {node1.node_id}")
            print(f"  Second: {node2.node_id}")
            return False

        if len(node1.children) != len(node2.children):
            print(f"[X] Different number of children at {path}")
            return False

        for i, (child1, child2) in enumerate(zip(node1.children, node2.children)):
            if not compare_nodes(child1, child2, f"{path}/{child1.name}"):
                return False

        return True

    if compare_nodes(tt_tree1.root, tt_tree2.root):
        print(" All node UUIDs are stable across conversions")
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
    root1 = Sequence(name="Root", memory=True, children=[Success(name="Task1")])

    # Tree 2 (different structure)
    root2 = Selector(name="Root", memory=False, children=[Success(name="Task1")])

    tt_tree1, _ = from_py_trees(root1, name="Tree1", use_deterministic_uuids=True)
    tt_tree2, _ = from_py_trees(root2, name="Tree2", use_deterministic_uuids=True)

    if tt_tree1.root.node_id != tt_tree2.root.node_id:
        print(" Different structures produce different UUIDs")
        print("  Sequence UUID:", tt_tree1.root.node_id)
        print("  Selector UUID:", tt_tree2.root.node_id)
    else:
        print("[X] Same UUID for different structures!")
        return False

    print()
    return True


def test_random_uuids():
    """Test that random UUIDs are different each time."""
    print("=" * 70)
    print("TEST 3: Random UUIDs (non-deterministic mode)")
    print("=" * 70)

    root = Sequence(name="Root", memory=True, children=[Success(name="Task1")])

    tt_tree1, _ = from_py_trees(root, name="Tree", use_deterministic_uuids=False)
    tt_tree2, _ = from_py_trees(root, name="Tree", use_deterministic_uuids=False)

    if tt_tree1.root.node_id != tt_tree2.root.node_id:
        print(" Random UUIDs are different each time")
        print("  First:", tt_tree1.root.node_id)
        print("  Second:", tt_tree2.root.node_id)
    else:
        print("[X] Random UUIDs are the same (unlikely but possible)")

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
                ],
            ),
        ],
    )

    tt_tree, _ = from_py_trees(root, name="Tree", use_deterministic_uuids=True)

    task1_uuid = tt_tree.root.children[0].node_id
    task2_uuid = tt_tree.root.children[1].children[0].node_id

    if task1_uuid != task2_uuid:
        print(" Same name at different paths → different UUIDs")
        print("  Root/Task:", task1_uuid)
        print("  Root/SubSeq/Task:", task2_uuid)
    else:
        print("[X] Same UUID despite different paths!")
        return False

    print()
    return True


if __name__ == "__main__":
    print("\n Testing Deterministic UUID Generation\n")

    results = []
    results.append(("UUID Stability", test_uuid_stability()))
    results.append(("UUID Determinism", test_uuid_determinism()))
    results.append(("Random UUIDs", test_random_uuids()))
    results.append(("Path Sensitivity", test_path_sensitivity()))

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for name, passed in results:
        status = " PASSED" if passed else "[X] FAILED"
        print(f"{status}: {name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n[PASS] All tests passed! Deterministic UUIDs are working correctly.")
    else:
        print("\n[FAIL] Some tests failed. Check output above.")

    print()
