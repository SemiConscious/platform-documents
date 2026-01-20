"""Index Generator Agent - creates navigation structures."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import aiofiles

from ..base import BaseAgent, AgentResult, AgentContext
from ...knowledge import Service, Domain, EntityType

logger = logging.getLogger("doc-agent.agents.quality.index_generator")


class IndexGeneratorAgent(BaseAgent):
    """
    Agent that creates navigation and index structures.
    
    Generates:
    - Main index with categorized links
    - Domain-level indexes
    - Service discovery guides
    - Search-friendly metadata
    - Glossary index
    """
    
    name = "index_generator"
    description = "Creates navigation structures and indexes"
    version = "0.1.0"
    
    def __init__(self, context: AgentContext):
        super().__init__(context)
        self.output_dir = context.output_dir
        self.dry_run = context.dry_run
    
    async def run(self) -> AgentResult:
        """Execute the index generation process."""
        self.logger.info("Generating indexes and navigation")
        
        generated = []
        errors = []
        
        # Generate architecture index
        try:
            path = await self._generate_architecture_index()
            generated.append(path)
        except Exception as e:
            errors.append(f"architecture index: {e}")
        
        # Generate services index
        try:
            path = await self._generate_services_index()
            generated.append(path)
        except Exception as e:
            errors.append(f"services index: {e}")
        
        # Generate domain indexes
        for domain in self.graph.get_domains():
            try:
                path = await self._generate_domain_index(domain)
                generated.append(path)
            except Exception as e:
                errors.append(f"domain {domain.name} index: {e}")
        
        # Generate reference index
        try:
            path = await self._generate_reference_index()
            generated.append(path)
        except Exception as e:
            errors.append(f"reference index: {e}")
        
        # Generate glossary
        try:
            path = await self._generate_glossary()
            generated.append(path)
        except Exception as e:
            errors.append(f"glossary: {e}")
        
        # Generate search metadata
        try:
            path = await self._generate_search_metadata()
            generated.append(path)
        except Exception as e:
            errors.append(f"search metadata: {e}")
        
        return AgentResult(
            success=len(errors) == 0 or len(generated) > 0,
            data={
                "indexes_generated": generated,
                "errors": errors,
            },
            error="; ".join(errors) if errors else None,
        )
    
    async def _generate_architecture_index(self) -> str:
        """Generate the architecture section index."""
        domains = self.graph.get_domains()
        
        domain_list = "\n".join([
            f"- [{d.name}](./domains/{d.id.replace('domain:', '')}/overview.md) - "
            f"{d.description or 'No description'}"
            for d in domains
        ])
        
        content = f"""---
title: Architecture
description: Platform architecture documentation
generated: true
---

# Architecture

Welcome to the platform architecture documentation.

## Contents

- [Overview](./overview.md) - High-level architecture overview
- [System Landscape](./system-landscape.md) - Map of all services
- [Technology Stack](./technology-stack.md) - Technologies used

## Domains

{domain_list if domain_list else 'No domains defined.'}

## Data Flows

- [Data Flows](./data-flows.md) - How data moves through the system

## Related Sections

- [Services](../services/) - Individual service documentation
- [Reference](../reference/) - Data dictionaries and schemas

---
*Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*
"""
        
        path = self.output_dir / "architecture" / "index.md"
        await self._write_file(path, content)
        return str(path)
    
    async def _generate_services_index(self) -> str:
        """Generate the services section index."""
        services = self.graph.get_services()
        domains = self.graph.get_domains()
        
        # Group services by domain
        by_domain: dict[str, list[Service]] = {}
        uncategorized = []
        
        for service in services:
            found_domain = None
            for domain in domains:
                if service.id in domain.services:
                    found_domain = domain.name
                    break
            
            if found_domain:
                if found_domain not in by_domain:
                    by_domain[found_domain] = []
                by_domain[found_domain].append(service)
            else:
                uncategorized.append(service)
        
        # Build sections
        sections = []
        for domain_name, domain_services in sorted(by_domain.items()):
            section = f"### {domain_name}\n\n"
            section += "| Service | Description | Status |\n"
            section += "|---------|-------------|--------|\n"
            for s in sorted(domain_services, key=lambda x: x.name):
                slug = s.id.replace("service:", "")
                section += f"| [{s.name}](./{slug}/README.md) | {s.description or 'N/A'} | {s.status} |\n"
            sections.append(section)
        
        if uncategorized:
            section = "### Other Services\n\n"
            section += "| Service | Description | Status |\n"
            section += "|---------|-------------|--------|\n"
            for s in sorted(uncategorized, key=lambda x: x.name):
                slug = s.id.replace("service:", "")
                section += f"| [{s.name}](./{slug}/README.md) | {s.description or 'N/A'} | {s.status} |\n"
            sections.append(section)
        
        content = f"""---
title: Services
description: Platform service documentation
generated: true
---

# Services

This section contains documentation for all platform services.

## Quick Stats

- **Total Services**: {len(services)}
- **Domains**: {len(domains)}

## Services by Domain

{chr(10).join(sections)}

## All Services (Alphabetical)

| Service | Domain | Language |
|---------|--------|----------|
{self._generate_service_table(services, domains)}

## Finding Services

- **By Domain**: Use the sections above
- **By Technology**: See [Technology Stack](../architecture/technology-stack.md)
- **By API**: See individual service API documentation

