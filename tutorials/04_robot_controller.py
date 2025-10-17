"""
PyForest SDK Tutorial 4: Complete Robot Controller Example
===========================================================

This tutorial shows a complete, realistic example of using PyForest
to control a simulated robot. We'll cover:

- Building a behavior tree for robot control
- Simulating sensor inputs over time
- Handling state transitions
- Performance monitoring
- Debugging behavior issues

Scenario: Autonomous patrol robot with battery management
- Patrol between waypoints when battery is sufficient
- Return to charging station when battery is low
- Handle emergency conditions
- Log all actions for debugging
"""

from py_forest.sdk import PyForest
from py_forest.core.profiler import ProfilingLevel
from py_forest.models.tree import (
    TreeDefinition, NodeDefinition,
    BlackboardDefinition, BlackboardVariable
)
import uuid
import time
import random
from typing import List, Dict, Tuple

# =============================================================================
# Robot Simulator
# =============================================================================

class RobotSimulator:
    """Simulates a simple robot with battery, position, and sensors"""

    def __init__(self, start_x: float = 0.0, start_y: float = 0.0):
        self.x = start_x
        self.y = start_y
        self.battery = 100.0
        self.charging = False
        self.waypoints = [
            (10.0, 0.0),
            (10.0, 10.0),
            (0.0, 10.0),
            (0.0, 0.0),  # Charging station
        ]
        self.current_waypoint = 0
        self.obstacle_detected = False
        self.mission_complete = False

    def update(self, action: str) -> Dict[str, float]:
        """Update robot state based on action and return sensor readings"""

        # Execute action
        if action == "move_to_waypoint":
            self._move_towards_waypoint()
            self.battery -= 2.0  # Moving costs battery
            self.charging = False

        elif action == "charge":
            if self._at_charging_station():
                self.battery = min(100.0, self.battery + 5.0)
                self.charging = True
            else:
                self.charging = False

        elif action == "return_to_base":
            self._move_towards_base()
            self.battery -= 1.5  # Returning costs less (optimized path)
            self.charging = False

        elif action == "wait":
            self.battery -= 0.1  # Waiting costs minimal battery
            self.charging = False

        # Random events
        if random.random() < 0.05:  # 5% chance of obstacle
            self.obstacle_detected = True
        else:
            self.obstacle_detected = False

        # Clamp battery
        self.battery = max(0.0, min(100.0, self.battery))

        # Check mission status
        if self.current_waypoint == 0 and self._at_waypoint():
            self.mission_complete = True

        return self.get_sensors()

    def _move_towards_waypoint(self):
        """Move towards current waypoint"""
        target = self.waypoints[self.current_waypoint]
        dx = target[0] - self.x
        dy = target[1] - self.y
        dist = (dx**2 + dy**2)**0.5

        if dist < 0.5:  # Reached waypoint
            self.x, self.y = target
            self.current_waypoint = (self.current_waypoint + 1) % len(self.waypoints)
        else:
            # Move 1 unit towards target
            self.x += (dx / dist) * min(1.0, dist)
            self.y += (dy / dist) * min(1.0, dist)

    def _move_towards_base(self):
        """Move towards charging station (0, 0)"""
        dx = 0.0 - self.x
        dy = 0.0 - self.y
        dist = (dx**2 + dy**2)**0.5

        if dist < 0.5:
            self.x, self.y = 0.0, 0.0
        else:
            self.x += (dx / dist) * min(1.5, dist)  # Faster return
            self.y += (dy / dist) * min(1.5, dist)

    def _at_waypoint(self) -> bool:
        """Check if at current waypoint"""
        target = self.waypoints[self.current_waypoint]
        dist = ((target[0] - self.x)**2 + (target[1] - self.y)**2)**0.5
        return dist < 0.5

    def _at_charging_station(self) -> bool:
        """Check if at charging station"""
        return (self.x**2 + self.y**2)**0.5 < 0.5

    def get_sensors(self) -> Dict[str, float]:
        """Get current sensor readings"""
        target = self.waypoints[self.current_waypoint]
        distance = ((target[0] - self.x)**2 + (target[1] - self.y)**2)**0.5

        return {
            "battery_level": self.battery,
            "distance_to_waypoint": distance,
            "at_charging_station": 1.0 if self._at_charging_station() else 0.0,
            "obstacle_detected": 1.0 if self.obstacle_detected else 0.0,
            "position_x": self.x,
            "position_y": self.y,
        }


