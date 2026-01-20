"""Overview Writer Agent - generates high-level overview documents."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Optional

import aiofiles

from ..base import BaseAgent, AgentResult, AgentContext
from ...knowledge import Domain, Service, EntityType
from ...knowledge.store import compute_entity_hash
from ...templates.renderer import TemplateRenderer

logger = logging.getLogger("doc-agent.agents.generation.overview_writer")


class OverviewWriterAgent(BaseAgent):
    """
    Agent that generates high-level overview documents.
    
    Generates:
    - Main index/landing page
    - Architecture overview
    - System landscape
    - Domain overview documents
    - Technology stack summary
    """
    
    name = "overview_writer"
    description = "Generates high-level architecture and overview documentation"
    version = "0.1.0"
    
    def __init__(self, context: AgentContext):
        super().__init__(context)
        self.renderer = TemplateRenderer()
        self.output_dir = context.output_dir
        self.dry_run = context.dry_run
    
    async def run(self) -> AgentResult:
        """Execute the overview generation process."""
        self.logger.info("Generating overview documents")
        
        generated_docs = []
        errors = []
        
        # Get data from knowledge graph
        services = self.graph.get_services()
        domains = self.graph.get_domains()
        
        # Get architecture metadata
        arch_metadata = self.graph.get_entity("architecture:metadata")
        
        # Generate main index
        try:
            index_path = await self._generate_index(services, domains, arch_metadata)
            generated_docs.append(index_path)
        except Exception as e:
            self.logger.error(f"Failed to generate index: {e}")
            errors.append(f"index: {str(e)}")
        
        # Generate architecture overview
        try:
            arch_path = await self._generate_architecture_overview(services, domains, arch_metadata)
            generated_docs.append(arch_path)
        except Exception as e:
            self.logger.error(f"Failed to generate architecture overview: {e}")
            errors.append(f"architecture: {str(e)}")
        
        # Generate system landscape
        try:
            landscape_path = await self._generate_system_landscape(services, domains)
            generated_docs.append(landscape_path)
        except Exception as e:
            self.logger.error(f"Failed to generate system landscape: {e}")
            errors.append(f"landscape: {str(e)}")
        
        # Generate domain overviews
        for domain in domains:
            try:
                domain_path = await self._generate_domain_overview(domain)
                generated_docs.append(domain_path)
            except Exception as e:
                self.logger.error(f"Failed to generate domain overview for {domain.name}: {e}")
                errors.append(f"domain/{domain.name}: {str(e)}")
        
        # Generate technology stack
        try:
            tech_path = await self._generate_tech_stack(services, arch_metadata)
            generated_docs.append(tech_path)
        except Exception as e:
            self.logger.error(f"Failed to generate tech stack: {e}")
            errors.append(f"tech-stack: {str(e)}")
        
        self.logger.info(f"Generated {len(generated_docs)} overview documents")
        
        return AgentResult(
            success=len(errors) == 0 or len(generated_docs) > 0,
            data={
                "generated_docs": generated_docs,
                "errors": errors,
            },
            error="; ".join(errors) if errors else None,
        )
    
    async def _generate_index(
        self,
        services: list[Service],
        domains: list[Domain],
        arch_metadata: Any,
    ) -> str:
        """Generate the main documentation index."""
        # Prepare data for template
        platform_data = {
            "name": "Natterbox Platform",
            "description": "Comprehensive documentation for the Natterbox platform.",
        }
        
        if arch_metadata and arch_metadata.definition:
            platform_data["description"] = arch_metadata.definition.get(
                "overview", platform_data["description"]
            )
        
        domain_data = [
            {
                "id": d.id.replace("domain:", ""),
                "name": d.name,
                "description": d.description,
                "service_count": len(d.services),
            }
            for d in domains
        ]
        
        service_data = [
            {
                "id": s.id.replace("service:", ""),
                "name": s.name,
                "description": s.description,
                "domain": self._get_service_domain(s, domains),
                "language": s.language,
                "status": s.status,
            }
            for s in services
        ]
        
        # Render template
        content = self.renderer.render_index(platform_data, domain_data, service_data)
        
        # Write file
        path = self.output_dir / "index.md"
        await self._write_file(path, content)
        
        # Register in store
        self.store.register_document(
            str(path),
            compute_entity_hash(services + domains),
            [s.id for s in services] + [d.id for d in domains],
        )
        
        return str(path)
    
    async def _generate_architecture_overview(
        self,
        services: list[Service],
        domains: list[Domain],
        arch_metadata: Any,
    ) -> str:
        """Generate the architecture overview document."""
        # Use Claude to generate detailed architecture content
        arch_content = await self._generate_architecture_content(services, domains, arch_metadata)
        
        # Build document
        content = f"""---
