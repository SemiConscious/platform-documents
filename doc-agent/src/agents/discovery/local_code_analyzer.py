"""
Local Code Analyzer - analyzes code from local repository clones.

This replaces the API-based code analyzer to avoid GitHub rate limiting.
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from ..base import BaseAgent, AgentContext, AgentResult
from ...knowledge.models import EntityType, RelationType

logger = logging.getLogger("doc-agent.agents.local_code_analyzer")


# File patterns for different analysis types
GRAPHQL_PATTERNS = ["*.graphql", "*.gql", "schema.graphql", "schema.gql"]
OPENAPI_PATTERNS = ["openapi.yaml", "openapi.yml", "openapi.json", "swagger.yaml", "swagger.yml", "swagger.json"]
PROTO_PATTERNS = ["*.proto"]
ROUTE_PATTERNS = ["*routes*", "*router*", "*handler*", "*controller*"]

# Language-specific patterns for finding API definitions
LANGUAGE_PATTERNS = {
    "go": {
        "http_routes": [
            r'(r|router|mux)\.(Get|Post|Put|Delete|Patch|Handle|HandleFunc)\s*\(\s*["\']([^"\']+)["\']',
            r'http\.(Get|Post|Put|Delete|Patch)\s*\(\s*["\']([^"\']+)["\']',
        ],
        "graphql": [r'type\s+(\w+)\s*\{', r'type\s+(Query|Mutation|Subscription)\s*\{'],
    },
    "python": {
        "http_routes": [
            r'@(app|router|api)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            r'@route\s*\(\s*["\']([^"\']+)["\']',
        ],
        "graphql": [r'type\s+(\w+)\s*\{'],
    },
    "javascript": {
        "http_routes": [
            r'(app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            r'@(Get|Post|Put|Delete|Patch)\s*\(\s*["\']([^"\']+)["\']',
        ],
        "graphql": [r'type\s+(\w+)\s*\{'],
    },
    "typescript": {
        "http_routes": [
            r'(app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            r'@(Get|Post|Put|Delete|Patch)\s*\(\s*["\']([^"\']+)["\']',
        ],
        "graphql": [r'type\s+(\w+)\s*\{'],
    },
}


@dataclass
class EndpointInfo:
    """Information about an API endpoint."""
    method: str
    path: str
    file: str
    line: int


@dataclass 
class SchemaInfo:
    """Information about a schema/type definition."""
    name: str
    type: str  # graphql, openapi, proto
    file: str
    content: str


class LocalCodeAnalyzer(BaseAgent):
    """
    Analyzes code from local repository clones.
    
    This agent scans local filesystem instead of making API calls,
    completely avoiding GitHub rate limits.
    """
    
    name = "local_code_analyzer"
    description = "Analyzes code from local repository clones"
    version = "1.0.0"
    
    def __init__(self, context: AgentContext, repos_dir: Path):
        super().__init__(context)
        self.repos_dir = repos_dir
        
        # Configuration
        code_config = context.config.get("sources", {}).get("github", {}).get("code_analysis", {})
        self.graphql_patterns = code_config.get("graphql_patterns", GRAPHQL_PATTERNS)
        self.openapi_patterns = code_config.get("openapi_patterns", OPENAPI_PATTERNS)
        self.max_file_size = code_config.get("max_file_size", 100 * 1024)  # 100KB
    
    async def run(self) -> AgentResult:
        """Analyze all services with local clones."""
        self.logger.info("Starting local code analysis")
        
        # Get all services from knowledge graph
        services = self.context.knowledge_graph.get_entities_by_type(EntityType.SERVICE)
        self.logger.info(f"Analyzing code for {len(services)} services")
        
        endpoints_found = 0
        schemas_found = 0
        errors = []
        
        for service in services:
            try:
                # Get repo info from service - use repository attribute or fall back to name
                repo_name = getattr(service, 'repository', None) or service.name
                # Extract org from repository if it's a full name like "redmatter/repo-name"
                if '/' in repo_name:
                    org, repo_name = repo_name.split('/', 1)
                else:
                    # Default org based on metadata or fallback
                    org = service.metadata.get("organization", "redmatter") if hasattr(service, 'metadata') else "redmatter"
                
                repo_path = self.repos_dir / org / repo_name
                if not repo_path.exists():
                    # Try just the service name in different orgs
                    for try_org in ["redmatter", "natterbox"]:
                        repo_path = self.repos_dir / try_org / service.name
                        if repo_path.exists():
                            break
                    else:
                        continue  # No repo found
                
                # Analyze the repository
                endpoints, schemas = await self._analyze_repo(repo_path, service.id)
                
                # Add endpoints to graph
                from ...knowledge.models import Endpoint as EndpointModel, Schema as SchemaModel, Relation
                
                for endpoint in endpoints:
                    endpoint_id = f"endpoint:{service.name}:{endpoint.method}:{endpoint.path}"
                    endpoint_entity = EndpointModel(
                        id=endpoint_id,
                        name=f"{endpoint.method} {endpoint.path}",
                        api_id=service.id,
                        path=endpoint.path,
                        method=endpoint.method,
                        metadata={
                            "file": endpoint.file,
                            "line": endpoint.line,
                        }
                    )
                    self.context.knowledge_graph.add_entity(endpoint_entity)
                    self.context.knowledge_graph.add_relation(Relation(
                        source_id=service.id,
                        target_id=endpoint_id,
                        relation_type=RelationType.EXPOSES
                    ))
                    endpoints_found += 1
                
                # Add schemas to graph
                for schema in schemas:
                    schema_id = f"schema:{service.name}:{schema.name}"
                    schema_entity = SchemaModel(
                        id=schema_id,
                        name=schema.name,
                        schema_type=schema.type,
                        service_id=service.id,
                        metadata={
                            "file": schema.file,
                            "content_preview": schema.content[:500] if schema.content else "",
                        }
                    )
                    self.context.knowledge_graph.add_entity(schema_entity)
                    self.context.knowledge_graph.add_relation(Relation(
                        source_id=service.id,
                        target_id=schema_id,
                        relation_type=RelationType.DEFINES
                    ))
                    schemas_found += 1
                    
            except Exception as e:
                self.logger.warning(f"Error analyzing {service.name}: {e}")
                errors.append(f"{service.name}: {str(e)[:100]}")
        
        self.logger.info(f"Local code analysis complete: {endpoints_found} endpoints, {schemas_found} schemas")
        
        return AgentResult(
            success=True,
            data={
                "services_analyzed": len(services),
                "endpoints_found": endpoints_found,
                "schemas_found": schemas_found,
            },
            metadata={
                "errors": errors[:10],  # First 10 errors
            }
        )
    
    async def _analyze_repo(self, repo_path: Path, service_id: str) -> tuple[list[EndpointInfo], list[SchemaInfo]]:
        """Analyze a single repository."""
        endpoints = []
        schemas = []
        
        # Detect primary language
        language = await self._detect_language(repo_path)
        
        # Find and analyze GraphQL schemas
        graphql_files = await self._find_files(repo_path, ["*.graphql", "*.gql"])
        for gql_file in graphql_files:
            schema_info = await self._analyze_graphql_file(gql_file)
            if schema_info:
                schemas.extend(schema_info)
        
        # Find and analyze OpenAPI specs
        openapi_files = await self._find_files(repo_path, ["openapi.yaml", "openapi.yml", "openapi.json", "swagger.*"])
        for api_file in openapi_files:
            schema_info = await self._analyze_openapi_file(api_file)
            if schema_info:
                schemas.append(schema_info)
        
        # Find HTTP routes based on language
        if language in LANGUAGE_PATTERNS:
            route_endpoints = await self._find_http_routes(repo_path, language)
            endpoints.extend(route_endpoints)
        
        return endpoints, schemas
    
    async def _detect_language(self, repo_path: Path) -> str:
        """Detect the primary language of a repository."""
        # Check for language-specific files
        indicators = {
            "go": ["go.mod", "go.sum", "main.go"],
            "python": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
            "javascript": ["package.json"],
            "typescript": ["tsconfig.json"],
            "rust": ["Cargo.toml"],
            "java": ["pom.xml", "build.gradle"],
        }
        
        for lang, files in indicators.items():
            for f in files:
                if (repo_path / f).exists():
                    return lang
        
        return "unknown"
    
    async def _find_files(self, repo_path: Path, patterns: list[str]) -> list[Path]:
        """Find files matching patterns in a repository."""
        found = []
        
        for pattern in patterns:
            # Use rglob for recursive search
            if "*" in pattern:
                found.extend(repo_path.rglob(pattern))
            else:
                # Exact filename, search recursively
                found.extend(repo_path.rglob(f"**/{pattern}"))
        
        # Filter out node_modules, vendor, etc.
        exclude_dirs = {"node_modules", "vendor", ".git", "dist", "build", "__pycache__"}
        found = [
            f for f in found 
            if not any(excl in f.parts for excl in exclude_dirs)
            and f.is_file()
            and f.stat().st_size < self.max_file_size
        ]
        
        return found[:50]  # Limit to 50 files per pattern
    
    async def _analyze_graphql_file(self, file_path: Path) -> list[SchemaInfo]:
        """Analyze a GraphQL schema file."""
        schemas = []
        
        try:
            content = file_path.read_text(errors='ignore')
            
            # Find type definitions
            type_pattern = r'type\s+(\w+)\s*(?:@\w+(?:\([^)]*\))?\s*)*\{'
            matches = re.finditer(type_pattern, content)
            
            for match in matches:
                type_name = match.group(1)
                # Extract the full type definition
                start = match.start()
                brace_count = 0
                end = start
                for i, char in enumerate(content[start:]):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end = start + i + 1
                            break
                
                type_content = content[start:end]
                
                schemas.append(SchemaInfo(
                    name=type_name,
                    type="graphql",
                    file=str(file_path.relative_to(file_path.parents[2]) if len(file_path.parts) > 3 else file_path.name),
                    content=type_content
                ))
                
        except Exception as e:
            self.logger.debug(f"Error reading {file_path}: {e}")
        
        return schemas
    
    async def _analyze_openapi_file(self, file_path: Path) -> Optional[SchemaInfo]:
        """Analyze an OpenAPI specification file."""
        try:
            content = file_path.read_text(errors='ignore')
            
            return SchemaInfo(
                name="OpenAPI",
                type="openapi",
                file=str(file_path.name),
                content=content[:2000]  # First 2KB
            )
            
        except Exception as e:
            self.logger.debug(f"Error reading {file_path}: {e}")
            return None
    
    async def _find_http_routes(self, repo_path: Path, language: str) -> list[EndpointInfo]:
        """Find HTTP route definitions in source code."""
        endpoints = []
        patterns = LANGUAGE_PATTERNS.get(language, {}).get("http_routes", [])
        
        if not patterns:
            return endpoints
        
        # Find relevant source files
        extensions = {
            "go": ["*.go"],
            "python": ["*.py"],
            "javascript": ["*.js", "*.jsx"],
            "typescript": ["*.ts", "*.tsx"],
        }
        
        source_files = []
        for ext in extensions.get(language, []):
            source_files.extend(await self._find_files(repo_path, [ext]))
        
        for source_file in source_files[:100]:  # Limit files to analyze
            try:
                content = source_file.read_text(errors='ignore')
                lines = content.split('\n')
                
                for pattern in patterns:
                    for i, line in enumerate(lines):
                        matches = re.finditer(pattern, line, re.IGNORECASE)
                        for match in matches:
                            groups = match.groups()
                            if len(groups) >= 2:
                                method = groups[-2].upper() if len(groups) > 2 else "GET"
                                path = groups[-1]
                                
                                endpoints.append(EndpointInfo(
                                    method=method,
                                    path=path,
                                    file=str(source_file.relative_to(repo_path)),
                                    line=i + 1
                                ))
                                
            except Exception as e:
                self.logger.debug(f"Error analyzing {source_file}: {e}")
        
        return endpoints