# =============================================================================
# Build Robot Behavior Tree
# =============================================================================

def build_robot_tree() -> TreeDefinition:
    """Build a complete robot control behavior tree"""

    # Node IDs
    root_id = str(uuid.uuid4())
    emergency_check_id = str(uuid.uuid4())
    emergency_handler_id = str(uuid.uuid4())
    normal_ops_id = str(uuid.uuid4())
    battery_check_id = str(uuid.uuid4())
    low_battery_handler_id = str(uuid.uuid4())
    patrol_id = str(uuid.uuid4())

    # Patrol sub-nodes
    obstacle_check_id = str(uuid.uuid4())
    obstacle_handler_id = str(uuid.uuid4())
    move_id = str(uuid.uuid4())

    # Return to base sub-nodes
    at_base_check_id = str(uuid.uuid4())
    charge_id = str(uuid.uuid4())
    return_id = str(uuid.uuid4())

    nodes = [
        # Root: Selector (try emergency, then normal ops)
        NodeDefinition(
            id=root_id,
            name="Robot Controller",
            node_type="selector",
            parent_id=None,
            properties={}
        ),

        # Emergency Handler (battery critical)
        NodeDefinition(
            id=emergency_check_id,
            name="Emergency Sequence",
            node_type="sequence",
            parent_id=root_id,
            properties={}
        ),
        NodeDefinition(
            id=str(uuid.uuid4()),
            name="Battery Critical?",
            node_type="condition",
            parent_id=emergency_check_id,
            properties={
                "blackboard_key": "battery_level",
                "operator": "less_than",
                "compare_value": 5.0
            }
        ),
        NodeDefinition(
            id=emergency_handler_id,
            name="Emergency Stop",
            node_type="action",
            parent_id=emergency_check_id,
            properties={
                "blackboard_key": "/robot_action",
                "value": "emergency_stop"
            }
        ),

        # Normal Operations
        NodeDefinition(
            id=normal_ops_id,
            name="Normal Operations",
            node_type="selector",
            parent_id=root_id,
            properties={}
        ),

        # Low Battery Handler
        NodeDefinition(
            id=battery_check_id,
            name="Low Battery Sequence",
            node_type="sequence",
            parent_id=normal_ops_id,
            properties={}
        ),
        NodeDefinition(
            id=str(uuid.uuid4()),
            name="Battery Low?",
            node_type="condition",
            parent_id=battery_check_id,
            properties={
                "blackboard_key": "battery_level",
                "operator": "less_than",
                "compare_value": 20.0
            }
        ),
        NodeDefinition(
            id=low_battery_handler_id,
            name="Return to Charge Selector",
            node_type="selector",
            parent_id=battery_check_id,
            properties={}
        ),

        # Charging logic
        NodeDefinition(
            id=at_base_check_id,
            name="At Base Sequence",
            node_type="sequence",
            parent_id=low_battery_handler_id,
            properties={}
        ),
        NodeDefinition(
            id=str(uuid.uuid4()),
            name="At Charging Station?",
            node_type="condition",
            parent_id=at_base_check_id,
            properties={
                "blackboard_key": "at_charging_station",
                "operator": "equals",
                "compare_value": 1.0
            }
        ),
        NodeDefinition(
            id=charge_id,
            name="Charge Battery",
            node_type="action",
            parent_id=at_base_check_id,
            properties={
                "blackboard_key": "/robot_action",
                "value": "charge"
            }
        ),

        # Return to base
        NodeDefinition(
            id=return_id,
            name="Return to Base",
            node_type="action",
            parent_id=low_battery_handler_id,
            properties={
                "blackboard_key": "/robot_action",
                "value": "return_to_base"
            }
        ),

        # Patrol (normal operation)
        NodeDefinition(
            id=patrol_id,
            name="Patrol Sequence",
            node_type="sequence",
            parent_id=normal_ops_id,
            properties={}
        ),

        # Obstacle handling
        NodeDefinition(
            id=obstacle_check_id,
            name="No Obstacle?",
            node_type="condition",
            parent_id=patrol_id,
            properties={
                "blackboard_key": "obstacle_detected",
                "operator": "equals",
                "compare_value": 0.0
            }
        ),
        NodeDefinition(
            id=move_id,
            name="Move to Waypoint",
            node_type="action",
            parent_id=patrol_id,
            properties={
                "blackboard_key": "/robot_action",
                "value": "move_to_waypoint"
            }
        ),
    ]

    # Blackboard definition
    blackboard = BlackboardDefinition(
        variables=[
            BlackboardVariable(
                name="battery_level",
                value_type="float",
                default_value=100.0,
                min_value=0.0,
                max_value=100.0
            ),
            BlackboardVariable(
                name="distance_to_waypoint",
                value_type="float",
                default_value=0.0,
                min_value=0.0
            ),
            BlackboardVariable(
                name="at_charging_station",
                value_type="float",
                default_value=0.0
            ),
            BlackboardVariable(
                name="obstacle_detected",
                value_type="float",
                default_value=0.0
            ),
            BlackboardVariable(
                name="position_x",
                value_type="float",
                default_value=0.0
            ),
            BlackboardVariable(
                name="position_y",
                value_type="float",
                default_value=0.0
            ),
            BlackboardVariable(
                name="/robot_action",
                value_type="string",
                default_value="wait"
            ),
        ]
    )

    tree = TreeDefinition(
        id=str(uuid.uuid4()),
        name="Autonomous Robot Controller",
        version="1.0.0",
        description="Patrol robot with battery management and emergency handling",
        root_id=root_id,
        nodes=nodes,
        blackboard=blackboard
    )

    return tree


