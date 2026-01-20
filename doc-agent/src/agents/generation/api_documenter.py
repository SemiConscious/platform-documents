"""API Documenter Agent - generates API reference documentation."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Optional

import aiofiles

from ..base import BaseAgent, AgentResult, AgentContext
from ...knowledge import Service, API, Endpoint, EntityType
from ...knowledge.store import compute_entity_hash
from ...templates.renderer import TemplateRenderer

logger = logging.getLogger("doc-agent.agents.generation.api_documenter")


class APIDocumenterAgent(BaseAgent):
    """
    Agent that generates API reference documentation.
    
    Generates:
    - API overview document
    - Endpoint reference
    - Schema documentation
    - Example requests/responses
    """
    
    name = "api_documenter"
    description = "Generates API reference documentation"
    version = "0.1.0"
    
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
        
        # Generate API overview
        overview_path = await self._generate_api_overview(service, api, endpoints, api_dir)
        generated.append(overview_path)
        
        # Generate endpoints reference
        endpoints_path = await self._generate_endpoints_doc(api, endpoints, api_dir)
        generated.append(endpoints_path)
        
        # Generate schemas document
        schemas_path = await self._generate_schemas_doc(api, endpoints, api_dir)
        generated.append(schemas_path)
        
        return generated
    
    async def _generate_api_overview(
        self,
        service: Service,
        api: API,
        endpoints: list[dict],
        api_dir: Path,
    ) -> str:
        """Generate the API overview document."""
        # Enhance API description using Claude
        enhanced = await self._enhance_api_description(api, endpoints)
        
        api_data = {
            "name": api.name,
            "description": enhanced.get("description", api.description),
            "api_type": api.api_type,
            "version": api.version,
            "base_url": api.base_url or f"/api/{service.id.replace('service:', '')}",
            "auth_type": api.auth_type or "Bearer Token",
            "auth_details": enhanced.get("auth_details"),
            "errors": enhanced.get("errors", []),
            "rate_limits": enhanced.get("rate_limits"),
        }
        
        content = self.renderer.render_api_overview(api_data, endpoints)
        
        path = api_dir / "overview.md"
        await self._write_file(path, content)
        
        self.store.register_document(
            str(path),
            compute_entity_hash([api]),
            [api.id, service.id],
        )
        
        return str(path)
    
    async def _generate_endpoints_doc(
        self,
        api: API,
        endpoints: list[dict],
        api_dir: Path,
    ) -> str:
        """Generate the endpoints reference document."""
        # Group endpoints by resource/path prefix
        grouped = self._group_endpoints(endpoints)
        
        sections = []
        for group_name, group_endpoints in grouped.items():
            section = f"## {group_name}\n\n"
            
            for endpoint in group_endpoints:
                section += f"### {endpoint['method']} `{endpoint['path']}`\n\n"
                section += f"{endpoint.get('description', 'No description.')}\n\n"
                
                if endpoint.get('parameters'):
                    section += "**Parameters:**\n\n"
                    section += "| Name | Type | Required | Description |\n"
                    section += "|------|------|----------|-------------|\n"
                    for param in endpoint['parameters']:
                        section += f"| `{param['name']}` | {param['type']} | "
                        section += f"{'Yes' if param.get('required') else 'No'} | "
                        section += f"{param.get('description', 'N/A')} |\n"
                    section += "\n"
                
                if endpoint.get('request_example'):
                    section += "**Request Example:**\n\n"
                    section += f"```json\n{json.dumps(endpoint['request_example'], indent=2)}\n```\n\n"
                
                if endpoint.get('response_example'):
                    section += "**Response Example:**\n\n"
                    section += f"```json\n{json.dumps(endpoint['response_example'], indent=2)}\n```\n\n"
                
                section += "---\n\n"
            
            sections.append(section)
        
        content = f"""---
title: {api.name} Endpoints
description: Complete endpoint reference for {api.name}
generated: true
---

# {api.name} Endpoints

This document provides detailed information about all endpoints in the {api.name}.

{''.join(sections)}

## See Also

- [API Overview](./overview.md)
- [Schemas](./schemas.md)
"""
        
        path = api_dir / "endpoints.md"
        await self._write_file(path, content)
        
        return str(path)
    
    async def _generate_schemas_doc(
        self,
        api: API,
        endpoints: list[dict],
        api_dir: Path,
    ) -> str:
        """Generate the schemas/data types document."""
        # Extract unique schemas from endpoints
        schemas = self._extract_schemas(endpoints)
        
        # Generate schema documentation using Claude
        schema_docs = await self._generate_schema_documentation(api, schemas)
        
        content = f"""---
title: {api.name} Schemas
description: Data types and schemas for {api.name}
generated: true
---

# {api.name} Schemas

This document describes the data types used in the {api.name}.

