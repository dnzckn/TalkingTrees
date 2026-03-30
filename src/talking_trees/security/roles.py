"""Role-based access control definitions."""

from enum import Enum


class Role(str, Enum):
    """API access roles."""

    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"