# =============================================================================
# Main Simulation
# =============================================================================

def run_simulation():
    """Run complete robot simulation"""
    print("=" * 70)
    print("AUTONOMOUS ROBOT SIMULATION")
    print("=" * 70)
    print()

    # Build and save tree
    print("Building behavior tree...")
    tree = build_robot_tree()
    pf = PyForest()
    pf.save_tree(tree, "tutorials/robot_controller.json")
    print(f"✓ Saved tree to tutorials/robot_controller.json")
    print(f"  Total nodes: {len(tree.nodes)}")
    print(f"  Blackboard vars: {len(tree.blackboard.variables)}")
    print()

    # Create execution with profiling
    print("Starting execution with profiling...")
    execution = pf.create_execution(
        tree,
        profiling_level=ProfilingLevel.BASIC
    )

    # Create robot simulator
    robot = RobotSimulator(start_x=0.0, start_y=0.0)

    # Simulation parameters
    max_ticks = 200
    log_interval = 10

    print(f"Running simulation for {max_ticks} ticks...")
    print("=" * 70)
    print()

    # Simulation loop
    action_history = []

    for tick in range(max_ticks):
        # Get sensor readings
        sensors = robot.get_sensors()

        # Tick behavior tree
        result = execution.tick(blackboard_updates=sensors)

        # Get action from tree
        action = result.blackboard.get("/robot_action", "wait")

        # Update robot based on action
        robot.update(action)

        # Log state
        action_history.append(action)

        if tick % log_interval == 0 or robot.battery < 10:
            print(f"Tick {tick:3d} | "
                  f"Battery: {robot.battery:5.1f}% | "
                  f"Pos: ({robot.x:4.1f}, {robot.y:4.1f}) | "
                  f"Action: {action:20s} | "
                  f"Status: {result.status}")

        # Check termination conditions
        if robot.battery <= 0:
            print("\n⚠ BATTERY DEPLETED - Simulation terminated")
            break

        if robot.mission_complete and robot.battery > 90:
            print("\n✓ MISSION COMPLETE - Robot returned and recharged")
            break

    print()
    print("=" * 70)
    print("SIMULATION COMPLETE")
    print("=" * 70)
    print()

    # Statistics
    print("Statistics:")
    print("-" * 70)
    print(f"  Total ticks: {tick + 1}")
    print(f"  Final battery: {robot.battery:.1f}%")
    print(f"  Final position: ({robot.x:.1f}, {robot.y:.1f})")
    print()

    # Action distribution
    from collections import Counter
    action_counts = Counter(action_history)
    print("Action Distribution:")
    for action, count in action_counts.most_common():
        percentage = (count / len(action_history)) * 100
        print(f"  {action:20s}: {count:4d} times ({percentage:5.1f}%)")
    print()

    # Performance report
    print("Performance Report:")
    print("-" * 70)
    report = execution.get_profiling_report(verbose=True)
    print(report)

    # Save action log
    import json
    log_data = {
        "total_ticks": tick + 1,
        "final_battery": robot.battery,
        "final_position": [robot.x, robot.y],
        "action_history": action_history,
        "action_counts": dict(action_counts)
    }

    with open("tutorials/robot_simulation_log.json", "w") as f:
        json.dump(log_data, f, indent=2)

    print("\n✓ Saved simulation log to tutorials/robot_simulation_log.json")


