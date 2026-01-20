"""Technical Writer Agent - generates service-level documentation."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Optional

import aiofiles

from ..base import BaseAgent, AgentResult, AgentContext
from ...knowledge import Service, Document, Repository, EntityType
from ...knowledge.store import compute_entity_hash
from ...templates.renderer import TemplateRenderer

logger = logging.getLogger("doc-agent.agents.generation.technical_writer")


class TechnicalWriterAgent(BaseAgent):
    """
    Agent that generates service-level technical documentation.
    
    Generates for each service:
    - README with overview
    - Architecture document
    - Configuration guide
    - Operations guide
    """
    
    name = "technical_writer"
    description = "Generates technical documentation for individual services"
    version = "0.1.0"
    
    def __init__(self, context: AgentContext, service_id: Optional[str] = None):
        super().__init__(context)
        self.renderer = TemplateRenderer()
        self.output_dir = context.output_dir
        self.dry_run = context.dry_run
        self.service_id = service_id  # If set, only document this service
    
    async def run(self) -> AgentResult:
        """Execute the technical writing process."""
        if self.service_id:
            service = self.graph.get_entity(self.service_id)
            if not service or not isinstance(service, Service):
                return AgentResult(
                    success=False,
                    error=f"Service not found: {self.service_id}",
                )
            services = [service]
        else:
            services = self.graph.get_services()
        
        self.logger.info(f"Generating technical documentation for {len(services)} services")
        
        generated_docs = []
        errors = []
        
        for service in services:
            try:
                docs = await self._document_service(service)
                generated_docs.extend(docs)
            except Exception as e:
                self.logger.error(f"Failed to document service {service.name}: {e}")
                errors.append(f"{service.name}: {str(e)}")
        
        return AgentResult(
            success=len(errors) == 0 or len(generated_docs) > 0,
            data={
                "generated_docs": generated_docs,
                "services_documented": len(services),
                "errors": errors,
            },
            error="; ".join(errors) if errors else None,
        )
    
    async def _document_service(self, service: Service) -> list[str]:
        """Generate all documentation for a service."""
        generated = []
        service_slug = service.id.replace("service:", "")
        service_dir = self.output_dir / "services" / service_slug
        
        # Gather related information
        related_docs = self._get_related_documents(service)
        sources = self._get_sources(service)
        
        # Generate README
        readme_path = await self._generate_service_readme(service, service_dir, related_docs, sources)
        generated.append(readme_path)
        
        # Generate architecture document
        arch_path = await self._generate_service_architecture(service, service_dir)
        generated.append(arch_path)
        
        # Generate configuration guide
        config_path = await self._generate_configuration_guide(service, service_dir)
        generated.append(config_path)
        
        # Generate operations guide
        ops_path = await self._generate_operations_guide(service, service_dir)
        generated.append(ops_path)
        
        return generated
    
    async def _generate_service_readme(
        self,
        service: Service,
        service_dir: Path,
        related_docs: list[dict],
        sources: list[dict],
    ) -> str:
        """Generate the main README for a service."""
        # Get dependencies and dependents
        deps = self.graph.get_service_dependencies(service.id)
        dependents = self.graph.get_service_dependents(service.id)
        apis = self.graph.get_service_apis(service.id)
        
        # Get repository info for bidirectional linking
        repo_info = self._get_repository_info(service)
        
        # Enhance service data using Claude
        enhanced_data = await self._enhance_service_description(service)
        
        service_data = {
            "id": service.id.replace("service:", ""),
            "name": service.name,
            "description": enhanced_data.get("description", service.description),
            "purpose": enhanced_data.get("purpose"),
            "repository": service.repository,
            "repository_url": f"https://github.com/{service.repository}" if service.repository else None,
            "repository_doc_url": repo_info.get("doc_url") if repo_info else None,
            "language": service.language,
            "framework": service.framework,
            "team": service.team,
            "status": service.status,
            "dependencies": [d.name for d in deps],
            "dependents": [d.name for d in dependents],
            "apis": [
                {"name": api.name, "description": api.description, "api_type": api.api_type}
                for api in apis
            ],
            "databases": service.databases,
            "config_keys": enhanced_data.get("config_keys", []),
        }
        
        content = self.renderer.render_service_readme(service_data, related_docs, sources)
        
        path = service_dir / "README.md"
        await self._write_file(path, content)
        
        self.store.register_document(
            str(path),
            compute_entity_hash([service]),
            [service.id],
        )
        
        return str(path)
    
    def _get_repository_info(self, service: Service) -> Optional[dict]:
        """Get repository information for bidirectional linking."""
        if not service.repository:
            return None
        
        # Try to find the repository entity
        for entity in self.graph.get_entities_by_type(EntityType.REPOSITORY):
            if isinstance(entity, Repository):
                if service.repository in entity.name or (entity.url and service.repository in entity.url):
                    repo_slug = entity.name.replace("/", "-")
                    return {
                        "name": entity.name,
                        "url": entity.url,
                        "doc_url": f"../../repositories/repos/{repo_slug}/README.md",
                    }
        
        # Fallback: generate doc URL from repo name
        repo_slug = service.repository.replace("/", "-")
        return {
            "name": service.repository,
            "url": f"https://github.com/{service.repository}",
            "doc_url": f"../../repositories/repos/{repo_slug}/README.md",
        }
    
    async def _generate_service_architecture(
        self,
        service: Service,
        service_dir: Path,
    ) -> str:
        """Generate the architecture document for a service."""
        # Use Claude to generate architecture content
        arch_content = await self._generate_architecture_content(service)
        
        content = f"""---
