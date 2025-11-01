"""Core constants for TalkingTrees.

This module provides type-safe constants for configuration keys, preventing
typos and enabling IDE autocomplete and refactoring support.
"""

# =============================================================================
# Configuration Keys
# =============================================================================


class ConfigKeys:
    """Type-safe configuration key constants.

    Use these instead of string literals to prevent typos and enable
    IDE autocomplete and refactoring.

    Example:
        >>> # Bad:
        >>> duration = config.get("duraton", 5.0)  # Typo!
        >>>
        >>> # Good:
        >>> duration = config.get(ConfigKeys.DURATION, 5.0)  # Type-safe
    """

    # Common keys
    MEMORY = "memory"
    VARIABLE = "variable"
    VALUE = "value"
    OPERATOR = "operator"
    OPERATOR_STR = "operator_str"
    DURATION = "duration"

    # Blackboard keys
    OVERWRITE = "overwrite"

    # Parallel policy keys
    POLICY = "policy"
    SYNCHRONISE = "synchronise"

    # Repetition keys
    NUM_SUCCESS = "num_success"
    NUM_FAILURES = "num_failures"

    # Status keys
    FINAL_STATUS = "final_status"
    STATUS = "status"
    EVENTUALLY = "eventually"
    QUEUE = "queue"

    # Time-based keys
    NUM_TICKS = "num_ticks"
    N = "n"

    # Comparison keys
    CHECKS = "checks"
    LOGICAL_OPERATOR = "logical_operator"

    # Probabilistic keys
    WEIGHTS = "weights"

    # Custom behavior keys
    THRESHOLD = "threshold"
    MESSAGE = "message"

    # Internal/debugging keys
    PY_TREES_CLASS = "_py_trees_class"


class PolicyNames:
    """Parallel policy name constants."""

    SUCCESS_ON_ALL = "SuccessOnAll"
    SUCCESS_ON_ONE = "SuccessOnOne"
    SUCCESS_ON_SELECTED = "SuccessOnSelected"


class OneShotPolicyNames:
    """OneShot policy name constants."""

    ON_COMPLETION = "ON_COMPLETION"
    ON_SUCCESSFUL_COMPLETION = "ON_SUCCESSFUL_COMPLETION"


class DefaultValues:
    """Default configuration values."""

    # Common defaults
    MEMORY = True  # For Sequence/Selector
    OPERATOR = "=="

    # Blackboard defaults
    VARIABLE = "var"
    OVERWRITE = True

    # Parallel defaults
    POLICY = PolicyNames.SUCCESS_ON_ALL
    SYNCHRONISE = True

    # Repetition defaults
    NUM_SUCCESS = 1
    NUM_FAILURES = 1

    # Time defaults
    DURATION = 5.0
    NUM_TICKS = 1
    N = 2

    # Probabilistic defaults
    WEIGHTS = [1.0, 1.0, 1.0]

    # Custom behavior defaults
    THRESHOLD = 0.2
    MESSAGE = ""


# =============================================================================
# Node Type Names
# =============================================================================


class NodeTypes:
    """Node type name constants."""

    # Composites
    SEQUENCE = "Sequence"
    SELECTOR = "Selector"
    PARALLEL = "Parallel"

    # Decorators - Basic
    INVERTER = "Inverter"

    # Decorators - Status converters
    SUCCESS_IS_FAILURE = "SuccessIsFailure"
    FAILURE_IS_SUCCESS = "FailureIsSuccess"
    FAILURE_IS_RUNNING = "FailureIsRunning"
    RUNNING_IS_FAILURE = "RunningIsFailure"
    RUNNING_IS_SUCCESS = "RunningIsSuccess"
    SUCCESS_IS_RUNNING = "SuccessIsRunning"

    # Decorators - Repetition
    REPEAT = "Repeat"
    RETRY = "Retry"
    ONE_SHOT = "OneShot"

    # Decorators - Time-based
    TIMEOUT = "Timeout"

    # Decorators - Advanced
    ETERNAL_GUARD = "EternalGuard"
    CONDITION = "Condition"
    COUNT = "Count"
    STATUS_TO_BLACKBOARD = "StatusToBlackboard"
    PASS_THROUGH = "PassThrough"

    # Behaviors - Basic
    SUCCESS = "Success"
    FAILURE = "Failure"
    RUNNING = "Running"
    DUMMY = "Dummy"

    # Behaviors - Blackboard
    CHECK_BLACKBOARD_CONDITION = "CheckBlackboardCondition"
    SET_BLACKBOARD_VARIABLE = "SetBlackboardVariable"
    CHECK_BLACKBOARD_VARIABLE_EXISTS = "CheckBlackboardVariableExists"
    UNSET_BLACKBOARD_VARIABLE = "UnsetBlackboardVariable"
    WAIT_FOR_BLACKBOARD_VARIABLE = "WaitForBlackboardVariable"
    CHECK_BLACKBOARD_VARIABLE_VALUES = "CheckBlackboardVariableValues"
    BLACKBOARD_TO_STATUS = "BlackboardToStatus"
    WAIT_FOR_BLACKBOARD_VARIABLE_VALUE = "WaitForBlackboardVariableValue"

    # Behaviors - Time-based
    TICK_COUNTER = "TickCounter"
    SUCCESS_EVERY_N = "SuccessEveryN"
    PERIODIC = "Periodic"
    STATUS_QUEUE = "StatusQueue"

    # Behaviors - Probabilistic
    PROBABILISTIC_BEHAVIOUR = "ProbabilisticBehaviour"

    # Custom behaviors
    CHECK_BATTERY = "CheckBattery"
    LOG = "Log"
    WAIT = "Wait"
    GET_BLACKBOARD_VARIABLE = "GetBlackboardVariable"


# =============================================================================
# Status Names
# =============================================================================


class StatusNames:
    """py_trees Status enum name constants."""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RUNNING = "RUNNING"
    INVALID = "INVALID"


# =============================================================================
# Helper Functions
# =============================================================================


def get_config_value(config: dict, key: str, default=None):
    """Type-safe config value getter.

    Args:
        config: Configuration dictionary
        key: Configuration key (use ConfigKeys constants)
        default: Default value if key not found

    Returns:
        Configuration value or default

    Example:
        >>> config = {"memory": True}
        >>> get_config_value(config, ConfigKeys.MEMORY, False)
        True
        >>> get_config_value(config, ConfigKeys.DURATION, 5.0)
        5.0
    """
    return config.get(key, default)
