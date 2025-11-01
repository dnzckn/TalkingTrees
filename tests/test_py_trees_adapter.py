"""
Comprehensive Test Suite for py_trees Adapter
==============================================

Tests all functionality of the py_trees <-> PyForest adapter.

Run with: python tests/test_py_trees_adapter.py
"""

import operator

import py_trees
from py_trees.common import ComparisonExpression

from py_forest.adapters import from_py_trees, to_py_trees
from py_forest.sdk import PyForest


def test_basic_conversion():
    """Test 1: Basic tree conversion"""
    print("\n" + "=" * 70)
    print("TEST 1: Basic Conversion (Composites + Success/Failure)")
    print("=" * 70)

    # Create py_trees tree
    root = py_trees.composites.Sequence(name="Test Sequence", memory=False)
    root.add_child(py_trees.behaviours.Success(name="Step 1"))
    root.add_child(py_trees.behaviours.Success(name="Step 2"))
    root.add_child(py_trees.behaviours.Failure(name="Step 3"))

    # Convert to PyForest
    pf_tree, _ = from_py_trees(root, name="Basic Test", version="1.0.0")

    # Verify structure
    assert pf_tree.metadata.name == "Basic Test"
    assert pf_tree.metadata.version == "1.0.0"
    assert pf_tree.root.node_type == "Sequence"
    assert len(pf_tree.root.children) == 3
    assert pf_tree.root.children[0].node_type == "Success"
    assert pf_tree.root.children[2].node_type == "Failure"

    print("✓ Structure validated")
    print("✓ TEST 1 PASSED")
    return pf_tree


def test_blackboard_condition():
    """Test 2: CheckBlackboardVariableValue with ComparisonExpression"""
    print("\n" + "=" * 70)
    print("TEST 2: Blackboard Condition (ComparisonExpression)")
    print("=" * 70)

    # Create tree with condition
    root = py_trees.composites.Sequence(name="Condition Test", memory=False)

    # Create comparison expression
    check = ComparisonExpression("battery_level", operator.lt, 20)
    condition = py_trees.behaviours.CheckBlackboardVariableValue(
        name="Battery Low?", check=check
    )
    root.add_child(condition)

    # Convert
    pf_tree, _ = from_py_trees(root, name="Condition Test", version="1.0.0")

    # Verify
    condition_node = pf_tree.root.children[0]
    assert condition_node.config["variable"] == "battery_level"
    assert condition_node.config["operator"] == "<"
    assert condition_node.config["value"] == 20

    print(
        f"✓ Condition config: variable={condition_node.config['variable']}, "
        f"op={condition_node.config['operator']}, value={condition_node.config['value']}"
    )
    print("✓ TEST 2 PASSED")
    return pf_tree


def test_blackboard_setter():
    """Test 3: SetBlackboardVariable"""
    print("\n" + "=" * 70)
    print("TEST 3: Blackboard Setter")
    print("=" * 70)

    # Create tree with setter
    root = py_trees.composites.Sequence(name="Setter Test", memory=False)
    setter = py_trees.behaviours.SetBlackboardVariable(
        name="Set Action",
        variable_name="robot_action",
        variable_value="charge",
        overwrite=True,
    )
    root.add_child(setter)

    # Convert
    pf_tree, _ = from_py_trees(root, name="Setter Test", version="1.0.0")

    # Verify
    setter_node = pf_tree.root.children[0]
    assert setter_node.config["variable"] == "robot_action"
    assert setter_node.config["overwrite"] is True

    # Note: value is not extractable from py_trees SetBlackboardVariable
    print(
        f"✓ Setter config: variable={setter_node.config['variable']}, "
        f"overwrite={setter_node.config['overwrite']}"
    )
    print("✓ TEST 3 PASSED")
    return pf_tree


