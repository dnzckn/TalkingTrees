"""
PyForest SDK Tutorial 3: Version Control & Tree Diffing
========================================================

This tutorial covers how to use PyForest's version control features:
- Compare different versions of behavior trees
- Understand what changed between versions
- Merge trees intelligently
- Track tree evolution over time

Perfect for:
- Code review workflows
- Understanding team changes
- Debugging behavior changes
- Maintaining tree history
"""

from py_forest.sdk import PyForest, diff_files
from py_forest.core.diff import diff_trees, merge_trees, DiffFormat
import json

# =============================================================================
# Example 1: Basic Tree Comparison
# =============================================================================

def example_1_basic_diff():
    """Compare two versions of a tree"""
    print("=" * 70)
    print("EXAMPLE 1: Basic Tree Diff - What Changed?")
    print("=" * 70)

    pf = PyForest()

    # Load both versions
    tree_v1 = pf.load_tree("examples/robot_v1.json")
    tree_v2 = pf.load_tree("examples/robot_v2.json")

    print(f"Tree V1: {tree_v1.name} v{tree_v1.version}")
    print(f"Tree V2: {tree_v2.name} v{tree_v2.version}")
    print()

    # Perform diff
    diff_result = pf.diff_trees(tree_v1, tree_v2, verbose=True)
    print(diff_result)


# =============================================================================
# Example 2: Using the Convenience Function
# =============================================================================

def example_2_diff_files():
    """Quick diff using the convenience function"""
    print("=" * 70)
    print("EXAMPLE 2: Quick Diff - One-Liner Comparison")
    print("=" * 70)

    # One-liner: compare files directly
    diff_output = diff_files("examples/robot_v1.json", "examples/robot_v2.json")
    print(diff_output)


# =============================================================================
# Example 3: Detailed Change Analysis
# =============================================================================

def example_3_detailed_analysis():
    """Analyze specific types of changes"""
    print("=" * 70)
    print("EXAMPLE 3: Detailed Change Analysis")
    print("=" * 70)

    from py_forest.core.diff import diff_trees

    pf = PyForest()
    tree_v1 = pf.load_tree("examples/robot_v1.json")
    tree_v2 = pf.load_tree("examples/robot_v2.json")

    # Get raw diff data structure
    diff_result = diff_trees(tree_v1, tree_v2, semantic_matching=True)

    # Analyze changes
    print("Change Summary:")
    print("-" * 70)
    print(f"  Added nodes: {len(diff_result.added_nodes)}")
    print(f"  Removed nodes: {len(diff_result.removed_nodes)}")
    print(f"  Modified nodes: {len(diff_result.modified_nodes)}")
    print(f"  Moved nodes: {len(diff_result.moved_nodes)}")
    print()

    # Show added nodes
    if diff_result.added_nodes:
        print("Added Nodes:")
        for node in diff_result.added_nodes:
            print(f"  + {node.name} ({node.node_type})")
        print()

    # Show removed nodes
    if diff_result.removed_nodes:
        print("Removed Nodes:")
        for node in diff_result.removed_nodes:
            print(f"  - {node.name} ({node.node_type})")
        print()

    # Show modified nodes with details
    if diff_result.modified_nodes:
        print("Modified Nodes:")
        for mod in diff_result.modified_nodes:
            print(f"  ~ {mod.node_name} ({mod.node_type})")
            for change in mod.changes:
                print(f"    • {change.property_name}: {change.old_value} → {change.new_value}")
        print()

    # Show moved nodes
    if diff_result.moved_nodes:
        print("Moved Nodes:")
        for move in diff_result.moved_nodes:
            print(f"  ↔ {move.node_name}")
            print(f"    Old parent: {move.old_parent_path}")
            print(f"    New parent: {move.new_parent_path}")
        print()

    # Blackboard changes
    if diff_result.blackboard_changes:
        print("Blackboard Changes:")
        if diff_result.blackboard_changes.added_variables:
            print("  Added variables:")
            for var in diff_result.blackboard_changes.added_variables:
                print(f"    + {var}")
        if diff_result.blackboard_changes.removed_variables:
            print("  Removed variables:")
            for var in diff_result.blackboard_changes.removed_variables:
                print(f"    - {var}")
        if diff_result.blackboard_changes.modified_variables:
            print("  Modified variables:")
            for var, changes in diff_result.blackboard_changes.modified_variables.items():
                print(f"    ~ {var}: {changes}")
        print()


# =============================================================================
# Example 4: Semantic vs UUID Matching
# =============================================================================

