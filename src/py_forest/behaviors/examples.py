"""Example custom behaviors demonstrating how to extend py_trees."""

import time
from typing import Any

from py_trees import behaviour, blackboard, common


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
        self.blackboard.register_key(
            key="/battery/level", access=common.Access.READ
        )

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
