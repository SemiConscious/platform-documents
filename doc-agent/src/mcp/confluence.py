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
        
        # Handle URL - may be relative or absolute
        url = data.get("_links", {}).get("webui", data.get("url", ""))
        if url and url.startswith("/"):
            # Convert relative URL to absolute
            url = f"https://natterbox.atlassian.net/wiki{url}"
        
        # Extract space key from URL if not directly available
        space_key = data.get("spaceKey", data.get("space", {}).get("key", ""))
        if not space_key and url:
            import re
            match = re.search(r'/spaces/([^/]+)/', url)
            if match:
                space_key = match.group(1)
        
        return cls(
            id=str(data.get("id", "")),
            title=data.get("title", ""),
            space_key=space_key,
            url=url,
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
            query: Search query (natural language or keywords)
            space_key: Optional space to limit search
            
        Returns:
            List of matching pages
        """
        args = {
            "operation": "search_content",
            "query": query,
        }
        if space_key:
            args["spaceKey"] = space_key
        
        response = await self.mcp.call_tool(self.TOOL_NAME, args)
        
        if not response.success:
            logger.error(f"Search failed: {response.error}")
            return []
        
        pages = []
        data = response.data
        
        # Handle nested response format
        if isinstance(data, dict):
            if "data" in data:
                data = data["data"]
            # Try various keys: contents (search), results, pages
            results = data.get("contents", data.get("results", data.get("pages", [])))
        elif isinstance(data, list):
            results = data
        else:
            results = []
        
        for page_data in results:
            try:
                # Skip non-page types (folders, attachments)
                if page_data.get("type") not in ("page", None):
                    continue
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
        max_results: int = 50,
        max_pages: int = 20,
    ) -> list[ConfluencePage]:
        """
        Get all pages in a space with pagination support.
        
        Args:
            space_key: Confluence space key
            max_results: Results per page (default 50)
            max_pages: Maximum number of API pages to fetch (default 20 = 1000 pages)
            
        Returns:
            List of all pages in the space
        """
        all_pages = []
        start = 0
        page_num = 0
        
        while page_num < max_pages:
            response = await self.mcp.call_tool(self.TOOL_NAME, {
                "operation": "get_space_content",
                "spaceKey": space_key,
                "maxResults": max_results,
                "startAt": start,
            })
            
            if not response.success:
                logger.error(f"Get pages in space failed: {response.error}")
                break
            
            data = response.data
            
            # Handle nested response format
            if isinstance(data, dict):
                results = data.get("data", {}).get("pages", [])
                pagination = data.get("pagination", {})
                has_more = pagination.get("hasMore", False)
            elif isinstance(data, list):
                results = data
                has_more = False
            else:
                results = []
                has_more = False
            
            for page_data in results:
                try:
                    all_pages.append(ConfluencePage.from_dict(page_data))
                except Exception as e:
                    logger.warning(f"Failed to parse page: {e}")
            
            if not results or not has_more:
                break
            
            start += len(results)
            page_num += 1
        
        logger.info(f"Fetched {len(all_pages)} pages from space {space_key}")
        return all_pages
    
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
        
        Searches for pages with architecture-related terms.
        """
        all_pages = []
        
        # Search terms for architecture docs
        search_terms = [
            "architecture",
            "design",
            "system diagram",
            "technical spec",
            "integration",
            "API documentation",
        ]
        
        for term in search_terms:
            try:
                # Search across all spaces
                pages = await self.search(term)
                all_pages.extend(pages)
            except Exception as e:
                logger.warning(f"Search failed for {term}: {e}")
        
        # Also get pages from specific spaces
        for space_key in space_keys:
            try:
                pages = await self.get_pages_in_space(space_key)
                all_pages.extend(pages)
            except Exception as e:
                logger.warning(f"Failed to get pages from space {space_key}: {e}")
        
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
