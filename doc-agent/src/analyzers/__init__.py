"""
Multi-language code analyzers.

This package provides AST-based code analysis for extracting
data models, API endpoints, side effects, and configuration
from source code across multiple programming languages.

Supported languages:
- Go
- PHP
- TypeScript/JavaScript
- Python
- Salesforce (Apex, LWC)
- Lua
- Bash
- Rust
- C/C++
- ActionScript
- Terraform/HCL
"""

from .base import BaseLanguageAnalyzer
from .factory import (
    AnalyzerFactory,
    AnalyzerRegistry,
    register_analyzer,
)
from .models import (
    AnalysisResult,
    ExtractedConfig,
    ExtractedDependency,
    ExtractedEndpoint,
    ExtractedField,
    ExtractedModel,
    ExtractedSideEffect,
    ModelType,
    SideEffectCategory,
)
from .integration import (
    analyze_repository,
    analyze_service_repository,
    get_models_for_documentation,
    get_endpoints_for_documentation,
    get_side_effects_for_documentation,
    get_config_for_documentation,
    enrich_service_metadata,
)
from .repo_type_detector import (
    RepoType,
    RepoTypeResult,
    detect_repo_type,
    get_documentation_requirements,
)
from .ai_analyzer import (
    AICodeAnalyzer,
    AIAnalysisConfig,
)

__all__ = [
    # Base classes
    "BaseLanguageAnalyzer",
    # Factory and registry
    "AnalyzerFactory",
    "AnalyzerRegistry",
    "register_analyzer",
    # Data models
    "AnalysisResult",
    "ExtractedConfig",
    "ExtractedDependency",
    "ExtractedEndpoint",
    "ExtractedField",
    "ExtractedModel",
    "ExtractedSideEffect",
    "ModelType",
    "SideEffectCategory",
    # Integration helpers
    "analyze_repository",
    "analyze_service_repository",
    "get_models_for_documentation",
    "get_endpoints_for_documentation",
    "get_side_effects_for_documentation",
    "get_config_for_documentation",
    "enrich_service_metadata",
    # Repository type detection
    "RepoType",
    "RepoTypeResult",
    "detect_repo_type",
    "get_documentation_requirements",
    # AI-powered analyzer
    "AICodeAnalyzer",
    "AIAnalysisConfig",
]
