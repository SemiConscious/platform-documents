"""Repository Documenter Agent - generates documentation for each repository."""

import logging
import os
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
    version = "0.2.0"
    
    def __init__(self, context: AgentContext, repo_id: Optional[str] = None):
        super().__init__(context)
        self.output_dir = context.output_dir
        self.dry_run = context.dry_run
        self.repo_id = repo_id
        
        # Set up local repos path
        workspace_root = Path(__file__).parent.parent.parent.parent
        self.local_repos_path = workspace_root / "repos"
        self.use_local_repos = self.local_repos_path.exists()
    
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
        """Generate the repository README document with actual repo content."""
        # Get local repo path for enriched content
        local_path = self._get_local_repo_path(repo)
        
        # Detect actual language
        detected_lang = self._detect_language_from_repo(local_path) if local_path else None
        actual_language = detected_lang or repo.language or "Unknown"
        
        # Read actual README for description
        actual_readme = ""
        description = repo.description or ""
        if local_path:
            readme_path = local_path / "README.md"
            if readme_path.exists():
                try:
                    actual_readme = readme_path.read_text(errors='ignore')
                    # Extract first paragraph as description if not set
                    if not description:
                        lines = actual_readme.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith('#') and not line.startswith('['):
                                description = line[:200]
                                break
                except Exception:
                    pass
        
        # Get linked services
        services = self._get_repo_services(repo)
        
        # Get APIs from services
        apis = []
        for service in services:
            service_apis = self.graph.get_service_apis(service.id)
            apis.extend(service_apis)
        
        # Get components for Go projects
        components = self._get_go_components(local_path) if local_path else []
        
        # Check for CI/CD
        has_ci = repo.has_ci
        if local_path and not has_ci:
            has_ci = (local_path / ".github" / "workflows").exists()
        
        # Build service links section
        service_section = ""
        if services:
            service_section = "## Related Services\n\n"
            service_section += "This repository is the source for the following services:\n\n"
            service_section += "| Service | Description |\n"
            service_section += "|---------|-------------|\n"
            for service in services:
                service_slug = service.id.replace("service:", "")
                desc = (service.description or "No description")[:60]
                service_section += f"| [{service.name}](../../services/{service_slug}/README.md) | {desc} |\n"
            service_section += "\n"
        
        # Build topics/tags section
        topics_section = ""
        if repo.topics:
            topics_section = f"**Topics:** {', '.join(f'`{t}`' for t in repo.topics)}\n\n"
        
        content = f"""---
title: {repo.name}
description: {description[:100] if description else 'Repository documentation'}
generated: true
repository_url: {repo.url}
---

# {repo.name}

{description or "No description available."}

## Overview

| Property | Value |
|----------|-------|
| **GitHub** | [{repo.url}]({repo.url}) |
| **Language** | {actual_language} |
| **Default Branch** | `{repo.default_branch}` |
| **CI/CD** | {"Yes" if has_ci else "No"} |

{topics_section}
"""

        # Add components section for Go projects
        if components:
            content += "## Components\n\n"
            content += "This repository contains the following executable components:\n\n"
            content += "| Component | Description |\n"
            content += "|-----------|-------------|\n"
            for comp in components:
                name = comp.get("name", "unknown")
                desc = comp.get("description", "No description")[:60]
                # Link to GitHub
                github_link = f"{repo.url}/tree/{repo.default_branch}/cmd/{name}"
                content += f"| [`{name}`]({github_link}) | {desc} |\n"
            content += "\n"
        
        content += service_section
        
        content += """## Repository Contents

See [Structure](./structure.md) for detailed directory layout and key files.

"""

        # Getting Started section
        content += "## Getting Started\n\n"
        
        # Language-specific prerequisites
        if actual_language.lower() in ("javascript", "typescript"):
            content += "### Prerequisites\n\n"
            content += f"- Node.js (see [`package.json`]({repo.url}/blob/{repo.default_branch}/package.json) for version)\n"
            content += "- npm or yarn\n\n"
        elif actual_language.lower() == "python":
            content += "### Prerequisites\n\n"
            content += "- Python 3.x\n"
            content += "- pip or poetry\n\n"
        elif actual_language.lower() == "go":
            content += "### Prerequisites\n\n"
            content += f"- Go (see [`go.mod`]({repo.url}/blob/{repo.default_branch}/go.mod) for version)\n\n"
        
        content += f"""### Clone and Build

```bash
git clone {repo.url}
cd {repo.name.split('/')[-1] if '/' in repo.name else repo.name}
"""
        
        # Add build command based on language
        if actual_language.lower() == "go":
            content += "make\n"
        elif actual_language.lower() in ("javascript", "typescript"):
            content += "npm install\nnpm run build\n"
        elif actual_language.lower() == "python":
            content += "pip install -r requirements.txt\n"
        
        content += "```\n\n"
        
        # Documentation Links
        if services or apis:
            content += "## Documentation\n\n"
            
            if services:
                for service in services:
                    service_slug = service.id.replace("service:", "")
                    content += f"- [Service Documentation](../../services/{service_slug}/README.md)\n"
            
            content += "\n"
        
        content += """## Related

- [Repository Index](../index.md)
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
        """Generate repository structure document with actual directory contents."""
        # Try to get actual structure from local repo
        local_path = self._get_local_repo_path(repo)
        
        # Detect actual language
        detected_lang = self._detect_language_from_repo(local_path) if local_path else None
        actual_language = detected_lang or repo.language or "Unknown"
        
        # Get language-specific structure expectations
        structure_info = self._get_language_structure(actual_language)
        
        content = f"""---
