"""Code Analyzer Agent - deep analysis of source code to extract APIs and schemas."""

import asyncio
import fnmatch
import logging
from typing import Any, Optional

from ..base import BaseAgent, AgentResult, AgentContext
from ...knowledge import (
    Service,
    API,
    Endpoint,
    Schema,
    Relation,
    RelationType,
)
from ...mcp.github import GitHubClient
from ...parsers import (
    GraphQLParser,
    GraphQLSchema,
    OpenAPIParser,
    OpenAPISpec,
    RouteExtractor,
    ExtractedRoute,
)

logger = logging.getLogger("doc-agent.agents.discovery.code_analyzer")


class CodeAnalyzerAgent(BaseAgent):
    """
    Agent that performs deep code analysis to extract API details.
    
    Responsibilities:
    - Find and parse GraphQL schema files
    - Find and parse OpenAPI/Swagger specifications
    - Extract routes from source code when no spec exists
    - Create detailed Endpoint and Schema entities in the knowledge graph
    """
    
    name = "code_analyzer"
    description = "Analyzes source code to extract detailed API information"
    version = "0.1.0"
    
    def __init__(self, context: AgentContext, service_id: Optional[str] = None):
        super().__init__(context)
        self.github = GitHubClient(self.mcp)
        self.service_id = service_id
        
        # Parsers
        self.graphql_parser = GraphQLParser()
        self.openapi_parser = OpenAPIParser()
        self.route_extractor = RouteExtractor()
        
        # Configuration
        source_config = context.config.get("sources", {}).get("github", {})
        code_analysis = source_config.get("code_analysis", {})
        
        self.graphql_patterns = code_analysis.get("graphql_patterns", [
            "**/*.graphql",
            "**/schema.graphql",
            "**/schema/*.graphql",
        ])
        self.openapi_patterns = code_analysis.get("openapi_patterns", [
            "openapi*.json",
            "openapi*.yaml",
            "openapi*.yml",
            "swagger*.json",
            "swagger*.yaml",
        ])
        self.route_patterns = code_analysis.get("route_patterns", [
            "**/routes/**/*.ts",
            "**/routes/**/*.js",
            "**/controllers/**/*.ts",
            "**/handlers/**/*.go",
            "**/api/**/*.py",
        ])
    
    async def run(self) -> AgentResult:
        """Execute the code analysis process."""
        # Get services to analyze
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
        
        self.logger.info(f"Analyzing code for {len(services)} services")
        
        analyzed_services = 0
        extracted_endpoints = 0
        extracted_schemas = 0
        errors = []
        
        for service in services:
            try:
                result = await self._analyze_service(service)
                if result:
                    analyzed_services += 1
                    extracted_endpoints += result.get("endpoints", 0)
                    extracted_schemas += result.get("schemas", 0)
            except Exception as e:
                self.logger.warning(f"Failed to analyze service {service.name}: {e}")
                errors.append(f"{service.name}: {str(e)}")
        
        self.logger.info(
            f"Code analysis complete: {analyzed_services} services, "
            f"{extracted_endpoints} endpoints, {extracted_schemas} schemas"
        )
        
        return AgentResult(
            success=len(errors) == 0 or analyzed_services > 0,
            data={
                "analyzed_services": analyzed_services,
                "extracted_endpoints": extracted_endpoints,
                "extracted_schemas": extracted_schemas,
            },
            error="; ".join(errors) if errors else None,
        )
    
    async def _analyze_service(self, service: Service) -> Optional[dict[str, int]]:
        """Analyze a single service's source code."""
        if not service.repository:
            self.logger.debug(f"Service {service.name} has no repository")
            return None
        
        # Parse repository info
        repo_parts = service.repository.split("/")
        if len(repo_parts) != 2:
            return None
        
        org, repo_name = repo_parts
        
        self.logger.debug(f"Analyzing repository: {service.repository}")
        
        # Get repository file tree
        tree = await self.github.get_tree(org, repo_name, recursive=True)
        if not tree:
            self.logger.warning(f"Could not get file tree for {service.repository}")
            return None
        
        # Extract file paths
        file_paths = [item.get("path", "") for item in tree if item.get("type") == "blob"]
        
        endpoints_count = 0
        schemas_count = 0
        
        # Get existing APIs for this service
        existing_apis = self.graph.get_service_apis(service.id)
        
        # Analyze GraphQL schemas
        graphql_files = self._match_patterns(file_paths, self.graphql_patterns)
        if graphql_files:
            result = await self._analyze_graphql(
                org, repo_name, graphql_files, service, existing_apis
            )
            endpoints_count += result.get("endpoints", 0)
            schemas_count += result.get("schemas", 0)
        
        # Analyze OpenAPI specs
        openapi_files = self._match_patterns(file_paths, self.openapi_patterns)
        if openapi_files:
            result = await self._analyze_openapi(
                org, repo_name, openapi_files, service, existing_apis
            )
            endpoints_count += result.get("endpoints", 0)
            schemas_count += result.get("schemas", 0)
        
        # If no specs found, try to extract routes from source code
        if not graphql_files and not openapi_files:
            route_files = self._match_patterns(file_paths, self.route_patterns)
            if route_files:
                result = await self._analyze_routes(
                    org, repo_name, route_files, service, existing_apis
                )
                endpoints_count += result.get("endpoints", 0)
        
        return {
            "endpoints": endpoints_count,
            "schemas": schemas_count,
        }
    
    def _match_patterns(
        self,
        file_paths: list[str],
        patterns: list[str],
    ) -> list[str]:
        """Match file paths against glob patterns."""
        matched = []
        for path in file_paths:
            for pattern in patterns:
                # Handle ** patterns
                if "**" in pattern:
                    # Convert glob pattern to a simpler check
                    pattern_parts = pattern.split("**")
                    if len(pattern_parts) == 2:
                        prefix = pattern_parts[0].rstrip("/")
                        suffix = pattern_parts[1].lstrip("/")
                        if (not prefix or path.startswith(prefix)) and \
                           (not suffix or fnmatch.fnmatch(path, f"*{suffix}")):
                            matched.append(path)
                            break
                elif fnmatch.fnmatch(path, pattern):
                    matched.append(path)
                    break
        return matched
    
    async def _analyze_graphql(
        self,
        org: str,
        repo: str,
        files: list[str],
        service: Service,
        existing_apis: list[API],
    ) -> dict[str, int]:
        """Analyze GraphQL schema files."""
        self.logger.debug(f"Analyzing {len(files)} GraphQL files for {service.name}")
        
        # Fetch all GraphQL file contents
        contents = []
        for file_path in files:
            content = await self.github.get_file_content(org, repo, file_path)
            if content and content.content:
                contents.append(content.content)
        
        if not contents:
            return {"endpoints": 0, "schemas": 0}
        
        # Parse all schemas together
        try:
            schema = self.graphql_parser.parse_multiple(contents)
        except Exception as e:
            self.logger.warning(f"Failed to parse GraphQL schema: {e}")
            return {"endpoints": 0, "schemas": 0}
        
        # Find or create the GraphQL API
        graphql_api = None
        for api in existing_apis:
            if api.api_type == "graphql":
                graphql_api = api
                break
        
        if not graphql_api:
            graphql_api = API(
                id=f"api:{repo}:graphql",
                name=f"{service.name} GraphQL API",
                service_id=service.id,
                api_type="graphql",
                spec_file=files[0] if files else None,
            )
            self.graph.add_entity(graphql_api)
            self.graph.add_relation(Relation(
                source_id=service.id,
                target_id=graphql_api.id,
                relation_type=RelationType.EXPOSES,
            ))
        
        endpoints_count = 0
        schemas_count = 0
        
        # Create Endpoint entities for queries
        for query in schema.queries:
            endpoint = Endpoint(
                id=f"endpoint:{repo}:graphql:query:{query.name}",
                name=query.name,
                description=query.description,
                api_id=graphql_api.id,
                path="/graphql",
                method="POST",
                auth_required=True,
                metadata={
                    "operation_type": "query",
                    "return_type": query.type,
                    "arguments": [arg.to_dict() for arg in query.arguments],
                },
            )
            self.graph.add_entity(endpoint)
            
            # Add to API's endpoints list
            if endpoint.id not in graphql_api.endpoints:
                graphql_api.endpoints.append(endpoint.id)
            
            endpoints_count += 1
        
        # Create Endpoint entities for mutations
        for mutation in schema.mutations:
            endpoint = Endpoint(
                id=f"endpoint:{repo}:graphql:mutation:{mutation.name}",
                name=mutation.name,
                description=mutation.description,
                api_id=graphql_api.id,
                path="/graphql",
                method="POST",
                auth_required=True,
                metadata={
                    "operation_type": "mutation",
                    "return_type": mutation.type,
                    "arguments": [arg.to_dict() for arg in mutation.arguments],
                },
            )
            self.graph.add_entity(endpoint)
            
            if endpoint.id not in graphql_api.endpoints:
                graphql_api.endpoints.append(endpoint.id)
            
            endpoints_count += 1
        
        # Create Schema entities for types
        for graphql_type in schema.types:
            # Skip Query, Mutation, Subscription root types
            if graphql_type.name in ("Query", "Mutation", "Subscription"):
                continue
            
            schema_entity = Schema(
                id=f"schema:{repo}:graphql:{graphql_type.name}",
                name=graphql_type.name,
                description=graphql_type.description,
                schema_type="graphql",
                service_id=service.id,
                fields=[f.to_dict() for f in graphql_type.fields],
                metadata={
                    "kind": graphql_type.kind.value if hasattr(graphql_type.kind, 'value') else str(graphql_type.kind),
                    "interfaces": graphql_type.interfaces,
                    "enum_values": [v.to_dict() for v in graphql_type.enum_values] if graphql_type.enum_values else None,
                },
            )
            self.graph.add_entity(schema_entity)
            schemas_count += 1
        
        # Store parsed schema data in API metadata
        graphql_api.metadata = graphql_api.metadata or {}
        graphql_api.metadata["parsed_schema"] = schema.to_dict()
        
        self.logger.info(
            f"Extracted {endpoints_count} GraphQL operations and "
            f"{schemas_count} types from {service.name}"
        )
        
        return {"endpoints": endpoints_count, "schemas": schemas_count}
    
    async def _analyze_openapi(
        self,
        org: str,
        repo: str,
        files: list[str],
        service: Service,
        existing_apis: list[API],
    ) -> dict[str, int]:
        """Analyze OpenAPI specification files."""
        self.logger.debug(f"Analyzing {len(files)} OpenAPI files for {service.name}")
        
        endpoints_count = 0
        schemas_count = 0
        
        for file_path in files:
            content = await self.github.get_file_content(org, repo, file_path)
            if not content or not content.content:
                continue
            
            # Parse OpenAPI spec
            try:
                format_type = "json" if file_path.endswith(".json") else "yaml"
                spec = self.openapi_parser.parse(content.content, format_type)
            except Exception as e:
                self.logger.warning(f"Failed to parse OpenAPI spec {file_path}: {e}")
                continue
            
            # Find or create REST API
            rest_api = None
            for api in existing_apis:
                if api.api_type == "rest" and api.spec_file == file_path:
                    rest_api = api
                    break
            
            if not rest_api:
                rest_api = API(
                    id=f"api:{repo}:rest",
                    name=spec.title,
                    description=spec.description,
                    service_id=service.id,
                    api_type="rest",
                    version=spec.version,
                    spec_file=file_path,
                    base_url=spec.servers[0]["url"] if spec.servers else None,
                )
                self.graph.add_entity(rest_api)
                self.graph.add_relation(Relation(
                    source_id=service.id,
                    target_id=rest_api.id,
                    relation_type=RelationType.EXPOSES,
                ))
            
            # Create Endpoint entities
            for openapi_endpoint in spec.endpoints:
                endpoint = Endpoint(
                    id=f"endpoint:{repo}:rest:{openapi_endpoint.method.value}:{openapi_endpoint.path}".replace("/", "_"),
                    name=openapi_endpoint.operation_id or f"{openapi_endpoint.method.value} {openapi_endpoint.path}",
                    description=openapi_endpoint.description or openapi_endpoint.summary,
                    api_id=rest_api.id,
                    path=openapi_endpoint.path,
                    method=openapi_endpoint.method.value,
                    auth_required=bool(openapi_endpoint.security),
                    deprecated=openapi_endpoint.deprecated,
                    metadata={
                        "tags": openapi_endpoint.tags,
                        "parameters": [p.to_dict() for p in openapi_endpoint.parameters],
                        "request_body": openapi_endpoint.request_body.to_dict() if openapi_endpoint.request_body else None,
                        "responses": [r.to_dict() for r in openapi_endpoint.responses],
                    },
                )
                self.graph.add_entity(endpoint)
                
                if endpoint.id not in rest_api.endpoints:
                    rest_api.endpoints.append(endpoint.id)
                
                endpoints_count += 1
            
            # Create Schema entities
            for openapi_schema in spec.schemas:
                schema_entity = Schema(
                    id=f"schema:{repo}:openapi:{openapi_schema.name}",
                    name=openapi_schema.name,
                    description=openapi_schema.description,
                    schema_type="openapi",
                    service_id=service.id,
                    definition=openapi_schema.to_dict(),
                    fields=[
                        {
                            "name": name,
                            "type": props.get("type", "unknown"),
                            "description": props.get("description"),
                            "required": props.get("required", False),
                        }
                        for name, props in openapi_schema.properties.items()
                    ],
                )
                self.graph.add_entity(schema_entity)
                schemas_count += 1
            
            # Store parsed spec in API metadata
            rest_api.metadata = rest_api.metadata or {}
            rest_api.metadata["parsed_spec"] = spec.to_dict()
        
        self.logger.info(
            f"Extracted {endpoints_count} REST endpoints and "
            f"{schemas_count} schemas from {service.name}"
        )
        
        return {"endpoints": endpoints_count, "schemas": schemas_count}
    
    async def _analyze_routes(
        self,
        org: str,
        repo: str,
        files: list[str],
        service: Service,
        existing_apis: list[API],
    ) -> dict[str, int]:
        """Extract routes from source code files."""
        self.logger.debug(f"Analyzing {len(files)} source files for routes in {service.name}")
        
        all_routes: list[ExtractedRoute] = []
        
        # Limit to reasonable number of files
        files_to_analyze = files[:20]
        
        for file_path in files_to_analyze:
            content = await self.github.get_file_content(org, repo, file_path)
            if not content or not content.content:
                continue
            
            try:
                routes = self.route_extractor.extract(content.content, file_path)
                all_routes.extend(routes)
            except Exception as e:
                self.logger.debug(f"Failed to extract routes from {file_path}: {e}")
        
        if not all_routes:
            return {"endpoints": 0}
        
        # Find or create REST API
        rest_api = None
        for api in existing_apis:
            if api.api_type == "rest":
                rest_api = api
                break
        
        if not rest_api:
            rest_api = API(
                id=f"api:{repo}:rest",
                name=f"{service.name} REST API",
                service_id=service.id,
                api_type="rest",
            )
            self.graph.add_entity(rest_api)
            self.graph.add_relation(Relation(
                source_id=service.id,
                target_id=rest_api.id,
                relation_type=RelationType.EXPOSES,
            ))
        
        endpoints_count = 0
        
        # Create Endpoint entities
        for route in all_routes:
            endpoint = Endpoint(
                id=f"endpoint:{repo}:rest:{route.method.value}:{route.path}".replace("/", "_"),
                name=route.handler_name or f"{route.method.value} {route.path}",
                description=route.description,
                api_id=rest_api.id,
                path=route.path,
                method=route.method.value,
                metadata={
                    "source_file": route.file_path,
                    "line_number": route.line_number,
                    "framework": route.framework.value,
                    "middleware": route.middleware,
                },
            )
            self.graph.add_entity(endpoint)
            
            if endpoint.id not in rest_api.endpoints:
                rest_api.endpoints.append(endpoint.id)
            
            endpoints_count += 1
        
        self.logger.info(
            f"Extracted {endpoints_count} routes from source code for {service.name}"
        )
        
        return {"endpoints": endpoints_count}
