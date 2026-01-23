"""Jinja2 template renderer for documentation generation."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..utils.markdown import (
    create_breadcrumb,
    create_frontmatter,
    create_related_section,
    create_source_references,
    create_toc,
    extract_headings,
    slugify,
)

logger = logging.getLogger("doc-agent.templates.renderer")


class TemplateRenderer:
    """
    Jinja2-based template renderer for documentation.
    
    Provides:
    - Template loading from the templates directory
    - Common filters and globals for documentation
    - Consistent document structure
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize the template renderer.
        
        Args:
            templates_dir: Directory containing templates
        """
        self.templates_dir = templates_dir or Path(__file__).parent.parent.parent / "templates"
        
        # Create Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        # Add custom filters
        self.env.filters["slugify"] = slugify
        self.env.filters["frontmatter"] = create_frontmatter
        self.env.filters["toc"] = lambda content: create_toc(extract_headings(content))
        
        # Add custom globals
        self.env.globals["now"] = datetime.utcnow
        self.env.globals["create_breadcrumb"] = create_breadcrumb
        self.env.globals["create_related_section"] = create_related_section
        self.env.globals["create_source_references"] = create_source_references
    
    def render(
        self,
        template_name: str,
        context: dict[str, Any],
    ) -> str:
        """
        Render a template with the given context.
        
        Args:
            template_name: Name of the template file
            context: Template context variables
            
        Returns:
            Rendered template string
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            raise
    
    def render_string(
        self,
        template_string: str,
        context: dict[str, Any],
    ) -> str:
        """
        Render a template from a string.
        
        Args:
            template_string: Template content as a string
            context: Template context variables
            
        Returns:
            Rendered string
        """
        try:
            template = self.env.from_string(template_string)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render template string: {e}")
            raise
    
    def render_service_readme(
        self,
        service: dict[str, Any],
        related_docs: Optional[list[dict[str, str]]] = None,
        sources: Optional[list[dict[str, str]]] = None,
    ) -> str:
        """
        Render a service README document.
        
        Args:
            service: Service data dictionary
            related_docs: Optional list of related documents
            sources: Optional list of source references
            
        Returns:
            Rendered markdown
        """
        return self.render("service-readme.md.j2", {
            "service": service,
            "related_docs": related_docs or [],
            "sources": sources or [],
        })
    
    def render_api_overview(
        self,
        api: dict[str, Any],
        endpoints: list[dict[str, Any]],
    ) -> str:
        """
        Render an API overview document.
        
        Args:
            api: API data dictionary
            endpoints: List of endpoint data
            
        Returns:
            Rendered markdown
        """
        return self.render("api-overview.md.j2", {
            "api": api,
            "endpoints": endpoints,
        })
    
    def render_domain_overview(
        self,
        domain: dict[str, Any],
        services: list[dict[str, Any]],
    ) -> str:
        """
        Render a domain overview document.
        
        Args:
            domain: Domain data dictionary
            services: List of services in the domain
            
        Returns:
            Rendered markdown
        """
        return self.render("domain-overview.md.j2", {
            "domain": domain,
            "services": services,
        })
    
    def render_index(
        self,
        platform: dict[str, Any],
        domains: list[dict[str, Any]],
        services: list[dict[str, Any]],
    ) -> str:
        """
        Render the main documentation index.
        
        Args:
            platform: Platform overview data
            domains: List of domains
            services: List of all services
            
        Returns:
            Rendered markdown
        """
        return self.render("index.md.j2", {
            "platform": platform,
            "domains": domains,
            "services": services,
        })


