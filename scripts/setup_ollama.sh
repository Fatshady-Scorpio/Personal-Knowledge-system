#!/bin/bash
# Setup Ollama for local retrieval

echo "=== Ollama Setup ==="

# Check if Ollama is installed
if command -v ollama &> /dev/null; then
    echo "Ollama is already installed"
else
    echo "Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
fi

# Start Ollama service
echo "Starting Ollama service..."
ollama serve &
sleep 3

# Pull model
MODEL=${1:-"qwen2.5-coder:7b"}
echo "Pulling model: $MODEL"
ollama pull $MODEL

echo ""
echo "=== Setup Complete ==="
echo "Ollama is running at http://localhost:11434"
echo "Model: $MODEL"
echo ""
echo "Test with: ollama run $MODEL 'Hello'"
