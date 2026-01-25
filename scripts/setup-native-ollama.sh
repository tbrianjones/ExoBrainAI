#!/bin/bash
#
# Setup Native Ollama for ExoBrain
#
# This script installs and configures Ollama to run natively on your Mac.
# Native Ollama uses Metal GPU acceleration and is 20-30x faster than Docker.
#
# Usage: ./scripts/setup-native-ollama.sh
#

set -e

# Find the project root (where .env lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load .env file if it exists
if [[ -f "$PROJECT_ROOT/.env" ]]; then
    echo "Loading settings from .env..."
    # Export variables from .env (skip comments and empty lines)
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

echo "==================================="
echo "ExoBrain Native Ollama Setup"
echo "==================================="
echo

# Check if running on Mac
if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: This script is for macOS only."
    echo "On Linux, install Ollama via: curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "Error: Homebrew is required but not installed."
    echo "Install it from: https://brew.sh"
    exit 1
fi

# Install Ollama if not present
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama via Homebrew..."
    brew install ollama
    echo "Ollama installed successfully."
else
    echo "Ollama is already installed: $(which ollama)"
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo
    echo "Starting Ollama service..."

    # Check if launchd service exists
    if brew services list | grep -q "ollama"; then
        brew services start ollama
        echo "Ollama service started via Homebrew."
    else
        echo "Starting Ollama in background..."
        ollama serve &> /dev/null &
        sleep 2
    fi

    # Wait for Ollama to be ready
    echo "Waiting for Ollama to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:11434/api/tags &> /dev/null; then
            echo "Ollama is ready."
            break
        fi
        sleep 1
    done
else
    echo "Ollama is already running."
fi

# Pull required models
echo
echo "Pulling required models..."

# Use settings from .env, fall back to defaults
LLM_MODEL="${EXOBRAIN_LLM_MODEL:-llama3.1:8b}"
EMBED_MODEL="${EXOBRAIN_EMBED_MODEL:-nomic-embed-text}"

echo "  LLM model: $LLM_MODEL"
echo "  Embed model: $EMBED_MODEL"
echo

ollama pull "$LLM_MODEL"
ollama pull "$EMBED_MODEL"

# Verify models
echo
echo "Installed models:"
ollama list

# Set recommended environment variables
echo
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo
echo "Ollama is now running natively with GPU acceleration."
echo
echo "To use with ExoBrain, ensure your .env file has:"
echo "  OLLAMA_MODE=native"
echo
echo "Then start ExoBrain:"
echo "  docker compose up -d"
echo
echo "To keep Ollama running in the background:"
echo "  brew services start ollama"
echo
echo "To stop Ollama:"
echo "  brew services stop ollama"
echo
