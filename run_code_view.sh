#!/bin/bash
# Launch the PyForest Code View Tool

echo "======================================="
echo "PyForest Code View Launcher"
echo "======================================="
echo ""

# Get the full path to the HTML file
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CODE_VIEW_PATH="$SCRIPT_DIR/visualization/code_view.html"

echo "Opening Code View in browser..."
echo ""

# Open in default browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "$CODE_VIEW_PATH"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open "$CODE_VIEW_PATH"
else
    # Windows (Git Bash)
    start "$CODE_VIEW_PATH"
fi

echo "======================================="
echo "Code View is now open!"
echo "======================================="
echo ""
echo "Features:"
echo "  • Visual tree display (read-only)"
echo "  • JSON TreeDefinition editor (editable)"
echo "  • py_trees Python code display (read-only)"
echo "  • Edit JSON → updates visual + Python code"
echo "  • Copy Python code to clipboard"
echo "  • Save edited JSON"
echo ""
echo "How to use:"
echo "  1. Click 'Load JSON File'"
echo "  2. Select a tree (e.g., examples/robot_v1.json)"
echo "  3. See three views: Visual | JSON | Python"
echo "  4. Edit JSON directly → click 'Apply Changes'"
echo "  5. Copy Python code for external development"
echo ""
echo "URL:"
echo "  file://$CODE_VIEW_PATH"
echo ""
