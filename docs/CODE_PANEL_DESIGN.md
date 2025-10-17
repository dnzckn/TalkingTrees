# Code Panel Feature - Design Document

## Vision

Add a code panel to the visual tree editor that shows Python code representation and allows bidirectional editing:
- **Visual Editor** ↔ **Python Code** ↔ **JSON Format**

## Use Cases

1. **Code Reference**: See the py_trees Python code for the current tree
2. **Copy/Paste Workflow**: Copy code to external IDE, edit, run, and load result
3. **Live Code Editing**: Edit Python code directly in the panel, updates visual tree
4. **Learning**: Understand how visual nodes map to py_trees code
5. **Hybrid Workflow**: Switch between visual and code-based editing

---

## Implementation Approaches

### Approach 1: Three-Panel Display (Recommended)

```
┌──────────────┬──────────────┬──────────────┐
│   Visual     │    JSON      │  py_trees    │
│   Tree       │   (editable) │  (reference) │
│  (editable)  │              │              │
└──────────────┴──────────────┴──────────────┘
```

**Panels:**
1. **Visual Tree** (left) - Current drag-and-drop editor
2. **JSON Editor** (center) - Editable TreeDefinition JSON
3. **Python Code** (right) - Read-only py_trees code

**Data Flow:**
```
Visual Edit → TreeDefinition → Update JSON Panel → Regenerate py_trees code
JSON Edit → Parse JSON → Update TreeDefinition → Redraw visual → Regenerate py_trees code
py_trees code → (Read-only, copy to clipboard)
```

**Pros:**
- ✅ Safe (no Python code parsing/eval)
- ✅ JSON is 1:1 with save format
- ✅ Direct control over tree structure
- ✅ py_trees code useful for external development

**Cons:**
- ❌ Can't edit py_trees code directly in the UI

---

### Approach 2: Dual-Panel with py_trees Code Editing (Complex)

```
┌──────────────┬──────────────┐
│   Visual     │  py_trees    │
│   Tree       │  Python Code │
│  (editable)  │  (editable)  │
└──────────────┴──────────────┘
```

**Data Flow:**
```
Visual Edit → TreeDefinition → Generate py_trees code
py_trees Edit → Parse/Execute Python → Generate TreeDefinition → Redraw visual
```

**Implementation:**
- Use Web Workers to execute Python code safely
- Options: Pyodide (Python in browser), Skulpt, Brython
- Parse Python AST or execute and capture result

**Pros:**
- ✅ Full py_trees API available
- ✅ Natural Python workflow

**Cons:**
- ❌ Security concerns (executing user code)
- ❌ Complex Python runtime in browser
- ❌ Error handling complexity
- ❌ Performance overhead
- ❌ Need full py_trees library in browser

---

### Approach 3: Smart Code Snippets (Middle Ground)

```
┌──────────────┬──────────────┐
│   Visual     │  Code View   │
│   Tree       │  (switchable)│
│  (editable)  │              │
└──────────────┴──────────────┘
```

**Code View Modes:**
1. **py_trees Code** (read-only, for reference)
2. **JSON Editor** (editable, direct tree editing)
3. **Code Snippets** (pre-built py_trees snippets to add branches)

**Snippets Example:**
```python
# Battery Check Sequence
battery_check = py_trees.composites.Sequence("Battery Check", memory=False)
battery_check.add_child(
    py_trees.behaviours.CheckBlackboardVariableValue(
        name="Battery Low?",
        check=ComparisonExpression('battery_level', operator.lt, 20)
    )
)
# [Add to Tree] button
```

**Pros:**
- ✅ Safe (snippets are pre-validated)
- ✅ Best of both worlds
- ✅ Educational (shows py_trees patterns)
- ✅ Practical (common patterns)

**Cons:**
- ❌ Limited to predefined snippets
- ❌ Not full code editing

---

## Recommended Implementation: Approach 1 Enhanced

### Layout

