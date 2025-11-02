# TalkingTrees API Reference

Complete reference for TalkingTrees REST API. The API provides 47 endpoints across 7 routers.

## Base URL

```
http://localhost:8000
```

## Interactive Documentation

View interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Table of Contents

1. [Trees Router](#trees-router) - 7 endpoints
2. [Behaviors Router](#behaviors-router) - 3 endpoints
3. [Executions Router](#executions-router) - 10 endpoints
4. [History Router](#history-router) - 4 endpoints
5. [Debug Router](#debug-router) - 10 endpoints
6. [Visualization Router](#visualization-router) - 5 endpoints
7. [Validation Router](#validation-router) - 7 endpoints
8. [WebSocket](#websocket) - 1 endpoint
9. [Error Handling](#error-handling)
10. [Rate Limiting](#rate-limiting)

---

## Trees Router

Manage behavior tree library.

### List All Trees

```http
GET /trees/
```

**Response 200**:
```json
[
  {
    "tree_id": "uuid-here",
    "metadata": {
      "name": "Simple Patrol",
      "version": "1.0.0",
      "description": "Basic patrol behavior",
      "tags": ["robot", "patrol"],
      "author": "John Doe",
      "created_at": "2024-01-01T00:00:00Z"
    },
    "root": { ... }
  }
]
```

### Get Tree by ID

```http
GET /trees/{tree_id}
```

**Parameters**:
- `tree_id` (path, required): UUID of the tree
- `version` (query, optional): Specific version to retrieve

**Response 200**:
```json
{
  "tree_id": "uuid-here",
  "$schema": "1.0.0",
  "metadata": { ... },
  "root": { ... },
  "blackboard_schema": { ... }
}
```

**Response 404**:
```json
{
  "detail": "Tree not found"
}
```

### Create Tree

```http
POST /trees/
```

**Request Body**:
```json
{
  "$schema": "1.0.0",
  "metadata": {
    "name": "My Tree",
    "version": "1.0.0",
    "description": "Description here",
    "tags": ["tag1", "tag2"]
  },
  "root": {
    "node_type": "Sequence",
    "name": "Root",
    "config": {},
    "children": []
  }
}
```

**Response 201**:
```json
{
  "tree_id": "generated-uuid",
  ...
}
```

### Update Tree

```http
PUT /trees/{tree_id}
```

**Parameters**:
- `tree_id` (path, required): UUID of the tree

**Request Body**: Same as Create Tree

**Response 200**:
```json
{
  "tree_id": "uuid-here",
  "metadata": {
    "version": "1.1.0"  // Version incremented
  },
  ...
}
```

### Delete Tree

```http
DELETE /trees/{tree_id}
```

**Parameters**:
- `tree_id` (path, required): UUID of the tree
- `version` (query, optional): Specific version to delete (omit to delete all versions)

**Response 204**: No content

**Response 404**:
```json
{
  "detail": "Tree not found"
}
```

### Search Trees

```http
GET /trees/search
```

**Parameters**:
- `name` (query, optional): Filter by name (substring match)
- `tags` (query, optional): Comma-separated tags
- `description` (query, optional): Filter by description (substring match)

**Response 200**:
```json
[
  {
    "tree_id": "uuid-here",
    "metadata": { ... }
  }
]
```

### Get Tree Versions

```http
GET /trees/{tree_id}/versions
```

**Parameters**:
- `tree_id` (path, required): UUID of the tree

**Response 200**:
```json
[
  {
    "version": "1.0.0",
    "created_at": "2024-01-01T00:00:00Z"
  },
  {
    "version": "1.1.0",
    "created_at": "2024-01-02T00:00:00Z"
  }
]
```

---

## Behaviors Router

Query available behavior types.

### List All Behaviors

```http
GET /behaviors/
```

**Response 200**:
```json
[
  {
    "name": "Sequence",
    "type": "composite",
    "description": "Execute children in order until one fails",
    "parameters": []
  },
  {
    "name": "Log",
    "type": "action",
    "description": "Log a message",
    "parameters": [
      {
        "name": "message",
        "type": "string",
        "required": true,
        "description": "Message to log"
      }
    ]
  }
]
```

### Get Behavior by Name

```http
GET /behaviors/{behavior_name}
```

**Parameters**:
- `behavior_name` (path, required): Name of the behavior

**Response 200**:
```json
{
  "name": "Retry",
  "type": "decorator",
  "description": "Retry child behavior on failure",
  "parameters": [
    {
      "name": "num_attempts",
      "type": "int",
      "required": true,
      "description": "Number of retry attempts",
      "default": 3
    }
  ],
  "allows_children": true,
  "requires_children": true,
  "max_children": 1
}
```

**Response 404**:
```json
{
  "detail": "Behavior 'UnknownBehavior' not found"
}
```

### Get Behavior Schema

```http
GET /behaviors/{behavior_name}/schema
```

**Parameters**:
- `behavior_name` (path, required): Name of the behavior

**Response 200**:
```json
{
  "name": "CheckBattery",
  "parameters": [
    {
      "name": "threshold",
      "type": "float",
      "required": true,
      "description": "Battery threshold percentage",
      "min": 0.0,
      "max": 100.0
    }
  ]
}
```

---

## Executions Router

Manage execution instances.

### List All Executions

```http
GET /executions/
```

**Response 200**:
```json
[
  {
    "execution_id": "exec-uuid",
    "tree_id": "tree-uuid",
    "root_status": "RUNNING",
    "tick_count": 42,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### Create Execution

```http
POST /executions/
```

**Request Body**:
```json
{
  "tree_id": "tree-uuid",
  "initial_blackboard": {
    "battery_level": 100.0,
    "position": [0, 0]
  }
}
```

**Response 201**:
```json
{
  "execution_id": "generated-uuid",
  "tree_id": "tree-uuid",
  "root_status": "INVALID",
  "tick_count": 0,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Get Execution

```http
GET /executions/{execution_id}
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution

**Response 200**:
```json
{
  "execution_id": "exec-uuid",
  "tree_id": "tree-uuid",
  "root_status": "SUCCESS",
  "tick_count": 100,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Tick Execution

```http
POST /executions/{execution_id}/tick
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution

**Request Body**:
```json
{
  "count": 1,
  "capture_snapshot": true
}
```

**Response 200**:
```json
{
  "ticks_executed": 1,
  "root_status": "RUNNING",
  "snapshot": {
    "execution_id": "exec-uuid",
    "tick_count": 101,
    "tree": { ... },
    "blackboard": { ... },
    "node_states": [ ... ]
  }
}
```

### Get Snapshot

```http
GET /executions/{execution_id}/snapshot
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution

**Response 200**:
```json
{
  "execution_id": "exec-uuid",
  "tick_count": 100,
  "tree": {
    "root": {
      "id": "node-uuid",
      "name": "Root",
      "status": "SUCCESS",
      "children": [ ... ]
    }
  },
  "blackboard": {
    "battery_level": 85.5,
    "position": [10, 20]
  },
  "node_states": [
    {
      "node_id": "node-uuid",
      "name": "Check Battery",
      "status": "SUCCESS",
      "message": "Battery OK"
    }
  ]
}
```

### Hot Reload Tree

```http
POST /executions/{execution_id}/reload
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution

**Request Body**:
```json
{
  "tree_id": "new-tree-uuid"
}
```

**Response 200**:
```json
{
  "execution_id": "exec-uuid",
  "tree_id": "new-tree-uuid",
  "root_status": "INVALID",
  "tick_count": 0
}
```

**Note**: Blackboard state is preserved during reload.

### Delete Execution

```http
DELETE /executions/{execution_id}
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution

**Response 204**: No content

### Start AUTO Mode

```http
POST /executions/{execution_id}/scheduler/auto
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution

**Response 200**:
```json
{
  "mode": "AUTO",
  "is_paused": false,
  "is_stopped": false
}
```

### Start INTERVAL Mode

```http
POST /executions/{execution_id}/scheduler/interval
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution

**Request Body**:
```json
{
  "interval_ms": 100
}
```

**Response 200**:
```json
{
  "mode": "INTERVAL",
  "interval_ms": 100,
  "is_paused": false,
  "is_stopped": false
}
```

### Pause Scheduler

```http
POST /executions/{execution_id}/scheduler/pause
```

**Response 200**:
```json
{
  "mode": "AUTO",
  "is_paused": true,
  "is_stopped": false
}
```

### Resume Scheduler

```http
POST /executions/{execution_id}/scheduler/resume
```

**Response 200**:
```json
{
  "mode": "AUTO",
  "is_paused": false,
  "is_stopped": false
}
```

### Stop Scheduler

```http
POST /executions/{execution_id}/scheduler/stop
```

**Response 200**:
```json
{
  "mode": "MANUAL",
  "is_paused": false,
  "is_stopped": true
}
```

---

## History Router

Access execution history.

### Get Execution History

```http
GET /history/executions/{execution_id}
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution
- `start_tick` (query, optional): Start tick number
- `end_tick` (query, optional): End tick number
- `limit` (query, optional): Max number of snapshots (default: 100)

**Response 200**:
```json
[
  {
    "tick": 1,
    "timestamp": "2024-01-01T00:00:00Z",
    "snapshot": { ... }
  },
  {
    "tick": 2,
    "timestamp": "2024-01-01T00:00:01Z",
    "snapshot": { ... }
  }
]
```

### Get Snapshot at Tick

```http
GET /history/executions/{execution_id}/ticks/{tick}
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution
- `tick` (path, required): Tick number

**Response 200**:
```json
{
  "tick": 42,
  "timestamp": "2024-01-01T00:00:42Z",
  "snapshot": { ... }
}
```

**Response 404**:
```json
{
  "detail": "Snapshot not found for tick 42"
}
```

### Get History Summary

```http
GET /history/executions/{execution_id}/summary
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution

**Response 200**:
```json
{
  "execution_id": "exec-uuid",
  "total_ticks": 1000,
  "first_tick": 1,
  "last_tick": 1000,
  "history_size": 1000,
  "oldest_timestamp": "2024-01-01T00:00:00Z",
  "newest_timestamp": "2024-01-01T00:16:40Z"
}
```

### Clear History

```http
DELETE /history/executions/{execution_id}
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution

**Response 204**: No content

---

## Debug Router

Debugging features.

### Get Debug State

```http
GET /debug/executions/{execution_id}
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution

**Response 200**:
```json
{
  "is_paused": false,
  "breakpoints": [
    {
      "node_id": "node-uuid",
      "condition": "blackboard.get('battery_level') < 20",
      "enabled": true
    }
  ],
  "watches": {
    "battery_level": {
      "key": "battery_level",
      "condition": "CHANGE",
      "last_value": 85.5
    }
  },
  "step_mode": null
}
```

### Add Breakpoint

```http
POST /debug/executions/{execution_id}/breakpoints
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution

**Request Body**:
```json
{
  "node_id": "node-uuid",
  "condition": "blackboard.get('counter') > 10",
  "enabled": true
}
```

**Response 200**: Returns updated debug state

### Remove Breakpoint

```http
DELETE /debug/executions/{execution_id}/breakpoints/{node_id}
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution
- `node_id` (path, required): UUID of the node

**Response 200**: Returns updated debug state

### Enable/Disable Breakpoint

```http
PATCH /debug/executions/{execution_id}/breakpoints/{node_id}
```

**Request Body**:
```json
{
  "enabled": false
}
```

**Response 200**: Returns updated debug state

### Add Watch

```http
POST /debug/executions/{execution_id}/watches
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution

**Request Body**:
```json
{
  "key": "battery_level",
  "condition": "LESS",
  "target_value": 20.0
}
```

**Condition Types**:
- `CHANGE`: Value changed
- `EQUALS`: Value equals target
- `NOT_EQUALS`: Value not equals target
- `GREATER`: Value > target
- `LESS`: Value < target
- `GREATER_OR_EQUAL`: Value >= target
- `LESS_OR_EQUAL`: Value <= target

**Response 200**: Returns updated debug state

### Remove Watch

```http
DELETE /debug/executions/{execution_id}/watches/{key}
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution
- `key` (path, required): Blackboard key being watched

**Response 200**: Returns updated debug state

### Pause Execution

```http
POST /debug/executions/{execution_id}/pause
```

**Response 200**: Returns updated debug state with `is_paused: true`

### Continue Execution

```http
POST /debug/executions/{execution_id}/continue
```

**Response 200**: Returns updated debug state with `is_paused: false`, `step_mode: null`

### Step Execution

```http
POST /debug/executions/{execution_id}/step
```

**Request Body**:
```json
{
  "mode": "STEP_OVER"
}
```

**Step Modes**:
- `STEP_OVER`: Execute until next node at same level
- `STEP_INTO`: Execute one node, enter children
- `STEP_OUT`: Execute until parent completes

**Response 200**: Returns updated debug state

### Get Breakpoint Events

```http
GET /debug/executions/{execution_id}/events/breakpoints
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution
- `since` (query, optional): ISO timestamp to get events since

**Response 200**:
```json
[
  {
    "timestamp": "2024-01-01T00:00:00Z",
    "node_id": "node-uuid",
    "node_name": "Check Battery",
    "condition": "blackboard.get('battery_level') < 20"
  }
]
```

---

## Visualization Router

Tree visualization and statistics.

### Get DOT Graph

```http
GET /visualizations/executions/{execution_id}/dot
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution

**Response 200**:
```json
{
  "format": "dot",
  "source": "digraph BehaviorTree {\n  ...\n}"
}
```

### Get py_trees_js Format

```http
GET /visualizations/executions/{execution_id}/pytrees_js
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution

**Response 200**:
```json
{
  "behaviours": {
    "node-uuid": {
      "id": "node-uuid",
      "name": "Check Battery",
      "status": "SUCCESS",
      "type": "behaviour",
      "children": []
    }
  },
  "visited_path": ["node-uuid-1", "node-uuid-2"],
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Export as SVG

```http
GET /visualizations/executions/{execution_id}/svg
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution

**Response 200**: SVG content (image/svg+xml)

**Note**: Requires graphviz package installed

### Export as PNG

```http
GET /visualizations/executions/{execution_id}/png
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution

**Response 200**: PNG content (image/png)

**Note**: Requires graphviz package installed

### Get Statistics

```http
GET /visualizations/executions/{execution_id}/statistics
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution

**Response 200**:
```json
{
  "execution_id": "exec-uuid",
  "total_ticks": 1000,
  "total_duration_ms": 1234.56,
  "avg_tick_duration_ms": 1.23,
  "min_tick_duration_ms": 0.5,
  "max_tick_duration_ms": 5.0,
  "node_stats": {
    "node-uuid": {
      "node_id": "node-uuid",
      "node_name": "Check Battery",
      "node_type": "CheckBattery",
      "tick_count": 1000,
      "total_duration_ms": 100.0,
      "avg_duration_ms": 0.1,
      "min_duration_ms": 0.05,
      "max_duration_ms": 0.5
    }
  }
}
```

---

## Validation Router

Tree and behavior validation.

### Validate Tree

```http
POST /validation/trees
```

**Request Body**: Complete tree definition (same as Create Tree)

**Response 200**:
```json
{
  "is_valid": true,
  "issues": [],
  "error_count": 0,
  "warning_count": 0,
  "info_count": 0
}
```

**Response 200** (with errors):
```json
{
  "is_valid": false,
  "issues": [
    {
      "level": "error",
      "code": "UNKNOWN_BEHAVIOR",
      "message": "Unknown behavior type: 'InvalidBehavior'",
      "node_id": "node-uuid",
      "node_path": "root/children[0]",
      "field": "node_type",
      "context": {"behavior_type": "InvalidBehavior"}
    },
    {
      "level": "warning",
      "code": "UNKNOWN_PARAMETER",
      "message": "Unknown parameter 'invalid_param' for behavior 'Log'",
      "node_id": "node-uuid-2",
      "node_path": "root/children[1]",
      "field": "config.invalid_param"
    }
  ],
  "error_count": 1,
  "warning_count": 1,
  "info_count": 0
}
```

### Validate Tree from Library

```http
POST /validation/trees/{tree_id}
```

**Parameters**:
- `tree_id` (path, required): UUID of the tree

**Response 200**: Same as Validate Tree

### Validate Behavior Config

```http
POST /validation/behaviors
```

**Parameters**:
- `behavior_type` (query, required): Name of the behavior

**Request Body**:
```json
{
  "message": "Hello, World!"
}
```

**Response 200**:
```json
{
  "is_valid": true,
  "issues": [],
  "error_count": 0
}
```

### List Templates

```http
GET /validation/templates
```

**Response 200**:
```json
[
  {
    "template_id": "simple_patrol",
    "name": "Simple Patrol Template",
    "description": "Parameterized patrol tree",
    "category": "robot",
    "tags": ["patrol", "robot"],
    "parameters": [
      {
        "name": "num_waypoints",
        "type": "int",
        "required": true,
        "default": 3
      }
    ]
  }
]
```

### Get Template

```http
GET /validation/templates/{template_id}
```

**Parameters**:
- `template_id` (path, required): ID of the template

**Response 200**:
```json
{
  "template_id": "simple_patrol",
  "name": "Simple Patrol Template",
  "description": "...",
  "category": "robot",
  "tags": ["patrol"],
  "parameters": [ ... ],
  "example_params": {
    "num_waypoints": 4,
    "scan_duration": 2.0
  },
  "tree_structure": {
    "root": { ... }
  }
}
```

### Create Template

```http
POST /validation/templates
```

**Request Body**:
```json
{
  "template_id": "my_template",
  "name": "My Template",
  "description": "Template description",
  "category": "custom",
  "tags": ["template"],
  "parameters": [
    {
      "name": "param1",
      "type": "string",
      "required": true,
      "default": "value"
    }
  ],
  "example_params": {
    "param1": "example"
  },
  "tree_structure": {
    "root": {
      "node_type": "Log",
      "name": "Log Message",
      "config": {
        "message": "{{param1}}"
      }
    }
  }
}
```

**Response 201**: Returns created template

### Instantiate Template

```http
POST /validation/templates/{template_id}/instantiate
```

**Parameters**:
- `template_id` (path, required): ID of the template

**Request Body**:
```json
{
  "template_id": "simple_patrol",
  "parameters": {
    "num_waypoints": 5,
    "scan_duration": 1.5,
    "battery_threshold": 25.0
  },
  "tree_name": "Office Patrol",
  "tree_version": "1.0.0"
}
```

**Response 200**: Returns instantiated tree definition (ready to create)

### Delete Template

```http
DELETE /validation/templates/{template_id}
```

**Parameters**:
- `template_id` (path, required): ID of the template

**Response 204**: No content

---

## WebSocket

Real-time execution monitoring.

### Connect to Execution

```
ws://localhost:8000/ws/executions/{execution_id}
```

**Parameters**:
- `execution_id` (path, required): UUID of the execution

**Connection**: Establish WebSocket connection

**Received Messages**: Events from execution

```json
{
  "type": "TICK_COMPLETED",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "tick_count": 42,
    "root_status": "RUNNING"
  }
}
```

**Event Types**:
- `TICK_STARTED`
- `TICK_COMPLETED`
- `NODE_VISITED`
- `NODE_STATUS_CHANGED`
- `BLACKBOARD_UPDATED`
- `EXECUTION_STARTED`
- `EXECUTION_COMPLETED`
- `ERROR_OCCURRED`
- `BREAKPOINT_HIT`
- `WATCH_TRIGGERED`

**Client Example** (JavaScript):
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/executions/exec-uuid');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(`Event: ${message.type}`, message.data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket connection closed');
};
```

---

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error message here"
}
```

### HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created
- `204 No Content`: Successful deletion
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

### Validation Error Response

```json
{
  "detail": [
    {
      "loc": ["body", "metadata", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limiting

Currently no rate limiting. For deployment, consider:
- Implementing rate limiting middleware
- Using API gateway with rate limiting
- Monitoring API usage

---

## Authentication

Currently no authentication. For deployment:
- Add API key authentication
- Implement OAuth2/JWT tokens
- Use HTTPS for all requests

---

## Versioning

Current API version: `v1` (implicit)

Future versions will use URL versioning:
- `/v1/trees/`
- `/v2/trees/`

---

## Best Practices

### Creating Executions

Always validate tree before creating execution:
```http
POST /validation/trees/{tree_id}
# If valid:
POST /executions/
```

### Long-Running Operations

For long executions, use scheduler:
```http
POST /executions/{execution_id}/scheduler/auto
# Monitor via WebSocket
ws://localhost:8000/ws/executions/{execution_id}
```

### Debugging

Enable debugging before execution:
```http
POST /debug/executions/{execution_id}/breakpoints
POST /debug/executions/{execution_id}/watches
POST /executions/{execution_id}/tick
```

### Cleanup

Always cleanup executions when done:
```http
DELETE /executions/{execution_id}
```

Or use scheduler stop for cleanup:
```http
POST /executions/{execution_id}/scheduler/stop
DELETE /executions/{execution_id}
```

---

## Examples

### Complete Workflow

```bash
# 1. Create tree
curl -X POST http://localhost:8000/trees/ \
  -H "Content-Type: application/json" \
  -d @my_tree.json

# 2. Validate tree
TREE_ID="..."
curl -X POST http://localhost:8000/validation/trees/$TREE_ID

# 3. Create execution
curl -X POST http://localhost:8000/executions/ \
  -H "Content-Type: application/json" \
  -d "{\"tree_id\": \"$TREE_ID\"}"

# 4. Execute ticks
EXEC_ID="..."
curl -X POST http://localhost:8000/executions/$EXEC_ID/tick \
  -H "Content-Type: application/json" \
  -d '{"count": 10, "capture_snapshot": true}'

# 5. Get statistics
curl http://localhost:8000/visualizations/executions/$EXEC_ID/statistics

# 6. Cleanup
curl -X DELETE http://localhost:8000/executions/$EXEC_ID
```

### Debugging Workflow

```bash
# 1. Create execution
EXEC_ID="..."

# 2. Add breakpoint
curl -X POST http://localhost:8000/debug/executions/$EXEC_ID/breakpoints \
  -H "Content-Type: application/json" \
  -d '{"node_id": "node-uuid", "condition": "blackboard.get(\"counter\") > 5"}'

# 3. Add watch
curl -X POST http://localhost:8000/debug/executions/$EXEC_ID/watches \
  -H "Content-Type: application/json" \
  -d '{"key": "counter", "condition": "CHANGE"}'

# 4. Execute with debugging
curl -X POST http://localhost:8000/executions/$EXEC_ID/tick \
  -H "Content-Type: application/json" \
  -d '{"count": 1}'

# 5. Check debug state
curl http://localhost:8000/debug/executions/$EXEC_ID

# 6. Continue or step
curl -X POST http://localhost:8000/debug/executions/$EXEC_ID/continue
```

---

## Summary

The TalkingTrees API provides comprehensive control over:
- Tree library management
- Execution lifecycle
- Real-time monitoring
- Debugging capabilities
- Visualization and statistics
- Template instantiation
- Validation

For interactive exploration, visit: `http://localhost:8000/docs`