title: {service.name} Architecture
description: Internal architecture and design of {service.name}
generated: true
---

# {service.name} Architecture

## Overview

{arch_content.get('overview', f'{service.name} is a service in the Natterbox platform.')}

## Components

{arch_content.get('components', 'No component information available.')}

## Data Model

{arch_content.get('data_model', 'See [Data Models](./data/models.md) for database schema details.')}

## Integration Points

{arch_content.get('integrations', 'This service integrates with other platform services via APIs.')}

## Design Decisions

{arch_content.get('design_decisions', 'No specific design decisions documented.')}

## Related Documents

- [Service Overview](./README.md)
- [API Documentation](./api/overview.md)
- [Configuration Guide](./configuration.md)
"""
        
        path = service_dir / "architecture.md"
        await self._write_file(path, content)
        
        return str(path)
    
    async def _generate_configuration_guide(
        self,
        service: Service,
        service_dir: Path,
    ) -> str:
        """Generate the configuration guide for a service."""
        config_content = await self._generate_config_content(service)
        
        content = f"""---
title: {service.name} Configuration
description: Configuration options for {service.name}
generated: true
---

# {service.name} Configuration

## Environment Variables

{config_content.get('env_vars', 'Configuration is managed via environment variables.')}

## Configuration Files

{config_content.get('config_files', 'No specific configuration files documented.')}

## Feature Flags

{config_content.get('feature_flags', 'No feature flags documented.')}

## Secrets Management

{config_content.get('secrets', 'Secrets should be provided via environment variables or a secrets manager.')}

## Example Configuration

```yaml
{config_content.get('example', '# Example configuration\n# Add environment-specific values')}
```

## Related Documents

- [Service Overview](./README.md)
- [Operations Guide](./operations.md)
"""
        
        path = service_dir / "configuration.md"
        await self._write_file(path, content)
        
        return str(path)
    
    async def _generate_operations_guide(
        self,
        service: Service,
        service_dir: Path,
    ) -> str:
        """Generate the operations guide for a service."""
        # Look for troubleshooting information from Jira
        troubleshooting_docs = self._get_troubleshooting_docs(service)
        ops_content = await self._generate_ops_content(service, troubleshooting_docs)
        
        content = f"""---
title: {service.name} Operations
description: Operational procedures for {service.name}
generated: true
---

# {service.name} Operations Guide

## Health Checks

{ops_content.get('health_checks', 'The service exposes a /health endpoint for health checks.')}

## Monitoring

{ops_content.get('monitoring', 'Monitor the service using standard platform observability tools.')}

## Logging

{ops_content.get('logging', 'Logs are written to stdout in JSON format.')}

## Common Issues

{ops_content.get('common_issues', 'No common issues documented.')}

## Troubleshooting

{ops_content.get('troubleshooting', 'For troubleshooting, check the logs and metrics dashboards.')}

## Runbooks

{ops_content.get('runbooks', 'No specific runbooks available.')}

## Related Documents

- [Service Overview](./README.md)
- [Configuration Guide](./configuration.md)
"""
        
        path = service_dir / "operations.md"
        await self._write_file(path, content)
        
        return str(path)
    
    async def _enhance_service_description(self, service: Service) -> dict[str, Any]:
        """Use Claude to enhance service description."""
        # Get related documents for context
        docs = self._get_related_documents(service)
        doc_context = "\n".join([d.get("title", "") for d in docs[:5]])
        
        prompt = f"""Enhance the documentation for this service:

Name: {service.name}
Current description: {service.description or 'None'}
Repository: {service.repository}
Language: {service.language}
Related docs: {doc_context}

