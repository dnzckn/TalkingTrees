"""Node builders for constructing py_trees from config.

This module provides a registry-based system for building py_trees nodes
from TalkingTrees TreeNodeDefinition during deserialization. Each node type
has a dedicated builder that knows how to construct it with proper config.
"""

from abc import ABC, abstractmethod
from typing import Any

import py_trees
from py_trees import behaviour

from talking_trees.core.constants import ConfigKeys, DefaultValues
from talking_trees.core.utils import string_to_operator

# =============================================================================
# Base Builder
# =============================================================================


class NodeBuilder(ABC):
    """Base class for building py_trees nodes from config."""

    @abstractmethod
    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        """Build a py_trees node.

        Args:
            name: Node name
            config: Configuration dict from TreeNodeDefinition
            **kwargs: Additional context (e.g., 'child' for decorators)

        Returns:
            py_trees node instance
        """
        pass


# =============================================================================
# Decorator Builders
# =============================================================================


class DecoratorBuilder(NodeBuilder):
    """Base class for decorator builders.

    Decorators require a child node which should be passed via kwargs.
    """

    def get_child(self, kwargs: dict[str, Any]) -> behaviour.Behaviour:
        """Extract and validate child from kwargs.

        Args:
            kwargs: Keyword arguments

        Returns:
            Child behaviour

        Raises:
            ValueError: If child not provided
        """
        child = kwargs.get("child")
        if not child:
            raise ValueError("Decorator requires 'child' parameter")
        return child


class InverterBuilder(DecoratorBuilder):
    """Build Inverter decorator."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        child = self.get_child(kwargs)
        return py_trees.decorators.Inverter(name=name, child=child)


class SuccessIsFailureBuilder(DecoratorBuilder):
    """Build SuccessIsFailure decorator."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        child = self.get_child(kwargs)
        return py_trees.decorators.SuccessIsFailure(name=name, child=child)


class FailureIsSuccessBuilder(DecoratorBuilder):
    """Build FailureIsSuccess decorator."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        child = self.get_child(kwargs)
        return py_trees.decorators.FailureIsSuccess(name=name, child=child)


class FailureIsRunningBuilder(DecoratorBuilder):
    """Build FailureIsRunning decorator."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        child = self.get_child(kwargs)
        return py_trees.decorators.FailureIsRunning(name=name, child=child)


class RunningIsFailureBuilder(DecoratorBuilder):
    """Build RunningIsFailure decorator."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        child = self.get_child(kwargs)
        return py_trees.decorators.RunningIsFailure(name=name, child=child)


class RunningIsSuccessBuilder(DecoratorBuilder):
    """Build RunningIsSuccess decorator."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        child = self.get_child(kwargs)
        return py_trees.decorators.RunningIsSuccess(name=name, child=child)


class SuccessIsRunningBuilder(DecoratorBuilder):
    """Build SuccessIsRunning decorator."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        child = self.get_child(kwargs)
        return py_trees.decorators.SuccessIsRunning(name=name, child=child)


class RepeatBuilder(DecoratorBuilder):
    """Build Repeat decorator."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        child = self.get_child(kwargs)
        num_success = config.get(ConfigKeys.NUM_SUCCESS, 1)
        return py_trees.decorators.Repeat(
            name=name, child=child, num_success=num_success
        )


class RetryBuilder(DecoratorBuilder):
    """Build Retry decorator."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        child = self.get_child(kwargs)
        num_failures = config.get(ConfigKeys.NUM_FAILURES, 3)
        return py_trees.decorators.Retry(
            name=name, child=child, num_failures=num_failures
        )


class OneShotBuilder(DecoratorBuilder):
    """Build OneShot decorator."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        child = self.get_child(kwargs)
        policy_str = config.get(ConfigKeys.POLICY, "ON_COMPLETION")
        policy = getattr(
            py_trees.common.OneShotPolicy,
            policy_str,
            py_trees.common.OneShotPolicy.ON_COMPLETION,
        )
        return py_trees.decorators.OneShot(name=name, child=child, policy=policy)


