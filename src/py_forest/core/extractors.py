"""Config extractors for py_trees nodes.

This module provides a registry-based system for extracting configuration
from py_trees nodes during serialization. Each node type has a dedicated
extractor that knows how to safely extract its configuration.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

from py_forest.core.utils import operator_to_string

# Type checking imports to avoid circular dependencies
if TYPE_CHECKING:
    pass


# =============================================================================
# Base Extractor
# =============================================================================


class ConfigExtractor(ABC):
    """Base class for extracting config from py_trees nodes."""

    @abstractmethod
    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        """Extract configuration from a py_trees node.

        Args:
            node: py_trees node instance
            context: Optional conversion context for warnings

        Returns:
            Configuration dictionary
        """
        pass


# =============================================================================
# Helper Extractors
# =============================================================================


class ComparisonBasedExtractor(ConfigExtractor):
    """Base extractor for nodes using ComparisonExpression.

    Many py_trees nodes use ComparisonExpression for conditional checks.
    This base class provides common extraction logic.
    """

    def extract_comparison(self, check) -> dict[str, Any]:
        """Extract comparison data and convert to config format."""
        # Import here to avoid circular dependency
        from py_forest.adapters.py_trees_adapter import ComparisonExpressionExtractor

        extracted = ComparisonExpressionExtractor.extract(check)
        return {
            "variable": extracted["variable"],
            "value": extracted["comparison_value"],
            "operator": operator_to_string(extracted["operator_function"]),
        }


# =============================================================================
# Blackboard Extractors
# =============================================================================


class CheckBlackboardVariableValueExtractor(ComparisonBasedExtractor):
    """Extract config from CheckBlackboardVariableValue nodes."""

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        if hasattr(node, "check"):
            return self.extract_comparison(node.check)
        return {}


class CheckBlackboardVariableExistsExtractor(ConfigExtractor):
    """Extract config from CheckBlackboardVariableExists nodes."""

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        if hasattr(node, "variable_name"):
            return {"variable": node.variable_name}
        return {}


class SetBlackboardVariableExtractor(ConfigExtractor):
    """Extract config from SetBlackboardVariable nodes.

    This is the most complex extractor because py_trees stores the value
    in different ways across versions and it's not always accessible.
    """

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        config = {}

        # Extract variable name
        if hasattr(node, "variable_name"):
            config["variable"] = node.variable_name
        elif hasattr(node, "key"):
            config["variable"] = node.key

        # Extract value (complex logic - try multiple approaches)
        value_extracted = False

        # Approach 1: Try variable_value_generator (py_trees 2.3+)
        if hasattr(node, "variable_value_generator") and callable(
            node.variable_value_generator
        ):
            try:
                config["value"] = node.variable_value_generator()
                value_extracted = True
            except Exception:
                # Fallback: Try extracting from lambda closure
                try:
                    closure = node.variable_value_generator.__closure__
                    if closure and len(closure) > 0:
                        config["value"] = closure[0].cell_contents
                        value_extracted = True
                except Exception:
                    pass

        # Approach 2: Try _value attribute (private, older versions)
        if not value_extracted and hasattr(node, "_value"):
            config["value"] = node._value
            value_extracted = True

        # Approach 3: Try variable_value (older API)
        elif not value_extracted and hasattr(node, "variable_value"):
            config["value"] = node.variable_value
            value_extracted = True

        # Approach 4: Try __dict__ access
        elif not value_extracted and "_value" in node.__dict__:
            config["value"] = node.__dict__["_value"]
            value_extracted = True

        if not value_extracted:
            # WARNING: Could not extract value
            warning_msg = (
                "SetBlackboardVariable value not accessible. "
                "Round-trip conversion will lose this value."
            )
            config["_data_loss_warning"] = warning_msg
            if context:
                context.warn(warning_msg, node_name=node.name)

        # Extract overwrite flag
        if hasattr(node, "overwrite"):
            config["overwrite"] = node.overwrite

        return config


class UnsetBlackboardVariableExtractor(ConfigExtractor):
    """Extract config from UnsetBlackboardVariable nodes."""

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        if hasattr(node, "variable_name"):
            return {"variable": node.variable_name}
        elif hasattr(node, "key"):
            return {"variable": node.key}
        return {}


class WaitForBlackboardVariableExtractor(ConfigExtractor):
    """Extract config from WaitForBlackboardVariable nodes."""

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        if hasattr(node, "variable_name"):
            return {"variable": node.variable_name}
        return {}


class WaitForBlackboardVariableValueExtractor(ComparisonBasedExtractor):
    """Extract config from WaitForBlackboardVariableValue nodes."""

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        if hasattr(node, "check"):
            return self.extract_comparison(node.check)
        return {}


class CheckBlackboardVariableValuesExtractor(ConfigExtractor):
    """Extract config from CheckBlackboardVariableValues nodes.

    This node handles multiple comparison expressions.
    """

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        config = {}

        if hasattr(node, "checks"):
            # Import here to avoid circular dependency
            from py_forest.adapters.py_trees_adapter import (
                ComparisonExpressionExtractor,
            )

            checks_list = []
            for check in node.checks:
                extracted = ComparisonExpressionExtractor.extract(check)
                checks_list.append(
                    {
                        "variable": extracted["variable"],
                        "operator": operator_to_string(extracted["operator_function"]),
                        "value": extracted["comparison_value"],
                    }
                )
            config["checks"] = checks_list

        if hasattr(node, "logical_operator"):
            config["logical_operator"] = str(node.logical_operator)

        return config


class BlackboardToStatusExtractor(ConfigExtractor):
    """Extract config from BlackboardToStatus nodes."""

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        if hasattr(node, "variable_name"):
            return {"variable": node.variable_name}
        return {}


# =============================================================================
# Time-based Extractors
# =============================================================================


class TickCounterExtractor(ConfigExtractor):
    """Extract config from TickCounter nodes."""

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        config = {}
        if hasattr(node, "num_ticks"):
            config["num_ticks"] = node.num_ticks
        if hasattr(node, "final_status"):
            config["final_status"] = str(node.final_status)
        return config


class SuccessEveryNExtractor(ConfigExtractor):
    """Extract config from SuccessEveryN nodes."""

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        if hasattr(node, "n"):
            return {"n": node.n}
        return {}


class PeriodicExtractor(ConfigExtractor):
    """Extract config from Periodic nodes."""

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        if hasattr(node, "n"):
            return {"n": node.n}
        return {}


class StatusQueueExtractor(ConfigExtractor):
    """Extract config from StatusQueue nodes."""

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        config = {}
        if hasattr(node, "queue"):
            config["queue"] = [str(status) for status in node.queue]
        if hasattr(node, "eventually"):
            config["eventually"] = str(node.eventually)
        return config


# =============================================================================
# Probabilistic Extractors
# =============================================================================


class ProbabilisticBehaviourExtractor(ConfigExtractor):
    """Extract config from ProbabilisticBehaviour nodes."""

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        if hasattr(node, "weights"):
            return {"weights": node.weights}
        return {}


# =============================================================================
# Decorator Extractors - Repetition
# =============================================================================


class RepeatExtractor(ConfigExtractor):
    """Extract config from Repeat decorator."""

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        if hasattr(node, "num_success"):
            return {"num_success": node.num_success}
        return {}


class RetryExtractor(ConfigExtractor):
    """Extract config from Retry decorator."""

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        if hasattr(node, "num_failures"):
            return {"num_failures": node.num_failures}
        return {}


class OneShotExtractor(ConfigExtractor):
    """Extract config from OneShot decorator."""

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        if hasattr(node, "policy"):
            return {"policy": str(node.policy)}
        return {}


# =============================================================================
# Decorator Extractors - Time-based
# =============================================================================


class TimeoutExtractor(ConfigExtractor):
    """Extract config from Timeout decorator."""

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        if hasattr(node, "duration"):
            return {"duration": node.duration}
        return {}


# =============================================================================
# Decorator Extractors - Advanced
# =============================================================================


class EternalGuardExtractor(ComparisonBasedExtractor):
    """Extract config from EternalGuard decorator."""

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        if hasattr(node, "check"):
            return self.extract_comparison(node.check)
        return {}


class ConditionExtractor(ComparisonBasedExtractor):
    """Extract config from Condition decorator."""

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        if hasattr(node, "check"):
            return self.extract_comparison(node.check)
        return {}


class ForEachExtractor(ConfigExtractor):
    """Extract config from ForEach decorator."""

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        if hasattr(node, "variable_name"):
            return {"variable": node.variable_name}
        return {}


class StatusToBlackboardExtractor(ConfigExtractor):
    """Extract config from StatusToBlackboard decorator."""

    def extract(self, node, context: Optional = None) -> dict[str, Any]:
        if hasattr(node, "variable_name"):
            return {"variable": node.variable_name}
        return {}


# =============================================================================
# Extractor Registry
# =============================================================================

# Global registry mapping node class names to extractor instances
EXTRACTOR_REGISTRY: dict[str, ConfigExtractor] = {
    # Blackboard behaviors
    "CheckBlackboardVariableValue": CheckBlackboardVariableValueExtractor(),
    "CheckBlackboardVariableExists": CheckBlackboardVariableExistsExtractor(),
    "SetBlackboardVariable": SetBlackboardVariableExtractor(),
    "UnsetBlackboardVariable": UnsetBlackboardVariableExtractor(),
    "WaitForBlackboardVariable": WaitForBlackboardVariableExtractor(),
    "WaitForBlackboardVariableValue": WaitForBlackboardVariableValueExtractor(),
    "CheckBlackboardVariableValues": CheckBlackboardVariableValuesExtractor(),
    "BlackboardToStatus": BlackboardToStatusExtractor(),
    # Time-based behaviors
    "TickCounter": TickCounterExtractor(),
    "SuccessEveryN": SuccessEveryNExtractor(),
    "Periodic": PeriodicExtractor(),
    "StatusQueue": StatusQueueExtractor(),
    # Probabilistic
    "ProbabilisticBehaviour": ProbabilisticBehaviourExtractor(),
    # Decorators - Repetition
    "Repeat": RepeatExtractor(),
    "Retry": RetryExtractor(),
    "OneShot": OneShotExtractor(),
    # Decorators - Time
    "Timeout": TimeoutExtractor(),
    # Decorators - Advanced
    "EternalGuard": EternalGuardExtractor(),
    "Condition": ConditionExtractor(),
    "ForEach": ForEachExtractor(),
    "StatusToBlackboard": StatusToBlackboardExtractor(),
}


def get_extractor(class_name: str) -> ConfigExtractor | None:
    """Get the extractor for a node class.

    Args:
        class_name: py_trees node class name (e.g., "CheckBlackboardVariableValue")

    Returns:
        ConfigExtractor instance or None if no extractor registered

    Example:
        >>> extractor = get_extractor("Timeout")
        >>> if extractor:
        >>>     config = extractor.extract(my_timeout_node)
    """
    return EXTRACTOR_REGISTRY.get(class_name)


def extract_config(node, context: Optional = None) -> dict[str, Any]:
    """Extract configuration from a py_trees node using the registry.

    Args:
        node: py_trees node instance
        context: Optional conversion context for warnings

    Returns:
        Configuration dictionary

    Example:
        >>> from py_forest.core.extractors import extract_config
        >>> config = extract_config(my_py_trees_node)
    """
    class_name = type(node).__name__

    # Use extractor if available
    extractor = get_extractor(class_name)
    config = extractor.extract(node, context) if extractor else {}

    # Common config for all composites (memory parameter)
    if hasattr(node, "memory"):
        config["memory"] = node.memory

    # Store original class name for reference
    config["_py_trees_class"] = class_name

    return config
