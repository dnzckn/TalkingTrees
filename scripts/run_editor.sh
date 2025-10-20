#!/bin/bash
# Launch the PyForest Tree Editor with API server

echo "======================================="
echo "PyForest Tree Editor Launcher"
echo "======================================="
echo ""

# Check if API server is already running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ API server is already running at http://localhost:8000"
else
    echo "Starting API server..."
    python run_server.py > /tmp/pyforest_server.log 2>&1 &
    SERVER_PID=$!
    echo "✓ API server started (PID: $SERVER_PID)"
    echo "  Log file: /tmp/pyforest_server.log"

    # Wait for server to be ready
    echo "  Waiting for server to be ready..."
    for i in {1..15}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "  ✓ Server is ready!"
            break
        fi
        sleep 1
        if [ $i -eq 15 ]; then
            echo "  ⚠ Server didn't start in time, but continuing..."
            echo "  Check /tmp/pyforest_server.log for errors"
        fi
    done
    echo ""
fi

echo ""
echo "Opening Tree Editor in browser..."
echo ""

# Get the full path to the HTML file
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
EDITOR_PATH="$SCRIPT_DIR/../visualization/tree_editor.html"

# Open in default browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "$EDITOR_PATH"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open "$EDITOR_PATH"
else
    # Windows (Git Bash)
    start "$EDITOR_PATH"
fi

echo "======================================="
echo "Tree Editor is now open!"
echo "======================================="
echo ""
echo "Features:"
echo "  • Create/edit behavior trees visually"
echo "  • Load JSON files (examples/, tutorials/)"
echo "  • Save to local JSON file"
echo "  • Save to API (with server running)"
echo "  • Export/import trees"
echo ""
echo "URLs:"
echo "  Editor:    file://$EDITOR_PATH"
echo "  API:       http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "Example trees to load:"
echo "  • examples/robot_v1.json"
echo "  • examples/robot_v2.json"
echo "  • tutorials/py_trees_complex.json"
echo "  • tutorials/py_trees_decorators.json"
echo ""
echo "To stop the API server later:"
echo "  pkill -f 'uvicorn py_forest.api.main:app'"
echo ""
