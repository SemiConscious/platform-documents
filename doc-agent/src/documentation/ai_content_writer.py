"""
AI-Powered Content Writer.

Uses Claude (preferably Opus 4.5) to generate rich, contextual
documentation content based on code analysis and templates.

This is the quality-critical component - it produces the actual
documentation that developers will read.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .ai_template_generator import DocumentTemplate, DocumentationPlan

logger = logging.getLogger("doc-agent.documentation.ai_content_writer")


@dataclass
class GeneratedContent:
    """Generated documentation content for a single document."""
    path: str
    title: str
    content: str
    word_count: int = 0
    sections_generated: int = 0


@dataclass 
class ContentGenerationResult:
    """Result of content generation for a repository."""
    service_name: str
    documents: list[GeneratedContent]
    total_tokens_used: int = 0
    estimated_cost: float = 0.0


class AIContentWriter:
    """
    AI-powered documentation content writer.
    
    Takes code analysis results and documentation plans, then uses
    Claude to write comprehensive, developer-friendly documentation.
    
    Uses the "writing" operation type, which should map to the highest
    quality model (Opus 4.5) for best results.
    """
    
    def __init__(
        self,
        llm_client: Any,
        model_selector: Any = None,
        token_tracker: Any = None,
    ):
        """
        Initialize the content writer.
        
        Args:
            llm_client: Anthropic client (Bedrock or direct)
            model_selector: Model selector for operation-specific models
            token_tracker: Token usage tracker
        """
        self.llm_client = llm_client
        self.model_selector = model_selector
        self.token_tracker = token_tracker
    
    def _get_model(self, operation_type: str = "writing") -> str:
        """Get the appropriate model for content writing."""
        if self.model_selector:
            from ..llm import Operation
            try:
                op = Operation(operation_type)
                return self.model_selector.get_model(op)
            except (ValueError, AttributeError):
                pass
        
        # Fallback - use Opus for writing (quality critical)
        return "us.anthropic.claude-opus-4-5-20251101-v1:0"
    
    def _detect_tech_stack(self, repo_path: Path) -> dict:
        """Detect the technology stack from repository files."""
        tech_stack = {
            "language": "unknown",
            "framework": None,
            "package_manager": None,
            "containerized": False,
        }
        
        # Check for language-specific files
        if (repo_path / "composer.json").exists():
            tech_stack["language"] = "PHP"
            tech_stack["package_manager"] = "Composer"
        elif (repo_path / "package.json").exists():
            tech_stack["language"] = "JavaScript/TypeScript"
            tech_stack["package_manager"] = "npm"
        elif (repo_path / "requirements.txt").exists() or (repo_path / "pyproject.toml").exists():
            tech_stack["language"] = "Python"
            tech_stack["package_manager"] = "pip"
        elif (repo_path / "go.mod").exists():
            tech_stack["language"] = "Go"
            tech_stack["package_manager"] = "go modules"
        elif (repo_path / "Cargo.toml").exists():
            tech_stack["language"] = "Rust"
            tech_stack["package_manager"] = "cargo"
        elif (repo_path / "pom.xml").exists() or (repo_path / "build.gradle").exists():
            tech_stack["language"] = "Java"
            tech_stack["package_manager"] = "Maven/Gradle"
        
        # Check for containerization
        if (repo_path / "Dockerfile").exists() or (repo_path / "docker-compose.yml").exists():
            tech_stack["containerized"] = True
        
        # Check for common frameworks
        if tech_stack["language"] == "PHP":
            if (repo_path / "artisan").exists():
                tech_stack["framework"] = "Laravel"
            elif (repo_path / "application" / "config").exists():
                tech_stack["framework"] = "Kohana"
        elif tech_stack["language"] == "JavaScript/TypeScript":
            if (repo_path / "next.config.js").exists():
                tech_stack["framework"] = "Next.js"
            elif (repo_path / "nuxt.config.js").exists():
                tech_stack["framework"] = "Nuxt.js"
        
        return tech_stack
    
    async def _call_llm(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int = 8000,
        operation: str = "writing",
        use_streaming: bool = True,
    ) -> str:
        """Call the LLM and track tokens, using streaming to avoid timeouts."""
        if not self.llm_client:
            return ""
        
        model = self._get_model(operation)
        logger.debug(f"Writing content with model: {model} (streaming={use_streaming})")
        
        try:
            if use_streaming:
                return await self._call_llm_streaming(
                    prompt, system_prompt, max_tokens, model, operation
                )
            else:
                response = await self.llm_client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}],
                )
                
                if self.token_tracker and hasattr(response, "usage"):
                    self.token_tracker.record(response, f"content_writer_{operation}")
                
                return response.content[0].text if response.content else ""
            
        except Exception as e:
            logger.error(f"Content writing LLM call failed: {e}")
            return ""
    
    async def _call_llm_streaming(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int,
        model: str,
        operation: str,
    ) -> str:
        """Call LLM with streaming to avoid timeouts on long generations."""
        chunks = []
        input_tokens = 0
        output_tokens = 0
        
        try:
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
            
            # Track tokens manually since streaming doesn't return usage the same way
            if self.token_tracker and (input_tokens or output_tokens):
                # Create a simple object with usage info for the tracker
                class UsageInfo:
                    def __init__(self, inp, out):
                        self.usage = type('Usage', (), {'input_tokens': inp, 'output_tokens': out})()
                
                self.token_tracker.record(
                    UsageInfo(input_tokens, output_tokens),
                    f"content_writer_{operation}"
                )
            
            return "".join(chunks)
            
        except Exception as e:
            logger.error(f"Streaming LLM call failed: {e}")
            # Fallback to non-streaming on error
            logger.info("Falling back to non-streaming call...")
            return await self._call_llm(
                prompt, system_prompt, max_tokens, operation, use_streaming=False
            )
    
    async def generate_documentation(
        self,
        plan: DocumentationPlan,
        analysis: Any,
        repo_path: Path,
        github_url: Optional[str] = None,
        max_concurrent: int = 20,
    ) -> ContentGenerationResult:
        """
        Generate complete documentation for a repository.
        
        Uses parallel document generation with bounded concurrency
        to speed up generation while avoiding API rate limits.
        
        Args:
            plan: Documentation plan from template generator
            analysis: Code analysis results
            repo_path: Path to the repository
            github_url: Optional GitHub URL for links
            max_concurrent: Maximum concurrent document writes (default: 3)
            
        Returns:
            ContentGenerationResult with all generated documents
        """
        logger.info(f"Generating documentation content for {plan.service_name}")
        
        templates = plan.get_documents_by_priority()
        logger.info(f"Writing {len(templates)} documents in parallel (max {max_concurrent} concurrent)")
        
        # Semaphore to limit concurrent API calls
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def write_with_semaphore(template: DocumentTemplate) -> Optional[GeneratedContent]:
            """Write a document with semaphore-bounded concurrency."""
            async with semaphore:
                logger.info(f"Writing {template.path}...")
                
                content = await self._write_document(
                    template=template,
                    plan=plan,
                    analysis=analysis,
                    repo_path=repo_path,
                    github_url=github_url,
                )
                
                if content:
                    return GeneratedContent(
                        path=template.path,
                        title=template.title,
                        content=content,
                        word_count=len(content.split()),
                        sections_generated=content.count("\n## ") + content.count("\n# "),
                    )
                return None
        
        # Run all document writes in parallel (bounded by semaphore)
        tasks = [write_with_semaphore(template) for template in templates]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        documents = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to write {templates[i].path}: {result}")
            elif result is not None:
                documents.append(result)
                logger.info(f"Completed {result.path} ({result.word_count} words)")
        
        logger.info(f"Generated {len(documents)} documents for {plan.service_name}")
        
        return ContentGenerationResult(
            service_name=plan.service_name,
            documents=documents,
        )
    
    async def _write_document(
        self,
        template: DocumentTemplate,
        plan: DocumentationPlan,
        analysis: Any,
        repo_path: Path,
        github_url: Optional[str] = None,
    ) -> str:
        """Write a single document based on its template."""
        
        # Build context for the document
        context = self._build_document_context(template, plan, analysis, repo_path, github_url)
        
        # Choose appropriate prompt based on document type
        if "endpoint" in template.path.lower() or "api" in template.path.lower():
            return await self._write_api_document(template, context)
        elif "model" in template.path.lower() or "schema" in template.path.lower():
            return await self._write_models_document(template, context)
        elif "config" in template.path.lower():
            return await self._write_config_document(template, context)
        elif "readme" in template.path.lower():
            return await self._write_readme_document(template, context)
        else:
            return await self._write_generic_document(template, context)
    
    def _build_document_context(
        self,
        template: DocumentTemplate,
        plan: DocumentationPlan,
        analysis: Any,
        repo_path: Path,
        github_url: Optional[str],
    ) -> dict:
        """Build context dictionary for document generation."""
        # Detect tech stack from repo files
        tech_stack = self._detect_tech_stack(repo_path)
        
        context = {
            "service_name": plan.service_name,
            "service_description": plan.description,
            "repo_type": plan.repo_type,
            "key_features": plan.key_features,
            "target_audience": plan.target_audience,
            "github_url": github_url or "",
            "tech_stack": tech_stack,
        }
        
        # Add analysis data if available
        if analysis:
            # Add language from analysis
            context["language"] = getattr(analysis, 'language', tech_stack.get('language', 'unknown'))
            # Endpoints
            endpoints = getattr(analysis, 'endpoints', [])
            context["endpoints"] = [
                {
                    "method": ep.method,
                    "path": ep.path,
                    "description": getattr(ep, 'description', ''),
                    "handler": getattr(ep, 'handler', ''),
                    "parameters": getattr(ep, 'parameters', []),
                }
                for ep in endpoints[:150]  # Increased limit for comprehensive docs
            ]
            
            # Models
            models = getattr(analysis, 'models', [])
            context["models"] = [
                {
                    "name": m.name,
                    "description": getattr(m, 'description', ''),
                    "fields": [
                        {"name": f.name, "type": f.type, "description": getattr(f, 'description', '')}
                        for f in getattr(m, 'fields', [])[:20]
                    ],
                }
                for m in models[:100]  # Increased for comprehensive docs
            ]
            
            # Config
            config = getattr(analysis, 'config', [])
            context["config"] = [
                {
                    "key": c.key,
                    "description": getattr(c, 'description', ''),
                    "default": getattr(c, 'default', None),
                    "required": getattr(c, 'required', False),
                }
                for c in config[:50]
            ]
            
            # Side effects
            side_effects = getattr(analysis, 'side_effects', [])
            context["side_effects"] = [
                {
                    "category": str(getattr(se, 'category', '')),
                    "operation": getattr(se, 'operation', ''),
                    "description": getattr(se, 'description', ''),
                }
                for se in side_effects[:30]
            ]
        
        # Add document linking info
        context["links_to"] = getattr(template, 'links_to', [])
        context["all_documents"] = [
            {"path": d.path, "title": d.title}
            for d in plan.documents
        ]
        
        return context
    
    async def _write_readme_document(
        self,
        template: DocumentTemplate,
        context: dict,
    ) -> str:
        """Write a README/overview document."""
        
        # Extract tech stack info
        tech_stack = context.get('tech_stack', {})
        language = context.get('language', tech_stack.get('language', 'unknown'))
        framework = tech_stack.get('framework', 'N/A')
        package_manager = tech_stack.get('package_manager', 'N/A')
        containerized = tech_stack.get('containerized', False)
        
        # Build links section
        links_to = context.get('links_to', [])
        all_docs = context.get('all_documents', [])
        related_docs_text = ""
        if links_to:
            related_docs_text = "RELATED DOCUMENTS (include links to these in a Documentation section):\n"
            for link in links_to:
                # Find the title for each link
                doc_info = next((d for d in all_docs if d['path'] == link), None)
                title = doc_info['title'] if doc_info else link
                related_docs_text += f"- [{title}]({link})\n"
        elif all_docs:
            related_docs_text = "ALL DOCUMENTATION (include links to these in a Documentation section):\n"
            for doc in all_docs:
                if doc['path'] != template.path:  # Don't link to self
                    related_docs_text += f"- [{doc['title']}]({doc['path']})\n"
        
        prompt = f"""Write a comprehensive README.md for the {context['service_name']} service.

