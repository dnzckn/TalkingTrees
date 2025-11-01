"""
TalkingTrees Tutorial 2: Complete Workflow - Design, Export, Control
===================================================================

This is THE DEFINITIVE TUTORIAL showing BOTH approaches to behavior trees:

APPROACH 1: CODE-FIRST (Programmatic)
--------------------------------------
1. Create tree using py_trees Python code (from scratch!)
2. Convert to TalkingTrees format
3. Use tree to control robot

APPROACH 2: VISUAL-FIRST (Recommended for beginners)
-----------------------------------------------------
1. Design trees visually in Tree Editor Pro
2. Use "Copy Python" button to get ready-to-use code
3. Load tree in Python
4. Use tree to control robot

This tutorial demonstrates:
- Creating trees entirely from Python code (py_trees)
- Visual design for rapid prototyping
- Complete integration with real systems
- THE CONTROL LOOP PATTERN (most important!)
"""

import random

from talking_trees.sdk import TalkingTrees

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
            "is_charging": 1.0 if self.charging else 0.0,
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
            distance_to_base = (self.x**2 + self.y**2) ** 0.5
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
            distance = (dx**2 + dy**2) ** 0.5
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
# STEP 2: Create Tree from Pure Python Code (py_trees)
# =============================================================================


def create_tree_from_code():
    """
    APPROACH 1: Create behavior tree entirely from Python code (no visual editor)

    This shows creating a tree using py_trees, then converting to TalkingTrees.
    This is the CODE-FIRST approach.
    """

    print("=" * 70)
    print("STEP 2A: Creating Tree from Pure Python Code (py_trees)")
    print("=" * 70)
    print()

    import operator

    import py_trees
    from py_trees.common import ComparisonExpression

    print("Building behavior tree with py_trees...")
    print()

    # Root: Selector (try each branch in order)
    root = py_trees.composites.Selector(name="Robot Controller", memory=False)

    # Branch 1: Emergency Handler (battery critical)
    emergency = py_trees.composites.Sequence("Emergency Handler", memory=False)

    # Check if battery is critical (< 5%)
    critical_check = ComparisonExpression("battery_level", operator.lt, 5.0)
    emergency.add_child(
        py_trees.behaviours.CheckBlackboardVariableValue(
            name="Battery Critical?", check=critical_check
        )
    )

    # If critical, emergency stop
    emergency.add_child(
        py_trees.behaviours.SetBlackboardVariable(
            name="Emergency Stop",
            variable_name="robot_action",
            variable_value="emergency_stop",
            overwrite=True,
        )
    )

    root.add_child(emergency)

    # Branch 2: Low Battery Handler (return to charge)
    low_battery = py_trees.composites.Sequence("Low Battery Handler", memory=False)

    # Check if battery is low (< 20%)
    low_check = ComparisonExpression("battery_level", operator.lt, 20.0)
    low_battery.add_child(
        py_trees.behaviours.CheckBlackboardVariableValue(
            name="Battery Low?", check=low_check
        )
    )

    # If low, command charge
    low_battery.add_child(
        py_trees.behaviours.SetBlackboardVariable(
            name="Command: Charge",
            variable_name="robot_action",
            variable_value="charge",
            overwrite=True,
        )
    )

    root.add_child(low_battery)

    # Branch 3: Normal Patrol (default behavior)
    patrol = py_trees.behaviours.SetBlackboardVariable(
        name="Command: Patrol",
        variable_name="robot_action",
        variable_value="patrol",
        overwrite=True,
    )

    root.add_child(patrol)

    print("✓ Created py_trees behavior tree:")
    print(f"  Root: {root.name} ({root.__class__.__name__})")
    print(f"  Children: {len(root.children)}")
    for i, child in enumerate(root.children, 1):
        print(f"    {i}. {child.name}")
    print()

    # Convert to TalkingTrees format
    print("Converting to TalkingTrees format...")
    tt = TalkingTrees()
    tree = tt.from_py_trees(
        root,
        name="Robot Controller (Code-Created)",
        version="1.0.0",
        description="Created entirely from py_trees code",
    )

    print("✓ Converted to TalkingTrees")
    print(f"  Tree: {tree.metadata.name}")
    print(f"  Version: {tree.metadata.version}")
    print()

    # Optionally save
    print("Saving to JSON...")
    tt.save_tree(tree, "tutorials/robot_from_code.json")
    print("✓ Saved to tutorials/robot_from_code.json")
    print("  (You can now load this in Tree Editor Pro to see visual representation!)")
    print()

    return tree


# =============================================================================
# STEP 3: Load Tree from Visual Editor
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

    tt = TalkingTrees()

    # Try to load tree exported from visual editor
    try:
        tree = tt.load_tree("robot_controller.json")
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
        tree = tt.load_tree("examples/robot_v1.json")
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
    tt = TalkingTrees()
    tree = load_tree_from_editor()

    # Create execution
    execution = tt.create_execution(tree)
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
            print(
                f"Tick {tick:3d} | "
                f"Battery: {robot.battery:5.1f}% | "
                f"Pos: ({robot.x:5.1f}, {robot.y:5.1f}) | "
                f"Action: {action:20s} | "
                f"Status: {robot.status:15s}"
            )

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
from talking_trees.sdk import TalkingTrees

# Initialize TalkingTrees SDK
tt = TalkingTrees()

# Load tree from JSON file
tree = tt.load_tree("robot_controller.json")

