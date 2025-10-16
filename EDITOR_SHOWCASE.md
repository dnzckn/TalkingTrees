# PyForest Professional Editor - Showcase & Guide

## Overview

The PyForest Professional Editor is a production-grade visual tool for creating behavior trees. It features a modern interface with all the tools needed to build, test, and deploy sophisticated automation behaviors.

## Key Features Demonstrated

### 1. Professional Interface
- **Modern Toolbar**: File operations, edit history, view controls, export options
- **Three-Panel Layout**: Node palette, canvas workspace, properties panel
- **Status Bar**: Real-time feedback on tree status and metrics
- **Dark Theme**: Professional VSCode-style appearance

### 2. File Management
- **New/Save/Load**: Full tree lifecycle management
- **Tree Library**: Save and organize multiple trees locally
- **Export to JSON**: Download trees for API deployment
- **API Integration**: Direct upload to PyForest backend

### 3. Editing Tools
- **Undo/Redo**: Full history with Ctrl+Z / Ctrl+Y (up to 50 steps)
- **Validation**: Real-time error checking and warnings
- **Search**: Filter nodes by name, type, or function
- **Auto Layout**: Intelligent tree arrangement algorithm
- **Grid Snap**: Optional alignment to 50px grid

### 4. Visualization
- **Pan & Zoom**: Smooth navigation (mouse wheel, drag, keyboard)
- **Minimap**: Overview of large trees
- **Collapse/Expand**: Hide subtrees for clarity
- **Execution Order**: Visual indicators show sibling order
- **Connection Highlighting**: Clear parent-child relationships

### 5. Keyboard Shortcuts
- `Ctrl+N`: New tree
- `Ctrl+O`: Open tree from library
- `Ctrl+S`: Save to library
- `Ctrl+Z`: Undo
- `Ctrl+Y`: Redo
- `Ctrl+L`: Auto layout
- `Ctrl+G`: Toggle grid
- `Ctrl+V`: Validate tree
- `Ctrl+0`: Zoom to fit
- `+/-`: Zoom in/out
- `Delete`: Delete selected node
- `Escape`: Cancel connection mode

## Example Trees

### Example 1: Robot Controller (Production-Ready)

This is the REAL automation pattern used in test_complete_flow.py. It demonstrates:
- Priority-based decision making (Selector at root)
- Sensor reading via blackboard
- Action commands via SetBlackboardVariable
- Proper memory settings

**Tree Structure:**
```
Selector (memory=false, reactive)
├─ Sequence (memory=true, committed) "Low Battery Handler"
│  ├─ CheckBlackboardCondition "battery_level < 20"
│  └─ SetBlackboardVariable "robot_action = charge"
├─ Sequence (memory=true, committed) "Object Detection"
│  ├─ CheckBlackboardCondition "object_distance < 5"
│  └─ SetBlackboardVariable "robot_action = grasp"
└─ SetBlackboardVariable "robot_action = patrol"
```

**How to Build:**
1. Drag Selector to canvas (this is root)
2. Name it "Robot Controller", set memory=false
3. Drag 3 children:
   - Sequence "Low Battery Handler" (memory=true)
   - Sequence "Object Detection" (memory=true)
   - SetBlackboardVariable "Command: Patrol"
4. For each Sequence:
   - Add CheckBlackboardCondition child
   - Add SetBlackboardVariable child
5. Configure conditions and actions
6. Export and run with: `python test_complete_flow.py`

**Expected Behavior:**
- External system updates: battery_level=15 → tree outputs: robot_action="charge"
- External system updates: battery_level=80, distance=3 → tree outputs: robot_action="grasp"
- External system updates: battery_level=80, distance=999 → tree outputs: robot_action="patrol"

### Example 2: E-commerce Order Processor

**Tree Structure:**
```
Sequence (memory=true) "Order Processor"
├─ CheckBlackboardCondition "order_status == pending"
├─ Selector (memory=false) "Payment & Inventory"
│  ├─ Sequence "Process Payment"
│  │  ├─ SetBlackboardVariable "payment_action = charge_card"
│  │  └─ CheckBlackboardCondition "payment_success == true"
│  └─ SetBlackboardVariable "order_status = payment_failed"
├─ Sequence "Reserve & Ship"
│  ├─ SetBlackboardVariable "inventory_action = reserve_items"
│  ├─ SetBlackboardVariable "shipping_action = create_label"
│  └─ SetBlackboardVariable "order_status = shipped"
└─ SetBlackboardVariable "notification_action = send_confirmation"
```

**Use Case:**
- External e-commerce platform updates blackboard with order data
- Tree decides processing steps
- External platform reads action commands and executes

### Example 3: Game AI - Enemy Behavior

**Tree Structure:**
```
Selector (memory=false) "Enemy AI"
├─ Sequence "Flee if Low Health"
│  ├─ CheckBlackboardCondition "health < 30"
│  └─ SetBlackboardVariable "ai_action = flee"
├─ Sequence "Attack if Player Close"
│  ├─ CheckBlackboardCondition "player_distance < 10"
│  └─ SetBlackboardVariable "ai_action = attack"
├─ Sequence "Chase if Player Visible"
│  ├─ CheckBlackboardCondition "player_visible == true"
│  └─ SetBlackboardVariable "ai_action = chase"
└─ SetBlackboardVariable "ai_action = patrol"
```

**Use Case:**
- Game engine updates: health, player_distance, player_visible
- Tree outputs: ai_action
- Game engine executes the action

## Common Patterns

