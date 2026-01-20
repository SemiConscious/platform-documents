"""Main CLI entry point for the documentation agent."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import click
import yaml
from rich.console import Console
from rich.table import Table

from .orchestrator import Orchestrator
from .utils.logging import setup_logging, console

# Default paths
DEFAULT_CONFIG_PATH = Path("config/config.yaml")
DEFAULT_OUTPUT_DIR = Path("./docs")
DEFAULT_STORE_DIR = Path("./store")


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file."""
    if not config_path.exists():
        # Try example config
        example_path = config_path.parent / "config.example.yaml"
        if example_path.exists():
            config_path = example_path
        else:
            return {}
    
    with open(config_path) as f:
        return yaml.safe_load(f) or {}


@click.group()
@click.option(
    "--config", "-c",
    type=click.Path(exists=False, path_type=Path),
    default=DEFAULT_CONFIG_PATH,
    help="Path to configuration file",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose logging",
)
@click.pass_context
def cli(ctx: click.Context, config: Path, verbose: bool):
    """
    Platform Documentation Agent - AI-powered documentation generation.
    
    Generate comprehensive, layered documentation for the Natterbox platform
    by analyzing GitHub repositories, Confluence spaces, and Jira projects.
    """
    ctx.ensure_object(dict)
    
    # Load configuration
    ctx.obj["config"] = load_config(config)
    ctx.obj["verbose"] = verbose
    
    # Setup logging
    log_config = ctx.obj["config"].get("logging", {})
    setup_logging(
        level="DEBUG" if verbose else log_config.get("level", "INFO"),
        log_file=log_config.get("file"),
        log_format=log_config.get("format"),
    )


