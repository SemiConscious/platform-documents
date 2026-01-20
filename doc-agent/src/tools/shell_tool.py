"""Shell execution tool for agents."""

import asyncio
import logging
import os
import shlex
from pathlib import Path
from typing import Any, Optional

from .tool_registry import Tool, ToolResult

logger = logging.getLogger("doc-agent.tools.shell")


class ShellTool(Tool):
    """
    Tool for executing shell commands.
    
    Includes safety restrictions on dangerous commands.
    """
    
    name = "shell_exec"
    description = """Execute a shell command in the workspace.
    
Supports:
- Running arbitrary shell commands
- Capturing stdout and stderr
- Setting working directory
- Timeout enforcement

Safety restrictions:
- Certain dangerous commands are blocked (rm -rf /, sudo, etc.)
- Commands run with workspace as working directory by default
- Output is captured and returned, not streamed

Use this to:
- Run linters or formatters on code
- Execute build commands
- Check git status or history
- Run analysis scripts
- Install dependencies
- Verify file contents with standard tools"""
    
    def __init__(
        self,
        registry: "ToolRegistry",
        default_timeout: int = 60,
        max_output_size: int = 100_000,
    ):
        self.registry = registry
        self.default_timeout = default_timeout
        self.max_output_size = max_output_size
    
    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute",
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory (relative to workspace or absolute, default: workspace root)",
                },
                "timeout": {
                    "type": "integer",
                    "description": f"Command timeout in seconds (default: {self.default_timeout})",
                },
                "env": {
                    "type": "object",
                    "description": "Additional environment variables to set",
                    "additionalProperties": {"type": "string"},
                },
            },
            "required": ["command"],
        }
    
    async def execute(
        self,
        command: str,
        working_dir: Optional[str] = None,
        timeout: Optional[int] = None,
        env: Optional[dict[str, str]] = None,
        **kwargs,
    ) -> ToolResult:
        """Execute a shell command."""
        try:
            # Security check
            if self.registry.is_command_blocked(command):
                return ToolResult(
                    success=False,
                    error=f"Command blocked for safety: {command}",
                )
            
            # Resolve working directory
            if working_dir:
                cwd = Path(working_dir)
                if not cwd.is_absolute():
                    cwd = self.registry.workspace_root / cwd
                cwd = cwd.resolve()
                
                # Security check
                if not self.registry.is_path_allowed(cwd):
                    return ToolResult(
                        success=False,
                        error=f"Working directory not allowed: {working_dir}",
                    )
            else:
                cwd = self.registry.workspace_root
            
            if not cwd.exists():
                return ToolResult(
                    success=False,
                    error=f"Working directory does not exist: {cwd}",
                )
            
            # Prepare environment
            run_env = os.environ.copy()
            if env:
                run_env.update(env)
            
            # Execute command
            timeout_secs = timeout or self.default_timeout
            
            logger.debug(f"Executing command: {command} in {cwd}")
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd),
                env=run_env,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_secs,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    error=f"Command timed out after {timeout_secs}s",
                    metadata={"command": command, "timeout": timeout_secs},
                )
            
            # Decode output
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            # Truncate if too large
            if len(stdout_str) > self.max_output_size:
                stdout_str = stdout_str[:self.max_output_size] + f"\n... (truncated, total {len(stdout)} bytes)"
            if len(stderr_str) > self.max_output_size:
                stderr_str = stderr_str[:self.max_output_size] + f"\n... (truncated, total {len(stderr)} bytes)"
            
            return ToolResult(
                success=process.returncode == 0,
                data={
                    "stdout": stdout_str,
                    "stderr": stderr_str,
                    "exit_code": process.returncode,
                },
                error=stderr_str if process.returncode != 0 else None,
                metadata={
                    "command": command,
                    "working_dir": str(cwd),
                    "exit_code": process.returncode,
                },
            )
            
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            return ToolResult(
                success=False,
                error=str(e),
            )


class GitTool(Tool):
    """
    Specialized tool for git operations.
    
    Provides safe access to git commands with parsed output.
    """
    
    name = "git"
    description = """Execute git commands in the workspace repository.
    
Supports:
- status: Get current repository status
- log: Get commit history
- diff: Show changes between commits or working tree
- branch: List or manage branches
- show: Show commit details

Use this to:
- Check what files have changed
- Review commit history
- Compare versions of files
- Understand the repository state"""
    
    def __init__(self, registry: "ToolRegistry"):
        self.registry = registry
        self._shell = ShellTool(registry, default_timeout=30)
    
    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["status", "log", "diff", "branch", "show", "ls-files"],
                    "description": "Git operation to perform",
                },
                "args": {
                    "type": "string",
                    "description": "Additional arguments for the git command",
                },
                "path": {
                    "type": "string",
                    "description": "Path to limit the operation to (relative to repo root)",
                },
            },
            "required": ["operation"],
        }
    
    async def execute(
        self,
        operation: str,
        args: Optional[str] = None,
        path: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        """Execute a git command."""
        # Build command
        allowed_ops = ["status", "log", "diff", "branch", "show", "ls-files"]
        if operation not in allowed_ops:
            return ToolResult(
                success=False,
                error=f"Unknown git operation: {operation}. Allowed: {allowed_ops}",
            )
        
        # Base command
        command = f"git {operation}"
        
        # Add operation-specific defaults
        if operation == "log":
            if not args or "--oneline" not in args:
                command += " --oneline -20"  # Default: one-line format, last 20
        elif operation == "diff":
            if not args:
                command += " --stat"  # Default: show stats
        elif operation == "branch":
            if not args:
                command += " -a"  # Default: show all branches
        
        # Add extra args
        if args:
            command += f" {args}"
        
        # Add path if specified
        if path:
            command += f" -- {shlex.quote(path)}"
        
        # Execute via shell tool
        result = await self._shell.execute(command)
        
        # Add git-specific metadata
        if result.metadata is None:
            result.metadata = {}
        result.metadata["git_operation"] = operation
        
        return result
