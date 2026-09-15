from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import Settings
from app.database import Database
from app.schemas import (
    ProgressUpdateRequest,
    RegenerateContentRequest,
    SectionContentRequest,
    StudyGuideRequest,
)
from app.services.content import ContentService, topic_hash
from app.services.ollama import OllamaService

STATIC_DIR = Path(__file__).parent / "static"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.ensure_runtime_directories()

    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    database = Database(settings.database_path)
    ollama = OllamaService(
        base_url=settings.ollama_base_url,
        connect_timeout_seconds=settings.ollama_connect_timeout_seconds,
        generation_timeout_seconds=settings.ollama_generation_timeout_seconds,
        preferred_models=settings.preferred_models,
        disabled=settings.disable_ollama,
    )
    content = ContentService(database, ollama)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        database.initialize()
        await ollama.initialize()
        app.state.settings = settings
        app.state.database = database
        app.state.ollama = ollama
        app.state.content = content
        yield

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "A local-first AI learning application powered by FastAPI, SQLite, "
            "and optional Ollama inference."
        ),
        lifespan=lifespan,
    )
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    def get_or_create_session(request: Request, response: Response) -> str:
        session_id = request.cookies.get(settings.session_cookie_name)
        if not session_id:
            session_id = str(uuid.uuid4())
            response.set_cookie(
                settings.session_cookie_name,
                session_id,
                max_age=settings.session_timeout_seconds,
                httponly=True,
                samesite="lax",
            )
        database.ensure_session(session_id)
        return session_id

    @app.get("/", include_in_schema=False)
    async def serve_frontend() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/health")
    async def health_check() -> dict[str, object]:
        return {
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version,
            "mode": "ollama" if ollama.available else "offline-fallback",
            "model_available": ollama.available,
            "active_model": ollama.selected_model,
            "available_models": ollama.available_models,
            "ollama_base_url": settings.ollama_base_url,
            "ollama_error": ollama.last_error,
            "ollama_generation_error": ollama.last_generation_error,
            "ollama_generation_timeout_seconds": (
                settings.ollama_generation_timeout_seconds
            ),
            # Backward-compatible fields used by the existing frontend.
            "fast_model": ollama.selected_model,
            "speed_optimized": ollama.available,
            "target_generation_time": "depends on local model and hardware",
            "database_initialized": True,
        }

    @app.post("/api/ollama/reconnect")
    async def reconnect_ollama() -> dict[str, object]:
        connected = await ollama.ensure_available(force=True)
        return {
            "connected": connected,
            "active_model": ollama.selected_model,
            "available_models": ollama.available_models,
            "error": ollama.last_error,
        }

    @app.post("/api/study-guide")
    async def generate_study_guide(
        payload: StudyGuideRequest, request: Request, response: Response
    ) -> dict[str, object]:
        session_id = get_or_create_session(request, response)
        topic = payload.topic.strip()
        structure = await content.get_study_guide(topic, payload.difficulty)
        return {
            "topic": topic,
            "difficulty": payload.difficulty,
            "structure": structure,
            "session_id": f"{session_id[:8]}...",
            "topic_hash": topic_hash(topic, payload.difficulty),
        }

    @app.post("/api/section-content")
    async def generate_section_content(
        payload: SectionContentRequest, request: Request, response: Response
    ) -> dict[str, object]:
        get_or_create_session(request, response)
        return await content.get_section_content(
            topic=payload.topic.strip(),
            section_title=payload.section_title.strip(),
            section_index=payload.section_index,
            difficulty=payload.difficulty,
            section_overview=payload.section_overview,
            learning_objectives=payload.learning_objectives,
            force_regenerate=False,
        )

    @app.post("/api/regenerate-content")
    async def regenerate_section_content(
        payload: RegenerateContentRequest, request: Request, response: Response
    ) -> dict[str, object]:
        get_or_create_session(request, response)
        return await content.get_section_content(
            topic=payload.topic.strip(),
            section_title=payload.section_title.strip(),
            section_index=payload.section_index,
            difficulty=payload.difficulty,
            section_overview=payload.section_overview,
            learning_objectives=payload.learning_objectives,
            force_regenerate=True,
        )

    @app.post("/api/progress/update")
    async def update_progress(
        payload: ProgressUpdateRequest, request: Request, response: Response
    ) -> dict[str, object]:
        session_id = get_or_create_session(request, response)
        database.update_progress(
            session_id=session_id,
            topic=payload.topic,
            topic_hash=payload.topic_hash,
            section_index=payload.section_index,
            completed=payload.completed,
            study_time=payload.study_time,
        )
        return {"success": True, "message": "Progress updated successfully"}

    @app.get("/api/progress/{guide_hash}")
    async def get_progress(
        guide_hash: str, request: Request, response: Response
    ) -> dict[str, object]:
        session_id = get_or_create_session(request, response)
        return database.get_progress(session_id, guide_hash)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    runtime_settings = Settings.from_env()
    uvicorn.run(
        "app.main:app",
        host=runtime_settings.host,
        port=runtime_settings.port,
        reload=True,
    )
