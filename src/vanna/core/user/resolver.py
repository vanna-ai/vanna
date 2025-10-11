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


class CookieEmailUserResolver(UserResolver):
    """Resolves users from email stored in vanna_email cookie.

    This is a simple demo resolver that creates users based on
    the email address stored in a cookie. For production use,
    you would want to:
    - Validate the email format
    - Look up the user in a database
    - Verify the cookie is signed/encrypted
    - Implement proper session management

    Example:
        resolver = CookieEmailUserResolver()
        context = RequestContext(cookies={'vanna_email': 'alice@example.com'})
        user = await resolver.resolve_user(context)
    """

    def __init__(self, cookie_name: str = 'vanna_email'):
        """Initialize resolver.

        Args:
            cookie_name: Name of cookie containing user email
        """
        self.cookie_name = cookie_name

    async def resolve_user(self, request_context: RequestContext) -> User:
        """Resolve user from email cookie.

        Args:
            request_context: Request context with cookies

        Returns:
            User object (authenticated if email found, anonymous otherwise)
        """
        email = request_context.get_cookie(self.cookie_name)

        if email and '@' in email:
            # Extract username from email
            username = email.split('@')[0]

            return User(
                id=email,
                username=username,
                email=email,
                permissions=['basic_user'],
                metadata={'auth_method': 'cookie'}
            )

        # Return anonymous user if no email found
        return User(
            id="anonymous",
            username="guest",
            email=None,
            permissions=[],
            metadata={'auth_method': 'none'}
        )
