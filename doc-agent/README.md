# Platform Documentation Agent

A multi-agent AI system that autonomously discovers, analyzes, and documents the entire Natterbox platform, producing a hierarchical, layered documentation library.

## Overview

The Platform Documentation Agent connects to Natterbox's internal systems (GitHub, Confluence, Jira) via the Natterbox MCP server, builds a comprehensive knowledge graph of the platform architecture, and generates beautiful, organized markdown documentation that can be browsed from high-level overviews down to detailed API specifications.

## Features

- **Multi-Agent Architecture**: Specialized agents for discovery, analysis, generation, and quality assurance
- **Knowledge Graph**: NetworkX-based graph database storing services, APIs, domains, and relationships
- **Layered Documentation**: Browse from platform overview → domain → service → API → schemas
- **Incremental Updates**: Content hashing detects changes; only regenerates affected documents
- **OAuth Authentication**: Secure token management for GitHub, Atlassian, and AWS SSO
- **Context Management**: FileStore system keeps LLM context manageable for large codebases
- **MCP Integration**: Native MCP protocol communication with the Natterbox server

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Platform Documentation Agent                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                            CLI (main.py)                              │   │
│  │  Commands: generate, discover, status, list-entities, auth           │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         Orchestrator                                  │   │
│  │  • Manages pipeline phases (Discovery → Analysis → Generation → QA)  │   │
│  │  • Coordinates agent execution                                        │   │
│  │  • Handles authentication and MCP connection                         │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│           │              │                │                │                 │
│           ▼              ▼                ▼                ▼                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  Discovery  │ │  Analysis   │ │ Generation  │ │   Quality   │           │
│  │   Agents    │ │   Agents    │ │   Agents    │ │   Agents    │           │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘           │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        Shared Components                              │   │
│  ├──────────────────────────────────────────────────────────────────────┤   │
│  │  Knowledge Graph    MCP Client      FileStore       Auth Manager     │   │
│  │  (NetworkX)         (MCP SDK)       (Context)       (OAuth/SSO)      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
└────────────────────────────────────┼─────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Natterbox MCP Server                                 │
│  Tools: GitHub (repos, files, search) │ Confluence (pages, spaces)          │
│         Jira (issues, projects, epics) │ ...                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Pipeline Phases

The documentation generation follows a four-phase pipeline:

#### Phase 1: Discovery
Parallel agents scan all data sources to gather raw information:

| Agent | Source | Extracts |
|-------|--------|----------|
| `RepositoryScannerAgent` | GitHub | Services, dependencies, APIs, READMEs |
| `ConfluenceHarvesterAgent` | Confluence | Architecture docs, runbooks, decision records |
| `JiraAnalyzerAgent` | Jira | Features (epics), tech debt, bug patterns |

#### Phase 2: Analysis
Sequential agents process discovered data to build understanding:

| Agent | Purpose |
|-------|---------|
| `ArchitectureInferenceAgent` | Classifies services, infers dependencies, detects patterns |
| `DomainMapperAgent` | Clusters services into logical domains, identifies boundaries |

#### Phase 3: Generation
Parallel agents generate documentation from the knowledge graph:

| Agent | Output |
|-------|--------|
| `OverviewWriterAgent` | Platform index, architecture overview, domain summaries |
| `TechnicalWriterAgent` | Service READMEs, architecture docs, configuration guides |
| `APIDocumenterAgent` | API overviews, endpoint documentation, request/response schemas |
| `SchemaDocumenterAgent` | Data models, database schemas, side-effect documentation |

#### Phase 4: Quality
Sequential agents validate and enhance the documentation:

| Agent | Purpose |
|-------|---------|
| `CrossReferenceAgent` | Adds internal links, breadcrumbs, validates references |
| `IndexGeneratorAgent` | Creates index files, glossary, search metadata |
| `QualityCheckerAgent` | Completeness checks, coverage reports, quality metrics |

### Core Components

#### Knowledge Graph (`src/knowledge/`)

A NetworkX-based graph database storing all discovered entities and relationships:

```
Entities:                    Relations:
├── Service                  ├── DEPENDS_ON
├── Domain                   ├── BELONGS_TO
├── API                      ├── EXPOSES
├── Endpoint                 ├── CALLS
├── Schema                   ├── DOCUMENTS
├── Document                 ├── OWNS
├── Repository               ├── IMPLEMENTS
├── Person                   └── RELATES_TO
└── Integration
```

The `KnowledgeStore` provides persistence with:
- JSON serialization of graph state
- Document registry with content hashing for change detection
- Agent checkpoints for incremental runs

#### MCP Client (`src/mcp/`)

