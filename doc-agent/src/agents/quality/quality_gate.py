"""
Quality Gate for documentation.

Demands high-quality documentation and flags repositories that need more work.
Provides detailed scoring, issue tracking, and actionable recommendations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional
import logging
import re

from ...analyzers.repo_type_detector import RepoType, get_documentation_requirements
from ...documentation.strategies.base import (
    DocumentSet,
    GeneratedDocument,
    QualityCriterion,
    QualityCriterionType,
    QualityScore,
)

logger = logging.getLogger("doc-agent.quality.gate")


class IssueSeverity(Enum):
    """Severity levels for quality issues."""
    CRITICAL = "critical"  # Must be fixed
    WARNING = "warning"    # Should be fixed
    INFO = "info"          # Nice to have


@dataclass
class QualityIssue:
    """A documentation quality issue."""
    severity: IssueSeverity
    category: str
    message: str
    document: Optional[str] = None
    line: Optional[int] = None
    recommendation: Optional[str] = None
    
    def __str__(self) -> str:
        loc = f" ({self.document}" if self.document else ""
        if self.line:
            loc += f":{self.line}"
        if loc:
            loc += ")"
        return f"[{self.severity.value.upper()}] {self.category}: {self.message}{loc}"


@dataclass
class QualityReport:
    """Comprehensive quality report for a repository."""
    repo_name: str
    repo_type: RepoType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Scores
    overall_score: float = 0.0
    scores_by_criterion: dict[str, float] = field(default_factory=dict)
    
    # Pass/fail
    passing: bool = False
    threshold: float = 0.80
    
    # Issues
    issues: list[QualityIssue] = field(default_factory=list)
    
    # Recommendations
    recommendations: list[str] = field(default_factory=list)
    
    # Document stats
    document_count: int = 0
    total_words: int = 0
    diagram_count: int = 0
    example_count: int = 0
    
    @property
    def critical_issues(self) -> list[QualityIssue]:
        """Get critical issues."""
        return [i for i in self.issues if i.severity == IssueSeverity.CRITICAL]
    
    @property
    def warning_issues(self) -> list[QualityIssue]:
        """Get warning issues."""
        return [i for i in self.issues if i.severity == IssueSeverity.WARNING]
    
    @property
    def has_critical_issues(self) -> bool:
        """Check if there are critical issues."""
        return len(self.critical_issues) > 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "repo_name": self.repo_name,
            "repo_type": self.repo_type.value,
            "timestamp": self.timestamp.isoformat(),
            "overall_score": round(self.overall_score * 100, 1),
            "passing": self.passing,
            "threshold": round(self.threshold * 100, 1),
            "scores": {k: round(v * 100, 1) for k, v in self.scores_by_criterion.items()},
            "issue_count": len(self.issues),
            "critical_count": len(self.critical_issues),
            "warning_count": len(self.warning_issues),
            "document_count": self.document_count,
            "total_words": self.total_words,
            "diagram_count": self.diagram_count,
            "example_count": self.example_count,
        }


@dataclass
class AggregateQualityReport:
    """Aggregate quality report across multiple repositories."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    total_repos: int = 0
    passing_repos: int = 0
    failing_repos: int = 0
    average_score: float = 0.0
    reports: list[QualityReport] = field(default_factory=list)
    
    @property
    def passing_percentage(self) -> float:
        """Percentage of repos passing."""
        return (self.passing_repos / self.total_repos * 100) if self.total_repos > 0 else 0.0
    
    @property
    def repos_needing_work(self) -> list[QualityReport]:
        """Get repos that need more work."""
        return [r for r in self.reports if not r.passing]
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_repos": self.total_repos,
            "passing_repos": self.passing_repos,
            "failing_repos": self.failing_repos,
            "passing_percentage": round(self.passing_percentage, 1),
            "average_score": round(self.average_score * 100, 1),
            "repos_needing_work": [
                {"name": r.repo_name, "score": round(r.overall_score * 100, 1), "issues": len(r.issues)}
                for r in self.repos_needing_work
            ],
        }


