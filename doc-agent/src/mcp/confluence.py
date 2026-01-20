"""Confluence-specific MCP operations."""

import logging
from typing import Any, Optional
from dataclasses import dataclass
from datetime import datetime

from .client import MCPClient

logger = logging.getLogger("doc-agent.mcp.confluence")


@dataclass
class ConfluencePage:
    """Confluence page information."""
    id: str
    title: str
    space_key: str
    url: str
    content: Optional[str]
    version: int
    created: Optional[datetime]
    modified: Optional[datetime]
    author: Optional[str]
    labels: list[str]
    parent_id: Optional[str]
    children_ids: list[str]
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConfluencePage":
        created = None
        modified = None
        
        if data.get("created"):
            try:
                created = datetime.fromisoformat(data["created"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass
        
        if data.get("modified"):
            try:
                modified = datetime.fromisoformat(data["modified"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass
        
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            space_key=data.get("space_key", data.get("spaceKey", "")),
            url=data.get("url", data.get("_links", {}).get("webui", "")),
            content=data.get("content", data.get("body", {}).get("storage", {}).get("value")),
            version=data.get("version", {}).get("number", 1) if isinstance(data.get("version"), dict) else data.get("version", 1),
            created=created,
            modified=modified,
            author=data.get("author", data.get("createdBy", {}).get("displayName")),
            labels=data.get("labels", []),
            parent_id=data.get("parent_id", data.get("parentId")),
            children_ids=data.get("children_ids", data.get("childrenIds", [])),
        )


@dataclass
class ConfluenceSpace:
    """Confluence space information."""
    key: str
    name: str
    description: Optional[str]
    url: str
    page_count: int
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConfluenceSpace":
        return cls(
            key=data.get("key", ""),
            name=data.get("name", ""),
            description=data.get("description", {}).get("plain", {}).get("value") if isinstance(data.get("description"), dict) else data.get("description"),
            url=data.get("url", data.get("_links", {}).get("webui", "")),
            page_count=data.get("page_count", 0),
        )


class ConfluenceClient:
    """
    Confluence-specific operations through MCP.
    
    Provides methods for searching and retrieving Confluence content.
    """
    
    def __init__(self, mcp_client: MCPClient):
        """
        Initialize the Confluence client.
        
        Args:
            mcp_client: The MCP client to use for requests
        """
        self.mcp = mcp_client
    
    async def get_space(self, space_key: str) -> Optional[ConfluenceSpace]:
        """
        Get information about a Confluence space.
        
        Args:
            space_key: The space key (e.g., "ARCH", "ENG")
            
        Returns:
            ConfluenceSpace object or None
        """
        response = await self.mcp.call_tool(
            "confluence_get_space",
            {"space_key": space_key}
        )
        
        if not response.success:
            logger.error(f"Failed to get space {space_key}: {response.error}")
            return None
        
        return ConfluenceSpace.from_dict(response.data)
    
    async def list_pages(
        self,
        space_key: str,
        exclude_labels: Optional[list[str]] = None,
        limit: int = 100,
    ) -> list[ConfluencePage]:
        """
        List pages in a Confluence space.
        
        Args:
            space_key: The space key
            exclude_labels: Labels to exclude from results
            limit: Maximum number of pages to return
            
        Returns:
            List of ConfluencePage objects
        """
        response = await self.mcp.call_tool(
            "confluence_list_pages",
            {"space_key": space_key, "limit": limit}
        )
        
        if not response.success:
            logger.error(f"Failed to list pages in {space_key}: {response.error}")
            return []
        
        pages = []
        exclude_labels = set(exclude_labels or [])
        
        for page_data in response.data or []:
            page = ConfluencePage.from_dict(page_data)
            
            # Check label exclusions
            if exclude_labels and any(label in exclude_labels for label in page.labels):
                logger.debug(f"Skipping page with excluded label: {page.title}")
                continue
            
            pages.append(page)
        
        logger.info(f"Found {len(pages)} pages in space {space_key}")
        return pages
    
    async def get_page(self, page_id: str) -> Optional[ConfluencePage]:
        """
        Get a specific Confluence page.
        
        Args:
            page_id: The page ID
            
        Returns:
            ConfluencePage object or None
        """
        response = await self.mcp.call_tool(
            "confluence_get_page",
            {"page_id": page_id}
        )
        
        if not response.success:
            logger.error(f"Failed to get page {page_id}: {response.error}")
            return None
        
        return ConfluencePage.from_dict(response.data)
    
    async def get_page_content(self, page_id: str) -> Optional[str]:
        """
        Get the content of a Confluence page.
        
        Args:
            page_id: The page ID
            
        Returns:
            Page content as HTML or None
        """
        page = await self.get_page(page_id)
        return page.content if page else None
    
    async def search(
        self,
        query: str,
        space_key: Optional[str] = None,
        limit: int = 50,
    ) -> list[ConfluencePage]:
        """
        Search Confluence content.
        
        Args:
            query: Search query (CQL or text)
            space_key: Optional space to limit search
            limit: Maximum results
            
        Returns:
            List of matching pages
        """
        args = {"query": query, "limit": limit}
        if space_key:
            args["space_key"] = space_key
        
        response = await self.mcp.call_tool("confluence_search", args)
        
        if not response.success:
            logger.error(f"Search failed: {response.error}")
            return []
        
        return [ConfluencePage.from_dict(p) for p in response.data or []]
    
    async def get_page_tree(
        self,
        space_key: str,
        root_page_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Get the page tree structure for a space.
        
        Args:
            space_key: The space key
            root_page_id: Optional root page to start from
            
        Returns:
            Hierarchical tree of pages
        """
        args = {"space_key": space_key}
        if root_page_id:
            args["root_page_id"] = root_page_id
        
        response = await self.mcp.call_tool("confluence_get_tree", args)
        
        if not response.success:
            logger.error(f"Failed to get page tree: {response.error}")
            return []
        
        return response.data or []
    
    async def get_pages_by_label(
        self,
        label: str,
        space_key: Optional[str] = None,
    ) -> list[ConfluencePage]:
        """
        Get all pages with a specific label.
        
        Args:
            label: The label to search for
            space_key: Optional space to limit search
            
        Returns:
            List of pages with the label
        """
        cql = f'label = "{label}"'
        if space_key:
            cql += f' and space = "{space_key}"'
        
        return await self.search(cql)
    
    async def extract_architecture_docs(
        self,
        space_key: str,
    ) -> list[ConfluencePage]:
        """
        Extract architecture-related documentation from a space.
        
        Searches for pages with architecture-related labels or titles.
        """
        architecture_labels = [
            "architecture",
            "design",
            "adr",
            "technical-design",
            "system-design",
        ]
        
        pages = []
        for label in architecture_labels:
            label_pages = await self.get_pages_by_label(label, space_key)
            pages.extend(label_pages)
        
        # Also search titles
        title_searches = [
            "architecture",
            "design document",
            "technical specification",
        ]
        
        for term in title_searches:
            search_pages = await self.search(f'title ~ "{term}"', space_key)
            pages.extend(search_pages)
        
        # Deduplicate by ID
        seen_ids = set()
        unique_pages = []
        for page in pages:
            if page.id not in seen_ids:
                seen_ids.add(page.id)
                unique_pages.append(page)
        
        return unique_pages
