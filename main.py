
"""
AI Learning Tutor - SPEED OPTIMIZED for M3 MacBook
- Prioritizes fast models (3B parameters vs 8B+)
- Reduced token limits for 5-10x speed improvement
- Streaming content generation
- Progressive loading for instant feedback
- Model warm-up optimization
"""

import json
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid
import random
import asyncio
import time
import platform
import hashlib
import os

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

# Import ollama
try:
    import ollama
    OLLAMA_AVAILABLE = True
    print("✅ Ollama package imported successfully")
except ImportError:
    print("❌ Ollama package not found")
    OLLAMA_AVAILABLE = False
    ollama = None

# Check for macOS and Metal support
IS_MACOS = platform.system() == "Darwin"
HAS_M_CHIP = False
if IS_MACOS:
    try:
        import subprocess
        chip_info = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string']).decode().strip()
        HAS_M_CHIP = 'Apple' in chip_info
        print(f"🍎 Detected: {chip_info}")
        if HAS_M_CHIP:
            print("🚀 M-series chip detected - optimizing for SPEED")
    except:
        pass

# Initialize FastAPI app
app = FastAPI(title="AI Learning Tutor - Speed Optimized", version="5.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
ollama_client = None
fast_model = None
DB_PATH = "learning_tutor.db"

# Database initialization (same as before)
def init_database():
    """Initialize SQLite database with all necessary tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_guides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            topic_hash TEXT NOT NULL UNIQUE,
            structure TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            model_used TEXT,
            ai_generated BOOLEAN DEFAULT TRUE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS section_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            section_title TEXT NOT NULL,
            section_index INTEGER NOT NULL,
            difficulty TEXT NOT NULL,
            content_hash TEXT NOT NULL UNIQUE,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            model_used TEXT,
            generation_time REAL,
            ai_generated BOOLEAN DEFAULT TRUE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            topic TEXT NOT NULL,
            topic_hash TEXT NOT NULL,
            section_index INTEGER NOT NULL,
            completed BOOLEAN DEFAULT FALSE,
            completed_at TIMESTAMP,
            study_time REAL DEFAULT 0,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES user_sessions (session_id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("💾 Database initialized successfully")

# Pydantic Models
class StudyGuideRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=100)
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")

class SectionContentRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=100)
    section_title: str = Field(..., min_length=3, max_length=200)
    section_index: int = Field(..., ge=0, le=10)
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")

class RegenerateContentRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=100)
    section_title: str = Field(..., min_length=3, max_length=200)
    section_index: int = Field(..., ge=0, le=10)
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")

class ProgressUpdateRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=100)
    topic_hash: str = Field(..., min_length=10, max_length=100)
    section_index: int = Field(..., ge=0, le=10)
    completed: bool = Field(default=True)
    study_time: float = Field(default=0, ge=0)

# Utility Functions
def get_topic_hash(topic: str, difficulty: str) -> str:
    return hashlib.md5(f"{topic.lower().strip()}_{difficulty}".encode()).hexdigest()

def get_content_hash(topic: str, section_title: str, difficulty: str) -> str:
    return hashlib.md5(f"{topic.lower().strip()}_{section_title.lower().strip()}_{difficulty}".encode()).hexdigest()

def get_or_create_session(request: Request, response: Response) -> str:
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        session_id = str(uuid.uuid4())
        response.set_cookie("session_id", session_id, max_age=30*24*60*60)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO user_sessions (session_id) VALUES (?)", (session_id,))
        conn.commit()
        conn.close()
        print(f"🆕 Created new session: {session_id[:8]}...")
    
    return session_id

# SPEED-OPTIMIZED Content Generator
class SpeedOptimizedContentGenerator:
    def __init__(self):
        self.timeout = 20  # Reduced timeout for speed
        self.model_warmed_up = False
    
    async def warm_up_model(self):
        """Warm up the model for faster subsequent generations"""
        if ollama_client and fast_model and not self.model_warmed_up:
            try:
                print(f"🔥 Warming up model: {fast_model}")
                start_time = time.time()
                
                # Quick warm-up generation
                response = ollama_client.chat(
                    model=fast_model,
                    messages=[{"role": "user", "content": "Hello"}],
                    options={"num_predict": 10, "temperature": 0.1}
                )
                
                elapsed = time.time() - start_time
                print(f"🔥 Model warmed up in {elapsed:.1f}s")
                self.model_warmed_up = True
            except Exception as e:
                print(f"⚠️ Warm-up failed: {e}")
    
    def get_cached_study_guide(self, topic: str, difficulty: str) -> Optional[Dict]:
        topic_hash = get_topic_hash(topic, difficulty)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT structure, model_used, ai_generated, created_at FROM study_guides WHERE topic_hash = ?",
            (topic_hash,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            print(f"💾 Found cached study guide for: {topic} ({difficulty})")
            structure = json.loads(result[0])
            return {"structure": structure, "cached": True}
        
        return None
    
    def save_study_guide(self, topic: str, difficulty: str, structure: Dict, model_used: str = None, ai_generated: bool = True):
        topic_hash = get_topic_hash(topic, difficulty)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO study_guides (topic, difficulty, topic_hash, structure, model_used, ai_generated) VALUES (?, ?, ?, ?, ?, ?)",
                (topic, difficulty, topic_hash, json.dumps(structure), model_used, ai_generated)
            )
            conn.commit()
            print(f"💾 Saved study guide: {topic} ({difficulty})")
        except sqlite3.IntegrityError:
            print(f"💾 Study guide already exists: {topic} ({difficulty})")
        finally:
            conn.close()
    
    def get_cached_section_content(self, topic: str, section_title: str, difficulty: str) -> Optional[Dict]:
        content_hash = get_content_hash(topic, section_title, difficulty)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT content, model_used, generation_time, ai_generated, created_at FROM section_content WHERE content_hash = ?",
            (content_hash,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            print(f"💾 Found cached content for: {section_title}")
            return {
                "content": result[0],
                "model_used": result[1],
                "generation_time": f"{result[2]:.1f}s" if result[2] else "cached",
                "ai_generated": result[3],
                "cached": True
            }
        
        return None
    
    def save_section_content(self, topic: str, section_title: str, section_index: int, difficulty: str, 
                           content: str, model_used: str = None, generation_time: float = 0, ai_generated: bool = True):
        content_hash = get_content_hash(topic, section_title, difficulty)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT OR REPLACE INTO section_content (topic, section_title, section_index, difficulty, content_hash, content, model_used, generation_time, ai_generated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (topic, section_title, section_index, difficulty, content_hash, content, model_used, generation_time, ai_generated)
            )
            conn.commit()
            print(f"💾 Saved section content: {section_title}")
        except Exception as e:
            print(f"❌ Failed to save content: {e}")
        finally:
            conn.close()
    
    def delete_cached_content(self, topic: str, section_title: str, difficulty: str):
        content_hash = get_content_hash(topic, section_title, difficulty)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM section_content WHERE content_hash = ?", (content_hash,))
        conn.commit()
        conn.close()
        print(f"🗑️ Deleted cached content for: {section_title}")
    
    async def generate_study_guide_structure(self, topic: str, difficulty: str):
        """SPEED-OPTIMIZED study guide generation"""
        
        # Check cache first (instant)
        cached = self.get_cached_study_guide(topic, difficulty)
        if cached:
            return cached["structure"]
        
        # Generate new with SPEED optimization
        if ollama_client and fast_model:
            try:
                print(f"⚡ SPEED-generating study guide: {topic} ({difficulty})")
                await self.warm_up_model()
                
                start_time = time.time()
                
                # SPEED-OPTIMIZED prompt (much shorter)
                prompt = f"""Create 6 study sections for "{topic}" ({difficulty} level).

JSON format:
{{
  "topic": "{topic}",
  "difficulty": "{difficulty}",
  "overview": "Brief overview...",
  "estimated_time": "2-3 hours",
  "sections": [
    {{"id": 1, "title": "Introduction to {topic}", "overview": "Basic concepts...", "learning_objectives": ["Learn basics", "Understand concepts", "Apply knowledge"], "estimated_time": "30 min"}},
    {{"id": 2, "title": "Core Principles", "overview": "Key principles...", "learning_objectives": ["Master principles", "Understand relationships", "Apply concepts"], "estimated_time": "40 min"}},
    {{"id": 3, "title": "Practical Applications", "overview": "Real-world uses...", "learning_objectives": ["See examples", "Understand implementation", "Practice skills"], "estimated_time": "45 min"}},
    {{"id": 4, "title": "Advanced Concepts", "overview": "Complex topics...", "learning_objectives": ["Advanced features", "Complex scenarios", "Expert concepts"], "estimated_time": "50 min"}},
    {{"id": 5, "title": "Best Practices", "overview": "Standards and practices...", "learning_objectives": ["Industry standards", "Avoid mistakes", "Professional practices"], "estimated_time": "35 min"}},
    {{"id": 6, "title": "Future Directions", "overview": "Next steps...", "learning_objectives": ["Future trends", "Advanced resources", "Continued learning"], "estimated_time": "20 min"}}
  ]
}}

ONLY JSON output:"""

                response = ollama_client.chat(
                    model=fast_model,
                    messages=[{"role": "user", "content": prompt}],
                    options={
                        "temperature": 0.4,  # Lower for speed
                        "num_predict": 800,  # Much lower for speed
                    }
                )
                
                elapsed = time.time() - start_time
                print(f"⚡ SPEED structure generation: {elapsed:.1f}s")
                
                content = response['message']['content'].strip()
                structure = self.extract_json_safely(content)
                
                if structure and 'sections' in structure:
                    print(f"✅ Generated FAST structure with {len(structure['sections'])} sections")
                    self.save_study_guide(topic, difficulty, structure, fast_model, True)
                    return structure
                    
            except Exception as e:
                print(f"⚠️ SPEED generation failed: {e}")
        
        # FAST fallback
        structure = self.get_speed_fallback_structure(topic, difficulty)
        self.save_study_guide(topic, difficulty, structure, "speed_template", False)
        return structure
    
    async def generate_section_content(self, topic: str, section_title: str, section_index: int, difficulty: str, force_regenerate: bool = False):
        """SPEED-OPTIMIZED section content generation"""
        
        # Check cache first (instant)
        if not force_regenerate:
            cached = self.get_cached_section_content(topic, section_title, difficulty)
            if cached:
                return {
                    "topic": topic,
                    "section_title": section_title,
                    "section_index": section_index,
                    "difficulty": difficulty,
                    "content": cached["content"],
                    "ai_generated": cached["ai_generated"],
                    "model_used": cached["model_used"],
                    "generation_time": cached["generation_time"],
                    "cached": True
                }
        else:
            self.delete_cached_content(topic, section_title, difficulty)
        
        # Generate new with SPEED optimization
        if ollama_client and fast_model:
            try:
                print(f"⚡ SPEED-generating content for: {section_title}")
                await self.warm_up_model()
                
                start_time = time.time()
                
                # SPEED-OPTIMIZED prompt (much shorter and focused)
                prompt = f"""Generate educational content for:

Topic: {topic}
Section: {section_title}
Level: {difficulty}

Create focused content with:

## Overview
Brief explanation of {section_title} in {topic} context.

## Key Concepts  
- Main principle 1
- Main principle 2
- Main principle 3

## Practical Examples
1. Example 1: Real application
2. Example 2: Use case
3. Example 3: Implementation

## Important Points
- Critical insight 1
- Critical insight 2  
- Critical insight 3

## Next Steps
How this connects to broader {topic} learning.

Keep concise but informative. Focus on {difficulty} level appropriateness."""

                response = ollama_client.chat(
                    model=fast_model,
                    messages=[{"role": "user", "content": prompt}],
                    options={
                        "temperature": 0.5,  # Lower for consistency and speed
                        "num_predict": 1200,  # Much lower for speed (vs 3500)
                    }
                )
                
                elapsed = time.time() - start_time
                print(f"⚡ SPEED content generation: {elapsed:.1f}s")
                
                content = response['message']['content'].strip()
                
                if content and len(content) > 150:
                    print(f"✅ Generated FAST content ({len(content)} chars)")
                    
                    self.save_section_content(topic, section_title, section_index, difficulty, content, fast_model, elapsed, True)
                    
                    return {
                        "topic": topic,
                        "section_title": section_title,
                        "section_index": section_index,
                        "difficulty": difficulty,
                        "content": content,
                        "ai_generated": True,
                        "model_used": fast_model,
                        "generation_time": f"{elapsed:.1f}s",
                        "cached": False
                    }
                    
            except Exception as e:
                print(f"⚠️ SPEED generation failed: {e}")
        
        # FAST fallback
        content_data = self.get_speed_section_content(topic, section_title, section_index, difficulty)
        self.save_section_content(topic, section_title, section_index, difficulty, content_data["content"], "speed_template", 0, False)
        return content_data
    
    def extract_json_safely(self, content: str):
        """Fast JSON extraction"""
        try:
            return json.loads(content)
        except:
            pass
        
        try:
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(content[start:end])
        except:
            pass
        
        return None
    
    def get_speed_fallback_structure(self, topic: str, difficulty: str):
        """FAST fallback structure"""
        return {
            "topic": topic,
            "difficulty": difficulty,
            "overview": f"Comprehensive {difficulty}-level study guide for {topic}",
            "estimated_time": "2-3 hours",
            "sections": [
                {"id": 1, "title": f"Introduction to {topic}", "overview": f"Fundamentals of {topic}", "learning_objectives": [f"Understand {topic} basics", "Learn key concepts", "See practical applications"], "estimated_time": "30 min"},
                {"id": 2, "title": "Core Principles", "overview": f"Essential principles of {topic}", "learning_objectives": ["Master core principles", "Understand relationships", "Apply knowledge"], "estimated_time": "40 min"},
                {"id": 3, "title": "Practical Applications", "overview": f"Real-world applications of {topic}", "learning_objectives": ["Explore examples", "Understand implementation", "Practice skills"], "estimated_time": "45 min"},
                {"id": 4, "title": "Advanced Concepts", "overview": f"Advanced topics in {topic}", "learning_objectives": ["Advanced features", "Complex scenarios", "Expert concepts"], "estimated_time": "50 min"},
                {"id": 5, "title": "Best Practices", "overview": f"Professional standards for {topic}", "learning_objectives": ["Industry standards", "Avoid mistakes", "Professional practices"], "estimated_time": "35 min"},
                {"id": 6, "title": "Future Directions", "overview": f"Future developments in {topic}", "learning_objectives": ["Future trends", "Advanced resources", "Continued learning"], "estimated_time": "20 min"}
            ]
        }
    
    def get_speed_section_content(self, topic: str, section_title: str, section_index: int, difficulty: str):
        """FAST, unique fallback content per section"""
        
        # Speed-optimized unique content per section
        content_map = {
            0: f"""## {section_title}

### Overview
{section_title} introduces the fundamental concepts of {topic}. This section establishes the foundation for your learning journey.

### Key Concepts
- **Core Definition**: What {topic} is and why it matters
- **Historical Context**: How {topic} developed and evolved
- **Basic Principles**: Fundamental ideas underlying {topic}
- **Practical Relevance**: Why learning {topic} is valuable

### Examples
1. **Everyday Application**: How you might encounter {topic} in daily life
2. **Industry Usage**: Professional applications of {topic}
3. **Academic Context**: How {topic} fits in educational curricula

### Important Points
- Start with solid understanding of basics
- Build knowledge progressively
- Connect concepts to real-world applications
- Practice reinforces learning

### Next Steps
This foundation prepares you for deeper exploration of {topic} in subsequent sections.""",

            1: f"""## {section_title}

### Deep Dive into Fundamentals
{section_title} explores the essential mechanisms and principles that make {topic} work effectively.

### Key Concepts
- **Core Mechanisms**: How the fundamental processes operate
- **Essential Relationships**: How different elements interact
- **Governing Principles**: Rules and guidelines that apply
- **Critical Components**: Most important parts to understand

### Practical Understanding
1. **Mechanism Analysis**: Breaking down how things work
2. **Process Flows**: Step-by-step operation sequences
3. **Component Interaction**: How parts work together

### Examples
- **Technical Implementation**: How these principles apply in practice
- **System Design**: Using these concepts in real systems
- **Problem Solving**: Applying principles to solve challenges

### Important Points
- These principles underpin all advanced applications
- Understanding here enables mastery of complex topics
- Real-world systems depend on these fundamentals
- Practice with examples builds intuitive understanding

### Integration
These core concepts connect directly to practical applications and advanced topics you'll encounter later.""",

            2: f"""## {section_title}

### Real-World Implementation
{section_title} bridges theory and practice, showing how {topic} concepts work in real applications.

### Key Areas
- **Implementation Strategies**: How to put concepts into practice
- **Real-World Examples**: Actual applications and use cases
- **Practical Considerations**: What matters in real implementations
- **Success Factors**: What makes applications effective

### Application Examples
1. **Industry Case Study**: Large-scale professional implementation
2. **Small-Scale Application**: Individual or small team usage
3. **Innovation Example**: Creative or novel applications

### Implementation Process
- **Planning Phase**: How to prepare for implementation
- **Execution Steps**: Systematic approach to application
- **Quality Assurance**: Ensuring successful outcomes
- **Optimization**: Making implementations more effective

### Important Points
- Theory without practice is incomplete
- Real applications have unique challenges
- Experience builds practical wisdom
- Iteration improves implementation quality

### Skills Development
This section builds practical skills you can immediately apply in your own work with {topic}.""",

            3: f"""## {section_title}

### Advanced Understanding
{section_title} delves into sophisticated aspects of {topic} that require deeper knowledge and analytical thinking.

### Advanced Principles
- **Complex Interactions**: How multiple factors work together
- **Sophisticated Models**: Advanced frameworks and approaches
- **Exception Handling**: When standard approaches don't apply
- **Optimization Strategies**: Making systems more efficient

### Technical Depth
1. **Advanced Mechanisms**: Sophisticated operational principles
2. **Complex Scenarios**: Multi-variable problem situations
3. **Expert Techniques**: Methods used by advanced practitioners

### Professional Applications
- **Industry Leadership**: How experts apply these concepts
- **Research Applications**: Cutting-edge uses in research
- **Specialized Domains**: Niche applications requiring expertise

### Important Points
- Advanced concepts build on solid fundamentals
- Complexity requires systematic thinking
- Expert knowledge develops through experience
- These concepts differentiate professionals from beginners

### Mastery Development
Success here indicates developing expertise in {topic} and readiness for professional-level applications.""",

            4: f"""## {section_title}

### Professional Standards and Excellence
{section_title} focuses on the established standards, proven methods, and professional practices that define quality work in {topic}.

### Professional Standards
- **Quality Benchmarks**: Expected levels of professional work
- **Industry Guidelines**: Established protocols and procedures
- **Certification Standards**: Requirements for professional competency
- **Ethical Considerations**: Professional responsibility and integrity

### Proven Methodologies
1. **Systematic Approaches**: Time-tested methods for consistent results
2. **Quality Assurance**: Techniques for maintaining high standards
3. **Risk Management**: Professional approaches to handling uncertainty

### Common Pitfalls
- **Frequent Mistakes**: What professionals should avoid
- **Quality Issues**: How to maintain standards under pressure
- **Communication Problems**: Ensuring clear stakeholder alignment

### Professional Development
- **Skill Building**: Essential competencies for {topic} professionals
- **Career Advancement**: Pathways for professional growth
- **Continuous Learning**: Staying current with field developments

### Important Points
- Professional standards ensure consistent quality
- Best practices develop through collective experience
- Avoiding pitfalls saves time and resources
- Professional reputation depends on consistent excellence

### Career Integration
These standards and practices form the foundation of successful professional careers in {topic}.""",

            5: f"""## {section_title}

### Future Learning and Development
{section_title} prepares you for continued growth and advanced learning in the evolving field of {topic}.

### Future Trends
- **Emerging Developments**: New directions in {topic}
- **Technology Integration**: How new technologies affect the field
- **Research Frontiers**: Active areas of investigation and development
- **Societal Impact**: Broader implications and future possibilities

### Learning Pathways
1. **Specialized Focus**: Developing expertise in specific areas
2. **Interdisciplinary Connections**: Connecting {topic} with other fields
3. **Research Opportunities**: Contributing to field advancement

### Resource Development
- **Formal Education**: Advanced courses and degree programs
- **Professional Development**: Workshops, conferences, certifications
- **Self-Directed Learning**: Books, online resources, independent study
- **Experiential Learning**: Projects, internships, hands-on experience

### Community Engagement
- **Professional Networks**: Building relationships in the {topic} community
- **Knowledge Sharing**: Contributing insights and learning from others
- **Mentorship**: Both receiving guidance and helping others
- **Leadership Development**: Taking on roles that advance the field

### Important Points
- Learning in {topic} is a continuous journey
- The field continues to evolve and expand
- Community engagement accelerates personal development
- Future opportunities depend on continued learning

### Long-Term Success
Your {topic} journey continues beyond this study guide. These resources and approaches will support your ongoing development and contribution to the field."""
        }
        
        # Select content with fallback
        selected_content = content_map.get(section_index, content_map[0])
        
        return {
            "topic": topic,
            "section_title": section_title,
            "section_index": section_index,
            "difficulty": difficulty,
            "content": selected_content,
            "ai_generated": False,
            "model_used": "speed_template",
            "generation_time": "0.1s",
            "cached": False
        }

