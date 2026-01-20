"""Schema Documenter Agent - generates data model documentation."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Optional

import aiofiles

from ..base import BaseAgent, AgentResult, AgentContext
from ...knowledge import Service, Schema, EntityType
from ...knowledge.store import compute_entity_hash

logger = logging.getLogger("doc-agent.agents.generation.schema_documenter")


class SchemaDocumenterAgent(BaseAgent):
    """
    Agent that generates data model and schema documentation.
    
    Generates:
    - Database model documentation
    - Event schema documentation
    - Data dictionary entries
    - Side-effect documentation (what writes where)
    """
    
    name = "schema_documenter"
    description = "Generates data model and schema documentation"
    version = "0.1.0"
    
    def __init__(self, context: AgentContext, service_id: Optional[str] = None):
        super().__init__(context)
        self.output_dir = context.output_dir
        self.dry_run = context.dry_run
        self.service_id = service_id
    
    async def run(self) -> AgentResult:
        """Execute the schema documentation process."""
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
        
        self.logger.info(f"Generating schema documentation for {len(services)} services")
        
        generated_docs = []
        errors = []
        
        for service in services:
            try:
                docs = await self._document_service_data(service)
                generated_docs.extend(docs)
            except Exception as e:
                self.logger.error(f"Failed to document data for {service.name}: {e}")
                errors.append(f"{service.name}: {str(e)}")
        
        # Generate cross-service data dictionary
        try:
            dict_path = await self._generate_data_dictionary(services)
            if dict_path:
                generated_docs.append(dict_path)
        except Exception as e:
            self.logger.error(f"Failed to generate data dictionary: {e}")
            errors.append(f"data-dictionary: {str(e)}")
        
        return AgentResult(
            success=len(errors) == 0 or len(generated_docs) > 0,
            data={
                "generated_docs": generated_docs,
                "errors": errors,
            },
            error="; ".join(errors) if errors else None,
        )
    
    async def _document_service_data(self, service: Service) -> list[str]:
        """Generate data documentation for a service."""
        generated = []
        service_slug = service.id.replace("service:", "")
        data_dir = self.output_dir / "services" / service_slug / "data"
        
        # Get schemas for this service
        schemas = self._get_service_schemas(service)
        
        # Generate models document
        models_path = await self._generate_models_doc(service, schemas, data_dir)
        generated.append(models_path)
        
        # Generate side effects document
        effects_path = await self._generate_side_effects_doc(service, data_dir)
        generated.append(effects_path)
        
        return generated
    
    async def _generate_models_doc(
        self,
        service: Service,
        schemas: list[Schema],
        data_dir: Path,
    ) -> str:
        """Generate the data models document."""
        # Use Claude to generate model documentation
        models_content = await self._generate_models_content(service, schemas)
        
        content = f"""---
title: {service.name} Data Models
description: Database models and data structures for {service.name}
generated: true
---

# {service.name} Data Models

This document describes the data models and structures used by {service.name}.

## Overview

{models_content.get('overview', f'{service.name} manages data through various models and schemas.')}

## Database Models

{models_content.get('database_models', 'No specific database models documented.')}

## Event Schemas

{models_content.get('event_schemas', 'No event schemas documented.')}

## Data Relationships

{models_content.get('relationships', 'See the entity relationship diagram below.')}

{self._generate_erd_placeholder(service)}

## Data Validation

{models_content.get('validation', 'Data validation is enforced at the API and database levels.')}

## Related Documents

- [Service Overview](../README.md)
- [API Schemas](../api/schemas.md)
- [Side Effects](./side-effects.md)
"""
        
        path = data_dir / "models.md"
        await self._write_file(path, content)
        
        return str(path)
    
    async def _generate_side_effects_doc(
        self,
        service: Service,
        data_dir: Path,
    ) -> str:
        """Generate the side effects document."""
        effects_content = await self._analyze_side_effects(service)
        
        content = f"""---
title: {service.name} Side Effects
description: Data operations and side effects for {service.name}
generated: true
---

# {service.name} Side Effects

This document describes the data operations performed by {service.name} and their effects on the system.

## Database Operations

{effects_content.get('database_ops', 'This service performs standard CRUD operations on its data models.')}

## External Service Calls

{effects_content.get('external_calls', 'No external service calls documented.')}

## Event Publishing

{effects_content.get('events_published', 'No events published.')}

## Event Consumption

{effects_content.get('events_consumed', 'No events consumed.')}

## Cache Operations

{effects_content.get('cache_ops', 'No cache operations documented.')}

## File Operations

{effects_content.get('file_ops', 'No file operations documented.')}

## Side Effect Summary

| Operation | Target | Type | Description |
|-----------|--------|------|-------------|
{effects_content.get('summary_table', '| N/A | N/A | N/A | No side effects documented |')}

## Related Documents

