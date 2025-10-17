"""Test script for tree diff functionality."""

import json
from uuid import uuid4

from py_forest.core.diff import TreeDiffer, format_diff_as_text
from py_forest.models.tree import (
    BlackboardVariableSchema,
    TreeDefinition,
    TreeMetadata,
    TreeNodeDefinition,
    UIMetadata,
)


def create_version_1() -> TreeDefinition:
    """Create first version of test tree."""
    # Simple robot controller
    root = TreeNodeDefinition(
        node_type="Selector",
        name="Robot Controller",
        config={"memory": False},
        children=[
            TreeNodeDefinition(
                node_type="Sequence",
                name="Low Battery Handler",
                config={"memory": True},
                children=[
                    TreeNodeDefinition(
                        node_type="CheckBlackboardCondition",
                        name="Battery Check",
                        config={
                            "variable": "battery_level",
                            "operator": "<",
                            "value": 20,
                        },
                    ),
                    TreeNodeDefinition(
                        node_type="SetBlackboardVariable",
                        name="Command: Charge",
                        config={
                            "variable": "robot_action",
                            "value": "charge",
                        },
                    ),
                ],
            ),
            TreeNodeDefinition(
                node_type="Sequence",
                name="Object Detection",
                config={"memory": True},
                children=[
                    TreeNodeDefinition(
                        node_type="CheckBlackboardCondition",
                        name="Distance Check",
                        config={
                            "variable": "object_distance",
                            "operator": "<",
                            "value": 5,
                        },
                    ),
                    TreeNodeDefinition(
                        node_type="SetBlackboardVariable",
                        name="Command: Grasp",
                        config={
                            "variable": "robot_action",
                            "value": "grasp",
                        },
                    ),
                ],
            ),
            TreeNodeDefinition(
                node_type="SetBlackboardVariable",
                name="Command: Patrol",
                config={
                    "variable": "robot_action",
                    "value": "patrol",
                },
            ),
        ],
    )

    tree = TreeDefinition(
        metadata=TreeMetadata(
            name="Robot Controller",
            version="1.0.0",
            description="Basic robot automation",
            tags=["robot", "automation"],
        ),
        root=root,
        blackboard_schema={
            "battery_level": BlackboardVariableSchema(
                type="float",
                default=100.0,
                min=0.0,
                max=100.0,
            ),
            "object_distance": BlackboardVariableSchema(
                type="float",
                default=999.0,
            ),
            "robot_action": BlackboardVariableSchema(
                type="string",
                default="idle",
            ),
        },
    )

    return tree


