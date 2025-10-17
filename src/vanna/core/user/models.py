"""
User domain models.

This module contains data models for user management.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    """User model for authentication and scoping."""

    id: str = Field(description="Unique user identifier")
    username: Optional[str] = Field(default=None, description="Username")
    email: Optional[str] = Field(default=None, description="User email")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional user metadata"
    )
    group_memberships: List[str] = Field(
        default_factory=list, description="Groups the user belongs to"
    )

    model_config = ConfigDict(extra="allow")
