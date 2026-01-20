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
import json
import logging
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

import boto3
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("documentation-agent")


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class Config:
    """Agent configuration."""
    
    # AWS Bedrock settings
    aws_region: str = field(default_factory=lambda: os.environ.get("AWS_REGION", "us-east-1"))
    bedrock_model_id: str = field(default_factory=lambda: os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-sonnet-4-20250514-v1:0"))
    max_tokens: int = 8192
    
    # MCP Server settings
    natterbox_mcp_url: str = field(default_factory=lambda: os.environ.get("NATTERBOX_MCP_URL", "https://avatar.natterbox-dev03.net/mcp/sse"))
    
    # Working directories
    work_dir: Path = field(default_factory=lambda: Path(os.environ.get("WORK_DIR", "/workspace")))
    output_dir: Path = field(default_factory=lambda: Path(os.environ.get("OUTPUT_DIR", "/workspace/output")))
    
    # Tool settings
    shell_timeout: int = 300  # seconds
    
    # Conversation settings
    max_turns: int = 50
    
    def __post_init__(self):
        self.work_dir = Path(self.work_dir)
        self.output_dir = Path(self.output_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Shell Tool
# =============================================================================

class ShellTool:
    """
    Provides shell command execution capabilities.
    Designed to run in a Docker container for isolation.
    """
    
    def __init__(self, work_dir: Path, timeout: int = 300):
        self.work_dir = work_dir
        self.timeout = timeout
        self.work_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(self, command: str, description: str = "") -> dict[str, Any]:
        """
        Execute a shell command and return the result.
        
        Args:
            command: The bash command to execute
            description: Human-readable description of why this command is being run
            
        Returns:
            Dict with 'returncode', 'stdout', 'stderr', and 'success' keys
        """
        logger.info(f"Shell: {description or command[:100]}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env={**os.environ, "HOME": str(self.work_dir)},
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
        """Read a file from the workspace."""
        try:
            file_path = self.work_dir / path if not path.startswith("/") else Path(path)
            content = file_path.read_text()
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def write_file(self, path: str, content: str) -> dict[str, Any]:
        """Write content to a file in the workspace."""
        try:
            file_path = self.work_dir / path if not path.startswith("/") else Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            return {"success": True, "path": str(file_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_directory(self, path: str = ".") -> dict[str, Any]:
        """List contents of a directory."""
        try:
            dir_path = self.work_dir / path if not path.startswith("/") else Path(path)
            items = []
            for item in dir_path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                })
            return {"success": True, "items": items}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_tool_definitions(self) -> list[dict]:
        """Return tool definitions for Claude."""
        return [
            {
                "name": "bash",
                "description": "Execute a bash command in the workspace. Use for running scripts, installing packages, git operations, file manipulation, etc.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash command to execute"
                        },
                        "description": {
                            "type": "string",
                            "description": "Brief description of why this command is being run"
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "read_file",
                "description": "Read the contents of a file from the workspace.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file (relative to workspace or absolute)"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "Write content to a file in the workspace. Creates parent directories if needed.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file (relative to workspace or absolute)"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        }
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "list_directory",
                "description": "List the contents of a directory in the workspace.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the directory (relative to workspace or absolute)",
                            "default": "."
                        }
                    }
                }
            }
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
                    }
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
                    }
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
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {
                                "name": "documentation-agent",
                                "version": "1.0.0"
                            }
                        }
                    }
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
                response = await client.post(
                    self._message_endpoint,
                    headers=headers,
                    json={
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/list",
                        "params": {}
                    }
                )
                
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
        logger.info(f"MCP tool call: {name}")
        
        # Proactively refresh token if needed
        await self._ensure_valid_token()
        
        headers = {"Authorization": f"Bearer {self._access_token}"}
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self._message_endpoint,
                    headers=headers,
                    json={
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {
                            "name": name,
                            "arguments": arguments
                        }
                    }
                )
                
                if response.status_code == 401:
                    # Try refresh and retry
                    if await self._refresh_access_token():
                        headers = {"Authorization": f"Bearer {self._access_token}"}
                        response = await client.post(
                            self._message_endpoint,
                            headers=headers,
                            json={
                                "jsonrpc": "2.0",
                                "id": 3,
                                "method": "tools/call",
                                "params": {
                                    "name": name,
                                    "arguments": arguments
                                }
                            }
                        )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "result": result.get("result", {})
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_tool_definitions(self) -> list[dict]:
        """Return tool definitions for Claude in Bedrock format."""
        definitions = []
        for name, tool in self.tools.items():
            definitions.append({
                "name": f"mcp_{name}",
                "description": tool.get("description", f"MCP tool: {name}"),
                "input_schema": tool.get("inputSchema", {"type": "object", "properties": {}})
            })
        return definitions


