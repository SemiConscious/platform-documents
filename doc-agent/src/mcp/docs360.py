"""Docs360 client - Natterbox's public documentation portal."""

import logging
from dataclasses import dataclass
from typing import Any, Optional

from .client import MCPClient, MCPResponse

logger = logging.getLogger("doc-agent.mcp.docs360")


@dataclass
class Docs360Article:
    """A Docs360 documentation article."""
    id: str
    title: str
    content: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    tags: list[str] = None
    last_modified: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Docs360Article":
        """Create from dictionary response."""
        return cls(
            id=data.get("id", data.get("articleId", "")),
            title=data.get("title", data.get("name", "")),
            content=data.get("content", data.get("body", "")),
            url=data.get("url", data.get("link", "")),
            category=data.get("category", data.get("categoryName", "")),
            subcategory=data.get("subcategory", data.get("subcategoryName", "")),
            tags=data.get("tags", data.get("keywords", [])),
            last_modified=data.get("lastModified", data.get("updatedAt", "")),
        )


@dataclass
class Docs360Category:
    """A category in Docs360."""
    id: str
    name: str
    description: Optional[str] = None
    article_count: int = 0
    subcategories: list[str] = None
    
    def __post_init__(self):
        if self.subcategories is None:
            self.subcategories = []
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Docs360Category":
        """Create from dictionary response."""
        return cls(
            id=data.get("id", data.get("categoryId", "")),
            name=data.get("name", data.get("title", "")),
            description=data.get("description", ""),
            article_count=data.get("articleCount", data.get("count", 0)),
            subcategories=data.get("subcategories", []),
        )


class Docs360Client:
    """
    Docs360 operations via the Natterbox MCP server.
    
    Docs360 is Natterbox's public-facing documentation portal.
    Content here should be accurate and up-to-date.
    
    Uses the 'docs360' MCP tool with operation parameter.
    """
    
    TOOL_NAME = "docs360"
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp = mcp_client
    
    async def list_categories(self) -> list[Docs360Category]:
        """
        List all documentation categories.
        
        Returns:
            List of Docs360Category objects
        """
        response = await self.mcp.call_tool(self.TOOL_NAME, {
            "operation": "list_categories",
        })
        
        if not response.success:
            logger.error(f"Failed to list categories: {response.error}")
            return []
        
        categories = []
        data = response.data
        
        # Handle nested response format
        if isinstance(data, dict):
            if "data" in data and isinstance(data["data"], dict):
                data = data["data"].get("categories", [])
            elif "categories" in data:
                data = data["categories"]
        
        if isinstance(data, list):
            for cat_data in data:
                try:
                    categories.append(Docs360Category.from_dict(cat_data))
                except Exception as e:
                    logger.warning(f"Failed to parse category: {e}")
        
        return categories
    
    async def get_category(self, category_id: str) -> Optional[Docs360Category]:
        """
        Get a specific category with its details.
        
        Args:
            category_id: The category ID
            
        Returns:
            Docs360Category or None if not found
        """
        response = await self.mcp.call_tool(self.TOOL_NAME, {
            "operation": "get_category",
            "categoryId": category_id,
        })
        
        if not response.success:
            logger.error(f"Failed to get category: {response.error}")
            return None
        
        if response.data:
            data = response.data
            if isinstance(data, dict) and "data" in data:
                data = data["data"]
            return Docs360Category.from_dict(data)
        
        return None
    
    async def list_articles(
        self,
        category_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[Docs360Article]:
        """
        List documentation articles.
        
        Args:
            category_id: Optional category to filter by
            limit: Maximum number of articles to return
            
        Returns:
            List of Docs360Article objects
        """
        args = {
            "operation": "list_articles",
            "limit": limit,
        }
        if category_id:
            args["categoryId"] = category_id
        
        response = await self.mcp.call_tool(self.TOOL_NAME, args)
        
        if not response.success:
            logger.error(f"Failed to list articles: {response.error}")
            return []
        
        articles = []
        data = response.data
        
        # Handle nested response format
        if isinstance(data, dict):
            if "data" in data and isinstance(data["data"], dict):
                data = data["data"].get("articles", [])
            elif "articles" in data:
                data = data["articles"]
        
        if isinstance(data, list):
            for article_data in data:
                try:
                    articles.append(Docs360Article.from_dict(article_data))
                except Exception as e:
                    logger.warning(f"Failed to parse article: {e}")
        
        return articles
    
    async def get_article(self, article_id: str) -> Optional[Docs360Article]:
        """
        Get a specific article with full content.
        
        Args:
            article_id: The article ID
            
        Returns:
            Docs360Article with content or None
        """
        response = await self.mcp.call_tool(self.TOOL_NAME, {
            "operation": "get_article",
            "articleId": article_id,
        })
        
        if not response.success:
            logger.error(f"Failed to get article: {response.error}")
            return None
        
        if response.data:
            data = response.data
            if isinstance(data, dict) and "data" in data:
                data = data["data"]
            return Docs360Article.from_dict(data)
        
        return None
    
    async def search(
        self,
        query: str,
        category_id: Optional[str] = None,
        limit: int = 50,
    ) -> list[Docs360Article]:
        """
        Search documentation articles.
        
        Args:
            query: Search query
            category_id: Optional category to filter results
            limit: Maximum results to return
            
        Returns:
            List of matching Docs360Article objects
        """
        args = {
            "operation": "search",
            "query": query,
            "limit": limit,
        }
        if category_id:
            args["categoryId"] = category_id
        
        response = await self.mcp.call_tool(self.TOOL_NAME, args)
        
        if not response.success:
            logger.error(f"Search failed: {response.error}")
            return []
        
        articles = []
        data = response.data
        
        # Handle nested response format
        if isinstance(data, dict):
            if "data" in data and isinstance(data["data"], dict):
                data = data["data"].get("results", data["data"].get("articles", []))
            elif "results" in data:
                data = data["results"]
            elif "articles" in data:
                data = data["articles"]
        
        if isinstance(data, list):
            for article_data in data:
                try:
                    articles.append(Docs360Article.from_dict(article_data))
                except Exception as e:
                    logger.warning(f"Failed to parse search result: {e}")
        
        return articles
