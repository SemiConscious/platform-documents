"""
Base documentation strategy.

Defines the abstract interface for type-specific documentation strategies.
Each repository type (API, Terraform, Lambda, etc.) implements its own
strategy that knows how to produce beautiful, detailed documentation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional
import logging

from ...analyzers.models import AnalysisResult
from ...analyzers.repo_type_detector import RepoType

logger = logging.getLogger("doc-agent.documentation.strategies")


@dataclass
class DocumentSpec:
    """Specification for a required document."""
    path: str  # Relative path from service/repo root
    title: str
    description: str
    required: bool = True
    priority: int = 1  # 1 = highest priority
    
    def __hash__(self):
        return hash(self.path)


@dataclass
class GeneratedDocument:
    """A generated documentation file."""
    path: Path
    title: str
    content: str
    spec: Optional[DocumentSpec] = None
    generated_at: datetime = field(default_factory=datetime.utcnow)
    token_usage: dict[str, int] = field(default_factory=dict)
    quality_scores: dict[str, float] = field(default_factory=dict)
    
    @property
    def word_count(self) -> int:
        """Count words in the document."""
        return len(self.content.split())
    
    @property
    def has_diagrams(self) -> bool:
        """Check if document contains diagrams."""
        return "```mermaid" in self.content or "```" in self.content and "flowchart" in self.content
    
    @property
    def has_code_examples(self) -> bool:
        """Check if document contains code examples."""
        # Count code blocks (excluding mermaid)
        code_blocks = self.content.count("```")
        mermaid_blocks = self.content.count("```mermaid")
        return (code_blocks - mermaid_blocks * 2) >= 2
    
    @property
    def has_tables(self) -> bool:
        """Check if document contains tables."""
        return "|" in self.content and "---" in self.content


@dataclass
class DocumentSet:
    """Collection of generated documents for a repository."""
    repo_name: str
    repo_type: RepoType
    documents: list[GeneratedDocument] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    generation_time: float = 0.0
    total_tokens: dict[str, int] = field(default_factory=dict)
    
    def add_document(self, doc: GeneratedDocument) -> None:
        """Add a document to the set."""
        self.documents.append(doc)
        for key, value in doc.token_usage.items():
            self.total_tokens[key] = self.total_tokens.get(key, 0) + value
    
    def get_document(self, path: str) -> Optional[GeneratedDocument]:
        """Get a document by path."""
        for doc in self.documents:
            if str(doc.path).endswith(path):
                return doc
        return None
    
    @property
    def total_words(self) -> int:
        """Total word count across all documents."""
        return sum(doc.word_count for doc in self.documents)
    
    @property
    def has_all_diagrams(self) -> bool:
        """Check if key documents have diagrams."""
        key_docs = ["architecture.md", "README.md"]
        for path in key_docs:
            doc = self.get_document(path)
            if doc and not doc.has_diagrams:
                return False
        return True


class QualityCriterionType(Enum):
    """Types of quality criteria."""
    COMPLETENESS = "completeness"      # All required docs present
    ACCURACY = "accuracy"              # Content matches code
    DIAGRAMS = "diagrams"              # Visualizations present
    EXAMPLES = "examples"              # Working code examples
    CROSS_REFERENCES = "cross_references"  # Links to related docs
    DEPTH = "depth"                    # Level of detail
    FORMATTING = "formatting"          # Markdown quality


@dataclass
class QualityCriterion:
    """A quality criterion for documentation."""
    name: str
    description: str
    criterion_type: QualityCriterionType
    weight: float = 1.0
    min_threshold: float = 0.8
    check_function: Optional[str] = None  # Name of check method
    
    def __hash__(self):
        return hash(self.name)


@dataclass
class QualityScore:
    """Quality score for a document or document set."""
    criterion: QualityCriterion
    score: float  # 0.0 to 1.0
    passed: bool
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class DocumentationStrategy(ABC):
    """
    Abstract base class for type-specific documentation strategies.
    
    Each repository type implements its own strategy that knows:
    - What documents are required
    - How to extract information from the code
    - How to generate beautiful, detailed documentation
    - What quality criteria to enforce
    """
    
    # Override in subclasses
    repo_type: RepoType = RepoType.UNKNOWN
    name: str = "base"
    description: str = "Base documentation strategy"
    
    def __init__(
        self,
        output_dir: Path,
        llm_client: Any = None,
        token_tracker: Any = None,
        config: Optional[dict] = None,
        model_selector: Any = None,
    ):
        """
        Initialize the strategy.
        
        Args:
            output_dir: Base directory for generated documentation
            llm_client: LLM client for AI-powered generation
            token_tracker: Token usage tracker
            config: Application configuration dict
            model_selector: Model selector for tiered model usage
        """
        self.output_dir = output_dir
        self.llm_client = llm_client
        self.token_tracker = token_tracker
        self.config = config or {}
        self.model_selector = model_selector
        self.logger = logging.getLogger(f"doc-agent.documentation.{self.name}")
    
    @abstractmethod
    def get_required_documents(self) -> list[DocumentSpec]:
        """
        Get the list of required documents for this repository type.
        
        Returns:
            List of DocumentSpec objects defining required documentation
        """
        pass
    
    @abstractmethod
    def get_quality_criteria(self) -> list[QualityCriterion]:
        """
        Get quality criteria for this repository type.
        
        Returns:
            List of QualityCriterion objects defining quality requirements
        """
        pass
    
    @abstractmethod
    async def generate(
        self,
        repo_path: Path,
        analysis: AnalysisResult,
        service_name: str,
        github_url: Optional[str] = None,
        existing_docs: Optional[dict[str, str]] = None,
    ) -> DocumentSet:
        """
        Generate documentation for the repository.
        
        Args:
            repo_path: Path to the repository
            analysis: Analysis result from code analyzers
            service_name: Name of the service/repository
            github_url: GitHub URL for source links
            existing_docs: Existing documentation to enhance
            
        Returns:
            DocumentSet containing all generated documents
        """
        pass
    
    async def evaluate_quality(self, doc_set: DocumentSet) -> list[QualityScore]:
        """
        Evaluate the quality of generated documentation.
        
        Args:
            doc_set: The generated document set
            
        Returns:
            List of QualityScore objects
        """
        scores = []
        criteria = self.get_quality_criteria()
        
        for criterion in criteria:
            score = await self._evaluate_criterion(criterion, doc_set)
            scores.append(score)
        
        return scores
    
    async def _evaluate_criterion(
        self,
        criterion: QualityCriterion,
        doc_set: DocumentSet,
    ) -> QualityScore:
        """Evaluate a single quality criterion."""
        issues = []
        recommendations = []
        score = 0.0
        
        if criterion.criterion_type == QualityCriterionType.COMPLETENESS:
            score, issues = self._check_completeness(doc_set)
            if score < criterion.min_threshold:
                recommendations.append("Add missing required documents")
        
        elif criterion.criterion_type == QualityCriterionType.DIAGRAMS:
            score, issues = self._check_diagrams(doc_set)
            if score < criterion.min_threshold:
                recommendations.append("Add architecture or flow diagrams")
        
        elif criterion.criterion_type == QualityCriterionType.EXAMPLES:
            score, issues = self._check_examples(doc_set)
            if score < criterion.min_threshold:
                recommendations.append("Add working code examples")
        
        elif criterion.criterion_type == QualityCriterionType.DEPTH:
            score, issues = self._check_depth(doc_set)
            if score < criterion.min_threshold:
                recommendations.append("Add more detailed explanations")
        
        else:
            score = 0.5  # Default for unimplemented checks
        
        return QualityScore(
            criterion=criterion,
            score=score,
            passed=score >= criterion.min_threshold,
            issues=issues,
            recommendations=recommendations,
        )
    
    def _check_completeness(self, doc_set: DocumentSet) -> tuple[float, list[str]]:
        """Check if all required documents are present."""
        required = self.get_required_documents()
        required_paths = {d.path for d in required if d.required}
        
        present = set()
        for doc in doc_set.documents:
            for req_path in required_paths:
                if str(doc.path).endswith(req_path):
                    present.add(req_path)
        
        missing = required_paths - present
        score = len(present) / len(required_paths) if required_paths else 1.0
        
        issues = [f"Missing: {path}" for path in missing]
        return score, issues
    
    def _check_diagrams(self, doc_set: DocumentSet) -> tuple[float, list[str]]:
        """Check if diagrams are present where needed."""
        diagram_required = ["architecture.md", "data-flows.md", "call-flows.md"]
        has_diagrams = 0
        total = 0
        issues = []
        
        for path in diagram_required:
            doc = doc_set.get_document(path)
            if doc:
                total += 1
                if doc.has_diagrams:
                    has_diagrams += 1
                else:
                    issues.append(f"No diagram in {path}")
        
        # Also check README for architecture diagram
        readme = doc_set.get_document("README.md")
        if readme:
            total += 1
            if readme.has_diagrams:
                has_diagrams += 1
            else:
                issues.append("No architecture diagram in README")
        
        score = has_diagrams / total if total > 0 else 0.5
        return score, issues
    
    def _check_examples(self, doc_set: DocumentSet) -> tuple[float, list[str]]:
        """Check if code examples are present."""
        example_docs = ["README.md", "api-reference.md", "examples.md", "api/README.md"]
        has_examples = 0
        total = 0
        issues = []
        
        for path in example_docs:
            doc = doc_set.get_document(path)
            if doc:
                total += 1
                if doc.has_code_examples:
                    has_examples += 1
                else:
                    issues.append(f"No code examples in {path}")
        
        score = has_examples / total if total > 0 else 0.5
        return score, issues
    
    def _check_depth(self, doc_set: DocumentSet) -> tuple[float, list[str]]:
        """Check documentation depth/detail level."""
        issues = []
        
        # Check average word count per document
        avg_words = doc_set.total_words / len(doc_set.documents) if doc_set.documents else 0
        
        # Expect at least 200 words per document on average
        word_score = min(avg_words / 200, 1.0)
        
        # Check for tables (indicates structured data)
        docs_with_tables = sum(1 for doc in doc_set.documents if doc.has_tables)
        table_score = docs_with_tables / len(doc_set.documents) if doc_set.documents else 0
        
        if avg_words < 100:
            issues.append(f"Documents are too brief (avg {avg_words:.0f} words)")
        
        if table_score < 0.3:
            issues.append("Consider adding more structured tables")
        
        score = (word_score * 0.6) + (table_score * 0.4)
        return score, issues
    
    async def _call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        operation: str = "generate",
        operation_type: Optional[str] = None,
    ) -> str:
        """
        Call the LLM for content generation.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens in response
            operation: Operation name for token tracking
            operation_type: Type of operation for model selection 
                           (analysis, templates, writing, review, summary, extraction)
            
        Returns:
            Generated text
        """
        if not self.llm_client:
            return ""
        
        messages = [{"role": "user", "content": prompt}]
        
        # Determine model using model selector if available
        model = None
        
        if self.model_selector and operation_type:
            # Import here to avoid circular dependency
            from ...llm import Operation
            try:
                op_enum = Operation(operation_type)
                model = self.model_selector.get_model(op_enum)
            except (ValueError, AttributeError):
                pass
        
        if not model:
            # Fallback: try to get from config
            llm_config = self.config.get("llm", {})
            model = llm_config.get("model")
        
        if not model:
            # Final fallback: detect client type
            if hasattr(self.llm_client, 'api_key'):
                # Direct Anthropic API
                model = "claude-sonnet-4-20250514"
            else:
                # AWS Bedrock
                model = "anthropic.claude-3-5-sonnet-20241022-v2:0"
        
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        try:
            self.logger.debug(f"Calling LLM: model={model}, operation={operation}")
            response = await self.llm_client.messages.create(**kwargs)
            
            # Track tokens
            if self.token_tracker and hasattr(response, "usage"):
                self.token_tracker.record(response, operation)
            
            return response.content[0].text if response.content else ""
        
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            return ""
    
    def _generate_mermaid_diagram(
        self,
        diagram_type: str,
        elements: list[dict],
        connections: list[tuple[str, str, Optional[str]]] = None,
    ) -> str:
        """
        Generate a Mermaid diagram.
        
        Args:
            diagram_type: 'flowchart', 'sequenceDiagram', 'classDiagram', etc.
            elements: List of nodes/elements
            connections: List of (from, to, label) tuples
            
        Returns:
            Mermaid diagram string
        """
        lines = [f"```mermaid", diagram_type]
        
        if diagram_type.startswith("flowchart"):
            # Group elements by category if available
            groups = {}
            for elem in elements:
                group = elem.get("group", "default")
                if group not in groups:
                    groups[group] = []
                groups[group].append(elem)
            
            # Generate subgraphs for groups
            for group_name, group_elems in groups.items():
                if group_name != "default":
                    safe_name = group_name.replace(" ", "_").replace("-", "_")
                    lines.append(f"    subgraph {safe_name}[{group_name}]")
                
                for elem in group_elems:
                    node_id = elem.get("id", elem.get("name", "node"))
                    safe_id = node_id.replace("-", "_").replace(" ", "_")
                    label = elem.get("label", node_id)
                    shape = elem.get("shape", "rect")
                    
                    if shape == "rect":
                        lines.append(f"        {safe_id}[{label}]")
                    elif shape == "round":
                        lines.append(f"        {safe_id}({label})")
                    elif shape == "diamond":
                        lines.append(f"        {safe_id}{{{label}}}")
                    elif shape == "cylinder":
                        lines.append(f"        {safe_id}[({label})]")
                
                if group_name != "default":
                    lines.append("    end")
            
            # Add connections
            if connections:
                for from_node, to_node, label in connections:
                    safe_from = from_node.replace("-", "_").replace(" ", "_")
                    safe_to = to_node.replace("-", "_").replace(" ", "_")
                    if label:
                        lines.append(f"    {safe_from} -->|{label}| {safe_to}")
                    else:
                        lines.append(f"    {safe_from} --> {safe_to}")
        
        lines.append("```")
        return "\n".join(lines)
    
    def _github_link(self, github_url: str, file_path: str, line: int = None) -> str:
        """Generate a GitHub link to a file."""
        if not github_url:
            return f"`{file_path}`"
        
        url = f"{github_url}/blob/main/{file_path}"
        if line:
            url += f"#L{line}"
        return f"[`{file_path}`]({url})"
