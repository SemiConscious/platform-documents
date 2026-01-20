#!/usr/bin/env python3
"""
Natterbox Platform Documentation Agent

This script automates platform documentation generation using Claude on AWS Bedrock
with MCP (Model Context Protocol) tools for accessing Natterbox services and
shell execution capabilities.

Requirements:
- Python 3.11+
- AWS credentials configured (for Bedrock access)
- Docker (for isolated shell execution)

Usage:
    python agent.py --task "Create runbooks for emergency response"
    python agent.py --interactive
"""

import argparse
import asyncio
import copy
import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Tuple

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

import boto3
import httpx


# Configure logging with immediate flush
class FlushingStreamHandler(logging.StreamHandler):
    """Handler that flushes after every emit for real-time output."""

    def emit(self, record):
        super().emit(record)
        self.flush()


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[FlushingStreamHandler()])
logger = logging.getLogger("documentation-agent")

# Suppress noisy httpx and httpcore logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class Config:
    """Agent configuration."""

    # AWS Bedrock settings
    aws_region: str = field(default_factory=lambda: os.environ.get("AWS_REGION", "us-east-1"))
    bedrock_model_id: str = field(default_factory=lambda: os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-sonnet-4-20250514-v1:0"))
    max_tokens: int = 32768  # Increased for generating large documentation

    # MCP Server settings
    natterbox_mcp_url: str = field(default_factory=lambda: os.environ.get("NATTERBOX_MCP_URL", "https://avatar.natterbox-dev03.net/mcp/sse"))

    # Working directories
    work_dir: Path = field(default_factory=lambda: Path(os.environ.get("WORK_DIR", "/workspace")))
    output_dir: Path = field(default_factory=lambda: Path(os.environ.get("OUTPUT_DIR", "/workspace/output")))

    # Tool settings
    shell_timeout: int = 300  # seconds

    # Conversation settings
    max_turns: int = 150  # Increased for deep research

    def __post_init__(self):
        self.work_dir = Path(self.work_dir)
        self.output_dir = Path(self.output_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


# =============================================================================
# File Store - Caches large results to prevent context overflow
# =============================================================================


class FileStore:
    """
    A file-based cache for storing ALL tool results.

    Strategy:
    - Store ALL tool results with content hashing for deduplication
    - For current requests: return full content if < 50K, else reference
    - For historical messages: compact references replace full content
    - This optimizes context by not re-sending data Claude has already processed
    """

    STORE_DIR = ".agent-store"
    INLINE_THRESHOLD = 50000  # Return inline if < 50K chars

    def __init__(self, work_dir: Path):
        self.work_dir = Path(work_dir).resolve()
        self.store_path = self.work_dir / self.STORE_DIR
        self.store_path.mkdir(parents=True, exist_ok=True)
        self._index: dict[str, dict] = {}  # file_id -> metadata
        self._content_hash_to_id: dict[str, str] = {}  # hash -> file_id for dedup
        self._load_index()

    def _index_path(self) -> Path:
        return self.store_path / "index.json"

    def _load_index(self):
        """Load the store index from disk."""
        try:
            if self._index_path().exists():
                self._index = json.loads(self._index_path().read_text())
                # Rebuild hash lookup
                for file_id, meta in self._index.items():
                    if "content_hash" in meta:
                        self._content_hash_to_id[meta["content_hash"]] = file_id
        except Exception as e:
            logger.warning(f"Failed to load file store index: {e}")
            self._index = {}

    def _save_index(self):
        """Save the store index to disk."""
        try:
            self._index_path().write_text(json.dumps(self._index, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save file store index: {e}")

    def _hash_content(self, content: str) -> str:
        """Generate a short hash of content for deduplication."""
        import hashlib

        return hashlib.sha256(content.encode()).hexdigest()[:12]

    def store(self, content: str, source: str, content_type: str = "text") -> dict:
        """
        Store content and return a reference.
        Uses content hashing for deduplication - same content returns same ID.

        Args:
            content: The content to store
            source: Description of where this came from (tool name, etc.)
            content_type: Type of content (text, json, etc.)

        Returns:
            Dict with file_id, size, lines, and info message
        """
        import uuid

        content_hash = self._hash_content(content)
        size = len(content)
        lines = content.count("\n") + 1

        # Check if we already have this content (dedup)
        if content_hash in self._content_hash_to_id:
            existing_id = self._content_hash_to_id[content_hash]
            if existing_id in self._index:
                # Already stored - return existing reference
                return {
                    "file_id": existing_id,
                    "size_bytes": size,
                    "lines": lines,
                    "stored_in_file_store": True,
                    "deduplicated": True,
                    "message": f"Content ({size:,} bytes, {lines} lines) available via read_from_store(file_id='{existing_id}')",
                }

        # New content - store it
        file_id = str(uuid.uuid4())[:8]
        file_path = self.store_path / f"{file_id}.txt"

        # Write content
        file_path.write_text(content)

        # Update index
        self._index[file_id] = {
            "source": source,
            "content_type": content_type,
            "content_hash": content_hash,
            "size": size,
            "lines": lines,
            "created": datetime.now().isoformat(),
            "path": str(file_path.relative_to(self.work_dir)),
        }
        self._content_hash_to_id[content_hash] = file_id
        self._save_index()

        # Silent storage - only log when reading from store

        return {
            "file_id": file_id,
            "size_bytes": size,
            "lines": lines,
            "stored_in_file_store": True,
            "message": f"Content ({size:,} bytes, {lines} lines) available via read_from_store(file_id='{file_id}')",
        }

    def read(self, file_id: str, offset: int = 0, limit: Optional[int] = None) -> dict:
        """
        Read content from the store using CHARACTER-based offsets.

        Args:
            file_id: The file ID returned from store()
            offset: Character position to start from (0-based)
            limit: Maximum number of characters to return (default: 10000 ≈ 2500 tokens)

        Returns:
            Dict with content, metadata, and whether there's more
        """
        DEFAULT_LIMIT = 50000  # ~12500 tokens worth

        if file_id not in self._index:
            return {"error": f"File ID '{file_id}' not found in store"}

        metadata = self._index[file_id]
        file_path = self.work_dir / metadata["path"]
        content_type = metadata.get("content_type", "text")

        if not file_path.exists():
            return {"error": f"File for ID '{file_id}' no longer exists"}

        try:
            content = file_path.read_text()
            total_chars = len(content)

            # Apply offset and limit (character-based)
            if offset >= total_chars:
                return {
                    "text": "",
                    "file_id": file_id,
                    "offset_chars": offset,
                    "chars_returned": 0,
                    "total_chars": total_chars,
                    "has_more": False,
                    "status": "COMPLETE - offset past end of file",
                }

            actual_limit = limit if limit is not None else DEFAULT_LIMIT
            end = min(offset + actual_limit, total_chars)
            selected_content = content[offset:end]
            remaining_chars = total_chars - end

            result = {
                "file_id": file_id,
                "content_type": content_type,
                "offset_chars": offset,
                "chars_returned": len(selected_content),
                "total_chars": total_chars,
                "source": metadata.get("source", "unknown"),
                "text": selected_content,  # Changed from "content" to "text" for clarity
            }

            if remaining_chars > 0:
                # Make it VERY clear there's more data
                pct_shown = int((end / total_chars) * 100)
                result["⚠️_WARNING"] = f"INCOMPLETE: Showing {pct_shown}% ({len(selected_content):,} of {total_chars:,} chars). {remaining_chars:,} chars remaining!"
                result["has_more"] = True
                result["remaining_chars"] = remaining_chars
                result["next_offset"] = end
                result["to_continue"] = f"read_from_store(file_id='{file_id}', offset={end}, limit={actual_limit})"

                # Warn about partial JSON
                if content_type == "json":
                    result["⚠️_JSON_NOTE"] = "This is partial JSON data. Read the complete file to parse it properly."
            else:
                result["has_more"] = False
                result["status"] = "COMPLETE - all data returned"

            return result

        except Exception as e:
            return {"error": f"Failed to read file: {e}"}

    def list_files(self) -> dict:
        """List all files in the store."""
        return {
            "files": [
                {
                    "file_id": fid,
                    "source": meta["source"],
                    "size": meta["size"],
                    "lines": meta["lines"],
                    "created": meta["created"],
                }
                for fid, meta in self._index.items()
            ]
        }

    def clear(self):
        """Clear old files from the store."""
        for file_id in list(self._index.keys()):
            try:
                file_path = self.work_dir / self._index[file_id]["path"]
                if file_path.exists():
                    file_path.unlink()
                del self._index[file_id]
            except Exception as e:
                logger.warning(f"Failed to delete {file_id}: {e}")
        self._save_index()
        logger.info("🗑️  Cleared file store")

    def get_tool_definitions(self) -> list[dict]:
        """Return tool definitions for Claude."""
        return [
            {
                "name": "read_from_store",
                "description": (
                    "Read data from the file store. Use this to:\n"
                    "1. Continue reading a truncated result (see _truncated.file_id in tool results)\n"
                    "2. Retrieve a compressed historical result (see compressed.file_id)\n"
                    "Specify offset and limit for chunked reading (CHARACTER-based, not lines).\n"
                    "ALWAYS check 'has_more' in the response - if true, use next_offset to continue."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_id": {"type": "string", "description": "The file ID from _truncated.file_id or compressed.file_id"},
                        "offset": {"type": "integer", "description": "Character position to start from (0-based). Use next_offset from previous response. Default: 0"},
                        "limit": {"type": "integer", "description": "Maximum characters to return. Default: 50000 chars (~12500 tokens)"},
                    },
                    "required": ["file_id"],
                },
            },
            {
                "name": "list_store_files",
                "description": "List all files currently in the file store with their IDs and metadata.",
                "input_schema": {"type": "object", "properties": {}},
            },
        ]


# =============================================================================
# Shell Tool
# =============================================================================


class ShellTool:
    """
    Provides shell command execution capabilities.
    All operations are sandboxed to the work_dir - no escaping allowed.
    """

    # Dangerous bash patterns to block
    BLOCKED_PATTERNS = [
        r"\bsudo\b",
        r"\brm\s+-rf\s+/",
        r"\bchmod\s+.*/",
        r"\bchown\s+.*/",
        r">\s*/(?!dev/null|workspace)",  # Redirect to absolute path (allow /dev/null)
        r"\bmkdir\s+-p\s+/",
        r"\bln\s+-s",  # Symlinks could escape sandbox
    ]

    def __init__(self, work_dir: Path, timeout: int = 300):
        self.work_dir = Path(work_dir).resolve()  # Get absolute path
        self.timeout = timeout
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self._blocked_re = [re.compile(p) for p in self.BLOCKED_PATTERNS]

    def _resolve_safe_path(self, path: str) -> tuple[Path, Optional[str]]:
        """
        Resolve a path and ensure it's within work_dir.
        Returns (resolved_path, error_message).
        If error_message is not None, the path is not safe.
        """
        try:
            # Handle relative and absolute paths
            if path.startswith("/"):
                resolved = Path(path).resolve()
            else:
                resolved = (self.work_dir / path).resolve()

            # Check if path is within work_dir
            try:
                resolved.relative_to(self.work_dir)
                return resolved, None
            except ValueError:
                return resolved, f"Path '{path}' resolves to '{resolved}' which is outside the workspace '{self.work_dir}'"

        except Exception as e:
            return Path(path), f"Invalid path '{path}': {e}"

    def _check_command_safety(self, command: str) -> Optional[str]:
        """
        Check if a bash command is safe to execute.
        Returns error message if unsafe, None if safe.
        """
        for pattern in self._blocked_re:
            if pattern.search(command):
                return f"Blocked potentially dangerous command pattern: {pattern.pattern}"
        return None

    def execute(self, command: str, description: str = "") -> dict[str, Any]:
        """
        Execute a shell command and return the result.
        Command runs with cwd set to work_dir and is checked for dangerous patterns.

        Args:
            command: The bash command to execute
            description: Human-readable description of why this command is being run

        Returns:
            Dict with 'returncode', 'stdout', 'stderr', and 'success' keys
        """
        logger.info(f"Shell: {description or command[:100]}")

        # Check command safety
        safety_error = self._check_command_safety(command)
        if safety_error:
            logger.warning(f"Blocked command: {safety_error}")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": safety_error,
            }

        try:
            # Create a restricted environment
            safe_env = {
                **os.environ,
                "HOME": str(self.work_dir),
                "PWD": str(self.work_dir),
            }

            result = subprocess.run(
                command,
                shell=True,
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=safe_env,
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {self.timeout} seconds",
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
            }

    def read_file(self, path: str) -> dict[str, Any]:
        """Read a file from the workspace. Path must be within work_dir."""
        resolved, error = self._resolve_safe_path(path)
        if error:
            logger.warning(f"Blocked read_file: {error}")
            return {"success": False, "error": error}

        try:
            content = resolved.read_text()
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def write_file(self, path: str, content: str) -> dict[str, Any]:
        """Write content to a file in the workspace. Path must be within work_dir."""
        resolved, error = self._resolve_safe_path(path)
        if error:
            logger.warning(f"Blocked write_file: {error}")
            return {"success": False, "error": error}

        try:
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(content)
            logger.info(f"Wrote file: {resolved}")
            return {"success": True, "path": str(resolved)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_directory(self, path: str = ".") -> dict[str, Any]:
        """List contents of a directory. Path must be within work_dir."""
        resolved, error = self._resolve_safe_path(path)
        if error:
            logger.warning(f"Blocked list_directory: {error}")
            return {"success": False, "error": error}

        try:
            items = []
            for item in resolved.iterdir():
                items.append(
                    {
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None,
                    }
                )
            return {"success": True, "items": items}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_tool_definitions(self) -> list[dict]:
        """Return tool definitions for Claude."""
        return [
            {
                "name": "bash",
                "description": f"Execute a bash command in the workspace ({self.work_dir}). Commands run with cwd set to workspace. Some dangerous patterns are blocked. Use for git operations, file manipulation, etc.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "The bash command to execute"},
                        "description": {"type": "string", "description": "Brief description of why this command is being run"},
                    },
                    "required": ["command"],
                },
            },
            {
                "name": "read_file",
                "description": "Read the contents of a file from the workspace.",
                "input_schema": {
                    "type": "object",
                    "properties": {"path": {"type": "string", "description": "Path to the file (relative to workspace or absolute)"}},
                    "required": ["path"],
                },
            },
            {
                "name": "write_file",
                "description": "Write content to a file in the workspace. Creates parent directories if needed.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the file (relative to workspace or absolute)"},
                        "content": {"type": "string", "description": "Content to write to the file"},
                    },
                    "required": ["path", "content"],
                },
            },
            {
                "name": "list_directory",
                "description": "List the contents of a directory in the workspace.",
                "input_schema": {
                    "type": "object",
                    "properties": {"path": {"type": "string", "description": "Path to the directory (relative to workspace or absolute)", "default": "."}},
                },
            },
        ]


