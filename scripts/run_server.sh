#!/bin/bash
# Launch only the TalkingTrees API server

echo "======================================="
echo "TalkingTrees API Server"
echo "======================================="
echo ""

# Check if server is already running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠ API server is already running at http://localhost:8000"
    echo ""
    echo "To stop it, run:"
    echo "  pkill -f 'uvicorn talking_trees.api.main:app'"
    echo ""
    exit 0
fi

echo "Starting API server..."

# Get script directory and change to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Start the server
python scripts/run_server.py

echo ""
echo "Server stopped."
echo ""
