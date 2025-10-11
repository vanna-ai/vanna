"""
User domain interface.

This module contains the abstract base class for user services.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .models import User


class UserService(ABC):
    """Service for user management and authentication."""

    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        pass

    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[User]:
        """Authenticate user and return User object if successful."""
        pass

    @abstractmethod
    async def has_permission(self, user: User, permission: str) -> bool:
        """Check if user has specific permission."""
        pass
