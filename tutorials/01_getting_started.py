"""
PyForest SDK Tutorial 1: Getting Started
=========================================

This tutorial covers the basics of using the PyForest SDK to:
- Load behavior trees from JSON files
- Create executions
- Tick trees with blackboard updates
- Read execution results

No API server required - everything runs in your Python process!
"""

from py_forest.sdk import PyForest, load_and_run
from py_forest.core.profiler import ProfilingLevel

# =============================================================================
# Example 1: The Simplest Possible Usage
# =============================================================================

def example_1_quick_start():
    """One-liner to load and run a tree"""
    print("=" * 70)
    print("EXAMPLE 1: Quick Start - One-Liner Execution")
    print("=" * 70)

    # Load tree, run 1 tick with sensor inputs
    result = load_and_run(
        "examples/robot_v1.json",
        blackboard_updates={"battery_level": 85.0, "distance": 2.5},
        ticks=1
    )

    print(f"✓ Tree Status: {result.status}")
    print(f"✓ Tick Count: {result.tick_count}")
    print(f"✓ Active Node: {result.tip_node}")
    print(f"✓ Robot Action: {result.blackboard.get('/robot_action')}")
    print()


# =============================================================================
# Example 2: Standard SDK Usage Pattern
# =============================================================================

def example_2_standard_usage():
    """The standard way to use PyForest SDK"""
    print("=" * 70)
    print("EXAMPLE 2: Standard Usage - Step by Step")
    print("=" * 70)

    # Step 1: Create PyForest instance
    pf = PyForest()

    # Step 2: Load tree from JSON file (exported from visual editor)
    tree = pf.load_tree("examples/robot_v1.json")
    print(f"✓ Loaded tree: {tree.name} (v{tree.version})")
    print(f"  Description: {tree.description}")
    print(f"  Total nodes: {len(tree.nodes)}")

    # Step 3: Create execution with initial blackboard state
    execution = pf.create_execution(
        tree,
        initial_blackboard={
            "battery_level": 100.0,
            "distance": 10.0,
            "temperature": 25.0
        }
    )
    print(f"✓ Created execution")

    # Step 4: Tick the tree (simulating sensor updates)
    result = execution.tick(
        blackboard_updates={
            "battery_level": 95.0,  # Battery dropped slightly
            "distance": 8.5,         # Getting closer to target
        }
    )

    print(f"✓ Tick completed:")
    print(f"  Status: {result.status}")
    print(f"  Tick count: {result.tick_count}")
    print(f"  Active node: {result.tip_node}")

    # Step 5: Read blackboard values (outputs from tree)
    print(f"\n📊 Blackboard State:")
    for key, value in result.blackboard.items():
        print(f"  {key}: {value}")
    print()


# =============================================================================
# Example 3: Multiple Ticks - Simulating Time
# =============================================================================

def example_3_multiple_ticks():
    """Run multiple ticks to simulate a robot over time"""
    print("=" * 70)
    print("EXAMPLE 3: Multiple Ticks - Simulation Over Time")
    print("=" * 70)

    pf = PyForest()
    tree = pf.load_tree("examples/robot_v1.json")
    execution = pf.create_execution(tree, initial_blackboard={
        "battery_level": 100.0,
        "distance": 10.0
    })

    # Simulate 5 time steps
    scenarios = [
        {"battery_level": 90.0, "distance": 8.0, "desc": "Normal operation"},
        {"battery_level": 75.0, "distance": 5.0, "desc": "Getting closer"},
        {"battery_level": 50.0, "distance": 3.0, "desc": "Battery dropping"},
        {"battery_level": 18.0, "distance": 2.0, "desc": "Low battery!"},
        {"battery_level": 12.0, "distance": 1.5, "desc": "Critical battery"},
    ]

    for i, scenario in enumerate(scenarios, 1):
        desc = scenario.pop("desc")
        result = execution.tick(blackboard_updates=scenario)

        print(f"Tick {i} - {desc}:")
        print(f"  Battery: {scenario['battery_level']}%")
        print(f"  Distance: {scenario['distance']}m")
        print(f"  Status: {result.status}")
        print(f"  Action: {result.blackboard.get('/robot_action', 'None')}")
        print(f"  Tip: {result.tip_node}")
        print()


# =============================================================================
# Example 4: Exploring Tree Structure
# =============================================================================

def example_4_tree_inspection():
    """Inspect tree structure programmatically"""
    print("=" * 70)
    print("EXAMPLE 4: Tree Inspection - Understanding Structure")
    print("=" * 70)

    pf = PyForest()
    tree = pf.load_tree("examples/robot_v1.json")

    # Tree metadata
    print(f"Tree Information:")
    print(f"  Name: {tree.name}")
    print(f"  Version: {tree.version}")
    print(f"  Description: {tree.description}")
    print(f"  Root ID: {tree.root_id}")
    print()

    # Count node types
    node_types = {}
    for node in tree.nodes:
        node_type = node.node_type
        node_types[node_type] = node_types.get(node_type, 0) + 1

    print(f"Node Type Distribution:")
    for node_type, count in sorted(node_types.items()):
        print(f"  {node_type}: {count}")
    print()

    # List blackboard variables
    if tree.blackboard:
        print(f"Blackboard Variables ({len(tree.blackboard.variables)}):")
        for var in tree.blackboard.variables:
            constraints = ""
            if hasattr(var, 'min_value') and var.min_value is not None:
                constraints = f" (min: {var.min_value})"
            if hasattr(var, 'max_value') and var.max_value is not None:
                constraints += f" (max: {var.max_value})"
            print(f"  {var.name}: {var.value_type}{constraints}")
    print()

    # Show root node and immediate children
    root = next((n for n in tree.nodes if n.id == tree.root_id), None)
    if root:
        print(f"Root Node: {root.name} ({root.node_type})")
        children = [n for n in tree.nodes if n.parent_id == root.id]
        if children:
            print(f"  Children ({len(children)}):")
            for child in children:
                print(f"    - {child.name} ({child.node_type})")
    print()


