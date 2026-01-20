"""Schema Documenter Agent - generates data model documentation."""

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
    - GraphQL type documentation
    - OpenAPI schema documentation
    - Event schema documentation
    - Data dictionary entries
    """
    
    name = "schema_documenter"
    description = "Generates data model and schema documentation"
    version = "0.2.0"
    
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
        
        # Group schemas by type
        graphql_schemas = [s for s in schemas if s.schema_type == "graphql"]
        openapi_schemas = [s for s in schemas if s.schema_type in ("openapi", "rest")]
        database_schemas = [s for s in schemas if s.schema_type == "database"]
        event_schemas = [s for s in schemas if s.schema_type == "event"]
        
        # Generate models document with actual data
        models_path = await self._generate_models_doc(
            service, 
            graphql_schemas, 
            openapi_schemas, 
            database_schemas, 
            event_schemas,
            data_dir
        )
        generated.append(models_path)
        
        # Generate side effects document
        effects_path = await self._generate_side_effects_doc(service, data_dir)
        generated.append(effects_path)
        
        return generated
    
    async def _generate_models_doc(
        self,
        service: Service,
        graphql_schemas: list[Schema],
        openapi_schemas: list[Schema],
        database_schemas: list[Schema],
        event_schemas: list[Schema],
        data_dir: Path,
    ) -> str:
        """Generate the data models document."""
        total_schemas = len(graphql_schemas) + len(openapi_schemas) + len(database_schemas) + len(event_schemas)
        
        content = f"""---
title: {service.name} Data Models
description: Data types, schemas, and models for {service.name}
generated: true
schema_count: {total_schemas}
---

# {service.name} Data Models

This document describes the data models and structures used by {service.name}.

## Overview

| Type | Count |
|------|-------|
| GraphQL Types | {len(graphql_schemas)} |
| API Schemas | {len(openapi_schemas)} |
| Database Models | {len(database_schemas)} |
| Event Schemas | {len(event_schemas)} |

"""
        
        # GraphQL Types section
        if graphql_schemas:
            content += "## GraphQL Types\n\n"
            content += "These types are defined in the GraphQL schema.\n\n"
            
            # Group by kind
            types = [s for s in graphql_schemas if s.metadata.get("kind") in ("type", "Type", "OBJECT", None)]
            inputs = [s for s in graphql_schemas if s.metadata.get("kind") in ("input", "Input", "INPUT")]
            enums = [s for s in graphql_schemas if s.metadata.get("kind") in ("enum", "Enum", "ENUM")]
            
            if types:
                content += "### Object Types\n\n"
                for schema in types:
                    content += self._format_schema_section(schema)
            
            if inputs:
                content += "### Input Types\n\n"
                for schema in inputs:
                    content += self._format_schema_section(schema)
            
            if enums:
                content += "### Enums\n\n"
                for schema in enums:
                    content += self._format_enum_section(schema)
        
        # OpenAPI/REST Schemas section
        if openapi_schemas:
            content += "## API Schemas\n\n"
            content += "These schemas are defined in the OpenAPI specification.\n\n"
            
            for schema in openapi_schemas:
                content += self._format_schema_section(schema)
        
        # Database Models section
        if database_schemas:
            content += "## Database Models\n\n"
            content += "These models represent database tables and collections.\n\n"
            
            for schema in database_schemas:
                content += self._format_schema_section(schema)
        else:
            content += "## Database Models\n\n"
            content += "*Database models are typically defined in migrations. "
            content += "Check the repository's migration files for the latest schema.*\n\n"
        
        # Event Schemas section
        if event_schemas:
            content += "## Event Schemas\n\n"
            content += "These schemas define the structure of events published by this service.\n\n"
            
            for schema in event_schemas:
                content += self._format_schema_section(schema)
        
        content += """
## Related Documents

- [Service Overview](../README.md)
- [API Documentation](../api/overview.md)
- [Side Effects](./side-effects.md)
"""
        
        path = data_dir / "models.md"
        await self._write_file(path, content)
        
        return str(path)
    
    def _format_schema_section(self, schema: Schema) -> str:
        """Format a schema as a markdown section."""
        section = f"### {schema.name}\n\n"
        
        if schema.description:
            section += f"{schema.description}\n\n"
        
        if schema.fields:
            section += "| Field | Type | Required | Description |\n"
            section += "|-------|------|----------|-------------|\n"
            
            for field in schema.fields:
                name = field.get("name", "")
                field_type = field.get("type", "unknown")
                required = "Yes" if field.get("required") else "No"
                desc = field.get("description") or "N/A"
                
                # Handle long descriptions
                if len(desc) > 60:
                    desc = desc[:57] + "..."
                
                section += f"| `{name}` | `{field_type}` | {required} | {desc} |\n"
            
            section += "\n"
        else:
            section += "*No fields defined.*\n\n"
        
        section += "---\n\n"
        return section
    
    def _format_enum_section(self, schema: Schema) -> str:
        """Format an enum schema as a markdown section."""
        section = f"### {schema.name}\n\n"
        
        if schema.description:
            section += f"{schema.description}\n\n"
        
        enum_values = schema.metadata.get("enum_values", [])
        if enum_values:
            section += "| Value | Description |\n"
            section += "|-------|-------------|\n"
            
            for value in enum_values:
                name = value.get("name", "")
                desc = value.get("description") or "N/A"
                deprecated = " *(deprecated)*" if value.get("deprecated") else ""
                section += f"| `{name}` | {desc}{deprecated} |\n"
            
            section += "\n"
        elif schema.fields:
            # Fallback to fields if enum_values not set
            section += "**Values:**\n\n"
            for field in schema.fields:
                section += f"- `{field.get('name', field.get('type', 'unknown'))}`\n"
            section += "\n"
        
        section += "---\n\n"
        return section
    
    async def _generate_side_effects_doc(
        self,
        service: Service,
        data_dir: Path,
    ) -> str:
        """Generate the side effects document."""
        # Get service dependencies
        deps = self.graph.get_service_dependencies(service.id)
        dep_names = [d.name for d in deps] if deps else []
        
        # Get schemas to identify data operations
        schemas = self._get_service_schemas(service)
        schema_names = [s.name for s in schemas]
        
        content = f"""---
