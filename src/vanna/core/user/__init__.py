"""
User domain.

This module provides the core abstractions for user management in the Vanna Agents framework.
"""

from .base import UserService
from .models import User
from .resolver import UserResolver, CookieEmailUserResolver
from .request_context import RequestContext

__all__ = [
    "UserService",
    "User",
    "UserResolver",
    "CookieEmailUserResolver",
    "RequestContext",
]
