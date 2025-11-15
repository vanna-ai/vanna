"""
User resolver interface for web request authentication.

This module provides the abstract base class for resolving web requests
to authenticated User objects.
"""

from abc import ABC, abstractmethod

from .models import User
from .request_context import RequestContext


class UserResolver(ABC):
    """Resolves web requests to authenticated users.

    Implementations of this interface handle the specifics of extracting
    user identity from request context (cookies, headers, tokens, etc.)
    and creating authenticated User objects.

    Example:
        class JwtUserResolver(UserResolver):
            async def resolve_user(self, request_context: RequestContext) -> User:
                token = request_context.get_header('Authorization')
                # ... validate JWT and extract user info
                return User(id=user_id, username=username, email=email)
    """

    @abstractmethod
    async def resolve_user(self, request_context: RequestContext) -> User:
        """Resolve user from request context.

        Args:
            request_context: Structured request context with cookies, headers, etc.

        Returns:
            Authenticated User object

        Raises:
            Can raise exceptions for authentication failures
        """
        pass
