# PyForest Tree Editor - Feature Guide

## ✅ Implemented Features (Production-Ready)

### 1. Pan & Zoom (DONE)
Navigate large behavior trees with ease:

- **Mouse Wheel**: Zoom in/out (10% - 500%)
- **Middle Mouse Drag**: Pan the canvas
- **Shift+Alt+Drag**: Alternative pan method
- **Zoom Buttons**: 🔍+ (zoom in), 🔍- (zoom out), Fit (frame all nodes)
- **Zoom Indicator**: Live zoom percentage display in top-right corner

**How it works:**
- All rendering uses viewport transform (translate + scale)
- Zoom anchors to mouse position (zoom where you point)
- World coordinates automatically converted for node placement

### 2. Collapse/Expand (DONE)
Manage tree complexity by hiding subtrees:

- **Click child count badge** (gray/orange circle, top-right of node): Toggle collapse
- **Collapsed indicator**: Badge turns orange with "+" symbol
- **Child count**: Shows `[N]` next to collapsed nodes
- **Automatic hiding**: All descendants hidden when parent collapsed
- **Connection hiding**: Connections to collapsed children not drawn

**Visual States:**
- Expanded: Gray badge with number (e.g., `3`)
- Collapsed: Orange badge with `+` symbol and `[3]` text

### 3. Enhanced Node Badges (DONE)
Better visual feedback for execution order:

- **Green badge (top-left)**: Execution order among siblings (1, 2, 3...)
- **Gray/Orange badge (top-right)**: Child count / collapse toggle
- **Category bar (left edge)**: Color-coded by node type

### 4. Production-Grade Canvas (DONE)
Professional editing experience:

- **Viewport transform**: Smooth pan & zoom
- **World coordinates**: Accurate placement at any zoom level
- **Visual feedback**: Zoom percentage, node counts
- **Performance**: Only visible nodes rendered

---

## 📋 Pending Features (Roadmap)

### 5. Tree Library System
Reusable component templates:

**Needed:**
- Save subtrees as templates
- Library panel with categories (Robotics, Game AI, DevOps)
- Drag from library to instantiate
- Parameterizable components (e.g., "Low Battery Handler" with configurable threshold)

**File structure:**
```
/visualization/library/
  robotics/
    low_battery_handler.json
    collision_avoidance.json
  game_ai/
    npc_behavior.json
  utilities/
    retry_pattern.json
```

### 6. Keyboard Shortcuts
Productivity enhancements:

- `Delete`: Remove selected node
- `Ctrl+C/V`: Copy/paste subtree
- `Ctrl+Z/Y`: Undo/redo
- `Ctrl+D`: Duplicate node
- `Space`: Toggle collapse/expand
- `F`: Zoom to fit
- `Ctrl+F`: Search nodes
- `+/-`: Zoom in/out
- `0`: Reset zoom to 100%

### 7. Minimap
Overview navigation:

- Fixed canvas overlay (bottom-right corner)
- Simplified tree visualization
- Viewport rectangle indicator
- Click to jump to location

### 8. Advanced Selection
Multi-node operations:

- Shift+click for multi-select
- Drag to select area
- Group move
- Group delete
- Copy/paste multiple nodes

### 9. Undo/Redo System
History management:

- State snapshots on each edit
- Undo stack (max 50 operations)
- Redo stack
- Visual indicator of history position

### 10. Node Search
Find nodes quickly:

- Search by name, type, or config value
- Highlight matching nodes
- Jump to next/previous match
- Filter palette by search

---

## 🎮 Current Controls

### Mouse Controls
| Action | Control |
|--------|---------|
| Zoom in/out | Mouse wheel |
| Pan canvas | Middle mouse drag |
| Pan canvas (alt) | Shift+Alt+drag |
| Select node | Left click |
| Drag node | Left drag |
| Connect nodes | Shift+click parent, then click child |
| Collapse/expand | Click child count badge |

### Header Buttons
| Button | Action |
|--------|--------|
| Load Example | Load robot controller demo tree |
| Auto Layout | Organize tree with automatic layout |
| 🔍+ | Zoom in (20%) |
| 🔍- | Zoom out (20%) |
| Fit | Zoom to fit all nodes |
| New | Clear canvas |
| Save to API | Save tree to PyForest backend |
| Export JSON | Download tree as JSON file |

