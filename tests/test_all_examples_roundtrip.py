#!/usr/bin/env python
"""
Test All Example Trees for Round-Trip Conversion
=================================================

This script tests all example tree files in examples/trees/ directory
for round-trip conversion integrity.

For each .json file, it:
1. Loads the JSON tree definition
2. Deserializes to py_trees (counts nodes)
3. Serializes back to TalkingTrees format (counts nodes)
4. Compares node counts and validates structure
5. Reports results with detailed error information

This ensures that:
- All example trees can be loaded successfully
- Round-trip conversion preserves tree structure
- No nodes are lost or duplicated during conversion
- All node types in examples are supported
"""

import json
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from talking_trees.adapters import compare_py_trees, from_py_trees, to_py_trees
from talking_trees.core.serializer import TreeSerializer
from talking_trees.models.tree import TreeDefinition, TreeNodeDefinition
from talking_trees.sdk import TalkingTrees


@dataclass
class TestResult:
    """Result of testing a single tree file."""

    filename: str
    success: bool
    original_nodes: int
    roundtrip_nodes: int
    error_message: str | None = None
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

    @property
    def status(self) -> str:
        """Get status emoji."""
        return "✅ PASS" if self.success else "❌ FAIL"

    @property
    def node_match(self) -> bool:
        """Check if node counts match."""
        return self.original_nodes == self.roundtrip_nodes


def count_nodes(node: TreeNodeDefinition) -> int:
    """Recursively count all nodes in a tree."""
    count = 1  # Count this node
    for child in node.children:
        count += count_nodes(child)
    return count


def test_tree_roundtrip(filepath: Path) -> TestResult:
    """Test round-trip conversion for a single tree file.

    Args:
        filepath: Path to JSON tree file

    Returns:
        TestResult with detailed information
    """
    filename = filepath.name
    warnings = []

    try:
        # Step 1: Load JSON tree definition
        with open(filepath) as f:
            tree_data = json.load(f)

        tree_def = TreeDefinition.model_validate(tree_data)
        original_nodes = count_nodes(tree_def.root)

        # Step 2: Deserialize to py_trees
        serializer = TreeSerializer()
        py_tree = serializer.deserialize(tree_def)

        # Step 3: Serialize back to TalkingTrees format (round-trip)
        # Convert py_trees back to TalkingTrees TreeDefinition
        roundtrip_tree, context = from_py_trees(
            py_tree.root,
            name=tree_def.metadata.name,
            version=tree_def.metadata.version,
            description=tree_def.metadata.description or "",
        )

        # Collect conversion warnings
        if context.has_warnings():
            warnings.extend(context.warnings)

        roundtrip_nodes = count_nodes(roundtrip_tree.root)

        # Step 4: Validate with py_trees comparison
        # Convert both to py_trees and compare
        original_py_tree = serializer.deserialize(tree_def)
        roundtrip_py_tree = serializer.deserialize(roundtrip_tree)

        trees_equivalent = compare_py_trees(
            original_py_tree.root, roundtrip_py_tree.root, verbose=False
        )

        # Determine success
        # Success if node counts match AND trees are structurally equivalent
        success = (original_nodes == roundtrip_nodes) and trees_equivalent

        error_message = None
        if not success:
            if original_nodes != roundtrip_nodes:
                error_message = f"Node count mismatch: {original_nodes} → {roundtrip_nodes}"
            elif not trees_equivalent:
                error_message = "Tree structures are not equivalent"

        return TestResult(
            filename=filename,
            success=success,
            original_nodes=original_nodes,
            roundtrip_nodes=roundtrip_nodes,
            error_message=error_message,
            warnings=warnings,
        )

    except Exception as e:
        # Capture full error details
        error_details = f"{type(e).__name__}: {str(e)}"
        traceback_str = traceback.format_exc()

        return TestResult(
            filename=filename,
            success=False,
            original_nodes=0,
            roundtrip_nodes=0,
            error_message=error_details,
            warnings=[f"Full traceback:\n{traceback_str}"],
        )


