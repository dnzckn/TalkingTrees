"""
Round-Trip Comparison Example
==============================

Demonstrates how to verify that py_trees -> TalkingTrees -> py_trees conversion
preserves tree structure and behavior using compare_py_trees().

This answers the question: "Are these two trees functionally identical?"
"""

import py_trees

from talking_trees.adapters import compare_py_trees, from_py_trees, to_py_trees
from talking_trees.sdk import TalkingTrees


def example_basic_comparison():
    """Basic comparison of original and round-trip trees."""
    print("=" * 70)
    print("Example 1: Basic Round-Trip Comparison")
    print("=" * 70)

    # Create original py_trees root
    root = py_trees.composites.Sequence(
        name="Main",
        memory=False,
        children=[
            py_trees.behaviours.Success(name="Task1"),
            py_trees.behaviours.Success(name="Task2"),
        ],
    )

    # Convert to TalkingTrees
    tt_tree, context = from_py_trees(root, name="My Tree", version="1.0.0")

    # Save and load (optional - demonstrates full round-trip)
    tt = TalkingTrees()
    tt.save_tree(tt_tree, "my_tree.json")
    loaded = tt.load_tree("my_tree.json")

    # Convert back to py_trees
    py_trees_root = to_py_trees(loaded)

    # Compare the trees
    print("\n1. Simple comparison (returns True/False):")
    is_equivalent = compare_py_trees(root, py_trees_root)
    if is_equivalent:
        print("    Trees are functionally identical!")
    else:
        print("   [X] Trees differ!")

    print("\n2. Verbose comparison (shows details):")
    compare_py_trees(root, py_trees_root, verbose=True)

    print("\n3. Object identity check:")
    print(f"   root is py_trees_root: {root is py_trees_root}")
    print(f"   root == py_trees_root: {root == py_trees_root}")
    print("   (They are different objects in memory, but functionally equivalent)")

    print()


def example_detect_differences():
    """Demonstrate detection of differences between trees."""
    print("=" * 70)
    print("Example 2: Detecting Differences")
    print("=" * 70)

    # Create two similar but different trees
    root1 = py_trees.composites.Sequence(
        name="Main",
        memory=True,  # Note: memory=True
        children=[
            py_trees.behaviours.Success(name="Task1"),
            py_trees.behaviours.Success(name="Task2"),
        ],
    )

    root2 = py_trees.composites.Sequence(
        name="Main",
        memory=False,  # Note: memory=False (different!)
        children=[
            py_trees.behaviours.Success(name="Task1"),
            py_trees.behaviours.Success(name="Task2"),
        ],
    )

    print("\nComparing two trees with different 'memory' parameters:")
    is_equivalent = compare_py_trees(root1, root2, verbose=True)

    if not is_equivalent:
        print("\nAs expected, they differ in the 'memory' parameter!")

    print()


def example_complex_tree():
    """Demonstrate comparison with complex trees including decorators."""
    print("=" * 70)
    print("Example 3: Complex Tree with Decorators")
    print("=" * 70)

    # Create complex tree
    root = py_trees.composites.Selector(
        name="Root",
        memory=False,
        children=[
            py_trees.decorators.Timeout(
                name="TimeoutTask",
                child=py_trees.behaviours.Success(name="LongTask"),
                duration=5.0,
            ),
            py_trees.decorators.Retry(
                name="RetryTask",
                child=py_trees.behaviours.Success(name="FlakeyTask"),
                num_failures=3,
            ),
        ],
    )

    # Round-trip
    tt_tree, _ = from_py_trees(root, name="Complex", version="1.0")
    py_trees_root = to_py_trees(tt_tree)

    # Compare
    print("\nComparing complex tree with decorators:")
    is_equivalent = compare_py_trees(root, py_trees_root, verbose=True)

    if is_equivalent:
        print("\n All decorator parameters preserved correctly!")

    print()


def example_assertion_mode():
    """Demonstrate assertion mode (raises on difference)."""
    print("=" * 70)
    print("Example 4: Assertion Mode")
    print("=" * 70)

    # Create tree
    root = py_trees.composites.Sequence(
        name="Main",
        memory=True,
        children=[py_trees.behaviours.Success(name="Task1")],
    )

    # Round-trip
    tt_tree, _ = from_py_trees(root, name="Test", version="1.0")
    py_trees_root = to_py_trees(tt_tree)

    # Assert equivalence (raises ValueError if different)
    print("\nTrying assertion mode:")
    try:
        compare_py_trees(root, py_trees_root, raise_on_difference=True)
        print(" No exception raised - trees are equivalent!")
    except ValueError as e:
        print(f"[X] Exception raised: {e}")

    print()


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Round-Trip Comparison Examples" + " " * 23 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    example_basic_comparison()
    example_detect_differences()
    example_complex_tree()
    example_assertion_mode()

    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print()
    print("The compare_py_trees() function answers the question:")
    print('"Are these two py_trees roots functionally identical?"')
    print()
    print("Key points:")
    print("  • root == py_trees_root returns False (different objects)")
    print("  • compare_py_trees(root, py_trees_root) returns True (same structure)")
    print("  • Use verbose=True to see detailed comparison")
    print("  • Use raise_on_difference=True for assertions in tests")
    print()
    print("Usage:")
    print("  from talking_trees.adapters import compare_py_trees")
    print("  is_same = compare_py_trees(root1, root2)")
    print()


if __name__ == "__main__":
    main()
