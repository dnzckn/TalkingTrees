# TalkingTrees Example Trees

This directory contains example behavior trees demonstrating various patterns and features of TalkingTrees.

## Examples

### 01_simple_sequence.json
Basic sequence that executes actions in order. Good starting point for understanding behavior trees.
- **Concepts**: Sequence composite
- **Use case**: Step-by-step execution

### 02_simple_selector.json
Selector that tries children until one succeeds. Demonstrates fallback logic.
- **Concepts**: Selector composite, CheckBattery behavior
- **Use case**: Decision making with fallbacks

### 03_retry_pattern.json
Demonstrates retry decorator for handling transient failures.
- **Concepts**: Retry decorator, error handling
- **Use case**: Robust task execution

### 04_parallel_tasks.json
Concurrent execution of multiple tasks.
- **Concepts**: Parallel composite
- **Use case**: Simultaneous operations

### 05_patrol_robot.json
Realistic robot patrol behavior with battery management.
- **Concepts**: Complex logic, blackboard usage, state management
- **Use case**: Autonomous robot behavior

### 06_debug_showcase.json
Designed to demonstrate debugging features.
- **Concepts**: Breakpoints, watches, step execution
- **Use case**: Learning debugging tools
- **Try**: Set breakpoints, watch 'counter' variable, use step modes

### 07_game_ai.json
Game NPC AI with combat and exploration modes.
- **Concepts**: Priority-based decisions, state machines
- **Use case**: Game AI behavior

### 08_stress_test.json
Large tree for performance testing.
- **Concepts**: Many nodes, deep nesting, parallel execution
- **Use case**: Performance benchmarking

## Using Examples

### Load via API
```bash
# Upload to library
curl -X POST http://localhost:8000/trees/ \
  -H "Content-Type: application/json" \
  -d @01_simple_sequence.json

# Execute
curl -X POST http://localhost:8000/executions/ \
  -H "Content-Type: application/json" \
  -d '{"tree_id": "TREE_ID_HERE"}'
```

### Validate Examples
```bash
# Validate tree structure
curl -X POST http://localhost:8000/validation/trees \
  -H "Content-Type: application/json" \
  -d @01_simple_sequence.json
```

### Debug Examples
Use `06_debug_showcase.json` to practice debugging:
1. Create execution
2. Add breakpoint at "Initialize" node
3. Add watch on "counter" variable
4. Use step modes to walk through execution

## Creating Your Own

Use these examples as templates for your own trees. Key patterns:
- **Sequence**: Execute actions in order (all must succeed)
- **Selector**: Try actions until one succeeds (fallback logic)
- **Parallel**: Execute multiple branches concurrently
- **Decorators**: Modify child behavior (Retry, Inverter, etc.)
