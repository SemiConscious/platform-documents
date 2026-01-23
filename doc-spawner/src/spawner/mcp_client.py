"""MCP client for communicating with the Natterbox MCP server."""

import asyncio
import json
import logging
import secrets
import webbrowser
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from .auth import TokenCache

logger = logging.getLogger("doc-spawner.mcp_client")


@dataclass
class MCPResponse:
    """Response from an MCP tool call."""
    success: bool
    data: Any
    error: Optional[str] = None


@dataclass
class MCPOAuthConfig:
    """OAuth configuration for MCP server."""
    authorization_url: str
    token_url: str
    client_id: str
    scopes: list[str] | None = None
    
    def __post_init__(self):
        if self.scopes is None:
            self.scopes = []


class MCPClient:
    """
    Client for the Natterbox MCP server.
    
    Handles OAuth authentication and tool calls via SSE transport.
    """
    
    def __init__(
        self,
        server_url: str = "https://avatar.natterbox-dev03.net/mcp/sse",
        oauth_config: Optional[MCPOAuthConfig] = None,
        timeout: int = 60,
    ):
        """
        Initialize the MCP client.
        
        Args:
            server_url: URL of the MCP server
            oauth_config: OAuth configuration
            timeout: Request timeout in seconds
        """
        self.server_url = server_url
        self.timeout = timeout
        
        self.oauth_config = oauth_config or MCPOAuthConfig(
            authorization_url="https://avatar.natterbox-dev03.net/mcp/authorize",
            token_url="https://avatar.natterbox-dev03.net/mcp/token",
            client_id="doc-spawner",
            scopes=[],
        )
        
        self._http_client: Optional[httpx.AsyncClient] = None
        self._access_token: Optional[str] = None
        self._connected = False
        self._available_tools: list[dict[str, Any]] = []
        self._token_cache = TokenCache()
    
    async def connect(self) -> None:
        """Establish connection to the MCP server."""
        if self._connected:
            return
        
        logger.info(f"Connecting to MCP server: {self.server_url}")
        
        self._http_client = httpx.AsyncClient(timeout=self.timeout)
        
        # Authenticate
        await self._authenticate()
        
        # Get available tools
        await self._fetch_tools()
        
        self._connected = True
        logger.info(f"Connected to MCP server with {len(self._available_tools)} tools")
    
    async def _authenticate(self) -> None:
        """Authenticate with the MCP server."""
        # Check for cached token
        cached = self._token_cache.get("mcp", "access_token", "natterbox")
        
        if cached and not cached.is_expired():
            self._access_token = cached.token
            logger.debug("Using cached MCP access token")
            return
        
        # Try refresh token
        if cached and cached.refresh_token:
            try:
                new_token = await self._refresh_token(cached.refresh_token)
                if new_token:
                    self._access_token = new_token
                    return
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")
        
        # Do OAuth flow
        logger.info("MCP authentication required")
        await self._do_oauth_flow()
    
    async def _do_oauth_flow(self) -> None:
        """Perform OAuth authorization code flow."""
        from aiohttp import web
        
        state = secrets.token_urlsafe(16)
        auth_code = None
        
        async def handle_callback(request):
            nonlocal auth_code
            auth_code = request.query.get("code")
            error = request.query.get("error")
            
            if error:
                return web.Response(
                    text=f"<html><body><h1>Authentication Failed</h1><p>{error}</p></body></html>",
                    content_type="text/html",
                )
            
            return web.Response(
                text="<html><body><h1>Authentication Successful</h1><p>You can close this window.</p></body></html>",
                content_type="text/html",
            )
        
        app = web.Application()
        app.router.add_get("/callback", handle_callback)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", 8085)
        await site.start()
        
        try:
            params = {
                "client_id": self.oauth_config.client_id,
                "redirect_uri": "http://localhost:8085/callback",
                "response_type": "code",
                "state": state,
            }
            if self.oauth_config.scopes:
                params["scope"] = " ".join(self.oauth_config.scopes)
            
            auth_url = f"{self.oauth_config.authorization_url}?{urlencode(params)}"
            
            print(f"\nPlease authenticate with the Natterbox MCP server.")
            print(f"Opening browser... If it doesn't open, visit:\n{auth_url}\n")
            webbrowser.open(auth_url)
            
            for _ in range(300):
                if auth_code:
                    break
                await asyncio.sleep(1)
            
            if not auth_code:
                raise RuntimeError("OAuth authentication timed out")
            
            await self._exchange_code(auth_code)
            
        finally:
            await site.stop()
            await runner.cleanup()
    
    async def _exchange_code(self, code: str) -> None:
        """Exchange authorization code for access token."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "http://localhost:8085/callback",
            "client_id": self.oauth_config.client_id,
        }
        
        response = await self._http_client.post(
            self.oauth_config.token_url,
            data=data,
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        
        token_data = response.json()
        self._access_token = token_data["access_token"]
        
        self._token_cache.set(
            service="mcp",
            token=self._access_token,
            token_type="access_token",
            identifier="natterbox",
            expires_in=token_data.get("expires_in"),
            refresh_token=token_data.get("refresh_token"),
        )
        
        logger.info("Successfully authenticated with MCP server")
    
    async def _refresh_token(self, refresh_token: str) -> Optional[str]:
        """Refresh the access token."""
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.oauth_config.client_id,
        }
        
        response = await self._http_client.post(
            self.oauth_config.token_url,
            data=data,
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        
        token_data = response.json()
        new_token = token_data["access_token"]
        
        self._token_cache.set(
            service="mcp",
            token=new_token,
            token_type="access_token",
            identifier="natterbox",
            expires_in=token_data.get("expires_in"),
            refresh_token=token_data.get("refresh_token", refresh_token),
        )
        
        logger.info("Refreshed MCP access token")
        return new_token
    
    async def _fetch_tools(self) -> None:
        """Fetch available tools from the MCP server."""
        response = await self._make_request("tools/list", {})
        
        if response.success and response.data:
            tools = response.data.get("tools", [])
            self._available_tools = [
                {
                    "name": tool.get("name"),
                    "description": tool.get("description"),
                    "input_schema": tool.get("inputSchema"),
                }
                for tool in tools
            ]
    
    async def _make_request(
        self,
        method: str,
        params: dict[str, Any],
    ) -> MCPResponse:
        """Make a JSON-RPC request to the MCP server."""
        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=self.timeout)
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }
        
        try:
            response = await self._http_client.post(
                self.server_url,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "error" in result:
                return MCPResponse(
                    success=False,
                    data=None,
                    error=result["error"].get("message", str(result["error"])),
                )
            
            return MCPResponse(success=True, data=result.get("result"))
            
        except httpx.HTTPStatusError as e:
            return MCPResponse(success=False, data=None, error=f"HTTP {e.response.status_code}")
        except Exception as e:
            return MCPResponse(success=False, data=None, error=str(e))
    
    async def disconnect(self) -> None:
        """Close the MCP connection."""
        if not self._connected:
            return
        
        logger.info("Disconnecting from MCP server")
        
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        
        self._connected = False
        self._available_tools = []
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> MCPResponse:
        """
        Call an MCP tool.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments for the tool
            
        Returns:
            MCPResponse with the result
        """
        if not self._connected:
            await self.connect()
        
        logger.debug(f"Calling MCP tool: {tool_name}")
        
        response = await self._make_request("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })
        
        if response.success and response.data:
            content = response.data.get("content", [])
            if content:
                data = []
                for item in content:
                    if item.get("type") == "text":
                        text = item.get("text", "")
                        try:
                            data.append(json.loads(text))
                        except json.JSONDecodeError:
                            data.append(text)
                    else:
                        data.append(item)
                
                if len(data) == 1:
                    data = data[0]
                
                return MCPResponse(success=True, data=data)
        
        return response
    
    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools."""
        if not self._connected:
            await self.connect()
        return self._available_tools
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