title: Architecture Overview
description: High-level architecture of the Natterbox platform
generated: true
---

# Architecture Overview

{arch_content.get('overview', 'The Natterbox platform is a comprehensive voice and communications solution.')}

## System Design

{arch_content.get('system_design', '')}

## Key Architectural Decisions

{arch_content.get('decisions', '')}

## Technology Stack

| Category | Technologies |
|----------|-------------|
{self._format_tech_table(arch_content.get('technologies', {}))}

## Domain Architecture

The platform is organized into the following domains:

{self._format_domain_list(domains)}

## Further Reading

- [System Landscape](./system-landscape.md) - Detailed service map
- [Data Flows](./data-flows.md) - How data moves through the system
- [Technology Stack](./technology-stack.md) - Detailed technology choices
"""
        
        path = self.output_dir / "architecture" / "overview.md"
        await self._write_file(path, content)
        
        self.store.register_document(
            str(path),
            compute_entity_hash(services),
            ["architecture:metadata"],
        )
        
        return str(path)
    
    async def _generate_system_landscape(
        self,
        services: list[Service],
        domains: list[Domain],
    ) -> str:
        """Generate the system landscape document with service map."""
        # Generate Mermaid diagram
        mermaid_diagram = self._generate_landscape_diagram(services, domains)
        
        # Generate service table
        service_table = self._generate_service_table(services, domains)
        
        content = f"""---
title: System Landscape
description: Overview of all services in the Natterbox platform
generated: true
---

# System Landscape

This document provides a map of all services in the Natterbox platform and their relationships.

## Service Map

```mermaid
{mermaid_diagram}
```

## Services by Domain

{service_table}

## Service Dependencies

The following diagram shows key dependencies between services:

```mermaid
{self._generate_dependency_diagram(services)}
```

## Infrastructure Overview

Services are deployed across the following infrastructure:

- **Compute**: Kubernetes clusters
- **Data**: PostgreSQL, Redis, Elasticsearch
- **Messaging**: RabbitMQ/Kafka
- **External**: Third-party integrations

## Related Documents

- [Architecture Overview](./overview.md)
- [Technology Stack](./technology-stack.md)
"""
        
        path = self.output_dir / "architecture" / "system-landscape.md"
        await self._write_file(path, content)
        
        return str(path)
    
    async def _generate_domain_overview(self, domain: Domain) -> str:
        """Generate an overview document for a specific domain."""
        # Get services in this domain
        domain_services = [
            self.graph.get_entity(sid)
            for sid in domain.services
            if self.graph.get_entity(sid)
        ]
        
        # Use Claude to generate domain description
        domain_content = await self._generate_domain_content(domain, domain_services)
        
        # Prepare service data
        service_data = [
            {
                "id": s.id.replace("service:", ""),
                "name": s.name,
                "description": s.description,
                "status": s.status,
            }
            for s in domain_services
            if isinstance(s, Service)
        ]
        
        domain_data = {
            "id": domain.id.replace("domain:", ""),
            "name": domain.name,
            "description": domain.description or domain_content.get("description"),
            "overview": domain_content.get("overview"),
            "responsibilities": domain.metadata.get("responsibilities", []),
            "interactions": domain_content.get("interactions"),
        }
        
        content = self.renderer.render_domain_overview(domain_data, service_data)
        
        # Create domain directory
        domain_slug = domain.id.replace("domain:", "")
        path = self.output_dir / "architecture" / "domains" / domain_slug / "overview.md"
        await self._write_file(path, content)
        
        return str(path)
    
    async def _generate_tech_stack(
        self,
        services: list[Service],
        arch_metadata: Any,
    ) -> str:
        """Generate the technology stack document."""
        # Collect technologies from services
        languages = {}
        frameworks = {}
        
        for service in services:
            if service.language:
                languages[service.language] = languages.get(service.language, 0) + 1
            if service.framework:
                frameworks[service.framework] = frameworks.get(service.framework, 0) + 1
        
        content = f"""---