SERVICE INFORMATION:
- Name: {context['service_name']}
- Type: {context['repo_type']}
- Description: {context['service_description']}
- Key Features: {', '.join(context.get('key_features', []))}
- Target Audience: {context['target_audience']}
- GitHub: {context.get('github_url', 'N/A')}

TECHNOLOGY STACK (IMPORTANT - use these exact technologies in your examples):
- Programming Language: {language}
- Framework: {framework}
- Package Manager: {package_manager}
- Containerized: {'Yes (Docker)' if containerized else 'No'}

TEMPLATE REQUIREMENTS:
- Title: {template.title}
- Sections to include: {', '.join(template.sections)}
- Description: {template.description}

AVAILABLE DATA:
- Endpoints: {len(context.get('endpoints', []))} found
- Models: {len(context.get('models', []))} found
- Config variables: {len(context.get('config', []))} found

{related_docs_text}

Write a professional, developer-friendly README that:
1. Clearly explains what this service does
2. Shows how to get started quickly using the CORRECT technology stack above
3. Provides architecture overview
4. Includes a "Documentation" or "Table of Contents" section with links to related documents
5. Includes relevant badges and quick reference

CRITICAL: Use the correct programming language ({language}) and package manager ({package_manager}) in ALL code examples.
Do NOT assume Node.js/npm unless the language is JavaScript/TypeScript.
IMPORTANT: Include markdown links to all related documentation files in a dedicated section.