def example_4_matching_strategies():
    """Understand semantic matching vs UUID matching"""
    print("=" * 70)
    print("EXAMPLE 4: Matching Strategies - Semantic vs UUID")
    print("=" * 70)

    pf = PyForest()
    tree_v1 = pf.load_tree("examples/robot_v1.json")
    tree_v2 = pf.load_tree("examples/robot_v2.json")

    print("Why Semantic Matching?")
    print("-" * 70)
    print("When you export a tree from the visual editor, node UUIDs might")
    print("change. Semantic matching uses (name + type + parent) to match")
    print("nodes, making diffs more meaningful.")
    print()

    # Semantic matching (default)
    print("With Semantic Matching (recommended):")
    diff_semantic = pf.diff_trees(tree_v1, tree_v2, semantic=True, verbose=False)
    print(diff_semantic)

    # Note: UUID-only matching would show everything as changed if UUIDs differ
    print("\nSemantic matching signature: {name}|{type}|{parent_path}")
    print("This gracefully handles UUID changes between versions.")
    print()


# =============================================================================
# Example 5: Tree Merging
# =============================================================================

def example_5_merging():
    """Merge changes from two tree versions"""
    print("=" * 70)
    print("EXAMPLE 5: Tree Merging - Combining Changes")
    print("=" * 70)

    from py_forest.core.diff import merge_trees

    pf = PyForest()
    base_tree = pf.load_tree("examples/robot_v1.json")
    version_a = pf.load_tree("examples/robot_v2.json")

    # For this example, we'll merge v2 back into v1 (trivial example)
    print("Attempting to merge changes...")
    print(f"  Base: {base_tree.name} v{base_tree.version}")
    print(f"  Their version: {version_a.name} v{version_a.version}")
    print()

    try:
        merged_tree, conflicts = merge_trees(
            base_tree,
            base_tree,  # Our version (same as base for simplicity)
            version_a   # Their version
        )

        if conflicts:
            print(f"⚠ Merge completed with {len(conflicts)} conflicts:")
            for conflict in conflicts:
                print(f"  • {conflict.node_name}: {conflict.conflict_type}")
                print(f"    Our value: {conflict.our_value}")
                print(f"    Their value: {conflict.their_value}")
        else:
            print("✓ Merge completed successfully with no conflicts!")

        print(f"\nMerged tree has {len(merged_tree.nodes)} nodes")

        # Save merged result
        pf.save_tree(merged_tree, "tutorials/merged_tree.json")
        print("✓ Saved merged tree to tutorials/merged_tree.json")

    except Exception as e:
        print(f"Merge failed: {e}")

    print()


# =============================================================================
# Example 6: Version History Tracking
# =============================================================================

def example_6_version_history():
    """Track tree evolution through multiple versions"""
    print("=" * 70)
    print("EXAMPLE 6: Version History - Tracking Evolution")
    print("=" * 70)

    from py_forest.models.tree import TreeDefinition, NodeDefinition
    import uuid

    pf = PyForest()

    # Create v1.0.0
    root_id = str(uuid.uuid4())
    tree_v1 = TreeDefinition(
        id=str(uuid.uuid4()),
        name="Feature Tree",
        version="1.0.0",
        description="Initial version",
        root_id=root_id,
        nodes=[
            NodeDefinition(
                id=root_id,
                name="Root",
                node_type="sequence",
                parent_id=None,
                properties={}
            )
        ]
    )
    pf.save_tree(tree_v1, "tutorials/feature_v1.json")
    print("✓ Created v1.0.0 (1 node)")

    # Create v1.1.0 - add a child
    child_id = str(uuid.uuid4())
    tree_v1_1 = TreeDefinition(
        id=tree_v1.id,
        name="Feature Tree",
        version="1.1.0",
        description="Added condition check",
        root_id=root_id,
        nodes=tree_v1.nodes + [
            NodeDefinition(
                id=child_id,
                name="Check Status",
                node_type="condition",
                parent_id=root_id,
                properties={"blackboard_key": "status", "operator": "equals", "compare_value": "ready"}
            )
        ]
    )
    pf.save_tree(tree_v1_1, "tutorials/feature_v1_1.json")
    print("✓ Created v1.1.0 (added Check Status node)")

    # Create v2.0.0 - major refactor
    tree_v2 = TreeDefinition(
        id=tree_v1.id,
        name="Feature Tree",
        version="2.0.0",
        description="Refactored to use selector",
        root_id=root_id,
        nodes=[
            NodeDefinition(
                id=root_id,
                name="Root",
                node_type="selector",  # Changed from sequence!
                parent_id=None,
                properties={}
            ),
            NodeDefinition(
                id=child_id,
                name="Check Status",
                node_type="condition",
                parent_id=root_id,
                properties={"blackboard_key": "status", "operator": "equals", "compare_value": "active"}  # Changed value!
            )
        ]
    )
    pf.save_tree(tree_v2, "tutorials/feature_v2.json")
    print("✓ Created v2.0.0 (changed root to selector, updated condition)")
    print()

    # Show evolution
    print("Version History:")
    print("-" * 70)

    # v1.0.0 → v1.1.0
    print("\nv1.0.0 → v1.1.0:")
    diff = pf.diff_trees(tree_v1, tree_v1_1, verbose=False)
    print(diff)

    # v1.1.0 → v2.0.0
    print("\nv1.1.0 → v2.0.0:")
    diff = pf.diff_trees(tree_v1_1, tree_v2, verbose=False)
    print(diff)


