# PyForest CLI Guide

The PyForest CLI (`pyforest`) provides a command-line interface for managing behavior trees, templates, and executions.

## Installation

Install PyForest with CLI support:

```bash
pip install -e .
```

For visualization support (DOT graph rendering):

```bash
pip install -e ".[viz]"
```

## Configuration

Configure the CLI to connect to your PyForest API:

```bash
# Show current configuration
pyforest config --show

# Set API URL
pyforest config --api-url http://localhost:8000

# Set timeout
pyforest config --set timeout=60
```

Configuration is stored in `~/.pyforest/config.json`.

## Tree Management

### List Trees

```bash
# List all trees
pyforest tree list

# Filter by name
pyforest tree list --name "patrol"

# Filter by tags
pyforest tree list --tags "robot,demo"
```

### Get Tree Details

```bash
# Get tree details
pyforest tree get TREE_ID

# Save tree to file
pyforest tree get TREE_ID --output tree.json

# Show raw JSON
pyforest tree get TREE_ID --json
```

### Create Tree

```bash
# Create tree from JSON file
pyforest tree create examples/trees/01_simple_sequence.json
```

### Validate Tree

```bash
# Validate tree file
pyforest tree validate --file examples/trees/01_simple_sequence.json

# Validate tree in library
pyforest tree validate --id TREE_ID
```

### Delete Tree

```bash
# Delete tree (with confirmation)
pyforest tree delete TREE_ID

# Force delete without confirmation
pyforest tree delete TREE_ID --force
```

## Template Management

### List Templates

```bash
# List all available templates
pyforest template list
```

### Get Template Details

```bash
# Get template details
pyforest template get simple_patrol

# Save template to file
pyforest template get simple_patrol --output template.json

# Show raw JSON
pyforest template get simple_patrol --json
```

### Create Template

```bash
# Create template from JSON file
pyforest template create my_template.json
```

### Instantiate Template

```bash
# Instantiate with default parameters
pyforest template instantiate simple_patrol --name "My Patrol"

# Instantiate with parameter file
pyforest template instantiate simple_patrol \
  --name "Custom Patrol" \
  --params params.json

# Interactive mode (prompts for parameters)
pyforest template instantiate simple_patrol \
  --name "Interactive Patrol" \
  --interactive

# Save to file instead of uploading
pyforest template instantiate simple_patrol \
  --name "Saved Patrol" \
  --output my_patrol.json
```

## Execution Management

### List Executions

```bash
# List all active executions
pyforest exec list
```

### Run Tree

```bash
# Run tree with N ticks
pyforest exec run TREE_ID --ticks 10

# Run in AUTO mode (continuous)
pyforest exec run TREE_ID --auto

# Run in INTERVAL mode (tick every N milliseconds)
pyforest exec run TREE_ID --interval 100

# Run with monitoring
pyforest exec run TREE_ID --auto --monitor
```

### Manual Ticking

```bash
# Tick existing execution
pyforest exec tick EXECUTION_ID --count 5
```

### Get Snapshot

```bash
# Get current snapshot
pyforest exec snapshot EXECUTION_ID

# Save snapshot to file
pyforest exec snapshot EXECUTION_ID --output snapshot.json
```

### Show Statistics

```bash
# Show execution statistics
pyforest exec stats EXECUTION_ID
```

### Stop Execution

```bash
# Stop scheduled execution
pyforest exec stop EXECUTION_ID
```

### Delete Execution

```bash
# Delete execution
pyforest exec delete EXECUTION_ID --force
```

## Import/Export

### Export Tree

```bash
# Export tree as JSON
pyforest export tree TREE_ID --output tree.json

# Export as YAML
pyforest export tree TREE_ID --output tree.yaml --format yaml
```

### Import Tree

```bash
# Import tree from JSON
pyforest export import tree.json

# Import from YAML
pyforest export import tree.yaml --format yaml
```

### Export DOT Graph

```bash
# Export execution as DOT graph
pyforest export dot EXECUTION_ID --output tree.dot

# Export and render to image
pyforest export dot EXECUTION_ID --output tree.dot --render
```

### Batch Operations

```bash
# Export all trees
pyforest export batch --output ./trees --format json

# Import all trees from directory
pyforest export batch-import ./trees --format json
```

## Performance Profiling

Profile a tree's performance:

