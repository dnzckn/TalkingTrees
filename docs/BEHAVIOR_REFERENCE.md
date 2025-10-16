# PyForest Behavior Reference

Reference for all available behaviors in PyForest.

## Table of Contents

1. [Composites](#composites)
2. [Decorators](#decorators)
3. [Actions](#actions)
4. [Conditions](#conditions)
5. [Custom Behaviors](#custom-behaviors)
6. [Creating New Behaviors](#creating-new-behaviors)

## Composites

Composites control child execution order and logic.

### Sequence

Execute children in order until one fails.

**Type**: Composite
**Children**: Multiple (required)
**Parameters**: None

**Behavior**:
- Ticks children sequentially
- Returns SUCCESS if all children succeed
- Returns FAILURE if any child fails
- Returns RUNNING if current child is running

**Example**:
```json
{
  "node_type": "Sequence",
  "name": "Do Task",
  "config": {},
  "children": [
    {"node_type": "CheckPrecondition", "name": "Check"},
    {"node_type": "ExecuteAction", "name": "Execute"},
    {"node_type": "VerifyResult", "name": "Verify"}
  ]
}
```

**Use Cases**:
- Sequential task execution
- Precondition checking before action
- Multi-step operations

### Selector

Try children until one succeeds (fallback logic).

**Type**: Composite
**Children**: Multiple (required)
**Parameters**: None

**Behavior**:
- Ticks children sequentially
- Returns SUCCESS if any child succeeds
- Returns FAILURE if all children fail
- Returns RUNNING if current child is running

**Example**:
```json
{
  "node_type": "Selector",
  "name": "Choose Action",
  "config": {},
  "children": [
    {"node_type": "PreferredAction", "name": "Try First"},
    {"node_type": "AlternativeAction", "name": "Try Second"},
    {"node_type": "LastResort", "name": "Fallback"}
  ]
}
```

**Use Cases**:
- Fallback logic
- Priority-based selection
- Error handling

### Parallel

Execute multiple children concurrently.

**Type**: Composite
**Children**: Multiple (required)

**Parameters**:
- `policy`: Success policy (default: `SuccessOnAll`)
  - `SuccessOnAll`: All children must succeed
  - `SuccessOnOne`: One child must succeed
  - `SuccessOnSelected`: N children must succeed

**Behavior**:
- Ticks all children every tick
- Returns based on policy
- Children execute independently

**Example**:
```json
{
  "node_type": "Parallel",
  "name": "Do Multiple Things",
  "config": {
    "policy": "SuccessOnAll"
  },
  "children": [
    {"node_type": "MonitorSensors", "name": "Monitor"},
    {"node_type": "ExecuteMotion", "name": "Move"},
    {"node_type": "UpdateUI", "name": "UI"}
  ]
}
```

**Use Cases**:
- Concurrent operations
- Multi-tasking
- Parallel monitoring

## Decorators

Decorators modify child behavior.

### Inverter

Invert child success/failure.

**Type**: Decorator
**Children**: One (required)
**Parameters**: None

**Behavior**:
- SUCCESS → FAILURE
- FAILURE → SUCCESS
- RUNNING → RUNNING
- INVALID → INVALID

**Example**:
```json
{
  "node_type": "Inverter",
  "name": "Check NOT Condition",
  "config": {},
  "children": [
    {"node_type": "CheckBattery", "name": "Battery Low"}
  ]
}
```

**Use Cases**:
- NOT logic
- Inverse conditions
- Failure-driven behavior

### Retry

Retry child on failure.

**Type**: Decorator
**Children**: One (required)

**Parameters**:
- `num_attempts` (int, required): Number of retry attempts

**Behavior**:
- Retries child up to N times
- Returns SUCCESS if any attempt succeeds
- Returns FAILURE after all attempts fail

**Example**:
```json
{
  "node_type": "Retry",
  "name": "Retry Connection",
  "config": {
    "num_attempts": 3
  },
  "children": [
    {"node_type": "ConnectToServer", "name": "Connect"}
  ]
}
```

**Use Cases**:
- Error handling
- Network operations
- Unreliable actions

### Timeout

Limit child execution time.

**Type**: Decorator
**Children**: One (required)

**Parameters**:
- `duration` (float, required): Timeout in seconds

**Behavior**:
- Returns FAILURE if child exceeds duration
- Returns child status otherwise

**Example**:
```json
{
  "node_type": "Timeout",
  "name": "Time Limited Operation",
  "config": {
    "duration": 5.0
  },
  "children": [
    {"node_type": "LongOperation", "name": "Operation"}
  ]
}
```

**Use Cases**:
- Time-limited operations
- Preventing deadlocks
- SLA enforcement

### RunningIsFailure / RunningIsSuccess

Convert RUNNING status.

**Type**: Decorator
**Children**: One (required)
**Parameters**: None

**Behavior**:
- `RunningIsFailure`: RUNNING → FAILURE
- `RunningIsSuccess`: RUNNING → SUCCESS
- Other statuses pass through

**Example**:
```json
{
  "node_type": "RunningIsFailure",
  "name": "Must Complete Immediately",
  "config": {},
  "children": [
    {"node_type": "QuickCheck", "name": "Check"}
  ]
}
```

**Use Cases**:
- Forcing immediate results
- Preventing RUNNING propagation
- Status conversion

## Actions

Actions perform operations.

### Success

Always returns SUCCESS.

**Type**: Action
**Children**: None
**Parameters**: None

**Example**:
```json
{
  "node_type": "Success",
  "name": "Always Succeed",
  "config": {}
}
```

**Use Cases**:
- Testing
- Placeholder behaviors
- Forced success paths

### Failure

Always returns FAILURE.

**Type**: Action
**Children**: None
**Parameters**: None

**Example**:
```json
{
  "node_type": "Failure",
  "name": "Always Fail",
  "config": {}
}
```

**Use Cases**:
- Testing
- Forced failure paths
- Error simulation

### Running

Always returns RUNNING.

**Type**: Action
**Children**: None
**Parameters**: None

**Example**:
```json
{
  "node_type": "Running",
  "name": "Never Complete",
  "config": {}
}
```

**Use Cases**:
- Testing
- Blocking behaviors
- Continuous operations

### Log

Log a message.

**Type**: Action (Custom)
**Children**: None

**Parameters**:
- `message` (string, required): Message to log
- `level` (string, optional): Log level (default: "INFO")

**Behavior**:
- Logs message to stdout
- Returns SUCCESS

**Example**:
```json
{
  "node_type": "Log",
  "name": "Log Status",
  "config": {
    "message": "Execution started",
    "level": "INFO"
  }
}
```

**Use Cases**:
- Debugging
- Execution tracing
- Status reporting

### Wait

Wait for duration.

**Type**: Action (Custom)
**Children**: None

**Parameters**:
- `duration` (float, required): Wait duration in seconds

**Behavior**:
- Returns RUNNING until duration elapsed
- Returns SUCCESS after duration

**Example**:
```json
{
  "node_type": "Wait",
  "name": "Wait 2 Seconds",
  "config": {
    "duration": 2.0
  }
}
```

**Use Cases**:
- Delays
- Rate limiting
- Synchronization

## Conditions

Conditions check state.

### CheckBlackboardVariableExists

Check if blackboard key exists.

**Type**: Condition
**Children**: None

**Parameters**:
- `key` (string, required): Blackboard key to check

**Behavior**:
- Returns SUCCESS if key exists
- Returns FAILURE otherwise

**Example**:
```json
{
  "node_type": "CheckBlackboardVariableExists",
  "name": "Check Battery Key",
  "config": {
    "key": "battery_level"
  }
}
```

### CheckBattery

Check battery level (custom behavior).

**Type**: Condition (Custom)
**Children**: None

**Parameters**:
- `threshold` (float, required): Battery threshold percentage (0-100)

**Behavior**:
- Reads `battery_level` from blackboard
- Returns SUCCESS if level >= threshold
- Returns FAILURE if level < threshold

**Example**:
```json
{
  "node_type": "CheckBattery",
  "name": "Check Battery OK",
  "config": {
    "threshold": 20.0
  }
}
```

**Use Cases**:
- Robot battery management
- Resource checking
- Threshold-based decisions

## Custom Behaviors

PyForest includes 3 custom behaviors:

1. **CheckBattery**: Battery level checking
2. **Log**: Message logging
3. **Wait**: Timed delays

These behaviors demonstrate how to extend PyForest with custom logic.

## Creating New Behaviors

### Step 1: Define Behavior Class

```python
from py_trees.behaviour import Behaviour
from py_trees.common import Status

class MyCustomBehavior(Behaviour):
    def __init__(self, name: str, param1: str, param2: int):
        super().__init__(name)
        self.param1 = param1
        self.param2 = param2

    def update(self) -> Status:
        # Implement behavior logic
        print(f"{self.param1}: {self.param2}")
        return Status.SUCCESS
```

### Step 2: Define Schema

```python
from py_forest.models.schema import BehaviorSchema, ParameterSchema

schema = BehaviorSchema(
    name="MyCustomBehavior",
    description="Does something custom",
    category="action",
    parameters=[
        ParameterSchema(
            name="param1",
            type="string",
            required=True,
            description="First parameter"
        ),
        ParameterSchema(
            name="param2",
            type="int",
            required=True,
            description="Second parameter",
            default=0
        )
    ],
    allows_children=False
)
```

### Step 3: Register Behavior

```python
from py_forest.core.registry import get_behavior_registry

registry = get_behavior_registry()
registry.register("MyCustomBehavior", MyCustomBehavior, schema)
```

### Step 4: Use in Trees

```json
{
  "node_type": "MyCustomBehavior",
  "name": "My Custom Node",
  "config": {
    "param1": "hello",
    "param2": 42
  }
}
```

## Behavior Guidelines

### Stateless Operations

Behaviors should be stateless when possible:

```python
def update(self) -> Status:
    # Read from blackboard
    value = self.blackboard.get("key")

    # Perform operation
    result = self.do_work(value)

    # Write to blackboard
    self.blackboard.set("result", result)

    return Status.SUCCESS
```

### Using Blackboard

Access shared state via blackboard:

```python
# Read
battery = self.blackboard.get("battery_level", default=100.0)

# Write
self.blackboard.set("position", [x, y])

# Check existence
if self.blackboard.exists("target"):
    target = self.blackboard.get("target")
```

### Status Returns

Return appropriate status:

- `SUCCESS`: Operation completed successfully
- `FAILURE`: Operation failed
- `RUNNING`: Operation in progress
- `INVALID`: Not yet initialized

### Initialization

Use `setup()` for initialization:

```python
def setup(self):
    # One-time setup
    self.connection = create_connection()

def update(self) -> Status:
    # Use initialized resources
    return Status.SUCCESS

def shutdown(self):
    # Cleanup
    self.connection.close()
```

## Best Practices

### Parameter Validation

Validate parameters in constructor:

```python
def __init__(self, name: str, threshold: float):
    super().__init__(name)
    if not 0 <= threshold <= 100:
        raise ValueError("Threshold must be 0-100")
    self.threshold = threshold
```

### Error Handling

Handle errors gracefully:

```python
def update(self) -> Status:
    try:
        self.do_risky_operation()
        return Status.SUCCESS
    except Exception as e:
        self.feedback_message = f"Error: {e}"
        return Status.FAILURE
```

### Feedback Messages

Provide useful feedback:

```python
def update(self) -> Status:
    if self.check_condition():
        self.feedback_message = "Condition met"
        return Status.SUCCESS
    else:
        self.feedback_message = "Waiting for condition"
        return Status.RUNNING
```

### Configuration Schemas

Provide complete schemas:

```python
ParameterSchema(
    name="timeout",
    type="float",
    required=False,
    default=10.0,
    description="Operation timeout in seconds",
    min=0.1,
    max=3600.0
)
```

## Summary

PyForest provides:
- 9 built-in py_trees behaviors
- 3 custom behaviors (CheckBattery, Log, Wait)
- Extension system for custom behaviors
- Schema-based configuration
- Blackboard for shared state

For more information:
- py_trees documentation: https://py-trees.readthedocs.io/
- Custom behaviors source: `src/py_forest/behaviors/examples.py`
