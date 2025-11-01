"""Shared utilities for py_trees conversion.

This module provides common utilities used across the conversion pipeline,
particularly for operator mappings between py_trees and PyForest formats.
"""

from typing import Callable, Dict, Any
import operator as op


# =============================================================================
# Operator Mappings
# =============================================================================

# Bidirectional operator mappings for comparison operations
OPERATOR_TO_STRING: Dict[Callable, str] = {
    op.gt: ">",
    op.ge: ">=",
    op.lt: "<",
    op.le: "<=",
    op.eq: "==",
    op.ne: "!=",
}

STRING_TO_OPERATOR: Dict[str, Callable] = {
    ">": op.gt,
    ">=": op.ge,
    "<": op.lt,
    "<=": op.le,
    "==": op.eq,
    "!=": op.ne,
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


# =============================================================================
# Future Utilities
# =============================================================================

# This module will grow to include other shared utilities as we refactor:
# - Status conversions (py_trees.Status ↔ string)
# - Common config validation helpers
# - UUID generation utilities
# - etc.
