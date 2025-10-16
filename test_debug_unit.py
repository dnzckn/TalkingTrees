"""Unit test for Phase 3C debug functionality."""

import py_trees
from uuid import uuid4

from py_forest.core.debug import DebugContext
from py_forest.models.debug import StepMode, WatchCondition

print("=" * 60)
print("Phase 3C: Unit Testing Debug Functionality")
print("=" * 60)

# Test 1: DebugContext initialization
print("\n1. Testing DebugContext initialization...")
exec_id = uuid4()
debug_ctx = DebugContext(exec_id)
assert debug_ctx.execution_id == exec_id
assert len(debug_ctx.breakpoints) == 0
assert len(debug_ctx.watches) == 0
assert debug_ctx.step_mode == StepMode.NONE
assert not debug_ctx.is_paused
print("   ✓ DebugContext initialized correctly")

# Test 2: Adding/removing breakpoints
print("\n2. Testing breakpoints...")
node_id = uuid4()
bp = debug_ctx.add_breakpoint(node_id)
assert node_id in debug_ctx.breakpoints
assert bp.enabled
assert bp.hit_count == 0
print(f"   ✓ Breakpoint added at node {node_id}")

# Toggle breakpoint
enabled = debug_ctx.toggle_breakpoint(node_id)
assert not enabled
assert not debug_ctx.breakpoints[node_id].enabled
print("   ✓ Breakpoint toggled off")

enabled = debug_ctx.toggle_breakpoint(node_id)
assert enabled
print("   ✓ Breakpoint toggled on")

# Remove breakpoint
removed = debug_ctx.remove_breakpoint(node_id)
assert removed
assert node_id not in debug_ctx.breakpoints
print("   ✓ Breakpoint removed")

# Test 3: Watch expressions
print("\n3. Testing watch expressions...")
watch = debug_ctx.add_watch("test_key", WatchCondition.CHANGE)
assert "test_key" in debug_ctx.watches
assert watch.enabled
assert watch.condition == WatchCondition.CHANGE
print("   ✓ Watch expression added")

# Toggle watch
enabled = debug_ctx.toggle_watch("test_key")
assert not enabled
print("   ✓ Watch toggled off")

enabled = debug_ctx.toggle_watch("test_key")
assert enabled
print("   ✓ Watch toggled on")

# Remove watch
removed = debug_ctx.remove_watch("test_key")
assert removed
assert "test_key" not in debug_ctx.watches
print("   ✓ Watch removed")

# Test 4: Watch condition evaluation
print("\n4. Testing watch condition evaluation...")
debug_ctx.add_watch("counter", WatchCondition.CHANGE)
debug_ctx.add_watch("threshold", WatchCondition.GREATER, 10)
debug_ctx.add_watch("status", WatchCondition.EQUALS, "ready")

# Initial check - no triggers
event = debug_ctx.check_watches({"counter": 0, "threshold": 5, "status": "init"})
assert event is None
print("   ✓ No watch triggered initially")

# Trigger CHANGE condition
event = debug_ctx.check_watches({"counter": 1, "threshold": 5, "status": "init"})
assert event is not None
assert event.key == "counter"
assert debug_ctx.is_paused  # Watch should pause execution
print("   ✓ CHANGE watch triggered")

# Reset pause
debug_ctx.resume()
assert not debug_ctx.is_paused

# Trigger GREATER condition
event = debug_ctx.check_watches({"counter": 1, "threshold": 15, "status": "init"})
assert event is not None
assert event.key == "threshold"
print("   ✓ GREATER watch triggered")

# Reset pause and clear watches for cleaner test
debug_ctx.resume()
debug_ctx.watches.clear()

# Add just the EQUALS watch
debug_ctx.add_watch("status", WatchCondition.EQUALS, "ready")
debug_ctx.last_watch_values = {"status": "init"}  # Set last value

# Trigger EQUALS condition
event = debug_ctx.check_watches({"status": "ready"})
assert event is not None
assert event.key == "status"
print("   ✓ EQUALS watch triggered")

# Test 5: Step modes
print("\n5. Testing step modes...")
debug_ctx.set_step_mode(StepMode.STEP_OVER, 3)
assert debug_ctx.step_mode == StepMode.STEP_OVER
assert debug_ctx.step_count == 3
assert debug_ctx.steps_remaining == 3
print("   ✓ STEP_OVER mode set with count=3")

debug_ctx.set_step_mode(StepMode.STEP_INTO)
assert debug_ctx.step_mode == StepMode.STEP_INTO
print("   ✓ STEP_INTO mode set")

debug_ctx.set_step_mode(StepMode.NONE)
assert debug_ctx.step_mode == StepMode.NONE
print("   ✓ Step mode cleared")

# Test 6: Breakpoint condition evaluation
print("\n6. Testing breakpoint with condition...")
node_id = uuid4()
debug_ctx.add_breakpoint(node_id, "status == 'SUCCESS'")

# Create a mock node
node = py_trees.behaviours.Success(name="TestNode")
node.status = py_trees.common.Status.SUCCESS

# Should break when condition is true
blackboard = {}
should_break = debug_ctx.should_break_at_node(node_id, node, blackboard)
assert should_break
assert debug_ctx.breakpoints[node_id].hit_count == 1
print("   ✓ Conditional breakpoint triggered when condition is true")

# Change status and test again
node.status = py_trees.common.Status.RUNNING
debug_ctx.breakpoints[node_id].hit_count = 0  # Reset
should_break = debug_ctx.should_break_at_node(node_id, node, blackboard)
assert not should_break
assert debug_ctx.breakpoints[node_id].hit_count == 0
print("   ✓ Conditional breakpoint not triggered when condition is false")

# Test 7: Pause/resume
print("\n7. Testing pause/resume...")
debug_ctx.pause(node_id)
assert debug_ctx.is_paused
assert debug_ctx.paused_at_node == node_id
print(f"   ✓ Execution paused at node {node_id}")

debug_ctx.resume()
assert not debug_ctx.is_paused
assert debug_ctx.paused_at_node is None
print("   ✓ Execution resumed")

# Test 8: Get debug state
print("\n8. Testing debug state retrieval...")
# Clear previous state for clean test
debug_ctx.breakpoints.clear()
debug_ctx.watches.clear()
debug_ctx.resume()

# Add some debug items
debug_ctx.add_breakpoint(uuid4())
debug_ctx.add_breakpoint(uuid4())
debug_ctx.add_watch("test1", WatchCondition.CHANGE)
debug_ctx.add_watch("test2", WatchCondition.EQUALS, "value")

state = debug_ctx.get_state()
assert state.execution_id == exec_id
assert len(state.breakpoints) == 2
assert len(state.watches) == 2
print("   ✓ Debug state retrieved correctly")
print(f"   - Breakpoints: {len(state.breakpoints)}")
print(f"   - Watches: {len(state.watches)}")
print(f"   - Breakpoint hits: {state.breakpoint_hits}")
print(f"   - Watch hits: {state.watch_hits}")

# Test 9: Clear all
print("\n9. Testing clear all...")
debug_ctx.clear_all()
assert len(debug_ctx.breakpoints) == 0
assert len(debug_ctx.watches) == 0
assert not debug_ctx.is_paused
assert debug_ctx.step_mode == StepMode.NONE
print("   ✓ All debug state cleared")

print("\n" + "=" * 60)
print("✓ All Phase 3C debug unit tests passed!")
print("=" * 60)
