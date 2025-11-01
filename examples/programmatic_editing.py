"""
Programmatic Tree Editing Examples
===================================

This demonstrates multiple ways to edit trees programmatically (in code),
without using the visual editor.

Workflow:
  py_trees code → TalkingTrees → JSON → **back to editable code** → TalkingTrees → JSON

You have THREE approaches:
1. Round-trip via py_trees (recommended for complex edits)
2. Direct TreeDefinition manipulation (recommended for simple edits)
3. Hybrid approach (combine both)
"""

import operator
from uuid import uuid4

import py_trees
from py_trees.common import ComparisonExpression

from talking_trees.adapters import to_py_trees
from talking_trees.models.tree import TreeNodeDefinition
from talking_trees.sdk import TalkingTrees

# =============================================================================
# Approach 1: Round-trip via py_trees (Recommended for Complex Edits)
# =============================================================================


def approach_1_py_trees_roundtrip():
    """Load JSON → py_trees → edit → TalkingTrees → save"""
    print("=" * 70)
    print("APPROACH 1: Round-trip via py_trees")
    print("=" * 70)

    # Step 1: Load existing tree from JSON
    print("\nStep 1: Load existing tree from JSON...")
    pf = TalkingTrees()
    tree_def = pf.load_tree("examples/robot_v1.json")
    print(f"✓ Loaded: {tree_def.metadata.name}")
    print(f"  Children: {len(tree_def.root.children)}")

    # Step 2: Convert to py_trees for editing
    print("\nStep 2: Convert to py_trees...")
    pt_root = to_py_trees(tree_def)
    print("✓ Converted to py_trees")
    print(f"  Root: {pt_root.name}")
    print(f"  Children: {len(pt_root.children)}")

    # Step 3: Edit in py_trees (full py_trees API available!)
    print("\nStep 3: Edit with py_trees API...")

    # Add a new emergency stop branch
    emergency_stop = py_trees.composites.Sequence("Emergency Stop", memory=False)

    # Add condition
    critical_check = ComparisonExpression("critical_error", operator.eq, True)
    emergency_stop.add_child(
        py_trees.behaviours.CheckBlackboardVariableValue(
            name="Critical Error?", check=critical_check
        )
    )

    # Add action
    emergency_stop.add_child(
        py_trees.behaviours.SetBlackboardVariable(
            name="Command: Emergency Stop",
            variable_name="robot_action",
            variable_value="emergency_stop",
            overwrite=True,
        )
    )

    # Insert at beginning (highest priority)
    pt_root.children.insert(0, emergency_stop)

    print("✓ Added emergency stop branch")
    print(f"  New children count: {len(pt_root.children)}")

    # Step 4: Convert back to TalkingTrees
    print("\nStep 4: Convert back to TalkingTrees...")
    updated_tree = pf.from_py_trees(
        pt_root,
        name=tree_def.metadata.name + " (Updated)",
        version="2.0.0",
        description="Added emergency stop branch",
    )
    print("✓ Converted to TalkingTrees")
    print(f"  Version: {updated_tree.metadata.version}")

    # Step 5: Save
    print("\nStep 5: Save to JSON...")
    pf.save_tree(updated_tree, "examples/robot_v2_edited.json")
    print("✓ Saved to examples/robot_v2_edited.json")

    print("\n✅ Approach 1 complete!")
    print("   You can now load robot_v2_edited.json and see the new branch")
    print()


# =============================================================================
# Approach 2: Direct TreeDefinition Manipulation (Simple Edits)
# =============================================================================


def approach_2_direct_manipulation():
    """Load JSON → modify TreeDefinition directly → save"""
    print("=" * 70)
    print("APPROACH 2: Direct TreeDefinition Manipulation")
    print("=" * 70)

    # Step 1: Load existing tree
    print("\nStep 1: Load existing tree from JSON...")
    pf = TalkingTrees()
    tree_def = pf.load_tree("examples/robot_v1.json")
    print(f"✓ Loaded: {tree_def.metadata.name}")

    # Step 2: Create new nodes directly
    print("\nStep 2: Create new nodes...")

    # Create a simple success node
    new_node = TreeNodeDefinition(
        node_type="Success",
        node_id=str(uuid4()),
        name="System Check Complete",
        config={},
        children=[],
    )

    print(f"✓ Created node: {new_node.name}")

    # Step 3: Add to tree
    print("\nStep 3: Add to tree...")
    tree_def.root.children.append(new_node)
    print("✓ Added to root")
    print(f"  Total children: {len(tree_def.root.children)}")

    # Step 4: Update metadata
    print("\nStep 4: Update metadata...")
    tree_def.metadata.version = "1.1.0"
    tree_def.metadata.description = "Added system check node"

    # Step 5: Save
    print("\nStep 5: Save...")
    pf.save_tree(tree_def, "examples/robot_v1_direct_edit.json")
    print("✓ Saved to examples/robot_v1_direct_edit.json")

    print("\n✅ Approach 2 complete!")
    print("   Direct manipulation is faster for simple additions")
    print()


