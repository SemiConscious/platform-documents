"""Docs360 Enricher Agent - enriches services with public documentation."""

import asyncio
import logging
from typing import Any, Optional

from ..base import BaseAgent, AgentResult, AgentContext
from ...knowledge import (
    Service,
    Document,
    Relation,
    RelationType,
    EntityType,
)
from ...mcp.docs360 import Docs360Client

logger = logging.getLogger("doc-agent.agents.docs360_enricher")


class Docs360EnricherAgent(BaseAgent):
    """
    Agent that enriches discovered services with Docs360 public documentation.
    
    Instead of harvesting all Docs360 articles, this agent:
    1. Iterates over services discovered from GitHub
    2. Performs semantic search for documentation related to each service
    3. Links found documents to services
    
    Docs360 is the public-facing documentation and typically high quality.
    """
    
    name = "docs360_enricher"
    description = "Enriches services with relevant Docs360 public documentation"
    version = "0.2.0"
    
    def __init__(self, context: AgentContext):
        super().__init__(context)
        self.docs360 = Docs360Client(self.mcp)
        
        # Configuration
        source_config = context.config.get("sources", {}).get("docs360", {})
        self.enabled = source_config.get("enabled", True)
        self.trust_level = source_config.get("trust_level", "high")
        self.priority = source_config.get("priority", "authoritative")
        self.max_results_per_service = source_config.get("max_results_per_service", 5)
        
        # Parallelism
        agent_config = context.config.get("agents", {}).get("enrichment", {})
        self.max_concurrent = agent_config.get("parallelism", 5)
    
    async def run(self) -> AgentResult:
        """Execute the Docs360 enrichment process."""
        if not self.enabled:
            self.logger.info("Docs360 enrichment is disabled")
            return AgentResult(
                success=True,
                data={"skipped": True, "reason": "disabled"},
            )
        
        # Get all discovered services from the knowledge graph
        services = self.graph.get_entities_by_type(EntityType.SERVICE)
        
        if not services:
            self.logger.warning("No services found to enrich")
            return AgentResult(
                success=True,
                data={"enriched": 0, "reason": "no services"},
            )
        
        self.logger.info(
            f"Enriching {len(services)} services with Docs360 documentation "
            f"(trust_level: {self.trust_level}, priority: {self.priority})"
        )
        
        # Load checkpoint for incremental updates
        checkpoint = await self.load_checkpoint()
        processed_services = set(checkpoint.get("processed_services", [])) if checkpoint else set()
        
        # Filter to services not yet processed
        services_to_process = [s for s in services if s.id not in processed_services]
        
        if not services_to_process:
            self.logger.info("All services already enriched with Docs360 docs")
            return AgentResult(
                success=True,
                data={"enriched": 0, "reason": "all processed"},
            )
        
        self.logger.info(f"Processing {len(services_to_process)} services")
        
        # Process services with controlled parallelism
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def enrich_with_semaphore(service: Service):
            async with semaphore:
                return await self._enrich_service(service)
        
        tasks = [enrich_with_semaphore(s) for s in services_to_process]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect results
        total_docs = 0
        errors = []
        
        for service, result in zip(services_to_process, results):
            if isinstance(result, Exception):
                self.logger.warning(f"Failed to enrich {service.name}: {result}")
                errors.append(f"{service.name}: {str(result)}")
            else:
                total_docs += result
            
            processed_services.add(service.id)
        
        # Save checkpoint
        await self.save_checkpoint({
            "processed_services": list(processed_services),
        })
        
        self.logger.info(
            f"Docs360 enrichment complete: {total_docs} documents linked to "
            f"{len(services_to_process)} services"
        )
        
        return AgentResult(
            success=len(errors) == 0 or total_docs > 0,
            data={
                "enriched_services": len(services_to_process),
                "documents_linked": total_docs,
            },
            error="; ".join(errors[:5]) if errors else None,
            metadata={
                "trust_level": self.trust_level,
                "priority": self.priority,
            },
        )
    
    async def _enrich_service(self, service: Service) -> int:
        """
        Enrich a single service with Docs360 documentation.
        
        Uses semantic search to find relevant public documentation.
        
        Returns:
            Number of documents linked
        """
        docs_linked = 0
        
        # Build semantic search queries for this service
        queries = self._build_search_queries(service)
        
        seen_article_ids = set()
        
        for query in queries:
            try:
                # Semantic search in Docs360
                articles = await self.docs360.search(query)
                
                for article in articles[:self.max_results_per_service]:
                    if article.id in seen_article_ids:
                        continue
                    seen_article_ids.add(article.id)
                    
                    # Create document entity
                    doc_id = f"doc:docs360:{article.id}"
                    
                    existing = self.graph.get_entity(doc_id)
                    if not existing:
                        # Get snippet or content preview
                        snippet = getattr(article, 'snippet', None) or getattr(article, 'content', None) or ""
                        if len(snippet) > 500:
                            snippet = snippet[:500] + "..."
                        
                        doc = Document(
                            id=doc_id,
                            name=article.title,
                            description=snippet or f"Docs360 article: {article.title}",
                            source_type="docs360",
                            url=article.url or "",
                            content=snippet if snippet else None,
                            trust_level=self.trust_level,
                            sources=[article.url] if article.url else [],
                            metadata={
                                "priority": self.priority,
                                "category": getattr(article, 'category', None),
                                "search_query": query,
                                "relevance_score": getattr(article, 'score', 0.0),
                                "article_id": article.id,
                            },
                        )
                        self.graph.add_entity(doc)
                    
                    # Link document to service
                    relation = Relation(
                        source_id=doc_id,
                        target_id=service.id,
                        relation_type=RelationType.DOCUMENTS,
                        metadata={
                            "search_query": query,
                            "relevance": "semantic_match",
                            "score": article.score,
                        },
                    )
                    self.graph.add_relation(relation)
                    docs_linked += 1
                    
            except Exception as e:
                self.logger.debug(f"Search failed for '{query}': {e}")
        
        if docs_linked > 0:
            self.logger.debug(f"Linked {docs_linked} Docs360 articles to {service.name}")
        
        return docs_linked
    
    def _build_search_queries(self, service: Service) -> list[str]:
        """Build semantic search queries for a service."""
        queries = []
        
        # Use service description if available
        if service.description:
            queries.append(f"How does {service.name} work? {service.description[:100]}")
        else:
            queries.append(f"What is {service.name}?")
        
        # Try to infer domain from service name
        name_lower = service.name.lower()
        
        if any(term in name_lower for term in ["voice", "call", "phone", "sip", "dial"]):
            queries.append(f"Voice and calling features for {service.name}")
        elif any(term in name_lower for term in ["sms", "message", "chat", "omni"]):
            queries.append(f"Messaging and omnichannel features")
        elif any(term in name_lower for term in ["auth", "login", "sso", "jwt"]):
            queries.append(f"Authentication and security")
        elif any(term in name_lower for term in ["report", "analytics", "insight"]):
            queries.append(f"Reporting and analytics")
        elif any(term in name_lower for term in ["integration", "salesforce", "sf"]):
            queries.append(f"Salesforce integration")
        
        return queries[:2]  # Limit to 2 queries per service
    
    def get_system_prompt(self) -> str:
        return """You are a documentation enrichment agent.
Your role is to find and correlate public documentation with software services."""