# =============================================================================
# Debugging Example
# =============================================================================

def debug_specific_scenario():
    """Debug a specific scenario step-by-step"""
    print("\n" + "=" * 70)
    print("DEBUGGING EXAMPLE: Low Battery Scenario")
    print("=" * 70)
    print()

    pf = PyForest(profiling_level=ProfilingLevel.DETAILED)
    tree = pf.load_tree("tutorials/robot_controller.json")
    execution = pf.create_execution(tree)

    # Create scenario: robot far from base with low battery
    robot = RobotSimulator(start_x=10.0, start_y=10.0)
    robot.battery = 15.0  # Low battery!

    print("Initial Conditions:")
    print(f"  Position: ({robot.x}, {robot.y})")
    print(f"  Battery: {robot.battery}%")
    print(f"  Distance to base: {(robot.x**2 + robot.y**2)**0.5:.1f}")
    print()

    print("Watching behavior tree decisions...")
    print("-" * 70)

    for i in range(20):
        sensors = robot.get_sensors()
        result = execution.tick(blackboard_updates=sensors)
        action = result.blackboard.get("/robot_action")

        robot.update(action)

        print(f"Tick {i:2d}: Battery {robot.battery:5.1f}% | "
              f"Pos ({robot.x:4.1f}, {robot.y:4.1f}) | "
              f"Action: {action:20s} | "
              f"Tip: {result.tip_node}")

        if robot.battery <= 0:
            print("\n💀 Robot ran out of battery before reaching base!")
            break

        if sensors["at_charging_station"] == 1.0 and robot.battery > 50:
            print("\n✓ Successfully returned to base and recharged!")
            break

    print()


# =============================================================================
# Run Everything
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" PyForest SDK Tutorial 4: Complete Robot Controller")
    print("=" * 70 + "\n")

    # Run main simulation
    run_simulation()

    # Run debugging example
    debug_specific_scenario()

    print("=" * 70)
    print(" Tutorial Complete! 🎉")
    print("=" * 70)
    print("\nWhat you learned:")
    print("  ✓ Building complex behavior trees programmatically")
    print("  ✓ Integrating with simulation/real systems")
    print("  ✓ Using profiling to monitor performance")
    print("  ✓ Debugging specific scenarios")
    print("  ✓ Logging and analyzing behavior patterns")
    print("\nFiles created:")
    print("  • tutorials/robot_controller.json - Behavior tree")
    print("  • tutorials/robot_simulation_log.json - Simulation log")
    print()