# =============================================================================
# Approach 3: Hybrid - Complex Nodes via py_trees, Simple Edits Direct
# =============================================================================


def approach_3_hybrid():
    """Combine both approaches for optimal workflow"""
    print("=" * 70)
    print("APPROACH 3: Hybrid Approach")
    print("=" * 70)

    pf = TalkingTrees()

    # Step 1: Create a complex branch with py_trees
    print("\nStep 1: Create complex branch with py_trees...")

    maintenance_seq = py_trees.composites.Sequence("Maintenance Check", memory=False)

    # Battery check
    battery_check = ComparisonExpression("battery_level", operator.lt, 30)
    maintenance_seq.add_child(
        py_trees.behaviours.CheckBlackboardVariableValue(
            name="Battery Below 30%?", check=battery_check
        )
    )

    # Maintenance action
    maintenance_seq.add_child(
        py_trees.behaviours.SetBlackboardVariable(
            name="Schedule Maintenance",
            variable_name="maintenance_scheduled",
            variable_value=True,
            overwrite=True,
        )
    )

    # Convert just this branch to TalkingTrees
    maintenance_branch = pf.from_py_trees(
        maintenance_seq, name="Maintenance Branch", version="1.0.0"
    )

    print("✓ Created maintenance branch with py_trees")

    # Step 2: Load existing tree
    print("\nStep 2: Load existing tree...")
    tree_def = pf.load_tree("examples/robot_v1.json")

    # Step 3: Insert the complex branch (direct manipulation)
    print("\nStep 3: Insert complex branch...")
    tree_def.root.children.insert(1, maintenance_branch.root)

    # Step 4: Add a simple node (direct manipulation)
    print("\nStep 4: Add simple node...")
    simple_node = TreeNodeDefinition(
        node_type="Success",
        node_id=str(uuid4()),
        name="All Systems Normal",
        config={},
        children=[],
    )
    tree_def.root.children.append(simple_node)

    # Step 5: Update metadata and save
    print("\nStep 5: Update and save...")
    tree_def.metadata.version = "2.1.0"
    tree_def.metadata.description = "Hybrid edit: maintenance branch + system check"

    pf.save_tree(tree_def, "examples/robot_hybrid_edit.json")
    print("✓ Saved to examples/robot_hybrid_edit.json")

    print("\n✅ Approach 3 complete!")
    print("   Use py_trees for complex logic, direct editing for simple nodes")
    print()


# =============================================================================
# Bonus: Helper Functions for Common Operations
# =============================================================================


def add_node_to_tree(tree_def, parent_path, new_node):
    """
    Helper: Add a node at a specific path in the tree

    Args:
        tree_def: TreeDefinition
        parent_path: List of indices [0, 2, 1] = root.children[0].children[2].children[1]
        new_node: TreeNodeDefinition to add
    """
    current = tree_def.root
    for index in parent_path:
        current = current.children[index]
    current.children.append(new_node)


def remove_node_from_tree(tree_def, node_path):
    """
    Helper: Remove a node at a specific path

    Args:
        tree_def: TreeDefinition
        node_path: List of indices to the node to remove
    """
    if not node_path:
        raise ValueError("Cannot remove root node")

    current = tree_def.root
    for index in node_path[:-1]:
        current = current.children[index]

    del current.children[node_path[-1]]


def find_node_by_name(tree_def, name):
    """
    Helper: Find a node by name

    Returns: (node, path) or (None, None)
    """

    def search(node, path):
        if node.name == name:
            return node, path
        for i, child in enumerate(node.children):
            result = search(child, path + [i])
            if result[0]:
                return result
        return None, None

    return search(tree_def.root, [])


def demonstration_with_helpers():
    """Demonstrate helper functions"""
    print("=" * 70)
    print("BONUS: Using Helper Functions")
    print("=" * 70)

    pf = TalkingTrees()
    tree_def = pf.load_tree("examples/robot_v1.json")

    # Find a specific node
    print("\nFinding node by name...")
    node, path = find_node_by_name(tree_def, "Low Battery Handler")
    if node:
        print(f"✓ Found: {node.name} at path {path}")

        # Add a new child to it
        new_child = TreeNodeDefinition(
            node_type="Success",
            node_id=str(uuid4()),
            name="Log Low Battery Event",
            config={},
            children=[],
        )
        add_node_to_tree(tree_def, path, new_child)
        print(f"✓ Added child to {node.name}")

    # Save
    pf.save_tree(tree_def, "examples/robot_helper_demo.json")
    print("\n✓ Saved to examples/robot_helper_demo.json")
    print()


# =============================================================================
# Comparison of Approaches
# =============================================================================


