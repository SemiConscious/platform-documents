"""OAuth manager for Natterbox MCP server services."""

import asyncio
import json
import logging
import secrets
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.parse import urlencode, urlparse, parse_qs
import hashlib
import base64

import httpx

from .token_cache import TokenCache, CachedToken

logger = logging.getLogger("doc-agent.auth.oauth")


@dataclass
class OAuthConfig:
    """OAuth configuration for a service."""
    service: str
    client_id: str
    client_secret: Optional[str] = None
    auth_url: str = ""
    token_url: str = ""
    scopes: list[str] = field(default_factory=list)
    redirect_uri: str = "http://localhost:8085/callback"
    use_pkce: bool = True
    
    @classmethod
    def github(cls, client_id: str, client_secret: Optional[str] = None) -> "OAuthConfig":
        """Create GitHub OAuth config."""
        return cls(
            service="github",
            client_id=client_id,
            client_secret=client_secret,
            auth_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            scopes=["repo", "read:org", "read:user"],
            use_pkce=False,  # GitHub doesn't support PKCE
        )
    
    @classmethod
    def atlassian(cls, client_id: str, client_secret: Optional[str] = None) -> "OAuthConfig":
        """Create Atlassian (Confluence/Jira) OAuth config."""
        return cls(
            service="atlassian",
            client_id=client_id,
            client_secret=client_secret,
            auth_url="https://auth.atlassian.com/authorize",
            token_url="https://auth.atlassian.com/oauth/token",
            scopes=[
                "read:jira-work",
                "read:jira-user",
                "read:confluence-content.all",
                "read:confluence-space.summary",
                "offline_access",
            ],
            use_pkce=True,
        )