Communicates with the Natterbox MCP server using the official MCP SDK:

```python
# Launches MCP server as subprocess
# Communicates via stdio using JSON-RPC protocol
# Automatically injects OAuth tokens into environment

client = MCPClient(
    server_command="npx",
    server_args=["@natterbox/mcp-server"],
    oauth_manager=oauth_manager,
)
await client.connect()
response = await client.call_tool("github_list_repos", {"org": "natterbox"})
```

Service-specific wrappers provide typed interfaces:
- `GitHubClient`: Repositories, files, search, package.json, OpenAPI specs
- `ConfluenceClient`: Spaces, pages, search, content extraction
- `JiraClient`: Projects, issues, epics, components, releases

#### FileStore (`src/context/`)

Manages LLM context size by storing large content externally:

```
┌────────────────────────────────────────────────────────────┐
│                   Conversation History                      │
├────────────────────────────────────────────────────────────┤
│ Tool Result: [FileRef: abc123, 45KB]                       │
│   Summary: "Contains 50 repositories with metadata..."     │
│   Use file_store_read(ref_id='abc123') to retrieve         │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│                      FileStore (Memory)                     │
├────────────────────────────────────────────────────────────┤
│ abc123: [Full 45KB content]                                │
└────────────────────────────────────────────────────────────┘
```

Features:
- **1KB threshold**: Content over 1KB is automatically stored
- **AI summaries**: Claude generates summaries for stored content
- **Byte-based chunks**: LLM can retrieve specific byte ranges
- **Session-only**: Cleared on shutdown (not persisted)

#### Authentication (`src/auth/`)

Secure token management for all external services:

```
┌─────────────────────────────────────────────────────────────┐
│                     Token Flow                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  OAuth Services              AWS SSO                         │
│  ├── GitHub ─────┐          ├── aws-vault ──┐               │
│  └── Atlassian ──┼──▶ TokenCache ◀──────────┘               │
│                  │     (encrypted)                           │
│                  │          │                                │
│                  │          ▼                                │
│                  └──▶ MCP Client env vars                   │
│                            │                                 │
│                            ▼                                 │
│                    Natterbox MCP Server                      │
└─────────────────────────────────────────────────────────────┘
```

Components:
- **TokenCache**: Encrypted storage in `~/.doc-agent/tokens/`
- **OAuthManager**: OAuth 2.0 flow with PKCE, automatic refresh
- **AWSSSOAuth**: AWS SSO integration via aws-vault or AWS CLI

### Agent Architecture

All agents inherit from `BaseAgent` which provides:

```python
class BaseAgent(ABC):
    # Shared resources via AgentContext
    @property
    def graph(self) -> KnowledgeGraph: ...
    @property
    def mcp(self) -> MCPClient: ...
    @property
    def file_store(self) -> FileStore: ...
    
    # Claude API integration
    async def call_claude(self, system_prompt, user_message) -> str: ...
    
    # Context management
    def store_large_content(self, content) -> str | FileReference: ...
    
    # Checkpointing for incremental runs
    async def save_checkpoint(self, data): ...
    async def load_checkpoint(self) -> dict: ...
    
    # Main execution
    @abstractmethod
    async def run(self) -> AgentResult: ...
```

Agents can run in parallel (via `ParallelAgentRunner`) or sequentially depending on dependencies.

## Installation

```bash
cd doc-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install with dependencies
pip install -e .

# Or use the setup script
./setup.sh
```

## Configuration

### Basic Setup

```bash
cp config/config.example.yaml config/config.yaml
```

### API Keys

```bash
# Anthropic API (direct)
export ANTHROPIC_API_KEY=your-api-key

# Or use AWS Bedrock (configure in config.yaml)
```

### Authentication

```bash
# Authenticate with services
doc-agent auth login github
doc-agent auth login atlassian
doc-agent auth login aws

# Check authentication status
doc-agent auth status
```

### Configuration File

```yaml
# config/config.yaml

llm:
  provider: anthropic  # or 'bedrock' for AWS
  model: claude-sonnet-4-20250514
  max_tokens: 4096

mcp:
  server: natterbox
  timeout: 60
  command: npx
  args: ["@natterbox/mcp-server"]

auth:
  github:
    enabled: true
    client_id: "your-github-oauth-client-id"
  atlassian:
    enabled: true
    client_id: "your-atlassian-oauth-client-id"
    client_secret: "your-atlassian-oauth-client-secret"
  aws:
    enabled: true
    profile: "your-sso-profile"
    region: us-east-1

sources:
  github:
    organizations: [natterbox]
    exclude_repos: [".*-deprecated", ".*-archive"]
  confluence:
    spaces: [ARCH, ENG, OPS, PLAT]
  jira:
    projects: [PLAT, VOICE, INT, INFRA]

output:
  directory: ./docs

agents:
  discovery:
    parallelism: 5
  generation:
    parallelism: 10
```

