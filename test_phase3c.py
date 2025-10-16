"""Test script for Phase 3C debugging features."""

import requests
from datetime import datetime
from uuid import uuid4

BASE_URL = "http://127.0.0.1:8000"

def test_debug_endpoints():
    """Test debugging endpoints."""
    print("=" * 60)
    print("Phase 3C: Testing Debug Endpoints")
    print("=" * 60)

    # 1. Create a simple tree
    print("\n1. Creating test tree...")
    tree_def = {
        "$schema": "1.0.0",
        "tree_id": str(uuid4()),
        "metadata": {
            "name": "Debug Test Tree",
            "version": "1.0.0",
            "description": "Test tree for Phase 3C debugging",
            "tags": ["test", "debug"]
        },
        "root": {
            "node_type": "Sequence",
            "name": "Root Sequence",
            "config": {},
            "children": [
                {
                    "node_type": "Success",
                    "name": "Step 1",
                    "config": {}
                },
                {
                    "node_type": "Success",
                    "name": "Step 2",
                    "config": {}
                }
            ]
        }
    }

    r = requests.post(f"{BASE_URL}/trees/", json=tree_def)
    if r.status_code != 201:
        print(f"   ERROR: Failed to create tree: {r.status_code}")
        print(f"   Response: {r.text}")
        return False

    tree_id = r.json()["tree_id"]
    print(f"   ✓ Tree created: {tree_id}")

    # 2. Start execution
    print("\n2. Starting execution...")
    r = requests.post(f"{BASE_URL}/executions/", json={"tree_id": tree_id})
    if r.status_code != 200:
        print(f"   ERROR: Failed to start execution: {r.status_code}")
        print(f"   Response: {r.text}")
        return False

    exec_id = r.json()["execution_id"]
    print(f"   ✓ Execution started: {exec_id}")

    # 3. Get initial debug state
    print("\n3. Getting initial debug state...")
    r = requests.get(f"{BASE_URL}/debug/executions/{exec_id}")
    if r.status_code != 200:
        print(f"   ERROR: Failed to get debug state: {r.status_code}")
        print(f"   Response: {r.text}")
        return False

    debug_state = r.json()
    print(f"   ✓ Paused: {debug_state['is_paused']}")
    print(f"   ✓ Breakpoints: {len(debug_state['breakpoints'])}")
    print(f"   ✓ Watches: {len(debug_state['watches'])}")

    # 4. Get tree snapshot to find node IDs
    print("\n4. Getting tree snapshot...")
    r = requests.post(f"{BASE_URL}/executions/{exec_id}/snapshot")
    if r.status_code != 200:
        print(f"   ERROR: Failed to get snapshot: {r.status_code}")
        print(f"   Response: {r.text}")
        return False

    snapshot = r.json()
    root_node_id = snapshot["tree"]["root"]["id"]
    print(f"   ✓ Root node ID: {root_node_id}")

    # 5. Add breakpoint
    print("\n5. Adding breakpoint...")
    r = requests.post(
        f"{BASE_URL}/debug/executions/{exec_id}/breakpoints",
        json={"node_id": root_node_id}
    )
    if r.status_code != 200:
        print(f"   ERROR: Failed to add breakpoint: {r.status_code}")
        print(f"   Response: {r.text}")
        return False

    debug_state = r.json()
    print(f"   ✓ Breakpoint added")
    print(f"   ✓ Total breakpoints: {len(debug_state['breakpoints'])}")

    # 6. Toggle breakpoint
    print("\n6. Toggling breakpoint...")
    r = requests.post(
        f"{BASE_URL}/debug/executions/{exec_id}/breakpoints/{root_node_id}/toggle"
    )
    if r.status_code != 200:
        print(f"   ERROR: Failed to toggle breakpoint: {r.status_code}")
        print(f"   Response: {r.text}")
        return False

    debug_state = r.json()
    bp_enabled = list(debug_state['breakpoints'].values())[0]['enabled']
    print(f"   ✓ Breakpoint toggled to: {bp_enabled}")

    # 7. Add watch expression
    print("\n7. Adding watch expression...")
    r = requests.post(
        f"{BASE_URL}/debug/executions/{exec_id}/watches",
        json={
            "key": "test_counter",
            "condition": "change"
        }
    )
    if r.status_code != 200:
        print(f"   ERROR: Failed to add watch: {r.status_code}")
        print(f"   Response: {r.text}")
        return False

    debug_state = r.json()
    print(f"   ✓ Watch added")
    print(f"   ✓ Total watches: {len(debug_state['watches'])}")

    # 8. Set step mode
    print("\n8. Setting step mode...")
    r = requests.post(
        f"{BASE_URL}/debug/executions/{exec_id}/step",
        json={"mode": "step_over", "count": 1}
    )
    if r.status_code != 200:
        print(f"   ERROR: Failed to set step mode: {r.status_code}")
        print(f"   Response: {r.text}")
        return False

    debug_state = r.json()
    print(f"   ✓ Step mode set to: {debug_state['step_mode']}")

    # 9. Test pause
    print("\n9. Testing pause...")
    r = requests.post(f"{BASE_URL}/debug/executions/{exec_id}/pause")
    if r.status_code != 200:
        print(f"   ERROR: Failed to pause: {r.status_code}")
        print(f"   Response: {r.text}")
        return False

    debug_state = r.json()
    print(f"   ✓ Paused: {debug_state['is_paused']}")

    # 10. Test resume
    print("\n10. Testing resume...")
    r = requests.post(f"{BASE_URL}/debug/executions/{exec_id}/continue")
    if r.status_code != 200:
        print(f"   ERROR: Failed to resume: {r.status_code}")
        print(f"   Response: {r.text}")
        return False

    debug_state = r.json()
    print(f"   ✓ Paused: {debug_state['is_paused']}")

    # 11. Remove watch
    print("\n11. Removing watch...")
    r = requests.delete(f"{BASE_URL}/debug/executions/{exec_id}/watches/test_counter")
    if r.status_code != 200:
        print(f"   ERROR: Failed to remove watch: {r.status_code}")
        print(f"   Response: {r.text}")
        return False

    debug_state = r.json()
    print(f"   ✓ Watch removed")
    print(f"   ✓ Total watches: {len(debug_state['watches'])}")

    # 12. Remove breakpoint
    print("\n12. Removing breakpoint...")
    r = requests.delete(
        f"{BASE_URL}/debug/executions/{exec_id}/breakpoints/{root_node_id}"
    )
    if r.status_code != 200:
        print(f"   ERROR: Failed to remove breakpoint: {r.status_code}")
        print(f"   Response: {r.text}")
        return False

    debug_state = r.json()
    print(f"   ✓ Breakpoint removed")
    print(f"   ✓ Total breakpoints: {len(debug_state['breakpoints'])}")

    # 13. Clear all debug
    print("\n13. Clearing all debug state...")
    r = requests.delete(f"{BASE_URL}/debug/executions/{exec_id}")
    if r.status_code != 204:
        print(f"   ERROR: Failed to clear debug: {r.status_code}")
        print(f"   Response: {r.text}")
        return False

    print(f"   ✓ Debug state cleared")

    # 14. Stop execution
    print("\n14. Stopping execution...")
    r = requests.post(f"{BASE_URL}/executions/{exec_id}/stop")
    if r.status_code != 200:
        print(f"   ERROR: Failed to stop execution: {r.status_code}")
        print(f"   Response: {r.text}")
        return False

    print(f"   ✓ Execution stopped")

    print("\n" + "=" * 60)
    print("✓ All Phase 3C debug endpoints working correctly!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_debug_endpoints()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
