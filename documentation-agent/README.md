# Natterbox Platform Documentation Agent

An automated documentation generation agent using Claude on AWS Bedrock with MCP (Model Context Protocol) tools.

## Overview

This agent automates platform documentation tasks by:
1. **Researching** - Accessing Confluence, GitHub, Document360, and other sources via MCP tools
2. **Analyzing** - Synthesizing information from multiple sources
3. **Creating** - Generating well-structured markdown documentation
4. **Organizing** - Managing documentation files in a consistent structure

## Features

- **Claude on AWS Bedrock** - Uses Claude Sonnet/Opus models via Bedrock API
- **MCP Tool Integration** - Connects to Natterbox MCP server for access to:
  - Confluence wiki pages
  - GitHub repositories
  - Document360 knowledge base
  - Salesforce data
  - Slack channels
  - And more...
- **Shell Execution** - Built-in bash, file read/write, and directory listing tools
- **Docker Container** - Isolated execution environment for safety

## Prerequisites

- Python 3.11+
- AWS account with Bedrock access
- AWS CLI configured with credentials
- Docker (for containerized execution)
- Access to Natterbox MCP server

## Installation

### Option 1: Docker (Recommended)

```bash
# Clone or create the directory
mkdir documentation-agent && cd documentation-agent

# Copy the files (agent.py, requirements.txt, Dockerfile, docker-compose.yml)

# Build the container
docker-compose build

# Run in interactive mode
docker-compose run agent --interactive
```

### Option 2: Local Python

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the agent
python agent.py --interactive
```

## Configuration

### AWS Credentials

The agent needs AWS credentials with Bedrock access. Configure using:

```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1

# Option 3: AWS Profile
export AWS_PROFILE=your-profile
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_REGION` | `us-east-1` | AWS region for Bedrock |
| `AWS_PROFILE` | `default` | AWS credentials profile |
| `NATTERBOX_MCP_URL` | `https://avatar.natterbox-dev03.net/mcp/sse` | Natterbox MCP server URL |

### Command Line Options

```bash
python agent.py --help

Options:
  --task TEXT           Documentation task to perform
  --interactive, -i     Run in interactive mode
  --region TEXT         AWS region for Bedrock (default: us-east-1)
  --model TEXT          Bedrock model ID (default: anthropic.claude-sonnet-4-20250514-v1:0)
  --mcp-url TEXT        Natterbox MCP server URL
  --work-dir TEXT       Working directory (default: /workspace)
  --output-dir TEXT     Output directory (default: /workspace/output)
```

## Usage

### Interactive Mode

```bash
# Start interactive session
python agent.py --interactive

# Or with Docker
docker-compose run agent --interactive
```

Example session:
```
Natterbox Documentation Agent - Interactive Mode
============================================================

Type your documentation requests or 'quit' to exit.

You: Create an emergency response runbook from Confluence

Agent: Working on it...

[Agent searches Confluence, processes content, creates files]

Agent: I've created the emergency response runbook at /workspace/output/operations/runbooks/emergency-response.md. The document includes:
- SDC failover procedures
- GeoDNS outage handling
- OOB access instructions
...
```

### Single Task Mode

```bash
# Run a specific task
python agent.py --task "Create developer onboarding guide"

# With Docker
docker-compose run agent --task "Create developer onboarding guide"
```

### Example Tasks

```bash
# Documentation creation
python agent.py --task "Create runbooks for emergency response, deployment, and monitoring"

# Research and analysis
python agent.py --task "Research the voice routing architecture and create a summary"

# Repository documentation
python agent.py --task "Document the repository structure for the platform"

# Onboarding guides
python agent.py --task "Create onboarding documentation for new platform engineers"
```

## Available Tools

### Shell Tools

| Tool | Description |
|------|-------------|
| `bash` | Execute shell commands |
| `read_file` | Read file contents |
| `write_file` | Create/update files |
| `list_directory` | List directory contents |

### MCP Tools (via Natterbox Server)

| Tool | Description |
|------|-------------|
| `mcp_confluence` | Search and read Confluence wiki pages |
| `mcp_github` | Access GitHub repositories and files |
| `mcp_docs360_search` | Search Document360 knowledge base |
| `mcp_salesforce` | Query Salesforce CRM data |
| `mcp_slack` | Access Slack channels and messages |
| `mcp_gdrive` | Google Drive file operations |
| `mcp_gmail` | Gmail email access |
| `mcp_jira` | Jira issue tracking |

## Output Structure

Generated documentation follows this structure:

```
/workspace/output/
├── architecture/
│   ├── global-architecture.md
│   └── voice-routing/
│       ├── overview.md
│       └── fsxinetd.md
├── operations/
│   └── runbooks/
│       ├── README.md
│       ├── emergency-response.md
│       ├── deployment-procedures.md
│       └── monitoring-alerting.md
├── onboarding/
│   ├── README.md
│   ├── developer.md
│   └── platform-engineer.md
└── services/
    └── repository-inventory.md
```

## Development

### Project Structure

```
documentation-agent/
├── agent.py           # Main agent code
├── requirements.txt   # Python dependencies
├── Dockerfile         # Container definition
├── docker-compose.yml # Container orchestration
├── README.md          # This file
├── workspace/         # Working directory (created at runtime)
└── output/            # Generated documentation
```

### Extending the Agent

#### Adding Custom Tools

```python
# In agent.py, add to ShellTool class:
def my_custom_tool(self, param: str) -> dict[str, Any]:
    """Custom tool implementation."""
    # Your logic here
    return {"success": True, "result": "..."}

# Add tool definition in get_tool_definitions():
{
    "name": "my_custom_tool",
    "description": "Description of what this tool does",
    "input_schema": {
        "type": "object",
        "properties": {
            "param": {"type": "string", "description": "Parameter description"}
        },
        "required": ["param"]
    }
}
```

#### Modifying the System Prompt

The system prompt is defined in `DocumentationAgent.SYSTEM_PROMPT`. Customize it to:
- Add domain-specific knowledge
- Change documentation standards
- Modify workflow instructions

### Running Tests

```bash
# Verify Python syntax
python -m py_compile agent.py

# Type checking (optional)
mypy agent.py
```

## Troubleshooting

### Common Issues

**AWS Credentials Error**
```
botocore.exceptions.NoCredentialsError
```
Solution: Configure AWS credentials via `aws configure` or environment variables.

**MCP Connection Failed**
```
Failed to connect to MCP server
```
Solution: Verify the MCP server URL and network connectivity. The agent will continue with shell tools only.

**Bedrock Model Not Available**
```
ValidationException: The provided model identifier is invalid
```
Solution: Check that you have access to the specified model in your AWS region. Try a different model ID.

**Permission Denied in Container**
```
PermissionError: [Errno 13] Permission denied
```
Solution: Ensure the workspace directory has correct permissions:
```bash
chmod -R 777 ./workspace ./output
```

### Logs

The agent logs to stdout with timestamps. Increase verbosity by modifying the logging level in `agent.py`:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## License

Internal use only - Natterbox

## Contributing

1. Create a feature branch
2. Make your changes
3. Test with Docker
4. Submit a pull request

## Support

For issues or questions:
- Slack: #platform-engineering
- Email: ops@redmatter.com
