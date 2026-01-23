"""Technical Writer Agent - generates service-level documentation."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Optional

import aiofiles

from ..base import BaseAgent, AgentResult, AgentContext
from ...knowledge import Service, Document, Repository, EntityType
from ...knowledge.store import compute_entity_hash
from ...templates.renderer import TemplateRenderer

logger = logging.getLogger("doc-agent.agents.generation.technical_writer")


class TechnicalWriterAgent(BaseAgent):
    """
    Agent that generates service-level technical documentation.
    
    Generates for each service:
    - README with overview
    - Architecture document
    - Configuration guide
    - Operations guide
    
    Uses local repository clones when available to extract rich content.
    """
    
    name = "technical_writer"
    description = "Generates technical documentation for individual services"
    version = "0.2.0"
    
    def __init__(self, context: AgentContext, service_id: Optional[str] = None):
        super().__init__(context)
        self.renderer = TemplateRenderer()
        self.output_dir = context.output_dir
        self.dry_run = context.dry_run
        self.service_id = service_id  # If set, only document this service
        
        # Local repos directory for rich content extraction
        self.repos_dir = context.store.store_dir.parent / "repos"
        self.use_local_repos = self.repos_dir.exists()
        if self.use_local_repos:
            self.logger.info(f"Using local repos for content extraction: {self.repos_dir}")
    
    def _get_local_repo_path(self, service: Service) -> Optional[Path]:
        """Get the local repo path for a service."""
        if not self.use_local_repos or not service.repository:
            return None
        
        # Repository format is usually "org/repo-name"
        if "/" in service.repository:
            org, repo_name = service.repository.split("/", 1)
        else:
            org = "redmatter"
            repo_name = service.repository
        
        repo_path = self.repos_dir / org / repo_name
        if repo_path.exists():
            return repo_path
        
        # Try with service name
        repo_path = self.repos_dir / org / service.name
        if repo_path.exists():
            return repo_path
        
        return None
    
    def _read_local_file(self, repo_path: Path, filename: str) -> Optional[str]:
        """Read a file from local repo."""
        file_path = repo_path / filename
        if file_path.exists() and file_path.is_file():
            try:
                return file_path.read_text(errors='ignore')
            except Exception:
                pass
        return None
    
    def _find_readme(self, repo_path: Path) -> Optional[str]:
        """Find and read main README."""
        for name in ["README.md", "README", "readme.md", "Readme.md"]:
            content = self._read_local_file(repo_path, name)
            if content:
                return content
        return None
    
    def _find_component_readmes(self, repo_path: Path) -> dict[str, str]:
        """Find component/submodule READMEs (e.g., cmd/*/README.md)."""
        components = {}
        
        # Check common patterns
        patterns = [
            "cmd/*/README.md",
            "internal/*/README.md",
            "pkg/*/README.md",
            "services/*/README.md",
            "apps/*/README.md",
        ]
        
        for pattern in patterns:
            for readme_path in repo_path.glob(pattern):
                try:
                    component_name = readme_path.parent.name
                    content = readme_path.read_text(errors='ignore')
                    if content and len(content) > 50:  # Skip trivial READMEs
                        components[component_name] = content
                except Exception:
                    pass
        
        return components
    
    def _extract_repo_context(self, service: Service) -> dict[str, Any]:
        """Extract rich context from local repository."""
        repo_path = self._get_local_repo_path(service)
        if not repo_path:
            return {"has_local_repo": False}
        
        context = {"has_local_repo": True, "repo_path": str(repo_path)}
        
        # Main README
        readme = self._find_readme(repo_path)
        if readme:
            context["readme"] = readme
        
        # Component READMEs
        components = self._find_component_readmes(repo_path)
        if components:
            context["components"] = components
        
        # Check for key files
        context["has_dockerfile"] = (repo_path / "Dockerfile").exists()
        context["has_makefile"] = (repo_path / "Makefile").exists()
        context["has_go_mod"] = (repo_path / "go.mod").exists()
        context["has_package_json"] = (repo_path / "package.json").exists()
        
        # Look for config patterns in code
        config_files = []
        for ext in ["*.go", "*.py", "*.ts", "*.yaml", "*.yml"]:
            for f in repo_path.glob(f"**/{ext}"):
                if "config" in f.name.lower() or "env" in f.name.lower():
                    config_files.append(str(f.relative_to(repo_path)))
        context["config_files"] = config_files[:10]
        
        # Extract CloudWatch metrics directly from component READMEs
        metrics = self._extract_cloudwatch_metrics(context.get("components", {}))
        if metrics:
            context["extracted_metrics"] = metrics
        
        return context
    
    def _extract_cloudwatch_metrics(self, components: dict[str, str]) -> list[dict]:
        """Extract CloudWatch metrics from component README files."""
        import re
        all_metrics = []
        
        for comp_name, content in components.items():
            if "## Metrics" not in content and "**Namespace:**" not in content:
                continue
            
            # Find all namespace blocks
            namespace_pattern = r'\*\*Namespace:\*\*\s*`([^`]+)`'
            namespaces = re.findall(namespace_pattern, content)
            
            for namespace in namespaces:
                # Find section for this namespace
                ns_start = content.find(f"**Namespace:** `{namespace}`")
                if ns_start == -1:
                    continue
                
                # Find next namespace or end of file
                next_ns = content.find("**Namespace:**", ns_start + 1)
                section_end = next_ns if next_ns > 0 else len(content)
                section = content[ns_start:section_end]
                
                metric_list = []
                current_category = ""
                
                # Process the section line by line
                lines = section.split('\n')
                in_metrics_block = False
                
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    
                    # Detect indentation level (number of leading spaces)
                    indent = len(line) - len(line.lstrip())
                    
                    # Category headers are at indent 0 with "* Name - Description" format
                    if indent == 0 and stripped.startswith('* ') and not stripped.startswith('* `'):
                        current_category = stripped[2:].split(' - ')[0].strip()
                        in_metrics_block = False
                        continue
                    
                    # "* Metrics:" or "    * Metrics:" markers
                    if '* Metrics:' in line:
                        in_metrics_block = True
                        continue
                    
                    # "* Dimensions:" or "* Additional Data" end the metrics block
                    if '* Dimensions:' in line or '* Additional Data' in line:
                        in_metrics_block = False
                        continue
                    
                    # Skip Unit lines (they're sub-items of metrics)
                    if 'Unit:' in stripped:
                        continue
                    
                    # In metrics block, look for metric definitions
                    # They have pattern: "        * `MetricName` - description"
                    if in_metrics_block and '`' in line:
                        match = re.match(r'\s+\*\s+`([^`]+)`\s*-\s*(.+)', line)
                        if match:
                            metric_name = match.group(1)
                            description = match.group(2)
                            
                            # Look ahead for unit on next line
                            unit = ""
                            if i + 1 < len(lines):
                                next_line = lines[i + 1]
                                unit_match = re.search(r'Unit:\s*`([^`]+)`', next_line)
                                if unit_match:
                                    unit = unit_match.group(1)
                            
                            metric_list.append({
                                "name": metric_name,
                                "description": description.strip().rstrip('.'),
                                "unit": unit,
                                "category": current_category
                            })
                
                if metric_list:
                    all_metrics.append({
                        "namespace": namespace,
                        "component": comp_name,
                        "metrics": metric_list
                    })
        
        return all_metrics
    
    async def run(self) -> AgentResult:
        """Execute the technical writing process."""
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
        
        self.logger.info(f"Generating technical documentation for {len(services)} services")
        
        generated_docs = []
        errors = []
        
        for service in services:
            try:
                docs = await self._document_service(service)
                generated_docs.extend(docs)
            except Exception as e:
                self.logger.error(f"Failed to document service {service.name}: {e}")
                errors.append(f"{service.name}: {str(e)}")
        
        return AgentResult(
            success=len(errors) == 0 or len(generated_docs) > 0,
            data={
                "generated_docs": generated_docs,
                "services_documented": len(services),
                "errors": errors,
            },
            error="; ".join(errors) if errors else None,
        )
    
    async def _document_service(self, service: Service) -> list[str]:
        """Generate all documentation for a service."""
        generated = []
        service_slug = service.id.replace("service:", "")
        service_dir = self.output_dir / "services" / service_slug
        
        # Gather related information
        related_docs = self._get_related_documents(service)
        sources = self._get_sources(service)
        
        # Enhance service data using Claude with rich repo context
        # This is called once and passed to all generation methods
        enhanced_data = await self._enhance_service_description(service)
        
        # Generate README (also uses enhanced_data internally)
        readme_path = await self._generate_service_readme(service, service_dir, related_docs, sources, enhanced_data)
        generated.append(readme_path)
        
        # Generate architecture document with enhanced data
        arch_path = await self._generate_service_architecture(service, service_dir, enhanced_data)
        generated.append(arch_path)
        
        # Generate configuration guide with enhanced data
        config_path = await self._generate_configuration_guide(service, service_dir, enhanced_data)
        generated.append(config_path)
        
        # Generate operations guide with enhanced data
        ops_path = await self._generate_operations_guide(service, service_dir, enhanced_data)
        generated.append(ops_path)
        
        return generated
    
    async def _generate_service_readme(
        self,
        service: Service,
        service_dir: Path,
        related_docs: list[dict],
        sources: list[dict],
        enhanced_data: dict[str, Any],
    ) -> str:
        """Generate the main README for a service."""
        # Get dependencies and dependents
        deps = self.graph.get_service_dependencies(service.id)
        dependents = self.graph.get_service_dependents(service.id)
        apis = self.graph.get_service_apis(service.id)
        
        # Get repository info for bidirectional linking
        repo_info = self._get_repository_info(service)
        
        service_data = {
            "id": service.id.replace("service:", ""),
            "name": service.name,
            "description": enhanced_data.get("description", service.description),
            "purpose": enhanced_data.get("purpose"),
            "repository": service.repository,
            "repository_url": f"https://github.com/{service.repository}" if service.repository else None,
            "repository_doc_url": repo_info.get("doc_url") if repo_info else None,
            "language": service.language,
            "framework": service.framework,
            "team": service.team,
            "status": service.status,
            "dependencies": [d.name for d in deps],
            "dependents": [d.name for d in dependents],
            "apis": [
                {"name": api.name, "description": api.description, "api_type": api.api_type}
                for api in apis
            ],
            "databases": service.databases,
            "config_keys": enhanced_data.get("config_keys", []),
        }
        
        content = self.renderer.render_service_readme(service_data, related_docs, sources)
        
        path = service_dir / "README.md"
        await self._write_file(path, content)
        
        self.store.register_document(
            str(path),
            compute_entity_hash([service]),
            [service.id],
        )
        
        return str(path)
    
    def _get_repository_info(self, service: Service) -> Optional[dict]:
        """Get repository information for bidirectional linking."""
        if not service.repository:
            return None
        
        # Try to find the repository entity
        for entity in self.graph.get_entities_by_type(EntityType.REPOSITORY):
            if isinstance(entity, Repository):
                if service.repository in entity.name or (entity.url and service.repository in entity.url):
                    repo_slug = entity.name.replace("/", "-")
                    return {
                        "name": entity.name,
                        "url": entity.url,
                        "doc_url": f"../../repositories/repos/{repo_slug}/README.md",
                    }
        
        # Fallback: generate doc URL from repo name
        repo_slug = service.repository.replace("/", "-")
        return {
            "name": service.repository,
            "url": f"https://github.com/{service.repository}",
            "doc_url": f"../../repositories/repos/{repo_slug}/README.md",
        }
    
    async def _generate_service_architecture(
        self,
        service: Service,
        service_dir: Path,
        enhanced_data: dict[str, Any],
    ) -> str:
        """Generate the architecture document for a service."""
        # Use enhanced data to generate architecture content
        arch_content = await self._generate_architecture_content(service, enhanced_data)
        
        # Generate diagrams
        component_diagram = await self._generate_component_diagram(service, enhanced_data)
        flow_diagram = await self._generate_flow_diagram(service, enhanced_data)
        
        content = f"""---
title: {service.name} Architecture
description: Internal architecture and design of {service.name}
generated: true
---

# {service.name} Architecture

## Overview

{arch_content.get('overview', f'{service.name} is a service in the Natterbox platform.')}

## Component Diagram

{component_diagram}

## Components

{arch_content.get('components', 'No component information available.')}

## Data Flow

{flow_diagram}

## Data Model

{arch_content.get('data_model', 'See [Data Models](./data/models.md) for database schema details.')}

## Integration Points

{arch_content.get('integrations', 'This service integrates with other platform services via APIs.')}

## Design Decisions

{arch_content.get('design_decisions', 'No specific design decisions documented.')}

## Related Documents

- [Service Overview](./README.md)
- [Configuration Guide](./configuration.md)
- [Operations Guide](./operations.md)
"""
        
        path = service_dir / "architecture.md"
        await self._write_file(path, content)
        
        return str(path)
    
    async def _generate_component_diagram(self, service: Service, enhanced_data: dict[str, Any]) -> str:
        """Generate a Mermaid component diagram for the service."""
        components = enhanced_data.get("components", [])
        
        if not components:
            # Try to generate from repo context
            repo_context = self._extract_repo_context(service)
            if repo_context.get("components"):
                components = [{"name": name, "type": "component"} for name in repo_context["components"].keys()]
        
        if not components:
            return "*No component diagram available.*"
        
        # Build Mermaid diagram
        diagram = "```mermaid\ngraph TB\n"
        diagram += f"    subgraph {service.name.replace(' ', '_').replace('-', '_')}[{service.name}]\n"
        
        for i, comp in enumerate(components):
            if isinstance(comp, dict):
                name = comp.get("name", f"Component{i}")
                comp_type = comp.get("type", "component").lower()
            else:
                name = str(comp)
                comp_type = "component"
            
            # Sanitize name for Mermaid
            safe_name = name.replace("-", "_").replace(" ", "_")
            display_name = name.replace("_", " ").title()
            
            # Choose shape based on type
            if "lambda" in comp_type.lower() or "lambda" in name.lower():
                diagram += f"        {safe_name}[/{display_name}/]\n"
            elif "ecs" in comp_type.lower() or "container" in comp_type.lower():
                diagram += f"        {safe_name}[{display_name}]\n"
            else:
                diagram += f"        {safe_name}[{display_name}]\n"
        
        diagram += "    end\n"
        
        # Add external systems if known
        deps = self.graph.get_service_dependencies(service.id)
        if deps:
            for dep in deps[:5]:
                safe_dep = dep.name.replace("-", "_").replace(" ", "_")
                diagram += f"    {safe_dep}[({dep.name})]\n"
                # Connect to first component
                if components:
                    first_comp = components[0]
                    if isinstance(first_comp, dict):
                        first_name = first_comp.get("name", "Component0").replace("-", "_").replace(" ", "_")
                    else:
                        first_name = str(first_comp).replace("-", "_").replace(" ", "_")
                    diagram += f"    {first_name} --> {safe_dep}\n"
        
        diagram += "```"
        return diagram
    
    async def _generate_flow_diagram(self, service: Service, enhanced_data: dict[str, Any]) -> str:
        """Generate a Mermaid data flow diagram for the service."""
        # Get repo context for components
        repo_context = self._extract_repo_context(service)
        components = list(repo_context.get("components", {}).keys()) if repo_context.get("components") else []
        
        if not components and not enhanced_data.get("components"):
            return "*No data flow diagram available.*"
        
        # Use Claude to generate a flow diagram based on the README
        readme = repo_context.get("readme", "")[:4000] if repo_context.get("readme") else ""
        
        if not readme:
            return "*No data flow diagram available.*"
        
        prompt = f"""Based on this README for {service.name}, generate a Mermaid sequence or flowchart diagram showing the data flow.

README:
{readme}

Components found: {', '.join(components) if components else 'unknown'}

Generate a Mermaid diagram (flowchart LR or sequence diagram) showing:
1. How data flows through the components
2. External systems involved (databases, S3, APIs)
3. Key interactions

Return ONLY the Mermaid code block, nothing else. Use simple node names without special characters."""

        try:
            response = await self.call_claude(
                system_prompt="You are generating Mermaid diagrams. Return ONLY valid Mermaid code wrapped in ```mermaid and ```. Keep it simple and readable.",
                user_message=prompt,
            )
            
            # Extract mermaid code
            response = response.strip()
            if "```mermaid" in response:
                return response
            elif "```" in response:
                return response.replace("```", "```mermaid", 1)
            else:
                return f"```mermaid\n{response}\n```"
        except Exception as e:
            self.logger.warning(f"Failed to generate flow diagram: {e}")
            return "*No data flow diagram available.*"
    
    async def _generate_configuration_guide(
        self,
        service: Service,
        service_dir: Path,
        enhanced_data: dict[str, Any],
    ) -> str:
        """Generate the configuration guide for a service."""
        config_content = await self._generate_config_content(service, enhanced_data)
        
        # Build content dynamically - only include sections with actual content
        content = f"""---
title: {service.name} Configuration
description: Configuration options for {service.name}
generated: true
---

# {service.name} Configuration

## Environment Variables

{config_content.get('env_vars', 'Configuration is managed via environment variables.')}
"""
        
        # Only add config files section if it has meaningful content
        config_files = config_content.get('config_files', '')
        if config_files and 'See the repository README' not in config_files and config_files != 'No specific configuration files documented.':
            content += f"\n## Configuration Files\n\n{config_files}\n"
        
        # Only add SSM/AWS section if relevant
        if 'SSM' in str(config_content.get('env_vars', '')) or 'skyconf' in str(config_content.get('env_vars', '')).lower():
            content += """
## Configuration Sources

This service uses a layered configuration approach:

1. **Default values** - Built-in defaults in the code
2. **Environment variables** - Override defaults via environment
3. **Command line flags** - Override at runtime
4. **AWS SSM Parameter Store** - Managed via `go-skyconf` for centralized config

Use `--help` to see available command line options and their corresponding environment variables.
Use `--debug-sky` to debug SSM parameters loaded by `go-skyconf`.
"""
        
        content += """
## Related Documents

- [Service Overview](./README.md)
- [Operations Guide](./operations.md)
"""
        
        path = service_dir / "configuration.md"
        await self._write_file(path, content)
        
        return str(path)
    
    def _format_ops_section(self, data: Any) -> str:
        """Format operations data (which might be dict/list) into markdown."""
        if data is None:
            return ""
        if isinstance(data, str):
            return data
        if isinstance(data, list):
            lines = []
            for item in data:
                if isinstance(item, dict):
                    # Format dict items based on content
                    if "issue" in item:  # Common issues format
                        lines.append(f"### {item.get('issue', 'Issue')}")
                        lines.append(f"**Symptom:** {item.get('symptom', 'N/A')}")
                        lines.append(f"**Cause:** {item.get('cause', 'N/A')}")
                        lines.append(f"**Resolution:** {item.get('resolution', 'N/A')}")
                        lines.append("")
                    elif "step" in item:  # Troubleshooting steps
                        lines.append(f"{item.get('step', '')}. **{item.get('action', 'Action')}**")
                        if item.get('command'):
                            lines.append(f"```bash\n{item['command']}\n```")
                        lines.append("")
                    elif "name" in item and "command" in item:  # Commands
                        lines.append(f"### {item.get('name', 'Command')}")
                        lines.append(f"```bash\n{item['command']}\n```")
                        if item.get('description'):
                            lines.append(f"{item['description']}")
                        lines.append("")
                    elif "description" in item and "command" in item:  # Diagnostic commands
                        lines.append(f"**{item.get('description', 'Command')}:**")
                        lines.append(f"```bash\n{item['command']}\n```")
                        lines.append("")
                    elif "path" in item:  # Endpoints
                        lines.append(f"- `{item.get('path', '/')}` (port {item.get('port', 'N/A')}): {item.get('description', '')}")
                    else:
                        # Generic dict - format nicely
                        for k, v in item.items():
                            if isinstance(v, str):
                                lines.append(f"- **{k}:** {v}")
                            elif isinstance(v, list):
                                lines.append(f"- **{k}:** {', '.join(str(x) for x in v)}")
                            else:
                                lines.append(f"- **{k}:** {v}")
                else:
                    lines.append(f"- {item}")
            return "\n".join(lines)
        if isinstance(data, dict):
            lines = []
            # Handle nested structures
            if "endpoints" in data:
                lines.append("**Endpoints:**")
                for ep in data["endpoints"]:
                    if isinstance(ep, dict):
                        lines.append(f"- `{ep.get('path', '/')}` (port {ep.get('port', 'N/A')}): {ep.get('description', '')}")
                    else:
                        lines.append(f"- {ep}")
            if "commands" in data:
                lines.append("\n**Commands:**")
                for cmd in data["commands"]:
                    if isinstance(cmd, dict):
                        lines.append(f"\n**{cmd.get('name', cmd.get('description', 'Command'))}:**")
                        lines.append(f"```bash\n{cmd.get('command', '')}\n```")
                    else:
                        lines.append(f"```bash\n{cmd}\n```")
            if "log_groups" in data:
                lines.append("**Log Groups:**")
                for lg in data["log_groups"]:
                    if isinstance(lg, dict):
                        lines.append(f"- `{lg.get('name', '')}`: {lg.get('description', '')}")
                    else:
                        lines.append(f"- {lg}")
            if "useful_queries" in data:
                lines.append("\n**Useful Queries:**")
                for q in data["useful_queries"]:
                    if isinstance(q, dict):
                        query_name = q.get('name', q.get('description', 'Query'))
                        query_cmd = q.get('query', q.get('command', ''))
                        lines.append(f"\n**{query_name}:**")
                        lines.append(f"```bash\n{query_cmd}\n```")
                    else:
                        lines.append(f"```bash\n{q}\n```")
            if "access_instructions" in data:
                lines.append(f"\n**Access:** {data['access_instructions']}")
            if "diagnostic_commands" in data:
                lines.append("\n**Diagnostic Commands:**")
                for cmd in data["diagnostic_commands"]:
                    if isinstance(cmd, dict):
                        lines.append(f"\n**{cmd.get('description', 'Command')}:**")
                        lines.append(f"```bash\n{cmd.get('command', '')}\n```")
                    else:
                        lines.append(f"```bash\n{cmd}\n```")
            if "configuration_sources" in data:
                lines.append("\n**Configuration Sources (in order of precedence):**")
                for src in data["configuration_sources"]:
                    lines.append(f"1. {src}")
            if "ssm_parameter_structure" in data:
                ssm = data["ssm_parameter_structure"]
                lines.append("\n**SSM Parameter Structure:**")
                if isinstance(ssm, dict):
                    if ssm.get("project_source"):
                        lines.append(f"- **Project source:** `{ssm['project_source']}`")
                    if ssm.get("app_source"):
                        lines.append(f"- **App source:** `{ssm['app_source']}`")
                    if ssm.get("note"):
                        lines.append(f"- *Note:* {ssm['note']}")
            if "steps" in data:
                lines.append("\n**Steps:**")
                for step in data["steps"]:
                    if isinstance(step, dict):
                        lines.append(f"{step.get('step', '')}. **{step.get('action', '')}**")
                        if step.get('command'):
                            lines.append(f"```bash\n{step['command']}\n```")
                    else:
                        lines.append(f"- {step}")
            if "debug_mode" in data:
                dm = data["debug_mode"]
                if isinstance(dm, dict):
                    desc = dm.get('description', 'Enable debug mode')
                    flag = dm.get('flag', dm.get('command', ''))
                    lines.append(f"\n**Debug Mode:** {desc}")
                    if flag:
                        lines.append(f"```bash\n{flag}\n```")
                elif isinstance(dm, str):
                    lines.append(f"\n**Debug Mode:** {dm}")
            if lines:
                return "\n".join(lines)
            # Fallback: format remaining keys nicely
            for k, v in data.items():
                if isinstance(v, str):
                    lines.append(f"**{k.replace('_', ' ').title()}:** {v}")
                elif isinstance(v, list):
                    lines.append(f"\n**{k.replace('_', ' ').title()}:**")
                    for item in v:
                        if isinstance(item, dict):
                            for ik, iv in item.items():
                                lines.append(f"- **{ik}:** {iv}")
                        else:
                            lines.append(f"- {item}")
                elif isinstance(v, dict):
                    lines.append(f"\n**{k.replace('_', ' ').title()}:**")
                    for ik, iv in v.items():
                        lines.append(f"- **{ik}:** {iv}")
            return "\n".join(lines)
        return str(data)
    
    async def _generate_operations_guide(
        self,
        service: Service,
        service_dir: Path,
        enhanced_data: dict[str, Any],
    ) -> str:
        """Generate the operations guide for a service."""
        # Look for troubleshooting information from Jira
        troubleshooting_docs = self._get_troubleshooting_docs(service)
        ops_content = await self._generate_ops_content(service, troubleshooting_docs, enhanced_data)
        
        # Format structured data into markdown
        health_md = self._format_ops_section(ops_content.get('health_checks')) or 'The service exposes a /health endpoint for health checks.'
        monitoring_md = self._format_ops_section(ops_content.get('monitoring')) or 'Monitor the service using standard platform observability tools.'
        logging_md = self._format_ops_section(ops_content.get('logging')) or 'Logs are written to stdout in JSON format.'
        issues_md = self._format_ops_section(ops_content.get('common_issues')) or 'No common issues documented.'
        troubleshooting_md = self._format_ops_section(ops_content.get('troubleshooting')) or 'For troubleshooting, check the logs and metrics dashboards.'
        runbooks_md = self._format_ops_section(ops_content.get('runbooks')) or 'No specific runbooks available.'
        
        # Add expvar explanation if the term is used
        expvar_note = ""
        combined_content = health_md + troubleshooting_md + runbooks_md
        if 'expvar' in combined_content.lower() or '/debug/vars' in combined_content:
            expvar_note = """
> **Note:** `expvar` refers to Go's built-in [expvar package](https://pkg.go.dev/expvar) which exposes runtime variables via HTTP. The `/debug/vars` endpoint returns JSON with memory stats, goroutine counts, and custom application metrics.

"""
        
        content = f"""---
title: {service.name} Operations
description: Operational procedures for {service.name}
generated: true
---

# {service.name} Operations Guide
{expvar_note}
## Health Checks

{health_md}

## Monitoring

{monitoring_md}

## Logging

{logging_md}

## Common Issues

{issues_md}

## Troubleshooting

{troubleshooting_md}

## Runbooks

{runbooks_md}

## Related Documents

- [Service Overview](./README.md)
- [Configuration Guide](./configuration.md)
"""
        
        path = service_dir / "operations.md"
        await self._write_file(path, content)
        
        return str(path)
    
    async def _enhance_service_description(self, service: Service) -> dict[str, Any]:
        """Use Claude to enhance service description with rich repo context."""
        # Get related documents for context
        docs = self._get_related_documents(service)
        doc_context = "\n".join([d.get("title", "") for d in docs[:5]])
        
        # Extract rich context from local repo
        repo_context = self._extract_repo_context(service)
        
        # Build comprehensive prompt
        readme_section = ""
        if repo_context.get("readme"):
            # Truncate but keep substantial content
            readme = repo_context["readme"][:8000]
            readme_section = f"\n\nREADME Content:\n```\n{readme}\n```"
        
        components_section = ""
        if repo_context.get("components"):
            comp_parts = []
            for comp_name, comp_readme in list(repo_context["components"].items())[:5]:
                # Include up to 2000 chars per component
                comp_parts.append(f"\n### {comp_name}:\n{comp_readme[:2000]}")
            components_section = f"\n\nComponent Documentation:{chr(10).join(comp_parts)}"
        
        prompt = f"""Analyze this service thoroughly and extract documentation:

Name: {service.name}
Repository: {service.repository}
Language: {service.language}
Current description: {service.description or 'None'}
Related docs: {doc_context}
Has Dockerfile: {repo_context.get('has_dockerfile', False)}
Has Makefile: {repo_context.get('has_makefile', False)}
Config files found: {repo_context.get('config_files', [])}
{readme_section}
{components_section}

Based on ALL the above information, provide:
1. description: Improved one-line description (be specific about what it does)
2. purpose: 2-3 sentences about what the service does and why it exists
3. config_keys: List of configuration options found in README/code (name, description, required)
4. components: List of main components/subservices if multi-component (name, description, type like "ECS Container" or "Lambda")
5. architecture_overview: 2-3 paragraphs describing the architecture based on README
6. metrics: Any CloudWatch metrics documented (namespace, metric names, dimensions)
7. dependencies: External services/systems this depends on (databases, queues, other services)
8. key_commands: Important operational commands mentioned (local testing, log viewing, etc.)

Return JSON. Be thorough - extract REAL information from the README, don't make things up."""
        
        try:
            response = await self.call_claude(
                system_prompt="You are a technical documentation expert. Extract accurate information from the provided README and source content. Do not invent information - only document what is explicitly stated or clearly implied.",
                user_message=prompt,
                temperature=0.2,
            )
            
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            return json.loads(response)
        except Exception as e:
            self.logger.warning(f"Failed to enhance service description: {e}")
            return {
                "description": service.description,
                "purpose": None,
                "config_keys": [],
            }
    
    async def _generate_architecture_content(self, service: Service, enhanced_data: dict[str, Any]) -> dict[str, Any]:
        """Generate architecture content using enhanced data from repo."""
        # If we have real architecture info from README, use it
        if enhanced_data.get("architecture_overview"):
            components_md = ""
            if enhanced_data.get("components"):
                comp_lines = []
                for comp in enhanced_data["components"]:
                    if isinstance(comp, dict):
                        comp_lines.append(f"- **{comp.get('name', 'Unknown')}** ({comp.get('type', 'Component')}): {comp.get('description', 'No description')}")
                    else:
                        comp_lines.append(f"- {comp}")
                components_md = "\n".join(comp_lines)
            
            deps_md = ""
            if enhanced_data.get("dependencies"):
                dep_lines = []
                for d in enhanced_data["dependencies"]:
                    if isinstance(d, dict):
                        dep_lines.append(f"- **{d.get('name', 'Unknown')}**: {d.get('description', 'N/A')}")
                    else:
                        dep_lines.append(f"- {d}")
                deps_md = "\n".join(dep_lines)
            
            return {
                "overview": enhanced_data["architecture_overview"],
                "components": components_md or "See component documentation for details.",
                "data_model": "See [Data Models](./data/models.md) for database schema details.",
                "integrations": deps_md or "This service integrates with other platform services via APIs.",
                "design_decisions": "See the repository README for design decisions and rationale.",
            }
        
        # Fall back to Claude generation with repo context
        repo_context = self._extract_repo_context(service)
        readme = repo_context.get("readme", "")[:6000] if repo_context.get("readme") else ""
        
        prompt = f"""Generate architecture documentation for:

Service: {service.name}
Description: {service.description}
Language: {service.language}
Framework: {service.framework}
Dependencies: {service.dependencies[:5]}

README Content:
{readme}

Generate sections for:
1. overview: High-level architecture description
2. components: Main components/modules (if multi-component, list each)
3. data_model: Data handling overview
4. integrations: How it integrates with other services
5. design_decisions: Key design decisions

Return JSON. Only include information that can be inferred from the README."""
        
        try:
            response = await self.call_claude(
                system_prompt="You are a technical writer documenting service architecture. Only document what is explicitly stated or clearly implied in the README.",
                user_message=prompt,
            )
            
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            return json.loads(response)
        except Exception:
            return {}
    
    async def _generate_config_content(self, service: Service, enhanced_data: dict[str, Any]) -> dict[str, Any]:
        """Generate configuration content using enhanced data from repo."""
        # If we have real config info, use it
        if enhanced_data.get("config_keys"):
            env_table = "| Variable | Description | Required |\n|----------|-------------|----------|\n"
            for cfg in enhanced_data["config_keys"]:
                if isinstance(cfg, dict):
                    name = cfg.get("name", "UNKNOWN")
                    desc = cfg.get("description", "No description")
                    req = "Yes" if cfg.get("required") else "No"
                    env_table += f"| `{name}` | {desc} | {req} |\n"
                else:
                    env_table += f"| `{cfg}` | See README | No |\n"
            
            return {
                "env_vars": env_table,
                "config_files": "Configuration is loaded from environment variables, command line flags, and AWS SSM parameters. See the repository README for details on the configuration hierarchy.",
                "feature_flags": "Feature flags are managed via configuration values.",
                "secrets": "Secrets are managed via AWS SSM Parameter Store or environment variables.",
                "example": "# See repository README for example configurations",
            }
        
        # Fall back to Claude generation with repo context
        repo_context = self._extract_repo_context(service)
        readme = repo_context.get("readme", "")[:6000] if repo_context.get("readme") else ""
        
        prompt = f"""Generate configuration documentation for:

Service: {service.name}
Language: {service.language}
Config files in repo: {repo_context.get('config_files', [])}

README Content:
{readme}

Generate sections for:
1. env_vars: Environment variables table in markdown (name, description, required)
2. config_files: Description of config file patterns used
3. feature_flags: Any feature flags mentioned
4. secrets: Secrets management approach mentioned
5. example: Example configuration commands from README

Return JSON. Extract REAL configuration info from the README."""
        
        try:
            response = await self.call_claude(
                system_prompt="You are a technical writer documenting service configuration. Extract real configuration details from the README.",
                user_message=prompt,
            )
            
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            return json.loads(response)
        except Exception:
            return {}
    
    async def _generate_ops_content(
        self,
        service: Service,
        troubleshooting_docs: list[Document],
        enhanced_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate operations content using enhanced data from repo."""
        # If we have real metrics/commands info, use it
        result = {}
        
        # Get repo context for directly extracted metrics
        repo_context = self._extract_repo_context(service)
        
        # First try directly extracted metrics (most reliable)
        if repo_context.get("extracted_metrics"):
            metrics_md = "### CloudWatch Metrics\n\n"
            for m in repo_context["extracted_metrics"]:
                namespace = m.get('namespace', 'N/A')
                component = m.get('component', '')
                metric_list = m.get('metrics', [])
                
                metrics_md += f"#### `{namespace}`"
                if component:
                    metrics_md += f" ({component})"
                metrics_md += "\n\n**Metrics:**\n"
                
                for metric in metric_list:
                    name = metric.get('name', '')
                    unit = metric.get('unit', '')
                    desc = metric.get('description', '')
                    metrics_md += f"- `{name}`"
                    if unit:
                        metrics_md += f" ({unit})"
                    if desc:
                        metrics_md += f" - {desc}"
                    metrics_md += "\n"
                metrics_md += "\n"
            
            result["monitoring"] = metrics_md
        elif enhanced_data.get("metrics"):
            metrics = enhanced_data["metrics"]
            if isinstance(metrics, list):
                metrics_md = "### CloudWatch Metrics\n\n"
                for m in metrics:
                    if isinstance(m, dict):
                        namespace = m.get('namespace', 'N/A')
                        category = m.get('category', '')
                        metric_names = m.get('metrics', [])
                        dimensions = m.get('dimensions', [])
                        cardinality = m.get('cardinality', '')
                        
                        metrics_md += f"#### `{namespace}`"
                        if category:
                            metrics_md += f" - {category}"
                        metrics_md += "\n\n"
                        
                        if cardinality:
                            metrics_md += f"*Cardinality: {cardinality}*\n\n"
                        
                        if dimensions:
                            dim_str = ", ".join([f"`{d}`" for d in dimensions]) if isinstance(dimensions, list) else f"`{dimensions}`"
                            metrics_md += f"**Dimensions:** {dim_str}\n\n"
                        
                        metrics_md += "**Metrics:**\n"
                        for metric in metric_names:
                            if isinstance(metric, dict):
                                name = metric.get('name', str(metric))
                                unit = metric.get('unit', '')
                                desc = metric.get('description', '')
                                metrics_md += f"- `{name}`"
                                if unit:
                                    metrics_md += f" ({unit})"
                                if desc:
                                    metrics_md += f" - {desc}"
                                metrics_md += "\n"
                            else:
                                metrics_md += f"- `{metric}`\n"
                        metrics_md += "\n"
                    else:
                        metrics_md += f"- {m}\n"
                result["monitoring"] = metrics_md
            elif isinstance(metrics, dict):
                metrics_md = f"**Namespace:** `{metrics.get('namespace', 'N/A')}`\n\nMetrics:\n"
                for name in metrics.get("metrics", []):
                    if isinstance(name, dict):
                        metrics_md += f"- `{name.get('name', str(name))}`\n"
                    else:
                        metrics_md += f"- `{name}`\n"
                result["monitoring"] = metrics_md
        
        if enhanced_data.get("key_commands"):
            cmds = enhanced_data["key_commands"]
            if isinstance(cmds, list):
                runbook_parts = []
                for cmd in cmds:
                    if isinstance(cmd, str):
                        runbook_parts.append(f"```bash\n{cmd}\n```")
                    else:
                        name = cmd.get('name', cmd.get('description', 'Command'))
                        command = cmd.get('command', '')
                        desc = cmd.get('description', '')
                        part = f"### {name}\n"
                        if desc and desc != name:
                            part += f"{desc}\n\n"
                        part += f"```bash\n{command}\n```"
                        runbook_parts.append(part)
                result["runbooks"] = "\n\n".join(runbook_parts)
        
        # Get trouble context
        trouble_context = "\n".join([
            f"- {d.name}: {d.description}"
            for d in troubleshooting_docs[:5]
        ])
        
        # Get repo context for more info
        repo_context = self._extract_repo_context(service)
        readme = repo_context.get("readme", "")[:5000] if repo_context.get("readme") else ""
        
        # Merge components that have monitoring info
        component_ops = ""
        if repo_context.get("components"):
            for comp_name, comp_readme in repo_context["components"].items():
                if "metric" in comp_readme.lower() or "monitor" in comp_readme.lower() or "log" in comp_readme.lower():
                    # Include full component README for metrics extraction (up to 4000 chars)
                    component_ops += f"\n\n### {comp_name}\n{comp_readme[:4000]}"
        
        prompt = f"""Generate operations documentation for:

Service: {service.name}
Known issues/troubleshooting info:
{trouble_context or 'None available'}

README Content (operational info):
{readme}

Component-specific operations info:
{component_ops}

Generate sections for:

1. health_checks: Health check endpoints as object with:
   - endpoints: list of {{path, port, description}}
   - commands: list of {{name, command, description}} for checking health

2. monitoring: CloudWatch metrics. EXTRACT EVERY METRIC mentioned in the README with FULL DETAIL:
   - For each namespace, list ALL metrics with their:
     - namespace (e.g. "RM/Archiving/PurgeLag")
     - category (e.g. "Org Level Metrics", "Summary Stats", "S3 Batch Job Metrics")
     - metrics: list ALL metric names (e.g. RegularPurgeLagDays, LaggingOrgsCount, PendingJobs)
     - dimensions (e.g. OrgID, Job)
     - units (Count, Percent, Seconds)
   - Include cardinality notes if mentioned

3. logging: Object with:
   - log_groups: list of {{name, description}}
   - useful_queries: list of {{name, query}} - include the FULL aws logs tail commands
   - access_instructions: how to login to AWS

4. common_issues: list of {{issue, symptom, cause, resolution}}

5. troubleshooting: Object with:
   - diagnostic_commands: list of {{description, command}}
   - debug_mode: {{description, flag}}

6. runbooks: List of operational commands with DESCRIPTIVE NAMES explaining what each does:
   - Format: list of {{name, command, description}}
   - name should describe the PURPOSE (e.g. "Build all binaries", "SSH tunnel to Big DB")
   - command is the actual shell command
   - description explains when/why to use it

Return JSON. Extract ALL operational info from the README - every metric, every command with context."""
        
        try:
            response = await self.call_claude(
                system_prompt="You are an SRE writing operations documentation. Extract real operational information from the README - metrics, log viewing commands, health checks, etc.",
                user_message=prompt,
            )
            
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            claude_result = json.loads(response)
            # Merge with our extracted data (our data takes precedence)
            for key, value in claude_result.items():
                if key not in result:
                    result[key] = value
            
            return result
        except Exception:
            return result if result else {}
    
    def _get_related_documents(self, service: Service) -> list[dict]:
        """Get documents related to a service."""
        docs = []
        
        # Get documents that reference this service
        relations = self.graph.get_relations(
            target_id=service.id,
            relation_type=RelationType.DOCUMENTS,
        ) if hasattr(self.graph, 'get_relations') else []
        
        for relation in relations:
            doc = self.graph.get_entity(relation.source_id)
            if doc and isinstance(doc, Document):
                docs.append({
                    "title": doc.name,
                    "path": doc.url,
                    "type": doc.source_type,
                })
        
        return docs
    
    def _get_sources(self, service: Service) -> list[dict]:
        """Get source references for a service."""
        sources = []
        
        for source_url in service.sources:
            if "github" in source_url:
                sources.append({
                    "type": "GitHub",
                    "title": f"{service.name} Repository",
                    "url": source_url,
                })
            elif "confluence" in source_url:
                sources.append({
                    "type": "Confluence",
                    "title": "Documentation",
                    "url": source_url,
                })
        
        return sources
    
    def _get_troubleshooting_docs(self, service: Service) -> list[Document]:
        """Get troubleshooting documents for a service."""
        docs = []
        
        # Get bug pattern documents
        all_docs = self.graph.get_entities_by_type(EntityType.DOCUMENT)
        for doc in all_docs:
            if isinstance(doc, Document):
                if "troubleshooting" in doc.labels or "bugs" in doc.labels:
                    if service.name.lower() in doc.name.lower() or \
                       service.name in doc.linked_services:
                        docs.append(doc)
        
        return docs
    
    async def _write_file(self, path: Path, content: str) -> None:
        """Write content to a file, creating directories as needed."""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would write: {path}")
            return
        
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w") as f:
            await f.write(content)
        
        self.logger.debug(f"Wrote: {path}")


# Import for type hints
from ...knowledge import Document
from ...knowledge.models import RelationType
