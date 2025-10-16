"""Behavior registry for mapping behavior types to implementations and schemas."""

from typing import Any, Dict, List, Optional, Type

import py_trees
from py_trees import behaviour, composites, decorators

from py_forest.models.schema import (
    BehaviorSchema,
    BlackboardAccess,
    ChildConstraints,
    ConfigPropertySchema,
    NodeCategory,
    StatusBehavior,
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
        self._implementations: Dict[str, Type[behaviour.Behaviour]] = {}
        self._schemas: Dict[str, BehaviorSchema] = {}

        # Register all built-in py_trees behaviors
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register all built-in py_trees behaviors."""
        # Composites
        self.register(
            node_type="Sequence",
            implementation=composites.Sequence,
            schema=BehaviorSchema(
                node_type="Sequence",
                category=NodeCategory.COMPOSITE,
                display_name="Sequence",
                description="Execute children sequentially. Returns SUCCESS if all children succeed, FAILURE if any fails.",
                icon="sequence",
                color="#4A90E2",
                config_schema={
                    "memory": ConfigPropertySchema(
                        type="boolean",
                        default=True,
                        description="Resume from last RUNNING child, or restart from beginning",
                        ui_hints={"widget": "checkbox"},
                    )
                },
                child_constraints=ChildConstraints(min_children=1, max_children=None),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE", "RUNNING"],
                    description="SUCCESS if all children succeed, FAILURE if any fails, RUNNING while in progress",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="Selector",
            implementation=composites.Selector,
            schema=BehaviorSchema(
                node_type="Selector",
                category=NodeCategory.COMPOSITE,
                display_name="Selector",
                description="Execute children in priority order. Returns SUCCESS if any child succeeds.",
                icon="selector",
                color="#E67E22",
                config_schema={
                    "memory": ConfigPropertySchema(
                        type="boolean",
                        default=False,
                        description="Resume from last RUNNING child, or restart from beginning",
                        ui_hints={"widget": "checkbox"},
                    )
                },
                child_constraints=ChildConstraints(min_children=1, max_children=None),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE", "RUNNING"],
                    description="SUCCESS if any child succeeds, FAILURE if all fail, RUNNING while in progress",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="Parallel",
            implementation=composites.Parallel,
            schema=BehaviorSchema(
                node_type="Parallel",
                category=NodeCategory.COMPOSITE,
                display_name="Parallel",
                description="Tick all children simultaneously. Policy determines success criteria.",
                icon="parallel",
                color="#9B59B6",
                config_schema={
                    "policy": ConfigPropertySchema(
                        type="string",
                        default="SuccessOnAll",
                        enum=["SuccessOnAll", "SuccessOnOne", "SuccessOnSelected"],
                        description="Success policy",
                        ui_hints={"widget": "select"},
                    ),
                    "synchronise": ConfigPropertySchema(
                        type="boolean",
                        default=True,
                        description="Skip successful children on subsequent ticks",
                        ui_hints={"widget": "checkbox"},
                    ),
                },
                child_constraints=ChildConstraints(min_children=2, max_children=None),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE", "RUNNING"],
                    description="Depends on policy. Returns FAILURE if any child fails.",
                ),
                is_builtin=True,
            ),
        )

        # Decorators
        self.register(
            node_type="Inverter",
            implementation=decorators.Inverter,
            schema=BehaviorSchema(
                node_type="Inverter",
                category=NodeCategory.DECORATOR,
                display_name="Inverter",
                description="Inverts child result: SUCCESS ↔ FAILURE",
                icon="inverter",
                color="#1ABC9C",
                config_schema={},
                child_constraints=ChildConstraints(min_children=1, max_children=1),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE", "RUNNING"],
                    description="Flips SUCCESS and FAILURE, passes through RUNNING",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="Timeout",
            implementation=decorators.Timeout,
            schema=BehaviorSchema(
                node_type="Timeout",
                category=NodeCategory.DECORATOR,
                display_name="Timeout",
                description="Fails if child doesn't complete within duration",
                icon="timeout",
                color="#E74C3C",
                config_schema={
                    "duration": ConfigPropertySchema(
                        type="number",
                        default=5.0,
                        minimum=0.1,
                        description="Timeout duration in seconds",
                        ui_hints={"widget": "number", "step": 0.1},
                    )
                },
                child_constraints=ChildConstraints(min_children=1, max_children=1),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE", "RUNNING"],
                    description="FAILURE if timeout exceeded, otherwise child status",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="Retry",
            implementation=decorators.Retry,
            schema=BehaviorSchema(
                node_type="Retry",
                category=NodeCategory.DECORATOR,
                display_name="Retry",
                description="Retry child on failure up to N times",
                icon="retry",
                color="#F39C12",
                config_schema={
                    "num_failures": ConfigPropertySchema(
                        type="integer",
                        default=3,
                        minimum=1,
                        description="Maximum number of failure attempts",
                        ui_hints={"widget": "number"},
                    )
                },
                child_constraints=ChildConstraints(min_children=1, max_children=1),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE", "RUNNING"],
                    description="Retries child on FAILURE up to num_failures times",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="OneShot",
            implementation=decorators.OneShot,
            schema=BehaviorSchema(
                node_type="OneShot",
                category=NodeCategory.DECORATOR,
                display_name="One Shot",
                description="Execute child once, then return final status forever",
                icon="oneshot",
                color="#3498DB",
                config_schema={
                    "policy": ConfigPropertySchema(
                        type="string",
                        default="ON_COMPLETION",
                        enum=["ON_COMPLETION", "ON_SUCCESSFUL_COMPLETION"],
                        description="When to activate oneshot",
                        ui_hints={"widget": "select"},
                    )
                },
                child_constraints=ChildConstraints(min_children=1, max_children=1),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE", "RUNNING"],
                    description="Child status on first execution, then fixed status",
                ),
                is_builtin=True,
            ),
        )

        # Basic behaviors from py_trees.behaviours
        self.register(
            node_type="Success",
            implementation=py_trees.behaviours.Success,
            schema=BehaviorSchema(
                node_type="Success",
                category=NodeCategory.ACTION,
                display_name="Success",
                description="Always returns SUCCESS",
                icon="success",
                color="#27AE60",
                config_schema={},
                child_constraints=ChildConstraints(min_children=0, max_children=0),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS"],
                    description="Always returns SUCCESS",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="Failure",
            implementation=py_trees.behaviours.Failure,
            schema=BehaviorSchema(
                node_type="Failure",
                category=NodeCategory.ACTION,
                display_name="Failure",
                description="Always returns FAILURE",
                icon="failure",
                color="#C0392B",
                config_schema={},
                child_constraints=ChildConstraints(min_children=0, max_children=0),
                status_behavior=StatusBehavior(
                    returns=["FAILURE"],
                    description="Always returns FAILURE",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="Running",
            implementation=py_trees.behaviours.Running,
            schema=BehaviorSchema(
                node_type="Running",
                category=NodeCategory.ACTION,
                display_name="Running",
                description="Always returns RUNNING",
                icon="running",
                color="#F39C12",
                config_schema={},
                child_constraints=ChildConstraints(min_children=0, max_children=0),
                status_behavior=StatusBehavior(
                    returns=["RUNNING"],
                    description="Always returns RUNNING",
                ),
                is_builtin=True,
            ),
        )

        # Register custom PyForest behaviors
        self._register_custom_behaviors()

    def _register_custom_behaviors(self) -> None:
        """Register custom PyForest behaviors."""
        from py_forest.behaviors import examples

        self.register(
            node_type="CheckBattery",
            implementation=examples.CheckBattery,
            schema=BehaviorSchema(
                node_type="CheckBattery",
                category=NodeCategory.CONDITION,
                display_name="Battery Check",
                description="Check if battery level is above threshold",
                icon="battery",
                color="#F39C12",
                config_schema={
                    "threshold": ConfigPropertySchema(
                        type="number",
                        default=0.2,
                        minimum=0.0,
                        maximum=1.0,
                        description="Minimum battery level (0.0-1.0)",
                        ui_hints={"widget": "slider", "step": 0.05},
                    )
                },
                child_constraints=ChildConstraints(min_children=0, max_children=0),
                blackboard_access=BlackboardAccess(
                    reads=["/battery/level"],
                    writes=[],
                ),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE"],
                    description="SUCCESS if battery above threshold, FAILURE otherwise",
                ),
                is_builtin=False,
            ),
        )

        self.register(
            node_type="Log",
            implementation=examples.Log,
            schema=BehaviorSchema(
                node_type="Log",
                category=NodeCategory.ACTION,
                display_name="Log Message",
                description="Log a message and return SUCCESS",
                icon="log",
                color="#3498DB",
                config_schema={
                    "message": ConfigPropertySchema(
                        type="string",
                        default="",
                        description="Message to log",
                        ui_hints={"widget": "textarea"},
                    )
                },
                child_constraints=ChildConstraints(min_children=0, max_children=0),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS"],
                    description="Always returns SUCCESS after logging",
                ),
                is_builtin=False,
            ),
        )

        self.register(
            node_type="Wait",
            implementation=examples.Wait,
            schema=BehaviorSchema(
                node_type="Wait",
                category=NodeCategory.ACTION,
                display_name="Wait/Delay",
                description="Wait for specified duration before returning SUCCESS",
                icon="wait",
                color="#9B59B6",
                config_schema={
                    "duration": ConfigPropertySchema(
                        type="number",
                        default=1.0,
                        minimum=0.1,
                        description="Wait duration in seconds",
                        ui_hints={"widget": "number", "step": 0.1},
                    )
                },
                child_constraints=ChildConstraints(min_children=0, max_children=0),
                status_behavior=StatusBehavior(
                    returns=["RUNNING", "SUCCESS"],
                    description="RUNNING while waiting, SUCCESS when complete",
                ),
                is_builtin=False,
            ),
        )

    def register(
        self,
        node_type: str,
        implementation: Type[behaviour.Behaviour],
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

    def get_implementation(self, node_type: str) -> Optional[Type[behaviour.Behaviour]]:
        """Get the implementation class for a behavior type.

        Args:
            node_type: Behavior type identifier

        Returns:
            Behaviour class or None if not found
        """
        return self._implementations.get(node_type)

    def get_schema(self, node_type: str) -> Optional[BehaviorSchema]:
        """Get the schema for a behavior type.

        Args:
            node_type: Behavior type identifier

        Returns:
            BehaviorSchema or None if not found
        """
        return self._schemas.get(node_type)

    def list_all(self) -> List[str]:
        """List all registered behavior types.

        Returns:
            List of behavior type identifiers
        """
        return list(self._implementations.keys())

    def list_by_category(self, category: NodeCategory) -> List[str]:
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

    def get_all_schemas(self) -> Dict[str, BehaviorSchema]:
        """Get all behavior schemas.

        Returns:
            Dictionary mapping node_type to BehaviorSchema
        """
        return self._schemas.copy()

    def create_node(
        self, node_type: str, name: str, config: Dict[str, Any]
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
                    return implementation(name=name, child=dummy_child, duration=duration)
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
            elif node_type == "CheckBattery":
                threshold = config.get("threshold", 0.2)
                return implementation(name=name, threshold=threshold)
            elif node_type == "Log":
                message = config.get("message", "")
                return implementation(name=name, message=message)
            elif node_type == "Wait":
                duration = config.get("duration", 1.0)
                return implementation(name=name, duration=duration)
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
        if policy_name == "SuccessOnAll":
            return py_trees.common.ParallelPolicy.SuccessOnAll(synchronise=synchronise)
        elif policy_name == "SuccessOnOne":
            return py_trees.common.ParallelPolicy.SuccessOnOne()
        elif policy_name == "SuccessOnSelected":
            # For now, return SuccessOnAll - proper implementation needs child list
            return py_trees.common.ParallelPolicy.SuccessOnAll(synchronise=synchronise)
        else:
            raise ValueError(f"Unknown parallel policy: {policy_name}")


# Global registry instance
_global_registry: Optional[BehaviorRegistry] = None


def get_registry() -> BehaviorRegistry:
    """Get the global behavior registry instance.

    Returns:
        Global BehaviorRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = BehaviorRegistry()
    return _global_registry