def print_comparison():
    """Print comparison of all approaches"""
    print("=" * 70)
    print("COMPARISON: Which Approach to Use?")
    print("=" * 70)
    print()

    comparison = """
╔════════════════════════════════════════════════════════════════════╗
║                      APPROACH COMPARISON                           ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  Approach 1: Round-trip via py_trees                              ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                  ║
║  ✅ BEST FOR:                                                      ║
║     • Complex tree modifications                                  ║
║     • Adding multiple nodes with logic                            ║
║     • Using py_trees decorators (Inverter, Repeat, etc.)          ║
║     • Restructuring large sections                                ║
║                                                                    ║
║  ⚡ PROS:                                                          ║
║     • Full py_trees API available                                 ║
║     • Type checking and IDE support                               ║
║     • Easier to reason about complex logic                        ║
║                                                                    ║
║  ⚠️  CONS:                                                          ║
║     • Extra conversion step                                       ║
║     • SetBlackboardVariable values lost (need manual add)         ║
║                                                                    ║
║  EXAMPLE:                                                          ║
║     tree_def = pf.load_tree("tree.json")                          ║
║     pt_root = to_py_trees(tree_def)                               ║
║     pt_root.add_child(py_trees.behaviours.Success("New"))         ║
║     updated = pf.from_py_trees(pt_root, "Updated", "2.0")         ║
║     pf.save_tree(updated, "updated.json")                         ║
║                                                                    ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  Approach 2: Direct TreeDefinition Manipulation                   ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║  ✅ BEST FOR:                                                      ║
║     • Simple additions (single nodes)                             ║
║     • Metadata updates                                            ║
║     • Quick modifications                                         ║
║     • Removing nodes                                              ║
║                                                                    ║
║  ⚡ PROS:                                                          ║
║     • Fastest (no conversion)                                     ║
║     • Direct access to all fields                                 ║
║     • No data loss                                                ║
║                                                                    ║
║  ⚠️  CONS:                                                          ║
║     • Manual UUID generation                                      ║
║     • Need to understand TreeNodeDefinition structure             ║
║     • More verbose for complex logic                              ║
║                                                                    ║
║  EXAMPLE:                                                          ║
║     tree_def = pf.load_tree("tree.json")                          ║
║     new_node = TreeNodeDefinition(                                ║
║         node_type="Success",                                      ║
║         node_id=str(uuid4()),                                     ║
║         name="New Node",                                          ║
║         config={}, children=[]                                    ║
║     )                                                              ║
║     tree_def.root.children.append(new_node)                       ║
║     pf.save_tree(tree_def, "updated.json")                        ║
║                                                                    ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  Approach 3: Hybrid                                               ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║  ✅ BEST FOR:                                                      ║
║     • Combining complex + simple edits                            ║
║     • Building complex branches separately                        ║
║     • Optimal workflow efficiency                                 ║
║                                                                    ║
║  ⚡ PROS:                                                          ║
║     • Best of both worlds                                         ║
║     • Maximum flexibility                                         ║
║                                                                    ║
║  ⚠️  CONS:                                                          ║
║     • Need to know both approaches                                ║
║                                                                    ║
║  EXAMPLE:                                                          ║
║     # Complex branch with py_trees                                ║
║     branch = create_complex_branch()                              ║
║     branch_def = pf.from_py_trees(branch, "Branch", "1.0")        ║
║                                                                    ║
║     # Load and modify directly                                    ║
║     tree_def = pf.load_tree("tree.json")                          ║
║     tree_def.root.children.append(branch_def.root)                ║
║     pf.save_tree(tree_def, "updated.json")                        ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
"""
    print(comparison)

    print("\n📊 DECISION MATRIX:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Task                                    | Recommended Approach")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Add single Success/Failure node         | Approach 2 (Direct)")
    print("Add complex Sequence with conditions    | Approach 1 (py_trees)")
    print("Add decorator (Inverter, Repeat, etc.)  | Approach 1 (py_trees)")
    print("Change node name or config              | Approach 2 (Direct)")
    print("Remove a node                           | Approach 2 (Direct)")
    print("Restructure entire branch               | Approach 1 (py_trees)")
    print("Update metadata (version, description)  | Approach 2 (Direct)")
    print("Add multiple related nodes              | Approach 3 (Hybrid)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" PROGRAMMATIC TREE EDITING - Complete Guide")
    print("=" * 70)
    print()
    print("This demonstrates that you DON'T need the visual editor!")
    print("You can edit trees programmatically in multiple ways.")
    print()

    # Run all demonstrations
    approach_1_py_trees_roundtrip()
    approach_2_direct_manipulation()
    approach_3_hybrid()
    demonstration_with_helpers()

    # Show comparison
    print_comparison()

    print("=" * 70)
    print(" Summary")
    print("=" * 70)
    print()
    print("✅ You have MULTIPLE ways to edit trees in code:")
    print("   1. Round-trip via py_trees (best for complex edits)")
    print("   2. Direct TreeDefinition manipulation (best for simple edits)")
    print("   3. Hybrid approach (best for mixed complexity)")
    print()
    print("✅ Files created:")
    print("   • examples/robot_v2_edited.json (Approach 1)")
    print("   • examples/robot_v1_direct_edit.json (Approach 2)")
    print("   • examples/robot_hybrid_edit.json (Approach 3)")
    print("   • examples/robot_helper_demo.json (Helper functions)")
    print()
    print("✅ The visual editor is just ONE option, not the ONLY option!")
    print()
    print("📖 See this file for complete code examples")
    print("🚀 Choose the approach that fits your workflow")
    print()
