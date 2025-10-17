"""
PyForest Tutorial 6: Complete Workflow - Design, Export, Control
===================================================================

This is THE DEFINITIVE TUTORIAL showing the complete PyForest workflow:

1. Design trees visually in Tree Editor Pro
2. Use "Copy Python" button to get ready-to-use code
3. Load tree in Python
4. Use tree to control a real system (robot simulator)

This tutorial demonstrates the recommended workflow for PyForest:
- Visual design for rapid prototyping
- Python integration for real control
- Complete simulation showing actual usage

WORKFLOW:
---------
Visual Editor → Copy Python Button → Python Code → Control System
"""

import time
import random
from py_forest.sdk import PyForest

# =============================================================================
# STEP 1: Simple Robot Simulator
# =============================================================================

class SimpleRobot:
    """
    A simple robot simulator to demonstrate using behavior trees
    for real control systems.

    The robot has:
    - Battery level (drains over time)
    - Position (can move)
    - Status (patrol, charging, emergency)
    """

    def __init__(self):
        self.battery = 100.0
        self.x = 0.0
        self.y = 0.0
        self.charging = False
        self.status = "idle"

    def get_sensors(self):
        """Get current sensor readings (inputs to behavior tree)"""
        return {
            "battery_level": self.battery,
            "position_x": self.x,
            "position_y": self.y,
            "is_charging": 1.0 if self.charging else 0.0
        }

    def execute_action(self, action):
        """Execute action from behavior tree (outputs)"""

        if action == "patrol":
            # Move and use battery
            self.x += random.uniform(-1, 1)
            self.y += random.uniform(-1, 1)
            self.battery -= 2.0
            self.charging = False
            self.status = "patrolling"

        elif action == "charge":
            # Charge battery (only at base 0,0)
            distance_to_base = (self.x**2 + self.y**2)**0.5
            if distance_to_base < 2.0:
                self.battery = min(100.0, self.battery + 5.0)
                self.charging = True
                self.status = "charging"
            else:
                self.status = "moving_to_base"

        elif action == "return_to_base":
            # Move towards base
            dx = 0.0 - self.x
            dy = 0.0 - self.y
            distance = (dx**2 + dy**2)**0.5
            if distance > 0.1:
                self.x += (dx / distance) * 1.5
                self.y += (dy / distance) * 1.5
            self.battery -= 1.0
            self.charging = False
            self.status = "returning"

        elif action == "emergency_stop":
            # Emergency stop
            self.charging = False
            self.status = "emergency"

        else:
            # Default: wait
            self.battery -= 0.1
            self.status = "idle"

        # Clamp battery
        self.battery = max(0.0, min(100.0, self.battery))


# =============================================================================
# STEP 2: Load Tree from Visual Editor
# =============================================================================

def load_tree_from_editor():
    """
    WORKFLOW STEP:
    ===============

    Before running this script:

    1. Run: ./run_editor.sh
    2. Design your tree in Tree Editor Pro (or load examples/robot_v1.json)
    3. Click "🐍 Copy Python" button
    4. Choose "📄 Load from JSON File"
    5. Click "Export" to save robot_controller.json
    6. Run this script!

    The tree should have:
    - Selector root (try emergency, then battery check, then patrol)
    - Emergency handler (if battery < 5%, emergency stop)
    - Battery handler (if battery < 20%, return to charge)
    - Patrol behavior (move around)
    """

    print("=" * 70)
    print("STEP 2: Loading Tree from Visual Editor")
    print("=" * 70)
    print()

    pf = PyForest()

    # Try to load tree exported from visual editor
    try:
        tree = pf.load_tree("robot_controller.json")
        print(f"✓ Loaded tree: {tree.metadata.name}")
        print(f"  Version: {tree.metadata.version}")
        print(f"  Description: {tree.metadata.description or 'No description'}")
        print()
        return tree

    except FileNotFoundError:
        print("⚠️  robot_controller.json not found!")
        print()
        print("To create it:")
        print("  1. Run: ./run_editor.sh")
        print("  2. Load examples/robot_v1.json")
        print("  3. Click 'Export' button to save as robot_controller.json")
        print()
        print("For now, using examples/robot_v1.json directly...")
        print()

        # Fallback to example file
        tree = pf.load_tree("examples/robot_v1.json")
        print(f"✓ Loaded tree: {tree.metadata.name}")
        print()
        return tree


