# Doc-Spawner

A recursive self-spawning AI agent system for documentation generation. The master agent can spawn child agents, which can spawn their own children, creating a hierarchical workforce that documents an entire codebase in parallel.

## Architecture

```
Master Agent (depth=0)
├── Category Agent (depth=1) - "Document all API services"
│   ├── Service Agent (depth=2) - "Document platform-api"
│   │   └── Detail Agent (depth=3) - "Document platform-api authentication"
│   └── Service Agent (depth=2) - "Document auth-service"
├── Category Agent (depth=1) - "Document all infrastructure"
│   └── Module Agent (depth=2) - "Document terraform-ecs module"
└── Category Agent (depth=1) - "Document all libraries"
    └── ...
```

### Key Features

- **Fire-and-forget spawning**: Parent agents spawn children and continue working independently
- **Task queue with SQLite**: Persistent tracking of all agent tasks
- **Depth limiting**: Configurable maximum spawn depth (default: 5)
- **Parallel execution**: Multiple worker agents process tasks concurrently
- **Cost tracking**: Token usage and cost estimation per task
- **Automatic index building**: Final pass creates navigation and cross-references

## Installation

```bash
cd doc-spawner
pip install -e .
```

### Prerequisites

- Python 3.11+
- AWS credentials configured for Bedrock access
- Repository clones in a local directory

## Usage

### Start Documentation Generation

```bash
# Basic usage
doc-spawner start --repos ./repos --output ./docs

# With options
doc-spawner start \
  --repos ./repos \
  --output ./docs \
  --workers 5 \
  --max-depth 5 \
  --config config.yaml

# Resume after interruption
doc-spawner start --repos ./repos --output ./docs --resume
```

### Monitor Progress

```bash
# Show task queue status
doc-spawner status --output ./docs

# List tasks
doc-spawner tasks --output ./docs --status-filter running

# Show failed tasks
doc-spawner failures --output ./docs
```

### Control Execution

```bash
# Cancel all pending tasks
doc-spawner cancel --output ./docs

# Reset task queue (start fresh)
doc-spawner reset --output ./docs
```

## Configuration

Create `config.yaml`:

```yaml
# Agent settings
max_depth: 5
max_turns: 50
max_tokens: 16384

# Workers
num_workers: 3

# LLM (AWS Bedrock)
llm:
  model: us.anthropic.claude-opus-4-5-20251101-v1:0
  temperature: 0.3

# AWS
aws:
  region: us-east-1
```

## How It Works

### 1. Master Agent Starts

The master agent receives a comprehensive system prompt describing:
- The documentation task
- Available tools (file operations, bash, spawn_agent)
- Output structure conventions
- Documentation standards

### 2. Master Spawns Children

The master agent uses the `spawn_agent` tool to delegate work:

```python
spawn_agent(
    task_description="Document all services in the natterbox organization",
    output_path="services/",
    context="Focus on API endpoints, data models, and configuration"
)
```

### 3. Fire-and-Forget Execution

- Child tasks are added to the SQLite queue
- Worker processes claim and execute pending tasks
- No feedback flows from children to parents
- Each agent writes directly to its assigned output path

### 4. Index Building

When all tasks complete, a special index builder agent:
- Reads all generated documentation
- Creates navigation hierarchy
- Adds cross-references between documents
- Validates internal links

## Tools Available to Agents

| Tool | Description |
|------|-------------|
| `spawn_agent` | Create a child agent with a specific task |
| `file_read` | Read source files from repositories |
| `file_write` | Write markdown documentation |
| `file_list` | List directory contents |
| `bash` | Run read-only shell commands (rg, git, tree, etc.) |

### spawn_agent Parameters

- `task_description`: Detailed instructions for the child
- `output_path`: Where the child should write documentation
- `context`: Optional additional context (JSON, lists, etc.)

## Cost Estimation

With Claude Opus 4.5 on Bedrock:
- Input: $15/M tokens
- Output: $75/M tokens

Estimated costs for documenting ~1000 repos:
- Conservative: ~$1,500
- Realistic: ~$3,000-5,000
- Worst case: ~$10,000

Use tiered models for cost optimization:
- Opus 4.5 for deep analysis and final writing
- Sonnet 3.5 for discovery and categorization
- Haiku 3.5 for simple file operations

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/

# Format
ruff format src/
```

## Architecture Details

### Task Queue (SQLite)

```sql
tasks (
    task_id TEXT PRIMARY KEY,
    prompt TEXT,
    output_path TEXT,
    depth INTEGER,
    status TEXT,  -- pending, running, completed, failed, cancelled
    parent_task_id TEXT,
    created_at TEXT,
    completed_at TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER
)
```

### Agent Executor

The executor implements an agentic loop:
1. Build tools and system prompt for task
2. Send initial message to Claude
3. Loop: process tool calls → feed results → get response
4. Continue until `end_turn` or max turns reached
5. Update task status in queue

### Completion Watcher

Monitors the queue and triggers index building:
- Polls every 10 seconds
- Logs progress statistics
- Detects when pending=0 and running=0
- Spawns index builder agent

## License

Proprietary - Natterbox Ltd.