@dataclass
class OAuthToken:
    """OAuth token response."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    
    @classmethod
    def from_response(cls, data: dict[str, Any]) -> "OAuthToken":
        """Create from OAuth token response."""
        return cls(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in"),
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope"),
        )


class OAuthCallbackServer:
    """Simple HTTP server to handle OAuth callbacks."""
    
    def __init__(self, port: int = 8085):
        self.port = port
        self.auth_code: Optional[str] = None
        self.error: Optional[str] = None
        self._server = None
    
    async def start(self) -> None:
        """Start the callback server."""
        from aiohttp import web
        
        app = web.Application()
        app.router.add_get("/callback", self._handle_callback)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        self._server = web.TCPSite(runner, "localhost", self.port)
        await self._server.start()
        
        logger.debug(f"OAuth callback server started on port {self.port}")
    
    async def _handle_callback(self, request) -> Any:
        """Handle the OAuth callback."""
        from aiohttp import web
        
        self.auth_code = request.query.get("code")
        self.error = request.query.get("error")
        
        if self.error:
            return web.Response(
                text=f"<html><body><h1>Authentication Failed</h1><p>{self.error}</p></body></html>",
                content_type="text/html",
            )
        
        return web.Response(
            text="<html><body><h1>Authentication Successful</h1><p>You can close this window.</p></body></html>",
            content_type="text/html",
        )
    
    async def wait_for_callback(self, timeout: int = 300) -> Optional[str]:
        """Wait for the OAuth callback."""
        start = datetime.utcnow()
        while (datetime.utcnow() - start).seconds < timeout:
            if self.auth_code or self.error:
                break
            await asyncio.sleep(0.1)
        
        return self.auth_code
    
    async def stop(self) -> None:
        """Stop the callback server."""
        if self._server:
            await self._server.stop()


class OAuthManager:
    """
    OAuth manager for handling authentication with external services.
    
    Supports:
    - OAuth 2.0 authorization code flow
    - PKCE for public clients
    - Token caching and refresh
    - Multiple service configurations
    """
    
    def __init__(
        self,
        token_cache: Optional[TokenCache] = None,
        configs: Optional[dict[str, OAuthConfig]] = None,
    ):
        """
        Initialize the OAuth manager.
        
        Args:
            token_cache: Token cache instance (creates default if not provided)
            configs: Service configurations
        """
        self.cache = token_cache or TokenCache()
        self.configs: dict[str, OAuthConfig] = configs or {}
        self._http_client: Optional[httpx.AsyncClient] = None
    
    def add_config(self, config: OAuthConfig) -> None:
        """Add an OAuth configuration."""
        self.configs[config.service] = config
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    def _generate_pkce(self) -> tuple[str, str]:
        """Generate PKCE code verifier and challenge."""
        # Generate code verifier (43-128 characters)
        verifier = secrets.token_urlsafe(32)
        
        # Generate code challenge (SHA256 hash of verifier, base64url encoded)
        digest = hashlib.sha256(verifier.encode()).digest()
        challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        
        return verifier, challenge
    
    async def get_token(
        self,
        service: str,
        force_refresh: bool = False,
    ) -> Optional[str]:
        """
        Get a valid access token for a service.
        
        Checks cache first, refreshes if expired, prompts for auth if needed.
        
        Args:
            service: Service name
            force_refresh: Force token refresh even if not expired
            
        Returns:
            Access token or None if unavailable
        """
        # Check cache first
        cached = self.cache.get(service, "access_token")
        
        if cached and not force_refresh and not cached.is_expired():
            return cached.token
        
        # Try to refresh
        if cached and cached.refresh_token:
            new_token = await self.refresh_token(service, cached.refresh_token)
            if new_token:
                return new_token.access_token
        
        # Need fresh authentication
        logger.info(f"No valid token for {service}, authentication required")
        return None
    
    async def authenticate(
        self,
        service: str,
        interactive: bool = True,
    ) -> Optional[OAuthToken]:
        """
        Perform OAuth authentication for a service.
        
        Args:
            service: Service name
            interactive: Whether to open browser for user interaction
            
        Returns:
            OAuthToken if successful, None otherwise
        """
        config = self.configs.get(service)
        if not config:
            logger.error(f"No OAuth config for service: {service}")
            return None
        
        # Generate state and PKCE
        state = secrets.token_urlsafe(16)
        verifier, challenge = self._generate_pkce() if config.use_pkce else (None, None)
        
        # Build authorization URL
        params = {
            "client_id": config.client_id,
            "redirect_uri": config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(config.scopes),
            "state": state,
        }
        
        if config.use_pkce and challenge:
            params["code_challenge"] = challenge
            params["code_challenge_method"] = "S256"
        
        # Atlassian-specific
        if service == "atlassian":
            params["audience"] = "api.atlassian.com"
            params["prompt"] = "consent"
        
        auth_url = f"{config.auth_url}?{urlencode(params)}"
        
        if interactive:
            # Start callback server
            callback_server = OAuthCallbackServer()
            await callback_server.start()
            
            try:
                # Open browser for user
                logger.info(f"Opening browser for {service} authentication...")
                print(f"\nPlease authenticate in your browser.\nIf it doesn't open automatically, visit:\n{auth_url}\n")
                webbrowser.open(auth_url)
                
                # Wait for callback
                auth_code = await callback_server.wait_for_callback()
                
                if not auth_code:
                    logger.error("No authorization code received")
                    return None
                
                # Exchange code for token
                return await self._exchange_code(config, auth_code, verifier)
                
            finally:
                await callback_server.stop()
        else:
            # Non-interactive mode - return URL for manual handling
            logger.info(f"Authorization URL: {auth_url}")
            return None
    
    async def _exchange_code(
        self,
        config: OAuthConfig,
        code: str,
        verifier: Optional[str] = None,
    ) -> Optional[OAuthToken]:
        """Exchange authorization code for tokens."""
        client = await self._get_client()
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": config.redirect_uri,
            "client_id": config.client_id,
        }
        
        if config.client_secret:
            data["client_secret"] = config.client_secret
        
        if verifier:
            data["code_verifier"] = verifier
        
        headers = {"Accept": "application/json"}
        
        try:
            response = await client.post(
                config.token_url,
                data=data,
                headers=headers,
            )
            response.raise_for_status()
            
            token_data = response.json()
            token = OAuthToken.from_response(token_data)
            
            # Cache the token
            scopes = token.scope.split() if token.scope else config.scopes
            self.cache.set(
                service=config.service,
                token=token.access_token,
                token_type="access_token",
                expires_in=token.expires_in,
                refresh_token=token.refresh_token,
                scopes=scopes,
            )
            
            logger.info(f"Successfully authenticated with {config.service}")
            return token
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Token exchange failed: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Token exchange error: {e}")
            return None
    
    async def refresh_token(
        self,
        service: str,
        refresh_token: str,
    ) -> Optional[OAuthToken]:
        """
        Refresh an access token.
        
        Args:
            service: Service name
            refresh_token: The refresh token
            
        Returns:
            New OAuthToken if successful
        """
        config = self.configs.get(service)
        if not config:
            logger.error(f"No OAuth config for service: {service}")
            return None
        
        client = await self._get_client()
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": config.client_id,
        }
        
        if config.client_secret:
            data["client_secret"] = config.client_secret
        
        headers = {"Accept": "application/json"}
        
        try:
            response = await client.post(
                config.token_url,
                data=data,
                headers=headers,
            )
            response.raise_for_status()
            
            token_data = response.json()
            token = OAuthToken.from_response(token_data)
            
            # Update cache
            scopes = token.scope.split() if token.scope else None
            self.cache.set(
                service=config.service,
                token=token.access_token,
                token_type="access_token",
                expires_in=token.expires_in,
                refresh_token=token.refresh_token or refresh_token,
                scopes=scopes,
            )
            
            logger.info(f"Successfully refreshed token for {config.service}")
            return token
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Token refresh failed: {e.response.text}")
            # Clear cached token if refresh fails
            self.cache.delete(service, "access_token")
            return None
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None
    
    async def revoke_token(self, service: str) -> bool:
        """
        Revoke tokens for a service.
        
        Args:
            service: Service name
            
        Returns:
            True if revocation was successful
        """
        # Clear from cache regardless of revocation result
        self.cache.clear_service(service)
        logger.info(f"Cleared tokens for {service}")
        return True
    
    def get_auth_header(self, service: str) -> Optional[dict[str, str]]:
        """
        Get authorization header for a service.
        
        Args:
            service: Service name
            
        Returns:
            Dict with Authorization header or None
        """
        cached = self.cache.get(service, "access_token")
        if cached and not cached.is_expired():
            return {"Authorization": f"Bearer {cached.token}"}
        return None
