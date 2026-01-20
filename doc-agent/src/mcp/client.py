"""Base MCP client for communicating with the Natterbox MCP server."""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Optional
from dataclasses import dataclass

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger("doc-agent.mcp.client")


@dataclass
class MCPResponse:
    """Response from an MCP tool call."""
    success: bool
    data: Any
    error: Optional[str] = None


class MCPClient:
    """
    Client for interacting with the Natterbox MCP server.
    
    This client provides a programmatic interface to call MCP tools
    and retrieve data from GitHub, Confluence, and Jira via the
    Natterbox MCP server.
    """
    
    def __init__(
        self,
        server_name: str = "natterbox",
        server_command: Optional[str] = None,
        server_args: Optional[list[str]] = None,
        server_env: Optional[dict[str, str]] = None,
        timeout: int = 60,
    ):
        """
        Initialize the MCP client.
        
        Args:
            server_name: Name of the MCP server (for logging)
            server_command: Command to launch the MCP server (e.g., "npx")
            server_args: Arguments for the server command
            server_env: Additional environment variables for the server
            timeout: Default timeout for operations in seconds
        """
        self.server_name = server_name
        self.timeout = timeout
        
        # Server launch configuration
        # Default assumes the natterbox MCP server is an npm package
        self.server_command = server_command or os.environ.get(
            "MCP_SERVER_COMMAND", "npx"
        )
        self.server_args = server_args or [
            arg for arg in os.environ.get(
                "MCP_SERVER_ARGS", "@natterbox/mcp-server"
            ).split()
        ]
        self.server_env = server_env or {}
        
        # Session state
        self._session: Optional[ClientSession] = None
        self._client_context = None
        self._connected = False
        self._available_tools: list[dict[str, Any]] = []
        
    async def connect(self) -> None:
        """Establish connection to the MCP server."""
        if self._connected:
            return
            
        logger.info(f"Connecting to MCP server: {self.server_name}")
        logger.debug(f"Server command: {self.server_command} {' '.join(self.server_args)}")
        
        # Merge environment
        env = {**os.environ, **self.server_env}
        
        # Create server parameters
        server_params = StdioServerParameters(
            command=self.server_command,
            args=self.server_args,
            env=env,
        )
        
        # Create the client context
        self._client_context = stdio_client(server_params)
        read, write = await self._client_context.__aenter__()
        
        # Create and initialize session
        self._session = ClientSession(read, write)
        await self._session.__aenter__()
        await self._session.initialize()
        
        # Cache available tools
        tools_result = await self._session.list_tools()
        self._available_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in tools_result.tools
        ]
        
        self._connected = True
        logger.info(f"Connected to MCP server with {len(self._available_tools)} tools available")
    
    async def disconnect(self) -> None:
        """Close the MCP connection."""
        if not self._connected:
            return
            
        logger.info("Disconnecting from MCP server")
        
        if self._session:
            await self._session.__aexit__(None, None, None)
            self._session = None
            
        if self._client_context:
            await self._client_context.__aexit__(None, None, None)
            self._client_context = None
        
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
        
        effective_timeout = timeout or self.timeout
        
        try:
            logger.debug(f"Calling MCP tool: {tool_name} with args: {json.dumps(arguments)[:200]}")
            
            # Call the tool with timeout
            result = await asyncio.wait_for(
                self._session.call_tool(tool_name, arguments),
                timeout=effective_timeout,
            )
            
            # Extract content from the result
            if result.content:
                # MCP tool results can have multiple content blocks
                # Usually we want the text content
                data = []
                for content_block in result.content:
                    if hasattr(content_block, 'text'):
                        # Try to parse as JSON
                        try:
                            parsed = json.loads(content_block.text)
                            data.append(parsed)
                        except json.JSONDecodeError:
                            data.append(content_block.text)
                    elif hasattr(content_block, 'data'):
                        data.append(content_block.data)
                
                # If single result, unwrap
                if len(data) == 1:
                    data = data[0]
                
                return MCPResponse(success=True, data=data)
            
            return MCPResponse(success=True, data=None)
            
        except asyncio.TimeoutError:
            error_msg = f"Tool call timed out after {effective_timeout}s"
            logger.error(error_msg)
            return MCPResponse(success=False, data=None, error=error_msg)
            
        except Exception as e:
            error_msg = f"Tool call failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return MCPResponse(success=False, data=None, error=error_msg)
    
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
        # Don't call parent __init__ to avoid setting up real server params
        self.server_name = kwargs.get("server_name", "mock")
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
        logger.info(f"Mock connected to: {self.server_name}")
    
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
