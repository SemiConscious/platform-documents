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
from ...mcp.docs360 import Docs360Client, Docs360Article

logger = logging.getLogger("doc-agent.agents.discovery.docs360_harvester")

# Discovery search queries to find documentation topics
DISCOVERY_QUERIES = [
    # Core platform features
    "How to set up call routing",
    "How to configure IVR",
    "How to manage user accounts",
    "How to configure Salesforce integration",
    "How to set up Microsoft Teams integration",
    
    # Voice and telephony
    "Call recording configuration",
    "Voice quality and troubleshooting",
    "Phone number management",
    "SIP trunk setup",
    
    # Analytics and reporting
    "Call analytics and reporting",
    "Dashboard configuration",
    "Real-time monitoring",
    
    # Administration
    "Admin portal guide",
    "User permissions and roles",
    "Organization settings",
    
    # API and integrations
    "API authentication",
    "Webhook configuration",
    "CRM integration options",
    
    # Omnichannel
    "SMS and messaging setup",
    "WhatsApp business integration",
    "Email channel configuration",
    
    # Contact center
    "Agent desktop configuration",
    "Queue management",
    "Skills-based routing",
    
    # Security and compliance
    "Security best practices",
    "GDPR compliance",
    "Data retention policies",
]


class Docs360HarvesterAgent(BaseAgent):
    """
    Agent that harvests documentation from Natterbox's Docs360 portal.
    
    Docs360 is the public-facing documentation for Natterbox products.
    This content is customer-facing and should be accurate and up-to-date.
    
    Uses semantic search to discover documentation topics.
    
    Trust level: HIGH - This is official public documentation.
    """
    
    name = "docs360_harvester"
    description = "Harvests documentation from Natterbox's public Docs360 portal via semantic search"
    version = "0.2.0"
    
    def __init__(self, context: AgentContext):
        super().__init__(context)
        self.docs360 = Docs360Client(self.mcp)
        
        # Configuration
        source_config = context.config.get("sources", {}).get("docs360", {})
        self.enabled = source_config.get("enabled", True)
        
        # Custom search queries from config (extend defaults)
        self.extra_queries = source_config.get("search_queries", [])
        
        # Trust level configuration - Docs360 is authoritative public docs
        self.priority = source_config.get("priority", "authoritative")
        self.trust_level = source_config.get("trust_level", "high")
    
    async def run(self) -> AgentResult:
        """Execute the Docs360 harvesting process using semantic search."""
        # Check if Docs360 is enabled
        if not self.enabled:
            self.logger.info("Docs360 harvesting is disabled in configuration")
            return AgentResult(
                success=True,
                data={"discovered_documents": 0, "skipped": True},
                metadata={"reason": "disabled"},
            )
        
        self.logger.info(
            f"Harvesting documentation from Docs360 via semantic search "
            f"(trust_level: {self.trust_level}, priority: {self.priority})"
        )
        
        # Load checkpoint for incremental updates
        checkpoint = await self.load_checkpoint()
        processed_articles = set(checkpoint.get("processed_articles", [])) if checkpoint else set()
        
        discovered_documents = 0
        linked_to_services = 0
        errors = []
        
        # Combine default and custom queries
        all_queries = DISCOVERY_QUERIES + self.extra_queries
        
        # Track unique articles (avoid duplicates across queries)
        seen_articles: dict[str, Docs360Article] = {}
        
        try:
            # Search for each topic
            for query in all_queries:
                try:
                    articles = await self.docs360.search(query)
                    
                    for article in articles:
                        # Skip if no ID or already seen
                        if not article.id or article.id in seen_articles:
                            continue
                        
                        seen_articles[article.id] = article
                        
                except Exception as e:
                    self.logger.warning(f"Search failed for '{query}': {e}")
                    errors.append(f"search:{query}: {str(e)}")
            
            self.logger.info(f"Found {len(seen_articles)} unique articles from {len(all_queries)} queries")
            
            # Process discovered articles
            for article_id, article in seen_articles.items():
                try:
                    # Skip if already processed
                    if article_id in processed_articles:
                        continue
                    
                    # Create document entity
                    document = await self._process_article(article)
                    
                    if document:
                        self.graph.add_entity(document)
                        discovered_documents += 1
                        
                        # Try to link to services
                        services_linked = await self._link_to_services(document)
                        linked_to_services += len(services_linked)
                    
                    processed_articles.add(article_id)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to process article {article.title}: {e}")
                    errors.append(f"{article.title}: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Failed to harvest from Docs360: {e}")
            errors.append(f"harvest: {str(e)}")
        
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
                "total_unique_articles": len(seen_articles),
                "queries_executed": len(all_queries),
            },
            error="; ".join(errors[:5]) if errors else None,  # Limit errors shown
            metadata={"query_count": len(all_queries)},
        )
    
    async def _process_article(self, article: Docs360Article) -> Optional[Document]:
        """
        Process a Docs360 article and create a document entity.
        """
        self.logger.debug(f"Processing article: {article.title}")
        
        # Classify the document type
        doc_type = self._classify_article(article)
        
        # Extract services mentioned (using Claude if available, otherwise heuristic)
        services = self._extract_services_heuristic(article)
        
        # Create document entity with HIGH trust level
        document = Document(
            id=f"docs360:{article.id}",
            name=article.title,
            description=article.content[:200] if article.content else article.title,
            source_type="docs360",
            url=article.url or f"https://docs.natterbox.com/{article.id}",
            content=article.content,
            labels=[doc_type, "public-documentation"],
            linked_services=services,
            sources=[article.url] if article.url else [],
            # HIGH trust level - this is official public documentation
            trust_level=self.trust_level,
            disclaimer=None,  # No disclaimer needed - this is authoritative
            metadata={
                "category": article.category,
                "doc_type": doc_type,
                "priority": self.priority,
                "is_public": True,
                "search_score": article.score,
            },
        )
        
        return document
    
    def _classify_article(self, article: Docs360Article) -> str:
        """
        Classify the type of documentation article.
        """
        title_lower = article.title.lower() if article.title else ""
        content_lower = (article.content or "").lower()[:500]
        category_lower = (article.category or "").lower()
        
        # Check for common patterns
        if any(word in title_lower for word in ["api", "endpoint", "webhook", "authentication"]):
            return "api"
        if any(word in title_lower for word in ["integrate", "integration", "connect"]):
            return "integration"
        if any(word in title_lower for word in ["admin", "configure", "setup", "setting"]):
            return "admin_guide"
        if any(word in title_lower for word in ["faq", "question", "troubleshoot", "issue"]):
            return "troubleshooting"
        if any(word in title_lower for word in ["release", "update", "change", "what's new"]):
            return "release_notes"
        if any(word in title_lower for word in ["guide", "how to", "tutorial", "getting started"]):
            return "user_guide"
        
        # Check category
        if "api" in category_lower:
            return "api"
        if "admin" in category_lower:
            return "admin_guide"
        
        return "reference"
    
    def _extract_services_heuristic(self, article: Docs360Article) -> list[str]:
        """
        Extract service names from article using heuristics.
        """
        services = []
        text = f"{article.title} {article.content or ''}"
        text_lower = text.lower()
        
        # Known service/feature patterns
        service_patterns = [
            ("ivr", "IVR Service"),
            ("call routing", "Routing Service"),
            ("salesforce", "Salesforce Integration"),
            ("microsoft teams", "Teams Integration"),
            ("teams", "Teams Integration"),
            ("recording", "Recording Service"),
            ("analytics", "Analytics Service"),
            ("reporting", "Reporting Service"),
            ("sms", "SMS Service"),
            ("whatsapp", "WhatsApp Integration"),
            ("omnichannel", "Omnichannel Service"),
            ("queue", "Queue Service"),
            ("agent desktop", "Agent Desktop"),
            ("webhook", "Webhook Service"),
            ("api", "API"),
        ]
        
        for pattern, service_name in service_patterns:
            if pattern in text_lower:
                if service_name not in services:
                    services.append(service_name)
        
        return services[:5]  # Limit to 5 services
    
    async def _link_to_services(self, document: Document) -> list[str]:
        """
        Link the document to services mentioned in it.
        """
        linked = []
        
        for service_name in document.linked_services:
            # Try to find matching service in graph
            for existing_service in self.graph.get_services():
                # Fuzzy match on name
                if (service_name.lower() in existing_service.name.lower() or 
                    existing_service.name.lower() in service_name.lower()):
                    self.graph.add_relation(Relation(
                        source_id=document.id,
                        target_id=existing_service.id,
                        relation_type=RelationType.DOCUMENTS,
                        metadata={"source": "docs360", "is_public": True},
                    ))
                    linked.append(existing_service.name)
                    break
        
        return linked
    
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
