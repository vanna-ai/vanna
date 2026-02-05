import http
import logging
from contextlib import AsyncExitStack
from functools import cached_property
from typing import Any

import httpx
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from authlib.oauth2.rfc6749 import OAuth2Token
from mcp.client.sse import sse_client  # pyright: ignore[reportMissingImports]
from mcp.shared.message import SessionMessage  # pyright: ignore[reportMissingImports]

from mistralai.extra.exceptions import MCPAuthException
from mistralai.extra.mcp.base import (
    MCPClientBase,
)
from mistralai.extra.mcp.auth import OAuthParams, AsyncOAuth2Client

from mistralai.types import BaseModel

logger = logging.getLogger(__name__)


class SSEServerParams(BaseModel):
    """Parameters required for a MCPClient with SSE transport"""

    url: str
    headers: dict[str, Any] | None = None
    timeout: float = 5
    sse_read_timeout: float = 60 * 5


class MCPClientSSE(MCPClientBase):
    """MCP client that uses sse for communication.

    The client provides authentication for OAuth2 protocol following the current MCP authorization spec:
    https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization.

    This is possibly going to change in the future since the protocol has ongoing discussions.
    """

    _oauth_params: OAuthParams | None
    _sse_params: SSEServerParams

    def __init__(
        self,
        sse_params: SSEServerParams,
        name: str | None = None,
        oauth_params: OAuthParams | None = None,
        auth_token: OAuth2Token | None = None,
    ):
        super().__init__(name=name)
        self._sse_params = sse_params
        self._oauth_params: OAuthParams | None = oauth_params
        self._auth_token: OAuth2Token | None = auth_token

    @cached_property
    def base_url(self) -> str:
        return self._sse_params.url.rstrip("/sse")

    def set_oauth_params(self, oauth_params: OAuthParams):
        """Update the oauth params and client accordingly."""
        if self._oauth_params is not None:
            logger.warning(f"Overriding current oauth params for {self._name}")
        self._oauth_params = oauth_params

    async def get_auth_url_and_state(self, redirect_url: str) -> tuple[str, str]:
        """Create the authorization url for client to start oauth flow."""
        if self._oauth_params is None:
            raise MCPAuthException(
                "Can't generate an authorization url without oauth_params being set, "
                "make sure the oauth params have been set."
            )
        oauth_client = AsyncOAuth2Client.from_oauth_params(self._oauth_params)
        auth_url, state = oauth_client.create_authorization_url(
            self._oauth_params.scheme.authorization_url, redirect_uri=redirect_url
        )
        return auth_url, state

    async def get_token_from_auth_response(
        self,
        authorization_response: str,
        redirect_url: str,
        state: str,
    ) -> OAuth2Token:
        """Fetch the authentication token from the server."""
        if self._oauth_params is None:
            raise MCPAuthException(
                "Can't fetch a token without oauth_params, make sure they have been set."
            )
        oauth_client = AsyncOAuth2Client.from_oauth_params(self._oauth_params)
        oauth_token = await oauth_client.fetch_token(
            url=self._oauth_params.scheme.token_url,
            authorization_response=authorization_response,
            redirect_uri=redirect_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            state=state,
        )
        return oauth_token

    async def refresh_auth_token(self):
        """Refresh an expired token."""
        if self._oauth_params is None or self._oauth_params.scheme.refresh_url is None:
            raise MCPAuthException(
                "Can't refresh a token without a refresh url make sure the oauth params have been set."
            )
        if self._auth_token is None:
            raise MCPAuthException(
                "Can't refresh a token without a refresh token, use the `set_auth_token` to add a OAuth2Token."
            )
        oauth_client = AsyncOAuth2Client.from_oauth_params(self._oauth_params)
        oauth_token = await oauth_client.refresh_token(
            url=self._oauth_params.scheme.refresh_url,
            refresh_token=self._auth_token["refresh_token"],
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.set_auth_token(oauth_token)

    def set_auth_token(self, token: OAuth2Token) -> None:
        """Register the authentication token with this client."""
        self._auth_token = token

    def _format_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self._sse_params.headers:
            headers |= self._sse_params.headers
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token['access_token']}"
        return headers

    async def requires_auth(self) -> bool:
        """Check if the client requires authentication to communicate with the server."""
        response = httpx.get(
            self._sse_params.url,
            headers=self._format_headers(),
            timeout=self._sse_params.timeout,
        )
        return response.status_code == http.HTTPStatus.UNAUTHORIZED

    async def _get_transport(
        self, exit_stack: AsyncExitStack
    ) -> tuple[
        MemoryObjectReceiveStream[SessionMessage | Exception],
        MemoryObjectSendStream[SessionMessage],
    ]:
        try:
            return await exit_stack.enter_async_context(
                sse_client(
                    url=self._sse_params.url,
                    headers=self._format_headers(),
                    timeout=self._sse_params.timeout,
                    sse_read_timeout=self._sse_params.sse_read_timeout,
                )
            )
        except Exception as e:
            if isinstance(e, httpx.HTTPStatusError):
                if e.response.status_code == http.HTTPStatus.UNAUTHORIZED:
                    if self._oauth_params is None:
                        raise MCPAuthException(
                            "Authentication required but no auth params provided."
                        ) from e
                    raise MCPAuthException("Authentication required.") from e
            raise
