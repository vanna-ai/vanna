"""
Cookie-based user resolver implementation.

This module provides a simple cookie-based user resolver that extracts
user email from a cookie.
"""

from typing import Optional
import hashlib

from .models import User
from .request_context import RequestContext
from .resolver import UserResolver


class CookieEmailUserResolver(UserResolver):
    """Resolves users from email cookies.

    This resolver extracts a user's email from a cookie and creates
    a User object. If no cookie is present, it creates an anonymous user.

    Example:
        resolver = CookieEmailUserResolver(cookie_name="vanna_email")
        context = RequestContext(cookies={"vanna_email": "alice@example.com"})
        user = await resolver.resolve_user(context)
        # user.email == "alice@example.com"
        # user.id == hash of email

        # Anonymous user when no cookie
        context = RequestContext(cookies={})
        user = await resolver.resolve_user(context)
        # user.email == None
        # user.username == "anonymous"
    """

    def __init__(self, cookie_name: str = "vanna_email"):
        """Initialize the cookie-based user resolver.

        Args:
            cookie_name: Name of the cookie containing the user's email.
                        Defaults to "vanna_email".
        """
        self.cookie_name = cookie_name

    async def resolve_user(self, request_context: RequestContext) -> User:
        """Resolve user from email cookie.

        Args:
            request_context: Request context containing cookies

        Returns:
            User object with email from cookie, or anonymous user if no cookie
        """
        email = request_context.get_cookie(self.cookie_name)

        if email:
            # Create authenticated user from email
            # Use hash of email as user ID for consistency
            user_id = hashlib.sha256(email.encode()).hexdigest()[:16]

            # Extract username from email (part before @)
            username = email.split('@')[0] if '@' in email else email

            return User(
                id=user_id,
                username=username,
                email=email,
                metadata={"auth_method": "cookie", "cookie_name": self.cookie_name}
            )
        else:
            # Create anonymous user
            # Use remote address if available for anonymous ID
            remote_addr = request_context.remote_addr or "unknown"
            anonymous_id = hashlib.sha256(f"anonymous-{remote_addr}".encode()).hexdigest()[:16]

            return User(
                id=anonymous_id,
                username="anonymous",
                email=None,
                metadata={"auth_method": "anonymous", "remote_addr": remote_addr}
            )
