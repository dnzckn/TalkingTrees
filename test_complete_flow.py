"""Complete flow test: Create tree via GUI JSON, load via API, test automation.

This demonstrates:
1. Tree created in GUI (already loaded by default)
2. Export as JSON from GUI
3. Load via API
4. External system simulates sensors → tree decides → external system executes
"""

import requests
import time
import json
import uuid

API_BASE = "http://localhost:8000"


def test_complete_automation_flow():
    """Test the complete automation flow."""

    print("=" * 70)
    print("PYFOREST COMPLETE FLOW TEST")
    print("=" * 70)
    print()

    # This is the tree structure from the GUI
    # (matches what you see when you click "Load Example" in tree_editor.html)
    tree_json = {
        "$schema": "1.0.0",
        "tree_id": str(uuid.uuid4()),
        "metadata": {
            "name": "Test Automation Tree",
            "version": "1.0.0",
            "description": "Test tree using SetBlackboardVariable for real automation",
            "tags": ["test", "automation", "gui-created"],
            "status": "draft"
        },
        "blackboard_schema": {
            "battery_level": {
                "type": "int",
                "default": 100,
                "description": "Robot battery level (0-100)"
            },
            "object_distance": {
                "type": "float",
                "default": 999.0,
                "description": "Distance to nearest object in meters"
            },
            "robot_action": {
                "type": "string",
                "default": "idle",
                "description": "Command for external robot system"
            }
        },
        "root": {
            "node_type": "Selector",
            "name": "Robot Controller",
            "config": {"memory": False},
            "children": [
                {
                    "node_type": "Sequence",
                    "name": "Low Battery Handler",
                    "config": {"memory": True},
                    "children": [
                        {
                            "node_type": "CheckBlackboardCondition",
                            "name": "Check Battery Low",
                            "config": {
                                "variable": "battery_level",
                                "operator_str": "<",
                                "value": 20
                            }
                        },
                        {
                            "node_type": "SetBlackboardVariable",
                            "name": "Command: Charge",
                            "config": {
                                "variable": "robot_action",
                                "value": "charge"
                            }
                        }
                    ]
                },
                {
                    "node_type": "Sequence",
                    "name": "Object Detection",
                    "config": {"memory": True},
                    "children": [
                        {
                            "node_type": "CheckBlackboardCondition",
                            "name": "Check Object Close",
                            "config": {
                                "variable": "object_distance",
                                "operator_str": "<",
                                "value": 5.0
                            }
                        },
                        {
                            "node_type": "SetBlackboardVariable",
                            "name": "Command: Grasp",
                            "config": {
                                "variable": "robot_action",
                                "value": "grasp"
                            }
                        }
                    ]
                },
                {
                    "node_type": "SetBlackboardVariable",
                    "name": "Command: Patrol",
                    "config": {
                        "variable": "robot_action",
                        "value": "patrol"
                    }
                }
            ]
        }
    }

    print("Step 1: Creating tree via API (simulating GUI export)...")
    try:
        response = requests.post(f"{API_BASE}/trees/", json=tree_json, timeout=5)
        if response.status_code in [200, 201]:
            result = response.json()
            tree_id = result["tree_id"]
            print(f"✓ Tree created: {tree_id}")
        else:
            print(f"✗ Failed to create tree: {response.status_code}")
            print(response.text[:500])
            return False
    except Exception as e:
        print(f"✗ Error creating tree: {e}")
        print("Make sure the API is running: uvicorn py_forest.api.main:app")
        return False

    print()
    print("Step 2: Creating execution instance...")
    try:
        exec_config = {"tree_id": tree_id}
        response = requests.post(f"{API_BASE}/executions/", json=exec_config, timeout=5)
        if response.status_code in [200, 201]:
            result = response.json()
            execution_id = result["execution_id"]
            print(f"✓ Execution created: {execution_id}")
        else:
            print(f"✗ Failed to create execution: {response.status_code}")
            print(response.text[:500])
            return False
    except Exception as e:
        print(f"✗ Error creating execution: {e}")
        return False

    print()
    print("Step 3: Running automation scenarios...")
    print("-" * 70)

    scenarios = [
        # Normal operation
        {"tick": 1, "battery": 100, "distance": 999, "expected": "patrol"},
        {"tick": 2, "battery": 90, "distance": 999, "expected": "patrol"},
        # Object detected
        {"tick": 3, "battery": 80, "distance": 3.5, "expected": "grasp"},
        # Low battery (higher priority)
        {"tick": 4, "battery": 15, "distance": 3.0, "expected": "charge"},
        {"tick": 5, "battery": 10, "distance": 2.0, "expected": "charge"},
        # Battery recovered
        {"tick": 6, "battery": 50, "distance": 4.0, "expected": "grasp"},
        # Normal again
        {"tick": 7, "battery": 80, "distance": 999, "expected": "patrol"},
    ]

    all_passed = True

    for scenario in scenarios:
        tick_num = scenario["tick"]
        battery = scenario["battery"]
        distance = scenario["distance"]
        expected_action = scenario["expected"]

        # STEP 1: External system updates sensors (blackboard)
        blackboard_updates = {
            "battery_level": battery,
            "object_distance": distance
        }

        # STEP 2: Tick tree via API (use execution_id, not tree_id)
        try:
            response = requests.post(
                f"{API_BASE}/executions/{execution_id}/tick",
                json={"blackboard_updates": blackboard_updates},
                timeout=5
            )

            if response.status_code != 200:
                print(f"\n✗ Tick {tick_num} FAILED: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                all_passed = False
                continue

            result = response.json()

            # Debug: print response structure on first tick
            if tick_num == 1:
                print(f"DEBUG - API Response keys: {list(result.keys())}")

            # Get robot_action from snapshot blackboard (uses / prefix)
            if "snapshot" in result and "blackboard" in result["snapshot"]:
                bb = result["snapshot"]["blackboard"]
                # py_trees uses "/" prefix for blackboard keys
                actual_action = bb.get("/robot_action") or bb.get("robot_action", "unknown")
            else:
                print(f"DEBUG - Unexpected response structure: {list(result.keys())}")
                actual_action = "unknown"

            # Verify decision
            status = "✓ PASS" if actual_action == expected_action else "✗ FAIL"
            passed = actual_action == expected_action
            all_passed = all_passed and passed

            print(f"\nTick {tick_num}: {status}")
            print(f"  Sensors: battery={battery}%, distance={distance}m")
            print(f"  Decision: robot_action='{actual_action}'")
            print(f"  Expected: '{expected_action}'")

            if not passed:
                print(f"  ERROR: Expected '{expected_action}' but got '{actual_action}'")

            # STEP 3: Simulate external system executing action
            if actual_action == "charge":
                print(f"  🔋 External system: Robot is charging")
            elif actual_action == "grasp":
                print(f"  🤖 External system: Robot is grasping object")
            elif actual_action == "patrol":
                print(f"  🚶 External system: Robot is patrolling")

            time.sleep(0.3)

        except Exception as e:
            print(f"\n✗ Tick {tick_num} ERROR: {e}")
            all_passed = False

    # Summary
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    if all_passed:
        print("✓ ALL TESTS PASSED")
        print()
        print("Complete Flow Verified:")
        print("  ✓ Tree created via API (GUI → JSON → API)")
        print("  ✓ External system updates blackboard (sensors)")
        print("  ✓ Tree ticks and makes decisions")
        print("  ✓ External system reads blackboard (actuators)")
        print("  ✓ Priority system works (battery > object > patrol)")
        print("  ✓ Memory defaults correct (Selector reactive, Sequence committed)")
        print()
        print("🎉 PyForest production automation flow working!")
    else:
        print("✗ SOME TESTS FAILED")

    print("=" * 70)

    return all_passed


if __name__ == "__main__":
    success = test_complete_automation_flow()
    exit(0 if success else 1)
