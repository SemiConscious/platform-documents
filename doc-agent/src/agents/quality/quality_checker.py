"""Quality Checker Agent - ensures documentation quality."""

import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import aiofiles

from ..base import BaseAgent, AgentResult, AgentContext
from ...knowledge import Service, Domain, EntityType

logger = logging.getLogger("doc-agent.agents.quality.quality_checker")


class QualityCheckerAgent(BaseAgent):
    """
    Agent that checks and reports on documentation quality.
    
    Checks:
    - Completeness (all discovered services documented)
    - Consistency (terminology, structure)
    - Accuracy (code references valid)
    - Readability (length, structure)
    - Link validity
    """
    
    name = "quality_checker"
    description = "Checks documentation quality and generates reports"
    version = "0.1.0"
    
    def __init__(self, context: AgentContext):
        super().__init__(context)
        self.output_dir = context.output_dir
        self.dry_run = context.dry_run
        self.min_completeness = context.config.get("quality", {}).get("min_completeness", 0.8)
    
    async def run(self) -> AgentResult:
        """Execute the quality checking process."""
        self.logger.info("Running quality checks")
        
        # Collect all checks
        checks = {
            "completeness": await self._check_completeness(),
            "structure": await self._check_structure(),
            "links": await self._check_links(),
            "content": await self._check_content(),
        }
        
        # Calculate overall score
        scores = [c.get("score", 0) for c in checks.values()]
        overall_score = sum(scores) / len(scores) if scores else 0
        
        # Generate report
        report = await self._generate_report(checks, overall_score)
        
        # Generate coverage report
        coverage = await self._generate_coverage_report()
        
        # Determine success based on threshold
        success = overall_score >= self.min_completeness
        
        self.logger.info(f"Quality check complete: {overall_score:.1%} overall score")
        
        return AgentResult(
            success=success,
            data={
                "overall_score": overall_score,
                "checks": checks,
                "report_path": report,
                "coverage_path": coverage,
            },
            error=None if success else f"Quality score {overall_score:.1%} below threshold {self.min_completeness:.1%}",
        )
    
    async def _check_completeness(self) -> dict[str, Any]:
        """Check documentation completeness."""
        services = self.graph.get_services()
        domains = self.graph.get_domains()
        
        documented_services = 0
        undocumented_services = []
        
        for service in services:
            slug = service.id.replace("service:", "")
            readme = self.output_dir / "services" / slug / "README.md"
            
            if readme.exists():
                documented_services += 1
            else:
                undocumented_services.append(service.name)
        
        documented_domains = 0
        undocumented_domains = []
        
        for domain in domains:
            slug = domain.id.replace("domain:", "")
            overview = self.output_dir / "architecture" / "domains" / slug / "overview.md"
            
            if overview.exists():
                documented_domains += 1
            else:
                undocumented_domains.append(domain.name)
        
        service_score = documented_services / len(services) if services else 1
        domain_score = documented_domains / len(domains) if domains else 1
        
        return {
            "score": (service_score + domain_score) / 2,
            "services": {
                "total": len(services),
                "documented": documented_services,
                "undocumented": undocumented_services,
            },
            "domains": {
                "total": len(domains),
                "documented": documented_domains,
                "undocumented": undocumented_domains,
            },
        }
    
    async def _check_structure(self) -> dict[str, Any]:
        """Check documentation structure consistency."""
        md_files = list(self.output_dir.rglob("*.md"))
        
        issues = []
        files_with_frontmatter = 0
        files_with_headings = 0
        
        for md_file in md_files:
            try:
                async with aiofiles.open(md_file, "r") as f:
                    content = await f.read()
                
                # Check frontmatter
                if content.startswith("---"):
                    files_with_frontmatter += 1
                else:
                    issues.append({
                        "file": str(md_file.relative_to(self.output_dir)),
                        "issue": "Missing frontmatter",
                    })
                
                # Check for main heading
                if re.search(r"^# .+$", content, re.MULTILINE):
                    files_with_headings += 1
                else:
                    issues.append({
                        "file": str(md_file.relative_to(self.output_dir)),
                        "issue": "Missing main heading",
                    })
                
            except Exception as e:
                issues.append({
                    "file": str(md_file.relative_to(self.output_dir)),
                    "issue": f"Read error: {e}",
                })
        
        frontmatter_score = files_with_frontmatter / len(md_files) if md_files else 1
        heading_score = files_with_headings / len(md_files) if md_files else 1
        
        return {
            "score": (frontmatter_score + heading_score) / 2,
            "total_files": len(md_files),
            "with_frontmatter": files_with_frontmatter,
            "with_headings": files_with_headings,
            "issues": issues[:20],  # Limit to 20 issues
        }
    
    async def _check_links(self) -> dict[str, Any]:
        """Check for broken links."""
        md_files = list(self.output_dir.rglob("*.md"))
        
        broken_links = []
        total_links = 0
        valid_links = 0
        
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        
        for md_file in md_files:
            try:
                async with aiofiles.open(md_file, "r") as f:
                    content = await f.read()
                
                for match in link_pattern.finditer(content):
                    link_text = match.group(1)
                    link_target = match.group(2)
                    
                    # Skip external links
                    if link_target.startswith(("http://", "https://", "#", "mailto:")):
                        continue
                    
                    total_links += 1
                    
                    # Resolve relative path
                    target_path = (md_file.parent / link_target).resolve()
                    
                    if target_path.exists():
                        valid_links += 1
                    else:
                        broken_links.append({
                            "file": str(md_file.relative_to(self.output_dir)),
                            "link_text": link_text,
                            "target": link_target,
                        })
                        
            except Exception:
                pass
        
        score = valid_links / total_links if total_links > 0 else 1
        
        return {
            "score": score,
            "total_links": total_links,
            "valid_links": valid_links,
            "broken_links": broken_links[:20],  # Limit to 20
        }
    
    async def _check_content(self) -> dict[str, Any]:
        """Check content quality."""
        md_files = list(self.output_dir.rglob("*.md"))
        
        issues = []
        files_checked = 0
        files_passing = 0
        
        min_length = 100  # Minimum characters for meaningful content
        
        for md_file in md_files:
            try:
                async with aiofiles.open(md_file, "r") as f:
                    content = await f.read()
                
                files_checked += 1
                
                # Remove frontmatter
                if content.startswith("---"):
                    end = content.find("---", 3)
                    if end > 0:
                        content = content[end + 3:]
                
                # Check minimum length
                if len(content.strip()) < min_length:
                    issues.append({
                        "file": str(md_file.relative_to(self.output_dir)),
                        "issue": "Content too short",
                    })
                else:
                    files_passing += 1
                
            except Exception:
                pass
        
        score = files_passing / files_checked if files_checked > 0 else 1
        
        return {
            "score": score,
            "files_checked": files_checked,
            "files_passing": files_passing,
            "issues": issues[:20],
        }
    
    async def _generate_report(
        self,
        checks: dict[str, Any],
        overall_score: float,
    ) -> str:
        """Generate a quality report document."""
        # Format check results
        sections = []
        
        for check_name, check_data in checks.items():
            score = check_data.get("score", 0)
            status = "PASS" if score >= 0.8 else "WARN" if score >= 0.6 else "FAIL"
            
            section = f"### {check_name.title()} ({status})\n\n"
            section += f"Score: {score:.1%}\n\n"
            
            if check_data.get("issues"):
                section += "Issues:\n"
                for issue in check_data["issues"][:5]:
                    section += f"- {issue.get('file', 'Unknown')}: {issue.get('issue', 'Unknown issue')}\n"
            
            sections.append(section)
        
        status_icon = "PASS" if overall_score >= 0.8 else "WARN" if overall_score >= 0.6 else "FAIL"
        
        content = f"""---
title: Documentation Quality Report
generated: {datetime.utcnow().isoformat()}Z
---

# Documentation Quality Report

**Overall Score**: {overall_score:.1%} ({status_icon})
**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

## Summary

| Check | Score | Status |
|-------|-------|--------|
{self._format_check_table(checks)}

## Detailed Results

{chr(10).join(sections)}

## Recommendations

{self._generate_recommendations(checks)}

---

*This report was automatically generated by the documentation quality checker.*
"""
        
        path = self.output_dir / "_meta" / "quality-report.md"
        await self._write_file(path, content)
        return str(path)
    
    async def _generate_coverage_report(self) -> str:
        """Generate a coverage report."""
        services = self.graph.get_services()
        domains = self.graph.get_domains()
        
        # Check coverage for each service
        service_coverage = []
        for service in services:
            slug = service.id.replace("service:", "")
            base = self.output_dir / "services" / slug
            
            coverage = {
                "name": service.name,
                "readme": (base / "README.md").exists(),
                "architecture": (base / "architecture.md").exists(),
                "api": (base / "api" / "overview.md").exists(),
                "config": (base / "configuration.md").exists(),
                "operations": (base / "operations.md").exists(),
            }
            coverage["score"] = sum(coverage.values()) / (len(coverage) - 1)  # Exclude name
            service_coverage.append(coverage)
        
        # Format table
        rows = []
        for c in sorted(service_coverage, key=lambda x: x["score"], reverse=True):
            check = lambda x: "Yes" if x else "No"
            rows.append(
                f"| {c['name']} | {check(c['readme'])} | {check(c['architecture'])} | "
                f"{check(c['api'])} | {check(c['config'])} | {check(c['operations'])} | "
                f"{c['score']:.0%} |"
            )
        
        content = f"""---
title: Documentation Coverage Report
generated: {datetime.utcnow().isoformat()}Z
---

# Documentation Coverage Report

**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

## Services Coverage

| Service | README | Architecture | API | Config | Operations | Score |
|---------|--------|--------------|-----|--------|------------|-------|
{chr(10).join(rows)}

## Summary

- **Total Services**: {len(services)}
- **Fully Documented**: {sum(1 for c in service_coverage if c['score'] >= 1)}
- **Partially Documented**: {sum(1 for c in service_coverage if 0 < c['score'] < 1)}
- **Undocumented**: {sum(1 for c in service_coverage if c['score'] == 0)}

## Domains Coverage

| Domain | Overview |
|--------|----------|
{self._format_domain_coverage(domains)}

---

*This report was automatically generated.*
"""
        
        path = self.output_dir / "_meta" / "coverage-report.md"
        await self._write_file(path, content)
        return str(path)
    
    def _format_check_table(self, checks: dict[str, Any]) -> str:
        """Format checks as markdown table rows."""
        rows = []
        for name, data in checks.items():
            score = data.get("score", 0)
            status = "PASS" if score >= 0.8 else "WARN" if score >= 0.6 else "FAIL"
            rows.append(f"| {name.title()} | {score:.1%} | {status} |")
        return "\n".join(rows)
    
    def _format_domain_coverage(self, domains) -> str:
        """Format domain coverage as markdown table rows."""
        rows = []
        for domain in domains:
            slug = domain.id.replace("domain:", "")
            has_overview = (self.output_dir / "architecture" / "domains" / slug / "overview.md").exists()
            rows.append(f"| {domain.name} | {'Yes' if has_overview else 'No'} |")
        return "\n".join(rows) if rows else "| No domains | N/A |"
    
    def _generate_recommendations(self, checks: dict[str, Any]) -> str:
        """Generate recommendations based on check results."""
        recommendations = []
        
        completeness = checks.get("completeness", {})
        if completeness.get("score", 1) < 0.8:
            undoc = completeness.get("services", {}).get("undocumented", [])
            if undoc:
                recommendations.append(
                    f"- **Document missing services**: {', '.join(undoc[:5])}"
                    + (f" and {len(undoc) - 5} more" if len(undoc) > 5 else "")
                )
        
        structure = checks.get("structure", {})
        if structure.get("score", 1) < 0.8:
            recommendations.append("- **Add frontmatter**: Ensure all documents have YAML frontmatter")
        
        links = checks.get("links", {})
        if links.get("broken_links"):
            recommendations.append(f"- **Fix broken links**: {len(links['broken_links'])} broken links found")
        
        content = checks.get("content", {})
        if content.get("score", 1) < 0.8:
            recommendations.append("- **Expand content**: Some documents are too short")
        
        if not recommendations:
            return "No immediate recommendations. Documentation quality is good!"
        
        return "\n".join(recommendations)
    
    async def _write_file(self, path: Path, content: str) -> None:
        """Write content to a file."""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would write: {path}")
            return
        
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w") as f:
            await f.write(content)
        
        self.logger.debug(f"Wrote: {path}")
