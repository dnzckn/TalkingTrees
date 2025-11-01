# PyForest SDK Guide

## Overview

The PyForest SDK (`sdk.py`) provides a comprehensive Python interface for working with behavior trees, including:
- Tree loading/saving (JSON/YAML)
- Tree validation and analysis
- Node search and query
- Statistics and introspection
- Batch operations
- Tree manipulation

All features are available in a single, unified SDK.

## Installation

PyForest requires:
```bash
pip install py-trees pydantic
```

For YAML support (optional):
```bash
pip install pyyaml
```

## Quick Start

```python
from py_forest.sdk import PyForest

pf = PyForest()
tree = pf.load_tree("my_tree.json")

# Validate before running
validation = pf.validate_tree(tree, verbose=True)
if not validation.is_valid:
    print("Tree has errors!")
    exit(1)

# Get statistics
stats = pf.get_tree_stats(tree)
print(stats.summary())

# Find specific nodes
timeouts = pf.find_nodes_by_type(tree, "Timeout")
print(f"Found {len(timeouts)} timeout decorators")

# Execute
execution = pf.create_execution(tree)
result = execution.tick(blackboard_updates={"battery": 75})
print(f"Status: {result.status}")
```

## Feature Guide

### 1. Tree Validation

Comprehensive validation checks for structural issues, type validity, and configuration correctness.

```python
# Validate a tree
validation = pf.validate_tree(tree, verbose=True)

if validation.is_valid:
    print("✓ Tree is valid")
else:
    print(f"✗ Found {validation.error_count} errors")
    for issue in validation.issues:
        if issue.level == "error":
            print(f"  - {issue.message} at {issue.node_path}")
```

**Validation checks:**
- Circular references
- Duplicate node IDs
- Unknown node types
- Invalid configuration parameters
- Missing required parameters
- Invalid subtree references
- Incorrect child counts for composites/decorators

### 2. Node Search & Query

Find nodes using powerful query methods.

```python
# Find by type
sequences = pf.find_nodes_by_type(tree, "Sequence")
timeouts = pf.find_nodes_by_type(tree, "Timeout")

# Find by name (exact or partial match)
battery_check = pf.find_nodes_by_name(tree, "CheckBattery")
all_checks = pf.find_nodes_by_name(tree, "check", exact=False)

# Find by UUID
node = pf.get_node_by_id(tree, some_uuid)

# Find with custom predicate
long_timeouts = pf.find_nodes(
    tree,
    lambda n: n.node_type == "Timeout" and n.config.get("duration", 0) > 10
)

# Get all nodes
all_nodes = pf.get_all_nodes(tree)
print(f"Tree has {len(all_nodes)} total nodes")
```

### 3. Tree Statistics & Introspection

Analyze tree structure and composition.

```python
# Get comprehensive statistics
stats = pf.get_tree_stats(tree)

print(stats.summary())
# Output:
# Tree Statistics:
#   Total Nodes: 42
#   Max Depth: 5
#   Avg Depth: 2.8
#   Leaf Nodes: 18
#   Composites: 8
#   Decorators: 4
#
# Node Types:
#   Sequence: 5
#   Timeout: 4
#   Success: 8
#   ...

# Count nodes by type
type_counts = pf.count_nodes_by_type(tree)
print(f"Sequences: {type_counts.get('Sequence', 0)}")

# Print tree structure
pf.print_tree_structure(tree, show_config=True, max_depth=3)
```

### 4. YAML Support

Load and save trees in YAML format (requires `pyyaml`).

```python
# Load from YAML
tree = pf.load_yaml("trees/robot_behavior.yaml")

# Save to YAML
pf.save_yaml(tree, "output/robot_behavior.yaml")

# YAML is more readable for version control
```

**Example YAML tree:**

```yaml
$schema: "1.0.0"
tree_id: "550e8400-e29b-41d4-a716-446655440000"
metadata:
  name: "Robot Controller"
  version: "1.0.0"
  description: "Main robot behavior"

root:
  node_type: "Sequence"
  name: "Main"
  config:
    memory: true
  children:
    - node_type: "CheckBattery"
      name: "BatteryCheck"
      config:
        threshold: 0.2
    - node_type: "Success"
      name: "Continue"
```

### 5. Batch Operations

Load and validate multiple trees efficiently.

