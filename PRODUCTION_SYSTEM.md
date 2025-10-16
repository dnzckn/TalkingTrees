# PyForest Production System Design

## Executive Summary

**Core Question:** How would users build and deploy automation behaviors in a production system?

**Answer:** PyForest needs to evolve from a development tool into a **full-stack behavior tree platform** with:
1. Professional visual editor (pan/zoom, collapse, library)
2. Reusable component system (tree library)
3. Multi-user collaboration (workspaces, permissions)
4. Deployment pipeline (dev → staging → prod)
5. Monitoring and observability

---

## 1. Visual Editor Improvements

### Current Issues:
- ❌ Can't handle large trees (no zoom, no collapse)
- ❌ No way to reuse common patterns
- ❌ Canvas is fixed, can't navigate
- ❌ No keyboard shortcuts
- ❌ No undo/redo

### Production Requirements:

#### A. Canvas Navigation
```
Features:
- Pan: Drag canvas with middle mouse or spacebar+drag
- Zoom: Scroll wheel to zoom in/out (10% - 500%)
- Zoom to fit: Auto-frame entire tree
- Minimap: Bird's-eye view with viewport indicator
```

#### B. Node Collapse/Expand
```
Features:
- Click badge to collapse children: [+3] indicates 3 hidden children
- Collapsed nodes show child count and status summary
- Recursive collapse: Collapse entire subtree
- Expand all: Keyboard shortcut to expand everything
```

#### C. Tree Library Panel
```
Features:
- Left sidebar with reusable components
- Categories: Robotics, Game AI, DevOps, Utilities
- Drag from library to canvas to instantiate
- Preview: Hover to see tree structure
- Search: Filter by name/description
```

#### D. Keyboard Shortcuts
```
Shortcuts:
- Delete: Remove selected node
- Ctrl+C/V: Copy/paste subtree
- Ctrl+Z/Y: Undo/redo
- Ctrl+D: Duplicate node
- Space: Toggle collapse/expand
- F: Zoom to fit
- Ctrl+F: Search nodes
```

#### E. Enhanced Properties Panel
```
Features:
- Visual config editors (sliders, color picker, dropdowns)
- Blackboard variable autocomplete
- Validation: Show errors inline
- Help tooltips for each config option
- Memory parameter toggle (for composites)
```

---

## 2. Tree Library System

### Component Model

```typescript
interface TreeComponent {
  id: string;
  name: string;
  description: string;
  category: string;  // "robotics", "game-ai", "devops", etc.
  tags: string[];
  version: string;
  author: string;

  // Tree structure (subtree JSON)
  tree: TreeNode;

  // Parameters (customizable values)
  parameters: {
    name: string;
    type: "int" | "float" | "string" | "bool";
    default: any;
    description: string;
  }[];

  // Blackboard requirements
  requires_variables: string[];  // Must exist in blackboard
  provides_variables: string[];  // Sets these variables

  // Metadata
  thumbnail?: string;  // Preview image
  documentation_url?: string;
  created_at: string;
  updated_at: string;
}
```

### Example Components

#### 1. Low Battery Handler
```json
{
  "name": "Low Battery Handler",
  "category": "robotics",
  "parameters": [
    {"name": "threshold", "type": "int", "default": 20},
    {"name": "action_name", "type": "string", "default": "charge"}
  ],
  "requires_variables": ["battery_level"],
  "provides_variables": ["robot_action"],
  "tree": {
    "node_type": "Sequence",
    "config": {"memory": true},
    "children": [
      {
        "node_type": "CheckBlackboardCondition",
        "config": {
          "variable": "battery_level",
          "operator_str": "<",
          "value": "{{threshold}}"  // Parameter placeholder
        }
      },
      {
        "node_type": "SetBlackboardVariable",
        "config": {
          "variable": "robot_action",
          "value": "{{action_name}}"  // Parameter placeholder
        }
      }
    ]
  }
}
```

#### 2. Retry Pattern
```json
{
  "name": "Retry with Exponential Backoff",
  "category": "utilities",
  "parameters": [
    {"name": "max_retries", "type": "int", "default": 3},
    {"name": "initial_delay", "type": "float", "default": 1.0}
  ],
  "tree": {
    "node_type": "Retry",
    "config": {
      "num_failures": "{{max_retries}}",
      "backoff": "exponential"
    },
    "children": [
      {
        "node_type": "Placeholder",
        "name": "Your Action Here"
      }
    ]
  }
}
```