```html
<div class="app">
  <div class="toolbar">...</div>

  <div class="left-panel">
    <!-- Existing node palette -->
  </div>

  <div class="center-panel">
    <div class="tabs">
      <button class="tab active" data-view="visual">Visual</button>
      <button class="tab" data-view="json">JSON</button>
    </div>

    <div class="view visual-view active">
      <!-- Existing canvas -->
    </div>

    <div class="view json-view">
      <textarea id="json-editor"></textarea>
      <button id="apply-json">Apply Changes</button>
    </div>
  </div>

  <div class="right-panel">
    <div class="tabs">
      <button class="tab active" data-view="properties">Properties</button>
      <button class="tab" data-view="code">Code</button>
    </div>

    <div class="view properties-view active">
      <!-- Existing properties panel -->
    </div>

    <div class="view code-view">
      <div class="code-header">
        <span>py_trees Code (Read-only)</span>
        <button id="copy-code">Copy</button>
      </div>
      <pre id="python-code"></pre>
    </div>
  </div>
</div>
```

### Key Functions

```javascript
// Generate py_trees code from TreeDefinition
function generatePyTreesCode(treeDefinition) {
    let code = `import py_trees\nimport operator\nfrom py_trees.common import ComparisonExpression\n\n`;

    code += `# ${treeDefinition.metadata.name} v${treeDefinition.metadata.version}\n\n`;

    code += generateNodeCode(treeDefinition.root, 0);

    return code;
}

function generateNodeCode(node, indent) {
    const ind = '    '.repeat(indent);
    let code = '';

    switch(node.node_type) {
        case 'Sequence':
            code += `${ind}${node.name.toLowerCase().replace(/\s+/g, '_')} = py_trees.composites.Sequence("${node.name}", memory=${node.config.memory || false})\n`;
            break;
        case 'Selector':
            code += `${ind}${node.name.toLowerCase().replace(/\s+/g, '_')} = py_trees.composites.Selector("${node.name}", memory=${node.config.memory || false})\n`;
            break;
        case 'CheckBlackboardVariableValue':
            const varName = node.config.variable_name;
            const operator = node.config.operator;
            const value = node.config.expected_value;
            code += `${ind}check_${varName} = ComparisonExpression('${varName}', operator.${getOperatorName(operator)}, ${JSON.stringify(value)})\n`;
            code += `${ind}${node.name.toLowerCase().replace(/\s+/g, '_')} = py_trees.behaviours.CheckBlackboardVariableValue(\n`;
            code += `${ind}    name="${node.name}",\n`;
            code += `${ind}    check=check_${varName}\n`;
            code += `${ind})\n`;
            break;
        // ... other node types
    }

    if (node.children) {
        for (const child of node.children) {
            code += generateNodeCode(child, indent + 1);
            code += `${ind}${node.name.toLowerCase().replace(/\s+/g, '_')}.add_child(${child.name.toLowerCase().replace(/\s+/g, '_')})\n`;
        }
    }

    return code;
}

// Update code panel when tree changes
function updateCodePanel() {
    if (!currentTree) return;

    const treeDefinition = serializeTreeToDefinition();
    const pythonCode = generatePyTreesCode(treeDefinition);

    document.getElementById('python-code').textContent = pythonCode;
}