def generate_report(results: list[TestResult]) -> str:
    """Generate a comprehensive test report.

    Args:
        results: List of test results

    Returns:
        Formatted report string
    """
    lines = []

    # Header
    lines.append("=" * 80)
    lines.append("Round-Trip Conversion Test Report")
    lines.append("=" * 80)
    lines.append("")

    # Summary statistics
    total = len(results)
    passed = sum(1 for r in results if r.success)
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0

    lines.append("SUMMARY")
    lines.append("-" * 80)
    lines.append(f"Total Files:  {total}")
    lines.append(f"Passed:       {passed} ({pass_rate:.1f}%)")
    lines.append(f"Failed:       {failed}")
    lines.append("")

    # Detailed results table
    lines.append("DETAILED RESULTS")
    lines.append("-" * 80)

    # Table header
    lines.append(
        f"{'Status':<12} {'File':<35} {'Original':<10} {'RoundTrip':<10} {'Match':<8}"
    )
    lines.append("-" * 80)

    # Table rows
    for result in results:
        match_symbol = "✓" if result.node_match else "✗"
        lines.append(
            f"{result.status:<12} {result.filename:<35} "
            f"{result.original_nodes:<10} {result.roundtrip_nodes:<10} {match_symbol:<8}"
        )

    lines.append("")

    # Errors and warnings
    has_errors_or_warnings = any(
        r.error_message or r.warnings for r in results if not r.success
    )

    if has_errors_or_warnings:
        lines.append("ERRORS AND WARNINGS")
        lines.append("-" * 80)

        for result in results:
            if not result.success:
                lines.append(f"\n{result.filename}:")

                if result.error_message:
                    lines.append(f"  ERROR: {result.error_message}")

                if result.warnings:
                    for warning in result.warnings[:1]:  # Show first warning with full detail
                        lines.append(f"  {warning}")
                    if len(result.warnings) > 1:
                        lines.append(f"  ... and {len(result.warnings) - 1} more warnings")

    # Conversion warnings for successful tests
    has_warnings = any(r.warnings for r in results if r.success)
    if has_warnings:
        lines.append("")
        lines.append("CONVERSION WARNINGS (Passed tests)")
        lines.append("-" * 80)

        for result in results:
            if result.success and result.warnings:
                lines.append(f"\n{result.filename}:")
                for warning in result.warnings:
                    lines.append(f"  {warning}")

    lines.append("")
    lines.append("=" * 80)

    # Final verdict
    if failed == 0:
        lines.append("✅ ALL TESTS PASSED!")
    else:
        lines.append(f"⚠️  {failed} TEST(S) FAILED")

    lines.append("=" * 80)
    lines.append("")

    return "\n".join(lines)


def main():
    """Main test runner."""
    print("\n🧪 Testing All Example Trees for Round-Trip Conversion\n")

    # Find all JSON files in examples/trees/
    examples_dir = Path(__file__).parent.parent / "examples" / "trees"

    if not examples_dir.exists():
        print(f"❌ ERROR: Examples directory not found: {examples_dir}")
        sys.exit(1)

    json_files = sorted(examples_dir.glob("*.json"))

    if not json_files:
        print(f"❌ ERROR: No .json files found in {examples_dir}")
        sys.exit(1)

    print(f"Found {len(json_files)} example tree files in {examples_dir}\n")

    # Run tests
    results = []
    for i, filepath in enumerate(json_files, 1):
        print(f"[{i}/{len(json_files)}] Testing {filepath.name}...", end=" ")

        result = test_tree_roundtrip(filepath)
        results.append(result)

        # Print immediate status
        if result.success:
            print(f"✅ PASS ({result.original_nodes} nodes)")
        else:
            print(f"❌ FAIL - {result.error_message}")

    print("\n")

    # Generate and print report
    report = generate_report(results)
    print(report)

    # Save report to file
    report_path = Path(__file__).parent / "roundtrip_test_report.txt"
    with open(report_path, "w") as f:
        f.write(report)

    print(f"📄 Detailed report saved to: {report_path}\n")

    # Exit with appropriate code
    failed_count = sum(1 for r in results if not r.success)
    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()
