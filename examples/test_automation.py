"""Test automation tree with real actions.

This demonstrates the complete automation loop:
1. Load tree from JSON
2. External system updates blackboard (simulated sensors)
3. Tree ticks and makes decisions
4. External system reads blackboard and executes (simulated actuators)
"""

import json
import time
from pathlib import Path
from py_forest.core.tree_manager import TreeManager
from py_trees import blackboard


def main():
    """Run the complete test automation loop."""

    # Load tree from JSON file
    tree_path = Path(__file__).parent / "test_tree.json"
    with open(tree_path) as f:
        tree_json = json.load(f)

    print("=" * 70)
    print("PYFOREST AUTOMATION TEST")
    print("=" * 70)
    print(f"Loading tree: {tree_json['metadata']['name']}")
    print(f"Description: {tree_json['metadata']['description']}")
    print()

    # Create tree
    manager = TreeManager()
    tree_id = manager.create_tree_from_dict(tree_json)
    tree = manager.get_tree(tree_id)

    # Get blackboard client for external system
    bb = blackboard.Client(name="ExternalSystem")
    bb.register_key("battery_level", access=blackboard.common.Access.WRITE)
    bb.register_key("object_distance", access=blackboard.common.Access.WRITE)
    bb.register_key("robot_action", access=blackboard.common.Access.READ)
    bb.register_key("tick_count", access=blackboard.common.Access.WRITE)

    print("Initial blackboard state:")
    print(f"  battery_level: {bb.get('battery_level')}")
    print(f"  object_distance: {bb.get('object_distance')}")
    print(f"  robot_action: {bb.get('robot_action')}")
    print()

    # Simulation scenarios
    scenarios = [
        # Scenario 1: Normal patrol
        {"tick": 1, "battery": 100, "distance": 999, "expected": "patrol"},
        {"tick": 2, "battery": 90, "distance": 999, "expected": "patrol"},

        # Scenario 2: Object detected
        {"tick": 3, "battery": 80, "distance": 3.5, "expected": "grasp"},
        {"tick": 4, "battery": 70, "distance": 2.0, "expected": "grasp"},

        # Scenario 3: Low battery (higher priority than object)
        {"tick": 5, "battery": 15, "distance": 3.0, "expected": "charge"},
        {"tick": 6, "battery": 10, "distance": 2.0, "expected": "charge"},

        # Scenario 4: Battery recovered, object still close
        {"tick": 7, "battery": 50, "distance": 4.0, "expected": "grasp"},

        # Scenario 5: Everything normal again
        {"tick": 8, "battery": 80, "distance": 999, "expected": "patrol"},
    ]

    print("-" * 70)
    print("RUNNING SIMULATION")
    print("-" * 70)

    all_passed = True

    for scenario in scenarios:
        tick_num = scenario["tick"]
        battery = scenario["battery"]
        distance = scenario["distance"]
        expected_action = scenario["expected"]

        # STEP 1: External system updates sensors (blackboard)
        bb.set("battery_level", battery)
        bb.set("object_distance", distance)
        bb.set("tick_count", tick_num)

        # STEP 2: Tree ticks and makes decision
        tree.tick_once()

        # STEP 3: External system reads decision (blackboard)
        actual_action = bb.get("robot_action")

        # STEP 4: Verify decision
        status = "✓ PASS" if actual_action == expected_action else "✗ FAIL"
        passed = actual_action == expected_action
        all_passed = all_passed and passed

        print(f"\nTick {tick_num}: {status}")
        print(f"  Sensors: battery={battery}%, distance={distance}m")
        print(f"  Decision: robot_action='{actual_action}'")
        print(f"  Expected: '{expected_action}'")

        if not passed:
            print(f"  ERROR: Expected '{expected_action}' but got '{actual_action}'")

        # STEP 5: Simulate external system executing action
        if actual_action == "charge":
            print(f"  🔋 External system: Robot is charging")
        elif actual_action == "grasp":
            print(f"  🤖 External system: Robot is grasping object")
        elif actual_action == "patrol":
            print(f"  🚶 External system: Robot is patrolling")

        time.sleep(0.3)  # Slow down for readability

    # Summary
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    if all_passed:
        print("✓ ALL TESTS PASSED")
        print()
        print("Key Behaviors Verified:")
        print("  ✓ Selector reactive (memory=false): Re-evaluates priorities each tick")
        print("  ✓ Sequence committed (memory=true): Completes checks in order")
        print("  ✓ Priority system: Low battery > Object detection > Patrol")
        print("  ✓ SetBlackboardVariable: Sets commands for external system")
        print("  ✓ CheckBlackboardCondition: Evaluates sensor conditions")
        print()
        print("🎉 PyForest automation loop working correctly!")
    else:
        print("✗ SOME TESTS FAILED")
        print("Check output above for details")

    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