# Create execution
execution = tt.create_execution(tree)

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

    tt = TalkingTrees()

    try:
        tree = tt.load_tree("robot_controller.json")
    except FileNotFoundError:
        tree = tt.load_tree("examples/robot_v1.json")

    # Scenario 1: Normal operation
    print("Scenario 1: Normal Operation (Battery: 80%)")
    print("-" * 70)

    execution = tt.create_execution(tree)
    result = execution.tick(blackboard_updates={"battery_level": 80.0})
    action = result.blackboard.get("/robot_action")

    print(f"  Tree Decision: {action}")
    print("  Expected: patrol or similar")
    print()

    # Scenario 2: Low battery
    print("Scenario 2: Low Battery (Battery: 15%)")
    print("-" * 70)

    execution = tt.create_execution(tree)
    result = execution.tick(blackboard_updates={"battery_level": 15.0})
    action = result.blackboard.get("/robot_action")

    print(f"  Tree Decision: {action}")
    print("  Expected: return_to_base or charge")
    print()

    # Scenario 3: Critical battery
    print("Scenario 3: Critical Battery (Battery: 3%)")
    print("-" * 70)

    execution = tt.create_execution(tree)
    result = execution.tick(blackboard_updates={"battery_level": 3.0})
    action = result.blackboard.get("/robot_action")

    print(f"  Tree Decision: {action}")
    print("  Expected: emergency_stop")
    print()


# =============================================================================
# RUN EVERYTHING
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" TalkingTrees Tutorial 2: Complete Workflow")
    print(" BOTH Approaches: Code-First + Visual-First")
    print("=" * 70 + "\n")

    print("This tutorial shows BOTH approaches:")
    print("  ✓ APPROACH 1: Create trees from pure Python code (py_trees)")
    print("  ✓ APPROACH 2: Design trees in visual editor")
    print("  ✓ HOW TO ACTUALLY USE TREES TO CONTROL SYSTEMS")
    print()

    input("Press Enter to start...")
    print()

    # APPROACH 1: Code-first
    print("\n" + "=" * 70)
    print(" APPROACH 1: CODE-FIRST (Programmatic)")
    print("=" * 70)
    print()
    print("We'll create a behavior tree entirely from Python code,")
    print("no visual editor needed!")
    print()
    input("Press Enter to see programmatic tree creation...")
    print()

    tree_from_code = create_tree_from_code()

    input("Press Enter to continue...")
    print()

    # APPROACH 2: Visual-first
    print("\n" + "=" * 70)
    print(" APPROACH 2: VISUAL-FIRST (Recommended for beginners)")
    print("=" * 70)
    print()
    print("This approach uses the visual editor + 'Copy Python' button")
    print()
    input("Press Enter to learn about visual workflow...")
    print()

    demonstrate_copy_python_workflow()

    input("Press Enter to test scenarios...")
    print()

    # Test scenarios
    test_scenarios()

    # Now use the tree we created from code!
    print("\n" + "=" * 70)
    print(" USING THE CODE-CREATED TREE TO CONTROL ROBOT")
    print("=" * 70)
    print()
    print("Now let's use the tree we created from code to control the robot!")
    print()
    input("Press Enter to run simulation...")
    print()

    # Use the tree created from code
    tt = TalkingTrees()
    execution = tt.create_execution(tree_from_code)
    print("✓ Created execution from code-created tree")
    print()

    # Create robot
    robot = SimpleRobot()
    print("✓ Created robot simulator")
    print(f"  Initial battery: {robot.battery}%")
    print()

    # Control loop
    print("=" * 70)
    print("CONTROL LOOP: Tree → Decisions → Robot Actions")
    print("=" * 70)
    print()

    max_ticks = 50
    log_interval = 5

    for tick in range(max_ticks):
        sensors = robot.get_sensors()
        result = execution.tick(blackboard_updates=sensors)
        action = result.blackboard.get("/robot_action", "wait")
        robot.execute_action(action)

        if tick % log_interval == 0 or robot.battery < 15:
            print(
                f"Tick {tick:3d} | "
                f"Battery: {robot.battery:5.1f}% | "
                f"Action: {action:20s} | "
                f"Status: {robot.status:15s}"
            )

        if robot.battery <= 0:
            print("\n⚠️  BATTERY DEPLETED")
            break

        if robot.battery > 95 and robot.charging:
            print("\n✓ FULLY CHARGED")
            break

    print()
    print("=" * 70)
    print(" Tutorial Complete! 🎉")
    print("=" * 70)
    print()

    print("What you learned:")
    print("  ✓ APPROACH 1: Creating trees from pure Python code (py_trees)")
    print("  ✓ APPROACH 2: Visual editor workflow + 'Copy Python' button")
    print("  ✓ Converting between py_trees and TalkingTrees formats")
    print("  ✓ THE CONTROL LOOP: sensors → tree → actions → execute")
    print("  ✓ How to integrate behavior trees into real systems")
    print()

    print("Key Takeaway:")
    print("  Behavior trees make decisions. Your code executes them.")
    print("  1. Get sensors → 2. Tick tree → 3. Get action → 4. Execute")
    print()

    print("BOTH Approaches Work:")
    print("  • Code-First: Full control, programmatic, py_trees API")
    print("  • Visual-First: Rapid prototyping, intuitive, drag-and-drop")
    print("  • Choose what fits your workflow!")
    print()

    print("Next Steps:")
    print("  • Try creating your own tree from code (like we did!)")
    print("  • Or design visually: ./run_editor.sh")
    print("  • Use the tree to control YOUR system")
    print()

    print("📖 See tutorials/robot_from_code.json (we just created this!)")
    print("🚀 Run: ./run_editor.sh to visualize it!")
    print()
