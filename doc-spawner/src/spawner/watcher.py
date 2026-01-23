"""Completion watcher and index builder trigger."""

import asyncio
import logging
from datetime import datetime
from typing import Callable, Awaitable

from .models import TaskStats
from .task_queue import TaskQueue

logger = logging.getLogger("doc-spawner.watcher")


class CompletionWatcher:
    """
    Monitors the task queue and triggers actions on completion.
    
    The watcher polls the task queue periodically and:
    1. Reports progress statistics
    2. Detects when all tasks are complete
    3. Triggers the index builder agent
    """
    
    def __init__(
        self,
        task_queue: TaskQueue,
        poll_interval: int = 10,
        on_complete: Callable[[], Awaitable[None]] | None = None,
    ):
        """
        Initialize the watcher.
        
        Args:
            task_queue: The task queue to monitor
            poll_interval: Seconds between status checks
            on_complete: Async callback when all tasks complete
        """
        self.task_queue = task_queue
        self.poll_interval = poll_interval
        self.on_complete = on_complete
        
        self._running = False
        self._last_stats: TaskStats | None = None
    
    async def watch(self) -> TaskStats:
        """
        Watch the task queue until all tasks complete.
        
        Returns:
            Final task statistics
        """
        self._running = True
        start_time = datetime.utcnow()
        
        logger.info("Watcher started, monitoring task queue...")
        
        while self._running:
            stats = await self.task_queue.get_stats()
            
            # Log progress if changed
            if self._stats_changed(stats):
                self._log_progress(stats, start_time)
                self._last_stats = stats
            
            # Check for completion
            if stats.is_complete and stats.total > 0:
                logger.info("All tasks completed!")
                self._log_final_report(stats, start_time)
                
                # Trigger callback
                if self.on_complete:
                    await self.on_complete()
                
                return stats
            
            await asyncio.sleep(self.poll_interval)
        
        # Watcher was stopped externally
        return await self.task_queue.get_stats()
    
    def stop(self) -> None:
        """Stop the watcher."""
        self._running = False
    
    def _stats_changed(self, stats: TaskStats) -> bool:
        """Check if stats have changed since last check."""
        if self._last_stats is None:
            return True
        
        return (
            stats.pending != self._last_stats.pending
            or stats.running != self._last_stats.running
            or stats.completed != self._last_stats.completed
            or stats.failed != self._last_stats.failed
        )
    
    def _log_progress(self, stats: TaskStats, start_time: datetime) -> None:
        """Log current progress."""
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        
        # Build depth breakdown
        depth_info = ", ".join(
            f"d{d}={c}" for d, c in sorted(stats.by_depth.items())
        )
        
        logger.info(
            f"Progress: {stats.completed}/{stats.total} completed, "
            f"{stats.running} running, {stats.pending} pending, "
            f"{stats.failed} failed | "
            f"Depth: [{depth_info}] | "
            f"Tokens: {stats.total_input_tokens:,}+{stats.total_output_tokens:,} | "
            f"Est. cost: ${stats.estimated_cost_usd:.2f} | "
            f"Elapsed: {elapsed:.0f}s"
        )
    
    def _log_final_report(self, stats: TaskStats, start_time: datetime) -> None:
        """Log final completion report."""
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info("=" * 60)
        logger.info("DOCUMENTATION GENERATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total tasks:     {stats.total}")
        logger.info(f"Completed:       {stats.completed}")
        logger.info(f"Failed:          {stats.failed}")
        logger.info(f"Success rate:    {stats.success_rate * 100:.1f}%")
        logger.info("-" * 60)
        logger.info(f"Input tokens:    {stats.total_input_tokens:,}")
        logger.info(f"Output tokens:   {stats.total_output_tokens:,}")
        logger.info(f"Estimated cost:  ${stats.estimated_cost_usd:.2f}")
        logger.info("-" * 60)
        logger.info(f"Total time:      {elapsed:.0f}s ({elapsed/60:.1f}m)")
        logger.info("=" * 60)


class ProgressReporter:
    """Utility for formatted progress reporting."""
    
    def __init__(self, task_queue: TaskQueue):
        self.task_queue = task_queue
    
    async def get_report(self) -> str:
        """Get a formatted status report."""
        stats = await self.task_queue.get_stats()
        
        lines = [
            "Task Queue Status",
            "=" * 40,
            f"Total:     {stats.total}",
            f"Pending:   {stats.pending}",
            f"Running:   {stats.running}",
            f"Completed: {stats.completed}",
            f"Failed:    {stats.failed}",
            f"Cancelled: {stats.cancelled}",
            "-" * 40,
        ]
        
        if stats.by_depth:
            lines.append("By Depth:")
            for depth, count in sorted(stats.by_depth.items()):
                lines.append(f"  Depth {depth}: {count}")
            lines.append("-" * 40)
        
        lines.extend([
            f"Input tokens:  {stats.total_input_tokens:,}",
            f"Output tokens: {stats.total_output_tokens:,}",
            f"Est. cost:     ${stats.estimated_cost_usd:.2f}",
            "=" * 40,
        ])
        
        return "\n".join(lines)
    
    async def get_failed_tasks(self) -> str:
        """Get a report of failed tasks."""
        from .models import TaskStatus
        
        failed = await self.task_queue.get_all_tasks(TaskStatus.FAILED)
        
        if not failed:
            return "No failed tasks."
        
        lines = [
            f"Failed Tasks ({len(failed)})",
            "=" * 40,
        ]
        
        for task in failed:
            lines.extend([
                f"Task: {task.task_id[:8]}",
                f"  Depth: {task.depth}",
                f"  Output: {task.output_path}",
                f"  Error: {task.error}",
                "-" * 40,
            ])
        
        return "\n".join(lines)