class TimeoutBuilder(DecoratorBuilder):
    """Build Timeout decorator."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        child = self.get_child(kwargs)
        duration = config.get(ConfigKeys.DURATION, 5.0)
        return py_trees.decorators.Timeout(name=name, child=child, duration=duration)


class EternalGuardBuilder(DecoratorBuilder):
    """Build EternalGuard decorator."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        from talking_trees.core.utils import ComparisonExpressionUtil

        child = self.get_child(kwargs)
        variable = config.get(ConfigKeys.VARIABLE, "condition")
        value = config.get(ConfigKeys.VALUE, True)
        op_str = config.get(ConfigKeys.OPERATOR, "==")

        check = ComparisonExpressionUtil.create(variable, op_str, value)

        return py_trees.decorators.EternalGuard(
            name=name, child=child, blackboard_keys=[variable], condition=check
        )


class ConditionBuilder(DecoratorBuilder):
    """Build Condition decorator."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        child = self.get_child(kwargs)
        status_str = config.get("status", "SUCCESS")

        # Convert string to Status enum
        status_map = {
            "SUCCESS": py_trees.common.Status.SUCCESS,
            "FAILURE": py_trees.common.Status.FAILURE,
            "RUNNING": py_trees.common.Status.RUNNING,
        }
        status = status_map.get(status_str, py_trees.common.Status.SUCCESS)

        return py_trees.decorators.Condition(name=name, child=child, status=status)


class CountBuilder(DecoratorBuilder):
    """Build Count decorator."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        child = self.get_child(kwargs)
        return py_trees.decorators.Count(name=name, child=child)


class StatusToBlackboardBuilder(DecoratorBuilder):
    """Build StatusToBlackboard decorator."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        child = self.get_child(kwargs)
        variable = config.get(ConfigKeys.VARIABLE, "status")
        return py_trees.decorators.StatusToBlackboard(
            name=name, child=child, variable_name=variable
        )


class ForEachBuilder(DecoratorBuilder):
    """Build ForEach decorator."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        child = self.get_child(kwargs)
        source_key = config.get("source_key", "items")
        target_key = config.get("target_key", "current_item")
        return py_trees.decorators.ForEach(
            name=name, child=child, source_key=source_key, target_key=target_key
        )


class PassThroughBuilder(DecoratorBuilder):
    """Build PassThrough decorator."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        child = self.get_child(kwargs)
        return py_trees.decorators.PassThrough(name=name, child=child)


# =============================================================================
# Composite Builders
# =============================================================================


class SequenceBuilder(NodeBuilder):
    """Build Sequence composite."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        memory = config.get(ConfigKeys.MEMORY, DefaultValues.MEMORY)
        return py_trees.composites.Sequence(name=name, memory=memory)


class SelectorBuilder(NodeBuilder):
    """Build Selector composite."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        memory = config.get(ConfigKeys.MEMORY, DefaultValues.MEMORY)
        return py_trees.composites.Selector(name=name, memory=memory)


class ParallelBuilder(NodeBuilder):
    """Build Parallel composite."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        from talking_trees.core.utils import ParallelPolicyFactory

        policy_name = config.get(ConfigKeys.POLICY, DefaultValues.POLICY)
        synchronise = config.get(ConfigKeys.SYNCHRONISE, DefaultValues.SYNCHRONISE)
        policy = ParallelPolicyFactory.create(policy_name, synchronise)

        return py_trees.composites.Parallel(name=name, policy=policy)


# =============================================================================
# Behavior Builders (Simple)
# =============================================================================


class SimpleBehaviorBuilder(NodeBuilder):
    """Builder for simple behaviors with just a name parameter.

    Used for: Success, Failure, Running, Dummy, etc.
    """

    def __init__(self, behavior_class):
        self.behavior_class = behavior_class

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        return self.behavior_class(name=name)


class TickCounterBuilder(NodeBuilder):
    """Builder for TickCounter."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        duration = config.get("duration", 1)
        completion_status_str = config.get("completion_status", "SUCCESS")

        # Convert string to Status enum
        status_map = {
            "SUCCESS": py_trees.common.Status.SUCCESS,
            "FAILURE": py_trees.common.Status.FAILURE,
            "RUNNING": py_trees.common.Status.RUNNING,
        }
        completion_status = status_map.get(completion_status_str, py_trees.common.Status.SUCCESS)

        return py_trees.behaviours.TickCounter(
            name=name, duration=duration, completion_status=completion_status
        )


class SetBlackboardVariableBuilder(NodeBuilder):
    """Builder for SetBlackboardVariable (maps to py_trees SetBlackboardVariable)."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        variable = config.get(ConfigKeys.VARIABLE, "output")
        value = config.get(ConfigKeys.VALUE, None)
        overwrite = config.get(ConfigKeys.OVERWRITE, True)

        return py_trees.behaviours.SetBlackboardVariable(
            name=name,
            variable_name=variable,
            variable_value=value,
            overwrite=overwrite,
        )


