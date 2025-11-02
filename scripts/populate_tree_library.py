#!/usr/bin/env python3
"""Populate the tree library with all example trees."""

import sys

sys.path.insert(0, 'src')

import json
from pathlib import Path
from uuid import uuid4

from talking_trees.storage.filesystem import FileSystemTreeLibrary


def populate_library():
    """Populate the library with all example trees."""

    # Initialize library
    data_path = Path("data")
    library = FileSystemTreeLibrary(data_path)

    # Get all example tree files
    examples_dir = Path("examples/trees")
    tree_files = sorted(examples_dir.glob("*.json"))

    print(f"Found {len(tree_files)} example trees")
    print("=" * 80)

    for tree_file in tree_files:
        print(f"\nLoading: {tree_file.name}")

        # Load tree JSON
        with open(tree_file) as f:
            tree_data = json.load(f)

        # Ensure tree has proper structure
        if 'tree_id' not in tree_data:
            tree_data['tree_id'] = str(uuid4())

        # Parse as TreeDefinition
        from talking_trees.models.tree import TreeDefinition
        tree_def = TreeDefinition(**tree_data)

        # Save to library
        library.save_tree(tree_def)

        print(f"  [PASS] Saved: {tree_def.metadata.name} (v{tree_def.metadata.version})")
        print(f"  Tree ID: {tree_def.tree_id}")
        print(f"  Status: {tree_def.metadata.status}")
        if tree_def.metadata.tags:
            print(f"  Tags: {', '.join(tree_def.metadata.tags)}")

    # List all trees in library
    print("\n" + "=" * 80)
    print("TREE LIBRARY SUMMARY")
    print("=" * 80)

    all_trees = library.list_trees()
    print(f"Total trees: {len(all_trees)}\n")

    for i, entry in enumerate(all_trees, 1):
        print(f"{i:2d}. {entry.tree_name} (v{entry.latest_version})")
        print(f"    Status: {entry.status}")
        if entry.description:
            print(f"    Description: {entry.description}")
        if entry.tags:
            print(f"    Tags: {', '.join(entry.tags)}")
        print()

    print("=" * 80)
    print("[PASS] Tree library populated successfully!")
    print("=" * 80)

if __name__ == '__main__':
    populate_library()
