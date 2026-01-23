"""
Recursive self-spawning documentation agent system.

This module implements a hierarchical agent architecture where a master agent
can spawn child agents, each of which can spawn their own children up to a
configurable depth (default 5). Agents operate independently (fire-and-forget) 
and write documentation directly to assigned paths.

Architecture:
    Master Agent (depth=0)
    ├── Child Agent (depth=1) - e.g., "Document all services"
    │   ├── Grandchild (depth=2) - e.g., "Document platform-api"
    │   └── Grandchild (depth=2) - e.g., "Document auth-service"
    └── Child Agent (depth=1) - e.g., "Document all infrastructure"
        └── ...

Key components:
    - TaskQueue: Tracks all spawned agent tasks with SQLite backend
    - AgentExecutor: Runs agent conversations with tool use
    - spawn_agent tool: Allows agents to create child agents
    - CompletionWatcher: Monitors task queue and triggers index builder

Usage:
    # Start the master agent
    doc-spawner start --config config.yaml --output ./docs
    
    # Check status
    doc-spawner status
    
    # Cancel all running tasks
    doc-spawner cancel
"""

from .models import AgentTask, TaskStatus, TaskStats
from .task_queue import TaskQueue
from .executor import AgentExecutor
from .watcher import CompletionWatcher, ProgressReporter
from .tools import ToolRegistry, SpawnAgentTool, FileReadTool, FileWriteTool, BashTool

__all__ = [
    "AgentTask",
    "TaskStatus",
    "TaskStats",
    "TaskQueue",
    "AgentExecutor",
    "CompletionWatcher",
    "ProgressReporter",
    "ToolRegistry",
    "SpawnAgentTool",
    "FileReadTool",
    "FileWriteTool",
    "BashTool",
]

__version__ = "0.1.0"
