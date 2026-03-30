"""Invariant definitions for tree verification."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from talking_trees.verification.trace import ExecutionTrace


@dataclass
class Invariant:
    """A property that must hold across all execution paths."""

    name: str
    description: str
    check: Callable[[ExecutionTrace], bool]


def tree_invariant(name: str, description: str = ""):
    """Decorator for defining tree invariants.

    Usage:
        @tree_invariant("safety_check", "Drone requires confirmation")
        def check(trace):
            if trace.node_reached("dispatch_drone"):
                return trace.node_returned("confirm", "SUCCESS")
            return True
    """
    def decorator(func: Callable[[ExecutionTrace], bool]) -> Invariant:
        return Invariant(name=name, description=description, check=func)
    return decorator