{schema_docs}

## Common Patterns

### Pagination

Paginated responses include:
- `page`: Current page number
- `limit`: Items per page
- `total`: Total number of items
- `items`: Array of results

### Error Responses

Error responses follow this structure:
```json
{{
  "error": {{
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {{}}
  }}
}}
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
                    "path": endpoint.path,
                    "method": endpoint.method,
                    "description": endpoint.description,
                    "auth_required": endpoint.auth_required,
                    "deprecated": endpoint.deprecated,
                    "parameters": [],  # Would need to be extracted from spec
                    "request_example": endpoint.examples[0].get("request") if endpoint.examples else None,
                    "response_example": endpoint.examples[0].get("response") if endpoint.examples else None,
                })
        
        # If no endpoints in graph, generate placeholder
        if not endpoints:
            endpoints = self._generate_placeholder_endpoints(api)
        
        return endpoints
    
    def _generate_placeholder_endpoints(self, api: API) -> list[dict]:
        """Generate placeholder endpoints based on API type."""
        if api.api_type == "rest":
            return [
                {
                    "path": "/health",
                    "method": "GET",
                    "description": "Health check endpoint",
                    "auth_required": False,
                },
                {
                    "path": "/",
                    "method": "GET",
                    "description": "List resources",
                    "auth_required": True,
                },
                {
                    "path": "/{id}",
                    "method": "GET",
                    "description": "Get a specific resource",
                    "auth_required": True,
                },
            ]
        elif api.api_type == "graphql":
            return [
                {
                    "path": "/graphql",
                    "method": "POST",
                    "description": "GraphQL endpoint",
                    "auth_required": True,
                },
            ]
        return []
    
    def _group_endpoints(self, endpoints: list[dict]) -> dict[str, list[dict]]:
        """Group endpoints by resource/path prefix."""
        grouped = {}
        
        for endpoint in endpoints:
            path = endpoint.get("path", "/")
            parts = path.strip("/").split("/")
            
            if parts and parts[0]:
                group = parts[0].title()
            else:
                group = "Root"
            
            if group not in grouped:
                grouped[group] = []
            grouped[group].append(endpoint)
        
        return grouped
    
    def _extract_schemas(self, endpoints: list[dict]) -> list[dict]:
        """Extract unique schemas from endpoint examples."""
        schemas = []
        seen = set()
        
        for endpoint in endpoints:
            for schema_source in ["request_example", "response_example"]:
                if endpoint.get(schema_source):
                    schema_str = json.dumps(endpoint[schema_source], sort_keys=True)
                    if schema_str not in seen:
                        seen.add(schema_str)
                        schemas.append({
                            "name": f"{endpoint['method']}_{endpoint['path'].replace('/', '_')}_{schema_source}",
                            "example": endpoint[schema_source],
                        })
        
        return schemas
    
    async def _enhance_api_description(
        self,
        api: API,
        endpoints: list[dict],
    ) -> dict[str, Any]:
        """Use Claude to enhance API description."""
        endpoint_summary = "\n".join([
            f"- {e['method']} {e['path']}: {e.get('description', 'N/A')}"
            for e in endpoints[:10]
        ])
        
        prompt = f"""Enhance the API documentation:

API: {api.name}
Type: {api.api_type}
Current description: {api.description or 'None'}

Endpoints:
{endpoint_summary}

Provide:
1. description: Improved description of the API
2. auth_details: Authentication details
3. errors: List of common error codes/types
4. rate_limits: Rate limiting info if applicable

Return JSON."""
        
        try:
            response = await self.call_claude(
                system_prompt="You are a technical writer creating API documentation.",
                user_message=prompt,
            )
            
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            return json.loads(response)
        except Exception:
            return {"description": api.description}
    
    async def _generate_schema_documentation(
        self,
        api: API,
        schemas: list[dict],
    ) -> str:
        """Use Claude to generate schema documentation."""
        if not schemas:
            return "No schemas extracted. See individual endpoint documentation for data formats."
        
        schema_examples = "\n".join([
            f"Schema {s['name']}:\n```json\n{json.dumps(s['example'], indent=2)}\n```"
            for s in schemas[:5]
        ])
        
        prompt = f"""Document these API schemas:

{schema_examples}

For each unique data structure, provide:
1. A descriptive name
2. Description of the structure
3. Field descriptions

Format as markdown with ### headers for each type."""
        
        try:
            response = await self.call_claude(
                system_prompt="You are a technical writer documenting API schemas.",
                user_message=prompt,
            )
            return response
        except Exception:
            return "Schema documentation generation failed."
    
    async def _write_file(self, path: Path, content: str) -> None:
        """Write content to a file."""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would write: {path}")
            return
        
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w") as f:
            await f.write(content)
        
        self.logger.debug(f"Wrote: {path}")