title: Technology Stack
description: Technologies used in the Natterbox platform
generated: true
---

# Technology Stack

## Languages

| Language | Service Count |
|----------|--------------|
{self._format_count_table(languages)}

## Frameworks

| Framework | Service Count |
|-----------|--------------|
{self._format_count_table(frameworks)}

## Infrastructure

### Compute
- Kubernetes for container orchestration
- Docker for containerization

### Data Storage
- PostgreSQL for relational data
- Redis for caching
- Elasticsearch for search

### Messaging
- Message queues for async communication
- Event streaming for real-time updates

### Observability
- Metrics collection and dashboards
- Distributed tracing
- Centralized logging

## Development Tools

- Git for version control
- CI/CD pipelines for deployment
- Infrastructure as Code (Terraform)
"""
        
        path = self.output_dir / "architecture" / "technology-stack.md"
        await self._write_file(path, content)
        
        return str(path)
    
    async def _generate_architecture_content(
        self,
        services: list[Service],
        domains: list[Domain],
        arch_metadata: Any,
    ) -> dict[str, Any]:
        """Use Claude to generate architecture documentation content."""
        # Build context
        service_summary = ", ".join([s.name for s in services[:20]])
        domain_summary = ", ".join([d.name for d in domains])
        
        existing_overview = ""
        if arch_metadata and arch_metadata.definition:
            existing_overview = arch_metadata.definition.get("overview", "")
        
        prompt = f"""Generate architecture documentation content for this platform.

Services ({len(services)}): {service_summary}...
Domains: {domain_summary}
Existing analysis: {existing_overview[:1000]}

Generate documentation sections:
1. overview: 2-3 paragraphs describing the overall architecture
2. system_design: Description of how the system is designed
3. decisions: Key architectural decisions (bullet points)
4. technologies: Dict of technology categories to lists

Return JSON:
{{
    "overview": "multi-paragraph overview",
    "system_design": "system design description",
    "decisions": "- Decision 1\\n- Decision 2",
    "technologies": {{
        "Languages": ["Go", "TypeScript"],
        "Databases": ["PostgreSQL"]
    }}
}}"""
        
        try:
            response = await self.call_claude(
                system_prompt="You are a technical writer creating architecture documentation.",
                user_message=prompt,
            )
            
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            return json.loads(response)
        except Exception as e:
            self.logger.warning(f"Failed to generate architecture content: {e}")
            return {
                "overview": "The platform consists of multiple microservices organized into domains.",
                "system_design": "",
                "decisions": "",
                "technologies": {},
            }
    
    async def _generate_domain_content(
        self,
        domain: Domain,
        services: list,
    ) -> dict[str, Any]:
        """Use Claude to generate domain documentation content."""
        service_names = ", ".join([s.name for s in services if hasattr(s, 'name')][:10])
        
        prompt = f"""Generate documentation for this domain:

Domain: {domain.name}
Description: {domain.description or 'None'}
Services: {service_names}
Responsibilities: {domain.metadata.get('responsibilities', [])}

Generate:
1. description: One paragraph description
2. overview: 2-3 paragraphs about what this domain does
3. interactions: How this domain interacts with others