```bash
# Basic profiling (100 ticks)
pyforest profile TREE_ID

# Custom tick count
pyforest profile TREE_ID --ticks 1000

# With warmup
pyforest profile TREE_ID --ticks 1000 --warmup 50
```

The profiler shows:
- Total execution time
- Average/min/max tick duration
- Throughput (ticks/sec)
- Per-node statistics
- Percentage breakdown

## Example Workflows

### Quick Start: Run an Example

```bash
# Import an example tree
pyforest export import examples/trees/01_simple_sequence.json

# List trees to get ID
pyforest tree list

# Run the tree
pyforest exec run TREE_ID --ticks 5
```

### Create Tree from Template

```bash
# List available templates
pyforest template list

# Create tree from template interactively
pyforest template instantiate simple_patrol \
  --name "Building A Patrol" \
  --interactive

# Run the created tree
pyforest tree list --name "Building A"
pyforest exec run TREE_ID --auto --monitor
```

### Performance Analysis

```bash
# Import stress test tree
pyforest export import examples/trees/08_stress_test.json

# Get tree ID
TREE_ID=$(pyforest tree list --name "stress" | grep -oE '[0-9a-f-]{36}' | head -1)

# Profile performance
pyforest profile $TREE_ID --ticks 1000
```

### Batch Import Examples

```bash
# Import all example trees
pyforest export batch-import examples/trees --format json

# List imported trees
pyforest tree list
```

### Export for Backup

```bash
# Create backup directory
mkdir backup

# Export all trees
pyforest export batch --output backup --format json

# Later, restore from backup
pyforest export batch-import backup --format json
```

## Tips and Tricks

### Using with Scripts

```bash
# Get tree ID from name
TREE_ID=$(pyforest tree list --name "my tree" | grep -oE '[0-9a-f-]{36}' | head -1)

# Run in background
pyforest exec run $TREE_ID --auto &

# Stop after some time
sleep 10
pyforest exec stop $(pyforest exec list | grep $TREE_ID | cut -d' ' -f1)
```

### Validation Pipeline

```bash
#!/bin/bash
# Validate all example trees

for file in examples/trees/*.json; do
  echo "Validating $file..."
  pyforest tree validate --file "$file" || echo "FAILED: $file"
done
```

### Performance Comparison

```bash
# Profile multiple trees
for tree_id in $(pyforest tree list | grep -oE '[0-9a-f-]{36}'); do
  echo "Profiling $tree_id..."
  pyforest profile $tree_id --ticks 100
done
```

## Shell Completion

Install shell completion for better CLI experience:

```bash
# Install completion
pyforest --install-completion

# Show completion script (for manual setup)
pyforest --show-completion
```

## API Server

The CLI requires a running PyForest API server. Start it with:

```bash
python run_server.py
```

Or use uvicorn directly:

```bash
uvicorn py_forest.api.main:app --host 0.0.0.0 --port 8000
```

## Troubleshooting

### Connection Errors

```bash
# Check API URL
pyforest config --show

# Test connection
curl http://localhost:8000/behaviors/
```

### Tree Not Found

```bash
# Verify tree exists
pyforest tree list

# Check tree ID format (should be UUID)
```

### Timeout Issues

```bash
# Increase timeout for large operations
pyforest config --set timeout=120
```

## Advanced Usage

### Combining with jq

```bash
# Get tree and extract specific field
pyforest tree get TREE_ID --json | jq '.metadata.name'

# List trees with specific tag
pyforest tree list --json | jq '.[] | select(.metadata.tags[] == "robot")'
```

### Monitoring Executions

```bash
# Create execution
EXEC_ID=$(pyforest exec run TREE_ID --auto | grep -oE '[0-9a-f-]{36}')

# Monitor in real-time
watch -n 1 "pyforest exec stats $EXEC_ID"
```

### Export Visualization

```bash
# Run tree
EXEC_ID=$(pyforest exec run TREE_ID --ticks 1 | grep -oE '[0-9a-f-]{36}')

# Export visualization
pyforest export dot $EXEC_ID --output tree.dot --render

# View PNG
open tree.png  # macOS
xdg-open tree.png  # Linux
```

## See Also

- [Examples README](examples/trees/README.md) - Example tree descriptions
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Phase Summaries](CONVERSATION_COMPACT.md) - Development history
