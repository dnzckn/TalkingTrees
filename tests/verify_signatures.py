#!/usr/bin/env python3
"""Automatic signature verification for TalkingTrees registry.

This script uses inspect.signature() to verify that our registry config schemas,
extractors, and builders match the actual py_trees node signatures.

This ensures perfect round-trip conversion (py_trees ↔ JSON ↔ py_trees).
"""

import inspect
import sys

sys.path.insert(0, 'src')

from talking_trees.core.builders import BUILDER_REGISTRY
from talking_trees.core.extractors import EXTRACTOR_REGISTRY
from talking_trees.core.registry import BehaviorRegistry


def get_py_trees_signature(node_type: str, implementation):
    """Get the actual __init__ signature from py_trees."""
    try:
        sig = inspect.signature(implementation.__init__)
        params = {}
        for param_name, param in sig.parameters.items():
            if param_name in ['self', 'name', 'child', 'children']:
                continue  # Skip common parameters
            params[param_name] = {
                'required': param.default == inspect.Parameter.empty,
                'default': None if param.default == inspect.Parameter.empty else param.default,
                'annotation': param.annotation if param.annotation != inspect.Parameter.empty else None
            }
        return params
    except Exception as e:
        return {'error': str(e)}


def verify_node_type(node_type: str, registry: BehaviorRegistry):
    """Verify a single node type's signature matches registry."""
    schema = registry.get_schema(node_type)
    if not schema:
        return {'status': 'NOT_REGISTERED', 'issues': []}

    implementation = registry.get_implementation(node_type)
    if not implementation:
        return {'status': 'ERROR', 'error': 'No implementation found', 'issues': []}

    actual_sig = get_py_trees_signature(node_type, implementation)

    if 'error' in actual_sig:
        return {'status': 'ERROR', 'error': actual_sig['error'], 'issues': []}

    issues = []

    # Check each config_schema parameter against actual signature
    for config_key, _config_prop in schema.config_schema.items():
        if config_key not in actual_sig:
            # Config key doesn't match any py_trees parameter
            # Check for common renamings
            possible_names = [config_key, f'{config_key}_key', f'{config_key}_name']
            found = False
            for possible in possible_names:
                if possible in actual_sig:
                    issues.append({
                        'severity': 'WARNING',
                        'message': f'Config key "{config_key}" maps to py_trees parameter "{possible}"'
                    })
                    found = True
                    break

            if not found:
                issues.append({
                    'severity': 'ERROR',
                    'message': f'Config key "{config_key}" not in py_trees signature: {list(actual_sig.keys())}'
                })

    # Check for missing parameters (py_trees has it but we don't)
    for param_name, param_info in actual_sig.items():
        if param_info['required']:
            # This is a required parameter in py_trees
            # Check if we have it in config_schema
            if param_name not in schema.config_schema:
                # Check for common renamings
                possible_configs = [param_name.replace('_key', '').replace('_name', '')]
                found = False
                for possible in possible_configs:
                    if possible in schema.config_schema:
                        found = True
                        break

                if not found:
                    issues.append({
                        'severity': 'ERROR',
                        'message': f'Required py_trees parameter "{param_name}" missing from config_schema'
                    })

    # Check if extractor exists
    has_extractor = node_type in EXTRACTOR_REGISTRY
    if not has_extractor and schema.config_schema:
        issues.append({
            'severity': 'WARNING',
            'message': 'No extractor found (needed if node has config)'
        })

    # Check if builder exists
    has_builder = node_type in BUILDER_REGISTRY
    if not has_builder:
        issues.append({
            'severity': 'WARNING',
            'message': 'No explicit builder found (will use registry.create_node fallback)'
        })

    status = 'PASS'
    if any(issue['severity'] == 'ERROR' for issue in issues):
        status = 'FAIL'
    elif any(issue['severity'] == 'WARNING' for issue in issues):
        status = 'WARNING'

    return {
        'status': status,
        'actual_signature': actual_sig,
        'config_schema': list(schema.config_schema.keys()),
        'has_extractor': has_extractor,
        'has_builder': has_builder,
        'issues': issues
    }


def main():
    """Run signature verification on all registered nodes."""
    print("=" * 80)
    print("TalkingTrees Automatic Signature Verification")
    print("=" * 80)
    print()

    registry = BehaviorRegistry()
    all_schemas = registry.get_all_schemas()
    all_node_types = list(all_schemas.keys())

    results = {}
    for node_type in sorted(all_node_types):
        results[node_type] = verify_node_type(node_type, registry)

    # Summary
    passed = sum(1 for r in results.values() if r['status'] == 'PASS')
    warned = sum(1 for r in results.values() if r['status'] == 'WARNING')
    failed = sum(1 for r in results.values() if r['status'] == 'FAIL')
    errors = sum(1 for r in results.values() if r['status'] == 'ERROR')

    print(" Summary:")
    print(f"   [PASS] PASS:    {passed}/{len(all_node_types)}")
    print(f"   [WARNING]  WARNING: {warned}/{len(all_node_types)}")
    print(f"   [FAIL] FAIL:    {failed}/{len(all_node_types)}")
    print(f"    ERROR:   {errors}/{len(all_node_types)}")
    print()

    # Detailed results
    if failed > 0 or errors > 0:
        print("=" * 80)
        print("[FAIL] FAILURES AND ERRORS")
        print("=" * 80)
        print()

        for node_type in sorted(all_node_types):
            result = results[node_type]
            if result['status'] in ['FAIL', 'ERROR']:
                print(f"{'=' * 80}")
                print(f"Node: {node_type} - {result['status']}")
                print(f"{'=' * 80}")

                if result['status'] == 'ERROR':
                    print(f"Error: {result.get('error', 'Unknown error')}")
                else:
                    print(f"Actual py_trees signature: {result['actual_signature']}")
                    print(f"Registry config_schema:    {result['config_schema']}")
                    print(f"Has extractor: {result['has_extractor']}")
                    print(f"Has builder:   {result['has_builder']}")
                    print()
                    print("Issues:")
                    for issue in result['issues']:
                        print(f"  [{issue['severity']}] {issue['message']}")
                print()

    if warned > 0:
        print("=" * 80)
        print("[WARNING]  WARNINGS")
        print("=" * 80)
        print()

        for node_type in sorted(all_node_types):
            result = results[node_type]
            if result['status'] == 'WARNING':
                print(f"{node_type}:")
                for issue in result['issues']:
                    if issue['severity'] == 'WARNING':
                        print(f"  - {issue['message']}")
                print()

    print("=" * 80)

    # Exit code
    if failed > 0 or errors > 0:
        print("[FAIL] Verification FAILED")
        sys.exit(1)
    elif warned > 0:
        print("[WARNING]  Verification passed with warnings")
        sys.exit(0)
    else:
        print("[PASS] All signatures verified successfully!")
        sys.exit(0)


if __name__ == '__main__':
    main()
