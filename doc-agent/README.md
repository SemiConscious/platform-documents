# Platform Documentation Agent

A multi-agent AI system that autonomously discovers, analyzes, and documents the entire Natterbox platform, producing a hierarchical documentation library.

## Features

- **Discovery Agents**: Scan GitHub repositories, Confluence spaces, and Jira projects
- **Knowledge Graph**: Build a comprehensive graph of services, APIs, and relationships
- **Documentation Generation**: AI-powered documentation writing with consistent structure
- **Incremental Updates**: Only regenerate documentation when sources change
- **Quality Assurance**: Cross-referencing, link validation, and completeness checks

## Installation

```bash
cd doc-agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

## Configuration

Copy the example configuration and customize:

```bash
cp config/config.example.yaml config/config.yaml
```

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY=your-api-key
```

## Usage

```bash
# Full documentation generation
doc-agent generate --full

# Incremental update (default)
doc-agent generate

# Discovery only (no generation)
doc-agent discover

# Generate for specific service
doc-agent generate --service voice-routing

# Generate from existing knowledge (skip discovery)
doc-agent generate --skip-discovery

# Show current status
doc-agent status
```

## Output Structure

```
docs/
├── index.md                    # Platform overview
├── architecture/
│   ├── overview.md             # System architecture
│   ├── system-landscape.md     # Service map
│   └── domains/                # Domain-specific docs
├── services/
│   └── {service}/              # Per-service documentation
├── integrations/               # Third-party integrations
├── reference/                  # Glossary, schemas
└── _meta/                      # Generation metadata
```

## Architecture

The system uses a phased approach:

1. **Discovery**: Parallel agents scan all data sources
2. **Knowledge Building**: Build and enrich a knowledge graph
3. **Documentation**: Generate markdown documents from knowledge
4. **Quality**: Cross-reference, validate, and index

## License

Proprietary - Natterbox Ltd.
