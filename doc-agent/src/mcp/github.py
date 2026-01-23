"""GitHub operations via the Natterbox MCP server."""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from .client import MCPClient

logger = logging.getLogger("doc-agent.mcp.github")


@dataclass
class Repository:
    """GitHub repository information."""
    name: str
    full_name: str
    description: str = ""
    url: str = ""
    default_branch: str = "main"
    language: str = ""
    topics: list[str] = field(default_factory=list)
    archived: bool = False
    
    @classmethod
    def from_dict(cls, data: dict) -> "Repository":
        return cls(
            name=data.get("name", ""),
            full_name=data.get("full_name", ""),
            description=data.get("description") or "",
            url=data.get("html_url") or data.get("url", ""),
            default_branch=data.get("default_branch", "main"),
            language=data.get("language") or "",
            topics=data.get("topics", []),
            archived=data.get("archived", False),
        )


@dataclass
class FileContent:
    """Content of a file from GitHub."""
    path: str
    content: str
    sha: str = ""
    size: int = 0
    
    @classmethod
    def from_dict(cls, data: dict) -> "FileContent":
        return cls(
            path=data.get("path", ""),
            content=data.get("content", ""),
            sha=data.get("sha", ""),
            size=data.get("size", 0),
        )


class GitHubClient:
    """
    GitHub operations via the Natterbox MCP server.
    
    Uses the 'github' MCP tool with operation parameter.
    """
    
    TOOL_NAME = "github"
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp = mcp_client
    
    async def list_repositories(
        self,
        org: Optional[str] = None,
        per_page: int = 100,
        max_pages: int = 20,
    ) -> list[Repository]:
        """
        List repositories for an organization or the authenticated user.
        
        Handles pagination to fetch all repos (up to max_pages).
        
        Args:
            org: Organization name (optional, lists user repos if not provided)
            per_page: Results per page (max 100)
            max_pages: Maximum pages to fetch (default 20 = up to 2000 repos)
            
        Returns:
            List of Repository objects
        """
        all_repos = []
        page = 1
        
        while page <= max_pages:
            args = {
                "operation": "list_repos",
                "perPage": per_page,
                "page": page,
            }
            if org:
                args["org"] = org
            
            response = await self.mcp.call_tool(self.TOOL_NAME, args)
            
            if not response.success:
                logger.error(f"Failed to list repositories page {page}: {response.error}")
                break
            
            repos = []
            raw_data = response.data
            has_more = False
            
            # Handle nested response format with pagination info
            if isinstance(raw_data, dict):
                # Check for API error
                if "error" in raw_data:
                    logger.error(f"GitHub API error: {raw_data['error']}")
                    break
                
                # Extract pagination info
                pagination = raw_data.get("pagination", {})
                has_more = pagination.get("hasMore", False)
                
                # Extract repositories
                if "data" in raw_data and isinstance(raw_data["data"], dict):
                    data = raw_data["data"].get("repositories", [])
                elif "repositories" in raw_data:
                    data = raw_data["repositories"]
                else:
                    data = []
            elif isinstance(raw_data, list):
                data = raw_data
            else:
                data = []
            
            if isinstance(data, list):
                for repo_data in data:
                    try:
                        repos.append(Repository.from_dict(repo_data))
                    except Exception as e:
                        logger.warning(f"Failed to parse repository: {e}")
            
            if not repos:
                # No more results
                break
            
            all_repos.extend(repos)
            logger.debug(f"Fetched page {page}: {len(repos)} repos (total: {len(all_repos)}), hasMore: {has_more}")
            
            # Check if there are more pages
            if not has_more and len(repos) < per_page:
                # Last page
                break
            
            page += 1
        
        logger.info(f"Listed {len(all_repos)} total repositories for {org or 'authenticated user'}")
        return all_repos
    
    async def get_repository(
        self,
        owner: str,
        repo: str,
    ) -> Optional[Repository]:
        """Get repository details."""
        response = await self.mcp.call_tool(self.TOOL_NAME, {
            "operation": "get_repo",
            "owner": owner,
            "repo": repo,
        })
        
        if not response.success:
            logger.error(f"Failed to get repository: {response.error}")
            return None
        
        if response.data:
            return Repository.from_dict(response.data)
        return None
    
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
            path: Path to file within repository
            ref: Branch, tag, or commit (default: repo's default branch)
            
        Returns:
            FileContent or None if not found
        """
        args = {
            "operation": "get_file_content",
            "owner": owner,
            "repo": repo,
            "path": path,
        }
        if ref:
            args["ref"] = ref
        
        response = await self.mcp.call_tool(self.TOOL_NAME, args)
        
        if not response.success:
            logger.debug(f"Failed to get file {path}: {response.error}")
            return None
        
        if response.data:
            return FileContent.from_dict(response.data)
        return None
    
    async def list_contents(
        self,
        owner: str,
        repo: str,
        path: str = "",
        ref: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        List contents of a directory in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: Directory path (empty for root)
            ref: Branch, tag, or commit
            
        Returns:
            List of content items (files and directories)
        """
        args = {
            "operation": "list_contents",
            "owner": owner,
            "repo": repo,
        }
        if path:
            args["path"] = path
        if ref:
            args["ref"] = ref
        
        response = await self.mcp.call_tool(self.TOOL_NAME, args)
        
        if not response.success:
            logger.error(f"Failed to list contents: {response.error}")
            return []
        
        if isinstance(response.data, list):
            return response.data
        return []
    
    async def get_tree(
        self,
        owner: str,
        repo: str,
        ref: Optional[str] = None,
        recursive: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Get the full tree of a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            ref: Branch, tag, or commit
            recursive: Whether to get tree recursively
            
        Returns:
            List of tree items (all files and directories)
        """
        args = {
            "operation": "get_tree",
            "owner": owner,
            "repo": repo,
            "recursive": "true" if recursive else "false",
        }
        if ref:
            args["ref"] = ref
        
        response = await self.mcp.call_tool(self.TOOL_NAME, args)
        
        if not response.success:
            logger.error(f"Failed to get tree: {response.error}")
            return []
        
        if isinstance(response.data, dict) and "tree" in response.data:
            return response.data["tree"]
        if isinstance(response.data, list):
            return response.data
        return []
    
    async def get_readme(
        self,
        owner: str,
        repo: str,
    ) -> Optional[str]:
        """Get the README content for a repository."""
        # Try common README filenames
        for filename in ["README.md", "README.rst", "README.txt", "README"]:
            content = await self.get_file_content(owner, repo, filename)
            if content:
                return content.content
        return None
    
    async def get_package_json(
        self,
        owner: str,
        repo: str,
    ) -> Optional[dict[str, Any]]:
        """Get package.json for a Node.js repository."""
        import json
        content = await self.get_file_content(owner, repo, "package.json")
        if content and content.content:
            try:
                return json.loads(content.content)
            except json.JSONDecodeError:
                logger.warning(f"Invalid package.json in {owner}/{repo}")
        return None
    
    async def get_openapi_spec(
        self,
        owner: str,
        repo: str,
    ) -> Optional[dict[str, Any]]:
        """Find and return OpenAPI/Swagger specification."""
        import json
        import yaml
        
        # Common OpenAPI file locations
        spec_paths = [
            "openapi.yaml", "openapi.yml", "openapi.json",
            "swagger.yaml", "swagger.yml", "swagger.json",
            "api/openapi.yaml", "api/openapi.yml", "api/openapi.json",
            "docs/openapi.yaml", "docs/openapi.yml",
        ]
        
        for path in spec_paths:
            content = await self.get_file_content(owner, repo, path)
            if content and content.content:
                try:
                    if path.endswith(".json"):
                        return json.loads(content.content)
                    else:
                        return yaml.safe_load(content.content)
                except Exception as e:
                    logger.warning(f"Failed to parse {path}: {e}")
        
        return None
    
    async def list_branches(
        self,
        owner: str,
        repo: str,
    ) -> list[str]:
        """List branches in a repository."""
        response = await self.mcp.call_tool(self.TOOL_NAME, {
            "operation": "list_branches",
            "owner": owner,
            "repo": repo,
        })
        
        if not response.success:
            logger.error(f"Failed to list branches: {response.error}")
            return []
        
        if isinstance(response.data, list):
            return [b.get("name", "") for b in response.data if isinstance(b, dict)]
        return []
    
    async def search_files(
        self,
        owner: str,
        repo: str,
        pattern: str,
    ) -> list[str]:
        """
        Search for files matching a pattern in the repository tree.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pattern: Glob pattern to match (e.g., "*.md", "src/**/*.py")
            
        Returns:
            List of matching file paths
        """
        import fnmatch
        
        tree = await self.get_tree(owner, repo)
        matches = []
        
        for item in tree:
            if item.get("type") == "blob":  # Files only
                path = item.get("path", "")
                if fnmatch.fnmatch(path, pattern):
                    matches.append(path)
        
        return matches
