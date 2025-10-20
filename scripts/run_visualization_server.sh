#!/bin/bash
# Run both the API server and a simple HTTP server for the visualization

echo "================================"
echo "PyForest Visualization Launcher"
echo "================================"
echo ""

# Check if API server is already running
if curl -s http://localhost:8000/trees/ > /dev/null 2>&1; then
    echo "✓ API server is already running at http://localhost:8000"
else
    echo "Starting API server..."
    python run_server.py > /tmp/pyforest_server.log 2>&1 &
    SERVER_PID=$!
    echo "✓ API server started (PID: $SERVER_PID)"

    # Wait for server to be ready
    echo "  Waiting for server to be ready..."
    for i in {1..10}; do
        if curl -s http://localhost:8000/trees/ > /dev/null 2>&1; then
            echo "  ✓ Server is ready!"
            break
        fi
        sleep 1
    done
fi

echo ""
echo "Starting HTTP server for visualization..."
cd /Users/deniz/Documents/GitHub/py_forest

# Check if port 8080 is already in use
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✓ HTTP server already running at http://localhost:8080"
else
    python3 -m http.server 8080 > /tmp/pyforest_http.log 2>&1 &
    HTTP_PID=$!
    echo "✓ HTTP server started (PID: $HTTP_PID)"
    sleep 2
fi

echo ""
echo "Opening visualization in browser..."
open http://localhost:8080/visualization/day_in_life.html

echo ""
echo "================================"
echo "Visualization is now running!"
echo "================================"
echo ""
echo "URLs:"
echo "  Visualization: http://localhost:8080/visualization/day_in_life.html"
echo "  API Server:    http://localhost:8000"
echo "  API Docs:      http://localhost:8000/docs"
echo ""
echo "Instructions:"
echo "  1. Click 'Start Simulation' button"
echo "  2. Watch the simulation run!"
echo "  3. Switch between tabs to see different views"
echo ""
echo "To stop servers later, run:"
echo "  pkill -f 'uvicorn py_forest.api.main:app'"
echo "  pkill -f 'python3 -m http.server 8080'"
echo ""
