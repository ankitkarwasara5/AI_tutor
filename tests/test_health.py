def test_health_endpoint(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["mode"] == "offline-fallback"
    assert payload["model_available"] is False
    assert payload["database_initialized"] is True


def test_frontend_is_served(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Local AI Learning Tutor" in response.text
