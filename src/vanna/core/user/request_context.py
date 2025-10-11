"""
Request context for user resolution.

This module provides the RequestContext model for passing web request
information to UserResolver implementations.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class RequestContext(BaseModel):
    """Context from a web request for user resolution.

    This structured object replaces raw dictionaries for passing request
    data to UserResolver implementations, making it easier to access
    cookies, headers, and other request metadata.

    Example:
        context = RequestContext(
            cookies={'vanna_email': 'alice@example.com'},
            headers={'Authorization': 'Bearer token'},
            remote_addr='127.0.0.1'
        )
        user = await resolver.resolve_user(context)
    """

    cookies: Dict[str, str] = Field(
        default_factory=dict,
        description="Request cookies"
    )

    headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Request headers"
    )

    remote_addr: Optional[str] = Field(
        default=None,
        description="Remote IP address"
    )

    query_params: Dict[str, str] = Field(
        default_factory=dict,
        description="Query parameters"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional framework-specific metadata"
    )

    def get_cookie(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get cookie value by name.

        Args:
            name: Cookie name
            default: Default value if cookie not found

        Returns:
            Cookie value or default
        """
        return self.cookies.get(name, default)

    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get header value by name (case-insensitive).

        Args:
            name: Header name
            default: Default value if header not found

        Returns:
            Header value or default
        """
        # Case-insensitive header lookup
        name_lower = name.lower()
        for key, value in self.headers.items():
            if key.lower() == name_lower:
                return value
        return default