title: {service.name} Side Effects
description: Data operations and side effects for {service.name}
generated: true
---

# {service.name} Side Effects

This document describes the data operations performed by {service.name} and their effects on the system.

## Database Operations

This service performs operations on the following data models:

"""
        
        if schema_names:
            for name in schema_names[:10]:
                content += f"- **{name}**: CRUD operations\n"
        else:
            content += "*No specific data models documented. Check migration files for database operations.*\n"
        
        content += f"""
## Service Dependencies

This service depends on the following services:

"""
        
        if dep_names:
            for name in dep_names:
                content += f"- `{name}`\n"
        else:
            content += "*No direct service dependencies identified.*\n"
        
        content += f"""
## Event Publishing

*Event schemas should be extracted from the service's event definitions.*

Common patterns:
- Entity created events
- Entity updated events
- Entity deleted events

## Event Consumption

*Events consumed by this service should be identified from message queue configurations.*

## Side Effect Summary

| Operation | Target | Type | Description |
|-----------|--------|------|-------------|
| API Call | External Service | Synchronous | Service-to-service communication |
| Database Write | Primary DB | Persistent | Data persistence operations |
| Event Publish | Message Queue | Async | Event-driven communication |

## Data Flow

```mermaid
flowchart LR
    subgraph {service.name.replace('-', '_')}
        API[API Layer]
        BL[Business Logic]
        DAL[Data Access]
    end
    
    Client --> API
    API --> BL
    BL --> DAL
    DAL --> DB[(Database)]
    BL --> MQ{{Message Queue}}
```

## Related Documents

- [Data Models](./models.md)
- [Service Overview](../README.md)
- [API Documentation](../api/overview.md)
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
        all_schemas: list[tuple[str, Schema]] = []
        for service in services:
            schemas = self._get_service_schemas(service)
            for schema in schemas:
                all_schemas.append((service.name, schema))
        
        if not all_schemas:
            return None
        
        # Group schemas by name to find shared types
        schema_by_name: dict[str, list[tuple[str, Schema]]] = {}
        for service_name, schema in all_schemas:
            if schema.name not in schema_by_name:
                schema_by_name[schema.name] = []
            schema_by_name[schema.name].append((service_name, schema))
        
        # Identify shared types (used by multiple services)
        shared_types = {
            name: schemas 
            for name, schemas in schema_by_name.items() 
            if len(schemas) > 1
        }
        
        content = f"""---
title: Platform Data Dictionary
description: Cross-service data dictionary for the Natterbox platform
generated: true
---

# Platform Data Dictionary

This document provides a comprehensive dictionary of data entities across all platform services.

## Overview

| Metric | Value |
|--------|-------|
| Services | {len(services)} |
| Total Schemas | {len(all_schemas)} |
| Unique Schema Names | {len(schema_by_name)} |
| Shared Types | {len(shared_types)} |

## Shared Data Types

These types are used by multiple services:

"""
        
        if shared_types:
            for name, schemas in sorted(shared_types.items()):
                services_using = [s[0] for s in schemas]
                content += f"### {name}\n\n"
                content += f"Used by: {', '.join(services_using)}\n\n"
                
                # Show fields from first schema
                if schemas[0][1].fields:
                    content += "| Field | Type |\n"
                    content += "|-------|------|\n"
                    for field in schemas[0][1].fields[:10]:
                        content += f"| `{field.get('name')}` | `{field.get('type', 'unknown')}` |\n"
                    content += "\n"
                
                content += "---\n\n"
        else:
            content += "*No shared data types identified across services.*\n\n"
        
        content += """## Entity Index

### By Service

"""
        
        # Group by service
        by_service: dict[str, list[Schema]] = {}
        for service_name, schema in all_schemas:
            if service_name not in by_service:
                by_service[service_name] = []
            by_service[service_name].append(schema)
        
        for service_name, schemas in sorted(by_service.items()):
            content += f"#### {service_name}\n\n"
            for schema in sorted(schemas, key=lambda s: s.name)[:20]:
                content += f"- `{schema.name}` ({schema.schema_type})\n"
            if len(schemas) > 20:
                content += f"- *... and {len(schemas) - 20} more*\n"
            content += "\n"
        
        content += """## Data Flow Patterns

Data flows between services through:

1. **Synchronous API calls** - REST or GraphQL requests
2. **Asynchronous events** - Message queue events
3. **Shared databases** - Direct database access (when applicable)

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
    
    async def _write_file(self, path: Path, content: str) -> None:
        """Write content to a file."""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would write: {path}")
            return
        
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w") as f:
            await f.write(content)
        
        self.logger.debug(f"Wrote: {path}")
