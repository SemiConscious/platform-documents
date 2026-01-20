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
    score: float = 0.0
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Docs360Article":
        """Create from dictionary response."""
        # Handle various response formats
        return cls(
            id=str(data.get("id", data.get("articleId", data.get("slug", "")))),
            title=data.get("title", data.get("name", "")),
            content=data.get("content", data.get("body", data.get("snippet", data.get("description", "")))),
            url=data.get("url", data.get("link", data.get("public_url", ""))),
            category=data.get("category", data.get("categoryName", data.get("category_name", ""))),
            score=float(data.get("score", data.get("relevance", 0.0))),
        )


class Docs360Client:
    """
    Docs360 semantic search via the Natterbox MCP server.
    
    Docs360 is Natterbox's public-facing documentation portal (Document360).
    Content here should be accurate and up-to-date.
    
    Uses the 'docs360_search' MCP tool which provides AI-powered semantic
    vector search using Google Cloud Vertex AI.
    
    Key features:
    - Semantic search that understands meaning and intent
    - Returns up to 5 results per query
    - Results include direct links to original articles
    - Best used with natural language questions
    """
    
    TOOL_NAME = "docs360_search"
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp = mcp_client
    
    async def search(self, query: str) -> list[Docs360Article]:
        """
        Perform semantic search on Docs360 knowledge base.
        
        Args:
            query: Natural language search query (questions work best)
            
        Returns:
            List of up to 5 matching Docs360Article objects
        """
        response = await self.mcp.call_tool(self.TOOL_NAME, {
            "query": query,
        })
        
        if not response.success:
            logger.error(f"Docs360 search failed: {response.error}")
            return []
        
        articles = []
        data = response.data
        
        # Handle various response formats
        if isinstance(data, str):
            # Sometimes returns as raw text - try to parse it
            logger.debug(f"Got string response: {data[:200]}...")
            return []
        
        if isinstance(data, dict):
            # Could be nested in results/articles/items
            if "results" in data:
                data = data["results"]
            elif "articles" in data:
                data = data["articles"]
            elif "items" in data:
                data = data["items"]
            elif "data" in data:
                data = data["data"]
        
        if isinstance(data, list):
            for item in data:
                try:
                    if isinstance(item, dict):
                        articles.append(Docs360Article.from_dict(item))
                    elif isinstance(item, str):
                        # Sometimes results are just text/URLs
                        logger.debug(f"Got string item: {item[:100]}...")
                except Exception as e:
                    logger.warning(f"Failed to parse search result: {e}")
        
        logger.debug(f"Docs360 search for '{query}' returned {len(articles)} results")
        return articles
    
    async def search_topics(self, topics: list[str]) -> dict[str, list[Docs360Article]]:
        """
        Search for multiple topics and return results grouped by topic.
        
        Args:
            topics: List of topics/queries to search for
            
        Returns:
            Dict mapping topic to list of articles
        """
        results = {}
        for topic in topics:
            articles = await self.search(topic)
            results[topic] = articles
        return results
