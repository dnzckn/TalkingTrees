"""Shared utilities for py_trees conversion.

This module provides common utilities used across the conversion pipeline,
particularly for operator mappings between py_trees and TalkingTrees formats.
"""

import hashlib
import operator as op
from collections.abc import Callable
from uuid import UUID

import py_trees

# =============================================================================
# Operator Mappings
# =============================================================================

# Bidirectional operator mappings for comparison operations
OPERATOR_TO_STRING: dict[Callable, str] = {
    op.gt: ">",
    op.ge: ">=",
    op.lt: "<",
    op.le: "<=",
    op.eq: "==",
    op.ne: "!=",
}

STRING_TO_OPERATOR: dict[str, Callable] = {
    ">": op.gt,
    ">=": op.ge,
    "<": op.lt,
    "<=": op.le,
    "==": op.eq,
    "!=": op.ne,
}

# Logical operator mappings for CheckBlackboardVariableValues
LOGICAL_OPERATOR_TO_STRING: dict[Callable, str] = {
    op.and_: "and",
    op.or_: "or",
    op.xor: "xor",
}

STRING_TO_LOGICAL_OPERATOR: dict[str, Callable] = {
    "and": op.and_,
    "or": op.or_,
    "xor": op.xor,
}


def operator_to_string(op_func: Callable) -> str:
    """Convert operator.* function to string representation.

    This is used during serialization (py_trees → JSON) to convert
    Python operator functions to their string equivalents.

    Args:
        op_func: Operator function from operator module (e.g., operator.gt)

    Returns:
        String representation (e.g., ">"), defaults to "==" if unknown

    Example:
        >>> import operator
        >>> operator_to_string(operator.gt)
        ">"
        >>> operator_to_string(operator.le)
        "<="
        >>> operator_to_string(operator.eq)
        "=="
    """
    return OPERATOR_TO_STRING.get(op_func, "==")


def string_to_operator(op_str: str) -> Callable:
    """Convert string to operator.* function.

    This is used during deserialization (JSON → py_trees) to convert
    string operators back to Python operator functions.

    Args:
        op_str: String representation (e.g., ">", "<=", "==")

    Returns:
        Operator function from operator module, defaults to operator.eq if unknown

    Example:
        >>> op_func = string_to_operator(">")
        >>> op_func(5, 3)
        True
        >>> op_func = string_to_operator("<=")
        >>> op_func(3, 5)
        True
    """
    return STRING_TO_OPERATOR.get(op_str, op.eq)


def logical_operator_to_string(op_func: Callable) -> str:
    """Convert logical operator function to string representation.

    Args:
        op_func: Logical operator function (e.g., operator.and_, operator.or_)

    Returns:
        String representation (e.g., "and", "or"), defaults to "and" if unknown

    Example:
        >>> import operator
        >>> logical_operator_to_string(operator.and_)
        "and"
        >>> logical_operator_to_string(operator.or_)
        "or"
    """
    return LOGICAL_OPERATOR_TO_STRING.get(op_func, "and")


def string_to_logical_operator(op_str: str) -> Callable:
    """Convert string to logical operator function.

    Args:
        op_str: String representation (e.g., "and", "or", "xor")

    Returns:
        Logical operator function, defaults to operator.and_ if unknown

    Example:
        >>> op_func = string_to_logical_operator("and")
        >>> op_func(True, False)
        False
        >>> op_func = string_to_logical_operator("or")
        >>> op_func(True, False)
        True
    """
    return STRING_TO_LOGICAL_OPERATOR.get(op_str, op.and_)


# =============================================================================
# Parallel Policy Factory
# =============================================================================


class ParallelPolicyFactory:
    """Factory for creating py_trees ParallelPolicy instances.

    Consolidates the parallel policy creation logic that was duplicated across
    serializer.py, builders.py, and registry.py.
    """

    @staticmethod
    def create(policy_name: str, synchronise: bool = True):
        """Create parallel policy from config.

        Args:
            policy_name: Name of the policy ("SuccessOnAll", "SuccessOnOne", "SuccessOnSelected")
            synchronise: Whether to skip successful children on subsequent ticks

        Returns:
            ParallelPolicy instance

        Raises:
            ValueError: If policy_name is unknown

        Example:
            >>> policy = ParallelPolicyFactory.create("SuccessOnAll", synchronise=True)
            >>> parallel = py_trees.composites.Parallel(name="MyParallel", policy=policy)
        """
        if policy_name == "SuccessOnAll":
            return py_trees.common.ParallelPolicy.SuccessOnAll(synchronise=synchronise)
        elif policy_name == "SuccessOnOne":
            return py_trees.common.ParallelPolicy.SuccessOnOne()
        elif policy_name == "SuccessOnSelected":
            # SuccessOnSelected requires a list of specific children at instantiation time.
            # This would require architectural changes to pass child selection to the factory.
            # For now, this policy is not supported through the config system.
            raise NotImplementedError(
                "SuccessOnSelected policy is not yet supported. "
                "It requires specifying which children to wait for at policy creation time, "
                "which is not currently supported by TalkingTrees's configuration system. "
                "Use SuccessOnAll or SuccessOnOne instead."
            )
        else:
            raise ValueError(f"Unknown parallel policy: {policy_name}")