# =============================================================================
# Example 7: Integration with Git
# =============================================================================

def example_7_git_integration():
    """Use PyForest diffs in a Git-based workflow"""
    print("=" * 70)
    print("EXAMPLE 7: Git Integration - Version Control Workflow")
    print("=" * 70)

    print("Recommended Git Workflow:")
    print("-" * 70)
    print()

    print("1. Track .json tree files in Git")
    print("   git add examples/*.json")
    print("   git commit -m 'Update robot behavior tree'")
    print()

    print("2. Review changes before committing")
    print("   python -c \"from py_forest.sdk import diff_files;")
    print("              print(diff_files('old.json', 'new.json'))\"")
    print()

    print("3. Use in PR descriptions")
    print("   # In your pull request description:")
    print("   ## Behavior Tree Changes")
    print("   ```")
    print("   [paste diff output here]")
    print("   ```")
    print()

    print("4. Create a Git pre-commit hook (optional)")
    print("   .git/hooks/pre-commit:")
    print("   #!/bin/bash")
    print("   python scripts/validate_trees.py")
    print()

    print("5. Tag releases with version numbers")
    print("   git tag -a v1.0.0 -m 'Release robot controller v1.0.0'")
    print()

    # Example: Create a validation script
    validation_script = '''#!/usr/bin/env python3
"""
Validate all behavior trees before commit
Usage: Run automatically via Git pre-commit hook
"""
from py_forest.sdk import PyForest
import sys
from pathlib import Path

pf = PyForest()
errors = []

# Find all tree JSON files
for tree_file in Path("examples").glob("*.json"):
    try:
        tree = pf.load_tree(str(tree_file))
        print(f"✓ {tree_file.name}: {tree.name} v{tree.version}")
    except Exception as e:
        errors.append(f"✗ {tree_file.name}: {e}")
        print(f"✗ {tree_file.name}: {e}")

if errors:
    print(f"\\n❌ {len(errors)} tree(s) failed validation")
    sys.exit(1)
else:
    print(f"\\n✓ All trees valid")
    sys.exit(0)
'''

    with open("tutorials/validate_trees.py", "w") as f:
        f.write(validation_script)

    print("✓ Created example validation script: tutorials/validate_trees.py")
    print()


# =============================================================================
# Example 8: Diff Output Formats
# =============================================================================

def example_8_output_formats():
    """Explore different diff output formats"""
    print("=" * 70)
    print("EXAMPLE 8: Diff Output Formats")
    print("=" * 70)

    from py_forest.core.diff import diff_trees, DiffFormat

    pf = PyForest()
    tree_v1 = pf.load_tree("examples/robot_v1.json")
    tree_v2 = pf.load_tree("examples/robot_v2.json")

    # Text format (default - human readable)
    print("TEXT FORMAT (human-readable):")
    print("-" * 70)
    text_diff = diff_trees(tree_v1, tree_v2, output_format=DiffFormat.TEXT)
    print(text_diff.to_text(verbose=False))
    print()

    # JSON format (machine-readable)
    print("JSON FORMAT (machine-readable):")
    print("-" * 70)
    json_diff = diff_trees(tree_v1, tree_v2, output_format=DiffFormat.JSON)
    json_output = json_diff.to_json(indent=2)
    print(json_output[:500] + "..." if len(json_output) > 500 else json_output)
    print()

    # Save JSON diff for external tools
    with open("tutorials/tree_diff.json", "w") as f:
        f.write(json_output)
    print("✓ Saved JSON diff to tutorials/tree_diff.json")
    print("  (Can be consumed by external tools, CI/CD, etc.)")
    print()


# =============================================================================
# Run All Examples
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" PyForest SDK Tutorial 3: Version Control & Tree Diffing")
    print("=" * 70 + "\n")

    example_1_basic_diff()
    example_2_diff_files()
    example_3_detailed_analysis()
    example_4_matching_strategies()
    example_5_merging()
    example_6_version_history()
    example_7_git_integration()
    example_8_output_formats()

    print("=" * 70)
    print(" Tutorial Complete! 🎉")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  ✓ Use semantic matching to handle UUID changes")
    print("  ✓ Track .json tree files in Git for version control")
    print("  ✓ Use diff_files() for quick comparisons")
    print("  ✓ Use merge_trees() for three-way merges")
    print("  ✓ Export to JSON format for CI/CD integration")
    print("\nNext: tutorial 04_robot_controller.py for a complete example")
    print()
