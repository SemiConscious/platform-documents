"""Orchestrator for coordinating agent phases."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from anthropic import AsyncAnthropic

from .agents.base import AgentContext, AgentResult, ParallelAgentRunner
from .knowledge import KnowledgeGraph, KnowledgeStore
from .mcp.client import MCPClient, MCPOAuthConfig
from .context import FileStore, FileStoreTool
from .auth import TokenCache, AWSSSOAuth
from .tools import ToolRegistry, FileReadTool, FileWriteTool, FileListTool, ShellTool, GitTool
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
    
    Coordinates the execution of agents across four phases:
    1. Discovery - Gather data from sources
    2. Analysis - Build knowledge graph and infer architecture
    3. Generation - Generate documentation
    4. Quality - Cross-reference and validate
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
            
            if response.content and len(response.content) > 0:
                return response.content[0].text
            return ""
            
        except Exception as e:
            logger.warning(f"Failed to generate summary: {e}")
            return ""
    
    async def shutdown(self) -> None:
        """Shutdown the orchestrator and save state."""
        logger.info("Shutting down orchestrator")
        
        # Save knowledge graph
        await self.store.save()
        
        # Disconnect from MCP
        await self.mcp_client.disconnect()
        
        # Clear file store (session-only)
        file_store_stats = self.file_store.get_stats()
        logger.info(f"Clearing file store: {file_store_stats['file_count']} files, {file_store_stats['total_size_bytes']} bytes")
        self.file_store.clear()
    
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
        )
    
    async def run_discovery_phase(self, context: AgentContext) -> PhaseResult:
        """
        Run the discovery phase.
        
        Agents scan GitHub, Confluence, and Jira to gather raw data.
        Then deep code analysis extracts actual API and schema details.
        
        Priority: GitHub (authoritative) > Confluence (reference) > Jira (disabled)
        """
        from .agents.discovery import (
            RepositoryScannerAgent,
            ConfluenceHarvesterAgent,
            JiraAnalyzerAgent,
            CodeAnalyzerAgent,
            Docs360HarvesterAgent,
        )
        
        logger.info("Starting discovery phase")
        start_time = datetime.utcnow()
        
        # Phase 1: Scan sources in parallel
        # Priority: GitHub (authoritative) > Docs360 (authoritative public) > Confluence (reference) > Jira (disabled)
        source_agents = [
            RepositoryScannerAgent(context),
            Docs360HarvesterAgent(context),  # Public documentation - high trust
            ConfluenceHarvesterAgent(context),  # Internal docs - reference only
            JiraAnalyzerAgent(context),  # Typically disabled
        ]
        
        parallelism = self.config.get("agents", {}).get("discovery", {}).get("parallelism", 5)
        runner = ParallelAgentRunner(max_concurrency=parallelism)
        source_results = await runner.run_agents(source_agents)
        
        # Phase 2: Deep code analysis (runs after repos are discovered)
        # This extracts GraphQL schemas, OpenAPI specs, and routes from source code
        logger.info("Starting deep code analysis")
        code_analyzer = CodeAnalyzerAgent(context)
        code_result = await code_analyzer.execute()
        
        # Combine results
        results = source_results + [code_result]
        
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
        )
        
        logger.info("Starting generation phase")
        start_time = datetime.utcnow()
        
        # Get services to document
        if services:
            target_services = [
                s for s in self.store.graph.get_services()
                if s.id in services or s.name in services
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
        skip_analysis: bool = False,
        skip_generation: bool = False,
        skip_quality: bool = False,
        services: Optional[list[str]] = None,
        dry_run: bool = False,
        verbose: bool = False,
    ) -> dict[str, PhaseResult]:
        """
        Run the full documentation pipeline.
        
        Args:
            skip_discovery: Skip the discovery phase
            skip_analysis: Skip the analysis phase
            skip_generation: Skip the generation phase
            skip_quality: Skip the quality phase
            services: Optional list of specific services
            dry_run: Don't write files, just simulate
            verbose: Enable verbose logging
            
        Returns:
            Dictionary of phase results
        """
        await self.initialize()
        
        try:
            context = self.create_context(dry_run=dry_run, verbose=verbose)
            
            if not skip_discovery:
                await self.run_discovery_phase(context)
                await self.store.save()  # Save after discovery
            
            if not skip_analysis:
                await self.run_analysis_phase(context)
                await self.store.save()  # Save after analysis
            
            if not skip_generation:
                await self.run_generation_phase(context, services=services)
            
            if not skip_quality:
                await self.run_quality_phase(context)
            
            return self.phase_results
            
        finally:
            await self.shutdown()
    
    def get_status(self) -> dict[str, Any]:
        """Get current status of the orchestrator."""
        return {
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
    
    def get_file_store_tool(self) -> FileStoreTool:
        """Get the file store tool for LLM tool use."""
        return self.file_store_tool
