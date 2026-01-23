"""MCP tool wrappers for external data sources."""

import json
import logging
from typing import Any

from .tools import Tool, ToolResult

logger = logging.getLogger("doc-spawner.mcp_tools")


class MCPToolWrapper(Tool):
    """
    Base wrapper for MCP tools.
    
    Wraps MCP tool calls to provide a consistent interface with the
    local tools used by the spawner system.
    """
    
    def __init__(self, mcp_client: Any, tool_name: str, tool_schema: dict[str, Any]):
        """
        Initialize the MCP tool wrapper.
        
        Args:
            mcp_client: The MCP client instance
            tool_name: Name of the MCP tool
            tool_schema: The tool's schema from MCP
        """
        self.mcp_client = mcp_client
        self.name = tool_name
        self.description = tool_schema.get("description", f"MCP tool: {tool_name}")
        self._schema = tool_schema.get("inputSchema", {})
    
    def get_schema(self) -> dict[str, Any]:
        return self._schema
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the MCP tool."""
        try:
            result = await self.mcp_client.call_tool(self.name, kwargs)
            
            # MCP results come as content blocks
            if hasattr(result, "content") and result.content:
                # Extract text from content blocks
                text_parts = []
                for block in result.content:
                    if hasattr(block, "text"):
                        text_parts.append(block.text)
                    elif isinstance(block, dict) and "text" in block:
                        text_parts.append(block["text"])
                
                data = "\n".join(text_parts)
                
                # Try to parse as JSON
                try:
                    data = json.loads(data)
                except (json.JSONDecodeError, TypeError):
                    pass
                
                return ToolResult(success=True, data=data)
            
            return ToolResult(success=True, data=result)
            
        except Exception as e:
            logger.error(f"MCP tool {self.name} failed: {e}")
            return ToolResult(success=False, error=str(e))


class GitHubTool(Tool):
    """
    GitHub tool for repository operations.
    
    Provides access to GitHub APIs for listing repos, reading files,
    and searching code across organizations.
    """
    
    name = "github"
    description = """Access GitHub repositories across Natterbox organizations.

Operations:
- list_repos: List repositories in an organization
- get_file: Get contents of a file from a repository  
- search_code: Search for code across repositories
- get_repo: Get repository metadata

Organizations available: natterbox, redmatter, SemiConscious"""
    
    def __init__(self, mcp_client: Any):
        self.mcp_client = mcp_client
    
    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["list_repos", "get_file", "search_code", "get_repo"],
                    "description": "The GitHub operation to perform",
                },
                "owner": {
                    "type": "string",
                    "description": "Repository owner (organization or user)",
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name",
                },
                "path": {
                    "type": "string",
                    "description": "File path within repository",
                },
                "query": {
                    "type": "string",
                    "description": "Search query for search_code operation",
                },
                "per_page": {
                    "type": "integer",
                    "description": "Results per page (max 100)",
                    "default": 30,
                },
            },
            "required": ["operation"],
        }
    
    async def execute(
        self,
        operation: str,
        owner: str | None = None,
        repo: str | None = None,
        path: str | None = None,
        query: str | None = None,
        per_page: int = 30,
        **kwargs,
    ) -> ToolResult:
        """Execute a GitHub operation."""
        try:
            if operation == "list_repos":
                if not owner:
                    return ToolResult(success=False, error="owner is required for list_repos")
                
                result = await self.mcp_client.call_tool(
                    "github",
                    {
                        "operation": "list_repos",
                        "owner": owner,
                        "perPage": per_page,
                    },
                )
                return self._parse_result(result)
            
            elif operation == "get_file":
                if not all([owner, repo, path]):
                    return ToolResult(
                        success=False, 
                        error="owner, repo, and path are required for get_file"
                    )
                
                result = await self.mcp_client.call_tool(
                    "github",
                    {
                        "operation": "get_file_content",
                        "owner": owner,
                        "repo": repo,
                        "path": path,
                    },
                )
                return self._parse_result(result)
            
            elif operation == "search_code":
                if not query:
                    return ToolResult(success=False, error="query is required for search_code")
                
                # Add org filter if owner provided
                search_query = query
                if owner:
                    search_query = f"org:{owner} {query}"
                
                result = await self.mcp_client.call_tool(
                    "github",
                    {
                        "operation": "search_code",  # Note: may need to be different
                        "query": search_query,
                        "perPage": per_page,
                    },
                )
                return self._parse_result(result)
            
            elif operation == "get_repo":
                if not all([owner, repo]):
                    return ToolResult(
                        success=False,
                        error="owner and repo are required for get_repo"
                    )
                
                result = await self.mcp_client.call_tool(
                    "github",
                    {
                        "operation": "get_repo",
                        "owner": owner,
                        "repo": repo,
                    },
                )
                return self._parse_result(result)
            
            else:
                return ToolResult(success=False, error=f"Unknown operation: {operation}")
                
        except Exception as e:
            logger.error(f"GitHub tool failed: {e}")
            return ToolResult(success=False, error=str(e))
    
    def _parse_result(self, result: Any) -> ToolResult:
        """Parse MCP result to ToolResult."""
        if hasattr(result, "content") and result.content:
            text_parts = []
            for block in result.content:
                if hasattr(block, "text"):
                    text_parts.append(block.text)
                elif isinstance(block, dict) and "text" in block:
                    text_parts.append(block["text"])
            
            data = "\n".join(text_parts)
            try:
                data = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                pass
            
            return ToolResult(success=True, data=data)
        
        return ToolResult(success=True, data=result)


class ConfluenceTool(Tool):
    """
    Confluence tool for documentation search.
    
    Searches Confluence spaces for existing documentation related to
    services and repositories.
    """
    
    name = "confluence"
    description = """Search Confluence for existing documentation.

