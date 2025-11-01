"""
PyForest SDK Tutorial 5: py_trees Integration
==============================================

This tutorial shows how to bridge between py_trees and PyForest:

1. Create trees using py_trees programmatic API
2. Convert to PyForest format
3. Visualize in PyForest editor
4. Save to JSON
5. Load from JSON
6. Run via PyForest SDK or REST API

Why use this workflow?
- py_trees has a mature, Pythonic API for creating trees programmatically
- PyForest provides visualization, profiling, and version control
- Best of both worlds: programmatic creation + visual tools

Prerequisites:
    pip install py_trees

"""

import operator

import py_trees
from py_trees.common import ComparisonExpression

from py_forest.adapters import print_comparison, to_py_trees
from py_forest.core.profiler import ProfilingLevel
from py_forest.sdk import PyForest

# =============================================================================
# Example 1: Basic Conversion
# =============================================================================


def example_1_basic_conversion():
    """Create a simple py_trees tree and convert to PyForest"""
    print("=" * 70)
    print("EXAMPLE 1: Basic Conversion - py_trees to PyForest")
    print("=" * 70)

    # Step 1: Create tree with py_trees
    print("\nStep 1: Create tree with py_trees...")
    root = py_trees.composites.Sequence(name="Robot Controller", memory=False)
    root.add_child(py_trees.behaviours.Success(name="Initialize"))
    root.add_child(py_trees.behaviours.Success(name="Execute Mission"))
    root.add_child(py_trees.behaviours.Success(name="Shutdown"))

    # Display py_trees structure
    print("\npy_trees Tree:")
    print(py_trees.display.ascii_tree(root, show_status=False))

    # Step 2: Convert to PyForest
    print("\nStep 2: Convert to PyForest format...")
    pf = PyForest()
    pf_tree = pf.from_py_trees(
        root,
        name="Simple Robot Controller",
        version="1.0.0",
        description="Basic sequence converted from py_trees",
    )

    print("✓ Converted to PyForest TreeDefinition")
    print(f"  Name: {pf_tree.metadata.name}")
    print(f"  Version: {pf_tree.metadata.version}")
    print(f"  Root node: {pf_tree.root.name}")

    # Step 3: Save to JSON (can be opened in editor)
    print("\nStep 3: Save to JSON...")
    pf.save_tree(pf_tree, "tutorials/py_trees_simple.json")
    print("✓ Saved to tutorials/py_trees_simple.json")
    print("  Open in visualization/tree_editor_pro.html to view!")

    # Step 4: Run with PyForest SDK
    print("\nStep 4: Run with PyForest SDK...")
    execution = pf.create_execution(pf_tree)
    result = execution.tick()

    print("✓ Execution complete")
    print(f"  Status: {result.status}")
    print(f"  Ticks: {result.tick_count}")
    print()


# =============================================================================
# Example 2: Complex Tree with Conditions
# =============================================================================


def example_2_complex_tree():
    """Demonstrate common py_trees node types with proper API"""
    print("=" * 70)
    print("EXAMPLE 2: Complex Tree - All Common Node Types")
    print("=" * 70)

    # Build tree with various node types
    root = py_trees.composites.Selector(name="Main Selector", memory=False)

    # Branch 1: Sequence with conditions (using ComparisonExpression)
    patrol_sequence = py_trees.composites.Sequence(name="Patrol Mode", memory=False)

    # Create condition check with ComparisonExpression
    battery_check = ComparisonExpression("battery_level", operator.gt, 50.0)
    patrol_sequence.add_child(
        py_trees.behaviours.CheckBlackboardVariableValue(
            name="Battery OK?", check=battery_check
        )
    )
    patrol_sequence.add_child(
        py_trees.behaviours.SetBlackboardVariable(
            name="Set Action",
            variable_name="robot_action",
            variable_value="patrol",
            overwrite=True,
        )
    )

    # Branch 2: Low battery handler
    low_battery_seq = py_trees.composites.Sequence(name="Low Battery", memory=False)

    low_battery_check = ComparisonExpression("battery_level", operator.lt, 20.0)
    low_battery_seq.add_child(
        py_trees.behaviours.CheckBlackboardVariableValue(
            name="Battery Low?", check=low_battery_check
        )
    )
    low_battery_seq.add_child(
        py_trees.behaviours.SetBlackboardVariable(
            name="Return to Base",
            variable_name="robot_action",
            variable_value="return_to_base",
            overwrite=True,
        )
    )

    # Branch 3: Parallel tasks
    parallel = py_trees.composites.Parallel(
        name="Monitor Systems", policy=py_trees.common.ParallelPolicy.SuccessOnAll()
    )
    parallel.add_child(py_trees.behaviours.Success(name="Monitor Sensors"))
    parallel.add_child(py_trees.behaviours.Success(name="Monitor Communications"))

    # Add branches to root
    root.add_child(low_battery_seq)
    root.add_child(patrol_sequence)
    root.add_child(parallel)

    # Display
    print("\npy_trees Tree Structure:")
    print(py_trees.display.ascii_tree(root, show_status=False))

    # Convert to PyForest
    pf = PyForest()
    pf_tree = pf.from_py_trees(root, name="Advanced Robot Controller", version="1.0.0")

    print("\n✓ Converted to PyForest")
    print(f"  Root: {pf_tree.root.node_type}")

    # Save
    pf.save_tree(pf_tree, "tutorials/py_trees_complex.json")
    print("\n✓ Saved to tutorials/py_trees_complex.json")
    print()