# =============================================================================
# MCP Client for Natterbox Tools (with OAuth + SSE)
# =============================================================================


class MCPClient:
    """
    Client for connecting to the Natterbox MCP server via SSE with OAuth authentication.
    Provides access to Confluence, GitHub, Salesforce, and other tools.
    """

    # OAuth configuration
    OAUTH_CONFIG = {
        "authorization_url": "https://avatar.natterbox-dev03.net/mcp/authorize",
        "token_url": "https://avatar.natterbox-dev03.net/mcp/token",
        "client_id": "documentation-agent",
        "redirect_uri": "http://localhost:8765/callback",
        "scopes": ["openid"],
    }

    # Token refresh threshold (refresh if expiring within this many seconds)
    TOKEN_REFRESH_THRESHOLD = 300  # 5 minutes

    def __init__(self, server_url: str, token_file: Optional[Path] = None):
        self.server_url = server_url
        self.tools: dict[str, dict] = {}
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expiry: Optional[float] = None  # Unix timestamp
        self._token_file = token_file or Path.home() / ".natterbox-mcp-tokens.json"
        self._message_endpoint = server_url  # SSE endpoint accepts POST for messages

    def _load_tokens(self) -> bool:
        """Load tokens from file if they exist."""
        try:
            if self._token_file.exists():
                data = json.loads(self._token_file.read_text())
                self._access_token = data.get("access_token")
                self._refresh_token = data.get("refresh_token")
                self._token_expiry = data.get("expires_at")

                # Check if token is expired or expiring soon
                if self._token_expiry:
                    import time

                    time_until_expiry = self._token_expiry - time.time()
                    if time_until_expiry < self.TOKEN_REFRESH_THRESHOLD:
                        logger.info(f"Token expiring in {time_until_expiry:.0f}s, will refresh")
                        return False  # Will trigger refresh

                logger.info("Loaded existing MCP tokens from file")
                return bool(self._access_token)
        except Exception as e:
            logger.warning(f"Failed to load tokens: {e}")
        return False

    def _save_tokens(self, expires_in: Optional[int] = None):
        """Save tokens to file with expiry tracking."""
        try:
            import time

            token_data = {
                "access_token": self._access_token,
                "refresh_token": self._refresh_token,
            }

            # Calculate expiry time
            if expires_in:
                self._token_expiry = time.time() + expires_in
                token_data["expires_at"] = self._token_expiry
                logger.info(f"Token expires in {expires_in}s")
            elif self._token_expiry:
                token_data["expires_at"] = self._token_expiry

            self._token_file.write_text(json.dumps(token_data))
            self._token_file.chmod(0o600)  # Secure permissions
            logger.info("Saved MCP tokens to file")
        except Exception as e:
            logger.warning(f"Failed to save tokens: {e}")

    def _should_refresh_token(self) -> bool:
        """Check if token should be proactively refreshed."""
        if not self._token_expiry:
            return False
        import time

        time_until_expiry = self._token_expiry - time.time()
        return time_until_expiry < self.TOKEN_REFRESH_THRESHOLD

    async def _do_oauth_flow(self) -> bool:
        """Perform OAuth authorization code flow with local callback server."""
        import webbrowser
        from http.server import HTTPServer, BaseHTTPRequestHandler
        from urllib.parse import urlparse, parse_qs
        import threading

        auth_code = None
        server_error = None

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                nonlocal auth_code, server_error
                query = parse_qs(urlparse(self.path).query)

                if "code" in query:
                    auth_code = query["code"][0]
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<html><body><h1>Authorization successful!</h1><p>You can close this window.</p></body></html>")
                elif "error" in query:
                    server_error = query.get("error_description", query["error"])[0]
                    self.send_response(400)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(f"<html><body><h1>Error: {server_error}</h1></body></html>".encode())
                else:
                    self.send_response(400)
                    self.end_headers()

            def log_message(self, format, *args):
                pass  # Suppress logging

        # Start local server
        server = HTTPServer(("localhost", 8765), CallbackHandler)
        server_thread = threading.Thread(target=server.handle_request)
        server_thread.start()

        # Build authorization URL
        auth_url = (
            f"{self.OAUTH_CONFIG['authorization_url']}?"
            f"client_id={self.OAUTH_CONFIG['client_id']}&"
            f"redirect_uri={self.OAUTH_CONFIG['redirect_uri']}&"
            f"response_type=code&"
            f"scope={' '.join(self.OAUTH_CONFIG['scopes'])}"
        )

        logger.info("Opening browser for OAuth authorization...")
        print(f"\n🔐 Please authorize in your browser: {auth_url}\n")
        webbrowser.open(auth_url)

        # Wait for callback
        server_thread.join(timeout=120)
        server.server_close()

        if server_error:
            logger.error(f"OAuth error: {server_error}")
            return False

        if not auth_code:
            logger.error("No authorization code received")
            return False

        # Exchange code for tokens
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.OAUTH_CONFIG["token_url"],
                    data={
                        "grant_type": "authorization_code",
                        "code": auth_code,
                        "client_id": self.OAUTH_CONFIG["client_id"],
                        "redirect_uri": self.OAUTH_CONFIG["redirect_uri"],
                    },
                )

                if response.status_code == 200:
                    tokens = response.json()
                    self._access_token = tokens.get("access_token")
                    self._refresh_token = tokens.get("refresh_token")
                    expires_in = tokens.get("expires_in", 3600)  # Default 1 hour
                    self._save_tokens(expires_in=expires_in)
                    logger.info("OAuth flow completed successfully")
                    return True
                else:
                    logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Token exchange error: {e}")
            return False

    async def _refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token."""
        if not self._refresh_token:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.OAUTH_CONFIG["token_url"],
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": self._refresh_token,
                        "client_id": self.OAUTH_CONFIG["client_id"],
                    },
                )

                if response.status_code == 200:
                    tokens = response.json()
                    self._access_token = tokens.get("access_token")
                    if tokens.get("refresh_token"):
                        self._refresh_token = tokens["refresh_token"]
                    expires_in = tokens.get("expires_in", 3600)
                    self._save_tokens(expires_in=expires_in)
                    logger.info("Access token refreshed successfully")
                    return True
                else:
                    logger.warning(f"Token refresh failed: {response.status_code}")
        except Exception as e:
            logger.warning(f"Token refresh failed: {e}")

        return False

    async def _ensure_valid_token(self) -> bool:
        """Ensure we have a valid token, refreshing proactively if needed."""
        if self._should_refresh_token():
            logger.info("Proactively refreshing token before expiry")
            if not await self._refresh_access_token():
                logger.warning("Proactive refresh failed, will retry on 401")
        return bool(self._access_token)

    async def connect(self) -> bool:
        """Connect to the MCP server and discover available tools."""
        logger.info(f"Connecting to MCP server: {self.server_url}")

        # Try to load existing tokens
        if not self._load_tokens():
            # No tokens - need to authenticate
            logger.info("No existing tokens - initiating OAuth flow")
            if not await self._do_oauth_flow():
                logger.error("OAuth authentication failed")
                return False

        # Try to connect with current token
        try:
            connected = await self._try_connect()
            if not connected and self._refresh_token:
                # Token might be expired, try refresh
                if await self._refresh_access_token():
                    connected = await self._try_connect()

            if not connected:
                # Tokens invalid - re-authenticate
                logger.info("Tokens invalid - re-authenticating")
                if await self._do_oauth_flow():
                    connected = await self._try_connect()

            return connected

        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return False

    async def _try_connect(self) -> bool:
        """Attempt to connect and list tools."""
        headers = {"Authorization": f"Bearer {self._access_token}"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Initialize connection
                response = await client.post(
                    self._message_endpoint,
                    headers=headers,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "documentation-agent", "version": "1.0.0"}},
                    },
                )

                if response.status_code == 401:
                    logger.warning("MCP authentication failed (401)")
                    return False

                if response.status_code != 200:
                    logger.error(f"Failed to initialize MCP connection: {response.status_code}")
                    return False

                init_result = response.json()
                logger.info(f"MCP server initialized: {init_result.get('result', {}).get('serverInfo', {})}")

                # List available tools
                response = await client.post(self._message_endpoint, headers=headers, json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})

                if response.status_code == 200:
                    tools_result = response.json()
                    for tool in tools_result.get("result", {}).get("tools", []):
                        self.tools[tool["name"]] = tool
                    logger.info(f"Discovered {len(self.tools)} MCP tools")

                return True

        except Exception as e:
            logger.error(f"Connection attempt failed: {e}")
            return False

    async def call_tool(self, name: str, arguments: dict) -> dict[str, Any]:
        """Call an MCP tool with the given arguments."""
        # Proactively refresh token if needed
        await self._ensure_valid_token()

        headers = {"Authorization": f"Bearer {self._access_token}"}

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self._message_endpoint, headers=headers, json={"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": name, "arguments": arguments}}
                )

                if response.status_code == 401:
                    # Try refresh and retry
                    if await self._refresh_access_token():
                        headers = {"Authorization": f"Bearer {self._access_token}"}
                        response = await client.post(
                            self._message_endpoint, headers=headers, json={"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": name, "arguments": arguments}}
                        )

                if response.status_code == 200:
                    result = response.json()
                    return {"success": True, "result": result.get("result", {})}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_tool_definitions(self) -> list[dict]:
        """Return tool definitions for Claude in Bedrock format."""
        definitions = []
        for name, tool in self.tools.items():
            definitions.append(
                {"name": f"mcp_{name}", "description": tool.get("description", f"MCP tool: {name}"), "input_schema": tool.get("inputSchema", {"type": "object", "properties": {}})}
            )
        return definitions


# =============================================================================
# Bedrock Client
# =============================================================================


class BedrockClient:
    """Client for AWS Bedrock Claude API with tool use support."""

    # Context limits (approximate - characters, not tokens)
    # Bedrock Opus has ~128K effective token limit, ~4 chars per token = ~512K chars
    # Being conservative to avoid "Input is too long" errors
    CONTEXT_WARNING_CHARS = 300000  # Warn at ~75K tokens
    CONTEXT_LIMIT_CHARS = 480000  # Hard limit at ~120K tokens (conservative)
    SAFETY_BUFFER = 80000  # Reserve for response + safety margin

    def __init__(self, config: Config):
        self.config = config
        # Add read timeout to prevent hanging
        from botocore.config import Config as BotoConfig

        boto_config = BotoConfig(
            read_timeout=300,  # 5 minute timeout for long generations
            connect_timeout=30,
            retries={"max_attempts": 2},
        )
        self.client = boto3.client("bedrock-runtime", region_name=config.aws_region, config=boto_config)

    def estimate_context_size(self, messages: list[dict], system: str, tools: list[dict]) -> int:
        """Estimate the context size in characters."""
        size = len(system)
        size += len(json.dumps(tools))
        size += len(json.dumps(messages))
        return size

    def available_for_result(self, messages: list[dict], system: str, tools: list[dict]) -> int:
        """Calculate how many chars are available for a new tool result."""
        current = self.estimate_context_size(messages, system, tools)
        return max(0, self.CONTEXT_LIMIT_CHARS - current - self.SAFETY_BUFFER)

    def create_message(
        self,
        messages: list[dict],
        system: str,
        tools: list[dict],
    ) -> dict:
        """
        Send a message to Claude via Bedrock and get a response.

        Args:
            messages: Conversation history
            system: System prompt
            tools: Available tools

        Returns:
            Claude's response

        Raises:
            Exception: If context is too large or API call fails
        """
        # Check context size
        context_size = self.estimate_context_size(messages, system, tools)
        estimated_tokens = context_size // 4

        if context_size > self.CONTEXT_LIMIT_CHARS:
            raise Exception(f"Context too large: ~{estimated_tokens:,} tokens (~{context_size:,} chars). Limit is ~{self.CONTEXT_LIMIT_CHARS // 4:,} tokens.")

        # Calculate percentage and status indicator
        pct = (context_size / self.CONTEXT_LIMIT_CHARS) * 100
        if pct >= 75:
            indicator = "🔴"  # Red - danger zone
            logger.warning(f"{indicator} Context: ~{estimated_tokens:,} tokens ({pct:.0f}% of limit)")
        elif pct >= 50:
            indicator = "🟡"  # Amber - caution
            logger.info(f"{indicator} Context: ~{estimated_tokens:,} tokens ({pct:.0f}% of limit)")
        else:
            indicator = "🟢"  # Green - healthy
            logger.info(f"{indicator} Context: ~{estimated_tokens:,} tokens ({pct:.0f}% of limit)")

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.config.max_tokens,
            "system": system,
            "messages": messages,
            "tools": tools,
        }

        try:
            response = self.client.invoke_model(
                modelId=self.config.bedrock_model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json",
            )

            response_body = json.loads(response["body"].read())
            return response_body

        except self.client.exceptions.ModelTimeoutException as e:
            raise Exception(f"Bedrock timeout after 5 minutes: {e}")
        except Exception as e:
            # Log the error with context info
            logger.error(f"Bedrock API error (context: ~{estimated_tokens:,} tokens): {e}")
            raise


# =============================================================================
# Sub-Agent for Parallel Task Execution
# =============================================================================


@dataclass
class PlanTask:
    """A single task from the planning phase."""

    id: str
    title: str
    description: str
    target_files: list[str]
    dependencies: list[str] = field(default_factory=list)
    priority: int = 1


@dataclass
class TaskResult:
    """Result from a sub-agent task execution."""

    task_id: str
    success: bool
    files_created: list[str]
    summary: str
    error: Optional[str] = None
    turns_used: int = 0


class SubAgent:
    """
    Lightweight agent for executing a single task in parallel.
    Shares tools and file store with parent but has own message history.
    """

    MAX_TURNS = 50  # Sub-agents get fewer turns for focused tasks

    def __init__(
        self,
        task: PlanTask,
        agent_id: str,
        shell: ShellTool,
        mcp: MCPClient,
        bedrock: BedrockClient,
        file_store: FileStore,
        tools: list[dict],
        work_dir: Path,
    ):
        self.task = task
        self.agent_id = agent_id  # Unique identifier for logging (e.g., "sub-1")
        self.shell = shell
        self.mcp = mcp
        self.bedrock = bedrock
        self.file_store = file_store
        self.tools = tools
        self.work_dir = work_dir
        self.messages: list[dict] = []
        self._files_written: set[str] = set()
        self._consecutive_errors = 0

    def _get_system_prompt(self) -> str:
        """Get comprehensive system prompt for sub-agent."""
        return f"""You are a documentation specialist creating COMPREHENSIVE technical documentation.

