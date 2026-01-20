"""Confluence operations via the Natterbox MCP server."""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from .client import MCPClient

logger = logging.getLogger("doc-agent.mcp.confluence")


@dataclass
class ConfluencePage:
    """Confluence page information."""
    id: str
    title: str
    space_key: str = ""
    url: str = ""
    body: str = ""
    labels: list[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    version: int = 1
    
    @classmethod
    def from_dict(cls, data: dict) -> "ConfluencePage":
        # Handle various response formats
        labels = []
        if "labels" in data:
            label_data = data["labels"]
            if isinstance(label_data, list):
                labels = [l.get("name", l) if isinstance(l, dict) else str(l) for l in label_data]
            elif isinstance(label_data, dict) and "results" in label_data:
                labels = [l.get("name", "") for l in label_data["results"]]
        
        body = ""
        if "body" in data:
            body_data = data["body"]
            if isinstance(body_data, dict):
                # Try storage format first, then view
                body = body_data.get("storage", {}).get("value", "")
                if not body:
                    body = body_data.get("view", {}).get("value", "")
            elif isinstance(body_data, str):
                body = body_data
        
        return cls(
            id=str(data.get("id", "")),
            title=data.get("title", ""),
            space_key=data.get("spaceKey", data.get("space", {}).get("key", "")),
            url=data.get("_links", {}).get("webui", data.get("url", "")),
            body=body,
            labels=labels,
            parent_id=data.get("parentId"),
            version=data.get("version", {}).get("number", 1) if isinstance(data.get("version"), dict) else 1,
        )


@dataclass
class ConfluenceSpace:
    """Confluence space information."""
    key: str
    name: str
    description: str = ""
    url: str = ""
    
    @classmethod
    def from_dict(cls, data: dict) -> "ConfluenceSpace":
        desc = data.get("description", {})
        if isinstance(desc, dict):
            desc = desc.get("plain", {}).get("value", "")
        
        return cls(
            key=data.get("key", ""),
            name=data.get("name", ""),
            description=desc if isinstance(desc, str) else "",
            url=data.get("_links", {}).get("webui", ""),
        )


class ConfluenceClient:
    """
    Confluence operations via the Natterbox MCP server.
    
    Uses the 'confluence' MCP tool with operation parameter.
    """
    
    TOOL_NAME = "confluence"
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp = mcp_client
    
    async def search(
        self,
        query: str,
        space_key: Optional[str] = None,
    ) -> list[ConfluencePage]:
        """
        Search for Confluence pages.
        
        Args:
            query: Search query (CQL or natural language)
            space_key: Optional space to limit search
            
        Returns:
            List of matching pages
        """
        search_query = query
        if space_key:
            search_query = f'space = "{space_key}" AND ({query})'
        
        response = await self.mcp.call_tool(self.TOOL_NAME, {
            "operation": "search_pages",
            "query": search_query,
        })
        
        if not response.success:
            logger.error(f"Search failed: {response.error}")
            return []
        
        pages = []
        data = response.data
        
        # Handle various response formats
        results = []
        if isinstance(data, list):
            results = data
        elif isinstance(data, dict):
            results = data.get("results", data.get("pages", []))
        
        for page_data in results:
            try:
                pages.append(ConfluencePage.from_dict(page_data))
            except Exception as e:
                logger.warning(f"Failed to parse page: {e}")
        
        return pages
    
    async def get_page(
        self,
        page_id: str,
    ) -> Optional[ConfluencePage]:
        """
        Get a specific Confluence page by ID.
        
        Args:
            page_id: Page ID
            
        Returns:
            ConfluencePage or None
        """
        response = await self.mcp.call_tool(self.TOOL_NAME, {
            "operation": "get_page",
            "pageId": str(page_id),
        })
        
        if not response.success:
            logger.error(f"Get page failed: {response.error}")
            return None
        
        if response.data:
            return ConfluencePage.from_dict(response.data)
        return None
    
    async def get_page_content(
        self,
        page_id: str,
    ) -> Optional[str]:
        """Get page content as plain text (HTML stripped)."""
        page = await self.get_page(page_id)
        if page:
            return self._strip_html(page.body)
        return None
    
    async def list_spaces(self) -> list[ConfluenceSpace]:
        """List all accessible Confluence spaces."""
        response = await self.mcp.call_tool(self.TOOL_NAME, {
            "operation": "list_spaces",
        })
        
        if not response.success:
            logger.error(f"List spaces failed: {response.error}")
            return []
        
        spaces = []
        data = response.data
        
        results = []
        if isinstance(data, list):
            results = data
        elif isinstance(data, dict):
            results = data.get("results", data.get("spaces", []))
        
        for space_data in results:
            try:
                spaces.append(ConfluenceSpace.from_dict(space_data))
            except Exception as e:
                logger.warning(f"Failed to parse space: {e}")
        
        return spaces
    
    async def get_space(
        self,
        space_key: str,
    ) -> Optional[ConfluenceSpace]:
        """Get space information."""
        response = await self.mcp.call_tool(self.TOOL_NAME, {
            "operation": "get_space",
            "spaceKey": space_key,
        })
        
        if not response.success:
            logger.error(f"Get space failed: {response.error}")
            return None
        
        if response.data:
            return ConfluenceSpace.from_dict(response.data)
        return None
    
    async def get_pages_in_space(
        self,
        space_key: str,
    ) -> list[ConfluencePage]:
        """Get all pages in a space."""
        return await self.search(f'space = "{space_key}"')
    
    async def get_pages_by_label(
        self,
        label: str,
        space_key: Optional[str] = None,
    ) -> list[ConfluencePage]:
        """Get pages with a specific label."""
        query = f'label = "{label}"'
        return await self.search(query, space_key)
    
    async def extract_architecture_docs(
        self,
        space_keys: list[str],
    ) -> list[ConfluencePage]:
        """
        Find architecture-related documentation across spaces.
        
        Searches for pages with architecture-related labels or titles.
        """
        all_pages = []
        
        # Search terms for architecture docs
        search_terms = [
            "architecture",
            "design",
            "system diagram",
            "technical spec",
            "integration",
            "API",
        ]
        
        for space_key in space_keys:
            for term in search_terms:
                try:
                    pages = await self.search(
                        f'title ~ "{term}" OR text ~ "{term}"',
                        space_key=space_key,
                    )
                    all_pages.extend(pages)
                except Exception as e:
                    logger.warning(f"Search failed for {term} in {space_key}: {e}")
        
        # Deduplicate by page ID
        seen_ids = set()
        unique_pages = []
        for page in all_pages:
            if page.id not in seen_ids:
                seen_ids.add(page.id)
                unique_pages.append(page)
        
        return unique_pages
    
    def _strip_html(self, html: str) -> str:
        """Strip HTML tags and decode entities."""
        if not html:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        
        # Decode common HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
