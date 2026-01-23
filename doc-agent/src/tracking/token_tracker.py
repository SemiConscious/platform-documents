"""
Token usage tracking for AI operations.

Tracks all LLM token usage and calculates costs for monitoring
and budgeting purposes.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional
import json
import logging
import threading
from pathlib import Path

logger = logging.getLogger("doc-agent.tracking.tokens")


# Pricing per model (USD per million tokens)
# Updated January 2025
MODEL_PRICING = {
    # Claude 4 models (Opus 4, Sonnet 4)
    "claude-opus-4-20250514": {
        "input": 15.0,
        "output": 75.0,
    },
    "claude-sonnet-4-20250514": {
        "input": 3.0,
        "output": 15.0,
    },
    # Claude 3.5 models
    "claude-3-5-sonnet-20241022": {
        "input": 3.0,
        "output": 15.0,
    },
    "claude-3-5-haiku-20241022": {
        "input": 1.0,
        "output": 5.0,
    },
    # Claude 3 models
    "claude-3-opus-20240229": {
        "input": 15.0,
        "output": 75.0,
    },
    "claude-3-sonnet-20240229": {
        "input": 3.0,
        "output": 15.0,
    },
    "claude-3-haiku-20240307": {
        "input": 0.25,
        "output": 1.25,
    },
    # AWS Bedrock Claude models
    "anthropic.claude-3-sonnet-20240229-v1:0": {
        "input": 3.0,
        "output": 15.0,
    },
    "anthropic.claude-3-haiku-20240307-v1:0": {
        "input": 0.25,
        "output": 1.25,
    },
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {
        "input": 3.0,
        "output": 15.0,
    },
    # Default for unknown models
    "default": {
        "input": 3.0,
        "output": 15.0,
    },
}


@dataclass
class TokenUsage:
    """Record of a single API call's token usage."""
    input_tokens: int
    output_tokens: int
    model: str
    operation: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    service_name: Optional[str] = None
    document: Optional[str] = None
    duration_ms: Optional[int] = None
    
    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.input_tokens + self.output_tokens
    
    @property
    def cost(self) -> float:
        """Calculate cost in USD."""
        pricing = self._get_pricing()
        input_cost = (self.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost
    
    def _get_pricing(self) -> dict:
        """Get pricing for this model."""
        # Try exact match
        if self.model in MODEL_PRICING:
            return MODEL_PRICING[self.model]
        
        # Try partial match
        model_lower = self.model.lower()
        for key, pricing in MODEL_PRICING.items():
            if key.lower() in model_lower or model_lower in key.lower():
                return pricing
        
        # Fall back to default
        return MODEL_PRICING["default"]
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "model": self.model,
            "operation": self.operation,
            "timestamp": self.timestamp.isoformat(),
            "cost_usd": round(self.cost, 6),
            "service_name": self.service_name,
            "document": self.document,
            "duration_ms": self.duration_ms,
        }


@dataclass
class UsageReport:
    """Aggregated usage report."""
    session_start: datetime
    session_end: datetime
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    api_calls: int
    by_operation: dict[str, dict]
    by_model: dict[str, dict]
    by_service: dict[str, dict]
    usages: list[TokenUsage]
    
    @property
    def session_duration(self) -> timedelta:
        """Duration of the session."""
        return self.session_end - self.session_start
    
    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.total_input_tokens + self.total_output_tokens
    
    @property
    def avg_tokens_per_call(self) -> float:
        """Average tokens per API call."""
        return self.total_tokens / self.api_calls if self.api_calls > 0 else 0
    
    @property
    def avg_cost_per_call(self) -> float:
        """Average cost per API call."""
        return self.total_cost_usd / self.api_calls if self.api_calls > 0 else 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "session_duration": str(self.session_duration),
            "session_start": self.session_start.isoformat(),
            "session_end": self.session_end.isoformat(),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "api_calls": self.api_calls,
            "avg_tokens_per_call": round(self.avg_tokens_per_call, 1),
            "avg_cost_per_call": round(self.avg_cost_per_call, 6),
            "by_operation": self.by_operation,
            "by_model": self.by_model,
            "by_service": self.by_service,
        }