## Your Task
{self.task.title}

## Task Description
{self.task.description}

## Suggested Files
{", ".join(self.task.target_files)}

## CRITICAL: Documentation Depth Requirements

You MUST document with FULL TECHNICAL DETAIL:

### For APIs/Services:
- **Every endpoint**: Method, path, description, authentication required
- **Request format**: All parameters (path, query, body), types, required/optional, defaults
- **Response format**: Full schema with all fields, types, and example values
- **Error responses**: All error codes, when they occur, error body format
- **Example requests/responses**: Complete curl examples or code snippets

### For Data Models:
- **Database schemas**: All tables, columns, types, constraints, indexes
- **Relationships**: Foreign keys, joins, cascade behavior
- **Data flow**: How data moves through the system

### For Service Integration:
- **Dependencies**: What other services are called
- **When**: Under what conditions calls are made
- **Data exchanged**: Request/response formats for inter-service calls
- **Failure handling**: What happens if dependency fails

### For Configuration:
- **All options**: Every config value, environment variable
- **Defaults**: What happens if not set
- **Examples**: Sample configuration files

## You May Create Additional Files
If the topic is large, subdivide into multiple files:
- Main overview file
- Separate API reference
- Configuration guide
- Troubleshooting guide

## Research Process
1. Search Confluence for existing documentation
2. Find the GitHub repository
3. READ THE ACTUAL SOURCE CODE - controllers, routes, models, services
4. Document what the CODE does, not just what docs claim

## Important
- Do NOT update STATUS.md or BACKLOG.md - that's handled by the coordinator
- When done, provide a clear summary of what you created

Current date: {datetime.now().strftime("%Y-%m-%d")}
"""

    def _format_mcp_call_details(self, tool_name: str, tool_input: dict) -> str:
        """Format MCP tool call details for human-readable logging."""
        details = []

        if "confluence" in tool_name:
            op = tool_input.get("operation", "unknown")
            if op == "search_pages":
                details.append(f"search: '{tool_input.get('query', '')}'")
            elif op == "get_page":
                details.append(f"page: {tool_input.get('pageId', 'unknown')}")
            else:
                details.append(f"op: {op}")

        elif "github" in tool_name:
            op = tool_input.get("operation", "unknown")
            owner = tool_input.get("owner", "")
            repo = tool_input.get("repo", "")
            if owner and repo:
                details.append(f"{owner}/{repo}")
            if op == "list_contents":
                details.append(f"list: {tool_input.get('path', '/')}")
            elif op == "get_file_content":
                details.append(f"read: {tool_input.get('path', '')}")
            elif op == "list_repos":
                details.append("listing repos")
            elif op == "get_tree":
                details.append("tree")
            else:
                details.append(f"op: {op}")

        elif "salesforce" in tool_name:
            obj = tool_input.get("object", "")
            op = tool_input.get("operation", "")
            query = tool_input.get("query", tool_input.get("soql", ""))
            if obj:
                details.append(f"object: {obj}")
            if query:
                details.append(f"query: {query[:60]}...")
            elif op:
                details.append(f"op: {op}")

        elif "slack" in tool_name:
            op = tool_input.get("operation", "")
            channel = tool_input.get("channel", "")
            if op:
                details.append(f"op: {op}")
            if channel:
                details.append(f"channel: {channel}")

        elif "docs360" in tool_name or "document360" in tool_name:
            query = tool_input.get("query", "")
            if query:
                details.append(f"search: '{query}'")
            else:
                op = tool_input.get("operation", "")
                if op:
                    details.append(f"op: {op}")

        else:
            # Generic: show first few key params
            for key in ["operation", "query", "path", "file", "name"]:
                if key in tool_input:
                    val = str(tool_input[key])[:50]
                    details.append(f"{key}: {val}")
                    break

        return ", ".join(details) if details else "..."

    async def _handle_tool_use(self, tool_use: dict) -> dict:
        """Execute a tool - same logic as main agent."""
        tool_name = tool_use["name"]
        tool_input = tool_use.get("input", {})

        if tool_name == "bash":
            result = self.shell.execute(tool_input.get("command", ""), tool_input.get("description", ""))
        elif tool_name == "read_file":
            result = self.shell.read_file(tool_input.get("path", ""))
        elif tool_name == "write_file":
            path = tool_input.get("path", "")
            result = self.shell.write_file(path, tool_input.get("content", ""))
            if result.get("success"):
                self._files_written.add(path)
        elif tool_name == "list_directory":
            result = self.shell.list_directory(tool_input.get("path", "."))
        elif tool_name == "read_from_store":
            logger.info(f"[{self.agent_id}] 📖 read_from_store: file_id={tool_input.get('file_id', '')}, offset={tool_input.get('offset', 0)}")
            result = self.file_store.read(tool_input.get("file_id", ""), tool_input.get("offset", 0), tool_input.get("limit"))
        elif tool_name == "list_store_files":
            result = self.file_store.list_files()
        elif tool_name.startswith("mcp_"):
            mcp_tool_name = tool_name[4:]
            details = self._format_mcp_call_details(mcp_tool_name, tool_input)
            logger.info(f"[{self.agent_id}] 🌐 mcp_{mcp_tool_name}: {details}")
            result = await self.mcp.call_tool(mcp_tool_name, tool_input)
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        return result

    def _find_largest_string_field(self, obj: Any, path: str = "") -> Tuple[Optional[str], str]:
        """Recursively find the largest string field in a dict."""
        largest_path: Optional[str] = None
        largest_value = ""

        if isinstance(obj, str):
            return path or "root", obj
        elif isinstance(obj, dict):
            for key, value in obj.items():
                if key.startswith("_"):
                    continue
                current_path = f"{path}.{key}" if path else key
                if isinstance(value, str) and len(value) > len(largest_value):
                    largest_path = current_path
                    largest_value = value
                elif isinstance(value, dict):
                    sub_path, sub_value = self._find_largest_string_field(value, current_path)
                    if len(sub_value) > len(largest_value):
                        largest_path = sub_path
                        largest_value = sub_value
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]"
                sub_path, sub_value = self._find_largest_string_field(item, current_path)
                if len(sub_value) > len(largest_value):
                    largest_path = sub_path
                    largest_value = sub_value

        return largest_path, largest_value

    def _set_nested_field(self, obj: Any, path: str, value: Any) -> None:
        """Set a nested field by path."""
        parts = []
        current = ""
        i = 0
        while i < len(path):
            if path[i] == ".":
                if current:
                    parts.append(current)
                current = ""
            elif path[i] == "[":
                if current:
                    parts.append(current)
                current = ""
                j = i + 1
                while j < len(path) and path[j] != "]":
                    j += 1
                parts.append(int(path[i + 1 : j]))
                i = j
            else:
                current += path[i]
            i += 1
        if current:
            parts.append(current)

        target = obj
        for part in parts[:-1]:
            target = target[part] if isinstance(part, int) else target[part]

        last_part = parts[-1]
        if isinstance(last_part, int):
            target[last_part] = value
        else:
            target[last_part] = value

    def _truncate_to_fit(self, result: dict, max_chars: int, store_info: dict) -> dict:
        """Truncate the largest text field to fit in available context space."""
        largest_field, largest_value = self._find_largest_string_field(result)

        if not largest_field or len(largest_value) == 0:
            result_str = json.dumps(result)
            if len(result_str) <= max_chars:
                return result
            return {
                "_truncated": {
                    "field": "entire_result",
                    "shown": max_chars,
                    "total": len(result_str),
                    "file_id": store_info["file_id"],
                },
                "partial_json": result_str[:max_chars],
            }

        result_without_field = copy.deepcopy(result)
        self._set_nested_field(result_without_field, largest_field, "")
        overhead = len(json.dumps(result_without_field))
        truncated_metadata_size = 250
        chars_for_content = max(0, max_chars - overhead - truncated_metadata_size)

        truncated = copy.deepcopy(result)
        truncated_value = largest_value[:chars_for_content]
        self._set_nested_field(truncated, largest_field, truncated_value)

        truncated["_truncated"] = {
            "field": largest_field,
            "shown": len(truncated_value),
            "total": len(largest_value),
            "file_id": store_info["file_id"],
        }

        return truncated

    def _process_tool_result(self, result: dict, source: str = "unknown") -> dict:
        """Process tool result: store in file store, truncate only if needed."""
        if result.get("_truncated") or result.get("_file_store_ref"):
            return result

        result_str = json.dumps(result)
        result_size = len(result_str)

        store_info = self.file_store.store(result_str, source, "json")

        available = self.bedrock.available_for_result(self.messages, self._get_system_prompt(), self.tools)

        if result_size <= available:
            result["_file_store_ref"] = {
                "file_id": store_info["file_id"],
                "size_bytes": store_info["size_bytes"],
            }
            return result

        # Log truncation
        logger.info(f"[{self.agent_id}] ✂️  Truncating: {result_size:,} → {available:,} chars")

        return self._truncate_to_fit(result, available, store_info)

    def _compress_historical_messages(self, keep_recent: int = 2) -> None:
        """
        Compress older tool results in message history to save context space.
        Same as main agent's method but for SubAgent.
        """
        # Find all user messages with tool_result content
        tool_result_indices = []
        for i, msg in enumerate(self.messages):
            if msg.get("role") == "user":
                content = msg.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "tool_result":
                            tool_result_indices.append(i)
                            break

        # Keep the most recent ones full, compress the rest
        if len(tool_result_indices) <= keep_recent:
            return  # Nothing to compress

        indices_to_compress = tool_result_indices[:-keep_recent]
        compressed_count = 0

        for msg_idx in indices_to_compress:
            msg = self.messages[msg_idx]
            content = msg.get("content", [])

            if not isinstance(content, list):
                continue

            new_content = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_result":
                    try:
                        result_content = item.get("content", "{}")
                        if isinstance(result_content, str):
                            result_data = json.loads(result_content)
                        else:
                            result_data = result_content

                        # Check for file store reference (from full results)
                        file_ref = result_data.get("_file_store_ref")
                        # Also check for truncated results which have file_id in _truncated
                        truncated_ref = result_data.get("_truncated")

                        if file_ref:
                            compact = {
                                "compressed": True,
                                "file_id": file_ref["file_id"],
                                "size_bytes": file_ref.get("size_bytes", 0),
                                "note": "Use read_from_store(file_id) if needed",
                            }
                            item["content"] = json.dumps(compact)
                            compressed_count += 1
                        elif truncated_ref and truncated_ref.get("file_id"):
                            compact = {
                                "compressed": True,
                                "file_id": truncated_ref["file_id"],
                                "original_size": truncated_ref.get("total", 0),
                                "note": "Use read_from_store(file_id) if needed",
                            }
                            item["content"] = json.dumps(compact)
                            compressed_count += 1
                        elif result_data.get("stored_in_file_store") or result_data.get("compressed"):
                            pass  # Already a reference
                        else:
                            # No file store ref - store it now if large
                            if len(result_content) > 1000:
                                store_info = self.file_store.store(result_content, "historical_compression", "json")
                                compact = {
                                    "compressed": True,
                                    "file_id": store_info["file_id"],
                                    "size_bytes": store_info["size_bytes"],
                                    "note": "Use read_from_store(file_id) if needed",
                                }
                                item["content"] = json.dumps(compact)
                                compressed_count += 1
                    except (json.JSONDecodeError, TypeError):
                        pass

                new_content.append(item)

            msg["content"] = new_content

        # Silent compression - context management happens automatically

    async def run(self) -> TaskResult:
        """Execute the task and return result."""
        logger.info(f"[{self.agent_id}] 🚀 Starting: {self.task.title}")

        self.messages = [
            {
                "role": "user",
                "content": f"""Execute this documentation task:

**Task**: {self.task.title}

**Description**: {self.task.description}

**Target Files**: {", ".join(self.task.target_files)}