# =============================================================================
# Bedrock Client
# =============================================================================

class BedrockClient:
    """Client for AWS Bedrock Claude API with tool use support."""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=config.aws_region
        )
        
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
        """
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.config.max_tokens,
            "system": system,
            "messages": messages,
            "tools": tools,
        }
        
        response = self.client.invoke_model(
            modelId=self.config.bedrock_model_id,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json",
        )
        
        response_body = json.loads(response["body"].read())
        return response_body


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
    PATTERN_WINDOW_SIZE = 5   # Look at last N tool calls for pattern detection
    
    SYSTEM_PROMPT = """You are an expert documentation engineer helping to create and maintain platform documentation for Natterbox.

You have access to the following tool categories:

1. **Shell Tools** (bash, read_file, write_file, list_directory):
   - Execute commands in the workspace
   - Create and edit documentation files
   - Manage the file system

2. **MCP Tools** (prefixed with mcp_):
   - mcp_confluence: Search and read Confluence wiki pages
   - mcp_github: Access GitHub repositories and files
   - mcp_docs360_search: Search Document360 knowledge base
   - mcp_salesforce: Query Salesforce data
   - mcp_slack: Access Slack channels and messages
   - And more...

## Your Workflow

1. **Research Phase**: Use MCP tools to gather information from:
   - Confluence for architecture docs, runbooks, processes
   - GitHub for repository structure and code
   - Document360 for customer-facing documentation

2. **Analysis Phase**: Synthesize information and plan documentation structure

3. **Creation Phase**: Use shell tools to create markdown files in the workspace

4. **Output Phase**: Organize final documentation in /workspace/output/

## Documentation Standards

- Use clear markdown formatting
- Include source references (Confluence links, etc.)
- Add "Last Updated" dates
- Use tables for structured information
- Include code examples where relevant

## Current Date: {date}

## Important Notes

- Always verify information from multiple sources when possible
- Keep documentation concise but comprehensive
- Focus on actionable, practical content
- Reference original sources for detailed information

## Task Completion

When you have completed the requested task:
1. Provide a clear summary of what was accomplished
2. List all files that were created or modified
3. Explicitly state "Task complete" or "Documentation has been created"
4. Suggest next steps if applicable

