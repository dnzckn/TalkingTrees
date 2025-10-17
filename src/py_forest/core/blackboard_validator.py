"""Runtime validation for typed blackboard variables."""

from typing import Any, Dict, List, Optional

from py_forest.models.tree import BlackboardVariableSchema


class ValidationError(Exception):
    """Raised when blackboard validation fails."""

    pass


class BlackboardValidator:
    """Validates blackboard values against schema at runtime."""

    def __init__(self, schema: Dict[str, BlackboardVariableSchema]):
        """Initialize validator with schema.

        Args:
            schema: Blackboard variable schemas
        """
        self.schema = schema

    def validate(self, key: str, value: Any, strict: bool = True) -> None:
        """Validate a blackboard value against schema.

        Args:
            key: Blackboard key
            value: Value to validate
            strict: If True, raise error on validation failure

        Raises:
            ValidationError: If validation fails and strict=True
        """
        # Remove leading slash if present (py_trees adds it)
        clean_key = key.lstrip("/")

        if clean_key not in self.schema:
            if strict:
                raise ValidationError(
                    f"Key '{clean_key}' not in blackboard schema. "
                    f"Available keys: {list(self.schema.keys())}"
                )
            return

        var_schema = self.schema[clean_key]

        # Validate type
        self._validate_type(clean_key, value, var_schema, strict)

        # Validate constraints
        if var_schema.type in ["int", "float"]:
            self._validate_numeric_constraints(clean_key, value, var_schema, strict)

        elif var_schema.type == "array":
            self._validate_array(clean_key, value, var_schema, strict)

    def _validate_type(
        self,
        key: str,
        value: Any,
        schema: BlackboardVariableSchema,
        strict: bool,
    ) -> None:
        """Validate value type matches schema."""
        expected_type = schema.type
        actual_type = type(value).__name__

        # Type mapping
        type_map = {
            "int": (int,),
            "float": (float, int),  # Allow int for float
            "string": (str,),
            "bool": (bool,),
            "array": (list,),
            "object": (dict,),
        }

        if expected_type not in type_map:
            if strict:
                raise ValidationError(
                    f"Unknown type '{expected_type}' for key '{key}'"
                )
            return

        allowed_types = type_map[expected_type]

        if not isinstance(value, allowed_types):
            if strict:
                raise ValidationError(
                    f"Type mismatch for '{key}': expected {expected_type}, "
                    f"got {actual_type} (value: {value})"
                )

    def _validate_numeric_constraints(
        self,
        key: str,
        value: Any,
        schema: BlackboardVariableSchema,
        strict: bool,
    ) -> None:
        """Validate numeric min/max constraints."""
        if schema.min is not None:
            if value < schema.min:
                if strict:
                    raise ValidationError(
                        f"Value {value} for '{key}' is below minimum {schema.min}"
                    )

        if schema.max is not None:
            if value > schema.max:
                if strict:
                    raise ValidationError(
                        f"Value {value} for '{key}' exceeds maximum {schema.max}"
                    )

    def _validate_array(
        self,
        key: str,
        value: Any,
        schema: BlackboardVariableSchema,
        strict: bool,
    ) -> None:
        """Validate array items match schema."""
        if not isinstance(value, list):
            if strict:
                raise ValidationError(
                    f"Expected array for '{key}', got {type(value).__name__}"
                )
            return

        # Validate item types if specified
        if schema.items and "type" in schema.items:
            item_type = schema.items["type"]
            type_map = {
                "int": int,
                "float": (float, int),
                "string": str,
                "bool": bool,
            }

            if item_type in type_map:
                expected = type_map[item_type]

                for idx, item in enumerate(value):
                    if not isinstance(item, expected):
                        if strict:
                            raise ValidationError(
                                f"Array item at index {idx} for '{key}' has wrong type: "
                                f"expected {item_type}, got {type(item).__name__}"
                            )

    def validate_all(
        self,
        blackboard_dict: Dict[str, Any],
        strict: bool = True,
    ) -> List[str]:
        """Validate all blackboard values.

        Args:
            blackboard_dict: Dictionary of blackboard values
            strict: If True, raise on first error

        Returns:
            List of validation error messages (empty if all valid)

        Raises:
            ValidationError: If strict=True and validation fails
        """
        errors = []

        for key, value in blackboard_dict.items():
            try:
                self.validate(key, value, strict=True)
            except ValidationError as e:
                if strict:
                    raise
                errors.append(str(e))

        return errors

    def get_default_values(self) -> Dict[str, Any]:
        """Get default values from schema.

        Returns:
            Dictionary of key -> default value
        """
        defaults = {}

        for key, var_schema in self.schema.items():
            if var_schema.default is not None:
                defaults[key] = var_schema.default

        return defaults

    def has_key(self, key: str) -> bool:
        """Check if key exists in schema.

        Args:
            key: Blackboard key (with or without leading slash)

        Returns:
            True if key in schema
        """
        clean_key = key.lstrip("/")
        return clean_key in self.schema

    def get_type(self, key: str) -> Optional[str]:
        """Get expected type for a key.

        Args:
            key: Blackboard key

        Returns:
            Type string or None if key not in schema
        """
        clean_key = key.lstrip("/")

        if clean_key in self.schema:
            return self.schema[clean_key].type

        return None

    def get_constraints(self, key: str) -> Optional[Dict[str, Any]]:
        """Get constraints for a key.

        Args:
            key: Blackboard key

        Returns:
            Dict with min/max/etc or None if key not in schema
        """
        clean_key = key.lstrip("/")

        if clean_key not in self.schema:
            return None

        var_schema = self.schema[clean_key]

        constraints = {}

        if var_schema.min is not None:
            constraints["min"] = var_schema.min

        if var_schema.max is not None:
            constraints["max"] = var_schema.max

        if var_schema.items is not None:
            constraints["items"] = var_schema.items

        return constraints if constraints else None


def create_validator(tree_def) -> BlackboardValidator:
    """Create validator from tree definition.

    Args:
        tree_def: TreeDefinition with blackboard_schema

    Returns:
        BlackboardValidator instance
    """
    return BlackboardValidator(tree_def.blackboard_schema)
