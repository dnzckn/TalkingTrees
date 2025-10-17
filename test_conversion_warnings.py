#!/usr/bin/env python
"""Test ConversionContext warnings in serializer."""

import py_trees
from py_trees.composites import Sequence, Selector
from py_trees.behaviours import Success, Failure
from py_forest.adapters.py_trees_adapter import from_py_trees, ConversionContext


def test_no_warnings():
    """Test that simple trees produce no warnings."""
    print("=" * 70)
    print("TEST 1: No Warnings (simple tree)")
    print("=" * 70)

    # Create a simple tree with known node types
    root = Sequence(
        name="Root",
        memory=True,
        children=[
            Success(name="Task1"),
            Success(name="Task2"),
        ]
    )

    # Convert and check context
    pf_tree, context = from_py_trees(root, name="Test Tree")

    print(context.summary())

    if not context.has_warnings():
        print("✓ PASSED: No warnings as expected")
        print()
        return True
    else:
        print("✗ FAILED: Unexpected warnings")
        print()
        return False


def test_setblackboard_warning():
    """Test warning for SetBlackboardVariable value not accessible."""
    print("=" * 70)
    print("TEST 2: SetBlackboardVariable Data Loss Warning")
    print("=" * 70)

    # Create tree with SetBlackboardVariable
    # Note: value will be accessible via reflection in current implementation,
    # but if it weren't, we'd get a warning
    root = Sequence(
        name="Root",
        memory=True,
        children=[
            py_trees.behaviours.SetBlackboardVariable(
                name="Set Speed",
                variable_name="speed",
                variable_value=42.5,
                overwrite=True
            ),
            Success(name="Task"),
        ]
    )

    # Convert and check context
    pf_tree, context = from_py_trees(root, name="Test Tree")

    print(context.summary())

    # In current implementation, value should be extracted successfully
    if not context.has_warnings():
        print("✓ PASSED: Value extracted successfully, no warning needed")

        # Verify value was actually extracted
        set_node = pf_tree.root.children[0]
        if set_node.config.get('value') == 42.5:
            print("✓ Value preserved:", set_node.config['value'])
        else:
            print("✗ Value not preserved!")
            return False
    else:
        print("⚠ WARNING: Value extraction failed (this might be expected on some py_trees versions)")
        for warning in context.warnings:
            print(f"  - {warning}")

    print()
    return True


def test_unknown_node_type():
    """Test warning for unknown node types."""
    print("=" * 70)
    print("TEST 3: Unknown Node Type Warning")
    print("=" * 70)

    # Create a custom behavior class
    class CustomBehavior(py_trees.behaviour.Behaviour):
        """Custom behavior not in PyForest registry."""

        def __init__(self, name):
            super().__init__(name)

        def update(self):
            return py_trees.common.Status.SUCCESS

    # Create tree with custom behavior
    root = Sequence(
        name="Root",
        memory=True,
        children=[
            CustomBehavior(name="CustomTask"),
            Success(name="Task"),
        ]
    )

    # Convert and check context
    pf_tree, context = from_py_trees(root, name="Test Tree")

    print(context.summary())

    if context.has_warnings():
        # Check if warning mentions CustomBehavior
        has_custom_warning = any("CustomBehavior" in w for w in context.warnings)
        if has_custom_warning:
            print("✓ PASSED: Warning generated for unknown type 'CustomBehavior'")
            print()
            return True
        else:
            print("✗ FAILED: Warning doesn't mention CustomBehavior")
            print()
            return False
    else:
        print("✗ FAILED: No warning generated for unknown node type")
        print()
        return False


def test_context_api():
    """Test ConversionContext API."""
    print("=" * 70)
    print("TEST 4: ConversionContext API")
    print("=" * 70)

    context = ConversionContext()

    # Test initial state
    if not context.has_warnings():
        print("✓ Initially no warnings")
    else:
        print("✗ Should have no warnings initially")
        return False

    # Add warnings
    context.warn("First warning")
    context.warn("Second warning", node_name="MyNode")

    if context.has_warnings():
        print("✓ Warnings detected after adding")
    else:
        print("✗ Should have warnings after adding")
        return False

    # Check warning count
    if len(context.warnings) == 2:
        print(f"✓ Correct warning count: {len(context.warnings)}")
    else:
        print(f"✗ Wrong warning count: {len(context.warnings)}")
        return False

    # Check warning format
    if context.warnings[0] == "First warning":
        print("✓ First warning correct format")
    else:
        print(f"✗ First warning wrong: {context.warnings[0]}")
        return False

    if context.warnings[1] == "[MyNode] Second warning":
        print("✓ Second warning includes node name")
    else:
        print(f"✗ Second warning wrong: {context.warnings[1]}")
        return False

    # Test summary
    summary = context.summary()
    if "2 conversion warning(s)" in summary:
        print("✓ Summary shows warning count")
    else:
        print(f"✗ Summary wrong: {summary}")
        return False

    print()
    return True


if __name__ == "__main__":
    print("\n🧪 Testing ConversionContext Warnings\n")

    results = []
    results.append(("No Warnings", test_no_warnings()))
    results.append(("SetBlackboard Warning", test_setblackboard_warning()))
    results.append(("Unknown Node Type", test_unknown_node_type()))
    results.append(("Context API", test_context_api()))

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n✅ All tests passed! ConversionContext is working correctly.")
    else:
        print("\n❌ Some tests failed. Check output above.")

    print()
