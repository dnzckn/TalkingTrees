# PyForest Launcher Scripts Guide

Quick reference for launching PyForest tools.

---

## 🚀 Quick Start Scripts

### 1. Tree Editor Pro (Main Editor)

```bash
./run_editor.sh
```

**What it does:**
- ✅ Starts the API server (if not running)
- ✅ Opens the PyForest Tree Editor Pro in your browser
- ✅ Provides full visual tree editing capabilities

**Use when:**
- Creating/editing behavior trees visually
- Loading and modifying existing trees (examples/, tutorials/)
- Testing trees with the integrated executor
- Saving trees to API or local files

**Features:**
- Visual node-based editor
- Drag-and-drop tree building
- Load/save JSON files
- API integration (save to PyForest server)
- Live execution and debugging

---

### 2. Code View (NEW: Visual ↔ JSON ↔ Python)

```bash
./run_code_view.sh
```

**What it does:**
- ✅ Opens the PyForest Code View tool
- ✅ Shows three synchronized views of your tree
- ✅ No API server needed (standalone tool)

**Use when:**
- You want to see Python code for a tree
- Editing JSON directly while seeing visual + code
- Copying py_trees code for external development
- Learning how visual nodes map to py_trees API

**Features:**
- **Visual Tree** (read-only) - See tree structure
- **JSON Editor** (editable) - Direct TreeDefinition editing
- **Python Code** (read-only) - Generated py_trees code
- Edit JSON → updates visual + Python automatically
- Copy Python code to clipboard
- Save edited JSON

---

### 3. Day in Life Simulation

```bash
./run_visualization.sh
```

**What it does:**
- ✅ Starts the API server (if not running)
- ✅ Opens the Day in Life simulation demo

**Use when:**
- Running the autonomous robot simulation demo
- Demonstrating PyForest capabilities
- Testing behavior trees in a simulated environment

---

### 4. Visualization with HTTP Server

```bash
./run_visualization_server.sh
```

**What it does:**
- ✅ Starts the API server (if not running)
- ✅ Starts a local HTTP server on port 8080
- ✅ Opens visualization via HTTP (not file://)

**Use when:**
- Need to avoid CORS issues
- Testing with multiple visualizations
- Serving visualizations on a local network

---

## 🔧 Manual Server Launch

### API Server Only

```bash
python run_server.py
```

**Options:**
```bash
python run_server.py --host 0.0.0.0 --port 8000 --reload
```

**URLs:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📁 Which Files to Open

### Tree Editor Pro (Recommended)
**File:** `visualization/tree_editor_pro.html`
**Launch:** `./run_editor.sh`
**Use for:** Visual tree creation/editing

### Code View (NEW)
**File:** `visualization/code_view.html`
**Launch:** `./run_code_view.sh`
**Use for:** Viewing Python code + JSON editing

### Other Visualizations

**Tree Diff Viewer:**
- File: `visualization/tree_diff_viewer.html`
- Use for: Comparing tree versions
- Open directly in browser (no server needed)

**Basic Tree Editor:**
- File: `visualization/tree_editor.html`
- Use for: Simple tree editing
- Open directly in browser

**Guard Patrol Game:**
- File: `visualization/guard_patrol_game.html`
- Use for: Game demo
- Open directly in browser

**Day in Life:**
- File: `visualization/day_in_life.html`
- Use for: Simulation demo
- Launch: `./run_visualization.sh`

---

## 🛑 Stopping Servers

### Stop API Server
```bash
pkill -f 'uvicorn py_forest.api.main:app'
```

### Stop HTTP Server
```bash
pkill -f 'python3 -m http.server 8080'
```

### Stop All
```bash
pkill -f 'uvicorn py_forest.api.main:app'
pkill -f 'python3 -m http.server 8080'
```

---

## 📋 Prerequisites

### Required
- Python 3.8+
- PyForest installed (`pip install -e .` from repo root)
- uvicorn (`pip install uvicorn[standard]`)

### Optional
- py_trees (for py_trees integration)
- requests (for REST API tests)

---

## 🔍 Troubleshooting

### "Port already in use"
The scripts check if servers are already running and reuse them.

### "Server not starting"
Check the log file:
```bash
cat /tmp/pyforest_server.log
```

### "API not responding"
Verify the server is running:
```bash
curl http://localhost:8000/health
```

### "Can't find tree files"
Example trees are in:
- `examples/` - Basic examples
- `tutorials/` - SDK tutorial output files

---

## 💡 Recommended Workflow

### For New Users
1. Run `./run_editor.sh`
2. Load `examples/robot_v1.json`
3. Explore the visual editor
4. Try executing the tree
5. Make modifications and save

### For py_trees Users
1. Run tutorials: `python tutorials/05_py_trees_integration.py`
2. Launch editor: `./run_editor.sh`
3. Load generated files: `tutorials/py_trees_decorators.json`
4. Visualize and modify trees
5. Save back to JSON or API

### For Development
1. Start server: `python run_server.py`
2. Run tests: `python tests/test_py_trees_adapter.py`
3. Open editor for visual testing
4. Use API docs at http://localhost:8000/docs

---

## 📊 Script Comparison

| Script | API Server | HTTP Server | Opens | Best For |
|--------|------------|-------------|-------|----------|
| `run_editor.sh` | ✅ | ❌ | Tree Editor Pro | **Visual editing** |
| `run_code_view.sh` | ❌ | ❌ | Code View | **Code/JSON editing** |
| `run_visualization.sh` | ✅ | ❌ | Day in Life | **Quick demo** |
| `run_visualization_server.sh` | ✅ | ✅ | Day in Life (HTTP) | **CORS-free** |
| `run_server.py` | ✅ | ❌ | Nothing | **Manual control** |

---

## ✅ Summary

**Just want to edit trees visually?**
```bash
./run_editor.sh
```

**Want to see Python code + edit JSON?**
```bash
./run_code_view.sh
```

**Want to see a demo?**
```bash
./run_visualization.sh
```

**Need the API for testing?**
```bash
python run_server.py
```

All scripts are **up to date** and handle server management automatically!
