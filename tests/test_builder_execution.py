"""Builder execution tests.

Verifies that TalkingTrees builders create executable py_trees nodes.
These are lightweight tests that don't require the API server.

Focus: Test the builder contract, not comprehensive execution testing.
       Comprehensive execution is py_trees' responsibility.
"""

import operator
from uuid import uuid4

import py_trees
import pytest

from talking_trees.adapters import to_py_trees
from talking_trees.models.tree import TreeDefinition, TreeMetadata, TreeNodeDefinition


def test_comparison_expression_builder_creates_executable_node():
    """Test that ComparisonExpression builder creates an executable node.

    This is a regression test for the ComparisonExpression parameter order bug.
    If builders create broken nodes, this will catch it immediately.
    """
    # Create a tree definition with a comparison node
    tree_def = TreeDefinition(
        tree_id=uuid4(),
        metadata=TreeMetadata(
            name="Comparison Execution Test",
            version="1.0.0",
        ),
        root=TreeNodeDefinition(
            node_type="Sequence",
            node_id=uuid4(),
            name="Test Sequence",
            config={"memory": False},
            children=[
                TreeNodeDefinition(
                    node_type="CheckBlackboardCondition",
                    node_id=uuid4(),
                    name="Battery Low?",
                    config={
                        "variable": "battery_level",
                        "operator": "<",
                        "value": 20,
                    },
                    children=[],
                ),
                TreeNodeDefinition(
                    node_type="Log",
                    node_id=uuid4(),
                    name="Log Low Battery",
                    config={"message": "Battery is low!"},
                    children=[],
                ),
            ],
        ),
    )

    # Build py_trees from definition (uses builders)
    root = to_py_trees(tree_def)

    # Setup tree
    bt = py_trees.trees.BehaviourTree(root)
    bt.setup()

    # Test 1: Low battery (should succeed)
    client = py_trees.blackboard.Client(name="test")
    client.register_key(key="battery_level", access=py_trees.common.Access.WRITE)
    client.set("battery_level", 10)

    bt.tick()

    assert bt.root.status == py_trees.common.Status.SUCCESS, (
        "Low battery (10 < 20) should succeed"
    )
    check_node = bt.root.children[0]
    assert check_node.status == py_trees.common.Status.SUCCESS, (
        "Comparison node should succeed for battery_level=10"
    )

    # Test 2: Normal battery (should fail)
    client.set("battery_level", 50)
    bt.tick()

    assert bt.root.status == py_trees.common.Status.FAILURE, (
        "Normal battery (50 < 20) should fail"
    )
    check_node = bt.root.children[0]
    assert check_node.status == py_trees.common.Status.FAILURE, (
        "Comparison node should fail for battery_level=50"
    )

    print(" ComparisonExpression builder creates executable nodes")


# Note: We only need one test to demonstrate the builder contract.
# More extensive execution testing is py_trees' responsibility.
# The ComparisonExpression test above is sufficient as a regression test.


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Builder Execution Test")
    print("=" * 70)

    test_comparison_expression_builder_creates_executable_node()

    print("\n" + "=" * 70)
    print("[PASS] Builder execution test passed!")
    print("=" * 70)
