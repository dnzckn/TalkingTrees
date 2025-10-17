# Blackboard Architecture - Design & Migration Plan

**Date:** 2025-10-17
**Status:** Deprecation in Progress
**Target:** v2.0.0 for breaking change

---

##  Current Problem

### Architectural Issue

**blackboard_schema is embedded in TreeDefinition**, mixing two distinct concerns:

1. **Tree Logic (Static):** What the tree does
   - Node structure
   - Control flow
   - Conditions to check
   - Actions to execute

2. **Runtime Data (Dynamic):** Values during execution
   - Blackboard variable schemas
   - Default values
   - Type constraints

### User's Insight

> "we shouldnt need to include anything backboard related into the serilization, only whats contained in the tree, blackboard stuff may eventually be a database or some other api sending data to some database etc"

**Key Realization:** Blackboard data might come from:
- In-memory blackboard (current)
- Database
- REST API
- Message queue
- File system

Trees should reference external data sources, not embed data schemas.

---

##  Current Implementation

### Data Model

```python
class TreeDefinition(BaseModel):
    tree_id: UUID
    metadata: TreeMetadata
    root: TreeNodeDefinition
    subtrees: Dict[str, TreeNodeDefinition]
    blackboard_schema: Dict[str, BlackboardVariableSchema]  #  Problem!
```

### Issues

1. **Auto-detection is Fragile**
   ```python
   # _collect_blackboard_variables() scans tree and infers types
   # But can't detect all variables, especially from custom behaviors
   blackboard_schema = _collect_blackboard_variables(root)
   ```

2. **Schema is Optional but Used**
   ```python
   # Currently used to initialize defaults:
   for key, schema in tree_def.blackboard_schema.items():
       bb.register_key(key=key, access=py_trees.common.Access.WRITE)
       if schema.default is not None:
           bb.set(key, schema.default, overwrite=False)
   ```

3. **Tree Structure References Variables**
   ```python
   # Nodes check/set blackboard variables by name:
   CheckBlackboardVariableValue(variable_name="battery_level")
   SetBlackboardVariable(variable_name="speed", value=42.5)
   ```

### What Trees Actually Need

Trees only need to **reference variable names**, not define their schemas:
- `if battery_level < 20` - references "battery_level"
- `set speed = 42.5` - references "speed"

The **source of those variables** should be external.

---

##  Proposed Architecture (v2.0)

### Separation of Concerns

```
┌─────────────────┐
│  TreeDefinition │   Pure Logic (what to do)
│  - Structure    │
│  - Control flow │
│  - Node configs │
└─────────────────┘
          references
┌─────────────────┐
│  Variable Names │   Just names: "battery", "speed"
│  (strings only) │
└─────────────────┘
          bound to
┌─────────────────┐
│  Data Source    │   Runtime State (where data lives)
│  - Blackboard   │
│  - Database     │
│  - API          │
└─────────────────┘
```

### New Execution API

**Option A: Explicit Data Source (Recommended)**
```python
# Tree doesn't contain blackboard_schema
tree = load_tree("patrol.json")  # No blackboard_schema in JSON

# Execution binds tree to data source
execution = pf.create_execution(
    tree=tree,
    data_source=my_blackboard  # or my_database, my_api, etc.
)
```

**Option B: Data Source as Constructor Argument**
```python
tree = load_tree("patrol.json")
tree.bind_data_source(my_blackboard)
execution = pf.create_execution(tree)
```

**Option C: Execution Engine Manages**
```python
engine = ExecutionEngine(data_source=my_blackboard)
execution = engine.execute(tree)
```

### Benefits

1. **Separation:** Tree structure separate from runtime data
2. **Flexibility:** Data from any source (DB, API, memory)
3. **Reusability:** Same tree with different data sources
4. **Testability:** Mock data sources for testing
5. **Simplicity:** Cleaner JSON, no schema auto-detection

---

##  Migration Strategy

### Phase 1: Deprecation (Current - v1.x)

**Status:**  IN PROGRESS

1. **Mark blackboard_schema as deprecated**
   - Add deprecation warnings
   - Update documentation
   - Recommend empty schema

2. **Make auto_detect_blackboard default to False**
   ```python
   from_py_trees(root, auto_detect_blackboard=False)  # New default
   ```

3. **Document migration path**
   - Show how to provide blackboard separately
   - Examples of external data sources

### Phase 2: Transition (v1.9)

1. **Add new execution API (backward compatible)**
   ```python
   # New way (preferred):
   execution = pf.create_execution(tree, data_source=bb)

   # Old way (still works):
   tree = deserialize(tree_def)  # Uses blackboard_schema if present
   ```

2. **Provide migration tools**
   - Script to strip blackboard_schema from JSONs
   - Script to extract schema to separate file

