"""
Round-Trip Validation
=====================

Validates that py_trees → PyForest → py_trees conversion preserves all data.

This is critical for ensuring lossless serialization.
"""

from typing import List, Optional, Any, Dict
import py_trees


class ValidationError:
    """Represents a validation error found during round-trip testing."""

    def __init__(self, path: str, message: str, expected: Any = None, actual: Any = None):
        self.path = path
        self.message = message
        self.expected = expected
        self.actual = actual

    def __str__(self) -> str:
        if self.expected is not None and self.actual is not None:
            return f"[{self.path}] {self.message}\n  Expected: {self.expected}\n  Actual: {self.actual}"
        return f"[{self.path}] {self.message}"


class RoundTripValidator:
    """
    Validates round-trip conversion: py_trees → PyForest → py_trees.

    Ensures that the conversion is lossless and preserves:
    - Tree structure
    - Node types
    - Node names
    - Node configurations
    - SetBlackboardVariable values
    """

    def __init__(self):
        self.errors: List[ValidationError] = []

    def validate(self, original: py_trees.behaviour.Behaviour, round_trip: py_trees.behaviour.Behaviour) -> bool:
        """
        Validate that round-trip conversion preserved the tree.

        Args:
            original: Original py_trees tree
            round_trip: Tree after round-trip conversion

        Returns:
            True if trees are equivalent, False otherwise
        """
        self.errors = []
        self._compare_nodes(original, round_trip, path="root")
        return len(self.errors) == 0

    def assert_equivalent(self, original: py_trees.behaviour.Behaviour, round_trip: py_trees.behaviour.Behaviour):
        """
        Assert that trees are equivalent, raising ValueError if not.

        Args:
            original: Original py_trees tree
            round_trip: Tree after round-trip conversion

        Raises:
            ValueError: If trees are not equivalent
        """
        if not self.validate(original, round_trip):
            error_summary = self.get_error_summary()
            raise ValueError(f"Round-trip validation failed:\n{error_summary}")

    def get_error_summary(self) -> str:
        """Get a formatted summary of all validation errors."""
        if not self.errors:
            return "✓ No validation errors"

        lines = [f"❌ {len(self.errors)} validation error(s):"]
        for i, error in enumerate(self.errors, 1):
            lines.append(f"\n{i}. {error}")

        return "\n".join(lines)

    def _compare_nodes(
        self,
        original: py_trees.behaviour.Behaviour,
        round_trip: py_trees.behaviour.Behaviour,
        path: str
    ):
        """Recursively compare two nodes."""

        # Compare node types
        if type(original).__name__ != type(round_trip).__name__:
            self.errors.append(ValidationError(
                path=path,
                message="Node type mismatch",
                expected=type(original).__name__,
                actual=type(round_trip).__name__
            ))

        # Compare node names
        if original.name != round_trip.name:
            self.errors.append(ValidationError(
                path=path,
                message="Node name mismatch",
                expected=original.name,
                actual=round_trip.name
            ))

        # Compare node-specific config
        self._compare_config(original, round_trip, path)

        # Compare children
        self._compare_children(original, round_trip, path)

    def _compare_config(
        self,
        original: py_trees.behaviour.Behaviour,
        round_trip: py_trees.behaviour.Behaviour,
        path: str
    ):
        """Compare node configuration attributes."""

        # Check memory parameter (for composites)
        if hasattr(original, 'memory') and hasattr(round_trip, 'memory'):
            if original.memory != round_trip.memory:
                self.errors.append(ValidationError(
                    path=path,
                    message="Memory parameter mismatch",
                    expected=original.memory,
                    actual=round_trip.memory
                ))

        # Check blackboard variable name
        if hasattr(original, 'variable_name') and hasattr(round_trip, 'variable_name'):
            if original.variable_name != round_trip.variable_name:
                self.errors.append(ValidationError(
                    path=path,
                    message="Variable name mismatch",
                    expected=original.variable_name,
                    actual=round_trip.variable_name
                ))

        # Check SetBlackboardVariable value (critical!)
        if type(original).__name__ == "SetBlackboardVariable":
            # Try to extract values using multiple approaches
            orig_value = self._extract_value(original)
            rt_value = self._extract_value(round_trip)

            if orig_value != rt_value:
                self.errors.append(ValidationError(
                    path=path,
                    message="SetBlackboardVariable value mismatch (DATA LOSS!)",
                    expected=orig_value,
                    actual=rt_value
                ))

        # Check decorator parameters
        if hasattr(original, 'duration') and hasattr(round_trip, 'duration'):
            if original.duration != round_trip.duration:
                self.errors.append(ValidationError(
                    path=path,
                    message="Duration parameter mismatch",
                    expected=original.duration,
                    actual=round_trip.duration
                ))

        if hasattr(original, 'num_failures') and hasattr(round_trip, 'num_failures'):
            if original.num_failures != round_trip.num_failures:
                self.errors.append(ValidationError(
                    path=path,
                    message="Num_failures parameter mismatch",
                    expected=original.num_failures,
                    actual=round_trip.num_failures
                ))

        if hasattr(original, 'num_success') and hasattr(round_trip, 'num_success'):
            if original.num_success != round_trip.num_success:
                self.errors.append(ValidationError(
                    path=path,
                    message="Num_success parameter mismatch",
                    expected=original.num_success,
                    actual=round_trip.num_success
                ))

        # Check CheckBlackboardVariableValue (ComparisonExpression)
        if type(original).__name__ == "CheckBlackboardVariableValue":
            if hasattr(original, 'check') and hasattr(round_trip, 'check'):
                # Compare variable name
                if original.check.variable != round_trip.check.variable:
                    self.errors.append(ValidationError(
                        path=path,
                        message="Check variable mismatch",
                        expected=original.check.variable,
                        actual=round_trip.check.variable
                    ))

                # Compare comparison value (py_trees swaps operator/value!)
                if original.check.operator != round_trip.check.operator:
                    self.errors.append(ValidationError(
                        path=path,
                        message="Check value mismatch",
                        expected=original.check.operator,
                        actual=round_trip.check.operator
                    ))

                # Compare operator function
                if original.check.value != round_trip.check.value:
                    self.errors.append(ValidationError(
                        path=path,
                        message="Check operator mismatch",
                        expected=original.check.value.__name__ if hasattr(original.check.value, '__name__') else str(original.check.value),
                        actual=round_trip.check.value.__name__ if hasattr(round_trip.check.value, '__name__') else str(round_trip.check.value)
                    ))

    def _extract_value(self, node) -> Any:
        """Extract value from SetBlackboardVariable using multiple approaches."""
        # Try multiple approaches (same as in adapter)
        if hasattr(node, '_value'):
            return node._value
        elif hasattr(node, 'variable_value'):
            return node.variable_value
        elif '_value' in node.__dict__:
            return node.__dict__['_value']
        else:
            return None  # Value not accessible

    def _compare_children(
        self,
        original: py_trees.behaviour.Behaviour,
        round_trip: py_trees.behaviour.Behaviour,
        path: str
    ):
        """Compare children of composite/decorator nodes."""

        # Get children lists
        orig_children = []
        rt_children = []

        if hasattr(original, 'children'):
            orig_children = original.children
        elif hasattr(original, 'child'):
            orig_children = [original.child]

        if hasattr(round_trip, 'children'):
            rt_children = round_trip.children
        elif hasattr(round_trip, 'child'):
            rt_children = [round_trip.child]

        # Compare counts
        if len(orig_children) != len(rt_children):
            self.errors.append(ValidationError(
                path=path,
                message="Different number of children",
                expected=len(orig_children),
                actual=len(rt_children)
            ))
            return  # Can't compare children if counts differ

        # Recursively compare each child
        for i, (orig_child, rt_child) in enumerate(zip(orig_children, rt_children)):
            child_path = f"{path}/{orig_child.name}[{i}]"
            self._compare_nodes(orig_child, rt_child, child_path)
