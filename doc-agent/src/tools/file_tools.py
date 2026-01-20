"""File operation tools for agents."""

import asyncio
import fnmatch
import logging
import os
from pathlib import Path
from typing import Any, Optional

import aiofiles

from .tool_registry import Tool, ToolResult

logger = logging.getLogger("doc-agent.tools.file")


class FileReadTool(Tool):
    """
    Tool for reading files from the workspace.
    
    Supports reading text files with optional line range selection.
    """
    
    name = "file_read"
    description = """Read the contents of a file from the workspace.
    
Supports:
- Reading entire files or specific line ranges
- Text files only (binary files will error)
- Files within the allowed workspace paths

Use this to:
- Read existing documentation
- Examine code files
- Check configuration files
- Review generated outputs"""
    
    def __init__(self, registry: "ToolRegistry"):
        self.registry = registry
    
    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file (relative to workspace root or absolute)",
                },
                "start_line": {
                    "type": "integer",
                    "description": "First line to read (1-indexed, optional)",
                },
                "end_line": {
                    "type": "integer",
                    "description": "Last line to read (1-indexed, inclusive, optional)",
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8",
                },
            },
            "required": ["path"],
        }
    
    async def execute(
        self,
        path: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        encoding: str = "utf-8",
        **kwargs,
    ) -> ToolResult:
        """Read a file's contents."""
        try:
            # Resolve path
            file_path = Path(path)
            if not file_path.is_absolute():
                file_path = self.registry.workspace_root / file_path
            file_path = file_path.resolve()
            
            # Security check
            if not self.registry.is_path_allowed(file_path):
                return ToolResult(
                    success=False,
                    error=f"Path not allowed: {path}",
                )
            
            if not file_path.exists():
                return ToolResult(
                    success=False,
                    error=f"File not found: {path}",
                )
            
            if not file_path.is_file():
                return ToolResult(
                    success=False,
                    error=f"Not a file: {path}",
                )
            
            # Read file
            async with aiofiles.open(file_path, mode='r', encoding=encoding) as f:
                content = await f.read()
            
            lines = content.splitlines(keepends=True)
            total_lines = len(lines)
            
            # Apply line range if specified
            if start_line is not None or end_line is not None:
                start_idx = (start_line - 1) if start_line else 0
                end_idx = end_line if end_line else total_lines
                
                # Bounds checking
                start_idx = max(0, min(start_idx, total_lines))
                end_idx = max(0, min(end_idx, total_lines))
                
                lines = lines[start_idx:end_idx]
                content = ''.join(lines)
            
            return ToolResult(
                success=True,
                data=content,
                metadata={
                    "path": str(file_path),
                    "total_lines": total_lines,
                    "lines_read": len(lines),
                    "size_bytes": len(content.encode(encoding)),
                },
            )
            
        except UnicodeDecodeError as e:
            return ToolResult(
                success=False,
                error=f"Cannot read file as text (binary?): {e}",
            )
        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            return ToolResult(
                success=False,
                error=str(e),
            )


class FileWriteTool(Tool):
    """
    Tool for writing files to the output directory.
    
    Restricted to the documentation output directory for safety.
    """
    
    name = "file_write"
    description = """Write content to a file in the documentation output directory.
    
Supports:
- Creating new files
- Overwriting existing files
- Creating parent directories automatically
- ONLY writes to the docs output directory (safety restriction)

Use this to:
- Create documentation files
- Generate markdown documents
- Write analysis reports
- Create index files"""
    
    def __init__(self, registry: "ToolRegistry"):
        self.registry = registry
    
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
                    "description": "Append to existing file instead of overwriting",
                    "default": False,
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8",
                },
            },
            "required": ["path", "content"],
        }
    
    async def execute(
        self,
        path: str,
        content: str,
        append: bool = False,
        encoding: str = "utf-8",
        **kwargs,
    ) -> ToolResult:
        """Write content to a file."""
        try:
            # Resolve path - MUST be within output directory
            file_path = Path(path)
            if file_path.is_absolute():
                # Check if it's within output dir
                if not str(file_path).startswith(str(self.registry.output_dir)):
                    return ToolResult(
                        success=False,
                        error=f"Can only write to output directory: {self.registry.output_dir}",
                    )
            else:
                file_path = self.registry.output_dir / file_path
            
            file_path = file_path.resolve()
            
            # Additional safety check
            if self.registry.output_dir not in file_path.parents and file_path != self.registry.output_dir:
                if not str(file_path).startswith(str(self.registry.output_dir)):
                    return ToolResult(
                        success=False,
                        error=f"Path escapes output directory: {path}",
                    )
            
            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            mode = 'a' if append else 'w'
            async with aiofiles.open(file_path, mode=mode, encoding=encoding) as f:
                await f.write(content)
            
            return ToolResult(
                success=True,
                data={"path": str(file_path)},
                metadata={
                    "path": str(file_path),
                    "size_bytes": len(content.encode(encoding)),
                    "mode": "append" if append else "write",
                },
            )
            
        except Exception as e:
            logger.error(f"Failed to write file {path}: {e}")
            return ToolResult(
                success=False,
                error=str(e),
            )


