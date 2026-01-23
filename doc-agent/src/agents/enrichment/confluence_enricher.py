"""Confluence Enricher Agent - enriches services with Confluence documentation."""

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
from ...mcp.confluence import ConfluenceClient

logger = logging.getLogger("doc-agent.agents.confluence_enricher")


class ConfluenceEnricherAgent(BaseAgent):
    """
    Agent that enriches discovered services with Confluence documentation.
    
    Instead of harvesting all Confluence pages, this agent:
    1. Iterates over services discovered from GitHub
    2. Searches Confluence for documentation related to each service
    3. Links found documents to services
    
    This is more efficient and produces better correlations.
    """
    
    name = "confluence_enricher"
    description = "Enriches services with relevant Confluence documentation"
    version = "0.2.0"
    
    def __init__(self, context: AgentContext):
        super().__init__(context)
        self.confluence = ConfluenceClient(self.mcp)
        
        # Configuration
        source_config = context.config.get("sources", {}).get("confluence", {})
        self.enabled = source_config.get("enabled", True)
        self.spaces = source_config.get("spaces", [])
        self.trust_level = source_config.get("trust_level", "low")
        self.priority = source_config.get("priority", "reference")
        self.disclaimer = source_config.get("disclaimer", "")
        self.max_results_per_service = source_config.get("max_results_per_service", 10)
        
        # Parallelism
        agent_config = context.config.get("agents", {}).get("enrichment", {})
        self.max_concurrent = agent_config.get("parallelism", 5)
    
    async def run(self) -> AgentResult:
        """Execute the Confluence enrichment process."""
        if not self.enabled:
            self.logger.info("Confluence enrichment is disabled")
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
            f"Enriching {len(services)} services with Confluence documentation "
            f"(trust_level: {self.trust_level}, priority: {self.priority})"
        )
        
        # Load checkpoint for incremental updates
        checkpoint = await self.load_checkpoint()
        processed_services = set(checkpoint.get("processed_services", [])) if checkpoint else set()
        
        # Filter to services not yet processed
        services_to_process = [s for s in services if s.id not in processed_services]
        
        if not services_to_process:
            self.logger.info("All services already enriched with Confluence docs")
            return AgentResult(
                success=True,
                data={"enriched": 0, "reason": "all processed"},
            )
        
        self.logger.info(f"Processing {len(services_to_process)} services (skipping {len(processed_services)} already done)")
        
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
            f"Confluence enrichment complete: {total_docs} documents linked to "
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
        Enrich a single service with Confluence documentation.
        
        Searches for pages mentioning the service name, repo name, or related terms.
        
        Returns:
            Number of documents linked
        """
        docs_linked = 0
        
        # Build search queries for this service
        search_terms = self._build_search_terms(service)
        
        seen_page_ids = set()
        
        for term in search_terms:
            try:
                # Search Confluence for this term
                pages = await self.confluence.search(term)
                
                for page in pages[:self.max_results_per_service]:
                    if page.id in seen_page_ids:
                        continue
                    seen_page_ids.add(page.id)
                    
                    # Create or update document entity
                    doc_id = f"doc:confluence:{page.id}"
                    
                    existing = self.graph.get_entity(doc_id)
                    if not existing:
                        # Get full page content if not already fetched
                        content = await self.confluence.get_page_content(page.id)
                        
                        doc = Document(
                            id=doc_id,
                            name=page.title,
                            description=f"Confluence page: {page.title}",
                            source_type="confluence",
                            url=page.url or "",
                            content=content[:2000] if content else None,
                            labels=page.labels,
                            trust_level=self.trust_level,
                            disclaimer=self.disclaimer if self.disclaimer else None,
                            sources=[page.url] if page.url else [],
                            metadata={
                                "priority": self.priority,
                                "search_term": term,
                                "space_key": page.space_key,
                                "page_id": page.id,
                            },
                        )
                        self.graph.add_entity(doc)
                    
                    # Link document to service
                    relation = Relation(
                        source_id=doc_id,
                        target_id=service.id,
                        relation_type=RelationType.DOCUMENTS,
                        metadata={
                            "search_term": term,
                            "relevance": "search_match",
                        },
                    )
                    self.graph.add_relation(relation)
                    docs_linked += 1
                    
            except Exception as e:
                self.logger.debug(f"Search failed for '{term}': {e}")
        
        if docs_linked > 0:
            self.logger.debug(f"Linked {docs_linked} Confluence docs to {service.name}")
        
        return docs_linked
    
    def _build_search_terms(self, service: Service) -> list[str]:
        """Build search terms for a service."""
        terms = []
        
        # Service name (most specific)
        terms.append(f'"{service.name}"')
        
        # Repository name if different from service name
        if service.repository:
            repo_name = service.repository.split("/")[-1]
            if repo_name != service.name:
                terms.append(f'"{repo_name}"')
        
        # Try without hyphens/underscores (more fuzzy)
        clean_name = service.name.replace("-", " ").replace("_", " ")
        if clean_name != service.name:
            terms.append(clean_name)
        
        return terms[:3]  # Limit to 3 search terms per service
    
    def get_system_prompt(self) -> str:
        return """You are a documentation enrichment agent.
Your role is to find and correlate Confluence documentation with software services."""
