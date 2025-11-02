#!/bin/bash
# Launch both the TalkingTrees API server and Tree Editor

echo "======================================="
echo "TalkingTrees Complete Launcher"
echo "======================================="
echo ""

# Get script directory and change to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Check if server is already running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ API server is already running at http://localhost:8000"
else
    echo "Starting API server..."
    python scripts/run_server.py > /tmp/talkingtrees_server.log 2>&1 &
    SERVER_PID=$!
    echo "✓ API server started (PID: $SERVER_PID)"
    echo "  Log file: /tmp/talkingtrees_server.log"

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
            echo "  Check /tmp/talkingtrees_server.log for errors"
        fi
    done
    echo ""
fi

# Check if HTTP server is already running on port 8080
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✓ HTTP server already running at http://localhost:8080"
else
    echo "Starting HTTP server on port 8080..."
    python3 -m http.server 8080 > /tmp/talkingtrees_http.log 2>&1 &
    HTTP_PID=$!
    echo "✓ HTTP server started (PID: $HTTP_PID)"
    sleep 1
fi

echo ""
echo "Opening Tree Editor in browser..."

# Open in default browser
EDITOR_URL="http://localhost:8080/visualization/tree_editor.html"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "$EDITOR_URL"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open "$EDITOR_URL"
else
    # Windows (Git Bash)
    start "$EDITOR_URL"
fi

echo ""
echo "======================================="
echo "TalkingTrees is now running!"
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
echo "  Editor:    $EDITOR_URL"
echo "  API:       http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "Example trees to load:"
echo "  • examples/robot_v1.json"
echo "  • examples/robot_v2.json"
echo "  • tutorials/assets/py_trees_complex.json"
echo "  • tutorials/assets/py_trees_decorators.json"
echo ""
echo "To stop servers later:"
echo "  pkill -f 'uvicorn talking_trees.api.main:app'"
echo "  pkill -f 'python3 -m http.server 8080'"
echo ""
