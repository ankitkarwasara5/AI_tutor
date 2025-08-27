# 🤖 AI Learning Tutor - Speed Optimized

A lightning-fast AI-powered learning companion that generates personalized study guides with unique content for each section. Optimized for M1/M2/M3 MacBooks with 3-10 second generation times.

## ⚡ Key Features

- **🔧 Unique Content**: Each section gets tailored, specific content
- **💾 Perfect Persistence**: Progress and content automatically saved across sessions
- **🔄 Regeneration**: One-click content regeneration for quality control
- **📱 Responsive Design**: Works on desktop and mobile devices
- **🎯 Difficulty Levels**: Easy, Medium, and Hard content adaptation

## 🚀 Quick Start

### Prerequisites

1. **Python 3.9+** installed
2. **Ollama** installed and running
3. **8GB+ RAM** recommended
4. **M1/M2/M3 Mac** recommended for best performance

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd ai-learning-tutor
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install and setup Ollama:**
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull recommended fast models
   ollama pull llama3.2:3b
   ollama pull qwen2.5:3b  
   ollama pull phi3:mini
   ```

4. **Run the application:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Open your browser:**
   ```
   http://localhost:8000
   ```

## 📖 Usage Guide

### Creating Study Guides

1. **Enter Topic**: Type any subject (e.g., "Machine Learning", "React Development")
2. **Select Difficulty**: Choose Easy, Medium, or Hard
3. **Generate Guide**: Click "⚡ Create Fast Study Guide" (2-5 seconds)
4. **Start Learning**: Click any section to begin studying

### Studying Sections

1. **Open Section**: Click on any section card
2. **Read Content**: Unique, tailored content loads in 3-8 seconds
3. **Mark Complete**: Track your progress automatically
4. **Regenerate**: Click "🔄 Regenerate Content" if quality needs improvement

### Progress Tracking

- **Automatic Saving**: Progress saved automatically across sessions
- **Visual Indicators**: Progress bars and completion badges
- **Session Memory**: Resume exactly where you left off
- **Time Tracking**: Monitor study time per section

## ⚡ Performance Optimizations

### Speed Features

- **Fast Models**: Prioritizes 3B parameter models (llama3.2:3b, qwen2.5:3b)
- **Reduced Tokens**: 1200 tokens vs 3500+ for 3x speed improvement
- **Model Warm-up**: Pre-loads models for faster subsequent generations
- **Progressive Loading**: Real-time feedback during content generation

### Expected Performance

- **Study Guide**: 2-5 seconds generation
- **Section Content**: 3-8 seconds per section
- **Regeneration**: 3-8 seconds for fresh content
- **Cached Access**: <100ms for previously generated content

## 🛠 Technical Architecture

### Backend (Python/FastAPI)

- **FastAPI**: High-performance web framework
- **SQLite**: Embedded database for persistence
- **Ollama Integration**: Local AI model management
- **Speed Optimization**: Model selection and prompt engineering

### Frontend (Vanilla JS)

- **Vanilla JavaScript**: No heavy frameworks for speed
- **Progressive Enhancement**: Works without JavaScript
- **Responsive Design**: Mobile-first approach
- **Real-time Updates**: WebSocket-like experience with REST

### Database Schema

```sql
-- Study guides with topic and structure
study_guides (topic, difficulty, structure, model_used)

-- Section content with caching
section_content (topic, section_title, content, generation_time)

-- User progress tracking
user_progress (session_id, topic, section_index, completed, study_time)

-- Session management
user_sessions (session_id, created_at, metadata)
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file (optional):

```bash
# Database
DATABASE_PATH=learning_tutor.db

# Model Preferences (optional)
PREFERRED_MODEL=llama3.2:3b
FALLBACK_MODEL=qwen2.5:3b

# Performance Settings
MAX_TOKENS=1200
TEMPERATURE=0.5
TIMEOUT_SECONDS=20
```

### Model Recommendations

**For Speed (Recommended):**
- `llama3.2:3b` - Best balance of speed and quality
- `qwen2.5:3b` - Very fast generation
- `phi3:mini` - Lightning fast for basic content

**For Quality (Slower):**
- `llama3:8b` - Higher quality, 8-15 second generation
- `mixtral:8x7b` - Highest quality, 20+ second generation

## 🐛 Troubleshooting

### Common Issues

**1. Slow Generation Times**
```bash
# Check if fast models are installed
ollama list

# Install recommended fast models
ollama pull llama3.2:3b
ollama pull qwen2.5:3b
```

**2. Ollama Connection Issues**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama service
brew services restart ollama  # macOS
```

**3. Database Issues**
```bash
# Remove database to reset (loses all data)
rm learning_tutor.db

# Restart server to recreate
uvicorn main:app --reload
```

### Performance Optimization

**For M1/M2/M3 Macs:**
- Ensure Ollama uses Metal acceleration
- Use 3B parameter models for best speed/quality balance
- Monitor temperature to prevent throttling

**For Intel Macs:**
- Use smaller models (phi3:mini) for acceptable performance
- Consider using fallback templates for instant responses

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ollama** for providing local AI model management
- **FastAPI** for the high-performance web framework
- **Meta** for Llama models
- **Alibaba** for Qwen models
- **Microsoft** for Phi-3 models

## 📧 Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Search [existing issues](../../issues)
3. Create a [new issue](../../issues/new) with detailed information

---

**⚡ Built for speed, designed for learning, optimized for M-series Macs.**
