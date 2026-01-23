"""CLI entry point for doc-spawner."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import click
import yaml
from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from .models import AgentTask, TaskStatus
from .task_queue import TaskQueue
from .executor import AgentExecutor
from .watcher import CompletionWatcher, ProgressReporter
from .prompts import get_index_builder_prompt

# Load environment variables from .env file
# Looks in current directory and parent directories
load_dotenv()

console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Configure logging with rich handler."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                rich_tracebacks=True,
                show_path=False,
            )
        ],
    )


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file."""
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


@click.group()
@click.option("--config", "-c", type=click.Path(exists=False), default="config.yaml",
              help="Path to configuration file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx: click.Context, config: str, verbose: bool) -> None:
    """Doc-Spawner: Recursive AI documentation agent system."""
    setup_logging(verbose)
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = Path(config)
    ctx.obj["verbose"] = verbose


@cli.command()
@click.option("--output", "-o", type=click.Path(), default="./docs",
              help="Output directory for documentation")
@click.option("--repos", "-r", type=click.Path(exists=True), required=True,
              help="Directory containing repository clones")
@click.option("--workers", "-w", type=int, default=3,
              help="Number of concurrent worker agents")
@click.option("--max-depth", "-d", type=int, default=5,
              help="Maximum spawn depth (default: 5)")
@click.option("--max-tasks", "-t", type=int, default=25,
              help="Maximum total tasks/agents to spawn (default: 25)")
@click.option("--max-turns", type=int, default=0,
              help="Maximum turns per task (0=unlimited, default: 0)")
@click.option("--model", "-m", type=str, default="opus",
              help="Model to use: opus, sonnet, haiku, gpt5, grok-code, grok-fast, deepseek, codestral, qwen-coder")
@click.option("--resume", is_flag=True,
              help="Resume from existing task queue (don't reset)")
@click.pass_context
def start(
    ctx: click.Context,
    output: str,
    repos: str,
    workers: int,
    max_depth: int,
    max_tasks: int,
    max_turns: int,
    model: str,
    resume: bool,
) -> None:
    """Start the documentation generation process."""
    from .models_config import get_model_config
    
    config_path = ctx.obj["config_path"]
    config = load_config(config_path)
    
    # Validate model
    try:
        model_config = get_model_config(model)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)
    
    # Override config with CLI options
    config["output_dir"] = output
    config["repos_dir"] = repos
    config["max_depth"] = max_depth
    config["max_tasks"] = max_tasks
    config["max_turns"] = max_turns if max_turns > 0 else 10000  # 0 = effectively unlimited
    config["num_workers"] = workers
    config["model"] = model
    
    console.print(f"[bold green]Doc-Spawner Starting[/bold green]")
    console.print(f"  Output:    {output}")
    console.print(f"  Repos:     {repos}")
    console.print(f"  Workers:   {workers}")
    console.print(f"  Max Depth: {max_depth}")
    console.print(f"  Max Tasks: {max_tasks}")
    console.print(f"  Max Turns: {'unlimited' if max_turns == 0 else max_turns}")
    console.print(f"  Model:     [cyan]{model_config.name}[/cyan] ({model_config.provider.value})")
    console.print(f"             {model_config.description}")
    console.print(f"             Cost: ${model_config.input_cost_per_mtok}/MTok in, ${model_config.output_cost_per_mtok}/MTok out")
    console.print()
    
    asyncio.run(_run_generation(config, resume))


@cli.command()
def models() -> None:
    """List available models and their pricing."""
    from rich.table import Table
    from .models_config import list_models
    
    table = Table(title="Available Models")
    table.add_column("Name", style="cyan")
    table.add_column("Provider", style="green")
    table.add_column("Context", justify="right")
    table.add_column("Input Cost", justify="right")
    table.add_column("Output Cost", justify="right")
    table.add_column("Description")
    
    for m in list_models():
        table.add_row(
            m["name"],
            m["provider"],
            m["context"],
            m["cost_in"],
            m["cost_out"],
            m["description"][:50] + "..." if len(m["description"]) > 50 else m["description"],
        )
    
    console.print(table)
    console.print()
    console.print("[dim]Use --model <name> with the start command to select a model.[/dim]")
    console.print("[dim]For OpenRouter models, set OPENROUTER_API_KEY env var.[/dim]")