---
*Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*
"""
        
        path = self.output_dir / "services" / "index.md"
        await self._write_file(path, content)
        return str(path)
    
    async def _generate_domain_index(self, domain: Domain) -> str:
        """Generate an index for a specific domain."""
        domain_services = []
        for service_id in domain.services:
            service = self.graph.get_entity(service_id)
            if service and isinstance(service, Service):
                domain_services.append(service)
        
        service_list = "\n".join([
            f"- [{s.name}](../../../services/{s.id.replace('service:', '')}/README.md) - "
            f"{s.description or 'No description'}"
            for s in sorted(domain_services, key=lambda x: x.name)
        ])
        
        content = f"""---
title: {domain.name}
description: Index for the {domain.name} domain
generated: true
---

# {domain.name}

{domain.description or 'Domain documentation.'}

## Contents

- [Overview](./overview.md) - Domain overview
- [Components](./components.md) - Domain components
- [Interactions](./interactions.md) - Inter-domain interactions

## Services

{service_list if service_list else 'No services in this domain.'}

## Quick Links

- [Back to Architecture](../../overview.md)
- [All Services](../../../services/index.md)

---
*Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*
"""
        
        domain_slug = domain.id.replace("domain:", "")
        path = self.output_dir / "architecture" / "domains" / domain_slug / "index.md"
        await self._write_file(path, content)
        return str(path)
    
    async def _generate_reference_index(self) -> str:
        """Generate the reference section index."""
        content = f"""---
title: Reference
description: Platform reference documentation
generated: true
---

# Reference

Technical reference documentation for the platform.

## Contents

- [Glossary](./glossary.md) - Platform terminology
- [Database Schemas](./database-schemas/) - Data dictionary
- [Message Formats](./message-formats/) - Event and message schemas

## Quick Links

- [Architecture](../architecture/index.md)
- [Services](../services/index.md)

---
*Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*
"""
        
        path = self.output_dir / "reference" / "index.md"
        await self._write_file(path, content)
        return str(path)
    
    async def _generate_glossary(self) -> str:
        """Generate a glossary of platform terms."""
        # Extract terms from services and domains
        terms = []
        
        for service in self.graph.get_services():
            terms.append({
                "term": service.name,
                "definition": service.description or f"A service in the platform.",
                "type": "Service",
            })
        
        for domain in self.graph.get_domains():
            terms.append({
                "term": domain.name,
                "definition": domain.description or f"A domain in the platform.",
                "type": "Domain",
            })
        
        # Sort alphabetically
        terms.sort(key=lambda x: x["term"].lower())
        
        # Group by first letter
        by_letter: dict[str, list] = {}
        for term in terms:
            letter = term["term"][0].upper()
            if letter not in by_letter:
                by_letter[letter] = []
            by_letter[letter].append(term)
        
        # Generate content
        sections = []
        for letter in sorted(by_letter.keys()):
            section = f"## {letter}\n\n"
            for term in by_letter[letter]:
                section += f"**{term['term']}** ({term['type']})\n"
                section += f": {term['definition']}\n\n"
            sections.append(section)
        
        content = f"""---
title: Glossary
description: Platform terminology and definitions
generated: true
---

# Glossary

This glossary contains definitions of terms used throughout the platform documentation.

## Quick Navigation

{' | '.join([f'[{letter}](#{letter.lower()})' for letter in sorted(by_letter.keys())])}

---

{chr(10).join(sections)}

---
*Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*
"""
        
        path = self.output_dir / "reference" / "glossary.md"
        await self._write_file(path, content)
        return str(path)
    
    async def _generate_search_metadata(self) -> str:
        """Generate search-friendly metadata JSON."""
        docs = []
        
        # Add services
        for service in self.graph.get_services():
            slug = service.id.replace("service:", "")
            docs.append({
                "title": service.name,
                "description": service.description,
                "path": f"/services/{slug}/README.md",
                "type": "service",
                "keywords": [service.name, service.language, service.framework],
            })
        
        # Add domains
        for domain in self.graph.get_domains():
            slug = domain.id.replace("domain:", "")
            docs.append({
                "title": domain.name,
                "description": domain.description,
                "path": f"/architecture/domains/{slug}/overview.md",
                "type": "domain",
                "keywords": [domain.name] + domain.metadata.get("responsibilities", []),
            })
        
        content = {
            "generated": datetime.utcnow().isoformat(),
            "documents": docs,
        }
        
        import json
        path = self.output_dir / "_meta" / "search-index.json"
        
        if not self.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(path, "w") as f:
                await f.write(json.dumps(content, indent=2))
        
        return str(path)
    
    def _generate_service_table(self, services: list[Service], domains: list[Domain]) -> str:
        """Generate a markdown table of all services."""
        rows = []
        for s in sorted(services, key=lambda x: x.name.lower()):
            slug = s.id.replace("service:", "")
            
            # Find domain
            domain_name = "N/A"
            for d in domains:
                if s.id in d.services:
                    domain_name = d.name
                    break
            
            rows.append(f"| [{s.name}](./{slug}/README.md) | {domain_name} | {s.language or 'N/A'} |")
        
        return "\n".join(rows)
    
    async def _write_file(self, path: Path, content: str) -> None:
        """Write content to a file."""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would write: {path}")
            return
        
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w") as f:
            await f.write(content)
        
        self.logger.debug(f"Wrote: {path}")
