"""Structured logging configuration for the documentation agent."""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


console = Console()


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
) -> logging.Logger:
    """
    Configure structured logging with rich console output.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        log_format: Optional custom log format
        
    Returns:
        Configured root logger
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create handlers
    handlers: list[logging.Handler] = [
        RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
        )
    ]
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(
            logging.Formatter(
                log_format or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True,
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    
    return logging.getLogger("doc-agent")


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module."""
    return logging.getLogger(f"doc-agent.{name}")


class ProgressLogger:
    """Context manager for logging progress of long-running operations."""
    
    def __init__(self, logger: logging.Logger, operation: str, total: Optional[int] = None):
        self.logger = logger
        self.operation = operation
        self.total = total
        self.current = 0
        
    def __enter__(self):
        self.logger.info(f"Starting: {self.operation}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.logger.info(f"Completed: {self.operation}")
        else:
            self.logger.error(f"Failed: {self.operation} - {exc_val}")
        return False
        
    def update(self, message: str, increment: int = 1):
        """Update progress with a message."""
        self.current += increment
        if self.total:
            self.logger.info(f"[{self.current}/{self.total}] {message}")
        else:
            self.logger.info(message)