async def _run_generation(config: dict, resume: bool) -> None:
    """Run the documentation generation process."""
    output_dir = Path(config["output_dir"]).resolve()
    repos_dir = Path(config["repos_dir"]).resolve()
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Task queue database
    db_path = output_dir / ".spawner" / "tasks.db"
    
    async with TaskQueue(db_path) as queue:
        # Handle resume vs fresh start
        if not resume:
            await queue.clear_all()
            console.print("[yellow]Starting fresh (use --resume to continue)[/yellow]")
        else:
            # Reset any stuck running tasks
            reset_count = await queue.reset_running_tasks()
            if reset_count > 0:
                console.print(f"[yellow]Reset {reset_count} stuck tasks to pending[/yellow]")
        
        # Check if we need to create master task
        stats = await queue.get_stats()
        if stats.total == 0:
            # Create master task
            master_task = AgentTask.create(
                prompt="Document the entire Natterbox platform",
                output_path="docs",
                depth=0,
            )
            await queue.add_task(master_task)
            console.print(f"[green]Created master task: {master_task.task_id[:8]}[/green]")
        else:
            console.print(f"[cyan]Resuming with {stats.pending} pending, {stats.running} running tasks[/cyan]")
        
        # Create executor
        executor = AgentExecutor(queue, config)
        
        # Create watcher with index builder callback
        async def on_complete():
            await _run_index_builder(queue, config)
        
        watcher = CompletionWatcher(
            queue,
            poll_interval=10,
            on_complete=on_complete,
        )
        
        # Run workers and watcher concurrently
        num_workers = config.get("num_workers", 3)
        
        await asyncio.gather(
            executor.run_workers(num_workers),
            watcher.watch(),
        )


async def _run_index_builder(queue: TaskQueue, config: dict) -> None:
    """Run the index builder agent after all other tasks complete."""
    console.print("[bold blue]Running index builder...[/bold blue]")
    
    output_dir = Path(config["output_dir"]).resolve()
    
    # Create index builder task
    index_task = AgentTask.create(
        prompt=get_index_builder_prompt(str(output_dir)),
        output_path="docs",
        depth=0,
        metadata={"type": "index_builder"},
    )
    await queue.add_task(index_task)
    
    # Execute it directly (don't spawn workers again)
    executor = AgentExecutor(queue, config)
    await executor.execute_task(index_task)
    
    console.print("[bold green]Index builder complete![/bold green]")


@cli.command()
@click.option("--output", "-o", type=click.Path(), default="./docs",
              help="Output directory (where task database is)")
@click.pass_context
def status(ctx: click.Context, output: str) -> None:
    """Show current task queue status."""
    asyncio.run(_show_status(output))


async def _show_status(output: str) -> None:
    """Show status of the task queue."""
    db_path = Path(output) / ".spawner" / "tasks.db"
    
    if not db_path.exists():
        console.print("[red]No task database found. Run 'start' first.[/red]")
        return
    
    async with TaskQueue(db_path) as queue:
        reporter = ProgressReporter(queue)
        report = await reporter.get_report()
        console.print(report)


@cli.command()
@click.option("--output", "-o", type=click.Path(), default="./docs",
              help="Output directory (where task database is)")
@click.pass_context
def failures(ctx: click.Context, output: str) -> None:
    """Show failed tasks with error details."""
    asyncio.run(_show_failures(output))