- [Data Models](./models.md)
- [Service Overview](../README.md)
"""
        
        path = data_dir / "side-effects.md"
        await self._write_file(path, content)
        
        return str(path)
    
    async def _generate_data_dictionary(
        self,
        services: list[Service],
    ) -> Optional[str]:
        """Generate a cross-service data dictionary."""
        # Collect all schemas
        all_schemas = []
        for service in services:
            schemas = self._get_service_schemas(service)
            for schema in schemas:
                all_schemas.append({
                    "service": service.name,
                    "schema": schema,
                })
        
        if not all_schemas:
            return None
        
        # Generate dictionary content
        dict_content = await self._generate_dictionary_content(all_schemas)
        
        content = f"""---
title: Platform Data Dictionary
description: Cross-service data dictionary for the Natterbox platform
generated: true
---

# Platform Data Dictionary

This document provides a comprehensive dictionary of data entities across all platform services.

## Overview

The platform manages data across {len(services)} services with various data stores and schemas.

## Core Entities

{dict_content.get('core_entities', 'No core entities identified.')}

## Entity Index

{dict_content.get('entity_index', 'No entities indexed.')}

## Shared Data Types

{dict_content.get('shared_types', 'No shared data types documented.')}

## Data Flow Patterns

{dict_content.get('data_flows', 'Data flows between services via APIs and events.')}

## Related Documents

- [Architecture Overview](../architecture/overview.md)
- [System Landscape](../architecture/system-landscape.md)
"""
        
        path = self.output_dir / "reference" / "database-schemas" / "data-dictionary.md"
        await self._write_file(path, content)
        
        return str(path)
    
    def _get_service_schemas(self, service: Service) -> list[Schema]:
        """Get schemas associated with a service."""
        schemas = []
        all_schemas = self.graph.get_entities_by_type(EntityType.SCHEMA)
        
        for schema in all_schemas:
            if isinstance(schema, Schema) and schema.service_id == service.id:
                schemas.append(schema)
        
        return schemas
    
    async def _generate_models_content(
        self,
        service: Service,
        schemas: list[Schema],
    ) -> dict[str, Any]:
        """Use Claude to generate model documentation content."""
        schema_info = "\n".join([
            f"- {s.name} ({s.schema_type}): {s.description or 'No description'}"
            for s in schemas[:10]
        ])
        
        prompt = f"""Generate data model documentation for:

Service: {service.name}
Databases: {service.databases}
Known schemas:
{schema_info or 'None'}

Generate sections:
1. overview: Brief overview of data management
2. database_models: Description of database models (markdown tables)
3. event_schemas: Description of event schemas
4. relationships: Data relationships
5. validation: Validation rules

Return JSON."""
        
        try:
            response = await self.call_claude(
                system_prompt="You are a technical writer documenting data models.",
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
    
    async def _analyze_side_effects(self, service: Service) -> dict[str, Any]:
        """Use Claude to analyze and document side effects."""
        deps = self.graph.get_service_dependencies(service.id)
        dep_names = [d.name for d in deps]
        
        prompt = f"""Analyze side effects for this service:

Service: {service.name}
Description: {service.description}
Databases: {service.databases}
Dependencies: {dep_names}

Generate sections:
1. database_ops: Database operations performed
2. external_calls: External service calls
3. events_published: Events this service publishes
4. events_consumed: Events this service consumes
5. cache_ops: Cache operations
6. file_ops: File operations
7. summary_table: Markdown table rows for summary

Return JSON."""
        
        try:
            response = await self.call_claude(
                system_prompt="You are analyzing data side effects for documentation.",
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
    
    async def _generate_dictionary_content(
        self,
        schemas: list[dict],
    ) -> dict[str, Any]:
        """Use Claude to generate data dictionary content."""
        schema_summary = "\n".join([
            f"- {s['service']}: {s['schema'].name} ({s['schema'].schema_type})"
            for s in schemas[:20]
        ])
        
        prompt = f"""Generate a data dictionary from these schemas:

{schema_summary}

Generate sections:
1. core_entities: Key entities shared across services
2. entity_index: Alphabetical index of entities
3. shared_types: Common data types
4. data_flows: How data flows between services

Return JSON."""
        
        try:
            response = await self.call_claude(
                system_prompt="You are creating a platform data dictionary.",
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
    
    def _generate_erd_placeholder(self, service: Service) -> str:
        """Generate a placeholder ERD diagram."""
        return f"""```mermaid
erDiagram
    {service.name.upper().replace('-', '_')} {{
        string id PK
        string name
        datetime created_at
        datetime updated_at
    }}
```

*Note: This is a placeholder diagram. Actual schema should be extracted from database migrations.*
"""
    
    async def _write_file(self, path: Path, content: str) -> None:
        """Write content to a file."""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would write: {path}")
            return
        
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w") as f:
            await f.write(content)
        
        self.logger.debug(f"Wrote: {path}")
