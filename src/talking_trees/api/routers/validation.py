"""Validation and template endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from talking_trees.api.dependencies import (
    behavior_registry_dependency,
    template_library_dependency,
    tree_library_dependency,
)
from talking_trees.core.registry import BehaviorRegistry
from talking_trees.core.templates import TemplateLibrary
from talking_trees.core.validation import BehaviorValidator, TreeValidator
from talking_trees.models.tree import TreeDefinition
from talking_trees.models.validation import (
    BehaviorValidationSchema,
    TemplateInstantiationRequest,
    TreeTemplate,
    TreeValidationResult,
)
from talking_trees.storage.base import TreeLibrary

router = APIRouter(prefix="/validation", tags=["validation"])


@router.post("/trees", response_model=TreeValidationResult)
def validate_tree(
    tree_def: TreeDefinition,
    registry: BehaviorRegistry = Depends(behavior_registry_dependency),
) -> TreeValidationResult:
    """Validate a tree definition.

    Checks for:
    - Structural issues (circular refs, duplicate IDs)
    - Unknown behavior types
    - Missing required parameters
    - Invalid configurations
    - Subtree references

    Args:
        tree_def: Tree definition to validate
        registry: Behavior registry

    Returns:
        Validation result with issues
    """
    validator = TreeValidator(registry)
    return validator.validate(tree_def)


@router.post("/trees/{tree_id}", response_model=TreeValidationResult)
def validate_tree_by_id(
    tree_id: UUID,
    version: str | None = None,
    library: TreeLibrary = Depends(tree_library_dependency),
    registry: BehaviorRegistry = Depends(behavior_registry_dependency),
) -> TreeValidationResult:
    """Validate a tree from the library.

    Args:
        tree_id: Tree identifier
        version: Optional version (defaults to latest)
        library: Tree library
        registry: Behavior registry

    Returns:
        Validation result

    Raises:
        HTTPException: If tree not found
    """
    try:
        tree_def = library.get_tree(tree_id, version)
        validator = TreeValidator(registry)
        return validator.validate(tree_def)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/behaviors", response_model=TreeValidationResult)
def validate_behavior(
    behavior_type: str,
    config: dict[str, Any],
    registry: BehaviorRegistry = Depends(behavior_registry_dependency),
) -> TreeValidationResult:
    """Validate a behavior configuration.

    Args:
        behavior_type: Behavior type identifier
        config: Configuration dictionary
        registry: Behavior registry

    Returns:
        Validation result

    Raises:
        HTTPException: If behavior type not found
    """
    if not registry.is_registered(behavior_type):
        raise HTTPException(
            status_code=404,
            detail=f"Behavior type not registered: {behavior_type}",
        )

    # Get behavior schema
    behavior_schema = registry.get_schema(behavior_type)

    if not behavior_schema:
        raise HTTPException(
            status_code=404,
            detail=f"Schema not found for behavior type: {behavior_type}",
        )

    # Convert to BehaviorValidationSchema
    from talking_trees.models.validation import BehaviorParameter

    parameters = []
    for param_name, param_schema in behavior_schema.config_schema.items():
        parameters.append(
            BehaviorParameter(
                name=param_name,
                type=param_schema.type,
                required=False,  # ConfigPropertySchema doesn't have required field
                default=param_schema.default,
                description=param_schema.description,
                min_value=param_schema.minimum,  # Map minimum → min_value
                max_value=param_schema.maximum,  # Map maximum → max_value
                allowed_values=param_schema.enum,  # Map enum → allowed_values
            )
        )

    schema = BehaviorValidationSchema(
        behavior_type=behavior_type,
        display_name=behavior_schema.display_name,
        category=behavior_schema.category.value,
        description=behavior_schema.description,
        parameters=parameters,
    )

    # Validate
    validator = BehaviorValidator()
    return validator.validate_behavior(behavior_type, config, schema)


# Template endpoints


@router.get("/templates", response_model=list[TreeTemplate])
def list_templates(
    library: TemplateLibrary = Depends(template_library_dependency),
) -> list[TreeTemplate]:
    """List all available templates.

    Returns:
        List of templates
    """
    return library.list_templates()


@router.get("/templates/{template_id}", response_model=TreeTemplate)
def get_template(
    template_id: str,
    library: TemplateLibrary = Depends(template_library_dependency),
) -> TreeTemplate:
    """Get a specific template.

    Args:
        template_id: Template identifier
        library: Template library

    Returns:
        Tree template

    Raises:
        HTTPException: If template not found
    """
    try:
        return library.load_template(template_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/templates/{template_id}/info")
def get_template_info(
    template_id: str,
    library: TemplateLibrary = Depends(template_library_dependency),
) -> dict[str, Any]:
    """Get template information.

    Args:
        template_id: Template identifier
        library: Template library

    Returns:
        Template info

    Raises:
        HTTPException: If template not found
    """
    try:
        return library.get_template_info(template_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/templates", response_model=TreeTemplate, status_code=201)
def create_template(
    template: TreeTemplate,
    library: TemplateLibrary = Depends(template_library_dependency),
) -> TreeTemplate:
    """Create a new template.

    Args:
        template: Template to create
        library: Template library

    Returns:
        Created template
    """
    library.save_template(template)
    return template


@router.post("/templates/{template_id}/instantiate", response_model=TreeDefinition)
def instantiate_template(
    template_id: str,
    request: TemplateInstantiationRequest,
    template_lib: TemplateLibrary = Depends(template_library_dependency),
    tree_lib: TreeLibrary = Depends(tree_library_dependency),
) -> TreeDefinition:
    """Instantiate a template to create a tree.

    Args:
        template_id: Template identifier
        request: Instantiation request with parameters
        template_lib: Template library
        tree_lib: Tree library

    Returns:
        Generated tree definition

    Raises:
        HTTPException: If template not found or parameters invalid
    """
    try:
        # Override template_id from path
        request.template_id = template_id

        # Instantiate template
        tree_def = template_lib.instantiate(request)

        # Optionally save to library
        # tree_lib.save_tree(tree_def)

        return tree_def

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/templates/{template_id}", status_code=204)
def delete_template(
    template_id: str,
    library: TemplateLibrary = Depends(template_library_dependency),
) -> None:
    """Delete a template.

    Args:
        template_id: Template identifier
        library: Template library

    Raises:
        HTTPException: If template not found
    """
    success = library.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
