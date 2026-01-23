"""Agent executor - runs agent conversations with tool use."""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

from anthropic import AsyncAnthropicBedrock

from .models import AgentTask, TaskStatus
from .task_queue import TaskQueue
from .tools import (
    ToolRegistry,
    SpawnAgentTool,
    FileReadTool,
    FileWriteTool,
    FileListTool,
    BashTool,
    ToolResult,
    ResponseCache,
    CacheReadTool,
)
from .prompts import get_master_prompt, get_child_prompt
from .auth import AWSSSOAuth
from .models_config import get_model_config, Provider, ModelConfig
from .openrouter_client import OpenRouterClient

logger = logging.getLogger("doc-spawner.executor")


class AgentExecutor:
    """
    Executes agent tasks with an agentic tool-use loop.
    
    The executor:
    1. Takes a task from the queue
    2. Builds the system prompt and tools for that task
    3. Runs a conversation loop with Claude until completion
    4. Updates the task status in the queue
    """
    
    def __init__(
        self,
        task_queue: TaskQueue,
        config: dict[str, Any],
    ):
        """
        Initialize the executor.
        
        Args:
            task_queue: The task queue for tracking tasks
            config: Configuration dictionary
        """
        self.task_queue = task_queue
        self.config = config
        
        # Paths
        self.output_dir = Path(config.get("output_dir", "./docs")).resolve()
        self.repos_dir = Path(config.get("repos_dir", "./repos")).resolve()
        
        # Limits
        self.max_depth = config.get("max_depth", 5)
        self.max_tasks = config.get("max_tasks", 25)
        self.max_turns = config.get("max_turns", 50)
        self.max_tokens = config.get("max_tokens", 16384)
        
        # Model configuration
        model_name = config.get("model", "opus")
        self.model_config: ModelConfig = get_model_config(model_name)
        self.model = self.model_config.model_id
        self.provider = self.model_config.provider
        
        # Other model settings
        llm_config = config.get("llm", {})
        self.temperature = llm_config.get("temperature", 0.3)
        
        # AWS settings (for Bedrock)
        aws_config = config.get("aws", {})
        self.aws_region = aws_config.get("region", "us-east-1")
        self.aws_profile = aws_config.get("profile", "sso-dev03-admin")
        
        # AWS SSO auth (for Bedrock)
        self._aws_auth = AWSSSOAuth(
            profile=self.aws_profile,
            region=self.aws_region,
        )
        
        # OpenRouter API key (for OpenRouter provider)
        self.openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        
        logger.info(f"Using model: {self.model_config.name} ({self.provider.value})")
        
        # Clients will be initialized per-execution to handle credentials
        self._bedrock_client: AsyncAnthropicBedrock | None = None
        self._openrouter_client: OpenRouterClient | None = None
    
    async def _get_bedrock_client(self) -> AsyncAnthropicBedrock:
        """Get or create the Anthropic Bedrock client with SSO credentials."""
        if self._bedrock_client is None:
            # Get credentials via aws-vault
            creds = await self._aws_auth.get_credentials()
            
            if creds is None:
                raise RuntimeError(
                    f"Failed to get AWS credentials for profile {self.aws_profile}. "
                    f"Run: aws-vault login {self.aws_profile}"
                )
            
            # Create client with explicit credentials
            self._bedrock_client = AsyncAnthropicBedrock(
                aws_access_key=creds.access_key_id,
                aws_secret_key=creds.secret_access_key,
                aws_session_token=creds.session_token,
                aws_region=creds.region,
            )
            
            logger.info(f"Created Bedrock client with {self.aws_profile} credentials")
        
        return self._bedrock_client
    
    def _get_openrouter_client(self) -> OpenRouterClient:
        """Get or create the OpenRouter client."""
        if self._openrouter_client is None:
            if not self.openrouter_api_key:
                raise RuntimeError(
                    "OpenRouter API key required. Set OPENROUTER_API_KEY env var."
                )
            
            self._openrouter_client = OpenRouterClient(
                api_key=self.openrouter_api_key,
                timeout=300.0,
            )
            
            logger.info(f"Created OpenRouter client for {self.model}")
        
        return self._openrouter_client
    
    async def _call_llm(
        self,
        messages: list[dict],
        system: str | list[dict],
        tools: list[dict],
    ) -> Any:
        """Call the LLM with the appropriate provider."""
        if self.provider == Provider.BEDROCK:
            client = await self._get_bedrock_client()
            return await client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system,
                tools=tools,
                messages=messages,
            )
        elif self.provider == Provider.OPENROUTER:
            client = self._get_openrouter_client()
            return await client.create_message(
                model=self.model,
                messages=messages,
                system=system,
                tools=tools,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _build_tools(self, task: AgentTask, response_cache: ResponseCache) -> ToolRegistry:
        """Build the tool registry for a task."""
        registry = ToolRegistry()
        
        # Allowed read paths
        allowed_read_paths = [
            self.repos_dir,
            self.output_dir,
        ]
        
        # File tools
        registry.register(FileReadTool(allowed_read_paths))
        registry.register(FileWriteTool(self.output_dir))
        registry.register(FileListTool(allowed_read_paths))
        
        # Bash tool
        registry.register(BashTool(
            working_dir=self.repos_dir,
            allowed_paths=allowed_read_paths,
            timeout=30,
        ))
        
        # Spawn agent tool (with depth and task limit tracking)
        registry.register(SpawnAgentTool(
            task_queue=self.task_queue,
            current_depth=task.depth,
            max_depth=self.max_depth,
            max_tasks=self.max_tasks,
            parent_task_id=task.task_id,
        ))
        
        # Cache read tool for reloading cached responses
        registry.register(CacheReadTool(response_cache))
        
        return registry
    
    def _build_system_prompt(self, task: AgentTask) -> str:
        """Build the system prompt for a task."""
        if task.depth == 0 and task.parent_task_id is None:
            # Master agent
            return get_master_prompt(
                max_depth=self.max_depth,
                output_dir=str(self.output_dir),
                repos_dir=str(self.repos_dir),
            )
        else:
            # Child agent
            return get_child_prompt(
                task_description=task.prompt,
                context=task.context,
                output_path=task.output_path,
                current_depth=task.depth,
                max_depth=self.max_depth,
                repos_dir=str(self.repos_dir),
            )
    
    def _compress_cached_responses(
        self,
        messages: list[dict],
        cached_responses: dict[tuple[int, str], str],
        response_cache: ResponseCache,
    ) -> int:
        """
        Replace cached tool results with stubs in older messages.
        
        This preserves the latest tool results in full but replaces older
        cached responses with stubs, saving significant context space.
        
        Args:
            messages: The conversation messages (modified in place)
            cached_responses: Map of (msg_index, tool_use_id) -> cache_id
            response_cache: The cache to get stubs from
            
        Returns:
            Number of responses compressed
        """
        compressed = 0
        
        # Find the last user message index (we don't compress the latest)
        last_user_msg_idx = None
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "user":
                last_user_msg_idx = i
                break
        
        if last_user_msg_idx is None:
            return 0
        
        # Go through all user messages except the last one
        for msg_idx, msg in enumerate(messages):
            if msg.get("role") != "user" or msg_idx >= last_user_msg_idx:
                continue
            
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            
            # Check each tool result in this message
            for item in content:
                if item.get("type") != "tool_result":
                    continue
                
                tool_use_id = item.get("tool_use_id")
                cache_key = (msg_idx, tool_use_id)
                
                if cache_key in cached_responses:
                    cache_id = cached_responses[cache_key]
                    current_content = item.get("content", "")
                    
                    # Only compress if not already a stub
                    if isinstance(current_content, str) and '"cached":' not in current_content:
                        stub = response_cache.get_stub(cache_id)
                        item["content"] = json.dumps(stub)
                        compressed += 1
        
        return compressed
    
    async def execute_task(self, task: AgentTask) -> None:
        """
        Execute a single agent task.
        
        Args:
            task: The task to execute
        """
        logger.info(f"Executing task {task.task_id[:8]} (depth={task.depth})")
        
        # Mark as running
        task.mark_running()
        await self.task_queue.update_task(task)
        
        # Create response cache for this task
        cache_dir = self.output_dir / ".spawner" / "response_cache" / task.task_id[:8]
        response_cache = ResponseCache(cache_dir)
        
        # Track cache IDs for tool results (maps message index + tool_use_id to cache_id)
        cached_responses: dict[tuple[int, str], str] = {}
        
        # Build tools and prompt
        tools = self._build_tools(task, response_cache)
        system_prompt = self._build_system_prompt(task)
        
        # Track token usage
        total_input_tokens = 0
        total_output_tokens = 0
        
        try:
            # Initialize conversation
            messages = []
            
            # For child agents, the task description is the initial user message
            if task.depth > 0:
                initial_message = f"Please complete the following documentation task:\n\n{task.prompt}"
                if task.context:
                    initial_message += f"\n\nAdditional context:\n{task.context}"
            else:
                initial_message = "Please begin documenting the Natterbox platform. Start by discovering what repositories exist, then spawn child agents to document them."
            
            messages.append({"role": "user", "content": initial_message})
            
            # Build system prompt with cache_control for prompt caching (Bedrock)
            # For OpenRouter, we'll pass as plain string
            if self.provider == Provider.BEDROCK:
                system_with_cache = [
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"}
                    }
                ]
            else:
                # OpenRouter uses plain string system prompts
                system_with_cache = system_prompt
            
            # Get tools with cache_control on the last one (for Bedrock caching)
            tool_schemas = tools.get_schemas_for_claude()
            if tool_schemas and self.provider == Provider.BEDROCK:
                # Add cache_control to last tool to cache all tools
                tool_schemas[-1]["cache_control"] = {"type": "ephemeral"}
            
            # Track cache statistics
            total_cache_creation_tokens = 0
            total_cache_read_tokens = 0
            
            # Agentic loop
            for turn in range(self.max_turns):
                logger.info(f"Task {task.task_id[:8]} turn {turn + 1}/{self.max_turns}")
                
                # Compress old tool results in history (replace with cache stubs)
                # This saves context by removing large responses we've already seen
                if cached_responses and len(messages) > 2:
                    compressed_count = self._compress_cached_responses(
                        messages, cached_responses, response_cache
                    )
                    if compressed_count > 0:
                        logger.debug(f"  Compressed {compressed_count} cached responses")
                
                # Call LLM (Bedrock or OpenRouter)
                response = await self._call_llm(
                    messages=messages,
                    system=system_with_cache,
                    tools=tool_schemas,
                )
                
                # Track tokens (including cache statistics)
                total_input_tokens += response.usage.input_tokens
                total_output_tokens += response.usage.output_tokens
                
                # Track cache tokens if available
                if hasattr(response.usage, 'cache_creation_input_tokens'):
                    total_cache_creation_tokens += response.usage.cache_creation_input_tokens or 0
                if hasattr(response.usage, 'cache_read_input_tokens'):
                    total_cache_read_tokens += response.usage.cache_read_input_tokens or 0
                    if response.usage.cache_read_input_tokens:
                        logger.debug(f"  Cache hit: {response.usage.cache_read_input_tokens} tokens read from cache")
                
                # Process response
                assistant_content = response.content
                messages.append({"role": "assistant", "content": assistant_content})
                
                # Log AI text responses
                for block in assistant_content:
                    if block.type == "text" and block.text.strip():
                        text_preview = block.text[:200].replace('\n', ' ')
                        if len(block.text) > 200:
                            text_preview += "..."
                        logger.info(f"  AI: \"{text_preview}\"")
                
                # Check if done (no tool calls)
                if response.stop_reason == "end_turn":
                    logger.info(f"Task {task.task_id[:8]} completed after {turn + 1} turns")
                    break
                
                # Process tool calls
                tool_results = []
                for block in assistant_content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        tool_use_id = block.id
                        
                        # Log tool call with key arguments
                        args_preview = json.dumps(tool_input, default=str)
                        if len(args_preview) > 150:
                            args_preview = args_preview[:150] + "..."
                        logger.info(f"  Tool: {tool_name}({args_preview})")
                        
                        # Execute tool
                        result = await tools.execute(tool_name, **tool_input)
                        
                        # Log result
                        if result.success:
                            if tool_name == "spawn_agent":
                                # Special logging for spawned agents
                                if result.data:
                                    stats = await self.task_queue.get_stats()
                                    logger.info(
                                        f"  SPAWNED: {result.data.get('task_id', '')[:8]} -> "
                                        f"{tool_input.get('output_path', '')} "
                                        f"(depth {result.data.get('depth', '?')}, {stats.total}/{self.max_tasks} tasks)"
                                    )
                            elif tool_name == "file_write":
                                # Special logging for file writes
                                content_len = len(tool_input.get('content', ''))
                                logger.info(f"  WROTE: {tool_input.get('path', '')} ({content_len:,} bytes)")
                            else:
                                # Generic success logging
                                data_preview = str(result.data)[:100] if result.data else "ok"
                                if len(str(result.data or "")) > 100:
                                    data_preview += "..."
                                logger.info(f"  Result: {data_preview}")
                        else:
                            logger.warning(f"  Error: {result.error}")
                        
                        # Format result for Claude
                        if result.success:
                            if isinstance(result.data, dict):
                                content = json.dumps(result.data, indent=2, default=str)
                            else:
                                content = str(result.data) if result.data else "Success"
                        else:
                            content = f"Error: {result.error}"
                        
                        # Truncate very large results
                        if len(content) > 30000:
                            content = content[:30000] + "\n\n... [truncated]"
                        
                        # Check if this response should be cached
                        cache_id = None
                        if response_cache.should_cache(content):
                            # Create summary for the stub
                            summary = f"{tool_name}"
                            if tool_name == "file_read":
                                summary = f"file_read: {tool_input.get('path', '')}"
                            elif tool_name == "file_list":
                                summary = f"file_list: {tool_input.get('path', '')}"
                            elif tool_name == "bash":
                                cmd = tool_input.get('command', '')[:50]
                                summary = f"bash: {cmd}"
                            
                            cache_id = response_cache.store(tool_name, content, summary)
                            # Track for later compression (will be replaced in next turn)
                            msg_index = len(messages)  # Index of the upcoming message
                            cached_responses[(msg_index, tool_use_id)] = cache_id
                        
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": content,
                        })
                
                if tool_results:
                    messages.append({"role": "user", "content": tool_results})
                else:
                    # No tool calls and not end_turn - unusual, break
                    logger.warning(f"Task {task.task_id[:8]} stopped without tool calls or end_turn")
                    break
            
            else:
                # Hit max turns
                logger.warning(f"Task {task.task_id[:8]} hit max turns ({self.max_turns})")
            
            # Mark completed
            task.mark_completed(
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
            )
            await self.task_queue.update_task(task)
            
            # Log completion with cache statistics
            cache_info = ""
            if total_cache_read_tokens > 0:
                savings_pct = (total_cache_read_tokens / total_input_tokens * 100) if total_input_tokens > 0 else 0
                cache_info = f" (cache saved ~{savings_pct:.0f}%)"
            
            logger.info(
                f"Task {task.task_id[:8]} completed: "
                f"{total_input_tokens:,} input, {total_output_tokens:,} output tokens{cache_info}"
            )
            
        except Exception as e:
            logger.exception(f"Task {task.task_id[:8]} failed with exception")
            task.mark_failed(str(e))
            task.input_tokens = total_input_tokens
            task.output_tokens = total_output_tokens
            await self.task_queue.update_task(task)
    
    async def run_worker(self, worker_id: int = 0) -> None:
        """
        Run a worker that continuously processes tasks.
        
        Args:
            worker_id: Identifier for this worker (for logging)
        """
        logger.info(f"Worker {worker_id} started")
        
        while True:
            # Try to claim a task
            task = await self.task_queue.claim_pending_task()
            
            if task is None:
                # No pending tasks, check if we should exit
                stats = await self.task_queue.get_stats()
                if stats.running == 0 and stats.pending == 0:
                    logger.info(f"Worker {worker_id} exiting: no more tasks")
                    break
                
                # Wait before checking again
                await asyncio.sleep(1)
                continue
            
            # Execute the task
            await self.execute_task(task)
    
    async def run_workers(self, num_workers: int = 3) -> None:
        """
        Run multiple workers in parallel.
        
        Args:
            num_workers: Number of concurrent workers
        """
        logger.info(f"Starting {num_workers} workers")
        
        workers = [
            self.run_worker(worker_id=i)
            for i in range(num_workers)
        ]
        
        await asyncio.gather(*workers)
        
        logger.info("All workers completed")
