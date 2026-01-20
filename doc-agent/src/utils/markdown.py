"""Markdown utilities for document generation."""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    # Convert to lowercase
    slug = text.lower()
    # Replace spaces and special chars with hyphens
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    # Remove leading/trailing hyphens
    return slug.strip("-")


def create_breadcrumb(path: Path, root: Path) -> str:
    """
    Create a breadcrumb navigation string for a document.
    
    Args:
        path: Path to the current document
        root: Root path of the documentation
        
    Returns:
        Markdown breadcrumb string
    """
    relative = path.relative_to(root)
    parts = list(relative.parts[:-1])  # Exclude filename
    
    if not parts:
        return ""
    
    breadcrumbs = ["[Home](../index.md)"]
    current_path = Path("..")
    
    for i, part in enumerate(parts):
        if i == len(parts) - 1:
            breadcrumbs.append(part.replace("-", " ").title())
        else:
            link_path = current_path / part / "index.md"
            breadcrumbs.append(f"[{part.replace('-', ' ').title()}]({link_path})")
            current_path = current_path / ".."
    
    return " > ".join(breadcrumbs)


def create_frontmatter(
    title: str,
    description: Optional[str] = None,
    sources: Optional[list[str]] = None,
    generated: bool = True,
    **kwargs,
) -> str:
    """
    Create YAML frontmatter for a markdown document.
    
    Args:
        title: Document title
        description: Short description
        sources: List of source URLs/references
        generated: Whether this was auto-generated
        **kwargs: Additional frontmatter fields
        
    Returns:
        YAML frontmatter string
    """
    lines = ["---", f"title: {title}"]
    
    if description:
        lines.append(f"description: {description}")
    
    if generated:
        lines.append(f"generated: {datetime.utcnow().isoformat()}Z")
        lines.append("auto_generated: true")
    
    if sources:
        lines.append("sources:")
        for source in sources:
            lines.append(f"  - {source}")
    
    for key, value in kwargs.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    
    lines.append("---")
    return "\n".join(lines)


def create_related_section(related_docs: list[dict[str, str]]) -> str:
    """
    Create a 'Related Documents' section.
    
    Args:
        related_docs: List of dicts with 'title' and 'path' keys
        
    Returns:
        Markdown section string
    """
    if not related_docs:
        return ""
    
    lines = ["\n## Related Documents\n"]
    for doc in related_docs:
        lines.append(f"- [{doc['title']}]({doc['path']})")
    
    return "\n".join(lines)


def create_source_references(sources: list[dict[str, str]]) -> str:
    """
    Create a 'Sources' section with links to original content.
    
    Args:
        sources: List of dicts with 'type', 'title', and 'url' keys
        
    Returns:
        Markdown section string
    """
    if not sources:
        return ""
    
    lines = ["\n---\n", "## Sources\n"]
    
    # Group by type
    by_type: dict[str, list[dict[str, str]]] = {}
    for source in sources:
        source_type = source.get("type", "Other")
        if source_type not in by_type:
            by_type[source_type] = []
        by_type[source_type].append(source)
    
    for source_type, items in by_type.items():
        lines.append(f"\n### {source_type}\n")
        for item in items:
            lines.append(f"- [{item['title']}]({item['url']})")
    
    return "\n".join(lines)


def extract_headings(content: str) -> list[dict[str, any]]:
    """
    Extract headings from markdown content.
    
    Args:
        content: Markdown content
        
    Returns:
        List of dicts with 'level', 'text', and 'slug' keys
    """
    headings = []
    pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    
    for match in pattern.finditer(content):
        level = len(match.group(1))
        text = match.group(2).strip()
        headings.append({
            "level": level,
            "text": text,
            "slug": slugify(text),
        })
    
    return headings


def create_toc(headings: list[dict[str, any]], max_level: int = 3) -> str:
    """
    Create a table of contents from headings.
    
    Args:
        headings: List of heading dicts from extract_headings
        max_level: Maximum heading level to include
        
    Returns:
        Markdown TOC string
    """
    if not headings:
        return ""
    
    lines = ["## Contents\n"]
    
    for heading in headings:
        if heading["level"] <= max_level:
            indent = "  " * (heading["level"] - 1)
            lines.append(f"{indent}- [{heading['text']}](#{heading['slug']})")
    
    return "\n".join(lines)


def wrap_code_block(code: str, language: str = "") -> str:
    """Wrap code in a fenced code block."""
    return f"```{language}\n{code}\n```"


def create_mermaid_diagram(diagram_type: str, content: str) -> str:
    """Create a mermaid diagram block."""
    return f"```mermaid\n{diagram_type}\n{content}\n```"


def sanitize_for_markdown(text: str) -> str:
    """Escape special markdown characters in text."""
    # Escape characters that have special meaning in markdown
    special_chars = ["\\", "`", "*", "_", "{", "}", "[", "]", "(", ")", "#", "+", "-", ".", "!"]
    for char in special_chars:
        text = text.replace(char, f"\\{char}")
    return text