class TokenTracker:
    """
    Track all LLM token usage and costs.
    
    Thread-safe implementation for use in async contexts.
    """
    
    def __init__(self, persist_path: Optional[Path] = None):
        """
        Initialize the tracker.
        
        Args:
            persist_path: Optional path to persist usage data
        """
        self._usages: list[TokenUsage] = []
        self._session_start = datetime.utcnow()
        self._lock = threading.Lock()
        self._persist_path = persist_path
        
        # Load previous data if persisting
        if persist_path and persist_path.exists():
            self._load_persisted_data()
    
    def record(
        self,
        response: Any,
        operation: str,
        service_name: Optional[str] = None,
        document: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> TokenUsage:
        """
        Record usage from an API response.
        
        Args:
            response: The API response object (must have 'usage' attribute)
            operation: Name of the operation (e.g., "generate_readme", "analyze_code")
            service_name: Optional service/repo being documented
            document: Optional document being generated
            duration_ms: Optional request duration in milliseconds
            
        Returns:
            TokenUsage record
        """
        # Extract usage from response
        usage_data = getattr(response, "usage", None)
        if not usage_data:
            logger.warning(f"No usage data in response for operation: {operation}")
            return None
        
        input_tokens = getattr(usage_data, "input_tokens", 0)
        output_tokens = getattr(usage_data, "output_tokens", 0)
        model = getattr(response, "model", "unknown")
        
        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
            operation=operation,
            service_name=service_name,
            document=document,
            duration_ms=duration_ms,
        )
        
        with self._lock:
            self._usages.append(usage)
        
        logger.debug(
            f"Recorded {usage.total_tokens} tokens for {operation} "
            f"(${usage.cost:.6f})"
        )
        
        # Persist if configured
        if self._persist_path:
            self._persist_usage(usage)
        
        return usage
    
    def record_manual(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str,
        operation: str,
        service_name: Optional[str] = None,
        document: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> TokenUsage:
        """
        Manually record token usage.
        
        Useful when you have token counts but not an API response object.
        """
        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
            operation=operation,
            service_name=service_name,
            document=document,
            duration_ms=duration_ms,
        )
        
        with self._lock:
            self._usages.append(usage)
        
        if self._persist_path:
            self._persist_usage(usage)
        
        return usage
    
    def get_report(self) -> UsageReport:
        """Generate a comprehensive usage report."""
        with self._lock:
            usages = self._usages.copy()
        
        if not usages:
            return UsageReport(
                session_start=self._session_start,
                session_end=datetime.utcnow(),
                total_input_tokens=0,
                total_output_tokens=0,
                total_cost_usd=0.0,
                api_calls=0,
                by_operation={},
                by_model={},
                by_service={},
                usages=[],
            )
        
        # Aggregate by operation
        by_operation = {}
        for u in usages:
            if u.operation not in by_operation:
                by_operation[u.operation] = {
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost_usd": 0.0,
                }
            by_operation[u.operation]["calls"] += 1
            by_operation[u.operation]["input_tokens"] += u.input_tokens
            by_operation[u.operation]["output_tokens"] += u.output_tokens
            by_operation[u.operation]["cost_usd"] += u.cost
        
        # Round costs
        for op in by_operation.values():
            op["cost_usd"] = round(op["cost_usd"], 4)
        
        # Aggregate by model
        by_model = {}
        for u in usages:
            if u.model not in by_model:
                by_model[u.model] = {
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost_usd": 0.0,
                }
            by_model[u.model]["calls"] += 1
            by_model[u.model]["input_tokens"] += u.input_tokens
            by_model[u.model]["output_tokens"] += u.output_tokens
            by_model[u.model]["cost_usd"] += u.cost
        
        for model in by_model.values():
            model["cost_usd"] = round(model["cost_usd"], 4)
        
        # Aggregate by service
        by_service = {}
        for u in usages:
            service = u.service_name or "unknown"
            if service not in by_service:
                by_service[service] = {
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost_usd": 0.0,
                }
            by_service[service]["calls"] += 1
            by_service[service]["input_tokens"] += u.input_tokens
            by_service[service]["output_tokens"] += u.output_tokens
            by_service[service]["cost_usd"] += u.cost
        
        for svc in by_service.values():
            svc["cost_usd"] = round(svc["cost_usd"], 4)
        
        return UsageReport(
            session_start=self._session_start,
            session_end=datetime.utcnow(),
            total_input_tokens=sum(u.input_tokens for u in usages),
            total_output_tokens=sum(u.output_tokens for u in usages),
            total_cost_usd=sum(u.cost for u in usages),
            api_calls=len(usages),
            by_operation=by_operation,
            by_model=by_model,
            by_service=by_service,
            usages=usages,
        )
    
    def get_current_cost(self) -> float:
        """Get current total cost."""
        with self._lock:
            return sum(u.cost for u in self._usages)
    
    def get_current_tokens(self) -> tuple[int, int]:
        """Get current token counts (input, output)."""
        with self._lock:
            input_tokens = sum(u.input_tokens for u in self._usages)
            output_tokens = sum(u.output_tokens for u in self._usages)
        return input_tokens, output_tokens
    
    def reset(self) -> None:
        """Reset the tracker."""
        with self._lock:
            self._usages.clear()
            self._session_start = datetime.utcnow()
    
    def print_summary(self) -> str:
        """Print a formatted summary of usage."""
        report = self.get_report()
        
        duration_str = str(report.session_duration).split(".")[0]  # Remove microseconds
        
        output = f"""
╔══════════════════════════════════════════════════════════════╗
║                    AI Token Usage Report                      ║
╠══════════════════════════════════════════════════════════════╣
║  Duration:        {duration_str:<42} ║
║  API Calls:       {report.api_calls:<42} ║
║  Input Tokens:    {report.total_input_tokens:>15,}                        ║
║  Output Tokens:   {report.total_output_tokens:>15,}                        ║
║  Total Tokens:    {report.total_tokens:>15,}                        ║
║  Estimated Cost:  ${report.total_cost_usd:<38.4f} ║
╠══════════════════════════════════════════════════════════════╣
║                     Usage by Operation                        ║
"""
        
        for op, data in sorted(report.by_operation.items(), key=lambda x: x[1]["cost_usd"], reverse=True)[:8]:
            op_name = op[:25] if len(op) > 25 else op
            tokens = data["input_tokens"] + data["output_tokens"]
            cost = data["cost_usd"]
            output += f"║  {op_name:<25} {tokens:>10,} tokens  ${cost:>8.4f} ║\n"
        
        if len(report.by_operation) > 8:
            output += f"║  ... and {len(report.by_operation) - 8} more operations{' ':24} ║\n"
        
        if report.by_service and len(report.by_service) > 1:
            output += """╠══════════════════════════════════════════════════════════════╣
║                     Usage by Service                          ║
"""
            for svc, data in sorted(report.by_service.items(), key=lambda x: x[1]["cost_usd"], reverse=True)[:5]:
                svc_name = svc[:25] if len(svc) > 25 else svc
                tokens = data["input_tokens"] + data["output_tokens"]
                cost = data["cost_usd"]
                output += f"║  {svc_name:<25} {tokens:>10,} tokens  ${cost:>8.4f} ║\n"
        
        output += "╚══════════════════════════════════════════════════════════════╝"
        
        print(output)
        return output
    
    def _persist_usage(self, usage: TokenUsage) -> None:
        """Persist a usage record to file."""
        if not self._persist_path:
            return
        
        try:
            # Append to JSONL file
            with open(self._persist_path, "a") as f:
                f.write(json.dumps(usage.to_dict()) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist usage: {e}")
    
    def _load_persisted_data(self) -> None:
        """Load previously persisted data."""
        if not self._persist_path or not self._persist_path.exists():
            return
        
        try:
            with open(self._persist_path, "r") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        usage = TokenUsage(
                            input_tokens=data["input_tokens"],
                            output_tokens=data["output_tokens"],
                            model=data["model"],
                            operation=data["operation"],
                            timestamp=datetime.fromisoformat(data["timestamp"]),
                            service_name=data.get("service_name"),
                            document=data.get("document"),
                            duration_ms=data.get("duration_ms"),
                        )
                        self._usages.append(usage)
            
            logger.info(f"Loaded {len(self._usages)} usage records from {self._persist_path}")
        except Exception as e:
            logger.warning(f"Failed to load persisted data: {e}")
    
    def export_to_json(self, path: Path) -> None:
        """Export all usage data to a JSON file."""
        report = self.get_report()
        
        with open(path, "w") as f:
            json.dump({
                "report": report.to_dict(),
                "usages": [u.to_dict() for u in report.usages],
            }, f, indent=2)
        
        logger.info(f"Exported usage data to {path}")


# Global singleton tracker
_global_tracker: Optional[TokenTracker] = None
_tracker_lock = threading.Lock()


def get_global_tracker() -> TokenTracker:
    """Get the global token tracker instance."""
    global _global_tracker
    
    with _tracker_lock:
        if _global_tracker is None:
            _global_tracker = TokenTracker()
        return _global_tracker


def reset_global_tracker() -> None:
    """Reset the global token tracker."""
    global _global_tracker
    
    with _tracker_lock:
        if _global_tracker:
            _global_tracker.reset()
