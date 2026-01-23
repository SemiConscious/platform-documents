"""
Strategy-based documentation generator.

Uses type-aware documentation strategies to generate comprehensive,
detailed documentation tailored to each repository type.
"""

import asyncio
from pathlib import Path
from typing import Any, Optional

from ..base import BaseAgent, AgentContext, AgentResult
from ...analyzers import detect_repo_type, RepoType
from ...analyzers.integration import analyze_service_repository
from ...documentation.strategies import StrategyFactory, DocumentSet
from ...llm import ModelSelector
from ...utils.logging import get_logger

logger = get_logger("doc-agent.agents.strategy_documenter")


class StrategyDocumenterAgent(BaseAgent):
    """
    Documentation agent that uses type-specific strategies.
    
    This agent:
    1. Detects the repository type (API, Terraform, Lambda, etc.)
    2. Selects the appropriate documentation strategy
    3. Generates comprehensive, detailed documentation
    4. Evaluates quality against strategy-specific criteria
    """
    
    name = "strategy_documenter"
    description = "Type-aware documentation generator using strategies"
    version = "1.0.0"
    
    def __init__(
        self,
        context: AgentContext,
        service_id: Optional[str] = None,
        repo_path: Optional[Path] = None,
        profile: Optional[str] = None,
    ):
        super().__init__(context)
        self.service_id = service_id
        self.repo_path = repo_path
        
        # Create model selector for tiered LLM usage
        self.model_selector = ModelSelector(
            config=context.config,
            profile_name=profile,
        )
        
        self.factory = StrategyFactory(
            output_dir=context.output_dir,
            llm_client=context.anthropic_client,
            token_tracker=context.token_tracker,
            config=context.config,
            model_selector=self.model_selector,
        )
        
        logger.info(f"Using model profile: {self.model_selector.profile.name}")
        
    async def run(self) -> AgentResult[dict[str, Any]]:
        """Generate documentation using type-specific strategy."""
        try:
            # Get the service from knowledge graph
            service = None
            if self.service_id:
                service = self.context.knowledge_graph.get_entity(self.service_id)
                if not service:
                    return AgentResult(
                        success=False,
                        error=f"Service not found: {self.service_id}"
                    )
            
            # Find the repository path
            repo_path = self._find_repo_path(service)
            if not repo_path:
                logger.warning(f"No local repository found for {self.service_id}")
                return AgentResult(
                    success=True,
                    data={"skipped": True, "reason": "No local repository"},
                )
            
            # Detect repository type
            repo_type_result = detect_repo_type(repo_path)
            logger.info(
                f"Detected repo type for {repo_path.name}: "
                f"{repo_type_result.primary_type.value} "
                f"(confidence: {repo_type_result.confidence:.2f})"
            )
            
            # Get appropriate strategy
            strategy = self.factory.get_strategy(repo_type_result.primary_type)
            if not strategy:
                logger.warning(
                    f"No strategy for {repo_type_result.primary_type.value}, "
                    f"using generic"
                )
                strategy = self.factory.get_strategy(RepoType.UNKNOWN)
            
            # Run code analysis
            analysis = await self._analyze_repository(repo_path, service)
            
            # Get GitHub URL
            github_url = self._get_github_url(service)
            
            # Get service name
            service_name = service.name if service else repo_path.name
            
            # Get existing documentation from knowledge graph
            existing_docs = self._get_existing_docs(service)
            
            # Generate documentation using strategy
            logger.info(
                f"Generating {strategy.name} documentation for {service_name}"
            )
            doc_set = await strategy.generate(
                repo_path=repo_path,
                analysis=analysis,
                service_name=service_name,
                github_url=github_url,
                existing_docs=existing_docs,
            )
            
            # Write documents to output directory
            docs_written = await self._write_documents(doc_set, service_name)
            
            # Evaluate quality
            quality_scores = await strategy.evaluate_quality(doc_set)
            avg_score = sum(s.score for s in quality_scores) / len(quality_scores) if quality_scores else 0
            
            return AgentResult(
                success=True,
                data={
                    "service": service_name,
                    "repo_type": repo_type_result.primary_type.value,
                    "strategy": strategy.name,
                    "documents_generated": len(doc_set.documents),
                    "documents_written": docs_written,
                    "quality_score": round(avg_score, 2),
                    "quality_details": [
                        {"criterion": s.criterion, "score": s.score, "passed": s.passed}
                        for s in quality_scores
                    ],
                },
            )
            
        except Exception as e:
            logger.exception(f"Strategy documenter failed: {e}")
            return AgentResult(success=False, error=str(e))
    
    def _find_repo_path(self, service) -> Optional[Path]:
        """Find the local repository path for a service."""
        repos_dir = self.context.output_dir.parent / "repos"
        
        if self.repo_path and self.repo_path.exists():
            return self.repo_path
        
        if not repos_dir.exists():
            logger.warning(f"Repos directory does not exist: {repos_dir}")
            return None
        
        # Try to find repo by service metadata
        if service:
            repo_attr = getattr(service, 'repository', None) or ""
            
            # Handle org/repo format (e.g., "redmatter/platform-api")
            if "/" in repo_attr:
                org, repo_name = repo_attr.split("/", 1)
                potential_path = repos_dir / org / repo_name
                if potential_path.exists():
                    logger.debug(f"Found repo at {potential_path}")
                    return potential_path
            
            # Fall back to checking various orgs with just repo name
            repo_name = repo_attr or service.name
            # Also try common slug transformations
            name_variants = [
                repo_name,
                repo_name.lower().replace(" ", "-").replace("_", "-"),
                service.name.lower().replace(" ", "-").replace("_", "-"),
                service.id.replace("service:", ""),
            ]
            
            org = service.metadata.get("organization", "redmatter") if service.metadata else "redmatter"
            
            # Try various organization paths with all name variants
            for org_name in [org, "redmatter", "natterbox"]:
                for name in name_variants:
                    potential_path = repos_dir / org_name / name
                    if potential_path.exists():
                        logger.debug(f"Found repo at {potential_path}")
                        return potential_path
        
        logger.warning(f"No repository found for service {service.id if service else 'unknown'}")
        return None
    
    async def _analyze_repository(self, repo_path: Path, service) -> Any:
        """Run code analysis on the repository."""
        try:
            repos_dir = repo_path.parent.parent
            repo_name = repo_path.name
            org = repo_path.parent.name
            
            analysis = analyze_service_repository(
                repos_dir=repos_dir,
                service_name=service.name if service else repo_name,
                repository=repo_name,
                organizations=[org, "redmatter", "natterbox"],
            )
            return analysis
        except Exception as e:
            logger.warning(f"Code analysis failed: {e}")
            return None
    
    def _get_github_url(self, service) -> Optional[str]:
        """Get GitHub URL for the service."""
        if not service:
            return None
        
        # Try metadata
        if service.metadata:
            if "github_url" in service.metadata:
                return service.metadata["github_url"]
            if "repository" in service.metadata:
                org = service.metadata.get("organization", "redmatter")
                return f"https://github.com/{org}/{service.metadata['repository']}"
        
        # Try repository attribute
        if hasattr(service, 'repository') and service.repository:
            return f"https://github.com/redmatter/{service.repository}"
        
        return None
    
    def _get_existing_docs(self, service) -> dict[str, str]:
        """Get existing documentation from knowledge graph."""
        existing = {}
        
        if not service:
            return existing
        
        # Get related documents from knowledge graph
        relations = self.context.knowledge_graph.get_relations(
            source_id=service.id,
            relation_type="documents"
        )
        
        for rel in relations:
            doc = self.context.knowledge_graph.get_entity(rel.target_id)
            if doc and hasattr(doc, 'content'):
                existing[doc.name] = doc.content
        
        return existing
    
    async def _write_documents(self, doc_set: DocumentSet, service_name: str) -> int:
        """Write generated documents to output directory."""
        # Create service-specific output directory
        service_slug = service_name.lower().replace(" ", "-").replace("_", "-")
        service_dir = self.context.output_dir / "services" / service_slug
        service_dir.mkdir(parents=True, exist_ok=True)
        
        written = 0
        for doc in doc_set.documents:
            try:
                # Determine output path
                # doc.path may be either a Path object or a string
                doc_path_raw = doc.path if isinstance(doc.path, Path) else Path(doc.path)
                
                # If path is already absolute, use it directly
                if doc_path_raw.is_absolute():
                    doc_path = doc_path_raw
                elif "/" in str(doc.path):
                    # Nested path like "api/endpoints.md"
                    doc_path = service_dir / doc_path_raw
                else:
                    doc_path = service_dir / doc_path_raw
                
                # Ensure parent directory exists
                doc_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write content
                doc_path.write_text(doc.content)
                written += 1
                logger.debug(f"Wrote: {doc_path}")
                
            except Exception as e:
                logger.warning(f"Failed to write {doc.path}: {e}")
        
        logger.info(f"Wrote {written} documents to {service_dir}")
        return written
