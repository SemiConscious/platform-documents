"""
API Service documentation strategy.

Produces comprehensive API documentation with:
- Detailed endpoint documentation with examples
- Request/response schemas with field descriptions
- Database side effects with actual SQL
- Authentication flow diagrams
- Error code reference tables
- Database schema reference (DDL)
"""

from pathlib import Path
from typing import Any, Optional
import re
import time

from ...analyzers.models import (
    AnalysisResult,
    ExtractedEndpoint,
    ExtractedModel,
    ExtractedSideEffect,
    ModelType,
    SideEffectCategory,
)
from ...analyzers.repo_type_detector import RepoType
from .base import (
    DocumentationStrategy,
    DocumentSpec,
    DocumentSet,
    GeneratedDocument,
    QualityCriterion,
    QualityCriterionType,
)
from .factory import register_strategy


@register_strategy(RepoType.API_SERVICE)
class APIServiceStrategy(DocumentationStrategy):
    """
    Documentation strategy for API services (REST/GraphQL).
    
    Generates beautiful, detailed API documentation including
    endpoint specs, request/response examples, and database side effects.
    """
    
    repo_type = RepoType.API_SERVICE
    name = "api_service"
    description = "API service documentation with endpoint details"
    
    def get_required_documents(self) -> list[DocumentSpec]:
        """Get required documents for API services."""
        return [
            DocumentSpec(
                path="README.md",
                title="Overview",
                description="API overview with architecture diagram",
                required=True,
                priority=1,
            ),
            DocumentSpec(
                path="api/README.md",
                title="API Reference",
                description="API overview, auth, quick start",
                required=True,
                priority=1,
            ),
            DocumentSpec(
                path="api/authentication.md",
                title="Authentication",
                description="Authentication flow with diagrams",
                required=True,
                priority=2,
            ),
            DocumentSpec(
                path="api/endpoints.md",
                title="Endpoints",
                description="All endpoints with examples",
                required=True,
                priority=2,
            ),
            DocumentSpec(
                path="architecture.md",
                title="Architecture",
                description="Component and data flow diagrams",
                required=True,
                priority=2,
            ),
            DocumentSpec(
                path="data/models.md",
                title="Data Models",
                description="Data structures with field docs",
                required=True,
                priority=3,
            ),
            DocumentSpec(
                path="data/side-effects.md",
                title="Side Effects",
                description="Database and external service operations",
                required=True,
                priority=3,
            ),
            DocumentSpec(
                path="data/database-schema.md",
                title="Database Schema",
                description="Full DDL reference",
                required=False,
                priority=4,
            ),
            DocumentSpec(
                path="configuration.md",
                title="Configuration",
                description="Environment variables and config",
                required=False,
                priority=4,
            ),
            DocumentSpec(
                path="operations.md",
                title="Operations",
                description="Health checks, monitoring, runbooks",
                required=False,
                priority=4,
            ),
        ]
    
    def get_quality_criteria(self) -> list[QualityCriterion]:
        """Get quality criteria for API services."""
        return [
            QualityCriterion(
                name="completeness",
                description="All required docs present",
                criterion_type=QualityCriterionType.COMPLETENESS,
                weight=1.0,
                min_threshold=0.90,
            ),
            QualityCriterion(
                name="endpoint_coverage",
                description="All endpoints documented with examples",
                criterion_type=QualityCriterionType.ACCURACY,
                weight=1.0,
                min_threshold=0.90,
            ),
            QualityCriterion(
                name="diagrams",
                description="Architecture and flow diagrams present",
                criterion_type=QualityCriterionType.DIAGRAMS,
                weight=0.9,
                min_threshold=0.85,
            ),
            QualityCriterion(
                name="examples",
                description="Request/response examples provided",
                criterion_type=QualityCriterionType.EXAMPLES,
                weight=0.9,
                min_threshold=0.85,
            ),
            QualityCriterion(
                name="depth",
                description="Documentation has sufficient detail",
                criterion_type=QualityCriterionType.DEPTH,
                weight=0.8,
                min_threshold=0.80,
            ),
        ]
    
    async def generate(
        self,
        repo_path: Path,
        analysis: AnalysisResult,
        service_name: str,
        github_url: Optional[str] = None,
        existing_docs: Optional[dict[str, str]] = None,
    ) -> DocumentSet:
        """Generate comprehensive API documentation."""
        start_time = time.time()
        doc_set = DocumentSet(
            repo_name=service_name,
            repo_type=self.repo_type,
        )
        
        # Categorize endpoints by domain
        endpoints_by_domain = self._categorize_endpoints(analysis.endpoints)
        
        # Extract database operations
        db_operations = self._extract_database_operations(analysis)
        
        # Extract authentication endpoints
        auth_endpoints = self._extract_auth_endpoints(analysis.endpoints)
        
        # === LLM Enrichment Phase ===
        # Use LLM to generate richer descriptions (if LLM client available)
        self.logger.info("Starting LLM enrichment phase...")
        
        enriched_endpoints = await self._enrich_endpoint_descriptions(
            analysis.endpoints, service_name
        )
        if enriched_endpoints:
            self.logger.info(f"Enriched {len(enriched_endpoints)} endpoint descriptions")
        
        enriched_models = await self._enrich_model_descriptions(
            analysis.models, service_name
        )
        if enriched_models:
            self.logger.info(f"Enriched {len(enriched_models)} model descriptions")
        
        enriched_configs = {}
        if analysis.config:
            enriched_configs = await self._enrich_config_descriptions(
                analysis.config, service_name
            )
            if enriched_configs:
                self.logger.info(f"Enriched {len(enriched_configs)} config descriptions")
        
        # === Document Generation Phase ===
        self.logger.info("Starting document generation phase...")
        
        # Generate main README
        readme = await self._generate_readme(
            repo_path, service_name, github_url, analysis, endpoints_by_domain
        )
        doc_set.add_document(readme)
        
        # Generate API README
        api_readme = await self._generate_api_readme(
            service_name, github_url, analysis, endpoints_by_domain
        )
        doc_set.add_document(api_readme)
        
        # Generate authentication docs
        if auth_endpoints:
            auth_doc = await self._generate_authentication(
                service_name, github_url, auth_endpoints, db_operations
            )
            doc_set.add_document(auth_doc)
        
        # Generate endpoint documentation with enriched descriptions
        endpoints_doc = await self._generate_endpoints(
            service_name, github_url, analysis.endpoints, db_operations,
            enriched_descriptions=enriched_endpoints
        )
        doc_set.add_document(endpoints_doc)
        
        # Generate architecture diagram
        arch_doc = await self._generate_architecture(
            service_name, github_url, analysis
        )
        doc_set.add_document(arch_doc)
        
        # Generate models documentation with enriched descriptions
        models_doc = await self._generate_models(
            service_name, github_url, analysis.models,
            enriched_models=enriched_models
        )
        doc_set.add_document(models_doc)
        
        # Generate side effects documentation
        side_effects_doc = await self._generate_side_effects(
            service_name, github_url, analysis.side_effects, db_operations
        )
        doc_set.add_document(side_effects_doc)
        
        # Generate database schema if we have DDL
        ddl_statements = self._extract_ddl(repo_path)
        if ddl_statements:
            schema_doc = await self._generate_database_schema(
                service_name, github_url, ddl_statements
            )
            doc_set.add_document(schema_doc)
        
        # Generate configuration docs with enriched descriptions
        if analysis.config:
            config_doc = await self._generate_configuration(
                service_name, github_url, analysis.config,
                enriched_configs=enriched_configs
            )
            doc_set.add_document(config_doc)
        
        # Generate operations guide
        ops_doc = await self._generate_operations(
            service_name, github_url, analysis
        )
        doc_set.add_document(ops_doc)
        
        doc_set.generation_time = time.time() - start_time
        return doc_set
    
    def _categorize_endpoints(
        self,
        endpoints: list[ExtractedEndpoint],
    ) -> dict[str, list[ExtractedEndpoint]]:
        """Categorize endpoints by domain/resource."""
        categorized = {}
        
        for endpoint in endpoints:
            # Extract domain from path
            path_parts = endpoint.path.strip("/").split("/")
            if path_parts:
                # Use first significant path segment as domain
                domain = path_parts[0] if path_parts[0] not in ["api", "v1", "v2"] else (
                    path_parts[1] if len(path_parts) > 1 else "general"
                )
            else:
                domain = "general"
            
            domain = domain.replace("-", " ").replace("_", " ").title()
            
            if domain not in categorized:
                categorized[domain] = []
            categorized[domain].append(endpoint)
        
        return categorized
    
    def _extract_auth_endpoints(
        self,
        endpoints: list[ExtractedEndpoint],
    ) -> list[ExtractedEndpoint]:
        """Extract authentication-related endpoints."""
        auth_patterns = ["auth", "login", "logout", "session", "token", "oauth", "sso"]
        auth_endpoints = []
        
        for endpoint in endpoints:
            path_lower = endpoint.path.lower()
            if any(pattern in path_lower for pattern in auth_patterns):
                auth_endpoints.append(endpoint)
        
        return auth_endpoints
    
    def _extract_database_operations(
        self,
        analysis: AnalysisResult,
    ) -> dict[str, list[ExtractedSideEffect]]:
        """Extract database operations grouped by table."""
        operations = {}
        
        for effect in analysis.side_effects:
            if effect.category == SideEffectCategory.DATABASE:
                table = effect.target or "unknown"
                if table not in operations:
                    operations[table] = []
                operations[table].append(effect)
        
        return operations
    
    def _extract_ddl(self, repo_path: Path) -> list[dict]:
        """Extract DDL statements from SQL files."""
        ddl_statements = []
        
        # Look for SQL files
        sql_files = list(repo_path.rglob("*.sql"))
        
        for sql_file in sql_files[:50]:  # Limit to prevent huge scans
            try:
                content = sql_file.read_text(errors='ignore')
                
                # Extract CREATE TABLE statements
                create_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"\[]?(\w+(?:\.\w+)?)[`"\]]?\s*\(([\s\S]*?)\);'
                
                for match in re.finditer(create_pattern, content, re.IGNORECASE):
                    table_name = match.group(1)
                    columns_def = match.group(2)
                    full_statement = match.group(0)
                    
                    ddl_statements.append({
                        "table": table_name,
                        "file": str(sql_file.relative_to(repo_path)),
                        "statement": full_statement,
                        "columns": self._parse_columns(columns_def),
                    })
            except Exception:
                pass
        
        return ddl_statements
    
    def _parse_columns(self, columns_def: str) -> list[dict]:
        """Parse column definitions from CREATE TABLE."""
        columns = []
        
        # Simple column pattern
        column_pattern = r'[`"\[]?(\w+)[`"\]]?\s+(\w+(?:\([^)]+\))?)\s*([^,]*)'
        
        for match in re.finditer(column_pattern, columns_def):
            name = match.group(1)
            data_type = match.group(2)
            constraints = match.group(3).strip()
            
            # Skip constraint definitions
            if name.upper() in ['PRIMARY', 'FOREIGN', 'UNIQUE', 'KEY', 'INDEX', 'CONSTRAINT']:
                continue
            
            columns.append({
                "name": name,
                "type": data_type,
                "constraints": constraints,
                "nullable": "NOT NULL" not in constraints.upper(),
            })
        
        return columns
    
    async def _enrich_endpoint_descriptions(
        self,
        endpoints: list[ExtractedEndpoint],
        service_name: str,
    ) -> dict[str, str]:
        """Use LLM to generate better endpoint descriptions."""
        if not self.llm_client or not endpoints:
            return {}
        
        # Batch endpoints for efficiency (max 20 at a time)
        enriched = {}
        batch_size = 20
        
        for i in range(0, min(len(endpoints), 60), batch_size):  # Limit to 60 endpoints total
            batch = endpoints[i:i + batch_size]
            
            endpoints_text = "\n".join([
                f"- {ep.method} {ep.path} (handler: {ep.handler or 'unknown'})"
                for ep in batch
            ])
            
            prompt = f"""For the {service_name} API, provide brief (1-2 sentence) descriptions for these endpoints.
Format: One line per endpoint: "METHOD /path: description"

Endpoints:
{endpoints_text}

Based on the handler names and paths, describe what each endpoint likely does.
Only output the descriptions, no preamble."""

            try:
                response = await self._call_llm(
                    prompt=prompt,
                    system_prompt="You are an API documentation expert. Generate clear, concise endpoint descriptions.",
                    max_tokens=2000,
                    operation=f"enrich_endpoints_{i}",
                    operation_type="extraction",  # Uses cost-efficient model for structured extraction
                )
                
                # Parse response
                for line in response.strip().split("\n"):
                    if ": " in line:
                        path_part, desc = line.split(": ", 1)
                        # Extract path from "METHOD /path"
                        parts = path_part.strip().split(" ", 1)
                        if len(parts) == 2:
                            key = f"{parts[0]} {parts[1]}"
                            enriched[key] = desc.strip()
                            
            except Exception as e:
                self.logger.warning(f"Failed to enrich endpoints: {e}")
        
        return enriched
    
    async def _enrich_model_descriptions(
        self,
        models: list[ExtractedModel],
        service_name: str,
    ) -> dict[str, dict]:
        """Use LLM to generate better model and field descriptions."""
        if not self.llm_client or not models:
            return {}
        
        enriched = {}
        
        # Process top 30 models
        for model in models[:30]:
            if not model.fields:
                continue
            
            fields_text = "\n".join([
                f"  - {f.name}: {f.type}"
                for f in model.fields[:15]
            ])
            
            prompt = f"""For the {service_name} data model "{model.name}", provide:
1. A brief description of what this model represents (1-2 sentences)
2. Descriptions for each field (1 sentence each)

Model: {model.name}
File: {model.file}
Fields:
{fields_text}

Format your response as:
MODEL_DESCRIPTION: <description>
FIELD <field_name>: <description>"""

            try:
                response = await self._call_llm(
                    prompt=prompt,
                    system_prompt="You are a database/API documentation expert. Generate clear descriptions based on naming conventions.",
                    max_tokens=1500,
                    operation=f"enrich_model_{model.name}",
                    operation_type="extraction",  # Uses cost-efficient model for structured extraction
                )
                
                model_info = {"description": "", "fields": {}}
                
                for line in response.strip().split("\n"):
                    if line.startswith("MODEL_DESCRIPTION:"):
                        model_info["description"] = line.split(":", 1)[1].strip()
                    elif line.startswith("FIELD "):
                        parts = line[6:].split(":", 1)
                        if len(parts) == 2:
                            model_info["fields"][parts[0].strip()] = parts[1].strip()
                
                enriched[model.name] = model_info
                
            except Exception as e:
                self.logger.warning(f"Failed to enrich model {model.name}: {e}")
        
        return enriched
    
    async def _enrich_config_descriptions(
        self,
        configs: list,
        service_name: str,
    ) -> dict[str, str]:
        """Use LLM to generate better config/environment variable descriptions."""
        if not self.llm_client or not configs:
            return {}
        
        config_text = "\n".join([
            f"- {c.key}: {c.default or 'no default'}"
            for c in configs[:40]
        ])
        
        prompt = f"""For the {service_name} service, provide descriptions for these configuration/environment variables.
Format: One line per variable: "VARIABLE_NAME: description"

Variables:
{config_text}

Based on the naming conventions, describe what each variable configures.
Only output the descriptions, no preamble."""

        try:
            response = await self._call_llm(
                prompt=prompt,
                system_prompt="You are a DevOps documentation expert. Generate clear config descriptions.",
                max_tokens=2000,
                operation="enrich_configs",
                operation_type="extraction",  # Uses cost-efficient model for structured extraction
            )
            
            enriched = {}
            for line in response.strip().split("\n"):
                if ": " in line:
                    key, desc = line.split(": ", 1)
                    enriched[key.strip()] = desc.strip()
            
            return enriched
            
        except Exception as e:
            self.logger.warning(f"Failed to enrich configs: {e}")
            return {}
    
    def _clean_ddl_statement(self, ddl: str) -> str:
        """Clean DDL statement by removing MySQL-specific comments and directives."""
        import re
        
        # Remove MySQL conditional comments like /*!40101 ... */
        cleaned = re.sub(r'/\*!\d+[^*]*\*/', '', ddl)
        
        # Remove MySQL SET statements
        cleaned = re.sub(r'SET\s+@\w+\s*=\s*[^;]+;', '', cleaned)
        cleaned = re.sub(r'SET\s+\w+\s*=\s*[^;]+;', '', cleaned)
        
        # Remove multiple blank lines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in cleaned.split('\n')]
        cleaned = '\n'.join(line for line in lines if line)
        
        return cleaned.strip()
    
    async def _generate_readme(
        self,
        repo_path: Path,
        service_name: str,
        github_url: Optional[str],
        analysis: AnalysisResult,
        endpoints_by_domain: dict,
    ) -> GeneratedDocument:
        """Generate main README with overview."""
        content = f"""---
title: {service_name}
description: API service documentation
generated: true
type: api_service
---

# {service_name}

## Overview

{service_name} is an API service that provides programmatic access to platform functionality.

"""
        
        # Architecture diagram
        content += "## Architecture\n\n"
        content += "```mermaid\nflowchart TB\n"
        content += "    Client[Client Application]\n"
        content += f"    API[{service_name}]\n"
        content += "    DB[(Database)]\n"
        content += "    Cache[(Cache)]\n"
        content += "    Queue[Message Queue]\n\n"
        content += "    Client --> API\n"
        content += "    API --> DB\n"
        content += "    API --> Cache\n"
        content += "    API --> Queue\n"
        content += "```\n\n"
        
        # Quick facts
        content += "## Quick Facts\n\n"
        content += "| Metric | Value |\n"
        content += "|--------|-------|\n"
        content += f"| Language | {analysis.language or 'N/A'} |\n"
        content += f"| Total Endpoints | {len(analysis.endpoints)} |\n"
        content += f"| API Domains | {len(endpoints_by_domain)} |\n"
        content += f"| Data Models | {len(analysis.models)} |\n\n"
        
        # Endpoint summary by domain
        if endpoints_by_domain:
            content += "## API Domains\n\n"
            content += "| Domain | Endpoints | Description |\n"
            content += "|--------|-----------|-------------|\n"
            for domain, endpoints in sorted(endpoints_by_domain.items()):
                methods = set(e.method for e in endpoints)
                content += f"| {domain} | {len(endpoints)} | {', '.join(methods)} operations |\n"
            content += "\n"
        
        # Documentation index
        content += "## Documentation\n\n"
        content += "| Document | Description |\n"
        content += "|----------|-------------|\n"
        content += "| [API Reference](./api/README.md) | Complete API documentation |\n"
        content += "| [Authentication](./api/authentication.md) | Auth flow and examples |\n"
        content += "| [Endpoints](./api/endpoints.md) | All endpoints with examples |\n"
        content += "| [Architecture](./architecture.md) | System architecture |\n"
        content += "| [Data Models](./data/models.md) | Data structures |\n"
        content += "| [Database](./data/database-schema.md) | Schema reference |\n"
        content += "| [Operations](./operations.md) | Deployment and monitoring |\n\n"
        
        if github_url:
            content += f"## Source\n\n- [Repository]({github_url})\n"
        
        return GeneratedDocument(
            path="README.md",
            title=f"{service_name} Overview",
            content=content,
        )
    
    async def _generate_api_readme(
        self,
        service_name: str,
        github_url: Optional[str],
        analysis: AnalysisResult,
        endpoints_by_domain: dict,
    ) -> GeneratedDocument:
        """Generate API reference overview."""
        content = f"""---
title: {service_name} API Reference
description: Complete API documentation
generated: true
---

# {service_name} API Reference

## Base URL

```
https://api.example.com/v1
```

## Authentication

All API requests require authentication via session token or API key.

```http
Authorization: Bearer <token>
```

Or via session cookie for browser-based clients.

## Quick Start

### 1. Authenticate

```bash
curl -X POST https://api.example.com/v1/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{{"username": "user@example.com", "password": "secret"}}'
```

### 2. Make Requests

```bash
curl https://api.example.com/v1/users/me \\
  -H "Authorization: Bearer <token>"
```

## API Index

"""
        
        # List all domains with their endpoints
        for domain, endpoints in sorted(endpoints_by_domain.items()):
            content += f"### {domain}\n\n"
            content += "| Method | Path | Description |\n"
            content += "|--------|------|-------------|\n"
            for endpoint in endpoints:
                desc = endpoint.description or "No description"
                if len(desc) > 50:
                    desc = desc[:47] + "..."
                content += f"| `{endpoint.method}` | `{endpoint.path}` | {desc} |\n"
            content += "\n"
        
        # Error codes
        content += """## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing or invalid auth |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource already exists |
| 422 | Validation Error - Invalid data |
| 500 | Server Error |

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid data",
    "details": [
      {"field": "email", "message": "Invalid email format"}
    ]
  }
}
```
"""
        
        return GeneratedDocument(
            path="api/README.md",
            title=f"{service_name} API Reference",
            content=content,
        )
    
    async def _generate_authentication(
        self,
        service_name: str,
        github_url: Optional[str],
        auth_endpoints: list[ExtractedEndpoint],
        db_operations: dict,
    ) -> GeneratedDocument:
        """Generate authentication documentation."""
        content = f"""---
title: {service_name} Authentication
description: Authentication flow and examples
generated: true
---

# {service_name} Authentication

## Overview

This API uses session-based authentication. Clients authenticate with credentials and receive a session token for subsequent requests.

## Authentication Flow

```
┌──────────┐                              ┌──────────┐                    ┌──────────┐
│  Client  │                              │   API    │                    │ Database │
└────┬─────┘                              └────┬─────┘                    └────┬─────┘
     │                                         │                               │
     │  POST /auth/login                       │                               │
     │  {{username, password}}                 │                               │
     │────────────────────────────────────────>│                               │
     │                                         │  Validate credentials         │
     │                                         │──────────────────────────────>│
     │                                         │                               │
     │                                         │  User + permissions           │
     │                                         │<──────────────────────────────│
     │                                         │                               │
     │                                         │  Create session               │
     │                                         │──────────────────────────────>│
     │                                         │                               │
     │  Set-Cookie: session=<token>            │                               │
     │<────────────────────────────────────────│                               │
     │                                         │                               │
     │  GET /api/resource                      │                               │
     │  Cookie: session=<token>                │                               │
     │────────────────────────────────────────>│                               │
     │                                         │  Validate session             │
     │                                         │──────────────────────────────>│
     │                                         │                               │
     │  200 OK {{data}}                        │                               │
     │<────────────────────────────────────────│                               │
     │                                         │                               │
```

## Authentication Endpoints

"""
        
        for endpoint in auth_endpoints:
            content += f"### {endpoint.method} {endpoint.path}\n\n"
            content += f"{endpoint.description or 'No description available.'}\n\n"
            
            # Request
            content += "**Request:**\n\n"
            content += f"```http\n{endpoint.method} {endpoint.path} HTTP/1.1\n"
            content += "Host: api.example.com\n"
            content += "Content-Type: application/json\n\n"
            
            # Generate example request body for POST/PUT
            if endpoint.method in ["POST", "PUT"]:
                if "login" in endpoint.path.lower():
                    content += """{
  "username": "user@example.com",
  "password": "secret123"
}
```\n\n"""
                elif "logout" in endpoint.path.lower():
                    content += "```\n\n"
                else:
                    content += "{}\n```\n\n"
            else:
                content += "```\n\n"
            
            # Response
            content += "**Response:**\n\n"
            content += "```http\nHTTP/1.1 200 OK\n"
            content += "Content-Type: application/json\n"
            if "login" in endpoint.path.lower():
                content += "Set-Cookie: session=<token>; HttpOnly; Secure\n"
            content += "\n"
            
            if "login" in endpoint.path.lower():
                content += """{
  "success": true,
  "user": {
    "id": 12345,
    "email": "user@example.com",
    "name": "John Doe",
    "permissions": ["read", "write"]
  }
}
```\n\n"""
            else:
                content += '{"success": true}\n```\n\n'
            
            # Database side effects
            if endpoint.handler:
                handler_ops = []
                for table, ops in db_operations.items():
                    for op in ops:
                        # Match side effects to endpoints by file or description
                        op_file = op.file or ""
                        op_desc = op.description or ""
                        if endpoint.handler in op_file or endpoint.handler in op_desc:
                            handler_ops.append((table, op))
                
                if handler_ops:
                    content += "**Database Side Effects:**\n\n"
                    for table, op in handler_ops:
                        content += f"- `{op.operation}` on `{table}`\n"
                    content += "\n"
            
            content += "---\n\n"
        
        # Session management
        content += """## Session Management

### Session Storage

Sessions are stored in the database with the following structure:

| Column | Type | Description |
|--------|------|-------------|
| session_id | VARCHAR(64) | Unique session identifier |
| user_id | INT | Associated user |
| created_at | TIMESTAMP | Session creation time |
| expires_at | TIMESTAMP | Session expiration |
| ip_address | VARCHAR(45) | Client IP |
| user_agent | TEXT | Client user agent |

### Session Expiration

- Default session lifetime: 24 hours
- Inactive timeout: 2 hours
- Sessions can be refreshed with activity

## Security Considerations

- All authentication endpoints require HTTPS
- Passwords are hashed using bcrypt
- Failed login attempts are rate-limited
- Sessions are invalidated on password change
"""
        
        return GeneratedDocument(
            path="api/authentication.md",
            title=f"{service_name} Authentication",
            content=content,
        )
    
    async def _generate_endpoints(
        self,
        service_name: str,
        github_url: Optional[str],
        endpoints: list[ExtractedEndpoint],
        db_operations: dict,
        enriched_descriptions: Optional[dict[str, str]] = None,
    ) -> GeneratedDocument:
        """Generate comprehensive endpoint documentation."""
        enriched_descriptions = enriched_descriptions or {}
        
        content = f"""---
title: {service_name} Endpoints
description: All API endpoints with examples
generated: true
---

# {service_name} Endpoints

## Overview

This document provides detailed documentation for all API endpoints.

## Endpoints

"""
        
        # Group by path prefix for organization
        for endpoint in sorted(endpoints, key=lambda e: (e.path, e.method)):
            content += f"### {endpoint.method} {endpoint.path}\n\n"
            
            # Use enriched description if available, else original or fallback
            endpoint_key = f"{endpoint.method} {endpoint.path}"
            description = enriched_descriptions.get(endpoint_key) or endpoint.description or "No description available."
            content += f"{description}\n\n"
            
            # Source link
            if github_url and endpoint.file:
                line_anchor = f"#L{endpoint.line}" if endpoint.line else ""
                content += f"**Source:** [{endpoint.file}]({github_url}/blob/main/{endpoint.file}{line_anchor})\n\n"
            
            # Handler info
            if endpoint.handler:
                content += f"**Handler:** `{endpoint.handler}`\n\n"
            
            # Parameters
            if endpoint.parameters:
                content += "**Parameters:**\n\n"
                content += "| Name | Type | Required | Description |\n"
                content += "|------|------|----------|-------------|\n"
                for param in endpoint.parameters:
                    required = "Yes" if param.required else "No"
                    desc = param.description or "No description"
                    content += f"| `{param.name}` | {param.type} | {required} | {desc} |\n"
                content += "\n"
            
            # Request example
            content += "**Request:**\n\n"
            content += f"```http\n{endpoint.method} {endpoint.path} HTTP/1.1\n"
            content += "Host: api.example.com\n"
            content += "Authorization: Bearer <token>\n"
            
            if endpoint.method in ["POST", "PUT", "PATCH"]:
                content += "Content-Type: application/json\n\n"
                # Generate sample request body from parameters if available
                if endpoint.parameters:
                    params_dict = {}
                    for param in endpoint.parameters:
                        if isinstance(param, dict):
                            params_dict[param.get("name", "field")] = param.get("type", "string")
                        else:
                            params_dict["data"] = "value"
                    content += self._generate_json_example(params_dict)
                else:
                    content += "{}\n"
            content += "```\n\n"
            
            # Response example
            content += "**Response:**\n\n"
            content += "```http\nHTTP/1.1 200 OK\n"
            content += "Content-Type: application/json\n\n"
            if endpoint.response_type:
                content += f'{{"data": {{"type": "{endpoint.response_type}"}}}}\n'
            else:
                content += '{"success": true}\n'
            content += "```\n\n"
            
            # Database side effects for this endpoint
            if endpoint.handler:
                handler_effects = []
                for table, ops in db_operations.items():
                    for op in ops:
                        # ExtractedSideEffect doesn't have handler, use file/description for matching
                        op_file = op.file or ""
                        op_desc = op.description or ""
                        if endpoint.handler in op_file or endpoint.handler in op_desc or endpoint.path in op_desc:
                            handler_effects.append((table, op))
                
                if handler_effects:
                    content += "**Database Side Effects:**\n\n"
                    content += "| Table | Operation | Details |\n"
                    content += "|-------|-----------|--------|\n"
                    for table, op in handler_effects:
                        details = op.description or "N/A"
                        if len(details) > 50:
                            details = details[:47] + "..."
                        content += f"| `{table}` | {op.operation} | {details} |\n"
                    content += "\n"
            
            content += "---\n\n"
        
        return GeneratedDocument(
            path="api/endpoints.md",
            title=f"{service_name} Endpoints",
            content=content,
        )
    
    def _generate_json_example(self, schema: dict) -> str:
        """Generate a JSON example from a schema."""
        import json
        
        def generate_value(field_schema):
            field_type = field_schema.get("type", "string")
            if field_type == "string":
                return "example"
            elif field_type == "integer" or field_type == "int":
                return 123
            elif field_type == "number" or field_type == "float":
                return 12.34
            elif field_type == "boolean" or field_type == "bool":
                return True
            elif field_type == "array":
                return []
            elif field_type == "object":
                return {}
            return "value"
        
        example = {}
        for key, value in schema.items():
            if isinstance(value, dict):
                example[key] = generate_value(value)
            else:
                example[key] = "value"
        
        return json.dumps(example, indent=2) + "\n"
    
    async def _generate_architecture(
        self,
        service_name: str,
        github_url: Optional[str],
        analysis: AnalysisResult,
    ) -> GeneratedDocument:
        """Generate architecture documentation."""
        content = f"""---
title: {service_name} Architecture
description: System architecture and design
generated: true
---

# {service_name} Architecture

## Component Diagram

```mermaid
flowchart TB
    subgraph Clients
        Web[Web Browser]
        Mobile[Mobile App]
        Service[Other Services]
    end
    
    subgraph LoadBalancer[Load Balancer]
        LB[ALB/NLB]
    end
    
    subgraph API[{service_name}]
        Router[Request Router]
        Auth[Auth Middleware]
        Controllers[Controllers]
        Services[Services]
        Models[Models]
    end
    
    subgraph Data[Data Layer]
        DB[(Primary Database)]
        Cache[(Redis Cache)]
        Queue[Message Queue]
    end
    
    Web --> LB
    Mobile --> LB
    Service --> LB
    LB --> Router
    Router --> Auth
    Auth --> Controllers
    Controllers --> Services
    Services --> Models
    Models --> DB
    Services --> Cache
    Services --> Queue
```

## Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant R as Router
    participant A as Auth
    participant Ctrl as Controller
    participant S as Service
    participant DB as Database
    
    C->>R: HTTP Request
    R->>A: Validate Auth
    A->>A: Check Token/Session
    A->>Ctrl: Authorized Request
    Ctrl->>Ctrl: Validate Input
    Ctrl->>S: Business Logic
    S->>DB: Data Operations
    DB-->>S: Results
    S-->>Ctrl: Processed Data
    Ctrl-->>C: JSON Response
```

## Component Descriptions

"""
        
        # Controllers/Handlers - filter by name pattern since ModelType doesn't have CONTROLLER
        controllers = [m for m in analysis.models 
                       if m.model_type == ModelType.CLASS and "Controller" in m.name]
        if controllers:
            content += "### Controllers\n\n"
            content += "| Controller | File | Endpoints |\n"
            content += "|------------|------|----------|\n"
            for ctrl in controllers[:20]:
                file_link = self._github_link(github_url, ctrl.file) if github_url else ctrl.file
                # Count endpoints for this controller
                ep_count = sum(1 for e in analysis.endpoints if e.handler and ctrl.name in e.handler)
                content += f"| {ctrl.name} | {file_link} | {ep_count} |\n"
            content += "\n"
        
        # Services/Models - filter classes that aren't controllers
        services = [m for m in analysis.models 
                    if m.model_type == ModelType.CLASS and "Controller" not in m.name]
        if services:
            content += "### Services\n\n"
            content += "| Service | Description | File |\n"
            content += "|---------|-------------|------|\n"
            for svc in services[:20]:
                file_link = self._github_link(github_url, svc.file) if github_url else svc.file
                desc = svc.description or "N/A"
                if len(desc) > 50:
                    desc = desc[:47] + "..."
                content += f"| {svc.name} | {desc} | {file_link} |\n"
            content += "\n"
        
        # Data flow
        content += """## Data Flow

1. **Request Reception**: Load balancer routes request to available instance
2. **Authentication**: Middleware validates session/token
3. **Authorization**: Permissions checked against resource
4. **Validation**: Input parameters validated
5. **Processing**: Business logic executed
6. **Data Access**: Database/cache operations
7. **Response**: JSON response returned to client

## Integration Points

"""
        
        # External dependencies (valid categories: HTTP, QUEUE, FILE, CACHE, EXTERNAL_API, CLOUD_SERVICE)
        external = [e for e in analysis.side_effects if e.category in [
            SideEffectCategory.HTTP,
            SideEffectCategory.QUEUE,
            SideEffectCategory.FILE,
            SideEffectCategory.EXTERNAL_API,
            SideEffectCategory.CLOUD_SERVICE,
        ]]
        
        if external:
            content += "| System | Operation | Description |\n"
            content += "|--------|-----------|-------------|\n"
            for ext in external[:15]:
                content += f"| {ext.target or 'External'} | {ext.operation} | {ext.description or 'N/A'} |\n"
            content += "\n"
        
        return GeneratedDocument(
            path="architecture.md",
            title=f"{service_name} Architecture",
            content=content,
        )
    
    async def _generate_models(
        self,
        service_name: str,
        github_url: Optional[str],
        models: list[ExtractedModel],
        enriched_models: Optional[dict[str, dict]] = None,
    ) -> GeneratedDocument:
        """Generate data models documentation."""
        enriched_models = enriched_models or {}
        
        content = f"""---
title: {service_name} Data Models
description: Data structures and schemas
generated: true
---

# {service_name} Data Models

## Overview

This document describes the data models used throughout the API.

## Models

"""
        
        # Filter to relevant models (exclude controllers, helpers, etc.)
        # Valid ModelTypes: CLASS, STRUCT, INTERFACE, TYPE_ALIAS, ENUM, TRAIT, PROTOCOL, DATACLASS, PYDANTIC, SCHEMA
        data_models = [m for m in models if m.model_type in [
            ModelType.STRUCT, ModelType.CLASS, ModelType.INTERFACE, 
            ModelType.DATACLASS, ModelType.PYDANTIC, ModelType.SCHEMA
        ]]
        
        for model in data_models[:50]:  # Limit to prevent huge docs
            content += f"### {model.name}\n\n"
            
            # Use enriched description if available
            enriched_info = enriched_models.get(model.name, {})
            model_desc = enriched_info.get("description") or model.description or "No description available."
            content += f"{model_desc}\n\n"
            
            # Source link
            if github_url and model.file:
                line_anchor = f"#L{model.line}" if model.line else ""
                content += f"**Source:** [{model.file}]({github_url}/blob/main/{model.file}{line_anchor})\n\n"
            
            # Fields table
            if model.fields:
                enriched_fields = enriched_info.get("fields", {})
                content += "| Field | Type | Required | Description |\n"
                content += "|-------|------|----------|-------------|\n"
                for field in model.fields:
                    # Use enriched field description if available
                    desc = enriched_fields.get(field.name) or field.description or "N/A"
                    required = "Yes" if field.required else "No"
                    default_info = f" (default: {field.default})" if field.default else ""
                    content += f"| `{field.name}` | {field.type} | {required} | {desc}{default_info} |\n"
                content += "\n"
            
            content += "---\n\n"
        
        return GeneratedDocument(
            path="data/models.md",
            title=f"{service_name} Data Models",
            content=content,
        )
    
    async def _generate_side_effects(
        self,
        service_name: str,
        github_url: Optional[str],
        side_effects: list[ExtractedSideEffect],
        db_operations: dict,
    ) -> GeneratedDocument:
        """Generate side effects documentation."""
        content = f"""---
title: {service_name} Side Effects
description: Database and external service operations
generated: true
---

# {service_name} Side Effects

## Overview

This document describes all external operations performed by the API.

## Database Operations

"""
        
        if db_operations:
            for table, ops in sorted(db_operations.items()):
                content += f"### {table}\n\n"
                content += "| Operation | File | Description |\n"
                content += "|-----------|------|-------------|\n"
                for op in ops:
                    # ExtractedSideEffect has: category, operation, target, file, line, description
                    file_ref = op.file or "N/A"
                    desc = op.description or "N/A"
                    if len(desc) > 50:
                        desc = desc[:47] + "..."
                    content += f"| {op.operation} | `{file_ref}` | {desc} |\n"
                content += "\n"
        else:
            content += "*No database operations detected.*\n\n"
        
        # Other side effects
        content += "## External Services\n\n"
        
        # Handle category being either enum or string
        def get_cat_str(cat):
            return cat.value if hasattr(cat, 'value') else str(cat)
        
        external = [e for e in side_effects 
                    if get_cat_str(e.category) != get_cat_str(SideEffectCategory.DATABASE)]
        
        if external:
            # Group by category
            by_category = {}
            for eff in external:
                cat = get_cat_str(eff.category)
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(eff)
            
            for category, effects in sorted(by_category.items()):
                content += f"### {category.title()}\n\n"
                content += "| Target | Operation | File |\n"
                content += "|--------|-----------|------|\n"
                for eff in effects:
                    target = eff.target or "N/A"
                    file_ref = eff.file or "N/A"
                    content += f"| {target} | {eff.operation} | `{file_ref}` |\n"
                content += "\n"
        else:
            content += "*No external service calls detected.*\n\n"
        
        return GeneratedDocument(
            path="data/side-effects.md",
            title=f"{service_name} Side Effects",
            content=content,
        )
    
    async def _generate_database_schema(
        self,
        service_name: str,
        github_url: Optional[str],
        ddl_statements: list[dict],
    ) -> GeneratedDocument:
        """Generate database schema documentation with DDL."""
        content = f"""---
title: {service_name} Database Schema
description: Database schema reference
generated: true
---

# {service_name} Database Schema

## Overview

This document provides the complete database schema reference.

## Database Architecture

```mermaid
erDiagram
"""
        
        # Generate ER diagram from DDL
        for ddl in ddl_statements[:20]:
            table_name = ddl["table"].replace(".", "_")
            content += f"    {table_name} {{\n"
            for col in ddl["columns"][:10]:
                col_type = col["type"].upper().split("(")[0]
                nullable = "NULL" if col["nullable"] else "NOT_NULL"
                content += f"        {col_type} {col['name']} \"{nullable}\"\n"
            content += "    }\n"
        
        content += "```\n\n"
        
        # Table documentation
        content += "## Tables\n\n"
        
        for ddl in ddl_statements:
            content += f"### {ddl['table']}\n\n"
            
            if github_url:
                content += f"**Defined in:** [{ddl['file']}]({github_url}/blob/main/{ddl['file']})\n\n"
            
            # Columns table
            if ddl["columns"]:
                content += "| Column | Type | Nullable | Constraints |\n"
                content += "|--------|------|----------|-------------|\n"
                for col in ddl["columns"]:
                    nullable = "Yes" if col["nullable"] else "No"
                    constraints = col["constraints"] or "None"
                    if len(constraints) > 30:
                        constraints = constraints[:27] + "..."
                    content += f"| `{col['name']}` | {col['type']} | {nullable} | {constraints} |\n"
                content += "\n"
            
            # Full DDL (cleaned of MySQL conditional comments)
            clean_ddl = self._clean_ddl_statement(ddl['statement'])
            content += "**DDL:**\n\n"
            content += f"```sql\n{clean_ddl}\n```\n\n"
            
            content += "---\n\n"
        
        return GeneratedDocument(
            path="data/database-schema.md",
            title=f"{service_name} Database Schema",
            content=content,
        )
    
    async def _generate_configuration(
        self,
        service_name: str,
        github_url: Optional[str],
        config: list,
        enriched_configs: Optional[dict[str, str]] = None,
    ) -> GeneratedDocument:
        """Generate configuration documentation."""
        enriched_configs = enriched_configs or {}
        
        content = f"""---
title: {service_name} Configuration
description: Environment variables and configuration
generated: true
---

# {service_name} Configuration

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
"""
        
        for cfg in config:
            required = "Yes" if getattr(cfg, 'required', False) else "No"
            default = cfg.default if cfg.default else "None"
            # Use enriched description if available
            desc = enriched_configs.get(cfg.key) or getattr(cfg, 'description', None) or "N/A"
            content += f"| `{cfg.key}` | {desc} | {required} | {default} |\n"
        
        content += "\n## Configuration Files\n\n"
        content += "Configuration can be provided via:\n\n"
        content += "1. Environment variables\n"
        content += "2. `.env` file in the application root\n"
        content += "3. Configuration file (YAML/JSON)\n"
        
        return GeneratedDocument(
            path="configuration.md",
            title=f"{service_name} Configuration",
            content=content,
        )
    
    async def _generate_operations(
        self,
        service_name: str,
        github_url: Optional[str],
        analysis: AnalysisResult,
    ) -> GeneratedDocument:
        """Generate operations guide."""
        content = f"""---
title: {service_name} Operations
description: Deployment, monitoring, and troubleshooting
generated: true
---

# {service_name} Operations

## Health Checks

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Basic health check |
| `/health/ready` | GET | Readiness probe |
| `/health/live` | GET | Liveness probe |

### Health Check Response

```json
{{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {{
    "database": "ok",
    "cache": "ok",
    "queue": "ok"
  }}
}}
```

## Monitoring

### Key Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests |
| `http_request_duration_seconds` | Histogram | Request latency |
| `http_requests_in_flight` | Gauge | Current active requests |
| `db_connections_active` | Gauge | Active database connections |

### Recommended Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| High Error Rate | error_rate > 5% | Critical |
| High Latency | p99 > 2s | Warning |
| Low Availability | success_rate < 99% | Critical |

## Troubleshooting

### Common Issues

| Issue | Symptoms | Resolution |
|-------|----------|------------|
| Database connection timeout | Slow responses, 500 errors | Check DB connection pool, verify credentials |
| Authentication failures | 401 errors | Verify token validity, check session storage |
| High memory usage | OOM errors | Review memory limits, check for leaks |

### Diagnostic Commands

```bash
# Check application logs
kubectl logs -f deployment/{service_name}

# Check database connectivity
curl http://localhost:8080/health/db

# View active connections
netstat -an | grep ESTABLISHED

# Check resource usage
kubectl top pods -l app={service_name}
```

## Deployment

### Prerequisites

- Kubernetes cluster
- Database instance
- Redis cache
- Environment secrets configured

### Deployment Steps

```bash
# Build and push image
docker build -t {service_name}:latest .
docker push registry.example.com/{service_name}:latest

# Deploy to Kubernetes
kubectl apply -f k8s/deployment.yaml

# Verify deployment
kubectl rollout status deployment/{service_name}
```

## Runbooks

### Restart Service

```bash
kubectl rollout restart deployment/{service_name}
```

### Scale Service

```bash
kubectl scale deployment/{service_name} --replicas=5
```

### Database Migration

```bash
kubectl exec -it deployment/{service_name} -- ./migrate up
```
"""
        
        return GeneratedDocument(
            path="operations.md",
            title=f"{service_name} Operations",
            content=content,
        )