class QualityGate:
    """
    Quality gate that demands excellence in documentation.
    
    Evaluates documentation against type-specific criteria and
    flags repositories that don't meet quality standards.
    """
    
    # Minimum thresholds by category (strict!)
    THRESHOLDS = {
        "completeness": 0.90,      # All required docs present
        "accuracy": 0.85,          # Content matches code
        "diagrams": 0.80,          # Visualizations present
        "examples": 0.85,          # Working examples
        "cross_references": 0.75,  # Links to related docs
        "depth": 0.75,             # Level of detail
        "formatting": 0.80,        # Markdown quality
    }
    
    # Minimum word counts for quality
    MIN_WORDS_PER_DOC = 150
    MIN_TOTAL_WORDS = 500
    
    # Required diagram documents
    DIAGRAM_REQUIRED = ["README.md", "architecture.md", "data-flows.md"]
    
    # Required example documents
    EXAMPLE_REQUIRED = ["README.md", "api/README.md", "examples.md", "api/endpoints.md"]
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize the quality gate.
        
        Args:
            strict_mode: If True, use stricter thresholds
        """
        self.strict_mode = strict_mode
        self.thresholds = self.THRESHOLDS.copy()
        
        if strict_mode:
            # Increase thresholds in strict mode
            self.thresholds = {k: min(v + 0.05, 0.98) for k, v in self.thresholds.items()}
    
    async def evaluate(
        self,
        doc_set: DocumentSet,
        strategy: Any = None,
    ) -> QualityReport:
        """
        Evaluate documentation quality for a repository.
        
        Args:
            doc_set: The generated documentation set
            strategy: The documentation strategy used (for type-specific criteria)
            
        Returns:
            QualityReport with scores, issues, and recommendations
        """
        report = QualityReport(
            repo_name=doc_set.repo_name,
            repo_type=doc_set.repo_type,
            threshold=self.thresholds.get("completeness", 0.80),
        )
        
        # Collect document statistics
        report.document_count = len(doc_set.documents)
        report.total_words = doc_set.total_words
        report.diagram_count = sum(1 for d in doc_set.documents if d.has_diagrams)
        report.example_count = sum(1 for d in doc_set.documents if d.has_code_examples)
        
        # Run quality checks
        scores = {}
        
        # 1. Completeness check
        completeness_score, completeness_issues = self._check_completeness(doc_set, strategy)
        scores["completeness"] = completeness_score
        report.issues.extend(completeness_issues)
        
        # 2. Diagram check
        diagram_score, diagram_issues = self._check_diagrams(doc_set)
        scores["diagrams"] = diagram_score
        report.issues.extend(diagram_issues)
        
        # 3. Example check
        example_score, example_issues = self._check_examples(doc_set)
        scores["examples"] = example_score
        report.issues.extend(example_issues)
        
        # 4. Depth check
        depth_score, depth_issues = self._check_depth(doc_set)
        scores["depth"] = depth_score
        report.issues.extend(depth_issues)
        
        # 5. Formatting check
        formatting_score, formatting_issues = self._check_formatting(doc_set)
        scores["formatting"] = formatting_score
        report.issues.extend(formatting_issues)
        
        # 6. Cross-reference check
        xref_score, xref_issues = self._check_cross_references(doc_set)
        scores["cross_references"] = xref_score
        report.issues.extend(xref_issues)
        
        # Calculate overall score (weighted average)
        weights = {
            "completeness": 1.0,
            "diagrams": 0.9,
            "examples": 0.8,
            "depth": 0.7,
            "formatting": 0.5,
            "cross_references": 0.6,
        }
        
        total_weight = sum(weights.values())
        weighted_sum = sum(scores[k] * weights.get(k, 0.5) for k in scores)
        report.overall_score = weighted_sum / total_weight
        
        # Store individual scores
        report.scores_by_criterion = scores
        
        # Determine pass/fail
        failing_criteria = [
            k for k, v in scores.items()
            if v < self.thresholds.get(k, 0.75)
        ]
        report.passing = len(failing_criteria) == 0 and report.overall_score >= 0.75
        
        # Generate recommendations
        report.recommendations = self._generate_recommendations(
            doc_set, scores, failing_criteria, report.issues
        )
        
        return report
    
    def _check_completeness(
        self,
        doc_set: DocumentSet,
        strategy: Any,
    ) -> tuple[float, list[QualityIssue]]:
        """Check if all required documents are present."""
        issues = []
        
        # Get requirements for this repo type
        requirements = get_documentation_requirements(doc_set.repo_type)
        required_docs = requirements.get("required_docs", ["README.md"])
        
        # Also use strategy requirements if available
        if strategy and hasattr(strategy, "get_required_documents"):
            strategy_docs = strategy.get_required_documents()
            required_docs = list(set(required_docs + [d.path for d in strategy_docs if d.required]))
        
        present = set()
        for doc in doc_set.documents:
            doc_path = str(doc.path)
            for req in required_docs:
                if doc_path.endswith(req):
                    present.add(req)
        
        missing = set(required_docs) - present
        
        for doc_path in missing:
            issues.append(QualityIssue(
                severity=IssueSeverity.CRITICAL,
                category="Completeness",
                message=f"Missing required document: {doc_path}",
                recommendation=f"Create {doc_path} with appropriate content",
            ))
        
        score = len(present) / len(required_docs) if required_docs else 1.0
        return score, issues
    
    def _check_diagrams(self, doc_set: DocumentSet) -> tuple[float, list[QualityIssue]]:
        """Check if diagrams are present in key documents."""
        issues = []
        diagram_docs = 0
        diagram_expected = 0
        
        for path in self.DIAGRAM_REQUIRED:
            doc = doc_set.get_document(path)
            if doc:
                diagram_expected += 1
                if doc.has_diagrams:
                    diagram_docs += 1
                else:
                    issues.append(QualityIssue(
                        severity=IssueSeverity.WARNING,
                        category="Diagrams",
                        message=f"No diagram found in {path}",
                        document=path,
                        recommendation="Add a Mermaid architecture or flow diagram",
                    ))
        
        # Check README specifically (critical if missing)
        readme = doc_set.get_document("README.md")
        if readme and not readme.has_diagrams:
            # Upgrade to critical if README has no diagram
            for issue in issues:
                if issue.document == "README.md":
                    issue.severity = IssueSeverity.CRITICAL
        
        score = diagram_docs / diagram_expected if diagram_expected > 0 else 0.5
        return score, issues
    
    def _check_examples(self, doc_set: DocumentSet) -> tuple[float, list[QualityIssue]]:
        """Check if code examples are present."""
        issues = []
        example_docs = 0
        example_expected = 0
        
        for path in self.EXAMPLE_REQUIRED:
            doc = doc_set.get_document(path)
            if doc:
                example_expected += 1
                if doc.has_code_examples:
                    example_docs += 1
                else:
                    issues.append(QualityIssue(
                        severity=IssueSeverity.WARNING,
                        category="Examples",
                        message=f"No code examples found in {path}",
                        document=path,
                        recommendation="Add working code examples demonstrating usage",
                    ))
        
        # Also check overall example density
        total_with_examples = sum(1 for d in doc_set.documents if d.has_code_examples)
        if total_with_examples < len(doc_set.documents) * 0.3:
            issues.append(QualityIssue(
                severity=IssueSeverity.INFO,
                category="Examples",
                message="Low overall code example density",
                recommendation="Add more code examples throughout documentation",
            ))
        
        score = example_docs / example_expected if example_expected > 0 else 0.5
        return score, issues
    
    def _check_depth(self, doc_set: DocumentSet) -> tuple[float, list[QualityIssue]]:
        """Check documentation depth and detail level."""
        issues = []
        
        # Check total word count
        if doc_set.total_words < self.MIN_TOTAL_WORDS:
            issues.append(QualityIssue(
                severity=IssueSeverity.CRITICAL,
                category="Depth",
                message=f"Total documentation too brief ({doc_set.total_words} words, minimum {self.MIN_TOTAL_WORDS})",
                recommendation="Add more detailed explanations and context",
            ))
        
        # Check individual document lengths
        short_docs = []
        for doc in doc_set.documents:
            if doc.word_count < self.MIN_WORDS_PER_DOC:
                short_docs.append(doc)
                issues.append(QualityIssue(
                    severity=IssueSeverity.WARNING,
                    category="Depth",
                    message=f"Document too brief ({doc.word_count} words)",
                    document=str(doc.path.name),
                    recommendation=f"Expand content to at least {self.MIN_WORDS_PER_DOC} words",
                ))
        
        # Check for tables (indicates structured content)
        docs_with_tables = sum(1 for d in doc_set.documents if d.has_tables)
        if docs_with_tables < len(doc_set.documents) * 0.4:
            issues.append(QualityIssue(
                severity=IssueSeverity.INFO,
                category="Depth",
                message="Limited use of structured tables",
                recommendation="Add tables for parameters, configurations, and reference data",
            ))
        
        # Calculate score
        avg_words = doc_set.total_words / len(doc_set.documents) if doc_set.documents else 0
        word_score = min(avg_words / 200, 1.0)
        
        table_ratio = docs_with_tables / len(doc_set.documents) if doc_set.documents else 0
        table_score = min(table_ratio / 0.5, 1.0)
        
        short_penalty = len(short_docs) / len(doc_set.documents) if doc_set.documents else 0
        
        score = (word_score * 0.5) + (table_score * 0.3) - (short_penalty * 0.2)
        return max(score, 0.0), issues
    
    def _check_formatting(self, doc_set: DocumentSet) -> tuple[float, list[QualityIssue]]:
        """Check markdown formatting quality."""
        issues = []
        format_scores = []
        
        for doc in doc_set.documents:
            doc_issues, doc_score = self._check_document_formatting(doc)
            issues.extend(doc_issues)
            format_scores.append(doc_score)
        
        score = sum(format_scores) / len(format_scores) if format_scores else 0.5
        return score, issues
    
    def _check_document_formatting(
        self,
        doc: GeneratedDocument,
    ) -> tuple[list[QualityIssue], float]:
        """Check formatting of a single document."""
        issues = []
        score_deductions = 0.0
        content = doc.content
        
        # Check for proper headings hierarchy
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        if headings:
            levels = [len(h[0]) for h in headings]
            if levels[0] != 1:
                issues.append(QualityIssue(
                    severity=IssueSeverity.INFO,
                    category="Formatting",
                    message="Document should start with H1 heading",
                    document=str(doc.path.name),
                ))
                score_deductions += 0.1
        
        # Check for broken links
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        for text, url in links:
            if url.startswith("./") or url.startswith("../"):
                # Relative link - we can't fully validate but check format
                if " " in url:
                    issues.append(QualityIssue(
                        severity=IssueSeverity.WARNING,
                        category="Formatting",
                        message=f"Link URL contains spaces: {url}",
                        document=str(doc.path.name),
                    ))
                    score_deductions += 0.05
        
        # Check for unclosed code blocks
        code_block_count = content.count("```")
        if code_block_count % 2 != 0:
            issues.append(QualityIssue(
                severity=IssueSeverity.CRITICAL,
                category="Formatting",
                message="Unclosed code block detected",
                document=str(doc.path.name),
            ))
            score_deductions += 0.2
        
        # Check for empty sections
        empty_sections = re.findall(r'^#{2,}\s+.+\n+(?=#{2,}|\Z)', content, re.MULTILINE)
        if empty_sections:
            issues.append(QualityIssue(
                severity=IssueSeverity.WARNING,
                category="Formatting",
                message="Empty section(s) detected",
                document=str(doc.path.name),
                recommendation="Add content or remove empty sections",
            ))
            score_deductions += 0.1
        
        # Check frontmatter
        if not content.startswith("---"):
            issues.append(QualityIssue(
                severity=IssueSeverity.INFO,
                category="Formatting",
                message="Missing YAML frontmatter",
                document=str(doc.path.name),
                recommendation="Add frontmatter with title and description",
            ))
            score_deductions += 0.05
        
        score = max(1.0 - score_deductions, 0.0)
        return issues, score
    
    def _check_cross_references(
        self,
        doc_set: DocumentSet,
    ) -> tuple[float, list[QualityIssue]]:
        """Check for cross-references between documents."""
        issues = []
        
        # Build set of document names
        doc_names = {str(d.path.name) for d in doc_set.documents}
        doc_paths = {str(d.path) for d in doc_set.documents}
        
        cross_ref_count = 0
        potential_refs = 0
        
        for doc in doc_set.documents:
            # Find internal links
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', doc.content)
            
            for text, url in links:
                if url.startswith("./") or url.startswith("../") or url.endswith(".md"):
                    potential_refs += 1
                    # Check if link target exists
                    link_name = url.split("/")[-1].split("#")[0]
                    if link_name in doc_names:
                        cross_ref_count += 1
        
        # README should link to other docs
        readme = doc_set.get_document("README.md")
        if readme:
            readme_links = re.findall(r'\[([^\]]+)\]\(\.\/([^)]+)\)', readme.content)
            if len(readme_links) < 3:
                issues.append(QualityIssue(
                    severity=IssueSeverity.WARNING,
                    category="Cross-References",
                    message="README has few links to other documentation",
                    document="README.md",
                    recommendation="Add links to all key documentation pages",
                ))
        
        # Check for related documents section
        for doc in doc_set.documents:
            if "Related" not in doc.content and "See Also" not in doc.content:
                if doc.path.name != "README.md":
                    issues.append(QualityIssue(
                        severity=IssueSeverity.INFO,
                        category="Cross-References",
                        message="No 'Related Documents' section",
                        document=str(doc.path.name),
                        recommendation="Add related documents or see also section",
                    ))
        
        score = cross_ref_count / potential_refs if potential_refs > 0 else 0.5
        return min(score, 1.0), issues
    
    def _generate_recommendations(
        self,
        doc_set: DocumentSet,
        scores: dict[str, float],
        failing_criteria: list[str],
        issues: list[QualityIssue],
    ) -> list[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Critical issues first
        critical = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        if critical:
            recommendations.append(
                f"🚨 Address {len(critical)} critical issue(s) immediately"
            )
        
        # Criterion-specific recommendations
        if "completeness" in failing_criteria:
            missing = [i.message for i in issues if "Missing required" in i.message]
            if missing:
                recommendations.append(
                    f"📝 Create missing documents: {', '.join(m.split(': ')[-1] for m in missing[:3])}"
                )
        
        if "diagrams" in failing_criteria:
            recommendations.append(
                "📊 Add architecture diagrams using Mermaid to README and architecture.md"
            )
        
        if "examples" in failing_criteria:
            recommendations.append(
                "💻 Add working code examples demonstrating API usage"
            )
        
        if "depth" in failing_criteria:
            recommendations.append(
                "📖 Expand documentation with more detailed explanations"
            )
        
        if "formatting" in failing_criteria:
            recommendations.append(
                "✨ Fix markdown formatting issues and add frontmatter"
            )
        
        if "cross_references" in failing_criteria:
            recommendations.append(
                "🔗 Add cross-references and 'Related Documents' sections"
            )
        
        # General improvements
        if scores.get("depth", 1.0) < 0.9:
            avg_words = doc_set.total_words / len(doc_set.documents) if doc_set.documents else 0
            if avg_words < 200:
                recommendations.append(
                    f"📝 Increase detail level (current avg: {avg_words:.0f} words/doc)"
                )
        
        return recommendations
    
    async def evaluate_multiple(
        self,
        doc_sets: list[DocumentSet],
        strategies: dict[str, Any] = None,
    ) -> AggregateQualityReport:
        """
        Evaluate multiple repositories and produce aggregate report.
        
        Args:
            doc_sets: List of documentation sets to evaluate
            strategies: Optional dict mapping repo names to strategies
            
        Returns:
            AggregateQualityReport with overall statistics
        """
        strategies = strategies or {}
        
        aggregate = AggregateQualityReport()
        aggregate.total_repos = len(doc_sets)
        
        total_score = 0.0
        
        for doc_set in doc_sets:
            strategy = strategies.get(doc_set.repo_name)
            report = await self.evaluate(doc_set, strategy)
            
            aggregate.reports.append(report)
            total_score += report.overall_score
            
            if report.passing:
                aggregate.passing_repos += 1
            else:
                aggregate.failing_repos += 1
        
        aggregate.average_score = total_score / aggregate.total_repos if aggregate.total_repos > 0 else 0.0
        
        return aggregate
    
    def print_report(self, report: QualityReport) -> str:
        """Generate a formatted report string."""
        score_pct = report.overall_score * 100
        status = "✅ PASSING" if report.passing else "❌ FAILING"
        
        output = f"""
