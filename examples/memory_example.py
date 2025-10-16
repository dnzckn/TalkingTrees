"""Example demonstrating memory in PyForest behavior trees.

Shows:
1. Blackboard memory (persistent state)
2. Composite memory (resume vs restart)
3. External system interaction
"""

import time
from py_forest.core.tree_manager import TreeManager
from py_trees import blackboard

def run_memory_example():
    """Demonstrate how memory works in behavior trees."""

    # Load tree with initial blackboard state
    tree_json = {
        "$schema": "1.0.0",
        "tree_id": "memory-demo",
        "metadata": {
            "name": "Memory Demo",
            "version": "1.0.0"
        },
        # Initial memory state
        "blackboard_schema": {
            "battery_level": {"type": "int", "default": 100},
            "robot_action": {"type": "string", "default": "idle"},
            "tick_count": {"type": "int", "default": 0}
        },
        "root": {
            "node_type": "Selector",
            "name": "Robot Controller",
            "config": {"memory": False},  # Re-evaluate every tick
            "children": [
                {
                    "node_type": "Sequence",
                    "name": "Low Battery",
                    "config": {"memory": True},
                    "children": [
                        {
                            "node_type": "CheckBlackboardCondition",
                            "name": "Check Battery",
                            "config": {
                                "variable": "battery_level",
                                "operator_str": "<",
                                "value": 20
                            }
                        },
                        {
                            "node_type": "SetBlackboardVariable",
                            "name": "Command Charge",
                            "config": {
                                "variable": "robot_action",
                                "value": "charge"
                            }
                        }
                    ]
                },
                {
                    "node_type": "SetBlackboardVariable",
                    "name": "Default Action",
                    "config": {
                        "variable": "robot_action",
                        "value": "patrol"
                    }
                }
            ]
        }
    }

    # Create tree
    manager = TreeManager()
    tree_id = manager.create_tree_from_dict(tree_json)
    tree = manager.get_tree(tree_id)

    # Get blackboard client
    bb = blackboard.Client()
    bb.register_key("battery_level", access=blackboard.common.Access.WRITE)
    bb.register_key("robot_action", access=blackboard.common.Access.READ)
    bb.register_key("tick_count", access=blackboard.common.Access.WRITE)

    print("=" * 60)
    print("MEMORY EXAMPLE: Blackboard Persistence")
    print("=" * 60)

    # Simulate robot running
    for tick in range(10):
        # External system updates blackboard (sensors)
        battery = 100 - (tick * 10)  # Drains 10% per tick
        bb.set("battery_level", battery)
        bb.set("tick_count", tick)

        # Tree ticks (makes decision)
        tree.tick_once()

        # External system reads blackboard (actuators)
        action = bb.get("robot_action")

        print(f"\nTick {tick + 1}:")
        print(f"  Battery: {battery}%")
        print(f"  Decision: {action}")

        # Simulate robot executing action
        if action == "charge":
            print(f"  🔋 Robot is charging!")
        elif action == "patrol":
            print(f"  🚶 Robot is patrolling")

        time.sleep(0.5)

    print("\n" + "=" * 60)
    print("MEMORY DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\nKey Points:")
    print("1. Blackboard persisted state across all ticks")
    print("2. External code updated battery_level each tick")
    print("3. Tree read battery, decided action, wrote robot_action")
    print("4. External code read robot_action and executed")
    print("5. Memory parameter controlled Sequence resume behavior")


if __name__ == "__main__":
    run_memory_example()
