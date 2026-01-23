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
    
    Uses local clones when available to avoid GitHub API rate limits.
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
        self.skip_archived = source_config.get("skip_archived", True)  # Skip archived by default
        
        # Local repos directory (for avoiding API rate limits)
        from pathlib import Path
        self.repos_dir = context.store.store_dir.parent / "repos"
        self.use_local = self.repos_dir.exists()
        if self.use_local:
            self.logger.info(f"Using local repo clones from {self.repos_dir}")
    
    def _get_local_repo_path(self, org: str, repo_name: str) -> Optional["Path"]:
        """Get the local path for a repository if it exists."""
        from pathlib import Path
        if not self.use_local:
            return None
        
        repo_path = self.repos_dir / org / repo_name
        if repo_path.exists() and (repo_path / ".git").exists():
            return repo_path
        return None
    
    def _read_local_file(self, repo_path: "Path", filename: str) -> Optional[str]:
        """Read a file from a local repository."""
        file_path = repo_path / filename
        if file_path.exists() and file_path.is_file():
            try:
                return file_path.read_text(errors='ignore')
            except Exception:
                pass
        return None
    
    def _find_readme(self, repo_path: "Path") -> Optional[str]:
        """Find and read README from local repo."""
        for name in ["README.md", "README", "readme.md", "Readme.md"]:
            content = self._read_local_file(repo_path, name)
            if content:
                return content
        return None
    
    async def run(self) -> AgentResult:
        """Execute the repository scanning process."""
        self.logger.info(f"Scanning repositories from {len(self.organizations)} organizations")
        
        # Load checkpoint for incremental updates
        checkpoint = await self.load_checkpoint()
        processed_repos = set(checkpoint.get("processed_repos", [])) if checkpoint else set()
        
        discovered_services = 0
        discovered_apis = 0
        errors = []
        used_cache = False
        
        # Parallelism for repo analysis (configurable)
        max_concurrent = self.context.config.get("agents", {}).get("discovery", {}).get("repo_parallelism", 10)
        semaphore = asyncio.Semaphore(max_concurrent)
        
        for org in self.organizations:
            try:
                result = await self._get_repositories_with_cache(org)
                
                if result is None:
                    # Rate limited and no cache available
                    self.logger.warning(f"Cannot list repos for {org}: rate limited with no cache")
                    errors.append(f"org/{org}: Rate limited, no cache available")
                    continue
                
                if isinstance(result, tuple):
                    # Used cache
                    all_repos, from_cache = result
                    if from_cache:
                        used_cache = True
                        self.logger.info(f"Using cached repository list for {org}")
                else:
                    all_repos = result
                
                # Filter out archived and excluded repositories
                archived_count = sum(1 for r in all_repos if r.archived)
                excluded_count = sum(1 for r in all_repos if self._should_exclude(r.name))
                
                repos = [
                    r for r in all_repos 
                    if (not self.skip_archived or not r.archived) and not self._should_exclude(r.name)
                ]
                
                if archived_count > 0 and self.skip_archived:
                    self.logger.info(f"Skipping {archived_count} archived repositories in {org}")
                if excluded_count > 0:
                    self.logger.debug(f"Excluded {excluded_count} repos by pattern in {org}")
                self.logger.info(f"Found {len(repos)} active repositories in {org} (filtered from {len(all_repos)})")
                
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
                "used_cache": used_cache,
            },
            error="; ".join(errors) if errors else None,
            metadata={"organizations": self.organizations, "used_cache": used_cache},
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
    
    async def _get_repositories_with_cache(
        self,
        org: str,
    ) -> Optional[list[GHRepo] | tuple[list[GHRepo], bool]]:
        """
        Get repositories with cache fallback.
        
        Tries GitHub API first. If rate limited, falls back to cache.
        On success, updates the cache.
        
        Args:
            org: Organization name
            
        Returns:
            - list of repos if successful from API
            - tuple of (repos, True) if from cache
            - None if rate limited and no cache available
        """
        try:
            # Try API first
            repos = await self.github.list_repositories(org=org)
            
            # Check if we got an empty list due to rate limiting
            # The error would have been logged inside list_repositories
            if not repos:
                # Check cache
                cached = self.context.store.get_cached_repositories(org)
                if cached:
                    self.logger.info(f"API returned empty for {org}, using {len(cached)} cached repos")
                    return ([GHRepo.from_dict(r) for r in cached], True)
                return None
            
            # Success - cache the results (include archived status)
            repo_dicts = [
                {
                    "name": r.name,
                    "full_name": r.full_name,
                    "description": r.description,
                    "html_url": r.url,
                    "default_branch": r.default_branch,
                    "language": r.language,
                    "topics": r.topics,
                    "archived": r.archived,
                }
                for r in repos
            ]
            self.context.store.cache_repositories(org, repo_dicts)
            
            return repos
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for rate limit error
            if "rate limit" in error_msg or "403" in error_msg:
                cached = self.context.store.get_cached_repositories(org)
                if cached:
                    self.logger.info(f"Rate limited for {org}, using {len(cached)} cached repos")
                    return ([GHRepo.from_dict(r) for r in cached], True)
                self.logger.warning(f"Rate limited for {org} with no cache available")
                return None
            
            raise
    
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
        
        # Get README for description (prefer local clone)
        local_path = self._get_local_repo_path(org, repo.name)
        if local_path:
            readme = self._find_readme(local_path)
        else:
            readme = await self.github.get_readme(org, repo.name)
        
        # Determine if this is a service
        is_service = await self._is_service_repo(repo, readme, local_path)
        
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
    
    async def _is_service_repo(self, repo: GHRepo, readme: Optional[str], local_path: Optional["Path"] = None) -> bool:
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
        
        # Check for service indicator files (prefer local if available)
        service_files = ["Dockerfile", "docker-compose.yml", "serverless.yml", "app.yaml", "main.go", "main.py", "index.ts", "package.json"]
        if local_path:
            for sf in service_files:
                if (local_path / sf).exists():
                    return True
        
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
        Uses local clones when available.
        """
        import yaml
        apis = []
        
        # Check for local repo first
        local_path = self._get_local_repo_path(org, repo.name)
        
        # Try to get OpenAPI spec
        openapi_spec = None
        if local_path:
            for spec_file in ["openapi.yaml", "openapi.yml", "swagger.yaml", "swagger.yml"]:
                spec_content = self._read_local_file(local_path, spec_file)
                if spec_content:
                    try:
                        openapi_spec = yaml.safe_load(spec_content)
                        break
                    except Exception:
                        pass
        else:
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
        graphql_content = None
        if local_path:
            for gql_file in ["schema.graphql", "schema.gql", "*.graphql"]:
                if gql_file.startswith("*"):
                    # Find any graphql file
                    for f in local_path.rglob("*.graphql"):
                        graphql_content = f.read_text(errors='ignore')
                        break
                else:
                    graphql_content = self._read_local_file(local_path, gql_file)
                if graphql_content:
                    break
        else:
            gql_result = await self.github.get_file_content(org, repo.name, "schema.graphql")
            graphql_content = gql_result.content if gql_result else None
        
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
        Uses local clones when available.
        """
        import json as json_module
        dependencies = {}
        
        # Check for local repo first
        local_path = self._get_local_repo_path(org, repo.name)
        
        # Check package.json for Node.js projects
        package_json = None
        if local_path:
            pkg_content = self._read_local_file(local_path, "package.json")
            if pkg_content:
                try:
                    package_json = json_module.loads(pkg_content)
                except Exception:
                    pass
        else:
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
        requirements_content = None
        if local_path:
            requirements_content = self._read_local_file(local_path, "requirements.txt")
        else:
            requirements = await self.github.get_file_content(org, repo.name, "requirements.txt")
            requirements_content = requirements.content if requirements else None
        
        if requirements_content:
            for line in requirements_content.split("\n"):
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
