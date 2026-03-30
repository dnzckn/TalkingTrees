"""Behavior registry for mapping behavior types to implementations and schemas."""

from typing import Any

import py_trees
from py_trees import behaviour

from talking_trees.models.schema import (
    BehaviorSchema,
    NodeCategory,
)


class BehaviorRegistry:
    """Registry for behavior types, implementations, and schemas.

    Manages:
    - Mapping from node_type string to py_trees Behaviour class
    - Schema information for each behavior (for editors)
    - Factory methods to instantiate behaviors with config
    """

    def __init__(self) -> None:
        """Initialize the registry with built-in py_trees behaviors."""
        self._implementations: dict[str, type[behaviour.Behaviour]] = {}
        self._schemas: dict[str, BehaviorSchema] = {}

        # Register all built-in py_trees behaviors
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register all built-in py_trees behaviors."""
        from talking_trees.core.registry_builtins import register_builtins
        register_builtins(self)

    def _register_custom_behaviors(self) -> None:
        """Register custom TalkingTrees behaviors.

        Note: Custom behaviors are available in talking_trees.behaviors.examples
        for demonstration purposes, but they are not automatically registered.
        TalkingTrees only serializes/deserializes py_trees nodes."""
        pass



    def register(
        self,
        node_type: str,
        implementation: type[behaviour.Behaviour],
        schema: BehaviorSchema,
    ) -> None:
        """Register a behavior type.

        Args:
            node_type: Unique identifier for this behavior type
            implementation: py_trees Behaviour class
            schema: Schema describing the behavior (for editors)
        """
        self._implementations[node_type] = implementation
        self._schemas[node_type] = schema

    def get_implementation(self, node_type: str) -> type[behaviour.Behaviour] | None:
        """Get the implementation class for a behavior type.

        Args:
            node_type: Behavior type identifier

        Returns:
            Behaviour class or None if not found
        """
        return self._implementations.get(node_type)

    def get_schema(self, node_type: str) -> BehaviorSchema | None:
        """Get the schema for a behavior type.

        Args:
            node_type: Behavior type identifier

        Returns:
            BehaviorSchema or None if not found
        """
        return self._schemas.get(node_type)

    def is_registered(self, node_type: str) -> bool:
        """Check if a behavior type is registered.

        Args:
            node_type: Behavior type identifier

        Returns:
            True if registered, False otherwise
        """
        return node_type in self._implementations

    def list_all(self) -> list[str]:
        """List all registered behavior types.

        Returns:
            List of behavior type identifiers
        """
        return list(self._implementations.keys())

    def list_by_category(self, category: NodeCategory) -> list[str]:
        """List behaviors by category.

        Args:
            category: Category to filter by

        Returns:
            List of behavior type identifiers in that category
        """
        return [
            node_type
            for node_type, schema in self._schemas.items()
            if schema.category == category
        ]

    def get_node_types_by_category(self, category: NodeCategory) -> set[str]:
        """Get all node types in a category as a set (for efficient lookup).

        Args:
            category: Category to filter by (COMPOSITE, DECORATOR, ACTION, CONDITION)

        Returns:
            Set of node type identifiers in that category

        Example:
            >>> registry = get_registry()
            >>> decorators = registry.get_node_types_by_category(NodeCategory.DECORATOR)
            >>> "Inverter" in decorators
            True
            >>> "Sequence" in decorators
            False
        """
        return set(self.list_by_category(category))

    def get_all_schemas(self) -> dict[str, BehaviorSchema]:
        """Get all behavior schemas.

        Returns:
            Dictionary mapping node_type to BehaviorSchema
        """
        return self._schemas.copy()

    def create_node(
        self, node_type: str, name: str, config: dict[str, Any]
    ) -> behaviour.Behaviour:
        """Factory method to create a behavior instance.

        Args:
            node_type: Type of behavior to create
            name: Name for the behavior instance
            config: Configuration parameters

        Returns:
            Instantiated behaviour

        Raises:
            ValueError: If node_type is not registered
            TypeError: If config parameters are invalid
        """
        implementation = self.get_implementation(node_type)
        if implementation is None:
            raise ValueError(f"Unknown behavior type: {node_type}")

        # Handle different constructor signatures for py_trees classes
        try:
            if node_type == "Parallel":
                # Parallel requires policy parameter
                policy_name = config.get("policy", "SuccessOnAll")
                synchronise = config.get("synchronise", True)
                policy = self._create_parallel_policy(policy_name, synchronise)
                return implementation(name=name, policy=policy)
            elif node_type in ["Timeout", "Retry", "OneShot"]:
                # Decorators need child parameter (will be added later)
                # For now, create with a dummy child
                dummy_child = py_trees.behaviours.Success(name="dummy")
                if node_type == "Timeout":
                    duration = config.get("duration", 5.0)
                    return implementation(
                        name=name, child=dummy_child, duration=duration
                    )
                elif node_type == "Retry":
                    num_failures = config.get("num_failures", 3)
                    return implementation(
                        name=name, child=dummy_child, num_failures=num_failures
                    )
                elif node_type == "OneShot":
                    policy_str = config.get("policy", "ON_COMPLETION")
                    policy = getattr(py_trees.common.OneShotPolicy, policy_str)
                    return implementation(name=name, child=dummy_child, policy=policy)
            elif node_type in ["Sequence", "Selector"]:
                # Composites with memory parameter
                memory = config.get("memory", True)
                return implementation(name=name, memory=memory)
            elif node_type == "SetBlackboardVariable":
                variable = config.get("variable", "result")
                value = config.get("value", "")
                return implementation(name=name, variable=variable, value=value)
            else:
                # Simple behaviors (Success, Failure, Running, etc.)
                return implementation(name=name)
        except Exception as e:
            raise TypeError(
                f"Failed to create {node_type} with config {config}: {e}"
            ) from e

    def _create_parallel_policy(
        self, policy_name: str, synchronise: bool
    ) -> py_trees.common.ParallelPolicy.Base:
        """Create a parallel policy object.

        Args:
            policy_name: Name of the policy
            synchronise: Whether to synchronise

        Returns:
            ParallelPolicy instance
        """
        from talking_trees.core.utils import ParallelPolicyFactory

        return ParallelPolicyFactory.create(policy_name, synchronise)


# Global registry instance
_global_registry: BehaviorRegistry | None = None


def get_registry() -> BehaviorRegistry:
    """Get the global behavior registry instance.

    Returns:
        Global BehaviorRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = BehaviorRegistry()
    return _global_registry