# =============================================================================
# STEP 3: Use Tree to Control Robot
# =============================================================================

def control_robot_with_tree():
    """
    THIS IS THE CRITICAL PART:
    ==========================

    This shows how to USE a behavior tree to actually CONTROL something!

    The pattern:
    1. Get sensor readings from system
    2. Tick behavior tree with sensor data
    3. Read action from behavior tree output
    4. Execute action on system
    5. Repeat

    This is the control loop pattern used in robotics, game AI, automation, etc.
    """

    print("=" * 70)
    print("STEP 3: Using Tree to Control Robot")
    print("=" * 70)
    print()

    # Load tree
    pf = PyForest()
    tree = load_tree_from_editor()

    # Create execution
    execution = pf.create_execution(tree)
    print("✓ Created execution")
    print()

    # Create robot
    robot = SimpleRobot()
    print("✓ Created robot simulator")
    print(f"  Initial battery: {robot.battery}%")
    print(f"  Initial position: ({robot.x:.1f}, {robot.y:.1f})")
    print()

    # =========================================================================
    # THE CONTROL LOOP: This is where the magic happens!
    # =========================================================================

    print("=" * 70)
    print("CONTROL LOOP: Tree → Decisions → Robot Actions")
    print("=" * 70)
    print()

    max_ticks = 100
    log_interval = 5

    print(f"Running for {max_ticks} ticks...")
    print("-" * 70)
    print()

    for tick in range(max_ticks):
        # 1. Get sensor readings from robot
        sensors = robot.get_sensors()

        # 2. Tick behavior tree with sensor data
        result = execution.tick(blackboard_updates=sensors)

        # 3. Read action from tree output
        action = result.blackboard.get("/robot_action", "wait")

        # 4. Execute action on robot
        robot.execute_action(action)

        # 5. Log state
        if tick % log_interval == 0 or robot.battery < 15:
            print(f"Tick {tick:3d} | "
                  f"Battery: {robot.battery:5.1f}% | "
                  f"Pos: ({robot.x:5.1f}, {robot.y:5.1f}) | "
                  f"Action: {action:20s} | "
                  f"Status: {robot.status:15s}")

        # Check termination
        if robot.battery <= 0:
            print()
            print("⚠️  BATTERY DEPLETED - Stopping simulation")
            break

        if robot.battery > 95 and robot.charging:
            print()
            print("✓ FULLY CHARGED - Mission can continue")
            break

    print()
    print("-" * 70)
    print()

    # Summary
    print("SIMULATION SUMMARY:")
    print(f"  Total ticks: {tick + 1}")
    print(f"  Final battery: {robot.battery:.1f}%")
    print(f"  Final position: ({robot.x:.1f}, {robot.y:.1f})")
    print(f"  Final status: {robot.status}")
    print()


# =============================================================================
# STEP 4: Understanding the Code from "Copy Python" Button
# =============================================================================

def demonstrate_copy_python_workflow():
    """
    When you click "Copy Python" in Tree Editor Pro, you get code like this.
    This shows what that code does and why it's useful.
    """

    print("=" * 70)
    print("STEP 4: Understanding 'Copy Python' Button Output")
    print("=" * 70)
    print()

    print("When you click '🐍 Copy Python' in the editor, you get code like:")
    print()
    print("=" * 70)
    print("""
from py_forest.sdk import PyForest

# Initialize PyForest SDK
pf = PyForest()

# Load tree from JSON file
tree = pf.load_tree("robot_controller.json")

# Create execution
execution = pf.create_execution(tree)

# Run with sensor updates
result = execution.tick(blackboard_updates={
    "battery_level": 50,
    "position_x": 10.0,
    "position_y": 5.0
})

print(f"Result: {result.status}")
print(f"Action: {result.blackboard.get('/robot_action')}")
""")
    print("=" * 70)
    print()

    print("This code:")
    print("  1. Loads your tree from the JSON file you exported")
    print("  2. Creates an execution (running instance)")
    print("  3. Ticks the tree with sensor data")
    print("  4. Reads the action output")
    print()

    print("You then integrate this into your control loop!")
    print()