async def _show_failures(output: str) -> None:
    """Show failed tasks."""
    db_path = Path(output) / ".spawner" / "tasks.db"
    
    if not db_path.exists():
        console.print("[red]No task database found.[/red]")
        return
    
    async with TaskQueue(db_path) as queue:
        reporter = ProgressReporter(queue)
        report = await reporter.get_failed_tasks()
        console.print(report)


@cli.command()
@click.option("--output", "-o", type=click.Path(), default="./docs",
              help="Output directory (where task database is)")
@click.confirmation_option(prompt="Cancel all pending tasks?")
@click.pass_context
def cancel(ctx: click.Context, output: str) -> None:
    """Cancel all pending tasks."""
    asyncio.run(_cancel_tasks(output))


async def _cancel_tasks(output: str) -> None:
    """Cancel pending tasks."""
    db_path = Path(output) / ".spawner" / "tasks.db"
    
    if not db_path.exists():
        console.print("[red]No task database found.[/red]")
        return
    
    async with TaskQueue(db_path) as queue:
        count = await queue.cancel_all_pending()
        console.print(f"[yellow]Cancelled {count} pending tasks[/yellow]")


@cli.command()
@click.option("--output", "-o", type=click.Path(), default="./docs",
              help="Output directory (where task database is)")
@click.option("--status-filter", "-s", type=click.Choice(["pending", "running", "completed", "failed", "all"]),
              default="all", help="Filter by status")
@click.option("--limit", "-n", type=int, default=20, help="Max tasks to show")
@click.pass_context
def tasks(ctx: click.Context, output: str, status_filter: str, limit: int) -> None:
    """List tasks in the queue."""
    asyncio.run(_list_tasks(output, status_filter, limit))


async def _list_tasks(output: str, status_filter: str, limit: int) -> None:
    """List tasks."""
    db_path = Path(output) / ".spawner" / "tasks.db"
    
    if not db_path.exists():
        console.print("[red]No task database found.[/red]")
        return
    
    async with TaskQueue(db_path) as queue:
        if status_filter == "all":
            tasks = await queue.get_all_tasks()
        else:
            tasks = await queue.get_all_tasks(TaskStatus(status_filter))
        
        # Create table
        table = Table(title=f"Tasks ({len(tasks)} total, showing {min(limit, len(tasks))})")
        table.add_column("ID", style="cyan", width=8)
        table.add_column("Depth", justify="center")
        table.add_column("Status", justify="center")
        table.add_column("Output Path", width=30)
        table.add_column("Tokens", justify="right")
        table.add_column("Duration", justify="right")
        
        for task in tasks[:limit]:
            status_style = {
                TaskStatus.PENDING: "yellow",
                TaskStatus.RUNNING: "blue",
                TaskStatus.COMPLETED: "green",
                TaskStatus.FAILED: "red",
                TaskStatus.CANCELLED: "dim",
            }.get(task.status, "white")
            
            duration = f"{task.duration_seconds:.1f}s" if task.duration_seconds else "-"
            tokens = f"{task.input_tokens}+{task.output_tokens}" if task.input_tokens else "-"
            
            table.add_row(
                task.task_id[:8],
                str(task.depth),
                f"[{status_style}]{task.status.value}[/{status_style}]",
                task.output_path[:30],
                tokens,
                duration,
            )
        
        console.print(table)


@cli.command()
@click.option("--output", "-o", type=click.Path(), default="./docs")
@click.confirmation_option(prompt="Delete ALL tasks and start fresh?")
@click.pass_context
def reset(ctx: click.Context, output: str) -> None:
    """Reset the task queue (delete all tasks)."""
    asyncio.run(_reset_queue(output))


async def _reset_queue(output: str) -> None:
    """Reset the task queue."""
    db_path = Path(output) / ".spawner" / "tasks.db"
    
    if db_path.exists():
        async with TaskQueue(db_path) as queue:
            await queue.clear_all()
        console.print("[green]Task queue reset[/green]")
    else:
        console.print("[yellow]No task database found[/yellow]")


def main() -> None:
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
