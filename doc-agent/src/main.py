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
DEFAULT_OUTPUT_DIR = Path("../docs")  # Write to root docs directory
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
    "--skip-enrichment",
    is_flag=True,
    help="Skip enrichment phase (Confluence/Docs360 queries)",
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
@click.option(
    "--no-local-repos",
    is_flag=True,
    help="Use GitHub API instead of local clones for code analysis",
)
@click.option(
    "--profile",
    type=click.Choice(["premium", "hybrid", "tiered", "economy"]),
    default=None,
    help="LLM model profile for cost/quality tradeoffs (default: from config)",
)
@click.pass_context
def generate(
    ctx: click.Context,
    output: Path,
    store: Path,
    full: bool,
    skip_discovery: bool,
    skip_enrichment: bool,
    skip_analysis: bool,
    skip_generation: bool,
    skip_quality: bool,
    service: tuple,
    dry_run: bool,
    no_local_repos: bool,
    profile: Optional[str],
):
    """
    Generate documentation from platform sources.
    
    Pipeline phases:
    1. Discovery - Scan GitHub repos to discover services
    2. Enrichment - Query Confluence/Docs360 for each service
    3. Analysis - Build knowledge graph and infer architecture
    4. Generation - Generate documentation
    5. Quality - Cross-reference and validate
    
    By default, runs incrementally - only regenerating documents
    whose sources have changed.
    """
    config = ctx.obj["config"]
    verbose = ctx.obj["verbose"]
    
    # Override profile if specified on command line
    if profile:
        if "llm" not in config:
            config["llm"] = {}
        config["llm"]["active_profile"] = profile
        console.print(f"[cyan]Using model profile: {profile}[/cyan]")
    else:
        active_profile = config.get("llm", {}).get("active_profile", "tiered")
        console.print(f"[dim]Using model profile: {active_profile}[/dim]")
    
    # If full run requested, clear the store (but preserve API caches)
    if full:
        import shutil
        if store.exists():
            console.print(f"[yellow]Clearing existing store at {store}[/yellow]")
            # Preserve github-cache.json and repo-commits.json (API rate limit workarounds)
            github_cache = store / "github-cache.json"
            repo_commits = store / "repo-commits.json"
            preserved_github = None
            preserved_commits = None
            if github_cache.exists():
                preserved_github = github_cache.read_text()
            if repo_commits.exists():
                preserved_commits = repo_commits.read_text()
            
            shutil.rmtree(store)
            store.mkdir(parents=True, exist_ok=True)
            
            # Restore preserved caches
            if preserved_github:
                github_cache.write_text(preserved_github)
                console.print("[dim]  (preserved github-cache.json)[/dim]")
            if preserved_commits:
                repo_commits.write_text(preserved_commits)
                console.print("[dim]  (preserved repo-commits.json)[/dim]")
    
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
            skip_enrichment=skip_enrichment,
            skip_analysis=skip_analysis,
            skip_generation=skip_generation,
            skip_quality=skip_quality,
            services=list(service) if service else None,
            dry_run=dry_run,
            verbose=verbose,
            use_local_repos=not no_local_repos,
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
@click.argument("service", type=click.Choice(["aws", "mcp"]))
@click.pass_context
def auth_login(ctx: click.Context, service: str):
    """
    Authenticate with an external service.
    
    - aws: AWS SSO for Bedrock API access
    - mcp: Natterbox MCP server (for GitHub/Confluence/Jira)
    """
    config = ctx.obj["config"]
    
    from .auth import TokenCache, AWSSSOAuth
    
    token_cache = TokenCache()
    
    if service == "aws":
        aws_config = config.get("auth", {}).get("aws", {})
        profile = aws_config.get("profile", "sso-dev03-admin")
        
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
    
    elif service == "mcp":
        # MCP server handles its own OAuth
        from .mcp.client import MCPClient, MCPOAuthConfig
        
        mcp_config = config.get("mcp", {})
        oauth_config = mcp_config.get("oauth", {})
        
        client = MCPClient(
            server_url=mcp_config.get("url", "https://avatar.natterbox-dev03.net/mcp/sse"),
            oauth_config=MCPOAuthConfig(
                authorization_url=oauth_config.get("authorization_url", "https://avatar.natterbox-dev03.net/mcp/authorize"),
                token_url=oauth_config.get("token_url", "https://avatar.natterbox-dev03.net/mcp/token"),
                client_id=oauth_config.get("client_id", "doc-agent"),
                scopes=oauth_config.get("scopes", []),
            ),
        )
        
        async def login():
            await client.connect()
            await client.disconnect()
        
        console.print("[blue]Authenticating with Natterbox MCP server...[/blue]")
        try:
            asyncio.run(login())
            console.print("[green]Successfully authenticated with MCP server![/green]")
        except Exception as e:
            console.print(f"[red]MCP authentication failed: {e}[/red]")


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
        console.print("Run 'doc-agent auth login aws' for Bedrock access.")
        console.print("Run 'doc-agent auth login mcp' for MCP server access.")
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
@click.argument("service", type=click.Choice(["aws", "mcp", "all"]))
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