# =============================================================================
# STEP 5: Complete Example with Different Scenarios
# =============================================================================

def test_scenarios():
    """
    Test different scenarios to show how the tree adapts
    """

    print("=" * 70)
    print("STEP 5: Testing Different Scenarios")
    print("=" * 70)
    print()

    pf = PyForest()

    try:
        tree = pf.load_tree("robot_controller.json")
    except FileNotFoundError:
        tree = pf.load_tree("examples/robot_v1.json")

    # Scenario 1: Normal operation
    print("Scenario 1: Normal Operation (Battery: 80%)")
    print("-" * 70)

    execution = pf.create_execution(tree)
    result = execution.tick(blackboard_updates={"battery_level": 80.0})
    action = result.blackboard.get("/robot_action")

    print(f"  Tree Decision: {action}")
    print(f"  Expected: patrol or similar")
    print()

    # Scenario 2: Low battery
    print("Scenario 2: Low Battery (Battery: 15%)")
    print("-" * 70)

    execution = pf.create_execution(tree)
    result = execution.tick(blackboard_updates={"battery_level": 15.0})
    action = result.blackboard.get("/robot_action")

    print(f"  Tree Decision: {action}")
    print(f"  Expected: return_to_base or charge")
    print()

    # Scenario 3: Critical battery
    print("Scenario 3: Critical Battery (Battery: 3%)")
    print("-" * 70)

    execution = pf.create_execution(tree)
    result = execution.tick(blackboard_updates={"battery_level": 3.0})
    action = result.blackboard.get("/robot_action")

    print(f"  Tree Decision: {action}")
    print(f"  Expected: emergency_stop")
    print()


# =============================================================================
# RUN EVERYTHING
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" PyForest Tutorial 6: Complete Workflow")
    print(" Design → Export → Control")
    print("=" * 70 + "\n")

    print("This tutorial shows:")
    print("  ✓ How to design trees in the visual editor")
    print("  ✓ How to use 'Copy Python' button")
    print("  ✓ How to load trees in Python")
    print("  ✓ HOW TO ACTUALLY USE TREES TO CONTROL SYSTEMS")
    print()

    input("Press Enter to start...")
    print()

    # Step 1: Explain workflow
    demonstrate_copy_python_workflow()

    input("Press Enter to continue...")
    print()

    # Step 2: Test scenarios
    test_scenarios()

    input("Press Enter to run full simulation...")
    print()

    # Step 3: Run full control simulation
    control_robot_with_tree()

    print("=" * 70)
    print(" Tutorial Complete! 🎉")
    print("=" * 70)
    print()

    print("What you learned:")
    print("  ✓ Complete workflow from visual design to robot control")
    print("  ✓ How 'Copy Python' button generates ready-to-use code")
    print("  ✓ The control loop pattern: sensors → tree → actions")
    print("  ✓ How to test different scenarios")
    print("  ✓ How to integrate behavior trees into real systems")
    print()

    print("Key Takeaway:")
    print("  Behavior trees make decisions. Your code executes them.")
    print("  1. Get sensors → 2. Tick tree → 3. Get action → 4. Execute")
    print()

    print("Next Steps:")
    print("  • Design your own tree in Tree Editor Pro")
    print("  • Export it and use it to control your system")
    print("  • Use the 'Copy Python' button for quick integration")
    print()

    print("📖 See examples/robot_v1.json and robot_v2.json for reference trees")
    print("🚀 Run: ./run_editor.sh to start designing!")
    print()
