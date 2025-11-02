#!/bin/bash
# Launch only the TalkingTrees Tree Editor via HTTP server
# Note: The editor will connect to http://localhost:8000 for API if available

echo "======================================="
echo "TalkingTrees Tree Editor"
echo "======================================="
echo ""

# Get script directory and change to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Check if API server is running (just informational)
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ API server detected at http://localhost:8000"
else
    echo "ℹ Note: API server not detected."
    echo "  The editor will work, but API features won't be available."
    echo "  To start the server, run: ./scripts/run_server.sh"
fi

echo ""

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
echo "Tree Editor is now running!"
echo "======================================="
echo ""
echo "URLs:"
echo "  Editor: $EDITOR_URL"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "  API:    http://localhost:8000"
fi
echo ""
echo "To stop the HTTP server:"
echo "  pkill -f 'python3 -m http.server 8080'"
echo ""