# =============================================================================
# Example 3: Complete Workflow - Create, Visualize, Run
# =============================================================================


def example_3_complete_workflow():
    """End-to-end workflow: py_trees → PyForest → Visualize → Run"""
    print("=" * 70)
    print("EXAMPLE 3: Complete Workflow")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # Step 1: Create tree programmatically with py_trees
    # -------------------------------------------------------------------------
    print("\nStep 1: Create tree programmatically with py_trees...")

    root = py_trees.composites.Selector(name="Task Manager", memory=False)

    # Emergency branch
    emergency = py_trees.composites.Sequence(name="Emergency", memory=False)

    error_check = ComparisonExpression("error_level", operator.gt, 90)
    emergency.add_child(
        py_trees.behaviours.CheckBlackboardVariableValue(
            name="Critical Error?", check=error_check
        )
    )
    emergency.add_child(
        py_trees.behaviours.SetBlackboardVariable(
            name="Activate Emergency Stop",
            variable_name="system_mode",
            variable_value="emergency_stop",
            overwrite=True,
        )
    )

    # Normal operation
    normal = py_trees.composites.Sequence(name="Normal Operation", memory=False)
    normal.add_child(py_trees.behaviours.Success(name="Check Config"))
    normal.add_child(
        py_trees.behaviours.SetBlackboardVariable(
            name="Set Running",
            variable_name="system_mode",
            variable_value="running",
            overwrite=True,
        )
    )

    root.add_child(emergency)
    root.add_child(normal)

    print("✓ Created tree with py_trees")

    # -------------------------------------------------------------------------
    # Step 2: Convert to PyForest format
    # -------------------------------------------------------------------------
    print("\nStep 2: Convert to PyForest format...")

    pf = PyForest()
    pf_tree = pf.from_py_trees(
        root,
        name="Task Manager",
        version="1.0.0",
        description="Manages emergency and normal operations",
    )

    print("✓ Converted to PyForest TreeDefinition")
    print(f"  Root: {pf_tree.root.name}")

    # -------------------------------------------------------------------------
    # Step 3: Save to JSON for visualization
    # -------------------------------------------------------------------------
    print("\nStep 3: Save to JSON for visualization...")

    output_path = "tutorials/py_trees_task_manager.json"
    pf.save_tree(pf_tree, output_path)

    print(f"✓ Saved to {output_path}")
    print("  → Open in visualization/tree_editor_pro.html")
    print("  → View structure visually")
    print("  → Make edits if needed")
    print("  → Export back to JSON")

    # -------------------------------------------------------------------------
    # Step 4: Load from JSON (simulating editor round-trip)
    # -------------------------------------------------------------------------
    print("\nStep 4: Load from JSON (after visual editing)...")

    loaded_tree = pf.load_tree(output_path)

    print(f"✓ Loaded tree: {loaded_tree.metadata.name} v{loaded_tree.metadata.version}")
    print(f"  Root: {loaded_tree.root.name}")

    # -------------------------------------------------------------------------
    # Step 5: Run via PyForest SDK
    # -------------------------------------------------------------------------
    print("\nStep 5: Run via PyForest SDK...")

    execution = pf.create_execution(loaded_tree)

    # Test 1: Normal operation
    print("\n  Test 1: Normal operation (error_level=10)")
    result = execution.tick(blackboard_updates={"error_level": 10})
    print(f"    Status: {result.status}")
    print(f"    System mode: {result.blackboard.get('system_mode')}")

    # Test 2: Emergency
    print("\n  Test 2: Emergency (error_level=95)")
    result = execution.tick(blackboard_updates={"error_level": 95})
    print(f"    Status: {result.status}")
    print(f"    System mode: {result.blackboard.get('system_mode')}")

    print("\n✓ Workflow complete!")
    print()


