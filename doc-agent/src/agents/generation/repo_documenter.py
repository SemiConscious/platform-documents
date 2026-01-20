"""Repository Documenter Agent - generates documentation for each repository."""

import logging
from pathlib import Path
from typing import Any, Optional

import aiofiles

from ..base import BaseAgent, AgentResult, AgentContext
from ...knowledge import Repository, Service, API, EntityType, RelationType
from ...knowledge.store import compute_entity_hash

logger = logging.getLogger("doc-agent.agents.generation.repo_documenter")


class RepositoryDocumenterAgent(BaseAgent):
    """
    Agent that generates documentation for each repository.
    
    Generates:
    - Repository index (all repos with drill-down)
    - Individual repository documentation
    - Links to services derived from the repo
    - Repository structure and contents overview
    """
    
    name = "repo_documenter"
    description = "Generates repository-level documentation with drill-down capability"
    version = "0.1.0"
    
    def __init__(self, context: AgentContext, repo_id: Optional[str] = None):
        super().__init__(context)
        self.output_dir = context.output_dir
        self.dry_run = context.dry_run
        self.repo_id = repo_id
    
    async def run(self) -> AgentResult:
        """Execute the repository documentation process."""
        # Get repositories to document
        if self.repo_id:
            repo = self.graph.get_entity(self.repo_id)
            if not repo or not isinstance(repo, Repository):
                return AgentResult(
                    success=False,
                    error=f"Repository not found: {self.repo_id}",
                )
            repositories = [repo]
        else:
            repositories = self.graph.get_entities_by_type(EntityType.REPOSITORY)
            repositories = [r for r in repositories if isinstance(r, Repository)]
        
        self.logger.info(f"Generating documentation for {len(repositories)} repositories")
        
        generated_docs = []
        errors = []
        
        # Generate repository index
        try:
            index_path = await self._generate_repo_index(repositories)
            generated_docs.append(index_path)
        except Exception as e:
            self.logger.error(f"Failed to generate repository index: {e}")
            errors.append(f"repo-index: {str(e)}")
        
        # Generate individual repo documentation
        for repo in repositories:
            try:
                docs = await self._document_repository(repo)
                generated_docs.extend(docs)
            except Exception as e:
                self.logger.error(f"Failed to document repo {repo.name}: {e}")
                errors.append(f"{repo.name}: {str(e)}")
        
        return AgentResult(
            success=len(errors) == 0 or len(generated_docs) > 0,
            data={
                "generated_docs": generated_docs,
                "documented_repos": len(repositories),
                "errors": errors,
            },
            error="; ".join(errors) if errors else None,
        )
    
    async def _generate_repo_index(self, repositories: list[Repository]) -> str:
        """Generate the repository index page."""
        # Group repos by organization
        by_org: dict[str, list[Repository]] = {}
        for repo in repositories:
            # Extract org from repo URL or full name
            org = "unknown"
            if repo.url:
                parts = repo.url.rstrip("/").split("/")
                if len(parts) >= 2:
                    org = parts[-2]
            elif "/" in repo.name:
                org = repo.name.split("/")[0]
            
            if org not in by_org:
                by_org[org] = []
            by_org[org].append(repo)
        
        # Generate index content
        content = """---
title: Repository Index
description: Complete listing of all platform repositories
generated: true
---

# Repository Index

This page provides a complete listing of all repositories in the platform with links to detailed documentation.

## Summary

| Organization | Repositories |
|--------------|--------------|
"""
        
        for org, repos in sorted(by_org.items()):
            content += f"| [{org}](#{org.lower()}) | {len(repos)} |\n"
        
        content += f"\n**Total Repositories:** {len(repositories)}\n\n"
        
        # Generate sections by organization
        for org, repos in sorted(by_org.items()):
            content += f"## {org}\n\n"
            content += "| Repository | Language | Description | Services |\n"
            content += "|------------|----------|-------------|----------|\n"
            
            for repo in sorted(repos, key=lambda r: r.name):
                # Get linked services
                services = self._get_repo_services(repo)
                service_links = ", ".join([
                    f"[{s.name}](../services/{s.id.replace('service:', '')}/README.md)"
                    for s in services[:3]
                ])
                if len(services) > 3:
                    service_links += f" +{len(services) - 3} more"
                
                repo_slug = repo.name.replace("/", "-")
                desc = (repo.description or "No description")[:60]
                if len(repo.description or "") > 60:
                    desc += "..."
                
                content += f"| [{repo.name}](./repos/{repo_slug}/README.md) | {repo.language or 'N/A'} | {desc} | {service_links or 'N/A'} |\n"
            
            content += "\n"
        
        content += """
## Navigation

- [Architecture Overview](../architecture/overview.md)
- [Services Index](../services/index.md)
- [API Reference](../reference/api/index.md)
"""
        
        path = self.output_dir / "repositories" / "index.md"
        await self._write_file(path, content)
        
        return str(path)
    
    async def _document_repository(self, repo: Repository) -> list[str]:
        """Generate documentation for a single repository."""
        generated = []
        repo_slug = repo.name.replace("/", "-")
        repo_dir = self.output_dir / "repositories" / "repos" / repo_slug
        
        # Generate README
        readme_path = await self._generate_repo_readme(repo, repo_dir)
        generated.append(readme_path)
        
        # Generate structure document
        structure_path = await self._generate_repo_structure(repo, repo_dir)
        generated.append(structure_path)
        
        return generated
    
    async def _generate_repo_readme(self, repo: Repository, repo_dir: Path) -> str:
        """Generate the repository README document."""
        # Get linked services
        services = self._get_repo_services(repo)
        
        # Get APIs from services
        apis = []
        for service in services:
            service_apis = self.graph.get_service_apis(service.id)
            apis.extend(service_apis)
        
        # Build service links section
        service_section = ""
        if services:
            service_section = "## Related Services\n\n"
            service_section += "This repository is the source for the following services:\n\n"
            service_section += "| Service | Description | API Type |\n"
            service_section += "|---------|-------------|----------|\n"
            for service in services:
                service_slug = service.id.replace("service:", "")
                service_apis = self.graph.get_service_apis(service.id)
                api_types = ", ".join(set(a.api_type for a in service_apis)) or "N/A"
                desc = (service.description or "No description")[:50]
                service_section += f"| [{service.name}](../../services/{service_slug}/README.md) | {desc} | {api_types} |\n"
            service_section += "\n"
        
        # Build topics/tags section
        topics_section = ""
        if repo.topics:
            topics_section = f"**Topics:** {', '.join(f'`{t}`' for t in repo.topics)}\n\n"
        
        content = f"""---
title: {repo.name}
description: Repository documentation for {repo.name}
generated: true
repository_url: {repo.url}
---

# {repo.name}

{repo.description or "No description available."}

## Overview

| Property | Value |
|----------|-------|
| **URL** | [{repo.url}]({repo.url}) |
| **Default Branch** | `{repo.default_branch}` |
| **Primary Language** | {repo.language or "N/A"} |
| **Has CI/CD** | {"Yes" if repo.has_ci else "No"} |
| **Has Documentation** | {"Yes" if repo.has_docs else "No"} |

{topics_section}
{service_section}
## Repository Contents

See [Structure](./structure.md) for detailed information about repository contents.

### Key Files

- `README.md` - Repository documentation
- Configuration files and dependencies
- Source code organization

## Getting Started

### Prerequisites

"""
        
        # Add language-specific prerequisites
        if repo.language:
            lang = repo.language.lower()
            if lang in ("javascript", "typescript"):
                content += "- Node.js (see `.nvmrc` or `package.json` for version)\n"
                content += "- npm or yarn\n"
            elif lang == "python":
                content += "- Python 3.x (see `requirements.txt` or `pyproject.toml`)\n"
                content += "- pip or poetry\n"
            elif lang == "go":
                content += "- Go (see `go.mod` for version)\n"
            elif lang == "java":
                content += "- Java JDK (see `pom.xml` or `build.gradle`)\n"
                content += "- Maven or Gradle\n"
        
        content += f"""
### Clone Repository

```bash
git clone {repo.url}
cd {repo.name.split('/')[-1] if '/' in repo.name else repo.name}
```

## Documentation Links

"""
        
        if services:
            content += "### Service Documentation\n\n"
            for service in services:
                service_slug = service.id.replace("service:", "")
                content += f"- [{service.name}](../../services/{service_slug}/README.md)\n"
            content += "\n"
        
        if apis:
            content += "### API Documentation\n\n"
            for api in apis:
                service_id = api.service_id.replace("service:", "")
                content += f"- [{api.name}](../../services/{service_id}/api/overview.md)\n"
            content += "\n"
        
        content += """
## Related

- [Repository Index](../index.md)
- [Architecture Overview](../../architecture/overview.md)
"""
        
        path = repo_dir / "README.md"
        await self._write_file(path, content)
        
        self.store.register_document(
            str(path),
            compute_entity_hash([repo]),
            [repo.id],
        )
        
        return str(path)
    
    async def _generate_repo_structure(self, repo: Repository, repo_dir: Path) -> str:
        """Generate repository structure document."""
        # Get language-specific structure expectations
        structure_info = self._get_language_structure(repo.language)
        
        content = f"""---
title: {repo.name} - Structure
description: Repository structure and organization for {repo.name}
generated: true
---

# {repo.name} - Repository Structure

## Overview

This document describes the structure and organization of the `{repo.name}` repository.

## Language: {repo.language or "Unknown"}

{structure_info}

## Expected Directory Structure

"""
        
        # Add language-specific structure
        if repo.language:
            lang = repo.language.lower()
            if lang in ("javascript", "typescript"):
                content += """```
├── src/                 # Source code
│   ├── index.ts         # Entry point
│   ├── routes/          # API routes
│   ├── controllers/     # Request handlers
│   ├── services/        # Business logic
│   ├── models/          # Data models
│   └── utils/           # Utilities
├── tests/               # Test files
├── docs/                # Documentation
├── package.json         # Dependencies
├── tsconfig.json        # TypeScript config
└── README.md            # Repository docs
```
"""
            elif lang == "python":
                content += """```
├── src/                 # Source code
│   ├── __init__.py
│   ├── main.py          # Entry point
│   ├── api/             # API endpoints
│   ├── services/        # Business logic
│   ├── models/          # Data models
│   └── utils/           # Utilities
├── tests/               # Test files
├── docs/                # Documentation
├── requirements.txt     # Dependencies
├── pyproject.toml       # Project config
└── README.md            # Repository docs
```
"""
            elif lang == "go":
                content += """```
├── cmd/                 # Command entry points
│   └── main.go
├── internal/            # Private packages
│   ├── handlers/        # HTTP handlers
│   ├── services/        # Business logic
│   └── models/          # Data models
├── pkg/                 # Public packages
├── api/                 # API definitions
├── docs/                # Documentation
├── go.mod               # Dependencies
├── go.sum               # Dependency checksums
└── README.md            # Repository docs
```
"""
            else:
                content += """```
├── src/                 # Source code
├── tests/               # Test files
├── docs/                # Documentation
├── config/              # Configuration
└── README.md            # Repository docs
```
"""
        
        content += f"""
## Key Files

### Configuration

Configuration files define project settings and dependencies.

### Entry Points

The main entry points for the application.

### API Definitions

API schemas and specifications (OpenAPI, GraphQL, etc.).

## Related

- [Repository Overview](./README.md)
- [Repository Index](../index.md)
"""
        
        path = repo_dir / "structure.md"
        await self._write_file(path, content)
        
        return str(path)
    
    def _get_repo_services(self, repo: Repository) -> list[Service]:
        """Get services that are derived from this repository."""
        services = []
        
        # Look for services that reference this repo
        for service in self.graph.get_services():
            if service.repository:
                # Check if repo matches
                if repo.name in service.repository or (repo.url and repo.url in (service.sources or [])):
                    services.append(service)
        
        # Also check relations
        relations = self.graph.get_relations_for_entity(repo.id)
        for rel in relations:
            if rel.relation_type == RelationType.CONTAINS:
                entity = self.graph.get_entity(rel.target_id)
                if entity and isinstance(entity, Service):
                    if entity not in services:
                        services.append(entity)
        
        return services
    
    def _get_language_structure(self, language: Optional[str]) -> str:
        """Get language-specific structure description."""
        if not language:
            return "No specific language detected."
        
        lang = language.lower()
        
        descriptions = {
            "javascript": "JavaScript project, typically using Node.js runtime with npm/yarn package management.",
            "typescript": "TypeScript project with type safety, compiling to JavaScript for Node.js runtime.",
            "python": "Python project, typically using pip/poetry for dependencies and virtual environments.",
            "go": "Go project following standard Go project layout with modules.",
            "java": "Java project, typically using Maven or Gradle for build and dependency management.",
            "c#": "C# .NET project using MSBuild and NuGet package management.",
            "rust": "Rust project using Cargo for builds and crate management.",
        }
        
        return descriptions.get(lang, f"{language} project with standard structure.")
    
    async def _write_file(self, path: Path, content: str) -> None:
        """Write content to a file."""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would write: {path}")
            return
        
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w") as f:
            await f.write(content)
        
        self.logger.debug(f"Wrote: {path}")
