"""Security configuration models."""

from pydantic import BaseModel, Field

from talking_trees.security.roles import Role


class SecurityConfig(BaseModel):
    """Configuration for API security."""

    enabled: bool = Field(default=False, description="Enable API authentication")
    api_keys: dict[str, Role] = Field(
        default_factory=dict,
        description="API key to role mapping {key: role}",
    )
    jwt_secret: str | None = Field(default=None, description="JWT signing secret")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    rate_limit_rpm: int | None = Field(
        default=None,
        description="Rate limit: requests per minute per key",
    )