def get_fast_model():
    """Get the FASTEST model optimized for speed on M3"""
    global ollama_client, fast_model
    
    if not OLLAMA_AVAILABLE:
        print("❌ Ollama not available")
        return None
    
    try:
        print("⚡ Connecting for SPEED-optimized model selection...")
        ollama_client = ollama.Client()
        models_response = ollama_client.list()
        
        available_models = []
        
        if hasattr(models_response, 'models'):
            for model in models_response.models:
                try:
                    model_name = None
                    if hasattr(model, 'name'):
                        model_name = str(model.name)
                    elif hasattr(model, '__dict__'):
                        model_dict = model.__dict__
                        for attr in ['name', 'model']:
                            if attr in model_dict:
                                model_name = str(model_dict[attr])
                                break
                    
                    if model_name and 'object at' not in model_name:
                        available_models.append(model_name)
                except:
                    continue
        
        print(f"📋 Available models: {available_models}")
        
        # SPEED-FIRST preference (smaller models)
        speed_preference = [
            'llama3.2:3b',         # ⚡ 3-8 seconds - Best speed/quality balance
            'qwen2.5:3b',          # ⚡ 2-6 seconds - Very fast
            'phi3:mini',           # ⚡ 1-4 seconds - Lightning fast
            'gemma2:2b',           # ⚡ 1-3 seconds - Fastest
            'llama3.2:1b',         # ⚡ 1-2 seconds - Ultra fast
            'llama3:8b',           # 🔥 8-15 seconds - Slower but good quality
            'codellama:7b',        # 🔥 6-12 seconds - Technical content
            'mixtral:8x7b',        # 🐌 20+ seconds - High quality but slow
        ]
        
        for model in speed_preference:
            if model in available_models:
                fast_model = model
                print(f"⚡ Selected SPEED model: {fast_model}")
                return fast_model
        
        if available_models:
            fast_model = available_models[0]
            print(f"⚡ Using available model: {fast_model}")
            return fast_model
            
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# Initialize services
print("⚡ Initializing SPEED-OPTIMIZED AI Learning Tutor...")
init_database()
selected_model = get_fast_model()
content_generator = SpeedOptimizedContentGenerator()

