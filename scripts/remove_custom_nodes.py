#!/usr/bin/env python3
"""Remove all custom nodes from TalkingTrees example trees.

Converts custom nodes to real py_trees equivalents:
- Log → Success (with descriptive name)
- Wait → TickCounter (counts N ticks before completing)
- CheckBattery → CheckBlackboardVariableValue
- GetBlackboardVariable → CheckBlackboardVariableExists
- CheckBlackboardCondition → CheckBlackboardVariableValue
"""

import json
from pathlib import Path


def convert_node(node):
    """Convert a single node from custom to py_trees equivalent."""
    node_type = node.get('node_type')

    if node_type == 'Log':
        # Convert Log to Success with descriptive name
        return {
            'node_type': 'Success',
            'name': node.get('name', 'Log'),
            'config': {}
        }

    elif node_type == 'Wait':
        # Convert Wait to TickCounter
        duration = node.get('config', {}).get('duration', 1.0)
        # TickCounter wants integer ticks, convert seconds to ticks (assume 10Hz)
        ticks = max(1, int(duration * 10))
        return {
            'node_type': 'TickCounter',
            'name': node.get('name', 'Wait'),
            'config': {
                'duration': ticks,
                'completion_status': 'SUCCESS'
            }
        }

    elif node_type == 'CheckBattery':
        # Convert CheckBattery to CheckBlackboardVariableValue
        threshold = node.get('config', {}).get('threshold', 20)
        return {
            'node_type': 'CheckBlackboardVariableValue',
            'name': node.get('name', 'Check Battery'),
            'config': {
                'variable': 'battery',
                'operator': '<',
                'value': threshold
            }
        }

    elif node_type == 'GetBlackboardVariable':
        # Convert GetBlackboardVariable to CheckBlackboardVariableExists
        variable = node.get('config', {}).get('variable', 'var')
        return {
            'node_type': 'CheckBlackboardVariableExists',
            'name': node.get('name', 'Check Variable'),
            'config': {
                'variable': variable
            }
        }

    elif node_type == 'CheckBlackboardCondition':
        # Convert CheckBlackboardCondition to CheckBlackboardVariableValue
        config = node.get('config', {})
        return {
            'node_type': 'CheckBlackboardVariableValue',
            'name': node.get('name', 'Check Condition'),
            'config': {
                'variable': config.get('variable', 'value'),
                'operator': config.get('operator_str', config.get('operator', '==')),
                'value': config.get('value', 0)
            }
        }

    # Not a custom node, return as-is (but recurse into children)
    return node


def convert_tree_recursive(node):
    """Recursively convert all nodes in a tree."""
    # Convert this node
    converted = convert_node(node)

    # Recurse into children
    if 'children' in converted and converted['children']:
        converted['children'] = [convert_tree_recursive(child) for child in converted['children']]

    return converted


def convert_file(filepath):
    """Convert a single JSON file."""
    print(f"Converting {filepath}...")

    with open(filepath) as f:
        data = json.load(f)

    # Convert the tree
    if 'root' in data:
        data['root'] = convert_tree_recursive(data['root'])

    # Write back
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

    print("  [PASS] Done")


def main():
    """Convert all example trees."""
    print("=" * 80)
    print("Removing Custom Nodes from Example Trees")
    print("=" * 80)
    print()

    examples_dir = Path('examples/trees')
    json_files = list(examples_dir.glob('*.json'))

    print(f"Found {len(json_files)} example trees")
    print()

    for filepath in sorted(json_files):
        convert_file(filepath)

    print()
    print("=" * 80)
    print("[PASS] All example trees converted to use real py_trees nodes!")
    print("=" * 80)


if __name__ == '__main__':
    main()
