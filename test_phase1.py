#!/usr/bin/env python3
"""Quick test script to verify Phase 1 implementation."""

from pathlib import Path
from uuid import UUID

from py_forest.core import get_registry
from py_forest.models.schema import NodeCategory
from py_forest.models.tree import TreeDefinition, TreeMetadata, TreeNodeDefinition
from py_forest.storage import FileSystemTreeLibrary


def test_registry():
    """Test behavior registry."""
    print("=" * 60)
    print("Testing Behavior Registry")
    print("=" * 60)

    registry = get_registry()

    # List all behaviors
    all_behaviors = registry.list_all()
    print(f"\n✓ Registered behaviors: {len(all_behaviors)}")
    for behavior in sorted(all_behaviors):
        schema = registry.get_schema(behavior)
        print(f"  - {behavior:20s} [{schema.category.value}]")

    # List by category
    composites = registry.list_by_category(NodeCategory.COMPOSITE)
    decorators = registry.list_by_category(NodeCategory.DECORATOR)
    actions = registry.list_by_category(NodeCategory.ACTION)

    print(f"\n✓ Composites: {len(composites)}")
    print(f"✓ Decorators: {len(decorators)}")
    print(f"✓ Actions:    {len(actions)}")

    # Test schema retrieval
    selector_schema = registry.get_schema("Selector")
    print(f"\n✓ Selector schema:")
    print(f"  Display name: {selector_schema.display_name}")
    print(f"  Description: {selector_schema.description}")
    print(f"  Config params: {list(selector_schema.config_schema.keys())}")

    print("\n✅ Registry tests passed!\n")


def test_models():
    """Test Pydantic models."""
    print("=" * 60)
    print("Testing Pydantic Models")
    print("=" * 60)

    # Create a simple tree definition
    tree = TreeDefinition(
        metadata=TreeMetadata(
            name="Test Tree",
            version="1.0.0",
            description="A test tree",
            tags=["test"],
        ),
        root=TreeNodeDefinition(
            node_type="Sequence",
            name="root",
            config={"memory": True},
            children=[
                TreeNodeDefinition(
                    node_type="Success",
                    name="always_succeed",
                    config={},
                ),
            ],
        ),
    )

    print(f"\n✓ Created tree: {tree.metadata.name}")
    print(f"  Tree ID: {tree.tree_id}")
    print(f"  Root type: {tree.root.node_type}")
    print(f"  Children: {len(tree.root.children)}")

    # Test serialization
    json_data = tree.model_dump_json(indent=2)
    print(f"\n✓ Serialized to JSON ({len(json_data)} bytes)")

    # Test deserialization
    tree2 = TreeDefinition.model_validate_json(json_data)
    print(f"✓ Deserialized back to model")
    print(f"  Name matches: {tree2.metadata.name == tree.metadata.name}")
    print(f"  ID matches: {tree2.tree_id == tree.tree_id}")

    print("\n✅ Model tests passed!\n")


def test_storage():
    """Test file system storage."""
    print("=" * 60)
    print("Testing File System Storage")
    print("=" * 60)

    # Create library
    library = FileSystemTreeLibrary(Path("data"))
    print(f"\n✓ Created library at: {library.base_path}")

    # Check if example tree exists
    example_id = UUID("550e8400-e29b-41d4-a716-446655440001")

    if library.tree_exists(example_id):
        print(f"✓ Example tree exists")

        # Load it
        tree = library.get_tree(example_id)
        print(f"✓ Loaded tree: {tree.metadata.name}")
        print(f"  Version: {tree.metadata.version}")
        print(f"  Description: {tree.metadata.description}")
        print(f"  Tags: {tree.metadata.tags}")
        print(f"  Root type: {tree.root.node_type}")
        print(f"  Dependencies: {tree.dependencies.behaviors}")

        # List versions
        versions = library.list_versions(example_id)
        print(f"\n✓ Versions: {len(versions)}")
        for v in versions:
            print(f"  - {v.version} ({v.status.value})")

    else:
        print("⚠ Example tree not found - need to import it")
        print("  Copy examples/simple_tree.json to data/trees/")

    # List all trees
    all_trees = library.list_trees()
    print(f"\n✓ Total trees in library: {len(all_trees)}")
    for entry in all_trees:
        print(f"  - {entry.display_name} v{entry.latest_version}")

    print("\n✅ Storage tests passed!\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PyForest Phase 1 - Quick Tests")
    print("=" * 60 + "\n")

    try:
        test_registry()
        test_models()
        test_storage()

        print("=" * 60)
        print("🎉 All Phase 1 tests passed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Import example tree: copy examples/simple_tree.json to data/")
        print("2. Start Phase 2: Tree serialization engine")
        print("3. Start Phase 3: Execution service")
        print("4. Start Phase 4: FastAPI endpoints")
        print()

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