---

## 🏗️ Architecture Notes

### Viewport Transform
```javascript
// Viewport state
let viewportX = 0;      // Pan offset X
let viewportY = 0;      // Pan offset Y
let viewportScale = 1.0; // Zoom level (0.1 - 5.0)

// Rendering with transform
ctx.save();
ctx.translate(viewportX, viewportY);
ctx.scale(viewportScale, viewportScale);
// ... draw tree ...
ctx.restore();

// Convert canvas coords to world coords
const worldX = (canvasX - viewportX) / viewportScale;
const worldY = (canvasY - viewportY) / viewportScale;
```

### Collapse State
```javascript
// Node structure
{
  id: 1,
  type: "Sequence",
  name: "My Sequence",
  x: 100,
  y: 200,
  collapsed: false,  // NEW: Collapse state
  children: [...]
}

// Visibility check
function isNodeVisible(node) {
  let parent = node.parent;
  while (parent) {
    if (parent.collapsed) return false;
    parent = parent.parent;
  }
  return true;
}
```

---

## 🚀 Next Implementation Priority

1. **Tree Library System** (Most impactful for production use)
   - Dramatically speeds up tree building
   - Enables best practices sharing
   - Critical for team workflows

2. **Keyboard Shortcuts** (Quality of life)
   - Faster editing
   - Professional UX
   - Easy to implement

3. **Undo/Redo** (Risk mitigation)
   - Safety net for editing
   - Expected feature in any editor
   - Moderate implementation effort

4. **Minimap** (Navigation aid)
   - Useful for very large trees
   - Nice-to-have visual feature
   - Lower priority than above

---

## 🎯 Production System Integration

### Current State
- ✅ Visual tree editor works locally
- ✅ Can save to API backend
- ✅ Can export JSON
- ✅ Pan/zoom for large trees
- ✅ Collapse for managing complexity

### Needed for Production
- 🔜 User authentication
- 🔜 Workspace/team support
- 🔜 Version history
- 🔜 Real-time collaboration
- 🔜 Tree validation
- 🔜 Execution monitoring
- 🔜 Tree library with sharing

See `PRODUCTION_SYSTEM.md` for full production requirements.

---

## 📖 Usage Examples

### Creating a Tree
1. Click "Load Example" to see a working tree
2. Or drag nodes from palette onto canvas
3. Shift+click parent, then click child to connect
4. Edit properties in right panel
5. Use "Auto Layout" to organize nodes

### Navigating Large Trees
1. Use mouse wheel to zoom out and see the whole tree
2. Middle-mouse drag to pan around
3. Click child count badges to collapse large subtrees
4. Click "Fit" button to frame entire tree

### Saving Work
1. Click "Export JSON" to download locally
2. Click "Save to API" to store in PyForest backend
3. Share JSON files with team

---

## 🐛 Known Limitations

1. **No undo/redo yet** - Be careful with destructive operations
2. **No multi-select** - Can only manipulate one node at a time
3. **No tree library** - Can't save/load reusable patterns yet
4. **No collaboration** - Single-user editing only
5. **No validation** - Tree errors not caught until execution
6. **Manual layout** - Auto-layout is basic, may need manual adjustment

---

## 🎨 Design Decisions

### Why Viewport Transform?
- Allows infinite canvas size
- Smooth zoom animation
- Accurate node placement at any zoom
- Standard approach in design tools (Figma, Miro)

### Why Collapse Instead of Fold?
- Simpler implementation
- Clear visual state (orange badge)
- Easier to understand (hidden vs visible)
- Faster than animated fold

### Why Click Badge to Collapse?
- Easy to discover (visible click target)
- Doesn't interfere with node selection
- Follows tree navigator UX patterns
- Clear toggle affordance

---

## 📚 Related Documentation

- `PRODUCTION_SYSTEM.md` - Full production platform design
- `MEMORY_AND_STATE.md` - Blackboard memory system
- `COMPOSITE_MEMORY.md` - Sequence/Selector memory parameter
- `AUTOMATION_PATTERNS.md` - Real-world automation examples

---

**Status**: Pan/zoom and collapse are production-ready! Tree library and keyboard shortcuts are next.
