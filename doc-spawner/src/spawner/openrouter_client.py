"""OpenRouter API client for accessing various LLM models."""

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, AsyncIterator

import httpx

logger = logging.getLogger("doc-spawner.openrouter")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1"


@dataclass
class OpenRouterMessage:
    """A message in the OpenRouter format."""
    role: str
    content: Any


@dataclass 
class OpenRouterUsage:
    """Token usage from OpenRouter response."""
    input_tokens: int
    output_tokens: int


class OpenRouterClient:
    """
    Async client for OpenRouter API.
    
    OpenRouter provides a unified API compatible with OpenAI's format,
    giving access to many models from different providers.
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 300.0,
        site_url: str = "https://github.com/natterbox/doc-spawner",
        site_name: str = "doc-spawner",
    ):
        """
        Initialize the OpenRouter client.
        
        Args:
            api_key: OpenRouter API key (or set OPENROUTER_API_KEY env var)
            timeout: Request timeout in seconds
            site_url: Your site URL (for OpenRouter analytics)
            site_name: Your site/app name
        """
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY env var "
                "or pass api_key parameter."
            )
        
        self.timeout = timeout
        self.site_url = site_url
        self.site_name = site_name
        self._client: httpx.AsyncClient | None = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=OPENROUTER_API_URL,
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.site_name,
                    "Content-Type": "application/json",
                },
            )
        return self._client
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def create_message(
        self,
        model: str,
        messages: list[dict],
        system: str | list[dict] | None = None,
        tools: list[dict] | None = None,
        max_tokens: int = 16384,
        temperature: float = 0.3,
    ) -> dict:
        """
        Create a chat completion with tool support.
        
        Args:
            model: Model ID (e.g., "openai/gpt-5.2", "x-ai/grok-code-fast-1")
            messages: Conversation messages
            system: System prompt (string or list of content blocks)
            tools: Tool definitions in OpenAI format
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Response dict with content, usage, etc.
        """
        client = await self._get_client()
        
        # Build request
        request_messages = []
        
        # Add system message if provided
        if system:
            if isinstance(system, str):
                request_messages.append({"role": "system", "content": system})
            elif isinstance(system, list):
                # Handle Claude-style system with cache_control
                system_text = ""
                for block in system:
                    if isinstance(block, dict) and block.get("type") == "text":
                        system_text += block.get("text", "")
                    elif isinstance(block, str):
                        system_text += block
                request_messages.append({"role": "system", "content": system_text})
        
        # Convert messages to OpenAI format
        for msg in messages:
            converted = self._convert_message(msg)
            if converted:
                if isinstance(converted, list):
                    # Multiple tool results returned as list
                    request_messages.extend(converted)
                else:
                    request_messages.append(converted)
        
        payload: dict[str, Any] = {
            "model": model,
            "messages": request_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        # Add tools if provided (convert from Claude format to OpenAI format)
        if tools:
            openai_tools = self._convert_tools_to_openai(tools)
            if openai_tools:
                payload["tools"] = openai_tools
                payload["tool_choice"] = "auto"
        
        logger.debug(f"OpenRouter request to {model}")
        
        response = await client.post("/chat/completions", json=payload)
        
        # Log error details before raising
        if response.status_code >= 400:
            try:
                error_body = response.json()
                logger.error(f"OpenRouter API error {response.status_code}: {error_body}")
            except Exception:
                logger.error(f"OpenRouter API error {response.status_code}: {response.text}")
        
        response.raise_for_status()
        
        data = response.json()
        
        # Convert response to Claude-like format for compatibility
        return self._convert_response(data)
    
    def _convert_message(self, msg: dict) -> dict | list[dict] | None:
        """Convert a message from Claude format to OpenAI format.
        
        Returns a single message dict, a list of messages (for multiple tool results),
        or None if the message should be skipped.
        """
        role = msg.get("role")
        content = msg.get("content")
        
        if role == "user":
            # Handle tool results
            if isinstance(content, list):
                # Check if this is tool results
                tool_results = [c for c in content if isinstance(c, dict) and c.get("type") == "tool_result"]
                if tool_results:
                    # Convert to OpenAI tool message format - return list for multiple
                    messages = []
                    for tr in tool_results:
                        result_content = tr.get("content", "")
                        # Handle content that might be a list
                        if isinstance(result_content, list):
                            text_parts = []
                            for part in result_content:
                                if isinstance(part, dict) and part.get("type") == "text":
                                    text_parts.append(part.get("text", ""))
                                elif isinstance(part, str):
                                    text_parts.append(part)
                            result_content = "\n".join(text_parts)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tr.get("tool_use_id", ""),
                            "content": str(result_content) if result_content else "",
                        })
                    return messages if len(messages) > 1 else messages[0]
                else:
                    # Regular user message with content blocks
                    text_parts = []
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "text":
                            text_parts.append(c.get("text", ""))
                        elif isinstance(c, str):
                            text_parts.append(c)
                    return {"role": "user", "content": "\n".join(text_parts)}
            else:
                return {"role": "user", "content": str(content)}
        
        elif role == "assistant":
            # Handle assistant messages with tool calls
            if isinstance(content, list):
                text_parts = []
                tool_calls = []
                
                for block in content:
                    if hasattr(block, "type"):
                        # Anthropic SDK object
                        if block.type == "text":
                            text_parts.append(block.text)
                        elif block.type == "tool_use":
                            tool_calls.append({
                                "id": block.id,
                                "type": "function",
                                "function": {
                                    "name": block.name,
                                    "arguments": json.dumps(block.input),
                                },
                            })
                    elif isinstance(block, dict):
                        if block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                        elif block.get("type") == "tool_use":
                            tool_calls.append({
                                "id": block.get("id", ""),
                                "type": "function",
                                "function": {
                                    "name": block.get("name", ""),
                                    "arguments": json.dumps(block.get("input", {})),
                                },
                            })
                
                msg_dict: dict[str, Any] = {"role": "assistant"}
                if text_parts:
                    msg_dict["content"] = "\n".join(text_parts)
                if tool_calls:
                    msg_dict["tool_calls"] = tool_calls
                return msg_dict
            else:
                return {"role": "assistant", "content": str(content) if content else ""}
        
        return None
    
    def _convert_tools_to_openai(self, claude_tools: list[dict]) -> list[dict]:
        """Convert Claude tool definitions to OpenAI format."""
        openai_tools = []
        for tool in claude_tools:
            # Skip cache_control metadata
            if "cache_control" in tool and "name" not in tool:
                continue
            
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {}),
                },
            }
            openai_tools.append(openai_tool)
        return openai_tools
    
    def _convert_response(self, openai_response: dict) -> "MockClaudeResponse":
        """Convert OpenAI response to Claude-like format."""
        choice = openai_response.get("choices", [{}])[0]
        message = choice.get("message", {})
        usage = openai_response.get("usage", {})
        
        # Build content blocks
        content = []
        
        # Add text content if present
        if message.get("content"):
            content.append(MockTextBlock(text=message["content"]))
        
        # Add tool calls if present
        tool_calls = message.get("tool_calls", [])
        for tc in tool_calls:
            func = tc.get("function", {})
            try:
                args = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                args = {}
            
            content.append(MockToolUseBlock(
                id=tc.get("id", ""),
                name=func.get("name", ""),
                input=args,
            ))
        
        # Determine stop reason
        finish_reason = choice.get("finish_reason", "")
        if finish_reason == "tool_calls":
            stop_reason = "tool_use"
        elif finish_reason == "stop":
            stop_reason = "end_turn"
        else:
            stop_reason = finish_reason
        
        return MockClaudeResponse(
            content=content,
            stop_reason=stop_reason,
            usage=MockUsage(
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
            ),
        )


# Mock classes to match Claude SDK response structure
class MockTextBlock:
    """Mock text block matching Claude's format."""
    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class MockToolUseBlock:
    """Mock tool use block matching Claude's format."""
    def __init__(self, id: str, name: str, input: dict):
        self.type = "tool_use"
        self.id = id
        self.name = name
        self.input = input


class MockUsage:
    """Mock usage matching Claude's format."""
    def __init__(self, input_tokens: int, output_tokens: int):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class MockClaudeResponse:
    """Mock response matching Claude's format."""
    def __init__(self, content: list, stop_reason: str, usage: MockUsage):
        self.content = content
        self.stop_reason = stop_reason
        self.usage = usage
