from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class Database:
    """Small SQLite repository layer for tutor persistence and caching."""

    def __init__(self, path: str):
        self.path = path

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        if self.path != ":memory:":
            Path(self.path).expanduser().resolve().parent.mkdir(
                parents=True, exist_ok=True
            )

        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS study_guides (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    topic_hash TEXT NOT NULL UNIQUE,
                    structure TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    model_used TEXT,
                    ai_generated INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS section_content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    section_title TEXT NOT NULL,
                    section_index INTEGER NOT NULL,
                    difficulty TEXT NOT NULL,
                    content_hash TEXT NOT NULL UNIQUE,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    model_used TEXT,
                    generation_time REAL,
                    ai_generated INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS user_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    topic_hash TEXT NOT NULL,
                    section_index INTEGER NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0,
                    completed_at TEXT,
                    study_time REAL NOT NULL DEFAULT 0,
                    last_accessed TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id),
                    UNIQUE(session_id, topic_hash, section_index)
                );
                """
            )

    def ensure_session(self, session_id: str) -> None:
        now = utc_now()
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO user_sessions (session_id, created_at, last_accessed)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    last_accessed = excluded.last_accessed
                """,
                (session_id, now, now),
            )

    def get_study_guide(self, topic_hash: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT structure, model_used, ai_generated, created_at
                FROM study_guides
                WHERE topic_hash = ?
                """,
                (topic_hash,),
            ).fetchone()

        if row is None:
            return None
        return {
            "structure": json.loads(row["structure"]),
            "model_used": row["model_used"],
            "ai_generated": bool(row["ai_generated"]),
            "created_at": row["created_at"],
        }

    def save_study_guide(
        self,
        *,
        topic: str,
        difficulty: str,
        topic_hash: str,
        structure: dict[str, Any],
        model_used: str,
        ai_generated: bool,
    ) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO study_guides (
                    topic, difficulty, topic_hash, structure, created_at,
                    model_used, ai_generated
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(topic_hash) DO UPDATE SET
                    structure=excluded.structure,
                    created_at=excluded.created_at,
                    model_used=excluded.model_used,
                    ai_generated=excluded.ai_generated
                """,
                (
                    topic,
                    difficulty,
                    topic_hash,
                    json.dumps(structure),
                    utc_now(),
                    model_used,
                    int(ai_generated),
                ),
            )

    def get_section_content(self, content_hash: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT content, model_used, generation_time, ai_generated, created_at
                FROM section_content
                WHERE content_hash = ?
                """,
                (content_hash,),
            ).fetchone()

        if row is None:
            return None
        return {
            "content": row["content"],
            "model_used": row["model_used"],
            "generation_time": row["generation_time"],
            "ai_generated": bool(row["ai_generated"]),
            "created_at": row["created_at"],
        }

    def save_section_content(
        self,
        *,
        topic: str,
        section_title: str,
        section_index: int,
        difficulty: str,
        content_hash: str,
        content: str,
        model_used: str,
        generation_time: float,
        ai_generated: bool,
    ) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO section_content (
                    topic, section_title, section_index, difficulty, content_hash,
                    content, created_at, model_used, generation_time, ai_generated
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(content_hash) DO UPDATE SET
                    content=excluded.content,
                    created_at=excluded.created_at,
                    model_used=excluded.model_used,
                    generation_time=excluded.generation_time,
                    ai_generated=excluded.ai_generated
                """,
                (
                    topic,
                    section_title,
                    section_index,
                    difficulty,
                    content_hash,
                    content,
                    utc_now(),
                    model_used,
                    generation_time,
                    int(ai_generated),
                ),
            )

    def delete_section_content(self, content_hash: str) -> None:
        with self.connection() as conn:
            conn.execute(
                "DELETE FROM section_content WHERE content_hash = ?", (content_hash,)
            )

    def update_progress(
        self,
        *,
        session_id: str,
        topic: str,
        topic_hash: str,
        section_index: int,
        completed: bool,
        study_time: float,
    ) -> None:
        now = utc_now()
        completed_at = now if completed else None
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO user_progress (
                    session_id, topic, topic_hash, section_index, completed,
                    completed_at, study_time, last_accessed
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id, topic_hash, section_index) DO UPDATE SET
                    completed=excluded.completed,
                    completed_at=excluded.completed_at,
                    study_time=user_progress.study_time + excluded.study_time,
                    last_accessed=excluded.last_accessed
                """,
                (
                    session_id,
                    topic,
                    topic_hash,
                    section_index,
                    int(completed),
                    completed_at,
                    study_time,
                    now,
                ),
            )

    def get_progress(self, session_id: str, topic_hash: str) -> dict[str, Any]:
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT section_index, completed, study_time, completed_at
                FROM user_progress
                WHERE session_id = ? AND topic_hash = ?
                ORDER BY section_index
                """,
                (session_id, topic_hash),
            ).fetchall()

        progress: dict[int, dict[str, Any]] = {}
        total_study_time = 0.0
        for row in rows:
            progress[row["section_index"]] = {
                "completed": bool(row["completed"]),
                "study_time": row["study_time"] or 0,
                "completed_at": row["completed_at"],
            }
            total_study_time += row["study_time"] or 0

        return {
            "progress": progress,
            "completed_sections": sum(
                1 for item in progress.values() if item["completed"]
            ),
            "total_study_time": total_study_time,
        }
