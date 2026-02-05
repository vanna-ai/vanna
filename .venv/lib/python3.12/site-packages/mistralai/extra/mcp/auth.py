import logging

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client as AsyncOAuth2ClientBase
from authlib.oauth2.rfc8414 import AuthorizationServerMetadata

from mistralai.types import BaseModel

logger = logging.getLogger(__name__)


class Oauth2AuthorizationScheme(BaseModel):
    """Information about the oauth flow to perform with the authorization server."""

    authorization_url: str
    token_url: str
    scope: list[str]
    description: str | None = None
    refresh_url: str | None = None


class OAuthParams(BaseModel):
    """Required params for authorization."""

    scheme: Oauth2AuthorizationScheme
    client_id: str
    client_secret: str


class AsyncOAuth2Client(AsyncOAuth2ClientBase):
    """Subclass of the Async httpx oauth client which provides a constructor from OAuthParams."""

    @classmethod
    def from_oauth_params(cls, oauth_params: OAuthParams) -> "AsyncOAuth2Client":
        return cls(
            client_id=oauth_params.client_id,
            client_secret=oauth_params.client_secret,
            scope=oauth_params.scheme.scope,
        )


async def get_well_known_authorization_server_metadata(
    server_url: str,
) -> AuthorizationServerMetadata | None:
    """Fetch the metadata from the well-known location.

    This should be available on MCP servers as described by the specification:
    https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization#2-3-server-metadata-discovery.
    """
    well_known_url = f"{server_url}/.well-known/oauth-authorization-server"
    response = await httpx.AsyncClient().get(well_known_url)
    if 200 <= response.status_code < 300:
        try:
            server_metadata = AuthorizationServerMetadata(**response.json())
            server_metadata.validate()
            return server_metadata
        except ValueError:
            logger.exception("Failed to parse oauth well-known metadata")
            return None
    else:
        logger.error(f"Failed to get oauth well-known metadata from {server_url}")
        return None


async def get_oauth_server_metadata(server_url: str) -> AuthorizationServerMetadata:
    """Fetch the metadata from the authorization server to perform the oauth flow."""
    # 1) attempt to get the metadata from the resource server at /.well-known/oauth-protected-resource
    # TODO: new self-discovery protocol, not released yet

    # 2) attempt to get the metadata from the authorization server at /.well-known/oauth-authorization-server
    metadata = await get_well_known_authorization_server_metadata(server_url=server_url)
    if metadata is not None:
        return metadata

    # 3) fallback on default endpoints
    # https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization#2-3-3-fallbacks-for-servers-without-metadata-discovery
    return AuthorizationServerMetadata(
        issuer=server_url,
        authorization_endpoint=f"{server_url}/authorize",
        token_endpoint=f"{server_url}/token",
        register_endpoint=f"{server_url}/register",
        response_types_supported=["code"],
        response_modes_supported=["query"],
        grant_types_supported=["authorization_code", "refresh_token"],
        token_endpoint_auth_methods_supported=["client_secret_basic"],
        code_challenge_methods_supported=["S256", "plain"],
    )


async def dynamic_client_registration(
    register_endpoint: str,
    redirect_url: str,
    async_client: httpx.AsyncClient,
) -> tuple[str, str]:
    """Try to register the client dynamically with an MCP server.

    Returns a client_id and client_secret.
    """
    # Construct the registration request payload
    registration_payload = {
        "client_name": "MistralSDKClient",
        "grant_types": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_method": "client_secret_basic",
        "response_types": ["code"],
        "redirect_uris": [redirect_url],
    }

    # Make the registration request
    response = await async_client.post(register_endpoint, json=registration_payload)
    try:
        response.raise_for_status()
        registration_info = response.json()
        client_id = registration_info["client_id"]
        client_secret = registration_info["client_secret"]
    except Exception as e:
        raise ValueError(
            f"Client registration failed: status={response.status_code}, error={response.text}"
        ) from e
    return client_id, client_secret


async def build_oauth_params(
    server_url: str,
    redirect_url: str,
    client_id: str | None = None,
    client_secret: str | None = None,
    scope: list[str] | None = None,
    async_client: httpx.AsyncClient | None = None,
) -> OAuthParams:
    """Get issuer metadata and build the oauth required params."""
    metadata = await get_oauth_server_metadata(server_url=server_url)
    oauth_scheme = Oauth2AuthorizationScheme(
        authorization_url=metadata.authorization_endpoint,
        token_url=metadata.token_endpoint,
        scope=scope or [],
        refresh_url=metadata.token_endpoint
        if "refresh_token" in metadata.grant_types_supported
        else None,
    )
    if client_id and client_secret:
        return OAuthParams(
            client_id=client_id,
            client_secret=client_secret,
            scheme=oauth_scheme,
        )

    # Try to dynamically register the client
    if async_client:
        reg_client_id, reg_client_secret = await dynamic_client_registration(
            register_endpoint=metadata.registration_endpoint,
            redirect_url=redirect_url,
            async_client=async_client,
        )
    else:
        async with httpx.AsyncClient() as async_client:
            reg_client_id, reg_client_secret = await dynamic_client_registration(
                register_endpoint=metadata.registration_endpoint,
                redirect_url=redirect_url,
                async_client=async_client,
            )
    return OAuthParams(
        client_id=reg_client_id,
        client_secret=reg_client_secret,
        scheme=oauth_scheme,
    )
