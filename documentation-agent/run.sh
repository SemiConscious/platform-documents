#!/bin/bash
# Natterbox Documentation Agent - Helper Script
#
# Usage:
#   ./run.sh                    # Interactive mode
#   ./run.sh task "Your task"   # Run a specific task
#   ./run.sh build              # Build Docker image
#   ./run.sh shell              # Open shell in container

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

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
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check for AWS credentials
    if [[ -z "$AWS_ACCESS_KEY_ID" ]] && [[ ! -f ~/.aws/credentials ]]; then
        log_warn "AWS credentials not found. Run 'aws configure' first."
    fi
}

# Build Docker image
build() {
    log_info "Building Docker image..."
    docker-compose build
    log_info "Build complete!"
}

# Run in interactive mode
interactive() {
    log_info "Starting interactive mode..."
    docker-compose run --rm agent --interactive
}

# Run a specific task
run_task() {
    local task="$1"
    if [[ -z "$task" ]]; then
        log_error "No task specified"
        echo "Usage: $0 task \"Your task description\""
        exit 1
    fi
    log_info "Running task: $task"
    docker-compose run --rm agent --task "$task"
}

# Open shell in container
shell() {
    log_info "Opening shell in container..."
    docker-compose run --rm --entrypoint /bin/bash agent
}

# Clean up containers and volumes
clean() {
    log_info "Cleaning up..."
    docker-compose down -v
    rm -rf workspace output
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

Commands:
    (none)          Start in interactive mode
    build           Build the Docker image
    task "..."      Run a specific documentation task
    shell           Open a bash shell in the container
    clean           Remove containers and clean up
    logs            Show container logs
    help            Show this help message

Examples:
    $0                                          # Interactive mode
    $0 build                                    # Build Docker image
    $0 task "Create emergency response runbook" # Run specific task
    $0 shell                                    # Debug shell

Environment Variables:
    AWS_REGION          AWS region for Bedrock (default: us-east-1)
    AWS_PROFILE         AWS credentials profile
    NATTERBOX_MCP_URL   MCP server URL

EOF
}

# Main entry point
main() {
    check_prerequisites
    
    case "${1:-}" in
        build)
            build
            ;;
        task)
            shift
            run_task "$*"
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
