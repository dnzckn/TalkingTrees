"""Tree and behavior validation."""

from uuid import UUID

from py_forest.core.registry import BehaviorRegistry
from py_forest.models.tree import TreeDefinition, TreeNodeDefinition
from py_forest.models.validation import (
    BehaviorValidationSchema,
    TreeValidationResult,
    ValidationIssue,
    ValidationLevel,
)


class TreeValidator:
    """Validates behavior tree definitions.

    Checks for:
    - Structural issues (circular refs, orphaned nodes)
    - Type validity (registered behaviors)
    - Configuration correctness
    - Subtree references
    """

    def __init__(self, registry: BehaviorRegistry):
        """Initialize validator.

        Args:
            registry: Behavior registry for type checking
        """
        self.registry = registry

    def validate(self, tree_def: TreeDefinition) -> TreeValidationResult:
        """Validate a complete tree definition.

        Args:
            tree_def: Tree definition to validate

        Returns:
            Validation result with issues
        """
        issues: list[ValidationIssue] = []

        # Collect all node IDs
        all_node_ids = self._collect_node_ids(tree_def.root)

        # Check for duplicate node IDs
        issues.extend(self._check_duplicate_ids(tree_def.root, all_node_ids))

        # Validate tree structure
        issues.extend(self._validate_node(tree_def.root, set(), "root"))

        # Validate subtrees
        for subtree_name, subtree_root in tree_def.subtrees.items():
            issues.extend(
                self._validate_node(subtree_root, set(), f"subtrees[{subtree_name}]")
            )

        # Check subtree references
        issues.extend(self._check_subtree_refs(tree_def))

        # Count issues by level
        error_count = sum(1 for i in issues if i.level == ValidationLevel.ERROR)
        warning_count = sum(1 for i in issues if i.level == ValidationLevel.WARNING)
        info_count = sum(1 for i in issues if i.level == ValidationLevel.INFO)

        return TreeValidationResult(
            is_valid=(error_count == 0),
            issues=issues,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
        )

    def _collect_node_ids(self, node: TreeNodeDefinition) -> list[UUID]:
        """Collect all node IDs in tree.

        Args:
            node: Root node

        Returns:
            List of all node IDs
        """
        ids = [node.node_id]
        for child in node.children:
            ids.extend(self._collect_node_ids(child))
        return ids

    def _check_duplicate_ids(
        self, node: TreeNodeDefinition, all_ids: list[UUID]
    ) -> list[ValidationIssue]:
        """Check for duplicate node IDs.

        Args:
            node: Root node
            all_ids: All node IDs in tree

        Returns:
            List of issues
        """
        issues = []
        seen = set()
        duplicates = set()

        for node_id in all_ids:
            if node_id in seen:
                duplicates.add(node_id)
            seen.add(node_id)

        for dup_id in duplicates:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    code="DUPLICATE_ID",
                    message=f"Duplicate node ID: {dup_id}",
                    node_id=dup_id,
                )
            )

        return issues

    def _validate_node(
        self, node: TreeNodeDefinition, visited: set[UUID], path: str
    ) -> list[ValidationIssue]:
        """Validate a single node recursively.

        Args:
            node: Node to validate
            visited: Set of visited node IDs (for cycle detection)
            path: Current path in tree

        Returns:
            List of validation issues
        """
        issues = []

        # Check for circular reference
        if node.node_id in visited:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    code="CIRCULAR_REFERENCE",
                    message="Circular reference detected",
                    node_id=node.node_id,
                    node_path=path,
                )
            )
            return issues  # Stop here to avoid infinite loop

        visited.add(node.node_id)

        # Check if behavior type is registered
        if not self.registry.is_registered(node.node_type):
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    code="UNKNOWN_BEHAVIOR",
                    message=f"Unknown behavior type: {node.node_type}",
                    node_id=node.node_id,
                    node_path=path,
                    context={"node_type": node.node_type},
                )
            )
        else:
            # Validate behavior configuration
            schema = self.registry.get_schema(node.node_type)
            issues.extend(self._validate_behavior_config(node, schema, path))

        # Validate children
        if node.children:
            # Check if behavior allows children
            if self.registry.is_registered(node.node_type):
                schema = self.registry.get_schema(node.node_type)
                category = schema.category.value if schema and schema.category else "behavior"

                if category not in ["composite", "decorator"]:
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.WARNING,
                            code="UNEXPECTED_CHILDREN",
                            message=f"Behavior type '{node.node_type}' typically does not have children",
                            node_id=node.node_id,
                            node_path=path,
                        )
                    )

            # Validate each child
            for i, child in enumerate(node.children):
                child_path = f"{path}.children[{i}]"
                issues.extend(self._validate_node(child, visited.copy(), child_path))
        else:
            # Check if composite/decorator without children
            if self.registry.is_registered(node.node_type):
                schema = self.registry.get_schema(node.node_type)
                category = schema.category.value if schema and schema.category else "behavior"

                if category in ["composite", "decorator"]:
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.ERROR,
                            code="MISSING_CHILDREN",
                            message=f"{category.capitalize()} '{node.node_type}' requires children",
                            node_id=node.node_id,
                            node_path=path,
                        )
                    )

        # Check subtree reference
        if node.ref:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.INFO,
                    code="SUBTREE_REFERENCE",
                    message=f"Node references subtree: {node.ref}",
                    node_id=node.node_id,
                    node_path=path,
                    context={"subtree_ref": node.ref},
                )
            )

        return issues

    def _validate_behavior_config(
        self, node: TreeNodeDefinition, schema, path: str
    ) -> list[ValidationIssue]:
        """Validate behavior configuration against schema.

        Args:
            node: Node to validate
            schema: Behavior schema (BehaviorSchema or None)
            path: Node path

        Returns:
            List of validation issues
        """
        issues = []

        # Get expected parameters from schema
        if schema is None:
            return issues

        params_schema = schema.config_schema if hasattr(schema, 'config_schema') else {}

        # Check for unknown parameters
        for param_name in node.config.keys():
            if param_name not in params_schema:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        code="UNKNOWN_PARAMETER",
                        message=f"Unknown parameter: {param_name}",
                        node_id=node.node_id,
                        node_path=path,
                        field=param_name,
                    )
                )

        # Validate parameter types
        for param_name, value in node.config.items():
            if param_name in params_schema:
                param_schema = params_schema[param_name]
                expected_type = param_schema.type if hasattr(param_schema, 'type') else None

                # Basic type validation
                if expected_type:
                    type_valid = self._check_param_type(value, expected_type)
                    if not type_valid:
                        issues.append(
                            ValidationIssue(
                                level=ValidationLevel.ERROR,
                                code="INVALID_PARAMETER_TYPE",
                                message=f"Parameter '{param_name}' has invalid type. Expected: {expected_type}",
                                node_id=node.node_id,
                                node_path=path,
                                field=param_name,
                                context={
                                    "expected_type": expected_type,
                                    "value": str(value),
                                },
                            )
                        )

        return issues

    def _check_param_type(self, value: any, expected_type: str) -> bool:
        """Check if parameter value matches expected type.

        Args:
            value: Parameter value
            expected_type: Expected type string

        Returns:
            True if type is valid
        """
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "int":
            return isinstance(value, int) and not isinstance(value, bool)
        elif expected_type == "float":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected_type == "bool":
            return isinstance(value, bool)
        elif expected_type == "object":
            return isinstance(value, dict)
        elif expected_type == "array":
            return isinstance(value, list)
        else:
            # Unknown type, assume valid
            return True

    def _check_subtree_refs(self, tree_def: TreeDefinition) -> list[ValidationIssue]:
        """Check that all subtree references are valid.

        Args:
            tree_def: Tree definition

        Returns:
            List of validation issues
        """
        issues = []

        # Collect all subtree refs
        refs = self._collect_subtree_refs(tree_def.root)

        # Check each ref
        for node_id, ref in refs:
            if ref not in tree_def.subtrees:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        code="INVALID_SUBTREE_REF",
                        message=f"Subtree reference '{ref}' not found in tree definition",
                        node_id=node_id,
                        context={"subtree_ref": ref},
                    )
                )

        return issues

    def _collect_subtree_refs(self, node: TreeNodeDefinition) -> list[tuple[UUID, str]]:
        """Collect all subtree references in tree.

        Args:
            node: Root node

        Returns:
            List of (node_id, ref) tuples
        """
        refs = []

        if node.ref:
            refs.append((node.node_id, node.ref))

        for child in node.children:
            refs.extend(self._collect_subtree_refs(child))

        return refs


