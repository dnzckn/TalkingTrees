# TalkingTrees GUI Usage Guide

## Understanding the Two Tabs

The GUI has **two tabs** in the left sidebar:

### 1. Node Palette Tab (Default)
- **Purpose**: Shows all available py_trees node types that you can drag onto the canvas
- **How to use**: 
  - Drag nodes from the palette onto the canvas
  - Shift+Click parent → Click child to connect nodes
  - Build your behavior tree visually

### 2. Library Tab
- **Purpose**: Shows saved demo trees and your saved trees
- **How to use**:
  - Click on a tree to load it into the editor
  - The tree will replace your current canvas

## Current Demo Trees

After the latest update, the library contains 2 demo trees using **real py_trees nodes**:

1. **Robot Controller Demo**
   - Uses EternalGuard and SetBlackboardVariable
   - Demonstrates conditional execution patterns
   - 6 nodes total

2. **Simple Patrol Behavior**  
   - Uses EternalGuard and SetBlackboardVariable
   - Simple 2-node example for learning
   - Good starting point

## How to Fix "Can't Drag Anything"

If you can't drag nodes:

1. **Make sure you're on the "Node Palette" tab** (not the Library tab)
2. Click on "Node Palette" in the left sidebar tabs
3. You should see node categories: COMPOSITES, DECORATORS, CONDITIONS, etc.
4. Now you can drag nodes onto the canvas

The **Library tab only shows saved trees** - you can't drag individual nodes from there.

## Removed Nodes

The following custom nodes have been **removed** as they don't exist in py_trees:
- ❌ CheckBattery
- ❌ CheckBlackboardCondition  
- ❌ Log
- ❌ Wait
- ❌ GetBlackboardVariable

Use real py_trees equivalents instead:
- ✅ EternalGuard (conditional decorator)
- ✅ CheckBlackboardVariableValue
- ✅ SetBlackboardVariable
- ✅ TickCounter (for timing)

## Quick Start

1. Click **Node Palette** tab
2. Drag a **Sequence** or **Selector** onto the canvas (this will be your root)
3. Drag more nodes onto the canvas
4. Connect them: Shift+Click parent → Click child
5. Configure nodes by clicking on them
6. Export to JSON or Python code

## Troubleshooting

- **Library tab is empty**: The demo trees will be created automatically on first load
- **Can't see nodes**: Switch to "Node Palette" tab
- **Drag not working**: Make sure you're clicking and holding on a node in the palette
- **Old custom nodes showing**: Clear browser cache and refresh (Ctrl+Shift+R)