def test_complex_tree():
    """Test 4: Complex tree with multiple node types"""
    print("\n" + "=" * 70)
    print("TEST 4: Complex Tree (Selector + Sequences + Conditions + Actions)")
    print("=" * 70)

    # Build complex tree
    root = py_trees.composites.Selector(name="Robot AI", memory=False)

    # Emergency branch
    emergency = py_trees.composites.Sequence(name="Emergency", memory=False)
    emergency_check = ComparisonExpression("error_level", operator.gt, 90)
    emergency.add_child(
        py_trees.behaviours.CheckBlackboardVariableValue(
            name="Critical Error?", check=emergency_check
        )
    )
    emergency.add_child(
        py_trees.behaviours.SetBlackboardVariable(
            name="Emergency Stop",
            variable_name="action",
            variable_value="stop",
            overwrite=True,
        )
    )

    # Normal branch
    normal = py_trees.composites.Sequence(name="Normal Ops", memory=False)
    normal.add_child(py_trees.behaviours.Success(name="Check Systems"))
    normal.add_child(
        py_trees.behaviours.SetBlackboardVariable(
            name="Set Running",
            variable_name="action",
            variable_value="run",
            overwrite=True,
        )
    )

    root.add_child(emergency)
    root.add_child(normal)

    # Convert
    pf_tree, _ = from_py_trees(root, name="Complex Robot AI", version="1.0.0")

    # Verify
    assert pf_tree.root.node_type == "Selector"
    assert len(pf_tree.root.children) == 2
    assert pf_tree.root.children[0].node_type == "Sequence"
    assert len(pf_tree.root.children[0].children) == 2

    print(
        f"✓ Root: {pf_tree.root.node_type} with {len(pf_tree.root.children)} children"
    )
    print("✓ TEST 4 PASSED")
    return pf_tree


def test_save_load_roundtrip():
    """Test 5: Save/Load round-trip"""
    print("\n" + "=" * 70)
    print("TEST 5: Save/Load Round-trip")
    print("=" * 70)

    # Create tree
    root = py_trees.composites.Selector(name="Test", memory=False)
    root.add_child(py_trees.behaviours.Success(name="A"))
    root.add_child(py_trees.behaviours.Success(name="B"))

    # Convert and save
    pf = PyForest()
    pf_tree, _ = from_py_trees(root, name="Roundtrip Test", version="1.0.0")
    pf.save_tree(pf_tree, "/tmp/test_roundtrip.json")

    # Load back
    loaded = pf.load_tree("/tmp/test_roundtrip.json")

    # Verify
    assert loaded.metadata.name == "Roundtrip Test"
    assert loaded.root.node_type == "Selector"
    assert len(loaded.root.children) == 2

    print("✓ Saved and loaded successfully")
    print("✓ Structure preserved")
    print("✓ TEST 5 PASSED")


def test_reverse_conversion():
    """Test 6: Reverse conversion (PyForest → py_trees)"""
    print("\n" + "=" * 70)
    print("TEST 6: Reverse Conversion (PyForest → py_trees)")
    print("=" * 70)

    # Create PyForest tree
    root = py_trees.composites.Sequence(name="Original", memory=False)
    check = ComparisonExpression("value", operator.eq, 42)
    root.add_child(
        py_trees.behaviours.CheckBlackboardVariableValue(
            name="Check Value", check=check
        )
    )
    root.add_child(
        py_trees.behaviours.SetBlackboardVariable(
            name="Set Result",
            variable_name="result",
            variable_value="success",
            overwrite=True,
        )
    )

    # Convert to PyForest
    pf = PyForest()
    pf_tree, _ = from_py_trees(root, name="Reverse Test", version="1.0.0")

    # Save
    pf.save_tree(pf_tree, "/tmp/test_reverse.json")

    # Load
    loaded = pf.load_tree("/tmp/test_reverse.json")

    # Convert back to py_trees
    pt_root = to_py_trees(loaded)

    # Verify
    assert pt_root.name == "Original"
    assert isinstance(pt_root, py_trees.composites.Sequence)
    assert len(pt_root.children) == 2
    assert isinstance(
        pt_root.children[0], py_trees.behaviours.CheckBlackboardVariableValue
    )
    assert isinstance(pt_root.children[1], py_trees.behaviours.SetBlackboardVariable)

    # Verify condition details
    condition = pt_root.children[0]
    assert condition.check.variable == "value"
    assert condition.check.operator == 42  # Remember py_trees swaps these
    assert condition.check.value == operator.eq

    print("✓ Converted PyForest → py_trees")
    print("✓ Structure validated")
    print("✓ Condition parameters preserved")
    print("✓ TEST 6 PASSED")


