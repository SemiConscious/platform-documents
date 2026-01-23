"""
Integration module for connecting analyzers with the documentation pipeline.

Provides helper functions to use the new multi-language analyzer system
with the existing agent framework.
"""

import logging
from pathlib import Path
from typing import Any, Optional

from .factory import AnalyzerFactory
from .models import AnalysisResult

logger = logging.getLogger("doc-agent.analyzers.integration")


def analyze_repository(
    repo_path: Path,
    github_url: Optional[str] = None,
    default_branch: str = "main",
) -> AnalysisResult:
    """
    Analyze a repository using all applicable language analyzers.
    
    This is the main entry point for the documentation pipeline.
    
    Args:
        repo_path: Path to the local repository clone
        github_url: GitHub URL for generating source links
        default_branch: Default branch for GitHub links
        
    Returns:
        Combined AnalysisResult from all language analyzers
    """
    return AnalyzerFactory.analyze_repository(
        repo_path=repo_path,
        github_url=github_url,
        default_branch=default_branch,
    )


def analyze_service_repository(
    repos_dir: Path,
    service_name: str,
    repository: Optional[str] = None,
    organizations: list[str] = None,
) -> Optional[AnalysisResult]:
    """
    Analyze a service's repository by finding it in the cloned repos.
    
    Args:
        repos_dir: Base directory containing cloned repositories
        service_name: Name of the service
        repository: Repository name (org/repo or just repo)
        organizations: List of organizations to search in
        
    Returns:
        AnalysisResult or None if repository not found
    """
    if organizations is None:
        organizations = ["redmatter", "natterbox", "SemiConscious"]
    
    # Determine repo name
    repo_name = repository or service_name
    org = None
    
    if "/" in repo_name:
        org, repo_name = repo_name.split("/", 1)
        organizations = [org]  # Only search in specified org
    
    # Clean up repo name
    repo_name = repo_name.replace("service:", "")
    
    # Search for the repository
    for try_org in organizations:
        repo_path = repos_dir / try_org / repo_name
        if repo_path.exists():
            github_url = f"https://github.com/{try_org}/{repo_name}"
            
            logger.info(f"Analyzing {try_org}/{repo_name}")
            return analyze_repository(
                repo_path=repo_path,
                github_url=github_url,
            )
    
    logger.warning(f"Repository not found for service: {service_name}")
    return None


def get_models_for_documentation(analysis: AnalysisResult) -> list[dict[str, Any]]:
    """
    Convert extracted models to documentation-friendly format.
    
    Args:
        analysis: AnalysisResult from analyzer
        
    Returns:
        List of model dictionaries ready for documentation templates
    """
    models = []
    
    for model in analysis.models:
        model_dict = {
            "name": model.name,
            "type": model.model_type.value,
            "file": model.file,
            "line": model.line,
            "github_url": model.github_url,
            "description": model.description,
            "fields": [
                {
                    "name": f.name,
                    "type": f.type,
                    "description": f.description,
                    "required": f.required,
                    "default": f.default,
                    "tags": f.tags,
                }
                for f in model.fields
            ],
            "methods": model.methods,
            "parent": model.parent,
            "implements": model.implements,
            "decorators": model.decorators,
        }
        models.append(model_dict)
    
    return models


def get_endpoints_for_documentation(analysis: AnalysisResult) -> list[dict[str, Any]]:
    """
    Convert extracted endpoints to documentation-friendly format.
    
    Args:
        analysis: AnalysisResult from analyzer
        
    Returns:
        List of endpoint dictionaries ready for documentation templates
    """
    endpoints = []
    
    for endpoint in analysis.endpoints:
        endpoint_dict = {
            "method": endpoint.method,
            "path": endpoint.path,
            "file": endpoint.file,
            "line": endpoint.line,
            "handler": endpoint.handler,
            "description": endpoint.description,
            "parameters": endpoint.parameters,
            "response_type": endpoint.response_type,
            "github_url": endpoint.github_url,
        }
        endpoints.append(endpoint_dict)
    
    return endpoints


def get_side_effects_for_documentation(analysis: AnalysisResult) -> dict[str, list[dict[str, Any]]]:
    """
    Convert extracted side effects to documentation-friendly format.
    
    Groups side effects by category for easier template rendering.
    
    Args:
        analysis: AnalysisResult from analyzer
        
    Returns:
        Dictionary mapping category to list of side effect dictionaries
    """
    effects_by_category: dict[str, list[dict]] = {}
    
    for effect in analysis.side_effects:
        category = effect.category.value
        
        if category not in effects_by_category:
            effects_by_category[category] = []
        
        effects_by_category[category].append({
            "operation": effect.operation,
            "target": effect.target,
            "file": effect.file,
            "line": effect.line,
            "description": effect.description,
            "github_url": effect.github_url,
        })
    
    return effects_by_category


def get_config_for_documentation(analysis: AnalysisResult) -> list[dict[str, Any]]:
    """
    Convert extracted configuration to documentation-friendly format.
    
    Args:
        analysis: AnalysisResult from analyzer
        
    Returns:
        List of config dictionaries ready for documentation templates
    """
    configs = []
    
    for config in analysis.config:
        config_dict = {
            "key": config.key,
            "source": config.source,
            "file": config.file,
            "line": config.line,
            "default": config.default,
            "description": config.description,
            "required": config.required,
            "github_url": config.github_url,
        }
        configs.append(config_dict)
    
    return configs


def enrich_service_metadata(
    service_metadata: dict[str, Any],
    analysis: AnalysisResult,
) -> dict[str, Any]:
    """
    Enrich service metadata with analysis results.
    
    Args:
        service_metadata: Existing service metadata dictionary
        analysis: AnalysisResult from analyzer
        
    Returns:
        Enriched metadata dictionary
    """
    enriched = dict(service_metadata)
    
    # Add analysis summary
    enriched["analysis"] = {
        "language": analysis.language,
        "model_count": len(analysis.models),
        "endpoint_count": len(analysis.endpoints),
        "side_effect_count": len(analysis.side_effects),
        "config_count": len(analysis.config),
        "dependency_count": len(analysis.dependencies),
    }
    
    # Add config keys
    enriched["config_keys"] = [c.key for c in analysis.config]
    
    # Add detected dependencies
    enriched["dependencies"] = [
        {"name": d.name, "version": d.version}
        for d in analysis.dependencies
    ]
    
    return enriched