@cli.command()
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    default=DEFAULT_OUTPUT_DIR,
    help="Output directory for documentation",
)
@click.option(
    "--store", "-s",
    type=click.Path(path_type=Path),
    default=DEFAULT_STORE_DIR,
    help="Directory for persistent storage",
)
@click.option(
    "--full", "-f",
    is_flag=True,
    help="Full run from scratch (ignore existing state)",
)
@click.option(
    "--skip-discovery",
    is_flag=True,
    help="Skip discovery phase",
)
@click.option(
    "--skip-analysis",
    is_flag=True,
    help="Skip analysis phase",
)
@click.option(
    "--skip-generation",
    is_flag=True,
    help="Skip generation phase",
)
@click.option(
    "--skip-quality",
    is_flag=True,
    help="Skip quality phase",
)
@click.option(
    "--service",
    multiple=True,
    help="Generate docs for specific service(s) only",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Simulate without writing files",
)
@click.pass_context
def generate(
    ctx: click.Context,
    output: Path,
    store: Path,
    full: bool,
    skip_discovery: bool,
    skip_analysis: bool,
    skip_generation: bool,
    skip_quality: bool,
    service: tuple,
    dry_run: bool,
):
    """
    Generate documentation from platform sources.
    
    By default, runs incrementally - only regenerating documents
    whose sources have changed.
    """
    config = ctx.obj["config"]
    verbose = ctx.obj["verbose"]
    
    # If full run requested, clear the store
    if full:
        import shutil
        if store.exists():
            console.print(f"[yellow]Clearing existing store at {store}[/yellow]")
            shutil.rmtree(store)
    
    console.print("[bold blue]Platform Documentation Agent[/bold blue]")
    console.print(f"Output directory: {output}")
    console.print(f"Store directory: {store}")
    
    if dry_run:
        console.print("[yellow]Dry run mode - no files will be written[/yellow]")
    
    # Create orchestrator
    orchestrator = Orchestrator(
        config=config,
        output_dir=output,
        store_dir=store,
    )
    
    # Run the pipeline
    async def run():
        results = await orchestrator.run_full_pipeline(
            skip_discovery=skip_discovery,
            skip_analysis=skip_analysis,
            skip_generation=skip_generation,
            skip_quality=skip_quality,
            services=list(service) if service else None,
            dry_run=dry_run,
            verbose=verbose,
        )
        return results
    
    try:
        results = asyncio.run(run())
        
        # Print summary
        console.print("\n[bold green]Generation Complete[/bold green]\n")
        
        table = Table(title="Phase Results")
        table.add_column("Phase", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Agents", style="yellow")
        table.add_column("Duration", style="magenta")
        
        for phase_name, result in results.items():
            status = "[green]Success[/green]" if result.success else "[red]Failed[/red]"
            agents = f"{result.successful_agents}/{len(result.agent_results)}"
            duration = f"{result.duration_seconds:.2f}s"
            table.add_row(phase_name.title(), status, agents, duration)
        
        console.print(table)
        
        # Exit with error if any phase failed
        if not all(r.success for r in results.values()):
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    default=DEFAULT_OUTPUT_DIR,
    help="Output directory for documentation",
)
@click.option(
    "--store", "-s",
    type=click.Path(path_type=Path),
    default=DEFAULT_STORE_DIR,
    help="Directory for persistent storage",
)
@click.pass_context
def discover(ctx: click.Context, output: Path, store: Path):
    """
    Run only the discovery phase.
    
    Scans sources and populates the knowledge graph without
    generating documentation.
    """
    config = ctx.obj["config"]
    verbose = ctx.obj["verbose"]
    
    console.print("[bold blue]Running Discovery Phase[/bold blue]")
    
    orchestrator = Orchestrator(
        config=config,
        output_dir=output,
        store_dir=store,
    )
    
    async def run():
        await orchestrator.initialize()
        try:
            context = orchestrator.create_context(verbose=verbose)
            result = await orchestrator.run_discovery_phase(context)
            await orchestrator.store.save()
            return result
        finally:
            await orchestrator.shutdown()
    
    try:
        result = asyncio.run(run())
        
        if result.success:
            console.print("[green]Discovery completed successfully[/green]")
            console.print(f"Agents: {result.successful_agents}/{len(result.agent_results)} succeeded")
        else:
            console.print("[red]Discovery failed[/red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    "--store", "-s",
    type=click.Path(path_type=Path),
    default=DEFAULT_STORE_DIR,
    help="Directory for persistent storage",
)
@click.pass_context
def status(ctx: click.Context, store: Path):
    """
    Show current status of the documentation system.
    
    Displays information about the knowledge graph, generated
    documents, and recent runs.
    """
    from .knowledge import KnowledgeStore
    
    console.print("[bold blue]Documentation Agent Status[/bold blue]\n")
    
    # Load store
    store_path = Path(store)
    if not store_path.exists():
        console.print("[yellow]No store found. Run 'doc-agent discover' first.[/yellow]")
        return
    
    knowledge_store = KnowledgeStore(store_path)
    
    async def load():
        await knowledge_store.load()
    
    asyncio.run(load())
    
    stats = knowledge_store.get_statistics()
    
    # Knowledge graph stats
    console.print("[bold]Knowledge Graph[/bold]")
    graph_stats = stats.get("graph", {})
    console.print(f"  Total entities: {graph_stats.get('total_entities', 0)}")
    console.print(f"  Total relations: {graph_stats.get('total_relations', 0)}")
    
    if graph_stats.get("entities_by_type"):
        console.print("  Entities by type:")
        for etype, count in graph_stats["entities_by_type"].items():
            console.print(f"    - {etype}: {count}")
    
    # Document stats
    console.print("\n[bold]Generated Documents[/bold]")
    doc_stats = stats.get("documents", {})
    console.print(f"  Total documents: {doc_stats.get('total', 0)}")
    
    by_status = doc_stats.get("by_status", {})
    if by_status:
        console.print(f"  Recent (< 7 days): {by_status.get('recent', 0)}")
        console.print(f"  Stale (> 7 days): {by_status.get('stale', 0)}")