Use proper Markdown formatting with headers, code blocks, and tables where appropriate.
Make it engaging and useful for developers encountering this service for the first time.

Output ONLY the Markdown content, starting with the title."""

        system_prompt = """You are a senior technical writer creating comprehensive documentation for a software service.
Write detailed, developer-friendly documentation that covers all aspects thoroughly.
Use proper Markdown formatting including headers, code blocks, tables, and lists.
Be COMPREHENSIVE and DETAILED - aim for 800-1200 words minimum.
Include practical examples, code snippets, and step-by-step instructions where helpful.
Document prerequisites, troubleshooting tips, and common pitfalls.
IMPORTANT: Always use the correct programming language and tools as specified in the prompt."""

        return await self._call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=32000,  # High limit to avoid truncation
            operation="writing",
        )
    
    async def _write_api_document(
        self,
        template: DocumentTemplate,
        context: dict,
    ) -> str:
        """Write an API reference document."""
        
        # Format all endpoints for the prompt
        all_endpoints = context.get('endpoints', [])
        endpoints_text = ""
        for ep in all_endpoints[:200]:  # Include more for AI to select from
            endpoints_text += f"\n- {ep['method']} {ep['path']}"
            if ep.get('description'):
                endpoints_text += f": {ep['description']}"
            if ep.get('handler'):
                endpoints_text += f" (handler: {ep['handler']})"
        
        total_endpoints = len(all_endpoints)
        
        # Check if this is a topic-specific document or a general overview
        is_overview = 'readme' in template.path.lower() or 'overview' in template.path.lower()
        
        # Build list of other API documents for reference
        other_api_docs = [
            doc['path'] for doc in context.get('all_documents', [])
            if 'api' in doc['path'].lower() and doc['path'] != template.path
        ]
        # Build topic-aware prompt
        if is_overview:
            # This is an API overview/index document
            prompt = f"""Write an API OVERVIEW document for {context['service_name']}.

