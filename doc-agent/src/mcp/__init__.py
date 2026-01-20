"""MCP client for accessing Natterbox data sources."""

from .client import MCPClient, MCPOAuthConfig, MCPResponse
from .github import GitHubClient
from .confluence import ConfluenceClient
from .jira import JiraClient

__all__ = [
    "MCPClient",
    "MCPOAuthConfig",
    "MCPResponse",
    "GitHubClient",
    "ConfluenceClient",
    "JiraClient",
]
