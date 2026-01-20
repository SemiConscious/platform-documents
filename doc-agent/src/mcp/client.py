"""MCP client for communicating with the Natterbox MCP server via SSE."""

import asyncio
import json
import logging
import os
from typing import Any, Optional, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

import httpx

if TYPE_CHECKING:
    from ..auth import OAuthManager

logger = logging.getLogger("doc-agent.mcp.client")


class MCPTransport(str, Enum):
    """MCP transport types."""
    SSE = "sse"
    STDIO = "stdio"


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
    scopes: list[str] = None
    
    def __post_init__(self):
        if self.scopes is None:
            self.scopes = []


class MCPClient:
    """
    Client for interacting with the Natterbox MCP server.
    
    Supports SSE transport with OAuth authentication, which is
    how the Natterbox MCP server operates.
    """
    
    def __init__(
        self,
        server_url: str = "https://avatar.natterbox-dev03.net/mcp/sse",
        transport: MCPTransport = MCPTransport.SSE,
        oauth_config: Optional[MCPOAuthConfig] = None,
        timeout: int = 60,
    ):
        """
        Initialize the MCP client.
        
        Args:
            server_url: URL of the MCP server (for SSE transport)
            transport: Transport type (SSE or STDIO)
            oauth_config: OAuth configuration for the MCP server
            timeout: Default timeout for operations in seconds
        """
        self.server_url = server_url
        self.transport = transport
        self.timeout = timeout
        
        # OAuth config for MCP server's built-in auth
        self.oauth_config = oauth_config or MCPOAuthConfig(
            authorization_url="https://avatar.natterbox-dev03.net/mcp/authorize",
            token_url="https://avatar.natterbox-dev03.net/mcp/token",
            client_id="doc-agent",
            scopes=[],
        )
        
        # Session state
        self._http_client: Optional[httpx.AsyncClient] = None
        self._access_token: Optional[str] = None
        self._connected = False
        self._available_tools: list[dict[str, Any]] = []
        
    async def connect(self) -> None:
        """Establish connection to the MCP server."""
        if self._connected:
            return
            
        logger.info(f"Connecting to MCP server: {self.server_url}")
        
        # Create HTTP client
        self._http_client = httpx.AsyncClient(timeout=self.timeout)
        
        # Authenticate with the MCP server
        await self._authenticate()
        
        # Get available tools
        await self._fetch_tools()
        
        self._connected = True
        logger.info(f"Connected to MCP server with {len(self._available_tools)} tools available")
    
    async def _authenticate(self) -> None:
        """Authenticate with the MCP server using OAuth."""
        from ..auth import TokenCache
        
        # Check for cached token
        cache = TokenCache()
        cached = cache.get("mcp", "access_token", "natterbox")
        
        if cached and not cached.is_expired():
            self._access_token = cached.token
            logger.debug("Using cached MCP access token")
            return
        
        # Try refresh token first
        if cached and cached.refresh_token:
            try:
                new_token = await self._refresh_token(cached.refresh_token)
                if new_token:
                    self._access_token = new_token
                    return
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")
        
        # Need to do OAuth flow
        logger.info("MCP authentication required")
        await self._do_oauth_flow()
    
    async def _do_oauth_flow(self) -> None:
        """Perform OAuth authorization code flow."""
        import secrets
        import webbrowser
        from aiohttp import web
        
        state = secrets.token_urlsafe(16)
        auth_code = None
        
        # Start local callback server
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
            # Build authorization URL
            from urllib.parse import urlencode
            params = {
                "client_id": self.oauth_config.client_id,
                "redirect_uri": "http://localhost:8085/callback",
                "response_type": "code",
                "state": state,
            }
            if self.oauth_config.scopes:
                params["scope"] = " ".join(self.oauth_config.scopes)
            
            auth_url = f"{self.oauth_config.authorization_url}?{urlencode(params)}"
            
            # Open browser
            print(f"\nPlease authenticate with the Natterbox MCP server.")
            print(f"Opening browser... If it doesn't open, visit:\n{auth_url}\n")
            webbrowser.open(auth_url)
            
            # Wait for callback
            for _ in range(300):  # 5 minute timeout
                if auth_code:
                    break
                await asyncio.sleep(1)
            
            if not auth_code:
                raise RuntimeError("OAuth authentication timed out")
            
            # Exchange code for token
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
        
        # Cache the token
        from ..auth import TokenCache
        cache = TokenCache()
        cache.set(
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
        
        # Update cache
        from ..auth import TokenCache
        cache = TokenCache()
        cache.set(
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
        # MCP tools/list endpoint
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
        
        # JSON-RPC request
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }
        
        try:
            # For SSE, we POST to the server URL
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
            return MCPResponse(success=False, data=None, error=f"HTTP {e.response.status_code}: {e.response.text}")
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
        logger.info("Disconnected from MCP server")
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        timeout: Optional[int] = None,
    ) -> MCPResponse:
        """
        Call an MCP tool and return the response.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            timeout: Optional timeout override
            
        Returns:
            MCPResponse with the result or error
        """
        if not self._connected:
            await self.connect()
        
        logger.debug(f"Calling MCP tool: {tool_name}")
        
        # MCP tools/call method
        response = await self._make_request("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })
        
        if response.success and response.data:
            # Extract content from MCP response
            content = response.data.get("content", [])
            if content:
                # Parse text content
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
                
                # Unwrap single results
                if len(data) == 1:
                    data = data[0]
                
                return MCPResponse(success=True, data=data)
        
        return response
    
    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools from the MCP server."""
        if not self._connected:
            await self.connect()
        return self._available_tools
    
    def get_tool_schema(self, tool_name: str) -> Optional[dict[str, Any]]:
        """Get the schema for a specific tool."""
        for tool in self._available_tools:
            if tool["name"] == tool_name:
                return tool
        return None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


class MockMCPClient(MCPClient):
    """
    Mock MCP client for testing and development.
    
    Provides sample data that mimics real MCP responses.
    """
    
    def __init__(self, *args, **kwargs):
        self.server_url = kwargs.get("server_url", "mock://localhost")
        self.timeout = kwargs.get("timeout", 30)
        self._connected = False
        self._mock_data: dict[str, Any] = {}
        self._available_tools: list[dict[str, Any]] = []
    
    def set_mock_data(self, tool_name: str, data: Any) -> None:
        """Set mock data for a specific tool."""
        self._mock_data[tool_name] = data
    
    def add_mock_tool(self, name: str, description: str, schema: dict[str, Any]) -> None:
        """Add a mock tool definition."""
        self._available_tools.append({
            "name": name,
            "description": description,
            "input_schema": schema,
        })
    
    async def connect(self) -> None:
        """Mock connect."""
        self._connected = True
        logger.info(f"Mock connected to: {self.server_url}")
    
    async def disconnect(self) -> None:
        """Mock disconnect."""
        self._connected = False
        logger.info("Mock disconnected")
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        timeout: Optional[int] = None,
    ) -> MCPResponse:
        """Return mock data for the tool call."""
        if tool_name in self._mock_data:
            data = self._mock_data[tool_name]
            # If data is callable, call it with arguments
            if callable(data):
                data = data(arguments)
            return MCPResponse(success=True, data=data)
        
        logger.warning(f"No mock data for tool: {tool_name}")
        return MCPResponse(success=True, data={})