If you encounter issues that prevent completion:
1. Explain what went wrong
2. Describe what was partially completed
3. Suggest how to resolve the issue
"""

    def __init__(self, config: Config):
        self.config = config
        self.shell = ShellTool(config.work_dir, config.shell_timeout)
        self.mcp = MCPClient(config.natterbox_mcp_url)
        self.bedrock = BedrockClient(config)
        self.messages: list[dict] = []
        self.tools: list[dict] = []
        
        # Tracking for loop detection and error handling
        self._tool_call_history: list[str] = []  # Hashes of recent tool calls
        self._consecutive_errors = 0
        self._files_written: set[str] = set()  # Track created files
        
    async def initialize(self) -> bool:
        """Initialize the agent and connect to services."""
        logger.info("Initializing documentation agent...")
        
        # Initialize shell tools
        self.tools.extend(self.shell.get_tool_definitions())
        logger.info(f"Loaded {len(self.shell.get_tool_definitions())} shell tools")
        
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
            self._tool_call_history = self._tool_call_history[-self.PATTERN_WINDOW_SIZE * 3:]
        
        # Check for repeated patterns
        if len(self._tool_call_history) >= self.PATTERN_WINDOW_SIZE * 2:
            recent = self._tool_call_history[-self.PATTERN_WINDOW_SIZE:]
            
            # Count how many times this exact pattern appears
            pattern_count = 0
            for i in range(len(self._tool_call_history) - self.PATTERN_WINDOW_SIZE + 1):
                window = self._tool_call_history[i:i + self.PATTERN_WINDOW_SIZE]
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
    
    async def _handle_tool_use(self, tool_use: dict) -> dict:
        """Execute a tool and return the result."""
        tool_name = tool_use["name"]
        tool_input = tool_use.get("input", {})
        
        # Handle shell tools
        if tool_name == "bash":
            result = self.shell.execute(
                tool_input.get("command", ""),
                tool_input.get("description", "")
            )
        elif tool_name == "read_file":
            result = self.shell.read_file(tool_input.get("path", ""))
        elif tool_name == "write_file":
            result = self.shell.write_file(
                tool_input.get("path", ""),
                tool_input.get("content", "")
            )
        elif tool_name == "list_directory":
            result = self.shell.list_directory(tool_input.get("path", "."))
        
        # Handle MCP tools
        elif tool_name.startswith("mcp_"):
            mcp_tool_name = tool_name[4:]  # Remove "mcp_" prefix
            result = await self.mcp.call_tool(mcp_tool_name, tool_input)
        
        else:
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
        """
        logger.info(f"Starting task: {task[:100]}...")
        
        # Reset tracking for new task
        self._tool_call_history = []
        self._consecutive_errors = 0
        self._files_written = set()
        
        # Add user message
        self.messages.append({
            "role": "user",
            "content": task
        })
        
        turns = 0
        while turns < self.config.max_turns:
            turns += 1
            logger.info(f"Turn {turns}/{self.config.max_turns}")
            
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
                self._consecutive_errors += 1
                logger.error(f"Bedrock API error ({self._consecutive_errors}/{self.MAX_CONSECUTIVE_ERRORS}): {e}")
                
                if self._consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                    return f"Task aborted: {self.MAX_CONSECUTIVE_ERRORS} consecutive API errors. Last error: {e}"
                
                # Wait before retrying
                import asyncio
                await asyncio.sleep(2 ** self._consecutive_errors)  # Exponential backoff
                continue
            
            # Check stop reason
            stop_reason = response.get("stop_reason")
            content = response.get("content", [])
            
            # Add assistant response to history
            self.messages.append({
                "role": "assistant",
                "content": content
            })
            
            # Extract text from response
            response_text = ""
            for block in content:
                if block.get("type") == "text":
                    response_text += block.get("text", "")
            
            # If no more tool use, we're done
            if stop_reason == "end_turn":
                logger.info("Task completed (end_turn)")
                
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
                        
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": json.dumps(result)
                        })
                
                # Check for loop
                if self._detect_loop(tool_calls_this_turn):
                    logger.error("Exiting due to detected loop in tool calls")
                    return (
                        f"Task aborted: Loop detected in tool calls. "
                        f"The same pattern of {self.PATTERN_WINDOW_SIZE} tool calls "
                        f"repeated {self.MAX_REPEATED_PATTERNS} times.\n\n"
                        f"Files created before abort: {list(self._files_written)}"
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
                self.messages.append({
                    "role": "user",
                    "content": tool_results
                })
                
            else:
                logger.warning(f"Unexpected stop reason: {stop_reason}")
                break
        
        logger.warning("Reached maximum turns")
        return (
            f"Task incomplete - reached maximum {self.config.max_turns} turns.\n\n"
            f"Files created: {list(self._files_written)}"
        )
    
    async def interactive_mode(self):
        """Run the agent in interactive mode."""
        print("\n" + "="*60)
        print("Natterbox Documentation Agent - Interactive Mode")
        print("="*60)
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
    
    # Custom configuration
    python agent.py --task "..." --region us-west-2 --model anthropic.claude-3-opus-20240229-v1:0
        """
    )
    
    parser.add_argument(
        "--task",
        type=str,
        help="Documentation task to perform"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--region",
        type=str,
        default="us-east-1",
        help="AWS region for Bedrock (default: us-east-1)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="anthropic.claude-sonnet-4-20250514-v1:0",
        help="Bedrock model ID"
    )
    parser.add_argument(
        "--mcp-url",
        type=str,
        default="https://avatar.natterbox-dev03.net/mcp/sse",
        help="Natterbox MCP server URL"
    )
    parser.add_argument(
        "--work-dir",
        type=str,
        default="/workspace",
        help="Working directory for the agent"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/workspace/output",
        help="Output directory for generated documentation"
    )
    
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
    elif args.task:
        result = await agent.run_task(args.task)
        print(result)
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