class FileListTool(Tool):
    """
    Tool for listing files and directories.
    
    Supports glob patterns and recursive listing.
    """
    
    name = "file_list"
    description = """List files and directories in a path.
    
Supports:
- Listing directory contents
- Glob patterns (e.g., "*.md", "**/*.py")
- Recursive directory traversal
- Files within allowed workspace paths

Use this to:
- Explore directory structure
- Find files by pattern
- Check what documentation exists
- Discover code files"""
    
    def __init__(self, registry: "ToolRegistry"):
        self.registry = registry
    
    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path (relative to workspace root or absolute)",
                    "default": ".",
                },
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to filter files (e.g., '*.md', '**/*.py')",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "List directories recursively",
                    "default": False,
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Include hidden files (starting with .)",
                    "default": False,
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum recursion depth (default: unlimited)",
                },
            },
            "required": [],
        }
    
    async def execute(
        self,
        path: str = ".",
        pattern: Optional[str] = None,
        recursive: bool = False,
        include_hidden: bool = False,
        max_depth: Optional[int] = None,
        **kwargs,
    ) -> ToolResult:
        """List files in a directory."""
        try:
            # Resolve path
            dir_path = Path(path)
            if not dir_path.is_absolute():
                dir_path = self.registry.workspace_root / dir_path
            dir_path = dir_path.resolve()
            
            # Security check
            if not self.registry.is_path_allowed(dir_path):
                return ToolResult(
                    success=False,
                    error=f"Path not allowed: {path}",
                )
            
            if not dir_path.exists():
                return ToolResult(
                    success=False,
                    error=f"Directory not found: {path}",
                )
            
            if not dir_path.is_dir():
                return ToolResult(
                    success=False,
                    error=f"Not a directory: {path}",
                )
            
            # Collect files
            files = []
            dirs = []
            
            def should_include(p: Path) -> bool:
                if not include_hidden and p.name.startswith('.'):
                    return False
                if pattern and not fnmatch.fnmatch(p.name, pattern):
                    return False
                return True
            
            def scan_dir(current: Path, depth: int = 0):
                if max_depth is not None and depth > max_depth:
                    return
                
                try:
                    for item in current.iterdir():
                        # Security check for each item
                        if not self.registry.is_path_allowed(item):
                            continue
                        
                        if item.is_file():
                            if should_include(item) or (pattern and fnmatch.fnmatch(str(item.relative_to(dir_path)), pattern)):
                                rel_path = item.relative_to(dir_path)
                                files.append({
                                    "path": str(rel_path),
                                    "size": item.stat().st_size,
                                    "type": "file",
                                })
                        elif item.is_dir():
                            if include_hidden or not item.name.startswith('.'):
                                rel_path = item.relative_to(dir_path)
                                dirs.append({
                                    "path": str(rel_path),
                                    "type": "directory",
                                })
                                if recursive:
                                    scan_dir(item, depth + 1)
                except PermissionError:
                    pass  # Skip directories we can't access
            
            # Run scan in executor to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: scan_dir(dir_path)
            )
            
            # Sort results
            files.sort(key=lambda x: x["path"])
            dirs.sort(key=lambda x: x["path"])
            
            return ToolResult(
                success=True,
                data={
                    "directories": dirs,
                    "files": files,
                },
                metadata={
                    "path": str(dir_path),
                    "total_files": len(files),
                    "total_dirs": len(dirs),
                },
            )
            
        except Exception as e:
            logger.error(f"Failed to list directory {path}: {e}")
            return ToolResult(
                success=False,
                error=str(e),
            )
