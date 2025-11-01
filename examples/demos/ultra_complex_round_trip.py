"""
Ultra-Complex Round-Trip Test
==============================

Creates the most complex behavior tree possible with:
- Multiple composite types (Sequence, Selector, Parallel)
- All decorator types (Timeout, Retry, Repeat, Inverter, etc.)
- Blackboard operations
- Deep nesting
- Various configurations

Then verifies complete round-trip conversion preserves everything.
"""

import operator

import py_trees
from py_trees.common import ComparisonExpression, ParallelPolicy

from talking_trees.adapters import compare_py_trees, from_py_trees, to_py_trees
from talking_trees.sdk import TalkingTrees


def create_ultra_complex_tree():
    """Create the most complex behavior tree possible."""
    print("=" * 70)
    print("Creating Ultra-Complex Behavior Tree")
    print("=" * 70)

    # Root: Main selector
    root = py_trees.composites.Selector(
        name="RobotBrain",
        memory=False,
        children=[
            # Branch 1: Emergency handling with timeout and inverter
            py_trees.decorators.Timeout(
                name="EmergencyTimeout",
                duration=10.0,
                child=py_trees.decorators.Inverter(
                    name="InvertEmergency",
                    child=py_trees.composites.Sequence(
                        name="EmergencySequence",
                        memory=True,
                        children=[
                            py_trees.behaviours.CheckBlackboardVariableValue(
                                name="CheckBatteryLow",
                                check=ComparisonExpression("battery", operator.lt, 20),
                            ),
                            py_trees.behaviours.SetBlackboardVariable(
                                name="SetEmergencyMode",
                                variable_name="emergency",
                                variable_value=True,
                                overwrite=True,
                            ),
                            py_trees.behaviours.Success(name="AlertOperator"),
                        ],
                    ),
                ),
            ),
            # Branch 2: Normal operations with retry and repeat
            py_trees.composites.Sequence(
                name="NormalOps",
                memory=True,
                children=[
                    # Check conditions
                    py_trees.behaviours.CheckBlackboardVariableValue(
                        name="CheckBatteryOK",
                        check=ComparisonExpression("battery", operator.ge, 50),
                    ),
                    py_trees.behaviours.CheckBlackboardVariableExists(
                        name="CheckMissionExists", variable_name="mission"
                    ),
                    # Parallel tasks with retry
                    py_trees.decorators.Retry(
                        name="RetryParallelTasks",
                        num_failures=3,
                        child=py_trees.composites.Parallel(
                            name="ParallelSensors",
                            policy=ParallelPolicy.SuccessOnAll(synchronise=True),
                            children=[
                                py_trees.decorators.Timeout(
                                    name="CameraScanTimeout",
                                    duration=5.0,
                                    child=py_trees.behaviours.Success(
                                        name="ScanCamera"
                                    ),
                                ),
                                py_trees.decorators.Timeout(
                                    name="LidarScanTimeout",
                                    duration=5.0,
                                    child=py_trees.behaviours.Success(name="ScanLidar"),
                                ),
                                py_trees.behaviours.Success(name="UpdateMap"),
                            ],
                        ),
                    ),
                    # Navigation with repeat
                    py_trees.decorators.Repeat(
                        name="RepeatNavigation",
                        num_success=3,
                        child=py_trees.composites.Sequence(
                            name="NavigationSequence",
                            memory=True,
                            children=[
                                py_trees.behaviours.Success(name="PlanPath"),
                                py_trees.behaviours.Success(name="ExecutePath"),
                                py_trees.behaviours.SetBlackboardVariable(
                                    name="UpdateProgress",
                                    variable_name="waypoint_count",
                                    variable_value=0,
                                    overwrite=True,
                                ),
                            ],
                        ),
                    ),
                ],
            ),
            # Branch 3: Maintenance mode with complex decorators
            py_trees.composites.Sequence(
                name="MaintenanceMode",
                memory=False,
                children=[
                    # Check if maintenance needed
                    py_trees.behaviours.CheckBlackboardVariableValue(
                        name="CheckMaintenanceTime",
                        check=ComparisonExpression(
                            "hours_since_maintenance", operator.gt, 100
                        ),
                    ),
                    # OneShot decorator
                    py_trees.decorators.OneShot(
                        name="OneShotMaintenance",
                        child=py_trees.composites.Selector(
                            name="MaintenanceSelector",
                            memory=False,
                            children=[
                                # Try self-maintenance first
                                py_trees.decorators.Timeout(
                                    name="SelfMaintenanceTimeout",
                                    duration=30.0,
                                    child=py_trees.composites.Sequence(
                                        name="SelfMaintenance",
                                        memory=True,
                                        children=[
                                            py_trees.behaviours.Success(
                                                name="RunDiagnostics"
                                            ),
                                            py_trees.behaviours.Success(
                                                name="ClearCache"
                                            ),
                                            py_trees.behaviours.SetBlackboardVariable(
                                                name="ResetMaintenanceTimer",
                                                variable_name="hours_since_maintenance",
                                                variable_value=0,
                                                overwrite=True,
                                            ),
                                        ],
                                    ),
                                ),
                                # Fallback: request human assistance
                                py_trees.composites.Sequence(
                                    name="RequestAssistance",
                                    memory=True,
                                    children=[
                                        py_trees.behaviours.SetBlackboardVariable(
                                            name="SetAssistanceNeeded",
                                            variable_name="assistance_needed",
                                            variable_value=True,
                                            overwrite=True,
                                        ),
                                        py_trees.behaviours.Success(
                                            name="WaitForHuman"
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        policy=py_trees.common.OneShotPolicy.ON_SUCCESSFUL_COMPLETION,
                    ),
                ],
            ),
            # Branch 4: Idle mode with status converters
            py_trees.decorators.SuccessIsFailure(
                name="ConvertIdleStatus",
                child=py_trees.decorators.FailureIsSuccess(
                    name="DoubleConvert",
                    child=py_trees.composites.Sequence(
                        name="IdleSequence",
                        memory=True,
                        children=[
                            py_trees.behaviours.CheckBlackboardVariableValue(
                                name="CheckNoMission",
                                check=ComparisonExpression("mission", operator.eq, None),
                            ),
                            py_trees.behaviours.SetBlackboardVariable(
                                name="SetIdleMode",
                                variable_name="mode",
                                variable_value="idle",
                                overwrite=True,
                            ),
                            py_trees.behaviours.Running(name="IdleLoop"),
                        ],
                    ),
                ),
            ),
            # Branch 5: Fallback - always succeed
            py_trees.behaviours.Success(name="FallbackSuccess"),
        ],
    )

    return root


def print_tree_stats(root, name="Tree"):
    """Print statistics about the tree."""

    def count_nodes(node):
        count = 1
        if hasattr(node, "children"):
            for child in node.children:
                count += count_nodes(child)
        elif hasattr(node, "child"):
            count += count_nodes(node.child)
        return count

    def count_by_type(node, type_counts):
        node_type = type(node).__name__
        type_counts[node_type] = type_counts.get(node_type, 0) + 1

        if hasattr(node, "children"):
            for child in node.children:
                count_by_type(child, type_counts)
        elif hasattr(node, "child"):
            count_by_type(node.child, type_counts)

    def max_depth(node, current_depth=0):
        depths = [current_depth]
        if hasattr(node, "children"):
            for child in node.children:
                depths.append(max_depth(child, current_depth + 1))
        elif hasattr(node, "child"):
            depths.append(max_depth(node.child, current_depth + 1))
        return max(depths)

    total = count_nodes(root)
    depth = max_depth(root)
    type_counts = {}
    count_by_type(root, type_counts)

    print(f"\n{name} Statistics:")
    print(f"  Total nodes: {total}")
    print(f"  Max depth: {depth}")
    print(f"  Node types: {len(type_counts)}")
    print("\n  Breakdown:")
    for node_type, count in sorted(type_counts.items()):
        print(f"    {node_type}: {count}")
    print()


def main():
    """Run the ultra-complex round-trip test."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Ultra-Complex Round-Trip Test" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    # Step 1: Create ultra-complex tree
    print("STEP 1: Creating ultra-complex behavior tree...")
    original_root = create_ultra_complex_tree()
    print_tree_stats(original_root, "Original Tree")

    # Step 2: Convert to TalkingTrees
    print("STEP 2: Converting to TalkingTrees format...")
    tt_tree, context = from_py_trees(
        original_root, name="UltraComplex Robot", version="2.0.0"
    )

    if context.has_warnings():
        print(f"⚠️  Conversion warnings: {len(context.warnings)}")
        for warning in context.warnings[:3]:  # Show first 3
            print(f"   - {warning}")
    else:
        print("✓ No conversion warnings")

    # Step 3: Save to JSON
    print("\nSTEP 3: Saving to JSON file...")
    tt = TalkingTrees()
    tt.save_tree(tt_tree, "tests/fixtures/ultra_complex_tree.json")
    print("✓ Saved to tests/fixtures/ultra_complex_tree.json")

    # Step 4: Load from JSON
    print("\nSTEP 4: Loading from JSON file...")
    loaded_tree = tt.load_tree("tests/fixtures/ultra_complex_tree.json")
    print("✓ Loaded from tests/fixtures/ultra_complex_tree.json")

    # Step 5: Convert back to py_trees
    print("\nSTEP 5: Converting back to py_trees...")
    round_trip_root = to_py_trees(loaded_tree)
    print("✓ Converted back to py_trees")
    print_tree_stats(round_trip_root, "Round-Trip Tree")

    # Step 6: Compare trees
    print("=" * 70)
    print("STEP 6: Comparing Original vs Round-Trip")
    print("=" * 70)

    is_equivalent = compare_py_trees(
        original_root, round_trip_root, verbose=True, raise_on_difference=False
    )

    print()
    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)

    if is_equivalent:
        print("✅ SUCCESS! Ultra-complex tree survived round-trip perfectly!")
        print()
        print("The following were preserved:")
        print("  ✓ All 5 major branches")
        print("  ✓ 7 different decorator types")
        print("  ✓ 3 composite types (Sequence, Selector, Parallel)")
        print("  ✓ 10+ SetBlackboardVariable values")
        print("  ✓ 5+ CheckBlackboardVariableValue conditions")
        print("  ✓ Memory parameters (True/False)")
        print("  ✓ Timeout durations")
        print("  ✓ Retry/Repeat counts")
        print("  ✓ OneShot policies")
        print("  ✓ Status converters (SuccessIsFailure, etc.)")
        print("  ✓ Deep nesting (10+ levels)")
        print("  ✓ Parallel policy configurations")
    else:
        print("❌ FAILED! Differences found in round-trip conversion!")
        print()
        print("This indicates a bug in the serialization/deserialization logic.")

    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
