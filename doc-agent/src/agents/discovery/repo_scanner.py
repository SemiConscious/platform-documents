"""Repository Scanner Agent - discovers services from GitHub repositories."""

import asyncio
import json
import logging
import re
from typing import Any, Optional

from ..base import BaseAgent, AgentResult, AgentContext
from ...knowledge import (
    Service,
    Repository,
    API,
    Schema,
    Relation,
    RelationType,
)
from ...mcp.github import GitHubClient, Repository as GHRepo

logger = logging.getLogger("doc-agent.agents.discovery.repo_scanner")


class RepositoryScannerAgent(BaseAgent):
    """
    Agent that scans GitHub repositories to discover services.
    
    Extracts:
    - Repository metadata and structure
    - README files for service descriptions
    - API definitions (OpenAPI, GraphQL schemas)
    - Database migrations and schemas
    - Dependencies (package.json, requirements.txt, etc.)
    - CI/CD configurations for deployment info
    """
    
    name = "repository_scanner"
    description = "Scans GitHub repositories to discover and catalog services"
    version = "0.1.0"
    
    def __init__(self, context: AgentContext):
        super().__init__(context)
        self.github = GitHubClient(self.mcp)
        
        # Configuration
        source_config = context.config.get("sources", {}).get("github", {})
        self.organizations = source_config.get("organizations", [])
        self.exclude_patterns = source_config.get("exclude_repos", [])
        self.include_patterns = source_config.get("include_patterns", [])
    
    async def run(self) -> AgentResult:
        """Execute the repository scanning process."""
        self.logger.info(f"Scanning repositories from {len(self.organizations)} organizations")
        
        # Load checkpoint for incremental updates
        checkpoint = await self.load_checkpoint()
        processed_repos = set(checkpoint.get("processed_repos", [])) if checkpoint else set()
        
        discovered_services = 0
        discovered_apis = 0
        errors = []
        
        # Parallelism for repo analysis (configurable)
        max_concurrent = self.context.config.get("agents", {}).get("discovery", {}).get("repo_parallelism", 10)
        semaphore = asyncio.Semaphore(max_concurrent)
        
        for org in self.organizations:
            try:
                all_repos = await self.github.list_repositories(org=org)
                
                # Filter out excluded repositories
                repos = [
                    r for r in all_repos 
                    if not self._should_exclude(r.name)
                ]
                
                self.logger.info(f"Found {len(repos)} repositories in {org} (filtered from {len(all_repos)})")
                
                # Filter to repos not yet processed
                repos_to_process = [
                    r for r in repos
                    if r.full_name not in processed_repos
                ]
                
                if not repos_to_process:
                    self.logger.info(f"All repos in {org} already processed")
                    continue
                
                self.logger.info(f"Processing {len(repos_to_process)} repos in parallel (max {max_concurrent} concurrent)")
                
                # Process repos in parallel with semaphore
                async def process_with_semaphore(repo):
                    async with semaphore:
                        return await self._process_single_repo(org, repo)
                
                tasks = [process_with_semaphore(repo) for repo in repos_to_process]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Collect results
                for repo, result in zip(repos_to_process, results):
                    if isinstance(result, Exception):
                        self.logger.warning(f"Failed to process repo {repo.name}: {result}")
                        errors.append(f"{repo.name}: {str(result)}")
                    elif result:
                        service, apis = result
                        if service:
                            self.graph.add_entity(service)
                            discovered_services += 1
                            
                            for api in apis:
                                self.graph.add_entity(api)
                                self.graph.add_relation(Relation(
                                    source_id=service.id,
                                    target_id=api.id,
                                    relation_type=RelationType.EXPOSES,
                                ))
                                discovered_apis += 1
                    
                    processed_repos.add(repo.full_name)
                
            except Exception as e:
                self.logger.error(f"Failed to scan organization {org}: {e}")
                errors.append(f"org/{org}: {str(e)}")
        
        # Save checkpoint
        await self.save_checkpoint({
            "processed_repos": list(processed_repos),
        })
        
        self.logger.info(
            f"Repository scanning complete: {discovered_services} services, "
            f"{discovered_apis} APIs discovered"
        )
        
        return AgentResult(
            success=len(errors) == 0 or discovered_services > 0,
            data={
                "discovered_services": discovered_services,
                "discovered_apis": discovered_apis,
                "processed_repos": len(processed_repos),
            },
            error="; ".join(errors) if errors else None,
            metadata={"organizations": self.organizations},
        )
    
    async def _process_single_repo(
        self,
        org: str,
        repo: GHRepo,
    ) -> Optional[tuple[Optional[Service], list[API]]]:
        """Process a single repository and return service + APIs."""
        try:
            service = await self._process_repository(org, repo)
            apis = []
            
            if service:
                apis = await self._extract_apis(org, repo, service.id)
            
            return (service, apis)
        except Exception as e:
            raise e
    
    def _should_exclude(self, repo_name: str) -> bool:
        """Check if a repository should be excluded based on patterns."""
        for pattern in self.exclude_patterns:
            if re.match(pattern, repo_name):
                return True
        return False
    
    async def _process_repository(
        self,
        org: str,
        repo: GHRepo,
    ) -> Optional[Service]:
        """
        Process a single repository and extract service information.
        """
        self.logger.debug(f"Processing repository: {repo.full_name}")
        
        # Create repository entity
        repo_entity = Repository(
            id=f"repo:{repo.full_name}",
            name=repo.name,
            description=repo.description,
            url=repo.url,
            default_branch=repo.default_branch,
            language=repo.language,
            languages={repo.language: 100} if repo.language else {},  # Approximate from primary language
            topics=repo.topics,
        )
        self.graph.add_entity(repo_entity)
        
        # Get README for description
        readme = await self.github.get_readme(org, repo.name)
        
        # Determine if this is a service
        is_service = await self._is_service_repo(repo, readme)
        
        if not is_service:
            self.logger.debug(f"Repository {repo.name} does not appear to be a service")
            return None
        
        # Extract service metadata using Claude
        service_info = await self._analyze_repository(repo, readme)
        
        # Create service entity
        service = Service(
            id=f"service:{repo.name}",
            name=service_info.get("name", repo.name),
            description=service_info.get("description", repo.description),
            repository=repo.full_name,
            language=repo.language,
            framework=service_info.get("framework"),
            team=service_info.get("team"),
            status="active",
            dependencies=service_info.get("dependencies", []),
            sources=[repo.url],
            metadata={
                "readme_summary": service_info.get("summary"),
                "topics": repo.topics,
            },
        )
        
        # Link service to repository
        self.graph.add_relation(Relation(
            source_id=service.id,
            target_id=repo_entity.id,
            relation_type=RelationType.CONTAINS,
        ))
        
        # Extract dependencies and create relations
        deps = await self._extract_dependencies(org, repo)
        for dep_name, dep_info in deps.items():
            service.dependencies.append(dep_name)
            # Check if this dependency is another service we know about
            dep_service_id = f"service:{dep_name}"
            if self.graph.get_entity(dep_service_id):
                self.graph.add_relation(Relation(
                    source_id=service.id,
                    target_id=dep_service_id,
                    relation_type=RelationType.DEPENDS_ON,
                    metadata=dep_info,
                ))
        
        return service
    
    async def _is_service_repo(self, repo: GHRepo, readme: Optional[str]) -> bool:
        """
        Determine if a repository represents a deployable service.
        
        Uses heuristics based on:
        - Repository topics
        - File presence (Dockerfile, CI configs, etc.)
        - Language patterns
        """
        # Check topics for service indicators
        service_topics = {"service", "api", "microservice", "backend", "server"}
        if any(topic in repo.topics for topic in service_topics):
            return True
        
        # Check for non-service indicators
        non_service_topics = {"library", "sdk", "cli", "tool", "config", "docs"}
        if any(topic in repo.topics for topic in non_service_topics):
            return False
        
        # Most repos with certain languages are likely services
        service_languages = {"go", "java", "python", "typescript", "javascript", "c#", "rust"}
        if repo.language and repo.language.lower() in service_languages:
            return True
        
        return False
    
    async def _analyze_repository(
        self,
        repo: GHRepo,
        readme: Optional[str],
    ) -> dict[str, Any]:
        """
        Use Claude to analyze the repository and extract service information.
        """
        # Build context for Claude
        context_parts = [
            f"Repository: {repo.full_name}",
            f"Description: {repo.description or 'None'}",
            f"Language: {repo.language}",
            f"Topics: {', '.join(repo.topics) if repo.topics else 'None'}",
        ]
        
        if readme:
            # Truncate README if too long
            readme_preview = readme[:3000] + "..." if len(readme) > 3000 else readme
            context_parts.append(f"\nREADME:\n{readme_preview}")
        
        context = "\n".join(context_parts)
        
        prompt = f"""Analyze this GitHub repository and extract service information.

{context}

Extract the following information in JSON format:
{{
    "name": "human-readable service name",
    "description": "one-line description of what the service does",
    "summary": "2-3 sentence summary of the service's purpose and function",
    "framework": "main framework used (e.g., Express, Spring, FastAPI, etc.) or null",
    "team": "team name if mentioned, or null",
    "dependencies": ["list", "of", "key", "internal", "dependencies"],
    "api_type": "REST, GraphQL, gRPC, or null if not an API service",
    "is_infrastructure": true/false if this is infrastructure rather than business logic
}}

Return ONLY valid JSON, no additional text."""
        
        try:
            response = await self.call_claude(
                system_prompt=self.get_system_prompt(),
                user_message=prompt,
                temperature=0.1,
            )
            
            # Parse JSON response
            # Handle markdown code blocks if present
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            return json.loads(response)
            
        except Exception as e:
            self.logger.warning(f"Failed to analyze repository with Claude: {e}")
            return {
                "name": repo.name,
                "description": repo.description,
            }
    
    async def _extract_apis(
        self,
        org: str,
        repo: GHRepo,
        service_id: str,
    ) -> list[API]:
        """
        Extract API definitions from the repository.
        """
        apis = []
        
        # Try to get OpenAPI spec
        openapi_spec = await self.github.get_openapi_spec(org, repo.name)
        
        if openapi_spec:
            api_info = openapi_spec.get("info", {})
            api = API(
                id=f"api:{repo.name}:rest",
                name=api_info.get("title", f"{repo.name} API"),
                description=api_info.get("description"),
                service_id=service_id,
                api_type="rest",
                version=api_info.get("version"),
                spec_file="openapi.yaml",
                sources=[f"{repo.url}/blob/{repo.default_branch}/openapi.yaml"],
                metadata={
                    "openapi_version": openapi_spec.get("openapi"),
                    "paths_count": len(openapi_spec.get("paths", {})),
                },
            )
            apis.append(api)
        
        # Check for GraphQL schema
        graphql_content = await self.github.get_file_content(org, repo.name, "schema.graphql")
        if graphql_content:
            api = API(
                id=f"api:{repo.name}:graphql",
                name=f"{repo.name} GraphQL API",
                service_id=service_id,
                api_type="graphql",
                spec_file="schema.graphql",
                sources=[f"{repo.url}/blob/{repo.default_branch}/schema.graphql"],
            )
            apis.append(api)
        
        return apis
    
    async def _extract_dependencies(
        self,
        org: str,
        repo: GHRepo,
    ) -> dict[str, dict[str, Any]]:
        """
        Extract dependencies from package management files.
        """
        dependencies = {}
        
        # Check package.json for Node.js projects
        package_json = await self.github.get_package_json(org, repo.name)
        if package_json:
            deps = package_json.get("dependencies", {})
            for name, version in deps.items():
                # Filter to internal packages (customize based on org naming)
                if name.startswith("@natterbox/") or name.startswith("@internal/"):
                    dependencies[name] = {
                        "version": version,
                        "type": "npm",
                    }
        
        # Check requirements.txt for Python projects
        requirements = await self.github.get_file_content(org, repo.name, "requirements.txt")
        if requirements:
            for line in requirements.content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    # Parse requirement line
                    match = re.match(r"^([a-zA-Z0-9_-]+)", line)
                    if match:
                        name = match.group(1)
                        # Filter to internal packages
                        if "natterbox" in name.lower() or "internal" in name.lower():
                            dependencies[name] = {
                                "version": line,
                                "type": "pip",
                            }
        
        return dependencies
    
    def get_system_prompt(self) -> str:
        return """You are a technical documentation agent analyzing software repositories.

Your role is to:
1. Understand the purpose and function of services from their repository content
2. Extract accurate technical metadata
3. Identify dependencies and relationships
4. Provide clear, concise descriptions suitable for documentation

Be precise and technical. If information is unclear, indicate that with null rather than guessing.
Focus on facts that can be determined from the available content."""
