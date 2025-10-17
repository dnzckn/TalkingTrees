# PyForest - Quick Reference Card

## What Was Built This Session

1. **Tree Diff/Merge** - `src/py_forest/core/diff.py`
2. **Execution Profiling** - `src/py_forest/core/profiler.py`
3. **Blackboard Validation** - `src/py_forest/core/blackboard_validator.py`
4. **Python SDK** - `src/py_forest/sdk.py`
5. **Visual Diff Viewer** - `visualization/tree_diff_viewer.html` (bug fixed)

## Quick Start - Python SDK

```python
from py_forest.sdk import PyForest, ProfilingLevel

# Initialize
pf = PyForest(profiling_level=ProfilingLevel.BASIC)

# Load and run
tree = pf.load_tree("my_tree.json")
execution = pf.create_execution(tree)
result = execution.tick(blackboard_updates={"sensor": 42})

# Check outputs
print(result.status)  # SUCCESS, FAILURE, RUNNING
print(result.blackboard.get("/output_key"))

# Profile performance
print(execution.get_profiling_report())

# Compare versions
diff = pf.diff_trees(tree_v1, tree_v2)
print(diff)
```

## Quick Start - API

```bash
# Start server
uvicorn py_forest.api.main:app --port 8000

# Compare tree versions
curl "http://localhost:8000/trees/{id}/diff?old_version=1.0.0&new_version=2.0.0"

# Get profiling report
curl http://localhost:8000/profiling/{execution_id}
```

## Key Files

**New Files:**
- `src/py_forest/sdk.py` - High-level Python API
- `src/py_forest/core/diff.py` - Diff/merge engine
- `src/py_forest/core/profiler.py` - Profiling system
- `src/py_forest/core/blackboard_validator.py` - Validation
- `src/py_forest/api/routers/profiling.py` - Profiling API
- `IMPROVEMENTS_SUMMARY.md` - Full documentation
- `SESSION_CONTEXT.md` - Session summary

**Modified Files:**
- `src/py_forest/core/execution.py` - Added profiling + validation
- `src/py_forest/api/routers/trees.py` - Added diff endpoint
- `src/py_forest/api/main.py` - Added profiling router
- `visualization/tree_diff_viewer.html` - Fixed semantic matching bug

## Critical Bug Fixed

**Issue:** Diff viewer showed identical trees as completely different (all red/green)
**Fix:** Implemented two-phase semantic matching by (name, type, parent_path)
**Location:** `visualization/tree_diff_viewer.html` lines 450-500

## Architecture

```
PyForest SDK → Core Logic (diff/profiler/validator) → TreeSerializer → py_trees
     ↓
FastAPI → Routers → Services → Core Logic
```

## Next Steps (If Needed)

1. Create Jupyter notebook examples
2. Extend per-node profiling (not just root)
3. Add rate limiting for node execution
4. Create CLI diff tool