# =============================================================================
# Comparison Expression Utility
# =============================================================================


class ComparisonExpressionUtil:
    """Centralized handling of py_trees ComparisonExpression.

    py_trees ComparisonExpression signature is:
    - ComparisonExpression(variable, value, operator)

    Where:
    - variable: string name of blackboard variable
    - value: the comparison value (RHS)
    - operator: the callable comparison function (e.g. operator.lt)

    This utility provides a clear abstraction for serialization/deserialization.
    """

    @staticmethod
    def extract(check) -> dict:
        """Extract config from py_trees ComparisonExpression.

        Args:
            check: py_trees ComparisonExpression instance

        Returns:
            Dict with 'variable', 'operator' (string), 'value'

        Example:
            >>> check = ComparisonExpression("battery", 20, operator.lt)
            >>> config = ComparisonExpressionUtil.extract(check)
            >>> config
            {'variable': 'battery', 'operator': '<', 'value': 20}
        """
        return {
            "variable": check.variable,
            "operator": operator_to_string(check.operator),
            "value": check.value,
        }

    @staticmethod
    def create(variable: str, operator_str: str, value):
        """Create py_trees ComparisonExpression from config.

        Args:
            variable: Blackboard variable name
            operator_str: Comparison operator as string ("==", "<", ">", etc.)
            value: Value to compare against

        Returns:
            py_trees ComparisonExpression instance

        Example:
            >>> check = ComparisonExpressionUtil.create("battery", "<", 20)
            >>> node = py_trees.behaviours.CheckBlackboardVariableValue(
            ...     name="Low Battery", check=check
            ... )
        """
        operator_func = string_to_operator(operator_str)
        # NOTE: ComparisonExpression signature is (variable, value, operator)
        # NOT (variable, operator, value)!
        return py_trees.common.ComparisonExpression(variable, value, operator_func)


# =============================================================================
# UUID Generation
# =============================================================================


def generate_deterministic_uuid(
    node, parent_path: str = "", config_keys: list | None = None
):
    """Generate deterministic UUID based on node structure.

    Uses SHA-256 hash of node's identifying characteristics to ensure
    the same node always gets the same UUID across conversions.

    Args:
        node: py_trees node
        parent_path: Path from root (e.g., "Root/Selector/Sequence")
        config_keys: Optional list of config keys to include in hash

    Returns:
        Deterministic UUID

    Example:
        >>> node = py_trees.behaviours.Success("Step1")
        >>> uuid1 = generate_deterministic_uuid(node, "Root/Sequence")
        >>> uuid2 = generate_deterministic_uuid(node, "Root/Sequence")
        >>> assert uuid1 == uuid2  # Same UUID!
    """
    # Build path including this node
    path = f"{parent_path}/{node.name}" if parent_path else node.name

    # Collect identifying characteristics
    parts = [
        type(node).__name__,  # Node class
        node.name,  # Node name
        path,  # Full path in tree
    ]

    # Add memory parameter if present (important for composites)
    if hasattr(node, "memory"):
        parts.append(f"memory={node.memory}")

    # Add key config values for blackboard nodes
    if hasattr(node, "variable_name"):
        parts.append(f"var={node.variable_name}")

    # Add decorator-specific config
    if hasattr(node, "duration"):
        parts.append(f"duration={node.duration}")
    if hasattr(node, "num_failures"):
        parts.append(f"num_failures={node.num_failures}")
    if hasattr(node, "num_success"):
        parts.append(f"num_success={node.num_success}")

    # Add custom config keys if specified
    if config_keys:
        for key in config_keys:
            if hasattr(node, key):
                parts.append(f"{key}={getattr(node, key)}")

    # Create deterministic string
    content = "|".join(str(p) for p in parts)

    # Hash to bytes
    hash_bytes = hashlib.sha256(content.encode("utf-8")).digest()

    # Use first 16 bytes as UUID
    return UUID(bytes=hash_bytes[:16])
