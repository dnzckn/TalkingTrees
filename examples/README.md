# PyForest Examples

This directory contains example tree definitions and usage demonstrations.

## Example Trees

### simple_tree.json
A basic patrol behavior tree demonstrating:
- Selector for priority-based decision making
- Sequence for sequential task execution
- Custom behaviors (CheckBattery, Log, Wait)
- Blackboard usage for shared state
- UI metadata for visual editors

Structure:
```
root_selector (Selector)
├── normal_operations (Sequence)
│   ├── battery_check (CheckBattery)
│   ├── patrol_log (Log)
│   └── patrol_action (Wait)
└── low_battery_log (Log)
```

Logic:
1. Try normal operations sequence
2. Check battery level (must be above 20%)
3. If battery OK, execute patrol
4. If battery low, log warning and return

## Running Examples

```python
from py_forest.storage import FileSystemTreeLibrary
from pathlib import Path

# Load tree library
library = FileSystemTreeLibrary(Path("data"))

# Load example tree
tree_def = library.get_tree(
    tree_id="550e8400-e29b-41d4-a716-446655440001"
)

# TODO: Add execution example once execution engine is implemented
```

## Creating Custom Trees

See the JSON schema in `simple_tree.json` for the required format.
Key fields:
- `metadata`: Tree information (name, version, description, etc.)
- `root`: Root node definition
- `blackboard_schema`: Blackboard variable definitions
- `dependencies`: Required behaviors and subtrees
