# TalkingTrees Visual Editors

This directory contains visual behavior tree editors for TalkingTrees.

## Files

### tree_editor.html
The professional-grade behavior tree editor with complete feature set.

**Features:**
- Modern toolbar with all essential actions
- Undo/Redo history (Ctrl+Z/Y)
- Tree library for saving/loading trees
- Validation with error checking
- Search/filter nodes
- Auto-layout algorithm
- Grid snap for alignment
- Pan, zoom, minimap
- Collapse/expand subtrees
- Export to JSON
- Save to TalkingTrees API
- Keyboard shortcuts
- Professional VSCode-style theme
- Properties panel with type-aware inputs
- Status bar with metrics

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
- `Ctrl+N`: New tree
- `Ctrl+O`: Open from library
- `Ctrl+S`: Save to library
- `Ctrl+Z/Y`: Undo/Redo
- `Ctrl+L`: Auto layout
- `Ctrl+G`: Toggle grid
- `Ctrl+V`: Validate
- `+/-`: Zoom
- `Delete`: Delete node

## Documentation

See [EDITOR_SHOWCASE.md](../EDITOR_SHOWCASE.md) for:
- Detailed feature walkthrough
- Example trees (Robot Controller, E-commerce, Game AI)
- Best practices
- Common patterns
- Deployment workflow
- Troubleshooting guide

## Example Trees

### Robot Controller Demo
```
Selector "Robot Controller" (memory=false)
├─ Sequence "Low Battery Handler" (memory=true)
│  ├─ CheckCondition "battery < 20"
│  └─ SetVariable "robot_action = charge"
├─ Sequence "Object Detection" (memory=true)
│  ├─ CheckCondition "distance < 5"
│  └─ SetVariable "robot_action = grasp"
└─ SetVariable "robot_action = patrol"
```

This tree is ready to export and test with:
```bash
python test_complete_flow.py
```

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

The professional editor is a single-page application built with:
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

### Workflow
1. **Design**: Sketch structure first
2. **Build**: Drag nodes, connect, configure
3. **Validate**: Check for errors (Ctrl+V)
4. **Save**: Store in library for reuse
5. **Test**: Export and run with test script
6. **Deploy**: Save to API for server storage

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