@cli.command()
@click.option(
    "--store", "-s",
    type=click.Path(path_type=Path),
    default=DEFAULT_STORE_DIR,
    help="Directory for persistent storage",
)
@click.option(
    "--type", "-t",
    "entity_type",
    type=click.Choice(["service", "domain", "api", "all"]),
    default="all",
    help="Type of entities to list",
)
@click.pass_context
def list_entities(ctx: click.Context, store: Path, entity_type: str):
    """
    List entities in the knowledge graph.
    """
    from .knowledge import KnowledgeStore, EntityType
    
    store_path = Path(store)
    if not store_path.exists():
        console.print("[yellow]No store found. Run 'doc-agent discover' first.[/yellow]")
        return
    
    knowledge_store = KnowledgeStore(store_path)
    
    async def load():
        await knowledge_store.load()
    
    asyncio.run(load())
    
    graph = knowledge_store.graph
    
    if entity_type == "all":
        types = [EntityType.SERVICE, EntityType.DOMAIN, EntityType.API]
    else:
        types = [EntityType(entity_type)]
    
    for etype in types:
        entities = graph.get_entities_by_type(etype)
        if entities:
            console.print(f"\n[bold]{etype.value.title()}s ({len(entities)})[/bold]")
            for entity in entities[:20]:  # Limit to 20
                console.print(f"  - {entity.name} ({entity.id})")
            if len(entities) > 20:
                console.print(f"  ... and {len(entities) - 20} more")


# ============================================================================
# Authentication Commands
# ============================================================================

@cli.group()
def auth():
    """Manage authentication for external services."""
    pass


@auth.command("login")
@click.argument("service", type=click.Choice(["github", "atlassian", "aws"]))
@click.pass_context
def auth_login(ctx: click.Context, service: str):
    """
    Authenticate with an external service.
    
    Opens browser for OAuth flow (GitHub, Atlassian) or initiates
    AWS SSO login.
    """
    config = ctx.obj["config"]
    
    from .auth import OAuthManager, OAuthConfig, TokenCache, AWSSSOAuth
    
    token_cache = TokenCache()
    
    if service == "github":
        github_config = config.get("auth", {}).get("github", {})
        if not github_config.get("client_id"):
            console.print("[red]GitHub OAuth not configured. Add client_id to config.[/red]")
            return
        
        oauth = OAuthManager(token_cache=token_cache)
        oauth.add_config(OAuthConfig.github(
            client_id=github_config["client_id"],
            client_secret=github_config.get("client_secret"),
        ))
        
        async def login():
            return await oauth.authenticate("github", interactive=True)
        
        console.print("[blue]Authenticating with GitHub...[/blue]")
        token = asyncio.run(login())
        
        if token:
            console.print("[green]Successfully authenticated with GitHub![/green]")
        else:
            console.print("[red]GitHub authentication failed[/red]")
    
    elif service == "atlassian":
        atlassian_config = config.get("auth", {}).get("atlassian", {})
        if not atlassian_config.get("client_id"):
            console.print("[red]Atlassian OAuth not configured. Add client_id to config.[/red]")
            return
        
        oauth = OAuthManager(token_cache=token_cache)
        oauth_config = OAuthConfig.atlassian(
            client_id=atlassian_config["client_id"],
            client_secret=atlassian_config.get("client_secret"),
        )
        if atlassian_config.get("scopes"):
            oauth_config.scopes = atlassian_config["scopes"]
        oauth.add_config(oauth_config)
        
        async def login():
            return await oauth.authenticate("atlassian", interactive=True)
        
        console.print("[blue]Authenticating with Atlassian...[/blue]")
        token = asyncio.run(login())
        
        if token:
            console.print("[green]Successfully authenticated with Atlassian![/green]")
        else:
            console.print("[red]Atlassian authentication failed[/red]")
    
    elif service == "aws":
        aws_config = config.get("auth", {}).get("aws", {})
        profile = aws_config.get("profile", "default")
        
        aws_sso = AWSSSOAuth(
            profile=profile,
            region=aws_config.get("region", "us-east-1"),
            token_cache=token_cache,
            use_aws_vault=aws_config.get("use_aws_vault", True),
        )
        
        async def login():
            return await aws_sso.get_credentials()
        
        console.print(f"[blue]Authenticating with AWS SSO (profile: {profile})...[/blue]")
        creds = asyncio.run(login())
        
        if creds:
            console.print(f"[green]Successfully authenticated with AWS![/green]")
            console.print(f"Credentials valid until: {creds.expiration}")
        else:
            console.print("[red]AWS SSO authentication failed[/red]")