Research thoroughly using Confluence and GitHub, then create comprehensive documentation.
When complete, provide a summary of what was created.""",
            }
        ]

        turns = 0
        while turns < self.MAX_TURNS:
            turns += 1

            # Compress historical tool results to save context space
            self._compress_historical_messages(keep_recent=3)

            try:
                response = self.bedrock.create_message(
                    messages=self.messages,
                    system=self._get_system_prompt(),
                    tools=self.tools,
                )
                self._consecutive_errors = 0
            except Exception as e:
                error_str = str(e)
                
                # Handle context-too-long errors with emergency compression
                if "Input is too long" in error_str or "ValidationException" in error_str:
                    logger.warning(f"[{self.agent_id}] ⚠️  Context too large - emergency compression")
                    self._compress_historical_messages(keep_recent=1)
                    continue
                
                self._consecutive_errors += 1
                if self._consecutive_errors >= 3:
                    return TaskResult(
                        task_id=self.task.id,
                        success=False,
                        files_created=list(self._files_written),
                        summary="",
                        error=f"API errors: {e}",
                        turns_used=turns,
                    )
                await asyncio.sleep(2**self._consecutive_errors)
                continue

            content = response.get("content", [])
            stop_reason = response.get("stop_reason")

            # Log thinking output
            for block in content:
                if block.get("type") == "text":
                    text = block.get("text", "").strip()
                    if text:
                        logger.info(f"[{self.agent_id}] 💭 Thinking ({len(text)} chars):")
                        for line in text.split("\n"):
                            logger.info(f"[{self.agent_id}]    {line}")
                        print(f"\n[{self.agent_id}] {'─' * 50}", flush=True)
                        print(f"[{self.agent_id}] 💭 Thinking:", flush=True)
                        print(text, flush=True)
                        print(f"[{self.agent_id}] {'─' * 50}\n", flush=True)

            # Handle max_tokens
            if stop_reason == "max_tokens":
                content = [b for b in content if not (b.get("type") == "tool_use" and not b.get("id"))]
                if content:
                    self.messages.append({"role": "assistant", "content": content})
                    self.messages.append({"role": "user", "content": "Continue where you left off."})
                continue

            self.messages.append({"role": "assistant", "content": content})

            # Check for completion
            if stop_reason == "end_turn":
                summary = ""
                for block in content:
                    if block.get("type") == "text":
                        summary = block.get("text", "")

                logger.info(f"[{self.agent_id}] ✅ Complete: {self.task.title} ({turns} turns, {len(self._files_written)} files)")
                return TaskResult(
                    task_id=self.task.id,
                    success=True,
                    files_created=list(self._files_written),
                    summary=summary,
                    turns_used=turns,
                )

            # Handle tool use
            if stop_reason == "tool_use":
                tool_results = []
                for block in content:
                    if block.get("type") == "tool_use":
                        result = await self._handle_tool_use(block)
                        if block["name"] not in ("read_from_store", "list_store_files"):
                            result = self._process_tool_result(result, block["name"])
                        tool_results.append({"type": "tool_result", "tool_use_id": block["id"], "content": json.dumps(result)})

                self.messages.append({"role": "user", "content": tool_results})

        # Max turns reached
        return TaskResult(
            task_id=self.task.id,
            success=len(self._files_written) > 0,
            files_created=list(self._files_written),
            summary=f"Reached max turns ({self.MAX_TURNS})",
            turns_used=turns,
        )


# =============================================================================
# Planning Coordinator - Manages parallel sub-agents
# =============================================================================


class PlanningCoordinator:
    """
    Coordinates planning phase, parallel execution, and review.

    Flow:
    1. PLAN: Ask Claude to create a TODO list for the iteration
    2. EXECUTE: Spawn sub-agents in parallel for each task
    3. REVIEW: Check results and update STATUS/BACKLOG
    """

    MAX_PARALLEL = 3  # Limit concurrent sub-agents to avoid rate limits

    PLANNING_PROMPT = """Analyze the project and select ONE high-priority item for COMPREHENSIVE documentation.

Read .project/STATUS.md and .project/BACKLOG.md first.

## Your Task
1. Select the HIGHEST PRIORITY item (not 'deferred' or 'complex')
2. Create a DEEP PLAN with as many subtasks as the topic requires
3. Identify ADDITIONAL FILES needed for complete coverage

## Detail Requirements - BE COMPREHENSIVE
Each subtask should aim to document:
- **API Endpoints**: ALL routes, methods, parameters, headers
- **Data Formats**: Complete request/response schemas with examples
- **Database Effects**: Tables affected, queries performed, transactions
- **Service Dependencies**: Which other services are called, when, why
- **Configuration**: All config options, environment variables, defaults
- **Error Handling**: Error codes, failure modes, retry behavior
- **Authentication**: Auth requirements, token handling, permissions

## Subtask Guidelines
- Create as many subtasks as needed to fully cover the topic
- Break down by logical component (e.g., "Auth API", "Data Models", "Integration Points")
- Subtasks should be parallelizable (no dependencies between them)
- Each subtask should produce DETAILED documentation, not summaries
- Sub-agents will read actual source code to verify accuracy

Respond with JSON:
```json
{
  "main_topic": {
    "title": "The backlog item",
    "backlog_reference": "Exact text from BACKLOG.md"
  },
  "subtasks": [
    {
      "id": "subtask_1",
      "title": "Short title",
      "description": "Detailed description including WHAT to document and WHAT DETAIL to include",
      "suggested_files": ["path/to/file.md"],
      "priority": 1
    }
  ],
  "additional_files": [
    {"path": "path/to/extra.md", "purpose": "Why needed"}
  ]
}
```

IMPORTANT:
- Do NOT include STATUS.md or BACKLOG.md as target files
- Each subtask gets its own sub-agent running in parallel
- Keep subtasks independent - no dependencies between them
- Focus on ONE main topic with deep, comprehensive coverage
"""

    REVIEW_PROMPT = """Review the results from parallel documentation tasks and update the project tracking files.

## Original Plan
{plan_summary}

## Task Results
{results_summary}

## Instructions
1. Read current .project/STATUS.md and .project/BACKLOG.md
2. Update STATUS.md to reflect completed work
3. Update BACKLOG.md to mark completed items with [x]
4. Note any failures or incomplete work

Provide a summary of what was accomplished this iteration.
"""

    def __init__(
        self,
        shell: ShellTool,
        mcp: MCPClient,
        bedrock: BedrockClient,
        file_store: FileStore,
        tools: list[dict],
        work_dir: Path,
    ):
        self.shell = shell
        self.mcp = mcp
        self.bedrock = bedrock
        self.file_store = file_store
        self.tools = tools
        self.work_dir = work_dir
        self._current_main_topic: Optional[dict] = None
        self._additional_files: list[dict] = []

    def _log_thinking(self, response: dict, agent_id: str) -> None:
        """Log thinking/reasoning output from Claude."""
        for block in response.get("content", []):
            if block.get("type") == "text":
                text = block.get("text", "").strip()
                if text:
                    logger.info(f"[{agent_id}] 💭 Thinking ({len(text)} chars):")
                    for line in text.split("\n"):
                        logger.info(f"[{agent_id}]    {line}")
                    print(f"\n[{agent_id}] {'─' * 50}", flush=True)
                    print(f"[{agent_id}] 💭 Thinking:", flush=True)
                    print(text, flush=True)
                    print(f"[{agent_id}] {'─' * 50}\n", flush=True)

    async def create_plan(self) -> list[PlanTask]:
        """Ask Claude to create a plan for this iteration."""
        logger.info("📋 PLANNING PHASE: Creating task plan...")
        print(f"\n{'=' * 60}")
        print("  PLANNING PHASE")
        print(f"{'=' * 60}\n")

        messages = [{"role": "user", "content": self.PLANNING_PROMPT}]

        # Allow Claude to read files for planning
        planning_tools = self.shell.get_tool_definitions()

        try:
            # First call - may need to read files
            response = self.bedrock.create_message(
                messages=messages,
                system="You are a documentation project planner. Create actionable, parallelizable task plans.",
                tools=planning_tools,
            )

            # Log any thinking from the planner
            self._log_thinking(response, "planner")

            # Handle tool use (reading STATUS/BACKLOG and exploring repo)
            max_planning_turns = 15
            for _ in range(max_planning_turns):
                if response.get("stop_reason") != "tool_use":
                    break

                content = response.get("content", [])
                messages.append({"role": "assistant", "content": content})

                tool_results = []
                for block in content:
                    if block.get("type") == "tool_use":
                        logger.info(f"[planner] Tool: {block['name']}")
                        if block["name"] == "read_file":
                            result = self.shell.read_file(block["input"].get("path", ""))
                        elif block["name"] == "list_directory":
                            result = self.shell.list_directory(block["input"].get("path", "."))
                        elif block["name"] == "bash":
                            # Allow read-only bash commands for exploration
                            result = self.shell.execute(block["input"].get("command", ""), block["input"].get("description", ""))
                        else:
                            result = {"error": "Only read operations allowed in planning"}
                        tool_results.append({"type": "tool_result", "tool_use_id": block["id"], "content": json.dumps(result)})

                messages.append({"role": "user", "content": tool_results})
                response = self.bedrock.create_message(messages=messages, system="You are a documentation project planner.", tools=planning_tools)

                # Log thinking after each turn
                self._log_thinking(response, "planner")

            # Extract plan from response
            plan_text = ""
            for block in response.get("content", []):
                if block.get("type") == "text":
                    plan_text = block.get("text", "")

            # Parse JSON from response
            main_topic, tasks, additional_files = self._parse_plan(plan_text)

            if main_topic:
                logger.info(f"📋 Main topic: {main_topic.get('title', 'Unknown')}")
                print(f"\n  🎯 MAIN TOPIC: {main_topic.get('title', 'Unknown')}")
                if main_topic.get("backlog_reference"):
                    print(f"     Backlog: {main_topic.get('backlog_reference')}")

            if tasks:
                logger.info(f"📋 Plan created with {len(tasks)} subtasks:")
                for t in tasks:
                    logger.info(f"   - {t.title} → {', '.join(t.target_files)}")
                    print(f"  📌 {t.title}")
                    print(f"     Files: {', '.join(t.target_files)}")
            else:
                logger.warning("Failed to parse plan - no subtasks extracted")

            if additional_files:
                logger.info(f"📋 Additional files suggested: {len(additional_files)}")
                for af in additional_files:
                    logger.info(f"   - {af.get('path')}: {af.get('purpose')}")

            # Store main_topic for review phase
            self._current_main_topic = main_topic
            self._additional_files = additional_files

            return tasks

        except Exception as e:
            logger.error(f"Planning failed: {e}")
            return []

    def _parse_plan(self, text: str) -> Tuple[Optional[dict], list[PlanTask], list[dict]]:
        """Parse plan JSON from Claude's response.

        Returns:
            Tuple of (main_topic, subtasks, additional_files)
        """
        try:
            # Find JSON in response
            json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON object
                json_match = re.search(r"\{[\s\S]*\}", text)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    return None, [], []

            plan_data = json.loads(json_str)

            # Handle new format with main_topic
            main_topic = plan_data.get("main_topic")
            additional_files = plan_data.get("additional_files", [])

            # Get subtasks (new format) or fall back to old array format
            subtasks_data = plan_data.get("subtasks", [])
            if not subtasks_data and isinstance(plan_data, list):
                # Old format - array of tasks
                subtasks_data = plan_data

            tasks = []
            for t in subtasks_data:
                tasks.append(
                    PlanTask(
                        id=t.get("id", f"subtask_{len(tasks)}"),
                        title=t.get("title", "Untitled"),
                        description=t.get("description", ""),
                        target_files=t.get("suggested_files", t.get("target_files", [])),
                        dependencies=t.get("dependencies", []),
                        priority=t.get("priority", 1),
                    )
                )

            return main_topic, tasks, additional_files

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse plan JSON: {e}")
            return None, [], []

    async def execute_parallel(self, tasks: list[PlanTask]) -> list[TaskResult]:
        """Execute tasks in parallel using sub-agents."""
        logger.info(f"🚀 EXECUTION PHASE: Running {len(tasks)} tasks in parallel (max {self.MAX_PARALLEL} concurrent)")
        print(f"\n{'=' * 60}")
        print(f"  EXECUTION PHASE - {len(tasks)} parallel tasks")
        print(f"{'=' * 60}\n")

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.MAX_PARALLEL)

        async def run_with_semaphore(task: PlanTask, agent_id: str) -> TaskResult:
            async with semaphore:
                print(f"  ▶️  [{agent_id}] Starting: {task.title}")
                logger.info(f"[{agent_id}] Starting task: {task.title}")
                sub_agent = SubAgent(
                    task=task,
                    agent_id=agent_id,
                    shell=self.shell,
                    mcp=self.mcp,
                    bedrock=self.bedrock,
                    file_store=self.file_store,
                    tools=self.tools,
                    work_dir=self.work_dir,
                )
                result = await sub_agent.run()
                status = "✅" if result.success else "❌"
                print(f"  {status} [{agent_id}] Finished: {task.title} ({result.turns_used} turns, {len(result.files_created)} files)")
                logger.info(f"[{agent_id}] Finished: {task.title} ({result.turns_used} turns, {len(result.files_created)} files)")
                return result

        # Run all tasks in parallel with unique agent IDs
        results = await asyncio.gather(*[run_with_semaphore(task, f"sub-{i + 1}") for i, task in enumerate(tasks)], return_exceptions=True)

        # Convert exceptions to failed results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(
                    TaskResult(
                        task_id=tasks[i].id,
                        success=False,
                        files_created=[],
                        summary="",
                        error=str(result),
                    )
                )
            else:
                final_results.append(result)

        return final_results

    async def review_results(self, tasks: list[PlanTask], results: list[TaskResult]) -> tuple[bool, list[str]]:
        """Review results and update STATUS/BACKLOG."""
        logger.info("📝 REVIEW PHASE: Updating project tracking...")
        print(f"\n{'=' * 60}")
        print("  REVIEW PHASE")
        print(f"{'=' * 60}\n")

        # Build summaries
        plan_summary = "\n".join([f"- {t.title}: {', '.join(t.target_files)}" for t in tasks])

        results_summary = ""
        all_files = []
        for r in results:
            status = "SUCCESS" if r.success else "FAILED"
            results_summary += f"\n### {r.task_id}: {status}\n"
            results_summary += f"Files created: {r.files_created}\n"
            results_summary += f"Turns used: {r.turns_used}\n"
            if r.error:
                results_summary += f"Error: {r.error}\n"
            if r.summary:
                results_summary += f"Summary: {r.summary[:500]}...\n" if len(r.summary) > 500 else f"Summary: {r.summary}\n"
            all_files.extend(r.files_created)

        # Ask Claude to review and update tracking files
        review_prompt = self.REVIEW_PROMPT.format(plan_summary=plan_summary, results_summary=results_summary)

        messages = [{"role": "user", "content": review_prompt}]

        try:
            response = self.bedrock.create_message(
                messages=messages,
                system="You are updating project tracking files based on completed documentation work.",
                tools=self.shell.get_tool_definitions(),
            )

            # Handle tool use for reading/writing STATUS and BACKLOG
            max_review_turns = 10
            for _ in range(max_review_turns):
                if response.get("stop_reason") != "tool_use":
                    break

                content = response.get("content", [])
                messages.append({"role": "assistant", "content": content})

                tool_results = []
                for block in content:
                    if block.get("type") == "tool_use":
                        tool_name = block["name"]
                        tool_input = block.get("input", {})

                        if tool_name == "read_file":
                            result = self.shell.read_file(tool_input.get("path", ""))
                        elif tool_name == "write_file":
                            path = tool_input.get("path", "")
                            # Only allow writing to .project/ files in review
                            if ".project/" in path:
                                result = self.shell.write_file(path, tool_input.get("content", ""))
                                if result.get("success"):
                                    all_files.append(path)
                            else:
                                result = {"error": "Review phase can only write to .project/ files"}
                        elif tool_name == "list_directory":
                            result = self.shell.list_directory(tool_input.get("path", "."))
                        else:
                            result = {"error": f"Tool {tool_name} not allowed in review phase"}

                        tool_results.append({"type": "tool_result", "tool_use_id": block["id"], "content": json.dumps(result)})

                messages.append({"role": "user", "content": tool_results})
                response = self.bedrock.create_message(messages=messages, system="You are updating project tracking files.", tools=self.shell.get_tool_definitions())

            # Extract summary
            for block in response.get("content", []):
                if block.get("type") == "text":
                    print(f"\n📋 Review summary:\n{block.get('text', '')[:500]}")

            # Check if any tasks succeeded
            any_success = any(r.success for r in results)
            return any_success, all_files

        except Exception as e:
            logger.error(f"Review phase failed: {e}")
            return False, all_files

    async def run_iteration(self) -> tuple[bool, list[str]]:
        """
        Run a complete iteration: plan -> execute -> review.

        Returns:
            (success, files_modified)
        """
        # Phase 1: Planning
        tasks = await self.create_plan()
        if not tasks:
            logger.info("No tasks to execute this iteration")
            return False, []

        # Phase 2: Parallel Execution
        results = await self.execute_parallel(tasks)

        # Phase 3: Review
        success, all_files = await self.review_results(tasks, results)

        return success, all_files


# =============================================================================
# Documentation Agent
# =============================================================================


class DocumentationAgent:
    """
    Main agent that orchestrates documentation generation using Claude
    with shell and MCP tools.

    Features:
    - Loop detection: Detects repeated tool call patterns
    - Error handling: Exits after consecutive errors
    - Completion detection: Recognizes when tasks are done
    """

    # Exit conditions
    MAX_CONSECUTIVE_ERRORS = 3
    MAX_REPEATED_PATTERNS = 3  # Exit if same pattern repeats this many times
    PATTERN_WINDOW_SIZE = 5  # Look at last N tool calls for pattern detection

    # Context management
    MAX_TOOL_RESULT_CHARS = 50000  # Store results larger than this (~12K tokens)
    CONTEXT_SOFT_RESET_THRESHOLD = 0.50  # Trigger soft reset at 50% - need room for summary!

    SYSTEM_PROMPT = """You are an expert documentation engineer helping to create and maintain platform documentation for Natterbox.

