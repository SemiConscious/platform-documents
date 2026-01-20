"""Base agent class with Claude integration."""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, TypeVar, Generic, Union
from pathlib import Path

from anthropic import AsyncAnthropic

from ..knowledge import KnowledgeGraph, KnowledgeStore
from ..mcp import MCPClient
from ..context import FileStore, FileReference

logger = logging.getLogger("doc-agent.agents.base")

T = TypeVar("T")


@dataclass
class AgentResult(Generic[T]):
    """Result from an agent execution."""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentContext:
    """
    Shared context passed to all agents.
    
    Contains references to shared resources like the knowledge graph,
    MCP client, file store, and configuration.
    """
    knowledge_graph: KnowledgeGraph
    store: KnowledgeStore
    mcp_client: MCPClient
    file_store: FileStore
    output_dir: Path
    config: dict[str, Any]
    
    # Runtime state
    dry_run: bool = False
    verbose: bool = False


class BaseAgent(ABC):
    """
    Base class for all documentation agents.
    
    Provides:
    - Claude API integration for AI-powered processing
    - Access to the shared knowledge graph
    - Structured logging
    - Checkpoint support for incremental runs
    """
    
    # Agent metadata - override in subclasses
    name: str = "base_agent"
    description: str = "Base agent class"
    version: str = "0.1.0"
    
    def __init__(
        self,
        context: AgentContext,
        anthropic_client: Optional[AsyncAnthropic] = None,
    ):
        """
        Initialize the agent.
        
        Args:
            context: Shared agent context
            anthropic_client: Optional pre-configured Anthropic client
        """
        self.context = context
        self.anthropic = anthropic_client or AsyncAnthropic()
        self.logger = logging.getLogger(f"doc-agent.agents.{self.name}")
        
        # Configuration
        self.llm_config = context.config.get("llm", {})
        self.model = self.llm_config.get("model", "claude-sonnet-4-20250514")
        self.max_tokens = self.llm_config.get("max_tokens", 4096)
        self.temperature = self.llm_config.get("temperature", 0.3)
    
    @property
    def graph(self) -> KnowledgeGraph:
        """Access to the knowledge graph."""
        return self.context.knowledge_graph
    
    @property
    def store(self) -> KnowledgeStore:
        """Access to the knowledge store."""
        return self.context.store
    
    @property
    def mcp(self) -> MCPClient:
        """Access to the MCP client."""
        return self.context.mcp_client
    
    @property
    def file_store(self) -> FileStore:
        """Access to the file store for context management."""
        return self.context.file_store
    
    def store_large_content(
        self,
        content: str,
        source: Optional[str] = None,
    ) -> Union[str, FileReference]:
        """
        Store content if it exceeds the threshold.
        
        Use this to wrap large tool responses or intermediate results
        to keep the conversation context manageable.
        
        Args:
            content: The content to potentially store
            source: Optional source identifier
            
        Returns:
            Original content if small, FileReference if stored
        """
        return self.file_store.store_if_large(
            content,
            source=source or self.name,
        )
    
    async def store_large_content_with_summary(
        self,
        content: str,
        source: Optional[str] = None,
    ) -> Union[str, FileReference]:
        """
        Store content with AI-generated summary if it exceeds threshold.
        
        Args:
            content: The content to potentially store
            source: Optional source identifier
            
        Returns:
            Original content if small, FileReference with summary if stored
        """
        return await self.file_store.store_if_large_async(
            content,
            source=source or self.name,
            generate_summary=True,
        )
    
    def format_for_context(
        self,
        data: Any,
        source: Optional[str] = None,
    ) -> str:
        """
        Format data for inclusion in conversation context.
        
        Automatically stores large content and returns a reference.
        
        Args:
            data: Data to format (will be JSON-serialized if not string)
            source: Optional source identifier
            
        Returns:
            String suitable for conversation context
        """
        if isinstance(data, str):
            content = data
        else:
            content = json.dumps(data, indent=2, default=str)
        
        result = self.store_large_content(content, source)
        
        if isinstance(result, FileReference):
            return result.to_context_string()
        return result
    
    @abstractmethod
    async def run(self) -> AgentResult:
        """
        Execute the agent's main logic.
        
        Returns:
            AgentResult with the outcome
        """
        pass
    
    async def call_claude(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Call Claude API with the given prompts.
        
        Args:
            system_prompt: System instructions for Claude
            user_message: User message/query
            max_tokens: Override max tokens
            temperature: Override temperature
            
        Returns:
            Claude's response text
        """
        try:
            response = await self.anthropic.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ],
            )
            
            # Extract text from response
            if response.content and len(response.content) > 0:
                return response.content[0].text
            return ""
            
        except Exception as e:
            self.logger.error(f"Claude API call failed: {e}")
            raise
    
    async def call_claude_with_context(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Call Claude with a conversation history.
        
        Args:
            system_prompt: System instructions
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Override max tokens
            
        Returns:
            Claude's response text
        """
        try:
            response = await self.anthropic.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=messages,
            )
            
            if response.content and len(response.content) > 0:
                return response.content[0].text
            return ""
            
        except Exception as e:
            self.logger.error(f"Claude API call failed: {e}")
            raise
    
    async def save_checkpoint(self, data: dict[str, Any]) -> None:
        """Save agent checkpoint for incremental runs."""
        await self.store.save_checkpoint(self.name, data)
        self.logger.debug(f"Saved checkpoint for {self.name}")
    
    async def load_checkpoint(self) -> Optional[dict[str, Any]]:
        """Load agent checkpoint from previous run."""
        return await self.store.load_checkpoint(self.name)
    
    async def clear_checkpoint(self) -> None:
        """Clear agent checkpoint."""
        await self.store.clear_checkpoint(self.name)
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        
        Override in subclasses to provide agent-specific prompts.
        """
        return f"""You are a documentation agent named {self.name}.
