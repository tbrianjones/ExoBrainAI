#!/bin/bash
#
# One-time setup for Claude Writer
# Run this after cloning the repo: ./scripts/init.sh
#

set -e

echo "Setting up Claude Writer..."
echo

# Get the repo root (parent of scripts/)
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# Create Python virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists."
fi

# Activate and install dependencies
echo "Installing Python dependencies..."
source .venv/bin/activate
pip install -q -r requirements.txt

# Copy .env.example to .env if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "Creating .env from template..."
        cp .env.example .env
        echo "Note: Edit .env to add your API keys (optional, for /gemini command)"
    fi
else
    echo ".env already exists."
fi

echo
echo "Setup complete!"
echo
echo "Next steps:"
echo "  1. Type /ideate to start exploring an idea"
echo "  2. (Optional) Edit .env to add your Gemini API key for image generation"
echo