You have access to the following tool categories:

1. **Shell Tools** (bash, read_file, write_file, list_directory):
   - Execute commands in the workspace
   - Create and edit documentation files
   - Manage the file system

2. **Tool Result Handling**:
   - Results are returned in their natural JSON format
   - When a result is too large for context, the largest text field is truncated
   - Look for `_truncated` metadata in results:
     ```
     {
       "text": "first N characters...",
       "_truncated": {
         "field": "text",
         "shown": 50000,
         "total": 152000,
         "file_id": "abc123"
       }
     }
     ```
   - To read more of a truncated field, use: read_from_store(file_id="abc123", offset=50000, limit=50000)
   - Older tool results may be compressed to `{"compressed": true, "file_id": "..."}` - use read_from_store to retrieve

3. **File Store Tools** (read_from_store, list_store_files):
   - Use read_from_store(file_id, offset, limit) to read truncated or compressed results
   - Offsets are in CHARACTERS not lines!
   - **CRITICAL**: ALWAYS check `has_more` in the response!
   - If `has_more` is true, you have NOT seen all the data
   - Use `next_offset` from the response to continue reading
   - Default limit is 50000 chars (~12500 tokens)

4. **MCP Tools** (prefixed with mcp_):
   - mcp_confluence: Search and read Confluence wiki pages
   - mcp_github: Access GitHub repositories and files  
   - mcp_docs360_search: Search Document360 knowledge base
   - mcp_salesforce: Query Salesforce data
   - mcp_slack: Access Slack channels and messages
   - And more...

## DEEP RESEARCH METHODOLOGY - THIS IS CRITICAL

You MUST go DEEP in your research. Surface-level documentation is not acceptable. For every topic:

### 1. Multi-Source Research (REQUIRED)
   - **Confluence**: Search for ALL related pages. Read the full content of each.
   - **GitHub**: Find the actual repository. Read README files, but ALSO:
     - Get the repository tree structure to understand the codebase layout
     - Read key source files (main entry points, configuration, core modules)
     - Check package.json, requirements.txt, Cargo.toml etc for dependencies
     - Look at Terraform/infrastructure code if present
     - Read tests to understand expected behavior
   - **Document360**: Check for customer-facing docs that may have additional context
   - Cross-reference between sources to verify accuracy

### 2. Source Code Verification (REQUIRED)
   - Do NOT just document what Confluence says - VERIFY it in the code
   - Read actual source files to understand:
     - How components really work (not just how docs say they work)
     - Configuration options and their defaults
     - API endpoints and their parameters  
     - Database schemas and data models
     - Error handling and edge cases
   - If Confluence says "X does Y", find the code that does Y and verify it
   - Note any discrepancies between docs and code

### 3. Architecture Understanding (REQUIRED)
   - Map out dependencies between services
   - Understand data flows
   - Document integration points with other systems
   - Identify configuration files and environment variables
   - Note deployment considerations

