# PyForest Automation Patterns

## Core Principle: Behavior Tree is a Traffic Controller

**CRITICAL: The behavior tree should NEVER block or stall!**

- Behavior tree ticks fast (~60Hz or faster)
- Each node returns immediately (SUCCESS/FAILURE/RUNNING)
- If a task takes time, return RUNNING and check status next tick
- External systems do the actual work
- **Behavior tree = decision maker, NOT task executor**

### Bad (Blocking):
```python
def update(self):
    robot.move_to(x, y)  # ❌ BLOCKS for 5 seconds!
    return SUCCESS
```

### Good (Non-blocking):
```python
def initialise(self):
    robot.start_move(x, y)  # Issue command, don't wait

def update(self):
    if robot.is_done():
        return SUCCESS
    return RUNNING  # Check again next tick
```

### Best (Pure state machine):
```python
def update(self):
    blackboard.set("robot_action", "move")  # Just set state
    blackboard.set("target", (x, y))
    return SUCCESS  # Done immediately!
```

External loop reads blackboard and executes:
```python
while True:
    tree.tick()  # Fast! Never blocks!
    action = blackboard.get("robot_action")
    robot.execute(action)  # External system does work
```

---

## The Problem with "Log as Final Action"

**Bad Pattern (Just for debugging):**
```
Sequence
├─ CheckHungry
└─ Log "Eating"  ← Does NOTHING in real world!
```

**Good Patterns for Real Automation:**

## Pattern 1: Set Blackboard Variables (External Control)

The behavior tree sets variables that external systems read and act upon.

```
Selector "Robot Controller"
├─ Sequence "If Battery Low"
│  ├─ CheckCondition "battery < 20"
│  └─ SetBlackboardVariable "robot_action" = "charge"  ← External robot reads this!
├─ Sequence "If Object Detected"
│  ├─ CheckCondition "distance < 5"
│  └─ SetBlackboardVariable "robot_action" = "grasp"
└─ SetBlackboardVariable "robot_action" = "patrol"  ← Default
```

**External Code:**
```python
# Main loop reads blackboard
tree.tick()
action = blackboard.get("robot_action")
if action == "charge":
    robot.charge_battery()
elif action == "grasp":
    robot.grasp_object()
elif action == "patrol":
    robot.patrol()
```

## Pattern 2: State Machine Control

Behavior tree controls a state machine.

```
Selector "Game AI"
├─ Sequence "If Enemy Close"
│  ├─ CheckCondition "enemy_distance < 10"
│  └─ SetBlackboardVariable "state" = "ATTACK"
├─ Sequence "If Health Low"
│  ├─ CheckCondition "health < 30"
│  └─ SetBlackboardVariable "state" = "FLEE"
└─ SetBlackboardVariable "state" = "PATROL"
```

## Pattern 3: API/Workflow Automation

```
Sequence "Process Order"
├─ CheckCondition "order_total > 100"
├─ SetBlackboardVariable "discount" = 0.1
├─ SetBlackboardVariable "priority" = "high"
└─ SetBlackboardVariable "notification" = "send_email"
```

## Pattern 4: Multi-System Coordination

```
Parallel "Coordinate Systems"
├─ SetBlackboardVariable "motors" = "forward"
├─ SetBlackboardVariable "camera" = "recording"
└─ SetBlackboardVariable "sensors" = "active"
```

## Real-World Use Cases

### 1. Robotics
```
Selector "Assembly Line Robot"
├─ Sequence "Quality Check Failed"
│  ├─ CheckCondition "defect_detected == true"
│  ├─ SetBlackboardVariable "conveyor_action" = "stop"
│  └─ SetBlackboardVariable "alert_type" = "quality_issue"
├─ Sequence "Part Ready"
│  ├─ CheckCondition "part_present == true"
│  ├─ SetBlackboardVariable "arm_action" = "pick"
│  └─ SetBlackboardVariable "conveyor_action" = "advance"
└─ SetBlackboardVariable "status" = "waiting"
```

### 2. Game AI
```
Selector "NPC Behavior"
├─ Sequence "Combat"
│  ├─ CheckCondition "player_distance < 15"
│  ├─ CheckCondition "has_weapon == true"
│  └─ SetBlackboardVariable "animation" = "attack"
├─ Sequence "Investigate"
│  ├─ CheckCondition "heard_noise == true"
│  └─ SetBlackboardVariable "move_target" = "noise_position"
└─ SetBlackboardVariable "animation" = "idle"
```

### 3. DevOps Automation
```
Sequence "Deployment Pipeline"
├─ CheckCondition "tests_passing == true"
├─ CheckCondition "cpu_usage < 70"
├─ SetBlackboardVariable "deploy_environment" = "production"
├─ SetBlackboardVariable "rollback_enabled" = true
└─ SetBlackboardVariable "notification_channel" = "slack"
```

### 4. Smart Home
```
Selector "Climate Control"
├─ Sequence "Too Hot"
│  ├─ CheckCondition "temperature > 75"
│  ├─ SetBlackboardVariable "ac_mode" = "cool"
│  └─ SetBlackboardVariable "fan_speed" = "high"
├─ Sequence "Too Cold"
│  ├─ CheckCondition "temperature < 65"
│  └─ SetBlackboardVariable "heater_mode" = "on"
└─ SetBlackboardVariable "climate_mode" = "eco"
```

## Why This Works

1. **Separation of Concerns**: Behavior tree handles LOGIC, external systems handle ACTIONS
2. **Testable**: Can verify blackboard state without needing real hardware
3. **Flexible**: Same tree works with different actuators (real robot vs simulator)
4. **Debuggable**: Can inspect blackboard to see what tree decided
5. **Composable**: Multiple trees can set different variables

## Future: Custom Action Nodes

For direct action execution (not just blackboard):

```python
class HTTPRequest(behaviour.Behaviour):
    def update(self):
        response = requests.post(self.url, json=self.payload)
        self.blackboard.set("response_status", response.status_code)
        return common.Status.SUCCESS

class MoveRobot(behaviour.Behaviour):
    def update(self):
        self.robot_controller.move_to(self.x, self.y, self.z)
        return common.Status.RUNNING  # Until position reached
```

But for most automation, **SetBlackboardVariable is the right pattern!**