3. **Update all examples and tutorials**

### Phase 3: Breaking Change (v2.0)

1. **Remove blackboard_schema from TreeDefinition**
   ```python
   class TreeDefinition(BaseModel):
       # ... other fields ...
       # blackboard_schema removed!
   ```

2. **Require data_source in execution**
   ```python
   # This becomes required:
   execution = pf.create_execution(tree, data_source=bb)
   ```

3. **Clean up auto-detection code**
   - Remove `_collect_blackboard_variables()`
   - Remove `auto_detect_blackboard` parameter

---

##  Implementation Plan

### Immediate (This Session)

- [x]  Analyze current usage
- [ ] Add deprecation warning to blackboard_schema
- [ ] Update documentation
- [ ] Add migration examples

### Short-term (Next Release - v1.9)

- [ ] Change `auto_detect_blackboard` default to False
- [ ] Add `data_source` parameter to execution
- [ ] Create migration script
- [ ] Update all examples

### Long-term (v2.0)

- [ ] Remove blackboard_schema field
- [ ] Remove auto-detection code
- [ ] Update schema version to 2.0.0
- [ ] Full migration guide

---

##  Examples

### Current (v1.x - Deprecated)

```python
# Tree contains blackboard_schema (embedded data)
tree_json = {
    "root": {"node_type": "CheckBatteryLevel", "config": {"threshold": 20}},
    "blackboard_schema": {
        "battery_level": {"type": "float", "default": 100.0}
    }
}

tree_def = TreeDefinition(**tree_json)
tree = serializer.deserialize(tree_def)  # Initializes blackboard from schema
tree.tick()
```

### Future (v2.0 - Recommended)

```python
# Tree is pure logic (no data schema)
tree_json = {
    "root": {"node_type": "CheckBatteryLevel", "config": {"threshold": 20}}
    # No blackboard_schema!
}

tree_def = TreeDefinition(**tree_json)
py_tree = serializer.deserialize(tree_def)

# Data comes from external source
bb = py_trees.blackboard.Client()
bb.register_key("battery_level", access=py_trees.common.Access.WRITE)
bb.set("battery_level", 100.0)

# Execute with data source
execution = pf.create_execution(py_tree, data_source=bb)
execution.tick()
```

### Alternative Data Sources

```python
# Database as data source
db_source = DatabaseBlackboardAdapter(connection_string="...")
execution = pf.create_execution(tree, data_source=db_source)

# REST API as data source
api_source = APIBlackboardAdapter(base_url="https://api.example.com")
execution = pf.create_execution(tree, data_source=api_source)

# Redis as data source
redis_source = RedisBlackboardAdapter(redis_client=redis_client)
execution = pf.create_execution(tree, data_source=redis_source)
```

---

##  Backward Compatibility

### v1.x Behavior (Current)

- `blackboard_schema` is optional (defaults to `{}`)
- If present, initializes blackboard with defaults
- Auto-detection available via `auto_detect_blackboard=True`

### Transition Period

- Deprecation warnings when `blackboard_schema` is used
- Both old and new execution APIs work
- Migration scripts available

### v2.0 Breaking Changes

- `blackboard_schema` field removed
- `data_source` required for execution
- Auto-detection code removed

---

##  Impact Analysis

### Files Affected

- `src/py_forest/models/tree.py` - Remove BlackboardVariableSchema, blackboard_schema field
- `src/py_forest/core/serializer.py` - Remove _initialize_blackboard method
- `src/py_forest/adapters/py_trees_adapter.py` - Remove _collect_blackboard_variables, auto_detect_blackboard
- `src/py_forest/core/execution.py` - Add data_source parameter
- All examples and tutorials - Update to new pattern

### User Code Changes

**Before (v1.x):**
```python
tree_def = from_py_trees(root, auto_detect_blackboard=True)
tree = serializer.deserialize(tree_def)
```

**After (v2.0):**
```python
tree_def, _ = from_py_trees(root)  # No blackboard auto-detect
py_tree = serializer.deserialize(tree_def)

# Setup data separately
bb = setup_blackboard()
execution = pf.create_execution(py_tree, data_source=bb)
```

---

##  Success Criteria

- [ ] blackboard_schema marked as deprecated
- [ ] Deprecation warnings displayed
- [ ] Migration guide published
- [ ] Examples updated
- [ ] Tests pass with empty blackboard_schema
- [ ] New data_source API implemented (v1.9)
- [ ] Migration scripts available
- [ ] v2.0 removes blackboard_schema completely

---

**Conclusion:** This architectural change separates tree logic from runtime data, enabling:
- Multiple data sources (DB, API, memory)
- Cleaner JSON representation
- Better testability
- More flexible deployment scenarios

The migration will be gradual (deprecation  transition  breaking change) to minimize disruption.