class CheckBlackboardVariableExistsBuilder(NodeBuilder):
    """Builder for CheckBlackboardVariableExists."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        variable = config.get(ConfigKeys.VARIABLE, "var")
        return py_trees.behaviours.CheckBlackboardVariableExists(
            name=name, variable_name=variable
        )


class CheckBlackboardVariableValueBuilder(NodeBuilder):
    """Builder for CheckBlackboardVariableValue (singular)."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        from talking_trees.core.utils import ComparisonExpressionUtil

        variable = config.get(ConfigKeys.VARIABLE, "value")
        value = config.get(ConfigKeys.VALUE, 0)
        op_str = config.get("operator", "==")

        check = ComparisonExpressionUtil.create(variable, op_str, value)

        return py_trees.behaviours.CheckBlackboardVariableValue(name=name, check=check)


class UnsetBlackboardVariableBuilder(NodeBuilder):
    """Builder for UnsetBlackboardVariable."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        variable = config.get(ConfigKeys.VARIABLE, "var")
        return py_trees.behaviours.UnsetBlackboardVariable(name=name, key=variable)


class WaitForBlackboardVariableBuilder(NodeBuilder):
    """Builder for WaitForBlackboardVariable."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        variable = config.get(ConfigKeys.VARIABLE, "var")
        return py_trees.behaviours.WaitForBlackboardVariable(
            name=name, variable_name=variable
        )