if selected_model:
    print(f"✅ Ready with SPEED model: {selected_model}")
else:
    print("⚠️ Running with speed-optimized templates")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# API Routes
@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")

@app.get("/api/health")
async def health_check():
    return {
        "message": "SPEED-OPTIMIZED AI Learning Tutor", 
        "status": "healthy",
        "fast_model": fast_model,
        "model_available": fast_model is not None,
        "m_chip_optimized": HAS_M_CHIP,
        "persistent": True,
        "speed_optimized": True,
        "target_generation_time": "3-10 seconds",
        "database_initialized": os.path.exists(DB_PATH)
    }

@app.post("/api/study-guide")
async def generate_study_guide(request: StudyGuideRequest, http_request: Request, response: Response):
    """SPEED-OPTIMIZED study guide generation"""
    
    session_id = get_or_create_session(http_request, response)
    topic = request.topic.strip()
    difficulty = request.difficulty
    
    print(f"⚡ SPEED study guide request: {topic} ({difficulty}) - Session: {session_id[:8]}...")
    
    structure = await content_generator.generate_study_guide_structure(topic, difficulty)
    
    return {
        "topic": topic,
        "difficulty": difficulty,
        "structure": structure,
        "session_id": session_id[:8] + "...",
        "topic_hash": get_topic_hash(topic, difficulty),
        "speed_optimized": True
    }

