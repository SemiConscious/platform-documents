"""Task queue with SQLite backend for tracking agent tasks."""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator

import aiosqlite

from .models import AgentTask, TaskStatus, TaskStats

logger = logging.getLogger("doc-spawner.task_queue")


class TaskQueue:
    """
    Persistent task queue using SQLite.
    
    Provides ACID guarantees for task state management and supports
    concurrent access from multiple executor workers.
    """
    
    def __init__(self, db_path: Path | str):
        """
        Initialize the task queue.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._db: aiosqlite.Connection | None = None
        self._lock = asyncio.Lock()
    
    async def connect(self) -> None:
        """Connect to the database and create tables if needed."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        
        # Enable WAL mode for better concurrency
        await self._db.execute("PRAGMA journal_mode=WAL")
        
        await self._create_tables()
        logger.info(f"Connected to task queue at {self.db_path}")
    
    async def disconnect(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()
            self._db = None
    
    async def _create_tables(self) -> None:
        """Create the task table if it doesn't exist."""
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                prompt TEXT NOT NULL,
                output_path TEXT NOT NULL,
                depth INTEGER NOT NULL,
                status TEXT NOT NULL,
                parent_task_id TEXT,
                context TEXT,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                error TEXT,
                metadata TEXT,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                FOREIGN KEY (parent_task_id) REFERENCES tasks(task_id)
            )
        """)
        
        # Indexes for common queries
        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)"
        )
        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_task_id)"
        )
        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_depth ON tasks(depth)"
        )
        
        await self._db.commit()
    
    async def add_task(self, task: AgentTask) -> None:
        """
        Add a new task to the queue.
        
        Args:
            task: The task to add
        """
        async with self._lock:
            await self._db.execute(
                """
                INSERT INTO tasks (
                    task_id, prompt, output_path, depth, status,
                    parent_task_id, context, created_at, started_at,
                    completed_at, error, metadata, input_tokens, output_tokens
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.task_id,
                    task.prompt,
                    task.output_path,
                    task.depth,
                    task.status.value,
                    task.parent_task_id,
                    task.context,
                    task.created_at.isoformat(),
                    task.started_at.isoformat() if task.started_at else None,
                    task.completed_at.isoformat() if task.completed_at else None,
                    task.error,
                    json.dumps(task.metadata),
                    task.input_tokens,
                    task.output_tokens,
                ),
            )
            await self._db.commit()
        
        logger.debug(f"Added task {task.task_id} (depth={task.depth})")
    
    async def get_task(self, task_id: str) -> AgentTask | None:
        """
        Get a task by ID.
        
        Args:
            task_id: The task ID to look up
            
        Returns:
            The task or None if not found
        """
        async with self._db.execute(
            "SELECT * FROM tasks WHERE task_id = ?",
            (task_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return self._row_to_task(row)
        return None
    
    async def update_task(self, task: AgentTask) -> None:
        """
        Update an existing task.
        
        Args:
            task: The task with updated fields
        """
        async with self._lock:
            await self._db.execute(
                """
                UPDATE tasks SET
                    status = ?,
                    started_at = ?,
                    completed_at = ?,
                    error = ?,
                    metadata = ?,
                    input_tokens = ?,
                    output_tokens = ?
                WHERE task_id = ?
                """,
                (
                    task.status.value,
                    task.started_at.isoformat() if task.started_at else None,
                    task.completed_at.isoformat() if task.completed_at else None,
                    task.error,
                    json.dumps(task.metadata),
                    task.input_tokens,
                    task.output_tokens,
                    task.task_id,
                ),
            )
            await self._db.commit()
    
    async def claim_pending_task(self) -> AgentTask | None:
        """
        Atomically claim a pending task for execution.
        
        Returns:
            A task that has been marked as running, or None if no pending tasks
        """
        async with self._lock:
            # Find oldest pending task
            async with self._db.execute(
                """
                SELECT * FROM tasks 
                WHERE status = ? 
                ORDER BY created_at ASC 
                LIMIT 1
                """,
                (TaskStatus.PENDING.value,),
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                
                task = self._row_to_task(row)
            
            # Mark it as running
            task.mark_running()
            await self._db.execute(
                """
                UPDATE tasks SET 
                    status = ?,
                    started_at = ?
                WHERE task_id = ? AND status = ?
                """,
                (
                    TaskStatus.RUNNING.value,
                    task.started_at.isoformat(),
                    task.task_id,
                    TaskStatus.PENDING.value,
                ),
            )
            await self._db.commit()
            
            logger.info(f"Claimed task {task.task_id} (depth={task.depth})")
            return task
    
    async def get_stats(self) -> TaskStats:
        """
        Get statistics about the task queue.
        
        Returns:
            TaskStats with counts by status and depth
        """
        stats = TaskStats()
        
        # Count by status
        async with self._db.execute(
            "SELECT status, COUNT(*) as count FROM tasks GROUP BY status"
        ) as cursor:
            async for row in cursor:
                status = row["status"]
                count = row["count"]
                stats.total += count
                if status == TaskStatus.PENDING.value:
                    stats.pending = count
                elif status == TaskStatus.RUNNING.value:
                    stats.running = count
                elif status == TaskStatus.COMPLETED.value:
                    stats.completed = count
                elif status == TaskStatus.FAILED.value:
                    stats.failed = count
                elif status == TaskStatus.CANCELLED.value:
                    stats.cancelled = count
        
        # Count by depth
        async with self._db.execute(
            "SELECT depth, COUNT(*) as count FROM tasks GROUP BY depth"
        ) as cursor:
            async for row in cursor:
                stats.by_depth[row["depth"]] = row["count"]
        
        # Sum tokens
        async with self._db.execute(
            "SELECT SUM(input_tokens) as input, SUM(output_tokens) as output FROM tasks"
        ) as cursor:
            row = await cursor.fetchone()
            stats.total_input_tokens = row["input"] or 0
            stats.total_output_tokens = row["output"] or 0
        
        return stats
    
    async def get_all_tasks(self, status: TaskStatus | None = None) -> list[AgentTask]:
        """
        Get all tasks, optionally filtered by status.
        
        Args:
            status: Optional status filter
            
        Returns:
            List of matching tasks
        """
        if status:
            query = "SELECT * FROM tasks WHERE status = ? ORDER BY created_at"
            params = (status.value,)
        else:
            query = "SELECT * FROM tasks ORDER BY created_at"
            params = ()
        
        tasks = []
        async with self._db.execute(query, params) as cursor:
            async for row in cursor:
                tasks.append(self._row_to_task(row))
        return tasks
    
    async def get_children(self, parent_task_id: str) -> list[AgentTask]:
        """
        Get all child tasks of a parent.
        
        Args:
            parent_task_id: The parent task ID
            
        Returns:
            List of child tasks
        """
        tasks = []
        async with self._db.execute(
            "SELECT * FROM tasks WHERE parent_task_id = ? ORDER BY created_at",
            (parent_task_id,),
        ) as cursor:
            async for row in cursor:
                tasks.append(self._row_to_task(row))
        return tasks
    
    async def cancel_all_pending(self) -> int:
        """
        Cancel all pending tasks.
        
        Returns:
            Number of tasks cancelled
        """
        async with self._lock:
            cursor = await self._db.execute(
                """
                UPDATE tasks 
                SET status = ?, completed_at = ?
                WHERE status = ?
                """,
                (
                    TaskStatus.CANCELLED.value,
                    datetime.utcnow().isoformat(),
                    TaskStatus.PENDING.value,
                ),
            )
            await self._db.commit()
            return cursor.rowcount
    
    async def reset_running_tasks(self) -> int:
        """
        Reset all running tasks back to pending (for recovery after crash).
        
        Returns:
            Number of tasks reset
        """
        async with self._lock:
            cursor = await self._db.execute(
                """
                UPDATE tasks 
                SET status = ?, started_at = NULL
                WHERE status = ?
                """,
                (TaskStatus.PENDING.value, TaskStatus.RUNNING.value),
            )
            await self._db.commit()
            count = cursor.rowcount
            if count > 0:
                logger.warning(f"Reset {count} running tasks to pending")
            return count
    
    async def clear_all(self) -> None:
        """Delete all tasks from the queue."""
        async with self._lock:
            await self._db.execute("DELETE FROM tasks")
            await self._db.commit()
        logger.warning("Cleared all tasks from queue")
    
    def _row_to_task(self, row: aiosqlite.Row) -> AgentTask:
        """Convert a database row to an AgentTask."""
        return AgentTask(
            task_id=row["task_id"],
            prompt=row["prompt"],
            output_path=row["output_path"],
            depth=row["depth"],
            status=TaskStatus(row["status"]),
            parent_task_id=row["parent_task_id"],
            context=row["context"],
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            error=row["error"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            input_tokens=row["input_tokens"] or 0,
            output_tokens=row["output_tokens"] or 0,
        )
    
    async def __aenter__(self) -> "TaskQueue":
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()
