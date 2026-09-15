from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "Local AI Learning Tutor"
    app_version: str = "1.3.0"
    database_path: str = "data/learning_tutor.db"
    ollama_base_url: str = "http://localhost:11434"
    ollama_connect_timeout_seconds: int = 8
    ollama_generation_timeout_seconds: int = 300
    preferred_models: tuple[str, ...] = (
        "qwen3:8b",
        "llama3.1:8b",
        "gemma3:4b",
        "qwen3:4b",
        "llama3.2:3b",
    )
    disable_ollama: bool = False
    session_cookie_name: str = "ai_tutor_session"
    session_timeout_seconds: int = 30 * 24 * 60 * 60
    log_level: str = "INFO"
    host: str = "127.0.0.1"
    port: int = 8000

    @classmethod
    def from_env(cls) -> Settings:
        defaults = cls()
        models_raw = os.getenv("PREFERRED_MODELS", "").strip()
        preferred_models = (
            tuple(model.strip() for model in models_raw.split(",") if model.strip())
            if models_raw
            else defaults.preferred_models
        )

        legacy_timeout = os.getenv("OLLAMA_TIMEOUT_SECONDS")
        connect_timeout = _as_int(
            os.getenv("OLLAMA_CONNECT_TIMEOUT_SECONDS", legacy_timeout),
            defaults.ollama_connect_timeout_seconds,
        )
        generation_timeout = _as_int(
            os.getenv("OLLAMA_GENERATION_TIMEOUT_SECONDS"),
            defaults.ollama_generation_timeout_seconds,
        )

        return cls(
            database_path=os.getenv("DATABASE_PATH", defaults.database_path),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", defaults.ollama_base_url),
            ollama_connect_timeout_seconds=connect_timeout,
            ollama_generation_timeout_seconds=generation_timeout,
            preferred_models=preferred_models,
            disable_ollama=_as_bool(os.getenv("DISABLE_OLLAMA"), False),
            session_cookie_name=os.getenv(
                "SESSION_COOKIE_NAME", defaults.session_cookie_name
            ),
            session_timeout_seconds=_as_int(
                os.getenv("SESSION_TIMEOUT_SECONDS"), defaults.session_timeout_seconds
            ),
            log_level=os.getenv("LOG_LEVEL", defaults.log_level).upper(),
            host=os.getenv("APP_HOST", defaults.host),
            port=_as_int(os.getenv("APP_PORT"), defaults.port),
        )

    def ensure_runtime_directories(self) -> None:
        if self.database_path == ":memory:":
            return
        Path(self.database_path).expanduser().resolve().parent.mkdir(
            parents=True, exist_ok=True
        )
