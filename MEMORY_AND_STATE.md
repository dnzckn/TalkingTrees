# Memory and State in PyForest

## Two Types of Memory

### 1. Blackboard Memory (Persistent State)
The blackboard is the **global memory** that persists across all ticks.

### 2. Composite Memory (Execution Resume)
Sequence/Selector nodes can **remember** which child was last RUNNING.

---

## 1. Blackboard Memory (The Main Memory System)

### Setting Initial Values

Define initial state in `blackboard_schema`:

```json
{
  "blackboard_schema": {
    "battery_level": {"type": "int", "default": 100},
    "robot_action": {"type": "string", "default": "idle"},
    "position_x": {"type": "float", "default": 0.0},
    "position_y": {"type": "float", "default": 0.0},
    "target_detected": {"type": "bool", "default": false},
    "sensor_data": {"type": "object", "default": {}}
  },
  "root": { ... }
}
```

### Reading Blackboard Values

**In behavior tree nodes:**
```python
# CheckBlackboardCondition decorator
CheckCondition "battery_level < 20"
  └─ SetVariable "robot_action" = "charge"

# CheckBlackboardVariableExists condition
CheckVariable "target_detected"
  └─ Log "Target found!"
```

**In Python code:**
```python
# Get current state
battery = blackboard.get("battery_level")
action = blackboard.get("robot_action")
```

### Writing Blackboard Values

**From behavior tree:**
```
SetBlackboardVariable
  variable: "robot_action"
  value: "charge"
```

**From external code (the main pattern!):**
```python
# External sensor updates blackboard
blackboard.set("battery_level", robot.get_battery())
blackboard.set("object_distance", sensor.get_distance())
blackboard.set("target_detected", camera.has_target())

# Tree ticks and reads these values
tree.tick()

# External system reads tree's decision
action = blackboard.get("robot_action")
robot.execute(action)
```

### Full Automation Loop

```python
# Initialize
tree = TreeManager.load_tree("robot_controller.json")
blackboard = tree.blackboard_client

# Main loop
while True:
    # 1. External systems update sensor data
    blackboard.set("battery_level", robot.get_battery())
    blackboard.set("object_distance", sensors.get_distance())
    blackboard.set("temperature", sensors.get_temp())

    # 2. Tree decides what to do (reads sensors, sets commands)
    tree.tick()

    # 3. External systems execute commands
    action = blackboard.get("robot_action")
    if action == "charge":
        robot.go_to_charger()
    elif action == "grasp":
        robot.grasp_object()
    elif action == "patrol":
        robot.patrol()

    # 4. Sleep (tree ticks fast, ~60Hz)
    time.sleep(0.016)  # 60 FPS
```

---

## 2. Composite Memory (Execution State)

Controls whether Sequence/Selector **resume** or **restart** when child returns RUNNING.

### Sequence with Memory = True (Default)

**Behavior:** Resumes from last RUNNING child

```json
{
  "node_type": "Sequence",
  "config": {"memory": true},
  "children": [...]
}
```

**Example:**
```
Sequence (memory=true) "Multi-Step Task"
├─ ① CheckBattery       → Returns SUCCESS
├─ ② StartCharging      → Returns RUNNING (still charging)
└─ ③ ResumePatrol       → Not reached yet

Tick 1: Runs ①, ②. Child ② is RUNNING
Tick 2: Resumes at ② (skips ①). Still RUNNING
Tick 3: Child ② returns SUCCESS. Runs ③
```

**Use Case:** Multi-step processes where each step takes time

### Sequence with Memory = False

**Behavior:** Restarts from first child every tick

```json
{
  "node_type": "Sequence",
  "config": {"memory": false},
  "children": [...]
}
```

**Example:**
```
Sequence (memory=false) "Continuous Monitoring"
├─ ① CheckBattery       → Returns SUCCESS
├─ ② CheckTemperature   → Returns RUNNING
└─ ③ Log "All OK"

Tick 1: Runs ①, ②. Child ② is RUNNING
Tick 2: Restarts from ①! Re-checks battery, then temperature
Tick 3: Restarts from ① again...
```

**Use Case:** Conditions that need constant re-checking

### Selector Memory

Same concept - determines if selector re-evaluates higher priority options:

**Memory = True:** Once a child succeeds, stick with it
**Memory = False:** Re-check higher priority options every tick

---

## 3. Node-Level State (Per-Node Memory)

Individual nodes can store state:

```python
class MoveTo(behaviour.Behaviour):
    def initialise(self):
        """Called once when node first ticks"""
        self.start_time = time.time()
        self.distance_traveled = 0.0

    def update(self):
        """Called every tick while node is active"""
        self.distance_traveled += self.calculate_movement()

        if self.reached_target():
            return common.Status.SUCCESS
        return common.Status.RUNNING

    def terminate(self, new_status):
        """Called when node finishes or is interrupted"""
        self.logger.info(f"Traveled {self.distance_traveled}m")
```

---

## 4. Common Patterns

### Pattern 1: Sensor → Tree → Actuator
```python
# Sensors write to blackboard
blackboard.set("battery_level", 15)
blackboard.set("object_distance", 3)

# Tree reads and decides
tree.tick()  # Sets robot_action = "charge"

# Actuators read blackboard
action = blackboard.get("robot_action")
robot.execute(action)
```

### Pattern 2: State Machine
```python
# Tree controls state
Selector
├─ Sequence "Emergency"
│  ├─ CheckCondition "battery < 5"
│  └─ SetVariable "state" = "EMERGENCY"
├─ Sequence "Low Power"
│  ├─ CheckCondition "battery < 20"
│  └─ SetVariable "state" = "LOW_POWER"
└─ SetVariable "state" = "NORMAL"

# External FSM reads state
state = blackboard.get("state")
fsm.transition_to(state)
```

### Pattern 3: Incremental Computation
```python
# Tree updates counter
Sequence
├─ GetVariable "counter"
├─ SetVariable "counter" = counter + 1  # Would need custom node
└─ CheckCondition "counter > 10"
```

---

## 5. Tree Editor Support (Currently Missing!)

**Current limitation:** Tree editor doesn't support editing `blackboard_schema`

**Workaround:** Edit JSON manually or create trees programmatically

**Example tree with initial state:**
```json
{
  "$schema": "1.0.0",
  "tree_id": "robot-controller",
  "metadata": {
    "name": "Robot Controller",
    "version": "1.0.0"
  },
  "blackboard_schema": {
    "battery_level": {"type": "int", "default": 100},
    "robot_action": {"type": "string", "default": "idle"},
    "object_distance": {"type": "float", "default": 999.0}
  },
  "root": {
    "node_type": "Selector",
    "name": "Main Loop",
    "config": {"memory": false},
    "children": [...]
  }
}
```

---

## Summary

| Memory Type | Purpose | Scope | Persistence |
|------------|---------|-------|-------------|
| **Blackboard** | Global state/data | Entire tree | All ticks until manually changed |
| **Composite Memory** | Resume vs restart | Single composite node | Current execution only |
| **Node State** | Per-node data | Single node instance | While node is active |

**Key Insight:** The blackboard IS the memory system. Everything else is just execution control!
