"""Built-in node type registrations for the BehaviorRegistry."""

import py_trees
from py_trees import composites, decorators

from talking_trees.models.schema import (
    BehaviorSchema,
    BlackboardAccess,
    ChildConstraints,
    ConfigPropertySchema,
    NodeCategory,
    StatusBehavior,
)


def register_builtins(registry) -> None:
    """Register all built-in py_trees node types with the registry.

    Args:
        registry: BehaviorRegistry instance to register types with
    """
    # Composites
    registry.register(
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

    registry.register(
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

    registry.register(
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
                    enum=["SuccessOnAll", "SuccessOnOne"],
                    description="Success policy (SuccessOnSelected not yet supported)",
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
    registry.register(
        node_type="Inverter",
        implementation=decorators.Inverter,
        schema=BehaviorSchema(
            node_type="Inverter",
            category=NodeCategory.DECORATOR,
            display_name="Inverter",
            description="Inverts child result: SUCCESS \u2194 FAILURE",
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

    registry.register(
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

    registry.register(
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

    registry.register(
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

    registry.register(
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
    registry.register(
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
                description="SUCCESS \u2192 FAILURE, FAILURE \u2192 FAILURE, RUNNING \u2192 RUNNING",
            ),
            is_builtin=True,
        ),
    )

    registry.register(
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
                description="FAILURE \u2192 SUCCESS, SUCCESS \u2192 SUCCESS, RUNNING \u2192 RUNNING",
            ),
            is_builtin=True,
        ),
    )

    registry.register(
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
                description="FAILURE \u2192 RUNNING, SUCCESS \u2192 SUCCESS, RUNNING \u2192 RUNNING",
            ),
            is_builtin=True,
        ),
    )

    registry.register(
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
                description="RUNNING \u2192 FAILURE, SUCCESS \u2192 SUCCESS, FAILURE \u2192 FAILURE",
            ),
            is_builtin=True,
        ),
    )

    registry.register(
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
                description="RUNNING \u2192 SUCCESS, SUCCESS \u2192 SUCCESS, FAILURE \u2192 FAILURE",
            ),
            is_builtin=True,
        ),
    )

    registry.register(
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
                description="SUCCESS \u2192 RUNNING, RUNNING \u2192 RUNNING, FAILURE \u2192 FAILURE",
            ),
            is_builtin=True,
        ),
    )

    # Advanced Decorators
    registry.register(
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

    registry.register(
        node_type="Condition",
        implementation=decorators.Condition,
        schema=BehaviorSchema(
            node_type="Condition",
            category=NodeCategory.DECORATOR,
            display_name="Condition",
            description="Blocking conditional - waits for child to return specified status",
            icon="condition",
            color="#16A085",
            config_schema={
                "status": ConfigPropertySchema(
                    type="string",
                    default="SUCCESS",
                    enum=["SUCCESS", "FAILURE", "RUNNING"],
                    description="Status to wait for from child",
                    ui_hints={"widget": "select"},
                ),
            },
            child_constraints=ChildConstraints(min_children=1, max_children=1),
            status_behavior=StatusBehavior(
                returns=["SUCCESS", "RUNNING"],
                description="RUNNING while waiting for child status, SUCCESS when condition met",
            ),
            is_builtin=True,
        ),
    )

    registry.register(
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

    registry.register(
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

    # ForEach (only in py_trees 2.3+)
    if hasattr(decorators, 'ForEach'):
        registry.register(
            node_type="ForEach",
            implementation=decorators.ForEach,
            schema=BehaviorSchema(
            node_type="ForEach",
            category=NodeCategory.DECORATOR,
            display_name="For Each",
            description="Execute child for each item in blackboard iterable",
            icon="for_each",
            color="#9B59B6",
            config_schema={
                "source_key": ConfigPropertySchema(
                    type="string",
                    default="items",
                    description="Blackboard key containing iterable",
                    ui_hints={"widget": "text"},
                ),
                "target_key": ConfigPropertySchema(
                    type="string",
                    default="current_item",
                    description="Blackboard key to set for each iteration",
                    ui_hints={"widget": "text"},
                ),
            },
            child_constraints=ChildConstraints(min_children=1, max_children=1),
            blackboard_access=BlackboardAccess(
                reads=["source_key"],
                writes=["target_key"],
            ),
            status_behavior=StatusBehavior(
                returns=["SUCCESS", "FAILURE", "RUNNING"],
                description="SUCCESS when all items processed, RUNNING while iterating",
            ),
            is_builtin=True,
        ),
    )

    registry.register(
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
    registry.register(
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

    registry.register(
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

    registry.register(
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

    registry.register(
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
    registry.register(
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
                "duration": ConfigPropertySchema(
                    type="integer",
                    default=1,
                    minimum=1,
                    description="Number of ticks to count",
                    ui_hints={"widget": "number"},
                ),
                "completion_status": ConfigPropertySchema(
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

    registry.register(
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

    registry.register(
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

    registry.register(
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
    registry.register(
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

    registry.register(
        node_type="CheckBlackboardVariableValue",
        implementation=py_trees.behaviours.CheckBlackboardVariableValue,
        schema=BehaviorSchema(
            node_type="CheckBlackboardVariableValue",
            category=NodeCategory.CONDITION,
            display_name="Check Variable Value",
            description="Check if a blackboard variable meets a comparison condition",
            icon="check_value",
            color="#16A085",
            config_schema={
                "variable": ConfigPropertySchema(
                    type="string",
                    default="value",
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
                returns=["SUCCESS", "FAILURE"],
                description="SUCCESS if comparison passes, FAILURE otherwise",
            ),
            is_builtin=True,
        ),
    )

    registry.register(
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

    registry.register(
        node_type="SetBlackboardVariable",
        implementation=py_trees.behaviours.SetBlackboardVariable,
        schema=BehaviorSchema(
            node_type="SetBlackboardVariable",
            category=NodeCategory.ACTION,
            display_name="Set Variable",
            description="Set a blackboard variable to a value",
            icon="set_variable",
            color="#E67E22",
            config_schema={
                "variable": ConfigPropertySchema(
                    type="string",
                    default="var",
                    description="Blackboard variable name to set",
                    ui_hints={"widget": "text"},
                ),
                "value": ConfigPropertySchema(
                    type="string",
                    default="",
                    description="Value to set",
                    ui_hints={"widget": "text"},
                ),
                "overwrite": ConfigPropertySchema(
                    type="boolean",
                    default=True,
                    description="Whether to overwrite existing value",
                    ui_hints={"widget": "checkbox"},
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
            is_builtin=True,
        ),
    )

    registry.register(
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

    registry.register(
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

    registry.register(
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
                "operator": ConfigPropertySchema(
                    type="string",
                    default="and",
                    enum=["and", "or", "xor"],
                    description="Logical operator to combine checks",
                    ui_hints={"widget": "select"},
                ),
                "namespace": ConfigPropertySchema(
                    type="string",
                    default=None,
                    description="Optional namespace to store check results",
                    ui_hints={"widget": "text"},
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

    # CompareBlackboardVariables (only in py_trees 2.3+)
    if hasattr(py_trees.behaviours, 'CompareBlackboardVariables'):
        registry.register(
            node_type="CompareBlackboardVariables",
            implementation=py_trees.behaviours.CompareBlackboardVariables,
            schema=BehaviorSchema(
            node_type="CompareBlackboardVariables",
            category=NodeCategory.CONDITION,
            display_name="Compare Two Variables",
            description="Compare two blackboard variables using an operator",
            icon="compare_vars",
            color="#16A085",
            config_schema={
                "var1_key": ConfigPropertySchema(
                    type="string",
                    default="var1",
                    description="First blackboard variable name",
                    ui_hints={"widget": "text"},
                ),
                "var2_key": ConfigPropertySchema(
                    type="string",
                    default="var2",
                    description="Second blackboard variable name",
                    ui_hints={"widget": "text"},
                ),
                "operator": ConfigPropertySchema(
                    type="string",
                    default="==",
                    enum=["<", "<=", "==", "!=", ">=", ">"],
                    description="Comparison operator",
                    ui_hints={"widget": "select"},
                ),
            },
            child_constraints=ChildConstraints(min_children=0, max_children=0),
            blackboard_access=BlackboardAccess(
                reads=["var1_key", "var2_key"],
                writes=[],
            ),
            status_behavior=StatusBehavior(
                returns=["SUCCESS", "FAILURE"],
                description="SUCCESS if comparison holds, FAILURE otherwise",
            ),
            is_builtin=True,
        ),
    )

    registry.register(
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
    registry.register(
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

    # WP5: Remote Subtree for distributed execution
    from talking_trees.behaviors.remote_subtree import RemoteSubtreeBehaviour

    registry.register(
        node_type="RemoteSubtree",
        implementation=RemoteSubtreeBehaviour,
        schema=BehaviorSchema(
            node_type="RemoteSubtree",
            category=NodeCategory.ACTION,
            display_name="Remote Subtree",
            description="Proxies execution to a remote TalkingTrees endpoint",
            icon="cloud",
            color="#9B59B6",
            config_schema={
                "endpoint": ConfigPropertySchema(
                    type="string",
                    description="Remote API endpoint URL",
                ),
                "timeout_ms": ConfigPropertySchema(
                    type="number",
                    default=5000,
                    description="Request timeout in milliseconds",
                ),
                "remote_execution_id": ConfigPropertySchema(
                    type="string",
                    description="Execution ID on remote instance",
                ),
                "auth_token": ConfigPropertySchema(
                    type="string",
                    description="Optional bearer token",
                ),
            },
            child_constraints=ChildConstraints(min_children=0, max_children=0),
            status_behavior=StatusBehavior(
                returns=["SUCCESS", "FAILURE", "RUNNING"],
                description="Maps remote execution status",
            ),
        ),
    )

    # WP-8: Async Action for non-blocking execution
    from talking_trees.execution.async_action import AsyncActionBehaviour
    registry.register(
        node_type="AsyncAction",
        implementation=AsyncActionBehaviour,
        schema=BehaviorSchema(
            node_type="AsyncAction",
            category=NodeCategory.ACTION,
            display_name="Async Action",
            description="Executes a callable asynchronously in a thread pool",
            icon="clock",
            color="#E67E22",
            config_schema={
                "callable": ConfigPropertySchema(type="string", description="Dotted import path to function"),
                "timeout_ms": ConfigPropertySchema(type="number", default=5000, description="Timeout in milliseconds"),
                "on_timeout": ConfigPropertySchema(type="string", default="FAILURE", description="Status on timeout"),
                "output_key": ConfigPropertySchema(type="string", description="Blackboard key for result"),
            },
            child_constraints=ChildConstraints(min_children=0, max_children=0),
            status_behavior=StatusBehavior(returns=["SUCCESS", "FAILURE", "RUNNING"]),
        ),
    )

    # Register custom TalkingTrees behaviors
    registry._register_custom_behaviors()