Use this to find existing docs about services, architecture, or processes
that can inform your documentation."""
    
    def __init__(self, mcp_client: Any):
        self.mcp_client = mcp_client
    
    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["search", "get_page"],
                    "description": "Operation to perform",
                },
                "query": {
                    "type": "string",
                    "description": "Search query text",
                },
                "page_id": {
                    "type": "string",
                    "description": "Page ID for get_page operation",
                },
                "space_key": {
                    "type": "string",
                    "description": "Confluence space key to search within",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results to return",
                    "default": 10,
                },
            },
            "required": ["operation"],
        }
    
    async def execute(
        self,
        operation: str,
        query: str | None = None,
        page_id: str | None = None,
        space_key: str | None = None,
        max_results: int = 10,
        **kwargs,
    ) -> ToolResult:
        """Execute a Confluence operation."""
        try:
            if operation == "search":
                if not query:
                    return ToolResult(success=False, error="query is required for search")
                
                params = {
                    "operation": "search_content",
                    "query": query,
                    "maxResults": max_results,
                }
                if space_key:
                    params["spaceKey"] = space_key
                
                result = await self.mcp_client.call_tool("confluence", params)
                return self._parse_result(result)
            
            elif operation == "get_page":
                if not page_id:
                    return ToolResult(success=False, error="page_id is required for get_page")
                
                result = await self.mcp_client.call_tool(
                    "confluence",
                    {
                        "operation": "get_page",
                        "pageId": page_id,
                    },
                )
                return self._parse_result(result)
            
            else:
                return ToolResult(success=False, error=f"Unknown operation: {operation}")
                
        except Exception as e:
            logger.error(f"Confluence tool failed: {e}")
            return ToolResult(success=False, error=str(e))
    
    def _parse_result(self, result: Any) -> ToolResult:
        """Parse MCP result."""
        if hasattr(result, "content") and result.content:
            text_parts = []
            for block in result.content:
                if hasattr(block, "text"):
                    text_parts.append(block.text)
                elif isinstance(block, dict) and "text" in block:
                    text_parts.append(block["text"])
            
            data = "\n".join(text_parts)
            try:
                data = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                pass
            
            return ToolResult(success=True, data=data)
        
        return ToolResult(success=True, data=result)


def register_mcp_tools(registry: Any, mcp_client: Any) -> None:
    """
    Register MCP tools with a tool registry.
    
    Args:
        registry: ToolRegistry instance
        mcp_client: Connected MCP client
    """
    # Register wrapped MCP tools
    registry.register(GitHubTool(mcp_client))
    registry.register(ConfluenceTool(mcp_client))
    
    logger.info("Registered MCP tools: github, confluence")
