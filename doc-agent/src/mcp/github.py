"""GitHub-specific MCP operations."""

import logging
import re
from typing import Any, Optional
from dataclasses import dataclass

from .client import MCPClient

logger = logging.getLogger("doc-agent.mcp.github")


@dataclass
class Repository:
    """GitHub repository information."""
    name: str
    full_name: str
    description: Optional[str]
    url: str
    default_branch: str
    language: Optional[str]
    languages: dict[str, int]
    topics: list[str]
    visibility: str
    archived: bool
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Repository":
        return cls(
            name=data.get("name", ""),
            full_name=data.get("full_name", ""),
            description=data.get("description"),
            url=data.get("html_url", data.get("url", "")),
            default_branch=data.get("default_branch", "main"),
            language=data.get("language"),
            languages=data.get("languages", {}),
            topics=data.get("topics", []),
            visibility=data.get("visibility", "private"),
            archived=data.get("archived", False),
        )


@dataclass
class FileContent:
    """Content of a file from GitHub."""
    path: str
    content: str
    sha: str
    size: int
    url: str
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileContent":
        return cls(
            path=data.get("path", ""),
            content=data.get("content", ""),
            sha=data.get("sha", ""),
            size=data.get("size", 0),
            url=data.get("html_url", data.get("url", "")),
        )


class GitHubClient:
    """
    GitHub-specific operations through MCP.
    
    Provides methods for discovering repositories, reading files,
    and extracting repository metadata.
    """
    
    def __init__(self, mcp_client: MCPClient):
        """
        Initialize the GitHub client.
        
        Args:
            mcp_client: The MCP client to use for requests
        """
        self.mcp = mcp_client
    
    async def list_repositories(
        self,
        organization: str,
        exclude_patterns: Optional[list[str]] = None,
    ) -> list[Repository]:
        """
        List repositories in an organization.
        
        Args:
            organization: GitHub organization name
            exclude_patterns: Regex patterns for repos to exclude
            
        Returns:
            List of Repository objects
        """
        response = await self.mcp.call_tool(
            "github_list_repos",
            {"organization": organization}
        )
        
        if not response.success:
            logger.error(f"Failed to list repos: {response.error}")
            return []
        
        repos = []
        exclude_patterns = exclude_patterns or []
        compiled_patterns = [re.compile(p) for p in exclude_patterns]
        
        for repo_data in response.data or []:
            repo = Repository.from_dict(repo_data)
            
            # Skip archived repos
            if repo.archived:
                logger.debug(f"Skipping archived repo: {repo.name}")
                continue
            
            # Check exclusion patterns
            excluded = False
            for pattern in compiled_patterns:
                if pattern.match(repo.name):
                    logger.debug(f"Skipping excluded repo: {repo.name}")
                    excluded = True
                    break
            
            if not excluded:
                repos.append(repo)
        
        logger.info(f"Found {len(repos)} repositories in {organization}")
        return repos
    
    async def get_repository(self, owner: str, repo: str) -> Optional[Repository]:
        """
        Get details for a specific repository.
        
        Args:
            owner: Repository owner (org or user)
            repo: Repository name
            
        Returns:
            Repository object or None
        """
        response = await self.mcp.call_tool(
            "github_get_repo",
            {"owner": owner, "repo": repo}
        )
        
        if not response.success:
            logger.error(f"Failed to get repo {owner}/{repo}: {response.error}")
            return None
        
        return Repository.from_dict(response.data)
    
    async def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: Optional[str] = None,
    ) -> Optional[FileContent]:
        """
        Get the content of a file from a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: Path to the file
            ref: Git ref (branch, tag, commit)
            
        Returns:
            FileContent object or None
        """
        args = {"owner": owner, "repo": repo, "path": path}
        if ref:
            args["ref"] = ref
        
        response = await self.mcp.call_tool("github_get_file", args)
        
        if not response.success:
            logger.debug(f"Failed to get file {path}: {response.error}")
            return None
        
        return FileContent.from_dict(response.data)
    
    async def search_files(
        self,
        owner: str,
        repo: str,
        patterns: list[str],
        ref: Optional[str] = None,
    ) -> list[str]:
        """
        Search for files matching patterns in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            patterns: Glob patterns to match
            ref: Git ref (branch, tag, commit)
            
        Returns:
            List of matching file paths
        """
        args = {
            "owner": owner,
            "repo": repo,
            "patterns": patterns,
        }
        if ref:
            args["ref"] = ref
        
        response = await self.mcp.call_tool("github_search_files", args)
        
        if not response.success:
            logger.error(f"Failed to search files: {response.error}")
            return []
        
        return response.data or []
    
    async def get_tree(
        self,
        owner: str,
        repo: str,
        path: str = "",
        ref: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Get the directory tree of a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: Path to start from (empty for root)
            ref: Git ref (branch, tag, commit)
            
        Returns:
            List of tree entries
        """
        args = {"owner": owner, "repo": repo, "path": path}
        if ref:
            args["ref"] = ref
        
        response = await self.mcp.call_tool("github_get_tree", args)
        
        if not response.success:
            logger.error(f"Failed to get tree: {response.error}")
            return []
        
        return response.data or []
    
    async def get_readme(self, owner: str, repo: str) -> Optional[str]:
        """
        Get the README content for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            README content or None
        """
        # Try common README locations
        readme_paths = ["README.md", "readme.md", "README", "README.rst"]
        
        for path in readme_paths:
            content = await self.get_file_content(owner, repo, path)
            if content:
                return content.content
        
        return None
    
    async def get_package_json(self, owner: str, repo: str) -> Optional[dict[str, Any]]:
        """Get package.json content if it exists."""
        content = await self.get_file_content(owner, repo, "package.json")
        if content:
            import json
            try:
                return json.loads(content.content)
            except json.JSONDecodeError:
                return None
        return None
    
    async def get_openapi_spec(
        self,
        owner: str,
        repo: str,
    ) -> Optional[dict[str, Any]]:
        """
        Find and return OpenAPI specification from a repository.
        
        Searches common locations for OpenAPI/Swagger specs.
        """
        spec_paths = [
            "openapi.yaml",
            "openapi.json",
            "swagger.yaml",
            "swagger.json",
            "api/openapi.yaml",
            "api/openapi.json",
            "docs/openapi.yaml",
            "docs/openapi.json",
        ]
        
        for path in spec_paths:
            content = await self.get_file_content(owner, repo, path)
            if content:
                import json
                import yaml
                try:
                    if path.endswith(".json"):
                        return json.loads(content.content)
                    else:
                        return yaml.safe_load(content.content)
                except Exception as e:
                    logger.warning(f"Failed to parse {path}: {e}")
        
        return None
