"""
Strategy factory for documentation generation.

Selects the appropriate documentation strategy based on repository type.
"""

from pathlib import Path
from typing import Any, Optional, Type
import logging

from ...analyzers.repo_type_detector import RepoType, detect_repo_type
from .base import DocumentationStrategy

logger = logging.getLogger("doc-agent.documentation.factory")

# Registry of strategy classes
_strategy_registry: dict[RepoType, Type[DocumentationStrategy]] = {}


def register_strategy(repo_type: RepoType):
    """Decorator to register a strategy for a repository type."""
    def decorator(cls: Type[DocumentationStrategy]):
        _strategy_registry[repo_type] = cls
        cls.repo_type = repo_type
        return cls
    return decorator


class StrategyFactory:
    """
    Factory for creating documentation strategies.
    
    Selects the appropriate strategy based on repository type detection.
    """
    
    def __init__(
        self,
        output_dir: Path,
        llm_client: Any = None,
        token_tracker: Any = None,
        config: Optional[dict] = None,
        model_selector: Any = None,
    ):
        """
        Initialize the factory.
        
        Args:
            output_dir: Base directory for generated documentation
            llm_client: LLM client for AI-powered generation
            token_tracker: Token usage tracker
            config: Application configuration dict
            model_selector: Model selector for tiered model usage
        """
        self.output_dir = output_dir
        self.llm_client = llm_client
        self.token_tracker = token_tracker
        self.config = config or {}
        self.model_selector = model_selector
        
        # Ensure all strategies are imported
        self._import_strategies()
    
    def _import_strategies(self):
        """Import all strategy modules to register them."""
        try:
            from . import api_service
        except ImportError:
            pass
        try:
            from . import terraform
        except ImportError:
            pass
        try:
            from . import lambda_strategy
        except ImportError:
            pass
        try:
            from . import salesforce
        except ImportError:
            pass
        try:
            from . import library
        except ImportError:
            pass
        try:
            from . import telephony
        except ImportError:
            pass
        try:
            from . import frontend
        except ImportError:
            pass
    
    def get_strategy(self, repo_type: RepoType) -> Optional[DocumentationStrategy]:
        """
        Get a strategy for the given repository type.
        
        Args:
            repo_type: The type of repository
            
        Returns:
            DocumentationStrategy instance or None if not available
        """
        strategy_cls = _strategy_registry.get(repo_type)
        
        if strategy_cls:
            return strategy_cls(
                output_dir=self.output_dir,
                llm_client=self.llm_client,
                token_tracker=self.token_tracker,
                config=self.config,
                model_selector=self.model_selector,
            )
        
        # Fall back to generic strategy
        from .generic import GenericStrategy
        return GenericStrategy(
            output_dir=self.output_dir,
            llm_client=self.llm_client,
            token_tracker=self.token_tracker,
            config=self.config,
            model_selector=self.model_selector,
        )
    
    def get_strategy_for_repo(self, repo_path: Path) -> Optional[DocumentationStrategy]:
        """
        Detect repository type and get appropriate strategy.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            DocumentationStrategy instance
        """
        result = detect_repo_type(repo_path)
        logger.info(
            f"Detected repo type: {result.primary_type.value} "
            f"(confidence: {result.confidence:.2f})"
        )
        
        return self.get_strategy(result.primary_type)
    
    @classmethod
    def get_registered_strategies(cls) -> dict[RepoType, Type[DocumentationStrategy]]:
        """Get all registered strategies."""
        return _strategy_registry.copy()
    
    @classmethod
    def is_strategy_available(cls, repo_type: RepoType) -> bool:
        """Check if a strategy is available for the given type."""
        return repo_type in _strategy_registry
