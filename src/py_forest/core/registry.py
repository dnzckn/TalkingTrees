"""Behavior registry for mapping behavior types to implementations and schemas."""

from typing import Any

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
        self._implementations: dict[str, type[behaviour.Behaviour]] = {}
        self._schemas: dict[str, BehaviorSchema] = {}

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

        self.register(
            node_type="Repeat",
            implementation=decorators.Repeat,
            schema=BehaviorSchema(
                node_type="Repeat",
                category=NodeCategory.DECORATOR,
                display_name="Repeat",
                description="Repeat child N times before returning SUCCESS",
                icon="repeat",
                color="#9B59B6",
                config_schema={
                    "num_success": ConfigPropertySchema(
                        type="integer",
                        default=2,
                        minimum=-1,
                        description="Number of successful completions required (-1 for infinite)",
                        ui_hints={"widget": "number"},
                    )
                },
                child_constraints=ChildConstraints(min_children=1, max_children=1),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE", "RUNNING"],
                    description="RUNNING until N successes, then SUCCESS. FAILURE propagates",
                ),
                is_builtin=True,
            ),
        )

        # Status Converter Decorators
        self.register(
            node_type="SuccessIsFailure",
            implementation=decorators.SuccessIsFailure,
            schema=BehaviorSchema(
                node_type="SuccessIsFailure",
                category=NodeCategory.DECORATOR,
                display_name="Success Is Failure",
                description="Converts child SUCCESS to FAILURE, passes through FAILURE and RUNNING",
                icon="success_to_fail",
                color="#E67E22",
                config_schema={},
                child_constraints=ChildConstraints(min_children=1, max_children=1),
                status_behavior=StatusBehavior(
                    returns=["FAILURE", "RUNNING"],
                    description="SUCCESS → FAILURE, FAILURE → FAILURE, RUNNING → RUNNING",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="FailureIsSuccess",
            implementation=decorators.FailureIsSuccess,
            schema=BehaviorSchema(
                node_type="FailureIsSuccess",
                category=NodeCategory.DECORATOR,
                display_name="Failure Is Success",
                description="Converts child FAILURE to SUCCESS, passes through SUCCESS and RUNNING",
                icon="fail_to_success",
                color="#27AE60",
                config_schema={},
                child_constraints=ChildConstraints(min_children=1, max_children=1),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "RUNNING"],
                    description="FAILURE → SUCCESS, SUCCESS → SUCCESS, RUNNING → RUNNING",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="FailureIsRunning",
            implementation=decorators.FailureIsRunning,
            schema=BehaviorSchema(
                node_type="FailureIsRunning",
                category=NodeCategory.DECORATOR,
                display_name="Failure Is Running",
                description="Converts child FAILURE to RUNNING",
                icon="fail_to_running",
                color="#F39C12",
                config_schema={},
                child_constraints=ChildConstraints(min_children=1, max_children=1),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "RUNNING"],
                    description="FAILURE → RUNNING, SUCCESS → SUCCESS, RUNNING → RUNNING",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="RunningIsFailure",
            implementation=decorators.RunningIsFailure,
            schema=BehaviorSchema(
                node_type="RunningIsFailure",
                category=NodeCategory.DECORATOR,
                display_name="Running Is Failure",
                description="Converts child RUNNING to FAILURE",
                icon="running_to_fail",
                color="#C0392B",
                config_schema={},
                child_constraints=ChildConstraints(min_children=1, max_children=1),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE"],
                    description="RUNNING → FAILURE, SUCCESS → SUCCESS, FAILURE → FAILURE",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="RunningIsSuccess",
            implementation=decorators.RunningIsSuccess,
            schema=BehaviorSchema(
                node_type="RunningIsSuccess",
                category=NodeCategory.DECORATOR,
                display_name="Running Is Success",
                description="Converts child RUNNING to SUCCESS",
                icon="running_to_success",
                color="#27AE60",
                config_schema={},
                child_constraints=ChildConstraints(min_children=1, max_children=1),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE"],
                    description="RUNNING → SUCCESS, SUCCESS → SUCCESS, FAILURE → FAILURE",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="SuccessIsRunning",
            implementation=decorators.SuccessIsRunning,
            schema=BehaviorSchema(
                node_type="SuccessIsRunning",
                category=NodeCategory.DECORATOR,
                display_name="Success Is Running",
                description="Converts child SUCCESS to RUNNING",
                icon="success_to_running",
                color="#F39C12",
                config_schema={},
                child_constraints=ChildConstraints(min_children=1, max_children=1),
                status_behavior=StatusBehavior(
                    returns=["RUNNING", "FAILURE"],
                    description="SUCCESS → RUNNING, RUNNING → RUNNING, FAILURE → FAILURE",
                ),
                is_builtin=True,
            ),
        )

        # Advanced Decorators
        self.register(
            node_type="EternalGuard",
            implementation=decorators.EternalGuard,
            schema=BehaviorSchema(
                node_type="EternalGuard",
                category=NodeCategory.DECORATOR,
                display_name="Eternal Guard",
                description="Continuously check condition; invalidate child if condition fails",
                icon="guard",
                color="#8E44AD",
                config_schema={
                    "variable": ConfigPropertySchema(
                        type="string",
                        default="condition",
                        description="Blackboard variable to check",
                        ui_hints={"widget": "text"},
                    ),
                    "operator": ConfigPropertySchema(
                        type="string",
                        default="==",
                        enum=["<", "<=", "==", "!=", ">=", ">"],
                        description="Comparison operator",
                        ui_hints={"widget": "select"},
                    ),
                    "value": ConfigPropertySchema(
                        type="number",
                        default=0,
                        description="Value to compare against",
                        ui_hints={"widget": "number"},
                    ),
                },
                child_constraints=ChildConstraints(min_children=1, max_children=1),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE", "RUNNING"],
                    description="Child status if condition holds, FAILURE if violated",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="Condition",
            implementation=decorators.Condition,
            schema=BehaviorSchema(
                node_type="Condition",
                category=NodeCategory.DECORATOR,
                display_name="Condition",
                description="Blocking conditional - waits for condition to be true before executing child",
                icon="condition",
                color="#16A085",
                config_schema={
                    "variable": ConfigPropertySchema(
                        type="string",
                        default="condition",
                        description="Blackboard variable to check",
                        ui_hints={"widget": "text"},
                    ),
                    "operator": ConfigPropertySchema(
                        type="string",
                        default="==",
                        enum=["<", "<=", "==", "!=", ">=", ">"],
                        description="Comparison operator",
                        ui_hints={"widget": "select"},
                    ),
                    "value": ConfigPropertySchema(
                        type="number",
                        default=0,
                        description="Value to compare against",
                        ui_hints={"widget": "number"},
                    ),
                },
                child_constraints=ChildConstraints(min_children=1, max_children=1),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE", "RUNNING"],
                    description="RUNNING while waiting, child status when condition met",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="Count",
            implementation=decorators.Count,
            schema=BehaviorSchema(
                node_type="Count",
                category=NodeCategory.DECORATOR,
                display_name="Count",
                description="Tracks execution statistics (tick count, success count, etc.)",
                icon="count",
                color="#3498DB",
                config_schema={},
                child_constraints=ChildConstraints(min_children=1, max_children=1),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE", "RUNNING"],
                    description="Passes through child status while tracking statistics",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="StatusToBlackboard",
            implementation=decorators.StatusToBlackboard,
            schema=BehaviorSchema(
                node_type="StatusToBlackboard",
                category=NodeCategory.DECORATOR,
                display_name="Status To Blackboard",
                description="Write child status to blackboard variable",
                icon="status_to_bb",
                color="#E67E22",
                config_schema={
                    "variable": ConfigPropertySchema(
                        type="string",
                        default="status",
                        description="Blackboard variable to write status to",
                        ui_hints={"widget": "text"},
                    ),
                },
                child_constraints=ChildConstraints(min_children=1, max_children=1),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE", "RUNNING"],
                    description="Passes through child status",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="PassThrough",
            implementation=decorators.PassThrough,
            schema=BehaviorSchema(
                node_type="PassThrough",
                category=NodeCategory.DECORATOR,
                display_name="Pass Through",
                description="Pass through for debugging and visualization",
                icon="passthrough",
                color="#95A5A6",
                config_schema={},
                child_constraints=ChildConstraints(min_children=1, max_children=1),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE", "RUNNING"],
                    description="Passes through child status unchanged",
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

        self.register(
            node_type="Dummy",
            implementation=py_trees.behaviours.Dummy,
            schema=BehaviorSchema(
                node_type="Dummy",
                category=NodeCategory.ACTION,
                display_name="Dummy",
                description="Crash test dummy for testing",
                icon="dummy",
                color="#95A5A6",
                config_schema={},
                child_constraints=ChildConstraints(min_children=0, max_children=0),
                status_behavior=StatusBehavior(
                    returns=["RUNNING"],
                    description="Always returns RUNNING",
                ),
                is_builtin=True,
            ),
        )

        # Time-based Behaviors
        self.register(
            node_type="TickCounter",
            implementation=py_trees.behaviours.TickCounter,
            schema=BehaviorSchema(
                node_type="TickCounter",
                category=NodeCategory.ACTION,
                display_name="Tick Counter",
                description="Counts N ticks before completing with specified status",
                icon="tick_counter",
                color="#3498DB",
                config_schema={
                    "num_ticks": ConfigPropertySchema(
                        type="integer",
                        default=1,
                        minimum=1,
                        description="Number of ticks to count",
                        ui_hints={"widget": "number"},
                    ),
                    "final_status": ConfigPropertySchema(
                        type="string",
                        default="SUCCESS",
                        enum=["SUCCESS", "FAILURE"],
                        description="Status to return after counting",
                        ui_hints={"widget": "select"},
                    ),
                },
                child_constraints=ChildConstraints(min_children=0, max_children=0),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE", "RUNNING"],
                    description="RUNNING while counting, then final_status",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="SuccessEveryN",
            implementation=py_trees.behaviours.SuccessEveryN,
            schema=BehaviorSchema(
                node_type="SuccessEveryN",
                category=NodeCategory.ACTION,
                display_name="Success Every N",
                description="Returns SUCCESS once every N ticks, FAILURE otherwise",
                icon="success_every_n",
                color="#27AE60",
                config_schema={
                    "n": ConfigPropertySchema(
                        type="integer",
                        default=2,
                        minimum=1,
                        description="Period in ticks",
                        ui_hints={"widget": "number"},
                    ),
                },
                child_constraints=ChildConstraints(min_children=0, max_children=0),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE"],
                    description="SUCCESS on every Nth tick, FAILURE otherwise",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="Periodic",
            implementation=py_trees.behaviours.Periodic,
            schema=BehaviorSchema(
                node_type="Periodic",
                category=NodeCategory.ACTION,
                display_name="Periodic",
                description="Cycles through all statuses periodically",
                icon="periodic",
                color="#F39C12",
                config_schema={
                    "n": ConfigPropertySchema(
                        type="integer",
                        default=3,
                        minimum=1,
                        description="Period for each status phase",
                        ui_hints={"widget": "number"},
                    ),
                },
                child_constraints=ChildConstraints(min_children=0, max_children=0),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE", "RUNNING"],
                    description="Rotates: RUNNING for N, SUCCESS for N, FAILURE for N",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="StatusQueue",
            implementation=py_trees.behaviours.StatusQueue,
            schema=BehaviorSchema(
                node_type="StatusQueue",
                category=NodeCategory.ACTION,
                display_name="Status Queue",
                description="Cycles through a predefined queue of statuses",
                icon="status_queue",
                color="#9B59B6",
                config_schema={
                    "queue": ConfigPropertySchema(
                        type="array",
                        default=["SUCCESS"],
                        description="Queue of status strings",
                        ui_hints={"widget": "textarea"},
                    ),
                    "eventually": ConfigPropertySchema(
                        type="string",
                        default=None,
                        enum=["SUCCESS", "FAILURE", "RUNNING"],
                        description="Status to eventually settle on (None = repeat queue)",
                        ui_hints={"widget": "select"},
                    ),
                },
                child_constraints=ChildConstraints(min_children=0, max_children=0),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE", "RUNNING"],
                    description="Returns statuses from queue in order",
                ),
                is_builtin=True,
            ),
        )

        # Blackboard Behaviors - Additional
        self.register(
            node_type="CheckBlackboardVariableExists",
            implementation=py_trees.behaviours.CheckBlackboardVariableExists,
            schema=BehaviorSchema(
                node_type="CheckBlackboardVariableExists",
                category=NodeCategory.CONDITION,
                display_name="Check Variable Exists",
                description="Check if a blackboard variable exists",
                icon="check_exists",
                color="#16A085",
                config_schema={
                    "variable": ConfigPropertySchema(
                        type="string",
                        default="var",
                        description="Blackboard variable name to check",
                        ui_hints={"widget": "text"},
                    ),
                },
                child_constraints=ChildConstraints(min_children=0, max_children=0),
                blackboard_access=BlackboardAccess(
                    reads=["variable"],
                    writes=[],
                ),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE"],
                    description="SUCCESS if exists, FAILURE if not",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="UnsetBlackboardVariable",
            implementation=py_trees.behaviours.UnsetBlackboardVariable,
            schema=BehaviorSchema(
                node_type="UnsetBlackboardVariable",
                category=NodeCategory.ACTION,
                display_name="Unset Variable",
                description="Remove a blackboard variable",
                icon="unset_variable",
                color="#E74C3C",
                config_schema={
                    "variable": ConfigPropertySchema(
                        type="string",
                        default="var",
                        description="Blackboard variable name to remove",
                        ui_hints={"widget": "text"},
                    ),
                },
                child_constraints=ChildConstraints(min_children=0, max_children=0),
                blackboard_access=BlackboardAccess(
                    reads=[],
                    writes=["variable"],
                ),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS"],
                    description="Always returns SUCCESS (even if variable doesn't exist)",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="WaitForBlackboardVariable",
            implementation=py_trees.behaviours.WaitForBlackboardVariable,
            schema=BehaviorSchema(
                node_type="WaitForBlackboardVariable",
                category=NodeCategory.CONDITION,
                display_name="Wait For Variable",
                description="Blocking - waits until blackboard variable exists",
                icon="wait_var",
                color="#3498DB",
                config_schema={
                    "variable": ConfigPropertySchema(
                        type="string",
                        default="var",
                        description="Blackboard variable name to wait for",
                        ui_hints={"widget": "text"},
                    ),
                },
                child_constraints=ChildConstraints(min_children=0, max_children=0),
                blackboard_access=BlackboardAccess(
                    reads=["variable"],
                    writes=[],
                ),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "RUNNING"],
                    description="RUNNING while waiting, SUCCESS when variable exists",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="WaitForBlackboardVariableValue",
            implementation=py_trees.behaviours.WaitForBlackboardVariableValue,
            schema=BehaviorSchema(
                node_type="WaitForBlackboardVariableValue",
                category=NodeCategory.CONDITION,
                display_name="Wait For Value",
                description="Blocking - waits until blackboard variable matches condition",
                icon="wait_value",
                color="#3498DB",
                config_schema={
                    "variable": ConfigPropertySchema(
                        type="string",
                        default="var",
                        description="Blackboard variable name to check",
                        ui_hints={"widget": "text"},
                    ),
                    "operator": ConfigPropertySchema(
                        type="string",
                        default="==",
                        enum=["<", "<=", "==", "!=", ">=", ">"],
                        description="Comparison operator",
                        ui_hints={"widget": "select"},
                    ),
                    "value": ConfigPropertySchema(
                        type="number",
                        default=0,
                        description="Value to compare against",
                        ui_hints={"widget": "number"},
                    ),
                },
                child_constraints=ChildConstraints(min_children=0, max_children=0),
                blackboard_access=BlackboardAccess(
                    reads=["variable"],
                    writes=[],
                ),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "RUNNING"],
                    description="RUNNING while waiting, SUCCESS when condition met",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="CheckBlackboardVariableValues",
            implementation=py_trees.behaviours.CheckBlackboardVariableValues,
            schema=BehaviorSchema(
                node_type="CheckBlackboardVariableValues",
                category=NodeCategory.CONDITION,
                display_name="Check Multiple Values",
                description="Check multiple blackboard conditions with logical AND/OR",
                icon="check_multi",
                color="#16A085",
                config_schema={
                    "checks": ConfigPropertySchema(
                        type="array",
                        default=[],
                        description="List of check objects {variable, operator, value}",
                        ui_hints={"widget": "textarea"},
                    ),
                    "logical_operator": ConfigPropertySchema(
                        type="string",
                        default="and",
                        enum=["and", "or"],
                        description="Logical operator to combine checks",
                        ui_hints={"widget": "select"},
                    ),
                },
                child_constraints=ChildConstraints(min_children=0, max_children=0),
                blackboard_access=BlackboardAccess(
                    reads=["*"],
                    writes=[],
                ),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE"],
                    description="SUCCESS if all/any checks pass, FAILURE otherwise",
                ),
                is_builtin=True,
            ),
        )

        self.register(
            node_type="BlackboardToStatus",
            implementation=py_trees.behaviours.BlackboardToStatus,
            schema=BehaviorSchema(
                node_type="BlackboardToStatus",
                category=NodeCategory.ACTION,
                display_name="Blackboard To Status",
                description="Return status stored in blackboard variable",
                icon="bb_to_status",
                color="#E67E22",
                config_schema={
                    "variable": ConfigPropertySchema(
                        type="string",
                        default="status",
                        description="Blackboard variable containing status",
                        ui_hints={"widget": "text"},
                    ),
                },
                child_constraints=ChildConstraints(min_children=0, max_children=0),
                blackboard_access=BlackboardAccess(
                    reads=["variable"],
                    writes=[],
                ),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE", "RUNNING"],
                    description="Returns status from blackboard variable",
                ),
                is_builtin=True,
            ),
        )

        # Probabilistic
        self.register(
            node_type="ProbabilisticBehaviour",
            implementation=py_trees.behaviours.ProbabilisticBehaviour,
            schema=BehaviorSchema(
                node_type="ProbabilisticBehaviour",
                category=NodeCategory.ACTION,
                display_name="Probabilistic",
                description="Returns status based on probability distribution",
                icon="probabilistic",
                color="#9B59B6",
                config_schema={
                    "weights": ConfigPropertySchema(
                        type="array",
                        default=[1.0, 1.0, 1.0],
                        description="Weights for [SUCCESS, FAILURE, RUNNING]",
                        ui_hints={"widget": "textarea"},
                    ),
                },
                child_constraints=ChildConstraints(min_children=0, max_children=0),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE", "RUNNING"],
                    description="Returns status based on weighted probability",
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

        self.register(
            node_type="SetBlackboardVariable",
            implementation=examples.SetBlackboardVariable,
            schema=BehaviorSchema(
                node_type="SetBlackboardVariable",
                category=NodeCategory.ACTION,
                display_name="Set Variable",
                description="Set a blackboard variable to a value (REAL ACTION for automation)",
                icon="set_variable",
                color="#E67E22",
                config_schema={
                    "variable": ConfigPropertySchema(
                        type="string",
                        default="result",
                        description="Blackboard variable name to set",
                        ui_hints={"widget": "text"},
                    ),
                    "value": ConfigPropertySchema(
                        type="string",
                        default="",
                        description="Value to set (JSON string, number, or boolean)",
                        ui_hints={"widget": "text"},
                    ),
                },
                child_constraints=ChildConstraints(min_children=0, max_children=0),
                blackboard_access=BlackboardAccess(
                    reads=[],
                    writes=["variable"],
                ),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS"],
                    description="Always returns SUCCESS after setting variable",
                ),
                is_builtin=False,
            ),
        )

        self.register(
            node_type="GetBlackboardVariable",
            implementation=examples.GetBlackboardVariable,
            schema=BehaviorSchema(
                node_type="GetBlackboardVariable",
                category=NodeCategory.ACTION,
                display_name="Get Variable",
                description="Read a blackboard variable (for debugging/testing)",
                icon="get_variable",
                color="#3498DB",
                config_schema={
                    "variable": ConfigPropertySchema(
                        type="string",
                        default="result",
                        description="Blackboard variable name to read",
                        ui_hints={"widget": "text"},
                    ),
                },
                child_constraints=ChildConstraints(min_children=0, max_children=0),
                blackboard_access=BlackboardAccess(
                    reads=["variable"],
                    writes=[],
                ),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE"],
                    description="SUCCESS if variable exists, FAILURE if not found",
                ),
                is_builtin=False,
            ),
        )

        self.register(
            node_type="CheckBlackboardCondition",
            implementation=examples.CheckBlackboardCondition,
            schema=BehaviorSchema(
                node_type="CheckBlackboardCondition",
                category=NodeCategory.DECORATOR,
                display_name="Check Condition",
                description="Check blackboard value with comparison operator, run child if true",
                icon="condition_check",
                color="#16A085",
                config_schema={
                    "variable": ConfigPropertySchema(
                        type="string",
                        default="value",
                        description="Blackboard variable name to check",
                        ui_hints={"widget": "text"},
                    ),
                    "operator_str": ConfigPropertySchema(
                        type="string",
                        default="==",
                        enum=["<", "<=", "==", "!=", ">=", ">"],
                        description="Comparison operator",
                        ui_hints={"widget": "select"},
                    ),
                    "value": ConfigPropertySchema(
                        type="number",
                        default=0,
                        description="Value to compare against",
                        ui_hints={"widget": "number"},
                    ),
                },
                child_constraints=ChildConstraints(min_children=1, max_children=1),
                blackboard_access=BlackboardAccess(
                    reads=["variable"],
                    writes=[],
                ),
                status_behavior=StatusBehavior(
                    returns=["SUCCESS", "FAILURE", "RUNNING"],
                    description="Child status if condition passes, FAILURE if condition fails",
                ),
                is_builtin=False,
            ),
        )

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
            elif node_type == "CheckBattery":
                threshold = config.get("threshold", 0.2)
                return implementation(name=name, threshold=threshold)
            elif node_type == "Log":
                message = config.get("message", "")
                return implementation(name=name, message=message)
            elif node_type == "Wait":
                duration = config.get("duration", 1.0)
                return implementation(name=name, duration=duration)
            elif node_type == "SetBlackboardVariable":
                variable = config.get("variable", "result")
                value = config.get("value", "")
                return implementation(name=name, variable=variable, value=value)
            elif node_type == "GetBlackboardVariable":
                variable = config.get("variable", "result")
                return implementation(name=name, variable=variable)
            elif node_type == "CheckBlackboardCondition":
                # Conditional decorator needs child parameter (will be added later)
                dummy_child = py_trees.behaviours.Success(name="dummy")
                variable = config.get("variable", "value")
                operator_str = config.get("operator_str", "==")
                value = config.get("value", 0)
                return implementation(
                    name=name,
                    child=dummy_child,
                    variable=variable,
                    operator_str=operator_str,
                    value=value,
                )
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