// Apply JSON edits to tree
function applyJsonEdits() {
    const jsonText = document.getElementById('json-editor').value;

    try {
        const treeDefinition = JSON.parse(jsonText);

        // Validate structure
        if (!treeDefinition.root || !treeDefinition.metadata) {
            throw new Error('Invalid tree structure');
        }

        // Rebuild tree from definition
        currentTree = deserializeTreeFromDefinition(treeDefinition);

        // Redraw
        renderTree();
        updateCodePanel();

        showNotification('JSON applied successfully', 'success');
    } catch (error) {
        showNotification(`JSON error: ${error.message}`, 'error');
    }
}
```

### User Workflow

**Workflow 1: Visual → Code**
```
1. User edits tree visually (drag nodes, change properties)
2. JSON panel and py_trees code panel update automatically
3. User copies py_trees code to use in external project
```

**Workflow 2: JSON → Visual**
```
1. User switches to JSON tab
2. User edits TreeDefinition JSON directly
3. User clicks "Apply Changes"
4. Visual tree updates
5. py_trees code regenerates
```

**Workflow 3: External → Editor**
```
1. User writes py_trees code in VS Code
2. User runs: tree = pf.from_py_trees(root, "Tree", "1.0")
3. User runs: pf.save_tree(tree, "tree.json")
4. User loads tree.json in editor
5. User sees visual + JSON + py_trees code
```

---

## Implementation Phases

### Phase 1: Code Display (1-2 hours)
- ✅ Add code panel to right sidebar
- ✅ Add tab switching (Properties / Code)
- ✅ Implement `generatePyTreesCode()` for basic nodes
- ✅ Auto-update on tree changes
- ✅ Copy to clipboard button

### Phase 2: JSON Editing (1-2 hours)
- ✅ Add JSON view tab to center panel
- ✅ Add JSON editor (textarea or CodeMirror)
- ✅ Implement `applyJsonEdits()` with validation
- ✅ Error handling and user feedback
- ✅ Sync between visual and JSON views

### Phase 3: Enhanced Code Generation (2-3 hours)
- ✅ Support all node types (decorators, conditions, etc.)
- ✅ Proper variable naming
- ✅ Add comments explaining tree structure
- ✅ Format code nicely (indentation, spacing)
- ✅ Add imports and boilerplate

### Phase 4: Code Snippets (Optional, 2-3 hours)
- ✅ Library of common patterns
- ✅ Snippet browser
- ✅ Insert snippet → generates nodes
- ✅ Customizable snippets

---

## Technical Considerations

### Security
- ✅ No eval/exec of user code (Approach 1)
- ✅ JSON validation only
- ✅ Safe to deploy

### Performance
- ✅ Code generation is fast (pure string manipulation)
- ✅ JSON parsing is native
- ✅ No external dependencies for basic version

### UX Challenges
1. **Keeping sync**: Visual ↔ JSON changes need immediate sync
2. **Error handling**: Invalid JSON needs clear error messages
3. **Layout**: Three panels might feel cramped on small screens
4. **Learning curve**: Users need to understand JSON structure

### Solutions
1. **Auto-save state**: Preserve user's tab preferences
2. **Collapsible panels**: Allow hiding panels to focus
3. **Tooltips and help**: Explain JSON structure
4. **Examples**: Provide sample trees to learn from

---

## Alternative: Separate Code View Tool

Instead of embedding in main editor, create a separate tool:

**File:** `visualization/code_view.html`

**Purpose:** Load JSON tree, show side-by-side:
- Visual tree (read-only)
- JSON (editable)
- py_trees code (read-only)

**Benefits:**
- ✅ Don't clutter main editor
- ✅ Focused tool for code-centric workflow
- ✅ Easier to implement
- ✅ Less risk to existing editor

**Usage:**
```bash
./run_code_view.sh tree.json
```

---

## Decision Matrix

| Approach | Complexity | Safety | Flexibility | Recommendation |
|----------|-----------|--------|-------------|----------------|
| **Three-Panel (JSON edit)** | Medium | ✅ High | ✅ High | **✅ Recommended** |
| **py_trees code edit** | High | ⚠️ Medium | ✅ Very High | Future enhancement |
| **Code snippets** | Medium | ✅ High | ⚠️ Medium | Nice-to-have |
| **Separate tool** | Low | ✅ High | ✅ High | **✅ Quick win** |

---

## Recommended Path Forward

### Immediate (1-2 hours): Create Separate Tool
Create `visualization/code_view.html` as a focused tool for code viewing/JSON editing.

**Benefits:**
- Quick to implement
- No risk to existing editor
- Proves the concept
- User can try it immediately

### Future (4-6 hours): Integrate into Main Editor
Add three-panel view to `tree_editor_pro.html` with full JSON editing support.

**Benefits:**
- Seamless workflow
- Professional polish
- Feature parity with other tree editors

---

## Next Steps

**Option A: Prototype First**
1. Create `visualization/code_view.html` (separate tool)
2. Test with users
3. Gather feedback
4. Integrate into main editor if successful

**Option B: Full Integration**
1. Enhance `tree_editor_pro.html` directly
2. Add three-panel layout
3. Implement JSON editing + py_trees code display
4. Test thoroughly

---

## Questions for User

1. **Priority**: Do you want a quick prototype (separate tool) or full integration?
2. **Code editing**: How important is editing py_trees code directly (vs JSON)?
3. **Layout**: Three-panel layout or tabbed views?
4. **Use case**: What's your primary use case for this feature?

---

## Conclusion

The **three-panel approach with JSON editing** provides the best balance of power, safety, and feasibility. It enables:

✅ Visual editing (existing)
✅ Direct JSON editing (new)
✅ py_trees code reference (new)
✅ Safe implementation
✅ Fast performance

The **separate tool approach** is the fastest path to getting this in your hands for testing.