### 4. Documentation Depth Requirements
   Your documentation MUST include:
   - **Technical architecture** with component diagrams (ASCII art)
   - **Code examples** from actual source files
   - **Configuration reference** with all options documented
   - **API documentation** with request/response examples
   - **Data models** and database schemas where relevant
   - **Deployment information** (how it's deployed, where it runs)
   - **Troubleshooting** common issues and their solutions
   - **Related services** and how they interact

## Your Workflow

1. **Deep Research Phase**: 
   - Search Confluence for ALL related pages (search multiple terms)
   - Find the GitHub repository and explore its structure
   - READ THE SOURCE CODE - don't just rely on READMEs
   - Cross-reference information between sources
   
2. **Verification Phase**:
   - Verify claims from docs against actual code
   - Check that documented APIs match implementation
   - Identify any outdated or incorrect documentation
   
3. **Synthesis Phase**: 
   - Combine information from all sources
   - Resolve conflicts (prefer code over docs when they disagree)
   - Structure the documentation logically
   
4. **Creation Phase**: 
   - Write comprehensive markdown documentation
   - Include code examples from actual sources
   - Add architecture diagrams
   - Reference specific files and line numbers where helpful

## Documentation Standards

- Use clear markdown formatting with proper hierarchy
- Include source references (Confluence links, GitHub file paths)
- Add "Last Updated" dates  
- Use tables for structured information (config options, API params)
- Include ASCII architecture diagrams
- Add code examples from actual repositories
- Document ALL configuration options, not just common ones
- Include troubleshooting sections

## Current Date: {date}

## THINKING OUT LOUD

IMPORTANT: Before making tool calls, explain your research strategy.
Share what you're looking for, what you've found, and what's still missing.
When you find discrepancies between sources, note them.
This helps ensure thorough, accurate documentation.

## Quality Standards

- NEVER create shallow documentation that just summarizes Confluence
- ALWAYS verify documentation against source code
- If you can't find source code, explicitly note this gap
- Documentation should be useful to a new engineer joining the team
- Include enough detail that someone could debug issues using your docs

## Task Completion

When you have completed the requested task:
1. Provide a clear summary of what was accomplished  
2. List all files that were created or modified
3. Note any source code you reviewed to verify accuracy
4. Explicitly state "Task complete"
5. Note any gaps or areas needing further investigation

If you encounter issues:
1. Explain what went wrong
2. Describe what was partially completed
3. Suggest how to resolve the issue
"""

    # Continuation file for resuming interrupted tasks
    CONTINUATION_FILE = ".project/continuation.json"

    def __init__(self, config: Config):
        self.config = config
        self.shell = ShellTool(config.work_dir, config.shell_timeout)
        self.mcp = MCPClient(config.natterbox_mcp_url)
        self.bedrock = BedrockClient(config)
        self.file_store = FileStore(config.work_dir)  # For caching large results
        self.messages: list[dict] = []
        self.tools: list[dict] = []

        # Tracking for loop detection and error handling
        self._tool_call_history: list[str] = []  # Hashes of recent tool calls
        self._consecutive_errors = 0
        self._files_written: set[str] = set()  # Track created files

        # Continuation file path
        self._continuation_path = self.config.work_dir / self.CONTINUATION_FILE

    def _check_continuation(self) -> Optional[dict]:
        """Check if there's a continuation file from a previous interrupted run."""
        try:
            if self._continuation_path.exists():
                data = json.loads(self._continuation_path.read_text())
                logger.info(f"📋 Found continuation file from: {data.get('timestamp', 'unknown')}")
                logger.info(f"   Original task: {data.get('original_task', 'unknown')[:80]}...")
                return data
        except Exception as e:
            logger.warning(f"Failed to load continuation file: {e}")
        return None

    def _clear_continuation(self):
        """Remove the continuation file after successful completion."""
        try:
            if self._continuation_path.exists():
                self._continuation_path.unlink()
                logger.info("🗑️  Cleared continuation file (task complete)")
        except Exception as e:
            logger.warning(f"Failed to clear continuation file: {e}")

    def _has_incomplete_tool_use(self) -> bool:
        """Check if the message history has tool_use blocks without corresponding tool_result."""
        if not self.messages:
            return False

        # Check the last assistant message
        for msg in reversed(self.messages):
            if msg.get("role") == "assistant":
                content = msg.get("content", [])
                if isinstance(content, list):
                    for block in content:
                        if block.get("type") == "tool_use":
                            # Found a tool_use - check if there's a tool_result after
                            return True  # If we're here, there's no tool_result yet
                break
            elif msg.get("role") == "user":
                # If user message comes first (going backwards), check if it has tool_result
                content = msg.get("content", [])
                if isinstance(content, list):
                    for block in content:
                        if block.get("type") == "tool_result":
                            return False  # Tool results exist, we're good
                break

        return False

    def _get_fallback_continuation(self, original_task: str, turns_used: int) -> str:
        """Generate a fallback continuation without calling Claude."""
        files_list = ", ".join(self._files_written) if self._files_written else "none yet"
        return f"""CONTINUATION: Resuming documentation task after interruption.

Task was interrupted after {turns_used} turns (context limit reached).

Files created so far: {files_list}

Original task: {original_task}

Please read .project/STATUS.md and .project/BACKLOG.md to understand current progress,
then continue with the next highest priority item."""

    def _generate_continuation_prompt(self, original_task: str, turns_used: int) -> str:
        """
        Ask Claude to generate a continuation prompt capturing current progress.
        This is called when we run out of turns.
        """
        logger.info("📝 Generating continuation prompt for next run...")

        # Check if we have incomplete tool_use blocks - if so, use fallback
        if self._has_incomplete_tool_use():
            logger.warning("⚠️  Cannot ask Claude for continuation - incomplete tool_use in history. Using fallback.")
            return self._get_fallback_continuation(original_task, turns_used)

        # Add a special message asking for a continuation summary
        continuation_request = """
IMPORTANT: The task has been interrupted due to reaching the maximum number of turns.

Please provide a CONTINUATION PROMPT that I can use to resume this task exactly where you left off.
The continuation prompt should:

1. Briefly summarize what has been accomplished so far
2. List any files that were created or modified
3. Clearly state what the NEXT STEPS should be
4. Include any important context or decisions made during this session

Format your response as a clear, actionable prompt that another instance can use to continue the work.
Start your response with "CONTINUATION PROMPT:" followed by the prompt text.
"""

        # Temporarily add this to messages
        self.messages.append({"role": "user", "content": continuation_request})

        try:
            response = self.bedrock.create_message(
                messages=self.messages,
                system=self._get_system_prompt(),
                tools=[],  # No tools needed for this
            )

            # Extract the continuation prompt
            for block in response.get("content", []):
                if block.get("type") == "text":
                    text = block.get("text", "")
                    # Try to extract just the continuation prompt
                    if "CONTINUATION PROMPT:" in text:
                        prompt = text.split("CONTINUATION PROMPT:", 1)[1].strip()
                        return prompt
                    return text

        except Exception as e:
            logger.error(f"Failed to generate continuation prompt: {e}")
            # Fallback: create a basic continuation prompt
            return f"""Continue the documentation task from where it was interrupted.

Original task: {original_task}

Files created so far: {list(self._files_written)}

The previous run used {turns_used} turns. Please review the project status files 
(.project/STATUS.md, .project/BACKLOG.md) and continue with the next logical step."""

        return ""

    def _save_continuation(self, original_task: str, continuation_prompt: str, turns_used: int):
        """Save continuation data for the next run."""
        try:
            self._continuation_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "timestamp": datetime.now().isoformat(),
                "original_task": original_task,
                "continuation_prompt": continuation_prompt,
                "turns_used": turns_used,
                "files_written": list(self._files_written),
            }

            self._continuation_path.write_text(json.dumps(data, indent=2))
            logger.info(f"💾 Saved continuation prompt to: {self._continuation_path}")

        except Exception as e:
            logger.error(f"Failed to save continuation: {e}")

    def _should_soft_reset(self) -> bool:
        """Check if context is large enough to warrant a soft reset."""
        context_size = self.bedrock.estimate_context_size(self.messages, self._get_system_prompt(), self.tools)
        threshold = int(self.bedrock.CONTEXT_LIMIT_CHARS * self.CONTEXT_SOFT_RESET_THRESHOLD)
        return context_size > threshold

    def _perform_soft_reset(self, original_task: str, turns_used: int) -> str:
        """
        Perform a soft reset: ask Claude to summarize progress, then clear context.
        Returns the continuation prompt to use for the fresh context.

        Strategy:
        1. Check for incomplete tool_use - use fallback if found
        2. Aggressively truncate messages to make room for summary request
        3. Ask for summary with the reduced context
        4. Fallback to state-based continuation if summary fails
        """
        logger.info("🔄 Context getting large - performing soft reset...")
        print(f"\n{'=' * 60}")
        print("SOFT RESET - Context approaching limit")
        print(f"{'=' * 60}\n")

        # Check for incomplete tool_use - if so, use fallback immediately
        if self._has_incomplete_tool_use():
            logger.warning("⚠️  Incomplete tool_use in history - using fallback continuation")
            return self._get_fallback_continuation(original_task, turns_used)

        # STEP 1: Aggressively truncate to make room for summary
        # Keep only first message (task) and last 3 exchanges
        original_message_count = len(self.messages)
        if len(self.messages) > 7:
            first_message = self.messages[0]  # Keep original task
            last_messages = self.messages[-6:]  # Keep last 3 exchanges (6 messages)
            self.messages = [first_message] + last_messages
            logger.info(f"📦 Truncated messages: {original_message_count} → {len(self.messages)} for summary request")

        # Also compress any remaining tool results
        self._compress_historical_messages(keep_recent=1)

        # STEP 2: Ask Claude for summary (with reduced context)
        reset_request = """CONTEXT RESET NEEDED. Provide a brief CONTINUATION summary:

1. DONE: Files created this task
2. CURRENT: What you were working on  
3. NEXT: Immediate next step

Keep it SHORT (under 500 words). Start with "CONTINUATION:"
"""

        self.messages.append({"role": "user", "content": reset_request})

        try:
            response = self.bedrock.create_message(
                messages=self.messages,
                system="You are summarizing your progress. Be concise.",
                tools=[],
            )

            continuation = ""
            for block in response.get("content", []):
                if block.get("type") == "text":
                    text = block.get("text", "")
                    if "CONTINUATION:" in text:
                        continuation = text.split("CONTINUATION:", 1)[1].strip()
                    else:
                        continuation = text

            if continuation:
                logger.info("✅ Got continuation prompt for soft reset")
                print(f"📋 Continuation summary received ({len(continuation)} chars)")
                return continuation

        except Exception as e:
            logger.error(f"Failed to get soft reset summary: {e}")

        # STEP 3: Fallback - build continuation from saved state
        logger.info("Using state-based fallback for continuation")

        # Read current status from file if possible
        status_hint = ""
        try:
            status_path = self.config.work_dir / ".project" / "STATUS.md"
            if status_path.exists():
                status_content = status_path.read_text()
                # Extract just the "Next Up" section if present
                if "## Next Up" in status_content:
                    next_up = status_content.split("## Next Up")[1].split("##")[0].strip()
                    status_hint = f"\nFrom STATUS.md Next Up:\n{next_up[:500]}"
        except Exception:
            pass

        files_list = ", ".join(self._files_written) if self._files_written else "none yet"

        return f"""CONTINUATION: Resuming documentation task after context reset.

**Files created this session**: {files_list}
**Turns completed**: {turns_used}
{status_hint}

**NEXT STEPS**:
1. Read .project/STATUS.md and .project/BACKLOG.md to understand current state
2. Continue with the next incomplete documentation item
3. Use the file store (list_store_files) if you need data from earlier research

Original task: {original_task}"""

    async def initialize(self) -> bool:
        """Initialize the agent and connect to services."""
        logger.info("Initializing documentation agent...")

        # Initialize shell tools
        self.tools.extend(self.shell.get_tool_definitions())
        logger.info(f"Loaded {len(self.shell.get_tool_definitions())} shell tools")

        # Initialize file store tools
        self.tools.extend(self.file_store.get_tool_definitions())
        logger.info(f"Loaded {len(self.file_store.get_tool_definitions())} file store tools")

        # Connect to MCP server
        if await self.mcp.connect():
            self.tools.extend(self.mcp.get_tool_definitions())
            logger.info(f"Loaded {len(self.mcp.get_tool_definitions())} MCP tools")
        else:
            logger.warning("MCP connection failed - continuing with shell tools only")

        logger.info(f"Agent initialized with {len(self.tools)} total tools")
        return True

    def _get_system_prompt(self) -> str:
        """Get the system prompt with current date."""
        return self.SYSTEM_PROMPT.format(date=datetime.now().strftime("%Y-%m-%d"))

    def _get_tool_call_hash(self, tool_name: str, tool_input: dict) -> str:
        """Generate a hash for a tool call to detect duplicates."""
        import hashlib

        # Create a normalized representation
        call_str = f"{tool_name}:{json.dumps(tool_input, sort_keys=True)}"
        return hashlib.md5(call_str.encode()).hexdigest()[:12]

    def _detect_loop(self, tool_calls: list[tuple[str, dict]]) -> bool:
        """
        Detect if we're in a loop by checking for repeated patterns.
        Returns True if a loop is detected.
        """
        # Add new tool calls to history
        for name, inputs in tool_calls:
            call_hash = self._get_tool_call_hash(name, inputs)
            self._tool_call_history.append(call_hash)

        # Keep only recent history
        if len(self._tool_call_history) > self.PATTERN_WINDOW_SIZE * 3:
            self._tool_call_history = self._tool_call_history[-self.PATTERN_WINDOW_SIZE * 3 :]

        # Check for repeated patterns
        if len(self._tool_call_history) >= self.PATTERN_WINDOW_SIZE * 2:
            recent = self._tool_call_history[-self.PATTERN_WINDOW_SIZE :]

            # Count how many times this exact pattern appears
            pattern_count = 0
            for i in range(len(self._tool_call_history) - self.PATTERN_WINDOW_SIZE + 1):
                window = self._tool_call_history[i : i + self.PATTERN_WINDOW_SIZE]
                if window == recent:
                    pattern_count += 1

            if pattern_count >= self.MAX_REPEATED_PATTERNS:
                logger.warning(f"Loop detected: pattern repeated {pattern_count} times")
                return True

        return False

    def _check_task_completion(self, response_text: str) -> bool:
        """
        Check if the response indicates task completion.
        """
        completion_indicators = [
            "task is complete",
            "task complete",
            "documentation has been created",
            "successfully created",
            "finished creating",
            "documentation is now available",
            "work is complete",
            "all done",
        ]

        text_lower = response_text.lower()
        return any(indicator in text_lower for indicator in completion_indicators)

    def _find_largest_string_field(self, obj: Any, path: str = "") -> Tuple[Optional[str], str]:
        """
        Recursively find the largest string field in a dict.

        Returns:
            Tuple of (field_path, field_value) for the largest string field.
            Returns (None, "") if no string field found.
        """
        largest_path: Optional[str] = None
        largest_value = ""

        if isinstance(obj, str):
            return path or "root", obj
        elif isinstance(obj, dict):
            for key, value in obj.items():
                if key.startswith("_"):  # Skip metadata fields
                    continue
                current_path = f"{path}.{key}" if path else key
                if isinstance(value, str) and len(value) > len(largest_value):
                    largest_path = current_path
                    largest_value = value
                elif isinstance(value, dict):
                    sub_path, sub_value = self._find_largest_string_field(value, current_path)
                    if len(sub_value) > len(largest_value):
                        largest_path = sub_path
                        largest_value = sub_value
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]"
                sub_path, sub_value = self._find_largest_string_field(item, current_path)
                if len(sub_value) > len(largest_value):
                    largest_path = sub_path
                    largest_value = sub_value

        return largest_path, largest_value

    def _set_nested_field(self, obj: Any, path: str, value: Any) -> None:
        """Set a nested field by path (e.g., 'result.content' or 'items[0].text')."""
        parts = []
        current = ""
        i = 0
        while i < len(path):
            if path[i] == ".":
                if current:
                    parts.append(current)
                current = ""
            elif path[i] == "[":
                if current:
                    parts.append(current)
                current = ""
                # Find closing bracket
                j = i + 1
                while j < len(path) and path[j] != "]":
                    j += 1
                parts.append(int(path[i + 1 : j]))
                i = j
            else:
                current += path[i]
            i += 1
        if current:
            parts.append(current)

        # Navigate to parent and set value
        target = obj
        for part in parts[:-1]:
            if isinstance(part, int):
                target = target[part]
            else:
                target = target[part]

        last_part = parts[-1]
        if isinstance(last_part, int):
            target[last_part] = value
        else:
            target[last_part] = value

    def _truncate_to_fit(self, result: dict, max_chars: int, store_info: dict) -> dict:
        """
        Truncate the largest text field to fit in available context space.

        Returns the truncated result with _truncated metadata added.
        """
        # Find the largest string field
        largest_field, largest_value = self._find_largest_string_field(result)

        if not largest_field or len(largest_value) == 0:
            # No string field to truncate - return truncated JSON
            result_str = json.dumps(result)
            if len(result_str) <= max_chars:
                return result
            # Best effort: truncate the JSON string itself
            return {
                "_truncated": {
                    "field": "entire_result",
                    "shown": max_chars,
                    "total": len(result_str),
                    "file_id": store_info["file_id"],
                },
                "partial_json": result_str[:max_chars],
            }

        # Calculate how much content we can keep
        # Account for overhead of other fields + _truncated metadata
        result_without_field = copy.deepcopy(result)
        self._set_nested_field(result_without_field, largest_field, "")
        overhead = len(json.dumps(result_without_field))
        truncated_metadata_size = 250  # Approximate size of _truncated field
        chars_for_content = max(0, max_chars - overhead - truncated_metadata_size)

        # Create truncated copy
        truncated = copy.deepcopy(result)
        truncated_value = largest_value[:chars_for_content]
        self._set_nested_field(truncated, largest_field, truncated_value)

        truncated["_truncated"] = {
            "field": largest_field,
            "shown": len(truncated_value),
            "total": len(largest_value),
            "file_id": store_info["file_id"],
        }

        return truncated

    def _process_tool_result(self, result: dict, source: str = "unknown") -> dict:
        """
        Process tool result: store in file store, truncate only if needed.

        Strategy:
        - Always store the full result in file store for later retrieval
        - Calculate available context space
        - If result fits: return as-is with _file_store_ref for later compression
        - If result too big: truncate largest text field and add _truncated metadata

        Args:
            result: The tool result dict
            source: Description of the source (tool name)

        Returns:
            The result, possibly truncated with _truncated metadata if it was too large
        """
        # Skip if already processed
        if result.get("_truncated") or result.get("_file_store_ref"):
            return result

        result_str = json.dumps(result)
        result_size = len(result_str)

        # Always store full result for later retrieval
        store_info = self.file_store.store(result_str, source, "json")

        # Calculate available context space
        available = self.bedrock.available_for_result(self.messages, self._get_system_prompt(), self.tools)

        # If result fits, return as-is with file reference for later compression
        if result_size <= available:
            result["_file_store_ref"] = {
                "file_id": store_info["file_id"],
                "size_bytes": store_info["size_bytes"],
            }
            return result

        # Log truncation
        logger.info(f"✂️  Truncating: {result_size:,} → {available:,} chars")

        return self._truncate_to_fit(result, available, store_info)

    def _compress_historical_messages(self, keep_recent: int = 2) -> None:
        """
        Compress older tool results in message history to save context space.

        Replaces full tool result content with compact file store references,
        since the LLM has already processed this data and can retrieve it
        if needed.

        Args:
            keep_recent: Number of recent tool result messages to keep full
        """
        # Find all user messages with tool_result content
        tool_result_indices = []
        for i, msg in enumerate(self.messages):
            if msg.get("role") == "user":
                content = msg.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "tool_result":
                            tool_result_indices.append(i)
                            break

        # Keep the most recent ones full, compress the rest
        if len(tool_result_indices) <= keep_recent:
            return  # Nothing to compress

        indices_to_compress = tool_result_indices[:-keep_recent]
        compressed_count = 0

        for msg_idx in indices_to_compress:
            msg = self.messages[msg_idx]
            content = msg.get("content", [])

            if not isinstance(content, list):
                continue

            new_content = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_result":
                    # Parse the tool result content
                    try:
                        result_content = item.get("content", "{}")
                        if isinstance(result_content, str):
                            result_data = json.loads(result_content)
                        else:
                            result_data = result_content

                        # Check for file store reference (from full results)
                        file_ref = result_data.get("_file_store_ref")
                        # Also check for truncated results which have file_id in _truncated
                        truncated_ref = result_data.get("_truncated")

                        if file_ref:
                            # Replace with compact reference
                            compact = {
                                "compressed": True,
                                "file_id": file_ref["file_id"],
                                "size_bytes": file_ref.get("size_bytes", 0),
                                "note": "Use read_from_store(file_id) if needed",
                            }
                            item["content"] = json.dumps(compact)
                            compressed_count += 1
                        elif truncated_ref and truncated_ref.get("file_id"):
                            # Was already truncated, compress to just reference
                            compact = {
                                "compressed": True,
                                "file_id": truncated_ref["file_id"],
                                "original_size": truncated_ref.get("total", 0),
                                "note": "Use read_from_store(file_id) if needed",
                            }
                            item["content"] = json.dumps(compact)
                            compressed_count += 1
                        elif result_data.get("stored_in_file_store") or result_data.get("compressed"):
                            # Already a reference, keep as is
                            pass
                        else:
                            # No file store ref - check if content is large
                            if len(result_content) > 1000:
                                # Store it now for future reference
                                store_info = self.file_store.store(result_content, "historical_compression", "json")
                                compact = {
                                    "compressed": True,
                                    "file_id": store_info["file_id"],
                                    "size_bytes": store_info["size_bytes"],
                                    "note": "Use read_from_store(file_id) if needed",
                                }
                                item["content"] = json.dumps(compact)
                                compressed_count += 1
                    except (json.JSONDecodeError, TypeError):
                        pass  # Keep original if we can't parse

                new_content.append(item)

            msg["content"] = new_content

        # Silent compression - context management happens automatically

    def _format_mcp_call_details(self, tool_name: str, tool_input: dict) -> str:
        """Format MCP tool call details for human-readable logging."""
        details = []

        # Handle specific MCP tools with meaningful summaries
        if tool_name == "confluence":
            op = tool_input.get("operation", "unknown")
            if op == "search_pages":
                details.append(f"searching for: '{tool_input.get('query', '')}'")
            elif op == "get_page":
                details.append(f"reading page ID: {tool_input.get('pageId', 'unknown')}")
            else:
                details.append(f"operation: {op}")

        elif tool_name == "github":
            op = tool_input.get("operation", "unknown")
            owner = tool_input.get("owner", "")
            repo = tool_input.get("repo", "")
            if owner and repo:
                details.append(f"repo: {owner}/{repo}")
            if op == "list_contents":
                path = tool_input.get("path", "/")
                details.append(f"listing: {path}")
            elif op == "get_file_content":
                path = tool_input.get("path", "")
                details.append(f"reading: {path}")
            elif op == "list_repos":
                details.append("listing repositories")
            elif op == "get_tree":
                details.append("getting repo tree")
            else:
                details.append(f"operation: {op}")

        elif tool_name == "docs360_search":
            details.append(f"searching: '{tool_input.get('query', '')}'")

        elif tool_name == "slack":
            op = tool_input.get("operation", "unknown")
            details.append(f"operation: {op}")
            if tool_input.get("query"):
                details.append(f"query: '{tool_input.get('query')}'")

        elif tool_name == "salesforce":
            obj = tool_input.get("object", "")
            if obj:
                details.append(f"querying: {obj}")
            if tool_input.get("soql"):
                details.append(f"SOQL: {tool_input.get('soql')[:50]}...")

        else:
            # Generic formatting for other tools
            for key in ["query", "operation", "path", "name"]:
                if key in tool_input:
                    val = str(tool_input[key])
                    if len(val) > 60:
                        val = val[:60] + "..."
                    details.append(f"{key}: {val}")

        return " | ".join(details) if details else json.dumps(tool_input)[:100]

    async def _handle_tool_use(self, tool_use: dict) -> dict:
        """Execute a tool and return the result."""
        tool_name = tool_use["name"]
        tool_input = tool_use.get("input", {})

        # Handle shell tools
        if tool_name == "bash":
            cmd = tool_input.get("command", "")
            desc = tool_input.get("description", "")
            logger.info(f"🔧 bash: {desc or cmd[:80]}")
            result = self.shell.execute(cmd, desc)

        elif tool_name == "read_file":
            path = tool_input.get("path", "")
            logger.info(f"📖 read_file: {path}")
            result = self.shell.read_file(path)

        elif tool_name == "write_file":
            path = tool_input.get("path", "")
            content_len = len(tool_input.get("content", ""))
            logger.info(f"📝 write_file: {path} ({content_len} chars)")
            result = self.shell.write_file(path, tool_input.get("content", ""))

        elif tool_name == "list_directory":
            path = tool_input.get("path", ".")
            logger.info(f"📁 list_directory: {path}")
            result = self.shell.list_directory(path)

        # Handle file store tools
        elif tool_name == "read_from_store":
            file_id = tool_input.get("file_id", "")
            offset = tool_input.get("offset", 0)
            limit = tool_input.get("limit", 50000)
            logger.info(f"📖 read_from_store: file_id={file_id}, offset={offset}")
            result = self.file_store.read(file_id, offset, limit)

        elif tool_name == "list_store_files":
            result = self.file_store.list_files()

        # Handle MCP tools
        elif tool_name.startswith("mcp_"):
            mcp_tool_name = tool_name[4:]  # Remove "mcp_" prefix
            details = self._format_mcp_call_details(mcp_tool_name, tool_input)
            logger.info(f"🌐 mcp_{mcp_tool_name}: {details}")
            result = await self.mcp.call_tool(mcp_tool_name, tool_input)

        else:
            logger.warning(f"❓ Unknown tool: {tool_name}")
            result = {"error": f"Unknown tool: {tool_name}"}

        return result

    async def run_task(self, task: str) -> str:
        """
        Run a documentation task.

        Args:
            task: Description of the documentation task

        Returns:
            Final response from the agent

        Exit conditions:
            - Task completes naturally (end_turn)
            - Maximum turns reached
            - Loop detected (repeated tool call patterns)
            - Too many consecutive errors

        Continuation:
            - If a previous run was interrupted, automatically resumes from there
            - On interruption, generates and saves a continuation prompt for next run
        """
        # Check for continuation from previous interrupted run
        continuation = self._check_continuation()
        original_task = task  # Keep original for logging

        if continuation:
            # Use continuation prompt instead of original task
            continuation_prompt = continuation.get("continuation_prompt", "")
            if continuation_prompt:
                logger.info("🔄 Resuming from continuation prompt...")
                print(f"\n📋 CONTINUING PREVIOUS TASK")
                print(f"   Original: {continuation.get('original_task', 'unknown')[:60]}...")
                print(f"   Turns used previously: {continuation.get('turns_used', 0)}")
                print(f"   Files from previous run: {continuation.get('files_written', [])}\n")

                # Use continuation as the task, but include context about it being a continuation
                task = f"""This is a CONTINUATION of a previous interrupted task.

PREVIOUS PROGRESS:
{continuation_prompt}

Please continue from where the previous run left off. Do not repeat work that was already completed.
If the task appears to be complete based on the progress summary, verify this and update the project tracking files.
"""
                # Pre-populate files written from previous run
                self._files_written = set(continuation.get("files_written", []))

        logger.info(f"Starting task: {task[:100]}...")

        # Reset tracking for new task (but keep files_written if continuing)
        self._tool_call_history = []
        self._consecutive_errors = 0
        if not continuation:
            self._files_written = set()

        # Add user message
        self.messages.append({"role": "user", "content": task})

        turns = 0
        soft_resets = 0
        max_soft_resets = 3  # Limit soft resets to prevent infinite loops

        while turns < self.config.max_turns:
            turns += 1
            logger.info(f"Turn {turns}/{self.config.max_turns}")

            # Check if context is getting too large and needs a soft reset
            if soft_resets < max_soft_resets and self._should_soft_reset():
                soft_resets += 1
                logger.warning(f"⚠️ Context size threshold reached - performing soft reset ({soft_resets}/{max_soft_resets})")

                # Get continuation prompt before clearing
                continuation_prompt = self._perform_soft_reset(original_task, turns)

                # Clear messages and start fresh with continuation
                self.messages = [
                    {
                        "role": "user",
                        "content": f"""SOFT RESET - continuing task with fresh context.

Previous task: {original_task}

CONTINUATION:
{continuation_prompt}

Please continue from where you left off. Files in the file store are still accessible using read_from_store.""",
                    }
                ]

                logger.info(f"🔄 Soft reset complete - context cleared, continuing with {len(continuation_prompt)} char summary")
                print(f"\n✅ Soft reset complete - continuing with fresh context\n")

            # Compress historical tool results to save context space
            self._compress_historical_messages(keep_recent=3)

            try:
                # Get Claude's response
                response = self.bedrock.create_message(
                    messages=self.messages,
                    system=self._get_system_prompt(),
                    tools=self.tools,
                )

                # Reset error counter on successful API call
                self._consecutive_errors = 0

            except Exception as e:
                error_str = str(e)
                
                # Check if this is a context-too-long error from Bedrock
                if "Input is too long" in error_str or "ValidationException" in error_str:
                    logger.warning(f"⚠️  Context too large for Bedrock - triggering emergency compression")
                    # Aggressive compression - keep only last 1 message
                    self._compress_historical_messages(keep_recent=1)
                    # Also clear file store to free up memory
                    self.file_store.clear()
                    logger.info("🗑️  Emergency cleanup: compressed history and cleared file store")
                    # Don't count this as a consecutive error, try again
                    continue
                
                self._consecutive_errors += 1
                logger.error(f"Bedrock API error ({self._consecutive_errors}/{self.MAX_CONSECUTIVE_ERRORS}): {e}")

                if self._consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                    return f"Task aborted: {self.MAX_CONSECUTIVE_ERRORS} consecutive API errors. Last error: {e}"

                # Wait before retrying
                import asyncio

                await asyncio.sleep(2**self._consecutive_errors)  # Exponential backoff
                continue

            # Check stop reason
            stop_reason = response.get("stop_reason")
            content = response.get("content", [])

            # Handle max_tokens - response was truncated
            if stop_reason == "max_tokens":
                logger.warning("⚠️  Response hit max_tokens limit - asking Claude to continue")

                # Check if there are incomplete tool_use blocks (no id or missing fields)
                has_incomplete_tool_use = any(block.get("type") == "tool_use" and (not block.get("id") or not block.get("name")) for block in content)

                if has_incomplete_tool_use:
                    # Remove incomplete tool_use blocks before adding to history
                    content = [b for b in content if not (b.get("type") == "tool_use" and (not b.get("id") or not b.get("name")))]
                    logger.info("Removed incomplete tool_use blocks from truncated response")

                # Add the (cleaned) assistant response
                if content:
                    self.messages.append({"role": "assistant", "content": content})
                    # Ask Claude to continue
                    self.messages.append({"role": "user", "content": "Your response was truncated. Please continue exactly where you left off."})
                continue  # Continue to next turn

            # Add assistant response to history
            self.messages.append({"role": "assistant", "content": content})

            # Extract and display text from response (Claude's thinking/reasoning)
            response_text = ""
            for block in content:
                if block.get("type") == "text":
                    text = block.get("text", "")
                    response_text += text

                    # Log and print ALL of Claude's thinking/reasoning
                    # Goes to both log file and stdout for visibility
                    if text.strip():
                        thinking_text = text.strip()
                        # Log FULL thinking to file (separate lines for readability)
                        logger.info(f"💭 Claude's thinking ({len(thinking_text)} chars):")
                        for line in thinking_text.split("\n"):
                            logger.info(f"   {line}")
                        # Also print to stdout with flush for real-time display
                        print(f"\n{'─' * 60}", flush=True)
                        print(f"💭 Claude's thinking:", flush=True)
                        print(f"{'─' * 60}", flush=True)
                        print(thinking_text, flush=True)
                        print(f"{'─' * 60}\n", flush=True)

            # If no more tool use, we're done
            if stop_reason == "end_turn":
                logger.info("✅ Task completed (end_turn)")

                # Clear continuation file on successful completion
                self._clear_continuation()

                # Print summary if files were created
                if self._files_written:
                    logger.info(f"Files created/modified: {len(self._files_written)}")
                    for f in sorted(self._files_written):
                        logger.info(f"  - {f}")

                return response_text

            # Handle tool use
            if stop_reason == "tool_use":
                tool_calls_this_turn = []
                tool_results = []
                tool_errors = 0

                for block in content:
                    if block.get("type") == "tool_use":
                        tool_id = block.get("id")
                        tool_name = block.get("name", "")
                        tool_input = block.get("input", {})

                        # Track tool call for loop detection
                        tool_calls_this_turn.append((tool_name, tool_input))

                        # Execute tool
                        result = await self._handle_tool_use(block)

                        # Track file writes
                        if tool_name == "write_file" and result.get("success"):
                            self._files_written.add(tool_input.get("path", "unknown"))

                        # Count errors
                        if not result.get("success", True) or result.get("error"):
                            tool_errors += 1

                        # Process result: store in file store, truncate only if context is tight
                        # (but don't re-store results from file store reads)
                        if tool_name not in ("read_from_store", "list_store_files"):
                            result = self._process_tool_result(result, source=tool_name)

                        tool_results.append({"type": "tool_result", "tool_use_id": tool_id, "content": json.dumps(result)})

                # Check for loop
                if self._detect_loop(tool_calls_this_turn):
                    logger.error("⚠️  Exiting due to detected loop in tool calls")

                    # Generate and save continuation for next run
                    continuation_prompt = self._generate_continuation_prompt(original_task, turns)
                    self._save_continuation(original_task, continuation_prompt, turns)

                    return (
                        f"Task interrupted: Loop detected in tool calls. "
                        f"The same pattern of {self.PATTERN_WINDOW_SIZE} tool calls "
                        f"repeated {self.MAX_REPEATED_PATTERNS} times.\n\n"
                        f"Files created: {list(self._files_written)}\n\n"
                        f"A continuation file has been saved. Run the agent again to resume."
                    )

                # Check for too many tool errors
                if tool_errors > 0:
                    self._consecutive_errors += tool_errors
                    if self._consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                        logger.error(f"Exiting due to {self._consecutive_errors} tool errors")
                        return f"Task aborted: Too many tool errors ({self._consecutive_errors})"
                else:
                    # Reset on successful tools
                    self._consecutive_errors = 0

                # Add tool results to messages
                self.messages.append({"role": "user", "content": tool_results})

            else:
                logger.warning(f"Unexpected stop reason: {stop_reason}")
                # Save continuation and exit cleanly
                logger.info(f"Exiting after {turns} turns due to unexpected stop reason")
                continuation_prompt = self._generate_continuation_prompt(original_task, turns)
                self._save_continuation(original_task, continuation_prompt, turns)
                return f"Task interrupted after {turns} turns due to unexpected stop reason: {stop_reason}"

        # Only reaches here if we actually hit max turns
        logger.warning(f"⏱️  Reached maximum turns ({self.config.max_turns})")

        # Generate and save continuation for next run
        continuation_prompt = self._generate_continuation_prompt(original_task, turns)
        self._save_continuation(original_task, continuation_prompt, turns)

        print(f"\n{'=' * 60}")
        print("TASK INTERRUPTED - CONTINUATION SAVED")
        print(f"{'=' * 60}")
        print(f"Turns used: {turns}/{self.config.max_turns}")
        print(f"Files created: {list(self._files_written)}")
        print(f"\nRun the agent again to continue from where it left off.")
        print(f"Continuation file: {self._continuation_path}")
        print(f"{'=' * 60}\n")

        return (
            f"Task incomplete - reached maximum {self.config.max_turns} turns.\n\n"
            f"Files created: {list(self._files_written)}\n\n"
            f"A continuation file has been saved to {self._continuation_path}\n"
            f"Run the agent again to resume from where it left off."
        )

    async def interactive_mode(self):
        """Run the agent in interactive mode."""
        print("\n" + "=" * 60)
        print("Natterbox Documentation Agent - Interactive Mode")
        print("=" * 60)
        print("\nType your documentation requests or 'quit' to exit.\n")

        while True:
            try:
                user_input = input("\nYou: ").strip()

                if user_input.lower() in ["quit", "exit", "q"]:
                    print("\nGoodbye!")
                    break

                if not user_input:
                    continue

                print("\nAgent: Working on it...\n")
                response = await self.run_task(user_input)
                print(f"\nAgent: {response}")

                # Clear messages for next task (optional - remove to keep context)
                self.messages = []

            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye!")
                break
            except Exception as e:
                logger.exception("Error during interactive mode")
                print(f"\nError: {e}")


