# Create .env.example file for environment variable template

env_example_content = """# AI Learning Tutor - Environment Variables Template
# Copy this file to .env and modify values as needed

# =================
# DATABASE SETTINGS
# =================

# SQLite database file path (default: learning_tutor.db)
DATABASE_PATH=learning_tutor.db

# =================
# AI MODEL SETTINGS  
# =================

# Preferred AI model for content generation (speed-optimized defaults)
PREFERRED_MODEL=llama3.2:3b

# Fallback model if preferred model is unavailable
FALLBACK_MODEL=qwen2.5:3b

# Alternative fast models you can use:
# - llama3.2:3b   (Best balance - 3-8 seconds)
# - qwen2.5:3b    (Very fast - 2-6 seconds) 
# - phi3:mini     (Lightning fast - 1-4 seconds)
# - gemma2:2b     (Fastest - 1-3 seconds)

# =================
# PERFORMANCE SETTINGS
# =================

# Maximum tokens to generate (lower = faster)
MAX_TOKENS=1200

# Temperature for AI generation (lower = more focused/faster)
TEMPERATURE=0.5

# Timeout for AI generation in seconds
TIMEOUT_SECONDS=20

# =================
# SERVER SETTINGS
# =================

# Server host (default: localhost)
SERVER_HOST=0.0.0.0

# Server port (default: 8000)
SERVER_PORT=8000

# Enable auto-reload in development
AUTO_RELOAD=true

# =================
# OLLAMA SETTINGS
# =================

# Ollama API base URL (default: http://localhost:11434)
OLLAMA_BASE_URL=http://localhost:11434

# Ollama connection timeout
OLLAMA_TIMEOUT=30

# =================
# LOGGING SETTINGS
# =================

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Enable request logging
LOG_REQUESTS=false

# =================
# FEATURE FLAGS
# =================

# Enable model warm-up on startup (recommended for M-series Macs)
ENABLE_MODEL_WARMUP=true

# Enable content caching (recommended)
ENABLE_CACHING=true

# Enable progress tracking
ENABLE_PROGRESS_TRACKING=true

# =================
# SECURITY SETTINGS  
# =================

# Session cookie name
SESSION_COOKIE_NAME=ai_tutor_session

# Session timeout in seconds (default: 30 days)
SESSION_TIMEOUT=2592000

# Enable CORS (for development)
ENABLE_CORS=true

# =================
# DEVELOPMENT SETTINGS
# =================

# Enable debug mode (shows detailed error messages)
DEBUG_MODE=false

# Enable API documentation (FastAPI docs)
ENABLE_DOCS=true

# API documentation URL path
DOCS_URL=/docs

# =================
# NOTES
# =================

# 1. All settings have sensible defaults - no .env file needed to run
# 2. Only create .env file if you want to customize these values
# 3. Never commit .env file to git (it's in .gitignore)
# 4. M-series Mac users: Keep PREFERRED_MODEL as 3B parameter model for best speed
# 5. Intel Mac users: Consider phi3:mini or gemma2:2b for better performance
"""

with open(".env.example", "w") as f:
    f.write(env_example_content)

print("✅ Created .env.example")
print("⚙️ Includes configuration options for:")
print("  • Database settings")
print("  • AI model preferences") 
print("  • Performance tuning")
print("  • Server configuration")
print("  • Ollama integration")
print("  • Security settings")
print("  • Development options")
print("  • Detailed usage notes")