def test_multiple_operators():
    """Test 7: All comparison operators"""
    print("\n" + "=" * 70)
    print("TEST 7: All Comparison Operators")
    print("=" * 70)

    operators_to_test = [
        (operator.lt, "<", 10),
        (operator.le, "<=", 20),
        (operator.gt, ">", 30),
        (operator.ge, ">=", 40),
        (operator.eq, "==", 50),
        (operator.ne, "!=", 60),
    ]

    for op_func, op_str, value in operators_to_test:
        # Create condition
        check = ComparisonExpression("test_var", op_func, value)
        condition = py_trees.behaviours.CheckBlackboardVariableValue(
            name=f"Test {op_str}", check=check
        )

        # Wrap in sequence
        root = py_trees.composites.Sequence(name="Test", memory=False)
        root.add_child(condition)

        # Convert
        pf_tree, _ = from_py_trees(root, name="Op Test", version="1.0.0")

        # Verify
        cond_node = pf_tree.root.children[0]
        assert cond_node.config["operator"] == op_str, f"Failed for {op_str}"
        assert cond_node.config["value"] == value

        print(f"  ✓ {op_str:3s} operator: test_var {op_str} {value}")

    print("✓ All operators tested successfully")
    print("✓ TEST 7 PASSED")


def test_nested_composites():
    """Test 8: Deeply nested composites"""
    print("\n" + "=" * 70)
    print("TEST 8: Nested Composites")
    print("=" * 70)

    # Create nested structure
    root = py_trees.composites.Selector(name="L1", memory=False)
    l2 = py_trees.composites.Sequence(name="L2", memory=False)
    l3 = py_trees.composites.Selector(name="L3", memory=False)
    l4 = py_trees.composites.Sequence(name="L4", memory=False)
    l4.add_child(py_trees.behaviours.Success(name="Leaf"))

    l3.add_child(l4)
    l2.add_child(l3)
    root.add_child(l2)

    # Convert
    pf_tree, _ = from_py_trees(root, name="Nested Test", version="1.0.0")

    # Verify depth
    assert pf_tree.root.node_type == "Selector"
    assert pf_tree.root.children[0].node_type == "Sequence"
    assert pf_tree.root.children[0].children[0].node_type == "Selector"
    assert pf_tree.root.children[0].children[0].children[0].node_type == "Sequence"
    assert (
        pf_tree.root.children[0].children[0].children[0].children[0].node_type
        == "Success"
    )

    print("✓ 4 levels of nesting preserved")
    print("✓ TEST 8 PASSED")


def test_parallel_composite():
    """Test 9: Parallel composite"""
    print("\n" + "=" * 70)
    print("TEST 9: Parallel Composite")
    print("=" * 70)

    # Create parallel
    root = py_trees.composites.Parallel(
        name="Monitor Systems", policy=py_trees.common.ParallelPolicy.SuccessOnAll()
    )
    root.add_child(py_trees.behaviours.Success(name="Monitor Sensors"))
    root.add_child(py_trees.behaviours.Success(name="Monitor Comms"))

    # Convert
    pf_tree, _ = from_py_trees(root, name="Parallel Test", version="1.0.0")

    # Verify
    assert pf_tree.root.node_type == "Parallel"
    assert len(pf_tree.root.children) == 2

    print("✓ Parallel node converted")
    print("✓ TEST 9 PASSED")


def test_inverter_decorator():
    """Test 10: Inverter decorator"""
    print("\n" + "=" * 70)
    print("TEST 10: Inverter Decorator")
    print("=" * 70)

    # Create inverter
    child = py_trees.behaviours.Success(name="Always Success")
    root = py_trees.decorators.Inverter(name="Invert It", child=child)

    # Convert
    pf_tree, _ = from_py_trees(root, name="Inverter Test", version="1.0.0")

    # Verify
    assert pf_tree.root.node_type == "Inverter"
    assert len(pf_tree.root.children) == 1
    assert pf_tree.root.children[0].node_type == "Success"

    print("✓ Inverter decorator converted")
    print("✓ Child preserved")
    print("✓ TEST 10 PASSED")


def test_repeat_decorator():
    """Test 11: Repeat decorator"""
    print("\n" + "=" * 70)
    print("TEST 11: Repeat Decorator")
    print("=" * 70)

    # Create repeat decorator (py_trees uses num_success, not num_repeats)
    child = py_trees.behaviours.Success(name="Task")
    root = py_trees.decorators.Repeat(name="Repeat 5 times", child=child, num_success=5)

    # Convert
    pf_tree, _ = from_py_trees(root, name="Repeat Test", version="1.0.0")

    # Verify
    assert pf_tree.root.node_type == "Repeat"
    assert pf_tree.root.config.get("num_success") == 5
    assert len(pf_tree.root.children) == 1

    print(
        f"✓ Repeat decorator converted with num_success={pf_tree.root.config.get('num_success')}"
    )
    print("✓ TEST 11 PASSED")


