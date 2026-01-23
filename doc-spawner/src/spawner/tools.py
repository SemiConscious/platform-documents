"""Tools available to agents, including the spawn_agent tool."""

import asyncio
import json
import logging
import os
import re
import shlex
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import AgentTask

logger = logging.getLogger("doc-spawner.tools")


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    data: Any = None
    error: str | None = None


class Tool(ABC):
    """Base class for tools."""
    
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


class SpawnAgentTool(Tool):
    """
    Tool that allows agents to spawn child agents.
    
    This is the key innovation - agents can delegate work to children
    who operate independently (fire-and-forget pattern).
    """
    
    name = "spawn_agent"
    description = """Spawn a child agent with a specific documentation task. 
The child will execute independently and you will not receive any feedback from it.
Use this to delegate work when:
- A task is too large for one agent
- Work can be done in parallel
- A subtask requires specialized focus

The child agent will have the same tools available as you, including the ability
to spawn its own children (up to the maximum depth).

IMPORTANT: Provide enough context in the task_description for the child to work
completely independently. Include specific repo names, paths, and any relevant
information the child will need."""
    
    def __init__(
        self,
        task_queue: Any,  # TaskQueue - avoiding circular import
        current_depth: int,
        max_depth: int,
        max_tasks: int,
        parent_task_id: str,
    ):
        self.task_queue = task_queue
        self.current_depth = current_depth
        self.max_depth = max_depth
        self.max_tasks = max_tasks
        self.parent_task_id = parent_task_id
    
    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task_description": {
                    "type": "string",
                    "description": "Detailed description of what the child agent should accomplish. Be specific about repos, services, or areas to document.",
                },
                "output_path": {
                    "type": "string",
                    "description": "Path where the agent should write documentation (relative to docs root). Example: 'services/platform-api' or 'repositories/natterbox/auth-service'",
                },
                "context": {
                    "type": "string",
                    "description": "Optional additional context the child needs (JSON data, lists, etc.)",
                },
            },
            "required": ["task_description", "output_path"],
        }
    
    async def execute(
        self,
        task_description: str,
        output_path: str,
        context: str | None = None,
    ) -> ToolResult:
        """Spawn a child agent task."""
        child_depth = self.current_depth + 1
        
        # Check depth limit
        if child_depth > self.max_depth:
            return ToolResult(
                success=False,
                error=f"Cannot spawn child: maximum depth {self.max_depth} reached. "
                      f"Current depth is {self.current_depth}. "
                      "You must complete this task yourself without delegating further.",
            )
        
        # Check total task limit
        stats = await self.task_queue.get_stats()
        if stats.total >= self.max_tasks:
            return ToolResult(
                success=False,
                error=f"Cannot spawn child: maximum tasks ({self.max_tasks}) reached. "
                      f"There are already {stats.total} tasks. "
                      "You must complete this task yourself without delegating further.",
            )
        
        # Create the child task
        task = AgentTask.create(
            prompt=task_description,
            output_path=output_path,
            depth=child_depth,
            parent_task_id=self.parent_task_id,
            context=context,
        )
        
        # Add to queue (fire-and-forget)
        await self.task_queue.add_task(task)
        
        logger.info(
            f"Spawned child agent {task.task_id[:8]} at depth {child_depth} "
            f"for output path: {output_path}"
        )
        
        return ToolResult(
            success=True,
            data={
                "task_id": task.task_id,
                "depth": child_depth,
                "message": f"Child agent spawned successfully. It will execute independently "
                          f"and write to '{output_path}'. You will not receive feedback from it.",
            },
        )


