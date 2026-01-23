"""
Generic documentation strategy.

Fallback strategy for repository types without a specific strategy.
Produces basic but useful documentation for any repository.
"""

from pathlib import Path
from typing import Optional
import time

from ...analyzers.models import AnalysisResult
from ...analyzers.repo_type_detector import RepoType
from .base import (
    DocumentationStrategy,
    DocumentSpec,
    DocumentSet,
    GeneratedDocument,
    QualityCriterion,
    QualityCriterionType,
)


class GenericStrategy(DocumentationStrategy):
    """
    Generic documentation strategy for unknown repository types.
    
    Provides basic documentation that works for any codebase.
    """
    
    repo_type = RepoType.UNKNOWN
    name = "generic"
    description = "Generic documentation for any repository"
    
    def get_required_documents(self) -> list[DocumentSpec]:
        """Get required documents for generic repos."""
        return [
            DocumentSpec(
                path="README.md",
                title="Overview",
                description="Repository overview and getting started",
                required=True,
                priority=1,
            ),
            DocumentSpec(
                path="architecture.md",
                title="Architecture",
                description="High-level architecture and design",
                required=False,
                priority=2,
            ),
            DocumentSpec(
                path="development.md",
                title="Development",
                description="Development setup and guidelines",
                required=False,
                priority=3,
            ),
        ]
    
    def get_quality_criteria(self) -> list[QualityCriterion]:
        """Get quality criteria for generic repos."""
        return [
            QualityCriterion(
                name="completeness",
                description="Required documents are present",
                criterion_type=QualityCriterionType.COMPLETENESS,
                weight=1.0,
                min_threshold=0.80,
            ),
            QualityCriterion(
                name="depth",
                description="Documentation has sufficient detail",
                criterion_type=QualityCriterionType.DEPTH,
                weight=0.8,
                min_threshold=0.60,
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
        """Generate basic documentation for the repository."""
        start_time = time.time()
        doc_set = DocumentSet(
            repo_name=service_name,
            repo_type=self.repo_type,
        )
        
        # Generate README
        readme = await self._generate_readme(
            repo_path, analysis, service_name, github_url
        )
        doc_set.add_document(readme)
        
        # Generate architecture if we have models/endpoints
        if analysis.models or analysis.endpoints:
            arch = await self._generate_architecture(
                repo_path, analysis, service_name, github_url
            )
            doc_set.add_document(arch)
        
        doc_set.generation_time = time.time() - start_time
        return doc_set
    
    async def _generate_readme(
        self,
        repo_path: Path,
        analysis: AnalysisResult,
        service_name: str,
        github_url: Optional[str],
    ) -> GeneratedDocument:
        """Generate README document."""
        content = f"""---
title: {service_name}
description: Documentation for {service_name}
generated: true
---

# {service_name}

## Overview

This repository contains {service_name}.

"""
        
        # Add language info
        if analysis.language:
            content += f"**Primary Language:** {analysis.language}\n\n"
        
        # Add basic stats
        content += "## Statistics\n\n"
        content += f"| Metric | Count |\n"
        content += f"|--------|-------|\n"
        content += f"| Models/Types | {len(analysis.models)} |\n"
        content += f"| Endpoints | {len(analysis.endpoints)} |\n"
        content += f"| Configuration Items | {len(analysis.config)} |\n"
        content += f"| Dependencies | {len(analysis.dependencies)} |\n\n"
        
        # Add dependencies if available
        if analysis.dependencies:
            content += "## Dependencies\n\n"
            content += "| Name | Version |\n"
            content += "|------|--------|\n"
            for dep in analysis.dependencies[:20]:  # Limit to 20
                content += f"| {dep.name} | {dep.version or 'N/A'} |\n"
            content += "\n"
        
        # Add source info
        if github_url:
            content += f"## Source\n\n- [Repository]({github_url})\n"
        
        return GeneratedDocument(
            path="README.md",  # Relative path, _write_documents handles directory
            title=f"{service_name} Overview",
            content=content,
        )
    
    async def _generate_architecture(
        self,
        repo_path: Path,
        analysis: AnalysisResult,
        service_name: str,
        github_url: Optional[str],
    ) -> GeneratedDocument:
        """Generate architecture document."""
        content = f"""---
title: {service_name} Architecture
description: Architecture overview for {service_name}
generated: true
---

# {service_name} Architecture

## Components

"""
        
        # Group models by type
        if analysis.models:
            content += "### Data Models\n\n"
            content += "| Name | Type | File |\n"
            content += "|------|------|------|\n"
            for model in analysis.models[:30]:
                file_link = self._github_link(github_url, model.file) if github_url else f"`{model.file}`"
                content += f"| {model.name} | {model.model_type.value} | {file_link} |\n"
            content += "\n"
        
        # List endpoints
        if analysis.endpoints:
            content += "### API Endpoints\n\n"
            content += "| Method | Path | Handler |\n"
            content += "|--------|------|---------|\n"
            for endpoint in analysis.endpoints[:30]:
                content += f"| {endpoint.method} | `{endpoint.path}` | {endpoint.handler or 'N/A'} |\n"
            content += "\n"
        
        # List side effects
        if analysis.side_effects:
            content += "### External Interactions\n\n"
            content += "| Category | Operation | Target |\n"
            content += "|----------|-----------|--------|\n"
            for effect in analysis.side_effects[:20]:
                content += f"| {effect.category.value} | {effect.operation} | {effect.target or 'N/A'} |\n"
            content += "\n"
        
        return GeneratedDocument(
            path="architecture.md",  # Relative path, _write_documents handles directory
            title=f"{service_name} Architecture",
            content=content,
        )
