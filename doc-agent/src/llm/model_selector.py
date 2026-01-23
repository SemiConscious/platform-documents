"""
Model selector for tiered LLM usage.

Allows different models to be used for different operations
to optimize cost vs quality tradeoffs.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import logging

logger = logging.getLogger("doc-agent.llm.model_selector")


class Operation(Enum):
    """Types of LLM operations."""
    ANALYSIS = "analysis"           # Code analysis and understanding
    TEMPLATES = "templates"         # Template/structure generation
    WRITING = "writing"             # Content writing (quality-critical)
    REVIEW = "review"               # Quality review and validation
    SUMMARY = "summary"             # Quick summaries
    EXTRACTION = "extraction"       # Data extraction from text


# Default model configurations for AWS Bedrock
# Note: US inference profiles required for on-demand throughput
BEDROCK_MODELS = {
    "opus-4.5": "us.anthropic.claude-opus-4-5-20251101-v1:0",
    "sonnet-3.5": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "haiku-3.5": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
}

# Direct Anthropic API models
ANTHROPIC_MODELS = {
    "opus-4.5": "claude-opus-4-5-20251101",
    "sonnet-4": "claude-sonnet-4-20250514",
    "sonnet-3.5": "claude-3-5-sonnet-20241022",
    "haiku-3.5": "claude-3-5-haiku-20241022",
}


@dataclass
class ModelProfile:
    """
    Configuration profile for model selection.
    
    Maps each operation type to a specific model.
    """
    name: str
    description: str
    models: dict[Operation, str] = field(default_factory=dict)
    
    # Cost tracking
    estimated_cost_per_repo: float = 0.0
    
    def get_model(self, operation: Operation) -> str:
        """Get the model ID for a specific operation."""
        return self.models.get(operation, self.models.get(Operation.WRITING, ""))
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "models": {op.value: model for op, model in self.models.items()},
            "estimated_cost_per_repo": self.estimated_cost_per_repo,
        }


# Predefined profiles
PROFILES = {
    "premium": ModelProfile(
        name="premium",
        description="Best quality - uses Opus 4.5 for all operations",
        models={
            Operation.ANALYSIS: BEDROCK_MODELS["opus-4.5"],
            Operation.TEMPLATES: BEDROCK_MODELS["opus-4.5"],
            Operation.WRITING: BEDROCK_MODELS["opus-4.5"],
            Operation.REVIEW: BEDROCK_MODELS["opus-4.5"],
            Operation.SUMMARY: BEDROCK_MODELS["opus-4.5"],
            Operation.EXTRACTION: BEDROCK_MODELS["opus-4.5"],
        },
        estimated_cost_per_repo=3.80,
    ),
    "tiered": ModelProfile(
        name="tiered",
        description="Cost-optimized - uses best model where it matters most",
        models={
            Operation.ANALYSIS: BEDROCK_MODELS["sonnet-3.5"],      # Good at understanding
            Operation.TEMPLATES: BEDROCK_MODELS["haiku-3.5"],      # Structured output
            Operation.WRITING: BEDROCK_MODELS["opus-4.5"],         # Quality critical
            Operation.REVIEW: BEDROCK_MODELS["sonnet-3.5"],        # Comparison tasks
            Operation.SUMMARY: BEDROCK_MODELS["haiku-3.5"],        # Quick summaries
            Operation.EXTRACTION: BEDROCK_MODELS["haiku-3.5"],     # Structured extraction
        },
        estimated_cost_per_repo=2.34,
    ),
    "economy": ModelProfile(
        name="economy",
        description="Lowest cost - for testing and iteration",
        models={
            Operation.ANALYSIS: BEDROCK_MODELS["haiku-3.5"],
            Operation.TEMPLATES: BEDROCK_MODELS["haiku-3.5"],
            Operation.WRITING: BEDROCK_MODELS["sonnet-3.5"],
            Operation.REVIEW: BEDROCK_MODELS["haiku-3.5"],
            Operation.SUMMARY: BEDROCK_MODELS["haiku-3.5"],
            Operation.EXTRACTION: BEDROCK_MODELS["haiku-3.5"],
        },
        estimated_cost_per_repo=0.46,
    ),
    "hybrid": ModelProfile(
        name="hybrid",
        description="Deep analysis with fast writing - Opus for discovery, Sonnet for generation",
        models={
            Operation.ANALYSIS: BEDROCK_MODELS["opus-4.5"],     # Deep code understanding
            Operation.EXTRACTION: BEDROCK_MODELS["opus-4.5"],  # Find all endpoints/models
            Operation.TEMPLATES: BEDROCK_MODELS["sonnet-3.5"], # Structure generation
            Operation.WRITING: BEDROCK_MODELS["sonnet-3.5"],   # Fast content writing
            Operation.REVIEW: BEDROCK_MODELS["sonnet-3.5"],    # Quality checks
            Operation.SUMMARY: BEDROCK_MODELS["haiku-3.5"],    # Quick summaries
        },
        estimated_cost_per_repo=2.00,
    ),
}


class ModelSelector:
    """
    Manages model selection based on operation type and profile.
    
    Allows switching between different cost/quality tradeoffs
    by selecting different profiles.
    """
    
    def __init__(
        self,
        config: dict[str, Any],
        profile_name: Optional[str] = None,
    ):
        """
        Initialize the model selector.
        
        Args:
            config: Application configuration dict
            profile_name: Override profile name (defaults to config value)
        """
        self.config = config
        llm_config = config.get("llm", {})
        
        # Determine which profile to use
        self.profile_name = profile_name or llm_config.get("active_profile", "tiered")
        
        # Load profile
        if self.profile_name in PROFILES:
            self.profile = PROFILES[self.profile_name]
        else:
            # Try to load custom profile from config
            profiles_config = llm_config.get("profiles", {})
            if self.profile_name in profiles_config:
                self.profile = self._load_profile_from_config(
                    self.profile_name, 
                    profiles_config[self.profile_name]
                )
            else:
                logger.warning(f"Unknown profile '{self.profile_name}', using 'tiered'")
                self.profile = PROFILES["tiered"]
        
        # Detect if using Bedrock or direct Anthropic
        provider = llm_config.get("provider", "anthropic")
        self.is_bedrock = provider == "bedrock"
        
        logger.info(
            f"Model selector initialized: profile={self.profile.name}, "
            f"provider={'bedrock' if self.is_bedrock else 'anthropic'}"
        )
    
    def _load_profile_from_config(
        self, 
        name: str, 
        profile_config: dict
    ) -> ModelProfile:
        """Load a custom profile from configuration."""
        models = {}
        for op in Operation:
            model_id = profile_config.get(op.value)
            if model_id:
                models[op] = model_id
        
        return ModelProfile(
            name=name,
            description=profile_config.get("description", f"Custom profile: {name}"),
            models=models,
            estimated_cost_per_repo=profile_config.get("estimated_cost", 0.0),
        )
    
    def get_model(self, operation: Operation) -> str:
        """
        Get the model ID for a specific operation.
        
        Args:
            operation: The type of operation to perform
            
        Returns:
            Model ID string suitable for the configured provider
        """
        model = self.profile.get_model(operation)
        
        if not model:
            # Fallback to writing model or config default
            model = self.profile.get_model(Operation.WRITING)
            if not model:
                model = self.config.get("llm", {}).get(
                    "model", 
                    BEDROCK_MODELS["sonnet-3.5"] if self.is_bedrock else ANTHROPIC_MODELS["sonnet-3.5"]
                )
        
        logger.debug(f"Selected model for {operation.value}: {model}")
        return model
    
    def get_profile_info(self) -> dict:
        """Get information about the current profile."""
        return {
            "name": self.profile.name,
            "description": self.profile.description,
            "estimated_cost_per_repo": self.profile.estimated_cost_per_repo,
            "models": {
                op.value: self.profile.get_model(op)
                for op in Operation
            },
            "provider": "bedrock" if self.is_bedrock else "anthropic",
        }
    
    @staticmethod
    def list_profiles() -> list[dict]:
        """List all available profiles."""
        return [
            {
                "name": profile.name,
                "description": profile.description,
                "estimated_cost_per_repo": profile.estimated_cost_per_repo,
            }
            for profile in PROFILES.values()
        ]
