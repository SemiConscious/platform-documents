"""Cross Reference Agent - adds links between related documents."""

import asyncio
import logging
import re
from pathlib import Path
from typing import Any, Optional

import aiofiles

from ..base import BaseAgent, AgentResult, AgentContext
from ...knowledge import Service, Domain, EntityType

logger = logging.getLogger("doc-agent.agents.quality.cross_reference")


class CrossReferenceAgent(BaseAgent):
    """
    Agent that adds cross-references between related documents.
    
    Capabilities:
    - Detect mentions of services/concepts and add links
    - Add "Related Documents" sections
    - Create breadcrumb navigation
    - Validate all internal links work
    """
    
    name = "cross_reference"
    description = "Adds cross-references and links between related documents"
    version = "0.1.0"
    
    def __init__(self, context: AgentContext):
        super().__init__(context)
        self.output_dir = context.output_dir
        self.dry_run = context.dry_run
        
        # Build lookup tables
        self.service_names: dict[str, str] = {}  # name -> id
        self.domain_names: dict[str, str] = {}   # name -> id
    
    async def run(self) -> AgentResult:
        """Execute the cross-referencing process."""
        self.logger.info("Starting cross-reference processing")
        
        # Build lookup tables
        self._build_lookup_tables()
        
        # Find all markdown files
        md_files = list(self.output_dir.rglob("*.md"))
        self.logger.info(f"Processing {len(md_files)} markdown files")
        
        updated_files = 0
        broken_links = []
        added_links = 0
        
        for md_file in md_files:
            try:
                result = await self._process_file(md_file)
                if result["updated"]:
                    updated_files += 1
                added_links += result["links_added"]
                broken_links.extend(result["broken_links"])
            except Exception as e:
                self.logger.warning(f"Failed to process {md_file}: {e}")
        
        self.logger.info(
            f"Cross-referencing complete: {updated_files} files updated, "
            f"{added_links} links added, {len(broken_links)} broken links found"
        )
        
        return AgentResult(
            success=True,
            data={
                "files_processed": len(md_files),
                "files_updated": updated_files,
                "links_added": added_links,
                "broken_links": broken_links,
            },
        )
    
    def _build_lookup_tables(self) -> None:
        """Build lookup tables for services and domains."""
        for service in self.graph.get_services():
            # Add various name variations
            self.service_names[service.name.lower()] = service.id
            self.service_names[service.name.lower().replace("-", " ")] = service.id
            self.service_names[service.name.lower().replace("_", " ")] = service.id
        
        for domain in self.graph.get_domains():
            self.domain_names[domain.name.lower()] = domain.id
    
    async def _process_file(self, file_path: Path) -> dict[str, Any]:
        """Process a single markdown file for cross-references."""
        async with aiofiles.open(file_path, "r") as f:
            content = await f.read()
        
        original_content = content
        links_added = 0
        broken_links = []
        
        # Add service links
        content, service_links = self._add_service_links(content, file_path)
        links_added += service_links
        
        # Add domain links
        content, domain_links = self._add_domain_links(content, file_path)
        links_added += domain_links
        
        # Validate existing links
        broken = self._validate_links(content, file_path)
        broken_links.extend(broken)
        
        # Add breadcrumbs if not present
        if "<!-- breadcrumb -->" not in content:
            breadcrumb = self._generate_breadcrumb(file_path)
            if breadcrumb:
                # Insert after frontmatter
                if content.startswith("---"):
                    end_frontmatter = content.find("---", 3)
                    if end_frontmatter > 0:
                        content = (
                            content[:end_frontmatter + 3] +
                            f"\n\n<!-- breadcrumb -->\n{breadcrumb}\n" +
                            content[end_frontmatter + 3:]
                        )
        
        # Write if changed
        updated = content != original_content
        if updated and not self.dry_run:
            async with aiofiles.open(file_path, "w") as f:
                await f.write(content)
        
        return {
            "updated": updated,
            "links_added": links_added,
            "broken_links": broken_links,
        }
    
    def _add_service_links(self, content: str, file_path: Path) -> tuple[str, int]:
        """Add links to service mentions in content."""
        links_added = 0
        
        for service_name, service_id in self.service_names.items():
            # Skip if this is the service's own documentation
            if service_id.replace("service:", "") in str(file_path):
                continue
            
            # Pattern to match service name not already in a link
            pattern = rf'(?<!\[)(?<!/)\b({re.escape(service_name)})\b(?!\]|\()'
            
            # Calculate relative path from current file to service
            service_slug = service_id.replace("service:", "")
            service_path = self.output_dir / "services" / service_slug / "README.md"
            
            if service_path.exists():
                rel_path = self._relative_path(file_path, service_path)
                
                def replace_match(match):
                    nonlocal links_added
                    links_added += 1
                    return f"[{match.group(1)}]({rel_path})"
                
                # Only replace first occurrence to avoid over-linking
                content = re.sub(pattern, replace_match, content, count=1, flags=re.IGNORECASE)
        
        return content, links_added
    
    def _add_domain_links(self, content: str, file_path: Path) -> tuple[str, int]:
        """Add links to domain mentions in content."""
        links_added = 0
        
        for domain_name, domain_id in self.domain_names.items():
            # Skip if this is the domain's own documentation
            if domain_id.replace("domain:", "") in str(file_path):
                continue
            
            pattern = rf'(?<!\[)(?<!/)\b({re.escape(domain_name)})\b(?!\]|\()'
            
            domain_slug = domain_id.replace("domain:", "")
            domain_path = self.output_dir / "architecture" / "domains" / domain_slug / "overview.md"
            
            if domain_path.exists():
                rel_path = self._relative_path(file_path, domain_path)
                
                def replace_match(match):
                    nonlocal links_added
                    links_added += 1
                    return f"[{match.group(1)}]({rel_path})"
                
                content = re.sub(pattern, replace_match, content, count=1, flags=re.IGNORECASE)
        
        return content, links_added
    
    def _validate_links(self, content: str, file_path: Path) -> list[dict[str, str]]:
        """Validate that all internal links point to existing files."""
        broken = []
        
        # Find all markdown links
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        
        for match in link_pattern.finditer(content):
            link_text = match.group(1)
            link_target = match.group(2)
            
            # Skip external links
            if link_target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            
            # Resolve relative path
            target_path = (file_path.parent / link_target).resolve()
            
            if not target_path.exists():
                broken.append({
                    "file": str(file_path),
                    "link_text": link_text,
                    "target": link_target,
                })
        
        return broken
    
    def _generate_breadcrumb(self, file_path: Path) -> str:
        """Generate breadcrumb navigation for a file."""
        try:
            rel_path = file_path.relative_to(self.output_dir)
        except ValueError:
            return ""
        
        parts = list(rel_path.parts[:-1])  # Exclude filename
        
        if not parts:
            return ""
        
        crumbs = [f"[Home](/{self._path_to_index(file_path, 'index.md')})"]
        
        current = self.output_dir
        for i, part in enumerate(parts):
            current = current / part
            index_file = current / "index.md"
            overview_file = current / "overview.md"
            
            if index_file.exists():
                rel = self._relative_path(file_path, index_file)
                crumbs.append(f"[{part.replace('-', ' ').title()}]({rel})")
            elif overview_file.exists():
                rel = self._relative_path(file_path, overview_file)
                crumbs.append(f"[{part.replace('-', ' ').title()}]({rel})")
            else:
                crumbs.append(part.replace('-', ' ').title())
        
        return " > ".join(crumbs)
    
    def _relative_path(self, from_file: Path, to_file: Path) -> str:
        """Calculate relative path from one file to another."""
        try:
            from_dir = from_file.parent
            rel = to_file.relative_to(self.output_dir)
            from_rel = from_dir.relative_to(self.output_dir)
            
            # Calculate up-traversals needed
            up_count = len(from_rel.parts)
            up = "../" * up_count
            
            return up + str(rel)
        except ValueError:
            return str(to_file)
    
    def _path_to_index(self, from_file: Path, index_name: str) -> str:
        """Get relative path from file to the root index."""
        try:
            from_dir = from_file.parent
            from_rel = from_dir.relative_to(self.output_dir)
            up_count = len(from_rel.parts)
            return "../" * up_count + index_name
        except ValueError:
            return index_name
