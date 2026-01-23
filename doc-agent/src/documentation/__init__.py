"""
Documentation generation package.

This package provides type-aware documentation strategies for different
repository types, producing beautiful, detailed documentation tailored
to each codebase's nature.

Includes AI-powered template generation for custom doc structures.
"""

from .strategies import (
    DocumentationStrategy,
    DocumentSpec,
    DocumentSet,
    QualityCriterion,
    StrategyFactory,
)
from .ai_template_generator import (
    AITemplateGenerator,
    DocumentationPlan,
    DocumentTemplate,
)
from .ai_content_writer import (
    AIContentWriter,
    GeneratedContent,
    ContentGenerationResult,
)

__all__ = [
    "DocumentationStrategy",
    "DocumentSpec",
    "DocumentSet",
    "QualityCriterion",
    "StrategyFactory",
    # AI template generation
    "AITemplateGenerator",
    "DocumentationPlan",
    "DocumentTemplate",
    # AI content writing
    "AIContentWriter",
    "GeneratedContent",
    "ContentGenerationResult",
]