class CheckBlackboardVariableValuesBuilder(NodeBuilder):
    """Builder for CheckBlackboardVariableValues (plural)."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:
        from talking_trees.core.utils import (
            ComparisonExpressionUtil,
            string_to_logical_operator,
        )

        # Build list of ComparisonExpression objects from checks config
        checks_config = config.get("checks", [])
        checks = []
        for check_dict in checks_config:
            variable = check_dict.get("variable", "var")
            op_str = check_dict.get("operator", "==")
            value = check_dict.get("value", True)
            check = ComparisonExpressionUtil.create(variable, op_str, value)
            checks.append(check)

        # Convert operator string to function
        operator_str = config.get("operator", "and")
        operator_func = string_to_logical_operator(operator_str)

        # Optional namespace
        namespace = config.get("namespace", None)

        return py_trees.behaviours.CheckBlackboardVariableValues(
            name=name, checks=checks, operator=operator_func, namespace=namespace
        )


class CompareBlackboardVariablesBuilder(NodeBuilder):
    """Builder for CompareBlackboardVariables."""

    def build(self, name: str, config: dict[str, Any], **kwargs) -> behaviour.Behaviour:

        var1_key = config.get("var1_key", "var1")
        var2_key = config.get("var2_key", "var2")
        op_str = config.get("operator", "==")

        operator_func = string_to_operator(op_str)

        return py_trees.behaviours.CompareBlackboardVariables(
            name=name, var1_key=var1_key, var2_key=var2_key, operator=operator_func
        )


# =============================================================================
# Builder Registry
# =============================================================================

# Decorator builders
DECORATOR_BUILDERS: dict[str, NodeBuilder] = {
    "Inverter": InverterBuilder(),
    "SuccessIsFailure": SuccessIsFailureBuilder(),
    "FailureIsSuccess": FailureIsSuccessBuilder(),
    "FailureIsRunning": FailureIsRunningBuilder(),
    "RunningIsFailure": RunningIsFailureBuilder(),
    "RunningIsSuccess": RunningIsSuccessBuilder(),
    "SuccessIsRunning": SuccessIsRunningBuilder(),
    "Repeat": RepeatBuilder(),
    "Retry": RetryBuilder(),
    "OneShot": OneShotBuilder(),
    "Timeout": TimeoutBuilder(),
    "EternalGuard": EternalGuardBuilder(),
    "Condition": ConditionBuilder(),
    "Count": CountBuilder(),
    "StatusToBlackboard": StatusToBlackboardBuilder(),
    "ForEach": ForEachBuilder(),
    "PassThrough": PassThroughBuilder(),
}

# Composite builders
COMPOSITE_BUILDERS: dict[str, NodeBuilder] = {
    "Sequence": SequenceBuilder(),
    "Selector": SelectorBuilder(),
    "Parallel": ParallelBuilder(),
}

# Simple behavior builders
SIMPLE_BEHAVIOR_BUILDERS: dict[str, NodeBuilder] = {
    "Success": SimpleBehaviorBuilder(py_trees.behaviours.Success),
    "Failure": SimpleBehaviorBuilder(py_trees.behaviours.Failure),
    "Running": SimpleBehaviorBuilder(py_trees.behaviours.Running),
    "Dummy": SimpleBehaviorBuilder(py_trees.behaviours.Dummy),
}

# Special behavior builders (with complex configuration)
SPECIAL_BEHAVIOR_BUILDERS: dict[str, NodeBuilder] = {
    "SetBlackboardVariable": SetBlackboardVariableBuilder(),
    "CheckBlackboardVariableExists": CheckBlackboardVariableExistsBuilder(),
    "CheckBlackboardVariableValue": CheckBlackboardVariableValueBuilder(),
    "CheckBlackboardVariableValues": CheckBlackboardVariableValuesBuilder(),
    "CompareBlackboardVariables": CompareBlackboardVariablesBuilder(),
    "UnsetBlackboardVariable": UnsetBlackboardVariableBuilder(),
    "WaitForBlackboardVariable": WaitForBlackboardVariableBuilder(),
    "TickCounter": TickCounterBuilder(),
}

# Combined registry
BUILDER_REGISTRY: dict[str, NodeBuilder] = {
    **DECORATOR_BUILDERS,
    **COMPOSITE_BUILDERS,
    **SIMPLE_BEHAVIOR_BUILDERS,
    **SPECIAL_BEHAVIOR_BUILDERS,
}


def get_builder(node_type: str) -> NodeBuilder | None:
    """Get the builder for a node type.

    Args:
        node_type: Node type (e.g., "Timeout", "Sequence")

    Returns:
        NodeBuilder instance or None if not registered

    Example:
        >>> builder = get_builder("Timeout")
        >>> if builder:
        >>>     node = builder.build("MyTimeout", {"duration": 10.0}, child=child_node)
    """
    return BUILDER_REGISTRY.get(node_type)


def build_decorator(
    node_type: str, name: str, config: dict[str, Any], child: behaviour.Behaviour
) -> behaviour.Behaviour:
    """Build a decorator node using the registry.

    Args:
        node_type: Decorator type
        name: Node name
        config: Configuration dict
        child: Child behaviour

    Returns:
        Decorator instance

    Raises:
        ValueError: If node_type not registered or not a decorator

    Example:
        >>> timeout = build_decorator("Timeout", "MyTimeout", {"duration": 5.0}, child_node)
    """
    builder = get_builder(node_type)

    if not builder:
        raise ValueError(f"Unknown decorator type: {node_type}")

    if node_type not in DECORATOR_BUILDERS:
        raise ValueError(f"{node_type} is not a decorator")

    return builder.build(name, config, child=child)


def build_composite(
    node_type: str, name: str, config: dict[str, Any]
) -> behaviour.Behaviour:
    """Build a composite node using the registry.

    Args:
        node_type: Composite type
        name: Node name
        config: Configuration dict

    Returns:
        Composite instance

    Raises:
        ValueError: If node_type not registered or not a composite

    Example:
        >>> seq = build_composite("Sequence", "MySeq", {"memory": True})
    """
    builder = get_builder(node_type)

    if not builder:
        raise ValueError(f"Unknown composite type: {node_type}")

    if node_type not in COMPOSITE_BUILDERS:
        raise ValueError(f"{node_type} is not a composite")

    return builder.build(name, config)


def build_behavior(
    node_type: str, name: str, config: dict[str, Any]
) -> behaviour.Behaviour:
    """Build a behavior node using the registry.

    Args:
        node_type: Behavior type
        name: Node name
        config: Configuration dict

    Returns:
        Behavior instance

    Raises:
        ValueError: If node_type not registered

    Example:
        >>> success = build_behavior("Success", "Task1", {})
    """
    builder = get_builder(node_type)

    if not builder:
        # Fallback: use registry factory for custom behaviors
        # This handles behaviors not in the builder registry
        # (e.g., TickCounter, CheckBattery, Log, custom user behaviors)
        from talking_trees.core.registry import get_registry

        registry = get_registry()
        return registry.create_node(node_type, name, config)

    return builder.build(name, config)
