"""Docs360 Harvester Agent - extracts documentation from Natterbox's public portal."""

import json
import logging
import re
from datetime import datetime
from typing import Any, Optional

from ..base import BaseAgent, AgentResult, AgentContext
from ...knowledge import (
    Document,
    Relation,
    RelationType,
)
from ...mcp.docs360 import Docs360Client, Docs360Article, Docs360Category

logger = logging.getLogger("doc-agent.agents.discovery.docs360_harvester")


class Docs360HarvesterAgent(BaseAgent):
    """
    Agent that harvests documentation from Natterbox's Docs360 portal.
    
    Docs360 is the public-facing documentation for Natterbox products.
    This content is customer-facing and should be accurate and up-to-date.
    
    Trust level: HIGH - This is official public documentation.
    
    Extracts:
    - Product documentation
    - User guides
    - API documentation (public)
    - Integration guides
    - Best practices
    """
    
    name = "docs360_harvester"
    description = "Harvests documentation from Natterbox's public Docs360 portal"
    version = "0.1.0"
    
    def __init__(self, context: AgentContext):
        super().__init__(context)
        self.docs360 = Docs360Client(self.mcp)
        
        # Configuration
        source_config = context.config.get("sources", {}).get("docs360", {})
        self.enabled = source_config.get("enabled", True)
        self.categories = source_config.get("categories", [])  # Empty = all
        self.exclude_categories = source_config.get("exclude_categories", [])
        
        # Trust level configuration - Docs360 is authoritative public docs
        self.priority = source_config.get("priority", "authoritative")
        self.trust_level = source_config.get("trust_level", "high")
    
    async def run(self) -> AgentResult:
        """Execute the Docs360 harvesting process."""
        # Check if Docs360 is enabled
        if not self.enabled:
            self.logger.info("Docs360 harvesting is disabled in configuration")
            return AgentResult(
                success=True,
                data={"discovered_documents": 0, "skipped": True},
                metadata={"reason": "disabled"},
            )
        
        self.logger.info(
            f"Harvesting documentation from Docs360 "
            f"(trust_level: {self.trust_level}, priority: {self.priority})"
        )
        
        # Load checkpoint for incremental updates
        checkpoint = await self.load_checkpoint()
        processed_articles = set(checkpoint.get("processed_articles", [])) if checkpoint else set()
        
        discovered_documents = 0
        linked_to_services = 0
        errors = []
        
        try:
            # Get all categories
            categories = await self.docs360.list_categories()
            
            # Filter categories if specified
            if self.categories:
                categories = [c for c in categories if c.name in self.categories or c.id in self.categories]
            
            # Exclude categories
            if self.exclude_categories:
                categories = [
                    c for c in categories 
                    if c.name not in self.exclude_categories and c.id not in self.exclude_categories
                ]
            
            self.logger.info(f"Found {len(categories)} categories to process")
            
            for category in categories:
                try:
                    # Get articles in category
                    articles = await self.docs360.list_articles(category_id=category.id)
                    
                    self.logger.debug(f"Found {len(articles)} articles in category {category.name}")
                    
                    for article in articles:
                        try:
                            # Skip if already processed
                            if article.id in processed_articles:
                                continue
                            
                            # Get full article content
                            full_article = await self.docs360.get_article(article.id)
                            if not full_article:
                                full_article = article
                            
                            # Process the article
                            document = await self._process_article(full_article, category)
                            
                            if document:
                                self.graph.add_entity(document)
                                discovered_documents += 1
                                
                                # Try to link to services
                                services_linked = await self._link_to_services(document)
                                linked_to_services += len(services_linked)
                            
                            processed_articles.add(article.id)
                            
                        except Exception as e:
                            self.logger.warning(f"Failed to process article {article.title}: {e}")
                            errors.append(f"{article.title}: {str(e)}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to process category {category.name}: {e}")
                    errors.append(f"category/{category.name}: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Failed to connect to Docs360: {e}")
            errors.append(f"connection: {str(e)}")
        
        # Save checkpoint
        await self.save_checkpoint({
            "processed_articles": list(processed_articles),
            "last_run": datetime.utcnow().isoformat(),
        })
        
        self.logger.info(
            f"Docs360 harvesting complete: {discovered_documents} documents, "
            f"{linked_to_services} links to services"
        )
        
        return AgentResult(
            success=len(errors) == 0 or discovered_documents > 0,
            data={
                "discovered_documents": discovered_documents,
                "linked_to_services": linked_to_services,
                "processed_articles": len(processed_articles),
            },
            error="; ".join(errors) if errors else None,
            metadata={"categories": [c.name for c in categories] if 'categories' in dir() else []},
        )
    
    async def _process_article(
        self,
        article: Docs360Article,
        category: Docs360Category,
    ) -> Optional[Document]:
        """
        Process a Docs360 article and create a document entity.
        """
        self.logger.debug(f"Processing article: {article.title}")
        
        # Classify the document
        doc_type = self._classify_article(article, category)
        
        # Extract key information using Claude
        doc_info = await self._analyze_article(article)
        
        # Create document entity with HIGH trust level
        document = Document(
            id=f"docs360:{article.id}",
            name=article.title,
            description=doc_info.get("summary"),
            source_type="docs360",
            url=article.url or f"https://docs.natterbox.com/article/{article.id}",
            content=article.content,
            labels=article.tags + [doc_type, category.name],
            linked_services=doc_info.get("services", []),
            last_modified=datetime.fromisoformat(article.last_modified) if article.last_modified else None,
            sources=[article.url] if article.url else [],
            # HIGH trust level - this is official public documentation
            trust_level=self.trust_level,
            disclaimer=None,  # No disclaimer needed - this is authoritative
            metadata={
                "category": category.name,
                "subcategory": article.subcategory,
                "doc_type": doc_type,
                "key_topics": doc_info.get("topics", []),
                "priority": self.priority,
                "is_public": True,
            },
        )
        
        return document
    
    def _classify_article(
        self,
        article: Docs360Article,
        category: Docs360Category,
    ) -> str:
        """
        Classify the type of documentation article.
        
        Returns one of:
        - user_guide: End-user documentation
        - admin_guide: Administrator documentation
        - api: API documentation
        - integration: Integration guides
        - faq: Frequently asked questions
        - release_notes: Release information
        - reference: General reference
        """
        title_lower = article.title.lower()
        category_lower = category.name.lower()
        tags_lower = [t.lower() for t in article.tags]
        
        # Check category
        if "api" in category_lower:
            return "api"
        if "integration" in category_lower:
            return "integration"
        if "admin" in category_lower:
            return "admin_guide"
        if "release" in category_lower:
            return "release_notes"
        
        # Check title
        if any(word in title_lower for word in ["api", "endpoint", "webhook"]):
            return "api"
        if any(word in title_lower for word in ["integrate", "integration", "connect"]):
            return "integration"
        if any(word in title_lower for word in ["admin", "configure", "setup", "setting"]):
            return "admin_guide"
        if any(word in title_lower for word in ["faq", "question", "troubleshoot"]):
            return "faq"
        if any(word in title_lower for word in ["release", "update", "change"]):
            return "release_notes"
        if any(word in title_lower for word in ["guide", "how to", "tutorial"]):
            return "user_guide"
        
        return "reference"
    
    async def _analyze_article(
        self,
        article: Docs360Article,
    ) -> dict[str, Any]:
        """
        Use Claude to analyze the article and extract key information.
        """
        if not article.content:
            return {
                "summary": article.title,
                "services": [],
                "topics": [],
            }
        
        # Clean content for analysis
        clean_content = self._clean_content(article.content)
        
        # Truncate if too long
        if len(clean_content) > 5000:
            clean_content = clean_content[:5000] + "..."
        
        prompt = f"""Analyze this Natterbox public documentation article and extract key information.

Title: {article.title}
Category: {article.category or 'Unknown'}
Tags: {', '.join(article.tags) if article.tags else 'None'}

Content:
{clean_content}

Extract the following in JSON format:
{{
    "summary": "2-3 sentence summary of what this article covers",
    "services": ["list", "of", "natterbox", "service", "names", "mentioned"],
    "topics": ["key", "topics", "covered"],
    "features": ["specific", "features", "documented"],
    "related_systems": ["external", "systems", "mentioned", "like", "salesforce", "teams"]
}}

For services, extract only specific Natterbox service/component names.
Return ONLY valid JSON, no additional text."""
        
        try:
            response = await self.call_claude(
                system_prompt=self.get_system_prompt(),
                user_message=prompt,
                temperature=0.1,
            )
            
            # Parse JSON response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            return json.loads(response)
            
        except Exception as e:
            self.logger.warning(f"Failed to analyze article with Claude: {e}")
            return {
                "summary": article.title,
                "services": [],
                "topics": [],
            }
    
    async def _link_to_services(self, document: Document) -> list[str]:
        """
        Link the document to services mentioned in it.
        """
        linked = []
        
        for service_name in document.linked_services:
            # Try to find matching service in graph
            service_id = f"service:{service_name}"
            service = self.graph.get_entity(service_id)
            
            if service:
                self.graph.add_relation(Relation(
                    source_id=document.id,
                    target_id=service_id,
                    relation_type=RelationType.DOCUMENTS,
                    metadata={"source": "docs360", "is_public": True},
                ))
                linked.append(service_name)
            else:
                # Try fuzzy match
                for existing_service in self.graph.get_services():
                    if service_name.lower() in existing_service.name.lower():
                        self.graph.add_relation(Relation(
                            source_id=document.id,
                            target_id=existing_service.id,
                            relation_type=RelationType.DOCUMENTS,
                            metadata={"source": "docs360", "is_public": True},
                        ))
                        linked.append(existing_service.name)
                        break
        
        return linked
    
    def _clean_content(self, content: str) -> str:
        """
        Clean article content for analysis.
        """
        if not content:
            return ""
        
        # Remove HTML tags if present
        content = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r"<[^>]+>", " ", content)
        
        # Clean up whitespace
        content = re.sub(r"\s+", " ", content)
        
        # Decode common HTML entities
        content = content.replace("&nbsp;", " ")
        content = content.replace("&amp;", "&")
        content = content.replace("&lt;", "<")
        content = content.replace("&gt;", ">")
        content = content.replace("&quot;", '"')
        
        return content.strip()
    
    def get_system_prompt(self) -> str:
        return """You are a technical documentation agent analyzing Natterbox's public documentation.

Your role is to:
1. Understand the purpose and content of documentation articles
2. Identify which Natterbox services or features are documented
3. Extract key topics and concepts
4. Identify integrations with external systems

Be precise about service names - only extract specific named services or components.
This is official public documentation, so it should be accurate and current.
Return structured JSON data that can be used to organize documentation."""
