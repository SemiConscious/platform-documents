"""Orchestrator for coordinating agent phases."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .agents.base import AgentContext, AgentResult, ParallelAgentRunner
from .knowledge import KnowledgeGraph, KnowledgeStore
from .mcp import MCPClient
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
        self.mcp_client = MCPClient(
            server_name=config.get("mcp", {}).get("server", "natterbox"),
            timeout=config.get("mcp", {}).get("timeout", 30),
        )
        
        # Phase results
        self.phase_results: dict[str, PhaseResult] = {}
        
    async def initialize(self) -> None:
        """Initialize the orchestrator and load existing state."""
        logger.info("Initializing orchestrator")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing knowledge
        await self.store.load()
        
        # Connect to MCP
        await self.mcp_client.connect()
        
        logger.info(f"Initialized with {self.store.graph.node_count} existing entities")
    
    async def shutdown(self) -> None:
        """Shutdown the orchestrator and save state."""
        logger.info("Shutting down orchestrator")
        
        # Save knowledge graph
        await self.store.save()
        
        # Disconnect from MCP
        await self.mcp_client.disconnect()
    
    def create_context(self, dry_run: bool = False, verbose: bool = False) -> AgentContext:
        """Create an agent context with current state."""
        return AgentContext(
            knowledge_graph=self.store.graph,
            store=self.store,
            mcp_client=self.mcp_client,
            output_dir=self.output_dir,
            config=self.config,
            dry_run=dry_run,
            verbose=verbose,
        )
    
    async def run_discovery_phase(self, context: AgentContext) -> PhaseResult:
        """
        Run the discovery phase.
        
        Agents scan GitHub, Confluence, and Jira to gather raw data.
        """
        from .agents.discovery import (
            RepositoryScannerAgent,
            ConfluenceHarvesterAgent,
            JiraAnalyzerAgent,
        )
        
        logger.info("Starting discovery phase")
        start_time = datetime.utcnow()
        
        # Create discovery agents
        agents = [
            RepositoryScannerAgent(context),
            ConfluenceHarvesterAgent(context),
            JiraAnalyzerAgent(context),
        ]
        
        # Run in parallel
        parallelism = self.config.get("agents", {}).get("discovery", {}).get("parallelism", 5)
        runner = ParallelAgentRunner(max_concurrency=parallelism)
        results = await runner.run_agents(agents)
        
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