### Library Storage

```
File structure:
/library/
  robotics/
    low_battery_handler.json
    collision_avoidance.json
    multi_step_navigation.json
  game_ai/
    npc_behavior.json
    combat_system.json
  devops/
    deployment_pipeline.json
    health_check.json
  utilities/
    retry_pattern.json
    timeout_wrapper.json
```

---

## 3. Multi-User Collaboration

### Architecture

```
Frontend (Tree Editor)
    ↓
API Gateway
    ↓
┌─────────────────────────────────┐
│  PyForest Backend Service       │
│  - User Management              │
│  - Tree Storage (PostgreSQL)    │
│  - Execution Engine             │
│  - WebSocket Server (real-time) │
└─────────────────────────────────┘
    ↓
External Systems
    - Robots, APIs, etc.
```

### Database Schema

```sql
-- Users and workspaces
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE,
  name TEXT,
  created_at TIMESTAMP
);

CREATE TABLE workspaces (
  id UUID PRIMARY KEY,
  name TEXT,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMP
);

CREATE TABLE workspace_members (
  workspace_id UUID REFERENCES workspaces(id),
  user_id UUID REFERENCES users(id),
  role TEXT,  -- 'owner', 'editor', 'viewer'
  PRIMARY KEY (workspace_id, user_id)
);

-- Trees and versions
CREATE TABLE trees (
  id UUID PRIMARY KEY,
  workspace_id UUID REFERENCES workspaces(id),
  name TEXT,
  description TEXT,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE tree_versions (
  id UUID PRIMARY KEY,
  tree_id UUID REFERENCES trees(id),
  version INTEGER,
  tree_json JSONB,  -- Full tree definition
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMP,
  commit_message TEXT
);

-- Deployments
CREATE TABLE deployments (
  id UUID PRIMARY KEY,
  tree_version_id UUID REFERENCES tree_versions(id),
  environment TEXT,  -- 'dev', 'staging', 'prod'
  status TEXT,  -- 'deploying', 'active', 'stopped', 'failed'
  deployed_by UUID REFERENCES users(id),
  deployed_at TIMESTAMP
);

-- Execution logs
CREATE TABLE execution_logs (
  id UUID PRIMARY KEY,
  deployment_id UUID REFERENCES deployments(id),
  tick_timestamp TIMESTAMP,
  tree_status TEXT,  -- 'SUCCESS', 'FAILURE', 'RUNNING'
  blackboard_snapshot JSONB,
  node_statuses JSONB  -- All node statuses at this tick
);

-- Tree library
CREATE TABLE library_components (
  id UUID PRIMARY KEY,
  name TEXT,
  category TEXT,
  description TEXT,
  component_json JSONB,
  is_public BOOLEAN,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMP
);
```

---

## 4. REST API Design

### Tree Management

```
# List trees in workspace
GET /api/workspaces/{workspace_id}/trees

# Create new tree
POST /api/workspaces/{workspace_id}/trees
{
  "name": "Robot Controller",
  "tree_json": {...}
}

# Get tree
GET /api/trees/{tree_id}

# Update tree (creates new version)
PUT /api/trees/{tree_id}
{
  "tree_json": {...},
  "commit_message": "Added low battery handler"
}

# Get tree versions
GET /api/trees/{tree_id}/versions

# Deploy tree
POST /api/trees/{tree_id}/deploy
{
  "environment": "staging",
  "version": 5
}
```

### Execution API

```
# Tick a deployed tree
POST /api/deployments/{deployment_id}/tick
{
  "blackboard_updates": {
    "battery_level": 15,
    "sensor_distance": 3.5
  }
}
Response:
{
  "status": "RUNNING",
  "blackboard": {
    "robot_action": "charge",
    "battery_level": 15
  }
}

# Get execution status
GET /api/deployments/{deployment_id}/status

# Get execution logs
GET /api/deployments/{deployment_id}/logs?limit=100
```

### Library API

```
# List library components
GET /api/library?category=robotics

# Get component
GET /api/library/{component_id}

# Create component (save subtree to library)
POST /api/library
{
  "name": "Custom Pattern",
  "category": "utilities",
  "tree_json": {...}
}
```

