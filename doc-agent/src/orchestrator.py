"""Orchestrator for coordinating agent phases."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from anthropic import AsyncAnthropic

from .agents.base import AgentContext, AgentResult, ParallelAgentRunner
from .agents.quality.quality_gate import QualityGate, QualityReport, AggregateQualityReport
from .knowledge import KnowledgeGraph, KnowledgeStore
from .mcp.client import MCPClient, MCPOAuthConfig
from .context import FileStore, FileStoreTool
from .auth import TokenCache, AWSSSOAuth
from .tools import ToolRegistry, FileReadTool, FileWriteTool, FileListTool, ShellTool, GitTool
from .tracking import TokenTracker, get_global_tracker
from .utils.logging import get_logger

logger = get_logger("orchestrator")


class PhaseResult:
    """Result from a phase execution."""
    
    def __init__(
        self,
        phase_name: str,
        success: bool,
        agent_results: list[AgentResult],
        duration_seconds: float = 0.0,
    ):
        self.phase_name = phase_name
        self.success = success
        self.agent_results = agent_results
        self.duration_seconds = duration_seconds
    
    @property
    def successful_agents(self) -> int:
        return sum(1 for r in self.agent_results if r.success)
    
    @property
    def failed_agents(self) -> int:
        return sum(1 for r in self.agent_results if not r.success)


class Orchestrator:
    """
    Main orchestrator for the documentation generation pipeline.
    
    Coordinates the execution of agents across five phases:
    1. Discovery - Scan GitHub repos to discover services
    2. Enrichment - Query Confluence/Docs360 for each discovered service
    3. Analysis - Build knowledge graph and infer architecture
    4. Generation - Generate documentation
    5. Quality - Cross-reference and validate
    
    The service-centric approach means we start with repos (source of truth)
    and then enrich with documentation, rather than harvesting everything.
    """
    
    def __init__(
        self,
        config: dict[str, Any],
        output_dir: Path,
        store_dir: Optional[Path] = None,
    ):
        """
        Initialize the orchestrator.
        
        Args:
            config: Configuration dictionary
            output_dir: Directory for generated documentation
            store_dir: Directory for persistent storage
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.store_dir = store_dir or Path("./store")
        
        # Initialize components
        self.store = KnowledgeStore(self.store_dir)
        
        # Initialize authentication (for AWS Bedrock)
        self.token_cache = TokenCache()
        self.aws_sso: Optional[AWSSSOAuth] = None
        self._setup_auth(config.get("auth", {}))
        
        # Configure MCP client for Natterbox server (SSE transport with OAuth)
        mcp_config = config.get("mcp", {})
        oauth_config = mcp_config.get("oauth", {})
        
        self.mcp_client = MCPClient(
            server_url=mcp_config.get("url", "https://avatar.natterbox-dev03.net/mcp/sse"),
            timeout=mcp_config.get("timeout", 60),
            oauth_config=MCPOAuthConfig(
                authorization_url=oauth_config.get("authorization_url", "https://avatar.natterbox-dev03.net/mcp/authorize"),
                token_url=oauth_config.get("token_url", "https://avatar.natterbox-dev03.net/mcp/token"),
                client_id=oauth_config.get("client_id", "doc-agent"),
                scopes=oauth_config.get("scopes", []),
            ),
        )
        
        # Initialize file store for context management (session-only)
        self.file_store = FileStore(threshold_bytes=1024)  # 1KB threshold
        self.file_store_tool = FileStoreTool(self.file_store)
        
        # Initialize local tool registry
        workspace_root = Path.cwd()  # Use current directory as workspace
        self.tool_registry = ToolRegistry(
            workspace_root=workspace_root,
            output_dir=self.output_dir,
            allowed_paths=[workspace_root, self.output_dir, self.store_dir],
        )
        self._setup_tools()
        
        # Anthropic client for summary generation
        self.anthropic: Optional[AsyncAnthropic] = None
        
        # Phase results
        self.phase_results: dict[str, PhaseResult] = {}
        
        # Token tracking
        self.token_tracker = get_global_tracker()
        
        # Quality gate
        self.quality_gate = QualityGate(strict_mode=config.get("quality", {}).get("strict_mode", True))
        self.quality_reports: list[QualityReport] = []
        self.aggregate_quality_report: Optional[AggregateQualityReport] = None
    
    def _setup_auth(self, auth_config: dict[str, Any]) -> None:
        """Set up authentication from config."""
        # AWS SSO for Bedrock
        aws_config = auth_config.get("aws", {})
        if aws_config.get("enabled"):
            self.aws_sso = AWSSSOAuth(
                profile=aws_config.get("profile", "default"),
                region=aws_config.get("region", "us-east-1"),
                token_cache=self.token_cache,
                use_aws_vault=aws_config.get("use_aws_vault", True),
            )
            logger.info(f"AWS SSO configured for profile: {aws_config.get('profile', 'default')}")
    
    def _setup_tools(self) -> None:
        """Set up local tools for agents."""
        # Register file tools
        self.tool_registry.register(FileReadTool(self.tool_registry))
        self.tool_registry.register(FileWriteTool(self.tool_registry))
        self.tool_registry.register(FileListTool(self.tool_registry))
        
        # Register shell tools
        self.tool_registry.register(ShellTool(self.tool_registry))
        self.tool_registry.register(GitTool(self.tool_registry))
        
        logger.info(f"Registered {len(self.tool_registry.list_tools())} local tools: {self.tool_registry.list_tools()}")
        
    async def initialize(self) -> None:
        """Initialize the orchestrator and load existing state."""
        logger.info("Initializing orchestrator")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing knowledge
        await self.store.load()
        
        # Validate/refresh authentication
        await self._ensure_authentication()
        
        # Connect to MCP (will use OAuth tokens from manager)
        await self.mcp_client.connect()
        
        # Initialize Anthropic client and set up summary generator
        await self._setup_anthropic_client()
        self.file_store.set_summary_generator(self._generate_summary)
        
        logger.info(f"Initialized with {self.store.graph.node_count} existing entities")
    
    async def _ensure_authentication(self) -> None:
        """Ensure all required authentication is in place."""
        # MCP server handles its own OAuth for GitHub/Confluence/Jira
        # We only need to ensure AWS SSO is valid for Bedrock
        
        if self.aws_sso:
            try:
                creds = await self.aws_sso.get_credentials()
                if creds:
                    logger.info(f"AWS SSO credentials valid until {creds.expiration}")
            except Exception as e:
                logger.warning(f"AWS SSO credentials not available: {e}")
                logger.info("Run 'aws-vault login sso-dev03-admin' to authenticate.")
    
    async def _setup_anthropic_client(self) -> None:
        """Set up the Anthropic client, using Bedrock if configured."""
        llm_config = self.config.get("llm", {})
        provider = llm_config.get("provider", "anthropic")
        
        if provider == "bedrock" and self.aws_sso:
            # Use Anthropic via AWS Bedrock
            try:
                creds = await self.aws_sso.get_credentials()
                if creds:
                    from anthropic import AsyncAnthropicBedrock
                    self.anthropic = AsyncAnthropicBedrock(
                        aws_access_key=creds.access_key_id,
                        aws_secret_key=creds.secret_access_key,
                        aws_session_token=creds.session_token,
                        aws_region=creds.region,
                    )
                    logger.info(f"Using Anthropic via AWS Bedrock in {creds.region}")
                    return
            except Exception as e:
                logger.warning(f"Failed to initialize Bedrock client: {e}")
                logger.info("Falling back to direct Anthropic API")
        
        # Default: direct Anthropic API
        self.anthropic = AsyncAnthropic()
    
    async def _generate_summary(self, content: str) -> str:
        """
        Generate an AI summary of content for the file store.
        
        Args:
            content: The content to summarize
            
        Returns:
            A concise summary
        """
        if not self.anthropic:
            return ""
        
        # Truncate very long content for summary generation
        content_for_summary = content[:8000] if len(content) > 8000 else content
        
        try:
            llm_config = self.config.get("llm", {})
            model = llm_config.get("model", "claude-sonnet-4-20250514")
            
            response = await self.anthropic.messages.create(
                model=model,
                max_tokens=200,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": f"Summarize this content in 1-2 sentences, focusing on what it contains and its key information:\n\n{content_for_summary}"
                }],
            )
            
            # Track token usage
            if self.token_tracker and hasattr(response, "usage"):
                self.token_tracker.record(
                    response, 
                    operation="generate_summary",
                )
            
            if response.content and len(response.content) > 0:
                return response.content[0].text
            return ""
            
        except Exception as e:
            logger.warning(f"Failed to generate summary: {e}")
            return ""
    
    async def shutdown(self) -> None:
        """Shutdown the orchestrator and save state."""
        logger.info("Shutting down orchestrator")
        
        # Print final reports
        self._print_final_reports()
        
        # Save knowledge graph
        await self.store.save()
        
        # Disconnect from MCP
        await self.mcp_client.disconnect()
        
        # Clear file store (session-only)
        file_store_stats = self.file_store.get_stats()
        logger.info(f"Clearing file store: {file_store_stats['file_count']} files, {file_store_stats['total_size_bytes']} bytes")
        self.file_store.clear()
    
    def _print_final_reports(self) -> None:
        """Print final quality and token usage reports."""
        # Print quality report if available
        if self.aggregate_quality_report:
            print(self.quality_gate.print_aggregate_report(self.aggregate_quality_report))
        elif self.quality_reports:
            for report in self.quality_reports:
                print(self.quality_gate.print_report(report))
        
        # Print token usage report
        if self.token_tracker:
            self.token_tracker.print_summary()
            
            # Export to file for analysis
            try:
                usage_report_path = self.output_dir / "token_usage.json"
                self.token_tracker.export_to_json(usage_report_path)
                logger.info(f"Token usage exported to {usage_report_path}")
            except Exception as e:
                logger.warning(f"Failed to export token usage: {e}")
    
    def create_context(self, dry_run: bool = False, verbose: bool = False) -> AgentContext:
        """Create an agent context with current state."""
        return AgentContext(
            knowledge_graph=self.store.graph,
            store=self.store,
            mcp_client=self.mcp_client,
            file_store=self.file_store,
            output_dir=self.output_dir,
            config=self.config,
            anthropic_client=self.anthropic,
            tool_registry=self.tool_registry,
            dry_run=dry_run,
            verbose=verbose,
            token_tracker=self.token_tracker,
        )
    
    async def run_discovery_phase(self, context: AgentContext, use_local_repos: bool = True) -> PhaseResult:
        """
        Run the discovery phase.
        
        Service-centric approach: GitHub repos are the source of truth.
        We discover services from repos, then enrich with docs later.
        
        Agents:
        - RepositoryScannerAgent: Discover services from GitHub repos
        - LocalCodeAnalyzer/CodeAnalyzerAgent: Deep analysis of code for APIs/schemas
        
        Args:
            use_local_repos: If True, use local clones for code analysis (avoids rate limits)
        """
        from .agents.discovery import (
            RepositoryScannerAgent,
            CodeAnalyzerAgent,
        )
        
        logger.info("Starting discovery phase (service-centric)")
        start_time = datetime.utcnow()
        
        # Phase 1: Scan GitHub repos to discover services
        repo_scanner = RepositoryScannerAgent(context)
        repo_result = await repo_scanner.execute()
        
        # Phase 2: Deep code analysis (extracts GraphQL schemas, OpenAPI specs, routes)
        logger.info("Starting deep code analysis")
        
        # Check if we should use local clones
        repos_dir = self.store_dir.parent / "repos"
        if use_local_repos and repos_dir.exists():
            from .agents.discovery.local_code_analyzer import LocalCodeAnalyzer
            logger.info("Using local repository clones for code analysis (no API rate limits)")
            code_analyzer = LocalCodeAnalyzer(context, repos_dir)
        else:
            if use_local_repos:
                logger.warning("Local repos not found, falling back to API-based analysis")
            code_analyzer = CodeAnalyzerAgent(context)
        
        code_result = await code_analyzer.execute()
        
        results = [repo_result, code_result]
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        success = all(r.success for r in results)
        
        phase_result = PhaseResult(
            phase_name="discovery",
            success=success,
            agent_results=results,
            duration_seconds=duration,
        )
        
        self.phase_results["discovery"] = phase_result
        logger.info(
            f"Discovery phase completed in {duration:.2f}s "
            f"({phase_result.successful_agents}/{len(results)} agents succeeded)"
        )
        
        return phase_result
    
    async def run_enrichment_phase(self, context: AgentContext) -> PhaseResult:
        """
        Run the enrichment phase.
        
        For each discovered service, query Confluence and Docs360 for
        relevant documentation. This is more efficient than harvesting
        all pages and produces better correlations.
        """
        from .agents.enrichment import (
            ConfluenceEnricherAgent,
            Docs360EnricherAgent,
        )
        
        logger.info("Starting enrichment phase (service-centric queries)")
        start_time = datetime.utcnow()
        
        # Run enrichment agents in parallel
        # Each agent iterates over discovered services and queries for docs
        agents = [
            ConfluenceEnricherAgent(context),
            Docs360EnricherAgent(context),
        ]
        
        parallelism = self.config.get("agents", {}).get("enrichment", {}).get("parallelism", 5)
        runner = ParallelAgentRunner(max_concurrency=parallelism)
        results = await runner.run_agents(agents)
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        success = all(r.success for r in results)
        
        phase_result = PhaseResult(
            phase_name="enrichment",
            success=success,
            agent_results=results,
            duration_seconds=duration,
        )
        
        self.phase_results["enrichment"] = phase_result
        logger.info(
            f"Enrichment phase completed in {duration:.2f}s "
            f"({phase_result.successful_agents}/{len(agents)} agents succeeded)"
        )
        
        return phase_result
    
    async def run_analysis_phase(self, context: AgentContext) -> PhaseResult:
        """
        Run the analysis phase.
        
        Agents analyze discovered data to build the knowledge graph
        and infer architecture.
        """
        from .agents.analysis import (
            ArchitectureInferenceAgent,
            DomainMapperAgent,
        )
        
        logger.info("Starting analysis phase")
        start_time = datetime.utcnow()
        
        # Run architecture inference first, then domain mapping
        agents = [
            ArchitectureInferenceAgent(context),
            DomainMapperAgent(context),
        ]
        
        # Run sequentially for analysis (order matters)
        results = []
        for agent in agents:
            result = await agent.execute()
            results.append(result)
            if not result.success:
                logger.warning(f"Analysis agent {agent.name} failed, continuing...")
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        success = all(r.success for r in results)
        
        phase_result = PhaseResult(
            phase_name="analysis",
            success=success,
            agent_results=results,
            duration_seconds=duration,
        )
        
        self.phase_results["analysis"] = phase_result
        logger.info(
            f"Analysis phase completed in {duration:.2f}s "
            f"({phase_result.successful_agents}/{len(agents)} agents succeeded)"
        )
        
        return phase_result
    
    async def run_generation_phase(
        self,
        context: AgentContext,
        services: Optional[list[str]] = None,
    ) -> PhaseResult:
        """
        Run the generation phase.
        
        Agents generate documentation from the knowledge graph.
        
        Args:
            context: Agent context
            services: Optional list of specific services to generate docs for
        """
        from .agents.generation import (
            OverviewWriterAgent,
            TechnicalWriterAgent,
            APIDocumenterAgent,
            SchemaDocumenterAgent,
            RepositoryDocumenterAgent,
            StrategyDocumenterAgent,
        )
        
        logger.info("Starting generation phase")
        start_time = datetime.utcnow()
        
        # Get services to document
        if services:
            # Flexible matching: check if any filter term is contained in ID or name
            def matches_filter(service):
                for term in services:
                    term_lower = term.lower()
                    if (term_lower in service.id.lower() or 
                        term_lower in service.name.lower() or
                        service.id == f"service:{term}" or
                        service.id == term):
                        return True
                return False
            
            target_services = [
                s for s in self.store.graph.get_services()
                if matches_filter(s)
            ]
        else:
            target_services = self.store.graph.get_services()
        
        logger.info(f"Generating documentation for {len(target_services)} services")
        
        # Create generation agents
        agents = [
            OverviewWriterAgent(context),  # High-level docs
            RepositoryDocumenterAgent(context),  # All repos with drill-down
        ]
        
        # Add per-service agents
        for service in target_services:
            agents.extend([
                TechnicalWriterAgent(context, service_id=service.id),
                APIDocumenterAgent(context, service_id=service.id),
                SchemaDocumenterAgent(context, service_id=service.id),
                # NEW: Type-aware strategy documenter for enhanced docs
                StrategyDocumenterAgent(context, service_id=service.id),
            ])
        
        # Run in parallel with higher concurrency
        parallelism = self.config.get("agents", {}).get("generation", {}).get("parallelism", 10)
        runner = ParallelAgentRunner(max_concurrency=parallelism)
        results = await runner.run_agents(agents)
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        success = all(r.success for r in results)
        
        phase_result = PhaseResult(
            phase_name="generation",
            success=success,
            agent_results=results,
            duration_seconds=duration,
        )
        
        self.phase_results["generation"] = phase_result
        logger.info(
            f"Generation phase completed in {duration:.2f}s "
            f"({phase_result.successful_agents}/{len(agents)} agents succeeded)"
        )
        
        return phase_result
    
    async def run_quality_phase(self, context: AgentContext) -> PhaseResult:
        """
        Run the quality phase.
        
        Agents cross-reference, index, and validate documentation.
        """
        from .agents.quality import (
            CrossReferenceAgent,
            IndexGeneratorAgent,
            QualityCheckerAgent,
        )
        
        logger.info("Starting quality phase")
        start_time = datetime.utcnow()
        
        # Run sequentially: cross-ref -> index -> quality check
        agents = [
            CrossReferenceAgent(context),
            IndexGeneratorAgent(context),
            QualityCheckerAgent(context),
        ]
        
        results = []
        for agent in agents:
            result = await agent.execute()
            results.append(result)
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        success = all(r.success for r in results)
        
        phase_result = PhaseResult(
            phase_name="quality",
            success=success,
            agent_results=results,
            duration_seconds=duration,
        )
        
        self.phase_results["quality"] = phase_result
        logger.info(
            f"Quality phase completed in {duration:.2f}s "
            f"({phase_result.successful_agents}/{len(agents)} agents succeeded)"
        )
        
        return phase_result
    
    async def run_full_pipeline(
        self,
        skip_discovery: bool = False,
        skip_enrichment: bool = False,
        skip_analysis: bool = False,
        skip_generation: bool = False,
        skip_quality: bool = False,
        services: Optional[list[str]] = None,
        dry_run: bool = False,
        verbose: bool = False,
        use_local_repos: bool = True,
    ) -> dict[str, PhaseResult]:
        """
        Run the full documentation pipeline.
        
        Phases:
        1. Discovery - Scan GitHub repos to discover services
        2. Enrichment - Query Confluence/Docs360 for each service
        3. Analysis - Build knowledge graph and infer architecture
        4. Generation - Generate documentation
        5. Quality - Cross-reference and validate
        
        Args:
            skip_discovery: Skip the discovery phase
            skip_enrichment: Skip the enrichment phase
            skip_analysis: Skip the analysis phase
            skip_generation: Skip the generation phase
            skip_quality: Skip the quality phase
            services: Optional list of specific services
            dry_run: Don't write files, just simulate
            verbose: Enable verbose logging
            use_local_repos: Use local repo clones for code analysis (avoids rate limits)
            
        Returns:
            Dictionary of phase results
        """
        await self.initialize()
        
        try:
            context = self.create_context(dry_run=dry_run, verbose=verbose)
            
            if not skip_discovery:
                await self.run_discovery_phase(context, use_local_repos=use_local_repos)
                await self.store.save()  # Save after discovery
            
            if not skip_enrichment:
                await self.run_enrichment_phase(context)
                await self.store.save()  # Save after enrichment
            
            if not skip_analysis:
                await self.run_analysis_phase(context)
                await self.store.save()  # Save after analysis
            
            if not skip_generation:
                await self.run_generation_phase(context, services=services)
            
            if not skip_quality:
                await self.run_quality_phase(context)
                
                # Run enhanced quality gate evaluation
                await self._run_quality_gate_evaluation(context, services=services)
            
            return self.phase_results
            
        finally:
            await self.shutdown()
    
    async def _run_quality_gate_evaluation(
        self,
        context: AgentContext,
        services: Optional[list[str]] = None,
    ) -> None:
        """
        Run the enhanced quality gate evaluation on generated documentation.
        
        This provides detailed quality scoring, issue tracking, and recommendations.
        """
        logger.info("Running quality gate evaluation")
        
        from .documentation.strategies.base import DocumentSet, GeneratedDocument
        from .analyzers.repo_type_detector import RepoType, detect_repo_type
        
        # Build document sets from generated documentation
        doc_sets = []
        
        # Get services to evaluate
        if services:
            def matches_filter(service):
                for term in services:
                    term_lower = term.lower()
                    if (term_lower in service.id.lower() or 
                        term_lower in service.name.lower()):
                        return True
                return False
            target_services = [s for s in self.store.graph.get_services() if matches_filter(s)]
        else:
            target_services = self.store.graph.get_services()
        
        for service in target_services:
            service_dir = self.output_dir / "services" / service.name
            if not service_dir.exists():
                continue
            
            # Detect repo type if possible
            repo_type = RepoType.UNKNOWN
            if service.metadata and service.metadata.get("repository"):
                repos_dir = self.store_dir.parent / "repos"
                for org in ["redmatter", "natterbox", "SemiConscious"]:
                    repo_path = repos_dir / org / service.metadata["repository"]
                    if repo_path.exists():
                        result = detect_repo_type(repo_path)
                        repo_type = result.primary_type
                        break
            
            # Build document set from generated files
            doc_set = DocumentSet(
                repo_name=service.name,
                repo_type=repo_type,
            )
            
            # Find all markdown files in service directory
            for md_file in service_dir.rglob("*.md"):
                try:
                    content = md_file.read_text()
                    rel_path = md_file.relative_to(service_dir)
                    doc = GeneratedDocument(
                        path=md_file,
                        title=str(rel_path),
                        content=content,
                    )
                    doc_set.add_document(doc)
                except Exception as e:
                    logger.warning(f"Failed to read {md_file}: {e}")
            
            if doc_set.documents:
                doc_sets.append(doc_set)
        
        # Evaluate all document sets
        if doc_sets:
            self.aggregate_quality_report = await self.quality_gate.evaluate_multiple(doc_sets)
            
            # Store individual reports
            self.quality_reports = self.aggregate_quality_report.reports
            
            # Log summary
            passing = self.aggregate_quality_report.passing_repos
            total = self.aggregate_quality_report.total_repos
            avg_score = self.aggregate_quality_report.average_score * 100
            
            logger.info(
                f"Quality gate evaluation complete: {passing}/{total} repos passing, "
                f"average score {avg_score:.1f}%"
            )
            
            # List repos needing attention
            for report in self.aggregate_quality_report.repos_needing_work[:5]:
                logger.warning(
                    f"  ⚠️  {report.repo_name}: {report.overall_score * 100:.1f}% "
                    f"({len(report.critical_issues)} critical issues)"
                )
        else:
            logger.warning("No documentation found to evaluate")
    
    def get_status(self) -> dict[str, Any]:
        """Get current status of the orchestrator."""
        status = {
            "knowledge_graph": self.store.graph.get_statistics(),
            "documents": {
                "total": len(self.store.get_all_document_paths()),
            },
            "file_store": self.file_store.get_stats(),
            "phases": {
                name: {
                    "success": result.success,
                    "agents_succeeded": result.successful_agents,
                    "agents_failed": result.failed_agents,
                    "duration_seconds": result.duration_seconds,
                }
                for name, result in self.phase_results.items()
            },
        }
        
        # Add token usage stats
        if self.token_tracker:
            input_tokens, output_tokens = self.token_tracker.get_current_tokens()
            status["token_usage"] = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "estimated_cost_usd": round(self.token_tracker.get_current_cost(), 4),
            }
        
        # Add quality stats
        if self.aggregate_quality_report:
            status["quality"] = self.aggregate_quality_report.to_dict()
        elif self.quality_reports:
            status["quality"] = {
                "reports_count": len(self.quality_reports),
                "passing": sum(1 for r in self.quality_reports if r.passing),
                "failing": sum(1 for r in self.quality_reports if not r.passing),
            }
        
        return status
    
    def get_file_store_tool(self) -> FileStoreTool:
        """Get the file store tool for LLM tool use."""
        return self.file_store_tool