# =============================================================================
# Example 4: Decorators - Inverter, Repeat, Retry, Timeout
# =============================================================================


def example_4_decorators():
    """Demonstrate py_trees decorators"""
    print("=" * 70)
    print("EXAMPLE 4: Decorators - Inverter, Repeat, Retry, Timeout")
    print("=" * 70)

    # Create tree with decorators
    root = py_trees.composites.Sequence(name="Decorator Demo", memory=False)

    # Inverter: flip success/failure
    success_task = py_trees.behaviours.Success(name="Always Success")
    inverter = py_trees.decorators.Inverter(name="Invert Result", child=success_task)
    root.add_child(inverter)

    # Repeat: repeat until N successes
    repeat_task = py_trees.behaviours.Success(name="Task")
    repeater = py_trees.decorators.Repeat(
        name="Repeat 3 Times", child=repeat_task, num_success=3
    )
    root.add_child(repeater)

    # Retry: retry until N failures
    retry_task = py_trees.behaviours.Failure(name="Flaky Task")
    retrier = py_trees.decorators.Retry(
        name="Retry 2 Times", child=retry_task, num_failures=2
    )
    root.add_child(retrier)

    # Timeout: fail if exceeds duration
    timeout_task = py_trees.behaviours.Running(name="Long Task")
    timeout = py_trees.decorators.Timeout(
        name="5 Second Timeout", child=timeout_task, duration=5.0
    )
    root.add_child(timeout)

    print("\npy_trees Tree with Decorators:")
    print(py_trees.display.ascii_tree(root, show_status=False))

    # Convert to PyForest
    pf = PyForest()
    pf_tree = pf.from_py_trees(root, name="Decorator Demo", version="1.0.0")

    print("\n✓ Converted decorators to PyForest")
    print("  All decorator parameters preserved in config")

    # Save
    pf.save_tree(pf_tree, "tutorials/py_trees_decorators.json")
    print("\n✓ Saved to tutorials/py_trees_decorators.json")
    print()


# =============================================================================
# Example 5: Reverse Conversion (PyForest → py_trees)
# =============================================================================


def example_5_reverse_conversion():
    """Load PyForest tree and convert back to py_trees"""
    print("=" * 70)
    print("EXAMPLE 5: Reverse Conversion - PyForest to py_trees")
    print("=" * 70)

    # Load a PyForest tree
    pf = PyForest()
    pf_tree = pf.load_tree("examples/robot_v1.json")

    print(f"Loaded PyForest tree: {pf_tree.metadata.name}")
    print(f"  Root: {pf_tree.root.node_type}")

    # Convert to py_trees
    print("\nConverting to py_trees...")
    py_trees_root = to_py_trees(pf_tree)

    print("✓ Converted to py_trees")
    print("\npy_trees Structure:")
    print(py_trees.display.ascii_tree(py_trees_root, show_status=False))

    # Can now use with standard py_trees tools
    print("\nCan now use with py_trees tools:")
    print("  - py_trees.display.render_dot_tree()")
    print("  - py_trees.visitors for custom analysis")
    print("  - py_trees debugging tools")
    print()


# =============================================================================
# Example 6: Comparison and Debugging
# =============================================================================


def example_6_comparison():
    """Compare py_trees and PyForest representations"""
    print("=" * 70)
    print("EXAMPLE 6: Tree Comparison - Debugging Conversions")
    print("=" * 70)

    # Create tree
    root = py_trees.composites.Selector(name="Root", memory=False)
    seq = py_trees.composites.Sequence(name="Sequence", memory=False)
    seq.add_child(py_trees.behaviours.Success(name="Child 1"))
    seq.add_child(py_trees.behaviours.Success(name="Child 2"))
    root.add_child(seq)
    root.add_child(py_trees.behaviours.Success(name="Fallback"))

    # Convert
    pf = PyForest()
    pf_tree = pf.from_py_trees(root, name="Comparison Tree")

    # Use utility to compare
    print("\nSide-by-side comparison:")
    print_comparison(root, pf_tree)


