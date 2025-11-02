"""Example custom behaviors demonstrating how to extend py_trees."""

from typing import Any

from py_trees import behaviour, common


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
