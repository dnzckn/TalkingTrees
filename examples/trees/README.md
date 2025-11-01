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

### 09_day_in_life_sim.json
Complex simulation of a person's daily routine.
- **Concepts**: State machines, time management, resource tracking (hunger, thirst, energy, stress)
- **Use case**: Life simulation, complex state management
- **Features**: Morning, work, and evening phases with realistic decision-making

### 10_guard_patrol_game.json
Interactive 2D grid game with NPC guard behavior.
- **Concepts**: Patrol patterns, investigation, chase logic, grid-based movement
- **Use case**: Game AI, interactive demos
- **Features**: Visual grid interface, real-time behavior execution

### 11_ultra_complex.json
**🚀 Comprehensive demo showcasing ALL major node types**
- **Concepts**: Timeout, Retry, Repeat, OneShot, Inverter, SuccessIsFailure, FailureIsSuccess, Parallel, complex blackboard operations
- **Use case**: Learning advanced patterns, testing GUI capabilities
- **Features**:
  - Emergency handling with timeout & inverter
  - Retry & repeat patterns
  - Parallel sensor processing
  - OneShot maintenance mode
  - Status converter chains
  - Deep nesting (5+ levels)
  - 30+ nodes total
- **Perfect for**: Exploring the visual editor's full 40+ node type support

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
