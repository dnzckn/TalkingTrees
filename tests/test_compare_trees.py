"""
Tests for compare_py_trees() function.

Tests the tree comparison functionality used to verify round-trip conversion
and check functional equivalence between py_trees roots.
"""

import operator

import py_trees
from py_trees.common import ComparisonExpression, ParallelPolicy

from talking_trees.adapters import compare_py_trees, from_py_trees, to_py_trees


def test_compare_identical_trees():
    """Test that identical trees are detected as equivalent."""
    root1 = py_trees.composites.Sequence(
        name="Main",
        memory=True,
        children=[
            py_trees.behaviours.Success(name="Task1"),
            py_trees.behaviours.Success(name="Task2"),
        ],
    )

    root2 = py_trees.composites.Sequence(
        name="Main",
        memory=True,
        children=[
            py_trees.behaviours.Success(name="Task1"),
            py_trees.behaviours.Success(name="Task2"),
        ],
    )

    assert compare_py_trees(root1, root2) is True


def test_compare_different_memory():
    """Test that different memory parameters are detected."""
    root1 = py_trees.composites.Sequence(
        name="Main",
        memory=True,
        children=[py_trees.behaviours.Success(name="Task1")],
    )

    root2 = py_trees.composites.Sequence(
        name="Main",
        memory=False,  # Different!
        children=[py_trees.behaviours.Success(name="Task1")],
    )

    assert compare_py_trees(root1, root2) is False


def test_compare_different_structure():
    """Test that different tree structures are detected."""
    root1 = py_trees.composites.Sequence(
        name="Main",
        memory=True,
        children=[
            py_trees.behaviours.Success(name="Task1"),
            py_trees.behaviours.Success(name="Task2"),
        ],
    )

    root2 = py_trees.composites.Sequence(
        name="Main",
        memory=True,
        children=[
            py_trees.behaviours.Success(name="Task1"),
            # Missing Task2!
        ],
    )

    assert compare_py_trees(root1, root2) is False


def test_compare_different_node_types():
    """Test that different node types are detected."""
    root1 = py_trees.composites.Sequence(
        name="Main",
        memory=True,
        children=[py_trees.behaviours.Success(name="Task1")],
    )

    root2 = py_trees.composites.Selector(  # Different type!
        name="Main",
        memory=True,
        children=[py_trees.behaviours.Success(name="Task1")],
    )

    assert compare_py_trees(root1, root2) is False


def test_compare_round_trip_simple():
    """Test that simple round-trip conversion is detected as equivalent."""
    root = py_trees.composites.Sequence(
        name="Main",
        memory=False,
        children=[
            py_trees.behaviours.Success(name="Task1"),
            py_trees.behaviours.Success(name="Task2"),
        ],
    )

    # Round-trip
    tt_tree, _ = from_py_trees(root, name="Test", version="1.0")
    round_trip = to_py_trees(tt_tree)

    assert compare_py_trees(root, round_trip) is True


def test_compare_round_trip_with_decorators():
    """Test round-trip with decorators."""
    root = py_trees.composites.Sequence(
        name="Main",
        memory=True,
        children=[
            py_trees.decorators.Timeout(
                name="TimeoutTask",
                child=py_trees.behaviours.Success(name="Task1"),
                duration=5.0,
            ),
            py_trees.decorators.Retry(
                name="RetryTask",
                child=py_trees.behaviours.Success(name="Task2"),
                num_failures=3,
            ),
        ],
    )

    # Round-trip
    tt_tree, _ = from_py_trees(root, name="Test", version="1.0")
    round_trip = to_py_trees(tt_tree)

    assert compare_py_trees(root, round_trip) is True


def test_compare_round_trip_with_blackboard():
    """Test round-trip with blackboard operations."""
    root = py_trees.composites.Sequence(
        name="Main",
        memory=True,
        children=[
            py_trees.behaviours.CheckBlackboardVariableValue(
                name="CheckBattery",
                check=ComparisonExpression("battery", 50, operator.ge),
            ),
            py_trees.behaviours.SetBlackboardVariable(
                name="SetMode",
                variable_name="mode",
                variable_value="active",
                overwrite=True,
            ),
        ],
    )

    # Round-trip
    tt_tree, _ = from_py_trees(root, name="Test", version="1.0")
    round_trip = to_py_trees(tt_tree)

    assert compare_py_trees(root, round_trip) is True


def test_compare_raise_on_difference():
    """Test that raise_on_difference parameter works."""
    root1 = py_trees.composites.Sequence(
        name="Main",
        memory=True,
        children=[py_trees.behaviours.Success(name="Task1")],
    )

    root2 = py_trees.composites.Sequence(
        name="Main",
        memory=False,  # Different!
        children=[py_trees.behaviours.Success(name="Task1")],
    )

    # Should not raise with default
    result = compare_py_trees(root1, root2, raise_on_difference=False)
    assert result is False

    # Should raise with raise_on_difference=True
    try:
        compare_py_trees(root1, root2, raise_on_difference=True)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not equivalent" in str(e).lower()