class FileReadTool(Tool):
    """Tool for reading files from allowed directories."""
    
    name = "file_read"
    description = """Read the contents of a file. Use this to examine source code,
configuration files, existing documentation, or any other text files.
You can read files from the repository clones or existing documentation."""
    
    def __init__(self, allowed_paths: list[Path]):
        self.allowed_paths = [p.resolve() for p in allowed_paths]
    
    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read (absolute or relative to workspace)",
                },
                "start_line": {
                    "type": "integer",
                    "description": "Optional: first line to read (1-indexed)",
                },
                "end_line": {
                    "type": "integer",
                    "description": "Optional: last line to read (1-indexed)",
                },
            },
            "required": ["path"],
        }
    
    async def execute(
        self,
        path: str,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> ToolResult:
        """Read a file."""
        file_path = Path(path).resolve()
        
        # Security check
        if not self._is_allowed(file_path):
            return ToolResult(
                success=False,
                error=f"Access denied: {path} is outside allowed directories",
            )
        
        if not file_path.exists():
            return ToolResult(success=False, error=f"File not found: {path}")
        
        if not file_path.is_file():
            return ToolResult(success=False, error=f"Not a file: {path}")
        
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            
            # Apply line range if specified
            if start_line or end_line:
                lines = content.splitlines()
                start_idx = (start_line - 1) if start_line else 0
                end_idx = end_line if end_line else len(lines)
                content = "\n".join(lines[start_idx:end_idx])
            
            # Truncate very large files
            if len(content) > 100_000:
                content = content[:100_000] + "\n\n... [truncated - file too large]"
            
            return ToolResult(success=True, data=content)
            
        except Exception as e:
            return ToolResult(success=False, error=f"Error reading file: {e}")
    
    def _is_allowed(self, path: Path) -> bool:
        """Check if path is within allowed directories."""
        resolved = path.resolve()
        return any(
            resolved == allowed or allowed in resolved.parents
            for allowed in self.allowed_paths
        )


class FileWriteTool(Tool):
    """Tool for writing documentation files."""
    
    name = "file_write"
    description = """Write content to a file. Use this to create documentation files.
You can only write to the documentation output directory.
Parent directories will be created automatically if they don't exist."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir.resolve()
    
    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path for the file (relative to output directory)",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
                "append": {
                    "type": "boolean",
                    "description": "If true, append to existing file instead of overwriting",
                },
            },
            "required": ["path", "content"],
        }
    
    async def execute(
        self,
        path: str,
        content: str,
        append: bool = False,
    ) -> ToolResult:
        """Write a file."""
        # Construct full path
        file_path = (self.output_dir / path).resolve()
        
        # Security check - must be within output directory
        if self.output_dir not in file_path.parents and file_path != self.output_dir:
            return ToolResult(
                success=False,
                error=f"Access denied: can only write within {self.output_dir}",
            )
        
        try:
            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            mode = "a" if append else "w"
            with open(file_path, mode, encoding="utf-8") as f:
                f.write(content)
            
            bytes_written = len(content.encode("utf-8"))
            logger.info(f"Wrote: {file_path} ({bytes_written:,} bytes)")
            
            return ToolResult(
                success=True,
                data={"path": str(file_path), "bytes_written": bytes_written},
            )
            
        except Exception as e:
            return ToolResult(success=False, error=f"Error writing file: {e}")


class FileListTool(Tool):
    """Tool for listing directory contents."""
    
    name = "file_list"
    description = """List files and directories in a path. Use this to explore
repository structure, find source files, or see what documentation already exists."""
    
    def __init__(self, allowed_paths: list[Path]):
        self.allowed_paths = [p.resolve() for p in allowed_paths]
    
    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to list",
                },
                "pattern": {
                    "type": "string",
                    "description": "Optional glob pattern to filter files (e.g., '*.py', '*.md')",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "If true, list recursively (default: false)",
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum recursion depth (default: 3)",
                },
            },
            "required": ["path"],
        }
    
    async def execute(
        self,
        path: str,
        pattern: str | None = None,
        recursive: bool = False,
        max_depth: int = 3,
    ) -> ToolResult:
        """List directory contents."""
        dir_path = Path(path).resolve()
        
        # Security check
        if not self._is_allowed(dir_path):
            return ToolResult(
                success=False,
                error=f"Access denied: {path} is outside allowed directories",
            )
        
        if not dir_path.exists():
            return ToolResult(success=False, error=f"Directory not found: {path}")
        
        if not dir_path.is_dir():
            return ToolResult(success=False, error=f"Not a directory: {path}")
        
        try:
            files = []
            if recursive:
                for item in self._walk_limited(dir_path, max_depth):
                    if pattern and not item.match(pattern):
                        continue
                    rel_path = item.relative_to(dir_path)
                    files.append({
                        "path": str(rel_path),
                        "type": "dir" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None,
                    })
            else:
                for item in sorted(dir_path.iterdir()):
                    if pattern and not item.match(pattern):
                        continue
                    files.append({
                        "path": item.name,
                        "type": "dir" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None,
                    })
            
            # Limit results
            if len(files) > 500:
                files = files[:500]
                files.append({"note": "... truncated (>500 items)"})
            
            return ToolResult(success=True, data={"files": files, "count": len(files)})
            
        except Exception as e:
            return ToolResult(success=False, error=f"Error listing directory: {e}")
    
    def _walk_limited(self, root: Path, max_depth: int, current_depth: int = 0):
        """Walk directory with depth limit."""
        if current_depth > max_depth:
            return
        
        try:
            for item in sorted(root.iterdir()):
                yield item
                if item.is_dir() and not item.name.startswith("."):
                    yield from self._walk_limited(item, max_depth, current_depth + 1)
        except PermissionError:
            pass
    
    def _is_allowed(self, path: Path) -> bool:
        """Check if path is within allowed directories."""
        resolved = path.resolve()
        return any(
            resolved == allowed or allowed in resolved.parents
            for allowed in self.allowed_paths
        )


class BashTool(Tool):
    """Tool for running safe bash commands."""
    
    name = "bash"
    description = """Execute a bash command. Use this to run git commands, search code
with ripgrep, count lines, or other read-only operations.

ALLOWED commands: ls, find, cat, head, tail, grep, rg (ripgrep), wc, tree, file,
stat, git (log, show, ls-files, diff, blame), jq, yq

BLOCKED: rm, mv, cp, chmod, sudo, curl, wget, and any command with shell operators
like |, &&, ||, ;, or redirects >, >>"""
    
    ALLOWED_COMMANDS = {
        "ls", "find", "cat", "head", "tail", "grep", "rg", "ripgrep",
        "wc", "tree", "file", "stat", "git", "jq", "yq", "awk", "sed",
        "sort", "uniq", "cut", "tr", "basename", "dirname", "realpath",
    }
    
    BLOCKED_PATTERNS = [
        r"\brm\b", r"\bmv\b", r"\bcp\b", r"\bchmod\b", r"\bchown\b",
        r"\bsudo\b", r"\bsu\b", r"\bcurl\b", r"\bwget\b",
        r">", r">>", r"\|", r"&&", r"\|\|", r";", r"`", r"\$\(",
        r"\bkill\b", r"\bpkill\b", r"\bmkdir\b", r"\btouch\b",
    ]
    
    def __init__(self, working_dir: Path, allowed_paths: list[Path], timeout: int = 30):
        self.working_dir = working_dir.resolve()
        self.allowed_paths = [p.resolve() for p in allowed_paths]
        self.timeout = timeout
    
    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute",
                },
                "working_dir": {
                    "type": "string",
                    "description": "Optional: working directory for the command",
                },
            },
            "required": ["command"],
        }
    
    async def execute(
        self,
        command: str,
        working_dir: str | None = None,
    ) -> ToolResult:
        """Execute a bash command."""
        # Security checks
        allowed, reason = self._is_command_allowed(command)
        if not allowed:
            return ToolResult(
                success=False,
                error=f"Command not allowed: {reason}. Command: {command[:100]}",
            )
        
        # Resolve working directory
        cwd = Path(working_dir).resolve() if working_dir else self.working_dir
        if not self._is_path_allowed(cwd):
            return ToolResult(
                success=False,
                error=f"Working directory {cwd} is outside allowed paths",
            )
        
        try:
            # Run command
            result = await asyncio.to_thread(
                subprocess.run,
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env={**os.environ, "LANG": "C.UTF-8"},
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"
            
            # Truncate large output
            if len(output) > 50_000:
                output = output[:50_000] + "\n\n... [truncated]"
            
            return ToolResult(
                success=result.returncode == 0,
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.returncode,
                    "output": output,
                },
                error=f"Command exited with code {result.returncode}" if result.returncode != 0 else None,
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error=f"Command timed out after {self.timeout}s")
        except Exception as e:
            return ToolResult(success=False, error=f"Error executing command: {e}")
    
    def _is_command_allowed(self, command: str) -> tuple[bool, str]:
        """Check if command is in allowlist and not in blocklist.
        
        Returns (allowed, reason) tuple.
        """
        # First check if base command is in allowlist
        try:
            parts = shlex.split(command)
        except ValueError:
            return False, "invalid command syntax"
        
        if not parts:
            return False, "empty command"
        
        cmd = Path(parts[0]).name  # Handle full paths like /usr/bin/git
        if cmd not in self.ALLOWED_COMMANDS:
            return False, f"command '{cmd}' not in allowlist"
        
        # Check for blocked patterns only OUTSIDE quoted strings
        # Remove quoted strings before checking for shell operators
        unquoted = re.sub(r'"[^"]*"', '', command)  # Remove double-quoted strings
        unquoted = re.sub(r"'[^']*'", '', unquoted)  # Remove single-quoted strings
        
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, unquoted):
                return False, f"blocked shell operator detected"
        
        return True, "ok"
    
    def _is_path_allowed(self, path: Path) -> bool:
        """Check if path is within allowed directories."""
        resolved = path.resolve()
        return any(
            resolved == allowed or allowed in resolved.parents
            for allowed in self.allowed_paths
        )


class ResponseCache:
    """
    Cache for tool responses to reduce context size.
    
    Large tool responses are stored to disk, and the conversation history
    is updated with stubs that reference the cached content. The LLM can
    reload cached content using the cache_read tool if needed.
    """
    
    # Only cache responses larger than this (characters)
    CACHE_THRESHOLD = 500
    
    def __init__(self, cache_dir: Path):
        """Initialize the cache."""
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_index: dict[str, dict] = {}  # id -> metadata
    
    def should_cache(self, content: str) -> bool:
        """Check if content should be cached (is it large enough?)."""
        return len(content) > self.CACHE_THRESHOLD
    
    def store(self, tool_name: str, content: str, summary: str = "") -> str:
        """
        Store content in cache and return cache ID.
        
        Args:
            tool_name: Name of the tool that produced this response
            content: The full response content
            summary: Brief summary for the stub (optional)
            
        Returns:
            Cache ID that can be used to retrieve the content
        """
        import hashlib
        import time
        
        # Generate unique ID
        cache_id = hashlib.md5(f"{time.time()}{content[:100]}".encode()).hexdigest()[:12]
        
        # Store content
        cache_file = self.cache_dir / f"{cache_id}.txt"
        cache_file.write_text(content)
        
        # Store metadata
        self._cache_index[cache_id] = {
            "tool": tool_name,
            "summary": summary or f"{tool_name} response",
            "size": len(content),
            "file": str(cache_file),
        }
        
        logger.debug(f"Cached response {cache_id}: {len(content)} chars from {tool_name}")
        return cache_id
    
    def retrieve(self, cache_id: str) -> str | None:
        """Retrieve cached content by ID."""
        cache_file = self.cache_dir / f"{cache_id}.txt"
        if cache_file.exists():
            return cache_file.read_text()
        return None
    
    def get_stub(self, cache_id: str) -> dict:
        """Get the stub message to replace cached content."""
        meta = self._cache_index.get(cache_id, {})
        return {
            "cached": True,
            "cache_id": cache_id,
            "summary": meta.get("summary", "cached response"),
            "size": meta.get("size", 0),
            "note": f"Response cached to save context. Use cache_read tool with id='{cache_id}' to reload if needed.",
        }


class CacheReadTool(Tool):
    """Tool to reload cached tool responses."""
    
    name = "cache_read"
    description = """Reload a previously cached tool response.

When tool responses become part of conversation history, large responses are 
cached to save context space. If you need to re-examine cached data, use this 
tool with the cache_id provided in the stub.

Only use this if you specifically need data from a previous tool response that
was cached. Most of the time you won't need this - the information you extracted
from the original response is usually sufficient."""
    
    def __init__(self, cache: ResponseCache):
        self.cache = cache
    
    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "cache_id": {
                    "type": "string",
                    "description": "The cache ID from the cached response stub",
                },
            },
            "required": ["cache_id"],
        }
    
    async def execute(self, cache_id: str) -> ToolResult:
        """Retrieve cached content."""
        content = self.cache.retrieve(cache_id)
        if content is None:
            return ToolResult(
                success=False,
                error=f"Cache ID '{cache_id}' not found",
            )
        
        return ToolResult(
            success=True,
            data={"content": content, "cache_id": cache_id},
        )


class ToolRegistry:
    """Registry of all available tools."""
    
    def __init__(self):
        self._tools: dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
    
    def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> list[str]:
        """List all tool names."""
        return list(self._tools.keys())
    
    def get_schemas_for_claude(self) -> list[dict[str, Any]]:
        """Get tool definitions formatted for Claude API."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.get_schema(),
            }
            for tool in self._tools.values()
        ]
    
    async def execute(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(success=False, error=f"Unknown tool: {name}")
        
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            logger.exception(f"Tool {name} raised exception")
            return ToolResult(success=False, error=str(e))
