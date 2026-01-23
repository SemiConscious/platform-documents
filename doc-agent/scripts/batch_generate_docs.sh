#!/bin/bash
# Batch documentation generation for all repos in the cache directory
# Usage: ./scripts/batch_generate_docs.sh [profile]

set -e

PROFILE="${1:-premium}"
REPO_CACHE="./repo-cache"
OUTPUT_BASE="../docs/services"
LOG_DIR="./logs"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="$LOG_DIR/batch-$PROFILE-$TIMESTAMP.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Start logging
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=================================================================="
echo "  Batch Documentation Generation"
echo "  Profile: $PROFILE"
echo "  Started: $(date)"
echo "=================================================================="
echo ""

# Get list of repos
REPOS=$(ls -1 "$REPO_CACHE" | sort)
TOTAL=$(echo "$REPOS" | wc -l | tr -d ' ')
CURRENT=0
SUCCEEDED=0
FAILED=0
FAILED_REPOS=""

echo "Found $TOTAL repositories to process"
echo ""

# Process each repo
for repo in $REPOS; do
    CURRENT=$((CURRENT + 1))
    REPO_PATH="$REPO_CACHE/$repo"
    OUTPUT_DIR="$OUTPUT_BASE/$repo"
    
    echo "=================================================================="
    echo "[$CURRENT/$TOTAL] Processing: $repo"
    echo "  Input: $REPO_PATH"
    echo "  Output: $OUTPUT_DIR"
    echo "=================================================================="
    
    START_TIME=$(date +%s)
    
    # Run the documentation generator
    if aws-vault exec sso-dev03-admin -- python3 -m src.main ai-docs \
        --profile "$PROFILE" \
        --output "$OUTPUT_DIR" \
        "$REPO_PATH"; then
        
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        echo ""
        echo "✓ SUCCESS: $repo completed in ${DURATION}s"
        SUCCEEDED=$((SUCCEEDED + 1))
    else
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        echo ""
        echo "✗ FAILED: $repo failed after ${DURATION}s"
        FAILED=$((FAILED + 1))
        FAILED_REPOS="$FAILED_REPOS $repo"
    fi
    
    echo ""
done

# Final summary
echo "=================================================================="
echo "  Batch Generation Complete"
echo "  Finished: $(date)"
echo "=================================================================="
echo ""
echo "Results:"
echo "  Total:     $TOTAL"
echo "  Succeeded: $SUCCEEDED"
echo "  Failed:    $FAILED"
echo ""

if [ $FAILED -gt 0 ]; then
    echo "Failed repos:$FAILED_REPOS"
fi

# Count generated files
TOTAL_DOCS=$(find "$OUTPUT_BASE" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
TOTAL_WORDS=$(find "$OUTPUT_BASE" -name "*.md" -exec cat {} \; 2>/dev/null | wc -w | tr -d ' ')

echo ""
echo "Output Statistics:"
echo "  Total documents: $TOTAL_DOCS"
echo "  Total words: $TOTAL_WORDS"
echo ""
echo "Log file: $LOG_FILE"