Provide:
1. description: Improved one-line description
2. purpose: 2-3 sentences about what the service does and why
3. config_keys: List of likely configuration options (name, description, required)

Return JSON."""
        
        try:
            response = await self.call_claude(
                system_prompt="You are a technical writer improving service documentation.",
                user_message=prompt,
                temperature=0.3,
            )
            
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            return json.loads(response)
        except Exception as e:
            return {
                "description": service.description,
                "purpose": None,
                "config_keys": [],
            }
    
    async def _generate_architecture_content(self, service: Service) -> dict[str, Any]:
        """Use Claude to generate architecture content."""
        prompt = f"""Generate architecture documentation for:

Service: {service.name}
Description: {service.description}
Language: {service.language}
Framework: {service.framework}
Dependencies: {service.dependencies[:5]}

Generate sections for:
1. overview: High-level architecture description
2. components: Main components/modules
3. data_model: Data handling overview
4. integrations: How it integrates with other services
5. design_decisions: Key design decisions

Return JSON."""
        
        try:
            response = await self.call_claude(
                system_prompt="You are a technical writer documenting service architecture.",
                user_message=prompt,
            )
            
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            return json.loads(response)
        except Exception:
            return {}
    
    async def _generate_config_content(self, service: Service) -> dict[str, Any]:
        """Use Claude to generate configuration content."""
        prompt = f"""Generate configuration documentation for:

Service: {service.name}
Language: {service.language}
Config files: {service.config_files}

Generate sections for:
1. env_vars: Environment variables table
2. config_files: Description of config files
3. feature_flags: Common feature flags
4. secrets: Secrets management approach
5. example: Example configuration

Return JSON."""
        
        try:
            response = await self.call_claude(
                system_prompt="You are a technical writer documenting service configuration.",
                user_message=prompt,
            )
            
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            return json.loads(response)
        except Exception:
            return {}
    
    async def _generate_ops_content(
        self,
        service: Service,
        troubleshooting_docs: list[Document],
    ) -> dict[str, Any]:
        """Use Claude to generate operations content."""
        trouble_context = "\n".join([
            f"- {d.name}: {d.description}"
            for d in troubleshooting_docs[:5]
        ])
        
        prompt = f"""Generate operations documentation for:

Service: {service.name}
Known issues/troubleshooting info:
{trouble_context or 'None available'}

Generate sections for:
1. health_checks: Health check endpoints
2. monitoring: Monitoring approach
3. logging: Logging configuration
4. common_issues: Common operational issues
5. troubleshooting: Troubleshooting steps
6. runbooks: Key operational procedures

Return JSON."""
        
        try:
            response = await self.call_claude(
                system_prompt="You are an SRE writing operations documentation.",
                user_message=prompt,
            )
            
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            return json.loads(response)
        except Exception:
            return {}
    
    def _get_related_documents(self, service: Service) -> list[dict]:
        """Get documents related to a service."""
        docs = []
        
        # Get documents that reference this service
        relations = self.graph.get_relations(
            target_id=service.id,
            relation_type=RelationType.DOCUMENTS,
        ) if hasattr(self.graph, 'get_relations') else []
        
        for relation in relations:
            doc = self.graph.get_entity(relation.source_id)
            if doc and isinstance(doc, Document):
                docs.append({
                    "title": doc.name,
                    "path": doc.url,
                    "type": doc.source_type,
                })
        
        return docs
    
    def _get_sources(self, service: Service) -> list[dict]:
        """Get source references for a service."""
        sources = []
        
        for source_url in service.sources:
            if "github" in source_url:
                sources.append({
                    "type": "GitHub",
                    "title": f"{service.name} Repository",
                    "url": source_url,
                })
            elif "confluence" in source_url:
                sources.append({
                    "type": "Confluence",
                    "title": "Documentation",
                    "url": source_url,
                })
        
        return sources
    
    def _get_troubleshooting_docs(self, service: Service) -> list[Document]:
        """Get troubleshooting documents for a service."""
        docs = []
        
        # Get bug pattern documents
        all_docs = self.graph.get_entities_by_type(EntityType.DOCUMENT)
        for doc in all_docs:
            if isinstance(doc, Document):
                if "troubleshooting" in doc.labels or "bugs" in doc.labels:
                    if service.name.lower() in doc.name.lower() or \
                       service.name in doc.linked_services:
                        docs.append(doc)
        
        return docs
    
    async def _write_file(self, path: Path, content: str) -> None:
        """Write content to a file, creating directories as needed."""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would write: {path}")
            return
        
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w") as f:
            await f.write(content)
        
        self.logger.debug(f"Wrote: {path}")


# Import for type hints
from ...knowledge import Document
from ...knowledge.models import RelationType
