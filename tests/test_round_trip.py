#!/usr/bin/env python
"""Test round-trip conversion validation."""

import py_trees
from py_trees.behaviours import Failure, SetBlackboardVariable, Success
from py_trees.composites import Selector, Sequence

from talking_trees.adapters.py_trees_adapter import from_py_trees, to_py_trees
from talking_trees.core.round_trip_validator import RoundTripValidator


def test_simple_round_trip():
    """Test round-trip with simple tree."""
    print("=" * 70)
    print("TEST 1: Simple Round-Trip (Success nodes)")
    print("=" * 70)

    # Create original tree
    original = Sequence(
        name="Root",
        memory=True,
        children=[
            Success(name="Step1"),
            Success(name="Step2"),
            Success(name="Step3"),
        ],
    )

    # Round-trip conversion
    pf_tree, context = from_py_trees(original, name="Test")
    round_trip = to_py_trees(pf_tree)

    # Validate
    validator = RoundTripValidator()
    is_valid = validator.validate(original, round_trip)

    if is_valid:
        print("✓ PASSED: Simple tree round-trip successful")
        print(validator.get_error_summary())
    else:
        print("✗ FAILED: Validation errors:")
        print(validator.get_error_summary())

    print()
    return is_valid


def test_complex_round_trip():
    """Test round-trip with complex tree."""
    print("=" * 70)
    print("TEST 2: Complex Round-Trip (Nested composites)")
    print("=" * 70)

    # Create complex tree
    original = Sequence(
        name="Root",
        memory=True,
        children=[
            Success(name="Init"),
            Selector(
                name="Choice",
                memory=False,
                children=[
                    Success(name="Option1"),
                    Failure(name="Option2"),
                    Success(name="Option3"),
                ],
            ),
            Sequence(
                name="Cleanup",
                memory=True,
                children=[
                    Success(name="Step1"),
                    Success(name="Step2"),
                ],
            ),
        ],
    )

    # Round-trip conversion
    pf_tree, context = from_py_trees(original, name="Test")
    round_trip = to_py_trees(pf_tree)

    # Validate
    validator = RoundTripValidator()
    is_valid = validator.validate(original, round_trip)

    if is_valid:
        print("✓ PASSED: Complex tree round-trip successful")
        print(validator.get_error_summary())
    else:
        print("✗ FAILED: Validation errors:")
        print(validator.get_error_summary())

    print()
    return is_valid


def test_setblackboard_round_trip():
    """Test round-trip with SetBlackboardVariable."""
    print("=" * 70)
    print("TEST 3: SetBlackboardVariable Round-Trip")
    print("=" * 70)

    # Create tree with SetBlackboardVariable
    original = Sequence(
        name="Root",
        memory=True,
        children=[
            SetBlackboardVariable(
                name="Set Speed",
                variable_name="speed",
                variable_value=42.5,
                overwrite=True,
            ),
            SetBlackboardVariable(
                name="Set Mode",
                variable_name="mode",
                variable_value="AUTO",
                overwrite=True,
            ),
            Success(name="Done"),
        ],
    )

    # Round-trip conversion
    pf_tree, context = from_py_trees(original, name="Test")

    # Check for conversion warnings
    if context.has_warnings():
        print("⚠ Conversion warnings detected:")
        print(context.summary())
        print()

    round_trip = to_py_trees(pf_tree)

    # Validate
    validator = RoundTripValidator()
    is_valid = validator.validate(original, round_trip)

    if is_valid:
        print("✓ PASSED: SetBlackboardVariable values preserved")
        print(validator.get_error_summary())
    else:
        print("⚠ FAILED: SetBlackboardVariable values NOT preserved")
        print(validator.get_error_summary())
        print("\nNote: This is a known issue with py_trees - values may not be")
        print("      accessible after construction due to private attributes.")

    print()
    return is_valid


def test_decorator_round_trip():
    """Test round-trip with decorators."""
    print("=" * 70)
    print("TEST 4: Decorator Round-Trip (Inverter, Timeout, Retry)")
    print("=" * 70)

    # Create tree with decorators
    original = Sequence(
        name="Root",
        memory=True,
        children=[
            py_trees.decorators.Inverter(name="Not", child=Failure(name="FailTask")),
            py_trees.decorators.Timeout(
                name="TimeLimit", child=Success(name="SlowTask"), duration=5.0
            ),
            py_trees.decorators.Retry(
                name="RetryThrice", child=Success(name="FlakeyTask"), num_failures=3
            ),
        ],
    )

    # Round-trip conversion
    pf_tree, context = from_py_trees(original, name="Test")
    round_trip = to_py_trees(pf_tree)

    # Validate
    validator = RoundTripValidator()
    is_valid = validator.validate(original, round_trip)

    if is_valid:
        print("✓ PASSED: Decorator tree round-trip successful")
        print(validator.get_error_summary())
    else:
        print("✗ FAILED: Validation errors:")
        print(validator.get_error_summary())

    print()
    return is_valid


def test_memory_parameter():
    """Test that memory parameter is preserved."""
    print("=" * 70)
    print("TEST 5: Memory Parameter Preservation")
    print("=" * 70)

    # Create trees with different memory settings
    original = Sequence(
        name="Root",
        memory=False,  # Important: memory=False
        children=[
            Selector(
                name="Choice",
                memory=True,  # Different from parent
                children=[
                    Success(name="Option1"),
                    Success(name="Option2"),
                ],
            ),
        ],
    )

    # Round-trip conversion
    pf_tree, context = from_py_trees(original, name="Test")
    round_trip = to_py_trees(pf_tree)

    # Validate
    validator = RoundTripValidator()
    is_valid = validator.validate(original, round_trip)

    # Check memory specifically
    if round_trip.memory is False and round_trip.children[0].memory is True:
        print(f"✓ Root memory: {round_trip.memory} (expected: False)")
        print(f"✓ Child memory: {round_trip.children[0].memory} (expected: True)")

    if is_valid:
        print("✓ PASSED: Memory parameters preserved")
        print(validator.get_error_summary())
    else:
        print("✗ FAILED: Memory parameters NOT preserved")
        print(validator.get_error_summary())

    print()
    return is_valid


if __name__ == "__main__":
    print("\n🧪 Testing Round-Trip Conversion Validation\n")

    results = []
    results.append(("Simple Round-Trip", test_simple_round_trip()))
    results.append(("Complex Round-Trip", test_complex_round_trip()))
    results.append(("SetBlackboard Round-Trip", test_setblackboard_round_trip()))
    results.append(("Decorator Round-Trip", test_decorator_round_trip()))
    results.append(("Memory Parameter", test_memory_parameter()))

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n✅ All tests passed! Round-trip validation is working correctly.")
    else:
        print("\n⚠ Some tests failed. This may indicate:")
        print("  - SetBlackboardVariable value extraction issues (known limitation)")
        print("  - Other conversion problems that need investigation")

    print()
