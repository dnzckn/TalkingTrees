"""FastAPI security middleware and dependencies."""

import logging
import time
from collections import defaultdict

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from talking_trees.security.config import SecurityConfig
from talking_trees.security.roles import Role

logger = logging.getLogger(__name__)

_config: SecurityConfig = SecurityConfig()
_rate_limit_tracker: dict[str, list[float]] = defaultdict(list)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def configure_security(config: SecurityConfig) -> None:
    """Set the global security configuration."""
    global _config
    _config = config


def get_current_role(
    api_key: str | None = Depends(api_key_header),
) -> Role | None:
    """Resolve current caller's role from API key."""
    if not _config.enabled:
        return None

    if api_key is None:
        raise HTTPException(status_code=401, detail="Missing API key")

    role = _config.api_keys.get(api_key)
    if role is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if _config.rate_limit_rpm:
        _check_rate_limit(api_key)

    return role


def require_role(minimum_role: Role):
    """FastAPI dependency that requires a minimum role level."""
    hierarchy = {Role.VIEWER: 0, Role.OPERATOR: 1, Role.ADMIN: 2}
    min_level = hierarchy[minimum_role]

    def check(role: Role | None = Depends(get_current_role)):
        if role is None:
            return
        if hierarchy.get(role, -1) < min_level:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {minimum_role.value}",
            )

    return check


def _check_rate_limit(api_key: str) -> None:
    now = time.monotonic()
    window = 60.0
    _rate_limit_tracker[api_key] = [
        t for t in _rate_limit_tracker[api_key] if now - t < window
    ]
    if len(_rate_limit_tracker[api_key]) >= _config.rate_limit_rpm:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    _rate_limit_tracker[api_key].append(now)
