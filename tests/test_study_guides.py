def test_create_study_guide_without_ollama(client):
    response = client.post(
        "/api/study-guide",
        json={"topic": "Machine Learning", "difficulty": "medium"},
    )

    assert response.status_code == 200
    payload = response.json()
    structure = payload["structure"]
    assert payload["topic"] == "Machine Learning"
    assert len(payload["topic_hash"]) == 64
    assert len(structure["sections"]) == 6
    assert structure["difficulty"] == "medium"
    assert structure["prerequisites"]
    assert structure["learning_outcomes"]
    assert all(section["learning_objectives"] for section in structure["sections"])
    assert all(section["key_concepts"] for section in structure["sections"])


def test_study_guide_is_cached(client):
    request = {"topic": "Python", "difficulty": "easy"}

    first = client.post("/api/study-guide", json=request)
    second = client.post("/api/study-guide", json=request)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["structure"] == second.json()["structure"]
    assert first.json()["topic_hash"] == second.json()["topic_hash"]


def test_invalid_difficulty_is_rejected(client):
    response = client.post(
        "/api/study-guide",
        json={"topic": "Python", "difficulty": "expert"},
    )

    assert response.status_code == 422


def test_short_topic_is_rejected(client):
    response = client.post(
        "/api/study-guide",
        json={"topic": "A", "difficulty": "easy"},
    )

    assert response.status_code == 422
