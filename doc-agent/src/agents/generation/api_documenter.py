"""API Documenter Agent - generates API reference documentation."""

import json
import logging
from pathlib import Path
from typing import Any, Optional

import aiofiles

from ..base import BaseAgent, AgentResult, AgentContext
from ...knowledge import Service, API, Endpoint, Schema, EntityType
from ...knowledge.store import compute_entity_hash
from ...templates.renderer import TemplateRenderer

logger = logging.getLogger("doc-agent.agents.generation.api_documenter")


class APIDocumenterAgent(BaseAgent):
    """
    Agent that generates API reference documentation.
    
    Generates:
    - API overview document
    - Endpoint/operation reference (REST or GraphQL)
    - Schema documentation
    - Example requests/responses
    """
    
    name = "api_documenter"
    description = "Generates API reference documentation"
    version = "0.2.0"
    
    def __init__(self, context: AgentContext, service_id: Optional[str] = None):
        super().__init__(context)
        self.renderer = TemplateRenderer()
        self.output_dir = context.output_dir
        self.dry_run = context.dry_run
        self.service_id = service_id
    
    async def run(self) -> AgentResult:
        """Execute the API documentation process."""
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
        
        self.logger.info(f"Generating API documentation for {len(services)} services")
        
        generated_docs = []
        errors = []
        
        for service in services:
            apis = self.graph.get_service_apis(service.id)
            if not apis:
                continue
            
            for api in apis:
                try:
                    docs = await self._document_api(service, api)
                    generated_docs.extend(docs)
                except Exception as e:
                    self.logger.error(f"Failed to document API {api.name}: {e}")
                    errors.append(f"{api.name}: {str(e)}")
        
        return AgentResult(
            success=len(errors) == 0 or len(generated_docs) > 0,
            data={
                "generated_docs": generated_docs,
                "errors": errors,
            },
            error="; ".join(errors) if errors else None,
        )
    
    async def _document_api(self, service: Service, api: API) -> list[str]:
        """Generate documentation for an API."""
        generated = []
        service_slug = service.id.replace("service:", "")
        api_dir = self.output_dir / "services" / service_slug / "api"
        
        # Get endpoints for this API
        endpoints = self._get_endpoints(api)
        
        # Get schemas for this service
        schemas = self._get_schemas(service)
        
        if api.api_type == "graphql":
            # Generate GraphQL-specific documentation
            docs = await self._document_graphql_api(service, api, endpoints, schemas, api_dir)
            generated.extend(docs)
        else:
            # Generate REST API documentation
            docs = await self._document_rest_api(service, api, endpoints, schemas, api_dir)
            generated.extend(docs)
        
        return generated
    
    async def _document_graphql_api(
        self,
        service: Service,
        api: API,
        endpoints: list[dict],
        schemas: list[Schema],
        api_dir: Path,
    ) -> list[str]:
        """Generate GraphQL API documentation."""
        generated = []
        
        # Separate queries and mutations
        queries = [e for e in endpoints if e.get("metadata", {}).get("operation_type") == "query"]
        mutations = [e for e in endpoints if e.get("metadata", {}).get("operation_type") == "mutation"]
        subscriptions = [e for e in endpoints if e.get("metadata", {}).get("operation_type") == "subscription"]
        
        # Generate overview
        overview_path = await self._generate_graphql_overview(service, api, queries, mutations, subscriptions, api_dir)
        generated.append(overview_path)
        
        # Generate queries documentation
        if queries:
            queries_path = await self._generate_graphql_queries(api, queries, api_dir)
            generated.append(queries_path)
        
        # Generate mutations documentation
        if mutations:
            mutations_path = await self._generate_graphql_mutations(api, mutations, api_dir)
            generated.append(mutations_path)
        
        # Generate types documentation
        types_path = await self._generate_graphql_types(api, schemas, api_dir)
        generated.append(types_path)
        
        return generated
    
    async def _generate_graphql_overview(
        self,
        service: Service,
        api: API,
        queries: list[dict],
        mutations: list[dict],
        subscriptions: list[dict],
        api_dir: Path,
    ) -> str:
        """Generate GraphQL API overview document."""
        content = f"""---
title: {api.name}
description: GraphQL API reference for {service.name}
generated: true
api_type: graphql
---

# {api.name}

{api.description or f"GraphQL API for {service.name}"}

## Overview

| Property | Value |
|----------|-------|
| **Endpoint** | `/graphql` |
| **Protocol** | GraphQL over HTTP |
| **Method** | POST |
| **Authentication** | Bearer Token |

## Operations Summary

| Type | Count | Description |
|------|-------|-------------|
| Queries | {len(queries)} | Read operations |
| Mutations | {len(mutations)} | Write operations |
| Subscriptions | {len(subscriptions)} | Real-time updates |

## Quick Start

### Making a Request

```bash
curl -X POST {api.base_url or '/graphql'} \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -d '{{"query": "{{ query {{ ... }} }}"}}'
```

### Example Query

```graphql
query {{
  # Your query here
}}
```

## Documentation

- [Queries](./queries.md) - Read operations ({len(queries)} available)
- [Mutations](./mutations.md) - Write operations ({len(mutations)} available)
- [Types](./types.md) - Type definitions and schemas

## Error Handling

GraphQL errors are returned in the `errors` array:

```json
{{
  "data": null,
  "errors": [
    {{
      "message": "Error description",
      "locations": [{{"line": 1, "column": 1}}],
      "path": ["fieldName"],
      "extensions": {{
        "code": "ERROR_CODE"
      }}
    }}
  ]
}}
```
"""
        
        path = api_dir / "overview.md"
        await self._write_file(path, content)
        
        self.store.register_document(
            str(path),
            compute_entity_hash([api]),
            [api.id, service.id],
        )
        
        return str(path)
    
    async def _generate_graphql_queries(
        self,
        api: API,
        queries: list[dict],
        api_dir: Path,
    ) -> str:
        """Generate GraphQL queries documentation."""
        sections = []
        
        for query in queries:
            name = query.get("name", "Unknown")
            description = query.get("description") or "No description available."
            metadata = query.get("metadata", {})
            return_type = metadata.get("return_type", "Unknown")
            arguments = metadata.get("arguments", [])
            
            section = f"## {name}\n\n"
            section += f"{description}\n\n"
            section += f"**Returns:** `{return_type}`\n\n"
            
            if arguments:
                section += "### Arguments\n\n"
                section += "| Name | Type | Required | Description |\n"
                section += "|------|------|----------|-------------|\n"
                for arg in arguments:
                    arg_name = arg.get("name", "")
                    arg_type = arg.get("type", "")
                    required = "Yes" if arg.get("required") or arg_type.endswith("!") else "No"
                    arg_desc = arg.get("description") or "N/A"
                    section += f"| `{arg_name}` | `{arg_type}` | {required} | {arg_desc} |\n"
                section += "\n"
            
            # Generate example
            section += "### Example\n\n"
            section += f"```graphql\nquery {{\n  {name}"
            if arguments:
                arg_examples = []
                for arg in arguments:
                    arg_type = arg.get("type", "String")
                    if "ID" in arg_type:
                        arg_examples.append(f'{arg["name"]}: "123"')
                    elif "Int" in arg_type:
                        arg_examples.append(f'{arg["name"]}: 10')
                    elif "Boolean" in arg_type:
                        arg_examples.append(f'{arg["name"]}: true')
                    else:
                        arg_examples.append(f'{arg["name"]}: "value"')
                section += f"({', '.join(arg_examples)})"
            section += " {\n    # fields\n  }\n}\n```\n\n"
            section += "---\n\n"
            
            sections.append(section)
        
        content = f"""---
title: {api.name} - Queries
description: GraphQL query operations for {api.name}
generated: true
---

# Queries

This document describes all available query operations in the {api.name}.

Queries are read-only operations that fetch data without modifying state.

{''.join(sections)}

## See Also

- [API Overview](./overview.md)
- [Mutations](./mutations.md)
- [Types](./types.md)
"""
        
        path = api_dir / "queries.md"
        await self._write_file(path, content)
        
        return str(path)
    
    async def _generate_graphql_mutations(
        self,
        api: API,
        mutations: list[dict],
        api_dir: Path,
    ) -> str:
        """Generate GraphQL mutations documentation."""
        sections = []
        
        for mutation in mutations:
            name = mutation.get("name", "Unknown")
            description = mutation.get("description") or "No description available."
            metadata = mutation.get("metadata", {})
            return_type = metadata.get("return_type", "Unknown")
            arguments = metadata.get("arguments", [])
            
            section = f"## {name}\n\n"
            section += f"{description}\n\n"
            section += f"**Returns:** `{return_type}`\n\n"
            
            if arguments:
                section += "### Arguments\n\n"
                section += "| Name | Type | Required | Description |\n"
                section += "|------|------|----------|-------------|\n"
                for arg in arguments:
                    arg_name = arg.get("name", "")
                    arg_type = arg.get("type", "")
                    required = "Yes" if arg.get("required") or arg_type.endswith("!") else "No"
                    arg_desc = arg.get("description") or "N/A"
                    section += f"| `{arg_name}` | `{arg_type}` | {required} | {arg_desc} |\n"
                section += "\n"
            
            # Generate example
            section += "### Example\n\n"
            section += f"```graphql\nmutation {{\n  {name}"
            if arguments:
                arg_examples = []
                for arg in arguments:
                    arg_type = arg.get("type", "String")
                    if "Input" in arg_type:
                        arg_examples.append(f'{arg["name"]}: {{ ... }}')
                    elif "ID" in arg_type:
                        arg_examples.append(f'{arg["name"]}: "123"')
                    elif "Int" in arg_type:
                        arg_examples.append(f'{arg["name"]}: 10')
                    elif "Boolean" in arg_type:
                        arg_examples.append(f'{arg["name"]}: true')
                    else:
                        arg_examples.append(f'{arg["name"]}: "value"')
                section += f"({', '.join(arg_examples)})"
            section += " {\n    # returned fields\n  }\n}\n```\n\n"
            section += "---\n\n"
            
            sections.append(section)
        
        content = f"""---
title: {api.name} - Mutations
description: GraphQL mutation operations for {api.name}
generated: true
---

# Mutations

This document describes all available mutation operations in the {api.name}.

Mutations are operations that create, update, or delete data.

{''.join(sections)}

## See Also

- [API Overview](./overview.md)
- [Queries](./queries.md)
- [Types](./types.md)
"""
        
        path = api_dir / "mutations.md"
        await self._write_file(path, content)
        
        return str(path)
    
    async def _generate_graphql_types(
        self,
        api: API,
        schemas: list[Schema],
        api_dir: Path,
    ) -> str:
        """Generate GraphQL types documentation."""
        # Filter to GraphQL schemas
        graphql_schemas = [s for s in schemas if s.schema_type == "graphql"]
        
        # Group by kind
        types = [s for s in graphql_schemas if s.metadata.get("kind") in ("type", "Type", "OBJECT", None)]
        inputs = [s for s in graphql_schemas if s.metadata.get("kind") in ("input", "Input", "INPUT")]
        enums = [s for s in graphql_schemas if s.metadata.get("kind") in ("enum", "Enum", "ENUM")]
        interfaces = [s for s in graphql_schemas if s.metadata.get("kind") in ("interface", "Interface", "INTERFACE")]
        
        content = f"""---
title: {api.name} - Types
description: GraphQL type definitions for {api.name}
generated: true
---

# Types

This document describes all GraphQL types defined in the {api.name}.

## Summary

| Category | Count |
|----------|-------|
| Object Types | {len(types)} |
| Input Types | {len(inputs)} |
| Enums | {len(enums)} |
| Interfaces | {len(interfaces)} |

"""
        
        # Object Types
        if types:
            content += "## Object Types\n\n"
            for schema in types:
                content += self._format_graphql_type(schema)
        
        # Input Types
        if inputs:
            content += "## Input Types\n\n"
            for schema in inputs:
                content += self._format_graphql_type(schema)
        
        # Enums
        if enums:
            content += "## Enums\n\n"
            for schema in enums:
                content += self._format_graphql_enum(schema)
        
        # Interfaces
        if interfaces:
            content += "## Interfaces\n\n"
            for schema in interfaces:
                content += self._format_graphql_type(schema)
        
        content += """
## See Also

- [API Overview](./overview.md)
- [Queries](./queries.md)
- [Mutations](./mutations.md)
"""
        
        path = api_dir / "types.md"
        await self._write_file(path, content)
        
        return str(path)
    
    def _format_graphql_type(self, schema: Schema) -> str:
        """Format a GraphQL type for documentation."""
        section = f"### {schema.name}\n\n"
        
        if schema.description:
            section += f"{schema.description}\n\n"
        
        if schema.fields:
            section += "| Field | Type | Description |\n"
            section += "|-------|------|-------------|\n"
            for field in schema.fields:
                name = field.get("name", "")
                field_type = field.get("type", "Unknown")
                desc = field.get("description") or "N/A"
                section += f"| `{name}` | `{field_type}` | {desc} |\n"
            section += "\n"
        
        section += "---\n\n"
        return section
    
    def _format_graphql_enum(self, schema: Schema) -> str:
        """Format a GraphQL enum for documentation."""
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
        
        section += "---\n\n"
        return section
    
    async def _document_rest_api(
        self,
        service: Service,
        api: API,
        endpoints: list[dict],
        schemas: list[Schema],
        api_dir: Path,
    ) -> list[str]:
        """Generate REST API documentation."""
        generated = []
        
        # Generate overview
        overview_path = await self._generate_rest_overview(service, api, endpoints, api_dir)
        generated.append(overview_path)
        
        # Generate endpoints reference
        endpoints_path = await self._generate_rest_endpoints(api, endpoints, api_dir)
        generated.append(endpoints_path)
        
        # Generate schemas document
        schemas_path = await self._generate_rest_schemas(api, schemas, api_dir)
        generated.append(schemas_path)
        
        return generated
    
    async def _generate_rest_overview(
        self,
        service: Service,
        api: API,
        endpoints: list[dict],
        api_dir: Path,
    ) -> str:
        """Generate REST API overview document."""
        # Group endpoints by method
        by_method = {}
        for e in endpoints:
            method = e.get("method", "GET")
            by_method[method] = by_method.get(method, 0) + 1
        
        method_summary = "\n".join([
            f"| {method} | {count} |"
            for method, count in sorted(by_method.items())
        ])
        
        content = f"""---
title: {api.name}
description: REST API reference for {service.name}
generated: true
api_type: rest
---

# {api.name}

{api.description or f"REST API for {service.name}"}

## Overview

| Property | Value |
|----------|-------|
| **Base URL** | `{api.base_url or f"/api/{service.id.replace('service:', '')}"}` |
| **Version** | {api.version or "v1"} |
| **Authentication** | {api.auth_type or "Bearer Token"} |

## Endpoints Summary

| Method | Count |
|--------|-------|
{method_summary}

**Total Endpoints:** {len(endpoints)}

## Authentication

All requests require a valid Bearer token in the Authorization header:

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## Documentation

- [Endpoints](./endpoints.md) - Complete endpoint reference
- [Schemas](./schemas.md) - Request/response data types

## Error Handling

Errors follow standard HTTP status codes with JSON error bodies:

```json
{{
  "error": {{
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {{}}
  }}
}}
```
"""
        
        path = api_dir / "overview.md"
        await self._write_file(path, content)
        
        self.store.register_document(
            str(path),
            compute_entity_hash([api]),
            [api.id, service.id],
        )
        
        return str(path)
    
    async def _generate_rest_endpoints(
        self,
        api: API,
        endpoints: list[dict],
        api_dir: Path,
    ) -> str:
        """Generate REST endpoints reference document."""
        # Group endpoints by path prefix
        grouped = self._group_endpoints(endpoints)
        
        sections = []
        for group_name, group_endpoints in sorted(grouped.items()):
            section = f"## {group_name}\n\n"
            
            for endpoint in group_endpoints:
                method = endpoint.get("method", "GET")
                path = endpoint.get("path", "/")
                description = endpoint.get("description") or "No description available."
                deprecated = endpoint.get("deprecated", False)
                metadata = endpoint.get("metadata", {})
                
                # Header with deprecation warning
                deprecation_badge = " *(deprecated)*" if deprecated else ""
                section += f"### {method} `{path}`{deprecation_badge}\n\n"
                section += f"{description}\n\n"
                
                # Parameters
                parameters = metadata.get("parameters", [])
                if parameters:
                    # Group by location
                    path_params = [p for p in parameters if p.get("in") == "path"]
                    query_params = [p for p in parameters if p.get("in") == "query"]
                    header_params = [p for p in parameters if p.get("in") == "header"]
                    
                    if path_params:
                        section += "**Path Parameters:**\n\n"
                        section += "| Name | Type | Description |\n"
                        section += "|------|------|-------------|\n"
                        for p in path_params:
                            section += f"| `{p.get('name')}` | `{p.get('type', 'string')}` | {p.get('description') or 'N/A'} |\n"
                        section += "\n"
                    
                    if query_params:
                        section += "**Query Parameters:**\n\n"
                        section += "| Name | Type | Required | Description |\n"
                        section += "|------|------|----------|-------------|\n"
                        for p in query_params:
                            required = "Yes" if p.get("required") else "No"
                            section += f"| `{p.get('name')}` | `{p.get('type', 'string')}` | {required} | {p.get('description') or 'N/A'} |\n"
                        section += "\n"
                
                # Request body
                request_body = metadata.get("request_body")
                if request_body:
                    section += "**Request Body:**\n\n"
                    if request_body.get("description"):
                        section += f"{request_body['description']}\n\n"
                    section += "```json\n// See schema documentation\n```\n\n"
                
                # Responses
                responses = metadata.get("responses", [])
                if responses:
                    section += "**Responses:**\n\n"
                    section += "| Status | Description |\n"
                    section += "|--------|-------------|\n"
                    for r in responses:
                        section += f"| {r.get('status_code')} | {r.get('description') or 'N/A'} |\n"
                    section += "\n"
                
                section += "---\n\n"
            
            sections.append(section)
        
        content = f"""---
title: {api.name} - Endpoints
description: Complete endpoint reference for {api.name}
generated: true
---

# Endpoints

This document provides detailed information about all endpoints in the {api.name}.

{''.join(sections)}

## See Also

- [API Overview](./overview.md)
- [Schemas](./schemas.md)
"""
        
        path = api_dir / "endpoints.md"
        await self._write_file(path, content)
        
        return str(path)
    
    async def _generate_rest_schemas(
        self,
        api: API,
        schemas: list[Schema],
        api_dir: Path,
    ) -> str:
        """Generate REST schemas documentation."""
        # Filter to OpenAPI/REST schemas
        rest_schemas = [s for s in schemas if s.schema_type in ("openapi", "rest", "request", "response")]
        
        content = f"""---
title: {api.name} - Schemas
description: Data types and schemas for {api.name}
generated: true
---

# Schemas

This document describes the data types used in the {api.name}.

"""
        
        if rest_schemas:
            for schema in rest_schemas:
                content += f"## {schema.name}\n\n"
                
                if schema.description:
                    content += f"{schema.description}\n\n"
                
                if schema.fields:
                    content += "| Field | Type | Required | Description |\n"
                    content += "|-------|------|----------|-------------|\n"
                    for field in schema.fields:
                        name = field.get("name", "")
                        field_type = field.get("type", "unknown")
                        required = "Yes" if field.get("required") else "No"
                        desc = field.get("description") or "N/A"
                        content += f"| `{name}` | `{field_type}` | {required} | {desc} |\n"
                    content += "\n"
                
                content += "---\n\n"
        else:
            content += "*No schemas extracted. See endpoint documentation for data formats.*\n\n"
        
        content += """
## Common Patterns

### Pagination

Paginated responses include:
- `page`: Current page number
- `limit`: Items per page
- `total`: Total number of items
- `items`: Array of results

### Error Responses

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

## See Also

- [API Overview](./overview.md)
- [Endpoints](./endpoints.md)
"""
        
        path = api_dir / "schemas.md"
        await self._write_file(path, content)
        
        return str(path)
    
    def _get_endpoints(self, api: API) -> list[dict]:
        """Get endpoints for an API from the knowledge graph."""
        endpoints = []
        
        # Get endpoint entities
        for endpoint_id in api.endpoints:
            endpoint = self.graph.get_entity(endpoint_id)
            if endpoint and isinstance(endpoint, Endpoint):
                endpoints.append({
                    "id": endpoint.id,
                    "name": endpoint.name,
                    "path": endpoint.path,
                    "method": endpoint.method,
                    "description": endpoint.description,
                    "auth_required": endpoint.auth_required,
                    "deprecated": endpoint.deprecated,
                    "metadata": endpoint.metadata,
                    "examples": endpoint.examples,
                })
        
        return endpoints
    
    def _get_schemas(self, service: Service) -> list[Schema]:
        """Get schemas for a service from the knowledge graph."""
        schemas = []
        
        # Get all schema entities for this service
        for entity in self.graph.get_entities_by_type(EntityType.SCHEMA):
            if isinstance(entity, Schema) and entity.service_id == service.id:
                schemas.append(entity)
        
        return schemas
    
    def _group_endpoints(self, endpoints: list[dict]) -> dict[str, list[dict]]:
        """Group endpoints by resource/path prefix."""
        grouped = {}
        
        for endpoint in endpoints:
            path = endpoint.get("path", "/")
            parts = path.strip("/").split("/")
            
            if parts and parts[0]:
                group = parts[0].replace("_", " ").replace("-", " ").title()
            else:
                group = "Root"
            
            if group not in grouped:
                grouped[group] = []
            grouped[group].append(endpoint)
        
        return grouped
    
    async def _write_file(self, path: Path, content: str) -> None:
        """Write content to a file."""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would write: {path}")
            return
        
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w") as f:
            await f.write(content)
        
        self.logger.debug(f"Wrote: {path}")
