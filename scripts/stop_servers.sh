#!/bin/bash
# Stop all TalkingTrees servers

echo "======================================="
echo "Stopping TalkingTrees Servers"
echo "======================================="
echo ""

# Stop API server
if pgrep -f 'uvicorn talking_trees.api.main:app' > /dev/null; then
    echo "Stopping API server..."
    pkill -f 'uvicorn talking_trees.api.main:app'
    echo "✓ API server stopped"
else
    echo "ℹ API server not running"
fi

# Stop HTTP server
if pgrep -f 'python3 -m http.server 8080' > /dev/null; then
    echo "Stopping HTTP server..."
    pkill -f 'python3 -m http.server 8080'
    echo "✓ HTTP server stopped"
else
    echo "ℹ HTTP server not running"
fi

echo ""
echo "All servers stopped."
echo ""