# ============================================================================
# Cache Management Commands
# ============================================================================

@cli.group()
def cache():
    """Manage local caches (GitHub repositories, etc.)."""
    pass


@cache.command("status")
@click.option(
    "--store", "-s",
    type=click.Path(path_type=Path),
    default=DEFAULT_STORE_DIR,
    help="Directory for persistent storage",
)
@click.pass_context
def cache_status(ctx: click.Context, store: Path):
    """Show cache status including GitHub repository cache."""
    from .knowledge import KnowledgeStore
    
    console.print("[bold blue]Cache Status[/bold blue]\n")
    
    store_path = Path(store)
    if not store_path.exists():
        console.print("[yellow]No store found.[/yellow]")
        return
    
    knowledge_store = KnowledgeStore(store_path)
    
    async def load():
        await knowledge_store.load()
    
    asyncio.run(load())
    
    # GitHub cache status
    console.print("[bold]GitHub Repository Cache[/bold]")
    
    cached_repos = knowledge_store.get_all_cached_repositories()
    cache_age = knowledge_store.get_github_cache_age()
    
    if not cached_repos:
        console.print("  [yellow]No cached repositories[/yellow]")
    else:
        total = sum(len(repos) for repos in cached_repos.values())
        console.print(f"  Total repositories: {total}")
        if cache_age:
            console.print(f"  Cached at: {cache_age.isoformat()}")
        
        console.print("  By organization:")
        for org, repos in sorted(cached_repos.items()):
            console.print(f"    - {org}: {len(repos)} repos")


