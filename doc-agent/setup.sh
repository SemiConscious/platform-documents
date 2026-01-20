#!/bin/bash
# Setup script for the Platform Documentation Agent

set -e

echo "Setting up Platform Documentation Agent..."

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -e .

# Copy config if not exists
if [ ! -f "config/config.yaml" ]; then
    echo "Creating config from example..."
    cp config/config.example.yaml config/config.yaml
fi

# Create required directories
mkdir -p store logs docs

echo ""
echo "Setup complete!"
echo ""
echo "To activate the environment:"
echo "  source venv/bin/activate"
echo ""
echo "To run the documentation agent:"
echo "  doc-agent --help"
echo ""
echo "Don't forget to:"
echo "  1. Set ANTHROPIC_API_KEY environment variable"
echo "  2. Configure config/config.yaml with your sources"