# =============================================================================
# Example 5: Creating Trees Programmatically
# =============================================================================

def example_5_programmatic_tree():
    """Create a simple tree from scratch using Python"""
    print("=" * 70)
    print("EXAMPLE 5: Programmatic Tree Creation")
    print("=" * 70)

    from py_forest.models.tree import TreeDefinition, NodeDefinition, BlackboardDefinition, BlackboardVariable
    import uuid

    # Create nodes
    root_id = str(uuid.uuid4())
    child1_id = str(uuid.uuid4())
    child2_id = str(uuid.uuid4())

    nodes = [
        # Root: Sequence
        NodeDefinition(
            id=root_id,
            name="Root Sequence",
            node_type="sequence",
            parent_id=None,
            properties={}
        ),
        # Child 1: Condition
        NodeDefinition(
            id=child1_id,
            name="Check Temperature",
            node_type="condition",
            parent_id=root_id,
            properties={
                "blackboard_key": "temperature",
                "operator": "greater_than",
                "compare_value": 30.0
            }
        ),
        # Child 2: Action
        NodeDefinition(
            id=child2_id,
            name="Activate Cooling",
            node_type="action",
            parent_id=root_id,
            properties={
                "blackboard_key": "/cooling_active",
                "value": True
            }
        ),
    ]

    # Create blackboard definition
    blackboard = BlackboardDefinition(
        variables=[
            BlackboardVariable(
                name="temperature",
                value_type="float",
                default_value=25.0,
                min_value=0.0,
                max_value=100.0
            ),
            BlackboardVariable(
                name="/cooling_active",
                value_type="bool",
                default_value=False
            )
        ]
    )

    # Create tree
    tree = TreeDefinition(
        id=str(uuid.uuid4()),
        name="Temperature Control",
        version="1.0.0",
        description="Simple temperature control tree",
        root_id=root_id,
        nodes=nodes,
        blackboard=blackboard
    )

    print(f"✓ Created tree: {tree.name}")
    print(f"  Nodes: {len(tree.nodes)}")
    print(f"  Blackboard vars: {len(tree.blackboard.variables)}")

    # Save it
    pf = PyForest()
    pf.save_tree(tree, "tutorials/temp_control.json")
    print(f"✓ Saved to tutorials/temp_control.json")

    # Run it
    execution = pf.create_execution(tree)

    # Test 1: Low temperature (< 30) - should fail at condition
    result = execution.tick(blackboard_updates={"temperature": 25.0})
    print(f"\nTest 1 - Low temp (25°C):")
    print(f"  Status: {result.status}")
    print(f"  Cooling: {result.blackboard.get('/cooling_active')}")

    # Test 2: High temperature (> 30) - should succeed
    result = execution.tick(blackboard_updates={"temperature": 35.0})
    print(f"\nTest 2 - High temp (35°C):")
    print(f"  Status: {result.status}")
    print(f"  Cooling: {result.blackboard.get('/cooling_active')}")
    print()


# =============================================================================
# Example 6: Error Handling
# =============================================================================

def example_6_error_handling():
    """Proper error handling when using the SDK"""
    print("=" * 70)
    print("EXAMPLE 6: Error Handling Best Practices")
    print("=" * 70)

    pf = PyForest()

    # 1. Handle missing files
    try:
        tree = pf.load_tree("nonexistent.json")
    except FileNotFoundError as e:
        print(f"✓ Caught missing file error: {e}")

    # 2. Handle invalid JSON
    try:
        # Create invalid JSON file
        with open("tutorials/invalid.json", "w") as f:
            f.write("not valid json{")
        tree = pf.load_tree("tutorials/invalid.json")
    except Exception as e:
        print(f"✓ Caught invalid JSON error: {type(e).__name__}")

    # 3. Handle validation errors (if tree has blackboard validation)
    tree = pf.load_tree("examples/robot_v1.json")
    execution = pf.create_execution(tree)

    try:
        # Try to set invalid value (if validation is enabled)
        result = execution.tick(blackboard_updates={"battery_level": -10.0})
        print(f"✓ Battery set to -10% (validation may have caught this)")
    except Exception as e:
        print(f"✓ Caught validation error: {e}")

    print()


# =============================================================================
# Run All Examples
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" PyForest SDK Tutorial 1: Getting Started")
    print("=" * 70 + "\n")

    # Run examples
    example_1_quick_start()
    example_2_standard_usage()
    example_3_multiple_ticks()
    example_4_tree_inspection()
    example_5_programmatic_tree()
    example_6_error_handling()

    print("=" * 70)
    print(" Tutorial Complete! 🎉")
    print("=" * 70)
    print("\nNext steps:")
    print("  - Try tutorial 02_profiling_performance.py for performance analysis")
    print("  - Try tutorial 03_version_control.py for tree diffing")
    print("  - Try tutorial 04_robot_controller.py for a complete example")
    print()
