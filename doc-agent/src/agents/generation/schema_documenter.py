"""Schema Documenter Agent - generates data model documentation."""

import json
import logging
import re
from pathlib import Path
from typing import Any, Optional

import aiofiles

from ..base import BaseAgent, AgentResult, AgentContext
from ...knowledge import Service, Schema, EntityType
from ...knowledge.store import compute_entity_hash
from ...analyzers.integration import (
    analyze_service_repository,
    get_models_for_documentation,
    get_side_effects_for_documentation,
)

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
    - Side effects documentation with actual code analysis
    """
    
    name = "schema_documenter"
    description = "Generates data model and schema documentation"
    version = "0.3.0"
    
    def __init__(self, context: AgentContext, service_id: Optional[str] = None):
        super().__init__(context)
        self.output_dir = context.output_dir
        self.dry_run = context.dry_run
        self.service_id = service_id
        
        # Set up local repos path
        workspace_root = Path(__file__).parent.parent.parent.parent
        self.local_repos_path = workspace_root / "repos"
        self.use_local_repos = self.local_repos_path.exists()
    
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
    
    def _extract_code_types(self, service: Service) -> list[dict]:
        """Extract types from code using multi-language analyzers."""
        types = []
        
        # Get local repos path
        repos_dir = self.output_dir.parent / "repos"
        if not repos_dir.exists():
            # Fall back to legacy Go extraction
            repo_path = self._get_local_repo_path(service)
            return self._extract_go_types_legacy(repo_path) if repo_path else []
        
        # Use new multi-language analyzer
        repo_name = getattr(service, 'repository', None) or service.name
        org = service.metadata.get("organization", "redmatter") if service.metadata else "redmatter"
        
        analysis = analyze_service_repository(
            repos_dir=repos_dir,
            service_name=service.name,
            repository=repo_name,
            organizations=[org, "redmatter", "natterbox"],
        )
        
        if not analysis:
            return types
        
        # Convert analyzer models to legacy format for compatibility
        for model in analysis.models:
            types.append({
                "name": model.name,
                "file": model.file,
                "fields": [
                    {
                        "name": f.name,
                        "type": f.type,
                        "tags": f.tags or "",
                        "description": f.description,
                    }
                    for f in model.fields
                ],
                "is_config": "config" in model.name.lower() or "config" in model.decorators,
                "github_url": model.github_url,
                "type_kind": model.model_type.value,
            })
        
        return types
    
    def _extract_go_types_legacy(self, repo_path: Path) -> list[dict]:
        """Legacy Go struct extraction (fallback when analyzers not available)."""
        types = []
        if not repo_path or not repo_path.exists():
            return types
        
        go_files = self._find_code_files(repo_path, ["**/*.go"], max_files=30)
        
        for file_path, content in go_files:
            # Skip test files
            if "_test.go" in file_path:
                continue
            
            # Find struct definitions
            struct_pattern = r"type\s+(\w+)\s+struct\s*\{([^}]+)\}"
            for match in re.finditer(struct_pattern, content, re.MULTILINE):
                name = match.group(1)
                body = match.group(2)
                
                # Extract fields
                fields = []
                field_pattern = r"(\w+)\s+([^\s`]+)(?:\s+`([^`]+)`)?"
                for field_match in re.finditer(field_pattern, body):
                    field_name = field_match.group(1)
                    field_type = field_match.group(2)
                    tags = field_match.group(3) or ""
                    
                    # Skip embedded types (start with capital, no explicit type)
                    if field_name[0].isupper() and not field_type:
                        continue
                    
                    fields.append({
                        "name": field_name,
                        "type": field_type,
                        "tags": tags,
                    })
                
                if fields:
                    types.append({
                        "name": name,
                        "file": file_path,
                        "fields": fields,
                        "is_config": "config" in name.lower(),
                    })
        
        return types
    
    def _extract_go_types(self, repo_path: Path) -> list[dict]:
        """Extract Go struct types from code (legacy method, kept for compatibility)."""
        return self._extract_go_types_legacy(repo_path)
    
    async def _generate_models_doc(
        self,
        service: Service,
        graphql_schemas: list[Schema],
        openapi_schemas: list[Schema],
        database_schemas: list[Schema],
        event_schemas: list[Schema],
        data_dir: Path,
    ) -> str:
        """Generate the data models document with actual code analysis."""
        service_slug = service.id.replace("service:", "")
        
        # Extract types using multi-language analyzers
        code_types = self._extract_code_types(service)
        
        # Separate config types from other types
        config_types = [t for t in code_types if t.get("is_config")]
        data_types = [t for t in code_types if not t.get("is_config")]
        
        total_schemas = len(graphql_schemas) + len(openapi_schemas) + len(database_schemas) + len(event_schemas)
        total_types = total_schemas + len(code_types)
        
        content = f"""---