---

## 5. External System Integration

### Pattern 1: HTTP Polling (Simple)

```python
import requests
import time

deployment_id = "abc-123"
api_url = "https://pyforest.example.com/api"

while True:
    # Update blackboard with sensor data
    response = requests.post(
        f"{api_url}/deployments/{deployment_id}/tick",
        json={
            "blackboard_updates": {
                "battery_level": robot.get_battery(),
                "object_distance": sensors.get_distance()
            }
        }
    )

    # Execute tree's decision
    action = response.json()["blackboard"]["robot_action"]
    robot.execute(action)

    time.sleep(0.016)  # 60Hz
```

### Pattern 2: WebSocket (Real-time)

```python
import websocket
import json

def on_message(ws, message):
    data = json.loads(message)

    if data["type"] == "tree_status":
        action = data["blackboard"]["robot_action"]
        robot.execute(action)

ws = websocket.WebSocketApp(
    "wss://pyforest.example.com/ws/deployments/abc-123",
    on_message=on_message
)

# Send sensor updates
def send_sensors():
    while True:
        ws.send(json.dumps({
            "type": "blackboard_update",
            "data": {
                "battery_level": robot.get_battery(),
                "object_distance": sensors.get_distance()
            }
        }))
        time.sleep(0.016)

threading.Thread(target=send_sensors).start()
ws.run_forever()
```

### Pattern 3: Embedded (Local execution)

```python
from py_forest.core.tree_manager import TreeManager

# Load tree from file or API
tree_json = requests.get(f"{api_url}/trees/{tree_id}").json()
manager = TreeManager()
tree_id = manager.create_tree_from_dict(tree_json)
tree = manager.get_tree(tree_id)

# Local execution loop
while True:
    # Update blackboard
    tree.blackboard.set("battery_level", robot.get_battery())

    # Tick tree
    tree.tick_once()

    # Execute action
    action = tree.blackboard.get("robot_action")
    robot.execute(action)

    time.sleep(0.016)
```

---

## 6. Monitoring and Observability

### Metrics to Track

```
Tree-level:
- Execution time per tick (avg, p95, p99)
- Success rate (% ticks that return SUCCESS)
- Most frequently executed branches
- Node failure rates

Node-level:
- How often each node is ticked
- Success/failure/running distribution
- Average execution time

Blackboard:
- Variable read/write frequency
- Variable value distributions
```

### Visualization Dashboard

```
Real-time view:
- Tree structure with highlighted active nodes
- Current blackboard state
- Execution timeline (ticks over time)
- Status history (SUCCESS/FAILURE/RUNNING chart)

Historical view:
- Execution traces (replay past ticks)
- Performance graphs
- Error logs
- Blackboard variable trends
```

---

## 7. Deployment Pipeline

### Environments

```
Development:
- Local tree editor
- Test against simulator
- Rapid iteration

Staging:
- Deploy to staging environment
- Integration tests with real systems
- A/B testing

Production:
- Blue-green deployment
- Gradual rollout (canary)
- Automatic rollback on errors
```

### Deployment Flow

```
1. Developer saves tree in editor
   ↓
2. Tree validation (schema check, blackboard variables)
   ↓
3. Unit tests (test individual subtrees)
   ↓
4. Deploy to staging
   ↓
5. Integration tests (test with real systems)
   ↓
6. Manual approval or auto-deploy
   ↓
7. Deploy to production (canary)
   ↓
8. Monitor metrics, rollback if needed
```

---

## 8. Testing Framework

### Unit Tests (Subtree level)

```python
def test_low_battery_handler():
    """Test that low battery triggers charge action."""
    tree_json = load_component("low_battery_handler")
    manager = TreeManager()
    tree_id = manager.create_tree_from_dict(tree_json)
    tree = manager.get_tree(tree_id)

    # Set battery low
    tree.blackboard.set("battery_level", 10)

    # Tick tree
    tree.tick_once()

    # Assert action is set
    assert tree.blackboard.get("robot_action") == "charge"
```

### Integration Tests

