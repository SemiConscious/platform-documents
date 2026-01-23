"""Model configurations for different LLM providers and models."""

from dataclasses import dataclass
from enum import Enum


class Provider(Enum):
    """LLM provider types."""
    BEDROCK = "bedrock"
    OPENROUTER = "openrouter"


@dataclass
class ModelConfig:
    """Configuration for a specific model.
    
    Note: OpenRouter provides automatic prompt caching which can reduce actual
    costs by 80-95% compared to estimates. The estimate_cost method provides
    a worst-case estimate; actual costs are typically much lower.
    
    Actual effective rates observed (Jan 2026):
    - DeepSeek: ~$0.35/MTok effective
    - Grok Code Fast: ~$0.72/MTok effective  
    - GPT-5.2 Codex: ~$4.56/MTok effective (93% cache hit)
    - Grok 4: ~$8.09/MTok effective
    """
    name: str
    provider: Provider
    model_id: str
    description: str
    context_window: int
    input_cost_per_mtok: float  # USD per million tokens (before caching)
    output_cost_per_mtok: float
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for given token counts.
        
        Note: This is a worst-case estimate. OpenRouter's automatic prompt
        caching typically reduces actual costs by 80-95%.
        """
        input_cost = (input_tokens / 1_000_000) * self.input_cost_per_mtok
        output_cost = (output_tokens / 1_000_000) * self.output_cost_per_mtok
        return input_cost + output_cost


# Available model configurations
MODEL_CONFIGS = {
    # === Bedrock Models ===
    "opus": ModelConfig(
        name="opus",
        provider=Provider.BEDROCK,
        model_id="us.anthropic.claude-opus-4-5-20251101-v1:0",
        description="Claude Opus 4.5 on Bedrock - highest quality, most expensive",
        context_window=200_000,
        input_cost_per_mtok=5.0,
        output_cost_per_mtok=25.0,
    ),
    "sonnet": ModelConfig(
        name="sonnet",
        provider=Provider.BEDROCK,
        model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
        description="Claude Sonnet 4 on Bedrock - excellent balance of quality and cost",
        context_window=200_000,
        input_cost_per_mtok=3.0,
        output_cost_per_mtok=15.0,
    ),
    "haiku": ModelConfig(
        name="haiku",
        provider=Provider.BEDROCK,
        model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        description="Claude Haiku 3.5 on Bedrock - fast and cheap",
        context_window=200_000,
        input_cost_per_mtok=1.0,
        output_cost_per_mtok=5.0,
    ),
    
    # === OpenRouter Models ===
    "gpt5": ModelConfig(
        name="gpt5",
        provider=Provider.OPENROUTER,
        model_id="openai/gpt-5.2-codex",
        description="GPT-5.2 Codex via OpenRouter - optimized for code (~$4.50/MTok effective)",
        context_window=400_000,
        input_cost_per_mtok=1.75,
        output_cost_per_mtok=14.0,
    ),
    "grok-code": ModelConfig(
        name="grok-code",
        provider=Provider.OPENROUTER,
        model_id="x-ai/grok-code-fast-1",
        description="Grok Code Fast 1 via OpenRouter - optimized for code, very cheap",
        context_window=256_000,
        input_cost_per_mtok=0.20,
        output_cost_per_mtok=1.50,
    ),
    "grok-fast": ModelConfig(
        name="grok-fast",
        provider=Provider.OPENROUTER,
        model_id="x-ai/grok-4-fast",
        description="Grok 4 Fast via OpenRouter - 2M context, very cheap",
        context_window=2_000_000,
        input_cost_per_mtok=0.20,
        output_cost_per_mtok=0.50,
    ),
    "grok4": ModelConfig(
        name="grok4",
        provider=Provider.OPENROUTER,
        model_id="x-ai/grok-4",
        description="Grok 4 via OpenRouter - full model, high quality (~$8/MTok effective)",
        context_window=256_000,
        input_cost_per_mtok=3.0,
        output_cost_per_mtok=15.0,
    ),
    "deepseek": ModelConfig(
        name="deepseek",
        provider=Provider.OPENROUTER,
        model_id="deepseek/deepseek-chat-v3-0324",
        description="DeepSeek V3 via OpenRouter - excellent quality (~$0.35/MTok effective)",
        context_window=163_000,
        input_cost_per_mtok=0.27,
        output_cost_per_mtok=1.10,
    ),
    "codestral": ModelConfig(
        name="codestral",
        provider=Provider.OPENROUTER,
        model_id="mistralai/codestral-2508",
        description="Codestral 2508 via OpenRouter - strong for code, 256K context",
        context_window=256_000,
        input_cost_per_mtok=0.30,
        output_cost_per_mtok=0.90,
    ),
    "qwen-coder": ModelConfig(
        name="qwen-coder",
        provider=Provider.OPENROUTER,
        model_id="qwen/qwen3-coder",
        description="Qwen3 Coder via OpenRouter - great for large codebases",
        context_window=262_000,
        input_cost_per_mtok=0.45,
        output_cost_per_mtok=1.80,
    ),
}


def get_model_config(name: str) -> ModelConfig:
    """Get model configuration by name."""
    if name not in MODEL_CONFIGS:
        available = ", ".join(MODEL_CONFIGS.keys())
        raise ValueError(f"Unknown model '{name}'. Available: {available}")
    return MODEL_CONFIGS[name]


def list_models() -> list[dict]:
    """List all available models with their details."""
    return [
        {
            "name": cfg.name,
            "provider": cfg.provider.value,
            "description": cfg.description,
            "context": f"{cfg.context_window:,}",
            "cost_in": f"${cfg.input_cost_per_mtok}/MTok",
            "cost_out": f"${cfg.output_cost_per_mtok}/MTok",
        }
        for cfg in MODEL_CONFIGS.values()
    ]