@cache.command("populate")
@click.option(
    "--store", "-s",
    type=click.Path(path_type=Path),
    default=DEFAULT_STORE_DIR,
    help="Directory for persistent storage",
)
@click.pass_context
def cache_populate(ctx: click.Context, store: Path):
    """
    Populate GitHub repository cache.
    
    Fetches repository lists from all configured organizations and caches them.
    Use this when the rate limit resets to build the cache for future runs.
    """
    from .knowledge import KnowledgeStore
    from .mcp.client import MCPClient
    from .mcp.github import GitHubClient, Repository
    
    config = ctx.obj["config"]
    
    console.print("[bold blue]Populating GitHub Cache[/bold blue]\n")
    
    store_path = Path(store)
    store_path.mkdir(parents=True, exist_ok=True)
    
    knowledge_store = KnowledgeStore(store_path)
    
    # Get organizations from config
    source_config = config.get("sources", {}).get("github", {})
    organizations = source_config.get("organizations", [])
    
    if not organizations:
        console.print("[yellow]No organizations configured in sources.github.organizations[/yellow]")
        return
    
    console.print(f"Organizations to cache: {', '.join(organizations)}")
    
    async def populate():
        await knowledge_store.load()
        
        mcp = MCPClient()
        await mcp.connect()
        
        try:
            github = GitHubClient(mcp)
            
            for org in organizations:
                console.print(f"\n[cyan]Fetching repositories for {org}...[/cyan]")
                
                try:
                    repos = await github.list_repositories(org=org)
                    
                    if not repos:
                        console.print(f"  [yellow]No repositories found (may be rate limited)[/yellow]")
                        continue
                    
                    # Check for API error in response
                    if isinstance(repos, list) and len(repos) == 0:
                        # Try to get error info
                        console.print(f"  [yellow]Empty response - possibly rate limited[/yellow]")
                        continue
                    
                    # Cache the repositories
                    # Count archived repos
                    archived_count = sum(1 for r in repos if r.archived)
                    
                    repo_dicts = [
                        {
                            "name": r.name,
                            "full_name": r.full_name,
                            "description": r.description,
                            "html_url": r.url,
                            "default_branch": r.default_branch,
                            "language": r.language,
                            "topics": r.topics,
                            "archived": r.archived,
                        }
                        for r in repos
                    ]
                    knowledge_store.cache_repositories(org, repo_dicts)
                    console.print(f"  [green]Cached {len(repos)} repositories ({archived_count} archived)[/green]")
                    
                except Exception as e:
                    console.print(f"  [red]Error: {e}[/red]")
            
            # Save the cache
            await knowledge_store.save()
            console.print("\n[green]Cache saved successfully[/green]")
            
        finally:
            await mcp.disconnect()
    
    try:
        asyncio.run(populate())
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cache.command("clear")
@click.option(
    "--store", "-s",
    type=click.Path(path_type=Path),
    default=DEFAULT_STORE_DIR,
    help="Directory for persistent storage",
)
@click.option(
    "--github", "clear_github",
    is_flag=True,
    help="Clear GitHub repository cache",
)
@click.option(
    "--all", "clear_all",
    is_flag=True,
    help="Clear all caches",
)
@click.pass_context
def cache_clear(ctx: click.Context, store: Path, clear_github: bool, clear_all: bool):
    """Clear cached data."""
    from .knowledge import KnowledgeStore
    
    if not clear_github and not clear_all:
        console.print("[yellow]Specify --github or --all to clear caches[/yellow]")
        return
    
    store_path = Path(store)
    if not store_path.exists():
        console.print("[yellow]No store found.[/yellow]")
        return
    
    knowledge_store = KnowledgeStore(store_path)
    
    async def clear():
        await knowledge_store.load()
        
        if clear_github or clear_all:
            knowledge_store.clear_github_cache()
            console.print("[green]Cleared GitHub cache[/green]")
        
        await knowledge_store.save()
    
    asyncio.run(clear())


@cache.command("check-rate-limit")
@click.pass_context
def cache_check_rate_limit(ctx: click.Context):
    """Check GitHub API rate limit status."""
    from .mcp.client import MCPClient
    
    console.print("[bold blue]GitHub Rate Limit Status[/bold blue]\n")
    
    async def check():
        mcp = MCPClient()
        await mcp.connect()
        
        try:
            # Make a minimal request to check rate limit
            response = await mcp.call_tool("github", {
                "operation": "list_repos",
                "org": "redmatter",
                "perPage": 1,
                "page": 1,
            })
            
            if response.success:
                data = response.data
                if isinstance(data, dict) and 'error' in data:
                    error = data['error']
                    if 'rate limit' in error.lower():
                        console.print("[red]Rate limited![/red]")
                        console.print(f"\n{error}")
                        
                        # Parse reset time if available
                        import re
                        timestamp_match = re.search(r'timestamp (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC)', error)
                        if timestamp_match:
                            console.print(f"\nRate limit hit at: {timestamp_match.group(1)}")
                            console.print("[yellow]Rate limit typically resets 1 hour after first exceeded[/yellow]")
                    else:
                        console.print(f"[red]API Error: {error}[/red]")
                else:
                    console.print("[green]Rate limit OK - API is accessible![/green]")
                    
                    # Show repo count from response
                    repos = []
                    if isinstance(data, dict):
                        if "data" in data and isinstance(data["data"], dict):
                            repos = data["data"].get("repositories", [])
                        elif "repositories" in data:
                            repos = data["repositories"]
                    elif isinstance(data, list):
                        repos = data
                    
                    if repos:
                        console.print(f"Test request returned {len(repos)} repo(s)")
            else:
                console.print(f"[red]Request failed: {response.error}[/red]")
                
        finally:
            await mcp.disconnect()
    
    try:
        asyncio.run(check())
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


