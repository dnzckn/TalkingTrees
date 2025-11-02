# TalkingTrees Visual Editors

This directory contains visual behavior tree editors for TalkingTrees.

## Files

### tree_editor.html
The behavior tree editor with complete feature set.

**Features:**
- **Visual Editing**: Modern toolbar with drag-and-drop node palette
- **Undo/Redo**: Full history tracking (Ctrl+Z/Y)
- **Tree Library**: Save/load trees locally or from remote API
  - Local mode: Load from any folder on your computer
  - Remote mode: Connect to team API server
  - Folder picker with auto-discovery of .json files
- **Live Execution Simulator**: Real-time tree execution with visual feedback
  - Play/Pause/Step controls
  - Adjustable simulation speed
  - Visual node states (SUCCESS=green, FAILURE=red, RUNNING=yellow)
  - Breakpoint support on any node
- **Execution Timeline Scrubber**: Video-player-style timeline
  - Scrub through execution history
  - Click/drag to jump to any tick
  - Keyboard shortcuts (← → for prev/next tick)
  - Color-coded tick visualization (green/yellow/red)
  - Last 100 ticks buffered
- **Blackboard Inspector**: Live variable viewer
  - Watch expressions
  - Edit variables during simulation
  - Variable usage tracking
- **Smart Validation**: Real-time error detection
  - Unreachable nodes
  - Infinite loops
  - Missing configurations
  - Unused/undefined blackboard variables
- **Layout & Navigation**:
  - Auto-layout algorithm
  - Grid snap for alignment
  - Pan, zoom, minimap
  - Collapse/expand subtrees
- **Modern UI**:
  - VSCode-style dark theme
  - Type-aware property inputs
  - Status bar with live metrics
  - Comprehensive keyboard shortcuts
  - Interactive tooltips with examples

**Usage:**
```bash
# Open in browser
open tree_editor.html

# Or via HTTP server
python -m http.server 8080
# Then visit: http://localhost:8080/tree_editor.html
```

**Quick Start:**
1. Drag nodes from left palette onto canvas
2. Shift+Click parent node
3. Click child node to connect
4. Configure properties in right panel
5. Use Auto Layout to organize
6. Save to library (Ctrl+S) or Export JSON

**Keyboard Shortcuts:**

*File & Edit:*
- `Ctrl+N`: New tree
- `Ctrl+O`: Open from library
- `Ctrl+S`: Save to library
- `Ctrl+Z/Y`: Undo/Redo

*View:*
- `Ctrl+L`: Auto layout
- `Ctrl+G`: Toggle grid
- `+/-`: Zoom in/out
- `0`: Reset zoom

*Simulation:*
- `Space`: Play/Pause simulation
- `S`: Step one tick
- `R`: Reset simulation
- `B`: Toggle breakpoint on selected node

*Timeline Scrubber:*
- `←`: Previous tick in history
- `→`: Next tick in history
- `Home`: Jump to first tick
- `End`: Return to live mode

*Node Operations:*
- `Delete`: Delete selected node
- `Backspace`: Disconnect from parent
- `C`: Collapse/expand subtree

## Documentation

See [EDITOR_SHOWCASE.md](../EDITOR_SHOWCASE.md) for:
- Detailed feature walkthrough
- Example trees (Robot Controller, E-commerce, Game AI)
- Best practices
- Common patterns
- Deployment workflow
- Troubleshooting guide

## Example Trees

The editor includes 12 interactive example trees demonstrating various patterns:

**Tutorial Trees:**
1. **Simple Sequence** - Basic sequential execution
2. **Simple Selector** - Fallback behavior
3. **Retry Pattern** - Decorator usage
4. **Parallel Tasks** - Concurrent execution

**Real-World Examples:**
5. **Robot Patrol** - Autonomous robot with battery management
6. **Game AI - NPC Behavior** - Combat and exploration AI
7. **Smart Home Automation** - Conditional logic with blackboard variables
8. **Guard Patrol Game** - Interactive 2D grid game with NPCs

**Advanced Demos:**
9. **Day in the Life** - Complex simulation with multiple needs
10. **Ultra Complex Demo** - Showcases all node types
11. **Debug Showcase** - Demonstrates debugging features
12. **Stress Test** - Large tree for performance testing

**Access Examples:**
- Click **Library** tab in the editor
- Choose **Local** or **Remote** mode
- Click any example to load it
- Or use **📁 Open Folder** to load from any directory

## Integration

### With TalkingTrees API
1. Click "API" button to save directly to backend
2. Or export JSON and POST to `/trees/` endpoint

### With External Systems
```python
# Create execution
response = requests.post(f"{API_BASE}/executions/", json={
    "tree_id": tree_id
})
execution_id = response.json()["execution_id"]

# Update sensors and tick
response = requests.post(
    f"{API_BASE}/executions/{execution_id}/tick",
    json={
        "blackboard_updates": {
            "sensor1": value1,
            "sensor2": value2
        }
    }
)

# Read action
action = response.json()["snapshot"]["blackboard"]["/action_name"]

# Execute
system.execute(action)
```

## Architecture

The editor is a single-page application built with:
- **No dependencies**: Pure HTML/CSS/JavaScript
- **localStorage**: For tree library and persistence
- **Canvas API**: For high-performance rendering
- **Modern ES6**: Clean, maintainable code

## Browser Compatibility

Tested on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Development

To modify the editor:

1. **Edit tree_editor.html** directly
2. **Reload browser** to see changes
3. **Check console** for errors (F12)

Key sections:
- **Lines 1-700**: Styles (CSS)
- **Lines 700-900**: HTML structure
- **Lines 900+**: JavaScript logic

## Tips

### Performance
- Trees with 100+ nodes: Use collapse feature
- Enable grid snap for cleaner alignment
- Use minimap for navigation
- Timeline buffers last 100 ticks (configurable in code)

### Debugging Workflow
1. **Build**: Create your tree with nodes and connections
2. **Validate**: Run validation (Ctrl+V) to check for errors
3. **Simulate**: Click **▶ Run** to start live execution
4. **Watch**: Open Blackboard Inspector to see variable changes
5. **Debug**: Set breakpoints on nodes to pause execution
6. **Scrub**: Use timeline to replay and analyze past ticks
7. **Fix**: Adjust tree based on observed behavior
8. **Iterate**: Repeat until tree behaves correctly

### Development Workflow
1. **Design**: Sketch tree structure on paper first
2. **Build**: Drag nodes, connect with Shift+Click
3. **Configure**: Set properties in right panel
4. **Validate**: Check for structural errors (Ctrl+V)
5. **Test**: Run simulation and verify behavior
6. **Save**: Store in library for reuse (Ctrl+S)
7. **Export**: Export JSON or save to API

### Best Practices
- One root node (Sequence or Selector)
- Decorators have exactly 1 child
- Actions are leaves (no children)
- Use SetBlackboardVariable for real actions
- Use Log nodes for debugging only
- Set memory correctly (Selector=false, Sequence=true)

## Support

- **Issues**: https://github.com/anthropics/talkingtrees/issues
- **Docs**: See MEMORY_AND_STATE.md
- **API**: http://localhost:8000/docs

## License

Same as TalkingTrees main project.
