"""Base MCP client for communicating with the Natterbox MCP server."""

import asyncio
import json
import logging
from typing import Any, Optional
from dataclasses import dataclass

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
    and retrieve data from GitHub, Confluence, and Jira.
    """
    
    def __init__(self, server_name: str = "natterbox", timeout: int = 30):
        """
        Initialize the MCP client.
        
        Args:
            server_name: Name of the MCP server to connect to
            timeout: Default timeout for operations in seconds
        """
        self.server_name = server_name
        self.timeout = timeout
        self._connected = False
        
    async def connect(self) -> None:
        """Establish connection to the MCP server."""
        # In a real implementation, this would establish the MCP connection
        # For now, we'll rely on the MCP being available through the environment
        self._connected = True
        logger.info(f"Connected to MCP server: {self.server_name}")
    
    async def disconnect(self) -> None:
        """Close the MCP connection."""
        self._connected = False
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
            logger.debug(f"Calling MCP tool: {tool_name} with args: {arguments}")
            
            # This is a placeholder for the actual MCP tool call
            # In the real implementation, this would use the MCP protocol
            # to call tools on the connected server
            result = await self._execute_tool(tool_name, arguments, effective_timeout)
            
            return MCPResponse(success=True, data=result)
            
        except asyncio.TimeoutError:
            error_msg = f"Tool call timed out after {effective_timeout}s"
            logger.error(error_msg)
            return MCPResponse(success=False, data=None, error=error_msg)
            
        except Exception as e:
            error_msg = f"Tool call failed: {str(e)}"
            logger.error(error_msg)
            return MCPResponse(success=False, data=None, error=error_msg)
    
    async def _execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        timeout: int,
    ) -> Any:
        """
        Execute an MCP tool call.
        
        This method should be overridden or the client should be configured
        to actually communicate with the MCP server. For now, it raises
        NotImplementedError to indicate where the actual implementation goes.
        """
        # In production, this would:
        # 1. Serialize the tool call request
        # 2. Send it to the MCP server via the appropriate transport
        # 3. Wait for and deserialize the response
        # 4. Return the result
        
        raise NotImplementedError(
            f"MCP tool execution not implemented. "
            f"Tool: {tool_name}, Args: {arguments}"
        )
    
    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools from the MCP server."""
        response = await self.call_tool("list_tools", {})
        if response.success:
            return response.data or []
        return []
    
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
        super().__init__(*args, **kwargs)
        self._mock_data: dict[str, Any] = {}
    
    def set_mock_data(self, tool_name: str, data: Any) -> None:
        """Set mock data for a specific tool."""
        self._mock_data[tool_name] = data
    
    async def _execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        timeout: int,
    ) -> Any:
        """Return mock data for the tool call."""
        if tool_name in self._mock_data:
            return self._mock_data[tool_name]
        
        # Return empty results for unknown tools
        logger.warning(f"No mock data for tool: {tool_name}")
        return {}