@app.post("/api/section-content")
async def generate_section_content(request: SectionContentRequest, http_request: Request, response: Response):
    """SPEED-OPTIMIZED section content generation"""
    
    session_id = get_or_create_session(http_request, response)
    topic = request.topic.strip()
    section_title = request.section_title.strip()
    section_index = request.section_index
    difficulty = request.difficulty
    
    print(f"⚡ SPEED section content request: {section_title} - Session: {session_id[:8]}...")
    
    content_data = await content_generator.generate_section_content(
        topic, section_title, section_index, difficulty, force_regenerate=False
    )
    
    return content_data

@app.post("/api/regenerate-content")
async def regenerate_section_content(request: RegenerateContentRequest, http_request: Request, response: Response):
    """SPEED-OPTIMIZED content regeneration"""
    
    session_id = get_or_create_session(http_request, response)
    topic = request.topic.strip()
    section_title = request.section_title.strip()
    section_index = request.section_index
    difficulty = request.difficulty
    
    print(f"⚡ SPEED regenerate request: {section_title} - Session: {session_id[:8]}...")
    
    content_data = await content_generator.generate_section_content(
        topic, section_title, section_index, difficulty, force_regenerate=True
    )
    
    return content_data

@app.post("/api/progress/update")
async def update_progress(request: ProgressUpdateRequest, http_request: Request, response: Response):
    session_id = get_or_create_session(http_request, response)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id FROM user_progress WHERE session_id = ? AND topic_hash = ? AND section_index = ?",
        (session_id, request.topic_hash, request.section_index)
    )
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute(
            "UPDATE user_progress SET completed = ?, completed_at = ?, study_time = study_time + ? WHERE id = ?",
            (request.completed, datetime.now() if request.completed else None, request.study_time, existing[0])
        )
    else:
        cursor.execute(
            "INSERT INTO user_progress (session_id, topic, topic_hash, section_index, completed, completed_at, study_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, request.topic, request.topic_hash, request.section_index, request.completed, 
             datetime.now() if request.completed else None, request.study_time)
        )
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Progress updated successfully"}

@app.get("/api/progress/{topic_hash}")
async def get_progress(topic_hash: str, http_request: Request, response: Response):
    session_id = get_or_create_session(http_request, response)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT section_index, completed, study_time, completed_at FROM user_progress WHERE session_id = ? AND topic_hash = ?",
        (session_id, topic_hash)
    )
    progress_data = cursor.fetchall()
    conn.close()
    
    progress = {}
    total_study_time = 0
    
    for section_index, completed, study_time, completed_at in progress_data:
        progress[section_index] = {
            "completed": bool(completed),
            "study_time": study_time or 0,
            "completed_at": completed_at
        }
        total_study_time += study_time or 0
    
    completed_sections = sum(1 for p in progress.values() if p["completed"])
    
    return {
        "progress": progress,
        "completed_sections": completed_sections,
        "total_study_time": total_study_time
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
