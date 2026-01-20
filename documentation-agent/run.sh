#!/bin/bash
# Natterbox Documentation Agent - Helper Script
#
# Usage:
#   ./run.sh                    # Interactive mode (local Python)
#   ./run.sh task "Your task"   # Run a specific task
#   ./run.sh docker             # Run in Docker (interactive)
#   ./run.sh docker-task "..."  # Run task in Docker
#   ./run.sh build              # Build Docker image

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load .env file if it exists
if [[ -f .env ]]; then
    export $(grep -v '^#' .env | xargs)
fi

# AWS Profile for Bedrock access
AWS_VAULT_PROFILE="${AWS_PROFILE:-sso-dev03-admin}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    # Check for aws-vault
    if ! command -v aws-vault &> /dev/null; then
        log_error "aws-vault is not installed. Install with: brew install aws-vault"
        exit 1
    fi
    
    # Check for Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    # Verify AWS SSO session
    if ! aws-vault exec "$AWS_VAULT_PROFILE" -- aws sts get-caller-identity &> /dev/null; then
        log_warn "AWS SSO session may have expired. You may need to re-authenticate."
    fi
}

# Check Docker prerequisites
check_docker_prerequisites() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
}

# Setup Python virtual environment
setup_venv() {
    if [[ ! -d "venv" ]]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -q -r requirements.txt
    else
        source venv/bin/activate
    fi
}

# Build Docker image
build() {
    check_docker_prerequisites
    log_info "Building Docker image..."
    docker-compose build
    log_info "Build complete!"
}

# Run in interactive mode (local Python with aws-vault)
interactive() {
    setup_venv
    log_info "Starting interactive mode with aws-vault ($AWS_VAULT_PROFILE)..."
    aws-vault exec "$AWS_VAULT_PROFILE" -- python agent.py --interactive --work-dir "$(pwd)/workspace" --output-dir "$(pwd)/output"
}

# Run a specific task (local Python with aws-vault)
run_task() {
    local task="$1"
    if [[ -z "$task" ]]; then
        log_error "No task specified"
        echo "Usage: $0 task \"Your task description\""
        exit 1
    fi
    setup_venv
    log_info "Running task with aws-vault ($AWS_VAULT_PROFILE): $task"
    aws-vault exec "$AWS_VAULT_PROFILE" -- python agent.py --task "$task" --work-dir "$(pwd)/../" --output-dir "$(pwd)/../"
}

# Run continuously until done (commits after each iteration)
run_continuous() {
    local max_iterations="${1:-10}"
    local log_file="logs/agent-continuous-$(date +%Y%m%d-%H%M%S).log"
    mkdir -p logs
    
    setup_venv
    log_info "Starting continuous mode (max $max_iterations iterations)"
    log_info "Log file: $log_file"
    log_info "Press Ctrl+C to stop"
    echo ""
    
    aws-vault exec "$AWS_VAULT_PROFILE" -- python agent.py \
        --continuous \
        --max-iterations "$max_iterations" \
        --work-dir "$(pwd)/../" \
        --output-dir "$(pwd)/../" \
        --model "${BEDROCK_MODEL_ID:-us.anthropic.claude-opus-4-5-20251101-v1:0}" \
        2>&1 | tee "$log_file"
}

# Run in Docker interactive mode
docker_interactive() {
    check_docker_prerequisites
    log_info "Starting Docker interactive mode..."
    # Export AWS credentials from aws-vault into Docker
    aws-vault exec "$AWS_VAULT_PROFILE" -- docker-compose run --rm agent --interactive
}

# Run task in Docker
docker_task() {
    local task="$1"
    if [[ -z "$task" ]]; then
        log_error "No task specified"
        exit 1
    fi
    check_docker_prerequisites
    log_info "Running Docker task: $task"
    aws-vault exec "$AWS_VAULT_PROFILE" -- docker-compose run --rm agent --task "$task"
}

# Open shell in container
shell() {
    check_docker_prerequisites
    log_info "Opening shell in container..."
    aws-vault exec "$AWS_VAULT_PROFILE" -- docker-compose run --rm --entrypoint /bin/bash agent
}

# Clean up containers and volumes
clean() {
    log_info "Cleaning up..."
    docker-compose down -v 2>/dev/null || true
    rm -rf workspace output venv __pycache__
    log_info "Cleanup complete!"
}

# Show logs
logs() {
    docker-compose logs -f
}

# Show help
show_help() {
    cat << EOF
Natterbox Documentation Agent - Helper Script

Usage:
    $0 [command] [arguments]

Commands (Local Python + aws-vault):
    (none)          Start in interactive mode
    task "..."      Run a specific documentation task
    continuous [N]  Run until done, committing after each iteration (max N, default 10)

Commands (Docker):
    docker          Start Docker interactive mode
    docker-task "." Run task in Docker
    build           Build the Docker image
    shell           Open a bash shell in the container

Utility:
    clean           Remove containers, venv, and clean up
    logs            Show container logs
    help            Show this help message

Examples:
    $0                                          # Interactive mode (local)
    $0 task "Create emergency response runbook" # Run specific task (local)
    $0 continuous                               # Run until done (default 10 iterations)
    $0 continuous 5                             # Run max 5 iterations
    $0 docker                                   # Interactive mode (Docker)
    $0 build                                    # Build Docker image

AWS Authentication:
    Uses aws-vault with profile: $AWS_VAULT_PROFILE
    Bedrock model: ${BEDROCK_MODEL_ID:-us.anthropic.claude-opus-4-5-20251101-v1:0}

Environment Variables (from .env):
    AWS_PROFILE         AWS credentials profile (default: sso-dev03-admin)
    AWS_REGION          AWS region for Bedrock (default: us-east-1)
    BEDROCK_MODEL_ID    Claude model to use
    NATTERBOX_MCP_URL   MCP server URL

EOF
}

# Main entry point
main() {
    case "${1:-}" in
        build)
            build
            ;;
        task)
            check_prerequisites
            shift
            run_task "$*"
            ;;
        continuous)
            check_prerequisites
            shift
            run_continuous "${1:-10}"
            ;;
        docker)
            check_prerequisites
            docker_interactive
            ;;
        docker-task)
            check_prerequisites
            shift
            docker_task "$*"
            ;;
        shell)
            shell
            ;;
        clean)
            clean
            ;;
        logs)
            logs
            ;;
        help|--help|-h)
            show_help
            ;;
        "")
            check_prerequisites
            interactive
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