SERVICE: {context['service_name']}
DESCRIPTION: {context['service_description']}

THIS DOCUMENT'S PURPOSE:
- Title: {template.title}
- Description: {template.description}
- This is an OVERVIEW/INDEX document

TOTAL ENDPOINTS IN API: {total_endpoints}

ALL AVAILABLE ENDPOINTS:
{endpoints_text}

OTHER API DOCUMENTATION FILES (link to these):
{chr(10).join(f'- {doc}' for doc in other_api_docs) if other_api_docs else 'None'}

REQUIREMENTS FOR THIS OVERVIEW:
1. Provide a high-level introduction to the API
2. Explain authentication methods
3. List ALL endpoint categories with brief descriptions
4. Create a table or index linking to the detailed documentation files listed above
5. Include common patterns, error handling, and rate limiting info
6. Do NOT document individual endpoints in detail - that's for the other files

Output ONLY the Markdown content."""
        else:
            # This is a topic-specific API document
            prompt = f"""Write API documentation for a SPECIFIC TOPIC within {context['service_name']}.

SERVICE: {context['service_name']}
DESCRIPTION: {context['service_description']}

THIS DOCUMENT'S SPECIFIC TOPIC:
- Title: {template.title}
- Description: {template.description}
- Path: {template.path}

ALL ENDPOINTS IN THE API ({total_endpoints} total):
{endpoints_text}