```python
def test_robot_controller_integration():
    """Test full robot controller with simulated robot."""
    robot_sim = RobotSimulator()
    tree = load_tree("robot_controller.json")

    # Simulate low battery
    robot_sim.battery = 10
    tree.blackboard.set("battery_level", robot_sim.battery)
    tree.tick_once()

    # Verify robot received charge command
    action = tree.blackboard.get("robot_action")
    assert action == "charge"

    # Simulate charging
    for _ in range(10):
        robot_sim.charge()
        tree.blackboard.set("battery_level", robot_sim.battery)
        tree.tick_once()

    # Verify robot resumes patrol
    action = tree.blackboard.get("robot_action")
    assert action == "patrol"
```

---

## 9. Implementation Roadmap

### Phase 1: Editor Improvements (1-2 weeks)
- ✅ Pan & zoom canvas
- ✅ Collapse/expand nodes
- ✅ Minimap
- ✅ Keyboard shortcuts
- ✅ Better properties panel

### Phase 2: Tree Library (1 week)
- ✅ Component model
- ✅ Save/load components
- ✅ Library panel in editor
- ✅ Parameterizable components
- ✅ Example library

### Phase 3: Backend API (2 weeks)
- ✅ FastAPI backend (already exists!)
- ✅ Database integration
- ✅ User authentication
- ✅ Tree CRUD operations
- ✅ Execution API

### Phase 4: Deployment (1-2 weeks)
- ✅ Multi-environment support
- ✅ Version management
- ✅ Deployment API
- ✅ Rollback mechanism

### Phase 5: Monitoring (1 week)
- ✅ Execution logging
- ✅ Metrics collection
- ✅ Visualization dashboard
- ✅ Alerting

### Phase 6: Collaboration (2 weeks)
- ✅ Workspaces
- ✅ Real-time collaboration
- ✅ Comments and annotations
- ✅ Change history

---

## 10. Production Example: E-commerce Automation

### Use Case
Automate order processing with dynamic business rules.

### Tree Structure
```
Selector "Order Processor"
├─ Sequence "High Value Order"
│  ├─ CheckCondition "order_total > 1000"
│  ├─ SetVariable "priority" = "high"
│  ├─ SetVariable "discount" = 0.15
│  └─ SetVariable "notification" = "alert_manager"
├─ Sequence "Returning Customer"
│  ├─ CheckCondition "customer_orders > 5"
│  ├─ SetVariable "priority" = "medium"
│  └─ SetVariable "discount" = 0.10
└─ Sequence "Standard Order"
   ├─ SetVariable "priority" = "normal"
   └─ SetVariable "discount" = 0.0
```

### Integration Code
```python
# Order processor service
from py_forest.api import PyForestClient

client = PyForestClient(api_url="https://pyforest.company.com")
deployment_id = "order-processor-prod"

@app.post("/orders")
def process_order(order: Order):
    # Update blackboard with order data
    response = client.tick_tree(
        deployment_id,
        blackboard_updates={
            "order_total": order.total,
            "customer_orders": order.customer.order_count,
            "inventory_available": check_inventory(order)
        }
    )

    # Read tree's decision
    priority = response["blackboard"]["priority"]
    discount = response["blackboard"]["discount"]

    # Apply business logic
    order.priority = priority
    order.discount = discount

    # Log for monitoring
    logger.info(f"Processed order {order.id}: priority={priority}, discount={discount}")

    return {"status": "processed", "order": order}
```

### Benefits
- ✅ Business rules are visual and editable by non-programmers
- ✅ Changes don't require code deployment
- ✅ A/B test different pricing strategies
- ✅ Monitor rule effectiveness in real-time
- ✅ Version control for business logic

---

## Summary

**PyForest as a Production Platform requires:**

1. **Professional Editor:** Pan/zoom, collapse, library, shortcuts
2. **Component System:** Reusable, parameterizable subtrees
3. **Backend API:** Tree management, execution, monitoring
4. **Deployment Pipeline:** Dev → staging → prod with testing
5. **Multi-User:** Workspaces, permissions, collaboration
6. **Monitoring:** Execution traces, metrics, dashboards

**Next Steps:**
1. Upgrade tree editor (Phase 1)
2. Build tree library system (Phase 2)
3. Enhance API backend (Phase 3)

**The Vision:**
PyForest becomes the "Figma for automation" - a visual platform where teams collaboratively build, test, and deploy behavior trees for any domain.
