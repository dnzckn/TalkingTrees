"""
Demonstration of PyForest SDK Features

This example shows how to use the PyForest SDK for:
- Tree validation
- Node search and query
- Statistics and analysis
- Batch operations
- Tree manipulation

Usage:
    python examples/sdk_enhanced_demo.py
"""

from py_forest.sdk import PyForest


def demo_validation():
    """Demonstrate tree validation features."""
    print("=" * 70)
    print("DEMO 1: Tree Validation")
    print("=" * 70)

    pf = PyForest()

    # Create a simple tree (in practice, you'd load from file)
    from uuid import uuid4

    from py_forest.models.tree import TreeDefinition, TreeMetadata, TreeNodeDefinition

    metadata = TreeMetadata(
        name="Demo Tree", version="1.0.0", description="Example for validation demo"
    )

    root = TreeNodeDefinition(
        node_type="Sequence",
        node_id=uuid4(),
        name="Root",
        config={"memory": True},
        children=[
            TreeNodeDefinition(
                node_type="Success", node_id=uuid4(), name="Step1", config={}
            ),
            TreeNodeDefinition(
                node_type="Success", node_id=uuid4(), name="Step2", config={}
            ),
        ],
    )

    tree = TreeDefinition(tree_id=uuid4(), metadata=metadata, root=root)

    # Validate the tree
    result = pf.validate_tree(tree, verbose=True)

    if result.is_valid:
        print("\n✓ Tree is valid and ready for execution!")
    else:
        print(f"\n✗ Tree has {result.error_count} errors")

    print()


def demo_search():
    """Demonstrate node search features."""
    print("=" * 70)
    print("DEMO 2: Node Search & Query")
    print("=" * 70)

    pf = PyForest()

    # Create a more complex tree
    from uuid import uuid4

    from py_forest.models.tree import TreeDefinition, TreeMetadata, TreeNodeDefinition

    metadata = TreeMetadata(name="Search Demo Tree", version="1.0.0")

    root = TreeNodeDefinition(
        node_type="Sequence",
        node_id=uuid4(),
        name="MainSequence",
        config={"memory": True},
        children=[
            TreeNodeDefinition(
                node_type="Timeout",
                node_id=uuid4(),
                name="TimeoutWrapper",
                config={"duration": 10.0},
                children=[
                    TreeNodeDefinition(
                        node_type="Success", node_id=uuid4(), name="Task1", config={}
                    )
                ],
            ),
            TreeNodeDefinition(
                node_type="Timeout",
                node_id=uuid4(),
                name="AnotherTimeout",
                config={"duration": 30.0},
                children=[
                    TreeNodeDefinition(
                        node_type="Success", node_id=uuid4(), name="Task2", config={}
                    )
                ],
            ),
        ],
    )

    tree = TreeDefinition(tree_id=uuid4(), metadata=metadata, root=root)

    # Find all Timeout nodes
    print("\n1. Finding all Timeout nodes...")
    timeouts = pf.find_nodes_by_type(tree, "Timeout")
    print(f"   Found {len(timeouts)} timeout decorators:")
    for node in timeouts:
        print(f"   - {node.name}: {node.config.get('duration')}s")

    # Find long-running timeouts
    print("\n2. Finding timeouts > 20 seconds...")
    long_timeouts = pf.find_nodes(
        tree, lambda n: n.node_type == "Timeout" and n.config.get("duration", 0) > 20
    )
    print(f"   Found {len(long_timeouts)} long timeouts:")
    for node in long_timeouts:
        print(f"   - {node.name}: {node.config.get('duration')}s")

    # Get all nodes
    all_nodes = pf.get_all_nodes(tree)
    print(f"\n3. Total nodes in tree: {len(all_nodes)}")

    # Find by name (partial match)
    print("\n4. Finding nodes with 'Task' in name...")
    task_nodes = pf.find_nodes_by_name(tree, "Task", exact=False)
    print(f"   Found {len(task_nodes)} task nodes:")
    for node in task_nodes:
        print(f"   - {node.name} ({node.node_type})")

    print()


def demo_statistics():
    """Demonstrate tree statistics and analysis."""
    print("=" * 70)
    print("DEMO 3: Tree Statistics & Analysis")
    print("=" * 70)

    pf = PyForest()

    # Create a tree with variety of nodes
    from uuid import uuid4

    from py_forest.models.tree import TreeDefinition, TreeMetadata, TreeNodeDefinition

    metadata = TreeMetadata(name="Statistics Demo", version="1.0.0")

    root = TreeNodeDefinition(
        node_type="Selector",
        node_id=uuid4(),
        name="Root",
        config={},
        children=[
            TreeNodeDefinition(
                node_type="Sequence",
                node_id=uuid4(),
                name="CheckAndAct",
                config={"memory": True},
                children=[
                    TreeNodeDefinition(
                        node_type="Success", node_id=uuid4(), name="Check1", config={}
                    ),
                    TreeNodeDefinition(
                        node_type="Success", node_id=uuid4(), name="Action1", config={}
                    ),
                ],
            ),
            TreeNodeDefinition(
                node_type="Inverter",
                node_id=uuid4(),
                name="InvertResult",
                config={},
                children=[
                    TreeNodeDefinition(
                        node_type="Failure",
                        node_id=uuid4(),
                        name="AlwaysFail",
                        config={},
                    )
                ],
            ),
        ],
    )

    tree = TreeDefinition(tree_id=uuid4(), metadata=metadata, root=root)

    # Get statistics
    print("\nComputing tree statistics...")
    stats = pf.get_tree_stats(tree)
    print(stats.summary())

    # Node type distribution
    print("\n\nNode type distribution:")
    type_counts = pf.count_nodes_by_type(tree)
    for node_type, count in sorted(type_counts.items()):
        print(f"  {node_type}: {count}")

    # Print structure
    print("\n\nTree structure:")
    pf.print_tree_structure(tree, show_config=True)

    print()