OTHER API DOCUMENTATION FILES (endpoints NOT in this file are documented elsewhere):
{chr(10).join(f'- {doc}' for doc in other_api_docs) if other_api_docs else 'None'}

CRITICAL INSTRUCTIONS:
1. This document covers ONLY: {template.title}
2. From the endpoint list above, SELECT and document ONLY the endpoints that belong to this topic
3. Do NOT document endpoints that belong to other topics - they are covered in the other files listed above
4. For each endpoint you select, provide COMPLETE documentation:
   - HTTP method and path
   - Description
   - Request parameters (table format)
   - Request example with curl
   - Response example
   - Error codes

5. If an endpoint clearly belongs to a different topic (e.g., billing endpoints in an auth doc), SKIP IT

Output ONLY the Markdown content for this specific topic."""

        system_prompt = """You are an API documentation expert creating production-grade API references.

IMPORTANT: You are writing documentation for a MULTI-FILE documentation system.
- If this is an OVERVIEW document: provide high-level info and link to detailed docs
- If this is a TOPIC-SPECIFIC document: ONLY document endpoints relevant to that specific topic

When documenting endpoints:
- Full HTTP method and path
- Detailed description
- All parameters in a table (path, query, body)
- Complete curl request example
- Complete response example
- Error codes

Use consistent formatting, tables for parameters, and proper Markdown syntax.
For topic-specific documents, use your judgment to select only relevant endpoints."""

        return await self._call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=64000,  # High limit to avoid truncation
            operation="writing",
        )
    
    async def _write_models_document(
        self,
        template: DocumentTemplate,
        context: dict,
    ) -> str:
        """Write a data models document."""
        
        # Format all models for the prompt
        all_models = context.get('models', [])
        models_text = ""
        for model in all_models[:150]:
            models_text += f"\n\n### {model['name']}"
            if model.get('description'):
                models_text += f"\n{model['description']}"
            if model.get('fields'):
                models_text += "\nFields:"
                for field in model['fields'][:15]:
                    models_text += f"\n  - {field['name']}: {field['type']}"
                    if field.get('description'):
                        models_text += f" - {field['description']}"
        
        total_models = len(all_models)
        is_overview = 'readme' in template.path.lower() or 'overview' in template.path.lower()
        
        # Build list of other model documents
        other_model_docs = [
            doc['path'] for doc in context.get('all_documents', [])
            if 'model' in doc['path'].lower() and doc['path'] != template.path
        ]
        
        if is_overview:
            prompt = f"""Write a MODELS OVERVIEW document for {context['service_name']}.

SERVICE: {context['service_name']}

THIS DOCUMENT'S PURPOSE:
- Title: {template.title}
- Description: {template.description}
- This is an OVERVIEW/INDEX document

TOTAL MODELS: {total_models}

ALL MODELS:
{models_text if models_text else 'No models discovered'}

OTHER MODEL DOCUMENTATION FILES (link to these):
{chr(10).join(f'- {doc}' for doc in other_model_docs) if other_model_docs else 'None'}

REQUIREMENTS:
1. Provide a high-level overview of the data architecture
2. List all model categories with brief descriptions
3. Create an index linking to detailed documentation files
4. Explain relationships between model groups
5. Do NOT document individual models in detail - that's for the other files

Output ONLY the Markdown content."""
        else:
            prompt = f"""Write data model documentation for a SPECIFIC TOPIC within {context['service_name']}.

SERVICE: {context['service_name']}

THIS DOCUMENT'S SPECIFIC TOPIC:
- Title: {template.title}
- Description: {template.description}
- Path: {template.path}

ALL MODELS ({total_models} total):
{models_text if models_text else 'No models discovered'}

OTHER MODEL DOCUMENTATION FILES (models NOT in this file are documented elsewhere):
{chr(10).join(f'- {doc}' for doc in other_model_docs) if other_model_docs else 'None'}

CRITICAL INSTRUCTIONS:
1. This document covers ONLY: {template.title}
2. SELECT and document ONLY the models that belong to this specific topic
3. Do NOT document models that belong to other topics
4. For each model you select:
   - Purpose and usage
   - Field definitions in a table (name, type, required, description)
   - Validation rules
   - Example JSON
   - Relationships to other models

Output ONLY the Markdown content for this specific topic."""

        system_prompt = """You are a technical writer specializing in data model documentation.