Your role is: {self.description}

You are part of a multi-agent system documenting a software platform.
Be precise, technical, and thorough in your analysis.
Focus on extracting accurate information that will be useful for documentation."""
    
    async def execute(self) -> AgentResult:
        """
        Execute the agent with timing and error handling.
        
        This is the public entry point that wraps run() with
        common functionality.
        """
        start_time = datetime.utcnow()
        self.logger.info(f"Starting agent: {self.name}")
        
        try:
            result = await self.run()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            result.duration_seconds = duration
            
            if result.success:
                self.logger.info(f"Agent {self.name} completed in {duration:.2f}s")
            else:
                self.logger.error(f"Agent {self.name} failed: {result.error}")
            
            return result
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.exception(f"Agent {self.name} raised exception")
            
            return AgentResult(
                success=False,
                error=str(e),
                duration_seconds=duration,
            )
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"


class ParallelAgentRunner:
    """
    Utility for running multiple agents in parallel.
    """
    
    def __init__(self, max_concurrency: int = 5):
        """
        Initialize the parallel runner.
        
        Args:
            max_concurrency: Maximum number of concurrent agents
        """
        self.max_concurrency = max_concurrency
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.logger = logging.getLogger("doc-agent.agents.parallel")
    
    async def run_agents(
        self,
        agents: list[BaseAgent],
    ) -> list[AgentResult]:
        """
        Run multiple agents in parallel with concurrency control.
        
        Args:
            agents: List of agents to run
            
        Returns:
            List of results in the same order as agents
        """
        async def run_with_semaphore(agent: BaseAgent) -> AgentResult:
            async with self.semaphore:
                return await agent.execute()
        
        self.logger.info(f"Running {len(agents)} agents with max concurrency {self.max_concurrency}")
        
        tasks = [run_with_semaphore(agent) for agent in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to AgentResults
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(AgentResult(
                    success=False,
                    error=str(result),
                ))
            else:
                processed_results.append(result)
        
        # Log summary
        successes = sum(1 for r in processed_results if r.success)
        self.logger.info(f"Completed: {successes}/{len(agents)} agents succeeded")
        
        return processed_results