### 1. Priority Selector (Reactive)
Use when higher priority options should pre-empt lower ones:
```
Selector (memory=false)
├─ High Priority Branch
├─ Medium Priority Branch
└─ Default Fallback
```

### 2. Sequential Steps (Committed)
Use when steps must complete in order:
```
Sequence (memory=true)
├─ Step 1
├─ Step 2
└─ Step 3
```

### 3. Guarded Action
Use decorators to conditionally execute actions:
```
CheckBlackboardCondition "guard_value > 0"
└─ SetBlackboardVariable "protected_action = execute"
```

### 4. Retry with Timeout
Use decorators to add resilience:
```
Timeout (duration=10.0)
└─ Retry (num_tries=3)
    └─ SetBlackboardVariable "network_action = api_call"
```

## Best Practices

### Memory Settings
- **Selector memory=false**: Re-evaluate priorities every tick (safety-critical)
- **Sequence memory=true**: Complete steps in order without restarting

### Action Nodes
- **Use SetBlackboardVariable**: Commands for external systems
- **Avoid Log nodes**: Only for debugging, not production
- **Never block**: Tree should tick fast (~60Hz)

### Tree Structure
- **Single root**: Only one node without parent
- **Decorators have 1 child**: Inverter, Retry, Timeout, CheckCondition
- **Leaves have 0 children**: Actions and conditions

### Validation
- Run validation before export (Ctrl+V)
- Fix all errors, review warnings
- Test with test_complete_flow.py pattern

## Workflow: From Idea to Production

### 1. Design Phase
- Sketch tree structure on paper
- Identify sensor inputs (blackboard reads)
- Identify action outputs (blackboard writes)
- Choose memory settings for composites

### 2. Build Phase
- Open PyForest Professional Editor
- Drag nodes from palette
- Connect with Shift+Click parent → Click child
- Configure properties in right panel
- Use Auto Layout for organization

### 3. Save Phase
- Name your tree (Ctrl+S)
- Add description for library
- Validate tree (Ctrl+V)
- Export JSON for deployment

### 4. Test Phase
- Save to API (☁ button) OR
- Export JSON and load via Python
- Create test script like test_complete_flow.py
- Simulate sensor updates
- Verify action outputs

### 5. Deploy Phase
- Create execution instance via API
- Connect to external automation system
- System updates blackboard (sensors)
- System reads blackboard (actuators)
- Tree ticks continuously

## Example Test Script

```python
import requests

API_BASE = "http://localhost:8000"

# 1. Create tree (or load existing)
tree_id = "your-tree-id-from-api"

# 2. Create execution instance
response = requests.post(f"{API_BASE}/executions/", json={
    "tree_id": tree_id
})
execution_id = response.json()["execution_id"]

# 3. Automation loop
while True:
    # External system reads sensors
    battery = robot.get_battery_level()
    distance = robot.get_object_distance()

    # Update blackboard and tick
    response = requests.post(
        f"{API_BASE}/executions/{execution_id}/tick",
        json={
            "blackboard_updates": {
                "battery_level": battery,
                "object_distance": distance
            }
        }
    )

    # Read action from blackboard
    action = response.json()["snapshot"]["blackboard"]["/robot_action"]

    # Execute action
    if action == "charge":
        robot.go_to_charging_station()
    elif action == "grasp":
        robot.grasp_object()
    elif action == "patrol":
        robot.patrol_area()

    time.sleep(0.1)  # ~10Hz
```

## Advanced Features

### Collapse Large Trees
- Click the numbered badge (top-right of parent)
- Orange badge with + indicates collapsed state
- Expand by clicking again

### Search Nodes
- Use search box in palette/library
- Filter by name, type, or keyword
- Useful for large node catalogs

### Tree Library
- Save multiple trees locally
- Organize by project or use case
- Load and modify existing trees
- Build component library for reuse

### Minimap
- Bottom-right corner shows tree overview
- Blue highlight indicates selected node
- Useful for navigating large trees

## Troubleshooting

### "No root node" error
- Ensure exactly one node has no parent
- Use Sequence or Selector as root
- Validate tree to find orphaned nodes

### Decorator child limit
- Decorators accept exactly 1 child
- Use Sequence/Selector for multiple children
- Check validation results

### Blackboard keys not working
- py_trees uses "/" prefix internally
- In config: use "battery_level"
- In API response: reads as "/battery_level"
- SetBlackboardVariable handles this automatically

### Tree won't export
- Check for root node
- Validate tree structure
- Save to library first
- Check browser console for errors

## Performance Tips

### Large Trees (100+ nodes)
- Use collapse to hide subtrees
- Enable grid snap for alignment
- Use Auto Layout sparingly
- Zoom to fit before editing

### Production Deployment
- Keep trees focused (max 50-100 nodes)
- Break complex logic into multiple trees
- Use tree library for reusable components
- Monitor tick performance (<16ms per tick)

## Next Steps

1. **Try the Examples**: Build one of the example trees manually
2. **Save to Library**: Practice save/load workflow
3. **Export & Test**: Run with test_complete_flow.py
4. **Build Your Own**: Design a tree for your use case
5. **Deploy**: Integrate with your automation system

## Support

- **GitHub**: https://github.com/anthropics/pyforest
- **Docs**: See MEMORY_AND_STATE.md, PRODUCTION_SYSTEM.md
- **API**: localhost:8000/docs for OpenAPI spec

---

**Pro Tip**: The editor auto-saves to browser localStorage. Your work persists across sessions, but use the Library feature for important trees!
