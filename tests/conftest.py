from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path: Path):
    settings = Settings(
        database_path=str(tmp_path / "test_learning_tutor.db"),
        disable_ollama=True,
        log_level="WARNING",
    )
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
