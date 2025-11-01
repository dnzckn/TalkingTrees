"""Example custom behaviors demonstrating how to extend py_trees."""

import operator
import time
from collections.abc import Callable
from typing import Any

from py_trees import behaviour, common, decorators


class CheckBattery(behaviour.Behaviour):
    """Check if battery level is above a threshold.

    This is a simple example of a custom behavior that reads from
    the blackboard and returns SUCCESS/FAILURE based on a condition.

    Args:
        name: Behaviour name
        threshold: Minimum acceptable battery level (0.0-1.0)
    """

    def __init__(self, name: str, threshold: float = 0.2):
        super().__init__(name=name)
        self.threshold = threshold
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="/battery/level", access=common.Access.READ)

    def update(self) -> common.Status:
        """Check battery level against threshold.

        Returns:
            SUCCESS if battery above threshold, FAILURE otherwise
        """
        try:
            battery_level = self.blackboard.get("/battery/level")
            self.logger.info(
                f"{self.name}: battery at {battery_level:.1%} (threshold: {self.threshold:.1%})"
            )

            if battery_level >= self.threshold:
                self.feedback_message = f"battery OK ({battery_level:.1%})"
                return common.Status.SUCCESS
            else:
                self.feedback_message = f"battery low ({battery_level:.1%})"
                return common.Status.FAILURE

        except KeyError:
            self.feedback_message = "battery level not available"
            return common.Status.FAILURE


class Log(behaviour.Behaviour):
    """Log a message and return SUCCESS.

    Useful for debugging and adding trace points in trees.

    Args:
        name: Behaviour name
        message: Message to log
    """

    def __init__(self, name: str, message: str = ""):
        super().__init__(name=name)
        self.message = message

    def update(self) -> common.Status:
        """Log message and return SUCCESS.

        Returns:
            Always SUCCESS
        """
        msg = self.message or f"{self.name} executed"
        self.logger.info(msg)
        self.feedback_message = msg
        return common.Status.SUCCESS


class Wait(behaviour.Behaviour):
    """Wait for a specified duration (simulates async operation).

    Returns RUNNING until duration has elapsed, then SUCCESS.

    Args:
        name: Behaviour name
        duration: Duration to wait in seconds
    """

    def __init__(self, name: str, duration: float = 1.0):
        super().__init__(name=name)
        self.duration = duration
        self.start_time: float = 0.0

    def initialise(self) -> None:
        """Record start time."""
        self.start_time = time.time()
        self.feedback_message = f"waiting {self.duration}s"

    def update(self) -> common.Status:
        """Check if wait duration has elapsed.

        Returns:
            RUNNING until duration elapsed, then SUCCESS
        """
        elapsed = time.time() - self.start_time

        if elapsed >= self.duration:
            self.feedback_message = f"wait complete ({elapsed:.1f}s)"
            return common.Status.SUCCESS
        else:
            remaining = self.duration - elapsed
            self.feedback_message = f"waiting ({remaining:.1f}s remaining)"
            return common.Status.RUNNING

    def terminate(self, new_status: common.Status) -> None:
        """Log termination.

        Args:
            new_status: Status being transitioned to
        """
        self.logger.debug(f"{self.name}: terminate with {new_status}")


class SetBlackboardVariable(behaviour.Behaviour):
    """Set a blackboard variable to a specific value.

    This is a REAL action that affects state - external systems can read this!
    Use this for automation where behavior tree controls state that other systems read.

    Args:
        name: Behaviour name
        variable: Blackboard variable name to set
        value: Value to set (can be any JSON-serializable type)
    """

    def __init__(self, name: str, variable: str = "result", value: Any = None):
        super().__init__(name=name)
        self.variable = variable
        self.value = value
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key=variable, access=common.Access.WRITE)

    def update(self) -> common.Status:
        """Set the blackboard variable and return SUCCESS.

        Returns:
            Always SUCCESS
        """
        self.blackboard.set(self.variable, self.value, overwrite=True)
        self.feedback_message = f"Set {self.variable} = {self.value}"
        self.logger.info(f"{self.name}: {self.feedback_message}")
        return common.Status.SUCCESS


class GetBlackboardVariable(behaviour.Behaviour):
    """Get a blackboard variable value and expose it in feedback.

    Useful for debugging or conditional logic based on values.

    Args:
        name: Behaviour name
        variable: Blackboard variable name to read
    """

    def __init__(self, name: str, variable: str = "result"):
        super().__init__(name=name)
        self.variable = variable
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key=variable, access=common.Access.READ)

    def update(self) -> common.Status:
        """Read blackboard variable.

        Returns:
            SUCCESS if variable exists, FAILURE if not found
        """
        try:
            value = self.blackboard.get(self.variable)
            self.feedback_message = f"{self.variable} = {value}"
            self.logger.info(f"{self.name}: {self.feedback_message}")
            return common.Status.SUCCESS
        except KeyError:
            self.feedback_message = f"{self.variable} not found"
            self.logger.warning(f"{self.name}: {self.feedback_message}")
            return common.Status.FAILURE


class CheckBlackboardCondition(decorators.Decorator):
    """Conditional decorator that checks a blackboard value and only runs child if condition passes.

    This answers the pattern: "check BB variable < 5 -> if true, run child".

    Supports comparison operators: <, <=, ==, !=, >=, >

    Args:
        name: Decorator name
        child: Child behaviour to conditionally execute
        variable: Blackboard variable name to check
        operator_str: Comparison operator as string ("<", "<=", "==", "!=", ">=", ">")
        value: Value to compare against
    """

    OPERATORS: dict[str, Callable] = {
        "<": operator.lt,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne,
        ">=": operator.ge,
        ">": operator.gt,
    }

    def __init__(
        self,
        name: str,
        child: behaviour.Behaviour,
        variable: str,
        operator_str: str = "==",
        value: Any = True,
    ):
        super().__init__(name=name, child=child)
        self.variable = variable
        self.operator_str = operator_str
        self.value = value

        if operator_str not in self.OPERATORS:
            raise ValueError(
                f"Invalid operator '{operator_str}'. Must be one of: {list(self.OPERATORS.keys())}"
            )

        self.op_func = self.OPERATORS[operator_str]
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key=variable, access=common.Access.READ)

    def update(self) -> common.Status:
        """Check condition and return child status if passed, FAILURE otherwise.

        Returns:
            Child status if condition passes, FAILURE if condition fails
        """
        try:
            bb_value = self.blackboard.get(self.variable)
            condition_passed = self.op_func(bb_value, self.value)

            if condition_passed:
                self.feedback_message = (
                    f"{self.variable}={bb_value} {self.operator_str} {self.value} ✓"
                )
                return self.decorated.status
            else:
                self.feedback_message = (
                    f"{self.variable}={bb_value} {self.operator_str} {self.value} ✗"
                )
                # Stop the child since condition failed
                if self.decorated.status == common.Status.RUNNING:
                    self.decorated.stop(common.Status.INVALID)
                return common.Status.FAILURE

        except KeyError:
            self.feedback_message = f"{self.variable} not found in blackboard"
            return common.Status.FAILURE