title: {service.name} Data Models
description: Data types, schemas, and models for {service.name}
generated: true
schema_count: {total_types}
---

<!-- breadcrumb -->
[Home](/../../../index.md) > [Services](../../../services/index.md) > {service.name.replace('-', ' ').title()} > Data


# {service.name} Data Models

This document describes the data models and structures used by {service.name}.

## Overview

| Type | Count |
|------|-------|
| GraphQL Types | {len(graphql_schemas)} |
| API Schemas | {len(openapi_schemas)} |
| Database Models | {len(database_schemas)} |
| Event Schemas | {len(event_schemas)} |
| Config Types | {len(config_types)} |
| Data Structures | {len(data_types)} |

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
        # Only show Database Models section if we have actual schemas
        # Skip the boilerplate placeholder text
        
        # Event Schemas section
        if event_schemas:
            content += "## Event Schemas\n\n"
            content += "These schemas define the structure of events published by this service.\n\n"
            
            for schema in event_schemas:
                content += self._format_schema_section(schema)
        
        # Config Types section (from Go code)
        if config_types:
            content += "## Configuration Types\n\n"
            content += "These types define configuration structures for each component.\n\n"
            
            # Get repo URL for linking
            repo_url = f"https://github.com/{service.repository}" if service.repository else None
            
            for go_type in config_types[:15]:
                # Extract component name from file path (e.g., cmd/monitor/main.go -> Monitor)
                file_path = go_type.get('file', '')
                component_name = ""
                if "cmd/" in file_path:
                    parts = file_path.split("/")
                    for i, part in enumerate(parts):
                        if part == "cmd" and i + 1 < len(parts):
                            component_name = parts[i + 1].replace("-", " ").title()
                            break
                
                # Better title for generic "config" types
                type_name = go_type['name']
                if type_name.lower() == "config" and component_name:
                    display_name = f"{component_name} Configuration"
                else:
                    display_name = type_name
                
                content += f"### {display_name}\n\n"
                if component_name and type_name.lower() == "config":
                    content += f"Main configuration structure for the **{component_name}** component.\n\n"
                
                # Link to GitHub source
                if repo_url and file_path:
                    github_link = f"{repo_url}/blob/main/{file_path}"
                    content += f"*Defined in: [`{file_path}`]({github_link})*\n\n"
                else:
                    content += f"*Defined in: `{file_path}`*\n\n"
                
                if go_type.get("fields"):
                    content += "| Field | Type | Tags |\n"
                    content += "|-------|------|------|\n"
                    for field in go_type["fields"][:20]:
                        name = field.get("name", "")
                        ftype = field.get("type", "unknown")
                        tags = field.get("tags", "")[:50]
                        content += f"| `{name}` | `{ftype}` | `{tags}` |\n"
                    content += "\n"
                
                content += "---\n\n"
        
        # Data Structures section (from Go code)
        if data_types:
            content += "## Data Structures\n\n"
            content += "Key data structures used by the service components.\n\n"
            
            for go_type in data_types[:20]:
                file_path = go_type.get('file', '')
                # Extract component context
                component_context = ""
                if "cmd/" in file_path:
                    parts = file_path.split("/")
                    for i, part in enumerate(parts):
                        if part == "cmd" and i + 1 < len(parts):
                            component_context = parts[i + 1].replace("-", " ").title()
                            break
                
                content += f"### {go_type['name']}\n\n"
                if component_context:
                    content += f"Used by the **{component_context}** component.\n\n"
                
                # Link to GitHub source
                if repo_url and file_path:
                    github_link = f"{repo_url}/blob/main/{file_path}"
                    content += f"*Defined in: [`{file_path}`]({github_link})*\n\n"
                else:
                    content += f"*Defined in: `{file_path}`*\n\n"
                
                if go_type.get("fields"):
                    content += "| Field | Type | Tags |\n"
                    content += "|-------|------|------|\n"
                    for field in go_type["fields"][:15]:
                        name = field.get("name", "")
                        ftype = field.get("type", "unknown")
                        tags = field.get("tags", "")[:50]
                        content += f"| `{name}` | `{ftype}` | `{tags}` |\n"
                    content += "\n"
                
                content += "---\n\n"
        
        # Only include relevant related docs links (not boilerplate)
        content += """
## Related Documents

- [Service Overview](../README.md)
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
    
    def _get_local_repo_path(self, service: Service) -> Optional[Path]:
        """Get the local path for a service's repository if it exists."""
        if not self.use_local_repos:
            return None
        
        # Extract repo name from service
        repo_name = getattr(service, 'repository', None) or service.name
        org = service.metadata.get("organization", "redmatter") if service.metadata else "redmatter"
        
        if "/" in repo_name:
            org, repo_name = repo_name.split("/", 1)
        
        # Clean up repo name
        repo_name = repo_name.replace("service:", "")
        
        # Try different paths
        for try_org in [org, "redmatter", "natterbox", "SemiConscious"]:
            path = self.local_repos_path / try_org / repo_name
            if path.exists():
                return path
        
        return None
    
    def _read_local_file(self, repo_path: Path, file_path: str) -> Optional[str]:
        """Read a file from a local repo."""
        if not repo_path:
            return None
        full_path = repo_path / file_path
        if full_path.exists():
            try:
                return full_path.read_text(errors='ignore')
            except Exception:
                return None
        return None
    
    def _find_code_files(self, repo_path: Path, patterns: list[str], max_files: int = 20) -> list[tuple[str, str]]:
        """Find code files matching patterns and return their content."""
        files = []
        if not repo_path or not repo_path.exists():
            return files
        
        for pattern in patterns:
            for file_path in repo_path.glob(pattern):
                if len(files) >= max_files:
                    break
                try:
                    content = file_path.read_text(errors='ignore')
                    rel_path = str(file_path.relative_to(repo_path))
                    files.append((rel_path, content[:8000]))  # Limit per file
                except Exception:
                    continue
        
        return files
    
    def _extract_side_effects_from_code(self, repo_path: Path) -> dict:
        """Extract side effects by analyzing code patterns."""
        effects = {
            "s3_operations": [],
            "database_operations": [],
            "api_calls": [],
            "events": [],
            "custom_types": [],
        }
        
        if not repo_path or not repo_path.exists():
            return effects
        
        # Get Go files
        go_files = self._find_code_files(repo_path, ["**/*.go"], max_files=30)
        
        for file_path, content in go_files:
            # S3 operations
            if "s3" in content.lower() or "S3" in content:
                s3_patterns = [
                    (r"S3PutObjectTagging|PutObjectTagging", "S3 Object Tagging"),
                    (r"CreateJob|s3control\.CreateJobInput", "S3 Batch Operations"),
                    (r"\.Upload\(|Upload\s*\(|s3\.Upload", "S3 Upload"),
                    (r"\.Download|GetObject", "S3 Download"),
                    (r"DeleteObject", "S3 Delete"),
                    (r"ListObjects", "S3 List"),
                ]
                for pattern, operation in s3_patterns:
                    if re.search(pattern, content):
                        if operation not in effects["s3_operations"]:
                            effects["s3_operations"].append({
                                "operation": operation,
                                "file": file_path,
                            })
            
            # Database operations
            db_patterns = [
                (r"sql\.Open|\.Query|\.Exec|mysql\.|\.QueryRow", "MySQL/SQL Database"),
                (r"dynamodb\.|DynamoDB|PutItem|GetItem|UpdateItem", "DynamoDB"),
                (r"mongo\.|MongoDB|Collection\(", "MongoDB"),
            ]
            for pattern, db_type in db_patterns:
                if re.search(pattern, content):
                    if not any(d["type"] == db_type for d in effects["database_operations"]):
                        effects["database_operations"].append({
                            "type": db_type,
                            "file": file_path,
                        })
            
            # API calls
            api_patterns = [
                (r"http\.Client|httpClient\.|\.Do\(|\.Get\(|\.Post\(", "HTTP API Calls"),
                (r"sqs\.|SQS|SendMessage|ReceiveMessage", "SQS Queue Operations"),
                (r"sns\.|SNS|Publish", "SNS Notifications"),
                (r"lambda\.|Lambda|Invoke", "Lambda Invocations"),
            ]
            for pattern, api_type in api_patterns:
                if re.search(pattern, content):
                    if not any(a["type"] == api_type for a in effects["api_calls"]):
                        effects["api_calls"].append({
                            "type": api_type,
                            "file": file_path,
                        })
            
            # Custom types (Go structs for config)
            type_matches = re.findall(r"type\s+(\w+)\s+struct\s*\{([^}]+)\}", content, re.MULTILINE)
            for name, body in type_matches:
                if "config" in name.lower() or "Config" in name:
                    effects["custom_types"].append({
                        "name": name,
                        "file": file_path,
                    })
        
        return effects
    
    async def _analyze_side_effects_with_llm(self, service: Service, repo_path: Path) -> dict:
        """Use Claude to analyze side effects from code."""
        # Read key files for analysis
        readme_content = self._read_local_file(repo_path, "README.md") or ""
        
        # Get handler/main files
        code_files = self._find_code_files(repo_path, [
            "cmd/**/handler.go",
            "cmd/**/main.go",
            "**/handler.go",
            "**/service.go",
        ], max_files=10)
        
        code_context = "\n\n".join([
            f"### {path}\n```go\n{content[:3000]}\n```"
            for path, content in code_files[:5]
        ])
        
        prompt = f"""Analyze the following code from the {service.name} service and identify ALL side effects.

README:
{readme_content[:2000]}

Key source files:
{code_context}

Identify:
1. **External System Interactions**: S3, databases, APIs, message queues
2. **Data Modifications**: What data is created, updated, or deleted
3. **Event Publishing**: Events sent to queues or topics
4. **Infrastructure Operations**: IAM role assumptions, resource creation

Return JSON with:
{{
  "s3_operations": [
    {{"operation": "Object Tagging", "description": "Tags S3 objects with purge-v2-delete=true", "target": "Cross-account S3 buckets"}}
  ],
  "database_operations": [
    {{"type": "MySQL", "operation": "Read/Update", "description": "Reads/updates retention records in Big DB"}}
  ],
  "message_queue": [
    {{"type": "SQS/SNS", "operation": "Publish/Consume", "description": "..."}}
  ],
  "api_calls": [
    {{"target": "Core API", "operation": "GET/POST", "description": "..."}}
  ],
  "iam_operations": [
    {{"operation": "AssumeRole", "description": "Assumes cross-account roles for S3 batch operations"}}
  ],
  "data_flow_description": "Brief description of the data flow through the service"
}}

Focus on ACTUAL operations found in the code, not generic patterns."""

        try:
            response = await self.call_claude(
                system_prompt="You are analyzing code to identify side effects. Return ONLY valid JSON with the requested fields. Focus on actual operations found in the code.",
                user_message=prompt,
            )
            
            # Clean up response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            return json.loads(response)
        except Exception as e:
            self.logger.warning(f"LLM analysis failed: {e}")
            return {}
    
    async def _generate_side_effects_doc(
        self,
        service: Service,
        data_dir: Path,
    ) -> str:
        """Generate the side effects document with actual code analysis."""
        service_slug = service.id.replace("service:", "")
        
        # Get service dependencies
        deps = self.graph.get_service_dependencies(service.id)
        dep_names = [d.name for d in deps] if deps else []
        
        # Get schemas to identify data operations
        schemas = self._get_service_schemas(service)
        schema_names = [s.name for s in schemas]
        
        # Try to get actual side effects from code using multi-language analyzers
        repos_dir = self.output_dir.parent / "repos"
        code_effects = {}
        repo_path = None  # Initialize to avoid unbound variable
        
        if repos_dir.exists():
            # Use new multi-language analyzer
            repo_name = getattr(service, 'repository', None) or service.name
            org = service.metadata.get("organization", "redmatter") if service.metadata else "redmatter"
            
            # Also set repo_path for LLM analysis
            for org_name in [org, "redmatter", "natterbox"]:
                potential_path = repos_dir / org_name / repo_name
                if potential_path.exists():
                    repo_path = potential_path
                    break
            
            analysis = analyze_service_repository(
                repos_dir=repos_dir,
                service_name=service.name,
                repository=repo_name,
                organizations=[org, "redmatter", "natterbox"],
            )
            
            if analysis:
                # Convert analyzer side effects to legacy format
                code_effects = get_side_effects_for_documentation(analysis)
        else:
            # Fall back to legacy extraction
            repo_path = self._get_local_repo_path(service)
            code_effects = self._extract_side_effects_from_code(repo_path) if repo_path else {}
        
        # Use LLM for deeper analysis if we have code
        llm_analysis = {}
        if repo_path:
            try:
                llm_analysis = await self._analyze_side_effects_with_llm(service, repo_path)
            except Exception as e:
                self.logger.warning(f"LLM side effects analysis failed: {e}")
        
        content = f"""---
title: {service.name} Side Effects
description: Data operations and side effects for {service.name}
generated: true
---

<!-- breadcrumb -->
[Home](/../../../index.md) > [Services](../../../services/index.md) > {service.name.replace('-', ' ').title()} > Data


# {service.name} Side Effects

This document describes the data operations performed by {service.name} and their effects on the system.

"""
        
        # S3 Operations section
        s3_ops = llm_analysis.get("s3_operations", []) or code_effects.get("s3_operations", [])
        if s3_ops:
            content += "## S3 Operations\n\n"
            content += "| Operation | Description | Target |\n"
            content += "|-----------|-------------|--------|\n"
            for op in s3_ops:
                if isinstance(op, dict):
                    operation = op.get("operation", "Unknown")
                    desc = op.get("description", "N/A")
                    target = op.get("target", op.get("file", "N/A"))
                    content += f"| {operation} | {desc} | {target} |\n"
            content += "\n"
        
        # Database Operations section
        db_ops = llm_analysis.get("database_operations", []) or code_effects.get("database_operations", [])
        if db_ops:
            content += "## Database Operations\n\n"
            content += "| Database | Operation | Description |\n"
            content += "|----------|-----------|-------------|\n"
            for op in db_ops:
                if isinstance(op, dict):
                    db_type = op.get("type", "Unknown")
                    operation = op.get("operation", "CRUD")
                    desc = op.get("description", "Data persistence")
                    content += f"| {db_type} | {operation} | {desc} |\n"
            content += "\n"
        elif schema_names:
            content += "## Database Operations\n\n"
            content += "This service performs operations on the following data models:\n\n"
            for name in schema_names[:10]:
                content += f"- **{name}**: CRUD operations\n"
            content += "\n"
        else:
            content += "## Database Operations\n\n"
            content += "*No specific database operations documented. Check source code for details.*\n\n"
        
        # Message Queue section
        mq_ops = llm_analysis.get("message_queue", [])
        if mq_ops:
            content += "## Message Queue Operations\n\n"
            content += "| Type | Operation | Description |\n"
            content += "|------|-----------|-------------|\n"
            for op in mq_ops:
                if isinstance(op, dict):
                    mq_type = op.get("type", "Unknown")
                    operation = op.get("operation", "Publish/Consume")
                    desc = op.get("description", "Message processing")
                    content += f"| {mq_type} | {operation} | {desc} |\n"
            content += "\n"
        
        # API Calls section
        api_ops = llm_analysis.get("api_calls", []) or code_effects.get("api_calls", [])
        if api_ops:
            content += "## External API Calls\n\n"
            content += "| Target | Operation | Description |\n"
            content += "|--------|-----------|-------------|\n"
            for op in api_ops:
                if isinstance(op, dict):
                    target = op.get("target", op.get("type", "Unknown"))
                    operation = op.get("operation", "HTTP")
                    desc = op.get("description", "API call")
                    content += f"| {target} | {operation} | {desc} |\n"
            content += "\n"
        
        # IAM Operations section
        iam_ops = llm_analysis.get("iam_operations", [])
        if iam_ops:
            content += "## IAM/Security Operations\n\n"
            for op in iam_ops:
                if isinstance(op, dict):
                    operation = op.get("operation", "Unknown")
                    desc = op.get("description", "IAM operation")
                    content += f"- **{operation}**: {desc}\n"
            content += "\n"
        
        # Service Dependencies
        content += "## Service Dependencies\n\n"
        if dep_names:
            content += "This service depends on the following services:\n\n"
            for name in dep_names:
                content += f"- `{name}`\n"
        else:
            content += "*No direct service dependencies identified.*\n"
        content += "\n"
        
        # Data Flow
        data_flow = llm_analysis.get("data_flow_description", "")
        if data_flow:
            content += f"## Data Flow\n\n{data_flow}\n"
        # Skip the generic Mermaid diagram - it doesn't add value
        
        content += f"""
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