Return JSON."""
        
        try:
            response = await self.call_claude(
                system_prompt="You are a technical writer creating domain documentation.",
                user_message=prompt,
            )
            
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            return json.loads(response)
        except Exception as e:
            return {
                "description": domain.description or f"The {domain.name} domain.",
                "overview": f"This domain contains services related to {domain.name.lower()}.",
                "interactions": "",
            }
    
    def _get_service_domain(self, service: Service, domains: list[Domain]) -> str:
        """Get the domain name for a service."""
        for domain in domains:
            if service.id in domain.services:
                return domain.name
        return "Uncategorized"
    
    def _generate_landscape_diagram(
        self,
        services: list[Service],
        domains: list[Domain],
    ) -> str:
        """Generate a Mermaid diagram showing the system landscape."""
        lines = ["graph TB"]
        
        # Group services by domain
        for domain in domains:
            domain_id = domain.id.replace("domain:", "").replace("-", "_")
            lines.append(f"    subgraph {domain_id}[{domain.name}]")
            
            for service_id in domain.services[:8]:  # Limit services per domain
                service = self.graph.get_entity(service_id)
                if service:
                    safe_id = service_id.replace("service:", "").replace("-", "_")
                    lines.append(f"        {safe_id}[{service.name}]")
            
            lines.append("    end")
        
        return "\n".join(lines)
    
    def _generate_dependency_diagram(self, services: list[Service]) -> str:
        """Generate a Mermaid diagram showing service dependencies."""
        lines = ["graph LR"]
        
        for service in services[:15]:  # Limit for readability
            deps = self.graph.get_service_dependencies(service.id)
            for dep in deps[:3]:  # Limit deps per service
                from_id = service.id.replace("service:", "").replace("-", "_")
                to_id = dep.id.replace("service:", "").replace("-", "_")
                lines.append(f"    {from_id} --> {to_id}")
        
        if len(lines) == 1:
            lines.append("    NoDepenciesFound[No dependencies mapped]")
        
        return "\n".join(lines)
    
    def _generate_service_table(
        self,
        services: list[Service],
        domains: list[Domain],
    ) -> str:
        """Generate a markdown table of services grouped by domain."""
        sections = []
        
        for domain in domains:
            section_lines = [f"### {domain.name}\n"]
            section_lines.append("| Service | Description | Language | Status |")
            section_lines.append("|---------|-------------|----------|--------|")
            
            for service_id in domain.services:
                service = self.graph.get_entity(service_id)
                if service and isinstance(service, Service):
                    sid = service.id.replace("service:", "")
                    section_lines.append(
                        f"| [{service.name}](../../services/{sid}/README.md) | "
                        f"{service.description or 'N/A'} | "
                        f"{service.language or 'N/A'} | "
                        f"{service.status or 'Active'} |"
                    )
            
            sections.append("\n".join(section_lines))
        
        return "\n\n".join(sections)
    
    def _format_tech_table(self, technologies: dict) -> str:
        """Format technologies dict as markdown table rows."""
        lines = []
        for category, techs in technologies.items():
            if isinstance(techs, list):
                lines.append(f"| {category} | {', '.join(techs)} |")
            else:
                lines.append(f"| {category} | {techs} |")
        return "\n".join(lines) if lines else "| N/A | N/A |"
    
    def _format_domain_list(self, domains: list[Domain]) -> str:
        """Format domains as a markdown list."""
        lines = []
        for domain in domains:
            domain_slug = domain.id.replace("domain:", "")
            lines.append(f"- **[{domain.name}](./domains/{domain_slug}/overview.md)**: {domain.description or 'No description'}")
        return "\n".join(lines) if lines else "No domains defined."
    
    def _format_count_table(self, counts: dict) -> str:
        """Format a count dict as markdown table rows."""
        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        lines = [f"| {name} | {count} |" for name, count in sorted_items]
        return "\n".join(lines) if lines else "| N/A | 0 |"
    
    async def _write_file(self, path: Path, content: str) -> None:
        """Write content to a file, creating directories as needed."""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would write: {path}")
            return
        
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w") as f:
            await f.write(content)
        
        self.logger.debug(f"Wrote: {path}")