# Default templates as strings (for when template files don't exist)
DEFAULT_TEMPLATES = {
    "service-readme.md.j2": """---
title: {{ service.name }}
description: {{ service.description or 'Service documentation' }}
generated: {{ now().isoformat() }}Z
auto_generated: true
{% if sources %}
sources:
{% for source in sources %}
  - {{ source.url }}
{% endfor %}
{% endif %}
---

# {{ service.name }}

> {{ service.description or 'No description available.' }}

## Overview

{% if service.purpose %}
{{ service.purpose }}
{% else %}
This service is part of the Natterbox platform.
{% endif %}

## Quick Facts

| Property | Value |
|----------|-------|
| **Repository** | {% if service.repository %}{% if service.repository_doc_url %}[{{ service.repository }}]({{ service.repository_doc_url }}){% else %}{{ service.repository }}{% endif %}{% else %}N/A{% endif %} |
| **Language** | {{ service.language or 'N/A' }} |
| **Framework** | {{ service.framework or 'N/A' }} |
| **Team** | {{ service.team or 'N/A' }} |
| **Status** | {{ service.status or 'active' }} |

## Documentation

Detailed documentation for this service:

| Document | Description |
|----------|-------------|
| [Architecture](./architecture.md) | Internal architecture and components |
| [Configuration](./configuration.md) | Environment variables and settings |
| [Operations](./operations.md) | Monitoring, logging, and runbooks |
| [Data Models](./data/models.md) | Data structures and schemas |
| [Side Effects](./data/side-effects.md) | External system interactions |
{% if service.apis %}| [API Reference](./api/overview.md) | API endpoints and usage |{% endif %}

{% if service.repository_doc_url %}
## Source Code

For detailed repository information, structure, and setup instructions, see the [Repository Documentation]({{ service.repository_doc_url }}).

{% endif %}
{% if service.dependencies %}
## Dependencies

This service depends on:

{% for dep in service.dependencies %}
- {{ dep }}
{% endfor %}
{% endif %}

{% if service.apis %}
## APIs

This service exposes the following APIs:

{% for api in service.apis %}
- [{{ api.name }}](./api/overview.md) - {{ api.api_type or 'REST' }}{% if api.description %}: {{ api.description }}{% endif %}

{% endfor %}
{% endif %}

{% if related_docs %}
{{ create_related_section(related_docs) }}
{% endif %}

{% if sources %}
{{ create_source_references(sources) }}
{% endif %}
""",
    
    "api-overview.md.j2": """---
title: {{ api.name }} API
description: API reference for {{ api.name }}
generated: {{ now().isoformat() }}Z
auto_generated: true
---

# {{ api.name }} API

{{ api.description or 'API documentation.' }}

## Overview

| Property | Value |
|----------|-------|
| **Type** | {{ api.api_type or 'REST' }} |
| **Version** | {{ api.version or 'v1' }} |
| **Base URL** | `{{ api.base_url or '/api' }}` |
| **Authentication** | {{ api.auth_type or 'Required' }} |

{% if endpoints %}
## Endpoints

{% for endpoint in endpoints %}
### {{ endpoint.method }} {{ endpoint.path }}

{{ endpoint.description or 'No description.' }}

{% if endpoint.request_schema %}
**Request Schema:**
```json
{{ endpoint.request_schema }}
```
{% endif %}

{% if endpoint.response_schema %}
**Response Schema:**
```json
{{ endpoint.response_schema }}
```
{% endif %}

---

{% endfor %}
{% endif %}
""",
    
    "domain-overview.md.j2": """---
title: {{ domain.name }}
description: {{ domain.description or 'Domain documentation' }}
generated: {{ now().isoformat() }}Z
auto_generated: true
---

# {{ domain.name }}

{{ domain.description or 'No description available.' }}

## Overview

{{ domain.overview or 'This domain is part of the Natterbox platform.' }}

{% if services %}
## Services

| Service | Description | Status |
|---------|-------------|--------|
{% for service in services %}
| [{{ service.name }}](../../services/{{ service.id }}/README.md) | {{ service.description or 'N/A' }} | {{ service.status or 'Active' }} |
{% endfor %}
{% endif %}

{% if domain.interactions %}
## Interactions with Other Domains

{{ domain.interactions }}
{% endif %}
""",
    
    "index.md.j2": """---
title: {{ platform.name or 'Platform Documentation' }}
description: {{ platform.description or 'Comprehensive platform documentation' }}
generated: {{ now().isoformat() }}Z
auto_generated: true
---

# {{ platform.name or 'Platform Documentation' }}

{{ platform.description or 'Welcome to the platform documentation.' }}

## Quick Links

- [Architecture Overview](./architecture/overview.md)
- [System Landscape](./architecture/system-landscape.md)
- [Service Catalog](#services)
- [Repository Index](./repositories/index.md)

## Architecture

Explore the platform architecture:

- [Overview](./architecture/overview.md) - High-level system architecture
- [System Landscape](./architecture/system-landscape.md) - Service map
- [Data Flows](./architecture/data-flows.md) - How data moves through the system
- [Technology Stack](./architecture/technology-stack.md) - Languages and frameworks

{% if domains %}
## Domains

{% for domain in domains %}
- [{{ domain.name }}](./architecture/domains/{{ domain.id }}/overview.md) - {{ domain.description or '' }}
{% endfor %}
{% endif %}

{% if services %}
## Services

| Service | Domain | Description |
|---------|--------|-------------|
{% for service in services %}
| [{{ service.name }}](./services/{{ service.id }}/README.md) | {{ service.domain or 'N/A' }} | {{ service.description or 'N/A' }} |
{% endfor %}
{% endif %}

## Repositories

Browse all repositories with detailed documentation:

- [Repository Index](./repositories/index.md) - Complete listing of all repositories

## Reference

- [Glossary](./reference/glossary.md) - Platform terminology
- [Message Formats](./reference/message-formats/) - Event schemas
- [Database Schemas](./reference/database-schemas/) - Data dictionary

---

*This documentation was automatically generated. Last updated: {{ now().strftime('%Y-%m-%d %H:%M UTC') }}*
""",
}
