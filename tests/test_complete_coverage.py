#!/usr/bin/env python
"""
Comprehensive Coverage Test for py_trees ↔ talkingtrees Reversibility
==================================================================

This script systematically tests ALL supported node types through the full pipeline:
py_trees → talkingtrees → flat file → talkingtrees → py_trees

Tests complete reversibility and identifies any gaps or data loss.
"""

import json
import operator
import tempfile
from pathlib import Path

import py_trees
from py_trees.behaviours import Failure, Running, SetBlackboardVariable, Success
from py_trees.common import ComparisonExpression, ParallelPolicy
from py_trees.composites import Parallel, Selector, Sequence
from py_trees.decorators import Inverter, Retry, Timeout

from talking_trees.adapters.py_trees_adapter import from_py_trees, to_py_trees
from talking_trees.core.round_trip_validator import RoundTripValidator
from talking_trees.sdk import TalkingTrees


class ComprehensiveCoverageTest:
    """Test coverage for all py_trees node types."""

    def __init__(self):
        self.results: list[tuple[str, bool, str]] = []
        self.tt = TalkingTrees()
        self.temp_dir = tempfile.mkdtemp()

    def run_all_tests(self):
        """Run all coverage tests."""
        print("=" * 80)
        print("COMPREHENSIVE REVERSIBILITY TEST")
        print("Testing: py_trees → talkingtrees → JSON → talkingtrees → py_trees")
        print("=" * 80)
        print()

        # Test each category
        self.test_composites()
        self.test_decorators()
        self.test_behaviors()
        self.test_blackboard_operations()
        self.test_complex_combinations()

        # Print summary
        self.print_summary()

    def test_node(self, name: str, root_node, check_execution: bool = False) -> bool:
        """
        Test a single node through the complete pipeline.

        Args:
            name: Test name
            root_node: py_trees node to test
            check_execution: If True, also test execution

        Returns:
            True if test passed, False otherwise
        """
        try:
            # Step 1: py_trees → talkingtrees
            tt_tree, context = from_py_trees(root_node, name=name, version="1.0.0")

            if context.has_warnings():
                print(f"  ⚠ Conversion warnings: {len(context.warnings)}")
                for warning in context.warnings:
                    print(f"    - {warning}")

            # Step 2: talkingtrees → JSON file
            json_path = Path(self.temp_dir) / f"{name.replace(' ', '_')}.json"
            self.tt.save_tree(tt_tree, str(json_path))

            # Verify JSON is valid
            with open(json_path) as f:
                json_data = json.load(f)
            assert json_data["$schema"] == "1.0.0", "Invalid schema version"

            # Step 3: JSON → talkingtrees
            loaded_tree = self.tt.load_tree(str(json_path))

            # Step 4: talkingtrees → py_trees
            round_trip = to_py_trees(loaded_tree)

            # Step 5: Validate equivalence
            validator = RoundTripValidator()
            is_valid = validator.validate(root_node, round_trip)

            if not is_valid:
                error_msg = validator.get_error_summary()
                self.results.append((name, False, error_msg))
                print(f"❌ {name}")
                print(f"   {error_msg}")
                return False

            # Optional: Test execution
            if check_execution:
                from talking_trees.core.serializer import TreeSerializer

                serializer = TreeSerializer()
                bt = serializer.deserialize(loaded_tree)
                bt.setup()
                bt.tick()  # Should not crash

            self.results.append((name, True, "✓ Complete reversibility verified"))
            print(f"✅ {name}")
            return True

        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            self.results.append((name, False, error_msg))
            print(f"❌ {name}")
            print(f"   {error_msg}")
            return False

    # ==================== COMPOSITES ====================

    def test_composites(self):
        """Test all composite node types."""
        print("\n" + "=" * 80)
        print("COMPOSITES")
        print("=" * 80)

        # Sequence with memory=True
        root = Sequence(
            name="SeqMemTrue",
            memory=True,
            children=[
                Success(name="Step1"),
                Success(name="Step2"),
                Success(name="Step3"),
            ],
        )
        self.test_node("Sequence (memory=True)", root)

        # Sequence with memory=False
        root = Sequence(
            name="SeqMemFalse",
            memory=False,
            children=[
                Success(name="Step1"),
                Success(name="Step2"),
            ],
        )
        self.test_node("Sequence (memory=False)", root)

        # Selector with memory=True
        root = Selector(
            name="SelMemTrue",
            memory=True,
            children=[
                Failure(name="Option1"),
                Success(name="Option2"),
                Failure(name="Option3"),
            ],
        )
        self.test_node("Selector (memory=True)", root)

        # Selector with memory=False
        root = Selector(
            name="SelMemFalse",
            memory=False,
            children=[
                Failure(name="Option1"),
                Success(name="Option2"),
            ],
        )
        self.test_node("Selector (memory=False)", root)

        # Parallel with SuccessOnAll
        root = Parallel(
            name="ParallelAll",
            policy=ParallelPolicy.SuccessOnAll(synchronise=True),
            children=[
                Success(name="Task1"),
                Success(name="Task2"),
                Success(name="Task3"),
            ],
        )
        self.test_node("Parallel (SuccessOnAll)", root)

        # Parallel with SuccessOnOne
        root = Parallel(
            name="ParallelOne",
            policy=ParallelPolicy.SuccessOnOne(),
            children=[
                Failure(name="Task1"),
                Success(name="Task2"),
            ],
        )
        self.test_node("Parallel (SuccessOnOne)", root)

    # ==================== DECORATORS ====================

    def test_decorators(self):
        """Test all decorator node types."""
        print("\n" + "=" * 80)
        print("DECORATORS")
        print("=" * 80)

        # Inverter
        root = Inverter(name="NotGate", child=Failure(name="FailTask"))
        self.test_node("Inverter", root)

        # Timeout
        root = Timeout(name="TimeLimit", child=Success(name="SlowTask"), duration=5.0)
        self.test_node("Timeout (5.0s)", root)

        # Timeout with different duration
        root = Timeout(name="ShortTimeLimit", child=Success(name="Task"), duration=0.5)
        self.test_node("Timeout (0.5s)", root)

        # Retry
        root = Retry(
            name="RetryThrice", child=Success(name="FlakeyTask"), num_failures=3
        )
        self.test_node("Retry (3 attempts)", root)

        # Retry with different count
        root = Retry(name="RetryFive", child=Success(name="Task"), num_failures=5)
        self.test_node("Retry (5 attempts)", root)

    # ==================== BEHAVIORS ====================

    def test_behaviors(self):
        """Test all basic behavior node types."""
        print("\n" + "=" * 80)
        print("BASIC BEHAVIORS")
        print("=" * 80)

        # Success
        root = Success(name="SuccessNode")
        self.test_node("Success", root)

        # Failure
        root = Failure(name="FailureNode")
        self.test_node("Failure", root)

        # Running
        root = Running(name="RunningNode")
        self.test_node("Running", root)

    # ==================== BLACKBOARD OPERATIONS ====================

    def test_blackboard_operations(self):
        """Test all blackboard-related operations."""
        print("\n" + "=" * 80)
        print("BLACKBOARD OPERATIONS")
        print("=" * 80)

        # SetBlackboardVariable - various types
        test_cases = [
            ("SetBB (int)", 42),
            ("SetBB (float)", 3.14159),
            ("SetBB (string)", "hello"),
            ("SetBB (bool)", True),
            ("SetBB (list)", [1, 2, 3]),
        ]

        for name, value in test_cases:
            root = Sequence(
                name="Root",
                memory=True,
                children=[
                    SetBlackboardVariable(
                        name="Setter",
                        variable_name="test_var",
                        variable_value=value,
                        overwrite=True,
                    ),
                    Success(name="Done"),
                ],
            )
            self.test_node(name, root)

        # CheckBlackboardVariableValue - all operators
        operators = [
            ("CheckBB (==)", operator.eq, 100, 100),
            ("CheckBB (!=)", operator.ne, 100, 50),
            ("CheckBB (<)", operator.lt, 50, 100),
            ("CheckBB (<=)", operator.le, 100, 100),
            ("CheckBB (>)", operator.gt, 100, 50),
            ("CheckBB (>=)", operator.ge, 100, 100),
        ]

        for name, op, var_value, check_value in operators:
            root = Sequence(
                name="Root",
                memory=True,
                children=[
                    SetBlackboardVariable(
                        name="SetValue",
                        variable_name="battery",
                        variable_value=var_value,
                        overwrite=True,
                    ),
                    py_trees.behaviours.CheckBlackboardVariableValue(
                        name="CheckValue",
                        check=ComparisonExpression("battery", check_value, op),
                    ),
                    Success(name="Done"),
                ],
            )
            self.test_node(name, root)

    # ==================== COMPLEX COMBINATIONS ====================

    def test_complex_combinations(self):
        """Test complex tree structures."""
        print("\n" + "=" * 80)
        print("COMPLEX COMBINATIONS")
        print("=" * 80)

        # Nested composites (4 levels deep)
        root = Sequence(
            name="L1Sequence",
            memory=True,
            children=[
                Selector(
                    name="L2Selector",
                    memory=False,
                    children=[
                        Sequence(
                            name="L3Sequence",
                            memory=True,
                            children=[
                                Selector(
                                    name="L4Selector",
                                    memory=False,
                                    children=[
                                        Failure(name="Opt1"),
                                        Success(name="Opt2"),
                                    ],
                                ),
                                Success(name="L3Task"),
                            ],
                        ),
                        Failure(name="L2Fallback"),
                    ],
                ),
                Success(name="L1Final"),
            ],
        )
        self.test_node("Nested Composites (4 levels)", root)

        # Decorator chain
        root = Inverter(
            name="Not",
            child=Timeout(
                name="TimeLimit",
                child=Retry(
                    name="RetryOnFail", child=Success(name="Task"), num_failures=3
                ),
                duration=5.0,
            ),
        )
        self.test_node("Decorator Chain (Inverter→Timeout→Retry)", root)

        # Mixed composite with all children types
        root = Sequence(
            name="MixedRoot",
            memory=True,
            children=[
                Success(name="SimpleLeaf"),
                Inverter(name="DecoratorChild", child=Failure(name="InvertedFail")),
                Selector(
                    name="CompositeChild",
                    memory=False,
                    children=[
                        Success(name="A"),
                        Success(name="B"),
                    ],
                ),
                SetBlackboardVariable(
                    name="BBWriter",
                    variable_name="result",
                    variable_value=42,
                    overwrite=True,
                ),
                Success(name="FinalLeaf"),
            ],
        )
        self.test_node("Mixed Node Types", root)

        # Parallel with nested sequences
        root = Parallel(
            name="ParallelRoot",
            policy=ParallelPolicy.SuccessOnAll(synchronise=True),
            children=[
                Sequence(
                    name="Branch1",
                    memory=True,
                    children=[
                        Success(name="B1T1"),
                        Success(name="B1T2"),
                    ],
                ),
                Sequence(
                    name="Branch2",
                    memory=True,
                    children=[
                        Success(name="B2T1"),
                        Success(name="B2T2"),
                    ],
                ),
            ],
        )
        self.test_node("Parallel with Nested Sequences", root)

    # ==================== SUMMARY ====================

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        passed = sum(1 for _, result, _ in self.results if result)
        total = len(self.results)

        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed} ({100 * passed / total:.1f}%)")
        print(f"Failed: {total - passed}")

        if total - passed > 0:
            print("\n" + "=" * 80)
            print("FAILED TESTS")
            print("=" * 80)
            for name, result, message in self.results:
                if not result:
                    print(f"\n❌ {name}")
                    print(f"   {message}")

        print("\n" + "=" * 80)
        print("NODE TYPE COVERAGE ANALYSIS")
        print("=" * 80)

        coverage = {
            "Composites": {
                "Sequence": "✅ Fully tested (memory=True/False)",
                "Selector": "✅ Fully tested (memory=True/False)",
                "Parallel": "✅ Fully tested (SuccessOnAll/SuccessOnOne)",
            },
            "Decorators": {
                "Inverter": "✅ Fully tested",
                "Timeout": "✅ Fully tested (multiple durations)",
                "Retry": "✅ Fully tested (multiple attempts)",
                "OneShot": "⚠️  Registered but not tested",
                "Repeat": "⚠️  In adapter but not in registry",
                "Other decorators": "❌ Not implemented (FailureIsRunning, etc.)",
            },
            "Behaviors": {
                "Success": "✅ Fully tested",
                "Failure": "✅ Fully tested",
                "Running": "✅ Fully tested",
                "SetBlackboardVariable": "✅ Fully tested (all types)",
                "CheckBlackboardVariableValue": "✅ Fully tested (all operators)",
                "Other behaviors": "❌ Not implemented (TickCounter, Wait*, etc.)",
            },
        }

        for category, items in coverage.items():
            print(f"\n{category}:")
            for item, status in items.items():
                print(f"  {item}: {status}")

        print("\n" + "=" * 80)
        if passed == total:
            print("✅ ALL TESTS PASSED - Complete reversibility verified!")
        else:
            print("⚠️  SOME TESTS FAILED - Review failures above")
        print("=" * 80)
        print()


if __name__ == "__main__":
    tester = ComprehensiveCoverageTest()
    tester.run_all_tests()
