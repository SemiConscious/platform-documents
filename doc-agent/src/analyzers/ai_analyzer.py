"""
AI-Powered Code Analyzer.

Uses Claude to semantically understand code instead of brittle regex patterns.
This handles the diverse coding styles across 50+ engineers and multiple
frameworks (Kohana, Express, Flask, etc.) without per-framework rules.
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .models import (
    AnalysisResult,
    ExtractedEndpoint,
    ExtractedModel,
    ExtractedField,
    ExtractedConfig,
    ExtractedSideEffect,
    ExtractedDependency,
    ModelType,
    SideEffectCategory,
)

logger = logging.getLogger("doc-agent.analyzers.ai_analyzer")


@dataclass
class AIAnalysisConfig:
    """Configuration for AI analysis."""
    max_file_size: int = 100_000  # Max file size to analyze (100KB)
    max_files_per_batch: int = 10  # Files per LLM call
    max_code_context: int = 50_000  # Max tokens of code context
    include_tests: bool = False  # Whether to analyze test files


class AICodeAnalyzer:
    """
    AI-powered code analyzer using Claude.
    
    Instead of per-language regex patterns, this analyzer sends code
    to Claude and asks it to extract structured information about:
    - API endpoints (methods, paths, handlers)
    - Data models (classes, schemas, types)
    - Configuration (env vars, config files)
    - Side effects (database queries, external APIs)
    
    This handles:
    - Multiple languages and frameworks
    - Diverse coding styles
    - Complex patterns (like Kohana __call methods)
    - Non-standard patterns
    """
    
    def __init__(
        self,
        llm_client: Any,
        model_selector: Any = None,
        config: Optional[AIAnalysisConfig] = None,
        token_tracker: Any = None,
        github_base_url: Optional[str] = None,
    ):
        """
        Initialize the AI analyzer.
        
        Args:
            llm_client: Anthropic client (Bedrock or direct)
            model_selector: Model selector for operation-specific models
            config: Analysis configuration
            token_tracker: Token usage tracker
            github_base_url: Base URL for GitHub links (e.g., https://github.com/org/repo)
        """
        self.llm_client = llm_client
        self.model_selector = model_selector
        self.config = config or AIAnalysisConfig()
        self.token_tracker = token_tracker
        self.github_base_url = github_base_url
    
    def _get_model(self, operation_type: str = "analysis") -> str:
        """Get the appropriate model for an operation."""
        if self.model_selector:
            from ..llm import Operation
            try:
                op = Operation(operation_type)
                return self.model_selector.get_model(op)
            except (ValueError, AttributeError):
                pass
        
        # Fallback
        return "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    async def _call_llm(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int = 4096,
        operation: str = "analysis",
    ) -> str:
        """Call the LLM with streaming and track tokens."""
        if not self.llm_client:
            return ""
        
        model = self._get_model(operation)
        
        try:
            # Use streaming to handle long operations
            chunks = []
            input_tokens = 0
            output_tokens = 0
            
            async with self.llm_client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                async for text in stream.text_stream:
                    chunks.append(text)
                
                # Get final message for token tracking
                final_message = await stream.get_final_message()
                if final_message and hasattr(final_message, "usage"):
                    input_tokens = final_message.usage.input_tokens
                    output_tokens = final_message.usage.output_tokens
            
            # Track tokens
            if self.token_tracker and (input_tokens or output_tokens):
                class UsageInfo:
                    def __init__(self, inp, out):
                        self.usage = type('Usage', (), {'input_tokens': inp, 'output_tokens': out})()
                
                self.token_tracker.record(
                    UsageInfo(input_tokens, output_tokens),
                    f"ai_analyzer_{operation}"
                )
            
            return "".join(chunks)
            
        except Exception as e:
            logger.error(f"AI analysis LLM call failed: {e}")
            return ""
    
    def _github_link(self, file_path: str, line: int = 1) -> Optional[str]:
        """Generate a GitHub link for a file and line."""
        if not self.github_base_url:
            return None
        return f"{self.github_base_url}/blob/master/{file_path}#L{line}"
    
    def _repair_truncated_json(self, json_str: str) -> str:
        """
        Attempt to repair truncated JSON by closing unclosed brackets/braces.
        
        This handles the common case where Claude's output is truncated mid-JSON
        due to max_tokens limits.
        """
        # Count unclosed brackets
        open_braces = json_str.count('{') - json_str.count('}')
        open_brackets = json_str.count('[') - json_str.count(']')
        
        # Check for unterminated strings
        # Simple heuristic: odd number of unescaped quotes
        quote_count = len(re.findall(r'(?<!\\)"', json_str))
        if quote_count % 2 != 0:
            # Try to close the string
            json_str = json_str.rstrip()
            if not json_str.endswith('"'):
                json_str += '"'
        
        # Remove trailing incomplete elements
        # Pattern: trailing comma or incomplete key-value pair
        json_str = re.sub(r',\s*$', '', json_str)
        json_str = re.sub(r',\s*"[^"]*$', '', json_str)  # Incomplete key
        json_str = re.sub(r':\s*$', ': null', json_str)  # Incomplete value
        
        # Close unclosed braces/brackets
        json_str += '}' * max(0, open_braces)
        json_str += ']' * max(0, open_brackets)
        
        return json_str
    
    def _extract_json_array(self, response: str) -> list:
        """
        Extract and parse a JSON array from an LLM response.
        
        Handles:
        - JSON wrapped in ```json``` code blocks
        - Truncated JSON (attempts repair)
        - Non-array responses (wraps in array)
        """
        json_str = response.strip()
        
        # Extract from code blocks
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            parts = json_str.split("```")
            if len(parts) >= 2:
                json_str = parts[1]
        
        json_str = json_str.strip()
        
        # Try parsing as-is first
        try:
            data = json.loads(json_str)
            return data if isinstance(data, list) else [data]
        except json.JSONDecodeError:
            pass
        
        # Try repairing truncated JSON
        try:
            repaired = self._repair_truncated_json(json_str)
            data = json.loads(repaired)
            logger.debug("Successfully parsed repaired JSON")
            return data if isinstance(data, list) else [data]
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON even after repair: {e}")
            return []
    
    async def analyze_repository(
        self,
        repo_path: Path,
        service_name: str,
    ) -> AnalysisResult:
        """
        Analyze a repository using AI.
        
        Args:
            repo_path: Path to the repository
            service_name: Name of the service being analyzed
            
        Returns:
            AnalysisResult with extracted information
        """
        logger.info(f"Starting AI analysis of {service_name} at {repo_path}")
        
        # Find relevant source files
        controller_files = self._find_files(repo_path, ["controller", "handler", "route", "api"])
        model_files = self._find_files(repo_path, ["model", "schema", "entity", "type"])
        config_files = self._find_config_files(repo_path)
        
        # If no controller files found, try to find all source files in src/lambda directories
        if not controller_files:
            controller_files = self._find_files(repo_path, [], include_src=True)
            logger.info(f"No explicit controller files, found {len(controller_files)} source files in src/lambda dirs")
        
        logger.info(
            f"Found {len(controller_files)} controller files, "
            f"{len(model_files)} model files, {len(config_files)} config files"
        )
        
        # Analyze in parallel
        endpoints_task = self._analyze_endpoints(controller_files, service_name)
        models_task = self._analyze_models(model_files, service_name)
        config_task = self._analyze_config(config_files, service_name)
        
        endpoints, models, config = await asyncio.gather(
            endpoints_task, models_task, config_task
        )
        
        # Extract side effects from endpoints
        side_effects = await self._extract_side_effects(controller_files, service_name)
        
        # Analyze dependencies
        dependencies = self._analyze_dependencies(repo_path)
        
        return AnalysisResult(
            language="multi",  # AI analyzer handles multiple languages
            endpoints=endpoints,
            models=models,
            config=config,
            side_effects=side_effects,
            dependencies=dependencies,
        )
    
    def _find_files(
        self,
        repo_path: Path,
        keywords: list[str],
        extensions: list[str] = None,
        include_src: bool = True,
    ) -> list[Path]:
        """Find files matching keywords in name or path."""
        if extensions is None:
            extensions = [".php", ".py", ".ts", ".js", ".go", ".java", ".rb", ".rs"]
        
        files = []
        skip_patterns = ["test", "spec", "vendor", "node_modules", ".git", "cache", "__pycache__", "dist", "build"]
        
        for ext in extensions:
            for f in repo_path.rglob(f"*{ext}"):
                # Skip test files, vendor, node_modules
                rel_path = str(f.relative_to(repo_path)).lower()
                if any(skip in rel_path for skip in skip_patterns):
                    continue
                
                # Check if any keyword matches
                name_lower = f.name.lower()
                keyword_match = any(kw in name_lower or kw in rel_path for kw in keywords)
                
                # Also include files in src/ or lambda/ directories (common patterns)
                src_dir_match = include_src and any(p in rel_path for p in ["/src/", "lambda/", "/lib/", "/app/"])
                
                if keyword_match or src_dir_match:
                    if f.stat().st_size <= self.config.max_file_size:
                        files.append(f)
        
        return files[:50]  # Limit to avoid overwhelming the LLM
    
    def _find_config_files(self, repo_path: Path) -> list[Path]:
        """Find configuration files."""
        config_patterns = [
            "*.env*", ".env*", "config.php", "config.py", "config.yaml", 
            "config.yml", "config.json", "settings.php", "settings.py",
            "**/config/*.php", "**/config/*.py", "**/config/*.yaml",
        ]
        
        files = []
        for pattern in config_patterns:
            files.extend(repo_path.glob(pattern))
        
        # Filter by size
        return [f for f in files if f.is_file() and f.stat().st_size <= self.config.max_file_size][:20]
    
    async def _analyze_endpoints(
        self,
        files: list[Path],
        service_name: str,
    ) -> list[ExtractedEndpoint]:
        """Use AI to extract API endpoints from controller files."""
        if not files:
            return []
        
        endpoints = []
        
        # Process files in batches
        for i in range(0, len(files), self.config.max_files_per_batch):
            batch = files[i:i + self.config.max_files_per_batch]
            batch_endpoints = await self._analyze_endpoint_batch(batch, service_name)
            endpoints.extend(batch_endpoints)
        
        logger.info(f"AI extracted {len(endpoints)} endpoints from {len(files)} files")
        return endpoints
    
    async def _analyze_endpoint_batch(
        self,
        files: list[Path],
        service_name: str,
    ) -> list[ExtractedEndpoint]:
        """Analyze a batch of files for endpoints."""
        # Build code context
        code_context = []
        for f in files:
            try:
                content = f.read_text(errors='ignore')
                # Truncate very long files
                if len(content) > 20000:
                    content = content[:20000] + "\n... (truncated)"
                code_context.append(f"=== FILE: {f.name} ===\n{content}")
            except Exception as e:
                logger.warning(f"Failed to read {f}: {e}")
        
        if not code_context:
            return []
        
        prompt = f"""Analyze the following code files from the {service_name} service and extract all API endpoints.

For each endpoint, provide:
- HTTP method (GET, POST, PUT, DELETE, PATCH)
- URL path (e.g., /users, /api/v1/orders/:id)
- Handler function/method name
- Brief description of what the endpoint does
- Request parameters (path params, query params, body)
- Response format

CODE FILES:
{"".join(code_context)}

OUTPUT FORMAT (JSON array):
[
  {{
    "method": "GET",
    "path": "/api/users",
    "handler": "UsersController::index",
    "description": "List all users with pagination",
    "parameters": ["page", "limit"],
    "response": "Array of user objects"
  }},
  ...
]

Important:
- Include ALL endpoints found, even if incomplete
- For REST controllers, identify CRUD patterns
- For framework-specific patterns (like Kohana __call), extract actual endpoints
- If a class handles multiple HTTP methods for the same entity, list each method
- Only output valid JSON, no other text"""

        system_prompt = """You are an expert code analyst specializing in API extraction.
Analyze code to identify HTTP endpoints regardless of framework or language.
Look for:
- Route definitions (annotations, decorators, config files)
- Controller methods with HTTP semantics
- Request handlers
- REST resource patterns
Output only valid JSON."""

        response = await self._call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=32000,  # High limit to avoid truncation
            operation="analysis",
        )
        
        return self._parse_endpoints_response(response, files)
    
    def _parse_endpoints_response(
        self,
        response: str,
        files: list[Path],
    ) -> list[ExtractedEndpoint]:
        """Parse the AI response into ExtractedEndpoint objects."""
        endpoints = []
        
        try:
            data = self._extract_json_array(response)
            
            for item in data:
                if not isinstance(item, dict):
                    continue
                
                method = item.get("method", "GET").upper()
                path = item.get("path", "")
                
                if not path:
                    continue
                
                endpoints.append(ExtractedEndpoint(
                    method=method,
                    path=path,
                    handler=item.get("handler", ""),
                    description=item.get("description", ""),
                    file=str(files[0]) if files else "",
                    line=1,
                    parameters=item.get("parameters", []),
                    response_type=item.get("response", ""),
                    decorators=["ai_extracted"],
                    github_url=self._github_link(str(files[0]) if files else "", 1),
                ))
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI endpoint response: {e}")
        except Exception as e:
            logger.warning(f"Error processing AI endpoint response: {e}")
        
        return endpoints
    
    async def _analyze_models(
        self,
        files: list[Path],
        service_name: str,
    ) -> list[ExtractedModel]:
        """Use AI to extract data models from source files."""
        if not files:
            return []
        
        models = []
        
        for i in range(0, len(files), self.config.max_files_per_batch):
            batch = files[i:i + self.config.max_files_per_batch]
            batch_models = await self._analyze_model_batch(batch, service_name)
            models.extend(batch_models)
        
        logger.info(f"AI extracted {len(models)} models from {len(files)} files")
        return models
    
    async def _analyze_model_batch(
        self,
        files: list[Path],
        service_name: str,
    ) -> list[ExtractedModel]:
        """Analyze a batch of files for data models."""
        code_context = []
        for f in files:
            try:
                content = f.read_text(errors='ignore')
                if len(content) > 15000:
                    content = content[:15000] + "\n... (truncated)"
                code_context.append(f"=== FILE: {f.name} ===\n{content}")
            except Exception:
                pass
        
        if not code_context:
            return []
        
        prompt = f"""Analyze these code files from {service_name} and extract all data models/schemas.

For each model, identify:
- Class/struct/type name
- Fields/properties with their types
- Whether each field is required or optional
- Default values
- Validation rules
- Relationships to other models

CODE FILES:
{"".join(code_context)}

OUTPUT FORMAT (JSON array):
[
  {{
    "name": "User",
    "description": "User account model",
    "fields": [
      {{"name": "id", "type": "int", "required": true, "description": "Primary key"}},
      {{"name": "email", "type": "string", "required": true, "description": "User email address"}},
      {{"name": "created_at", "type": "datetime", "required": false, "default": "now()"}}
    ],
    "relationships": ["has_many:orders", "belongs_to:organization"]
  }}
]

Only output valid JSON."""

        system_prompt = """You are an expert at analyzing code to extract data models and schemas.
Identify classes, structs, types, and database models regardless of language.
Look for:
- ORM models (SQLAlchemy, Eloquent, ActiveRecord)
- TypeScript interfaces and types
- Pydantic models
- Database migration schemas
- GraphQL types"""

        response = await self._call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=32000,  # High limit to avoid truncation
            operation="analysis",
        )
        
        return self._parse_models_response(response, files)
    
    def _parse_models_response(
        self,
        response: str,
        files: list[Path],
    ) -> list[ExtractedModel]:
        """Parse the AI response into ExtractedModel objects."""
        models = []
        
        try:
            data = self._extract_json_array(response)
            
            for item in data:
                if not isinstance(item, dict):
                    continue
                
                name = item.get("name", "")
                if not name:
                    continue
                
                fields = []
                for field_data in item.get("fields", []):
                    if isinstance(field_data, dict):
                        fields.append(ExtractedField(
                            name=field_data.get("name", ""),
                            type=field_data.get("type", "unknown"),
                            description=field_data.get("description", ""),
                            required=field_data.get("required", False),
                            default=field_data.get("default"),
                        ))
                
                models.append(ExtractedModel(
                    name=name,
                    model_type=ModelType.CLASS,
                    description=item.get("description", ""),
                    fields=fields,
                    file=str(files[0]) if files else "",
                    line=1,
                    github_url=self._github_link(str(files[0]) if files else "", 1),
                ))
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI model response: {e}")
        except Exception as e:
            logger.warning(f"Error processing AI model response: {e}")
        
        return models
    
    async def _analyze_config(
        self,
        files: list[Path],
        service_name: str,
    ) -> list[ExtractedConfig]:
        """Use AI to extract configuration variables."""
        if not files:
            return []
        
        code_context = []
        for f in files:
            try:
                content = f.read_text(errors='ignore')
                if len(content) > 10000:
                    content = content[:10000] + "\n... (truncated)"
                code_context.append(f"=== FILE: {f.name} ===\n{content}")
            except Exception:
                pass
        
        if not code_context:
            return []
        
        prompt = f"""Analyze these configuration files from {service_name} and extract all configuration variables.

Identify:
- Environment variables
- Config keys
- Default values
- Whether required or optional
- What each variable controls

CODE FILES:
{"".join(code_context)}

OUTPUT FORMAT (JSON array):
[
  {{
    "key": "DATABASE_URL",
    "description": "PostgreSQL database connection string",
    "default": null,
    "required": true,
    "source": "env"
  }}
]

Only output valid JSON."""

        system_prompt = """You are an expert at analyzing configuration files.
Extract all environment variables and configuration options regardless of format.
Look for:
- getenv(), os.environ, process.env
- Config files (YAML, JSON, PHP arrays)
- Default values and fallbacks
- Required vs optional settings"""

        response = await self._call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=16000,  # Increased to avoid truncation
            operation="extraction",
        )
        
        return self._parse_config_response(response, files)
    
    def _parse_config_response(
        self,
        response: str,
        files: list[Path],
    ) -> list[ExtractedConfig]:
        """Parse the AI response into ExtractedConfig objects."""
        configs = []
        
        try:
            data = self._extract_json_array(response)
            
            for item in data:
                if not isinstance(item, dict):
                    continue
                
                key = item.get("key", "")
                if not key:
                    continue
                
                configs.append(ExtractedConfig(
                    key=key,
                    description=item.get("description", ""),
                    default=item.get("default"),
                    required=item.get("required", False),
                    source=item.get("source", "config"),
                    file=str(files[0]) if files else "",
                    line=1,
                ))
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI config response: {e}")
        except Exception as e:
            logger.warning(f"Error processing AI config response: {e}")
        
        return configs
    
    async def _extract_side_effects(
        self,
        files: list[Path],
        service_name: str,
    ) -> list[ExtractedSideEffect]:
        """Use AI to extract side effects (DB queries, external API calls)."""
        if not files:
            return []
        
        # Sample files for side effects (limit to reduce tokens)
        sample_files = files[:5]
        
        code_context = []
        for f in sample_files:
            try:
                content = f.read_text(errors='ignore')
                if len(content) > 10000:
                    content = content[:10000] + "\n... (truncated)"
                code_context.append(f"=== FILE: {f.name} ===\n{content}")
            except Exception:
                pass
        
        if not code_context:
            return []
        
        prompt = f"""Analyze these code files from {service_name} and identify side effects:

1. Database operations (SELECT, INSERT, UPDATE, DELETE)
2. External API calls (HTTP requests to other services)
3. File system operations
4. Message queue operations
5. Cache operations

CODE FILES:
{"".join(code_context)}

OUTPUT FORMAT (JSON array):
[
  {{
    "type": "database",
    "operation": "SELECT",
    "table": "users",
    "description": "Fetch user by email",
    "file": "UserController.php"
  }},
  {{
    "type": "external_api",
    "service": "PaymentGateway",
    "method": "POST",
    "endpoint": "/v1/charges",
    "description": "Create payment charge"
  }}
]

Only output valid JSON."""

        system_prompt = """You are an expert at identifying side effects in code.
Find all operations that modify state or communicate with external systems.
Look for:
- SQL queries (raw or ORM)
- HTTP client calls
- File read/write operations
- Queue publish/consume
- Cache get/set"""

        response = await self._call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=16000,  # Increased to avoid truncation
            operation="analysis",
        )
        
        return self._parse_side_effects_response(response, sample_files)
    
    def _parse_side_effects_response(
        self,
        response: str,
        files: list[Path],
    ) -> list[ExtractedSideEffect]:
        """Parse the AI response into ExtractedSideEffect objects."""
        side_effects = []
        
        try:
            data = self._extract_json_array(response)
            
            for item in data:
                if not isinstance(item, dict):
                    continue
                
                effect_type = item.get("type", "").lower()
                
                # Map to SideEffectCategory
                if effect_type == "database":
                    category = SideEffectCategory.DATABASE
                elif effect_type == "external_api":
                    category = SideEffectCategory.EXTERNAL_API
                elif effect_type == "file":
                    category = SideEffectCategory.FILE
                elif effect_type == "cache":
                    category = SideEffectCategory.CACHE
                elif effect_type == "queue":
                    category = SideEffectCategory.QUEUE
                else:
                    category = SideEffectCategory.DATABASE
                
                description = item.get("description", "")
                if item.get("operation"):
                    description = f"{item.get('operation')} - {description}"
                if item.get("table"):
                    description += f" (table: {item.get('table')})"
                
                side_effects.append(ExtractedSideEffect(
                    category=category,
                    operation=item.get("operation", "UNKNOWN"),
                    target=item.get("table") or item.get("endpoint") or item.get("service"),
                    description=description,
                    file=item.get("file", str(files[0]) if files else ""),
                    line=1,
                ))
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI side effects response: {e}")
        except Exception as e:
            logger.warning(f"Error processing AI side effects response: {e}")
        
        return side_effects
    
    def _analyze_dependencies(self, repo_path: Path) -> list[ExtractedDependency]:
        """Extract dependencies from manifest files (non-AI, simple parsing)."""
        dependencies = []
        
        # Check various dependency files
        manifests = [
            ("package.json", "npm"),
            ("requirements.txt", "pip"),
            ("Pipfile", "pipenv"),
            ("composer.json", "composer"),
            ("go.mod", "go"),
            ("Cargo.toml", "cargo"),
            ("pom.xml", "maven"),
        ]
        
        for filename, manager in manifests:
            manifest_path = repo_path / filename
            if manifest_path.exists():
                try:
                    content = manifest_path.read_text()
                    if filename == "package.json":
                        data = json.loads(content)
                        for name, version in data.get("dependencies", {}).items():
                            dependencies.append(ExtractedDependency(
                                name=name,
                                version=version,
                                source=manager,
                            ))
                    elif filename == "requirements.txt":
                        for line in content.split("\n"):
                            line = line.strip()
                            if line and not line.startswith("#"):
                                parts = line.split("==")
                                name = parts[0].split(">=")[0].split("<=")[0].strip()
                                version = parts[1] if len(parts) > 1 else "*"
                                dependencies.append(ExtractedDependency(
                                    name=name,
                                    version=version,
                                    source=manager,
                                ))
                except Exception as e:
                    logger.warning(f"Failed to parse {filename}: {e}")
        
        return dependencies
