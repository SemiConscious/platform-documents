"""Data models for the spawner system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import uuid


class TaskStatus(str, Enum):
    """Status of an agent task."""
    PENDING = "pending"      # Task created, waiting to be picked up
    RUNNING = "running"      # Agent is currently executing
    COMPLETED = "completed"  # Agent finished successfully
    FAILED = "failed"        # Agent encountered an error
    CANCELLED = "cancelled"  # Task was manually cancelled


@dataclass
class AgentTask:
    """
    Represents a single agent task in the system.
    
    Each task corresponds to one agent execution. Tasks form a tree structure
    where each task (except the root) has a parent task that spawned it.
    """
    task_id: str
    prompt: str                          # The agent's mission/instructions
    output_path: str                     # Where to write documentation
    depth: int                           # Depth in the spawn tree (0 = master)
    status: TaskStatus = TaskStatus.PENDING
    parent_task_id: str | None = None    # None for the master agent
    context: str | None = None           # Additional context passed by parent
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Token usage tracking
    input_tokens: int = 0
    output_tokens: int = 0
    
    @classmethod
    def create(
        cls,
        prompt: str,
        output_path: str,
        depth: int = 0,
        parent_task_id: str | None = None,
        context: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "AgentTask":
        """Create a new task with a generated UUID."""
        return cls(
            task_id=str(uuid.uuid4()),
            prompt=prompt,
            output_path=output_path,
            depth=depth,
            parent_task_id=parent_task_id,
            context=context,
            metadata=metadata or {},
        )
    
    def mark_running(self) -> None:
        """Mark the task as running."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def mark_completed(self, input_tokens: int = 0, output_tokens: int = 0) -> None:
        """Mark the task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
    
    def mark_failed(self, error: str) -> None:
        """Mark the task as failed with an error message."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error = error
    
    def mark_cancelled(self) -> None:
        """Mark the task as cancelled."""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.utcnow()
    
    @property
    def duration_seconds(self) -> float | None:
        """Get the duration of the task in seconds."""
        if self.started_at is None:
            return None
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()
    
    @property
    def is_terminal(self) -> bool:
        """Check if the task is in a terminal state."""
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "prompt": self.prompt,
            "output_path": self.output_path,
            "depth": self.depth,
            "status": self.status.value,
            "parent_task_id": self.parent_task_id,
            "context": self.context,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "metadata": self.metadata,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentTask":
        """Create from dictionary."""
        return cls(
            task_id=data["task_id"],
            prompt=data["prompt"],
            output_path=data["output_path"],
            depth=data["depth"],
            status=TaskStatus(data["status"]),
            parent_task_id=data.get("parent_task_id"),
            context=data.get("context"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error=data.get("error"),
            metadata=data.get("metadata", {}),
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
        )


@dataclass
class TaskStats:
    """Statistics about the task queue."""
    total: int = 0
    pending: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0
    
    # Token totals
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    
    # Depth distribution
    by_depth: dict[int, int] = field(default_factory=dict)
    
    @property
    def is_complete(self) -> bool:
        """Check if all tasks are in terminal states."""
        return self.pending == 0 and self.running == 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of completed tasks."""
        finished = self.completed + self.failed
        if finished == 0:
            return 0.0
        return self.completed / finished
    
    @property
    def estimated_cost_usd(self) -> float:
        """Estimate cost based on Opus 4.5 Bedrock pricing."""
        # Opus 4.5: $15/M input, $75/M output
        input_cost = (self.total_input_tokens / 1_000_000) * 15
        output_cost = (self.total_output_tokens / 1_000_000) * 75
        return input_cost + output_cost
