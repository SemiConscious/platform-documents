"""Tool registry for managing local tools available to agents."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger("doc-agent.tools.registry")


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Tool(ABC):
    """Base class for local tools."""
    
    name: str = "base_tool"
    description: str = "Base tool"
    
    @abstractmethod
    def get_schema(self) -> dict[str, Any]:
        """Get the tool's JSON schema for Claude."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        pass


class ToolRegistry:
    """
    Registry for local tools available to agents.
    
    Manages tool registration, schema generation for Claude,
    and tool execution.
    """
    
    def __init__(
        self,
        workspace_root: Path,
        output_dir: Path,
        allowed_paths: Optional[list[Path]] = None,
        blocked_commands: Optional[list[str]] = None,
    ):
        """
        Initialize the tool registry.
        
        Args:
            workspace_root: Root directory of the workspace
            output_dir: Directory for documentation output
            allowed_paths: Paths allowed for file operations (default: workspace_root)
            blocked_commands: Commands blocked from shell execution
        """
        self.workspace_root = workspace_root.resolve()
        self.output_dir = output_dir.resolve()
        self.allowed_paths = [p.resolve() for p in (allowed_paths or [workspace_root])]
        self.blocked_commands = blocked_commands or [
            "rm -rf /", "rm -rf ~", "rm -rf *",
            "sudo", "su",
            "chmod 777", "chmod -R 777",
            "> /dev/sda", "dd if=",
            "mkfs", "fdisk",
            ":(){:|:&};:",  # Fork bomb
        ]
        
        self._tools: dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
    
    def get_schemas_for_claude(self) -> list[dict[str, Any]]:
        """
        Get tool schemas formatted for Claude's tool use.
        
        Returns:
            List of tool definitions for Claude API
        """
        schemas = []
        for tool in self._tools.values():
            schema = tool.get_schema()
            schemas.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": schema,
            })
        return schemas
    
    async def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool arguments
            
        Returns:
            ToolResult with execution outcome
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Unknown tool: {tool_name}",
            )
        
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
            )
    
    def is_path_allowed(self, path: Path) -> bool:
        """Check if a path is within allowed directories."""
        resolved = path.resolve()
        return any(
            resolved == allowed or allowed in resolved.parents
            for allowed in self.allowed_paths
        )
    
    def is_command_blocked(self, command: str) -> bool:
        """Check if a command contains blocked patterns."""
        cmd_lower = command.lower()
        return any(blocked.lower() in cmd_lower for blocked in self.blocked_commands)
