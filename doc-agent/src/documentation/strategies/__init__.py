"""
Documentation strategies package.

Provides type-specific documentation generation strategies.
"""

from .base import (
    DocumentationStrategy,
    DocumentSpec,
    DocumentSet,
    GeneratedDocument,
    QualityCriterion,
    QualityScore,
)
from .factory import StrategyFactory

__all__ = [
    "DocumentationStrategy",
    "DocumentSpec",
    "DocumentSet",
    "GeneratedDocument",
    "QualityCriterion",
    "QualityScore",
    "StrategyFactory",
]