╔══════════════════════════════════════════════════════════════════╗
║              Documentation Quality Report                         ║
║              {report.repo_name:^42}                               ║
╠══════════════════════════════════════════════════════════════════╣
║  Status:          {status:<44} ║
║  Overall Score:   {score_pct:>5.1f}%{' ':<42} ║
║  Type:            {report.repo_type.value:<44} ║
╠══════════════════════════════════════════════════════════════════╣
║                        Scores by Criterion                        ║
"""
        
        for criterion, score in sorted(report.scores_by_criterion.items()):
            pct = score * 100
            threshold = self.thresholds.get(criterion, 0.75) * 100
            status_icon = "✓" if pct >= threshold else "✗"
            output += f"║  {criterion:<18} {pct:>5.1f}%  (threshold: {threshold:.0f}%)  {status_icon:<8} ║\n"
        
        output += """╠══════════════════════════════════════════════════════════════════╣
║                         Statistics                                ║
"""
        output += f"║  Documents:       {report.document_count:>5}{'':45} ║\n"
        output += f"║  Total Words:     {report.total_words:>5}{'':45} ║\n"
        output += f"║  With Diagrams:   {report.diagram_count:>5}{'':45} ║\n"
        output += f"║  With Examples:   {report.example_count:>5}{'':45} ║\n"
        
        if report.issues:
            output += """╠══════════════════════════════════════════════════════════════════╣