IMPORTANT: You are writing for a MULTI-FILE documentation system.
- If this is an OVERVIEW: provide high-level info and link to detailed docs  
- If this is a TOPIC-SPECIFIC document: ONLY document models relevant to that topic

For each model, include:
- Purpose and when to use it
- Complete field listing in a table (name, type, required, description)
- Validation rules and constraints
- Complete JSON example with realistic data
- Relationships to other models
- Common use cases and patterns
Include an entity-relationship diagram description and document all relationships.
Do NOT abbreviate or skip models - document every single one provided."""

        return await self._call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=64000,  # High limit to avoid truncation
            operation="writing",
        )
    
    async def _write_config_document(
        self,
        template: DocumentTemplate,
        context: dict,
    ) -> str:
        """Write a configuration document."""
        
        # Format config for the prompt (use all available, up to 100)
        config_text = ""
        for cfg in context.get('config', [])[:100]:
            config_text += f"\n- {cfg['key']}"
            if cfg.get('description'):
                config_text += f": {cfg['description']}"
            if cfg.get('default'):
                config_text += f" (default: {cfg['default']})"
            if cfg.get('required'):
                config_text += " [REQUIRED]"
        
        prompt = f"""Write comprehensive configuration documentation for {context['service_name']}.

SERVICE: {context['service_name']}

CONFIGURATION VARIABLES DISCOVERED:
{config_text if config_text else 'Document typical configuration for this service type'}

TEMPLATE REQUIREMENTS:
- Title: {template.title}
- Sections: {', '.join(template.sections)}

Write documentation that includes:
1. Overview of configuration approach
2. Environment variables section with:
   - Variable name
   - Description
   - Type and format
   - Default value
   - Whether required
   - Example values
3. Configuration files section if applicable
4. Environment-specific configurations (dev, staging, prod)
5. Security considerations for sensitive values
6. Example .env file

Use Markdown tables for variable listings.

Output ONLY the Markdown content."""

        system_prompt = """You are a DevOps documentation expert creating comprehensive configuration guides.
Create DETAILED documentation - aim for 1000-2000 words.
Include:
- Complete table of all configuration variables (name, type, default, required, description)
- Example values for each variable
- Environment-specific configurations (dev, staging, production)
- Complete .env file example
- Docker/Kubernetes configuration if applicable
- Security considerations for sensitive values
- Troubleshooting common configuration issues
Do NOT abbreviate - document every configuration variable provided."""

        return await self._call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=32000,  # High limit to avoid truncation
            operation="writing",
        )
    
    async def _write_generic_document(
        self,
        template: DocumentTemplate,
        context: dict,
    ) -> str:
        """Write a generic document based on template."""
        
        # Extract tech stack info
        tech_stack = context.get('tech_stack', {})
        language = context.get('language', tech_stack.get('language', 'unknown'))
        
        prompt = f"""Write documentation for "{template.title}" for the {context['service_name']} service.

SERVICE INFORMATION:
- Name: {context['service_name']}
- Type: {context['repo_type']}
- Description: {context['service_description']}
- Key Features: {', '.join(context.get('key_features', []))}
- Programming Language: {language}
- Package Manager: {tech_stack.get('package_manager', 'N/A')}

DOCUMENT REQUIREMENTS:
- Title: {template.title}
- Purpose: {template.description}
- Sections to include: {', '.join(template.sections)}

AVAILABLE CONTEXT:
- {len(context.get('endpoints', []))} API endpoints documented
- {len(context.get('models', []))} data models documented
- {len(context.get('config', []))} configuration variables
- {len(context.get('side_effects', []))} side effects (DB, external APIs)

Write comprehensive documentation following the template requirements.
Make it practical and useful for the target audience ({context['target_audience']}).
Use proper Markdown formatting.
IMPORTANT: Use the correct programming language ({language}) in any code examples.

Output ONLY the Markdown content."""

        system_prompt = """You are a senior technical writer creating comprehensive documentation.
Create DETAILED, well-structured documentation - aim for 800-1500 words minimum.
Follow the template sections provided and expand each section thoroughly.
Include practical examples, code snippets, and step-by-step instructions.
Document edge cases, best practices, and common pitfalls.
Always use the correct programming language as specified."""

        return await self._call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=32000,  # High limit to avoid truncation
            operation="writing",
        )
