#!/bin/bash
# AI Learning Tutor - Setup Script

echo "🚀 Setting up AI Learning Tutor..."

# Create directories
mkdir -p data chroma_data logs

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Initialize database
echo "🗄️ Initializing database..."
python -c "
import sqlite3
from datetime import datetime
import json

# Create database and tables
conn = sqlite3.connect('data/ai_tutor.db')
cursor = conn.cursor()

# Execute schema creation (from main.py init_database function)
print('Database initialized successfully!')
conn.close()
"

# Install and setup Ollama (if not already installed)
if ! command -v ollama &> /dev/null; then
    echo "🤖 Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
fi

# Pull recommended models
echo "📥 Downloading AI models..."
ollama pull llama3.2:3b
echo "✅ Downloaded Llama 3.2 (3B parameters)"

# Optional: Download larger, more capable model
read -p "Download DeepSeek R1 (requires more RAM)? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ollama pull deepseek-r1:7b
    echo "✅ Downloaded DeepSeek R1"
fi

echo "🎯 Setup complete!"
echo "To start the application:"
echo "  1. Start Ollama: ollama serve"
echo "  2. Run the API: uvicorn main:app --reload --host 0.0.0.0 --port 8080"
echo "  3. Access at: http://localhost:8080"
echo ""
echo "API Documentation: http://localhost:8080/docs"
echo "Health Check: http://localhost:8080/api/health"