title: {repo.name} - Structure
description: Repository structure and organization for {repo.name}
generated: true
---

<!-- breadcrumb -->
[Home](/../../../index.md) > [Repositories](../../../repositories/index.md) > Repos > {repo.name.split('/')[-1].replace('-', ' ').title()}


# {repo.name} - Repository Structure

## Overview

This document describes the structure and organization of the `{repo.name}` repository.

## Language: {actual_language}

{structure_info}

## Directory Structure

"""
        
        # Try to get actual structure
        actual_structure = self._read_actual_structure(local_path) if local_path else ""
        
        if actual_structure:
            content += actual_structure + "\n"
        else:
            # Fallback to template structure based on language
            if actual_language.lower() in ("javascript", "typescript"):
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
            elif actual_language.lower() == "python":
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
            elif actual_language.lower() == "go":
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
        
        # Get GitHub URL base for linking
        github_base = f"{repo.url}/blob/{repo.default_branch}"
        github_tree = f"{repo.url}/tree/{repo.default_branch}"
        
        # For Go projects, document cmd/ components
        if local_path and actual_language.lower() == "go":
            components = self._get_go_components(local_path)
            if components:
                content += "\n## Components\n\n"
                content += "This repository contains the following executable components:\n\n"
                content += "| Component | Path | Description |\n"
                content += "|-----------|------|-------------|\n"
                for comp in components:
                    desc = comp.get("description", "No description")[:60]
                    github_link = f"{github_tree}/{comp['path']}"
                    content += f"| `{comp['name']}` | [`{comp['path']}`]({github_link}) | {desc} |\n"
                content += "\n"
        
        # Key files section
        content += """
## Key Files

### Configuration

"""
        # List actual config files if we have local repo
        if local_path:
            config_files = []
            for cf in ["go.mod", "package.json", "requirements.txt", "pyproject.toml", 
                       "Dockerfile", "Makefile", "docker-compose.yml", ".env.example"]:
                if (local_path / cf).exists():
                    config_files.append(cf)
            
            if config_files:
                for cf in config_files:
                    content += f"- [`{cf}`]({github_base}/{cf})\n"
            else:
                content += "Configuration files define project settings and dependencies.\n"
        else:
            content += "Configuration files define project settings and dependencies.\n"
        
        content += """
### Entry Points