@auth.command("status")
@click.pass_context
def auth_status(ctx: click.Context):
    """Show authentication status for all services."""
    from .auth import TokenCache
    
    console.print("[bold blue]Authentication Status[/bold blue]\n")
    
    token_cache = TokenCache()
    tokens = token_cache.list_tokens()
    
    if not tokens:
        console.print("[yellow]No cached tokens found.[/yellow]")
        console.print("Run 'doc-agent auth login <service>' to authenticate.")
        return
    
    table = Table(title="Cached Tokens")
    table.add_column("Service", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Expires", style="magenta")
    table.add_column("Refresh", style="blue")
    
    for token in tokens:
        status = "[red]Expired[/red]" if token["is_expired"] else "[green]Valid[/green]"
        expires = token.get("expires_at", "Never")[:19] if token.get("expires_at") else "Never"
        refresh = "[green]Yes[/green]" if token.get("has_refresh_token") else "[red]No[/red]"
        
        table.add_row(
            token["service"],
            token["token_type"],
            status,
            expires,
            refresh,
        )
    
    console.print(table)


@auth.command("logout")
@click.argument("service", type=click.Choice(["github", "atlassian", "aws", "all"]))
@click.pass_context
def auth_logout(ctx: click.Context, service: str):
    """Clear cached tokens for a service."""
    from .auth import TokenCache
    
    token_cache = TokenCache()
    
    if service == "all":
        token_cache.clear_all()
        console.print("[green]Cleared all cached tokens[/green]")
    else:
        count = token_cache.clear_service(service)
        if count > 0:
            console.print(f"[green]Cleared {count} token(s) for {service}[/green]")
        else:
            console.print(f"[yellow]No tokens found for {service}[/yellow]")


@auth.command("refresh")
@click.argument("service", type=click.Choice(["github", "atlassian"]))
@click.pass_context
def auth_refresh(ctx: click.Context, service: str):
    """Manually refresh token for a service."""
    config = ctx.obj["config"]
    
    from .auth import OAuthManager, OAuthConfig, TokenCache
    
    token_cache = TokenCache()
    oauth = OAuthManager(token_cache=token_cache)
    
    # Get cached token
    cached = token_cache.get(service, "access_token")
    if not cached:
        console.print(f"[yellow]No cached token for {service}. Run 'doc-agent auth login {service}' first.[/yellow]")
        return
    
    if not cached.refresh_token:
        console.print(f"[red]No refresh token available for {service}. Re-authenticate.[/red]")
        return
    
    # Configure OAuth
    if service == "github":
        github_config = config.get("auth", {}).get("github", {})
        oauth.add_config(OAuthConfig.github(
            client_id=github_config.get("client_id", ""),
            client_secret=github_config.get("client_secret"),
        ))
    elif service == "atlassian":
        atlassian_config = config.get("auth", {}).get("atlassian", {})
        oauth.add_config(OAuthConfig.atlassian(
            client_id=atlassian_config.get("client_id", ""),
            client_secret=atlassian_config.get("client_secret"),
        ))
    
    async def refresh():
        return await oauth.refresh_token(service, cached.refresh_token)
    
    console.print(f"[blue]Refreshing {service} token...[/blue]")
    new_token = asyncio.run(refresh())
    
    if new_token:
        console.print(f"[green]Successfully refreshed {service} token![/green]")
    else:
        console.print(f"[red]Failed to refresh token. Try re-authenticating.[/red]")


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