def test_retry_decorator():
    """Test 12: Retry decorator"""
    print("\n" + "=" * 70)
    print("TEST 12: Retry Decorator")
    print("=" * 70)

    # Create retry decorator (py_trees uses num_failures, not num_retries)
    child = py_trees.behaviours.Failure(name="Flaky Task")
    root = py_trees.decorators.Retry(name="Retry 3 times", child=child, num_failures=3)

    # Convert
    pf_tree, _ = from_py_trees(root, name="Retry Test", version="1.0.0")

    # Verify
    assert pf_tree.root.node_type == "Retry"
    assert pf_tree.root.config.get("num_failures") == 3
    assert len(pf_tree.root.children) == 1

    print(
        f"✓ Retry decorator converted with num_failures={pf_tree.root.config.get('num_failures')}"
    )
    print("✓ TEST 12 PASSED")


def test_timeout_decorator():
    """Test 13: Timeout decorator"""
    print("\n" + "=" * 70)
    print("TEST 13: Timeout Decorator")
    print("=" * 70)

    # Create timeout decorator
    child = py_trees.behaviours.Running(name="Long Task")
    root = py_trees.decorators.Timeout(
        name="5 second timeout", child=child, duration=5.0
    )

    # Convert
    pf_tree, _ = from_py_trees(root, name="Timeout Test", version="1.0.0")

    # Verify
    assert pf_tree.root.node_type == "Timeout"
    assert pf_tree.root.config.get("duration") == 5.0
    assert len(pf_tree.root.children) == 1

    print(
        f"✓ Timeout decorator converted with duration={pf_tree.root.config.get('duration')}s"
    )
    print("✓ TEST 13 PASSED")


def test_decorator_reverse_conversion():
    """Test 14: Decorator reverse conversion (PyForest → py_trees)"""
    print("\n" + "=" * 70)
    print("TEST 14: Decorator Reverse Conversion")
    print("=" * 70)

    # Create py_trees tree with decorators
    child = py_trees.behaviours.Success(name="Task")
    inverter = py_trees.decorators.Inverter(name="Not Task", child=child)
    root = py_trees.composites.Sequence(name="With Decorator", memory=False)
    root.add_child(inverter)

    # Convert to PyForest
    pf = PyForest()
    pf_tree, _ = from_py_trees(root, name="Decorator Test", version="1.0.0")

    # Save and load
    pf.save_tree(pf_tree, "/tmp/test_decorator.json")
    loaded = pf.load_tree("/tmp/test_decorator.json")

    # Convert back to py_trees
    pt_root = to_py_trees(loaded)

    # Verify structure
    assert pt_root.name == "With Decorator"
    assert isinstance(pt_root, py_trees.composites.Sequence)
    assert len(pt_root.children) == 1
    assert isinstance(pt_root.children[0], py_trees.decorators.Inverter)

    print("✓ Decorator round-trip successful")
    print("✓ Structure preserved")
    print("✓ TEST 14 PASSED")


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 80)
    print(" COMPREHENSIVE PY_TREES ADAPTER TEST SUITE")
    print("=" * 80)

    tests = [
        test_basic_conversion,
        test_blackboard_condition,
        test_blackboard_setter,
        test_complex_tree,
        test_save_load_roundtrip,
        test_reverse_conversion,
        test_multiple_operators,
        test_nested_composites,
        test_parallel_composite,
        test_inverter_decorator,
        test_repeat_decorator,
        test_retry_decorator,
        test_timeout_decorator,
        test_decorator_reverse_conversion,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            failed += 1

    # Summary
    print("\n" + "=" * 80)
    print(" TEST SUMMARY")
    print("=" * 80)
    print(f"  Total:  {passed + failed}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")

    if failed == 0:
        print("\n  ✓ ALL TESTS PASSED!")
    else:
        print(f"\n  ✗ {failed} TEST(S) FAILED")

    print("=" * 80 + "\n")

    return failed == 0


if __name__ == "__main__":
    import sys

    success = run_all_tests()
    sys.exit(0 if success else 1)