║                          Issues                                   ║
"""
            for issue in report.issues[:10]:  # Limit to 10 issues
                msg = str(issue)
                if len(msg) > 60:
                    msg = msg[:57] + "..."
                output += f"║  {msg:<62} ║\n"
            
            if len(report.issues) > 10:
                output += f"║  ... and {len(report.issues) - 10} more issues{' ':38} ║\n"
        
        if report.recommendations:
            output += """╠══════════════════════════════════════════════════════════════════╣
║                      Recommendations                              ║
"""
            for rec in report.recommendations[:5]:
                if len(rec) > 60:
                    rec = rec[:57] + "..."
                output += f"║  {rec:<62} ║\n"
        
        output += "╚══════════════════════════════════════════════════════════════════╝"
        
        return output
    
    def print_aggregate_report(self, report: AggregateQualityReport) -> str:
        """Generate formatted aggregate report string."""
        avg_pct = report.average_score * 100
        pass_pct = report.passing_percentage
        
        output = f"""
╔══════════════════════════════════════════════════════════════════╗
║                Documentation Quality Summary                      ║
╠══════════════════════════════════════════════════════════════════╣
║  Total Repositories:     {report.total_repos:>5}{'':38} ║
║  Passing Quality Gate:   {report.passing_repos:>5}  ({pass_pct:.1f}%){'':27} ║
║  Needs Attention:        {report.failing_repos:>5}{'':38} ║
║  Average Score:          {avg_pct:>5.1f}%{'':37} ║
╠══════════════════════════════════════════════════════════════════╣
"""
        
        if report.repos_needing_work:
            output += "║                 Repositories Needing Work                        ║\n"
            for failing in report.repos_needing_work[:10]:
                score_pct = failing.overall_score * 100
                issues = len(failing.issues)
                critical = len(failing.critical_issues)
                line = f"  {failing.repo_name}: {score_pct:.1f}% ({issues} issues, {critical} critical)"
                output += f"║{line:<64}║\n"
            
            if len(report.repos_needing_work) > 10:
                output += f"║  ... and {len(report.repos_needing_work) - 10} more{' ':47} ║\n"
        
        output += "╚══════════════════════════════════════════════════════════════════╝"
        
        return output