# =============================================================================
# Main Entry Point
# =============================================================================

DEFAULT_CONTINUOUS_TASK = """Read .project/STATUS.md and .project/BACKLOG.md to understand the project state.
Choose the single highest-priority incomplete item and create COMPREHENSIVE documentation for it.

PRIORITIZATION: Work on items NOT marked as 'deferred' or 'complex' first. 
Leave 'deferred' and 'complex' items until all other work is complete.

DEEP RESEARCH REQUIREMENTS - YOU MUST:
1. Search Confluence for ALL related pages (try multiple search terms)
2. Find the GitHub repository and get its tree structure
3. READ ACTUAL SOURCE CODE FILES - don't just rely on READMEs
   - Read main entry points and core modules
   - Check configuration files
   - Look at API definitions
   - Review database schemas if present
4. Cross-reference information between Confluence and code
5. VERIFY that what Confluence says matches the actual implementation

DOCUMENTATION QUALITY REQUIREMENTS:
- Include architecture diagrams (ASCII art)
- Document ALL configuration options from the code
- Include code examples from actual source files
- Document API endpoints with request/response examples
- Add troubleshooting sections
- Note any discrepancies between docs and code

Write the documentation to the appropriate location in the repository.
Update .project/STATUS.md and .project/BACKLOG.md to reflect your progress."""


