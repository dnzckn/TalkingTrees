"""Tree template system for generating trees from patterns."""

import copy
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from py_forest.models.tree import TreeDefinition, TreeMetadata
from py_forest.models.validation import (
    TemplateInstantiationRequest,
    TreeTemplate,
)


class TemplateEngine:
    """Engine for instantiating trees from templates.

    Supports parameter substitution using {{param_name}} syntax.
    """

    def __init__(self):
        """Initialize template engine."""
        self.param_pattern = re.compile(r"\{\{(\w+)\}\}")

    def instantiate(
        self,
        template: TreeTemplate,
        params: dict[str, Any],
        tree_name: str | None = None,
        tree_version: str = "1.0.0",
    ) -> TreeDefinition:
        """Instantiate a tree from a template.

        Args:
            template: Tree template
            params: Parameter values
            tree_name: Name for generated tree (defaults to template name)
            tree_version: Version for generated tree

        Returns:
            Generated tree definition

        Raises:
            ValueError: If required parameters missing or invalid
        """
        # Validate parameters
        self._validate_params(template, params)

        # Apply defaults for missing optional parameters
        full_params = self._apply_defaults(template, params)

        # Clone tree structure
        tree_structure = copy.deepcopy(template.tree_structure)

        # Substitute parameters
        tree_structure = self._substitute_params(tree_structure, full_params)

        # Build tree definition
        tree_def = TreeDefinition(
            tree_id=uuid4(),
            metadata=TreeMetadata(
                name=tree_name or f"{template.name} Instance",
                version=tree_version,
                description=f"Generated from template: {template.name}",
                tags=template.tags + ["template-generated"],
                created_at=datetime.utcnow(),
                modified_at=datetime.utcnow(),
            ),
            root=tree_structure["root"],
            subtrees=tree_structure.get("subtrees", {}),
        )

        return tree_def

    def _validate_params(self, template: TreeTemplate, params: dict[str, Any]) -> None:
        """Validate template parameters.

        Args:
            template: Tree template
            params: Parameter values

        Raises:
            ValueError: If parameters invalid
        """
        # Check for required parameters
        for param_def in template.parameters:
            if param_def.required and param_def.name not in params:
                raise ValueError(f"Missing required parameter: {param_def.name}")

        # Check for unknown parameters
        known_params = {p.name for p in template.parameters}
        for param_name in params.keys():
            if param_name not in known_params:
                raise ValueError(f"Unknown parameter: {param_name}")

        # Type validation
        for param_def in template.parameters:
            if param_def.name in params:
                value = params[param_def.name]
                if not self._check_param_type(value, param_def.type):
                    raise ValueError(
                        f"Parameter '{param_def.name}' has invalid type. "
                        f"Expected: {param_def.type}, got: {type(value).__name__}"
                    )

    def _check_param_type(self, value: Any, expected_type: str) -> bool:
        """Check if parameter value matches expected type."""
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

    def _apply_defaults(
        self, template: TreeTemplate, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply default values for missing optional parameters.

        Args:
            template: Tree template
            params: Parameter values

        Returns:
            Parameters with defaults applied
        """
        full_params = params.copy()

        for param_def in template.parameters:
            if param_def.name not in full_params and param_def.default is not None:
                full_params[param_def.name] = param_def.default

        return full_params

    def _substitute_params(self, structure: Any, params: dict[str, Any]) -> Any:
        """Recursively substitute parameters in structure.

        Args:
            structure: Tree structure (dict, list, or value)
            params: Parameter values

        Returns:
            Structure with parameters substituted
        """
        if isinstance(structure, dict):
            return {k: self._substitute_params(v, params) for k, v in structure.items()}
        elif isinstance(structure, list):
            return [self._substitute_params(item, params) for item in structure]
        elif isinstance(structure, str):
            # Substitute {{param}} patterns
            return self._substitute_string(structure, params)
        else:
            return structure

    def _substitute_string(self, text: str, params: dict[str, Any]) -> Any:
        """Substitute parameters in string.

        Args:
            text: String with {{param}} patterns
            params: Parameter values

        Returns:
            Substituted value (may not be string if entire text is a param ref)
        """
        # Check if entire string is a parameter reference
        match = self.param_pattern.fullmatch(text)
        if match:
            param_name = match.group(1)
            if param_name in params:
                return params[param_name]
            else:
                raise ValueError(f"Parameter not found: {param_name}")

        # Partial substitution
        def replace_func(match):
            param_name = match.group(1)
            if param_name in params:
                return str(params[param_name])
            else:
                raise ValueError(f"Parameter not found: {param_name}")

        return self.param_pattern.sub(replace_func, text)


class TemplateLibrary:
    """Library for managing tree templates."""

    def __init__(self, templates_dir: Path):
        """Initialize template library.

        Args:
            templates_dir: Directory containing template files
        """
        self.templates_dir = templates_dir
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.engine = TemplateEngine()

    def list_templates(self) -> list[TreeTemplate]:
        """List all available templates.

        Returns:
            List of templates
        """
        templates = []

        for template_file in self.templates_dir.glob("*.json"):
            try:
                template = self.load_template(template_file.stem)
                templates.append(template)
            except Exception as e:
                print(f"Warning: Failed to load template {template_file}: {e}")

        return templates

    def load_template(self, template_id: str) -> TreeTemplate:
        """Load a template by ID.

        Args:
            template_id: Template identifier

        Returns:
            Tree template

        Raises:
            ValueError: If template not found
        """
        template_file = self.templates_dir / f"{template_id}.json"

        if not template_file.exists():
            raise ValueError(f"Template not found: {template_id}")

        with open(template_file) as f:
            data = json.load(f)

        return TreeTemplate(**data)

    def save_template(self, template: TreeTemplate) -> None:
        """Save a template.

        Args:
            template: Template to save
        """
        template_file = self.templates_dir / f"{template.template_id}.json"

        with open(template_file, "w") as f:
            json.dump(template.model_dump(), f, indent=2, default=str)

    def delete_template(self, template_id: str) -> bool:
        """Delete a template.

        Args:
            template_id: Template identifier

        Returns:
            True if deleted, False if not found
        """
        template_file = self.templates_dir / f"{template_id}.json"

        if template_file.exists():
            template_file.unlink()
            return True

        return False

    def instantiate(self, request: TemplateInstantiationRequest) -> TreeDefinition:
        """Instantiate a template.

        Args:
            request: Instantiation request

        Returns:
            Generated tree definition

        Raises:
            ValueError: If template not found or parameters invalid
        """
        template = self.load_template(request.template_id)

        return self.engine.instantiate(
            template,
            request.parameters,
            request.tree_name,
            request.tree_version,
        )

    def get_template_info(self, template_id: str) -> dict[str, Any]:
        """Get template information including parameters.

        Args:
            template_id: Template identifier

        Returns:
            Template info dictionary

        Raises:
            ValueError: If template not found
        """
        template = self.load_template(template_id)

        return {
            "template_id": template.template_id,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "tags": template.tags,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default,
                }
                for p in template.parameters
            ],
            "example_params": template.example_params,
        }