## Usage

### Generate Documentation

```bash
# Full generation from scratch
doc-agent generate --full

# Incremental update (default - only changed content)
doc-agent generate

# Skip specific phases
doc-agent generate --skip-discovery --skip-analysis

# Generate for specific services
doc-agent generate --service voice-routing --service call-manager

# Dry run (no file writes)
doc-agent generate --dry-run
```

### Other Commands

```bash
# Discovery only (populate knowledge graph)
doc-agent discover

# Show system status
doc-agent status

# List discovered entities
doc-agent list-entities --type service
doc-agent list-entities --type domain
doc-agent list-entities --type api
```

### Authentication Commands

```bash
# Login to services
doc-agent auth login github
doc-agent auth login atlassian
doc-agent auth login aws

# Check token status
doc-agent auth status

# Logout / clear tokens
doc-agent auth logout github
doc-agent auth logout all

# Manual token refresh
doc-agent auth refresh atlassian
```

## Output Structure

```
docs/
├── index.md                           # Platform overview & navigation
├── architecture/
│   ├── index.md                       # Architecture section index
│   ├── overview.md                    # System architecture summary
│   ├── system-landscape.md            # Service map with Mermaid diagrams
│   ├── technology-stack.md            # Languages, frameworks, infrastructure
│   ├── data-flows.md                  # How data moves through the system
│   └── domains/
│       └── {domain}/
│           ├── overview.md            # Domain purpose and scope
│           ├── services.md            # Services in this domain
│           └── integrations.md        # External integrations
├── services/
│   └── {service}/
│       ├── README.md                  # Service overview
│       ├── architecture.md            # Internal architecture
│       ├── configuration.md           # Environment, settings
│       ├── operations.md              # Deployment, monitoring
│       ├── api/
│       │   ├── overview.md            # API summary
│       │   ├── endpoints.md           # Endpoint reference
│       │   └── schemas.md             # Request/response schemas
│       └── data/
│           ├── models.md              # Data models
│           └── side-effects.md        # Database operations
├── integrations/
│   └── {integration}/                 # Third-party service docs
├── reference/
│   ├── index.md                       # Reference section index
│   ├── glossary.md                    # Platform terminology
│   └── database-schemas/
│       └── data-dictionary.md         # Cross-service data dictionary
└── _meta/
    ├── quality-report.md              # Documentation quality metrics
    └── coverage-report.md             # What's documented vs. discovered
```

## Development

### Project Structure

```
doc-agent/
├── src/
│   ├── main.py                 # CLI entry point
│   ├── orchestrator.py         # Pipeline coordinator
│   ├── agents/
│   │   ├── base.py             # BaseAgent class
│   │   ├── discovery/          # Discovery phase agents
│   │   ├── analysis/           # Analysis phase agents
│   │   ├── generation/         # Generation phase agents
│   │   └── quality/            # Quality phase agents
│   ├── knowledge/
│   │   ├── models.py           # Entity/relation models
│   │   ├── graph.py            # NetworkX graph wrapper
│   │   └── store.py            # Persistence layer
│   ├── mcp/
│   │   ├── client.py           # MCP protocol client
│   │   ├── github.py           # GitHub operations
│   │   ├── confluence.py       # Confluence operations
│   │   └── jira.py             # Jira operations
│   ├── context/
│   │   └── file_store.py       # Large content management
│   ├── auth/
│   │   ├── oauth.py            # OAuth 2.0 manager
│   │   ├── token_cache.py      # Encrypted token storage
│   │   └── aws_sso.py          # AWS SSO integration
│   ├── templates/
│   │   └── renderer.py         # Jinja2 template engine
│   └── utils/
│       ├── logging.py          # Structured logging
│       └── markdown.py         # Markdown utilities
├── config/
│   ├── config.example.yaml     # Example configuration
│   └── prompts/
│       └── system-prompts.yaml # Agent system prompts
├── templates/                  # Jinja2 document templates
├── pyproject.toml              # Python project config
└── setup.sh                    # Environment setup script
```

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Adding a New Agent

1. Create agent class inheriting from `BaseAgent`
2. Implement `run()` method returning `AgentResult`
3. Add to appropriate phase in `orchestrator.py`
4. Add system prompt to `config/prompts/system-prompts.yaml`

## License

Proprietary - Natterbox Ltd.