# =============================================================================
# Example 7: Real-World Use Case - Custom Behaviors
# =============================================================================


def example_7_custom_behaviors():
    """Create tree with custom py_trees behaviors"""
    print("=" * 70)
    print("EXAMPLE 7: Custom Behaviors - Real-World Example")
    print("=" * 70)

    # Define custom behavior
    class CheckSensorThreshold(py_trees.behaviour.Behaviour):
        """Custom behavior: Check if sensor exceeds threshold"""

        def __init__(self, name, sensor_key, threshold):
            super().__init__(name)
            self.sensor_key = sensor_key
            self.threshold = threshold
            self.blackboard = self.attach_blackboard_client(name=name)
            self.blackboard.register_key(
                key=sensor_key, access=py_trees.common.Access.READ
            )

        def update(self):
            value = self.blackboard.get(self.sensor_key)
            if value is None:
                return py_trees.common.Status.FAILURE

            if value > self.threshold:
                return py_trees.common.Status.SUCCESS
            else:
                return py_trees.common.Status.FAILURE

    # Build tree using custom behavior
    root = py_trees.composites.Sequence(name="Sensor Monitor", memory=False)
    root.add_child(CheckSensorThreshold("Temp Check", "temperature", 75.0))
    root.add_child(
        py_trees.behaviours.SetBlackboardVariable(
            name="Activate Cooling",
            variable_name="cooling_active",
            variable_value=True,
            overwrite=True,
        )
    )

    print("Created tree with custom behavior:")
    print(py_trees.display.ascii_tree(root, show_status=False))

    # Convert to PyForest
    pf = PyForest()
    pf_tree = pf.from_py_trees(root, name="Sensor Monitor")

    print("\n✓ Converted custom tree to PyForest")
    print("  Note: Custom behaviors converted to generic 'Action' type")
    print("  Original class stored in config['_py_trees_class']")

    # Save
    pf.save_tree(pf_tree, "tutorials/py_trees_custom.json")
    print("\n✓ Saved to tutorials/py_trees_custom.json")
    print()


# =============================================================================
# Example 8: Using with Profiling
# =============================================================================


def example_8_profiling():
    """Convert py_trees tree and run with profiling"""
    print("=" * 70)
    print("EXAMPLE 8: Profiling Converted Trees")
    print("=" * 70)

    # Create tree
    root = py_trees.composites.Sequence(name="Profiled Sequence", memory=False)
    for i in range(5):
        root.add_child(py_trees.behaviours.Success(name=f"Step {i + 1}"))

    # Convert with profiling enabled
    pf = PyForest(profiling_level=ProfilingLevel.BASIC)
    pf_tree = pf.from_py_trees(root, name="Profiled Tree")

    print(f"✓ Converted tree: {pf_tree.metadata.name}")

    # Run with profiling
    execution = pf.create_execution(pf_tree)

    print("\nRunning 50 ticks with profiling...")
    for i in range(50):
        execution.tick()

    # Get report
    report = execution.get_profiling_report(verbose=True)
    print("\nProfiling Report:")
    print(report)
    print()


# =============================================================================
# Run All Examples
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" PyForest SDK Tutorial 5: py_trees Integration")
    print("=" * 70 + "\n")

    example_1_basic_conversion()
    example_2_complex_tree()
    example_3_complete_workflow()
    example_4_decorators()
    example_5_reverse_conversion()
    example_6_comparison()
    example_7_custom_behaviors()
    example_8_profiling()

    print("=" * 70)
    print(" Tutorial Complete! 🎉")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  ✓ Use py_trees API for programmatic tree creation")
    print("  ✓ Use ComparisonExpression for condition checks")
    print("  ✓ Convert to PyForest with pf.from_py_trees()")
    print("  ✓ Visualize in PyForest editor")
    print("  ✓ Run with SDK or REST API")
    print("  ✓ Reverse conversion supported (to_py_trees)")
    print("  ✓ Decorators fully supported (Inverter, Repeat, Retry, Timeout)")
    print("\nFiles created:")
    print("  • tutorials/py_trees_simple.json")
    print("  • tutorials/py_trees_complex.json")
    print("  • tutorials/py_trees_task_manager.json")
    print("  • tutorials/py_trees_decorators.json")
    print("  • tutorials/py_trees_custom.json")
    print("\n👉 Open these in visualization/tree_editor_pro.html to view!")
    print()