# =============================================================================
# Repository Clone Commands
# =============================================================================

DEFAULT_REPOS_DIR = Path("repos")


@cli.group()
def repos():
    """Manage local repository clones."""
    pass


@repos.command("clone")
@click.option(
    "--repos-dir", "-r",
    type=click.Path(path_type=Path),
    default=DEFAULT_REPOS_DIR,
    help="Directory to store cloned repositories",
)
@click.option(
    "--store", "-s",
    type=click.Path(path_type=Path),
    default=DEFAULT_STORE_DIR,
    help="Directory for persistent storage",
)
@click.option(
    "--max-concurrent", "-c",
    type=int,
    default=10,
    help="Maximum concurrent clone operations",
)
@click.option(
    "--org", "-o",
    multiple=True,
    help="Specific organization(s) to clone (default: all configured)",
)
@click.pass_context
def repos_clone(ctx: click.Context, repos_dir: Path, store: Path, max_concurrent: int, org: tuple):
    """
    Clone all repositories locally.
    
    This avoids GitHub API rate limits by working with local clones.
    First run will clone all repos; subsequent runs will fetch updates.
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from .knowledge import KnowledgeStore
    from .repos import RepoCloneManager, CloneManagerConfig
    
    config = ctx.obj["config"]
    
    console.print("[bold blue]Cloning Repositories[/bold blue]\n")
    
    # Setup paths
    repos_path = Path(repos_dir)
    repos_path.mkdir(parents=True, exist_ok=True)
    store_path = Path(store)
    store_path.mkdir(parents=True, exist_ok=True)
    
    # Load cached repository list
    knowledge_store = KnowledgeStore(store_path)
    
    async def clone_all():
        await knowledge_store.load()
        
        # Get organizations
        source_config = config.get("sources", {}).get("github", {})
        skip_archived = source_config.get("skip_archived", True)
        
        if org:
            organizations = list(org)
        else:
            organizations = source_config.get("organizations", [])
        
        console.print(f"Organizations: {', '.join(organizations)}")
        console.print(f"Repos directory: {repos_path.absolute()}")
        console.print(f"Max concurrent: {max_concurrent}")
        console.print()
        
        # Get repos from cache
        all_repos = []
        for organization in organizations:
            cached = knowledge_store.get_cached_repositories(organization)
            if cached:
                # Filter archived if configured
                if skip_archived:
                    repos = [r for r in cached if not r.get("archived", False)]
                    archived_count = len(cached) - len(repos)
                    console.print(f"  {organization}: {len(repos)} repos ({archived_count} archived skipped)")
                else:
                    repos = cached
                    console.print(f"  {organization}: {len(repos)} repos")
                all_repos.extend(repos)
            else:
                console.print(f"  [yellow]{organization}: No cached repos (run 'cache populate' first)[/yellow]")
        
        if not all_repos:
            console.print("\n[yellow]No repositories to clone. Run 'cache populate' first.[/yellow]")
            return
        
        console.print(f"\n[cyan]Cloning/updating {len(all_repos)} repositories...[/cyan]\n")
        
        # Setup clone manager
        clone_config = CloneManagerConfig(
            repos_dir=repos_path,
            max_concurrent=max_concurrent,
            shallow_clone=True,
        )
        cache_path = store_path / "repo-commits.json"
        clone_manager = RepoCloneManager(clone_config, cache_path)
        
        # Progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Cloning...", total=len(all_repos))
            
            def progress_callback(completed, total, repo_name):
                progress.update(task, completed=completed, description=f"[cyan]{repo_name}[/cyan]")
            
            results = await clone_manager.clone_all(all_repos, progress_callback)
        
        # Summary
        success = sum(1 for r in results if not r.error)
        failed = sum(1 for r in results if r.error)
        changed = sum(1 for r in results if r.changed and not r.error)
        
        console.print(f"\n[bold green]Clone complete![/bold green]")
        console.print(f"  Successful: {success}")
        console.print(f"  Changed: {changed}")
        console.print(f"  Failed: {failed}")
        
        if failed > 0:
            console.print("\n[yellow]Failed repositories:[/yellow]")
            for r in results:
                if r.error:
                    console.print(f"  - {r.full_name}: {r.error[:80]}")
    
    try:
        asyncio.run(clone_all())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@repos.command("status")
@click.option(
    "--repos-dir", "-r",
    type=click.Path(path_type=Path),
    default=DEFAULT_REPOS_DIR,
    help="Directory containing cloned repositories",
)
@click.option(
    "--store", "-s",
    type=click.Path(path_type=Path),
    default=DEFAULT_STORE_DIR,
    help="Directory for persistent storage",
)
@click.pass_context
def repos_status(ctx: click.Context, repos_dir: Path, store: Path):
    """Show status of local repository clones."""
    import json
    
    repos_path = Path(repos_dir)
    store_path = Path(store)
    cache_path = store_path / "repo-commits.json"
    
    console.print("[bold blue]Repository Clone Status[/bold blue]\n")
    
    # Check if repos directory exists
    if not repos_path.exists():
        console.print(f"[yellow]Repos directory does not exist: {repos_path}[/yellow]")
        console.print("Run 'repos clone' to clone repositories.")
        return
    
    # Count cloned repos
    cloned_count = 0
    org_counts = {}
    
    for org_dir in repos_path.iterdir():
        if org_dir.is_dir():
            repos = [r for r in org_dir.iterdir() if r.is_dir() and (r / ".git").exists()]
            org_counts[org_dir.name] = len(repos)
            cloned_count += len(repos)
    
    console.print(f"Repos directory: {repos_path.absolute()}")
    console.print(f"Total cloned repos: {cloned_count}")
    console.print()
    
    for org, count in sorted(org_counts.items()):
        console.print(f"  {org}: {count} repos")
    
    # Check commit cache
    if cache_path.exists():
        console.print()
        with open(cache_path) as f:
            cache = json.load(f)
        console.print(f"Commit cache: {len(cache)} entries")
    else:
        console.print("\n[yellow]No commit cache found[/yellow]")
    
    # Calculate disk usage
    try:
        import subprocess
        result = subprocess.run(
            ["du", "-sh", str(repos_path)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            size = result.stdout.split()[0]
            console.print(f"Disk usage: {size}")
    except:
        pass


@repos.command("clean")
@click.option(
    "--repos-dir", "-r",
    type=click.Path(path_type=Path),
    default=DEFAULT_REPOS_DIR,
    help="Directory containing cloned repositories",
)
@click.option(
    "--store", "-s",
    type=click.Path(path_type=Path),
    default=DEFAULT_STORE_DIR,
    help="Directory for persistent storage",
)
@click.option(
    "--confirm", is_flag=True,
    help="Confirm deletion without prompting",
)
@click.pass_context
def repos_clean(ctx: click.Context, repos_dir: Path, store: Path, confirm: bool):
    """Remove all cloned repositories."""
    import shutil
    
    repos_path = Path(repos_dir)
    store_path = Path(store)
    cache_path = store_path / "repo-commits.json"
    
    if not repos_path.exists():
        console.print("[yellow]Repos directory does not exist[/yellow]")
        return
    
    if not confirm:
        if not click.confirm(f"Delete all repos in {repos_path}?"):
            console.print("Cancelled")
            return
    
    console.print(f"[yellow]Removing {repos_path}...[/yellow]")
    shutil.rmtree(repos_path)
    
    if cache_path.exists():
        console.print(f"[yellow]Removing commit cache...[/yellow]")
        cache_path.unlink()
    
    console.print("[green]Done[/green]")


# =============================================================================
# AI Analysis Commands
# =============================================================================

@cli.command("ai-docs")
@click.argument("repo_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory for generated docs",
)
@click.option(
    "--profile",
    type=click.Choice(["premium", "hybrid", "tiered", "economy"]),
    default="hybrid",
    help="LLM model profile (hybrid: Opus analysis + Sonnet writing)",
)
@click.pass_context
def ai_docs(ctx: click.Context, repo_path: Path, output: Optional[Path], profile: str):
    """
    Generate full AI-powered documentation for a repository.
    
    This runs the complete AI pipeline:
    1. AI Code Analysis - understand the codebase
    2. AI Template Generation - create custom doc structure
    3. AI Content Writing - generate rich documentation
    
    Uses hybrid profile by default (Opus for deep analysis, Sonnet for fast writing).
    """
    from anthropic import AsyncAnthropicBedrock
    from .analyzers import AICodeAnalyzer, AIAnalysisConfig
    from .documentation import AITemplateGenerator, AIContentWriter
    from .llm import ModelSelector
    from .auth import AWSSSOAuth, TokenCache
    from .tracking import TokenTracker
    
    config = ctx.obj["config"]
    
    # Override profile
    if "llm" not in config:
        config["llm"] = {}
    config["llm"]["active_profile"] = profile
    
    # Default output directory
    if output is None:
        output = Path("./docs") / repo_path.name
    
    console.print(f"[bold blue]AI Documentation Generation[/bold blue]")
    console.print(f"Repository: {repo_path}")
    console.print(f"Output: {output}")
    console.print(f"Profile: {profile}")
    console.print()
    
    async def generate():
        # Setup
        token_cache = TokenCache()
        aws_config = config.get("auth", {}).get("aws", {})
        aws_sso = AWSSSOAuth(
            profile=aws_config.get("profile", "sso-dev03-admin"),
            region=aws_config.get("region", "us-east-1"),
            token_cache=token_cache,
            use_aws_vault=aws_config.get("use_aws_vault", True),
        )
        
        creds = await aws_sso.get_credentials()
        if not creds:
            console.print("[red]Failed to get AWS credentials[/red]")
            return
        
        bedrock_client = AsyncAnthropicBedrock(
            aws_access_key=creds.access_key_id,
            aws_secret_key=creds.secret_access_key,
            aws_session_token=creds.session_token,
            aws_region=creds.region,
        )
        
        model_selector = ModelSelector(config, profile)
        token_tracker = TokenTracker()
        
        # Phase 1: Code Analysis
        console.print("[cyan]Phase 1: Analyzing codebase...[/cyan]")
        analyzer = AICodeAnalyzer(
            llm_client=bedrock_client,
            model_selector=model_selector,
            token_tracker=token_tracker,
        )
        analysis = await analyzer.analyze_repository(repo_path, repo_path.name)
        console.print(f"  Found {len(analysis.endpoints)} endpoints, {len(analysis.models)} models")
        
        # Phase 2: Template Generation
        console.print("[cyan]Phase 2: Generating documentation template...[/cyan]")
        template_gen = AITemplateGenerator(
            llm_client=bedrock_client,
            model_selector=model_selector,
            token_tracker=token_tracker,
        )
        plan = await template_gen.generate_plan(repo_path, repo_path.name, analysis)
        console.print(f"  Created plan with {len(plan.documents)} documents")
        
        # Phase 3: Content Writing
        console.print("[cyan]Phase 3: Writing documentation content...[/cyan]")
        writer = AIContentWriter(
            llm_client=bedrock_client,
            model_selector=model_selector,
            token_tracker=token_tracker,
        )
        result = await writer.generate_documentation(plan, analysis, repo_path)
        
        # Write output files
        console.print("[cyan]Writing files...[/cyan]")
        output.mkdir(parents=True, exist_ok=True)
        
        for doc in result.documents:
            doc_path = output / doc.path
            doc_path.parent.mkdir(parents=True, exist_ok=True)
            doc_path.write_text(doc.content)
            console.print(f"  Wrote {doc.path} ({doc.word_count} words)")
        
        # Print summary
        console.print()
        console.print("[bold green]Documentation Complete![/bold green]")
        console.print(f"  Documents: {len(result.documents)}")
        console.print(f"  Total words: {sum(d.word_count for d in result.documents)}")
        
        # Token usage
        console.print()
        token_tracker.print_summary()
    
    try:
        asyncio.run(generate())
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()


@cli.command("ai-template")
@click.argument("repo_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--profile",
    type=click.Choice(["premium", "hybrid", "tiered", "economy"]),
    default="economy",
    help="LLM model profile (economy recommended for templates)",
)
@click.pass_context
def ai_template(ctx: click.Context, repo_path: Path, profile: str):
    """
    Generate a custom documentation template for a repository.
    
    Uses AI to analyze the repo and determine the optimal
    documentation structure.
    """
    from anthropic import AsyncAnthropicBedrock
    from .documentation import AITemplateGenerator
    from .llm import ModelSelector
    from .auth import AWSSSOAuth, TokenCache
    
    config = ctx.obj["config"]
    
    # Override profile
    if "llm" not in config:
        config["llm"] = {}
    config["llm"]["active_profile"] = profile
    
    console.print(f"[bold blue]AI Template Generation[/bold blue]")
    console.print(f"Repository: {repo_path}")
    console.print(f"Profile: {profile}")
    console.print()
    
    async def generate():
        # Setup Bedrock client
        token_cache = TokenCache()
        aws_config = config.get("auth", {}).get("aws", {})
        aws_sso = AWSSSOAuth(
            profile=aws_config.get("profile", "sso-dev03-admin"),
            region=aws_config.get("region", "us-east-1"),
            token_cache=token_cache,
            use_aws_vault=aws_config.get("use_aws_vault", True),
        )
        
        creds = await aws_sso.get_credentials()
        if not creds:
            console.print("[red]Failed to get AWS credentials[/red]")
            return
        
        bedrock_client = AsyncAnthropicBedrock(
            aws_access_key=creds.access_key_id,
            aws_secret_key=creds.secret_access_key,
            aws_session_token=creds.session_token,
            aws_region=creds.region,
        )
        
        model_selector = ModelSelector(config, profile)
        
        generator = AITemplateGenerator(
            llm_client=bedrock_client,
            model_selector=model_selector,
        )
        
        console.print("[cyan]Analyzing repository and generating template...[/cyan]")
        
        plan = await generator.generate_plan(
            repo_path=repo_path,
            service_name=repo_path.name,
        )
        
        # Print results
        console.print()
        console.print(f"[bold green]Documentation Plan[/bold green]")
        console.print(f"  Service: {plan.service_name}")
        console.print(f"  Type: {plan.repo_type}")
        console.print(f"  Audience: {plan.target_audience}")
        console.print(f"  Description: {plan.description[:80]}...")
        
        if plan.key_features:
            console.print()
            console.print("[bold]Key Features:[/bold]")
            for feature in plan.key_features[:5]:
                console.print(f"  - {feature}")
        
        console.print()
        console.print(f"[bold]Documents ({len(plan.documents)}):[/bold]")
        for doc in plan.get_documents_by_priority():
            status = "[green]required[/green]" if doc.required else "[dim]optional[/dim]"
            console.print(f"  [{doc.priority}] {doc.path} - {doc.title} ({status})")
            if doc.sections:
                console.print(f"      Sections: {', '.join(doc.sections[:4])}")
    
    try:
        asyncio.run(generate())
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()


@cli.command("ai-analyze")
@click.argument("repo_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--profile",
    type=click.Choice(["premium", "hybrid", "tiered", "economy"]),
    default="tiered",
    help="LLM model profile",
)
@click.pass_context
def ai_analyze(ctx: click.Context, repo_path: Path, profile: str):
    """
    Test AI-powered code analysis on a repository.
    
    This uses Claude to extract endpoints, models, and config
    instead of regex patterns.
    """
    from anthropic import AsyncAnthropicBedrock
    from .analyzers import AICodeAnalyzer, AIAnalysisConfig
    from .llm import ModelSelector
    from .auth import AWSSSOAuth, TokenCache
    
    config = ctx.obj["config"]
    
    # Override profile
    if "llm" not in config:
        config["llm"] = {}
    config["llm"]["active_profile"] = profile
    
    console.print(f"[bold blue]AI Code Analysis[/bold blue]")
    console.print(f"Repository: {repo_path}")
    console.print(f"Profile: {profile}")
    console.print()
    
    async def analyze():
        # Setup Bedrock client
        token_cache = TokenCache()
        aws_config = config.get("auth", {}).get("aws", {})
        aws_sso = AWSSSOAuth(
            profile=aws_config.get("profile", "sso-dev03-admin"),
            region=aws_config.get("region", "us-east-1"),
            token_cache=token_cache,
            use_aws_vault=aws_config.get("use_aws_vault", True),
        )
        
        creds = await aws_sso.get_credentials()
        if not creds:
            console.print("[red]Failed to get AWS credentials[/red]")
            return
        
        # Use AsyncAnthropicBedrock for AWS Bedrock
        bedrock_client = AsyncAnthropicBedrock(
            aws_access_key=creds.access_key_id,
            aws_secret_key=creds.secret_access_key,
            aws_session_token=creds.session_token,
            aws_region=creds.region,
        )
        
        # Create model selector
        model_selector = ModelSelector(config, profile)
        console.print(f"[dim]Model selector: {model_selector.profile.name}[/dim]")
        
        # Create AI analyzer
        analyzer = AICodeAnalyzer(
            llm_client=bedrock_client,
            model_selector=model_selector,
            config=AIAnalysisConfig(),
        )
        
        console.print("[cyan]Analyzing repository...[/cyan]")
        
        result = await analyzer.analyze_repository(
            repo_path=repo_path,
            service_name=repo_path.name,
        )
        
        # Print results
        console.print()
        console.print(f"[bold green]Analysis Results[/bold green]")
        console.print(f"  Endpoints: {len(result.endpoints)}")
        console.print(f"  Models: {len(result.models)}")
        console.print(f"  Config vars: {len(result.config)}")
        console.print(f"  Side effects: {len(result.side_effects)}")
        console.print(f"  Dependencies: {len(result.dependencies)}")
        
        if result.endpoints:
            console.print()
            console.print("[bold]Sample Endpoints:[/bold]")
            for ep in result.endpoints[:5]:
                console.print(f"  {ep.method} {ep.path} - {ep.description[:50] if ep.description else 'No description'}...")
        
        if result.models:
            console.print()
            console.print("[bold]Sample Models:[/bold]")
            for m in result.models[:5]:
                console.print(f"  {m.name} ({len(m.fields)} fields) - {m.description[:50] if m.description else 'No description'}...")
    
    try:
        asyncio.run(analyze())
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