def test_ultra_complex_round_trip():
    """Test ultra-complex tree with all node types and configurations."""
    # Create complex tree with multiple decorator types, composites, etc.
    root = py_trees.composites.Selector(
        name="RobotBrain",
        memory=False,
        children=[
            # Branch 1: Timeout + Inverter + Sequence
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
                                check=ComparisonExpression("battery", 20, operator.lt),
                            ),
                            py_trees.behaviours.SetBlackboardVariable(
                                name="SetEmergencyMode",
                                variable_name="emergency",
                                variable_value=True,
                                overwrite=True,
                            ),
                        ],
                    ),
                ),
            ),
            # Branch 2: Retry + Parallel
            py_trees.decorators.Retry(
                name="RetryTasks",
                num_failures=3,
                child=py_trees.composites.Parallel(
                    name="ParallelSensors",
                    policy=ParallelPolicy.SuccessOnAll(synchronise=True),
                    children=[
                        py_trees.behaviours.Success(name="Sensor1"),
                        py_trees.behaviours.Success(name="Sensor2"),
                    ],
                ),
            ),
            # Branch 3: Repeat + Sequence
            py_trees.decorators.Repeat(
                name="RepeatNavigation",
                num_success=3,
                child=py_trees.composites.Sequence(
                    name="NavigationSequence",
                    memory=True,
                    children=[
                        py_trees.behaviours.Success(name="PlanPath"),
                        py_trees.behaviours.Success(name="ExecutePath"),
                    ],
                ),
            ),
            # Branch 4: OneShot
            py_trees.decorators.OneShot(
                name="OneShotTask",
                child=py_trees.behaviours.Success(name="InitTask"),
                policy=py_trees.common.OneShotPolicy.ON_SUCCESSFUL_COMPLETION,
            ),
            # Branch 5: Status converters
            py_trees.decorators.SuccessIsFailure(
                name="ConvertStatus",
                child=py_trees.behaviours.Success(name="Task"),
            ),
        ],
    )

    # Round-trip conversion
    tt_tree, _ = from_py_trees(root, name="UltraComplex", version="1.0")
    round_trip = to_py_trees(tt_tree)

    # Verify equivalence
    assert compare_py_trees(root, round_trip) is True


def test_complex_nested_decorators():
    """Test deeply nested decorators."""
    root = py_trees.decorators.Timeout(
        name="Outer",
        duration=30.0,
        child=py_trees.decorators.Retry(
            name="Middle",
            num_failures=5,
            child=py_trees.decorators.Repeat(
                name="Inner",
                num_success=2,
                child=py_trees.behaviours.Success(name="Task"),
            ),
        ),
    )

    # Round-trip
    tt_tree, _ = from_py_trees(root, name="Nested", version="1.0")
    round_trip = to_py_trees(tt_tree)

    assert compare_py_trees(root, round_trip) is True


def test_multiple_blackboard_operations():
    """Test multiple blackboard operations."""
    root = py_trees.composites.Sequence(
        name="Main",
        memory=True,
        children=[
            py_trees.behaviours.CheckBlackboardVariableExists(
                name="CheckVar1", variable_name="var1"
            ),
            py_trees.behaviours.SetBlackboardVariable(
                name="SetVar2",
                variable_name="var2",
                variable_value=42,
                overwrite=False,
            ),
            py_trees.behaviours.CheckBlackboardVariableValue(
                name="CheckVar3", check=ComparisonExpression("var3", "test", operator.eq)
            ),
            py_trees.behaviours.SetBlackboardVariable(
                name="SetVar4",
                variable_name="var4",
                variable_value=[1, 2, 3],
                overwrite=True,
            ),
        ],
    )

    # Round-trip
    tt_tree, _ = from_py_trees(root, name="Blackboard", version="1.0")
    round_trip = to_py_trees(tt_tree)

    assert compare_py_trees(root, round_trip) is True


def test_all_status_converters():
    """Test all status converter decorators."""
    root = py_trees.composites.Sequence(
        name="Main",
        memory=True,
        children=[
            py_trees.decorators.SuccessIsFailure(
                name="SF", child=py_trees.behaviours.Success(name="T1")
            ),
            py_trees.decorators.FailureIsSuccess(
                name="FS", child=py_trees.behaviours.Success(name="T2")
            ),
            py_trees.decorators.FailureIsRunning(
                name="FR", child=py_trees.behaviours.Success(name="T3")
            ),
            py_trees.decorators.RunningIsFailure(
                name="RF", child=py_trees.behaviours.Success(name="T4")
            ),
            py_trees.decorators.RunningIsSuccess(
                name="RS", child=py_trees.behaviours.Success(name="T5")
            ),
            py_trees.decorators.SuccessIsRunning(
                name="SR", child=py_trees.behaviours.Success(name="T6")
            ),
        ],
    )

    # Round-trip
    tt_tree, _ = from_py_trees(root, name="StatusConverters", version="1.0")
    round_trip = to_py_trees(tt_tree)

    assert compare_py_trees(root, round_trip) is True