class BehaviorValidator:
    """Validates individual behavior configurations."""

    def validate_behavior(
        self,
        behavior_type: str,
        config: dict,
        schema: BehaviorValidationSchema,
    ) -> TreeValidationResult:
        """Validate a behavior configuration.

        Args:
            behavior_type: Behavior type
            config: Configuration dictionary
            schema: Validation schema

        Returns:
            Validation result
        """
        issues = []

        # Check for unknown parameters
        schema_param_names = {p.name for p in schema.parameters}
        for param_name in config.keys():
            if param_name not in schema_param_names:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        code="UNKNOWN_PARAMETER",
                        message=f"Unknown parameter: {param_name}",
                        field=param_name,
                    )
                )

        # Check required parameters and types
        for param in schema.parameters:
            if param.required and param.name not in config:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        code="MISSING_REQUIRED_PARAMETER",
                        message=f"Missing required parameter: {param.name}",
                        field=param.name,
                    )
                )
            elif param.name in config:
                value = config[param.name]

                # Type validation
                if not self._check_type(value, param.type):
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.ERROR,
                            code="INVALID_TYPE",
                            message=f"Parameter '{param.name}' has invalid type. Expected: {param.type}",
                            field=param.name,
                            context={"expected_type": param.type, "value": str(value)},
                        )
                    )

                # Range validation for numeric types
                if param.type in ["int", "float"]:
                    if param.min_value is not None and value < param.min_value:
                        issues.append(
                            ValidationIssue(
                                level=ValidationLevel.ERROR,
                                code="VALUE_TOO_SMALL",
                                message=f"Parameter '{param.name}' is below minimum value {param.min_value}",
                                field=param.name,
                            )
                        )
                    if param.max_value is not None and value > param.max_value:
                        issues.append(
                            ValidationIssue(
                                level=ValidationLevel.ERROR,
                                code="VALUE_TOO_LARGE",
                                message=f"Parameter '{param.name}' exceeds maximum value {param.max_value}",
                                field=param.name,
                            )
                        )

                # Enum validation
                if param.allowed_values and value not in param.allowed_values:
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.ERROR,
                            code="INVALID_VALUE",
                            message=f"Parameter '{param.name}' must be one of: {param.allowed_values}",
                            field=param.name,
                        )
                    )

        # Count issues
        error_count = sum(1 for i in issues if i.level == ValidationLevel.ERROR)
        warning_count = sum(1 for i in issues if i.level == ValidationLevel.WARNING)
        info_count = sum(1 for i in issues if i.level == ValidationLevel.INFO)

        return TreeValidationResult(
            is_valid=(error_count == 0),
            issues=issues,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
        )

    def _check_type(self, value: any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "int":
            return isinstance(value, int) and not isinstance(value, bool)
        elif expected_type == "float":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected_type == "bool":
            return isinstance(value, bool)
        elif expected_type == "object":
            return isinstance(value, dict)
        elif expected_type == "array":
            return isinstance(value, list)
        else:
            return True