"""
        if local_path and actual_language.lower() == "go":
            # List main.go files
            main_files = list(local_path.glob("cmd/*/main.go"))
            if main_files:
                for mf in main_files[:10]:
                    rel = mf.relative_to(local_path)
                    content += f"- [`{rel}`]({github_base}/{rel})\n"
            else:
                content += "The main entry points for the application.\n"
        else:
            content += "The main entry points for the application.\n"
        
        content += """
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
        
        # Also check relations (using source_id filter)
        relations = self.graph.get_relations(source_id=repo.id)
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
    
    def _get_local_repo_path(self, repo: Repository) -> Optional[Path]:
        """Get the local path for a repository if it exists."""
        if not self.use_local_repos:
            return None
        
        # Extract org and repo name
        repo_name = repo.name
        org = None
        
        if "/" in repo_name:
            org, repo_name = repo_name.split("/", 1)
        elif repo.url:
            parts = repo.url.rstrip("/").split("/")
            if len(parts) >= 2:
                org = parts[-2]
                repo_name = parts[-1].replace(".git", "")
        
        if not org:
            org = "redmatter"  # Default
        
        # Try different paths
        for try_org in [org, "redmatter", "natterbox", "SemiConscious"]:
            path = self.local_repos_path / try_org / repo_name
            if path.exists():
                return path
        
        return None
    
    def _detect_language_from_repo(self, repo_path: Path) -> Optional[str]:
        """Detect the primary language from local repo files."""
        if not repo_path or not repo_path.exists():
            return None
        
        # Language detection by file presence
        if (repo_path / "go.mod").exists():
            return "Go"
        if (repo_path / "package.json").exists():
            # Check if TypeScript
            if (repo_path / "tsconfig.json").exists():
                return "TypeScript"
            return "JavaScript"
        if (repo_path / "requirements.txt").exists() or (repo_path / "pyproject.toml").exists():
            return "Python"
        if (repo_path / "pom.xml").exists() or (repo_path / "build.gradle").exists():
            return "Java"
        if (repo_path / "Cargo.toml").exists():
            return "Rust"
        if any(repo_path.glob("*.csproj")):
            return "C#"
        
        return None
    
    def _read_actual_structure(self, repo_path: Path, max_depth: int = 3) -> str:
        """Read the actual directory structure from a local repo."""
        if not repo_path or not repo_path.exists():
            return ""
        
        def build_tree(path: Path, prefix: str = "", depth: int = 0) -> list[str]:
            if depth > max_depth:
                return []
            
            lines = []
            items = []
            
            try:
                for item in sorted(path.iterdir()):
                    # Skip hidden files and common non-essential dirs
                    if item.name.startswith(".") or item.name in ["node_modules", "__pycache__", "vendor", "build", "dist", ".git"]:
                        continue
                    items.append(item)
            except PermissionError:
                return []
            
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "
                
                if item.is_dir():
                    lines.append(f"{prefix}{connector}{item.name}/")
                    extension = "    " if is_last else "│   "
                    lines.extend(build_tree(item, prefix + extension, depth + 1))
                else:
                    lines.append(f"{prefix}{connector}{item.name}")
            
            return lines
        
        tree_lines = build_tree(repo_path)
        if tree_lines:
            return "```\n" + "\n".join(tree_lines[:60]) + "\n```"
        return ""
    
    def _get_go_components(self, repo_path: Path) -> list[dict]:
        """Get components from Go cmd/ directory."""
        components = []
        cmd_dir = repo_path / "cmd"
        
        if not cmd_dir.exists():
            return components
        
        for item in sorted(cmd_dir.iterdir()):
            if item.is_dir():
                component = {"name": item.name, "path": f"cmd/{item.name}"}
                
                # Check for README
                readme_path = item / "README.md"
                if readme_path.exists():
                    try:
                        content = readme_path.read_text()[:500]
                        # Extract first line as description
                        first_line = content.split("\n")[0].strip("#").strip()
                        component["description"] = first_line
                    except Exception:
                        pass
                
                # Check for main.go
                if (item / "main.go").exists():
                    component["has_main"] = True
                
                components.append(component)
        
        return components
    
    async def _write_file(self, path: Path, content: str) -> None:
        """Write content to a file."""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would write: {path}")
            return
        
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w") as f:
            await f.write(content)
        
        self.logger.debug(f"Wrote: {path}")
