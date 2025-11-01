"""
Minimal Working Example: py_trees → TalkingTrees Integration
=========================================================

This example demonstrates the TESTED and WORKING functionality
of the py_trees adapter.

What works:
- Creating trees with py_trees API
- Converting to TalkingTrees format
- Saving to JSON
- Loading from JSON
- Visualizing in TalkingTrees editor

What's NOT in this example (needs more work):
- Blackboard conditions (py_trees API changed)
- SetBlackboardVariable (needs testing)
- Complex decorators (needs testing)

For advanced features, see TESTING_STATUS.md
"""

import py_trees

from talking_trees.sdk import TalkingTrees


def create_simple_tree():
    """Create a simple behavior tree using py_trees"""
    print("Creating behavior tree with py_trees...")

    # Root selector
    root = py_trees.composites.Selector(name="Robot Controller", memory=False)

    # Branch 1: Emergency sequence
    emergency = py_trees.composites.Sequence(name="Emergency Handler", memory=False)
    emergency.add_child(py_trees.behaviours.Success(name="Detect Emergency"))
    emergency.add_child(py_trees.behaviours.Success(name="Stop Robot"))
    emergency.add_child(py_trees.behaviours.Success(name="Alert Operator"))

    # Branch 2: Normal operation sequence
    normal = py_trees.composites.Sequence(name="Normal Operation", memory=False)
    normal.add_child(py_trees.behaviours.Success(name="Check Systems"))
    normal.add_child(py_trees.behaviours.Success(name="Execute Task"))
    normal.add_child(py_trees.behaviours.Success(name="Report Status"))

    # Branch 3: Idle
    idle = py_trees.behaviours.Success(name="Idle Mode")

    # Add branches to root
    root.add_child(emergency)
    root.add_child(normal)
    root.add_child(idle)

    print(f"✓ Created tree with {len(root.children)} top-level branches")
    return root


def convert_to_talkingtrees(py_trees_root):
    """Convert py_trees tree to TalkingTrees format"""
    print("\nConverting to TalkingTrees format...")

    pf = TalkingTrees()
    tt_tree = pf.from_py_trees(
        py_trees_root,
        name="Robot Controller",
        version="1.0.0",
        description="Simple robot controller created with py_trees",
    )

    print("✓ Converted to TalkingTrees")
    print(f"  Tree: {tt_tree.metadata.name} v{tt_tree.metadata.version}")
    print(f"  Root type: {tt_tree.root.node_type}")
    print(f"  Root children: {len(tt_tree.root.children)}")

    return tt_tree


def save_and_load(tt_tree):
    """Save tree to JSON and load it back"""
    print("\nSaving to JSON...")

    pf = TalkingTrees()
    output_path = "examples/py_trees_robot.json"

    pf.save_tree(tt_tree, output_path)
    print(f"✓ Saved to {output_path}")

    # Load it back
    loaded = pf.load_tree(output_path)
    print(f"✓ Loaded back: {loaded.metadata.name}")

    return loaded


def visualize_structure(tt_tree):
    """Print the tree structure"""
    print("\nTree Structure:")
    print("=" * 60)

    def print_node(node, indent=0):
        print("  " * indent + f"- {node.name} ({node.node_type})")
        for child in node.children:
            print_node(child, indent + 1)

    print_node(tt_tree.root)
    print("=" * 60)


def main():
    print("=" * 60)
    print(" Minimal Working Example: py_trees → TalkingTrees")
    print("=" * 60)

    # Step 1: Create tree with py_trees
    py_trees_root = create_simple_tree()

    # Step 2: Convert to TalkingTrees
    tt_tree = convert_to_talkingtrees(py_trees_root)

    # Step 3: Save and load
    loaded_tree = save_and_load(tt_tree)

    # Step 4: Show structure
    visualize_structure(loaded_tree)

    print("\n" + "=" * 60)
    print(" Success! ✓")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Open visualization/tree_editor_pro.html in a browser")
    print("  2. Load examples/py_trees_robot.json")
    print("  3. View your tree visually!")
    print("\nFor advanced features, see TESTING_STATUS.md")
    print()


if __name__ == "__main__":
    main()