```python
# Load multiple trees
trees = pf.load_batch([
    "trees/patrol.json",
    "trees/charge.yaml",
    "trees/explore.json"
])

# Validate all
results = pf.validate_batch(trees)

for name, result in results.items():
    status = "✓" if result.is_valid else "✗"
    print(f"{status} {name}: {result.error_count} errors, {result.warning_count} warnings")
```

### 6. Tree Manipulation

Clone, extract, and compare trees.

```python
# Clone a tree
tree_copy = pf.clone_tree(original_tree)
tree_copy.metadata.name = "Modified Version"
tree_copy.metadata.version = "2.0.0"

# Extract a subtree
composite_node = pf.find_nodes_by_name(tree, "PatrolBehavior")[0]
subtree = pf.get_subtree(tree, composite_node.node_id)
pf.save_tree(subtree, "patrol_only.json")

# Compare trees
if pf.trees_equal(tree1, tree2):
    print("Trees are structurally identical")
else:
    print("Trees differ")

# Get content hash for version tracking
hash1 = pf.hash_tree(tree)
# ... modify tree ...
hash2 = pf.hash_tree(tree)
if hash1 != hash2:
    print("Tree was modified")
```

### 7. Advanced Node Analysis

Get detailed node information and paths.

```python
# Get path to a node
node = pf.find_nodes_by_name(tree, "CriticalAction")[0]
path = pf.get_node_path(tree, node.node_id)
print(" -> ".join(path))
# Output: "Root -> MainSequence -> SafetyCheck -> CriticalAction"

# Analyze node distribution
type_counts = pf.count_nodes_by_type(tree)
most_common = max(type_counts.items(), key=lambda x: x[1])
print(f"Most common node type: {most_common[0]} ({most_common[1]} instances)")
```

## Convenience Functions

Quick one-liners for common tasks:

```python
from py_forest.sdk import quick_validate, compare_tree_structures, analyze_tree

# Quick validation
result = quick_validate("my_tree.json")  # Prints results

# Quick comparison
if compare_tree_structures("v1.json", "v2.json"):
    print("No structural changes")

# Complete analysis
report = analyze_tree("my_tree.json")
print(report)
# Output:
# Analysis of: Robot Controller (v1.0.0)
# ======================================================================
#
# VALIDATION:
#   Status: ✓ VALID
#   Errors: 0
#   Warnings: 0
#
# Tree Statistics:
#   Total Nodes: 42
#   Max Depth: 5
#   ...
```

## Performance Optimizations

The PyForest SDK includes several optimizations:

### 1. Caching

Tree hashes are cached for faster comparison:

```python
# Enable caching (default)
pf = PyForest(enable_cache=True)

# First hash computation
hash1 = pf.hash_tree(tree)  # Computes hash

# Subsequent calls use cache
hash2 = pf.hash_tree(tree)  # Returns cached value (fast!)
```

### 2. Lazy Loading

The registry and validator are only initialized when needed.

### 3. Efficient Search

Node search uses a single traversal for all matches.

## Using New Features

All features are available in the single SDK - just import and use:

```python
from py_forest.sdk import PyForest

pf = PyForest()
tree = pf.load_tree("tree.json")

# Basic execution (always worked)
execution = pf.create_execution(tree)
result = execution.tick()

# New validation features
validation = pf.validate_tree(tree)
if not validation.is_valid:
    print("Tree has errors!")

# New search features
timeouts = pf.find_nodes_by_type(tree, "Timeout")

# New statistics
stats = pf.get_tree_stats(tree)
print(stats.summary())
```

## Complete Example: Tree Analysis Workflow

