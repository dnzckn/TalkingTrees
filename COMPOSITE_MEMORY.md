# Composite Memory Parameter

## The Critical Memory Setting

**Every Sequence and Selector has a `memory` parameter that controls execution flow!**

From py_trees source code:

```python
# Sequence/Selector constructor
def __init__(self, name: str, memory: bool, children=None):
    self.memory = memory
```

---

## What Memory Does

### Memory = True (Resume from last RUNNING child)

When a child returns RUNNING, **skip** earlier children on next tick.

```python
# py_trees/composites.py line 163-165
elif self.memory and common.Status.RUNNING:
    index = self.children.index(self.current_child)  # Resume here!
```

### Memory = False (Restart from first child)

When a child returns RUNNING, **restart** from first child on next tick.

```python
# py_trees/composites.py line 166-167
elif not self.memory and common.Status.RUNNING:
    self.current_child = self.children[0]  # Start over!
```

---

## Sequence Memory Examples

### Example 1: Multi-Step Task (memory=True)

**Use Case:** Long-running process where you don't want to re-check guards

```
Sequence (memory=TRUE) "Cook Meal"
├─ ① CheckIngredients     → Returns SUCCESS
├─ ② Preheat Oven         → Returns RUNNING (heating up...)
└─ ③ Bake                 → Not reached yet

Tick 1: Runs ①, ②. Child ② is RUNNING (oven heating)
Tick 2: RESUMES at ② (skips ①!). Still RUNNING
Tick 3: RESUMES at ②. Returns SUCCESS. Runs ③
```

**Why memory=True:** Don't want to keep checking ingredients while oven heats!

### Example 2: Guarded Action (memory=False)

**Use Case:** Condition must be true EVERY tick to continue

```
Sequence (memory=FALSE) "Charge Battery"
├─ ① CheckBattery < 100%  → Returns SUCCESS
├─ ② StartCharging        → Returns RUNNING (charging...)
└─ ③ Log "Complete"       → Not reached yet

Tick 1: Runs ①, ②. Child ② is RUNNING (charging)
Tick 2: RESTARTS at ①! Re-checks battery. Still < 100%, runs ②. RUNNING
Tick 3: RESTARTS at ①! Re-checks battery. Now = 100%, returns FAILURE!
         Sequence stops! (child ② interrupted, ③ never runs)
```

**Why memory=False:** Want to stop charging when battery reaches 100%, even mid-execution!

---

## Selector Memory Examples

### Example 1: Priority Lock-In (memory=True)

**Use Case:** Stick with chosen priority until complete

```
Selector (memory=TRUE) "NPC Behavior"
├─ ① Flee (if health < 20%)
├─ ② Attack (if enemy close)
└─ ③ Patrol

Tick 1: Health=50%, enemy close. Runs ①(FAIL), ②(SUCCESS). Locks to ②
Tick 2: Health=15%! But RESUMES at ② (skips ①!). Continues attacking!
Tick 3: Attack still RUNNING. Still locked to ②
Tick 4: Attack completes (SUCCESS). Next tick can re-evaluate
```

**Why memory=True:** Don't switch mid-attack even if health drops!

### Example 2: Continuous Re-Evaluation (memory=False)

**Use Case:** Always check highest priority options

```
Selector (memory=FALSE) "Robot Controller"
├─ ① Emergency Stop (if collision detected)
├─ ② Charge (if battery < 20%)
└─ ③ Work

Tick 1: No collision, battery=50%. Runs ①(FAIL), ②(FAIL), ③(RUNNING)
Tick 2: COLLISION DETECTED! RESTARTS from ①. Returns SUCCESS!
         (interrupts ③, handles emergency immediately!)
```

**Why memory=False:** Higher priority emergencies can interrupt lower priority work!

---

## PyForest Tree JSON

```json
{
  "root": {
    "node_type": "Sequence",
    "name": "Multi-Step Process",
    "config": {
      "memory": true    ← SET THIS!
    },
    "children": [...]
  }
}
```

---

## When to Use Each

| Pattern | Memory | Use Case |
|---------|--------|----------|
| **Long Task** | TRUE | Multi-step process where guards shouldn't re-run |
| **Conditional Guard** | FALSE | Condition must stay true throughout execution |
| **Priority Lock** | TRUE | Stick with chosen option until complete |
| **Reactive Behavior** | FALSE | Re-check higher priorities every tick |

---

## Real-World Examples

### Robot Assembly Line (Sequence memory=TRUE)

```
Sequence (memory=TRUE) "Assemble Widget"
├─ CheckPartsAvailable    → One-time check
├─ PickupPart            → RUNNING (moving arm...)
├─ AlignPart             → RUNNING (adjusting position...)
├─ WeldPart              → RUNNING (welding...)
└─ PlaceInBin            → Final step
```

Don't want to re-check "CheckPartsAvailable" while welding!

### Robot Safety Monitor (Sequence memory=FALSE)

```
Sequence (memory=FALSE) "Safe Operation"
├─ CheckNoCollision      → Must be true EVERY tick
├─ CheckEmergencyStop    → Must be true EVERY tick
└─ ExecuteMovement       → RUNNING (moving...)
```

If collision detected mid-movement, stop immediately!

### Game AI Attack (Selector memory=TRUE)

```
Selector (memory=TRUE) "Combat"
├─ UseSpecialAttack (if energy > 80%)
├─ UseMeleeAttack (if close)
└─ Retreat
```

Once committed to melee attack, don't switch mid-swing!

### Alert System (Selector memory=FALSE)

```
Selector (memory=FALSE) "Monitoring"
├─ CriticalAlert (severity > 9)
├─ Warning (severity > 5)
└─ Normal
```

Must immediately escalate if critical alert comes in!

---

## Summary

**Sequence:**
- **memory=TRUE**: Run through steps without re-checking earlier conditions
- **memory=FALSE**: Re-check conditions every tick (guards remain active)

**Selector:**
- **memory=TRUE**: Lock to chosen priority until complete
- **memory=FALSE**: Re-evaluate priorities every tick (reactive)

**Default in py_trees:**
- Sequence: memory=True
- Selector: memory=False

**Critical Insight:** Memory controls whether behavior is **committed** (memory=TRUE) or **reactive** (memory=FALSE)!
