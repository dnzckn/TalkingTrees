#!/bin/bash
# Quick script to run the TalkingTrees Day in Life visualization

echo "================================"
echo "TalkingTrees Visualization Launcher"
echo "================================"
echo ""

# Check if server is already running
if curl -s http://localhost:8000/trees/ > /dev/null 2>&1; then
    echo "✓ API server is already running at http://localhost:8000"
else
    echo "Starting API server..."
    python run_server.py > /tmp/talkingtrees_server.log 2>&1 &
    SERVER_PID=$!
    echo "✓ API server started (PID: $SERVER_PID)"
    echo "  Log file: /tmp/talkingtrees_server.log"

    # Wait for server to be ready
    echo "  Waiting for server to be ready..."
    for i in {1..10}; do
        if curl -s http://localhost:8000/trees/ > /dev/null 2>&1; then
            echo "  ✓ Server is ready!"
            break
        fi
        sleep 1
        echo -n "."
    done
    echo ""
fi

echo ""
echo "Opening visualization in browser..."
open visualization/day_in_life.html

echo ""
echo "================================"
echo "Instructions:"
echo "================================"
echo "1. Wait for the page to load"
echo "2. Click 'Start Simulation' button"
echo "3. Watch the simulation run!"
echo "4. Switch tabs to see:"
echo "   - Simulation View: Stats and activity log"
echo "   - Tree Visualization: Backend tree nodes"
echo ""
echo "To stop the server later, run:"
echo "  pkill -f 'uvicorn talking_trees.api.main:app'"
echo ""