```python
from py_forest.sdk import PyForest

# Initialize
pf = PyForest()

# Load tree
tree = pf.load_tree("complex_robot_behavior.json")

# Step 1: Validate
print("Step 1: Validation")
validation = pf.validate_tree(tree, verbose=True)
if not validation.is_valid:
    exit(1)

# Step 2: Analyze structure
print("\nStep 2: Structure Analysis")
stats = pf.get_tree_stats(tree)
print(stats.summary())

# Step 3: Find potential issues
print("\nStep 3: Issue Detection")

# Find long-running timeouts
long_timeouts = pf.find_nodes(
    tree,
    lambda n: n.node_type == "Timeout" and n.config.get("duration", 0) > 30
)
if long_timeouts:
    print(f"⚠ Warning: {len(long_timeouts)} timeouts > 30 seconds")

# Find missing battery checks
battery_checks = pf.find_nodes_by_name(tree, "battery", exact=False)
if not battery_checks:
    print("⚠ Warning: No battery checks found")

# Step 4: Performance check
print("\nStep 4: Performance Analysis")
if stats.max_depth > 10:
    print(f"⚠ Warning: Max depth {stats.max_depth} may impact performance")

node_count = stats.node_count
if node_count > 100:
    print(f"⚠ Warning: Large tree ({node_count} nodes) may need optimization")

# Step 5: Generate report
print("\nStep 5: Generating report...")
with open("analysis_report.txt", "w") as f:
    f.write(f"Tree Analysis: {tree.metadata.name}\n")
    f.write("=" * 70 + "\n\n")
    f.write(stats.summary())
    f.write("\n\nValidation: ✓ PASSED\n")
    f.write(f"Hash: {pf.hash_tree(tree)}\n")

print("✓ Analysis complete!")
```

## API Reference

### PyForest Class

**Constructor:**
- `PyForest(profiling_level=ProfilingLevel.OFF, enable_cache=True)`

**Validation:**
- `validate_tree(tree, verbose=False) -> TreeValidationResult`

**Search:**
- `find_nodes(tree, predicate) -> List[TreeNodeDefinition]`
- `find_nodes_by_type(tree, node_type) -> List[TreeNodeDefinition]`
- `find_nodes_by_name(tree, name, exact=True) -> List[TreeNodeDefinition]`
- `get_node_by_id(tree, node_id) -> Optional[TreeNodeDefinition]`
- `get_all_nodes(tree) -> List[TreeNodeDefinition]`

**Statistics:**
- `get_tree_stats(tree) -> TreeStatistics`
- `count_nodes_by_type(tree) -> Dict[str, int]`
- `print_tree_structure(tree, show_config=False, max_depth=None)`

**YAML:**
- `load_yaml(path) -> TreeDefinition`
- `save_yaml(tree, path)`

**Batch:**
- `load_batch(paths) -> Dict[str, TreeDefinition]`
- `validate_batch(trees) -> Dict[str, TreeValidationResult]`

**Manipulation:**
- `clone_tree(tree) -> TreeDefinition`
- `hash_tree(tree) -> str`
- `trees_equal(tree1, tree2) -> bool`
- `get_node_path(tree, node_id) -> Optional[List[str]]`
- `get_subtree(tree, node_id) -> Optional[TreeDefinition]`

## Best Practices

1. **Always validate before deployment:**
   ```python
   validation = pf.validate_tree(tree)
   assert validation.is_valid, "Tree has errors!"
   ```

2. **Use batch operations for multiple trees:**
   ```python
   trees = pf.load_batch(file_paths)
   results = pf.validate_batch(trees)
   ```

3. **Cache tree hashes for version tracking:**
   ```python
   version_hashes = {
       "v1.0.0": pf.hash_tree(tree_v1),
       "v1.1.0": pf.hash_tree(tree_v1_1),
   }
   ```

4. **Use YAML for human-readable storage:**
   ```python
   # JSON for production, YAML for development
   pf.save_yaml(tree, "dev/tree.yaml")
   pf.save_tree(tree, "prod/tree.json")
   ```

5. **Profile complex trees:**
   ```python
   pf = PyForest(profiling_level=ProfilingLevel.DETAILED)
   # ... run tree ...
   report = execution.get_profiling_report(verbose=True)
   ```

## Troubleshooting

**ImportError: PyYAML not installed**
```bash
pip install pyyaml
```

**Validation errors on valid trees:**
- Check that all custom behaviors are registered in the registry
- Verify node type names match exactly (case-sensitive)

**Slow tree operations:**
- Enable caching: `PyForest(enable_cache=True)`
- Reduce tree depth and node count
- Use batch operations instead of loops

## Future Enhancements

Planned features for future versions:
- Async tree execution support
- Tree diff visualization
- Performance profiling integration
- Tree optimization suggestions
- GraphQL-style query language for nodes
- Tree composition DSL

## Contributing

To add new convenience methods:

1. Add method to `PyForest` class in `sdk_enhanced.py`
2. Add tests in `tests/test_sdk_enhanced.py`
3. Update this documentation
4. Add example in `examples/sdk_examples.py`