def demo_batch_operations():
    """Demonstrate batch loading and validation."""
    print("=" * 70)
    print("DEMO 4: Batch Operations")
    print("=" * 70)

    # Note: This demo shows the API, but requires actual files to run
    # In practice, you would have multiple JSON/YAML files to load

    print("\nBatch operations allow you to:")
    print("  - Load multiple trees in one call")
    print("  - Validate all trees together")
    print("  - Process results efficiently")

    print("\nExample code:")
    print("""
    # Load multiple trees
    trees = pf.load_batch([
        "trees/patrol.json",
        "trees/charge.yaml",
        "trees/explore.json"
    ])

    # Validate all
    results = pf.validate_batch(trees)

    # Process results
    for name, result in results.items():
        status = "✓" if result.is_valid else "✗"
        print(f"{status} {name}: {result.error_count} errors")
    """)

    print()


def demo_tree_manipulation():
    """Demonstrate tree cloning, hashing, and comparison."""
    print("=" * 70)
    print("DEMO 5: Tree Manipulation")
    print("=" * 70)

    pf = PyForest()

    # Create original tree
    from uuid import uuid4

    from py_forest.models.tree import TreeDefinition, TreeMetadata, TreeNodeDefinition

    metadata = TreeMetadata(name="Original", version="1.0.0")
    root = TreeNodeDefinition(
        node_type="Sequence",
        node_id=uuid4(),
        name="Root",
        config={"memory": True},
        children=[
            TreeNodeDefinition(
                node_type="Success", node_id=uuid4(), name="Step1", config={}
            )
        ],
    )
    tree1 = TreeDefinition(tree_id=uuid4(), metadata=metadata, root=root)

    # Clone the tree
    print("\n1. Cloning tree...")
    tree2 = pf.clone_tree(tree1)
    tree2.metadata.name = "Copy"
    tree2.metadata.version = "1.0.1"
    print(f"   Original: {tree1.metadata.name} v{tree1.metadata.version}")
    print(f"   Clone: {tree2.metadata.name} v{tree2.metadata.version}")

    # Compare trees
    print("\n2. Comparing trees...")
    are_equal = pf.trees_equal(tree1, tree2)
    print(f"   Trees structurally equal: {are_equal}")

    # Get content hashes
    print("\n3. Computing content hashes...")
    hash1 = pf.hash_tree(tree1)
    hash2 = pf.hash_tree(tree2)
    print(f"   Tree1 hash: {hash1[:16]}...")
    print(f"   Tree2 hash: {hash2[:16]}...")
    print(f"   Hashes match: {hash1 == hash2}")

    # Modify tree2
    print("\n4. Modifying clone...")
    tree2.root.children.append(
        TreeNodeDefinition(
            node_type="Success", node_id=uuid4(), name="Step2", config={}
        )
    )
    hash2_modified = pf.hash_tree(tree2)
    print(f"   Modified hash: {hash2_modified[:16]}...")
    print(f"   Still equal: {hash1 == hash2_modified}")

    # Get node path
    if tree2.root.children:
        child = tree2.root.children[0]
        path = pf.get_node_path(tree2, child.node_id)
        if path:
            print(f"\n5. Node path for '{child.name}':")
            print(f"   {' -> '.join(path)}")

    print()


def demo_convenience_functions():
    """Demonstrate convenience functions."""
    print("=" * 70)
    print("DEMO 6: Convenience Functions")
    print("=" * 70)

    print("\nQuick validation (requires actual file):")
    print("""
    from py_forest.sdk_enhanced import quick_validate

    result = quick_validate("my_tree.json")
    # Automatically loads, validates, and prints results
    """)

    print("\nQuick tree comparison (requires actual files):")
    print("""
    from py_forest.sdk_enhanced import compare_tree_structures

    if compare_tree_structures("v1.json", "v2.json"):
        print("No structural changes")
    else:
        print("Trees are different")
    """)

    print("\nComplete analysis (requires actual file):")
    print("""
    from py_forest.sdk_enhanced import analyze_tree

    report = analyze_tree("complex_tree.json")
    print(report)
    # Prints: validation + statistics + analysis
    """)

    print()


def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "PyForest Enhanced SDK Demonstration" + " " * 18 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    try:
        demo_validation()
        demo_search()
        demo_statistics()
        demo_batch_operations()
        demo_tree_manipulation()
        demo_convenience_functions()

        print("=" * 70)
        print("✓ All demonstrations completed successfully!")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Read SDK_ENHANCEMENTS.md for full API documentation")
        print("  2. Try the enhanced SDK with your own trees")
        print("  3. Explore the 20+ convenience methods available")
        print()

    except Exception as e:
        print(f"\n✗ Error during demonstration: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