def create_version_2() -> TreeDefinition:
    """Create second version with modifications."""
    # Modified version with:
    # - Changed battery threshold from 20 to 15
    # - Added new emergency handler sequence
    # - Changed patrol to "explore"
    # - Added temperature monitoring

    root = TreeNodeDefinition(
        node_type="Selector",
        name="Robot Controller v2",  # CHANGED: name
        config={"memory": False},
        children=[
            # NEW: Emergency handler
            TreeNodeDefinition(
                node_type="Sequence",
                name="Emergency Handler",
                config={"memory": True},
                children=[
                    TreeNodeDefinition(
                        node_type="CheckBlackboardCondition",
                        name="Temperature Check",
                        config={
                            "variable": "temperature",
                            "operator": ">",
                            "value": 80,
                        },
                    ),
                    TreeNodeDefinition(
                        node_type="SetBlackboardVariable",
                        name="Command: Shutdown",
                        config={
                            "variable": "robot_action",
                            "value": "emergency_shutdown",
                        },
                    ),
                ],
            ),
            TreeNodeDefinition(
                node_type="Sequence",
                name="Low Battery Handler",
                config={"memory": True},
                children=[
                    TreeNodeDefinition(
                        node_type="CheckBlackboardCondition",
                        name="Battery Check",
                        config={
                            "variable": "battery_level",
                            "operator": "<",
                            "value": 15,  # CHANGED: from 20 to 15
                        },
                    ),
                    TreeNodeDefinition(
                        node_type="SetBlackboardVariable",
                        name="Command: Charge",
                        config={
                            "variable": "robot_action",
                            "value": "charge",
                        },
                    ),
                ],
            ),
            TreeNodeDefinition(
                node_type="Sequence",
                name="Object Detection",
                config={"memory": True},
                children=[
                    TreeNodeDefinition(
                        node_type="CheckBlackboardCondition",
                        name="Distance Check",
                        config={
                            "variable": "object_distance",
                            "operator": "<",
                            "value": 5,
                        },
                    ),
                    TreeNodeDefinition(
                        node_type="SetBlackboardVariable",
                        name="Command: Grasp",
                        config={
                            "variable": "robot_action",
                            "value": "grasp",
                        },
                    ),
                ],
            ),
            TreeNodeDefinition(
                node_type="SetBlackboardVariable",
                name="Command: Explore",  # CHANGED: from "Patrol"
                config={
                    "variable": "robot_action",
                    "value": "explore",  # CHANGED: from "patrol"
                },
            ),
        ],
    )

    tree = TreeDefinition(
        metadata=TreeMetadata(
            name="Robot Controller",
            version="2.0.0",  # CHANGED: version bump
            description="Enhanced robot automation with emergency handling",  # CHANGED
            tags=["robot", "automation", "safety"],  # CHANGED: added "safety"
        ),
        root=root,
        blackboard_schema={
            "battery_level": BlackboardVariableSchema(
                type="float",
                default=100.0,
                min=0.0,
                max=100.0,
            ),
            "object_distance": BlackboardVariableSchema(
                type="float",
                default=999.0,
            ),
            "robot_action": BlackboardVariableSchema(
                type="string",
                default="idle",
            ),
            # NEW: temperature variable
            "temperature": BlackboardVariableSchema(
                type="float",
                default=25.0,
                min=0.0,
                max=100.0,
            ),
        },
    )

    return tree


def main():
    """Run diff tests."""
    print("=" * 80)
    print("TREE DIFF TEST")
    print("=" * 80)
    print()

    # Create two versions
    print("Creating version 1.0.0...")
    v1 = create_version_1()
    print(f"  Root: {v1.root.name}")
    print(f"  Children: {len(v1.root.children)}")
    print(f"  Blackboard vars: {len(v1.blackboard_schema)}")
    print()

    print("Creating version 2.0.0...")
    v2 = create_version_2()
    print(f"  Root: {v2.root.name}")
    print(f"  Children: {len(v2.root.children)}")
    print(f"  Blackboard vars: {len(v2.blackboard_schema)}")
    print()

    # Compute diff
    print("Computing diff...")
    differ = TreeDiffer()
    diff = differ.diff_trees(v1, v2, semantic=True)
    print()

    # Show summary
    print("DIFF SUMMARY:")
    summary = diff.summary
    print(f"  Added nodes:          {summary['added']}")
    print(f"  Removed nodes:        {summary['removed']}")
    print(f"  Modified nodes:       {summary['modified']}")
    print(f"  Moved nodes:          {summary['moved']}")
    print(f"  Metadata changes:     {summary['metadata_changes']}")
    print(f"  Blackboard changes:   {summary['blackboard_changes']}")
    print()

    # Show detailed diff
    print("DETAILED DIFF:")
    print(format_diff_as_text(diff, verbose=False))
    print()

    # Show JSON representation
    print("JSON DIFF (first 3 node diffs):")
    json_diff = {
        "summary": diff.summary,
        "node_diffs": [
            {
                "node_id": str(nd.node_id),
                "name": nd.name,
                "node_type": nd.node_type,
                "diff_type": nd.diff_type.value,
                "path": nd.path,
                "property_count": len(nd.property_diffs),
            }
            for nd in diff.node_diffs[:3]
        ],
    }
    print(json.dumps(json_diff, indent=2))
    print()

    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print()
    print("Expected changes:")
    print("  ✓ Root name: 'Robot Controller' → 'Robot Controller v2'")
    print("  ✓ Battery threshold: 20 → 15")
    print("  ✓ Added emergency handler (2 nodes)")
    print("  ✓ Patrol → Explore (name and value)")
    print("  ✓ Added temperature blackboard variable")
    print("  ✓ Metadata: version 1.0.0 → 2.0.0")
    print("  ✓ Metadata: added 'safety' tag")
    print()


if __name__ == "__main__":
    main()
