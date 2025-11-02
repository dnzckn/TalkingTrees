#!/usr/bin/env python3
"""Generate ultra complex tree demo JSON for the library."""

import sys
sys.path.insert(0, 'src')

import operator
import py_trees
from py_trees.common import ComparisonExpression, ParallelPolicy
from talking_trees.adapters import from_py_trees
from talking_trees.sdk import TalkingTrees


def create_ultra_complex_tree():
    """Create the most complex behavior tree possible."""
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


if __name__ == "__main__":
    print("Creating ultra complex tree...")
    root = create_ultra_complex_tree()

    print("Converting to TalkingTrees format...")
    tt_tree, context = from_py_trees(
        root,
        name="Ultra Complex Robot AI",
        version="1.0.0",
        description="Comprehensive demo showcasing all major node types: Timeout, Retry, Repeat, OneShot, Inverter, SuccessIsFailure, FailureIsSuccess, Parallel, and complex blackboard operations"
    )

    print("Saving to examples/trees/11_ultra_complex.json...")
    tt = TalkingTrees()
    tt.save_tree(tt_tree, "examples/trees/11_ultra_complex.json")

    print(" Ultra complex demo tree saved!")
    print("  Load in visual editor to explore advanced patterns")
