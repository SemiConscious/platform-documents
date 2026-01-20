"""Confluence Harvester Agent - extracts documentation from Confluence."""

import asyncio
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
from ...mcp.confluence import ConfluenceClient, ConfluencePage

logger = logging.getLogger("doc-agent.agents.discovery.confluence_harvester")


class ConfluenceHarvesterAgent(BaseAgent):
    """
    Agent that harvests documentation from Confluence.
    
    Extracts:
    - Architecture documents and diagrams
    - Design documents and ADRs
    - Runbooks and operational procedures
    - Integration guides
    - Historical context and decisions
    """
    
    name = "confluence_harvester"
    description = "Harvests existing documentation from Confluence spaces"
    version = "0.1.0"
    
    def __init__(self, context: AgentContext):
        super().__init__(context)
        self.confluence = ConfluenceClient(self.mcp)
        
        # Configuration
        source_config = context.config.get("sources", {}).get("confluence", {})
        self.spaces = source_config.get("spaces", [])
        self.exclude_labels = source_config.get("exclude_labels", [])
    
    async def run(self) -> AgentResult:
        """Execute the Confluence harvesting process."""
        self.logger.info(f"Harvesting documentation from {len(self.spaces)} Confluence spaces")
        
        # Load checkpoint for incremental updates
        checkpoint = await self.load_checkpoint()
        processed_pages = set(checkpoint.get("processed_pages", [])) if checkpoint else set()
        last_run = checkpoint.get("last_run") if checkpoint else None
        
        discovered_documents = 0
        linked_to_services = 0
        errors = []
        
        for space_key in self.spaces:
            try:
                pages = await self.confluence.list_pages(
                    space_key=space_key,
                    exclude_labels=self.exclude_labels,
                )
                
                self.logger.info(f"Found {len(pages)} pages in space {space_key}")
                
                for page in pages:
                    try:
                        # Skip if already processed and not updated
                        if page.id in processed_pages and last_run:
                            if page.modified and page.modified < datetime.fromisoformat(last_run):
                                continue
                        
                        # Process the page
                        document = await self._process_page(page)
                        
                        if document:
                            self.graph.add_entity(document)
                            discovered_documents += 1
                            
                            # Try to link to services
                            services_linked = await self._link_to_services(document)
                            linked_to_services += len(services_linked)
                        
                        processed_pages.add(page.id)
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to process page {page.title}: {e}")
                        errors.append(f"{page.title}: {str(e)}")
                
            except Exception as e:
                self.logger.error(f"Failed to harvest space {space_key}: {e}")
                errors.append(f"space/{space_key}: {str(e)}")
        
        # Also extract architecture-specific documents
        for space_key in self.spaces:
            try:
                arch_docs = await self.confluence.extract_architecture_docs(space_key)
                for page in arch_docs:
                    if page.id not in processed_pages:
                        document = await self._process_page(page, is_architecture=True)
                        if document:
                            self.graph.add_entity(document)
                            discovered_documents += 1
                        processed_pages.add(page.id)
            except Exception as e:
                self.logger.warning(f"Failed to extract architecture docs from {space_key}: {e}")
        
        # Save checkpoint
        await self.save_checkpoint({
            "processed_pages": list(processed_pages),
            "last_run": datetime.utcnow().isoformat(),
        })
        
        self.logger.info(
            f"Confluence harvesting complete: {discovered_documents} documents, "
            f"{linked_to_services} links to services"
        )
        
        return AgentResult(
            success=len(errors) == 0 or discovered_documents > 0,
            data={
                "discovered_documents": discovered_documents,
                "linked_to_services": linked_to_services,
                "processed_pages": len(processed_pages),
            },
            error="; ".join(errors) if errors else None,
            metadata={"spaces": self.spaces},
        )
    
    async def _process_page(
        self,
        page: ConfluencePage,
        is_architecture: bool = False,
    ) -> Optional[Document]:
        """
        Process a Confluence page and create a document entity.
        """
        self.logger.debug(f"Processing page: {page.title}")
        
        # Get full content if not already loaded
        content = page.content
        if not content:
            full_page = await self.confluence.get_page(page.id)
            content = full_page.content if full_page else None
        
        # Classify the document
        doc_type = await self._classify_document(page, content, is_architecture)
        
        if doc_type == "ignore":
            return None
        
        # Extract key information using Claude
        doc_info = await self._analyze_document(page, content)
        
        # Create document entity
        document = Document(
            id=f"confluence:{page.id}",
            name=page.title,
            description=doc_info.get("summary"),
            source_type="confluence",
            url=page.url,
            content=content,
            labels=page.labels + [doc_type],
            linked_services=doc_info.get("services", []),
            last_modified=page.modified,
            sources=[page.url],
            metadata={
                "space": page.space_key,
                "doc_type": doc_type,
                "author": page.author,
                "key_topics": doc_info.get("topics", []),
                "is_architecture": is_architecture,
            },
        )
        
        return document
    
    async def _classify_document(
        self,
        page: ConfluencePage,
        content: Optional[str],
        is_architecture: bool,
    ) -> str:
        """
        Classify the type of document.
        
        Returns one of:
        - architecture: Architecture/design documents
        - runbook: Operational runbooks
        - adr: Architecture Decision Records
        - integration: Integration guides
        - reference: Reference documentation
        - ignore: Should be ignored
        """
        title_lower = page.title.lower()
        labels = [l.lower() for l in page.labels]
        
        # Check for explicit types
        if is_architecture or "architecture" in labels or "design" in labels:
            return "architecture"
        
        if "adr" in labels or title_lower.startswith("adr"):
            return "adr"
        
        if "runbook" in labels or "runbook" in title_lower:
            return "runbook"
        
        if "integration" in labels or "integration" in title_lower:
            return "integration"
        
        # Check title patterns
        if any(word in title_lower for word in ["architecture", "design", "overview", "diagram"]):
            return "architecture"
        
        if any(word in title_lower for word in ["how to", "guide", "tutorial", "setup"]):
            return "reference"
        
        if any(word in title_lower for word in ["troubleshoot", "incident", "alert"]):
            return "runbook"
        
        # Default to reference
        return "reference"
    
    async def _analyze_document(
        self,
        page: ConfluencePage,
        content: Optional[str],
    ) -> dict[str, Any]:
        """
        Use Claude to analyze the document and extract key information.
        """
        if not content:
            return {
                "summary": page.title,
                "services": [],
                "topics": [],
            }
        
        # Clean HTML content for analysis
        clean_content = self._clean_html(content)
        
        # Truncate if too long
        if len(clean_content) > 5000:
            clean_content = clean_content[:5000] + "..."
        
        prompt = f"""Analyze this Confluence documentation page and extract key information.

Title: {page.title}
Labels: {', '.join(page.labels) if page.labels else 'None'}

Content:
{clean_content}

Extract the following in JSON format:
{{
    "summary": "2-3 sentence summary of what this document covers",
    "services": ["list", "of", "service", "names", "mentioned"],
    "topics": ["key", "topics", "covered"],
    "is_outdated": true/false based on any indicators the content may be stale,
    "related_systems": ["external", "systems", "mentioned"]
}}

For services, extract only specific service/component names mentioned, not general concepts.
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
            self.logger.warning(f"Failed to analyze document with Claude: {e}")
            return {
                "summary": page.title,
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
                        ))
                        linked.append(existing_service.name)
                        break
        
        return linked
    
    def _clean_html(self, html: str) -> str:
        """
        Clean HTML content for analysis.
        """
        if not html:
            return ""
        
        # Remove script and style tags
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML tags but keep content
        html = re.sub(r"<[^>]+>", " ", html)
        
        # Clean up whitespace
        html = re.sub(r"\s+", " ", html)
        
        # Decode common HTML entities
        html = html.replace("&nbsp;", " ")
        html = html.replace("&amp;", "&")
        html = html.replace("&lt;", "<")
        html = html.replace("&gt;", ">")
        html = html.replace("&quot;", '"')
        
        return html.strip()
    
    def get_system_prompt(self) -> str:
        return """You are a technical documentation agent analyzing Confluence pages.

Your role is to:
1. Understand the purpose and content of documentation pages
2. Identify which services or systems are documented
3. Extract key topics and concepts
4. Identify potential issues like outdated content

Be precise about service names - only extract specific named services or components.
If content appears to be outdated based on dates or deprecated language, flag it.
Return structured JSON data that can be used to organize documentation."""