async def run_continuous(agent: "DocumentationAgent", task: str, max_iterations: int = 10):
    """
    Run the agent continuously with parallel task execution.

    Each iteration:
    1. PLAN: Create a TODO list of parallelizable tasks
    2. EXECUTE: Run sub-agents in parallel for each task
    3. REVIEW: Check results and update STATUS/BACKLOG
    4. COMMIT: Generate commit message and push
    """
    iteration = 0
    total_files = []

    # Create the planning coordinator
    coordinator = PlanningCoordinator(
        shell=agent.shell,
        mcp=agent.mcp,
        bedrock=agent.bedrock,
        file_store=agent.file_store,
        tools=agent.tools,
        work_dir=agent.config.work_dir,
    )

    while iteration < max_iterations:
        iteration += 1
        print(f"\n{'=' * 70}")
        print(f"  ITERATION {iteration}/{max_iterations} - PARALLEL EXECUTION MODE")
        print(f"{'=' * 70}\n")

        # Clear file store at start of each iteration to free memory
        agent.file_store.clear()
        logger.info("🗑️  Cleared file store for new iteration")

        # Run the full plan -> execute -> review cycle
        success, files_this_iteration = await coordinator.run_iteration()

        if not files_this_iteration:
            print(f"\n✅ No files modified in iteration {iteration} - work complete!")
            break

        total_files.extend(files_this_iteration)
        print(f"\n📁 Files modified this iteration: {files_this_iteration}")

        # Generate commit message and commit/push
        commit_result = await _generate_and_commit(agent, files_this_iteration, iteration)
        if not commit_result:
            print("⚠️  Commit failed, stopping continuous mode")
            break

        # Check if there's more work
        more_work = await _check_more_work(agent)
        if not more_work:
            print(f"\n✅ No more high-priority work remaining - stopping")
            break

        print(f"\n🔄 More work available, continuing to iteration {iteration + 1}...")

    # Final summary
    print(f"\n{'=' * 70}")
    print(f"  CONTINUOUS RUN COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Iterations: {iteration}")
    print(f"  Total files modified: {len(set(total_files))}")
    for f in sorted(set(total_files)):
        print(f"    - {f}")
    print(f"{'=' * 70}\n")


async def run_continuous_single(agent: "DocumentationAgent", task: str, max_iterations: int = 10):
    """
    Original single-agent continuous mode (fallback).
    Use --single flag to run this instead of parallel mode.
    """
    iteration = 0
    total_files = []

    while iteration < max_iterations:
        iteration += 1
        print(f"\n{'=' * 70}")
        print(f"  ITERATION {iteration}/{max_iterations} (SINGLE AGENT)")
        print(f"{'=' * 70}\n")

        # Clear file store at start of each iteration
        agent.file_store.clear()
        logger.info("🗑️  Cleared file store for new iteration")

        agent.messages = []
        agent._tool_call_history = []
        agent._consecutive_errors = 0
        files_before = set(agent._files_written)

        result = await agent.run_task(task)
        print(f"\n📋 Iteration {iteration} result:\n{result[:500]}..." if len(result) > 500 else f"\n📋 Iteration {iteration} result:\n{result}")

        files_this_iteration = agent._files_written - files_before

        if not files_this_iteration:
            print(f"\n✅ No files modified in iteration {iteration} - work complete!")
            break

        total_files.extend(files_this_iteration)
        print(f"\n📁 Files modified this iteration: {list(files_this_iteration)}")

        commit_result = await _generate_and_commit(agent, list(files_this_iteration), iteration)
        if not commit_result:
            print("⚠️  Commit failed, stopping continuous mode")
            break

        more_work = await _check_more_work(agent)
        if not more_work:
            print(f"\n✅ Agent indicates no more high-priority work - stopping")
            break

        print(f"\n🔄 More work available, continuing to iteration {iteration + 1}...")

    print(f"\n{'=' * 70}")
    print(f"  CONTINUOUS RUN COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Iterations: {iteration}")
    print(f"  Total files modified: {len(total_files)}")
    for f in sorted(set(total_files)):
        print(f"    - {f}")
    print(f"{'=' * 70}\n")


async def _generate_and_commit(agent: "DocumentationAgent", files: list[str], iteration: int) -> bool:
    """Generate a commit message and commit/push the changes."""

    # Ask agent to generate commit message
    commit_prompt = f"""Generate a concise git commit message for these documentation changes:
    
Files modified: {files}

The commit message should:
1. Start with a type prefix (docs:, feat:, fix:, etc.)
2. Be one line summary (max 72 chars)
3. Optionally include bullet points for details

Reply with ONLY the commit message, nothing else."""

    agent.messages = [{"role": "user", "content": commit_prompt}]

    try:
        response = agent.bedrock.create_message(
            messages=agent.messages,
            system="You are a helpful assistant that generates concise git commit messages.",
            tools=[],
        )

        commit_msg = ""
        for block in response.get("content", []):
            if block.get("type") == "text":
                commit_msg = block.get("text", "").strip()
                break

        if not commit_msg:
            commit_msg = f"docs: iteration {iteration} - update documentation"

        # Truncate if too long
        lines = commit_msg.split("\n")
        if len(lines[0]) > 72:
            lines[0] = lines[0][:69] + "..."
        commit_msg = "\n".join(lines)

        print(f"\n📝 Commit message:\n{commit_msg}")

        # Execute git commands
        work_dir = agent.config.work_dir

        # git add
        add_result = subprocess.run(["git", "add", "-A"], cwd=work_dir, capture_output=True, text=True)
        if add_result.returncode != 0:
            logger.error(f"git add failed: {add_result.stderr}")
            return False

        # git commit
        commit_result = subprocess.run(["git", "commit", "-m", commit_msg], cwd=work_dir, capture_output=True, text=True)
        if commit_result.returncode != 0:
            if "nothing to commit" in commit_result.stdout:
                print("ℹ️  Nothing to commit")
                return True
            logger.error(f"git commit failed: {commit_result.stderr}")
            return False

        print(f"✅ Committed: {commit_result.stdout.strip()}")

        # git push
        push_result = subprocess.run(["git", "push"], cwd=work_dir, capture_output=True, text=True)
        if push_result.returncode != 0:
            logger.error(f"git push failed: {push_result.stderr}")
            return False

        print(f"✅ Pushed to remote")
        return True

    except Exception as e:
        logger.error(f"Commit/push failed: {e}")
        return False


async def _check_more_work(agent: "DocumentationAgent") -> bool:
    """Check if there's more work by reading the backlog directly."""

    # Read backlog directly and check for unchecked items
    try:
        backlog_path = agent.config.work_dir / ".project" / "BACKLOG.md"
        if backlog_path.exists():
            backlog = backlog_path.read_text()

            # Count unchecked items (not deferred/complex)
            unchecked = 0
            for line in backlog.split("\n"):
                line_lower = line.lower()
                # Look for unchecked markdown checkboxes
                if "- [ ]" in line:
                    # Skip deferred or complex items
                    if "deferred" not in line_lower and "complex" not in line_lower:
                        unchecked += 1
                        logger.info(f"📋 Remaining work: {line.strip()}")

            if unchecked > 0:
                logger.info(f"📊 Found {unchecked} unchecked items in backlog (excluding deferred/complex)")
                return True
            else:
                logger.info("📊 No more unchecked items found in backlog (or all remaining are deferred/complex)")
                return False
        else:
            logger.warning("Backlog file not found")
            return False

    except Exception as e:
        logger.error(f"Error reading backlog: {e}")
        # Fall back to asking Claude
        pass

    # Fallback: ask Claude
    check_prompt = """Read .project/BACKLOG.md and count unchecked items (lines with '- [ ]').
Exclude items marked as 'deferred' or 'complex'.
Reply with ONLY one word: YES if there are unchecked items, NO if all are done."""

    agent.messages = [{"role": "user", "content": check_prompt}]

    try:
        response = agent.bedrock.create_message(
            messages=agent.messages,
            system="You are checking if more documentation work remains. Be concise.",
            tools=agent.shell.get_tool_definitions(),  # Allow file reading
        )

        # Handle tool use if agent wants to read files
        content = response.get("content", [])
        if response.get("stop_reason") == "tool_use":
            # Execute tool and get response
            for block in content:
                if block.get("type") == "tool_use":
                    result = await agent._handle_tool_use(block)
                    agent.messages.append({"role": "assistant", "content": content})
                    agent.messages.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": block.get("id"), "content": json.dumps(result)}]})

            # Get final answer
            response = agent.bedrock.create_message(
                messages=agent.messages,
                system="You are checking if more documentation work remains. Reply YES or NO.",
                tools=[],
            )
            content = response.get("content", [])

        # Extract answer
        for block in content:
            if block.get("type") == "text":
                answer = block.get("text", "").strip().upper()
                return "YES" in answer

        return False

    except Exception as e:
        logger.error(f"Check more work failed: {e}")
        return False


async def main():
    parser = argparse.ArgumentParser(
        description="Natterbox Platform Documentation Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run a specific task
    python agent.py --task "Create emergency response runbook from Confluence"
    
    # Interactive mode
    python agent.py --interactive
    
    # Continuous mode - run until done
    python agent.py --continuous
    
    # Custom configuration
    python agent.py --task "..." --region us-west-2 --model anthropic.claude-3-opus-20240229-v1:0
        """,
    )

    parser.add_argument("--task", type=str, help="Documentation task to perform")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    parser.add_argument("--continuous", "-c", action="store_true", help="Run continuously with parallel task execution")
    parser.add_argument("--single", "-s", action="store_true", help="Use single-agent mode (no parallel execution)")
    parser.add_argument("--max-iterations", type=int, default=10, help="Maximum iterations for continuous mode (default: 10)")
    parser.add_argument("--max-parallel", type=int, default=3, help="Maximum parallel sub-agents (default: 3)")
    parser.add_argument("--region", type=str, default="us-east-1", help="AWS region for Bedrock (default: us-east-1)")
    parser.add_argument("--model", type=str, default="anthropic.claude-sonnet-4-20250514-v1:0", help="Bedrock model ID")
    parser.add_argument("--mcp-url", type=str, default="https://avatar.natterbox-dev03.net/mcp/sse", help="Natterbox MCP server URL")
    parser.add_argument("--work-dir", type=str, default="/workspace", help="Working directory for the agent")
    parser.add_argument("--output-dir", type=str, default="/workspace/output", help="Output directory for generated documentation")

    args = parser.parse_args()

    # Create configuration
    config = Config(
        aws_region=args.region,
        bedrock_model_id=args.model,
        natterbox_mcp_url=args.mcp_url,
        work_dir=Path(args.work_dir),
        output_dir=Path(args.output_dir),
    )

    # Create and initialize agent
    agent = DocumentationAgent(config)
    await agent.initialize()

    # Run task or interactive mode
    if args.interactive:
        await agent.interactive_mode()
    elif args.continuous:
        task = args.task or DEFAULT_CONTINUOUS_TASK
        if args.single:
            # Single-agent continuous mode (original behavior)
            await run_continuous_single(agent, task, args.max_iterations)
        else:
            # Parallel execution mode (new default)
            # Update max parallel setting if specified
            PlanningCoordinator.MAX_PARALLEL = args.max_parallel
            await run_continuous(agent, task, args.max_iterations)
    elif args.task:
        result = await agent.run_task(args.task)
        print(result)
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
